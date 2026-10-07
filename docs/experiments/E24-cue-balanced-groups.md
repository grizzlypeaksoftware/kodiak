# E24: cue-balanced contrast groups: make step safety read the facts, not the hedge words

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
E23 (the v0.4 candidate, D71) learned part of step safety from hedge words. Split by whether a reader that sees only the changed words can
solve a contrastive pair: on pairs it can, E23 rose 0.36 → 0.75 (contrastive v0.2) and 0.11 → 0.61 (v0.1); on pairs it can't, only
0.15 → 0.29 and 0.04 → 0.28 (3 seeds, D70). The training groups carry the cue: "but" appears only in the "ask first" version in 98% of
1,063 groups, "before" 93%, "wants" 86%. Found by a Hugging Face user before E23's verdict.

## 2. Why should this change move that failure?
E23 showed the mechanism works when the cue is absent: refund, whose groups carried fewer hedge cues, gained most on cue-free pairs
(0.34 → 0.60). Cue-balanced groups require every version of a group to contain the same connective and hedge words (scripts/build_groups_cues.py;
groups that differ are dropped before checking), so the only thing that separates the answers is the facts. Pilot (D70 check, 129 groups,
$0.37): the hedge cues are gone (the most answer-tied changed words are now facts such as "rm -rf" and "overwrite"); refund's changed-words
reader falls 0.80 → 0.51 at the same size (majority 0.40); step safety's stays 0.63, now through content words.

## 2b. Prediction and plan (rules 4-6, D65/D68)
- Prediction: on cue-hard pairs (contrastive v0.3), +0.08 to +0.20 over E23 for step safety, refund flat to slightly up. Evidence: E23's
  cue-free gain was +0.14 / +0.24 for step safety and +0.26 / +0.33 for refund; with the hedge shortcut removed, more of the training
  signal has to go through the facts. Pair accuracy on the old v0.2 step test may fall (72 of its 100 pairs are cue-solvable).
- Zero-training check: done. Cue split of E23 vs v0.3 (D70); changed-words reader on the E23 groups (0.87 / 0.92) and on the pilot.
- Time box: shortcuts in step safety: 3 days from 2026-10-07 (set by Shane; ends 2026-10-10)
- If it passes: E24 becomes the v0.4 release (release audit first), with step safety described by its cue-hard numbers.
- If it fails: release v0.4 from E23 with step safety marked "partly hedge words, not a safety control", and stop working on step safety
  with synthetic data; the next step would be human-written or real agent traces, decided with Shane. No variation of the groups.

## 3. Kill line
- Metric: **pair accuracy on contrastive v0.3**, step safety + refund pooled: pairs written by DeepSeek-V3.2 and checked by gpt-oss-120b,
  every answer pair (including "never") attempted and capped equally, then filtered to the pairs a changed-words reader trained on our
  training groups gets wrong (scripts/filter_cue_hard.py). Never trained on. Reported, not gating: each kind; contrastive v0.1 / v0.2
  (125 of their 298 pairs are cue-solvable, so a drop there can mean the shortcut is gone).
- Baseline: (measured 2026-10-07, before training) contrastive v0.3 has 182 cue-hard pairs (step safety 54, refund 128; built from 302
  checked pairs, $2.07; "never" is 17 of 108 step-safety sides: better than v0.2's 7 of 200, not balanced, because the checker rarely
  agrees on "never"). E23 seeds 0 / 1 / 2: 0.330 / 0.396 / 0.363, **mean 0.363, SD 0.033** (step safety 0.241 / 0.426 / 0.315; refund
  0.367 / 0.383 / 0.383). v0.3 for reference: 0.231. Keep line: 3-seed mean **≥ 0.443** (+0.08, about 4 standard errors of a 3-seed mean).
  Step safety alone (54 pairs) is reported, not gating.
- Smoke test (≤ 500 steps): kill if validation choice accuracy is more than 0.02 behind the E23 run of the same seed at step 500
- Full run: keep only if the 3-seed mean meets the keep line; guards on 3-seed means, E23 lines from docs/NOISE.md: never-seen forced
  ≥ 0.677, familiar ≥ 0.862, abstain precision ≥ 0.891, real-anchor score ≥ 0.345, wording-trap eval ≥ 0.880
- Noise: guard lines from docs/NOISE.md (baseline mean − 2 SD, judged on 3-seed means; one run rejects only past 3 SD); the gating test has
  ≥ 100 pairs; 5 guards. Seed 1 runs first; seeds 0 and 2 run unless seed 1 is more than 3 SD past a guard line or shows no target gain.
- Shortcut guards: (rule 7) flip rate on the wording eval ≤ 0.352 (E23 mean 0.320 + 2 × the SD pooled over v0.3 and E23, 0.016, because E23's three-seed SD of 0.003 is too small to trust); contrastive test: policy-violation pairs ≥ 0.542 (NOISE.md), and refund pairs on the 74 cue-free pairs of v0.1 + v0.2 ≥ 0.510 (E23: 0.635 / 0.649 / 0.554, mean 0.613, SD 0.051)

## 4. How is this different from killed ideas?
- Not E18 (more reworded data, killed): no more data of the same kind; the same count of examples, with one measured cue removed
- Not E20 (consistency loss, killed): no new loss; only which examples the writer is allowed to produce changes

## Change (one variable)
Training data: the E23 recipe with its contrast groups (2,500 each, step safety and refund) **replaced** by 2,500 each from cue-balanced
groups (scripts/build_groups.py --cue-balanced: the writer is asked to keep the same linking words, and any group whose versions differ in
their connective or hedge words is dropped). Same count, backbone, steps, learning rate, seeds and everything else as E23.

## Budget
- Cloud: $14 cap (pilot $0.45; batch ≤ $11; contrastive v0.3 ~$2)
- GPU: ~5 h for seed 1, +10 h for seeds 0 and 2 · Runs: test + baseline (E23, free) → batch → smoke → seed 1 → seeds 0 and 2

## Approval
Approved: <Shane writes "Approved: Shane" here before any full run>
