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
| D23 | 2026-09-24 | Iterate on the small backbone; ModernBERT-large later; public naming decided before release | active |
| D24 | 2026-09-24 | Scaling test result: don't buy more v1-style data; improve data *kind* (Generator v2) and the training recipe | active |
| D25 | 2026-09-24 | Training defaults: repeat cap of 3 passes per source, full LR schedule (no early stopping), abstain threshold tuned on validation | active |

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

### D23: Iterate on small; large later
**Context.** ModernBERT-large (~395M) would likely generalize better, at roughly 2–3× the inference cost (to be measured) and slower
CPU serving. Data experiments take ~1 hour on small vs. several hours on large.
**Decision (Shane).** Keep improving with the small backbone for now; defer a large probe run. The likely release plan is two sizes
(fast and quality), decided after Phase 5.
**Open naming question for release.** "b" = Track B. Kodiak's "small" is built on ModernBERT-*base*, which may confuse people;
a candidate is public names `kodiak-base-v0.1` / `kodiak-large-v0.1` (internal run names unchanged).

### D24: Scaling-test result, better data rather than more data
**Evidence (three otherwise identical small models, 0 / 3,300 / 9,411 synthetic examples from the same pool; final checkpoints).**
Overall 0.766 → 0.769 → 0.778; in-domain 0.807 → 0.811 → 0.820; synthetic slice 0.52 → 0.89 → 0.93; calibration error 0.068 → 0.053;
**held-out 0.639 → 0.617 → 0.625 (flat, within noise), and held-out if forced to answer 0.663 → 0.645 → 0.649 (no gain).**
**Decision.** Per the rule agreed before the test, a flat held-out curve means more v1-style data won't close the generalization gap.
Keep the 9.4k synthetic set (it helps overall accuracy, calibration, abstention, and realistic inputs), don't buy a bigger v1 batch, and put effort
into (1) the training recipe (small-dataset overfitting, checkpoint choice, abstain threshold) and (2) Generator v2, especially
"answerable by inference" questions (see the over-abstention finding in LEARNING.md).
**Also confirmed.** For all three models the final checkpoint beat early stopping's "best" overall, so the stopping criterion needs rework.

### D25: New training defaults from the recipe ablation
**Evidence (same 9.4k synthetic data; full eval set; baseline = scaling-test 9,411 model, final checkpoint).**

| Variant | Overall | In-domain | Held-out | Held-out, forced | ECE |
|---|---|---|---|---|---|
| Baseline (early-stopped, threshold 0.5) | 0.778 | 0.820 | 0.625 | 0.649 | 0.053 |
| R0: + threshold tuned on validation (0.70) | 0.776 | 0.818 | 0.636 | 0.649 | 0.055 |
| **R1: repeat cap 3 + full schedule + tuned threshold (0.75)** | 0.780 | 0.808 | **0.664** | **0.691** | **0.049** |
| R2: full schedule, no cap, tuned threshold (0.60) | 0.781 | **0.824** | 0.621 | 0.664 | 0.069 |

**Decision.** Adopt R1's recipe as the default: `max_epochs=3`, `patience=0`, and a threshold tuned at calibration. The cap trades about 1.6
in-domain points (the losses are concentrated on small, memorizable sets: OpenBookQA, Qasper, WinoGrande) for about 4 points on never-seen tasks
(jailbreak +8.8, Banking77 +2.8). Kodiak's value is zero-shot decisions with new label sets, so generalization wins.
**Threshold.** The abstain threshold is a precision/recall dial (users can set it per request); tuning only picks a sensible default.
**Next.** A cap between 3 and 5 might recover some in-domain accuracy; worth one cheap run later.

### D26: Generator v2.0 as built, and two pilot-driven rules
**Context.** v2.0 was built per GENERATOR_V2.md §9 (build log §10). Two 50–60-job pilots (seed 8, $0.15 total) and reading every writer/checker
disagreement drove two changes.
**Decisions.**
1. **Answer basis + an inference-tolerant checker.** Every question is `stated`, `inferred` or `unanswerable`; the checker is told that confident
   inference counts as an answer. This targets the over-abstention measured in D24.
2. **No "unknown"-style options, ever.** Kodiak abstains through its null head. An option like "Not known" is a second, conflicting way to say
   "I don't know", and it made unanswerable questions look answerable to the checker. Prompt rule + mechanical filter.
3. **Reader-style decisions for real web text.** Routing / next action / compliance only on synthetic records; grounded passages get
   classification, extraction, judgment scores, comparison and claim checks.
