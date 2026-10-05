# E21 confirmation: v0.2 + skills-2, 3 seeds vs Kodiak-v0.2-1B 3 seeds

Rule (written before these seeds ran, D63 option B): every line judged on 3-seed means; see docs/experiments/E21-skills-batch-2.md.

## Skills-2 eval (+ MT-Bench anchor)

```
reports/preds_skills2/v02-s1-baseline.jsonl: skills-2 score 0.142
  pairwise_judge                     n=100 acc=0.410 skill=+0.115
  pairwise_judge (MT-Bench anchor)   n=150 acc=0.360 skill=+0.040
  policy_violation                   n=100 acc=0.640 skill=+0.550
  sarcasm                            n=100 acc=0.380 skill=-0.240
reports/preds_skills2/e21-xl-skills2-s0.jsonl: skills-2 score 0.953
  pairwise_judge                     n=100 acc=0.920 skill=+0.880
  pairwise_judge (MT-Bench anchor)   n=150 acc=0.533 skill=+0.300
  policy_violation                   n=100 acc=1.000 skill=+1.000
  sarcasm                            n=100 acc=0.990 skill=+0.980
reports/preds_skills2/e21-xl-skills2-s1.jsonl: skills-2 score 0.950
  pairwise_judge                     n=100 acc=0.900 skill=+0.850
  pairwise_judge (MT-Bench anchor)   n=150 acc=0.520 skill=+0.280
  policy_violation                   n=100 acc=1.000 skill=+1.000
  sarcasm                            n=100 acc=1.000 skill=+1.000
reports/preds_skills2/e21-xl-skills2-s2.jsonl: skills-2 score 0.975
  pairwise_judge                     n=100 acc=0.950 skill=+0.925
  pairwise_judge (MT-Bench anchor)   n=150 acc=0.567 skill=+0.350
  policy_violation                   n=100 acc=1.000 skill=+1.000
  sarcasm                            n=100 acc=1.000 skill=+1.000
```

# Seed comparison: v0.2 (3 seeds) vs E21 (3 seeds)

