# Bootstrapped: one engineer, one desk, and about $45 toward a frontier-class open model

*Source material for a single podcast episode (NotebookLM audio overview) about the Kodiak project. It's one continuous story. Every
number in it is measured and true; the tone is meant to be fun. Current as of September 26, 2026.*

---

## For the hosts

Tell this as **one story**, start to finish: a bootstrapper's story. No investors, no research lab, no cluster of rented GPUs. One engineer
who already runs two small companies, one desktop computer he already owned, an AI pair programmer, and about **$45** of cloud
credit, grinding toward something the big labs spend fortunes on: a frontier-class model in its category.

The heart of the episode is **gritty resourcefulness**: doing more with less, spending pennies before dollars, owning the hardware, borrowing
what's free and legitimately licensed, and doing the unglamorous checking that most people skip. Celebrate the sweat, the small wins, the
receipts, and the honesty about what didn't work.

Keep it energetic, warm and funny, but never claim more than the numbers say. Kodiak is not trying to beat GPT or Claude at being GPT or
Claude. It's trying to be the best open model in *its* class, and the story is honest that it isn't there yet. End on the open question.

---

## The story

### A bootstrapper with an itch

In September 2026 a company called TypeSafe AI announced Jev, a closed "System One" decision model. Shane Larson, a veteran software
engineer who runs two small companies, Cortex Agent LLC and Grizzly Peak Software, and a book-publishing business on the side, read about it
and couldn't let it go. The idea behind it was too good: most of what companies pay giant AI models to do **isn't writing at all. It's
deciding.** Which of these twelve intents is this customer message? How urgent is this ticket? Which tool should this AI agent call next? Is
this a prompt-injection attack? Can this even be answered from what we know?

Today most of those decisions go to a chatbot the size of a small city, which writes out an answer word by word, costs money every time,
takes seconds, and occasionally answers something that isn't even one of your options. That's like hiring a novelist to sort your mail.

