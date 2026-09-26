# The $35 frontier bet: how one engineer and an AI built an open decision model in four days

*Source material for a single podcast episode (NotebookLM audio overview) about the Kodiak project. It's one continuous story. Every
number in it is measured and true; the tone is meant to be fun. Current as of September 26, 2026.*

---

## For the hosts

Tell this as **one story**, start to finish: a guerrilla-engineering heist. The target is something the big AI labs spend fortunes on, a
frontier-class model. The crew is one engineer, one desktop computer and an AI pair programmer. The budget is about **$35**. The whole
episode is about *how you punch that far above your weight*: the cheap tricks, the borrowed muscle, the discipline, the failures that
turned into rules, and a brutally honest scoreboard at the end.

Keep it energetic, funny and a little cheeky toward the big labs, but never claim more than the numbers say. Kodiak is not trying to beat
GPT or Claude at being GPT or Claude. It's trying to be the best open model in *its* class, and the story is honest that it isn't there yet.
End on the open question.

---

## The story

### The itch

In September 2026 a company called TypeSafe AI announced Jev, a closed "System One" decision model. Shane Larson, a veteran software
engineer who runs Cortex Agent LLC and Grizzly Peak Software (and a book-publishing business on the side), read about it and couldn't let it
go. The idea behind it was too good: most of what companies pay giant AI models to do **isn't writing at all. It's deciding.** Which of these
twelve intents is this customer message? How urgent is this ticket? Which tool should this AI agent call next? Is this a prompt-injection
attack? Can this even be answered from what we know?

Today most of those decisions go to a chatbot the size of a small city, which writes out an answer word by word, costs money every time,
takes seconds, and occasionally answers something that isn't even one of your options. That's like hiring a novelist to sort your mail.

Shane had never trained a machine-learning model. He did have an NVIDIA DGX Spark on his desk (a desktop-sized AI computer he already
owned) and Claude, Anthropic's AI, as a pair engineer inside his terminal. The bet: build an **open** version, from scratch, his own way,
and see how close to frontier-class a garage project can get. The rules were set on day one:
- no chatbot underneath;
- it must be physically unable to answer outside the options you give it;
- only permissively licensed data and models, so everything can be given away;
- an honest comparison against real rivals, including publishing the losses.

He called it **Kodiak**.

### Guerrilla move #1: don't build the brain, hire it

The first plan had two tracks. Track A: train a brand-new model from scratch. Track B: take an open model that already knows how to read
English (ModernBERT, from Answer.AI, trained on about two trillion words) and teach it a new job.

On day one, Track B produced a working model in **35 minutes**. Shane asked the question that killed Track A on the spot: *"Track A has to
literally learn to read?"* Yes, and on one desktop box it would have spent days reading a tiny fraction of what ModernBERT already had, only to
end up a worse reader. Someone else had already paid millions for "reading." The guerrilla move was to hire the reader and teach it to decide.
Track A got shelved with a note: *if Kodiak ever earns money, we'll build our own brain.*

The part Kodiak did build is the clever part. Instead of generating text, it reads a whole request in one pass: the document, then every
question, then every question's options, packed into one sequence, with custom rules about who can "see" whom inside the model. Picture an
exam hall where every question sits in its own soundproof booth with a window onto the same document. The payoff:
- **it answers every question at once in about 8 milliseconds;**
- it can never pick an option you didn't give it;
- shuffling the options can't change its answer (the classic chatbot habit of favoring "option A" is impossible by construction);
- and every question can come back as **"I can't tell from this,"** with a probability you can actually trust.

To wire those booths, Kodiak re-implemented ModernBERT's entire architecture in its own code, then proved the copy was **bit-identical** to the
original. Not close: identical.

### Guerrilla move #2: pick a fight you can learn from

Day one also brought the first fight: Kodiak against Qwen 27B, a chatbot about 180 times its size, running on the same box. Kodiak was about
**400 times faster** (8 ms vs. 3.4 seconds), roughly tied on familiar kinds of tasks, and about twice as trustworthy about its own confidence.
Then the gut punch: on kinds of tasks it had never seen, the big model was **21 points better** (86% vs. 65%). That gap became the villain.

