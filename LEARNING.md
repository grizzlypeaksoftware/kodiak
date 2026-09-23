# Kodiak Learning Journal

A running log of concepts, decisions, and results. Newest entries at the bottom of each phase.
Each entry has three parts: **what** we did, **why** we did it, and **what we learned**.

---

## Phase 0: Environment check (2026-09-23)

### The machine

| Item | Value | Why it matters |
|---|---|---|
| CPU | 20-core ARM (10x Cortex-X925 + 10x Cortex-A725), aarch64 | Python wheels must exist for `aarch64`. Many ML packages ship x86-only binaries, so we check every dependency. |
| GPU | NVIDIA GB10 (Blackwell), driver 580.173, CUDA 13.0 | Blackwell supports bf16 natively, which is the training precision we'll use. |
| Memory | 121 GiB **unified** (shared by CPU and GPU) + 15 GiB swap | See below. This is the most important constraint. |
| Disk | 3.7 TB NVMe, 3.3 TB free | Plenty for datasets and checkpoints. |
| OS | Ubuntu 24.04.4, kernel 6.17 (nvidia) | |
| Python | 3.12.3, `uv` installed | We'll use `uv` for fast, reproducible environments. |
| PyTorch | Not installed system-wide. `torch==2.14.0+cu130` resolves for aarch64 from the official PyTorch index. | Native ARM CUDA wheels exist, so we don't need the NGC container. We keep it as a fallback. |
| Docker | Installed, GPU reachable through CDI (`--device nvidia.com/gpu=all`) | The NGC container fallback will work if we need it. |
| Node | v24.18.1 (nvm) | Phase 6 inference server. |
| Ollama | 0.32.13, `qwen3.8:27b` loaded | Teacher/labeler and baseline. |

### Concept: unified memory

On a normal workstation the GPU has its own VRAM (for example 24 GB) and the CPU has system RAM.
On the DGX Spark, CPU and GPU share one 121 GiB pool. That's why `nvidia-smi` reports GPU memory as
"Not Supported": there is no separate GPU memory to report.

What this means for us:
- **The upside:** we can fit larger batches or models than a 24 GB card would allow.
- **The downside:** everything competes for the same pool. The two Ollama servers resident right now
  (`qwen3.8:27b` ≈ 18 GB and `qwen3:30b-a3b` ≈ 32 GB, both set to `keep_alive: Forever` with 131k context)
  take about 50 GB before we start. The system was also already using 9.4 GiB of swap when we checked.
  If a training job runs out of memory on this machine, the OS starts swapping instead of failing
  cleanly the way a discrete GPU would. Training gets much slower rather than crashing.
- **Decision:** don't train while the teacher model is loaded. Phases that use Qwen (labeling, baseline)
  and phases that train will take turns, and the training scripts will log memory headroom.

### Concept: memory bandwidth, not FLOPs, is often the bottleneck

The Spark's LPDDR5x memory has much lower bandwidth than the HBM on datacenter GPUs. Encoder training
at moderate sequence lengths does a lot of computation per byte moved, so it copes with this better
than LLM token generation does. That's one reason a small encoder is a good fit for this machine.
We'll measure real throughput in Phase 3 instead of guessing.

### Name check

"kodiak" is taken on every registry we checked:

| Registry | `kodiak` | `kodiak-s1` | `openkodiak` |
|---|---|---|---|
| PyPI | taken (feature-engineering lib) | free | free |
| npm | taken (abandoned 2022) | free | free |
| GitHub user/org | taken; also `chdsbd/kodiak`, a popular GitHub PR-merge bot (1.1k★) | free | free |
| Hugging Face user | taken (user `kodiak` exists) | free | free |

The name decision is pending: see the Phase 0 questions.

