# E<n>: <short name>

**Product sentence (quoted from docs/GOAL.md):** <paste it>

## 1. What exact failure of the current model does this fix?
<one concrete failure, with the number that shows it (eval slice, probe, user report)>

## 2. Why should this change move that failure?
<the mechanism, in two or three sentences; evidence from the log if any>

## 3. Kill line
- Metric: <primary metric or named probe>
- Baseline: <current value, from docs/GOAL.md or EXPERIMENTS.md>
- Smoke test (≤ 500 steps): kill if <condition vs the baseline run at the same step>
- Full run: keep only if <metric ≥ value>; guards: <familiar / calibration / abstain precision / speed>

## 4. How is this different from killed ideas?
- Not <E#: name> because <reason>
- Not <E#: name> because <reason>

## Change (one variable)
<the single thing that differs from the baseline run; anything else that differs must be listed and justified>

## Budget
- Cloud: $<amount> (ask Shane first) · GPU: <hours> · Runs: smoke → 1 full → 2 confirm only if it clears the bar

## Approval
Approved: <Shane writes "Approved: Shane" here before any full run>
