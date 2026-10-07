# Evaluation Design for ML Decision Models

From first principles to production practice, for a fine-tuned ModernBERT-style decision/classification model and the regulated banking service that calls it.

The thread through all four levels: **an eval exists to make a decision, and it is only as good as its match to that decision.** Every technique below follows from taking that seriously.

## Contents

- [Level 1: What an eval is](#level-1-what-an-eval-is)
- [Level 2: What makes an eval good or bad](#level-2-what-makes-an-eval-good-or-bad)
- [Level 3: Designing evals for a decision model](#level-3-designing-evals-for-a-decision-model)
- [Level 4: Using this on a Next.js / Postgres / MuleSoft banking project](#level-4-using-this-on-a-nextjs--postgres--mulesoft-banking-project)
- [Template: One-page eval spec](#template-one-page-eval-spec)
- [Template: One-page release checklist](#template-one-page-release-checklist)

---

## Level 1: What an eval is

### Five words people use interchangeably

**Metric.** A function that turns predictions and labels into a number, such as accuracy, recall, or expected cost. A metric has no opinion about which data you feed it or what you do with the result.

**Eval.** A designed measurement procedure that answers a specific question well enough to act on. It has five parts: a task definition, a set of examples, a scoring rule, a way of aggregating scores, and a decision rule. "Recall on the dispute slice" is a metric. "On 400 adjudicated messages from last quarter's secure-message channel, we auto-handle no dispute messages, and if we do, we don't ship" is an eval.

**Benchmark.** An eval that has been frozen and shared so different people can compare systems on it, such as GLUE or MTEB. Benchmarks are useful for picking a starting checkpoint. They are nearly useless for deciding whether *your* router is safe. They also go stale: they saturate, they leak into training data, and the community overfits to them.

**Test.** A deterministic pass/fail assertion about behavior on specified inputs. Software tests look like "a POST with a missing `channel` returns 422." Model tests look like "changing the customer name in this message must not change the route." Tests check specific promises. Evals estimate rates.

**Monitoring.** Continuous measurement on live traffic, usually *without* labels at the moment of the decision. Monitoring detects change, such as shifts in score distribution, override rates, or input mix. It tells you *when* to re-run an eval. It does not replace one.

The relationship between them: a benchmark helps you choose a base model. Tests pin specific behaviors. An eval decides whether to ship. Monitoring tells you when the eval's assumptions have stopped holding.

### Why a held-out accuracy number is not an eval

Say you fine-tune ModernBERT to route incoming secure messages into five queues: `card_services`, `disputes_fraud`, `payments`, `account_maintenance`, `general_inquiry`. You hold out 15% at random and get **94% accuracy**.

That number fails as an eval in at least six ways:

1. **No decision attached.** Is 94% good enough? Compared to what? There is no ship/don't-ship rule.
2. **Errors are treated as equal.** A 6% error rate could all be `general_inquiry ↔ account_maintenance` confusion, which is harmless because an agent re-queues it in 30 seconds. Or it could include fraud reports routed to the FAQ bot, which is a regulatory problem. Accuracy can't tell these apart.
3. **The test distribution is the training distribution.** A random split of your labeled pile measures how well you fit that pile. Your labeled pile is rarely what production looks like. It's often whatever was easy to export or label.
4. **The aggregate hides slices.** If 3% of traffic is Spanish and the model is 50% accurate on it, overall accuracy drops by about 1.4 points. That is invisible as a headline and catastrophic for those customers.
5. **No operating point.** You will ship a threshold, maybe with an abstain band. Accuracy at argmax describes a system you aren't deploying.
6. **No uncertainty.** With 150 test examples, 94% has a 95% confidence interval of roughly 89–97%. A "1-point improvement" is noise.

### The basic loop

```
task definition → slice of examples → scoring function → aggregation → decision
       ↑                                                                   │
       └──────────────── (change the task) ←──────────────────────────────┘
```

Here is the loop on a concrete case.

1. **Task definition.** "Given a secure message plus product context, decide whether it can be handled by the automated payment-status flow (`auto`) or must go to a human (`human`)." The task definition also states what *auto* is allowed to do, because that determines what an error costs.
2. **Slice of examples.** 300 messages sampled from the last 90 days, stratified so that disputes, Spanish-language messages, and business accounts each get at least 40 examples.
3. **Scoring function.** Per example: correct, false accept (auto-handled but needed a human), or false reject (sent to a human unnecessarily).
4. **Aggregation.** Report overall expected cost, plus the false-accept count *per slice*, plus the automation rate.
5. **Decision.** Ship if total cost is below the current process, if there are zero false accepts on the dispute slice, and if the automation rate is at least 40%. Otherwise you have three options: don't ship, change the threshold, or change the task. An example of changing the task: "the model can't tell disputes from payment-status questions without seeing the last transaction, so add that to the input contract."

The last arrow matters most. A good eval can tell you the *task* is wrong, not just the model.

### Leakage in plain language

Leakage means **your test set contains information the model could not have in production, or information it already saw during training.** Either way, your score measures memory or cheating, not skill.

Here is an encoder-classifier example. You export 5,000 secure-message threads and split the *messages* randomly 80/20. Three things go wrong:

- **Quoted replies.** Message 2 in a thread often quotes message 1. If message 1 is in train and message 2 is in test, the model has literally seen most of the test text with its label.
- **Same customer, same template.** One small-business customer sends 60 near-identical "please confirm ACH batch #____ posted" messages. Random splitting puts about 48 in train and 12 in test. The model memorizes that customer's phrasing and looks brilliant on 12 "test" examples.
- **Label in the input.** Agent replies carry a signature like "— Card Disputes Team." If your export concatenates the thread, the label is sitting in the text. ModernBERT will find it, because finding exactly that is what an 8k-context encoder is good at.

The fixes follow directly:

- Split by **group**: thread, customer, or both.
- Split by **time**: train on months 1–9, test on months 10–12. This also tests robustness to drift.
- **Strip post-decision artifacts** from inputs. The input contract should contain only what exists at the moment the decision is made.
- **Deduplicate** near-identical texts before splitting. MinHash works, and so does embedding similarity above about 0.95.
- **Tune nothing on the test set.** That includes thresholds, early stopping, and which checkpoint you pick. Every time you look at test results and change something, the test set leaks a little into your choices.

One sanity check catches most leakage: **if your group-split score is much lower than your random-split score, the random split was leaking.** The gap measures how much of the score was memory.

### When LLM-as-judge doesn't apply

LLM-as-judge and chatbot arenas exist because generative output has no single correct answer, so you need something to grade free text. Your model outputs a label from a fixed set, and you can get human gold labels. You don't need a judge model, and in a regulated workflow you shouldn't have one in the scoring path.

An LLM can still be useful *around* the eval. It can draft labels for humans to verify. It can generate paraphrases for invariance tests. It can help cluster error explanations. In none of those roles is it the source of truth.

### Level 1 self-check

1. Your teammate says, "We ran the eval, it's 91% F1." What three questions do you ask before believing that's an eval?
2. You get 96% on a random split and 81% on a customer-grouped split. What is the most likely explanation, and which number do you report?
3. Name one thing that is a test and not an eval for your router, and one thing that is monitoring and not an eval.

### Level 1 exercise: the leakage detector (about 3 hours)

Build a CSV of **60 messages from 12 fictional customers**, five messages each. Give each customer a consistent writing style or template quirk. Label each message `auto` or `human`.

```csv
customer_id,thread_id,text,label
C01,T01,"Hi, did my $250 payment to Chase card post yet? -Dana",auto
C01,T02,"Hey it's Dana again, payment to Chase still pending?",auto
C02,T03,"I don't recognize a charge from NEXUSPAY for $89.12",human
C02,T03,"> I don't recognize a charge... Following up, please advise",human
...
```

Then:

1. Train a quick baseline. Logistic regression on TF-IDF is fine here. Evaluate it with a random message-level split, then with a `customer_id` group split. Record the gap.
2. Deliberately add a leaky feature: append "— Disputes Team" to some `human` messages. Measure how much the random-split score jumps.
3. Write one sentence on what your input contract must exclude.

---

## Level 2: What makes an eval good or bad

### The definition of a good eval

A good eval measures **the decision that matters**, on **the distribution you will actually see**, with **a scoring rule that matches the cost of errors**.

Each phrase rules something out:

- **"The decision that matters"** rules out measuring 5-way routing accuracy when the real risk is a binary question: "did something risky get auto-handled?"
- **"The distribution you will actually see"** rules out a curated, balanced, English-only labeled set when production is 8% Spanish, 30% phone transcripts, and growing.
- **"A scoring rule that matches the cost of errors"** rules out accuracy and F1 when one error type costs 50 times more than the other.

### Failure modes, each with a mini example

**Proxy metric.** You measure what's easy instead of what matters. Example: you optimize top-1 queue accuracy, but the business cost lives entirely in whether *dispute* messages ever reach automation. Five-way accuracy improves while dispute misroutes stay flat.

**Goodharting.** The metric becomes the target and stops tracking reality. Example: the team is rewarded on "automation rate." Someone lowers the threshold, automation goes from 45% to 62%, and false accepts quietly triple. Any single number you optimize needs a *guardrail* number you don't.

**Contaminated set.** Test examples leaked into training, as in Level 1. A subtler version: annotators labeled the test set *after* seeing model predictions and anchored on them. The set then measures agreement with the model, not correctness.

**Too-easy set.** The set is 90% "what's my balance" messages that any keyword rule gets right. The hard 10% decides your risk, and its contribution to the overall score barely moves.

**Missing slices.** The eval set has zero business-account messages, zero phone transcripts, or zero messages over $10k. You can't measure what isn't there. A missing slice is not a pass.

**Class imbalance.** If 3% of messages are fraud reports, "always route to non-fraud" scores 97% accuracy. Any metric that rewards the majority class will praise a useless model.

**Label noise.** Gold labels are wrong 8% of the time. Your model can't measurably exceed about 92% agreement with gold, and model differences under 2–3 points are dominated by which items happened to be mislabeled. In early datasets, a large share of apparent "model errors" turn out to be label errors.

**Happy path only.** Every eval message is clean, complete, and single-intent. Real messages say things like "pay my card and also why was I charged twice?" You need examples that are multi-intent, truncated, empty, in the wrong language, or carrying missing context fields.

### Checklist: does this eval measure the wrong thing?

Run this before trusting any eval.

| Check | Symptom | Example |
|---|---|---|
| **Wrong unit of decision** | You score at a different granularity than you act on | Scoring per message when routing is per thread; scoring the 5-way label when the action is binary auto/human |
| **Wrong label** | Gold means something different from what the action needs | Gold is "queue the agent eventually used," which reflects queue workload, not the correct route |
| **Wrong population** | Eval data ≠ production traffic | Eval from the web form; production adds phone transcripts with ASR errors |
| **Wrong cost asymmetry** | Errors weighted equally when they aren't | F1 headline for a decision where a false accept costs 50× a false reject |
| **No calibration** | Thresholds set on scores that don't mean what they say | "0.9 confidence" is right 70% of the time, so the threshold is a guess |
| **No slice breakdown** | One aggregate number | 95% overall, 60% on Spanish, never seen because nobody looked |

### Common metrics, and when each is the wrong headline

| Metric | What it answers | Wrong headline when… |
|---|---|---|
| **Precision** (of accepts) | Of what we auto-handled, how much should have been? | Missing items is costly; precision ignores what you rejected |
| **Recall** (of accepts) | Of what was automatable, how much did we automate? | False accepts are costly; recall rewards accepting everything |
| **F1** | Harmonic mean of precision and recall | Costs are asymmetric (almost always in banking). F1 weights FA and FR equally and ignores true negatives entirely |
| **ROC-AUC** | Does the model rank positives above negatives? | You ship a single threshold. Under heavy imbalance, many easy negatives inflate AUC; 0.97 AUC can coexist with a poor operating point |
| **PR-AUC** | Ranking quality focused on the rare class | Comparing across datasets with different base rates (PR-AUC moves with prevalence), or when you only care about one region of the curve |
| **Calibration / ECE** | Do scores mean what they say? | Used as the sole headline. Predicting the base rate for every example is perfectly calibrated and useless. ECE is also sensitive to the binning choice |
| **Confusion matrix** | Exactly which errors happen | Never wrong to *look at*, but it isn't a number, so it can't be a headline or a gate. Gates need scalars per slice |
| **Cost-weighted error** | What do errors cost us? | Costs are made-up guesses presented as facts, or a "never" constraint is folded into a weight. A regulatory "must not" is a constraint, not a cost |

ECE, for reference: bin predictions by confidence and compute `Σ_b (n_b / N) · |accuracy_b − confidence_b|`. For multi-class, use the top-label confidence. Always look at the reliability diagram alongside the number.

### Worked example: routing banking requests with asymmetric costs

**Decision:** route a message to the automated payment-status flow (`accept`) or to a human (`reject`).

**Eval set:** 1,000 messages. 700 are genuinely automatable and 300 need a human.

**Costs:**

- **False accept (FA).** A needs-human message gets auto-handled. Average cost is about $150: a delayed fraud report, a complaint, rework, and sometimes a missed regulatory clock.
- **False reject (FR).** An automatable message goes to an agent. Cost is about $3 of agent time.

Here is the same model at two thresholds:

| | Threshold 0.50 | Threshold 0.85 |
|---|---|---|
| Accepted | 690 (660 correct, **30 FA**) | 560 (555 correct, **5 FA**) |
| Rejected | 310 (270 correct, 40 FR) | 440 (295 correct, 145 FR) |
| Accuracy | **93.0%** | 85.0% |
| F1 (accept class) | **0.950** | 0.881 |
| Automation rate | 69% | 56% |
| Expected cost | 30×150 + 40×3 = **$4,620** | 5×150 + 145×3 = **$1,185** |

Accuracy and F1 both prefer 0.50. The cost metric says 0.85 is about 4× cheaper. The headline metric picks the winner, which is why choosing the headline is part of eval design.

**In general,** you would sweep thresholds and choose the cheapest one subject to a minimum automation rate.

**On a regulated workflow,** I would add a **constraint layer** that cost can't buy its way out of. Some of those 5 false accepts might be dispute messages subject to Reg E error-resolution timelines. That isn't a $150 cost. It's a compliance failure. So the gate becomes: **"0 FA on the dispute/fraud slice"** plus **"total cost ≤ $X."**

You also need to be honest about what zero means. **Zero errors in n examples gives a 95% upper bound of roughly 3/n** (the "rule of three"). Zero false accepts on 60 dispute examples means the true rate could still be as high as about 5%. To claim it's under 1%, you need about 300 clean dispute examples.

A small JS helper for the threshold sweep:

```js
// rows: [{ score, label, slice }]; label 1 = automatable, 0 = needs human
function evaluateAt(rows, t, costFA = 150, costFR = 3) {
  let ta = 0, fa = 0, fr = 0, tr = 0;
  for (const { score, label } of rows) {
    const accept = score >= t;
    if (accept && label === 1) ta++;
    else if (accept && label === 0) fa++;
    else if (!accept && label === 1) fr++;
    else tr++;
  }
  const n = rows.length;
  return {
    t,
    accuracy: (ta + tr) / n,
    automationRate: (ta + fa) / n,
    faCount: fa,
    cost: fa * costFA + fr * costFR,
  };
}

const sweep = [0.3, 0.5, 0.7, 0.85, 0.95].map(t => evaluateAt(rows, t));
console.table(sweep);
```

### Level 2 self-check

1. Model A has a higher ROC-AUC than model B but a higher expected cost at your chosen operating point. Which do you ship, and why isn't this a contradiction?
2. Your eval shows 0 false accepts on 40 high-value payment messages. What can you honestly claim about the false-accept rate?
3. Why should "never auto-handle a fraud report" be a gate rather than a large cost weight?

### Level 2 exercise: watch the winner flip (about 3 hours)

1. Label **80 messages** as automatable or needs-human, with about 25% needs-human. Tag each with one slice: `dispute`, `payment_status`, `balance`, or `other`.
2. Assign scores. You can use your model, a TF-IDF baseline, or hand-assigned scores that mimic a plausible model.
3. Run the sweep above at five thresholds. Make a table of accuracy, F1, automation rate, false-accept count by slice, and cost.
4. Find the threshold that wins on F1 and the one that wins on cost. Check whether they differ.
5. Bin the scores into 5 buckets and compare the average score to the actual accept rate in each bucket. That is your first reliability diagram.

---

## Level 3: Designing evals for a decision model

### The spec template, with example values

Write this down *before* labeling, because it dictates what you label.

| Field | Example for the auto/human router |
|---|---|
| **Decision** | Whether a message can be handled by the payment-status automation without human review |
| **Action on accept** | Bot replies with payment status, closes the ticket. No money moves |
| **Labels** | `auto`, `human`, `ambiguous` (kept as its own label, never forced into one of the others) |
| **Label definition** | `auto` if a correct, complete answer needs only payment-status data and the message contains no dispute, fraud, complaint, or hardship signal |
| **Input contract** | Redacted message text, channel, product type, account type (personal/business). No agent notes, no post-decision fields |
| **Slices** | Language (en/es/other); product (card/loan/deposit); amount band (<$500, $500–5k, >$5k); channel (secure msg/web form/phone transcript); ambiguity (annotator-flagged); intent count (single/multi) |
| **Gold set size** | 600 total; ≥60 per slice; ≥300 dispute-signal examples for the critical slice |
| **Annotation** | Two independent annotators per item, adjudication by a senior agent, written guidelines with 20 worked examples |
| **Inter-annotator agreement** | Cohen's κ ≥ 0.75 overall; slices below 0.6 are flagged as task problems, not model problems |
| **Pass bar** | 0 FA on dispute/fraud; FA rate ≤ 1% overall (upper 95% bound); cost ≤ current baseline; automation ≥ 40% |

**Why inter-annotator agreement belongs in the spec.** If two trained humans agree only 70% of the time, your model can't meaningfully score above roughly 70% agreement with either of them. More importantly, the *task* is underspecified.

Cohen's kappa is `κ = (p_o − p_e) / (1 − p_e)`, where `p_o` is observed agreement and `p_e` is the agreement you'd expect by chance. For example, two annotators agree on 42 of 50 items (`p_o = 0.84`), and given their label frequencies chance agreement is 0.50. Then κ = 0.34 / 0.50 = **0.68**: moderate. Read the 8 disagreements before labeling anything else. They are usually the most informative items in the whole set.

For three or more annotators, or when annotators skip items, use Krippendorff's alpha instead.

### Error analysis: from failures to decisions

1. **Sample.** Pull 50–100 errors, stratified by FA vs FR and by confidence (high-confidence errors and near-threshold errors separately). Don't just read the first 50, which over-samples whatever came first in the export.
2. **Open-code.** For each error, write one free-text sentence on why it went wrong. Don't use categories yet.
3. **Cluster.** Group the sentences into 4–8 named clusters and count them.
4. **Decide per cluster.** For each cluster, choose a fix:

| Cluster (example counts out of 60 errors) | Diagnosis | Fix |
|---|---|---|
| 18: gold label is wrong on re-read | Label noise | **Fix labels**; update guidelines |
| 14: multi-intent ("pay my card + why double charged?") | Task assumes one intent | **Change the task**: any secondary dispute signal → human |
| 11: scores between 0.45 and 0.6, ranking is fine | Operating point | **Change threshold** or add an abstain band |
| 9: Spanish messages | Under-represented in training | **Fix data**: add training examples |
| 8: needs last-transaction context to decide | Input lacks the information | **Change the input contract** |

The most common early surprise is that the biggest cluster is wrong *gold*, not wrong model. The second most common is that a cluster is undecidable from the input alone, which means the input contract is wrong. No amount of model training fixes that.

### Thresholds and operating points

A score is not a decision. Treat these as part of the shipped artifact:

- **Pick the threshold on validation data, never on test.** Then report test performance *at that fixed threshold*.
- **State results at an operating point.** "At a false-accept rate ≤ 0.5%, automation rate is 52% (95% CI 47–57%)" is a deployable claim. "AUC is 0.96" is not.
- **Use a three-way decision.** Accept above t_high, reject below t_low, send to human review in between. Evaluate this with a **coverage vs. risk curve**: as you widen the abstain band, coverage (the fraction decided automatically) drops and error among the decided items drops. You choose the point on that curve.
- **Calibrate** before thresholding, for example with temperature scaling on validation. Then 0.85 means roughly 85%, and a new checkpoint's threshold means the same thing as the old one's. Without calibration, every retrain silently moves your operating point.
- **Per-slice thresholds** can help, for example a stricter threshold for business accounts. They add complexity and governance burden, so use them only when error analysis shows a slice behaves differently, and document them.

### Regression evals: winning overall while breaking a slice

| Slice | Checkpoint v3 (FA / n) | Checkpoint v4 (FA / n) |
|---|---|---|
| Overall cost | $1,310 | **$1,020** ✅ |
| English | 4 / 480 | 2 / 480 |
| Spanish | 0 / 80 | **3 / 80** ❌ |
| Dispute signal | 0 / 300 | 0 / 300 |
| Phone transcript | 2 / 90 | 1 / 90 |

v4 is cheaper overall and worse on Spanish. If Spanish is a must-pass slice, v4 doesn't ship, no matter how good the aggregate is.

Three practices make regressions visible:

1. **Slice table on every candidate.** Compare against the current production model, not just against the gate.
2. **Flip analysis.** Because both models score the same examples, count the items whose prediction *changed*. Use `b` for items v3 got right and v4 got wrong, and `c` for the reverse. Two models with identical accuracy can disagree on 5% of items. Read the `b` items, because each one is a customer who used to get the right outcome. McNemar's test on b vs. c tells you whether the net change is real or noise.
3. **A pinned "never-regress" set.** Keep 50–150 hand-picked critical examples: past incidents, regulator-sensitive phrasings, known traps. Every one must keep its correct outcome. This works like a unit-test suite for the model.

### Small-data reality

Before you have thousands of labels, "good enough" looks like this:

- **100–300 carefully adjudicated gold examples** beat 3,000 noisy ones. Double-label everything at this stage.
- **Report intervals, not points.** With n = 200, a 3-point difference is usually noise.
- **Use cross-validation for model selection**, with group splits. Keep a small locked test set you look at rarely, ideally once per release candidate.
- **Add behavioral tests** in the style of CheckList. They need no new labels:
  - *Invariance:* changing the name, a non-salient amount, or the date must not flip the route.
  - *Directional:* appending "I didn't authorize this" must not *increase* the auto score.
  - *Minimum functionality:* 20 obvious cases per class must be correct.
- **Make claims you can defend.** "0 dispute FA out of 60, so the rate is ≤ about 5% at 95% confidence, and we will run in shadow mode to tighten that" is honest and actionable.
- **You know the eval is adequate for this stage when** you can name your top three error clusters, every critical slice has at least some examples, and you know what you'll learn next from shadow traffic.

### Level 3 self-check

1. Inter-annotator κ on the business-account slice is 0.45. Do you add more training data for that slice? What do you do instead?
2. A new checkpoint has 0.4 points better accuracy and flips 6% of predictions. What do you look at before deciding?
3. Most errors cluster at scores between 0.4 and 0.6, and the score ranking looks good. Is this a data problem or a threshold problem, and what would you build?

### Level 3 exercise: agreement, clusters, and a regression (an afternoon)

1. Take 50 genuinely ambiguous messages. Have two people label them independently: you and a colleague, or you on two days a week apart. Compute κ.
2. Write half a page of guidelines from the disagreements. Relabel and recompute κ.
3. Train two checkpoints, for example different seeds or epochs. On a 100-example set, build a slice table and a flip table (b and c counts). Read every `b` item.
4. Open-code and cluster 30 errors. Assign each cluster one fix: data, label, threshold, task, or input contract.

---

## Level 4: Using this on a Next.js / Postgres / MuleSoft banking project

### Where evals live outside the model

The model is one component. Most production incidents in decision systems come from the plumbing around it: fields that weren't populated, a retry that ran twice, a timeout that defaulted to "accept," a flag that wasn't flipped back. Each layer needs its own checks.

| Layer | What to verify | Concrete check |
|---|---|---|
| **API contract** (Next.js route ↔ model service) | Schema, enums, versioning, defined behavior for bad input | Contract tests (e.g., Pact) that fail CI if the model service adds a label or renames a field. Missing or invalid input → `review`, never `accept` |
| **MuleSoft integrations** | Timeouts, retries, partial enrichment, error mapping | MUnit tests with mocked endpoints: enrichment timeout → decision downgraded to `review`; a 5xx from core → no auto action |
| **Postgres invariants** | Things that must never be true in the data | Constraints (CHECK, FK, UNIQUE) plus nightly invariant queries that must return 0 rows |
| **Idempotency** | Retries don't double-decide or double-act | The same idempotency key returns the stored decision instead of re-scoring. Test by replaying a request 3 times |
| **Audit log** | Every decision is reproducible and attributable | Test that each decision row has model version, threshold version, score, input hash, final route, and actor |
| **Feature flags** | Kill switch works; both paths are tested | CI runs the suite with the model on and off. "Off" routes everything to the legacy path or to humans |
| **Human review queue** | Abstained items land there and outcomes come back | Test that the abstain band creates a queue item. Track queue depth and SLA as operational metrics. Reviewer decisions write back as labels |

One design rule matters more than any of these: **fail closed.** Any missing input, timeout, unknown label, flag lookup error, or schema mismatch should resolve to human review, never to automation. Write that rule as a test.

### Mapping model slices onto product risk

Eval slices should come from the risk register, not from whatever metadata happens to be convenient.

| Slice | Why it's risky | Tier | Eval requirement |
|---|---|---|---|
| Payment-initiating vs. inquiry | Payments move money; inquiries don't | 1 vs. 3 | Payment-initiating may never be `accept` for an action that executes; inquiry can automate |
| Dispute / fraud / unauthorized language | Reg E and network timelines; customer harm | 1 | 0 FA; ≥300 gold examples; pinned never-regress set |
| High value (e.g., > $5k band) | Loss magnitude | 1 | Stricter threshold or always review |
| New counterparty / payee | Fraud and scam pattern | 1 | Always review, or a separate slice with its own gate |
| Business accounts | Different products, different authority rules | 2 | Slice gate on FA rate |
| Non-English | Fairness and service obligations; less training data | 2 | Slice gate; no regression vs. production |
| Phone transcripts (ASR) | Noisy input | 2 | Slice gate; invariance tests on transcription errors |
| **MuleSoft partial failure** (enrichment missing) | Model sees degraded input | 1 | Eval the gold set with enrichment fields nulled out; system rule: missing enrichment → no auto for tier-1 products |

The last row is the bridge between model eval and integration eval. **Build a "degraded input" copy of your gold set** with the fields that MuleSoft sometimes fails to populate set to null. Then measure how the model behaves in exactly the conditions the integration produces under stress.

### Offline vs. online

**Offline eval** happens on the gold set before release. It is necessary, and it is never sufficient, because production traffic drifts and your gold set is old the day you freeze it.

Online checks, in the order you'd adopt them:

1. **Shadow mode.** The model scores live traffic, but the decision isn't acted on. The existing process (humans or rules) still decides. You compare the model's decision to what actually happened. This gives you a production-distribution eval with zero customer risk.
2. **Canary.** The model acts on a small percentage of traffic, perhaps only tier-3 slices, with automatic rollback triggers such as an override rate above X or a queue spike.
3. **Disagreement sampling.** Send to labeling: (a) items where the model disagrees with the legacy process or a human, and (b) items near the threshold. This is where new gold examples come from most efficiently.
4. **Drift monitoring.** Track input mix (channel, language, product, message length), score distribution (Population Stability Index against the eval-time baseline), automation rate, and human override rate. Drift doesn't mean the model is wrong. It means the eval no longer describes reality, so re-run it.

One subtlety bites every team: **you only observe outcomes for what you did.** If the model auto-handles a message, no human looks at it, so you never learn it was a false accept unless the customer complains, and complaints are a delayed, biased, partial signal. The fix is a **random audit sample of accepted items**, for example 1–2% sent to human review regardless of score. That audit sample is the only unbiased estimate of your production false-accept rate. On a regulated workflow I wouldn't treat this as optional.

### What to log

You want to rebuild an eval set from production later without storing secrets. Log decisions with pointers, not raw sensitive data.

```sql
CREATE TABLE decision_log (
  decision_id        uuid PRIMARY KEY,
  request_id         text NOT NULL,           -- upstream id
  idempotency_key    text NOT NULL UNIQUE,
  received_at        timestamptz NOT NULL,
  channel            text NOT NULL,
  product            text,
  account_type       text,
  amount_band        text,                    -- banded, never raw amount
  language           text,
  enrichment_status  text NOT NULL,           -- complete / partial / timeout
  input_hash         text NOT NULL,           -- sha256 of redacted input
  redacted_input_ref text,                    -- pointer into restricted store
  model_version      text NOT NULL,
  threshold_version  text NOT NULL,
  score              numeric NOT NULL CHECK (score BETWEEN 0 AND 1),
  model_decision     text NOT NULL CHECK (model_decision IN ('accept','review','reject')),
  rule_override      text,                    -- e.g. 'high_value_force_review'
  final_route        text NOT NULL,
  audit_sampled      boolean NOT NULL DEFAULT false,
  human_decision     text,
  reviewer_id        text,
  final_outcome      text,                    -- filled later: resolved / complaint / dispute_opened
  outcome_at         timestamptz
);
```

Rules for this table:

- **Redact before both inference and logging.** Tokenize card and account numbers, SSNs, and similar identifiers at the edge. The model should never need them for routing, so they shouldn't be in the input contract either.
- **Store a pointer, not a copy.** Redacted text lives in a restricted store with its own retention policy. The log keeps a reference and a hash, so you can prove which input produced which decision.
- **Version thresholds separately from models.** A threshold change is a release. It needs to be visible in the log and reviewable.
- **Follow your institution's data classification and retention policy.** That policy decides how long the restricted store keeps text, not the convenience of building eval sets.

Invariant queries that must return 0 rows, run nightly and in CI against seeded data:

```sql
-- 1. Auto action without model accept, unless a rule explains it
SELECT * FROM decision_log
WHERE final_route = 'auto' AND model_decision <> 'accept' AND rule_override IS NULL;

-- 2. Fail-closed: no auto when enrichment was incomplete
SELECT * FROM decision_log
WHERE final_route = 'auto' AND enrichment_status <> 'complete';

-- 3. Tier-1 products never auto
SELECT * FROM decision_log
WHERE final_route = 'auto' AND product IN ('dispute','fraud','payment_initiation');

-- 4. Same request decided differently (idempotency broken)
SELECT request_id FROM decision_log
GROUP BY request_id HAVING count(DISTINCT final_route) > 1;

-- 5. Decisions from unapproved model versions
SELECT * FROM decision_log
WHERE model_version NOT IN (SELECT version FROM approved_models WHERE active);
```

These are evals too, just on system behavior rather than model behavior. They are fully automatic, they need no labels, and when one of them returns rows it is an incident.

### A release gate a team could actually adopt

**In general:** a gate is a short list of conditions that are checkable by script, agreed on *before* results come in, and not renegotiated after.

**On a regulated workflow,** I would also require that the gate itself is versioned, that results are archived with the release, and that model-risk sign-off is part of it. Many institutions follow SR 11-7-style model risk management principles even outside Fed supervision. Ask your compliance team which framework applies to you.

The gate has three kinds of conditions:

1. **Must-pass slices** (absolute). 0 FA on dispute/fraud, high-value, and new-counterparty gold. The never-regress set is 100% correct. The degraded-input set has 0 accepts on tier-1.
2. **Cost ceiling** (relative to production). Expected cost on the full gold set is at most the current production model's, at the release threshold.
3. **No-regression rule** (relative, per slice). No tier-1 or tier-2 slice has worse FA than production beyond a noise margin set in advance. Every `b` flip (production right, candidate wrong) in tier-1 slices is read and signed off.

If any condition fails, the release doesn't go out. "But the overall number went up" is not an exception.

### Level 4 self-check

1. The enrichment call times out and the model gets a message with null product and account type. Where should that case be caught: in the model, the API, the database, or all three? What does each layer do?
2. Your production false-accept rate, estimated from customer complaints, is 0.1%. Why don't you trust that number, and what would you build to get a better one?
3. A teammate raises the threshold from 0.85 to 0.80 in a config file to hit an automation target. Which parts of your system should have caught that, and how?

### Level 4 exercise: the mini harness (an afternoon)

1. Create `decision_log` in a local Postgres. Seed 30 rows by hand, including 5 deliberately bad rows: auto with timeout, auto on dispute, a duplicate request with different routes, an unapproved model version, and auto without accept.
2. Run the five invariant queries and confirm each one catches its planted row.
3. Write a small Node script that reads gold-set predictions for two checkpoints and prints a slice table, a flip table, and PASS/FAIL against a `gate.json` file containing must-pass slices, the cost ceiling, and the regression margin.
4. Simulate a MuleSoft timeout with a stub in your Next.js API route. Assert that the decision becomes `review`.

---

## Template: One-page eval spec

```markdown
# Eval Spec — <model name> v<spec version>
Owner: ________  Reviewers: ________  Date frozen: ________

## 1. Decision
- Decision being made: ______________________________________
- Action taken on each output (accept / review / reject): ____
- Who/what consumes the score: ______________________________

## 2. Labels
- Label set: ______________________ (include `ambiguous`? Y/N)
- Label definitions (link to guidelines): ____________________
- Gold source: [ ] fresh annotation  [ ] adjudicated history  [ ] other: ___

## 3. Input contract
- Fields available at decision time: _________________________
- Fields explicitly EXCLUDED (post-decision, leaky, sensitive): ___
- Redaction applied before inference: ________________________
- Behavior when a field is missing: __________________________

## 4. Data & splits
- Time window: ________  Split method: [ ] time [ ] group by ______
- Dedup method & threshold: _________________________________
- Locked test set location; who may view; how often: _________

## 5. Slices (min n per slice)
| Slice | Values | Risk tier | Min n | Current n |
|-------|--------|-----------|-------|-----------|
| Language | | | | |
| Product | | | | |
| Amount band | | | | |
| Channel | | | | |
| Ambiguity / multi-intent | | | | |
| Degraded input (enrichment missing) | | | | |

## 6. Annotation quality
- Annotators per item: ___  Adjudicator: ________
- Agreement metric: κ / α  Target: ___  Actual (overall / worst slice): ___ / ___

## 7. Scoring
- Cost of false accept: $___  Cost of false reject: $___  (source: _____)
- Hard constraints (not costs): _______________________________
- Calibration method: ______  Calibration check: ECE + reliability diagram
- Thresholds: t_high ___  t_low ___  (chosen on: validation set ______)

## 8. Behavioral tests
- Invariance: ____________________  Directional: ________________
- Never-regress set: n = ___, location: _______________________

## 9. Pass bar
- Must-pass slices: ___________________ (FA = 0, report 95% upper bound)
- Overall: cost ≤ ___ ; FA rate upper bound ≤ ___ ; automation ≥ ___
- Regression rule vs. production: no tier-1/2 slice worse by > ___

## 10. Reporting
- Slice table, flip table (b/c + McNemar), coverage–risk curve,
  confusion matrix, top error clusters with chosen fix
```

---

## Template: One-page release checklist

```markdown
# Release Checklist — <service> release <id>   Date: ______

## Model gate (from eval spec)
- [ ] Eval spec version ___ frozen before results were viewed
- [ ] Must-pass slices: 0 FA (dispute/fraud, high-value, new payee) — upper bounds recorded
- [ ] Never-regress set 100% correct
- [ ] Degraded-input set: 0 accepts on tier-1
- [ ] Expected cost ≤ production at release threshold
- [ ] No tier-1/2 slice regressed beyond agreed margin
- [ ] All tier-1 "b" flips read and signed off by: ________
- [ ] Calibration checked; threshold version ___ recorded

## Contract & integration
- [ ] API contract tests pass (Next.js ↔ model service)
- [ ] MUnit tests pass: timeout, 5xx, partial enrichment → review
- [ ] Fail-closed test: missing/invalid input → review, never accept
- [ ] Idempotency replay test: same key 3× → one decision, one action

## Data & audit
- [ ] Postgres constraints migrated; invariant queries return 0 on seeded + staging data
- [ ] Decision log captures model_version, threshold_version, score, input_hash, route, enrichment_status
- [ ] No raw sensitive identifiers in logs or model inputs (verified by scan)
- [ ] Audit sample rate configured: ___% of accepts → human review

## Rollout
- [ ] Feature flag tested ON and OFF in CI; kill switch owner: ________
- [ ] Shadow period complete: ___ days, model vs. actual disagreement reviewed
- [ ] Canary scope (slices / %): ________  Rollback triggers: override rate > ___, queue depth > ___, any invariant row
- [ ] Review queue capacity confirmed for expected abstain volume

## Monitoring
- [ ] Dashboards: input mix, score PSI, automation rate, override rate, audit-sample FA
- [ ] Alert owners named: ________
- [ ] Re-eval trigger defined (e.g., PSI > 0.2 or override rate +50%)

## Sign-off
- [ ] Engineering ____  [ ] Product/Ops ____  [ ] Model risk / Compliance ____
- [ ] Eval artifacts archived with release: location ____________
```