The fight also set the project's sportsmanship rule. The first time they ran Qwen, it refused 96% of judgment questions, because the prompt
said "only use information in the text." Declaring victory would have been easy. Instead they fixed the prompt twice and compared only once
the big model had a fair shot. Beating a handicapped opponent proves nothing.

### Guerrilla move #3: a data factory that runs on pennies

A small model learns from examples, and good examples cost money. So they built a **synthetic data factory**: a big open AI writes
realistic documents (support chats, invoices, server logs, legal letters) and questions about them, some deliberately unanswerable. First on
the Spark itself (3,290 examples, free), then, when that was too slow, on rented open-weight models in the cloud.

Three rules made it cheap *and* trustworthy:
1. **No sketchy teachers.** Grok was cheap, but its terms forbid using outputs to build competing models, and Kodiak's data will be public.
   Only openly licensed models were allowed: gpt-oss-120b as the writer and DeepSeek V3.2 as the checker.
2. **Don't let the student grade its own homework.** Why not let the writer check its own work? Instead of arguing, they ran a bake-off
   against Shane's hand-graded answers. A model from a *different company* answering blind agreed with him 97% of the time; the writer checking
   itself managed 92%, ten times slower. And a 397-billion-parameter contender thought for three and a half minutes and returned nothing.
3. **Pilot everything.** The first cloud pilot kept just 26% of its output, because the writer paraphrased its evidence instead of quoting it.
   Three small fixes later: 88%. That pilot cost **four cents**.

The first real batch, 6,412 examples, cost **$8.46**.

### The humbling: more data didn't help

Here's where the heist hit its first alarm. They trained three identical models on 0, 3,300 and 9,400 synthetic examples. More data helped
overall accuracy and calibration, but on never-seen tasks, the villain, the line was **flat**.

The detective work found two culprits:
- **The model had learned to refuse too much.** The synthetic data taught "if the fact isn't written down, say you can't tell," and Kodiak
  started refusing questions any reasonable person could infer: a biography that never literally says "attorney," or "why hasn't my card
  arrived?", which obviously means card delivery. It had become the coworker who won't answer anything that isn't in the email verbatim.
- **It was cramming.** The training mix showed a few tiny datasets 20 to 30 times per run: the prompt-injection examples 29 times. It was
  memorizing flashcards instead of learning.

The fix cost nothing: cap every dataset at three passes and let training finish its schedule. Never-seen-task accuracy jumped **nearly four
points** overnight. The bigger lesson became a rule: **decide what result would change your plan before you run the experiment.** They had
written down "if more data doesn't help, stop buying more of the same," so a disappointing result turned into a clear next move: *better* data,
not more.

### Guerrilla move #4: smarter data, and a human in the loop

So the factory got rebuilt. Instead of 60 hand-typed topics: 16 sectors expanded by the AI into **971 kinds of documents** (tenant noise
complaints, CI logs, payment webhooks, soil test reports) for about **a penny**. About 45% of examples now used **real text from the web**, with
the AI only writing questions. Every question was labeled *stated*, *inferred* or *truly unanswerable*, to cure the refusing habit.

Reading the rejects, not just counting them, caught a sneaky teacher: the writer kept slipping options like **"Not known"** into the answers,
a second way to say "I don't know" that would have muddled Kodiak's calibrated abstention. Banned. A whole morning of pilots cost **25 cents**.

Then Shane graded 165 of the new answers by hand: 92.7% right, and every "unanswerable" correct. The misses had a pattern that made the
episode's best line: questions with two defensible answers where **two AIs from two different companies agreed on the same wrong answer.**
Agreement isn't correctness. The fix: stricter rules plus two AI "critics" whose only job is to attack each answer. The full new batch,
**9,428 examples, cost $25.38**.

### The 3 a.m. plot twist

