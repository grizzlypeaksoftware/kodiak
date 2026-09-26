# Generator v2: targeted, grounded synthetic data (design proposal)

> **Status: APPROVED 2026-09-24** (answers to §7 below). **v2.0 BUILT 2026-09-25** (`src/kodiak_s1/data/gen2/`; build log in §10).
> v2.0 batch and A/B done (§11): v2.0 fixes over-refusal and improves calibration; no gain in never-seen ranking.
> Generator v1 is `src/kodiak_s1/data/synth.py`.

## 1. Why a v2

Generator v1 works (≈88% of jobs kept, ~95% label precision under human review), but it has four limits that matter
more as batches grow:

| Limit in v1 | Consequence |
|---|---|
| One prompt template, 60 hand-listed document types × 3 formats | Near-duplicates at scale; 100k jobs would mostly repeat 10k |
| The teacher invents the *documents* too | Kodiak learns "LLM-written text" style, not real-world text |
| Blind to what Kodiak gets wrong | Most of the budget goes to examples Kodiak already handles |
| Disagreements are silently discarded | The hardest, most informative cases never reach a human |

The measured weakness this targets: **held-out tasks, 65% (Kodiak v0) vs. 86% (Qwen 27B)**, plus specific misses like the
urgency score in the demo.

**Success criterion.** At an *equal number of synthetic examples*, a model trained on v2 data beats one trained on v1 data on
the held-out slice and the weak slices, without losing in-domain accuracy or calibration, and v2 label precision stays at
95% or better under human review.

## 2. Pipeline

```
 eval/validation report ─► PLANNER ─► spec weights ─┐
 coverage map ──────────────────────────────────────┤
                                                    ▼
 taxonomy ──► SPEC SAMPLER ──► spec ──► SOURCE: real document (FineWeb-Edu) or synthetic state
                                                    │
                                                    ▼
                                    WRITER (gpt-oss): questions + answers + evidence
                                                    │
                          mechanical checks (schema, evidence, labels) ──► drop
                                                    │
                           CHECKER (DeepSeek, blind) ──► disagree ──► REVIEW QUEUE (human)
                                                    │
                          CRITIC (sampled): ambiguous? ──► yes ──► REVIEW QUEUE
                                                    │
                          PERTURBER (optional): minimal pair (flip / make unanswerable) ──► re-check
                                                    │
                          STUDENT SCREEN: current Kodiak scores each candidate (8 ms each)
                                                    │
                          SELECTION: hard examples + a quota of easy ones, per spec cell
                                                    │
                          NEAR-DUPLICATE FILTER ──► synthetic train shard (+ coverage map update)
```

"Agentic" here means **bounded LLM steps where judgment helps** (planning, taxonomy, critique, perturbation) inside an
otherwise deterministic, resumable, logged pipeline, like v1. No open-ended agent loops; every step's effect is measured.

## 3. Components

### 3.1 Specs and the taxonomy
Every job starts from a **spec**, a small JSON object that says what to make:

```json
{"domain": "property management", "doc_type": "maintenance request", "source": "synthetic",
 "format": "list", "decision": "judgment_score", "scale": "urgency 0-10", "n_questions": 3,
 "difficulty": "hard", "null_kind": "missing_fact", "pair": "none"}
```

The **taxonomy** that specs are sampled from is generated once by an LLM, skimmed by a human, and versioned
(`data/synthetic/taxonomy_v2.json`): ~300 domains, each with its own document types, and cross-cutting axes:
- **decision types:** classification, extraction-as-choice, judgment score, routing and tool choice, comparison, compliance/yes-no, next action
- **answer scales:** 0–1, 1–5, 0–10, 0–100, with varied anchor wording (urgency, confidence, severity, risk, sentiment, quality…)
- **difficulty:** easy, medium, hard (multi-hop, distractors, long states)
- **null kinds:** missing fact, out of scope, no option fits, underspecified, temporal (asks about something not yet known)

