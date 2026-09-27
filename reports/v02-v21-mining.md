# Seed comparison: random selection vs mined (v2.1)

| Measure | random selection | mined (v2.1) | Difference (mined (v2.1) − random selection) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.508 ± 0.013 (n=3) | 0.512 ± 0.018 (n=3) | +0.003 |
| Never-seen tasks, forced | 0.545 ± 0.011 (n=3) | 0.546 ± 0.017 (n=3) | +0.001 |
| New never-seen tasks (v0.2), forced | 0.503 ± 0.007 (n=3) | 0.497 ± 0.007 (n=3) | -0.006 |
| Never-seen score error (MAE) | 0.280 ± 0.004 (n=3) | 0.276 ± 0.008 (n=3) | -0.003 |
| Overall accuracy | 0.621 ± 0.009 (n=3) | 0.624 ± 0.012 (n=3) | +0.004 |
| Familiar tasks | 0.818 ± 0.005 (n=3) | 0.820 ± 0.003 (n=3) | +0.003 |
| Calibration error (ECE) | 0.102 ± 0.004 (n=3) | 0.098 ± 0.015 (n=3) | -0.004 |
| Never-seen calibration error (ECE) | 0.153 ± 0.008 (n=3) | 0.152 ± 0.027 (n=3) | -0.002 |
| Abstain precision | 0.839 ± 0.076 (n=3) | 0.869 ± 0.021 (n=3) | +0.031 |
| Constructed unanswerables | 0.923 ± 0.006 (n=3) | 0.937 ± 0.007 (n=3) | +0.013 |
| Banking77 (forced) | 0.740 ± 0.029 (n=3) | 0.773 ± 0.017 (n=3) | +0.033 |
| Bias in Bios (forced) | 0.644 ± 0.026 (n=3) | 0.660 ± 0.021 (n=3) | +0.016 |
| Jailbreak (forced) | 0.688 ± 0.070 (n=3) | 0.720 ± 0.147 (n=3) | +0.032 |
| Poem sentiment, has 'mixed' (forced) | 0.278 ± 0.030 (n=3) | 0.242 ± 0.011 (n=3) | -0.036 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.688 ± 0.003 (n=3) | 0.695 ± 0.004 (n=3) | +0.007 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
