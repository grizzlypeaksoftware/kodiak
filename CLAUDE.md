# Working on Kodiak (read first, every session)

Kodiak is an open, encoder-only decision model by Cortex Agent LLC (owner: Shane Larson). The goal, metrics and budgets are frozen in
**docs/GOAL.md** (Shane owns it; propose changes, never edit it). Every experiment ever run is in **docs/EXPERIMENTS.md** (append-only).

## Before proposing any experiment
1. Re-read docs/GOAL.md and docs/EXPERIMENTS.md. Quote the product sentence in the proposal.
2. Write the proposal from docs/experiments/TEMPLATE.md: the exact failure it fixes, why it should work, a numeric kill line set **before**
   the run, one variable, a budget, and two killed ideas it is not repeating. Check the "Dead families" list.
3. `uv run python scripts/gate.py docs/experiments/E<n>-*.md` must print OK. A smoke test (≤ 500 steps) may then run;
   `scripts/smoke_check.py` must pass before a full run; a full run needs `Approved: Shane` in the file (`gate.py --full`).
4. Give Shane options with reasons, and a recommendation. Ask before spending any money.

## After a result
Append the row to docs/EXPERIMENTS.md (verdict keep / kill / park), record the decision in docs/DECISIONS.md, and update the dashboard
(docs/progress.json: queue, experiments, milestones). Check running jobs promptly; don't estimate from memory.

## Standing rules
- Never train or tune on the eval sets; thresholds and model selection use validation data only.
- Three seeds before claiming a small effect; one run is enough to reject or to justify confirming a big one.
- Permissive licenses only (data, teachers, backbones). Never print API keys.
- Commit as Shane Larson <shane@grizzlypeaksoftware.com>; keep scope tight: do what was asked, propose extras in one line.