A **coverage map** counts examples per cell, so the sampler can fill gaps instead of repeating popular cells.

### 3.2 Grounding in real documents
For prose document types, the source is a **real passage** from FineWeb-Edu (100–450 words; the 19 GB sample already on disk,
ODC-By), and the writer only writes questions about it. Structured formats (JSON records, logs, chat transcripts) stay synthetic,
since FineWeb is prose. Target mix: about 50% grounded.
*Why:* it breaks the "teacher-written text" monoculture, so Kodiak learns to read the kind of text it will meet in the wild.

### 3.3 Writer, checks, checker
The same as v1, which is proven: gpt-oss-120b writes, mechanical checks run, DeepSeek V3.2 verifies blind (DECISIONS.md D21).
Two changes:
1. The writer receives the spec (difficulty, scale wording, null kind), not a random domain string.
2. **Disagreements aren't discarded.** They go to a review queue (`tools/review.html`), prioritized by how often that spec
   cell produces disagreements. Human time goes where the pipeline is least sure.

### 3.4 Critic (sampled)
On a sample of kept examples (and all "hard" ones, see 3.6), a critic call asks one thing: *does this question have more than
one defensible answer given the state?* Flagged examples go to the review queue. This targets the failure the human review
found: questions like "overall assessment" where the state supports two options.

### 3.5 Minimal pairs (perturber)
For a fraction of kept examples, generate a twin:
- **Flip pair:** edit the state minimally so the correct answer becomes a specified *different* option; the checker must agree.
- **Null pair:** remove the evidence sentence(s) **mechanically** (we know the quote), so the question becomes unanswerable;
  the checker must agree that it is.

Pairs teach exactly which facts matter, which is Kodiak's abstention skill in particular. **Both halves always go to the same
split** (the WinoGrande lesson, LEARNING.md).

### 3.6 Student screen and selection (hard-example mining)
The current Kodiak model scores every candidate. It's cheap (≈8 ms per request), so each question can be classified:
- **hard:** Kodiak picks a different answer, or is confident about the wrong thing, or unsure (probability < 0.6)
- **easy:** Kodiak is already right and confident

**Selection:** keep all hard examples (after the critic pass) plus a quota of easy ones (default 30%, per spec cell), so the data
doesn't drift entirely to edge cases and Kodiak doesn't forget what it knows.

**Known pitfall:** "Kodiak is wrong" is also what a *teacher* error looks like, so hard-example mining concentrates label noise.
Mitigations: checker agreement is still required, every hard example goes through the critic, and the human review sample
(§5) is drawn with extra weight on hard examples, so we measure precision where the risk is.

### 3.7 Planner
Once per batch (not per job, to keep cost and complexity down), the planner:
1. reads the latest **validation** report: per-source and per-slice metrics, plus a sample of Kodiak's errors;
2. turns failure clusters into spec weights, e.g. "urgency and priority scales on customer messages: 3× weight";
3. splits the batch: **40% targeted** (weak slices), **40% coverage** (fill thin taxonomy cells), **20% exploration** (random specs).

**Guard against teaching to the test:** the planner never sees the frozen eval set, only validation data and its own
generated dev set. Otherwise we'd be tuning data to the exam (Goodhart's law).

### 3.8 Near-duplicate filter
MinHash over word shingles of `state + questions`; drop anything with Jaccard similarity > 0.8 to an existing example, in
this batch or earlier. Cheap, deterministic, and it makes the "100k are mostly 10k" problem measurable.

## 4. Cost and throughput (estimates)

| Step | Calls per job | Notes |
|---|---|---|
| Writer (gpt-oss) | 1 | ~$0.73 / 1k jobs (measured) |
| Checker (DeepSeek) | 1 | ~400 in / 100 out tokens per call (measured); price TBD |
| Critic | ~0.4 | only on samples and hard examples |
| Perturber | ~0.3 (plus a re-check) | only on a fraction of kept examples |
| Student screen | local | Kodiak on the Spark, ≈8 ms per request |
| Planner, taxonomy | negligible | once per batch / once per version |

