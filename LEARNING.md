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
