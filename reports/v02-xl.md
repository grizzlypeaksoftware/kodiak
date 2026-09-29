# Seed comparison: large v2 (ModernBERT-large, 400M) vs xl v2 (Ettin-1B)

| Measure | large v2 (ModernBERT-large, 400M) | xl v2 (Ettin-1B) | Difference (xl v2 (Ettin-1B) − large v2 (ModernBERT-large, 400M)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.571 ± 0.003 (n=3) | 0.625 ± 0.000 (n=1) | +0.054 |
| Never-seen tasks, forced | 0.609 ± 0.008 (n=3) | 0.666 ± 0.000 (n=1) | +0.057 |
| New never-seen tasks (v0.2), forced | 0.570 ± 0.006 (n=3) | 0.622 ± 0.000 (n=1) | +0.051 |
| Never-seen score error (MAE) | 0.257 ± 0.001 (n=3) | 0.276 ± 0.000 (n=1) | +0.018 |
| Overall accuracy | 0.674 ± 0.002 (n=3) | 0.716 ± 0.000 (n=1) | +0.042 |
| Familiar tasks | 0.855 ± 0.001 (n=3) | 0.878 ± 0.000 (n=1) | +0.023 |
| Calibration error (ECE) | 0.087 ± 0.014 (n=3) | 0.077 ± 0.000 (n=1) | -0.010 |
| Never-seen calibration error (ECE) | 0.128 ± 0.018 (n=3) | 0.116 ± 0.000 (n=1) | -0.013 |
| Abstain precision | 0.842 ± 0.082 (n=3) | 0.859 ± 0.000 (n=1) | +0.017 |
| Constructed unanswerables | 0.948 ± 0.022 (n=3) | 0.957 ± 0.000 (n=1) | +0.009 |
| Banking77 (forced) | 0.791 ± 0.002 (n=3) | 0.792 ± 0.000 (n=1) | +0.001 |
| Bias in Bios (forced) | 0.772 ± 0.008 (n=3) | 0.808 ± 0.000 (n=1) | +0.036 |
| Jailbreak (forced) | 0.669 ± 0.089 (n=3) | 0.864 ± 0.000 (n=1) | +0.195 |
| Poem sentiment, has 'mixed' (forced) | 0.443 ± 0.059 (n=3) | 0.605 ± 0.000 (n=1) | +0.162 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.755 ± 0.023 (n=3) | 0.715 ± 0.000 (n=1) | -0.040 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

Pass bar (set before the run): never-seen forced >= 0.629.

## Label-overlap probe

| model | right (of 8) | mean p(right) |
|---|---|---|
| b-base-s1-v2-s1 | 5 | 0.58 |
| b-xl-s1-v2-s1 | 4 | 0.54 |

| sentence | better answer | b-base-s1-v2-s1 | b-xl-s1-v2-s1 |
|---|---|---|---|
| If it can't arrive by then, please cancel and refund me. | delivery status or expedite | 0.12 | 0.01 |
| If it can't arrive by then, please give me my money back. | delivery status or expedite | 0.68 | 0.40 |
| If it can't arrive by then, please cancel my order and refund me. | delivery status or expedite | 0.05 | 0.01 |
| If it can't arrive by then, I'd like a refund instead. | delivery status or expedite | 0.76 | 0.39 |
| I do NOT want to cancel or get a refund, I just need it here by Monday. | delivery status or expedite | 0.80 | 0.69 |
| Honestly I've given up on it. Please just give me my money back. | cancel and refund | 0.98 | 0.87 |
| Forget it. Cancel the order and refund me today. | cancel and refund | 1.00 | 1.00 |
| Can you tell me where it actually is and whether it will make it? | delivery status or expedite | 0.26 | 0.97 |
