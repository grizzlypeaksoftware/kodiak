# The Kodiak Story

*How and why Kodiak was built, including the parts that didn't go to plan.*
*Maintained as the project goes. For technical detail, see [LEARNING.md](../LEARNING.md); for the decision log, [DECISIONS.md](DECISIONS.md).*

---

## Why build this

In September 2026, TypeSafe AI launched **Jev**, which it describes as a "System One" decision model: instead of an LLM
writing text that you parse, the model answers typed questions directly and quickly. The idea struck a chord.
Much of what software asks LLMs to do isn't really *generation*. It's decisions: *which intent is this? is this
urgent? which tool should the agent call? can this even be answered from what we know?* Using a chat model for those
means paying for token-by-token generation, then parsing its output and hoping it stayed inside the format.

Kodiak is an open-source attempt at the same idea, built from first principles. It is **inspired by** Jev, not a copy of it:
we have no access to Jev's internals, and we make no claims about matching it. (The term "RLCD" came up while planning
calibration; we don't know exactly what it refers to, so we don't claim to replicate it.)

Kodiak is also a **learning project**. Its author, Shane Larson (Cortex Agent LLC), is an experienced software engineer
who is new to training models. Every phase explains its *why*, and the explanations are kept in
[LEARNING.md](../LEARNING.md). Making the journey legible is as much a goal as the model.

## The rules we set ourselves

1. **No autoregressive LLM backbone, and no constrained decoding of a chat model.** That's what Kodiak is trying to beat.
   Kodiak uses a bidirectional transformer *encoder*.
2. **The model must be structurally unable to answer outside the answer space.** Choice answers are one of the labels you
   supplied. Scores are inside your range. "Not answerable" is always a legal answer. There's no text output and nothing to parse.
3. **Everything in one forward pass, with calibrated probabilities.** Confidence should mean something.
4. **Build two versions and compare them honestly:** Track A trains an encoder from scratch; Track B starts from open
   pretrained weights (ModernBERT). Both are measured against a local LLM baseline on the same eval.
5. **Permissive licenses only**, because the weights will be released under Apache-2.0.
6. **A $0 budget.** One personal NVIDIA DGX Spark, borrowed from a book-publishing workflow. We work the way
   low-budget labs do: small first, reuse what others have already paid for, and scale only when the evidence says so.

## The machine

The DGX Spark is an unusual box: an ARM (Grace) CPU and a Blackwell GB10 GPU sharing **one 121 GiB pool of
memory**. There's no separate GPU memory, so a local LLM, the desktop, and a training job all compete for the same RAM.
When we first looked, two resident Ollama models held about 50 GB and the system was already swapping. The first
practical decision of the project was to unload one of them, and to adopt a rule: *teacher models and training jobs
take turns.*

## Day one (2026-09-23): Phases 0–3

Everything below happened in a single, long working day.

### Phase 0: What do we have?
Environment checks went smoothly (PyTorch ships official CUDA 13 wheels for ARM), but the name didn't:
"kodiak" was taken on PyPI, npm, GitHub, and Hugging Face. There's even a popular GitHub bot called Kodiak. The project
kept its name under an org namespace: **github.com/grizzlypeaksoftware/kodiak**, a Python package
called `kodiak-s1` ("System One"), with copyright held by Cortex Agent LLC. Scope decisions: English only, task domains
"as broad as possible", and states up to 2,048 tokens for v0.1, with 8k later.

### Phase 1: The design
The central idea came from a question: *how do you answer many questions about one text in one pass, without the
questions interfering with each other?* The answer was a **structured attention mask**. The state, every question, and
every candidate label are packed into one sequence. The state can only see itself; each question sees the state and
its own options; each option sees the state and its question. Choosing position ids so every question "starts at the same
place" makes the answers independent of question order and label order *by construction*. The classic LLM bias of
preferring option A becomes impossible rather than merely trained away. "Null" became an answer any question can get,
not a separate question type. The design was written up in [ARCHITECTURE.md](ARCHITECTURE.md) and approved as proposed.

### Phase 2: Data, and the value of reading it
The pipeline converts 20 permissively licensed datasets (NLI, intent, emotion, moderation, response quality, tool
routing, long-document QA, and more) into one format, and adds synthetic examples written by a local Qwen model and
checked by a second, independent pass.

Checking licenses at their source cost us some famous datasets (SNLI, BoolQ, SQuAD v2), and turned up MultiNLI's
share-alike *fiction* genre, which we dropped.

The most important lesson of the day was that **reading actual examples found the bugs that tests didn't**:
- Tool-routing rows labeled "no tool" were really cases where the assistant called the tool a turn later.
- One NLI phrasing ("Does the text say that…?") made "can't tell" read as "no", which would have taught the model the
  wrong meaning of abstaining.
