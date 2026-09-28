# Seed comparison: small v2 vs small v2 + unfamiliar

| Measure | small v2 | small v2 + unfamiliar | Difference (small v2 + unfamiliar − small v2) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.521 ± 0.008 (n=3) | 0.516 ± 0.012 (n=3) | -0.005 |
| Never-seen tasks, forced | 0.553 ± 0.007 (n=3) | 0.548 ± 0.013 (n=3) | -0.005 |
| New never-seen tasks (v0.2), forced | 0.505 ± 0.006 (n=3) | 0.503 ± 0.011 (n=3) | -0.002 |
| Never-seen score error (MAE) | 0.278 ± 0.001 (n=3) | 0.272 ± 0.004 (n=3) | -0.006 |
| Overall accuracy | 0.629 ± 0.006 (n=3) | 0.626 ± 0.006 (n=3) | -0.003 |
| Familiar tasks | 0.817 ± 0.004 (n=3) | 0.817 ± 0.007 (n=3) | -0.000 |
| Calibration error (ECE) | 0.093 ± 0.012 (n=3) | 0.091 ± 0.015 (n=3) | -0.002 |
| Never-seen calibration error (ECE) | 0.136 ± 0.018 (n=3) | 0.137 ± 0.024 (n=3) | +0.001 |
| Abstain precision | 0.910 ± 0.022 (n=3) | 0.915 ± 0.029 (n=3) | +0.006 |
| Constructed unanswerables | 0.927 ± 0.023 (n=3) | 0.920 ± 0.009 (n=3) | -0.007 |
| Banking77 (forced) | 0.753 ± 0.021 (n=3) | 0.756 ± 0.018 (n=3) | +0.003 |
| Bias in Bios (forced) | 0.633 ± 0.027 (n=3) | 0.645 ± 0.020 (n=3) | +0.012 |
| Jailbreak (forced) | 0.775 ± 0.040 (n=3) | 0.715 ± 0.073 (n=3) | -0.060 |
| Poem sentiment, has 'mixed' (forced) | 0.258 ± 0.016 (n=3) | 0.259 ± 0.028 (n=3) | +0.002 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.704 ± 0.006 (n=3) | 0.693 ± 0.001 (n=3) | -0.011 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
