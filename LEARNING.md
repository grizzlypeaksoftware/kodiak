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

### Phase 2 addendum: a faster teacher
Benchmarked `qwen3.6:35b-a3b` (a mixture-of-experts model, about 3B parameters active per token) as the *generator*,
with `qwen3.8:27b` still verifying every label: **196 vs 80 jobs/hour**, 92% vs 86% kept, similar null rate and
quality. We switched, which cut the 10k run from about 6 days to about 2.5. Lesson: `OLLAMA_NUM_PARALLEL=4` barely helped
the dense 27B model (the GPU was already at 96%), but a model that does less work per token did.

---

## Phase 3: A tiny model, end to end (2026-09-23)

### What we built
- `src/kodiak_s1/packing.py`: request → one token sequence with roles, question/label indices, and
  order-independent position ids; several examples packed per row.
- `src/kodiak_s1/model/encoder.py`: a ModernBERT-compatible encoder with Kodiak's structured attention mask,
  written once as a rule (`allowed(...)`) and compiled two ways: FlexAttention block masks for training and a
  dense mask for export and tests.
- `src/kodiak_s1/model/heads.py`: choice-matching, null, and Beta score heads, plus the §6 loss.
- `src/kodiak_s1/train.py`: resumable, logged, temperature-aware trainer.
- `tests/test_model.py`: the architecture's promises as tests.

### Results
| Check | Result |
|---|---|
| Question independence, order invariance, label-order invariance, state independent of questions, packed examples isolated | all pass (to 1e-5) |
| FlexAttention on GB10 vs dense SDPA | matches (1e-4); ~7× faster on packed inputs; backward works |
| Our encoder + ModernBERT weights vs Hugging Face ModernBERT | **bit-identical** (max diff 0.0 over 300 tokens) |
| Overfit 32 examples, tiny from scratch (15M params) | 100% choice + null accuracy by step 50; score MAE 0.004 by step 400 |
| Overfit 32 examples, ModernBERT-base backbone | 100% choice + null accuracy by step 25 |
| Resume | continues from the last checkpoint, with identical data order |
| SIGTERM | finishes the step, checkpoints, exits cleanly |
| bf16 matmul peak (idle GPU) | ≈ 94 TFLOP/s (26 while Ollama was busy) |
| b-small training throughput | 17k tok/s eager → **34k tok/s with `torch.compile`**, ~11 GB |

### Concept: the overfit test
Before spending days training, prove the model *can* learn: give it a handful of examples and train until it memorizes them.
If it can't memorize 32 examples, something is wired wrong (masks, labels, loss sign, optimizer). The test says nothing
about generalization; it's purely a plumbing check. Both tracks passed within 25–50 steps.

### Concept: why the loss went negative
The score head's loss is the negative log of a probability *density*, not a probability. A density can be larger than 1
(a sharp Beta around 0.8 might have density 20 there), so its negative log can be below zero. Choice and null losses
are log *probabilities* and can't go below zero; they went to about 0.00001.

### Concept: parity tests
"We load ModernBERT's weights" is only true if our re-implementation computes exactly what the original does.
One test runs both on the same input and compares every output number: 0.0 difference. Without that test, a subtle
mismatch (a missing norm, a different window boundary) would quietly make Track B worse and we'd blame the data.

### Concept: memory bandwidth on the Spark
The Spark's GPU can do about 94 TFLOP/s of matrix math, but its memory is much slower than a datacenter GPU's.
Operations that do little math per byte (GELU, LayerNorm, rotary embeddings, residual adds) are limited by memory speed.
`torch.compile` fuses chains of them into single kernels, so the data is read once instead of many times: 2× faster.
That's also why power draw was only about 50 W before compiling: the GPU was mostly waiting on memory.

### Decisions
- `torch.compile` on by default for training; gradient checkpointing off (b-small fits in about 11 GB at 8 × 2,048 tokens).
- The trainer caps itself at 60% of unified memory and pauses above 85 °C (resumes at 75 °C).
- Measured Phase 4 cost: b-small S1 over ~2B tokens ≈ **16 hours** at 34k tok/s.

