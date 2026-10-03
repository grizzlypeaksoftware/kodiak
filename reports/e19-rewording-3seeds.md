# E19: E17 vs E17 + reworded options (E18 recipe), 3 seeds each

Keep line (set before the runs): never-seen forced 3-seed mean >= 0.682 and never-seen ECE mean <= 0.109; guards: familiar >= 0.87,
abstain precision mean >= 0.86, skills >= 0.95, label-overlap probe mean >= 4 of 8.

# Seed comparison: E17 vs E17 + reworded options

| Measure | E17 | E17 + reworded options | Difference (E17 + reworded options − E17) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.621 ± 0.013 (n=3) | 0.645 ± 0.010 (n=3) | +0.024 |
| Never-seen tasks, forced | 0.662 ± 0.012 (n=3) | 0.689 ± 0.008 (n=3) | +0.027 |
| New never-seen tasks (v0.2), forced | 0.611 ± 0.012 (n=3) | 0.644 ± 0.010 (n=3) | +0.034 |
| Never-seen score error (MAE) | 0.276 ± 0.007 (n=3) | 0.274 ± 0.003 (n=3) | -0.002 |
| Overall accuracy | 0.713 ± 0.008 (n=3) | 0.729 ± 0.006 (n=3) | +0.016 |
| Familiar tasks | 0.878 ± 0.002 (n=3) | 0.877 ± 0.003 (n=3) | -0.001 |
| Calibration error (ECE) | 0.072 ± 0.005 (n=3) | 0.056 ± 0.007 (n=3) | -0.016 |
| Never-seen calibration error (ECE) | 0.109 ± 0.007 (n=3) | 0.085 ± 0.009 (n=3) | -0.024 |
| Abstain precision | 0.889 ± 0.029 (n=3) | 0.880 ± 0.013 (n=3) | -0.009 |
| Constructed unanswerables | 0.949 ± 0.018 (n=3) | 0.948 ± 0.008 (n=3) | -0.001 |
| Banking77 (forced) | 0.812 ± 0.008 (n=3) | 0.821 ± 0.005 (n=3) | +0.009 |
| Bias in Bios (forced) | 0.793 ± 0.010 (n=3) | 0.811 ± 0.010 (n=3) | +0.017 |
| Jailbreak (forced) | 0.913 ± 0.040 (n=3) | 0.896 ± 0.022 (n=3) | -0.017 |
| Poem sentiment, has 'mixed' (forced) | 0.544 ± 0.062 (n=3) | 0.698 ± 0.019 (n=3) | +0.154 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.702 ± 0.016 (n=3) | 0.728 ± 0.018 (n=3) | +0.026 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

## Skills eval

```
reports/preds_skills/e18-xl-wording-s0.jsonl: skills score 0.985  grounding 1.00  tools 0.98  claims 0.99  relevance 0.97  | {'grounding/which': 0.978, 'tools/missing': 0.976, 'tools/value': 1.0}
reports/preds_skills/e18-xl-wording-s1.jsonl: skills score 0.985  grounding 1.00  tools 0.98  claims 0.99  relevance 0.97  | {'grounding/which': 1.0, 'tools/missing': 0.976, 'tools/value': 1.0}
reports/preds_skills/e18-xl-wording-s2.jsonl: skills score 0.978  grounding 0.99  tools 0.99  claims 0.98  relevance 0.95  | {'grounding/which': 1.0, 'tools/missing': 0.976, 'tools/value': 1.0}
```

## Wording eval

```
reports/preds_wording/e17-s1-baseline.jsonl: consistency 0.621 | accuracy original 0.717, description 0.673, paraphrase 0.689, reworded mean 0.681 | n=605
  consistency by task: arxiv_field 0.53, banking77 0.64, bias_in_bios 0.61, contract_nli 0.73, ethics_commonsense 0.70, fin_tweets_sentiment 0.59, fin_tweets_topic 0.38, jailbreak_classification 0.85
reports/preds_wording/e18-xl-wording-s0.jsonl: consistency 0.676 | accuracy original 0.736, description 0.724, paraphrase 0.688, reworded mean 0.706 | n=605
  consistency by task: arxiv_field 0.49, banking77 0.74, bias_in_bios 0.59, contract_nli 0.76, ethics_commonsense 0.84, fin_tweets_sentiment 0.71, fin_tweets_topic 0.44, jailbreak_classification 0.89
reports/preds_wording/e18-xl-wording-s1.jsonl: consistency 0.678 | accuracy original 0.714, description 0.683, paraphrase 0.676, reworded mean 0.679 | n=605
  consistency by task: arxiv_field 0.55, banking77 0.71, bias_in_bios 0.68, contract_nli 0.64, ethics_commonsense 0.75, fin_tweets_sentiment 0.76, fin_tweets_topic 0.44, jailbreak_classification 0.88
reports/preds_wording/e18-xl-wording-s2.jsonl: consistency 0.679 | accuracy original 0.714, description 0.706, paraphrase 0.676, reworded mean 0.691 | n=605
  consistency by task: arxiv_field 0.53, banking77 0.72, bias_in_bios 0.69, contract_nli 0.80, ethics_commonsense 0.65, fin_tweets_sentiment 0.75, fin_tweets_topic 0.47, jailbreak_classification 0.88
```

## Label-overlap probe

| model | right (of 8) | mean p(right) |
|---|---|---|
| b-xl-s1-e17-s0 | 4 | 0.53 |
| b-xl-s1-e17-s1 | 6 | 0.71 |
| b-xl-s1-e17-s2 | 4 | 0.52 |
| b-xl-s1-e18-s0 | 5 | 0.56 |
| b-xl-s1-e18-s1 | 6 | 0.66 |
| b-xl-s1-e18-s2 | 6 | 0.66 |

| sentence | better answer | b-xl-s1-e17-s0 | b-xl-s1-e17-s1 | b-xl-s1-e17-s2 | b-xl-s1-e18-s0 | b-xl-s1-e18-s1 | b-xl-s1-e18-s2 |
|---|---|---|---|---|---|---|---|
| If it can't arrive by then, please cancel and refund me. | delivery status or expedite | 0.00 | 0.05 | 0.00 | 0.00 | 0.01 | 0.01 |
| If it can't arrive by then, please give me my money back. | delivery status or expedite | 0.32 | 0.91 | 0.26 | 0.58 | 0.80 | 0.83 |
| If it can't arrive by then, please cancel my order and refund me. | delivery status or expedite | 0.00 | 0.13 | 0.01 | 0.00 | 0.02 | 0.02 |
| If it can't arrive by then, I'd like a refund instead. | delivery status or expedite | 0.08 | 0.91 | 0.06 | 0.17 | 0.68 | 0.64 |
| I do NOT want to cancel or get a refund, I just need it here by Monday. | delivery status or expedite | 0.89 | 0.98 | 0.88 | 0.77 | 0.96 | 0.98 |
| Honestly I've given up on it. Please just give me my money back. | cancel and refund | 0.96 | 0.75 | 0.99 | 0.97 | 0.85 | 0.81 |
| Forget it. Cancel the order and refund me today. | cancel and refund | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Can you tell me where it actually is and whether it will make it? | delivery status or expedite | 0.98 | 0.98 | 0.98 | 0.98 | 0.99 | 0.99 |
