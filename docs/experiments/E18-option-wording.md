# E18: option-wording robustness

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
Kodiak's answer depends on how the options are worded, not only on what they mean. On PhishNChips (D56), the two-option "verdict" question with
long descriptions flips to "phishing" on 87-99% of emails (XL v2 seed 2, all three E17 seeds), while three other wordings of the same question
about the same emails say "safe" (click = yes on 61-98%). The skill drops 0.28 → 0.08 across seeds. Teams write their own options, often as
sentences, so the same decision must not change with the wording. It is the same family as the open wording-trap goal in GOAL.md.

## 2. Why should this change move that failure?
84% of the option texts Kodiak trains on are 1-3 words and only 3% are 9+ words (sample of the public training data), and no question is ever
seen with two different wordings of the same options, so nothing teaches the model that the meaning, not the surface, decides. Training on
the same examples with options re-worded (short label, one-sentence description, "Yes. ..." / "No. ..." style, synonyms), with the answer
unchanged by construction, should teach that invariance. Changing the data kind is what has worked before (E3, E17).

## 3. Kill line
- Metric: **wording consistency** on a new held-out wording eval: never-seen eval v0.2 questions (tasks never trained on) each asked with
  3 wordings of the same options (the original plus 2 written for this eval, checked to mean the same; separate from any training wording);
  consistency = share of questions whose forced answer is the same under all 3 wordings. Secondary: forced accuracy averaged over the wordings.
- Baseline: E17 seed 1 on the wording eval, measured before training (expected well below 1.0).
- Smoke test (≤ 500 steps): kill if validation choice accuracy is more than 0.02 behind the E17 seed-1 run at step 500
- Full run: keep only if wording consistency rises ≥ 10 points over the baseline and reworded-option accuracy rises ≥ 3 points; guards:
  never-seen forced (eval v0.2, original wording) ≥ 0.645, familiar ≥ 0.87, "can't tell" precision not below 0.86, skills score ≥ 0.95
  (keeps E17), label-overlap probe not below 4 of 8.

## 4. How is this different from killed ideas?
- Not E12/E13 (Returns Desk simulator, parked) because those changed the *state* content (new scenarios) on the small model and cost ~1 point
  never-seen; this keeps every state and answer identical and changes only how the options are worded, on XL.
- Not E9 (mixed/neutral tone batch, killed) because that added more examples of one existing decision type; this adds no new examples or
  decision types, only alternative wordings of existing options, and is judged on a test built for that failure.

## Change (one variable)
Training data: E17's mix (public + v2.0 + 10k skills), where each question's options are swapped for an alternative wording with
probability 0.5 (the same option ids and answer; a different text). Alternative wordings are written once per label set (each public task's
label set and the fixed skills label sets) by the open-weight writer and checked by the checker to mean the same as the original; per-example
options in the v2.0 data keep their wording. Same backbone, recipe, steps, learning rate and seed as E17 seed 1. Wordings for the wording eval
are written separately, for eval tasks only, and are never trained on.

## Budget
- Cloud: $5 (alternative wordings for ~60 training label sets + ~15 eval label sets; ~$0.50 expected; cap $5) · GPU: ~6 h (1 run), +12 h
  only if it clears the bar · Runs: wordings → wording eval + Shane spot-check → baseline → smoke → 1 full → 2 confirm only if it clears the bar

**Baseline measured (2026-10-01, before training):** E17 seed 1 on the wording eval (640 questions × 3 wordings): consistency **0.621**, accuracy with reworded options **0.681** (original options 0.717). Keep lines: consistency **≥ 0.721**, reworded accuracy **≥ 0.711**. Details: reports/e18-wording-baseline.md. Wording eval spot-checked by Shane: OK (2026-10-01).

## Approval
Approved: Shane (2026-10-01, "approved")
