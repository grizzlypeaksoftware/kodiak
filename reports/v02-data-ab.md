# Seed comparison: small v1 vs small v2

| Measure | small v1 | small v2 | Difference (small v2 − small v1) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.495 ± 0.009 (n=3) | 0.521 ± 0.008 (n=3) | +0.025 |
| Never-seen tasks, forced | 0.545 ± 0.008 (n=3) | 0.553 ± 0.007 (n=3) | +0.008 |
| New never-seen tasks (v0.2), forced | 0.495 ± 0.003 (n=3) | 0.505 ± 0.006 (n=3) | +0.011 |
| Never-seen score error (MAE) | 0.275 ± 0.004 (n=3) | 0.278 ± 0.001 (n=3) | +0.003 |
| Overall accuracy | 0.612 ± 0.005 (n=3) | 0.629 ± 0.006 (n=3) | +0.017 |
| Familiar tasks | 0.814 ± 0.001 (n=3) | 0.817 ± 0.004 (n=3) | +0.003 |
| Calibration error (ECE) | 0.103 ± 0.009 (n=3) | 0.093 ± 0.012 (n=3) | -0.010 |
| Abstain precision | 0.686 ± 0.039 (n=3) | 0.910 ± 0.022 (n=3) | +0.224 |
| Constructed unanswerables | 0.942 ± 0.011 (n=3) | 0.927 ± 0.023 (n=3) | -0.016 |
| Banking77 (forced) | 0.763 ± 0.012 (n=3) | 0.753 ± 0.021 (n=3) | -0.009 |
| Bias in Bios (forced) | 0.636 ± 0.022 (n=3) | 0.633 ± 0.027 (n=3) | -0.003 |
| Jailbreak (forced) | 0.764 ± 0.106 (n=3) | 0.775 ± 0.040 (n=3) | +0.011 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
