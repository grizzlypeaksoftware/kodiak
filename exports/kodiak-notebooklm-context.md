# Kodiak: the complete project context

*A self-contained briefing on the Kodiak project: what it is, why it exists, how it works, what happened while building it,
what was learned, and where it's going. Written for use as a NotebookLM source. Current as of the evening of September 24, 2026.*

---

## 1. Kodiak in one paragraph

**Kodiak** is an open-source "System One" decision model built by **Shane Larson** (Cortex Agent LLC / Grizzly Peak Software)
on a single personal NVIDIA DGX Spark, with Claude (Anthropic's AI) as pair engineer. You give Kodiak a *state* (a piece of
text, a list of messages, or a JSON record) and a set of *typed questions*: multiple-choice questions whose options you define
on the fly, numeric scores on a scale you choose, and for every question the option of saying "this can't be answered from
what I was given." Kodiak answers **all the questions at once, in a single pass, in about 8 milliseconds**, and every answer
comes with a calibrated probability. It never generates text, so it can't ramble, can't break a format, and can't answer
outside the options it was given. It's a small bidirectional *encoder* (about 152 million parameters), not a chat LLM,
which is the whole point: most of what software asks LLMs to do isn't really writing, it's deciding.

**One-line pitch:** *a 150M-parameter model that answers typed decision questions about any text in 8 ms with trustworthy
confidence, roughly 400 times faster than asking a 27-billion-parameter LLM the same questions.*

---

## 2. People, project, and principles

- **Shane Larson:** project owner and creator. Experienced software engineer, new to training ML models. Runs Cortex Agent
  LLC and Grizzly Peak Software, and uses the same DGX Spark for a book-publishing business. Made every call on scope,
  naming, licensing, budget, hardware, and data spending, and personally human-reviewed synthetic training data.
- **Claude (Anthropic):** pair engineer. Designed, implemented, experimented, and documented, working in review loops
  where Shane approved each phase before the next began.
- **Copyright:** Cortex Agent LLC. **License:** Apache-2.0. **Repo:** github.com/grizzlypeaksoftware/kodiak.
  **Python package:** `kodiak-s1` ("System One"), because the name "kodiak" was already taken on PyPI, npm, GitHub, and Hugging Face.
- **It's a learning project:** every step explains its *why*, and those explanations live in a project journal. Making the
  journey legible is as much a goal as the model.
- **Budget:** $0 for hardware beyond the Spark Shane already owned. The only money spent so far is a few dollars of cloud
  inference for generating training data.

---

## 3. Why build it: "System One" decisions

In September 2026 an AI company called TypeSafe AI launched **Jev**, which it describes as a "System One" decision model.
The phrase echoes Daniel Kahneman's split between fast, intuitive "System 1" thinking and slow, deliberate "System 2" thinking.
The idea struck Shane: an enormous amount of what software asks large language models to do isn't writing at all. It's
decisions:
- *What does this customer want?*
- *How urgent is this ticket?*
- *Which tool should this AI agent call next?*
- *Is this message spam? A prompt injection? Toxic?*
- *Can this question even be answered from the information we have?*

Using a chat LLM for these means paying for slow, token-by-token text generation, then parsing the output and hoping it stayed
inside the expected format. Kodiak answers them directly.

