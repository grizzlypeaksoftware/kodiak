# E15: Ettin-1B backbone

*Written retroactively on 2026-09-28 from D45 (the bar was set before the run; this file adds the rest of the template).*

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
On never-seen tasks that need knowledge (arXiv fields 0.57, CaseHOLD 0.45, poem sentiment 0.40 forced), large Kodiak trails Qwen3-8B by 18-23 points (D37); never-seen forced is 0.609.

## 2. Why should this change move that failure?
Model size was the biggest lever so far (150M → 400M: +5.6, E5); a 1B encoder carries more knowledge. Same architecture and tokenizer, so nothing else changes.

## 3. Kill line
- Metric: never-seen forced accuracy, eval v0.2
- Baseline: 0.609 ± 0.008 (large v2, 3 seeds)
- Smoke test (≤ 500 steps): kill if validation choice accuracy is more than 0.02 behind large at step 500 (retroactive check: +0.036, pass)
- Full run: keep only if never-seen forced ≥ 0.629; guards: familiar ≥ 0.845, abstain precision ≥ 0.90, report speed

## 4. How is this different from killed ideas?
- Not E9 (mixed/neutral data) because it changes the model, not the data
- Not E11 (unfamiliar-input data) because data tweaks on a fixed model are the dead family; this changes the backbone

## Change (one variable)
Backbone ModernBERT-large (400M) → Ettin-encoder-1B. Also lr 5e-5 → 3e-5 (stability at 1B): a second variable, accepted knowingly; if the result is borderline, rerun at 5e-5 before concluding.

## Budget
- Cloud: $0 · GPU: ~5 hours · Runs: 1 full → 2 confirming seeds only if it clears 0.629

## Approval
Approved: Shane (2026-09-28, "I will go with it")