- Taking "the first N rows" of sorted datasets produced a test set with *zero* out-of-scope examples.
- The Qwen verifier said "unanswerable" to almost everything. Its JSON schema asked it to decide
  `unanswerable: true/false` *before* it had looked for evidence. Asking for the evidence quote first fixed it.
- Qwen sometimes wrote multiple-choice questions with no options at all; splitting the output schema by question type fixed that.

A human review of the synthetic data (24 examples, 64 questions) found **95% of the teacher's surviving labels
correct**. That's a useful honest number, and it's why headline results use human-labeled data.

The teacher was slow, too. Asking Ollama for parallel requests barely helped, because the GPU was already busy.
Switching the *writer* to a mixture-of-experts model (`qwen3.6:35b-a3b`), with `qwen3.8:27b` still checking every
label, made it about 2.4× faster at the same quality.

### Phase 3: Proving the plumbing
The encoder re-implements ModernBERT so its weights load directly, with Kodiak's mask swapped in. Two moments stood out:
- **Bit-identical parity.** On ordinary text, our implementation with ModernBERT's weights produces *exactly* the same
  numbers as Hugging Face's reference (a max difference of 0.0). Track B really does start from the published model.
- **Overfit tests.** Both a 15M-parameter model from scratch and ModernBERT memorized 32 examples perfectly within
  25–50 steps. The pipeline works end to end.

Measuring the machine gave two surprises. First, `torch.compile` **doubled** training speed. The Spark's GPU has
plenty of compute but modest memory bandwidth, so fusing small operations matters. Second, the decision-tuning data turned out to be
**53 million tokens**, not the 2 billion the design doc assumed. A training pass takes 25 minutes, not 16 hours,
which moved the main risk from compute to overfitting.

### Phase 4 begins
The first Track B training run started the same afternoon, with validation on every dataset and early stopping, while
10,000 more synthetic examples and the FineWeb-Edu corpus for Track A downloaded in the background.

That afternoon also settled a question about the original idea. Watching Track B learn in about an hour raised it:
*is ModernBERT an LLM, and does building on it compromise the idea?* It isn't an LLM in the ruled-out sense; it's an
encoder that reads but can't write, and everything that makes Kodiak a decision model is Kodiak's own. That led to a
bigger decision: **skip Track A.** Pretraining our own encoder would spend days reading about 200× less text than
ModernBERT did, just to prove a gap everyone expects. Shane decided to put the effort into Track B's data, calibration,
and evaluation instead, and to revisit a custom encoder, perhaps shaped specifically for decisions, if Kodiak earns it.

Before the day ended, the first Track B model was measured against Qwen 27B on the same eval set: roughly a tie on
the kinds of tasks Kodiak was trained on, about **400× faster** (8 ms vs. 3.4 s per request), and noticeably better
calibrated and better at abstaining, but clearly weaker on task types it had never seen (65% vs. 86%). Getting a
*fair* comparison took three baseline runs: the first prompt made Qwen refuse judgment questions, and a loose output
schema let it answer ">= 0.8", which the scorer counted as an abstention. A small local dashboard went up that evening so
progress could be followed without reading log files.

## Day two (2026-09-24): a cloud teacher

The local synthetic run was going to take about two more days, and Kodiak's weak spot, new kinds of tasks, called for
more varied, higher-quality examples. Grok was considered and rejected: xAI's terms forbid using outputs to build
competing models. The answer was open-weight models on **DigitalOcean's serverless inference**: gpt-oss-120b
(Apache-2.0) at $0.10 / $0.70 per million tokens.

Getting connected was its own small saga:
- **"Unauthorized," despite correct settings.** The key's settings (all models, no VPC restriction) were fine. Checking the key's
  *shape* without ever printing it (length, character classes, whether loading altered it) found the answer: the stored key was
  68 characters and the regenerated one 71. The first copy had been clipped.
- **"Payment Required."** The new key authenticated, but every model returned 402. Adding a $62 prepaid balance with
  auto-reload didn't clear it immediately. A background watcher retried every five minutes and started the pilot automatically
  when access opened at 10:33, about 35 minutes later.

The first 50-job pilot kept only **26%** of its examples. Reading the output showed why: gpt-oss *paraphrases* its evidence
("Commenter: Jane Doe") instead of quoting the state (`"author":"Jane Doe"`), so the hallucination guard threw out correct
answers. The fix asked for exact quotes, accepted rewording as long as nearly all content words appear in the state, and dropped
single bad questions instead of whole jobs. The second pilot kept **88%**, at **$0.73 per 1,000 jobs**, with the whole pilot
costing four cents.

That raised a design question from Shane: *why not let gpt-oss check its own work too?* Because a model tends to repeat its own
mistakes when it re-reads them; the checker is only useful if it has different blind spots. Rather than argue it, we measured
it: a **verifier bake-off** scored candidate checkers against Shane's human review from Phase 2, the one set of synthetic labels a
person had actually verified.

