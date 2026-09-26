# Strategy: a frontier-class open-weights decision model

> Adopted 2026-09-25 (DECISIONS.md D27). This page says what Kodiak is trying to be, how we'll know if it got there, and
> what we'll do next. The numbers are updated as experiments land; every number links to a report or a decision.

## 1. The goal

**Kodiak aims to be the best open-weights model for structured decisions**: given a state and typed questions, return
calibrated answers that stay inside the answer space, fast enough to put in front of every request, cheap enough to run
anywhere, and honest enough to say "I can't tell from this."

"Frontier" here means **frontier in its class**, not frontier in general:

| Kodiak *is* aiming for | Kodiak is *not* aiming for |
|---|---|
| The best accuracy, calibration and abstention among open decision models of its size | Beating GPT- or Claude-class LLMs at reasoning, knowledge or writing |
| Near-LLM accuracy on decision tasks at 100×+ the speed and a fraction of the cost | Replacing LLMs; the best systems use both (see §5) |
| Openness: weights, data recipe, eval and every decision published under permissive licenses | A closed product with an open demo |

## 2. Why this is worth doing

Much of what software asks LLMs to do is *deciding*, not generating: which intent, how urgent, which tool, is this safe,
can this even be answered? Today that usually means an LLM API call per decision: slow (seconds), costly at volume, hard to
threshold (verbalized confidence is poorly calibrated), and able to answer outside the allowed options.

