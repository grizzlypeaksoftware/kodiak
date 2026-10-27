# E25: does training on more kinds of task help on new kinds of task?

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
Kodiak-v0.4-1B is weak on kinds of task it has never trained on. On our new-domains test v0.1 (D76: 15 real read-and-decide tasks from
never-trained domains, balanced answers) its mean chance-corrected skill is 0.335 (3 seeds), against 0.685 forced accuracy on our older,
closer-to-home never-seen eval; on the Decision Index's private new-domain tasks it scores 0.9 on the public scale (D72). Every experiment
since E17 added skills one at a time and none moved never-seen accuracy. This experiment doesn't fix the failure directly: it decides which
of two fixes to build next (task variety, or a different backbone, D74).

## 2. Why should this change move that failure?
Instruction-tuning research (T0, FLAN) found that zero-shot performance on held-out tasks grows with the number of *distinct* training tasks,
not with more examples of the same tasks. Kodiak trains on 28 kinds of task, several near-duplicates (3 intent, 2 NLI, 3 multiple choice);
those papers used hundreds to thousands. If variety is the lever, a model trained on 28 kinds should beat one trained on 7 kinds on new
domains **at the same amount of data and training**. The model check (D74: untrained Qwen3-1.7B 0.572 vs Kodiak 0.676 on never-seen) says
the encoder isn't the obvious ceiling, which makes variety the prime suspect.

## 2b. Prediction and plan (rules 4-6, D65/D68)
- Prediction: the 28-kind run at matched data beats the mean of the two 7-kind runs by +0.03 to +0.08 on the new-domains read slice. Evidence:
  the T0/FLAN task-count curves (qualitative), and that a 7-kind model has seen 1/4 of the task formats the test draws on.
- Zero-training check: done. New-domains baseline for v0.4 (0.335, SD 0.008 over 3 seeds, D76); model check (D74). No existing model varies
  task count at fixed data, so the question can't be answered without training.
- Time box: generalization to new kinds of task: 5 days from 2026-10-27 (proposed; Shane sets it)
- If it passes: task variety is the lever. Next (E26): a variety program: convert many more permissively licensed public datasets into
  training kinds (towards 100+, kept separate from the new-domains test), sized by this curve, trained at 1B.
- If it fails: variety at this scale isn't the lever. Next: the backbone test (fine-tune a ~1.7B open decoder on Kodiak's data and compare on
  the new-domains test), a GOAL-level choice for Shane.

## 3. Kill line
- Metric: **new-domains test v0.1, read-slice mean chance-corrected skill** (scripts/newdomain_score.py; 15 task-questions, 2,233 items
  in the slice; never trained on).
- Baseline: no 400M baseline exists for this comparison; it is internal to the experiment. Arms (all ModernBERT-large 396M, the v0.4 recipe's
  data and settings, 6,000 steps, seed 0, the same validation set): **A7** and **B7**, two random draws of 7 of the 28 kinds with all their data
  (68,525 and 103,921 unique examples); **all28-matched**, all 28 kinds cut to 86k unique examples (--kind-budget 110000, the mean of A7 and B7);
  **all28-full**, all 28 kinds with all their data (392,109; reference for the effect of more data). Kinds: docs/experiments/E25-arms.json.
  v0.4 (1B) scores 0.335 for orientation.
- Smoke test (≤ 500 steps): kill if validation choice accuracy at step 500 is below 0.60 (the run is broken; v0.4 runs are ~0.85 there)
- Full run: keep only if all28-matched ≥ mean(A7, B7) + 0.03 **and** all28-matched is above both A7 and B7 ("variety helps"); below
  mean + 0.01 = "variety doesn't help at this scale"; in between = inconclusive (add a seed only if Shane wants). Guards: report only
  (no model ships from E25): never-seen forced and familiar accuracy on eval v0.2, the knowledge slice.
- Noise: the new-domains read slice varies by SD 0.008 across seeds for v0.4 (docs/NOISE.md); +0.03 is ~4 SD of one run. The two 7-kind draws
  also show how much the choice of kinds matters. The gating test has 2,233 items; guards are report-only here.
- Shortcut guards: (rule 7) flip rate on the wording eval and the contrastive tests are reported for each arm, not gating (no model ships)

## 4. How is this different from killed ideas?
- Not E1 (more v1 synthetic data, killed: flat on never-seen) because that added more examples of the same kinds; this holds the amount of
  data fixed and changes only how many different kinds there are
- Not E18 (more reworded data, killed as a wording fix) because that targeted one known failure with more of one data type; this tests a
  general mechanism (task variety) on a test built from domains we have never trained on

## Change (one variable)
The number of kinds of task in training (7 vs 28) at matched unique examples and identical steps, backbone, settings and validation set
(new train.py options --kinds and --kind-budget; with neither set, training data is byte-identical to before, checked by hash). all28-full adds
a second comparison (more data at 28 kinds), reported separately.

## Budget
- Cloud: $0 (no new data) · GPU: ~9 h (4 runs × ~2 h training + evaluation), overnight · Runs: 4, one seed each (a direction, not a
  proof; rule: three seeds before claiming a small effect)

## Approval
Approved: <Shane writes "Approved: Shane" here before any full run>