4. **Hand-written sectors, generated domains.** 16 sectors fixed by us (breadth by construction), 320 domains and 971 document types by the writer.
**Evidence.** Pilot #1 → #2 checker disagreement: stated 8% → 2%, inferred 37% → 20%, unanswerable 44% → 36%, at the same yield (82%) and cost
($1.35 per 1k jobs, about half the §4 estimate because the critic and perturber aren't in v2.0).

### D27: The strategy is "frontier-class open-weights decision model"
**Context.** Shane asked whether Kodiak can provide real-world value and reach "frontier" (2026-09-25). Current numbers: tied with Qwen 27B
in-domain at ~400× the speed with better calibration, but 66% vs. 86% on never-seen tasks.
**Decision.** Aim for frontier *in class*, not frontier in general: the best open model for structured decisions (accuracy, calibration,
abstention, speed), deployed as a System 1 in front of an LLM or a human. A measurable release bar was written *before* the comparison
runs (docs/STRATEGY.md §6): beat every open zero-shot classifier on held-out choice questions; within ~10 points of a 7–8B LLM at ≥100× speed;
ECE ≤ 0.05 and best of all systems; abstain precision ≥ 0.90; fully reproducible and permissively licensed.
**Consequences.** Open zero-shot classifiers (NLI zero-shot v2.0, GLiClass) join the eval as baselines (`eval/zeroshot.py`), with forced
accuracy as a new metric; a 7–8B LLM baseline and a public benchmark suite are still to be chosen.
**Not chosen.** Competing with general LLMs on reasoning or knowledge: the wrong fight for a 150–400M encoder.
**Result (same day).** First baseline comparison (`reports/zeroshot-baselines.md`, STRATEGY.md §4): Kodiak leads overall by a wide
margin and on calibration and latency, but on held-out choice questions GLiClass-instruct-large (~0.4B) edges it out (forced 0.705 vs. 0.691).
Criterion 1 is not met yet. The standard NLI zero-shot v2.0 models trained on banking77 (a Kodiak held-out source), so their clean "-28heldout"
variant is the fair comparison (0.671). The deciding tests are now the Generator v2 A/B and ModernBERT-large.

### D28: Release home on Hugging Face
**Decision (Shane, 2026-09-25).** Models, datasets and the demo Space are published under the Hugging Face **organization
`cortex-agent-llc`** (https://huggingface.co/cortex-agent-llc), owned by Shane's personal account, rather than under a personal account or
a separate company login. The organization owns the artifacts (matching the Cortex Agent LLC copyright), teammates can be added later, and uploads
use a fine-grained write token scoped to the org. Repo ids will look like `cortex-agent-llc/kodiak-<size>-v0.1` (the public size names are
still open, D23). The code stays at github.com/grizzlypeaksoftware/kodiak for now; a Cortex Agent GitHub org is a possible later move.

### D29: What v2.0 bought, and three seeds before any claim
**Evidence.** GENERATOR_V2.md §11 (three seeds each, equal size). v2.0 vs v1: held-out forced accuracy unchanged (0.720 vs 0.721); wrong
refusals on held-out tasks cut by about 60% in every seed; abstain precision 0.84 → 0.92; ECE 0.038 → 0.029; familiar tasks tied.
**Correction.** The single-seed comparison the night before reported +4.9 to +6.8 points on never-seen tasks and a jailbreak jump; the seed
repeats show that was training noise (the jailbreak source swings ±10 points between identical runs). It was reported to Shane as a single run
with a noise caveat and corrected the same night.
**Decisions.**
1. **v2-style data replaces v1 going forward** (it fixes over-abstention, which v1 causes; mixing them brings it back). v1 stays archived.
2. **Any claimed improvement needs ≥ 3 training seeds** (mean ± sd), and the held-out set gets bigger before we steer by it.
3. **Next public preview:** a v2.0 model, with the seed chosen on *validation* data, never on the eval set.
4. **Release criterion 1 (best in class):** v1 and v2 both average ~0.72 held-out forced vs 0.705 for GLiClass-instruct, inside the noise:
   call it **roughly tied**, not met.
5. **Next levers:** ModernBERT-large for raw generalization; score-question data (anchored scales, urgency/risk minimal pairs) for the
   judgment-score weakness.
**Follow-up (2026-09-26).** Published as `cortex-agent-llc/kodiak-small-v2-preview`: run `b-small-s1-B-v2` (seed 0, lowest final validation
loss 0.1576 vs 0.1579 / 0.1708). The demo Space now loads it. A spot check found the "crushed box → refund" fix is input-sensitive (right with an
order id, wrong without), so the model card says so.

### D30: Eval set v0.2, a held-out section big enough to steer by
**Context.** v0.1 held out 4 tasks (1,000 questions); jailbreak alone swings ±10 points between identical runs (D29).
**Decision (Shane approved 2026-09-26).** `data/eval/kodiak-eval-v0.2.jsonl` = v0.1 unchanged + 400 examples from each of 8 new never-trained-on
sources: ContractNLI, ETHICS commonsense, financial tweets (topic, sentiment), arXiv field, CaseHOLD, Webis clickbait (a score task), poem
sentiment. Held-out grows to 12 tasks / 4,200 examples (tags `eval:heldout_v01` and `eval:heldout_v02` keep old numbers comparable). Licenses
re-verified upstream while building (data/LICENSES.md). PubMedQA was excluded (abstract licensing unclear).
**Rules.** Frozen (the builder refuses to overwrite); never trained or tuned on; every model is re-scored on it (`scripts/rescore_v02.sh`).
**Build notes.** arXiv's legacy query API returned HTTP 406 and OAI-PMH throttled after one response, so the arXiv source uses the CC0 metadata
snapshot mirror instead; two newer fields (economics, EESS) are distractors only.

### D31: Stage 3 (synthetic judgment scores) paused after five pilots
**Evidence.** GENERATOR_V2.md §12: two independent, blind LLM raters disagree on 58–82% of anchored ratings (vs. near-agreement on choice
questions); a writer asked to aim at a target band also grades toward that target. Total cost $0.54 of the ~$30 approved.
**Decision (Shane, 2026-09-26).** Spend nothing more on Stage 3 until the ModernBERT-large results on eval v0.2's score tasks are in. If ratings
are still weak, pilot the "bands instead of numbers" variant (~$0.15) before any batch.
**Why it matters.** It explains the weakness itself: rating data (human or LLM) is noisy, so a model can't learn a crisp scale from it. The fix
has to reduce label noise (bands, more raters), not just add examples.

### D32: Zork showed that calibration doesn't survive distribution shift
**Evidence.** Shane's Zork benchmark (github.com/grizzlypeaksoftware/kodiak-plays-zork; article "Jev vs. Kodiak", 2026-09-26): same harness and seeds,
Zork I, 5 × 100 moves. Zero invalid moves for every model (~20,000 moves). Jev's own moves earned 45 points vs. ~0–2 for Kodiak r1/v2; v2 made more
moves itself (31–53%) but earned almost nothing, looped confidently on Detective (178 → 10 points vs. r1), and answered "in danger" 60% of the time
(Jev 4%). A no-model exploration baseline beat Kodiak on Zork. Question wording changed Kodiak's points per move 35×.
**Reading.** v2's calibration is the best we've measured *on the eval set* (ECE 0.029), yet on game states (far from any training data) its
confidence doesn't track correctness. Calibration is only guaranteed near the calibration distribution. For a System 1 / System 2 cascade, an
over-confident System 1 is the dangerous failure: the fallback never gets the turn.
**Decisions.**
1. Add a sequential / out-of-distribution slice to evaluation (confidence vs. correctness on Zork-style states from **practice games**); Zork I
   itself stays a held-out benchmark, never training data.
2. Training data gets (a) out-of-distribution inputs labeled "can't tell", so Kodiak learns to be unsure when lost, (b) sequential next-action
   decisions in context (agent logs, practice games with verified licenses), and (c) more descriptive question phrasings.
3. Re-run the frozen Zork harness on every candidate model (including ModernBERT-large) as a standing long-horizon benchmark.
4. Product: "the second question guards the first" (e.g., act only if "in danger?" is no) becomes a documented usage pattern for cascades.

### D33: ModernBERT-large clears the best-in-class bar on eval v0.2
**Evidence (3 training seeds each; eval v0.2; reports/v02-backbone.md, reports/v02-vs-baselines.md).** Never-seen tasks, choice questions,
forced accuracy: **large 0.609 ± 0.008**, small 0.553 ± 0.007; open classifiers: NLI DeBERTa-v3-large *-28heldout* (clean) 0.579, NLI
ModernBERT-large 0.569, NLI DeBERTa-v3-large 0.556, GLiClass-instruct-large 0.550, GLiClass-large 0.528. New tasks only (v0.2): large 0.570,
small 0.505, best rival 0.552. Large also improves familiar tasks (0.817 → 0.855), Bias in Bios (+14), banking (+4), ContractNLI (0.84 vs. rivals
0.20–0.63), financial topics and arXiv fields. Rivals win on poem sentiment and financial sentiment.
**What didn't move.** Ratings: clickbait score error 0.28–0.32 (poor for both sizes). Calibration on never-seen tasks: held-out ECE ~0.13 for
both sizes; better than every rival (0.21–0.60) but far from the 0.05 target, consistent with D32 (calibration degrades off-distribution).
**Release criteria (STRATEGY §6).** (1) best in class on never-seen tasks: **met by large** (+3.0 over the best clean rival, >3 sd), small roughly
tied; (3) calibration: best of all systems, but ECE ≤ 0.05 **not met** off-distribution; (2) 7–8B LLM comparison and (4) abstain precision on v0.2
still to confirm (large 0.84 ± 0.08 is noisy; small 0.91).
**Decisions.** ModernBERT-large becomes the quality tier; small stays the fast tier (8 ms vs. 16 ms GPU). Next levers, in order: calibration
off-distribution (D32: unfamiliar inputs labeled "can't tell", a sequential eval slice, Zork re-run on large), then ratings (bands, D31).
v1 vs v2 on v0.2 confirms D29: v2 abstain precision 0.69 → 0.91, never-seen forced +0.8 (small, within noise).

### D34: A three-run ensemble fixes much of the calibration gap
**Evidence (eval v0.2, existing predictions averaged, no retraining; abstain threshold 0.7 untuned).** Large, one run (mean of 3) → ensemble of the
3 runs: never-seen forced 0.609 → **0.623**, never-seen accuracy 0.571 → 0.590, never-seen ECE ~0.128 → **0.099**, overall ECE ~0.087 → **0.059**,
abstain precision 0.84 (range 0.76–0.92 across runs) → **0.93**, familiar 0.855 → 0.869. Small: forced 0.553 → 0.571, never-seen ECE ~0.136 → 0.112.
**Reading.** Independently trained runs are overconfident in different places; averaging cancels much of it. This is the first lever that improves
calibration on unfamiliar tasks (D32) rather than only in-distribution.
**Decisions.** (1) Offer ensembles as an option ("accuracy mode") where 3× compute is acceptable (large: ~48 ms GPU, ~750 ms CPU). (2) Next
experiment: **distill** the 3-run ensemble into one model (train on the ensemble's averaged probabilities) to keep most of the gain at single-model
cost; free on the Spark. (3) Tune the ensemble's abstain threshold on validation data before any release.
**Note.** The published large preview (seed 1, chosen by validation loss) happens to have the lowest abstain precision of the three on eval v0.2
(0.845); selection stays validation-based so the eval set remains untouched.

### D35: Self-hosting via ONNX + Node, fp32 only (Phase 6)
**Built.** `kodiak_s1.onnx_export` exports a model folder to one ONNX file (small 610 MB, large 1.6 GB) and checks it against PyTorch
(relative difference ~1e-5 on both). `server/` is a Node.js twin of the Python packer and decision rule, an Express API (`POST /v1/decide`)
and a Dockerfile. JS vs Python parity on 44 fixture requests (40 from the eval set): identical tokens, probabilities within 1e-4. CPU latency
p50 in Node, 8 threads: small ~30 ms, large ~80 ms; Docker image 554 MB, ~1 GB RAM with small.
**Design change.** The attention mask is built inside the graph from token roles, not by the client (ARCHITECTURE §12 originally said client),
so any client only tokenizes and packs.
**Rejected: int8.** Dynamic int8 (per-tensor and per-channel) cut size in half and latency ~2×, but flipped 11 of 41 fixture choice answers and
moved p(null) by up to 0.58. A calibrated model can't ship with that; revisit only with quantization-aware checks on the eval set.
**Published.** `model.onnx` added to both preview repos (Shane approved 2026-09-26); `from_pretrained` skips it, so Python users don't download it. The hosted Cortex Agent API (STRATEGY §5b) can run on this server.

### D36: Distilling the ensemble into small didn't help (negative result)
**Evidence (3 student seeds vs. the 3 small v2 runs; eval v0.2; reports/v02-distill.md).** Student = small, public + v2.0 data, loss = 0.5 × hard
labels + 0.5 × the averaged calibrated distribution of the three large v2 runs (D34). Accuracy unchanged within noise (never-seen forced 0.553 →
0.558 ± 0.013; familiar 0.817 → 0.816). **Calibration worse:** never-seen ECE 0.136 → 0.148, familiar 0.018 → 0.030, overall 0.093 → 0.105;
abstain precision 0.91 → 0.88. Bias in Bios +4 and Banking +2 (within 1–2 sd).
**Likely reason.** The soft targets were computed on the teachers' own *training* data, where the teachers are near-certain, so they carried little
"dark knowledge" beyond the hard labels; the benefit of an ensemble shows up on unfamiliar inputs, which the student never saw through the teachers'
eyes. The student's own temperature calibration then had less to work with.
**Decisions.** (1) Don't publish a distilled small. (2) The ensemble (D34) stays the calibration lever ("accuracy mode"). (3) If distillation is
retried, distill on inputs the teachers did *not* train on (e.g. unlabeled real text or held-back synthetic states), with the teachers' uncertainty
as the target; cost ≈ one overnight run. Not scheduled.

