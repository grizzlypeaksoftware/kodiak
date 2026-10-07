# Kodiak: the frozen goal

> **Owner: Shane Larson.** Claude may *propose* changes to this file in chat, but never edits it. Every experiment proposal quotes the
> product sentence below and is judged against the metrics here. Status: **approved by Shane (2026-09-30)**.

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

- **Primary:** never-seen tasks, forced accuracy, choice questions, frozen eval set v0.2 (`eval:heldout`). Current best: **0.689 ± 0.008**
  (E17 skills + reworded options, 3 seeds, D58); before it XL v2 0.659 ± 0.013 (D47), large accuracy mode 0.623 (D45), single large 0.609.
- **Guards (must not get worse beyond noise; Shane, 2026-10-04, D65):** familiar tasks, never-seen calibration error, abstain precision
  (target ≥ 0.90), ranking (`aurc_gap_closed`, never-seen; added 2026-10-03 after a Hugging Face reviewer, D60), wording consistency and the 100-item wording-trap eval. **Each guard line comes from
  docs/NOISE.md:** the current model's 3-seed mean minus 2 SD (plus 2 SD for lower-is-better), judged on the new experiment's 3-seed mean; one
  run alone rejects only past 3 SD. Re-measure the table when the baseline changes. Speed: report the multiple vs the current model (~38 ms GPU).
- **Every experiment carries two shortcut guards (Shane, 2026-10-06, D67):** the **flip rate** on the wording eval (share of questions whose
  answer changes when only the option wording changes; line from docs/NOISE.md) and, for any skill trained on synthetic data, a
  **contrastive test** (pairs where the same input appears under different answers because of one detail), on which a keyword shortcut
  scores about chance. They count on top of the ≤ ~5 other guards.
- **Gate tests need ≥ ~100 items.** Small probes (e.g. the 8-sentence label-overlap probe) are reported but never decide an experiment.
- **Targeted fixes** (e.g. a wording trap) may use a named test of ≥ ~100 items as their metric, but must still pass the guards.
- Never trained or tuned on the eval set; thresholds and model selection use validation data only.

## The ambition

Frontier-class in its class: a best-in-class decision model, built with guerrilla ML engineering (small budgets, sharp experiments, open
tools). The strategy and the primary metric above stay the same.

## Public comparison: the Decision Index

- The public Decision Index (github.com/apolinario/decision-index) is one of our benchmark comparison tools. It shows where Kodiak stands
  against other decision models, and its report card points at the skills to train next.
- It does not replace the primary metric: a change still has to win on the frozen eval v0.2 and pass the guards.
- Never train or tune on its questions; data built for its skills comes from our own generators (as in E17).
- Current (preliminary, not submitted): **17.19**, #48 of 71, 5th among models ≤ 2B (D51). Submit only with Shane's OK.

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

Status (2026-09-30): bigger backbone **done** (XL 0.659, D47); fine-tuning kit **done**; wording trap **open** (E12/E13 parked: probe up,
~1 point general cost); abstain precision 0.90 **open** for XL (E16 missed it).

**Decision (Shane, 2026-10-02): ship v0.2 now.** The recipe is E17 skills + reworded options (never-seen 0.689, D58). The wording trap
improved (consistency 0.62 → 0.68, probe 4.7 → 5.7 of 8) but isn't fixed; it moves to the **v0.3 goal**, with "can't tell" precision ≥ 0.90.
The model card says so.