Then the showdown: the same model trained on the old data vs. the new data, same size, same recipe, running overnight on the Spark.

**9 p.m.:** triumph. The new data won by five to seven points on never-seen tasks. It even fixed the demo case where a customer's box arrived
crushed and the old model thought they wanted "delivery status."

A lot of projects would have tweeted that. This one did the unglamorous thing. Training is random (which examples come first, how the new
layers start out), so each version was trained **three times** with different random seeds. Four more hours of the Spark humming in the dark.

**3 a.m.:** the averages told a more honest story. On never-seen tasks, old and new data **tied**: 72% each. The first run of the old data had
simply been unlucky; one test task swings twenty points between runs with *identical* data. But in every single run, the new data did exactly
what it was built to do: wrong "can't tell" answers dropped by about 60%, its "can't tell" became right 92% of the time instead of 84%, and it
got better calibrated. The rulebook got a new line: **one training run is an anecdote. No claim without three.**

### The honest scoreboard

The goal was never "beat ChatGPT." It was **frontier in its class**: the best open model for *decisions*, deployed as the fast "System 1"
in front of a slow "System 2." Kodiak answers everything in milliseconds, confident answers get used immediately, and only the uncertain ones
go to a big model or a human. Because its confidence is calibrated, "90% sure" really means about 90% right, so you only pay big-model prices on
the hard cases.

And they wrote down what "best in class" would have to mean **before** measuring it: beat every open zero-shot classifier on never-seen tasks,
come within about 10 points of an 8-billion-parameter chatbot at 100 times its speed, and have the best calibration of anyone.

Then they measured against the real rivals, the open models people actually use to label text, each about **three times Kodiak's size**:
- **Overall, a blowout:** 78% accuracy vs. 55% for the best rival, calibration error 0.049 vs. 0.156, and faster (8 ms vs. 27 ms), while also
  handling numeric scores and "can't tell," which the rivals can't do properly.
- **On never-seen tasks: roughly tied.** About 72% averaged over three runs, vs. 70.5% for the best rival; that's inside the noise.
- **The contamination catch:** one rival looked great on banking intents, one of Kodiak's supposedly never-seen tests, until its model card
  showed it had *trained on that dataset*. Its clean version dropped 12 points. A zero-shot score only counts if the model never saw the test.

Verdict: **ahead on almost everything, tied where it matters most, not frontier-class yet.** Writing the bar down first is what makes that
sentence honest.

### Going public, the guerrilla way

Within four days the whole thing was public:
- the code, and every decision and dead end, on GitHub;
- the model on Hugging Face under Cortex Agent LLC;
- a free demo anyone can type into;
- a one-click hosting option.

Kodiak runs in 8 ms on a GPU and about **80 ms on a plain CPU**, so nobody needs special hardware. Even the launch had a caught-it-ourselves
moment: the first upload was missing its calibration settings, because the evaluation code had been applying them separately. Lesson: test
the thing users actually download.

The model page lists its misses out loud. It still rates "I was charged twice and nobody answers my emails!" as barely urgent, and close
calls can flip on small wording changes. The plan to make money is just as scrappy: the weights stay free, which builds trust and adoption,
and a hosted Kodiak API from Cortex Agent is for teams who just want an API key.

### The rating riddle

Next target: Kodiak's weakest skill, ratings. It still called "I was charged twice and nobody answers my emails!" barely urgent. The plan was
the usual trick: have the AI factory write practice examples with the right rating. Five pilot runs, about ten cents each, revealed a riddle:
**the AI teachers couldn't agree on the ratings themselves.** Two different models read the same tenant email; one said the tenant was furious
(9 out of 10), the other said mildly annoyed (3). Worse, when the writer was told to make a situation "highly urgent," it graded its own work as
highly urgent even when the text wasn't. On multiple-choice questions the teachers agree almost every time; on ratings they disagreed more than
half the time. You can't teach a sharp answer from a wobbly answer key. So the batch was paused after 54 cents, the lesson went in the notebook,
and the next idea (coarser labels: low, medium, high) is waiting on the bigger brain's results.

