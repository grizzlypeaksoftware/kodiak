# Noise table: how much each metric moves between training seeds

Baseline: Kodiak-v0.2-1B, three training seeds (E18 seed 1 + E19 seeds 0 and 2), measured 2026-10-04. SD = standard deviation across seeds.
**Rule 1 (D65):** a guard line is the baseline mean minus **2 SD** (plus 2 SD for lower-is-better), judged on the new experiment's 3-seed
mean; a single run can only reject when it is more than **3 SD** past the baseline mean. Lines narrower than the noise make kills a coin flip.

| Metric | v0.2 mean | SD | Guard line (3-seed mean) | Single run rejects only past |
|---|---|---|---|---|
| Never-seen forced (eval v0.2) — primary | 0.689 | 0.008 | ≥ 0.673 | 0.665 |
| Familiar tasks | 0.877 | 0.003 | ≥ 0.871 | 0.868 |
| Never-seen calibration error (ECE) | 0.085 | 0.009 | ≤ 0.103 | 0.112 |
| Abstain precision | 0.880 | 0.013 | ≥ 0.854 | 0.841 |
| Ranking (aurc_gap_closed, never-seen) | 0.556 | 0.007 | ≥ 0.542 | 0.535 |
| Flip rate (wording eval; 1 − consistency; lower is better) | 0.322 | 0.002 | ≤ 0.326 | 0.328 |
| Wording consistency (wording eval) | 0.678 | 0.002 | ≥ 0.675 | 0.673 |
| Wording-trap eval v0.1, trap items (100-item test) | 0.867 | 0.031 | ≥ 0.806 | 0.775 |
| E17 skills score | 0.983 | 0.004 | ≥ 0.975 | 0.971 |
| Real-anchor score (MT-Bench + RAGBench + SemEval stance, 352 items) | 0.211 | 0.063 | ≥ 0.085 | 0.022 |

**Rule 2:** tests used as gates need ≥ ~100 items. The 8-sentence label-overlap probe (v0.2 seeds 5 / 6 / 6 of 8, SD 0.6 = 7.5 points)
is reported but never gates; the 100-item wording-trap eval (`data/eval/kodiak-trap-eval-v0.1.jsonl`, 50 trap + 50 control) replaces it.
Re-measure this table whenever the baseline model changes.

## Contrastive eval v0.1 (rule 7, D67): v0.3 baseline, pair accuracy, 3 seeds

| Kind | Pairs | v0.3 mean ± SD | Guard (mean − 2 SD) |
|---|---|---|---|
| Policy violation | 30 | 0.567 ± 0.034 | ≥ 0.499 |
| Refund eligibility | 50 | 0.220 ± 0.080 | ≥ 0.060 |
| Step safety | 50 | 0.053 ± 0.023 | ≥ 0.007 |
| Sarcasm | 7 | too few pairs | report only |

Below ~100 items per kind (rule 2), so these are guards against collapse, not gates. Source: reports/contrastive-v0.1.md.


## v0.3 baseline (Kodiak-v0.3-1B = E22 runs, 3 seeds): guard lines for E23 onward

| Measure | Seeds 0 / 1 / 2 | Mean | SD | Guard (2 SD) | Single-run reject (3 SD) |
|---|---|---|---|---|---|
| Never-seen forced | 0.694 / 0.675 / 0.691 | 0.687 | 0.010 | ≥ 0.666 | 0.656 |
| Familiar | 0.884 / 0.873 / 0.879 | 0.879 | 0.006 | ≥ 0.868 | 0.862 |
| Abstain precision | 0.943 / 0.961 / 0.888 | 0.931 | 0.038 | ≥ 0.855 | 0.817 |
| Real-anchor score | 0.333 / 0.353 / 0.387 | 0.358 | 0.027 | ≥ 0.303 | 0.276 |
| Wording-trap eval (100) | 0.920 / 0.900 / 0.880 | 0.900 | 0.020 | ≥ 0.860 | 0.840 |
| Ranking (aurc gap closed) | 0.532 / 0.583 / 0.519 | 0.545 | 0.034 | ≥ 0.477 | 0.443 |
| Flip rate (wording eval) | 0.302 / 0.347 / 0.331 | 0.327 | 0.023 | ≤ 0.372 | 0.395 |

Source: reports/e22-xl-skills3.md, reports/preds_wording/e22-*. v0.3's flip rate varies far more across seeds (SD 0.023) than v0.2's (0.002).
