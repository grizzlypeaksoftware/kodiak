# Seed comparison: small v2 vs large v2

| Measure | small v2 | large v2 | Difference (large v2 − small v2) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.703 ± 0.019 (n=3) | 0.712 ± 0.027 (n=3) | +0.009 |
| Never-seen tasks, forced | 0.720 ± 0.012 (n=3) | 0.744 ± 0.032 (n=3) | +0.024 |
| Never-seen score error (MAE) | 0.241 ± 0.002 (n=3) | 0.242 ± 0.002 (n=3) | +0.001 |
| Overall accuracy | 0.799 ± 0.006 (n=3) | 0.826 ± 0.010 (n=3) | +0.027 |
| Familiar tasks | 0.817 ± 0.004 (n=3) | 0.855 ± 0.001 (n=3) | +0.038 |
| Calibration error (ECE) | 0.029 ± 0.003 (n=3) | 0.045 ± 0.004 (n=3) | +0.015 |
| Abstain precision | 0.917 ± 0.018 (n=3) | 0.887 ± 0.043 (n=3) | -0.030 |
| Constructed unanswerables | 0.927 ± 0.023 (n=3) | 0.948 ± 0.022 (n=3) | +0.021 |
| Banking77 (forced) | 0.753 ± 0.021 (n=3) | 0.791 ± 0.002 (n=3) | +0.037 |
| Bias in Bios (forced) | 0.633 ± 0.027 (n=3) | 0.772 ± 0.008 (n=3) | +0.139 |
| Jailbreak (forced) | 0.775 ± 0.040 (n=3) | 0.669 ± 0.089 (n=3) | -0.105 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