### Where it stands right now

As this was written, the Spark was training **ModernBERT-large**, a reader about three times bigger, three times over, to answer the next
question: is model size what's holding back never-seen tasks? A bigger, cleaner test set is being assembled so one noisy task can't swing the
verdict. Targeted data for the judgment-score weakness (urgency, risk) is next.

The open question to end on: **can a four-day, $35 garage project with a fully open recipe become the go-to open model for decisions, and
what changes for everyone building with AI if the answer is yes?**

---

## The guerrilla playbook (the rules this project runs on)

1. **Hire the brain, build the job.** Start from open pretrained weights; fine-tuning a decision layer takes an hour, learning to read takes months.
2. **Own your hardware, rent the rest by the penny.** Training runs free on a desktop box; big models are rented only to *write practice data*.
3. **Pilot everything.** Four cents to find out a pipeline is broken beats forty dollars.
4. **Don't let the student grade its own homework.** Use a checker from a different family, and grade a sample by hand.
5. **Read the data, not just the metrics.** Most real bugs were found by reading examples.
6. **Clean licenses only,** verified at the source, so everything can be given away.
7. **Give your rivals their best shot,** and check whether they trained on your test.
8. **Decide what would change your mind before you run the experiment.**
9. **One training run is an anecdote.** Three before any claim.
10. **Publish the misses.** Honesty is the marketing.

## The receipt

| Item | Cost |
|---|---|
| Hardware | $0 extra (an NVIDIA DGX Spark Shane already owned) |
| Training compute | $0 (every training run, about an hour each, on the Spark) |
| First synthetic batch (6,412 examples, cloud) | $8.46 |
| Second-generation batch (9,428 examples, with two AI critics) | $25.38 |
| Pilots (incl. five rating pilots), taxonomy, checker bake-off | about $1.40 |
| **Total cloud spend** | **about $35** |
| Time | about four days, one person plus an AI pair engineer |

## Wait-what moments

- 8 milliseconds vs. 3.4 seconds: **400× faster** than a 27B chatbot on the same desk.
- First working model: **35 minutes**.
- A cloud pilot of training data: **four cents**. A map of 971 document types: **a penny**.
- A 397-billion-parameter model **thought for 3.5 minutes and said nothing**.
- The model saw one dataset **29 times** per run. It was cramming.
- Two AIs from two companies **agreed on the wrong answer**; a human caught it.
- The new data "won by 7 points" at 9 p.m. and **tied** by 3 a.m.
- A rival "zero-shot" model had **trained on the test**.

## Fact sheet (for accuracy)

- **Model:** encoder-only; ModernBERT-base backbone (Apache-2.0) plus Kodiak's decision heads, about 152M parameters. Choice answers via a
  label-matching head (new label sets work zero-shot), a "can't tell" head, and a score head using a Beta distribution (always in range, with
  an uncertainty interval). Trained with log loss (a proper scoring rule), then temperature-calibrated on validation data.
- **Data:** 20 public datasets (356k examples), licenses verified at the source; 4 held out entirely to test never-seen tasks. Synthetic: v1
  (9,702 examples) and v2 (9,428), from open-weight teachers only.
- **Best current model:** "kodiak-small-v2-preview": overall 79.5%, familiar tasks 81.3%, never-seen tasks 70.3% (72% averaged when forced to
  answer), calibration error 0.028–0.029, abstain precision about 92%; 8 ms GPU, about 80 ms CPU.
- **Rivals:** Qwen 27B (86% on never-seen tasks on a 200-example sample, 3.4 s); GLiClass-instruct-large (439M; 70.5% never-seen forced, 54.8%
  overall, calibration error 0.156, 27 ms).
- **Open source:** Apache-2.0 code and weights by Cortex Agent LLC; github.com/grizzlypeaksoftware/kodiak; Hugging Face "cortex-agent-llc".
  Inspired by Jev, built independently; no claims about Jev's internals.
