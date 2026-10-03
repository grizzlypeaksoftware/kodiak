# E18 result: option-wording robustness (seed 1) vs E17 seed 1

Keep line (set before the run): wording consistency >= 0.721 (baseline 0.621) and reworded accuracy >= 0.711 (0.681); guards:
never-seen >= 0.645, familiar >= 0.87, abstain precision >= 0.86, skills score >= 0.95, label-overlap probe >= 4 of 8.

## Wording eval

```
reports/preds_wording/e17-s1-baseline.jsonl: consistency 0.621 | accuracy original 0.717, description 0.673, paraphrase 0.689, reworded mean 0.681 | n=605
  consistency by task: arxiv_field 0.53, banking77 0.64, bias_in_bios 0.61, contract_nli 0.73, ethics_commonsense 0.70, fin_tweets_sentiment 0.59, fin_tweets_topic 0.38, jailbreak_classification 0.85
reports/preds_wording/e18-xl-wording-s1.jsonl: consistency 0.678 | accuracy original 0.714, description 0.683, paraphrase 0.676, reworded mean 0.679 | n=605
  consistency by task: arxiv_field 0.55, banking77 0.71, bias_in_bios 0.68, contract_nli 0.64, ethics_commonsense 0.75, fin_tweets_sentiment 0.76, fin_tweets_topic 0.44, jailbreak_classification 0.88
```

## Skills eval

```
reports/preds_skills/e17-xl-skills-s1.jsonl: skills score 0.980  grounding 1.00  tools 0.97  claims 0.99  relevance 0.96  | {'grounding/which': 1.0, 'tools/missing': 0.976, 'tools/value': 1.0}
reports/preds_skills/e18-xl-wording-s1.jsonl: skills score 0.985  grounding 1.00  tools 0.98  claims 0.99  relevance 0.97  | {'grounding/which': 1.0, 'tools/missing': 0.976, 'tools/value': 1.0}
```

## Eval v0.2

# Seed comparison: E17 (seed 1) vs E18 (seed 1)

| Measure | E17 (seed 1) | E18 (seed 1) | Difference (E18 (seed 1) − E17 (seed 1)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.624 ± 0.000 (n=1) | 0.635 ± 0.000 (n=1) | +0.010 |
| Never-seen tasks, forced | 0.664 ± 0.000 (n=1) | 0.680 ± 0.000 (n=1) | +0.016 |
| New never-seen tasks (v0.2), forced | 0.612 ± 0.000 (n=1) | 0.633 ± 0.000 (n=1) | +0.021 |
| Never-seen score error (MAE) | 0.282 ± 0.000 (n=1) | 0.271 ± 0.000 (n=1) | -0.011 |
| Overall accuracy | 0.716 ± 0.000 (n=1) | 0.723 ± 0.000 (n=1) | +0.006 |
| Familiar tasks | 0.880 ± 0.000 (n=1) | 0.877 ± 0.000 (n=1) | -0.003 |
| Calibration error (ECE) | 0.073 ± 0.000 (n=1) | 0.060 ± 0.000 (n=1) | -0.013 |
| Never-seen calibration error (ECE) | 0.111 ± 0.000 (n=1) | 0.094 ± 0.000 (n=1) | -0.018 |
| Abstain precision | 0.891 ± 0.000 (n=1) | 0.870 ± 0.000 (n=1) | -0.021 |
| Constructed unanswerables | 0.950 ± 0.000 (n=1) | 0.957 ± 0.000 (n=1) | +0.007 |
| Banking77 (forced) | 0.820 ± 0.000 (n=1) | 0.824 ± 0.000 (n=1) | +0.004 |
| Bias in Bios (forced) | 0.804 ± 0.000 (n=1) | 0.820 ± 0.000 (n=1) | +0.016 |
| Jailbreak (forced) | 0.916 ± 0.000 (n=1) | 0.892 ± 0.000 (n=1) | -0.024 |
| Poem sentiment, has 'mixed' (forced) | 0.578 ± 0.000 (n=1) | 0.690 ± 0.000 (n=1) | +0.112 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.693 ± 0.000 (n=1) | 0.715 ± 0.000 (n=1) | +0.022 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

## Label-overlap probe

| model | right (of 8) | mean p(right) |
|---|---|---|
| b-xl-s1-e17-s1 | 6 | 0.71 |
| b-xl-s1-e18-s1 | 6 | 0.66 |

| sentence | better answer | b-xl-s1-e17-s1 | b-xl-s1-e18-s1 |
|---|---|---|---|
| If it can't arrive by then, please cancel and refund me. | delivery status or expedite | 0.05 | 0.01 |
| If it can't arrive by then, please give me my money back. | delivery status or expedite | 0.91 | 0.80 |
| If it can't arrive by then, please cancel my order and refund me. | delivery status or expedite | 0.13 | 0.02 |
| If it can't arrive by then, I'd like a refund instead. | delivery status or expedite | 0.91 | 0.68 |
| I do NOT want to cancel or get a refund, I just need it here by Monday. | delivery status or expedite | 0.98 | 0.96 |
| Honestly I've given up on it. Please just give me my money back. | cancel and refund | 0.75 | 0.85 |
| Forget it. Cancel the order and refund me today. | cancel and refund | 1.00 | 1.00 |
| Can you tell me where it actually is and whether it will make it? | delivery status or expedite | 0.98 | 0.99 |