**Update:** the project is "Kodiak by Cortex Agent LLC". Under an org namespace (for example
`github.com/<org>/kodiak`, `huggingface.co/<org>/kodiak-b-small-v0.1`) the name "kodiak" is fine.
Only the flat, global registries (PyPI, npm) need a distinct identifier. Org handle check:
`cortexagent` exists as a GitHub org (created 2025-04, 0 public repos) and as an npm scope, and is free on HF.
`cortex-agent` is taken on GitHub, npm, and HF. `cortexagentllc` is free everywhere.

**Decision (hosting):** the repo will be `github.com/grizzlypeaksoftware/kodiak`, the user's existing
open-source org, which is free. It may move to a Cortex Agent org later. GitHub redirects transferred
repos, so a later move is cheap. `grizzlypeaksoftware` is also free on Hugging Face (as both org and user)
and already exists as an npm scope.

### Phase 0 decisions

| Question | Decision |
|---|---|
| Copyright holder | Cortex Agent LLC |
| Hosting | `github.com/grizzlypeaksoftware/kodiak`, HF `grizzlypeaksoftware/*`, PyPI `kodiak-s1` (`import kodiak_s1`), npm `@grizzlypeaksoftware/kodiak` |
| Task domains | As broad as possible (general-purpose decision model) |
| Language | English only for v0.1 |
| Budget | $0 cash; the Spark is ours for a while. Guerrilla approach: prove it small, scale only if resources appear. |
| Box sharing | The user still browses and runs Claude Code on it, and book-publishing work doesn't call inference. We leave memory headroom and watch temperatures. |
| Ollama | Unloaded `qwen3:30b-a3b`. Used memory fell from 85 GiB to 52 GiB. `qwen3.8:27b` (18 GB) stays for labeling and the baseline. |
| Jev | No spec available; we design from our own contract and make no claims of parity. |

### Concept: why input length is the most expensive dial

A transformer's self-attention compares every token with every other token, so doubling the input
length roughly quadruples the attention cost. Going from 512 to 8,192 tokens is 16x the length and,
for the attention part, up to 256x the work. Most decision inputs (a ticket, a message, a tool result)
are short, so paying long-context cost on every training example wastes most of our compute.

**Plan:** "short first, stretch later".
1. Train most steps at 512 tokens, which covers most examples at the lowest cost.
2. Finish with a short phase at 2,048 tokens (and later up to 8k) so the model learns to use long states.
   This is the same trick ModernBERT and most LLMs use.
3. Use **RoPE** (rotary position embeddings), which encode *relative* positions, so extending
   the context later is extra training rather than a redesign.
4. **Packing:** concatenate short examples into one sequence, masked so they can't see each other,
   so no compute is wasted on padding.

v0.1 target: 2,048-token states. Long-context (8k) is a v0.2 goal, gated on the short model working.

### Concept: guerrilla training

The low-budget playbook (DeepSeek, Qwen, and many academic labs): spend compute where it counts most.
- **Reuse, don't re-learn:** Track B starts from ModernBERT, which already absorbed about 2T tokens of
  pretraining we could never afford. That's why Track B is likely to win at our budget; Track A tells us
  how much that pretraining is worth.
- **Distillation:** a big model (Qwen) labels data offline; the small model learns from those labels.
  We pay for the big model once, not on every request.
- **Small first:** get a small model working end to end, measure, and only then scale.
  A failed small run costs hours; a failed big run costs weeks.
- **Protect the hardware:** training scripts will log GPU temperature and power and pause if the box
  runs hot, and they'll cap memory so the desktop stays usable.

---

## Phase 1: Scaffold, schema, architecture (2026-09-23)

### What we built
- Repo skeleton: Apache-2.0 `LICENSE`, `NOTICE` (Cortex Agent LLC), `pyproject.toml` (`kodiak-s1`, managed with `uv`).
- `src/kodiak_s1/schema.py`: the contract as pydantic models, with 18 tests. JSON Schemas in `schema/` are
  *generated* from it, and a test fails if they go stale, so the Python trainer and the Node server can't drift apart.
- `docs/ARCHITECTURE.md`: the model design, awaiting approval.
- `data/LICENSES.md`: the license ledger, with a permissive-only policy.

