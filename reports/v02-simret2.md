# Seed comparison: small v2 vs small v2 + Returns Desk v2

| Measure | small v2 | small v2 + Returns Desk v2 | Difference (small v2 + Returns Desk v2 − small v2) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.521 ± 0.008 (n=3) | 0.511 ± 0.006 (n=3) | -0.010 |
| Never-seen tasks, forced | 0.553 ± 0.007 (n=3) | 0.544 ± 0.006 (n=3) | -0.009 |
| New never-seen tasks (v0.2), forced | 0.505 ± 0.006 (n=3) | 0.496 ± 0.009 (n=3) | -0.010 |
| Never-seen score error (MAE) | 0.278 ± 0.001 (n=3) | 0.277 ± 0.010 (n=3) | -0.001 |
| Overall accuracy | 0.629 ± 0.006 (n=3) | 0.623 ± 0.002 (n=3) | -0.006 |
| Familiar tasks | 0.817 ± 0.004 (n=3) | 0.822 ± 0.001 (n=3) | +0.004 |
| Calibration error (ECE) | 0.093 ± 0.012 (n=3) | 0.094 ± 0.004 (n=3) | +0.001 |
| Never-seen calibration error (ECE) | 0.136 ± 0.018 (n=3) | 0.138 ± 0.004 (n=3) | +0.002 |
| Abstain precision | 0.910 ± 0.022 (n=3) | 0.902 ± 0.018 (n=3) | -0.008 |
| Constructed unanswerables | 0.927 ± 0.023 (n=3) | 0.918 ± 0.025 (n=3) | -0.009 |
| Banking77 (forced) | 0.753 ± 0.021 (n=3) | 0.763 ± 0.024 (n=3) | +0.009 |
| Bias in Bios (forced) | 0.633 ± 0.027 (n=3) | 0.656 ± 0.056 (n=3) | +0.023 |
| Jailbreak (forced) | 0.775 ± 0.040 (n=3) | 0.727 ± 0.082 (n=3) | -0.048 |
| Poem sentiment, has 'mixed' (forced) | 0.258 ± 0.016 (n=3) | 0.253 ± 0.025 (n=3) | -0.005 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.704 ± 0.006 (n=3) | 0.698 ± 0.007 (n=3) | -0.007 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

## Label-overlap probe (GENERATOR_V2 §16)

| model | right (of 8) | mean p(right) |
|---|---|---|
| b-small-s1-B-v2 | 3 | 0.45 |
| b-small-s1-B-v2-s1 | 2 | 0.34 |
| b-small-s1-B-v2-s2 | 4 | 0.44 |
| b-small-s1-simret-s0 | 6 | 0.57 |
| b-small-s1-simret2-s0 | 3 | 0.33 |
| b-small-s1-simret2-s1 | 4 | 0.54 |
| b-small-s1-simret2-s2 | 7 | 0.77 |

| sentence | better answer | b-small-s1-B-v2 | b-small-s1-B-v2-s1 | b-small-s1-B-v2-s2 | b-small-s1-simret-s0 | b-small-s1-simret2-s0 | b-small-s1-simret2-s1 | b-small-s1-simret2-s2 |
|---|---|---|---|---|---|---|---|---|
| If it can't arrive by then, please cancel and refund me. | delivery status or expedite | 0.02 | 0.02 | 0.01 | 0.58 | 0.04 | 0.13 | 0.47 |
| If it can't arrive by then, please give me my money back. | delivery status or expedite | 0.44 | 0.22 | 0.75 | 0.85 | 0.41 | 0.42 | 0.89 |
| If it can't arrive by then, please cancel my order and refund me. | delivery status or expedite | 0.02 | 0.01 | 0.02 | 0.61 | 0.05 | 0.07 | 0.65 |
| If it can't arrive by then, I'd like a refund instead. | delivery status or expedite | 0.29 | 0.04 | 0.25 | 0.37 | 0.15 | 0.67 | 0.60 |
| I do NOT want to cancel or get a refund, I just need it here by Monday. | delivery status or expedite | 0.81 | 0.21 | 0.59 | 0.57 | 0.25 | 0.75 | 0.88 |
| Honestly I've given up on it. Please just give me my money back. | cancel and refund | 0.57 | 0.78 | 0.35 | 0.51 | 0.70 | 0.97 | 0.91 |
| Forget it. Cancel the order and refund me today. | cancel and refund | 1.00 | 1.00 | 1.00 | 0.99 | 1.00 | 1.00 | 1.00 |
| Can you tell me where it actually is and whether it will make it? | delivery status or expedite | 0.41 | 0.41 | 0.57 | 0.12 | 0.06 | 0.31 | 0.76 |