### Correction: the decision-tuning data is small
The architecture doc assumed "2B tokens" for decision tuning. Measured: the whole public training set is **≈ 53M tokens
per epoch** (most examples are 40–130 tokens; HelpSteer2 and UltraFeedback are the long ones), so one epoch of b-small takes
**≈ 25 minutes**, not 16 hours. Two consequences for Phase 4:
1. Track B is cheap: we can afford several runs and ablations instead of one big bet.
2. The risk moves from compute to **overfitting**. With temperature sampling (∝ size^0.3), small sources like
   OpenBookQA or SMS spam get repeated many times per epoch. We'll watch validation loss per source and stop early.
Track A's MLM pretraining (billions of tokens of plain text) is still the expensive part.

### Concept: is ModernBERT an LLM? (a question from the project owner, Phase 4)
Not in the sense this project rules out. "LLM" usually means an **autoregressive** model like Qwen or GPT that *writes*
text one token at a time, each token seeing only the ones before it. ModernBERT is an **encoder**: it *reads* a whole text
at once (bidirectionally) and turns it into vectors that represent meaning. It has no way to generate text. It learned by
filling in blanked-out words (masked language modeling) over about 2T tokens, and at 150M parameters it's about 180× smaller
than the 27B Qwen teacher.

What Track B borrows from ModernBERT is **reading comprehension**, nothing else. Everything that makes Kodiak a
decision model is Kodiak's own design: the packed sequence and structured mask, the choice/null/score heads, the log-loss
objective, and the data. An analogy: Track B hires a fluent reader and teaches them the job; Track A teaches reading from the
alphabet and then the same job. The Track A vs. B comparison measures what that head start is worth.
ModernBERT is Apache-2.0, so building on it doesn't limit Kodiak's openness.

### Caught: WinoGrande validation is probably inflated
During the first Track B run, WinoGrande validation accuracy reached 84%, suspiciously high for a 150M encoder.
Likely cause: WinoGrande is built from **twin sentences** (near-identical, opposite answers). Our val split is carved from
the upstream train split by hashing each sentence, so one twin can land in train and the other in val, and the model can
partly memorize pair-specific cues. Our *test* split is WinoGrande's official dev set, which doesn't have this problem;
Phase 5 reports that number. Fix for the next data build: split WinoGrande by twin group (e.g. hash the sentence with the
option words removed) rather than by sentence.

### Decision: Track A deferred (D19)
After seeing Track B decision-tune in about an hour, the project owner decided to skip Track A for v0.1. The asymmetry is the lesson:
**pretraining is where almost all the cost is; fine-tuning is cheap.** Track A would spend days of the Spark to learn to
read from ~10B tokens (ModernBERT read ~2T), only to produce a weaker reader. The effort goes into Track B's data,
calibration, and evaluation instead. A custom encoder (decision-shaped pretraining, ELECTRA-style objectives, or continued
pretraining of an open encoder) is the plan *if* Kodiak proves valuable.

### Result: first Track B run (b-small-s1-v0)
ModernBERT-base, public data + 114 synthetic examples (generation was paused), 8 × 2,048-token batches, lr 5e-5 / heads 5e-4.
Early-stopped at step 3,250 (about 35 minutes); "best" checkpoint at step 1,750 by macro validation loss.

| Step | Macro val loss | Synthetic val loss | Constructed nulls (abstain acc.) | MNLI | CommonsenseQA |
|---|---|---|---|---|---|
| 250 | 0.504 | 0.94 | 55% | 62% | 39% |
| 1,750 | **0.265** | ~1.9 | 86% | 78% | 56% |
| 2,750 | 0.408 | 3.76 | 93% | 84% | 63% |
| 3,250 | 0.429 | 3.77 | 93% | 83% | 60% |