### Decision: Null is an answer, not a question type
The brief listed Choice, Score, and Null side by side, but "not answerable" can happen to *any* question. So every
question has `allow_null` (default true), and the model reports `p_null` for each.

### Concept: why a structured attention mask gives us "one pass" for free
A transformer's attention mask decides which tokens can read which. By packing
`state | question 1 + labels | question 2 + labels | …` into one sequence and blocking the state from reading questions,
the state is encoded once, and each question block reads the state as if it were alone. Choosing position ids so every
question (and every label) "starts at the same place" makes answers independent of question order and label order.
That removes a whole class of LLM bias ("prefers option A") by construction instead of by training.

### Concept: proper scoring rules
A scoring rule is *proper* if you get the best expected score only by reporting your true belief. Log loss is one.
If the model says 90% and is right 70% of the time, log loss punishes it. We found that the factored output
(p_null, then which label) trained with BCE + CE is *exactly* the log loss of the full answer distribution, so the model
has one consistent probabilistic objective.

### Concept: why RL for calibration mostly isn't needed here
Papers like RLCR use RL because an LLM's confidence is text it writes, so there's no gradient through it.
Kodiak's confidence *is* its output distribution, so ordinary gradient descent on log loss optimizes it directly.
RL-style training (optional stage S4) is only for the *decision* of when to abstain under a cost.

### Concept: FLOPs ≈ 6 × params × tokens
A forward pass costs about 2 FLOPs per parameter per token, and the backward pass about twice that. That rule of thumb
gives our first compute estimates (b-small decision tuning ≈ 17 h, a-mini pretraining ≈ 2–3 days), assuming
about 30 TFLOP/s sustained. Phase 3 replaces the assumption with a measurement.

### Learned along the way
- ModernBERT's tokenizer has 83 `[unused*]` tokens, so we get our marker tokens without resizing embeddings.
- `kodiak` is taken on PyPI; the package is `kodiak-s1`, imported as `kodiak_s1`.

### Phase 1 review
Approved as proposed, including: Null as an answer on every question; question independence; shared
ModernBERT tokenizer for Track A; "none of the options fit" counted as null (tagged).

---

## Phase 2: Data pipeline and eval set (2026-09-23)

### What we built
- `src/kodiak_s1/data/sources.py`: 20 public datasets, each with a small converter to the `Example` schema.
- `src/kodiak_s1/data/build.py`: download → convert → validate → dedupe → leakage check → gzip shards + manifest.
- `src/kodiak_s1/data/synth.py`: synthetic examples from Qwen, with independent verification.
- `src/kodiak_s1/data/augment.py`: constructed null examples (mismatched claims, correct answer removed).
- `src/kodiak_s1/data/evalset.py`: the frozen eval set, with slices for in-domain, held-out, constructed-null, and synthetic.
- `tools/review.html`: a local page for human review of synthetic eval examples.
- `data/LICENSES.md`: every source verified against its **upstream** license, plus what we excluded and why.

### Concept: license hygiene is part of the data work
Hugging Face license tags are often "unknown" or wrong, so we checked upstream sources. Share-alike (CC-BY-SA) and
non-commercial sets are out, because our weights are Apache-2.0. That cost us some famous datasets (SNLI, BoolQ,
SQuAD v2, ARC). A subtle case: MultiNLI is mostly permissive, but its *fiction* genre includes a CC-BY-SA novel,
so we dropped that genre entirely.

### Concept: data leakage
If the same text appears in both train and test, test accuracy measures memorization, not skill.
The build creates test first and drops any training row whose state already appeared in test or val. Glaive
showed why this matters: the same user message appears under many different system prompts, and splitting on the whole
row leaked hundreds of test states into train. We now split on the user message.

### Concept: "the first N rows" is a biased sample
We cap each dataset (for example 50k training rows), but upstream files are often sorted by label or by sub-source.
Taking the first N rows of CLINC's test split gave *zero* out-of-scope examples, because they're at the end. Every loader
now shuffles with a fixed seed before capping, which keeps it random and reproducible.

