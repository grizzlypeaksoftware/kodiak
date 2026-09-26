# Generator A/B: v1 vs v2.0 at equal size (9,137 synthetic examples), 3 training seeds each

| Measure | v1 (equal size) | v2.0 | Difference (v2 - v1) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.678 ± 0.039 (n=3) | 0.703 ± 0.019 (n=3) | +0.025 |
| Never-seen tasks, forced | 0.721 ± 0.043 (n=3) | 0.720 ± 0.012 (n=3) | -0.000 |
| Overall accuracy | 0.792 ± 0.010 (n=3) | 0.799 ± 0.006 (n=3) | +0.008 |
| Familiar tasks | 0.814 ± 0.001 (n=3) | 0.817 ± 0.004 (n=3) | +0.003 |
| Calibration error (ECE) | 0.038 ± 0.004 (n=3) | 0.029 ± 0.003 (n=3) | -0.008 |
| Abstain precision | 0.844 ± 0.005 (n=3) | 0.917 ± 0.018 (n=3) | +0.073 |
| Constructed unanswerables | 0.942 ± 0.011 (n=3) | 0.927 ± 0.023 (n=3) | -0.016 |
| Banking77 (forced) | 0.763 ± 0.012 (n=3) | 0.753 ± 0.021 (n=3) | -0.009 |
| Bias in Bios (forced) | 0.636 ± 0.022 (n=3) | 0.633 ± 0.027 (n=3) | -0.003 |
| Jailbreak (forced) | 0.764 ± 0.106 (n=3) | 0.775 ± 0.040 (n=3) | +0.011 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