Kodiak is **inspired by** Jev but built independently, from first principles. The team has no access to Jev's internals and
makes no claims about matching it. (Shane believes Jev uses its own custom encoder; that's unverified.) The term "RLCD" came
up during calibration planning; nobody on the project knows exactly what it refers to, so Kodiak deliberately doesn't claim
to replicate it.

---

## 4. The rules Kodiak was built under

1. **No autoregressive LLM backbone, and no constrained decoding of a chat model.** That approach is the thing Kodiak is trying to beat.
2. **Structurally unable to answer outside the answer space.** A choice answer is always one of the options you supplied, and a score
   is always inside your range. "Not answerable" is always a legal answer. There's no text output and nothing to parse.
3. **Everything in one forward pass, with calibrated probabilities.** When Kodiak says 80%, it should be right about 80% of the time.
4. **Permissive licenses only**, for both data and base models, so the weights can be released under Apache-2.0.
5. **An honest comparison** against a local LLM on the same evaluation.
6. **Guerrilla economics:** start small, reuse what others have already paid for, and scale only when evidence says so.

---

## 5. The machine: one NVIDIA DGX Spark

- ARM CPU (NVIDIA Grace, 20 cores) plus an NVIDIA **GB10** Blackwell GPU.
- **121 GiB of *unified* memory**, shared by the CPU and GPU. There's no separate GPU memory, so a local LLM, the desktop,
  and a training job all compete for the same pool. On day one, two resident Ollama models held about 50 GB and the
  system was already swapping, so one of the first decisions was a rule: *teacher models and training jobs take turns.*
- 3.7 TB NVMe disk; Ubuntu 24.04; CUDA 13; PyTorch 2.14 with native ARM wheels (no container needed).
- Measured: about **94 TFLOP/s** bf16 matrix-multiply peak. Training runs at roughly a third of that, because the Spark's memory
  bandwidth, not its compute, limits the many small operations in a transformer.
- A local status dashboard (a small Python server on localhost) shows phase progress, data-generation runs with ETAs and
  dollar costs, training curves, eval results, and GPU temperature, memory, and disk.

---

## 6. How Kodiak works (the architecture)

### 6.1 The core trick: one sequence, a structured attention mask
A request is packed into one token sequence:

```
[CLS] state [SEP] | [CHOICE] question 1 | [LABEL] option A | [LABEL] option B | [SCORE] question 2 | ...
```

A transformer's *attention mask* decides which tokens can "see" which. Kodiak's mask is structured:
- **State tokens see only the state.** So the state is encoded once, identically, no matter how many questions are asked
  (and could later be cached).
- **Each question sees the state, itself, and its own options.**
- **Each option sees the state, its question, and itself**, but not the other options.

**Position ids** are chosen so every question block "starts at the same place," and every option of a question starts at the
same place too. Three guarantees follow *by construction*, and they're verified by automated tests:
1. A question's answer is identical whether it's asked alone or with 30 others, in any order.
2. Shuffling the options can't change any probability. The classic LLM bias of "preferring option A" is impossible.
3. Several requests can be packed into one training row without seeing each other.

### 6.2 The heads (the "decision layer")
- **Choice head:** scores each option by matching its encoding against the question's (features: option, question, and their
  product). Options are represented by their *text*, so **brand-new label sets work zero-shot**; there are no fixed classes.
- **Null head:** a per-question probability that the question is unanswerable from this state.
- **Score head:** predicts a **Beta distribution** on [0,1], parameterized by a mean and a "concentration," then mapped to the
  requested range. A Beta can't go out of bounds, and it expresses uncertainty ("about 0.8, fairly sure" vs. "no idea"),
  which gives every score a real credible interval.

### 6.3 Training objective and calibration
Kodiak is trained to maximize the log-likelihood of the correct outcome under its full answer distribution (all options plus
"unanswerable"). That objective, log loss, is a **strictly proper scoring rule**: the model gets its best expected score only
by reporting its true beliefs, which is the foundation of calibration. After training, one **temperature** per head is fitted
on validation data (temperature scaling) to correct leftover overconfidence. It changes confidence numbers without changing
any answer.

An important framing: RL-based calibration methods for LLMs (such as RLCR, "Beyond Binary Rewards") exist because an LLM's
confidence is *text it writes*, so there's no gradient through it. Kodiak's confidence *is* its output distribution, so
ordinary training optimizes it directly. RL is reserved for an optional later stage that tunes *when to abstain* under a cost
of being wrong.

### 6.4 The backbone: ModernBERT (and why it's not an LLM)
Kodiak's reading ability comes from **ModernBERT-base** (Apache-2.0; 149.6M parameters; 22 layers; pretrained by Answer.AI
on about 2 trillion tokens). ModernBERT is an **encoder**: it reads a whole text at once, in both directions, and turns it into
vectors that represent meaning. It *cannot* generate text. It learned by filling in blanked-out words (masked language
modeling). An analogy Shane found useful: Kodiak "hires a fluent reader" (ModernBERT) and teaches it the job of making
decisions. Everything that makes it a decision model (the packing, the mask, the heads, the objective, the data) is Kodiak's
own design.

Kodiak re-implements ModernBERT's architecture in its own code (to control masks and positions) and loads the published
weights. A **parity test** proved the re-implementation is **bit-identical** to Hugging Face's reference: a maximum difference of
exactly 0.0 across 300 tokens.

