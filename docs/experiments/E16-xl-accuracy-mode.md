# E16: 1B accuracy mode (average the three Ettin-1B runs)

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
The 1B model's "can't tell" precision is 0.868 ± 0.007 on eval v0.2, below the 0.90 guard on all three seeds (D47): when it abstains it is wrong 13% of the time.

## 2. Why should this change move that failure?
Independently trained runs are overconfident in different places; averaging their calibrated answers cancelled much of it for large (abstain precision 0.84 → 0.94, never-seen +1.4, E6/E14). The three 1B runs already exist.

## 3. Kill line
- Metric: "can't tell" precision on eval v0.2 (threshold from the validation rule, D45 addendum)
- Baseline: 0.868 (1B single, 3-seed mean); never-seen forced 0.659
- Smoke test (≤ 500 steps): kill if not applicable (no training); instead kill if the validation-rule threshold cannot reach 0.90 validation precision
- Full run: keep only if "can't tell" precision ≥ 0.90 and never-seen forced ≥ 0.659; guards: familiar ≥ 0.871, never-seen ECE ≤ 0.113, speed reported (expect ~3 × 38 ms)

## 4. How is this different from killed ideas?
- Not E8 (distilling the ensemble into small) because nothing is trained: the ensemble itself is evaluated
- Not E11 (unfamiliar-input data for calibration) because it changes no data; it averages existing models

## Change (one variable)
Serving: three 1B runs averaged instead of one; nothing else changes.

## Budget
- Cloud: $0 · GPU: < 1 hour of evaluation · Runs: none

## Approval
Approved: Shane (2026-09-29, "Go with A and then B")
