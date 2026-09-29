# Kodiak: the frozen goal

> **Owner: Shane Larson.** Claude may *propose* changes to this file in chat, but never edits it. Every experiment proposal quotes the
> product sentence below and is judged against the metrics here. Status: **draft for Shane's approval (2026-09-28)**; delete this line to approve.

## The product sentence

Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks)
**fast, cheaply and with honest confidence**, and hand the cases it isn't sure about to a person or an LLM.

## What "better" means for the people using it

1. **More right answers on decisions it has never been trained for** (a new team's labels, zero-shot).
2. **Confidence that means something**, so a team can safely automate the sure answers.
3. **An honest "can't tell"** instead of a guess.
4. **Fast and cheap to run** (CPU is enough).
5. **Easy to teach a team's own decisions** (the fine-tuning kit).

## The metric that matters

- **Primary:** never-seen tasks, forced accuracy, choice questions, frozen eval set v0.2 (`eval:heldout`). Current best: **0.623**
  (accuracy mode, D45); single large model **0.609 ± 0.008** (3 seeds).
- **Guards (must not get worse beyond noise):** familiar tasks accuracy (large 0.855), never-seen calibration error (0.128 single / 0.098
  accuracy mode), abstain precision (≥ 0.90 at the default threshold), speed (report the multiple vs the current model).
- **Targeted fixes** (e.g. a wording trap) may use a named probe as their metric, but must still pass the guards.
- Never trained or tuned on the eval set; thresholds and model selection use validation data only.

## What counts as a win

- **+2.0 points** on the primary metric over the current best of the same size tier (twice the run-to-run noise), or
- a targeted fix that moves its probe clearly (≥ 2 of 8 on the label-overlap probe, all 3 seeds) **and** passes every guard.
- Anything smaller is "no change", however interesting.

## Budgets

- **Cloud money:** ask Shane before any spend. Default cap per experiment: $10. Total budget $535 (≈ $60 spent by 2026-09-28).
- **GPU:** a smoke test (≤ 500 steps, ≤ 1 GPU-hour) needs no approval. **Any full training run needs "Approved: Shane"** in its proposal.
- **Runs per hypothesis:** 1 smoke → 1 full run (1 seed) → 2 confirming seeds only if the full run clears the bar. No re-runs of a killed idea
  without a new reason written in the proposal.

## v0.2 goal (current)

Beat 0.623 never-seen (accuracy mode) or 0.609 per single model with a bigger backbone, ship the fine-tuning kit, and fix the user-found wording
trap without a general cost. No release until then; the Hugging Face previews stay up.