**Lesson: early stopping stopped for the wrong reason.** Real tasks kept improving after step 1,750; what rose was the
synthetic group's loss. Its val set had 7 examples, and its 114 training examples were oversampled (weight ∝ size^0.3) until the model memorized them.
An unweighted macro average let that tiny group outvote everything else. Fix: groups with fewer than 50 val questions are
logged but excluded from the early-stopping metric. The oversampling resolves itself once the 10k synthetic run finishes.
The run's real value was testing the Phase 4 machinery before the run that matters.

---

## Phase 5 (preliminary): evaluation harness (2026-09-23)

### What we built
- `src/kodiak_s1/infer.py`: requests → answers: grouped softmax, null probability, the decision rule, Beta summaries.
- `src/kodiak_s1/eval/metrics.py`: accuracy (with "unanswerable" as an outcome), macro-F1, ECE, Brier, NLL, AURC,
  abstain precision/recall, score MAE, 90%-interval coverage, latency, sliced by eval slice, source, and null type.
- `src/kodiak_s1/eval/run.py`: `calibrate` (temperature fitting on *validation* data), `predict`, `baseline`
  (Ollama LLM with JSON-schema-constrained output), and `report`. Kodiak and the LLM write the same prediction format, so one
  scorer judges both.

### Concept: calibration, measured
**ECE** (expected calibration error) sorts answers by confidence into bins and asks: when the model says 80%, is it right
80% of the time? Temperature scaling divides the logits by one fitted number T per head. T > 1 means the model was
overconfident. Our first model had T ≈ 1.5 for choices; calibration cut overall ECE from 0.093 to 0.062 (in-domain
0.075 → 0.036) without changing a single answer, since dividing all logits by T doesn't change which is largest.

### Finding: early stopping picked the wrong checkpoint
On the frozen eval set, the step-3,250 model beat the saved "best" (step 1,750): accuracy 0.772 vs. 0.746,
constructed-null accuracy 0.907 vs. 0.787. That confirms the tiny-synthetic-group problem from Phase 4.

### Finding: two metric bugs caught before they misled us
1. **Interval coverage looked like 50% for a 90% interval.** Many gold scores sit exactly at 0 or 1 (for example, toxicity 0.0),
   and a Beta interval can never contain an endpoint. Training squeezes targets slightly inward; the metric now does the same.
   Real in-domain coverage: 0.89–0.94, well calibrated. Held-out hate speech: 0.61, overconfident out of domain.
2. **An abstaining LLM had no score value**, which crashed MAE. MAE is now computed over given values, and "score given"
   is reported next to it, so abstaining on hard items can't quietly improve MAE.

### Finding: the baseline's prompt can handicap it
The first Qwen prompt said "using only information in the state". Qwen then answered "unanswerable" to 96% of score
questions (quality ratings, toxicity) and to general-knowledge multiple choice: 110 of 280 answers were unwarranted
abstentions. That's a flaw in *our* baseline, not in Qwen. The v2 prompt says judgments and general knowledge are allowed,
and reserves "unanswerable" for missing specific facts. Both runs are kept on record. **A comparison is only honest if the
baseline gets its best shot.**

### Preliminary result: Kodiak v0 vs. Qwen 27B (200 eval examples, 280 questions)
Kodiak = the first Track B model (step 3,250, calibrated; trained with only 114 synthetic examples).
Qwen = `qwen3.8:27b` via Ollama, JSON-schema-constrained, v3 prompt (judgments allowed, numeric score schema), verbalized confidence.

| | Kodiak v0 (150M) | Qwen 27B |
|---|---|---|
| Accuracy, overall | 0.732 | 0.765 |
| Accuracy, in-domain | 0.755 | 0.765 |
| Accuracy, held-out datasets (zero-shot) | 0.649 | **0.860** |
| Constructed nulls (n = 19) | **0.895** | 0.368 |
| Abstain precision / recall | **0.90 / 0.79** | 0.68 / 0.39 |
| Calibration error (ECE) | **0.095** | 0.192 |
| Score MAE (unit scale) | **0.168** | 0.213 |
| Score 90%-interval coverage | 0.86 | n/a (point estimates only) |
| Median latency per request | **8 ms** | 3,431 ms |

