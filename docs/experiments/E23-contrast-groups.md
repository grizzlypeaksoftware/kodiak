# E23: contrast groups: train step safety and refund so no single field gives the answer away

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
Kodiak-v0.3-1B answers agent step safety and refund eligibility from one field instead of the whole case (D67). On contrastive pairs (the
same case twice, one detail changed, different correct answer; contrastive eval v0.1, 3 seeds) it gets both versions right 0.053 of the time
for step safety (50 pairs) and 0.220 for refund (50 pairs), and gives the same answer to both versions 89% / 71% of the time. A user found it:
`git push origin main` while 3 tests fail → "yes, safe" at 0.97. Our synthetic skills test (0.96 / 0.97) didn't catch it because a
word-counter that reads only the next step passes that test at 0.94 (only the request: 0.95).

## 2. Why should this change move that failure?
The training data teaches the shortcut: a bag-of-words model reading only the next step predicts the E22 step-safety labels at 0.92 (5-fold;
refund, request only: 0.97, policy only: 0.96). Contrast groups put the same next step (or request, or policy) under all three answers, so
the shared field carries no information and the model has to read the other one. Evidence that this works: policy violation, the one kind
whose data a word-counter can't predict (0.64), is the one kind that holds up on contrastive pairs (0.122 in v0.2 → 0.567 in v0.3).

## 2b. Prediction and attempt (rules 4 and 6, D65)
- Prediction: mean contrastive pair accuracy (step safety + refund, contrastive eval v0.2) rises by about +0.20 to +0.40 over v0.3, toward
  policy violation's 0.567; synthetic skills scores for the two kinds may drop a little (the old test rewards the shortcut). Other metrics
  flat (only 5,000 of ~90k training examples change).
- Zero-training check: done. Contrastive v0.1 on v0.2 and v0.3 (3 seeds each); word-counter on training data and tests
  (scripts/shortcut_check.py); the pilot must pass the word-counter line below before any batch is bought.
- Attempt: 1 of 2 on single-field shortcuts in synthetic skills data (a new problem, found in D67; not the wording trap).

## 3. Kill line
- Metric: **contrastive pair accuracy** on step safety + refund eligibility, pooled over both contrastive tests (298 pairs, 596 items;
  never trained on): v0.1 (gpt-oss writes, DeepSeek checks; 50 + 50 pairs) and v0.2 (DeepSeek writes, gpt-oss checks, the reverse of the
  training data's roles; 100 + 98 pairs). Pooled because the two tests differ a lot in difficulty for v0.3 (below) and neither alone is the
  full picture; a word-counter trained on E22 data gets pair accuracy ≤ 0.09 on both. Reported, not gating: each test and kind separately,
  synthetic skills tests.
- Baseline: v0.3 (E22 runs, seeds 0 / 1 / 2), measured 2026-10-06 before any training: pooled 0.312 / 0.282 / 0.312, **mean 0.302,
  SD 0.017** (v0.1 test: step 0.053, refund 0.220; v0.2 test: step 0.303, refund 0.470). Keep line: 3-seed mean **≥ 0.452** (+0.15).
- Pilot (before buying the batch): word-counter on the pilot, each single field, 5-fold accuracy ≤ 0.65 for both kinds (E22 data: 0.85-0.97).
  **Result (2026-10-06, $0.10, 120 groups): passed.** Step safety task 0.38 / next step 0.31; refund policy 0.49 / request 0.58. E22 data
  at the same size (100 per kind): 0.76 / 0.81 and 0.82 / 0.91. Kept groups: step safety 35 of 60, refund 48 of 60.
- Smoke test (≤ 500 steps): kill if validation choice accuracy is more than 0.02 behind the v0.3 run of the same seed at step 500
- Full run: keep only if the 3-seed mean meets the keep line; guards on 3-seed means, v0.3 lines from docs/NOISE.md: never-seen forced
  ≥ 0.666, familiar ≥ 0.868, abstain precision ≥ 0.855, real-anchor score ≥ 0.303, wording-trap eval ≥ 0.860
- Noise: guard lines from docs/NOISE.md (baseline mean − 2 SD, judged on 3-seed means; one run rejects only past 3 SD); the gating test has
  596 items; 5 guards. Seed 1 runs first; seeds 0 and 2 run unless seed 1 is more than 3 SD past a guard line or shows no target gain.
- Shortcut guards: (rule 7) flip rate on the wording eval ≤ 0.372 (v0.3 line, NOISE.md); contrastive test: policy-violation pair accuracy on contrastive v0.1
  ≥ 0.499 (NOISE.md), and the target itself is a contrastive test

## 4. How is this different from killed ideas?
- Not E18 (more reworded data for the wording trap, killed) or the "small data tweaks" dead family: this doesn't add more of the same
  examples; it changes their structure so a known, measured shortcut (word-counter 0.92-0.97) stops working, at the same example count
- Not E20 (consistency loss, killed): no new loss; the model sees ordinary single examples, only the data's information content changes

## Change (one variable)
Training data: the E22 recipe (v0.3) with its step-safety and refund examples (2,500 each, single examples) **replaced** by 2,500 each from
contrast groups (scripts/build_groups.py: one writer call, a shared field, one version per answer, each version checked blind). Same count,
backbone, steps, learning rate, seeds and everything else as E22.

## Budget
- Cloud: $12 cap (contrastive v0.2 ~$0.65; pilot ≤ $1; batch sized toward the cap, extra groups banked)
- GPU: ~5 h for seed 1, +10 h for seeds 0 and 2 · Runs: test set + baseline (3 seeds, free) → pilot + word-counter → batch → smoke →
  seed 1 → seeds 0 and 2

## Approval
Approved: Shane (2026-10-06, "approved!  how exciting")
