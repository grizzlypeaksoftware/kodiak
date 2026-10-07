# E23 result: 3 seeds vs Kodiak-v0.3-1B (lines set before the run)

```
contrastive pair accuracy, step safety + refund, both tests: 0.560, 0.577, 0.560 → mean 0.566 (keep ≥ 0.452; v0.3 mean 0.302)
never-seen forced: 0.695, 0.683, 0.694 → mean 0.691 (line ≥ 0.666) ok
familiar: 0.887, 0.873, 0.873 → mean 0.878 (line ≥ 0.868) ok
abstain precision: 0.938, 0.952, 0.910 → mean 0.933 (line ≥ 0.855) ok
real-anchor score: 0.372, 0.354, 0.371 → mean 0.366 (line ≥ 0.303) ok
wording-trap eval: 0.940, 0.920, 0.900 → mean 0.920 (line ≥ 0.86) ok
flip rate (shortcut guard): 0.322, 0.317, 0.321 → mean 0.320 (line ≤ 0.372) ok
policy contrastive pairs (shortcut guard): 0.633, 0.700, 0.600 → mean 0.644 (line ≥ 0.499) ok
VERDICT: KEEP (3-seed means vs the pre-set lines)
```

## Contrastive tests by kind (report only)

```
reports/preds_contrastive/e23-s0.jsonl
  policy_violation     pairs= 30 item acc=0.817 pair acc=0.633 same answer=0.367
  refund_eligibility   pairs= 50 item acc=0.740 pair acc=0.520 same answer=0.460
  sarcasm              pairs=  7 item acc=0.571 pair acc=0.143 same answer=0.857
  step_safety          pairs= 50 item acc=0.660 pair acc=0.400 same answer=0.460
reports/preds_contrastive/e23-s1.jsonl
  policy_violation     pairs= 30 item acc=0.850 pair acc=0.700 same answer=0.267
  refund_eligibility   pairs= 50 item acc=0.770 pair acc=0.560 same answer=0.420
  sarcasm              pairs=  7 item acc=0.571 pair acc=0.143 same answer=0.857
  step_safety          pairs= 50 item acc=0.670 pair acc=0.360 same answer=0.440
reports/preds_contrastive/e23-s2.jsonl
  policy_violation     pairs= 30 item acc=0.800 pair acc=0.600 same answer=0.333
  refund_eligibility   pairs= 50 item acc=0.710 pair acc=0.440 same answer=0.480
  sarcasm              pairs=  7 item acc=0.643 pair acc=0.286 same answer=0.714
  step_safety          pairs= 50 item acc=0.630 pair acc=0.320 same answer=0.500
reports/preds_contrastive2/e23-s0.jsonl
  refund_eligibility   pairs= 98 item acc=0.816 pair acc=0.673 same answer=0.255
  step_safety          pairs=100 item acc=0.720 pair acc=0.550 same answer=0.320
reports/preds_contrastive2/e23-s1.jsonl
  refund_eligibility   pairs= 98 item acc=0.796 pair acc=0.622 same answer=0.286
  step_safety          pairs=100 item acc=0.800 pair acc=0.650 same answer=0.220
reports/preds_contrastive2/e23-s2.jsonl
  refund_eligibility   pairs= 98 item acc=0.811 pair acc=0.643 same answer=0.265
  step_safety          pairs=100 item acc=0.800 pair acc=0.660 same answer=0.220
```

## Synthetic held-out skills-3 (report only; rewards the old shortcut)

