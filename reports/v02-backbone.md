# Seed comparison: small v2 vs large v2

| Measure | small v2 | large v2 | Difference (large v2 − small v2) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.521 ± 0.008 (n=3) | 0.571 ± 0.003 (n=3) | +0.050 |
| Never-seen tasks, forced | 0.553 ± 0.007 (n=3) | 0.609 ± 0.008 (n=3) | +0.056 |
| New never-seen tasks (v0.2), forced | 0.505 ± 0.006 (n=3) | 0.570 ± 0.006 (n=3) | +0.065 |
| Never-seen score error (MAE) | 0.278 ± 0.001 (n=3) | 0.257 ± 0.001 (n=3) | -0.020 |
| Overall accuracy | 0.629 ± 0.006 (n=3) | 0.674 ± 0.002 (n=3) | +0.045 |
| Familiar tasks | 0.817 ± 0.004 (n=3) | 0.855 ± 0.001 (n=3) | +0.038 |
| Calibration error (ECE) | 0.093 ± 0.012 (n=3) | 0.087 ± 0.014 (n=3) | -0.006 |
| Abstain precision | 0.910 ± 0.022 (n=3) | 0.842 ± 0.082 (n=3) | -0.067 |
| Constructed unanswerables | 0.927 ± 0.023 (n=3) | 0.948 ± 0.022 (n=3) | +0.021 |
| Banking77 (forced) | 0.753 ± 0.021 (n=3) | 0.791 ± 0.002 (n=3) | +0.037 |
| Bias in Bios (forced) | 0.633 ± 0.027 (n=3) | 0.772 ± 0.008 (n=3) | +0.139 |
| Jailbreak (forced) | 0.775 ± 0.040 (n=3) | 0.669 ± 0.089 (n=3) | -0.105 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