Roughly **$1.5–2 per 1,000 jobs**. Selection keeps about 60% (all hard examples plus a quota of easy ones), so **~$3 per 1,000 kept
examples**, and a 30k-job batch costs about $50. A budget cap (`--max-usd`) stops the run cleanly when reached.

## 5. Evaluation plan

1. **A/B at equal size:** train `public + 10k v1` vs. `public + 10k v2` (same recipe, same seed); compare the held-out slice, the
   weak slices the planner targeted, null handling, calibration, and in-domain accuracy (it must not drop).
2. **Ablations, cheap because training is free:** v2 without grounding, without hard-example mining, without pairs. This tells us which
   parts earn their keep.
3. **Human review:** 50 v2 examples in `tools/review.html`, weighted toward hard ones; target ≥ 95% label precision.
4. **Scaling curve:** 10k → 30k v2 examples, to decide whether a 100k batch is worth it (the question that started this).

## 6. Build order

| Step | Contents | Measured by |
|---|---|---|
| v2.0 | Specs + taxonomy + coverage map, grounding, near-duplicate filter, review queue, budget cap | A/B vs. v1 at 10k |
| v2.1 | Student screen + selection (hard-example mining) + critic | Ablation: with vs. without mining |
| v2.2 | Minimal pairs + planner | Weak-slice and null metrics |

Each step ships only if it beats the previous one on the evaluation plan.

## 7. Open questions, resolved at review (2026-09-24)

All four recommendations were accepted: publish a rebuild script instead of web excerpts; start the easy quota at 30%;
~50 human reviews per batch; ~$50 budget for the first 30k-job v2 batch.


1. **Web text in the released dataset.** Grounded examples contain FineWeb-Edu excerpts (ODC-By, drawn from Common Crawl). Fine for
   training, but should the *published* synthetic dataset include them, or release only the synthetic-state part plus a script
   to rebuild the grounded part? (Recommendation: the latter.)
2. **Easy-example quota:** 30% is a guess; the v2.1 ablation will tune it.
3. **Human review time:** how many examples per batch are you willing to review (the queue can be capped)? About 50 takes ~20 minutes.
4. **Budget:** is ~$50 for the first 30k-job v2 batch acceptable?

## 8. Not doing (for now)

- Training the generator itself (RL on the teacher). The teachers stay off-the-shelf open models.
- Fully autonomous loops that generate, train and evaluate without a human checkpoint.
- Closed-model teachers (DECISIONS.md D20).

## 9. Implementation plan (written 2026-09-25, before building)

State of play when this plan was written:
- **Best model:** `runs/b-small-s1-R1-cap3/checkpoints/step_0006000.pt` + `calibration-final-thr.json` (abstain threshold 0.75).
  Full eval: overall 0.780, in-domain 0.808, held-out 0.664 (forced 0.691), ECE 0.049. It's the student for v2.1 screening.
- **v1 synthetic data:** `data/synthetic/synth_v1.jsonl` (3,290 local Qwen) + `data/synthetic/synth_v1_cloud.jsonl` (6,412 cloud), 9,702 examples.
- **Training defaults (D25):** `--max-epochs 3 --patience 0` (now the defaults in `TrainConfig`), 6,000 steps, lr 5e-5 / heads 5e-4.
- **Cloud teacher:** writer `do:openai-gpt-oss-120b`, checker `do:deepseek-3.2` (DECISIONS D20/D21). The key is `DO_INFERENCE_KEY`, loaded with
  `eval "$(grep -E '^\s*export DO_INFERENCE_KEY=' ~/.bashrc | tail -1)" && export DO_INFERENCE_KEY` (never print it).
- **Known weakness to target:** over-abstention on questions answerable **by inference** (Banking77, Bias in Bios), plus the held-out gap
  to Qwen (66% vs. 86%) and the "urgency score" demo miss.

### v2.0: build first (A/B against v1 at equal size)
New package `src/kodiak_s1/data/gen2/`:

| Module | Job |
|---|---|
| `taxonomy.py` | Generate `data/gen2/taxonomy_v2.json` once with the writer model: ~12 sectors → ~300 domains → 3–6 document types each, plus the cross-cutting axes in §3.1. Deterministic loader; the human skims before first use. **Committed** (small). |
| `specs.py` | `Spec` dataclass and sampler (seeded per job id). Decision types, scale wordings (urgency, severity, confidence, risk, quality, sentiment…), difficulty, null kind. Coverage map `data/gen2/coverage.json`. v2.0 weights: 60% coverage, 40% exploration (the planner comes in v2.2). |
| `passages.py` | FineWeb-Edu passage sampler from `data/pretrain/fineweb-edu/sample/10BT/*.parquet` (19 GB, 9 files on disk): pick 100–450-word windows at paragraph boundaries, deterministic by job id. ~50% of prose specs are grounded. |
| `prompts.py` | Writer prompt built from the spec (and the passage when grounded). **Must include:** ≥1 question answerable only **by inference** (labeled answerable; evidence = the supporting quote), unanswerable questions that are *truly missing* the fact, varied scale wording with anchors, and exact-quote evidence rules (v1 lessons: evidence before verdict, separate choice/score schemas, real JSON objects, no double quotes in prose). |
| `pipeline.py` | `run_job(job_id)`: spec → (passage) → writer → `synth.build_questions` (reuse) → checker via `synth.verify_*` (reuse) → keep agreements. Disagreements go to `data/gen2/review_queue.jsonl` (compatible with `tools/review.html`). Records carry the spec and tags: `gen2`, `grounded`, `inference`, `null:<kind>`, `scale:<wording>`. |
| `dedupe.py` | MinHash over word 5-shingles of state + questions (a pure-Python implementation, no new dependency); drop Jaccard > 0.8 against the v1 files and earlier gen2 output. |
| `__main__.py` | CLI: `python -m kodiak_s1.data.gen2 --n N --seed 6 --workers 16 --out data/synthetic/gen2_v20.jsonl --max-usd 15`. Resumable like v1; the **budget cap** comes from the token counts × `docs/progress.json` prices. |

**Seeds:** 6 = gen2 training data, 7 = gen2 eval candidates (human review), 8 = pilots. Never train on seed 7.
**Tests (`tests/test_gen2.py`):** taxonomy load/shape, deterministic spec sampling, passage windowing/filters, MinHash near-duplicate detection,
a pipeline run with a mocked teacher, and the budget-cap stop.
**Licensing:** add FineWeb-Edu (ODC-By; used for grounding) to `data/LICENSES.md`. Release policy (§7): publish a rebuild script, not the excerpts.
**Dashboard:** register every gen2 run in `docs/progress.json` → `synthetic.runs`, and add milestones.

**Execution order:**
1. Build the modules + tests; generate and skim the taxonomy (show Shane a sample).
2. Pilot 50 jobs (seed 8): check yield (target ≥ 80%), inference-question share, grounded share, and cost per 1k; read 10 examples by hand.
3. Eval candidates: ~70 jobs (seed 7) → Shane reviews ~50 in `tools/review.html` → label precision (target ≥ 95%).
4. Full v2.0 batch: ~11k jobs (seed 6) → ~9.4k kept (equal to v1), about $10–15.
5. **A/B test** (new defaults, same seed/steps): (a) public + v1 9.4k [already = R1], (b) public + v2 9.4k, (c) public + v1 + v2.
   Compare held-out accuracy, held-out wrong-abstain rate, Banking77/Bias in Bios, the urgency demo, in-domain, ECE, and the synthetic slice.
6. Record in STORY, DECISIONS (D26), LEARNING, progress.json, the NotebookLM export. Commit after Shane approves.

### v2.1: after v2.0 is measured
Student screen with the best model (≈8 ms/request): classify hard vs. easy (wrong, or top probability < 0.6); keep all hard + a 30% easy quota
per spec cell; critic call on all hard examples + a 10% sample of the rest ("more than one defensible answer?"); the review queue is weighted to hard examples.
Ablate: v2.0 vs. v2.1 at equal size.