The bake-off answered it. Checked against Shane's review, gpt-oss checking gpt-oss-style output kept 92% of the answers
he'd approved and broke its JSON twice; **DeepSeek V3.2**, a different model family, kept 97%, never failed, and was about ten
times faster. (Qwen 3.5 397B thought for three and a half minutes per example and then returned nothing.) The local 27B
Qwen couldn't be scored fairly at all: the review set had been *built* from examples it approved, so it "agreed" with every one,
including the three a human rejected. That was the same-family blind spot, seen from the other side.

So the pipeline moved to the cloud: **gpt-oss-120b writes, DeepSeek V3.2 checks**, with every example tagged with both
models. The local run stopped at 3,290 examples, and the remaining ~7,700 jobs went to DigitalOcean at 16 in parallel,
about 1,200 jobs an hour, for roughly $8 in total. That turned a two-day local job into an afternoon and freed the Spark's GPU for training.

That evening the free scaling test ran: three identical models trained on 0, 3,300, and 9,411 synthetic examples. The
answer was more interesting than "more is better." Synthetic data made Kodiak better overall (+1.2 points), much better on realistic
LLM-style documents (52% → 93%), and better calibrated. But on the held-out tasks it had never seen, **accuracy didn't move**.
A mid-test peek showed why the 3,300 model briefly looked *worse* there: it had learned the synthetic data's lesson, "say unanswerable when
the fact isn't in the text," a little too well, and started abstaining on questions that needed *inference* (a biography that never literally
says "attorney"; "why hasn't my card arrived?" meaning *card arrival*). Forced to answer, it knew just as much. The verdict followed the rule
agreed before the test: don't buy more of the same data; build *better* data. That pointed straight at Generator v2.

The night ended with a recipe ablation that ran unattended until 11:30 PM. The scaling test had shown two
recipe problems: small datasets were being repeated until memorized (the sampler showed the model prompt-injection examples 29 times
per run and Qasper 23 times), and early stopping kept halting runs before the learning-rate schedule's gentle finish. Capping
repeats at three passes per dataset produced the day's biggest single gain: **held-out accuracy 62.5% → 66.4%**, with jailbreak
detection alone up almost 9 points, at the cost of about 1.6 points on the small datasets it had been memorizing. It was a textbook
demonstration of memorization vs. generalization, and for a model whose whole purpose is handling *new* label sets, the choice was easy.
The cap and the full schedule became the defaults.

### Day three: building the better generator

With the data test pointing firmly at *better* data rather than more, Generator v2 went from design doc to working code in a morning. The first
step was the map: sixteen hand-picked sectors (commerce to tool-using AI agents), which the writer model expanded into 320 domains and 971
kinds of documents, from "tenant noise complaint email" to "soil test laboratory report", for about a penny. Almost half of the new examples
don't use invented text at all; they're real paragraphs from the web, and the teacher only writes the questions.

The first pilot looked healthy on paper (82% kept) but the checker was rejecting almost half the "unanswerable" questions. Reading them one by
one showed the culprit wasn't the checker: the writer had been sneaking "Not known" into the answer options, a second way of saying "I don't
know" that would have muddled Kodiak's abstain signal. It had also been asking which "processing queue" should handle a history article. Two
small rules later, the second pilot's disagreements fell by a third to three quarters, depending on the kind of question, and nearly a quarter
of all kept questions were the "answerable by inference" kind that v1 never produced. The whole morning of pilots cost 25 cents.

Midway through day three, with the v2 batch humming in the cloud, Shane asked the big question: *can this actually matter? Can it
be frontier?* The honest answer set the project's direction. Kodiak will never out-reason a 27-billion-parameter LLM, and it shouldn't
try. But it already matched one on familiar decisions at four hundred times the speed, with confidence you can threshold on. The goal
became **frontier in its class**: the best open model for structured decisions, the fast "System 1" that handles most traffic and knows
which cases to hand to a slower "System 2." To keep that claim honest, we wrote down what it would take *before* measuring
(docs/STRATEGY.md), and added the real competition to the scoreboard: the open zero-shot classifiers people use for this job today.

That afternoon the repository went public (github.com/grizzlypeaksoftware/kodiak), a few days before the weights: code, docs,
decisions and dead ends first, so anyone could follow the build as it happened. The model itself stayed private on Hugging Face
(cortex-agent-llc) until the v2 data test decides which version launches.

*(Continued as the project progresses.)*

---

## People and credits

- **Shane Larson** (Cortex Agent LLC / Grizzly Peak Software): project owner; made the calls on scope, naming, licensing,
  budget, and hardware; human reviewer of synthetic data.
- **Claude** (Anthropic): pair engineer: design, implementation, experiments, and documentation, in daily review loops.
- Built on the work of the ModernBERT, Ettin, Qwen, and dataset authors listed in [data/LICENSES.md](../data/LICENSES.md).