| Measure | v0.2 (3 seeds) | E21 (3 seeds) | Difference (E21 (3 seeds) − v0.2 (3 seeds)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.645 ± 0.010 (n=3) | 0.650 ± 0.011 (n=3) | +0.005 |
| Never-seen tasks, forced | 0.689 ± 0.008 (n=3) | 0.690 ± 0.014 (n=3) | +0.001 |
| New never-seen tasks (v0.2), forced | 0.644 ± 0.010 (n=3) | 0.641 ± 0.019 (n=3) | -0.003 |
| Never-seen score error (MAE) | 0.274 ± 0.003 (n=3) | 0.277 ± 0.003 (n=3) | +0.003 |
| Overall accuracy | 0.729 ± 0.006 (n=3) | 0.732 ± 0.007 (n=3) | +0.003 |
| Familiar tasks | 0.877 ± 0.003 (n=3) | 0.878 ± 0.003 (n=3) | +0.000 |
| Calibration error (ECE) | 0.056 ± 0.007 (n=3) | 0.050 ± 0.006 (n=3) | -0.005 |
| Never-seen calibration error (ECE) | 0.085 ± 0.009 (n=3) | 0.073 ± 0.005 (n=3) | -0.012 |
| Abstain precision | 0.880 ± 0.013 (n=3) | 0.919 ± 0.025 (n=3) | +0.039 |
| Constructed unanswerables | 0.948 ± 0.008 (n=3) | 0.947 ± 0.010 (n=3) | -0.001 |
| Banking77 (forced) | 0.821 ± 0.005 (n=3) | 0.824 ± 0.011 (n=3) | +0.003 |
| Bias in Bios (forced) | 0.811 ± 0.010 (n=3) | 0.812 ± 0.011 (n=3) | +0.001 |
| Jailbreak (forced) | 0.896 ± 0.022 (n=3) | 0.941 ± 0.005 (n=3) | +0.045 |
| Poem sentiment, has 'mixed' (forced) | 0.698 ± 0.019 (n=3) | 0.705 ± 0.016 (n=3) | +0.007 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.728 ± 0.018 (n=3) | 0.718 ± 0.011 (n=3) | -0.010 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

## Skills eval

```
reports/preds_skills/e21-xl-skills2-s0.jsonl: skills score 0.972  grounding 0.98  tools 0.98  claims 0.99  relevance 0.94  | {'grounding/which': 0.978, 'tools/missing': 0.976, 'tools/value': 1.0}
reports/preds_skills/e21-xl-skills2-s1.jsonl: skills score 0.982  grounding 1.00  tools 0.98  claims 1.00  relevance 0.95  | {'grounding/which': 1.0, 'tools/missing': 0.988, 'tools/value': 1.0}
reports/preds_skills/e21-xl-skills2-s2.jsonl: skills score 0.982  grounding 0.98  tools 0.99  claims 1.00  relevance 0.96  | {'grounding/which': 1.0, 'tools/missing': 0.988, 'tools/value': 1.0}
```

## Wording eval

```
reports/preds_wording/e18-xl-wording-s0.jsonl: consistency 0.676 | accuracy original 0.736, description 0.724, paraphrase 0.688, reworded mean 0.706 | n=605
  consistency by task: arxiv_field 0.49, banking77 0.74, bias_in_bios 0.59, contract_nli 0.76, ethics_commonsense 0.84, fin_tweets_sentiment 0.71, fin_tweets_topic 0.44, jailbreak_classification 0.89
reports/preds_wording/e18-xl-wording-s1.jsonl: consistency 0.678 | accuracy original 0.714, description 0.683, paraphrase 0.676, reworded mean 0.679 | n=605
  consistency by task: arxiv_field 0.55, banking77 0.71, bias_in_bios 0.68, contract_nli 0.64, ethics_commonsense 0.75, fin_tweets_sentiment 0.76, fin_tweets_topic 0.44, jailbreak_classification 0.88
reports/preds_wording/e18-xl-wording-s2.jsonl: consistency 0.679 | accuracy original 0.714, description 0.706, paraphrase 0.676, reworded mean 0.691 | n=605
  consistency by task: arxiv_field 0.53, banking77 0.72, bias_in_bios 0.69, contract_nli 0.80, ethics_commonsense 0.65, fin_tweets_sentiment 0.75, fin_tweets_topic 0.47, jailbreak_classification 0.88
reports/preds_wording/e21-xl-skills2-s0.jsonl: consistency 0.702 | accuracy original 0.732, description 0.724, paraphrase 0.701, reworded mean 0.712 | n=605
  consistency by task: arxiv_field 0.57, banking77 0.82, bias_in_bios 0.66, contract_nli 0.80, ethics_commonsense 0.78, fin_tweets_sentiment 0.68, fin_tweets_topic 0.49, jailbreak_classification 0.86
reports/preds_wording/e21-xl-skills2-s1.jsonl: consistency 0.674 | accuracy original 0.719, description 0.702, paraphrase 0.706, reworded mean 0.704 | n=605
  consistency by task: arxiv_field 0.49, banking77 0.74, bias_in_bios 0.60, contract_nli 0.82, ethics_commonsense 0.78, fin_tweets_sentiment 0.70, fin_tweets_topic 0.47, jailbreak_classification 0.86
reports/preds_wording/e21-xl-skills2-s2.jsonl: consistency 0.671 | accuracy original 0.716, description 0.694, paraphrase 0.688, reworded mean 0.691 | n=605
  consistency by task: arxiv_field 0.51, banking77 0.70, bias_in_bios 0.62, contract_nli 0.71, ethics_commonsense 0.76, fin_tweets_sentiment 0.79, fin_tweets_topic 0.44, jailbreak_classification 0.85
```

## Ranking (never-seen aurc_gap_closed)

- e18-xl-wording-s0: 0.548
- e18-xl-wording-s1: 0.561
- e18-xl-wording-s2: 0.559
- e21-xl-skills2-s0: 0.545
- e21-xl-skills2-s1: 0.574
- e21-xl-skills2-s2: 0.547

## Label-overlap probe

| model | right (of 8) | mean p(right) |
|---|---|---|
| b-xl-s1-e18-s0 | 5 | 0.56 |
| b-xl-s1-e18-s1 | 6 | 0.66 |
| b-xl-s1-e18-s2 | 6 | 0.66 |
| b-xl-s1-e21-s0 | 5 | 0.62 |
| b-xl-s1-e21-s1 | 4 | 0.53 |
| b-xl-s1-e21-s2 | 5 | 0.56 |

| sentence | better answer | b-xl-s1-e18-s0 | b-xl-s1-e18-s1 | b-xl-s1-e18-s2 | b-xl-s1-e21-s0 | b-xl-s1-e21-s1 | b-xl-s1-e21-s2 |
|---|---|---|---|---|---|---|---|
| If it can't arrive by then, please cancel and refund me. | delivery status or expedite | 0.00 | 0.01 | 0.01 | 0.01 | 0.00 | 0.00 |
| If it can't arrive by then, please give me my money back. | delivery status or expedite | 0.58 | 0.80 | 0.83 | 0.82 | 0.24 | 0.58 |
| If it can't arrive by then, please cancel my order and refund me. | delivery status or expedite | 0.00 | 0.02 | 0.02 | 0.01 | 0.00 | 0.00 |
| If it can't arrive by then, I'd like a refund instead. | delivery status or expedite | 0.17 | 0.68 | 0.64 | 0.48 | 0.13 | 0.08 |
| I do NOT want to cancel or get a refund, I just need it here by Monday. | delivery status or expedite | 0.77 | 0.96 | 0.98 | 0.92 | 0.94 | 0.91 |
| Honestly I've given up on it. Please just give me my money back. | cancel and refund | 0.97 | 0.85 | 0.81 | 0.72 | 0.96 | 0.91 |
| Forget it. Cancel the order and refund me today. | cancel and refund | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Can you tell me where it actually is and whether it will make it? | delivery status or expedite | 0.98 | 0.99 | 0.99 | 1.00 | 0.99 | 1.00 |