Reading it honestly:
- **Speed is the clearest win:** ~400× faster per request on the same machine.
- **Calibration and abstention are real strengths.** Kodiak's confidence is about twice as trustworthy, and its "unanswerable" is
  learned, not prompt-sensitive: Qwen's null accuracy swung from 0.68 (v1 prompt) to 0.37 (v2/v3) with wording alone.
- **Generalization to new tasks is the weakness:** 0.65 vs. 0.86 on held-out datasets. A 27B generalist knows far more
  than a 150M encoder trained on 16 datasets. That's the gap more diverse data (the synthetic run) should narrow.
- **Caveats:** 200 examples (±~5 points on accuracy); an early model; Qwen's confidence is verbalized.

### Demo of b-small-s1-v0 (the README example request)
- intent → "refund or billing fix" (64%) ✅; card brand → unanswerable (68%) ✅, the headline behavior; urgency →
  unanswerable (61%), and even when forced, 0.10 "not urgent" ❌ (rent is due Friday).
- **Why urgency failed:** every score question in the training data is a moderation or quality rating (toxicity, hate, helpfulness),
  mostly near 0, and none is about urgency. The model learned "scores are usually low" instead of reading a new scale. The same
  generalization gap shows on held-out tasks. The varied score questions in the 10k synthetic set target it; urgency is now a
  spot check for the next model.
- **Bug found by the demo:** `infer.answer` passed raw requests to the packer, so the documented label shorthand
  (`"labels": ["a", "b"]`) crashed. Requests are now validated and normalized through the schema first, with a test.
  Third time in this project a demo or sample read caught what unit tests didn't.

### Cloud teacher setup, and a lesson about secrets (2026-09-24)
Added a DigitalOcean serverless-inference backend to the synthetic generator (`--model do:openai-gpt-oss-120b`).
Getting authenticated took some debugging: the first key returned 401 even though its settings were right. The
cause was simple: **the key in `.bashrc` was 68 characters, and the regenerated one is 71.** The first copy was clipped.
We found it by checking the key's *shape* (length, character classes, whether loading changed it) without ever printing
it. The new key authenticates; the account then returned 402 Payment Required, a billing issue on DigitalOcean's side.
Jobs that fail this way are marked `retry` rather than done, so nothing is lost.

### Cloud pilots: reading the output again beat guessing (2026-09-24)
| | Pilot #1 | Pilot #2 | Local Qwen writer |
|---|---|---|---|
| Jobs kept | 26% | **88%** | 92% |
| Questions per example | 2.2 | 2.7 | 2.9 |
| Unanswerable share | 45% (survivorship bias) | 20% | 16% |
| Cost per 1,000 jobs | $0.74 | $0.73 | free |

Pilot #1 failed quietly: 94 questions were dropped by the evidence check. Printing gpt-oss's raw output showed it
**paraphrases** evidence for JSON states ("Commenter: Jane Doe" for `"author":"Jane Doe"`). Its *answers* were fine; the
hallucination guard was too literal for this writer. Worse, the drop was lopsided: unanswerable questions need no evidence, so
they survived and skewed the kept set to 45% nulls, with zero score questions. Fixes (they help every writer):
1. The prompt asks for character-for-character quotes (for JSON: an exact fragment).
2. `evidence_supported()`: an exact normalized match, **or** at least 80% of the evidence's content words present in the state. That
   tolerates rewording but still rejects invented evidence (there are tests for both).
3. A question with invalid options (e.g. duplicate texts) is dropped on its own instead of failing the whole job.
4. Blank items in list-type states are removed.
Cost came in far under the estimate ($0.73 vs. the $1–4 per 1,000 I expected): at low reasoning effort, gpt-oss barely
"thinks" on this task.

