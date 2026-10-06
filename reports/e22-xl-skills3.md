# E22 result: 3 seeds vs Kodiak-v0.2-1B (lines set before the run)

```
real-anchor score: 0.333, 0.353, 0.387 → mean 0.358 (keep ≥ 0.311; v0.2 mean 0.211)
never-seen forced: 0.694, 0.675, 0.691 → mean 0.687 (line ≥ 0.673) ok
familiar: 0.884, 0.873, 0.879 → mean 0.879 (line ≥ 0.871) ok
abstain precision: 0.943, 0.961, 0.888 → mean 0.931 (line ≥ 0.854) ok
ranking: 0.532, 0.583, 0.519 → mean 0.545 (line ≥ 0.542) ok
wording-trap eval: 0.920, 0.900, 0.880 → mean 0.900 (line ≥ 0.806) ok
VERDICT: KEEP (3-seed means vs the pre-set lines)
```

## Synthetic held-out skills (report only)

```
reports/preds_skills3/e22-xl-skills3-s0.jsonl: skills-2 score 0.943
  long_hallucination                 n= 83 acc=0.892 skill=+0.783
  pairwise_judge                     n=100 acc=0.920 skill=+0.880
  policy_violation                   n=100 acc=1.000 skill=+1.000
  refund_eligibility                 n= 96 acc=0.969 skill=+0.953
  sarcasm                            n=100 acc=1.000 skill=+1.000
  stance                             n=100 acc=1.000 skill=+1.000
  step_safety                        n=100 acc=0.990 skill=+0.985
reports/preds_skills3/e22-xl-skills3-s1.jsonl: skills-2 score 0.949
  long_hallucination                 n= 83 acc=0.904 skill=+0.807
  pairwise_judge                     n=100 acc=0.930 skill=+0.895
  policy_violation                   n=100 acc=1.000 skill=+1.000
  refund_eligibility                 n= 96 acc=0.990 skill=+0.984
  sarcasm                            n=100 acc=1.000 skill=+1.000
  stance                             n=100 acc=1.000 skill=+1.000
  step_safety                        n=100 acc=0.970 skill=+0.955
reports/preds_skills3/e22-xl-skills3-s2.jsonl: skills-2 score 0.949
  long_hallucination                 n= 83 acc=0.904 skill=+0.807
  pairwise_judge                     n=100 acc=0.970 skill=+0.955
  policy_violation                   n=100 acc=0.990 skill=+0.988
  refund_eligibility                 n= 96 acc=0.969 skill=+0.953
  sarcasm                            n=100 acc=1.000 skill=+1.000
  stance                             n=100 acc=1.000 skill=+1.000
  step_safety                        n=100 acc=0.960 skill=+0.940
```

## Real-data probes incl. aspect sentiment (report only)

```
reports/preds_probes/e22-s0-real.jsonl: skills-2 score 0.468
  aspect_sentiment                   n=100 acc=0.750 skill=+0.667
  long_hallucination                 n=100 acc=0.700 skill=+0.400
  stance                             n=102 acc=0.559 skill=+0.338
reports/preds_probes/e22-s1-real.jsonl: skills-2 score 0.475
  aspect_sentiment                   n=100 acc=0.770 skill=+0.693
  long_hallucination                 n=100 acc=0.690 skill=+0.380
  stance                             n=102 acc=0.569 skill=+0.353
reports/preds_probes/e22-s2-real.jsonl: skills-2 score 0.515
  aspect_sentiment                   n=100 acc=0.770 skill=+0.693
  long_hallucination                 n=100 acc=0.720 skill=+0.440
  stance                             n=102 acc=0.608 skill=+0.412
```

# Seed comparison: v0.2 (3 seeds) vs E22 (3 seeds)

| Measure | v0.2 (3 seeds) | E22 (3 seeds) | Difference (E22 (3 seeds) − v0.2 (3 seeds)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.645 ± 0.010 (n=3) | 0.647 ± 0.008 (n=3) | +0.002 |
| Never-seen tasks, forced | 0.689 ± 0.008 (n=3) | 0.687 ± 0.010 (n=3) | -0.002 |
| New never-seen tasks (v0.2), forced | 0.644 ± 0.010 (n=3) | 0.641 ± 0.019 (n=3) | -0.003 |
| Never-seen score error (MAE) | 0.274 ± 0.003 (n=3) | 0.276 ± 0.003 (n=3) | +0.002 |
| Overall accuracy | 0.729 ± 0.006 (n=3) | 0.730 ± 0.008 (n=3) | +0.000 |
| Familiar tasks | 0.877 ± 0.003 (n=3) | 0.879 ± 0.005 (n=3) | +0.001 |
| Calibration error (ECE) | 0.056 ± 0.007 (n=3) | 0.051 ± 0.003 (n=3) | -0.005 |
| Never-seen calibration error (ECE) | 0.085 ± 0.009 (n=3) | 0.076 ± 0.004 (n=3) | -0.009 |
| Abstain precision | 0.880 ± 0.013 (n=3) | 0.931 ± 0.038 (n=3) | +0.051 |
| Constructed unanswerables | 0.948 ± 0.008 (n=3) | 0.922 ± 0.018 (n=3) | -0.026 |
| Banking77 (forced) | 0.821 ± 0.005 (n=3) | 0.835 ± 0.002 (n=3) | +0.013 |
| Bias in Bios (forced) | 0.811 ± 0.010 (n=3) | 0.813 ± 0.016 (n=3) | +0.003 |
| Jailbreak (forced) | 0.896 ± 0.022 (n=3) | 0.889 ± 0.044 (n=3) | -0.007 |
| Poem sentiment, has 'mixed' (forced) | 0.698 ± 0.019 (n=3) | 0.708 ± 0.010 (n=3) | +0.009 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.728 ± 0.018 (n=3) | 0.714 ± 0.009 (n=3) | -0.013 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
