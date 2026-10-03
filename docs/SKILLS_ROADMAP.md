# Skills roadmap: which kinds of decision to teach next

**Why.** Every big gain came from a new *kind* of data or a bigger model, never from more of the same (EXPERIMENTS.md). E17 showed that a new
decision kind costs ~$10-20 of checked synthetic data plus one GPU night, and that it carries over to real benchmarks (ESCI, HoVer, BFCL).
This page decides which kinds come next. The live list of trained kinds and candidates is on the dashboard (Research tab → Decision kinds;
`docs/progress.json` → `decision_kinds`).

**How a kind gets picked.**
1. **Screen** it cheaply: ~50 checked synthetic probes (writer + blind checker, answer fixed by construction; `kodiak_s1.data.sim.probes`,
   seed 21, never trained on) and measure the current model.
2. **Anchor it on real data** before training: the skills test for a new kind must include human-written items from a permissively licensed
   dataset. Lesson from E17: a test built by the same generators as the training data saturates (0.98) and says little.
3. **Train** the real gaps in batches of ~4 kinds per experiment (one variable: the data mix), through the gate, with three seeds.

## Screening 1 (2026-10-03): Kodiak-v0.2-1B on 12 candidate kinds ($0.35)

Forced accuracy on ~50 probes per kind; skill = (accuracy − chance) / (1 − chance), so 0 means random guessing. One model (seed 1).

| Kind | n | v0.2 accuracy | chance | skill (0 = chance) | most common mistakes |
|---|---|---|---|---|---|
| pairwise_judge | 49 | 0.31 | 0.33 | -0.04 | first→second (16), tie→first (7), tie→second (5), first→tie (3), second→first (3) |
| sarcasm | 50 | 0.62 | 0.50 | +0.24 | yes→no (19) |
| policy_violation | 50 | 0.72 | 0.20 | +0.65 | rule_2→none (3), rule_1→none (2), rule_3→none (2), rule_3→rule_1 (2), rule_2→rule_1 (2), r |
| duplicate | 48 | 0.81 | 0.33 | +0.72 | related→unrelated (5), same→related (4) |
| tool_unavailable | 50 | 0.88 | 0.50 | +0.76 | no→yes (6) |
| escalation | 50 | 0.84 | 0.25 | +0.79 | no→churn (7), no→safety (1) |
| task_done | 50 | 0.86 | 0.33 | +0.79 | complete→partial (5), partial→complete (1), failed→partial (1) |
| pii | 50 | 0.88 | 0.20 | +0.85 | health→none (2), financial→none (2), gov_id→none (1), contact→none (1) |
| stance | 50 | 0.92 | 0.33 | +0.88 | neutral→favor (3), against→neutral (1) |
| aspect_sentiment | 50 | 0.92 | 0.25 | +0.89 | mixed→positive (3), not_mentioned→mixed (1) |
| long_hallucination | 50 | 0.98 | 0.50 | +0.96 | unsupported→supported (1) |
| tool_result | 50 | 1.00 | 0.33 | +1.00 |  |

## What it says

- **Clear gaps (train these):**
  - **Pairwise judge** (which of two answers is better): at chance. Kodiak has trained on single-answer ratings, never on comparing two.
  - **Sarcasm:** it calls 19 of 25 sarcastic messages sincere.
  - **Policy violation** (which written rule is broken): it often misses a violation ("none") or names the wrong rule.
- **Probably fine, for now:** tool results, PII, escalation (some false "churn" alarms), task completion, duplicates, "no tool fits".
- **Don't trust these scores yet:** long-answer hallucination (0.96 here, but RAGTruth on the Decision Index is 0.00), aspect sentiment (0.89
  here, ACOS 0.02) and stance (0.88 here, VAST ~0.07). Synthetic probes are cleaner and more obvious than real data, so a high probe score
  can't clear a kind. These need real-data probes first (RAGTruth-style, ACOS-style and VAST-style items from permissive datasets).
- **Caveat:** 50 items per kind is a screen, not a result (±0.07 at these accuracies); the three gaps are far below the rest.

## Proposed next batch (v0.3 or v0.4; through the gate, Shane's approval)

Pairwise judge, sarcasm and policy violation, plus one of the three "real-data probe" kinds once its real probe confirms a gap.
