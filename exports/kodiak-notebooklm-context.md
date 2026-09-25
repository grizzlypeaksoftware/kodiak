# Kodiak: one engineer, one box, and a bet against the big models

*A story-first briefing on the Kodiak project, written as a source for podcast-style audio overviews (NotebookLM). Everything
here is true and every number is measured; the tone is meant to be fun. Current as of September 25, 2026.*

---

## A note to the hosts: how to tell this story

This is an underdog story with receipts. One engineer, one desktop AI computer, an AI pair programmer, and a few tens of dollars of
cloud credit, taking a swing at a problem the big labs solve with giant models. Play it like a heist movie or a garage-band origin story:
scrappy, funny, a little cheeky, and brutally honest. The honesty is the edge: this project publishes its failures next to its wins,
and some of the best moments are when the team caught its own mistakes.

**Tone:** excited, irreverent, allergic to hype. Tease the big labs a little, celebrate clever cheap tricks, and never claim more
than the numbers say. Kodiak does not beat GPT or Claude at being GPT or Claude, and it doesn't try.

---

## The cold open

Picture this. You run a support desk, and every day ten thousand messages come in. For each one you need three answers: *what does
this person want, how urgent is it, and which team gets it?* Today, lots of companies send every message to a giant AI model, the kind
that writes poetry, and ask it to write back an answer. It takes a few seconds, costs money every time, and once in a while it answers
something that isn't even one of your options.

Now picture a model that answers all three questions in **8 milliseconds**, can't physically answer outside your options, and when
it doesn't know, *says so*, with a probability you can actually trust.

That's Kodiak. It was built in about three days, on one machine, by one person and an AI.

---

## The cast

- **Shane Larson.** The builder. A seasoned software engineer who had never trained an ML model before this project, founder of Cortex Agent
  LLC and Grizzly Peak Software, and a book publisher on the side (the same AI computer that trains Kodiak also helps run a publishing
  business). He made every call on scope, money, licensing and direction, and personally graded the AI's homework. Handle on X: @PeakGrizzly.
- **Claude.** Anthropic's AI, working as Shane's pair engineer: designing, coding, running experiments, and writing everything down.
- **The Box.** An NVIDIA DGX Spark: a desktop-sized AI computer with 121 GB of memory shared between the processor and the GPU. Powerful,
  but with a quirk that shaped the whole project: everything shares one pool of memory, so AI teachers and training jobs have to take turns.
- **The Hired Reader.** ModernBERT, an open-source model from Answer.AI that already knows how to *read* English, because someone else
  spent a fortune training it on about 2 trillion words. Kodiak hires it and teaches it a new job: making decisions.
- **The Writer and the Checker.** Two open-weight AI models rented in the cloud for pennies: gpt-oss-120b (from OpenAI, openly licensed)
  writes practice questions, and DeepSeek V3.2 (from a different company, on purpose) checks them blind.
- **The Rivals.** Qwen 27B, a big open chat model roughly 180 times Kodiak's size; and the "zero-shot classifiers," the specialized
  open models people use today for labeling text (NLI-based models and GLiClass), each about three times Kodiak's size.
- **The Inspiration.** In September 2026 a company called TypeSafe AI announced Jev, a closed "System One" decision model. Shane loved the
  idea and decided to build an open version from scratch, his own way. Kodiak is *inspired by* Jev; it doesn't copy it or claim to match it.

---

## The big idea: deciding is not writing

Psychologist Daniel Kahneman described two kinds of thinking: **System 1**, fast and intuitive, and **System 2**, slow and deliberate.
Big chat models are System 2 machines. They're amazing at writing, reasoning and explaining. But a huge amount of what businesses ask them to
do isn't writing at all. It's *deciding*:

- Which of these 12 intents is this customer message?
- How urgent is this ticket, from 0 to 10?
- Which tool should this AI agent call next?
- Is this message a prompt-injection attack?
- Can this question even be answered from the information we have?

