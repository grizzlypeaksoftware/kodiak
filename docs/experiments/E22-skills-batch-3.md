# E22: skills batch 3: the banked skills-2 data plus four new kinds, judged on real data

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
Kodiak-v0.2-1B is near chance on decision kinds that teams ask for, measured on **real, human- or expert-labelled data** (skills roadmap,
2026-10-04): checking whether a long answer is supported by its sources (RAGBench, skill +0.14: it calls 39 of 50 unsupported answers
supported), stance toward a named target (SemEval-2016, +0.24: it calls most opinionated tweets neutral), and judging which of two answers is
better (MT-Bench human judgments, +0.04). On synthetic probes it is also weak at refund eligibility under a written policy (+0.19) and
whether an agent's next step is safe to run (+0.21).

## 2. Why should this change move that failure?
New *kinds* of decision, built by the checked-synthetic recipe, are the one lever that has worked repeatedly: E17 (ESCI 0.04 → 0.24 on the
Decision Index) and E21 (MT-Bench human pairwise +0.04 → +0.31 over 3 seeds, with no regression on the 100-item trap test or never-seen).
E22 keeps E21's skills-2 data unchanged and adds four new kinds, with generators tightened where the real data showed the synthetic probes
were too easy (unsupported claims that are small changes rather than invented facts; stance that is implied, not stated).

## 2b. Prediction and attempt (rules 4 and 6, D65)
- Prediction: real-anchor score (mean skill over the three real anchors) from 0.211 (3-seed mean) to about 0.33-0.45 (+0.12 to +0.24): MT-Bench as in E21
  (+0.27), RAGBench and SemEval stance smaller (+0.10 to +0.20), because synthetic training transfers to real data at roughly half to a
  third of its synthetic gain (E17, E21). Refund eligibility and step safety near 0.9+ on their synthetic held-out sets, as in E17/E21.
- Zero-training check: done. Screening 1 and 2 (synthetic) plus real-data probes on v0.2 (above); E21's models on the 100-item trap test
  (0.913 vs v0.2 0.867) and MT-Bench (+0.31), which is the evidence that the skills-2 data transfers and doesn't harm the wording trap.
- Attempt: 2 of 2 on shipping the skills-2 data (E21 was attempt 1); 1 of 2 on the four new kinds. Invoice checks (+0.07) are left out: they
  need arithmetic, and there is no evidence an encoder learns sums from this recipe (rule 4).

## 3. Kill line
- Metric: **real-anchor score** = mean chance-corrected skill over three real-data anchors, never trained on: MT-Bench human pairwise
  judgments (150, CC BY 4.0), RAGBench long-answer adherence (100, CC BY 4.0), SemEval-2016 stance (102, MIT). Reported alongside (not
  gating): synthetic held-out evals for all seven kinds (100 each), aspect sentiment on SemEval-2014 ABSA.
- Baseline: Kodiak-v0.2-1B seeds 0-2 on the same anchors, measured before training: 0.243 / 0.138 / 0.251, **mean 0.211, SD 0.063**
  (MT-Bench +0.03 / +0.04 / +0.11; RAGBench +0.36 / +0.14 / +0.32; stance +0.34 / +0.24 / +0.32). Keep line: 3-seed mean **≥ 0.311**
  (+0.10, about 2.8 standard errors of a 3-seed mean).
- Smoke test (≤ 500 steps): kill if validation choice accuracy is more than 0.02 behind the v0.2 run of the same seed at step 500
- Full run: keep only if the 3-seed mean real-anchor score rises ≥ 0.10 over the baseline 3-seed mean; guards on 3-seed means, lines from
  docs/NOISE.md: never-seen forced ≥ 0.673, familiar ≥ 0.871, abstain precision ≥ 0.854, ranking ≥ 0.542, 100-item wording-trap eval ≥ 0.806
- Noise: guard lines from docs/NOISE.md (baseline mean − 2 SD, judged on 3-seed means; one run rejects only past 3 SD); every gating test has
  ≥ 100 items; 5 guards. Seed 1 runs first; seeds 0 and 2 run unless seed 1 is more than 3 SD past a guard line or shows no target gain.

## 4. How is this different from killed ideas?
- Not E21 (skills batch 2, killed on the 8-sentence probe) because the gate now uses the 100-item trap test on which E21's models were
  better than v0.2, the guards come from measured noise, and the target is real data rather than synthetic
- Not E9 (mixed/neutral tone batch, killed) because that added more of an existing kind on the small model, judged on two unrelated tasks;
  this adds new decision kinds on the 1B model, judged on real-data anchors built for them

## Change (one variable)
Training data: the v0.2 recipe (E19: public + v2.0 + E17 skills 10k + reworded options p = 0.5) **plus** E21's banked skills-2 sample
(2,500 each: pairwise judge, sarcasm, policy violation) **plus** ~2,500 checked examples each of four new kinds: long-answer adherence,
stance, refund eligibility under a policy, agent step safety. Same backbone, steps, learning rate and seeds as v0.2. The data mix is the one
variable (as in E17 and E21).

## Budget
- Cloud: $20 cap (held-out synthetic evals ~$0.40; ~32k-job batch for the four new kinds, sized from a pilot, extra examples banked)
- GPU: ~6 h for seed 1, +10 h for seeds 0 and 2 · Runs: evals + spot-check → baseline (3 seeds) → batch → smoke → seed 1 → seeds 0 and 2

## Approval
Approved: <Shane writes "Approved: Shane" here before any full run>