A decision model that is fast, calibrated, abstains honestly and can't go off-menu makes automated decisions **reliable
and cheap**. It can run on a CPU, privately, at the edge. The closest product to this vision (TypeSafe AI's Jev) is closed.
The open alternatives (§3) each cover part of it. That gap is the dent we want to make.

## 3. The class and the competition

| System | What it does well | What it lacks for this job |
|---|---|---|
| **NLI zero-shot classifiers** (e.g. `MoritzLaurer/*-zeroshot-v2.0`) | Mature, widely used, any label set | One label pass per label (slow with many labels); no typed questions, scores or abstention; confidence not calibrated for decisions |
| **GLiClass** (`knowledgator/gliclass-*`) | All labels in one pass, fast | Classification only: no numeric scores with uncertainty, no calibrated abstain, no multiple typed questions per state |
| **LLMs used as classifiers** (e.g. Qwen 27B with JSON schemas) | Broad knowledge and reasoning; strongest on unseen tasks | Seconds per call; verbalized confidence; constrained decoding needed to stay on-menu |
| **Jev** (TypeSafe AI) | The original "System One" idea | Closed |
| **Kodiak** | Many typed questions (choice + score + null) in one pass; calibrated probabilities; can't answer off-menu; 8 ms | Generalization to never-seen tasks is still behind LLMs (§4) |

The baselines are measured on our frozen eval set with `src/kodiak_s1/eval/zeroshot.py` (choice questions only; forced accuracy
compares pure ranking skill, since these models can't abstain).

## 4. Where we stand (updated 2026-09-25)

Current best model: `b-small-s1-R1-cap3` (ModernBERT-base backbone, 150M parameters). Frozen eval set v0.1. Choice questions only,
so the open classifiers can be compared (`reports/zeroshot-baselines.md`); "forced" = always pick a label, the fair ranking comparison.

| System | Params | Overall acc | Overall forced | **Held-out forced** | Held-out acc | ECE (overall) | p50 latency |
|---|---|---|---|---|---|---|---|
| **Kodiak small, v2.0 data (mean of 3 seeds)** | 150M | **0.799**† | – | 0.720 ± 0.012 | **0.703** ± 0.019 | **0.029**† | **8 ms** |
| Kodiak small, v1 data (mean of 3 seeds, equal size) | 150M | 0.792† | – | **0.721** ± 0.043 | 0.678 ± 0.039 | 0.038† | 8 ms |
| Kodiak small (R1, single run, 2026-09-24) | 150M | 0.780 | 0.774 | 0.691 | 0.664 | 0.049 | 8 ms |
| GLiClass instruct large v1.0 | 439M | 0.548 | 0.655 | 0.705 | 0.689 | 0.156 | 27 ms |
| GLiClass large v3.0 | 439M | 0.533 | 0.630 | 0.681 | 0.605 | 0.203 | 26 ms |
| NLI DeBERTa-v3-large zeroshot v2.0 | 435M | 0.398 | 0.684 | 0.712* | 0.291 | 0.450 | 47 ms |
| NLI DeBERTa-v3-large v2.0 **-28heldout** (clean) | 435M | 0.332 | 0.629 | 0.671 | 0.247 | 0.515 | 48 ms |
| NLI ModernBERT-large zeroshot v2.0 | 395M | 0.404 | 0.676 | 0.708* | 0.360 | 0.451 | 14 ms |
| Qwen 27B (LLM, 200-example sample, all question types) | 27B | – | – | ≈ 0.86 | – | worse | ≈ 3,400 ms |

† All question types (choice + score); the other rows are choice questions only. Seed means: `reports/generator-ab-seeds.md` (D29).

\* Trained on banking77, one of our held-out sources (it's one of their 28 training tasks). Their clean "-28heldout" variant drops
from 0.812 to 0.692 forced accuracy on banking77.

**Reading it.**
- **Overall, Kodiak is far ahead** (+23 points accuracy, +9 forced) at a third of the latency or less, with 3–10× lower calibration error, while
  also answering score questions and abstaining, which the others can't do properly. Much of the overall lead is on task types Kodiak trained on,
  so the held-out row is the real test.
- **Update 2026-09-26 (3 seeds, D29):** averaged over three training runs, Kodiak scores ~0.72 held-out forced with either v1 or v2 data,
  vs. 0.705 for GLiClass-instruct. That difference is inside the run-to-run noise, so criterion 1 is **roughly tied, not met**. v2 data makes
  Kodiak refuse far less often and abstain more trustworthily (held-out accuracy 0.703 vs. GLiClass-instruct 0.689).
- **Held-out (first single-run read, 2026-09-25): criterion 1 (§6) is NOT met yet.** GLiClass-instruct-large beats Kodiak by 1.4 points forced (0.705 vs. 0.691) and 2.5 points in
  accuracy, with 2.9× the parameters (439M vs. 150M). Against the clean NLI model, Kodiak leads (0.691 vs. 0.671).
- **Where Kodiak loses:** occupation from a biography (Bias in Bios: 0.64 vs. 0.79–0.82 forced) and banking intents (0.76 vs. 0.84). These are
  classic "infer the category" tasks, the classifiers' specialty, and exactly the over-abstention/inference weakness Generator v2 targets.
- **Where Kodiak wins big:** jailbreak detection, held-out for everyone (0.68 vs. ≤ 0.52); the NLI models abstain on almost everything with
  a naive threshold, which is why their plain accuracy is low.

## 5. The product shape: System 1 in front of System 2

Kodiak doesn't have to win every decision; it has to know **which ones it has won**. The deployment pattern:

1. Kodiak answers every request in milliseconds, with calibrated probabilities.
2. Confident answers are used directly (typically most of the traffic).
3. Uncertain answers and abstentions escalate to an LLM or a human.

Calibration is what makes this safe: a threshold at "90% sure" actually means about 90% right.

**Outside evidence (2026-09-26).** Li, Miao, Krishnan and Padman (Carnegie Mellon), *JEV-as-a-Judge: Accept When Confident, Escalate When
Unsure* (arXiv:2609.26550): a decision-only judge came within three points of a state-of-the-art LLM judge on preference and evidence-grounded
factuality at 0.36% of its cost, and a frozen accept-confident / escalate-unsure cascade kept 99% of the big judge's accuracy at lower cost. Its
weak spots were checking derivations and resisting elaborately written wrong answers, consistent with Kodiak's (recognition strong, multi-step
reasoning weak). Separately, TypeSafe and OpenRouter launched `typesafe/jev-router` (a cache-aware model router, Sep 2026): routing is now a
proven commercial use of decision models. That turns LLM-level quality into
something affordable at volume. The second selling point is **adaptation**: fine-tuning on a few hundred of a customer's own labeled
examples, which typically lifts a specific task well past any zero-shot model.

## 5b. Distribution: how people will run it

Third-party inference providers (the "Inference Providers" panel on Hugging Face) serve standard architectures at scale, mostly LLMs; a
custom model like Kodiak only gets picked up once demand is visible. Kodiak doesn't depend on them: it runs at ~80 ms per request on CPU,
so it is cheap to host anywhere. Four ways to run it, from free to product:

| Channel | Who it's for | Status |
|---|---|---|
| **Demo Space** (Gradio, free CPU) | Try it in a browser | Built: `spaces/kodiak-demo/`; deploy at release |
| **Hugging Face Inference Endpoints** (Deploy button; `handler.py` in the model repo) | "Host it for me", billed hourly by Hugging Face | Built: `release/handler.py`, copied into every export |
| **Self-host** (`pip install kodiak-s1[infer]`; later a Docker image with the ONNX + Node/Express server, Phase 6) | Run it on your own laptop, VPS or cloud, no GPU needed | pip path built; Docker/ONNX in Phase 6 |
| **Kodiak hosted API by Cortex Agent** | Teams that want an API key and an SLA, not infrastructure | **The productization path** (Shane, 2026-09-25); designed after the public release |

The hosted API is the business model: open weights build trust and adoption, and the hosted service (plus, later, fine-tuning on a
customer's own labels) is what customers pay for. It is also what could fund the larger models and a custom encoder (Track A).

## 5c. Use cases to lead with, and parked product ideas

**Use cases for the pitch** (all "decisions, not writing"): support triage (intent, urgency, routing, "missing info → ask"); agent tool
routing and next-action guards; prompt-injection / jailbreak / toxicity screening in front of LLMs; RAG answerability ("can this be answered
from the retrieved context?"); form and record completeness checks; a cheap LLM-output judge; the System 1 → System 2 cascade.

**Parked (back burner, 2026-09-25): Kodiak Compliance.** A vertical product on top of a compliance-fine-tuned Kodiak: extract text from
Word/PDF, chunk it, check each requirement of a standard (PCI DSS, SOC 2, HIPAA…) against each chunk, and report met / gap / partial with
the supporting section, where calibrated abstention *is* the gap list. Positioned as a gap-analysis and evidence-finding assistant (a human
signs off), private/on-prem and cheap per check. Open issues: long documents (chunking now, longer states later), standards' license terms,
competition (Vanta, Drata, Secureframe). Validation plan when revived: one standard, ~100 human-labeled requirement checks, baseline vs. a
compliance-weighted generator batch + fine-tune. Keep the open model general; verticals are the product layer.

**Post-launch demo backlog, ranked (2026-09-26):**

1. **Kodiak-as-a-judge** (Shane's pick for the next demo). The state holds a prompt and one or two responses; questions: "Which response is
   better?" (A / B / tie), "Is the answer supported by the evidence?", quality scores, with abstain = escalate to an LLM judge. Show the cascade
   live: share of verdicts Kodiak accepts, accuracy of those, cost per 1,000 judgments vs. an LLM judge. Doubles as the **public benchmark** we
   need for release criterion 1: reproduce the CMU paper's setup on whichever of its benchmarks are permissively licensed (check each at the
   source), so the story is "the open model, tested the way CMU tested Jev." Needs: longer states (prompt + responses exceed 512 tokens) and
   pairwise-preference training data with clean licenses (HelpSteer2 and UltraFeedback are already in training).
2. **Kodiak Router** (most commercially relevant; a flagship for the hosted API). JSON state: conversation summary, current model, cached
   tokens, candidate models with prices and speeds; questions: which model, which reasoning effort, task difficulty (score); abstain = use the
   strong model. The open, self-hostable counterpart to `jev-router`. Hard part: outcome labels (which model would have succeeded), from running
   candidate models on real prompts and grading, or from public router datasets with verified licenses.
3. **Kodiak plays Zork** (see below): the fun, viral one.

**Kodiak plays Zork (2026-09-25).** Kodiak can't type, so it plays by *choosing*: a text-game harness
(e.g. Microsoft Research's Jericho) lists the valid actions each turn, Kodiak picks one ("What's the best next command?"), and when it
abstains the turn goes to exploration or an LLM. That makes it a live System 1 / System 2 demo ("Kodiak made 85% of the moves; the LLM 15%;
total cost 2 cents") and a real long-horizon decision benchmark (game score). Expect weak play at first (Zork is hard even for LLMs);
the point is the cascade and the "can't go off-menu" property. Before building: verify the licenses for the game files and the harness;
state = last few turns + location + inventory (512-token limit). Effort: about a day for a playable demo.

## 6. The release bar ("frontier in class", defined before we measure)

Kodiak v0.1 is called frontier-class only if all of these hold on the frozen eval set (and, once chosen, a public benchmark suite):

1. **Best in class:** higher forced accuracy than every open zero-shot classifier baseline on held-out choice questions, and on the
   public suite.
2. **Near-LLM:** within ~10 points of a 7–8B open LLM on held-out tasks, at ≥100× its speed.
3. **Calibrated:** ECE ≤ 0.05 and lower than every baseline.
4. **Honest abstention:** abstain precision ≥ 0.90 at the default threshold.
5. **Reproducible:** weights, data recipe (including rebuild scripts for web text), eval set and reports published under permissive licenses.

If a criterion fails, the release says so plainly. Criteria may be tightened later, never loosened after seeing results.

## 7. The levers, in expected order of impact

| # | Lever | Status | Evidence so far |
|---|---|---|---|
| 1 | **Better synthetic data** (Generator v2: taxonomy, real text, inference questions, critics) | v2.0 batch running | More v1-style data didn't help held-out (D24); v2 targets the diagnosed failure (over-abstention on inference) |
| 2 | **Training recipe** (repeat cap, full schedule, tuned threshold) | Done | Held-out 62.5% → 66.4% (D25) |
| 3 | **Bigger backbone** (ModernBERT-large, ~400M) | Planned after the v2 A/B | Larger encoders usually generalize better; costs ~3× latency (still ~25 ms) |
| 4 | **Hard-example mining + minimal pairs** (Generator v2.1, v2.2) | Designed | Targets Kodiak's own mistakes and the "which fact matters" skill |
| 5 | **Longer states** (stage S2, up to 8k tokens) | Planned | Real documents are often longer than 512 tokens |
| 6 | **Fine-tuning kit** for users' own labels | Planned for release | The main path to production accuracy on a specific task |
| 7 | **Custom encoder** (Track A) | Deferred (D19) | Only if Kodiak earns revenue or the backbone becomes the bottleneck |

Two sizes are the likely release: a fast one (small) and a quality one (large). Public names are still open (D23).

## 8. Guardrails

- **Honest evaluation:** never train or tune on the frozen eval set; the Generator v2 planner sees only validation data; baselines
  get fair prompts (the Qwen baseline was fixed twice so it wasn't handicapped).
- **Clean licensing:** permissive open-weight teachers only (gpt-oss, DeepSeek, Qwen), never closed models (D20); every data source
  is listed in data/LICENSES.md.
- **Measure before building:** each lever ships only if it beats the previous best on the eval plan (GENERATOR_V2.md §5).

## 9. Open questions and risks

- **The size ceiling.** A 150M encoder may plateau below the bar on never-seen tasks; ModernBERT-large is the planned answer.
- **Teacher ceiling.** Synthetic labels are only as good as writer + checker + critics (human review: 92.7% for v2.0). Label noise
  caps what the student can learn.
- **Which public benchmark?** To choose: permissively licensed zero-shot classification sets, disjoint from our training sources.
- **The LLM comparison point.** Qwen 27B is measured; a 7–8B LLM baseline (criterion 2) still needs to run.
