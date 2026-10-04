# E21 result: skills batch 2 (seed 1) vs Kodiak-v0.2-1B (seed 1)

Keep line (set before the run): skills-2 score >= 0.392 (0.142), each kind +0.10, MT-Bench anchor >= +0.040; guards: never-seen >= 0.679,
familiar >= 0.87, abstain precision >= 0.86, E17 skills >= 0.95, ranking >= 0.541, wording consistency >= 0.66, probe >= 5 of 8.

## Skills-2 eval (+ MT-Bench anchor)

```
reports/preds_skills2/v02-s1-baseline.jsonl: skills-2 score 0.142
  pairwise_judge                     n=100 acc=0.410 skill=+0.115
  pairwise_judge (MT-Bench anchor)   n=150 acc=0.360 skill=+0.040
  policy_violation                   n=100 acc=0.640 skill=+0.550
  sarcasm                            n=100 acc=0.380 skill=-0.240
reports/preds_skills2/e21-xl-skills2-s1.jsonl: skills-2 score 0.950
  pairwise_judge                     n=100 acc=0.900 skill=+0.850
  pairwise_judge (MT-Bench anchor)   n=150 acc=0.520 skill=+0.280
  policy_violation                   n=100 acc=1.000 skill=+1.000
  sarcasm                            n=100 acc=1.000 skill=+1.000
```

## Wording eval

```
reports/preds_wording/e18-xl-wording-s1.jsonl: consistency 0.678 | accuracy original 0.714, description 0.683, paraphrase 0.676, reworded mean 0.679 | n=605
  consistency by task: arxiv_field 0.55, banking77 0.71, bias_in_bios 0.68, contract_nli 0.64, ethics_commonsense 0.75, fin_tweets_sentiment 0.76, fin_tweets_topic 0.44, jailbreak_classification 0.88
reports/preds_wording/e21-xl-skills2-s1.jsonl: consistency 0.674 | accuracy original 0.719, description 0.702, paraphrase 0.706, reworded mean 0.704 | n=605
  consistency by task: arxiv_field 0.49, banking77 0.74, bias_in_bios 0.60, contract_nli 0.82, ethics_commonsense 0.78, fin_tweets_sentiment 0.70, fin_tweets_topic 0.47, jailbreak_classification 0.86
```

## Skills eval

```
reports/preds_skills/e18-xl-wording-s1.jsonl: skills score 0.985  grounding 1.00  tools 0.98  claims 0.99  relevance 0.97  | {'grounding/which': 1.0, 'tools/missing': 0.976, 'tools/value': 1.0}
reports/preds_skills/e21-xl-skills2-s1.jsonl: skills score 0.982  grounding 1.00  tools 0.98  claims 1.00  relevance 0.95  | {'grounding/which': 1.0, 'tools/missing': 0.988, 'tools/value': 1.0}
```

## Eval v0.2

# Seed comparison: v0.2 (seed 1) vs E21 (seed 1)

| Measure | v0.2 (seed 1) | E21 (seed 1) | Difference (E21 (seed 1) − v0.2 (seed 1)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.635 ± 0.000 (n=1) | 0.637 ± 0.000 (n=1) | +0.003 |
| Never-seen tasks, forced | 0.680 ± 0.000 (n=1) | 0.674 ± 0.000 (n=1) | -0.007 |
| New never-seen tasks (v0.2), forced | 0.633 ± 0.000 (n=1) | 0.619 ± 0.000 (n=1) | -0.014 |
| Never-seen score error (MAE) | 0.271 ± 0.000 (n=1) | 0.274 ± 0.000 (n=1) | +0.003 |
| Overall accuracy | 0.723 ± 0.000 (n=1) | 0.725 ± 0.000 (n=1) | +0.002 |
| Familiar tasks | 0.877 ± 0.000 (n=1) | 0.878 ± 0.000 (n=1) | +0.001 |
| Calibration error (ECE) | 0.060 ± 0.000 (n=1) | 0.054 ± 0.000 (n=1) | -0.007 |
| Never-seen calibration error (ECE) | 0.094 ± 0.000 (n=1) | 0.078 ± 0.000 (n=1) | -0.016 |
| Abstain precision | 0.870 ± 0.000 (n=1) | 0.940 ± 0.000 (n=1) | +0.070 |
| Constructed unanswerables | 0.957 ± 0.000 (n=1) | 0.957 ± 0.000 (n=1) | +0.000 |
| Banking77 (forced) | 0.824 ± 0.000 (n=1) | 0.828 ± 0.000 (n=1) | +0.004 |
| Bias in Bios (forced) | 0.820 ± 0.000 (n=1) | 0.820 ± 0.000 (n=1) | +0.000 |
| Jailbreak (forced) | 0.892 ± 0.000 (n=1) | 0.944 ± 0.000 (n=1) | +0.052 |
| Poem sentiment, has 'mixed' (forced) | 0.690 ± 0.000 (n=1) | 0.688 ± 0.000 (n=1) | -0.002 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.715 ± 0.000 (n=1) | 0.710 ± 0.000 (n=1) | -0.005 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

## Ranking (never-seen aurc_gap_closed)

- e18-xl-wording-s1: 0.561
- e21-xl-skills2-s1: 0.574

## Label-overlap probe

| model | right (of 8) | mean p(right) |
|---|---|---|
| b-xl-s1-e18-s1 | 6 | 0.66 |
| b-xl-s1-e21-s1 | 4 | 0.53 |

| sentence | better answer | b-xl-s1-e18-s1 | b-xl-s1-e21-s1 |
|---|---|---|---|
| If it can't arrive by then, please cancel and refund me. | delivery status or expedite | 0.01 | 0.00 |
| If it can't arrive by then, please give me my money back. | delivery status or expedite | 0.80 | 0.24 |
| If it can't arrive by then, please cancel my order and refund me. | delivery status or expedite | 0.02 | 0.00 |
| If it can't arrive by then, I'd like a refund instead. | delivery status or expedite | 0.68 | 0.13 |
| I do NOT want to cancel or get a refund, I just need it here by Monday. | delivery status or expedite | 0.96 | 0.94 |
| Honestly I've given up on it. Please just give me my money back. | cancel and refund | 0.85 | 0.96 |
| Forget it. Cancel the order and refund me today. | cancel and refund | 1.00 | 1.00 |
| Can you tell me where it actually is and whether it will make it? | delivery status or expedite | 0.99 | 0.99 |