```
reports/preds_skills3/e23-xl-groups-s0.jsonl: skills-2 score 0.879
  long_hallucination                 n= 83 acc=0.904 skill=+0.807
  refund_eligibility                 n= 96 acc=0.927 skill=+0.891
  stance                             n=100 acc=1.000 skill=+1.000
  step_safety                        n=100 acc=0.880 skill=+0.820
reports/preds_skills3/e23-xl-groups-s1.jsonl: skills-2 score 0.845
  long_hallucination                 n= 83 acc=0.880 skill=+0.759
  refund_eligibility                 n= 96 acc=0.917 skill=+0.875
  stance                             n=100 acc=1.000 skill=+1.000
  step_safety                        n=100 acc=0.830 skill=+0.745
reports/preds_skills3/e23-xl-groups-s2.jsonl: skills-2 score 0.863
  long_hallucination                 n= 83 acc=0.892 skill=+0.783
  refund_eligibility                 n= 96 acc=0.948 skill=+0.922
  stance                             n=100 acc=1.000 skill=+1.000
  step_safety                        n=100 acc=0.830 skill=+0.745
```

# Seed comparison: v0.3 (3 seeds) vs E23 (3 seeds)

| Measure | v0.3 (3 seeds) | E23 (3 seeds) | Difference (E23 (3 seeds) − v0.3 (3 seeds)) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.647 ± 0.008 (n=3) | 0.651 ± 0.005 (n=3) | +0.004 |
| Never-seen tasks, forced | 0.687 ± 0.010 (n=3) | 0.691 ± 0.007 (n=3) | +0.004 |
| New never-seen tasks (v0.2), forced | 0.641 ± 0.019 (n=3) | 0.645 ± 0.010 (n=3) | +0.004 |
| Never-seen score error (MAE) | 0.276 ± 0.003 (n=3) | 0.275 ± 0.003 (n=3) | -0.001 |
| Overall accuracy | 0.730 ± 0.008 (n=3) | 0.732 ± 0.006 (n=3) | +0.003 |
| Familiar tasks | 0.879 ± 0.005 (n=3) | 0.878 ± 0.008 (n=3) | -0.001 |
| Calibration error (ECE) | 0.051 ± 0.003 (n=3) | 0.054 ± 0.004 (n=3) | +0.003 |
| Never-seen calibration error (ECE) | 0.076 ± 0.004 (n=3) | 0.082 ± 0.007 (n=3) | +0.006 |
| Abstain precision | 0.931 ± 0.038 (n=3) | 0.933 ± 0.021 (n=3) | +0.003 |
| Constructed unanswerables | 0.922 ± 0.018 (n=3) | 0.928 ± 0.010 (n=3) | +0.006 |
| Banking77 (forced) | 0.835 ± 0.002 (n=3) | 0.817 ± 0.009 (n=3) | -0.017 |
| Bias in Bios (forced) | 0.813 ± 0.016 (n=3) | 0.809 ± 0.013 (n=3) | -0.004 |
| Jailbreak (forced) | 0.889 ± 0.044 (n=3) | 0.925 ± 0.018 (n=3) | +0.036 |
| Poem sentiment, has 'mixed' (forced) | 0.708 ± 0.010 (n=3) | 0.688 ± 0.014 (n=3) | -0.020 |
| Financial tweet sentiment, has 'neutral' (forced) | 0.714 ± 0.009 (n=3) | 0.737 ± 0.013 (n=3) | +0.023 |

± is the standard deviation across seeds (training noise). Same data subset for every seed.

## Where the gain comes from (D70, added after the verdict): pairs a changed-words reader can and can't solve, 3-seed pair accuracy

| Test, kind | Pairs cue words can solve: v0.3 → E23 | Pairs they can't: v0.3 → E23 |
|---|---|---|
| v0.1 step_safety | 0.11 → 0.61 (12) | 0.04 → 0.28 (38) |
| v0.1 refund_eligibility | 0.11 → 0.33 (21) | 0.30 → 0.63 (29) |
| v0.2 step_safety | 0.36 → 0.75 (72) | 0.15 → 0.29 (28) |
| v0.2 refund_eligibility | 0.58 → 0.69 (53) | 0.34 → 0.60 (45) |

Refund gains most where cue words don't help (a real fix). Step safety gains much more on cue-solvable pairs; its gain on the rest (+0.14 to +0.24) is real but smaller. Source: scripts/diff_reader.py.