### v2.2: then
Minimal pairs (flip via the writer + re-check; null via mechanical removal of the evidence sentence + re-check; pairs share a `pair_id` and a split);
the planner (reads **validation** per-source metrics + an error sample from the latest run, never the eval set; 40/40/20 targeted/coverage/explore).

### Other small queued items
- A cap experiment: `--max-epochs 5` vs. 3 (free, ~1 hour) to see whether in-domain accuracy recovers without losing held-out.
- RUNBOOK §5 still shows the old training flags; update to the D25 defaults.
- Uncommitted work since `f6deff9`: scaling test, recipe test, new defaults, docs. Commit when Shane approves.

## 10. Build log: v2.0 (2026-09-25)

**Built.** `src/kodiak_s1/data/gen2/`: `taxonomy.py`, `specs.py`, `passages.py`, `prompts.py`, `pipeline.py`, `dedupe.py`, `__main__.py`
(subcommands `taxonomy`, `show`, `run`, `stats`, `queue`, `coverage`); `tests/test_gen2.py` (11 tests, mocked teacher, no network).
Differences from the plan:
- The taxonomy's **sectors are hand-written** (16), and the model fills in domains and document types. Result: **16 sectors, 320 domains,
  971 document types** (v1: 60 settings). Cost about $0.01.
- **Coverage mode** walks a seed-shuffled list of all 971 document types (each used once before any repeats), and weights the other axes by
  `1 / (0.1 + count / average)` from a coverage snapshot frozen per output file (so resumes stay deterministic).
- **Every question declares a basis** (`stated` / `inferred` / `unanswerable`) and the **checker prompt now accepts sound inference**. v1's checker
  ("using ONLY information in the state") would have vetoed exactly the inference questions v2 exists to add.
