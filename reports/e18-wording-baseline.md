# E18 baseline: E17 seed 1 on the wording eval v0.1

640 never-seen questions (605 with an answer label) from 8 eval v0.2 tasks, each asked three ways: original options, a one-sentence
description of each option, a short paraphrase (checker-verified to mean the same; written for eval tasks only, never trained on).
Model: `runs/b-xl-s1-e17-s1` (final weights), measured before any E18 training.

| Measure | E17 seed 1 | E18 needs |
|---|---|---|
| **Consistency** (same answer under all 3 wordings) | **0.621** | **≥ 0.721** |
| Accuracy, original options | 0.717 | (guard: eval v0.2 never-seen ≥ 0.645) |
| Accuracy, description options | 0.673 | |
| Accuracy, paraphrased options | 0.689 | |
| **Accuracy with reworded options** (mean of the two) | **0.681** | **≥ 0.711** |

Consistency by task: jailbreak 0.85, contract NLI 0.73, ethics 0.70, banking77 0.64, bias in bios 0.61, fin sentiment 0.59, arXiv field
0.53, fin topic 0.38.

Reading: on more than a third of never-seen questions, Kodiak's answer changes when the same options are worded differently, and rewording
costs 3.6 points of accuracy. This is the failure E18 targets.
