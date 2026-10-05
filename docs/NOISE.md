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
| Wording consistency (wording eval) | 0.678 | 0.002 | ≥ 0.675 | 0.673 |
| Wording-trap eval v0.1, trap items (100-item test) | 0.867 | 0.031 | ≥ 0.806 | 0.775 |
| E17 skills score | 0.983 | 0.004 | ≥ 0.975 | 0.971 |
| Real-anchor score (MT-Bench + RAGBench + SemEval stance, 352 items) | 0.211 | 0.063 | ≥ 0.085 | 0.022 |

**Rule 2:** tests used as gates need ≥ ~100 items. The 8-sentence label-overlap probe (v0.2 seeds 5 / 6 / 6 of 8, SD 0.6 = 7.5 points)
is reported but never gates; the 100-item wording-trap eval (`data/eval/kodiak-trap-eval-v0.1.jsonl`, 50 trap + 50 control) replaces it.
Re-measure this table whenever the baseline model changes.