Shane had never trained a machine-learning model. He had no funding round, no team and no lab. What he did have was an NVIDIA DGX Spark on his
desk (a desktop-sized AI computer he'd already bought, the same machine that helps run his publishing business) and Claude, Anthropic's AI,
as a pair engineer in his terminal. The plan: build an **open** version from scratch, his own way, on what he already had, and see how close
to frontier-class a self-funded, one-desk project can get. The ground rules:
- no chatbot underneath;
- it must be physically unable to answer outside the options you give it;
- only permissively licensed data and models, so everything can be given away;
- an honest comparison against real rivals, including publishing the losses.

He called it **Kodiak**.

### Bootstrapper rule #1: don't pay for what you can borrow

The first plan had two tracks. Track A: train a brand-new model from scratch. Track B: take an open model that already knows how to read
English (ModernBERT, from Answer.AI, trained on about two trillion words) and teach it a new job.

On day one, Track B produced a working model in **35 minutes**. Shane asked the question that ended Track A on the spot: *"Track A has to
literally learn to read?"* Yes, and on one desktop box it would have spent days reading a tiny fraction of what ModernBERT already had, only to
end up a worse reader. Someone else had already paid millions for "reading," and released it openly. A bootstrapper takes that gift, says
thank you, and builds the part nobody has built yet. Track A got shelved with a note: *if Kodiak ever earns money, we'll build our own.*

The part Kodiak did build is the clever part. Instead of writing out answers, it reads a whole request in one pass: the document, then every
question, then every question's options, packed into one sequence, with custom rules about who can "see" whom inside the model. Picture an
exam hall where every question sits in its own soundproof booth with a window onto the same document. The payoff:
- **it answers every question at once in about 8 milliseconds;**
- it can never pick an option you didn't give it;
- shuffling the options can't change its answer (the classic chatbot habit of favoring "option A" is impossible by construction);
- and every question can come back as **"I can't tell from this,"** with a probability you can actually trust.

To wire those booths, Kodiak re-implemented ModernBERT's entire architecture in its own code, then proved the copy was **bit-identical** to the
original. Not close: identical. Doing it yourself doesn't mean doing it sloppy.

### Bootstrapper rule #2: measure yourself against the big kids, fairly

Day one also brought the first reality check: Kodiak against Qwen 27B, a chatbot about 180 times its size, running on the same desk. Kodiak was
about **400 times faster** (8 ms vs. 3.4 seconds), roughly tied on familiar kinds of tasks, and about twice as trustworthy about its own
confidence. Then the gut punch: on kinds of tasks it had never seen, the big model was **21 points better** (86% vs. 65%). That gap became the
thing to chase.

It also set a rule of fair play. The first time they ran Qwen, it refused 96% of judgment questions, because the prompt said "only use
information in the text." Declaring victory would have been easy. Instead they fixed the prompt twice and compared only once the big model had
a fair shot. A win against a handicapped opponent isn't worth anything.

### Bootstrapper rule #3: spend pennies before dollars

A small model learns from examples, and good examples usually cost money. So they built a **data factory on a shoestring**: a big open AI
writes realistic documents (support chats, invoices, server logs, legal letters) and questions about them, some deliberately unanswerable. First
on the desk machine itself (3,290 examples, free), then, when that was too slow, on open-weight models rented in the cloud by the penny.

Three habits kept it cheap *and* trustworthy:
1. **Only clean, free-to-use teachers.** Grok was cheap, but its terms forbid using outputs to build competing models, and Kodiak's data will be
   public. Only openly licensed models were allowed: gpt-oss-120b as the writer and DeepSeek V3.2 as the checker.
2. **Don't let the student grade its own homework.** Why not let the writer check its own work? Instead of arguing, they ran a bake-off
   against Shane's hand-graded answers. A model from a *different company* answering blind agreed with him 97% of the time; the writer checking
   itself managed 92%, ten times slower. And a 397-billion-parameter contender thought for three and a half minutes and returned nothing.
3. **Pilot everything.** The first cloud pilot kept just 26% of its output, because the writer paraphrased its evidence instead of quoting it.
   Three small fixes later: 88%. That pilot cost **four cents**. Finding a broken pipeline for four cents beats finding it for forty dollars.

The first real batch, 6,412 examples, cost **$8.46**.

### The humbling: more wasn't better

Then came the first hard lesson. They trained three identical models on 0, 3,300 and 9,400 synthetic examples. More data helped overall
accuracy and calibration, but on never-seen tasks, the number that mattered most, the line was **flat**.

The digging found two culprits:
- **The model had learned to refuse too much.** The synthetic data taught "if the fact isn't written down, say you can't tell," and Kodiak
  started refusing questions any reasonable person could infer: a biography that never literally says "attorney," or "why hasn't my card
  arrived?", which obviously means card delivery. It had become the coworker who won't answer anything that isn't in the email verbatim.
- **It was cramming.** The training mix showed a few tiny datasets 20 to 30 times per run: the prompt-injection examples 29 times. It was
  memorizing flashcards instead of learning.

The fix cost nothing: cap every dataset at three passes and let training finish its schedule. Never-seen-task accuracy jumped **nearly four
points** overnight. The lesson became a rule: **decide what result would change your plan before you run the experiment.** They had written down
"if more data doesn't help, stop buying more of the same," so a disappointing result became a clear, cheap next move: *better* data, not more.

### Bootstrapper rule #4: work smarter, and check your own work

So the factory got rebuilt for quality. Instead of 60 hand-typed topics: 16 industries expanded by the AI into **971 kinds of documents**
(tenant noise complaints, CI logs, payment webhooks, soil test reports) for about **a penny**. About 45% of examples now used **real text from
the web**, with the AI only writing questions. Every question was labeled *stated*, *inferred* or *truly unanswerable*, to cure the refusing habit.

Reading the rejects, not just counting them, caught a sneaky teacher: the writer kept slipping options like **"Not known"** into the answers,
a second way to say "I don't know" that would have muddled Kodiak's calibrated abstention. Banned. A whole morning of pilots cost **25 cents**.

Then Shane graded 165 of the new answers by hand, the unglamorous part most people skip: 92.7% right, and every "unanswerable" correct. The
misses had a pattern: questions with two defensible answers where **two AIs from two different companies agreed on the same wrong answer.**
Agreement isn't correctness. The fix: stricter rules plus two AI "critics" whose only job is to attack each answer. The full new batch,
**9,428 examples, cost $25.38**.

### The 3 a.m. check

Then the head-to-head: the same model trained on the old data vs. the new data, same size, same recipe, running overnight on the desk.

**9 p.m.:** it looked like a big win. The new data beat the old by five to seven points on never-seen tasks. It even fixed the demo case where a
customer's box arrived crushed and the old model thought they wanted "delivery status."

The easy move was to post that and go to bed. Instead: training is random (which examples come first, how the new layers start out), so each
version was trained **three times** with different random seeds. Four more hours of the machine humming in the dark, for free, because the
hardware was already paid for.

**3 a.m.:** the averages told a more honest story. On never-seen tasks, old and new data **tied**: 72% each. The first run of the old data had
simply been unlucky; one test task swings twenty points between runs with *identical* data. But in every single run, the new data did exactly
what it was built to do: wrong "can't tell" answers dropped by about 60%, its "can't tell" became right 92% of the time instead of 84%, and it
got better calibrated. The notebook got a new rule: **one training run is an anecdote. No claim without three.**

They also fixed the scoreboard itself. The never-seen test covered only four tasks, too few to trust, so they added eight more, every license
checked at the source: legal contracts, moral judgments, finance posts, scientific abstracts, court cases, clickbait ratings and poetry. The
never-seen test grew from 1,000 examples to 4,200.

### The rating riddle

Next target: Kodiak's weakest skill, ratings. It still called "I was charged twice and nobody answers my emails!" barely urgent. The plan was
the usual move: have the AI factory write practice examples with the right rating. Five pilot runs, about ten cents each, turned up a riddle:
**the AI teachers couldn't agree on the ratings themselves.** Two different models read the same tenant email; one said the tenant was furious
(9 out of 10), the other said mildly annoyed (3). Worse, when the writer was told to make a situation "highly urgent," it graded its own work as
highly urgent even when the text wasn't. On multiple-choice questions the teachers agree almost every time; on ratings they disagreed more than
half the time. You can't teach a sharp answer from a wobbly answer key. So a bootstrapper does the thrifty thing: stop after **54 cents**, write
down the lesson, and try a coarser idea (low, medium, high) only if the next experiment says it's still needed.

### Losing at Zork, on purpose, in public

Then Shane did something most model builders wouldn't: he put Kodiak head to head with Jev in a text adventure, Zork, and published the loss.
Both models played by choosing from the game's valid commands, so across about twenty thousand moves **neither made a single invalid one.** That
part held perfectly. The rest was humbling. On Zork, Kodiak lost to a baseline with no model at all, one that just tried untried things at random.
Jev played clearly better: its own moves earned 45 points to Kodiak's almost none. The new v2 Kodiak was the cautionary tale: confident, not
right, it spent ninety-five turns picking up and putting down the same piece of paper while the exit sat on the list every turn. Its calibration
had looked like the best ever on the test set; on game states it had never seen anything like, it meant nothing. Even Jev wasn't spared: three
times it walked into a grue in the dark while its own answer to "is the player in danger?" said yes at 95%. The harness hadn't listened. Two
bootstrapper lessons came out of it: one sentence of question wording made Kodiak's moves 35 times more productive, and a model that's
confidently wrong is more dangerous than one that's unsure, because nobody takes the wheel.

### The honest scoreboard

The goal was never "beat ChatGPT." It was **frontier in its class**: the best open model for *decisions*, deployed as the fast "System 1"
in front of a slow "System 2." Kodiak answers everything in milliseconds, confident answers get used immediately, and only the uncertain ones
go to a big model or a human. Because its confidence is calibrated, "90% sure" really means about 90% right, so you only pay big-model prices on
the hard cases. For a small business, that's the whole point: expensive AI only where it earns its keep.

They wrote down what "best in class" would have to mean **before** measuring it: beat every open zero-shot classifier on never-seen tasks, come
within about 10 points of an 8-billion-parameter chatbot at 100 times its speed, and have the best calibration of anyone.

Then they measured against the real rivals, the open models people actually use to label text, each about **three times Kodiak's size**:
- **Overall, a clear win:** 78% accuracy vs. 55% for the best rival, calibration error 0.049 vs. 0.156, and faster (8 ms vs. 27 ms), while also
  handling numeric scores and "can't tell," which the rivals can't do properly.
- **On never-seen tasks: small roughly tied, large won.** On the original four-task test the small model was inside the noise of the best
  rival; on the bigger twelve-task test the large model beat every rival by three points.
- **The contamination catch:** one rival looked great on banking intents, one of Kodiak's supposedly never-seen tests, until its model card
  showed it had *trained on that dataset*. Its clean version dropped 12 points. A zero-shot score only counts if the model never saw the test.

Verdict: **ahead on almost everything, and with the larger model now ahead where it matters most, but not frontier-class yet:** calibration on unfamiliar tasks and ratings are still weak. Writing the bar down first is what keeps that
sentence honest.

### Shipping it, bootstrapper style

Within four days the whole thing was public, for free:
- the code, and every decision and dead end, on GitHub;
- the model on Hugging Face under Cortex Agent LLC;
- a free demo anyone can type into;
- a one-click hosting option.

Kodiak runs in 8 ms on a GPU and about **80 ms on a plain CPU**, so nobody needs special hardware to use it, which matters to the kind of small
teams who'll use it. Even the launch had a caught-it-ourselves moment: the first upload was missing its calibration settings, because the
evaluation code had been applying them separately. Lesson: test the thing users actually download.

The model page lists its misses out loud: it still rates "I was charged twice and nobody answers my emails!" as barely urgent, and close calls
can flip on small wording changes. The business plan is bootstrapped too: the weights stay free, which builds trust and adoption, and a hosted
Kodiak API from Cortex Agent is for teams that just want an API key. Shane has set aside a $500 cloud budget, to be spent only where an
experiment proves it's worth it.

### The bigger brain reports back

Next came the experiment the whole week had been pointing at: a bigger reader. The desk machine trained **ModernBERT-large**, about three times
the size, three times over (free, overnight-style, on hardware already paid for), and every model was re-graded on the new twelve-task test.
The result was the first clean win against the field: **on never-seen tasks, large Kodiak scored 60.9%, beating every open zero-shot
classifier** (the best clean rival scored 57.9%), with the three runs agreeing within less than a point. The small model only tied. It was
strongest exactly where Kodiak had been weakest: guessing someone's job from a biography jumped 14 points, and on legal contract clauses it
scored 84% while the rivals managed 20 to 63%. The first line of the bar written down days earlier, "beat every open classifier on never-seen
tasks," was finally met. Two things size didn't fix: ratings, and knowing when it's out of its depth.

### The trick that didn't work (and cost nothing to learn)

Averaging three trained copies of the large model made Kodiak much more honest about uncertainty, but three models means three times the
compute. So one evening the desk machine tried to have it both ways: train one small model to imitate the trio. Three overnight runs later, the
verdict: no better, and slightly *worse* at knowing when it's unsure. The trio had been quizzed on homework they'd already memorized, so they
were confidently right about everything and had no wisdom to pass on. Price of the lesson: zero dollars, a night of electricity. It went straight
into the public decision log, dead end and all.

The same night, two cheaper wins: Kodiak learned to run without Python (a plain Node.js server in a Docker container, about 30 milliseconds per
request on an ordinary processor), and a ten-dollar batch of practice data went out to teach it "mixed" and "neutral", after Shane noticed his
own demo calling a two-sided review "positive."

### The 2 a.m. scoreboard: small model plus big model beats both

The last test on the list was the one everybody asks about: how does Kodiak stack up against a real chatbot-style LLM? Shane's desk ran an open
8-billion-parameter model through the entire exam overnight. It won on never-seen tasks by about eight points, and every bit of that lead came
from questions that need outside knowledge: which science field a paper belongs to, legal case law, the mood of a poem. Where the answer is in
the text, Kodiak won or tied, while running on the order of a hundred times faster, and it was far more honest: the LLM said "can't tell" correctly
less than half the time, Kodiak 92%.

Then the fun part. Using only answers already saved on disk, a tiny script played out the real product idea: Kodiak answers when it's sure,
and only the rest goes to the LLM. **The team beat both players.** With Kodiak handling four questions out of five on its own, the pair scored
higher than the LLM alone, and handing over a few more put it three points ahead. The whole bet of the project, a fast model that knows what it
knows, working in front of a slow one that knows more, had its first real number. Cost of the experiment: zero dollars.

### Where it stands right now

The next fights are the two honest weak spots: calibration on unfamiliar tasks (the Zork lesson: a System 1 that knows when it's lost) and
ratings. The large model becomes the quality tier; the small one stays the fast tier.

The open question to end on: **can a self-funded, one-desk project with a fully open recipe become the go-to open model for decisions, and what
changes for every small team building with AI if the answer is yes?**

---

## The bootstrapper's playbook (the rules this project runs on)

1. **Borrow the brain, build the job.** Start from open pretrained weights; fine-tuning a decision layer takes an hour, learning to read takes months.
2. **Own the hardware, rent the rest by the penny.** Training runs free on a desktop box; big models are rented only to *write practice data*.
3. **Pilot everything.** Four cents to find out a pipeline is broken beats forty dollars.
4. **Don't let the student grade its own homework.** Use a checker from a different company, and grade a sample by hand.
5. **Read the data, not just the metrics.** Most real bugs were found by reading examples.
6. **Clean licenses only,** verified at the source, so everything can be given away.
7. **Give your rivals their best shot,** and check whether they trained on your test.
8. **Decide what would change your mind before you run the experiment.**
9. **One training run is an anecdote.** Three before any claim.
10. **Stop when the lesson is learned.** Fifty-four cents of pilots beat thirty dollars of noisy data.
11. **Publish the misses.** Honesty is the marketing.

## The receipt

| Item | Cost |
|---|---|
| Hardware | $0 extra (an NVIDIA DGX Spark Shane already owned) |
| Training compute | $0 (every training run, about an hour each, on the desk) |
| First synthetic batch (6,412 examples, cloud) | $8.46 |
| Second-generation batch (9,428 examples, with two AI critics) | $25.38 |
| Pilots (including five rating pilots), taxonomy, checker bake-off | about $1.60 |
| "Mixed and neutral" batch (3,894 examples) | $9.78 |
| **Total cloud spend** | **about $45** |
| Time | about four days, one person plus an AI pair engineer |

## Wait-what moments

- 8 milliseconds vs. 3.4 seconds: **400× faster** than a 27B chatbot on the same desk.
- First working model: **35 minutes**.
- A cloud pilot of training data: **four cents**. A map of 971 document types: **a penny**.
- A 397-billion-parameter model **thought for 3.5 minutes and said nothing**.
- The model saw one dataset **29 times** per run. It was cramming.
- Two AIs from two companies **agreed on the wrong answer**; a human caught it.
- The new data "won by 7 points" at 9 p.m. and **tied** by 3 a.m.
- Two AI teachers rated the same email's frustration **9 and 3**.
- A rival "zero-shot" model had **trained on the test**.
- Twenty thousand Zork moves, **zero invalid**; Kodiak still lost to random exploration on Zork.
- One sentence of question wording made Kodiak's moves **35× more productive**.
- The bigger model beat every open rival on never-seen tasks, with three runs agreeing **within less than a point**.
- Averaging three models made Kodiak more honest; teaching one model to copy the average made it **slightly less** honest.
- Kodiak answering 4 of 5 questions and passing the rest to an 8B LLM **beat the LLM answering all of them**.
- "Study only what you got wrong" **tied** with random studying, three runs each.
- A stranger on X reworded one sentence and Kodiak's confidence fell from **97% to 48%**: it had been matching words, not meaning.

## Fact sheet (for accuracy)

- **Model:** encoder-only; ModernBERT-base backbone (Apache-2.0) plus Kodiak's decision heads, about 152M parameters. Choice answers via a
  label-matching head (new label sets work zero-shot), a "can't tell" head, and a score head using a Beta distribution (always in range, with
  an uncertainty interval). Trained with log loss (a proper scoring rule), then temperature-calibrated on validation data.
- **Data:** 20 public datasets (356k examples), licenses verified at the source. Synthetic: v1 (9,702 examples) and v2 (9,428), from open-weight
  teachers only.
- **Evaluation:** a frozen test set, now v0.2: 6,102 examples, with 12 never-seen tasks (4,200 examples) that are never trained on.
- **Best current model:** "kodiak-small-v2-preview": overall 79.5%, familiar tasks 81.3%, never-seen tasks 70.3% (72% averaged when forced to
  answer), calibration error 0.028–0.029, abstain precision about 92%; 8 ms GPU, about 80 ms CPU.
- **Rivals:** Qwen 27B (86% on never-seen tasks on a 200-example sample, 3.4 s); GLiClass-instruct-large (439M; 70.5% never-seen forced, 54.8%
  overall, calibration error 0.156, 27 ms).
- **Open source:** Apache-2.0 code and weights by Cortex Agent LLC; github.com/grizzlypeaksoftware/kodiak; Hugging Face "cortex-agent-llc".
  Inspired by Jev, built independently; no claims about Jev's internals.
