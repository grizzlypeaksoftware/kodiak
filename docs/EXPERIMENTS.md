# Experiment log (append-only)

Read this **before proposing anything**. Every proposal must cite two killed ideas it is not repeating and say how it differs.
Rows are never edited after the verdict, except to add a link. Baseline for each row is the best model *of the same size tier* at the time.
Metric = never-seen forced accuracy on eval v0.2 unless noted (see docs/GOAL.md). Verdicts: **keep**, **kill**, **park** (a real signal, not
worth it now), **running**.

## Dead families (don't propose more of these without a new reason)

- **Small-model data tweaks at ~10k-example scale** (more of the same kind, re-weighting, re-selection): D24, D36, D39, D41, D42 all flat.
- **Distilling the ensemble on the teachers' own training data** (D36).
- **Int8 quantization without calibration checks** (D35).
- **Exact-number judgment ratings from AI raters** (D31): raters disagree too much; only bands are left to try.

## Log

| # | Date | Hypothesis | Change (one variable) | Budget | Pre-set bar | Result vs baseline | Verdict |
|---|---|---|---|---|---|---|---|
| E1 | 09-24 | More v1 synthetic data helps never-seen tasks | 0 / 3k / 10k v1 examples (small) | free | none set | flat on never-seen | kill (D24) |
| E2 | 09-24 | Repeat cap + full schedule + tuned threshold | training recipe (small) | free | none set | never-seen 0.625 → 0.664 (v0.1 eval) | **keep** (D25) |
| E3 | 09-25/26 | Generator v2.0 data beats v1 at equal size | data kind, 9.1k each (small, 3 seeds) | $25 | none set | never-seen tie; wrong refusals −60%, abstain precision 0.84 → 0.92 | **keep** (D29) |
| E4 | 09-26 | Stage 3: synthetic judgment scores | 5 pilots of score data | $0.54 | rater agreement | raters disagree 58-82% | kill / park as bands (D31) |
| E5 | 09-26 | Bigger backbone (ModernBERT-large) | backbone 150M → 400M (3 seeds) | free | none set | **0.553 → 0.609** | **keep** (D33) |
| E6 | 09-26 | Averaging 3 large runs improves calibration | ensemble (no training) | free | none set | 0.609 → 0.623; never-seen ECE 0.128 → 0.099 | **keep** (D34, shipped D45) |
| E7 | 09-26 | Int8 makes self-hosting cheaper | quantization | free | answer agreement | 11/41 answers flipped | kill (D35) |
| E8 | 09-26/27 | Distill the ensemble into small | loss: soft targets (3 seeds) | free | none set | accuracy same, ECE worse | kill (D36) |
| E9 | 09-27 | Mixed/neutral tone data fixes poem/fin sentiment | +3.9k polarity examples (small, 3 seeds) | $10 | none set | poem +2.5 (noise) | kill (D39) |
| E10 | 09-27 | Hard-example mining beats random selection | selection rule at 6.2k (small, 3 seeds each) | free | beats random | tie | kill (D41) |
| E11 | 09-27 | "Can't tell" data for unfamiliar inputs fixes calibration | +3.5k unfamiliar examples (small, 3 seeds) | $10 | ECE down | ECE 0.136 → 0.137 | kill (D42) |
| E12 | 09-28 | Computed-label simulator fixes the wording trap | +5.1k Returns Desk cases (small, 3 seeds) | $2 | probe up, guards hold | probe 3 → 5 of 8; never-seen −1.0 | park (D43) |
| E13 | 09-28 | Same, with 3 worlds and split intent | +3.2k Returns Desk v2 (small, 3 seeds) | $1.2 | probe up, guards hold | probe 3 → 4.7 of 8 (spread 3-7); never-seen −0.9 | park (D44) |
| E14 | 09-28 | Validation threshold rule keeps abstain precision ≥ 0.90 | threshold rule (accuracy mode) | free | precision ≥ 0.90 | 0.81 → 0.94, other metrics equal | **keep** (D45) |
| E15 | 09-28 | Bigger backbone again: Ettin-1B | backbone 400M → 1B (1 seed; lr 3e-5 vs 5e-5) | free, ~5 GPU-h | **≥ 0.629** | **0.609 → 0.666**; familiar 0.878; never-seen ECE 0.116; guard miss: abstain precision 0.86 (< 0.90); speed 38 ms (~40× vs Qwen3-8B) | **keep: confirmed** (3 seeds: 0.659 ± 0.013; D47) |
| E16 | 09-29 | 1B accuracy mode fixes "can't tell" precision | average the three 1B runs (no training) | free | precision ≥ 0.90 and never-seen ≥ 0.659 | precision 0.868 → **0.879** (miss); never-seen 0.673, never-seen ECE 0.088 (best ever), familiar 0.885; ~3 × 38 ms | kill as a precision fix; park as a slower top tier (D48) |
| E17 | 09-30 | Four in-purpose skills the Decision Index found near zero (grounding, tools, claims, relevance) are learnable from constructed-label data | +10k skills examples, 2,500 per skill (XL, seed 1) | $21.52 batch + $1.3 eval/pilots, ~5 GPU-h | skills score ≥ 0.618 (baseline 0.518); guards: never-seen ≥ 0.645, familiar ≥ 0.87, abstain precision ≥ 0.86, probe ≥ 4/8 | 3 seeds: skills **0.518 → 0.981** (all three 0.98); never-seen 0.659 → 0.662, familiar 0.881 → 0.878, ECE 0.113 → 0.109; abstain precision 0.868 → 0.889 ± 0.029 and probe 5.3 → 4.7 (noise: seed 1's bonus didn't hold). Same-generator eval; Decision Index re-run pending | **keep** (D53) |
| E18 | 10-01 | Kodiak's answer changes with how options are worded; training on reworded options (same answers) fixes it | options swapped for checker-verified rewordings with p = 0.5 (E17 mix, XL, seed 1) | ~$0.05 wordings (cap $5), ~6 GPU-h | wording consistency +10 pts, reworded accuracy +3 pts; guards: never-seen ≥ 0.645, familiar ≥ 0.87, abstain precision ≥ 0.86, skills ≥ 0.95, probe ≥ 4/8 | consistency 0.621 → 0.678 (needed 0.721), reworded accuracy 0.681 → 0.679 (needed 0.711): both missed; guards hold. Side effect, one seed: never-seen 0.664 → 0.680, never-seen ECE 0.111 → 0.094 (unconfirmed) | kill as a wording fix; park the never-seen signal (D57) |
| E19 | 10-01 | Training with reworded options raises never-seen accuracy (E18's one-seed side effect) | none beyond E18; seeds 0 and 2 (3 seeds vs E17's 3) | free, ~12 GPU-h | 3-seed never-seen mean ≥ 0.682 and ECE ≤ 0.109; guards: familiar ≥ 0.87, abstain precision ≥ 0.86, skills ≥ 0.95, probe ≥ 4/8 | 3 seeds: never-seen **0.662 → 0.689 ± 0.008**, never-seen ECE 0.109 → 0.085, poem +15, familiar 0.877, abstain precision 0.880, skills 0.98, probe 4.7 → 5.7; wording consistency ~0.68 (wording trap still open) | **keep** (D58): joins the v0.2 recipe |
**Lesson from E8-E13 (written 2026-09-28):** after the large model shipped, work drifted into local data tweaks on the small model without
pre-set bars. The only big wins came from changing the search space (data *kind* E3, backbone E5, ensembling E6). From E15 on, every
experiment uses `docs/experiments/TEMPLATE.md` and passes `scripts/gate.py` before a full run.