- The review queue is a `queue` subcommand (disagreements sampled by their cell's disagreement rate), not written live.
- DeepSeek V3.2 price (DO pricing page): $0.50 in / $1.60 out per 1M tokens, now in `docs/progress.json`.

**Pilot #1 (50 jobs, seed 8, $0.07).** Yield 82%, grounded 44% of kept examples, inferred 22% of kept questions, cost $1.34 per 1k jobs.
But the checker disputed 37% of inferred and 44% of unanswerable questions. Reading every disagreement showed two writer faults:
1. **"Unknown" options:** for unanswerable questions the writer added options like "Not known" / "Result is not yet known"; the checker then
   picked them. That duplicates the null answer (two ways to abstain), so now the prompt forbids them and a regex filter drops any choice
   question with an unknown-style option (`pipeline.has_unknown_option`).
2. **Contrived questions on real text:** routing / next-action questions about web articles ("which processing queue should handle a
   correction about Nakhichevan?"). Grounded jobs now use reader-style decisions (classification, extraction, judgment score, comparison,
   and a new `claim_check`); synthetic jobs keep the full list.
Also seen: hard multi-step arithmetic errors by the writer (caught by the checker, as designed).

**Pilot #2 (60 jobs, seed 8, jobs 50–109, $0.08).** Yield 82%, grounded 47%, inferred 24%, null 16% of kept questions. Checker disagreement:
stated 8% → **2%**, inferred 37% → **20%**, unanswerable 44% → **36%**. The remaining null disagreements are mostly the *writer* being wrong
(calling a question unanswerable when the text answers it); the checker removes them. Spot-checks of kept inferred and null questions looked right.

**Eval candidates (70 jobs, seed 7, $0.10):** `data/synthetic/eval_gen2_v20.jsonl`: 55 kept examples, 165 questions (93 stated, 39 inferred,
33 unanswerable). **Next: Shane reviews them in `tools/review.html`** (target ≥ 95% label precision), then step 4 (the ~11k-job batch).

**Human review of the eval candidates (Shane, 2026-09-25): 153 / 165 = 92.7% label precision, below the 95% gate.**
By basis: unanswerable 33/33 (100%), inferred 35/39 (90%), stated 85/93 (91%). Grounded 69/72 (96%), synthetic 84/93 (90%). Errors were spread
evenly across easy/medium/hard. Most rejections had **more than one defensible answer** ("which is NOT listed" with two unlisted options, "which term
is defined" with two defined, "the next stop" in a thread with two stops, overheated vs. mechanical failure); others were a stale "current status"
(both models answered from an old log line) and a score whose end labels didn't match its dimension (from my "rate the closest judgment" rule).
Saved: `data/eval/synthetic_reviewed_gen2_v0.1.jsonl`.

**Critic bake-off** (`gen2/critic_bakeoff.py`, report `reports/critic-bakeoff.json`): shown the proposed answer and asked to attack it, each
critic alone caught only 3 of the 12 rejections (DeepSeek 1 false flag of 153, gpt-oss 2). They catch *different* ones: flagging when either
objects catches 5/12 with 3 false flags → estimated precision ≈ 95.5% (measured on the same set used to pick it, so optimistic).
**Response (v2.0c):** (1) prompt rules aimed at the observed failures: one defensible answer (check every option), no negative/set-membership
questions, one unambiguous referent, latest information wins, confident inferences only, scale anchors on the same dimension; (2) an optional
`--critics do:deepseek-3.2,do:openai-gpt-oss-120b` step (the v2.1 critic pulled forward), about +$0.9 per 1k jobs.

## 11. Result: v2.0 vs v1 at equal size (2026-09-25/26)

Batch: `data/synthetic/gen2_v20.jsonl`, 11,800 jobs → **9,428 kept** (80%), **$25.38** (writer + checker + 2 critics; $2.69 per 1k kept).
A/B (`scripts/ab_test.sh`, `scripts/seed_repeats.sh`): public data + 9,137 synthetic training examples from v1 or v2.0, D25 recipe, 6,000 steps,
**three training seeds each** (same data subset; seeds change order, augmentation and head init). Full table: `reports/generator-ab-seeds.md`.

| Measure (mean ± sd over 3 seeds) | v1 | v2.0 | v2 − v1 | Consistent across seeds? |
|---|---|---|---|---|
| Held-out, forced accuracy | 0.721 ± 0.043 | 0.720 ± 0.012 | 0.000 | no difference |
| Held-out, accuracy | 0.678 ± 0.039 | 0.703 ± 0.019 | +0.025 | mostly |
| Held-out wrong-refusal gap (forced − acc) | 0.043 (0.037–0.047) | 0.017 (0.009–0.024) | −0.026 | **yes, every v2 seed < every v1 seed** |
| Abstain precision | 0.844 ± 0.005 | 0.917 ± 0.018 | +0.073 | **yes** |
| Calibration error (ECE) | 0.038 ± 0.004 | 0.029 ± 0.003 | −0.008 | yes |
| Familiar tasks | 0.814 ± 0.001 | 0.817 ± 0.004 | +0.003 | tie |
| Constructed unanswerables | 0.942 ± 0.011 | 0.927 ± 0.023 | −0.016 | slight v1 edge |

**Reading.** v2.0 did what it was designed to do (stop refusing inference questions; make "can't tell" trustworthy; calibrate better) and did
**not** improve ranking on never-seen tasks. The single-seed result the night before (+4.9 forced, jailbreak +15) was mostly training noise:
the jailbreak source alone swings 0.65–0.86 between v1 seeds with identical data. Combining v1 + v2 (one seed) brought the wrong refusals back
(gap 0.059), so v1's "fact missing = unanswerable" style is the likely cause of over-abstention. Judgment scores (urgency, risk) remain broken.
**Next:** the held-out eval is too noisy to steer by (grow it, and use ≥ 3 seeds for decisions); raw generalization now points at the backbone
(ModernBERT-large) and at score-question data (v2.1/v2.2).
