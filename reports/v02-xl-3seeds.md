# Seed comparison: large v2 (400M) vs xl v2 (Ettin-1B)

| Measure | large v2 (400M) | xl v2 (Ettin-1B) | Difference (xl v2 (Ettin-1B) − large v2 (400M)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.571 ± 0.003 (n=3) | 0.619 ± 0.010 (n=3) | +0.048 |
| Never-seen tasks, forced | 0.609 ± 0.008 (n=3) | 0.659 ± 0.013 (n=3) | +0.050 |
| New never-seen tasks (v0.2), forced | 0.570 ± 0.006 (n=3) | 0.608 ± 0.016 (n=3) | +0.038 |
| Never-seen score error (MAE) | 0.257 ± 0.001 (n=3) | 0.272 ± 0.003 (n=3) | +0.015 |
| Overall accuracy | 0.674 ± 0.002 (n=3) | 0.713 ± 0.006 (n=3) | +0.039 |
| Familiar tasks | 0.855 ± 0.001 (n=3) | 0.881 ± 0.002 (n=3) | +0.026 |
| Calibration error (ECE) | 0.087 ± 0.014 (n=3) | 0.076 ± 0.006 (n=3) | -0.011 |
| Never-seen calibration error (ECE) | 0.128 ± 0.018 (n=3) | 0.113 ± 0.010 (n=3) | -0.015 |
| Abstain precision | 0.842 ± 0.082 (n=3) | 0.868 ± 0.007 (n=3) | +0.026 |
| Constructed unanswerables | 0.948 ± 0.022 (n=3) | 0.961 ± 0.008 (n=3) | +0.013 |
| Banking77 (forced) | 0.791 ± 0.002 (n=3) | 0.813 ± 0.019 (n=3) | +0.023 |
| Bias in Bios (forced) | 0.772 ± 0.008 (n=3) | 0.805 ± 0.012 (n=3) | +0.033 |
| Jailbreak (forced) | 0.669 ± 0.089 (n=3) | 0.893 ± 0.035 (n=3) | +0.224 |
| Poem sentiment, has 'mixed' (forced) | 0.443 ± 0.059 (n=3) | 0.540 ± 0.058 (n=3) | +0.098 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.755 ± 0.023 (n=3) | 0.699 ± 0.014 (n=3) | -0.056 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