Asking a writing machine to make these calls is like hiring a novelist to sort your mail. It works, but it's slow, pricey, and
sometimes they write you a poem instead of putting the letter in a box.

**Kodiak is the mail sorter.** You give it a "state" (a message, a thread, or a JSON record) and a list of typed questions:
- **Choice** questions, with options you make up on the spot ("refund", "track order", "cancel"). It picks one, and can never pick
  something that isn't on the list.
- **Score** questions on any scale you choose (0–10 urgency, 1–5 stars). It gives a number *and* how sure it is (a range).
- And for every question, the option to say **"I can't tell from this."** That's not a failure; it's a feature, with its own probability.

All the questions get answered at once, in one pass through the network. No text is generated, so there's nothing to parse and nothing to
go off the rails.

**The pitch in one line:** a 150-million-parameter model that answers decision questions in 8 milliseconds with trustworthy confidence,
about 400 times faster than asking a 27-billion-parameter chatbot.

---

## Episode 1: "Does it have to learn to read first?"

The original plan had two tracks. Track A: build a brand-new model from scratch. Track B: take a model that already reads (ModernBERT) and
teach it to decide.

On day one, Track B trained its first working model in **35 minutes**. Shane asked the question that killed Track A on the spot:
*"Track A has to literally learn to read?"* Yes. From scratch, the Box would have spent days reading about 10 billion words (roughly 200 times
less than ModernBERT already had) just to end up a worse reader. Track A was shelved: "if Kodiak earns it, we'll build our own brain later."

