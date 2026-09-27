# Seed comparison: small v2 vs small distilled

| Measure | small v2 | small distilled | Difference (small distilled − small v2) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.521 ± 0.008 (n=3) | 0.523 ± 0.010 (n=3) | +0.002 |
| Never-seen tasks, forced | 0.553 ± 0.007 (n=3) | 0.558 ± 0.013 (n=3) | +0.005 |
| New never-seen tasks (v0.2), forced | 0.505 ± 0.006 (n=3) | 0.508 ± 0.010 (n=3) | +0.002 |
| Never-seen score error (MAE) | 0.278 ± 0.001 (n=3) | 0.274 ± 0.002 (n=3) | -0.003 |
| Overall accuracy | 0.629 ± 0.006 (n=3) | 0.630 ± 0.008 (n=3) | +0.001 |
| Familiar tasks | 0.817 ± 0.004 (n=3) | 0.816 ± 0.003 (n=3) | -0.002 |
| Calibration error (ECE) | 0.093 ± 0.012 (n=3) | 0.105 ± 0.014 (n=3) | +0.012 |
| Abstain precision | 0.910 ± 0.022 (n=3) | 0.880 ± 0.022 (n=3) | -0.030 |
| Constructed unanswerables | 0.927 ± 0.023 (n=3) | 0.929 ± 0.014 (n=3) | +0.002 |
| Banking77 (forced) | 0.753 ± 0.021 (n=3) | 0.771 ± 0.014 (n=3) | +0.017 |
| Bias in Bios (forced) | 0.633 ± 0.027 (n=3) | 0.675 ± 0.034 (n=3) | +0.041 |
| Jailbreak (forced) | 0.775 ± 0.040 (n=3) | 0.756 ± 0.102 (n=3) | -0.019 |
| Poem sentiment, has 'mixed' (forced) | 0.258 ± 0.016 (n=3) | 0.263 ± 0.021 (n=3) | +0.005 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.704 ± 0.006 (n=3) | 0.692 ± 0.008 (n=3) | -0.012 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
