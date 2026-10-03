# E20 result: wording-consistency loss (seed 1) vs Kodiak-v0.2-1B (E18/E19 recipe, seed 1)

Keep line (set before the run): consistency >= 0.75 and reworded accuracy >= 0.712; guards: never-seen >= 0.679, familiar >= 0.87,
abstain precision >= 0.86, skills >= 0.95, label-overlap probe >= 5 of 8, never-seen ranking (aurc_gap_closed) >= 0.541.

## Wording eval

```
reports/preds_wording/e18-xl-wording-s1.jsonl: consistency 0.678 | accuracy original 0.714, description 0.683, paraphrase 0.676, reworded mean 0.679 | n=605
  consistency by task: arxiv_field 0.55, banking77 0.71, bias_in_bios 0.68, contract_nli 0.64, ethics_commonsense 0.75, fin_tweets_sentiment 0.76, fin_tweets_topic 0.44, jailbreak_classification 0.88
reports/preds_wording/e20-xl-consistency-s1.jsonl: consistency 0.684 | accuracy original 0.704, description 0.701, paraphrase 0.681, reworded mean 0.691 | n=605
  consistency by task: arxiv_field 0.47, banking77 0.79, bias_in_bios 0.70, contract_nli 0.69, ethics_commonsense 0.91, fin_tweets_sentiment 0.62, fin_tweets_topic 0.45, jailbreak_classification 0.84
```

## Skills eval

```
reports/preds_skills/e18-xl-wording-s1.jsonl: skills score 0.985  grounding 1.00  tools 0.98  claims 0.99  relevance 0.97  | {'grounding/which': 1.0, 'tools/missing': 0.976, 'tools/value': 1.0}
reports/preds_skills/e20-xl-consistency-s1.jsonl: skills score 0.982  grounding 1.00  tools 0.99  claims 0.99  relevance 0.95  | {'grounding/which': 1.0, 'tools/missing': 0.976, 'tools/value': 1.0}
```

## Eval v0.2

# Seed comparison: v0.2 (seed 1) vs E20 (seed 1)

| Measure | v0.2 (seed 1) | E20 (seed 1) | Difference (E20 (seed 1) − v0.2 (seed 1)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.635 ± 0.000 (n=1) | 0.639 ± 0.000 (n=1) | +0.004 |
| Never-seen tasks, forced | 0.680 ± 0.000 (n=1) | 0.678 ± 0.000 (n=1) | -0.002 |
| New never-seen tasks (v0.2), forced | 0.633 ± 0.000 (n=1) | 0.632 ± 0.000 (n=1) | -0.001 |
| Never-seen score error (MAE) | 0.271 ± 0.000 (n=1) | 0.269 ± 0.000 (n=1) | -0.002 |
| Overall accuracy | 0.723 ± 0.000 (n=1) | 0.721 ± 0.000 (n=1) | -0.001 |
| Familiar tasks | 0.877 ± 0.000 (n=1) | 0.863 ± 0.000 (n=1) | -0.014 |
| Calibration error (ECE) | 0.060 ± 0.000 (n=1) | 0.062 ± 0.000 (n=1) | +0.001 |
| Never-seen calibration error (ECE) | 0.094 ± 0.000 (n=1) | 0.090 ± 0.000 (n=1) | -0.003 |
| Abstain precision | 0.870 ± 0.000 (n=1) | 0.890 ± 0.000 (n=1) | +0.020 |
| Constructed unanswerables | 0.957 ± 0.000 (n=1) | 0.947 ± 0.000 (n=1) | -0.010 |
| Banking77 (forced) | 0.824 ± 0.000 (n=1) | 0.812 ± 0.000 (n=1) | -0.012 |
| Bias in Bios (forced) | 0.820 ± 0.000 (n=1) | 0.820 ± 0.000 (n=1) | +0.000 |
| Jailbreak (forced) | 0.892 ± 0.000 (n=1) | 0.888 ± 0.000 (n=1) | -0.004 |
| Poem sentiment, has 'mixed' (forced) | 0.690 ± 0.000 (n=1) | 0.660 ± 0.000 (n=1) | -0.030 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.715 ± 0.000 (n=1) | 0.757 ± 0.000 (n=1) | +0.042 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

## Ranking (never-seen aurc_gap_closed)

- e18-xl-wording-s1: 0.561
- e20-xl-consistency-s1: 0.510

## Label-overlap probe

| model | right (of 8) | mean p(right) |
|---|---|---|
| b-xl-s1-e18-s1 | 6 | 0.66 |
| b-xl-s1-e20-s1 | 6 | 0.64 |

| sentence | better answer | b-xl-s1-e18-s1 | b-xl-s1-e20-s1 |
|---|---|---|---|
| If it can't arrive by then, please cancel and refund me. | delivery status or expedite | 0.01 | 0.01 |
| If it can't arrive by then, please give me my money back. | delivery status or expedite | 0.80 | 0.74 |
| If it can't arrive by then, please cancel my order and refund me. | delivery status or expedite | 0.02 | 0.02 |
| If it can't arrive by then, I'd like a refund instead. | delivery status or expedite | 0.68 | 0.50 |
| I do NOT want to cancel or get a refund, I just need it here by Monday. | delivery status or expedite | 0.96 | 0.97 |
| Honestly I've given up on it. Please just give me my money back. | cancel and refund | 0.85 | 0.90 |
| Forget it. Cancel the order and refund me today. | cancel and refund | 1.00 | 1.00 |
| Can you tell me where it actually is and whether it will make it? | delivery status or expedite | 0.99 | 0.99 |
