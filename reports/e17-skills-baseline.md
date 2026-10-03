# E17 baseline: Kodiak XL (seed 1) on the skills eval v0.1

Held-out skills eval (`data/eval/kodiak-skills-eval-v0.1.jsonl`, seed 7, 400 examples, never trained on; spot-checked by Shane
2026-09-30). Forced accuracy (the best option, "can't tell" not allowed). Model: `runs/b-xl-s1-v2-s1` (= kodiak-xl-v2-preview), measured
**before** any E17 training.

| Skill | Main question | Chance | XL accuracy |
|---|---|---|---|
| Grounding | Is every claim supported? (3 options) | 0.33 | **0.45** |
| Tools | What should the assistant do next? (tools + ask + answer directly) | ~0.15 | **0.46** |
| Claims | Does the text support the claim? (3 options) | 0.33 | **0.81** |
| Relevance | How relevant is this product? (4 options) | 0.25 | **0.35** |
| **Skills score (mean of the four)** | | | **0.518** |

Other questions: which sentence is unsupported 0.24 (46), which parameter value 1.00 (47), is a parameter missing 0.53 (83); all 576
questions 0.536.

**E17 kill line (set before training):** the full run must reach a skills score of **≥ 0.618** (+10 points), with the guards in the proposal.
