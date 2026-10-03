# E21: skills batch 2: pairwise judge, sarcasm, policy violation

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
Skills-roadmap screening 1 (docs/SKILLS_ROADMAP.md, ~50 checked probes per kind) found three decision kinds where Kodiak-v0.2-1B is at or near
chance: **pairwise judge** ("which of two answers is better?") skill −0.04, **sarcasm** +0.24 (it calls 19 of 25 sarcastic messages sincere),
and **policy violation** ("which written rule does this message break?") +0.65, often missing the violation. All three are core product
uses: a cheap LLM judge, sentiment that isn't fooled by tone, and guardrails against a team's own written policy.

## 2. Why should this change move that failure?
It's the E17 recipe, which moved four near-zero kinds to 0.98 on its own test and carried over to real benchmarks (ESCI 0.04 → 0.24, HoVer
0.04 → 0.20; D53, D61): new *kinds* of decision, each answer fixed by construction and confirmed by a blind checker. Kodiak has never seen a
two-answer comparison or a written-rules check in training, and its sentiment data has almost no sarcasm, so the gap is missing data, not
model size.

## 3. Kill line
- Metric: **skills-2 score** = mean chance-corrected skill over the three kinds on a held-out skills-2 eval: 100 checked synthetic examples
  per kind (seed 22, never trained on), plus a real-data anchor where a permissively licensed human-written set exists (sarcasm and pairwise
  judgments; checked for license before use, reported separately, never trained on). Shane spot-checks the eval as for E17.
- Baseline: Kodiak-v0.2-1B (seed 1) on the skills-2 eval, measured before training (screening 1 suggests about 0.28).
- Smoke test (≤ 500 steps): kill if validation choice accuracy is more than 0.02 behind the v0.2 seed-1 run (E18 seed 1) at step 500
- Full run: keep only if the skills-2 score rises ≥ 0.25 over the baseline and each kind rises ≥ 0.10; the real-data anchor must not fall;
  guards: never-seen forced ≥ 0.679, familiar ≥ 0.87, "can't tell" precision ≥ 0.86, E17 skills score ≥ 0.95, ranking (aurc_gap_closed)
  ≥ 0.541, label-overlap probe ≥ 5 of 8, wording consistency ≥ 0.66

## 4. How is this different from killed ideas?
- Not E9 (mixed/neutral tone batch, killed) because that added more of an existing sentiment kind on the small model, judged on two unrelated
  tasks; this adds three decision kinds the model has never seen, on the 1B model, judged on a test built for them with a real-data anchor
- Not E20 (wording-consistency loss, killed) because that changed the loss on existing label sets; this changes the data kind and leaves the
  loss alone

## Change (one variable)
Training data: the v0.2 recipe (E19: public + v2.0 + E17 skills 10k + reworded options p = 0.5) **plus** ~2,500 checked examples per new kind
(~7.5k). Same backbone, steps, learning rate and seed as v0.2 seed 1. The three kinds are one variable here (a data mix), as in E17.
Generators: the screening specs in `kodiak_s1.data.sim.probes` with training seeds; their wording rules are tightened from the screening
pilot (e.g. policy messages must break exactly one rule unambiguously).

## Budget
- Cloud: $15 cap (eval ~$0.40; batch sized from the pilot cost so all ~10k jobs fit with room, extra examples banked) · GPU: ~6 h (1 run),
  +12 h only if it clears the bar · Runs: eval + spot-check → baseline → batch → smoke → 1 full → 2 confirm

**Baseline measured (2026-10-03, before training):** Kodiak-v0.2-1B seed 1 on the skills-2 eval (100 per kind, seed 22): skills-2 score
**0.142** (pairwise judge +0.115, sarcasm **−0.240**, policy violation +0.550); MT-Bench human pairwise anchor (150, CC BY 4.0) +0.040. Keep line:
skills-2 score **≥ 0.392**, each kind ≥ +0.10 over its baseline, anchor not below +0.040. Sarcasm anchor: no permissively licensed
human-written set found on the Hub (license missing or unknown), so sarcasm is synthetic-only. Details: reports/preds_skills2/.

## Approval
Approved: Shane (2026-10-03, "Approved")
