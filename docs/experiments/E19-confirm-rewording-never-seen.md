# E19: does training with reworded options raise never-seen accuracy? (confirm E18's side effect)

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
On never-seen tasks (eval v0.2, the primary metric) the current best recipe, E17, scores 0.662 ± 0.012 forced over 3 seeds, with never-seen
calibration error 0.109. E18's single run (E17 + reworded options) scored 0.680 never-seen and 0.094 ECE (D57), but one seed can't separate
that from training noise, so we don't know whether to put rewording into the v0.2 recipe.

## 2. Why should this change move that failure?
Never-seen tasks come with label wordings the model has never seen; training with several wordings of familiar labels should make it rely on
meaning rather than memorized label strings, which is exactly what a never-seen task demands. E18's run moved never-seen +1.6, the new v0.2
tasks +2.1 and calibration error −0.018 in that direction; two more seeds tell us whether it holds.

## 3. Kill line
- Metric: never-seen forced accuracy on eval v0.2, mean of 3 seeds (E18 seed 1 + seeds 0 and 2, identical recipe)
- Baseline: E17 3-seed mean 0.662 ± 0.012 (D53)
- Smoke test (≤ 500 steps): kill if validation choice accuracy is more than 0.02 behind the E17 run of the same seed at step 500
- Full run: keep only if the 3-seed never-seen mean ≥ 0.682 (+2.0, GOAL.md's definition of a win) and the never-seen ECE mean is not worse
  than 0.109; guards: familiar ≥ 0.87, "can't tell" precision mean ≥ 0.86, skills score ≥ 0.95, label-overlap probe mean ≥ 4 of 8

## 4. How is this different from killed ideas?
- Not E18 (reworded options as a wording fix, killed) because E18 was judged on the wording eval; this asks a different, pre-registered
  question (the primary metric) with the confirmation seeds E18 never earned, and the bar is set here, before the seeds run
- Not E9 (mixed/neutral tone batch, killed) because that added examples of an existing decision type on the small model; this adds no
  examples and is measured on the primary metric with 3 seeds

## Change (one variable)
None beyond E18: E18's exact recipe (E17 data + options reworded with p = 0.5), seeds 0 and 2. Compared with E17's three seeds.

## Budget
- Cloud: $0 (wordings already made) · GPU: ~12 h (2 runs) · Runs: seeds 0 and 2 (each with its own step-500 smoke check vs E17's same seed)

## Approval
Approved: Shane (2026-10-01, "I approve E19")