### Concept: why a model shouldn't check its own work
A verifier is useful to the extent that its mistakes are *independent* of the writer's. If the same model writes and checks,
a wrong label that came from a gap in its knowledge will usually be re-confirmed by the same gap. So the check filters out
random slips but not systematic errors, which are the ones that hurt the student most. A checker from a different model family
(different data, different training) is more likely to catch them. Rather than assume this, the verifier bake-off measures it
against human review.

### Result: verifier bake-off (2026-09-24)
| Checker | Keeps human-approved (61) | Rejects human-rejected (3) | Failures | s/example |
|---|---|---|---|---|
| gpt-oss-120b | 92% | 1/3 | 2 (runaway JSON) | 26 |
| **DeepSeek V3.2** | **97%** | 1/3 | 0 | **2.3** |
| Qwen 3.5 397B | – | – | returned no content after ~215 s | – |
| Qwen 27B (local) | 100%* | 0/3* | – | – |

\*By construction: the review set was built from examples Qwen 27B had approved, so it can't be scored fairly here. That's
**selection bias**, and a textbook case: an evaluation set filtered by a model can't evaluate that model.
Also learned: "thinking" models can burn their whole token budget reasoning and return an empty answer; the backend now
raises a clear error instead of crashing. Process lesson: I piped the bake-off through `tail`, which hid per-model progress
for 30 minutes; long jobs should stream their progress.

### Result: the data-scaling test (2026-09-24)
Three otherwise identical small models (same seed and recipe), trained on 0 / 3,300 / 9,411 synthetic examples drawn from the same
pool; each calibrated on validation and scored on the full eval set (4,189 questions). Final checkpoints:

| Synthetic examples | Overall | In-domain | Held-out | Held-out, forced to answer | Synthetic slice | ECE | Abstain P/R |
|---|---|---|---|---|---|---|---|
| 0 | 0.766 | 0.807 | 0.639 | 0.663 | 0.52 | 0.068 | 0.86 / 0.88 |
| 3,300 | 0.769 | 0.811 | 0.617 | 0.645 | 0.89 | 0.067 | 0.86 / 0.89 |
| 9,411 | **0.778** | **0.820** | 0.625 | 0.649 | **0.93** | **0.053** | **0.89 / 0.90** |

**What it says:**
- Synthetic data **helps**: overall +1.2 points (about 2 standard errors on 4,189 questions), in-domain +1.3, realistic LLM-style inputs
  +41 points (on only 61 questions), and better calibration and abstention.
- It does **not** transfer to held-out tasks: 0.64 → 0.62 → 0.63, and forced-answer accuracy is flat too. The held-out slice has about 750
  choice questions (±~1.7 points), so this is "no gain," not a clear loss.
- **Over-abstention, caught mid-test:** the 3,300 "best" checkpoint abstained on 11% of held-out questions (Banking77 19%, Bias in Bios 15%),
  which all have answers. Forced to answer, it was *more* accurate than the no-synthetic model. The synthetic data's unanswerable
  questions ("the fact isn't in the text") taught the model to treat **"not stated literally"** as **"unanswerable,"** when the right line is
  "inferable" vs. "truly missing." Generator v2 should teach the distinction explicitly (answerable-by-inference questions, minimal pairs).
- **Early stopping keeps picking the wrong checkpoint:** for all three sizes, the final checkpoint beat "best" overall. The stopping metric
  is dominated by small datasets that overfit (Qasper, OpenBookQA, CommonsenseQA), so the recipe needs fixing: cap repeats of small
  datasets, and choose checkpoints by a better criterion.
**Decision (D24):** keep the 9.4k synthetic set; don't buy more v1-style data; fix the recipe and build Generator v2.

