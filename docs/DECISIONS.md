# Decision Log

Every significant decision, with its context and the alternatives we rejected. Newest at the bottom.
Status: **active** (in force), **superseded** (replaced by a later decision), or **revisit** (expected to change).

| # | Date | Decision | Status |
|---|---|---|---|
| D1 | 2026-09-23 | Encoder-only architecture; no LLM backbone | active |
| D2 | 2026-09-23 | Name, namespace, and package id | active |
| D3 | 2026-09-23 | Permissive-license-only data and weights | active |
| D4 | 2026-09-23 | Scope for v0.1: English, broad domains, 2k-token states | active |
| D5 | 2026-09-23 | One packed sequence with a structured attention mask | active |
| D6 | 2026-09-23 | Null is an answer on every question, not a question type | active |
| D7 | 2026-09-23 | Beta distribution for scores | active |
| D8 | 2026-09-23 | Log loss + post-hoc temperature; RL only for abstention policy | active |
| D9 | 2026-09-23 | Shared ModernBERT tokenizer for both tracks | active |
| D10 | 2026-09-23 | Teacher and training take turns on unified memory | active |
| D11 | 2026-09-23 | Headline metrics use human-labeled data only | active |
| D12 | 2026-09-23 | Synthetic data: evidence quote + independent verification | active |
| D13 | 2026-09-23 | MoE writer + 27B verifier for bulk synthetic data | active |
| D14 | 2026-09-23 | Re-implement ModernBERT rather than wrap Hugging Face | active |
| D15 | 2026-09-23 | `torch.compile` on by default | active |
| D16 | 2026-09-23 | Validation per source + early stopping | active |
| D17 | 2026-09-23 | FineWeb-Edu (10BT sample) for Track A pretraining | superseded by D19 |
| D18 | 2026-09-23 | Gated datasets (WildGuardMix, xLAM) deferred | revisit |
| D19 | 2026-09-23 | Track A (from-scratch encoder) deferred; v0.1 is Track B only | revisit |
| D20 | 2026-09-24 | Cloud teachers: permissive open-weight models only (pilot: gpt-oss-120b on DigitalOcean) | active |
| D21 | 2026-09-24 | Checker chosen by bake-off against human review: DeepSeek V3.2 (different family from the gpt-oss writer) | active |
| D22 | 2026-09-24 | Generator v2: targeted, grounded, hard-example-mined synthetic data; scale in measured steps | active |

---

### D1: Encoder-only architecture; no LLM backbone
**Context.** The goal is a fast "System One" decision model. Constrained decoding of a chat model is the thing we're trying to beat.
**Decision.** Use a bidirectional transformer encoder (ModernBERT architecture). Heads produce label logits, a null probability, and a Beta distribution. There's no vocabulary head at inference.
**Rejected.** Autoregressive LLMs with grammar-constrained decoding (slow, and the answer space is only enforced by a sampler); T5-style encoder-decoders (still generate).
**Consequence.** Out-of-space answers are impossible by construction; one forward pass per request.