### Concept: what "null" means has to be defined carefully
"Not answerable from this state" sounds simple, but several constructions are only *almost* null:
- NLI "neutral" is null **only** in yes/no form. In the 3-way form, "neither" is an offered, correct answer.
  And the wording matters: "Does the text say that X?" invites a "no" instead of "can't tell", so we rephrased it.
- Removing the correct option makes "none of these" correct only when the options are clearly distinct.
  That's fine for intents and multiple choice, but not for emotions ("joy" vs "excitement") or tool routing, where
  "no tool" or "ask for details" may become the right answer.
- Asking an unrelated claim ("Is it true that X?") about a text is unanswerable; asking "What's the sentiment?"
  about an unrelated text is *not*, because any text has a sentiment. Only claim-style questions can be moved between states.
Each kind is tagged, so eval reports them separately.

### Concept: a teacher LLM checking its own work
Synthetic data is only as good as its labels. Two cheap filters:
1. **Evidence check:** every answerable question must quote the state, and the quote must actually be there.
2. **Self-consistency:** a second call answers the same questions *without* seeing the first answers; we keep only agreement.

### Concept: constrained JSON output has its own biases
With JSON-schema-constrained decoding and thinking off, Qwen answered "unanswerable" to nearly everything when the schema
put a boolean `unanswerable` field *first*. It had to decide before it had looked for the evidence. Reordering the output
to "quote the evidence, then answer," with the answer constrained to the valid label ids, fixed it. A related problem:
an unescaped `"` inside a JSON string ends the string early, so one state came back truncated mid-sentence.
Lesson for the Phase 5 baseline: an LLM's output format can move its accuracy, so we'll document the exact prompt and schema.

### Results
- **Public data:** 20 sources → **356k train / 10.9k val / 27k test** examples (16 trained-on sources, 4 held out),
  61 MB compressed. Families: NLI, multiple-choice reasoning, intent, emotion/sentiment, moderation scores, spam,
  prompt safety, response-quality scores, tool routing, occupation, long-document QA.
- **Eval set v0.1:** 2,878 examples / 4,128 questions: 1,578 in-domain, 1,000 held-out (zero-shot), and 300 constructed
  nulls (mismatch + gold removed), plus natural nulls (NLI, out-of-scope, Qasper). The synthetic slice is pending human review.
- **Synthetic pilot, after three fixes** (verifier field order, label-less choice questions, JSON states as strings):
  kept 20 of 24 jobs (up from 5 of 12), with 54 verified questions, 15% of them null. About 87 jobs/hour with Ollama
  serving one request at a time: roughly 1,700 examples/day.
- **Bugs caught by reading actual examples**, not by tests: Glaive "no tool" labels that were really delayed calls,
  NLI phrasing that made "can't tell" read as "no", unsorted-sample bias, and the verifier defaulting to unanswerable.
  Lesson: always read a sample of every dataset after conversion.

### Phase 2 review
- **Human review of the teacher:** the user checked 24 synthetic examples (64 questions) and marked 61 correct, 3 wrong.
  So after the evidence and self-consistency filters, **about 95% of accepted teacher labels are right**. That's a rough
  noise ceiling for synthetic training data, and why headline metrics use human-labeled data. The 3 wrong ones are
  excluded; the 24 reviewed examples (61 questions) form the `eval:synthetic` slice.
- **Ollama parallelism:** set `OLLAMA_NUM_PARALLEL=4` (a systemd drop-in, `ollama.service.d/parallel.conf`).
- **Bulk synthetic run:** 12,500 jobs (target ≈10k accepted examples), detached with `nohup` and resumable.
- **Another JSON pitfall:** the evidence check compared the teacher's pretty-printed quotes against our compact JSON,
  so every JSON-format state failed. Normalizing punctuation on both sides fixed it.
- Gated datasets (WildGuardMix, xLAM) deferred.