### 6.5 Size and speed
- 151,968,772 parameters in total (the ModernBERT reader plus about 2.4M in Kodiak's heads); about 600 MB on disk.
- Training: about 34,000 tokens/second with `torch.compile` (17,000 without it); about 11 GB of memory.
- Inference: **about 8 ms per request** (all questions in one pass), versus about 3,400 ms for the 27B-parameter Qwen LLM on the same machine.

---

## 7. The two tracks, and why Track A was deferred

The original plan built two versions and compared them honestly:
- **Track A (pure):** pretrain an encoder from scratch, then teach it decisions.
- **Track B (pragmatic):** start from open pretrained weights (ModernBERT), then teach it decisions.

Once Track B was running, a striking asymmetry appeared: **decision-tuning Track B takes about an hour**, because the expensive
part, learning to *read*, was already paid for by ModernBERT's ~2 trillion tokens of pretraining. Track A would have
spent days of the Spark reading about 10 billion tokens, roughly 200× less, just to produce a clearly weaker reader. Shane
decided to **skip Track A for v0.1** and put the effort into Track B's data, calibration, and evaluation, with a **custom
encoder** as a future option "if Kodiak earns it." Ideas for that future encoder include pretraining shaped around decisions,
the more efficient ELECTRA-style objective, and continued pretraining of an open encoder on decision-like text.

---

## 8. The data

### 8.1 Public datasets (20 sources, permissive licenses only)
Every license was verified at its **upstream source**, not just the Hugging Face tag. Converted into Kodiak's format:
- **Natural language inference:** MultiNLI (with the fiction genre removed, because it contains share-alike text), SciTail
- **Multiple-choice reasoning:** CommonsenseQA, OpenBookQA, WinoGrande
- **Intent:** CLINC150 (out-of-scope requests become "unanswerable"), MASSIVE (English), Banking77 (held out)
- **Emotion and sentiment:** GoEmotions
- **Moderation scores:** Civil Comments (toxicity as a fraction of human raters, which is ideal for Beta targets), Measuring Hate Speech (held out)
- **Spam and safety:** SMS Spam, deepset prompt-injections, jailbreak classification (held out)
- **Response quality scores:** HelpSteer2, UltraFeedback
- **Tool routing:** Glaive function-calling v2, ToolACE (labels: call a specific tool, ask the user for missing details, or answer without a tool)
- **Occupation from biographies:** Bias in Bios (held out)
- **Long-document QA with unanswerable questions:** Qasper

**Totals:** 356k training / 10.9k validation / 27k test examples; about 53 million tokens per epoch. Four datasets are *held out*
(never trained on) to measure zero-shot generalization.

**Excluded on principle:** share-alike datasets (SNLI, BoolQ, SQuAD v2, ARC, FEVER), non-commercial ones (ANLI, SciQ,
ToxicChat), and ones with unclear terms (AG News, IMDB, SST-2, Yelp, and others).

### 8.2 The frozen eval set
2,902 examples / 4,189 questions: 1,578 in-domain, 1,000 from held-out datasets, 300 *constructed* unanswerable questions (a claim
about a different text, or the correct option removed), and 24 synthetic examples **human-reviewed by Shane**. It's never
trained on.

### 8.3 Synthetic data: an LLM teacher (labels only, never part of the model)
The generator asks a teacher LLM to write a realistic state (support chats, invoices, CI logs, game states, legal letters:
about 60 domains in three formats: text, lists, and JSON) plus 3–5 typed questions, including **deliberately unanswerable**
ones. Two quality gates:
1. **Evidence check:** every answerable question must quote the state, and the quote must really be there.
2. **Independent verification:** a *different* model answers the same questions blind; only agreements are kept.

**Human review** of 24 synthetic examples (64 questions) found **61 correct, 3 wrong, about 95% precision.** That's why headline
results use human-labeled data.

### 8.4 From local teachers to a cloud teacher
- **Local phase:** Qwen models via Ollama on the Spark: `qwen3.6:35b-a3b` (a mixture-of-experts model, 2.4× faster) writing and
  `qwen3.8:27b` verifying. It produced **3,290 examples**, but would have needed about 2 more days.
- **Rejected option: Grok.** xAI's terms forbid using outputs to build competing models, and Kodiak's released data would
  redistribute those outputs.
- **Chosen: DigitalOcean serverless inference with open-weight models only.** gpt-oss-120b (Apache-2.0) costs $0.10 per million
  input tokens and $0.70 per million output tokens.
- **Setup saga:** the first key returned "Unauthorized" despite correct settings. Checking the key's *shape* without ever printing
  it revealed it was **68 characters instead of 71**: it had been clipped when copied. Then every model returned **402 "Payment
  Required"** until Shane added $62 prepaid credit with auto-reload. A background watcher started the pilot automatically when
  access opened, about 35 minutes later.
- **Pilot #1 kept only 26%.** gpt-oss *paraphrases* its evidence ("Commenter: Jane Doe") instead of quoting the JSON
  (`"author":"Jane Doe"`), so the evidence check threw out correct answers, and the survivors skewed to unanswerable questions.
- **Pilot #2 kept 88%** after three fixes: ask for exact quotes, accept rewording when at least 80% of the evidence's content words
  appear in the state, and drop only the bad question instead of the whole job. **Cost: $0.73 per 1,000 jobs.** The whole pilot
  cost four cents.
- **The verifier bake-off.** Shane asked: why not let gpt-oss check its own work? Because a model tends to re-confirm its own
  systematic mistakes. Instead of arguing, the team measured it against Shane's human review:

| Checker | Keeps human-approved answers | Failures | Seconds/example |
|---|---|---|---|
| gpt-oss-120b | 92% | 2 (runaway JSON) | 26 |
| **DeepSeek V3.2 (MIT)** | **97%** | **0** | **2.3** |
| Qwen 3.5 397B | thought for ~215 s, then returned nothing | – | – |
| Qwen 27B (local) | 100%, *but only by construction*: the review set was built from Qwen-approved examples | – | – |

  **Result: gpt-oss-120b writes, DeepSeek V3.2 checks**, running 16 requests in parallel at about 1,600 jobs/hour and roughly
  $0.71 per 1,000 jobs. The local Qwen models were unloaded, and the Spark's GPU was freed for training.
- **Result:** the cloud run finished all 7,700 jobs by 5 PM on September 24 (83% kept; 9 timed-out jobs were retried). With the local
  run, the batch totals **9,702 synthetic examples** (3,290 local + 6,412 cloud), 97% of the goal, for about **$5.50** of gpt-oss
  output plus a small DeepSeek share.

---

## 9. Training the first model: `b-small-s1-v0`

**Name decoded:** **b** = Track B (ModernBERT backbone); **small** = the ~150M size; **s1** = stage 1 (states up to 512 tokens);
**v0** = the first, pilot version.

- **Data:** public datasets plus only 114 synthetic examples (generation was paused), with about 8% of training examples
  turned into unanswerable questions on the fly.
- **Recipe:** batches of 8 × 2,048 tokens; learning rate 5e-5 for the pretrained reader and 10× higher for the new heads; bf16; `torch.compile`;
  validation every 250 steps on every dataset.
- **Run:** early-stopped at step 3,250 of a planned 6,000, after about 35 minutes.

**The early-stopping bug.** Early stopping ends training when validation stops improving. It fired at step 3,250 and kept step 1,750
as "best," but the real tasks were still improving. The culprit was a **7-example synthetic validation group**. Its 114
training examples were being heavily oversampled, the model memorized them, and that group's loss doubled. In an unweighted
average, it outvoted 16 real datasets. On the frozen eval set, step 3,250 beat the "best" checkpoint (**77.2% vs. 74.6%**). Fix:
groups with fewer than 50 validation questions no longer count toward stopping.

---

## 10. The first evaluation: Kodiak v0 vs. Qwen 27B

The same 200 eval examples (280 questions), run on the same machine. Qwen got JSON-schema-constrained output and a prompt refined to
give it a fair shot.

| | Kodiak v0 (150M) | Qwen 27B |
|---|---|---|
| Accuracy, overall | 0.732 | 0.765 |
| Accuracy, in-domain | 0.755 | 0.765 |
| Accuracy, held-out datasets (zero-shot) | 0.649 | **0.860** |
| Abstain precision / recall | **0.90 / 0.79** | 0.68 / 0.39 |
| Calibration error (ECE, lower is better) | **0.095** | 0.192 |
| Score error (MAE, 0–1 scale) | **0.168** | 0.213 |
| Median latency per request | **8 ms** | 3,431 ms |

**Reading it honestly:**
- **Speed:** about 400× faster on the same box.
- **In-domain:** roughly a tie in accuracy on the kinds of tasks Kodiak trained on.
- **Calibration and abstention:** Kodiak's confidence is about twice as trustworthy, and its "unanswerable" is *learned*.
  Qwen's accuracy on unanswerable questions swung from 68% to 37% from prompt wording alone.
- **The weakness is new kinds of tasks:** 65% vs. 86%. A 27B generalist knows far more than a small encoder trained on 16
  datasets. That's the gap the synthetic data and Generator v2 target.
- **Caveats:** 200 examples (about ±5 points), an early model, and Qwen's confidence is self-reported.

**Making the baseline fair took three tries:**
1. The first prompt said "use only information in the state," and Qwen refused 96% of judgment questions ("how toxic is this?").
2. The fixed prompt still let Qwen answer scores like ">= 0.8", which the scorer counted as abstentions.
3. A numeric-or-"UNANSWERABLE" schema fixed it.

All three runs are kept on record.

**Calibration in practice:** temperature scaling cut the calibration error from 0.093 to 0.062 overall (in-domain 0.075 → 0.036),
without changing a single answer. Score intervals turned out well calibrated in-domain (0.89–0.94 coverage for a 90%
interval), once a metric bug was fixed (see §12).

---

## 11. A live demo

Request: *"Customer: My card was charged twice for order #4411 and I need it fixed before my rent is due Friday."* / *"Agent:
Sorry about that! Can you confirm the last four digits of the card?"*

| Question | Kodiak's answer | Verdict |
|---|---|---|
| What does the customer want? | **refund or billing fix** (64%) | ✅ |
| Which card brand? | **Unanswerable** (68%) | ✅ The text says "my card" but never names a brand. This is the headline behavior. |
| How urgent is this? | Unanswerable, or "not urgent" (0.10) when forced | ❌ Rent is due Friday |

**Why urgency failed:** every score question in the public training data is a moderation or quality rating (toxicity, hate
speech, helpfulness), mostly near zero, and none is about urgency. So the model learned "scores are usually low" rather than
how to read a new scale. It's a small, concrete example of the generalization gap. The demo also caught a real bug: the
documented shorthand for options (`"labels": ["a", "b"]`) crashed the inference path. It was fixed and a test was added.

---

## 12. Bugs, surprises, and lessons (the good stuff)

1. **Reading the data beats testing it.** Most of the important bugs were found by reading converted examples, not by unit tests:
   - tool-routing rows labeled "no tool" that were really delayed tool calls;
   - an NLI phrasing ("Does the text say that X?") that made "can't tell" read as "no";
   - a test set with *zero* out-of-scope examples, because "take the first N rows" of a sorted dataset is a biased sample.
2. **A JSON schema's field order changes an LLM's answers.** The Qwen verifier said "unanswerable" to almost everything, because its schema
   asked for `unanswerable: true/false` *before* it had looked for evidence. Asking for the evidence quote first fixed it.
3. **Constrained JSON has sharp edges:**
   - an unescaped quote ended a string early and truncated a document;
   - an LLM wrote multiple-choice questions with *no options* until the schema was split by question type;
   - JSON states written as escaped strings broke often, so they're requested as real objects instead.
4. **Data leakage hides in twins.** WinoGrande validation looked like 84% but was really 63% on the official dev set. The dataset is
   built from near-identical "twin" sentences, and the split separated twins. The fix is to split pairs together.
5. **Early stopping can stop for the wrong reason** when a tiny group dominates an unweighted average (see §9).
6. **Metric bugs can masquerade as model problems.** Interval coverage looked like 50% for a 90% interval, because many gold scores
   are exactly 0 or 1, and a Beta interval can never include an endpoint. The metric now nudges targets inward the same way training does.
7. **Baselines need their best shot:** three prompt and schema revisions before the Qwen comparison was fair (§10).
8. **Selection bias:** an evaluation set that was *filtered by a model* can't evaluate that model. The local Qwen verifier "agreed" with
   100% of the human-reviewed examples, because those examples were chosen by its agreement in the first place.
9. **A model shouldn't grade its own work.** Same-family checking repeats systematic errors; a different family (DeepSeek) did better.
10. **Pretraining is where almost all the cost lives.** Fine-tuning the decision layer takes about an hour, because someone else paid for reading.
11. **The design doc guessed wrong about data size** (2 billion tokens vs. 53 million measured), which moved the main risk from compute to overfitting.
12. **The Spark is bandwidth-bound, not compute-bound.** `torch.compile` doubled throughput by fusing many small operations.
13. **Parallel requests didn't help a saturated GPU,** but a model that does less work per token (a mixture-of-experts writer) did: 2.4×.
14. **Secrets can be debugged without being seen:** a clipped API key was found by checking its length and character classes, never its value.
15. **Engineering gotcha:** `pkill -f` killed its own shell (twice) when the pattern also appeared in the same command line.
16. **Thinking models can burn their entire token budget reasoning** and return nothing (Qwen 3.5 397B in the bake-off).

---

## 13. Key decisions (the decision log, D1–D26; D23–D26 are summarized in 14a–14c)

- **D1:** Encoder-only; no LLM backbone.
- **D2:** Name and namespace (`kodiak-s1` under grizzlypeaksoftware).
- **D3:** Permissive licenses only, verified upstream.
- **D4:** v0.1 scope: English, broad domains, 2k-token states.
- **D5:** One packed sequence with a structured attention mask.
- **D6:** "Null" is an answer every question can get, not a question type.
- **D7:** Beta distribution for scores.
- **D8:** Log loss + temperature scaling; RL only for the abstention policy.
- **D9:** Shared ModernBERT tokenizer.
- **D10:** Teachers and training take turns on unified memory.
- **D11:** Headline metrics use human-labeled data only.
- **D12:** Synthetic data gates: evidence quote + independent verification.
- **D13:** Mixture-of-experts writer + dense verifier (local phase).
- **D14:** Re-implement ModernBERT (bit-identical parity test).
- **D15:** `torch.compile` on by default.
- **D16:** Per-source validation + early stopping.
- **D17:** FineWeb-Edu for Track A (superseded).
- **D18:** Gated datasets (WildGuardMix, xLAM) deferred.
- **D19:** Track A deferred; v0.1 is Track B only.
- **D20:** Cloud teachers must be permissive open-weight models; no closed models, no Llama.
- **D21:** The checker is chosen by a bake-off against human review: DeepSeek V3.2.
- **D22:** Generator v2, and scaling synthetic data in measured steps.

---

## 14. What's next

1. ~~Finish the 10k synthetic batch~~: done, 9,702 examples.
2. ~~The data-scaling test~~: done (see §14a). Verdict: better data, not more of the same.
3. **Build Generator v2 (approved design),** an "agentic" generator in bounded steps:
   - a **planner** that aims new data at Kodiak's *validation* weak spots (never the eval set);
   - a **taxonomy** of ~300 domains × decision types × scales × difficulty, with coverage tracking;
   - **grounding in real text** (FineWeb-Edu passages), so Kodiak learns real-world writing rather than LLM style;
   - **hard-example mining**: Kodiak screens every candidate in 8 ms, and the pipeline keeps mostly what it gets wrong, plus a 30% quota of easy ones;
   - **minimal pairs**: change one fact to flip the answer, or remove the evidence to make it unanswerable;
   - a **critic** for ambiguous questions, a **human review queue** for disagreements, and **near-duplicate filtering**.

   Estimated ~$3 per 1,000 kept examples; the first v2 batch is ~30k jobs for ~$50. Each piece is kept only if it measurably helps.
4. **The final Track B model** (`kodiak-b-small-v0.1`) and the full Phase 5 evaluation vs. Qwen.
5. **Phase 6:** ONNX export, a Node.js/Express inference server (plain JavaScript), and a Bootstrap demo page.
6. **Later:** a model card and Hugging Face release, then a plan for scaling beyond one Spark (a bigger backbone like ModernBERT-large, longer
   states up to 8k tokens, and perhaps a custom encoder).

---

## 14a. Result: the data-scaling test (evening of Sept 24)

Three otherwise identical models trained on 0, 3,300, and 9,411 synthetic examples, drawn from the same pool, each scored on the full eval set:

| Synthetic examples | Overall | In-domain | Held-out (never-seen tasks) | Realistic LLM-style inputs | Calibration error |
|---|---|---|---|---|---|
| 0 | 76.6% | 80.7% | 63.9% | 52% | 0.068 |
| 3,300 | 76.9% | 81.1% | 61.7% | 89% | 0.067 |
| 9,411 | **77.8%** | **82.0%** | 62.5% | **93%** | **0.053** |

**What it means:** synthetic data made Kodiak better overall, far better on realistic documents, and better calibrated, but it didn't
help on task types it had never seen. The best detective moment: halfway through, the 3,300 model looked *worse* on held-out tasks. It turned
out it hadn't forgotten anything (forced to answer, it was slightly *more* accurate). It had learned the synthetic data's lesson, "say
unanswerable when the fact isn't in the text," too well, and started refusing questions that needed *inference*: a biography that never
literally says "attorney," or "why hasn't my card arrived?" meaning *card arrival*. The rule agreed *before* the test said a flat held-out
curve means "don't buy more of the same data," so the next steps are fixing the training recipe (early stopping kept choosing an
earlier, worse checkpoint; small datasets overfit) and building Generator v2 with "answerable by inference" questions.

## 14b. Result: the recipe fix (late night, Sept 24)

The scaling test exposed two recipe problems: the sampler was showing the model a few small datasets **20–30 times per run**
(prompt-injection examples 29×, Qasper 23×), and early stopping kept halting training before the learning rate's gentle final stretch.
An unattended overnight ablation tested the fixes:

| Variant | Overall | In-domain | Never-seen tasks | Calibration error |
|---|---|---|---|---|
| Before (early-stopped) | 77.8% | 82.0% | 62.5% | 0.053 |
| **Repeat cap (max 3 passes) + full schedule** | 78.0% | 80.8% | **66.4%** | **0.049** |
| Full schedule, no cap | 78.1% | 82.4% | 62.1% | 0.069 |

The repeat cap was the biggest single gain of the project so far: **+3.9 points on never-seen tasks** (jailbreak detection +8.8), at a
cost of about 1.6 points on the small datasets that had been memorized. It's a textbook demonstration of memorization vs. generalization,
and since Kodiak's purpose is handling *new* label sets, generalization won. The cap and the full schedule became the defaults. The
gap to Qwen 27B on never-seen tasks narrowed from about 24 points to about 20.

## 14c. Generator v2.0: built and piloted (Sept 25)

Because the scaling test said *better* data, not more, the next step was a better data generator. Generator v2 changes where examples come from:
- **A map of the world, not a list of 60 topics.** Sixteen hand-chosen sectors (from commerce to tool-using AI agents) were expanded by the
  writer model into **320 domains and 971 document types** ("tenant noise complaint email", "soil test laboratory report", "payment gateway
  webhook"), for about a penny. Each job gets a *spec*: which document, which kind of decision (classify, extract, score, route, compare,
  check a rule, pick a next action, check a claim), which scale (urgency, risk, sentiment...), how hard, and how many questions should be
  unanswerable, and why (missing fact, out of scope, no option fits, underspecified, not yet known).
- **Real text.** About 45% of examples use a real paragraph from the web (FineWeb-Edu) as the state; the teacher only writes questions.
  Kodiak stops learning only "AI-written" prose.
- **Answerable by inference.** Every question is labeled *stated*, *inferred* or *unanswerable*, and the checker was told that confident
  inference counts as answering. This goes straight at the over-abstention problem found on Sept 24. About a quarter of kept questions are now
  inference questions, which v1 essentially never produced.
- **Near-duplicate detection** (MinHash), a **budget cap**, and a **review queue** for the cases the writer and checker disagree on.

**The pilot story.** Pilot #1 kept 82% of jobs, but the checker rejected almost half the "unanswerable" questions. Reading them showed that
the writer was adding answer options like "Not known", a second way of saying "I don't know" that would have muddled Kodiak's calibrated
abstain signal. It was also asking silly routing questions about history articles. After two small rules (no "unknown" options, reader-style
questions for real text), pilot #2's disagreement on inferred questions fell from 37% to 20%, and on plainly stated ones from 8% to 2%.
Cost: **about $1.35 per 1,000 jobs**; all pilots together cost 25 cents. Next: Shane reviews 55 examples by hand (target: at least 95% of
labels correct), then an ~11,000-job batch (~$15) and an A/B test: v1 data vs. v2 data at equal size.

## 15. Timeline

- **Sept 23 (day one):** environment check; name collision; architecture designed and approved; 20 datasets converted; eval set
  built with Shane's human review; local synthetic generation started; bit-identical ModernBERT parity; overfit tests pass; first
  Track B model trained (35 minutes); Track A deferred; evaluation harness built; first comparison vs. Qwen (after three baseline
  fixes); status dashboard added.
- **Sept 24 (day two):** DigitalOcean cloud teacher connected (clipped key, billing gate); pilots #1 (26%) and #2 (88%); verifier
  bake-off picks DeepSeek V3.2; generation moves fully to the cloud at ~1,600–1,800 jobs/hour; Generator v2 design approved; synthetic
  batch completed (9,702 examples); data-scaling test run: synthetic data helps overall and calibration but not never-seen tasks;
  over-abstention on inference questions discovered; overnight recipe fix (repeat cap) lifts never-seen-task accuracy to 66.4%.
- **Sept 25 (day three):** Generator v2.0 built (taxonomy of 971 document types, real-text grounding, inference questions, dedupe,
  budget cap); two pilots fix "unknown" options and contrived questions; 55 eval candidates ready for human review.

---

## 16. Glossary (for learners)

- **LLM (autoregressive):** a model that writes text one token at a time, each token seeing only earlier ones. Examples: GPT, Qwen.
- **Encoder:** a model that reads a whole text at once (bidirectionally) and outputs vectors representing meaning; it can't generate. Example: ModernBERT.
- **Pretraining vs. fine-tuning:** pretraining teaches general reading from massive text (expensive); fine-tuning teaches a specific job (cheap).
- **Masked language modeling (MLM):** pretraining by hiding words and guessing them.
- **Attention mask:** rules for which tokens can attend to (read) which others.
- **RoPE (rotary position embeddings):** a way of encoding token positions as *relative* distances; it lets Kodiak choose position ids freely.
- **Zero-shot labels:** options defined at request time, never seen in training; they work because options are read as text.
- **Calibration:** confidence matching reality (80% confident means 80% correct).
- **ECE (expected calibration error):** the average gap between confidence and accuracy; lower is better.
- **Brier score:** the squared error of the probabilities; lower is better.
- **Proper scoring rule:** a loss that is minimized only by reporting true beliefs (log loss is one).
- **Temperature scaling:** dividing logits by a fitted number to fix over- or under-confidence without changing answers.
- **Beta distribution:** a probability distribution on [0,1]; Kodiak uses it for scores with uncertainty.
- **Abstention / null:** answering "not answerable from this state."
- **Overfitting / early stopping:** memorizing training data instead of learning; stopping when validation stops improving.
- **Data leakage:** test examples (or near-copies) appearing in training, which inflates scores.
- **Selection bias:** evaluating on data that was filtered by the thing being evaluated.
- **Distillation / teacher model:** a big model labels data that a small model learns from.
- **Mixture of experts (MoE):** a model that uses only part of its parameters per token, which makes it faster.
- **Hard-example mining:** keeping the training examples a model currently gets wrong.
- **Minimal pairs:** two nearly identical examples with different answers, which teach exactly which detail matters.
- **Bit-identical parity:** two implementations producing exactly the same numbers.

---

## 17. FAQ

**Is Kodiak an LLM?** No. It's a ~150M-parameter encoder that reads text and scores options. It can't write text, which is exactly
why it can't break a format.

**What does "one forward pass" mean?** The whole request (the state and every question and option) goes through the network once,
and all answers come out together. There's no back-and-forth generation.

**How can it handle labels it's never seen?** Options are given as text and encoded alongside the question, so "refund or billing fix"
is understood by its meaning, not by a trained class number.

**Why does "unanswerable" matter so much?** In real systems, a confident wrong answer is worse than "I don't know." Kodiak treats
abstaining as a learned, calibrated answer. In testing it was far more reliable at this than a 27B LLM, whose abstaining swung
with prompt wording.

**How fast is it?** About 8 ms per request on a DGX Spark, versus about 3.4 seconds for Qwen 27B, roughly 400× faster.

**Is it as smart as a big LLM?** On tasks like the ones it was trained on, roughly yes. On brand-new kinds of tasks, not yet (65% vs.
86%). Closing that gap is the current focus.

**Why not train it from scratch?** Pretraining is where almost all the cost lives. Building on ModernBERT's open weights turned weeks
into an hour. A custom encoder is on the table if Kodiak proves valuable.

**What has it cost?** Hardware Shane already owned, plus about $6–7 of cloud inference for the whole ~10k-example synthetic batch.

**Why not use GPT or Claude to generate training data?** Their terms (like xAI's for Grok) generally forbid using outputs to build
competing models, and Kodiak's data will be public. It uses open-weight models with permissive licenses instead.

**How is quality checked?** Every synthetic answer must quote evidence from the text, a model from a different family must
independently agree, and a human reviews samples (about 95% precision measured). Headline results use human-labeled data only.

**Will it be open source?** Yes: Apache-2.0 code and weights, with every dataset's license documented, and a Hugging Face release planned.

---

## 18. Numbers cheat sheet

| What | Number |
|---|---|
| Model size | ~152M parameters (ModernBERT-base 149.6M + heads) |
| Inference latency | ~8 ms per request (batch 1, all questions) |
| Qwen 27B latency, same machine | ~3,400 ms |
| Training speed | ~34k tokens/s (compiled), ~11 GB memory |
| One training run | ~35–60 minutes |
| Public training data | 356k examples, ~53M tokens/epoch, 20 sources (4 held out) |
| Eval set | 2,902 examples / 4,189 questions |
| Human-reviewed teacher precision | ~95% (61 of 64 questions) |
| Synthetic batch | 9,702 examples (3,290 local Qwen + 6,412 cloud gpt-oss/DeepSeek) |
| Cloud cost | ~$0.71–0.73 per 1,000 generation jobs |
| First model vs. Qwen (200-example sample) | 73.2% vs. 76.5% overall; 64.9% vs. 86.0% held-out; ECE 0.095 vs. 0.192 |
| Early-stopping lesson | step 3,250 beat the saved "best" step 1,750: 77.2% vs. 74.6% |
| DGX Spark | GB10 GPU, 121 GiB unified memory, ~94 TFLOP/s bf16 peak |
