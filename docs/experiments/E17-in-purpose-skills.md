# E17: four in-purpose skills from the Decision Index report card

**Product sentence (quoted from docs/GOAL.md):** Kodiak is an open decision model that lets teams automate routine "read this and decide" work (routing, triage, guardrails, checks) fast, cheaply and with honest confidence, and hand the cases it isn't sure about to a person or an LLM.

## 1. What exact failure of the current model does this fix?
On the public Decision Index (D51), Kodiak XL is near chance on decisions that are squarely its job: hallucination checks (RAGTruth 0.00), API choice (API-Bank 0.02; BFCL/When2Call/ToolRet 0.15-0.19), claim verification (HoVer 0.04, ANLI 0.02) and relevance judgments (Amazon ESCI 0.04). None of these decision types exist in its training data.

## 2. Why should this change move that failure?
Every real gain so far came from changing the kind of data (v2.0 inference questions, E3) or the model (E5, E15), never from more of the same (E1, E9-E11). These are new kinds, each with its answer fixed by construction (the writer is told which answer to build toward, and a blind checker must agree), the recipe that moved the word-trap probe (E12).

Four generators (Generator v2 `--focus` modes), ~2,500 kept examples each:
- **S1 grounding:** a real passage (FineWeb-Edu) + a response written to be faithful, to add one unsupported detail, or to contradict it. "Is every claim in the response supported by the source?" (supported / adds unsupported claims / contradicts the source), plus "which sentence is unsupported?".
- **S2 tool selection with full specs:** 3-8 realistic API specs (JSON, with parameters) + a user request; code picks the target (a tool, "ask the user for a missing required parameter", or "answer directly"). "Which tool next?", "which value for parameter X?", "is a required parameter missing?".
- **S3 claim verification:** one or two real passages + claims built as supported / refuted (number, entity, negation or time swap) / not enough information, including two-passage claims. "Is the claim supported?"
- **S4 relevance:** a shopping query + a product description built as exact match / substitute / complement / irrelevant (the ESCI scheme). "How relevant is this product?"

## 3. Kill line
- Metric: accuracy on a new held-out **skills eval**: 100 examples per skill from the same generators with a separate seed (7), never trained on, spot-checked by Shane (like the v2.0 eval candidates). The Decision Index is re-run only once, as the final check.
- Baseline: Kodiak XL (seed 1) on the skills eval, measured before training.
- Smoke test (≤ 500 steps): kill if validation choice accuracy is more than 0.02 behind the XL seed-1 run at step 500
- Full run: keep only if skills-eval accuracy rises ≥ 10 points over the baseline; guards: never-seen forced (eval v0.2) ≥ 0.645, familiar ≥ 0.87, "can't tell" precision not below 0.86, label-overlap probe not below 4 of 8

## 4. How is this different from killed ideas?
- Not E9 (mixed/neutral tone batch) because that was more of an existing decision type on the small model, judged on two unrelated eval tasks; this adds new decision types, on XL, judged on a test built for them
- Not E11 (unfamiliar-input batch) because that aimed at calibration with generic "can't tell" questions; this targets specific skills measured near zero on an external benchmark

## Change (one variable)
Training data: public + v2.0 (as XL v2) **plus** the four new skill sets (~10k examples). Same backbone, recipe, steps and learning rate as XL v2 seed 1. The four sets are one variable here (a data mix); if it wins, a later ablation shows which sets earn their keep.

## Budget
- Cloud: $30 (pilots ~$1, then ~$27 for ~10k kept at ~$2.7 per 1,000; the runner's cap stops it) · GPU: ~5 h (1 run), +10 h only if it clears the bar · Runs: pilots → skills eval → smoke → 1 full → 2 confirm

## Approval