### Result: recipe ablation (2026-09-24, late)
Same 9.4k synthetic data. Full table in DECISIONS.md D25. Key rows (overall / in-domain / **held-out** / held-out forced):
- Baseline (early-stopped, threshold 0.5): 0.778 / 0.820 / 0.625 / 0.649
- **Repeat cap 3 + full schedule + tuned threshold: 0.780 / 0.808 / 0.664 / 0.691**
- Full schedule, no cap: 0.781 / 0.824 / 0.621 / 0.664

**Concept: memorization vs. generalization, in one experiment.** Without the cap, a few small datasets were seen 20–30 times
per run. The model got better at *those* datasets (in-domain +1.6), and worse at everything it had never seen. With the cap, those
examples are seen at most three times, and the freed training time goes to large, varied sources. The model memorizes less and
learns more transferable skill: never-seen tasks +3.9 points (jailbreak detection +8.8, Banking77 +2.8), and even with forced answers
(no abstaining) +4.2. Per-dataset in-domain losses were concentrated on small, memorizable sets (OpenBookQA −6, Qasper −5, WinoGrande −4,
each ±~4.5 points of noise with ~100 questions).

**Concept: early stopping vs. a full schedule.** The learning rate follows a curve: warm up, then decay to 10%. The last stretch at a low
learning rate settles the weights, and early stopping never let runs reach it. With the cap in place, the final checkpoint doesn't
overfit badly, so the full schedule simply wins. New defaults: `max_epochs=3`, `patience=0` (validation still logged; `best.pt` still saved).

**Concept: the abstain threshold is a dial.** Tuning it on validation moved it to 0.70–0.75: fewer wrong refusals and higher
abstain precision (0.94), but a few more missed unanswerables. There's no free lunch; it's a precision/recall choice users can make per request.

## Generator v2.0 built (2026-09-25)

**What changed from v1, in one line each.** Every job starts from a *spec* (setting, decision type, scale, difficulty, how many inferred and
unanswerable questions, and of which kind); the settings come from a 971-document-type taxonomy instead of 60 hand-typed strings; ~45% of states
are real web passages (FineWeb-Edu) instead of teacher-written text; near-duplicates are detected with MinHash; a budget cap stops the run cleanly.

**Concept: MinHash, or how to find "almost the same" text cheaply.** Break each text into overlapping 5-word phrases ("shingles"). Two texts'
similarity is the share of shingles they have in common (Jaccard similarity). Comparing every pair is too slow at 20k+ examples, so each text is
summarized by 64 numbers: for each of 64 random hash functions, the *smallest* hash of any of its shingles. The chance that two texts share that
minimum equals their Jaccard similarity, so the fraction of matching numbers estimates it. Banding (16 groups of 4) finds likely matches without
comparing everything to everything. Our threshold: 0.8.

**Concept: the checker's instructions define what "correct" means.** v1's checker was told "answer using ONLY information in the state; otherwise
UNANSWERABLE." That sounds rigorous, but it quietly defined *inference* as unanswerable, and every inference question would have been filtered out.
Changing one sentence ("confident inference counts") changed which data survives. A filter is also a specification.

**Pilot lesson: read the disagreements, not just the rates.** Pilot #1 had 44% disagreement on unanswerable questions. The number alone said
"the checker is too strict." Reading them said something else: the *writer* was adding options like "Not known", so the checker (reasonably)
picked them. The fix was a writer rule plus a regex filter, not a checker change. A second pattern: routing questions about web articles were
nonsense, so real passages now get reader-style questions. Disagreement on inferred questions went 37% → 20% and on stated ones 8% → 2%.

**Concept: two ways to say "I don't know" is one too many.** Kodiak abstains through a dedicated null head with its own calibrated probability.
If training data also had "Unknown" as a regular option, the model would have to learn two competing mechanisms for the same thing, and the
calibrated abstain signal (which users threshold on) would leak into an ordinary label.

