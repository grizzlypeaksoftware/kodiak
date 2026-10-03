# E17 confirmation: XL v2 vs XL v2 + skills, 3 seeds each

## Skills eval

```
reports/preds_skills/xl-s1-baseline.jsonl: skills score 0.518  grounding 0.45  tools 0.46  claims 0.81  relevance 0.35  | {'grounding/which': 0.239, 'tools/missing': 0.53, 'tools/value': 1.0}
reports/preds_skills/e17-xl-skills-s0.jsonl: skills score 0.980  grounding 1.00  tools 0.97  claims 0.99  relevance 0.96  | {'grounding/which': 1.0, 'tools/missing': 0.988, 'tools/value': 1.0}
reports/preds_skills/e17-xl-skills-s1.jsonl: skills score 0.980  grounding 1.00  tools 0.97  claims 0.99  relevance 0.96  | {'grounding/which': 1.0, 'tools/missing': 0.976, 'tools/value': 1.0}
reports/preds_skills/e17-xl-skills-s2.jsonl: skills score 0.982  grounding 1.00  tools 0.99  claims 1.00  relevance 0.94  | {'grounding/which': 1.0, 'tools/missing': 0.988, 'tools/value': 1.0}
```

# Seed comparison: xl v2 vs xl v2 + skills (E17)

| Measure | xl v2 | xl v2 + skills (E17) | Difference (xl v2 + skills (E17) − xl v2) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.619 ± 0.010 (n=3) | 0.621 ± 0.013 (n=3) | +0.002 |
| Never-seen tasks, forced | 0.659 ± 0.013 (n=3) | 0.662 ± 0.012 (n=3) | +0.002 |
| New never-seen tasks (v0.2), forced | 0.608 ± 0.016 (n=3) | 0.611 ± 0.012 (n=3) | +0.002 |
| Never-seen score error (MAE) | 0.272 ± 0.003 (n=3) | 0.276 ± 0.007 (n=3) | +0.004 |
| Overall accuracy | 0.713 ± 0.006 (n=3) | 0.713 ± 0.008 (n=3) | +0.000 |
| Familiar tasks | 0.881 ± 0.002 (n=3) | 0.878 ± 0.002 (n=3) | -0.003 |
| Calibration error (ECE) | 0.076 ± 0.006 (n=3) | 0.072 ± 0.005 (n=3) | -0.003 |
| Never-seen calibration error (ECE) | 0.113 ± 0.010 (n=3) | 0.109 ± 0.007 (n=3) | -0.005 |
| Abstain precision | 0.868 ± 0.007 (n=3) | 0.889 ± 0.029 (n=3) | +0.021 |
| Constructed unanswerables | 0.961 ± 0.008 (n=3) | 0.949 ± 0.018 (n=3) | -0.012 |
| Banking77 (forced) | 0.813 ± 0.019 (n=3) | 0.812 ± 0.008 (n=3) | -0.001 |
| Bias in Bios (forced) | 0.805 ± 0.012 (n=3) | 0.793 ± 0.010 (n=3) | -0.012 |
| Jailbreak (forced) | 0.893 ± 0.035 (n=3) | 0.913 ± 0.040 (n=3) | +0.020 |
| Poem sentiment, has 'mixed' (forced) | 0.540 ± 0.058 (n=3) | 0.544 ± 0.062 (n=3) | +0.004 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.699 ± 0.014 (n=3) | 0.702 ± 0.016 (n=3) | +0.003 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

## Label-overlap probe

| model | right (of 8) | mean p(right) |
|---|---|---|
| b-xl-s1-v2-s0 | 6 | 0.65 |
| b-xl-s1-v2-s1 | 4 | 0.54 |
| b-xl-s1-v2-s2 | 6 | 0.65 |
| b-xl-s1-e17-s0 | 4 | 0.53 |
| b-xl-s1-e17-s1 | 6 | 0.71 |
| b-xl-s1-e17-s2 | 4 | 0.52 |

| sentence | better answer | b-xl-s1-v2-s0 | b-xl-s1-v2-s1 | b-xl-s1-v2-s2 | b-xl-s1-e17-s0 | b-xl-s1-e17-s1 | b-xl-s1-e17-s2 |
|---|---|---|---|---|---|---|---|
| If it can't arrive by then, please cancel and refund me. | delivery status or expedite | 0.01 | 0.01 | 0.03 | 0.00 | 0.05 | 0.00 |
| If it can't arrive by then, please give me my money back. | delivery status or expedite | 0.72 | 0.40 | 0.78 | 0.32 | 0.91 | 0.26 |
| If it can't arrive by then, please cancel my order and refund me. | delivery status or expedite | 0.01 | 0.01 | 0.04 | 0.00 | 0.13 | 0.01 |
| If it can't arrive by then, I'd like a refund instead. | delivery status or expedite | 0.60 | 0.39 | 0.65 | 0.08 | 0.91 | 0.06 |
| I do NOT want to cancel or get a refund, I just need it here by Monday. | delivery status or expedite | 0.92 | 0.69 | 0.93 | 0.89 | 0.98 | 0.88 |
| Honestly I've given up on it. Please just give me my money back. | cancel and refund | 0.93 | 0.87 | 0.82 | 0.96 | 0.75 | 0.99 |
| Forget it. Cancel the order and refund me today. | cancel and refund | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Can you tell me where it actually is and whether it will make it? | delivery status or expedite | 0.99 | 0.97 | 0.98 | 0.98 | 0.98 | 0.98 |
