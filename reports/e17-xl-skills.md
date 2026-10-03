# E17 result: XL + skills data (seed 1)

Keep line (set before the run): skills score >= 0.618 (baseline 0.518); guards: never-seen >= 0.645, familiar >= 0.87,
abstain precision >= 0.86, label-overlap probe >= 4 of 8.

## Skills eval

```
reports/preds_skills/xl-s1-baseline.jsonl: skills score 0.518  grounding 0.45  tools 0.46  claims 0.81  relevance 0.35  | {'grounding/which': 0.239, 'tools/missing': 0.53, 'tools/value': 1.0}
reports/preds_skills/e17-xl-skills-s1.jsonl: skills score 0.980  grounding 1.00  tools 0.97  claims 0.99  relevance 0.96  | {'grounding/which': 1.0, 'tools/missing': 0.976, 'tools/value': 1.0}
```

## Eval v0.2 (never-seen, familiar, calibration, abstain precision)

# Seed comparison: xl v2 (seed 1) vs xl v2 + skills (E17)

| Measure | xl v2 (seed 1) | xl v2 + skills (E17) | Difference (xl v2 + skills (E17) − xl v2 (seed 1)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.625 ± 0.000 (n=1) | 0.624 ± 0.000 (n=1) | -0.001 |
| Never-seen tasks, forced | 0.666 ± 0.000 (n=1) | 0.664 ± 0.000 (n=1) | -0.002 |
| New never-seen tasks (v0.2), forced | 0.622 ± 0.000 (n=1) | 0.612 ± 0.000 (n=1) | -0.010 |
| Never-seen score error (MAE) | 0.276 ± 0.000 (n=1) | 0.282 ± 0.000 (n=1) | +0.006 |
| Overall accuracy | 0.716 ± 0.000 (n=1) | 0.716 ± 0.000 (n=1) | +0.000 |
| Familiar tasks | 0.878 ± 0.000 (n=1) | 0.880 ± 0.000 (n=1) | +0.001 |
| Calibration error (ECE) | 0.077 ± 0.000 (n=1) | 0.073 ± 0.000 (n=1) | -0.003 |
| Never-seen calibration error (ECE) | 0.116 ± 0.000 (n=1) | 0.111 ± 0.000 (n=1) | -0.004 |
| Abstain precision | 0.859 ± 0.000 (n=1) | 0.891 ± 0.000 (n=1) | +0.032 |
| Constructed unanswerables | 0.957 ± 0.000 (n=1) | 0.950 ± 0.000 (n=1) | -0.007 |
| Banking77 (forced) | 0.792 ± 0.000 (n=1) | 0.820 ± 0.000 (n=1) | +0.028 |
| Bias in Bios (forced) | 0.808 ± 0.000 (n=1) | 0.804 ± 0.000 (n=1) | -0.004 |
| Jailbreak (forced) | 0.864 ± 0.000 (n=1) | 0.916 ± 0.000 (n=1) | +0.052 |
| Poem sentiment, has 'mixed' (forced) | 0.605 ± 0.000 (n=1) | 0.578 ± 0.000 (n=1) | -0.027 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.715 ± 0.000 (n=1) | 0.693 ± 0.000 (n=1) | -0.022 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

## Label-overlap probe

| model | right (of 8) | mean p(right) |
|---|---|---|
| b-xl-s1-v2-s1 | 4 | 0.54 |
| b-xl-s1-e17-s1 | 6 | 0.71 |

| sentence | better answer | b-xl-s1-v2-s1 | b-xl-s1-e17-s1 |
|---|---|---|---|
| If it can't arrive by then, please cancel and refund me. | delivery status or expedite | 0.01 | 0.05 |
| If it can't arrive by then, please give me my money back. | delivery status or expedite | 0.40 | 0.91 |
| If it can't arrive by then, please cancel my order and refund me. | delivery status or expedite | 0.01 | 0.13 |
| If it can't arrive by then, I'd like a refund instead. | delivery status or expedite | 0.39 | 0.91 |
| I do NOT want to cancel or get a refund, I just need it here by Monday. | delivery status or expedite | 0.69 | 0.98 |
| Honestly I've given up on it. Please just give me my money back. | cancel and refund | 0.87 | 0.75 |
| Forget it. Cancel the order and refund me today. | cancel and refund | 1.00 | 1.00 |
| Can you tell me where it actually is and whether it will make it? | delivery status or expedite | 0.97 | 0.98 |