### D2: Name, namespace, and package id
**Context.** "kodiak" is taken on PyPI, npm, GitHub (including a popular PR-merge bot), and Hugging Face.
**Decision.** Brand "Kodiak by Cortex Agent LLC"; repo `github.com/grizzlypeaksoftware/kodiak` (the owner's existing open-source org); Python package `kodiak-s1` (`import kodiak_s1`); npm `@grizzlypeaksoftware/kodiak`; checkpoints `kodiak-{track}-{size}-v{n}`. Copyright: Cortex Agent LLC.
**Rejected.** `openkodiak` (fine, but "s1" says "System One"); a new Cortex Agent GitHub org (maybe later; GitHub redirects transferred repos).

### D3: Permissive-license-only data and weights
**Context.** Weights will be Apache-2.0. Share-alike and non-commercial training data would muddy that.
**Decision.** Only Apache/MIT/BSD/CC0/CC-BY/ODC-By sources, **verified at the upstream source**, not just the Hugging Face tag. Tracked in [data/LICENSES.md](../data/LICENSES.md).
**Cost.** We lose SNLI, BoolQ, SQuAD v2, ARC, FEVER, and others. MultiNLI's fiction genre is dropped (it contains CC-BY-SA text).

### D4: Scope for v0.1
**Decision.** English only; task domains as broad as possible; states up to 2,048 tokens (train mostly at 512, then extend); 8k is a v0.2 goal.
**Why.** Attention cost grows with the square of length; most decision inputs are short; RoPE allows extending later.

### D5: One packed sequence with a structured attention mask
**Decision.** `[state | question₁ + labels | question₂ + labels | …]` in one sequence. The state sees only itself; a question sees the state, itself, and its labels; a label sees the state, its question, and itself. Every question block (and every label) starts at the same position id.
**Why.** One pass; state encoded once (and cacheable later); answers independent of question order and label order *by construction*.
**Rejected.** One pass per question (N passes); a state-only encoder with a light cross-attention decoder (shallow interaction; kept as a v0.2 option for very large label sets).
**Accepted cost.** Questions can't see each other, so cross-question consistency isn't enforced.

### D6: Null is an answer, not a question type
**Decision.** Every question has `allow_null` (default true) and gets its own `p_null`. "None of the offered options fits" also maps to null (tagged separately).
**Why.** Any question can be unanswerable for a given state.

### D7: Beta distribution for scores
**Decision.** The score head predicts mean and concentration of a Beta on [0,1], mapped to the requested range.
**Why.** It can't go out of bounds; it expresses uncertainty (including "no idea" and "either very low or very high").
**Rejected.** MSE regression (no uncertainty); histogram bins (kept as an ablation).

### D8: Calibration approach
**Decision.** Train with log loss (a strictly proper scoring rule) on the full answer distribution, then post-hoc temperature scaling per head. An optional RL-style stage only tunes the *abstention policy* under a cost of being wrong.
**Why.** RL-for-calibration methods (e.g. RLCR) exist because an LLM's confidence is generated text. Kodiak's confidence *is* its output distribution, so ordinary gradients already optimize it. No claim to replicate "RLCD".

### D9: Shared tokenizer
**Decision.** Both tracks use ModernBERT's tokenizer, with `[unused*]` slots as marker tokens.
**Why.** A tokenizer is a vocabulary, not learned weights. Sharing it isolates the variable we're testing: pretrained vs. from-scratch weights.

### D10: Teacher and training take turns
**Context.** The Spark has 121 GiB of *unified* memory; running out means swapping, not a clean failure.
**Decision.** Pause synthetic generation and unload Ollama models during training runs. The trainer caps itself at 60% of memory and pauses above 85 °C.

### D11: Human-labeled headline metrics
**Decision.** Headline results use human-labeled eval data. Teacher-labeled results are reported separately.
**Evidence.** Human review found ~95% of accepted teacher labels correct; a student can't be fairly graded against its own teacher's noise.

### D12: Synthetic data quality gates
**Decision.** The teacher must quote evidence from the state for every answer (checked mechanically), and a second blind call must agree. Unanswerable questions are generated deliberately.
**Lessons folded in.** Ask for evidence *before* the verdict; split choice and score schemas; real JSON objects for JSON states; normalize punctuation for evidence matching.

### D13: MoE writer + dense verifier
**Context.** `qwen3.8:27b` alone produced ~80 jobs/hour; `OLLAMA_NUM_PARALLEL=4` didn't help (the GPU was saturated).
**Decision.** `qwen3.6:35b-a3b` writes examples; `qwen3.8:27b` verifies every label. ~196 jobs/hour, 92% kept, similar quality. Each example records both models in `meta.teacher`.

### D14: Re-implement ModernBERT
**Decision.** Our own encoder module with ModernBERT's parameter names, so the weights load directly and we control masks and position ids.
**Guard.** A parity test: bit-identical outputs to Hugging Face's ModernBERT on ordinary inputs.

### D15: `torch.compile` on by default
**Evidence.** 17k → 34k tokens/s for b-small. The Spark's GPU is memory-bandwidth-bound on elementwise ops, and compile fuses them.

### D16: Validation per source + early stopping
**Context.** Decision-tuning data is only ~53M tokens/epoch (the design doc assumed 2B), so overfitting, not compute, is the risk.
**Decision.** Evaluate every 250 steps on each source's val split, synthetic val, and a constructed-null group; keep the best checkpoint by macro validation loss; stop after 6 evals without improvement.

### D17: FineWeb-Edu for Track A
**Decision.** Pretrain Track A on the FineWeb-Edu `sample-10BT` subset (ODC-By, not gated, 28.5 GB).
**Why.** High-quality educational web text with a permissive license; big enough for a ~50M-parameter model on one machine.

### D18: Gated datasets deferred
**Decision.** WildGuardMix (safety) and xLAM (tool calling) wait until someone logs in to Hugging Face and accepts their terms. Revisit before v0.1 release.

### D19: Track A deferred; v0.1 is Track B only
**Context.** Track B (ModernBERT backbone) decision-tunes in about an hour, because the expensive reading skills come from
ModernBERT's ~2T-token pretraining. Track A would spend days of the Spark on ~10B tokens (~200× less) to produce a clearly
weaker reader, and its main value was answering "how much is pretraining worth?"
**Decision (project owner).** Skip Track A for v0.1 and put the effort into Track B's data, calibration, and evaluation.
Revisit a **custom encoder** if Kodiak proves valuable (e.g. generates revenue), using the approaches noted in
[LEARNING.md](../LEARNING.md): decision-shaped pretraining, ELECTRA-style objectives, or continued pretraining of an open encoder.
**Given up.** A measured Track A vs. B comparison, and a "trained from nothing" claim. A cheap optional stand-in:
decision-tune a *randomly initialized* ModernBERT for an hour to show the value of pretraining.
**Kept.** The encoder code trains from scratch already (`--init scratch`), and 19 GB of FineWeb-Edu stays in `data/pretrain/`.

### D20: Cloud teachers, permissive open-weight models only
**Context.** A stronger teacher than local Qwen could narrow Kodiak's generalization gap, and cloud inference is cheap
(gpt-oss-120b on DigitalOcean: $0.10 / $0.70 per 1M input/output tokens; ≈ $10–40 per 10k synthetic jobs including reasoning tokens).
**Decision.** Use only open-weight models whose licenses allow training on outputs (e.g. gpt-oss, Apache-2.0; DeepSeek, Qwen
open weights, once verified). No closed commercial models (GPT-5.x, Claude, Qwen-Max, Grok) and no Llama (its license requires
derived models to carry "Llama" in the name). Keep the local 27B verifier, so writer and checker come from different model families.
**Status.** Backend built (`do:` model prefix); pilot waiting on a DigitalOcean billing issue (HTTP 402).

### D21: Choose the checker by measurement, from a different model family
**Context.** Shane asked why not let gpt-oss check its own output: faster, fully cloud. The concern: a model re-checking its own
work repeats its own systematic mistakes.
**Evidence (verifier bake-off, 24 human-reviewed examples: 61 approved and 3 rejected questions).**
gpt-oss-120b kept 92% of approved answers, had 2 broken-JSON failures, took 26 s/example; DeepSeek V3.2 (MIT) kept 97%, 0 failures,
2.3 s/example, half the output tokens; Qwen 3.5 397B returned nothing after ~215 s (thinking budget exhausted). Both usable checkers
rejected 1 of the 3 human-rejected answers; with n = 3 that part is inconclusive. Local Qwen 27B can't be scored on this set:
it was built from Qwen-approved examples.
**Decision.** For cloud generation: gpt-oss-120b writes, DeepSeek V3.2 checks.
**Next.** A larger human-reviewed set would make future checker comparisons (especially "catches bad labels") meaningful.

### D22: Generator v2, and scaling synthetic data in measured steps
**Context.** Shane proposed a 100k-job next batch and an agentic generator. At that scale, v1's single template produces
near-duplicates and pushes the model toward the teacher's style.
**Decision.** Build Generator v2 ([GENERATOR_V2.md](GENERATOR_V2.md)): taxonomy-driven specs, grounding in real FineWeb-Edu text, hard-example
mining with the student model, minimal pairs, a validation-driven planner (never the eval set), near-duplicate filtering, and a
human review queue. Scale 10k → 30k → (maybe) 100k only as the measured scaling curve justifies it.
**Resolved at review.** Publish a rebuild script rather than web excerpts; 30% easy-example quota; ~50 human reviews per
batch; ~$50 for the first 30k-job v2 batch.
