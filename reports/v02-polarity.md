# Seed comparison: small v2 vs small v2 + polarity

| Measure | small v2 | small v2 + polarity | Difference (small v2 + polarity − small v2) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.521 ± 0.008 (n=3) | 0.523 ± 0.006 (n=3) | +0.002 |
| Never-seen tasks, forced | 0.553 ± 0.007 (n=3) | 0.559 ± 0.009 (n=3) | +0.006 |
| New never-seen tasks (v0.2), forced | 0.505 ± 0.006 (n=3) | 0.505 ± 0.002 (n=3) | +0.000 |
| Never-seen score error (MAE) | 0.278 ± 0.001 (n=3) | 0.275 ± 0.009 (n=3) | -0.003 |
| Overall accuracy | 0.629 ± 0.006 (n=3) | 0.630 ± 0.006 (n=3) | +0.001 |
| Familiar tasks | 0.817 ± 0.004 (n=3) | 0.817 ± 0.007 (n=3) | -0.001 |
| Calibration error (ECE) | 0.093 ± 0.012 (n=3) | 0.102 ± 0.010 (n=3) | +0.009 |
| Abstain precision | 0.910 ± 0.022 (n=3) | 0.845 ± 0.079 (n=3) | -0.064 |
| Constructed unanswerables | 0.927 ± 0.023 (n=3) | 0.923 ± 0.015 (n=3) | -0.003 |
| Banking77 (forced) | 0.753 ± 0.021 (n=3) | 0.769 ± 0.033 (n=3) | +0.016 |
| Bias in Bios (forced) | 0.633 ± 0.027 (n=3) | 0.661 ± 0.014 (n=3) | +0.028 |
| Jailbreak (forced) | 0.775 ± 0.040 (n=3) | 0.804 ± 0.079 (n=3) | +0.029 |
| Poem sentiment, has 'mixed' (forced) | 0.258 ± 0.016 (n=3) | 0.282 ± 0.016 (n=3) | +0.025 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.704 ± 0.006 (n=3) | 0.699 ± 0.010 (n=3) | -0.005 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