**The clever part: one pass, many questions, zero cheating.** Kodiak crams the whole request into one sequence (the document, then each
question, then each question's options) and uses a custom set of rules about who can "look at" whom inside the model:
- The document can only see itself, so it's read the same way no matter what you ask.
- Each question sees the document and its own options, but not the other questions.
- Each option sees the document and its own question, but not the other options.

Think of an exam hall where every question gets its own soundproof booth with a window onto the same document. That buys three guarantees,
proven by automated tests:
1. A question gets the exact same answer whether you ask it alone or alongside 30 others, in any order.
2. Shuffling the options changes nothing. The classic chatbot habit of favoring "option A" is *impossible* here.
3. You can pack several customers' requests into one batch and they can't peek at each other.

**Wait, what?** Kodiak re-implemented the hired reader's entire architecture in its own code, to control those booths, and then proved the
copy produced **bit-identical** numbers to the original. Not "close." Identical, to the last decimal.

---

## Episode 2: Picking a fight with a model 180 times bigger

First real test: Kodiak's first model versus Qwen 27B, a big open chatbot running on the same Box, same 200 test examples.

| | Kodiak (150M) | Qwen 27B |
|---|---|---|
| Speed per request | **8 ms** | 3,431 ms |
| Accuracy on familiar kinds of tasks | 75.5% | 76.5% |
| Accuracy on never-seen kinds of tasks | 64.9% | **86.0%** |
| Calibration error (lower = more trustworthy confidence) | **0.095** | 0.192 |
| When it says "can't tell," how often it's right | **90%** | 68% |

**The headline:** about 400 times faster, roughly tied on familiar tasks, twice as trustworthy about its own confidence. **The gut punch:**
on tasks it had never seen, the big model was 21 points better. That gap became the villain of the rest of the story.

**The sportsmanship subplot.** The first time they ran Qwen, it refused 96% of judgment questions ("how toxic is this?") because the prompt
said "only use information in the text." The team could have published that and declared victory. Instead they fixed the prompt, then fixed
it *again* when Qwen started answering scores like ">= 0.8", and only compared once Qwen had a fair shot. All three runs are on record.
Beating a handicapped opponent proves nothing.

**The urgency flop.** A live demo: *"My card was charged twice and I need it fixed before my rent is due Friday."* Kodiak nailed the intent
(refund) and correctly said the card brand was unknowable. Then it rated urgency as *not urgent*. Rent is due Friday! Why? Every scoring
dataset it trained on was about toxicity or quality, mostly near zero, so it had learned "scores are usually low." A perfect little example of
the villain: it hadn't learned to handle *new kinds* of questions yet.

---

## Episode 3: The training-data factory (and the "don't grade your own homework" rule)

Public datasets only get you so far, and every one Kodiak used had to pass a license check at its original source; anything
"share-alike" or "non-commercial" was thrown out, because the goal is fully open weights. So the team built a **synthetic data factory**: an AI
teacher writes realistic documents (support chats, invoices, server logs, legal letters) plus questions about them, including some that
*can't* be answered from the document, on purpose.

**Rule one: the teacher is never the model.** The big AI writes practice exams; the small model learns from them.

**Rule two: no sketchy teachers.** Grok was cheap and tempting, but its terms forbid using outputs to build competing models, and Kodiak's
data will be public. Closed models were out. Only openly licensed teachers allowed.

**Moving to the cloud for pennies.** Local teachers on the Box would have needed two more days, so the factory moved to rented open models on
DigitalOcean. The first pilot kept only **26%** of its output. Why? The writer kept *paraphrasing* its evidence ("Commenter: Jane Doe") instead
of quoting the document, so the fact-checker threw out correct answers. Three small fixes later: **88%** kept. The pilot cost four cents.

**Don't let the student grade its own homework.** Shane asked: why not let the writer check its own work? Because a model tends to agree with
its own blind spots. Instead of arguing, the team held a **bake-off** against Shane's own hand-graded answers:

| Checker | Agrees with the human-approved answers | Speed |
|---|---|---|
| gpt-oss-120b (the writer itself) | 92% | 26 s |
| **DeepSeek V3.2** (a different company's model) | **97%** | **2.3 s** |
| Qwen 3.5 397B | thought for 3.5 minutes, then said nothing | – |

**Wait, what?** A model with 397 billion parameters thought so hard it forgot to answer. DeepSeek won: more accurate, and ten times faster.

The factory then produced about 9,700 examples for around six dollars.

---

## Episode 4: The plot twists

**Twist 1: More data didn't help. Wait, what?** The team trained three identical models on 0, 3,300 and 9,400 synthetic examples. More data
made Kodiak better overall and much better calibrated, but on never-seen tasks the line was flat. The villain didn't budge.

**Twist 2: The detective moment.** Halfway through, the 3,300-example model looked *worse* on new tasks. Had it forgotten something? No: forced
to answer, it was actually slightly *more* accurate. It had learned the synthetic data's lesson, "if the fact isn't written down, say you can't
tell," far too well. It started refusing questions that needed a little common sense: a biography that never literally says "attorney," or
"why hasn't my card arrived?", which obviously means *card delivery*. It had become the coworker who won't answer anything that isn't in the
email verbatim.

**Twist 3: The model had been cramming.** The training mix showed a few small datasets to the model 20 to 30 times per run: the prompt-injection
examples 29 times. It was memorizing flashcards instead of learning. The fix: a **repeat cap** (no dataset more than three passes), and let
training finish its full schedule instead of stopping early. Result: **+3.9 points on never-seen tasks** overnight, and jailbreak detection
up almost 9 points. The cost: about 1.6 points on the small sets it had memorized. For a model whose whole job is handling *new* questions,
that's an easy trade.

**The rule behind all three twists:** decide what result would change your plan *before* you run the experiment. The team wrote down "if
more data doesn't help never-seen tasks, stop buying more of the same" before the test ran, so a disappointing result turned into a clear
next move instead of an excuse.

---

## Episode 5: Generator v2, the smarter factory

The data test said *better* data, not more of it. So the factory got rebuilt:

- **A map of the world.** Instead of 60 hand-typed topics, 16 sectors (commerce to AI agents) expanded into **320 domains and 971 document
  types** ("tenant noise complaint email," "soil test lab report," "payment gateway webhook"), for about a penny of AI time.
- **Real text.** About 45% of examples now use real paragraphs from the web, and the teacher only writes the questions. Kodiak stops learning
  that all text sounds like an AI wrote it.
- **"Answerable by inference."** Every question is labeled *stated*, *inferred* or *truly unanswerable*, and the checker was told that sound
  common sense counts. This goes straight at the coworker-who-won't-infer problem.

**The sneaky teacher.** In the first pilot, the checker rejected almost half the "unanswerable" questions. Reading them one by one revealed the
culprit wasn't the checker: the writer kept slipping options like **"Not known"** into the answer list. That's a second way to say "I don't know,"
which would have muddled Kodiak's calibrated "can't tell" signal. It was also asking which "processing queue" should handle a history article.
Two rules later, disagreements dropped by up to three quarters. Every pilot that morning, combined, cost **25 cents**.

**The human in the loop.** Shane graded 165 of the new questions by hand: **92.7% correct**, and every single "unanswerable" was right. The
misses had a pattern: questions with *two* defensible answers ("which of these is NOT listed?" when two weren't). **Wait, what?** Two AIs from
two different companies had *agreed* on those wrong answers. Agreement isn't correctness. So v2 gained rules against ambiguous questions and
a pair of AI "critics" whose only job is to attack each answer. The full 11,000-job batch is running overnight, for about $25.

---

## Episode 6: "Can this actually make a dent?"

On day three, Shane asked the big question: *can this be frontier?* The honest answer became the strategy.

**Not frontier like GPT or Claude.** A small model won't out-reason a giant one, and shouldn't try. **Frontier in its class:** the best open
model for *decisions*, deployed as the fast System 1 in front of a slow System 2. Kodiak answers everything in milliseconds; the confident
answers get used immediately, and only the unsure ones get escalated to a big model or a human. Because its confidence is calibrated, "90%
sure" really means about 90% right, so you can set that dial and know what you're getting. You pay big-model prices only on the hard cases.

**The release bar, written down *before* measuring.** Beat every open zero-shot classifier on never-seen tasks; come within about 10 points of an
8-billion-parameter chatbot at 100 times its speed; best calibration of anyone; fully open. If Kodiak misses a bar, the release says so.

**The scoreboard against the real rivals** (Kodiak at 150M parameters vs. specialized classifiers about 3× its size):
- **Overall: a blowout.** 78% vs. 55% for the best rival, calibration error 0.049 vs. 0.156, and faster (8 ms vs. 14–48 ms), while also doing
  scores and "can't tell," which they can't do properly.
- **Never-seen tasks: close, and Kodiak is slightly behind.** 69.1% vs. 70.5% for GLiClass-instruct. Kodiak crushes them at spotting jailbreak
  prompts (68% vs. about 50%) but loses at guessing someone's job from a biography.
- **Wait, what? The contamination catch.** One rival looked great on banking intents, one of Kodiak's supposedly never-seen tasks. Its model card
  revealed it had *trained* on that exact dataset. Its clean version dropped 12 points there. A "zero-shot" score only counts if the model never
  saw the test.

**Verdict:** best-in-class bar not met *yet*. That's exactly why it was written down first.

---

## Episode 7: Going public

On day three the project went public: the GitHub repo with every decision and dead end, and a **research-preview model** on Hugging Face under
Cortex Agent LLC. It runs in 8 ms on a GPU and about 80 ms on a plain CPU, so no special hardware is needed. A demo you can type into is built and ready to open up,
and there's a one-click hosting option.

Even the launch had a catch-our-own-mistake moment: the first upload was missing its calibration settings (the eval had been applying them
separately). Caught and fixed before anyone used it. **Lesson: test the thing users actually download, not just the pipeline you evaluate.**

The preview is honest about its misses. Ask it about a box that arrived crushed with a broken lamp and it says the customer wants
"delivery status" (wrong: they want a refund). Ask about a calm user scheduling a meeting and it guesses they're "excited." Those misses are
the before-and-after test for the new data.

**The business angle:** the weights are free and open, which builds trust and adoption. The plan is a hosted Kodiak API from Cortex Agent for
teams that just want an API key, and later, fine-tuning on a customer's own labels, which usually lifts one specific task far beyond any
zero-shot model.

---

## The cliffhanger

Tonight, the new factory's 11,000 jobs finish, and the showdown runs: Kodiak trained on the old data vs. the new data, same size, same recipe.
Does "better data" finally move the never-seen-task number? After that come the next moves:
- **Hard-example mining:** Kodiak screens every new practice question in 8 ms, and the factory keeps mostly the ones it gets *wrong*, like a
  tutor who stops drilling what you've mastered.
- **Minimal pairs:** twin examples where one word flips the answer ("arrived yesterday" vs. "still in transit"), which teach *exactly* which
  fact matters.
- **A bigger brain:** ModernBERT-large, about 400M parameters, for the quality tier.

The open question for the show to end on: *can a garage project with a fully open recipe become the go-to open model for decisions, and
what changes for everyone building with AI if it does?*

---

## Spicy takes for the hosts to argue about

- **"Most AI spending is wasted on writing machines doing sorting jobs."** Fair, or too cute?
- **"Calibration matters more than accuracy."** A model that knows when it's unsure versus one that's slightly more accurate but always confident: which
  would you put in front of real customers?
- **"Synthetic data is just AI eating its own tail."** Or, with real text, a different-company checker, critics and human grading, is it a legit
  shortcut?
- **"Publishing your failures is the best marketing."** This project puts its misses on the model page. Bold or naive?
- **"One person with a desktop box and an AI partner can now do what used to need a research lab."** How true is that, really?

## "Wait, what?" moments (quick reference)

- 8 milliseconds vs. 3.4 seconds: about **400× faster** than a 27B chatbot on the same machine.
- The first working model trained in **35 minutes**.
- A cloud pilot of new training data cost **four cents**; a morning of pilots, **25 cents**.
- A 397-billion-parameter model **thought for 3.5 minutes and returned nothing**.
- More data made the model better at everything *except* the thing that mattered, until the team found out why.
- The model saw one dataset **29 times** per run. It was cramming.
- Two AIs from two companies **agreed on wrong answers**; a human caught it.
- A rival "zero-shot" model had **trained on the test**.
- Shuffling the answer options **cannot** change Kodiak's answer, by construction.

## Lines worth quoting

- "Most of what we ask AI to do isn't writing. It's deciding."
- "Hiring a novelist to sort your mail."
- "It can't answer off the menu."
- "Don't let the student grade its own homework."
- "Agreement isn't correctness."
- "Decide what would change your mind before you run the experiment."
- "Frontier in its class, not frontier in general."
- "Test the thing users download, not the pipeline you evaluate."

---

## Technical appendix (accurate details, for depth)

**Architecture.**
- Encoder-only: ModernBERT-base backbone (Apache-2.0, 149.6M parameters, 22 layers) plus Kodiak's heads, about 152M parameters in total.
- Input is one packed sequence, `[CLS] state [SEP] | [CHOICE] question | [LABEL] option ... | [SCORE] question`, with a structured attention
  mask (state sees state; a question sees the state, itself and its options; an option sees the state, its question and itself).
- Position ids restart per question and per option (rotary position embeddings make that possible). Answers are therefore independent of
  question order and option order.
- **Heads:**
  - choice: a matching network over the option and question encodings, so brand-new label sets work zero-shot;
  - null: a sigmoid probability of "unanswerable";
  - score: a Beta distribution (mean and concentration), which can't go out of range and gives real intervals.
- **Training:** the joint log-likelihood of the correct outcome. That's a strictly proper scoring rule: the model scores best only by reporting
  its true beliefs.
- **Calibration:** three temperatures fit on validation data; they change confidence without changing any answer. Why no reinforcement learning:
  an LLM's confidence is text it writes (no gradient), while Kodiak's confidence *is* its output distribution, trained directly.

**Hardware.**
- NVIDIA DGX Spark: GB10 Blackwell GPU, 121 GiB unified memory, about 94 TFLOP/s bf16 peak.
- Training is limited by memory bandwidth, not compute; `torch.compile` doubled throughput by fusing small operations.
- About 34k tokens/s and 11 GB of memory; one training run takes 35–60 minutes.

**Data.**
- 20 public datasets, every license verified at its source (share-alike and non-commercial data excluded). They cover inference, reasoning,
  intents (CLINC150, MASSIVE, Banking77), emotions, toxicity scores, spam, prompt injection, jailbreaks, response-quality ratings, tool routing
  (Glaive, ToolACE), occupations (Bias in Bios) and long-document QA (Qasper).
- About 356k training examples. **Four datasets are held out entirely** to measure never-seen-task generalization.
- Frozen eval set: 2,902 examples / 4,189 questions, never trained or tuned on.
- **Synthetic v1:** about 9,700 examples (local Qwen teachers, then the cloud writer gpt-oss-120b + checker DeepSeek V3.2), at about $0.73 per
  1,000 jobs; human-graded precision about 95%.
- **Synthetic v2:**
  - built from a 971-document-type taxonomy, with about 45% real web passages (FineWeb-Edu);
  - every question labeled stated / inferred / unanswerable, and "unknown"-style options banned;
  - MinHash near-duplicate filtering and two critic models;
  - about $2.2 per 1,000 jobs; human-graded precision 92.7% before the critics were added.

**Key results (best model so far: repeat cap + full schedule).**

| Measure | Kodiak small | Notes |
|---|---|---|
| Overall accuracy | 78.0% | frozen eval set |
| Familiar-task accuracy | 80.8% | |
| Never-seen-task accuracy | 66.4% (69.1% forced to answer) | Qwen 27B ≈ 86% on a 200-example sample |
| Calibration error (ECE) | 0.049 | lowest of every system tested |
| Latency | ~8 ms GPU, ~80 ms CPU | Qwen 27B ≈ 3,400 ms |
| vs. best open zero-shot classifier | 78% vs. 55% overall; 69.1% vs. 70.5% never-seen (forced) | rival is 439M parameters |

**Glossary.**
- **Encoder:** reads the whole text at once and turns it into meaning vectors; it can't write.
- **Autoregressive LLM:** writes text one token at a time.
- **Calibration:** confidence that matches reality (80% sure means right 80% of the time).
- **ECE:** the average gap between confidence and accuracy (lower is better).
- **Abstention:** answering "can't tell from this."
- **Zero-shot:** handling labels or tasks never seen in training.
- **Held-out:** datasets deliberately never trained on.
- **Forced accuracy:** accuracy when the model must pick an answer (no abstaining).
- **Overfitting:** memorizing instead of learning.
- **Data leakage / contamination:** the test (or copies of it) appearing in training.
- **Proper scoring rule:** a loss minimized only by honest probabilities.
- **Temperature scaling:** a single number that softens or sharpens confidence.
- **Beta distribution:** a probability curve on 0–1, used for scores with uncertainty.
- **MinHash:** a fast way to spot near-duplicate texts.
- **Hard-example mining:** keeping the examples the model gets wrong.
- **Minimal pairs:** near-identical examples with different answers.

**Timeline.**
- **Sept 23:** architecture, 20 datasets, eval set, bit-identical backbone, first model in 35 minutes, first bout with Qwen 27B.
- **Sept 24:** cloud data factory, checker bake-off, 9.7k synthetic examples, the "more data didn't help" twist, the overnight repeat-cap fix.
- **Sept 25:** Generator v2 built and piloted, human review, the frontier-in-class strategy, the rival scoreboard, the repo and research
  preview go public, demo built; the overnight v2 batch and the old-vs-new-data showdown are next.

**Open source.** Apache-2.0 code and weights; every dataset's license documented; the code is at github.com/grizzlypeaksoftware/kodiak and the
model is on Hugging Face under cortex-agent-llc.