**Human review result: 92.7%, and why agreement isn't correctness.** Shane approved 153 of 165 v2 labels. All 33 unanswerable questions were right,
but ~9% of answerable ones were not, and the typical failure was a question with *two* defensible answers. Two models agreeing doesn't catch that:
both pick the same plausible option. A "critic" that is shown the answer and asked to attack it is a different task, but each critic model caught
only 3 of the 12 bad labels; two different critics together caught 5. Lesson: it's cheaper to *prevent* ambiguity in the writer prompt (one
defensible answer, one clear referent, no "which is NOT…" questions) than to detect it afterwards. Also: 12 errors in 165 means the true rate
could plausibly be anywhere from about 4% to 12%, so one review batch can't separate 92.7% from 95% with confidence.

## The real competition: open zero-shot classifiers (2026-09-25)

**Why this comparison.** Beating a 27B LLM on speed says nothing about whether Kodiak is the best *of its kind*. The fair rivals are the open
models built for zero-shot classification: NLI-based classifiers (MoritzLaurer zeroshot-v2.0) and GLiClass. Numbers are in STRATEGY.md §4.

**Concept: forced accuracy.** These models can't abstain, so plain accuracy punishes them for guessing badly about *when* to abstain. Forced
accuracy asks only: on answerable questions, is the top-ranked label right? That isolates ranking skill.

**Concept: contamination.** One baseline looked strong on banking77, one of our held-out tasks, and its model card revealed it was trained
on banking77. Its clean variant (trained without those tasks) lost 12 points there. A "zero-shot" number is only zero-shot if the model never saw
the task: always check the training data of a baseline, not just of your own model.

**Result.** Kodiak wins overall by a wide margin, and on calibration and speed, but on never-seen *classification* tasks (occupation from a bio,
banking intent) a GLiClass model with 2.9× the parameters is 1–2 points ahead. That's the honest gap to "best in class," and it lines up with the known
weakness: inferring a category that isn't stated word for word.

## Release kit, and a calibration bug caught before shipping (2026-09-25)

`kodiak_s1.hub.Kodiak` loads a model folder or Hub repo and answers requests; `python -m kodiak_s1.hub export|push` packages and
uploads. Two findings:
- **Calibration lived in the wrong place.** The three temperatures are model buffers that default to 1.0; training checkpoints never set
  them, because the eval harness applied `calibration.json` itself. The first private upload was therefore uncalibrated (intent confidence
  0.95 instead of 0.84; the default 0.5 abstain threshold instead of 0.75). Eval numbers were unaffected. Now export bakes the temperatures into
  the weights and the loader assigns them, so it's correct either way. Lesson: test the artifact users get, not just the pipeline you evaluate.
- **CPU works:** ~80 ms per request on the Spark's 8 ARM cores (fp32), ~8 ms on its GPU; answers agree within bf16 rounding.
- **Two honest demo misses** kept as before/after tests for Generator v2: "charged twice, nobody answers" gets urgency 1.3/10, and
  "box arrived crushed, lamp broken" gets intent "delivery status" (0.54) instead of "refund or replacement".

## Lesson: one training run is an anecdote (2026-09-26)

Last night a single training run said the new data added 5–7 points on never-seen tasks. Three training seeds each (same data, different random
order and initialization) said: **no difference** in raw accuracy on never-seen tasks (0.720 vs 0.721), because one run of the *old* data had
simply been unlucky. One held-out task, jailbreak detection, swings from 65% to 86% between identical runs.

**Concept: training noise.** Fine-tuning is a random process: the order examples arrive in, random augmentations and the new layers' starting
weights all change the result. With a small held-out set (1,000 questions from four tasks), that noise is several points. The standard fix is
to run each setup several times and compare means with their spread; a difference smaller than the spread isn't a finding.

**What was real, because it held in every seed:** v2 cut wrong refusals by about 60%, made "can't tell" more trustworthy (abstain precision
0.84 → 0.92) and improved calibration. That's exactly what v2 was designed to fix. It just didn't make the model better at *ranking* answers on
tasks it has never seen. That's a different problem, probably about model size, and the next experiments target it.
