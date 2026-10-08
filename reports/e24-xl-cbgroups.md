# E24 result: 3 seeds vs E23 (lines set before the run)

```
cue-hard pair accuracy (contrastive v0.3), step safety + refund: 0.527, 0.505, 0.440 → mean 0.491 (keep ≥ 0.443; E23 mean 0.363)
never-seen forced: 0.697, 0.676, 0.682 → mean 0.685 (line ≥ 0.677) ok
familiar: 0.882, 0.873, 0.884 → mean 0.880 (line ≥ 0.862) ok
abstain precision: 0.967, 0.972, 0.883 → mean 0.941 (line ≥ 0.891) ok
real-anchor score: 0.349, 0.359, 0.364 → mean 0.357 (line ≥ 0.345) ok
wording-trap eval: 0.900, 0.880, 0.900 → mean 0.893 (line ≥ 0.88) ok
flip rate (shortcut guard): 0.302, 0.327, 0.319 → mean 0.316 (line ≤ 0.352) ok
policy contrastive pairs (shortcut guard): 0.600, 0.633, 0.533 → mean 0.589 (line ≥ 0.542) ok
refund cue-free pairs (shortcut guard): 0.716, 0.757, 0.703 → mean 0.725 (line ≥ 0.51) ok
VERDICT: KEEP (3-seed means vs the pre-set lines)
```

## Contrastive tests by kind (report only)

```
reports/preds_contrastive/e24-s0.jsonl
  policy_violation     pairs= 30 item acc=0.800 pair acc=0.600 same answer=0.367
  refund_eligibility   pairs= 50 item acc=0.890 pair acc=0.800 same answer=0.180
  sarcasm              pairs=  7 item acc=0.571 pair acc=0.143 same answer=0.857
  step_safety          pairs= 50 item acc=0.630 pair acc=0.320 same answer=0.500
reports/preds_contrastive/e24-s1.jsonl
  policy_violation     pairs= 30 item acc=0.817 pair acc=0.633 same answer=0.367
  refund_eligibility   pairs= 50 item acc=0.890 pair acc=0.800 same answer=0.180
  sarcasm              pairs=  7 item acc=0.571 pair acc=0.143 same answer=0.857
  step_safety          pairs= 50 item acc=0.600 pair acc=0.300 same answer=0.520
reports/preds_contrastive/e24-s2.jsonl
  policy_violation     pairs= 30 item acc=0.767 pair acc=0.533 same answer=0.367
  refund_eligibility   pairs= 50 item acc=0.880 pair acc=0.780 same answer=0.200
  sarcasm              pairs=  7 item acc=0.643 pair acc=0.286 same answer=0.714
  step_safety          pairs= 50 item acc=0.660 pair acc=0.440 same answer=0.380
reports/preds_contrastive2/e24-s0.jsonl
  refund_eligibility   pairs= 98 item acc=0.878 pair acc=0.765 same answer=0.143
  step_safety          pairs=100 item acc=0.755 pair acc=0.510 same answer=0.450
reports/preds_contrastive2/e24-s1.jsonl
  refund_eligibility   pairs= 98 item acc=0.883 pair acc=0.765 same answer=0.122
  step_safety          pairs=100 item acc=0.670 pair acc=0.430 same answer=0.430
reports/preds_contrastive2/e24-s2.jsonl
  refund_eligibility   pairs= 98 item acc=0.837 pair acc=0.684 same answer=0.224
  step_safety          pairs=100 item acc=0.755 pair acc=0.520 same answer=0.390
reports/preds_contrastive3/e24-s0.jsonl
  refund_eligibility   pairs=128 item acc=0.809 pair acc=0.625 same answer=0.234
  step_safety          pairs= 54 item acc=0.602 pair acc=0.296 same answer=0.537
reports/preds_contrastive3/e24-s1.jsonl
  refund_eligibility   pairs=128 item acc=0.793 pair acc=0.594 same answer=0.266
  step_safety          pairs= 54 item acc=0.611 pair acc=0.296 same answer=0.537
reports/preds_contrastive3/e24-s2.jsonl
  refund_eligibility   pairs=128 item acc=0.742 pair acc=0.508 same answer=0.359
  step_safety          pairs= 54 item acc=0.574 pair acc=0.278 same answer=0.556
```

