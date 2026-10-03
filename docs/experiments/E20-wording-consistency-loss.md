# E20: wording-consistency loss (v0.3's main goal)

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
Kodiak-v0.2-1B still answers differently when the same options are worded differently: on the held-out wording eval (640 never-seen
questions × 3 wordings) it gives the same answer under all three wordings only **0.676-0.679** of the time (3 seeds, D58), and accuracy with
reworded options is 0.692 (mean) vs 0.721 with the original wording. On real data this shows up as PhishNChips, where a two-option question
with long descriptions flips to "phishing" on 91-99% of emails while other wordings of the same question say "safe" (D56). This is the
v0.3 goal in GOAL.md and the first known limit in the model card.

## 2. Why should this change move that failure?
E18/E19 trained on reworded options as *independent* examples: the model saw each wording separately, never the two side by side, so
nothing told it that its answers to them must agree. A consistency loss pairs them: an example and its reworded twin go into the same batch,
and the loss adds a penalty when the two answer distributions differ (symmetric KL over the options, plus the "can't tell" probability).
This is the standard recipe for invariance (consistency regularization, as in UDA and R-Drop) and targets the measured failure directly,
rather than hoping it emerges from more varied data.

## 3. Kill line
- Metric: wording consistency on the wording eval v0.1 (share of questions answered the same under all 3 wordings); secondary: accuracy
  with reworded options (mean of description and paraphrase)
- Baseline: E19 recipe (Kodiak-v0.2-1B), 3-seed means: consistency 0.678, reworded accuracy 0.692; seed 1: 0.678 and 0.679
- Smoke test (≤ 500 steps): kill if validation choice accuracy is more than 0.02 behind the E18 seed-1 run at step 500
- Full run: keep only if consistency ≥ 0.75 (+7 points; the 3 seeds of the baseline span only 0.676-0.679) and reworded accuracy ≥ 0.712;
  guards: never-seen forced (eval v0.2) ≥ 0.679 (baseline mean minus one seed SD), familiar ≥ 0.87, "can't tell" precision ≥ 0.86,
  skills score ≥ 0.95, label-overlap probe ≥ 5 of 8. Then 2 confirming seeds.

## 4. How is this different from killed ideas?
- Not E18 (reworded options as a wording fix, killed: consistency 0.678 < 0.721) because E18 only added varied wordings as separate
  examples; this pairs the wordings in one batch and trains on their *agreement* with an explicit loss term
- Not E12/E13 (Returns Desk simulator for the wording trap, parked: probe up, ~1 point general cost) because those added new states on the
  small model; this adds no new data and no new states, only a loss between two wordings of the same example, on the 1B model

## Change (one variable)
The consistency loss: with probability 0.25 a sampled example gets a reworded twin (same state, same answers, options in a different
wording style from the checker-verified table) packed into the same batch, and the loss adds λ = 1.0 × symmetric KL between the twins'
per-question answer distributions (choice probabilities and p(can't tell)). The twin also gets the ordinary loss. Everything else is the
E19 recipe (E17 data + reworded options p = 0.5, seed 1, 6,000 steps, same learning rate). Twins add ~25% more examples per batch's token
budget share, so slightly fewer distinct examples per step; that is part of the variable and is listed here.

## Budget
- Cloud: $0 (wordings already made) · GPU: ~6 h (1 run), +12 h only if it clears the bar · Runs: smoke → 1 full → 2 confirm

## Approval
Approved: <Shane writes "Approved: Shane" here before any full run>
