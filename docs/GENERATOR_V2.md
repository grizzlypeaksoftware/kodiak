# Generator v2: targeted, grounded synthetic data (design proposal)

> **Status: APPROVED 2026-09-24** (answers to §7 below). Not built yet; build starts after the data scaling test.
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