## Synthetic held-out skills-3 (report only; rewards the old shortcut)

```
reports/preds_skills3/e24-xl-cbgroups-s0.jsonl: skills-2 score 0.797
  long_hallucination                 n= 83 acc=0.892 skill=+0.783
  refund_eligibility                 n= 96 acc=0.844 skill=+0.766
  stance                             n=100 acc=1.000 skill=+1.000
  step_safety                        n=100 acc=0.760 skill=+0.640
reports/preds_skills3/e24-xl-cbgroups-s1.jsonl: skills-2 score 0.839
  long_hallucination                 n= 83 acc=0.916 skill=+0.831
  refund_eligibility                 n= 96 acc=0.823 skill=+0.734
  stance                             n=100 acc=1.000 skill=+1.000
  step_safety                        n=100 acc=0.860 skill=+0.790
reports/preds_skills3/e24-xl-cbgroups-s2.jsonl: skills-2 score 0.806
  long_hallucination                 n= 83 acc=0.855 skill=+0.711
  refund_eligibility                 n= 96 acc=0.854 skill=+0.781
  stance                             n=100 acc=1.000 skill=+1.000
  step_safety                        n=100 acc=0.820 skill=+0.730
```

# Seed comparison: E23 (3 seeds) vs E24 (3 seeds)

| Measure | E23 (3 seeds) | E24 (3 seeds) | Difference (E24 (3 seeds) − E23 (3 seeds)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.651 ± 0.005 (n=3) | 0.646 ± 0.012 (n=3) | -0.005 |
| Never-seen tasks, forced | 0.691 ± 0.007 (n=3) | 0.685 ± 0.011 (n=3) | -0.006 |
| New never-seen tasks (v0.2), forced | 0.645 ± 0.010 (n=3) | 0.639 ± 0.013 (n=3) | -0.006 |
| Never-seen score error (MAE) | 0.275 ± 0.003 (n=3) | 0.276 ± 0.004 (n=3) | +0.000 |
| Overall accuracy | 0.732 ± 0.006 (n=3) | 0.729 ± 0.008 (n=3) | -0.003 |
| Familiar tasks | 0.878 ± 0.008 (n=3) | 0.880 ± 0.006 (n=3) | +0.002 |
| Calibration error (ECE) | 0.054 ± 0.004 (n=3) | 0.046 ± 0.005 (n=3) | -0.008 |
| Never-seen calibration error (ECE) | 0.082 ± 0.007 (n=3) | 0.070 ± 0.008 (n=3) | -0.012 |
| Abstain precision | 0.933 ± 0.021 (n=3) | 0.941 ± 0.050 (n=3) | +0.007 |
| Constructed unanswerables | 0.928 ± 0.010 (n=3) | 0.922 ± 0.033 (n=3) | -0.006 |
| Banking77 (forced) | 0.817 ± 0.009 (n=3) | 0.813 ± 0.008 (n=3) | -0.004 |
| Bias in Bios (forced) | 0.809 ± 0.013 (n=3) | 0.817 ± 0.019 (n=3) | +0.008 |
| Jailbreak (forced) | 0.925 ± 0.018 (n=3) | 0.907 ± 0.018 (n=3) | -0.019 |
| Poem sentiment, has 'mixed' (forced) | 0.688 ± 0.014 (n=3) | 0.697 ± 0.003 (n=3) | +0.009 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.737 ± 0.013 (n=3) | 0.749 ± 0.010 (n=3) | +0.012 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.
