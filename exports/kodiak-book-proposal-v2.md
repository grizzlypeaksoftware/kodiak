# Book Proposal: The Kodiak Field Guide

**Generated:** 2026-09-28. **Revised:** 2026-10-02 to the current state of Kodiak. v0.2 has shipped. Two open decisions are resolved
(timing and pinning). Figures are re-pulled from the v0.2 release. The outline gains the release, the Decision Index report card, the
rewording experiment that failed and then won, and the outside reviewer who changed the headline. Earlier draft: the claude.ai artifact
`DJxBwWPCg3GzqRjiarzr9M` and `~/development/kodiak/exports/kodiak-book-proposal.html`.

## Title
**The Kodiak Field Guide: Fast, Honest AI Decisions for Everyday Software**

## Subtitle Options
- Fast, Honest AI Decisions for Everyday Software
- Fast, Honest AI Decisions and the Open Model That Knows When to Say "I Can't Tell"
- How a Small Open Model Makes Reliable AI Decisions in Milliseconds

Alternative main titles from the draft: *The Bear Who Knew When to Ask* · *Decide in Milliseconds* ·
*System One: AI That Decides Fast and Admits What It Doesn't Know*

> ⚠ **TITLE GATE OUTSTANDING.** The §3 procedure (Amazon exact-phrase, Amazon title-plus-subtitle,
> Google exact-phrase) has not been run. Record `title_gate: "OUTSTANDING"` in metadata.json.

---

## Open decisions

**Resolved since the first draft**
1. ~~Timing~~ **Resolved.** Kodiak v0.2 shipped on 2026-10-02: **Kodiak-v0.2-1B** and its **accuracy mode** are public on Hugging Face
   (`cortex-agent-llc/kodiak-v0.2-1b`, `cortex-agent-llc/kodiak-v0.2-1b-accuracy`). The release has a published eval. The book can now
   be generated against real release numbers. (There was never a public "v0.1": the September models were research previews, and v0.2 is
   the first release.)
3. ~~Pinning~~ **Resolved: pin the whole book to "Kodiak-v0.2-1B, eval set v0.2"**, using the three-run figures. Every number cites
   that pin. The companion site carries v0.3+, and a second edition goes out with v1, not with every point release.

**Still open: resolve before `/new-book`**
2. **Imprint.** Unchanged. **Recommendation:** Peak Grizzly Publishing (same shelf as *Fine-Tuning LLMs* and *Loop Engineering*),
   crediting Cortex Agent LLC and Grizzly Peak Software as the makers of Kodiak inside the book.
4. **Release channel.** Unchanged. Draft2Digital by default under the 2026-09-27 allocation, or one of the two weekly KDP slots for a
   product-tied technical title. Shane's call; flag it before KDP Select enrolment.
5. **Naming people.** Two outside contributors now shape the story:
   - **The stranger on X** who found the rewording anomaly (Chapters 4 and 12). Keep them anonymous unless they agree to be credited.
   - **dipankarsarkar**, the Hugging Face user whose public comment showed that Kodiak's calibration lead over Qwen3-8B was partly a fixable
     offset and that its real lead is *ranking* (D60). Their comment is public, but ask before quoting or naming them.
   Either way, thank both in the Acknowledgements.
6. **New: the Decision Index chapter.** Kodiak's results on the public Decision Index benchmark (a preliminary run, not yet submitted) make
   a strong report-card story (Chapter 11). Under the standing rule, **leaderboard standings are not published without Shane's OK**, the same
   rule as submitting to the board. Decide whether to submit before the manuscript is generated. If not, the chapter describes per-skill
   results without a rank.

---

## Overview

**Genre:** AI & Technology / Hands-On Practitioner
**Target Length:** ~75,000 words: Introduction, 14 chapters in three parts, Conclusion, 4 appendices
**Projected print:** ~280 pages 6×9 (code listings and figures run long; *Fine-Tuning LLMs* is 339pp)
**Target Price:** $9.99 ebook, matching the catalog's premium technical titles · paperback priced at build from `print_page_count`
**Code:** short runnable Python and JavaScript, maintained in the Kodiak repo's `examples/` and tested against Kodiak-v0.2-1B
**Figures:** ~20 rendered diagrams and charts (see Format)
**Series Connection:** companion to *Fine-Tuning LLMs* (Chapter 9 is its practical sequel for a small model) and *Loop Engineering*
(Chapter 7 puts a decision model in the agent loop); cross-link with *Prompt Engineering for Real Work*.

---

## Premise

Most of what businesses want from AI isn't conversation. It's decisions: which team gets this ticket, is this message an attack, does this
contract clause allow that. Today people send those decisions to chatbots that are slow, expensive and confidently wrong.

This book is a field guide to a different kind of AI: an open **decision model** called Kodiak. You give it a situation (a message, a
document, a record) and questions with your own answer options. It returns an answer to every question at once, each with a calibrated
confidence, or an honest "I can't tell". On decisions it has never been trained for, the released 1-billion-parameter model matches an
8-billion-parameter chatbot in our tests, at about 40× the speed. And it is far better at the thing that makes automation safe: putting its
own mistakes at the bottom of its confidence list.

Psychologists describe a fast, automatic "System 1" and a slow, deliberate "System 2." AI products have been all System 2. Kodiak is a System
1: it handles routine decisions instantly and hands the hard ones to a person or a bigger model. Outside research points the same way (Li,
Miao, Krishnan and Padman at Carnegie Mellon, *JEV-as-a-Judge: Accept When Confident, Escalate When Unsure*, arXiv:2609.26550; **verify
before print**), and model routers are now shipping as products.

There is no accessible book on this. Machine-learning books assume math; LLM books assume the chatbot is the answer. This one fills the gap:
how to get reliable, cheap, fast AI decisions, and how to know when not to trust them. It is also the story of the model's open development,
from a desk in Alaska to a public release in ten days (2026-09-23 to 2026-10-02), for roughly $80 of cloud spend. Every result in it can be checked against the
published weights, eval, data recipe and decision log.

**Honesty is the brand.** Every number comes from a published test, averaged over three training runs, with its limits stated. Where Kodiak
loses, the book says so. When an outside reviewer showed that one of our headline comparisons was flattering, we changed the model card, and
the book tells that story too.

---

## Target Audience

- **Application developers** who've called an LLM API and want something faster, cheaper and more predictable for classification and routing
- **Product managers and founders** deciding where AI belongs in their product and how to make it trustworthy
- **Automation builders and small teams** (support desks, shops, publishers, agencies) who want AI help without a data-science department
- **Readers of *Fine-Tuning LLMs* and *Loop Engineering*** who want the small-model, decision-first counterpart
- **Curious technologists** who want to see how a model is actually built and tested, told as a story

**Assumed:** comfort reading short Python or JavaScript. **Not assumed:** any math, statistics or ML background. Every concept arrives with
an everyday analogy first: a weather forecast for calibration, a new employee who knows when to ask for help for abstention, a triage nurse
sorting a waiting room for ranking.

### What readers will be able to do
- Explain the difference between a decision model and a chatbot, and pick the right one for a job
- Run Kodiak three ways: the free web demo, five lines of Python, or a self-hosted server in Docker
- Write questions and answer options that get reliable results, and recognise the wording traps
- Build a review queue: automate the confident answers, route the rest to a human
- Put Kodiak in front of an LLM as a fast first pass and measure what it saves
- Test any AI system honestly: held-out tests, repeated runs, calibration *and* ranking, and a public benchmark used as a report card

---

## Key Themes

### 1. Most AI is a decision in disguise
Routing, flagging, approving, sorting: the hidden majority of AI work has a short list of right answers. A generative model is the wrong tool
for it on speed, cost, format and honesty.

### 2. Confidence you can measure, and confidence you can rank
Calibration (when Kodiak says 90%, is it right about 90% of the time?) and, more important for automation, ranking: does high confidence
actually mark the right answers, and low confidence the mistakes? The second can't be faked by adjusting the numbers afterwards, and it's
where Kodiak's lead over the 8B chatbot is largest (55.6% vs 14.7% of the way from a random order to a perfect one).

### 3. "I can't tell" is the most valuable answer
Abstention is what turns a model into something you can automate. The book treats it as the spine, not a footnote.

### 4. Fast first, smart second
The cascade: Kodiak takes the confident cases, the LLM gets the rest.

### 5. Teach the kind, not more of the same
Every big gain came from a new *kind* of data or a bigger model, never from more of the same. Four new kinds of decision (E17), taught
with checked synthetic data for about $22, carried over to real public benchmarks. A skills roadmap now screens dozens of candidate kinds
before spending anything.

### 6. Built in public, with the failures left in
Three runs before any claim, a second AI checking the first, a run of experiments that failed, one failure that turned out to be the
release's biggest win, and the budget that made it possible. The decision log is the source, not a retrospective.

### 7. Knowing the limits
Wording still moves answers, long-document hallucination is unsolved, ratings are rough, and decisions about people need a human.

### 8. The human in the loop is the one doing the thinking
Kodiak was built by one person working with AI partners: Claude as pair engineer, open models as teachers and checkers. The AI brought
speed, breadth and tireless implementation. The humans brought what the project couldn't run without: noticing which anomaly matters,
forming a theory, imagining the experiment that would test it, and deciding what counts as proof. Two of the turning points came from
strangers: a rewording on X and a calibration critique on Hugging Face. That is the near future of technical work, and it asks more of
people, not less.

---

## Where Kodiak stands: Kodiak-v0.2-1B, eval set v0.2 (re-pull from the reports at generation time)

"Never-seen" = tasks and label sets the model was never trained on. Kodiak figures with ± are three-run means.

| Claim | Result | Status |
|---|---|---|
| Matches an 8B chatbot on decisions it never trained for | 0.689 ± 0.008 vs Qwen3-8B 0.688 (accuracy mode: 0.706) | **Met** |
| At least 40× faster | ~38 ms vs ~1,500 ms per request (GPU) | **Met** |
| Ranks its own mistakes last (what a confidence threshold relies on) | 55.6% vs 14.7% | **Kodiak far ahead** |
| Confidence is honest (calibration error, never-seen; lower is better) | 0.085 vs 0.293 raw; **0.044-0.058 vs 0.178** after giving both the same fitted recalibration | Ahead, by less than the raw numbers say |
| When it says "can't tell", it's right | 0.88 (accuracy mode 0.905; target 0.90) | Accuracy mode met; single model **not yet** |
| Same answer when the options are reworded | 0.68 of never-seen questions (v0.3 goal) | **Not yet** |
| Kodiak first, chatbot only when unsure, beats the chatbot alone | measured on the September large model (74.0% vs 70.9%) | **Re-run on v0.2 before print** |

The book states the "not yet" rows plainly. That is the brand.

---

## Chapter Outline

Heading scheme for writers: `introduction.md` and `conclusion.md` use `### Introduction: …` / `### Conclusion: …`; chapter files use
`#### Chapter N: …`; part openers are `###`.

### Introduction: Most AI Is a Decision
- A support team paying a chatbot to read an email and pick one of four words: the slow, per-call round trip, multiplied by a million
- Decisions dressed up as conversation: the ticket, the review, the contract clause, the jailbreak
- Why a chatbot is the wrong tool: slow, costly per call, can answer outside your options, equally confident right or guessing
- System 1 and System 2, and the outside evidence that "accept when confident, escalate when not" works
- Meet Kodiak, named for the largest bears in Alaska, where it was built; how the book is organised

### Part One: Meet the Bear

**Chapter 1: What a Decision Model Is**
- Situations, questions and your own options; choice, score and "can't tell" as the three answer shapes
- Reading models versus writing models (encoders versus decoders), without math
- Why reading is so much faster than writing
- The release: Kodiak-v0.2-1B (built on Ettin-encoder-1B, Johns Hopkins, MIT) and accuracy mode (three models averaged); Apache-2.0;
  what "open" covers: weights, eval, data recipe, decision log. The smaller research previews (150M, 400M) as the road there.
- **The showcase exchange, done two ways:** the walnut-desk ticket where Kodiak is confident and right about the intent (0.94) and
  correctly says "can't tell" about the carrier

**Chapter 2: Confidence You Can Trust**
- Calibration through the weather forecast: does it rain on 70% of the 70% days?
- Ranking through the triage nurse: are the patients she's surest about really the ones who can wait?
- Why an LLM's stated confidence is text, not a measurement, and the reviewer's lesson that a constant overconfidence can be corrected
  while bad ranking can't
- The numbers: 0.085 vs 0.293 raw, 0.044-0.058 vs 0.178 recalibrated, ranking 55.6% vs 14.7%

**Chapter 3: The Honest "I Can't Tell"**
- Abstention as the feature that makes automation safe; the new employee who knows when to ask
- The missing carrier, the unanswerable question, and "can't tell" precision (0.88; 0.905 in accuracy mode)
- Thresholds: trading coverage for accuracy, and choosing the trade on purpose
- What abstention cannot do: it knows when the answer is absent, not when the question is wrong

### Part Two: Put Kodiak to Work

**Chapter 4: Your First Decisions**
- The web demo, then five lines of Python
- Writing good questions and options: mutually exclusive, exhaustive, short and plainly worded
- The stranger who reworded one sentence and dropped confidence from 97% to 48%; and the related finding that reworded options change the
  answer on about a third of never-seen questions. Practical advice: keep labels short and distinct, and test a few wordings on your own data
- Hands-on: the demo · Python quick start

**Chapter 5: Sorting the Pile**
- Categorising a spreadsheet of reviews or tickets in seconds (the demo's categorizer tab)
- The review queue: confident rows through, uncertain rows to a person
- Choosing the threshold from your own error costs, and why ranking quality decides how much you can automate
- Hands-on: a categoriser with a review queue

**Chapter 6: Guardrails in Front of Your Chatbot**
- Prompt injection and jailbreaks explained for non-specialists
- Kodiak as a filter before the LLM; jailbreak detection on never-seen data (0.89-0.92 on eval v0.2); injection results **re-pulled for v0.2**
- Grounding checks (new in v0.2): is this answer supported by its source, and which sentence isn't
- Layering filters, and what they can't catch
- Hands-on: an injection filter and a grounding check

**Chapter 7: The Cascade: Fast First, Smart Second**
- Kodiak answers the confident cases; the LLM gets the rest
- Measuring the trade-off: accuracy, cost, latency, and the fraction escalated (**re-run on v0.2**)
- Picking an assistant's next step from API specs (call a tool, ask for missing information, answer directly), new in v0.2
- Decision models inside agent loops (link to *Loop Engineering*)
- Hands-on: a working router with cost math

**Chapter 8: Running It Yourself**
- What a GPU and a CPU handle, measured (~38 ms per request on a GPU; a few hundred milliseconds on a CPU)
- The Node.js server and Docker image; privacy by default
- When a hosted API is the better choice
- Hands-on: self-host in three commands

**Chapter 9: Teaching Kodiak Your Business**
- Turning past decisions (tickets, approvals, a publisher's release and pricing calls) into a private model
- The fine-tuning kit, which has shipped: a CSV in, a recalibrated model and a before-and-after report on held-back rows out (demo: 75.8% → 98.3%)
- Labelling, held-out testing on your own data, and "good enough" defined in advance
- Hands-on: the fine-tuning kit

### Part Three: How It's Made, and Who Makes It

**Chapter 10: Built in Public for About $80**
- The bootstrapper's playbook: borrowing a pretrained reader instead of training from scratch, then a bigger one (150M → 400M → 1B)
- Open-model teachers writing practice data, and a second AI checking the first
- The three-runs-before-any-claim rule, and why single runs lie
- The budget, the one desktop machine (82 GPU-hours, ~6 kWh), and what that constraint forced

**Chapter 11: The Report Card**
- A public benchmark used the right way: not to chase a rank, but to find out what the model can't do
- The first run's surprise (an input-format mismatch, fixed by one general rule), and what the report card said: near zero on
  hallucination checks, API calls, claim checks and product relevance
- Turning gaps into *kinds* of decision: four checked synthetic datasets (E17, ~$22) and a held-out skills test
- The test that couldn't fail (0.98 on data from the same generators) and the real-world check that could: product relevance 0.04 → 0.23,
  claim verification 0.12 → 0.23, function calling 0.20 → 0.28
- When "regressions" are luck: the three-seed diagnosis that showed most single-run drops were noise (D56)
- The skills roadmap: screening dozens of candidate decision kinds for cents before spending dollars
- *Writer's note: leaderboard rank only with Shane's OK (open decision 6).*

**Chapter 12: Failures, and the Failure That Won**
- The experiments that came back flat (distillation, mixed data, hard-example mining, the unfamiliar-inputs batch), with what each ruled out
- Why adding a few thousand examples of the same kind to ~370,000 barely moves a model, and the dead-ends list that stops you repeating them
- **E18 → E19:** rewording the options failed its own bar as a wording fix, but one run hinted at a side effect on never-seen tasks. Rather
  than claim it, a new pre-registered test with three runs: never-seen 0.662 → 0.689, calibration error 0.109 → 0.085. The release's
  biggest gain came from a failed experiment, tested properly
- What a failed experiment is worth when it is written down

**Chapter 13: The Human in the Loop: Building Kodiak With AI Partners**
*(the book's most personal chapter, and the ground the Conclusion stands on)*
- The working arrangement: Shane as project owner (scope, naming, licensing, budget, approvals, human review of the synthetic data);
  Claude as pair engineer (design, implementation, experiments, documentation) in daily review loops; open models as data writers and
  checkers. Who did what, drawn from the credits and the decision log rather than generalised
- **Case study 1, the rewording on X:** observation → hypothesis (a word-matching shortcut) → the Enchanted Returns Desk simulator (5,139
  cases for about $2) → three runs per arm → progress with a price (probe 3/2/4 → 6/4/5 of 8, a little general accuracy lost, a new
  shortcut learned); and how the same theme led to E18-E20 and the v0.3 goal
- **Case study 2, the reviewer on Hugging Face:** a stranger reproduced our numbers from the public repo and showed the calibration
  headline was partly an offset anyone could fix, and that the real lead is ranking. We reproduced it, added ranking as a guard on every
  experiment, and changed the model card the same day. Publishing everything is what made that possible
- What the human mind contributed that the AI partners did not, and what the AI contributed that one person could not
- A reusable loop for the reader: observe, name the failure, hypothesise, design one targeted fix, set the bar first, replicate, read the cost

**Chapter 14: Knowing the Limits**
- Where chatbots still win: questions that need world knowledge
- Weak spots: wording sensitivity, long-answer hallucination (RAGTruth still near zero), some tool-calling benchmarks, ratings
- Bias in training data, and using a decision model responsibly when the decision is about a person
- A checklist for when not to automate

### Conclusion: The Road Ahead
- The thesis restated: fast, honest decisions are a different product from conversation, and the more valuable one for most software
- Where decision models are going: more kinds of decision (the skills roadmap), longer documents, steps inside agents, learning from reviewed feedback
- Kodiak's roadmap as horizons, each shipping only when it beats the last on published tests; the companion site tracks shipped features
- **The near future of technical work.** People working alongside AI research and programming partners, as this book was made
- **Why breadth matters more, not less.** Steering an AI toward a problem requires understanding the problem
- **A project for humanity.** Learning to direct these systems well belongs to everyone willing to think hard
- Closing: the bear that knows when to ask, and the people who taught it
- *Writer's note: argue this as the author's conviction from building Kodiak, grounded in Chapter 13. No job-loss statistics, no dated
  forecasts, no claims about what any particular field "will" require stated as fact.*

### Appendices
- **Appendix A: Plain-English Glossary**
- **Appendix B: Question-Writing Cheat Sheet**: option design, wording traps, threshold selection
- **Appendix C: API Reference for Python and JavaScript** (pinned to Kodiak-v0.2-1B)
- **Appendix D: The Full Scoreboards**: every published eval, with version, seeds and caveats

Plus back matter: Acknowledgements, A Request for Review, About the Author.

---

## Source material: writers must not invent numbers

Every figure, benchmark result, cost, parameter count and anecdote comes from the Kodiak repo at `~/development/kodiak` (public at
github.com/grizzlypeaksoftware/kodiak). Writing agents receive the paths relevant to their chapters (an explicit exception to the three-file
context rule, scoped per chapter) and **cite nothing that is not in them**:

| Source | Use |
|---|---|
| Kodiak-v0.2-1B model card (Hugging Face; `dist/kodiak-v0.2-1b/README.md`) | release numbers, ranking, limits, intended use (Ch. 1-3, 14, App. D). **Supersedes `docs/MODEL_CARD.md`, which describes the previews** |
| `reports/v02-release-vs-llm-8b.md` | v0.2 vs Qwen3-8B, including ranking (Ch. 2, 3, App. D) |
| `reports/e19-rewording-3seeds.md`, `reports/e18-xl-wording.md` | the failure that won (Ch. 12) |
| `reports/e17-xl-skills-3seeds.md`, `reports/d55-di-diagnosis.md`, `reports/v02-di-sample.md` | new decision kinds and the report card (Ch. 11) |
| `docs/SKILLS_ROADMAP.md` | screening candidate decision kinds (Ch. 11, Conclusion) |
| `docs/STORY.md` | the build narrative and the People and Credits section (Introduction, Ch. 10-13) |
| `docs/DECISIONS.md` | the decision log: failures, the three-runs rule, D36-D60 (Ch. 10-13) |
| `docs/EXPERIMENTS.md` | the experiment log and dead-ends list (Ch. 12) |
| `docs/GENERATOR_V2.md` §16-17, `reports/v02-simret.md` | the label-overlap probe and the Returns Desk (Ch. 13) |
| `docs/STRATEGY.md` | positioning, the CMU paper, where Kodiak wins and loses (Introduction, Ch. 6) |
| `docs/ARCHITECTURE.md` | encoder design, answer shapes (Ch. 1-3) |
| `LEARNING.md` | plain-language explanations written while learning (analogies, all chapters) |
| `README.md`, `server/`, `examples/`, the fine-tuning kit | quick start, API, self-hosting, fine-tuning (Ch. 4-9, App. C) |
| `docs/progress.json` → finance | cloud spend (~$80 estimated from logged tokens), GPU-hours (Ch. 10) |

Pre-release figures (`reports/v02-*.md` from September) may be used only as history ("the September preview scored…"), never as current results.

---

## Format and Approach

- **Voice:** the catalog's: direct, anti-hype, respects the reader. Analogy first, then the mechanism, then the code.
- **Code:** short and runnable, written to a **72-character line limit** (the print measure fits 66; longer lines soft-wrap). Every listing
  lives in the repo and is tested against Kodiak-v0.2-1B.
- **Figures: ~20.** Keep the ones that carry an argument: the answer shapes, a reliability diagram, a risk-coverage (ranking) curve, the
  coverage/accuracy threshold curve, the cascade flow and its trade-off chart, the self-hosting architecture, the training pipeline, the
  report-card bar chart, the E18 → E19 timeline, the failure timeline. Built in `scripts/diagrams/kodiak-field-guide.js`, drawn for print
  (canvas ≤ ~560 units, vertical layouts, two or three words per box, argument in the caption), greyscale-safe, and gated on
  `diagrams_reviewed`. Charts are generated from the report JSON, never retyped. **No mermaid.**
- **Illustrated EPUB** is the ebook upload.
- **Companion site** (cortexagent.com) tracks the live scoreboard and roadmap and flags superseded chapters. The book never promises a date.

---

## Differentiation

- The only accessible book on **small, calibrated decision models**: ML books assume math, LLM books assume the chatbot is the answer
- Treats **abstention, calibration and ranking** as the central features, not advanced topics
- A **live, released open model behind every page**: free demo, Hugging Face weights, public repo, public decision log
- Tells the failures, the unmet goals and the outside correction, which is rare in product-adjacent books and is the point

---

## Comparable Titles

For also-bought and category planning only. **Never name these in the KDP description.**

- *Thinking, Fast and Slow* (Daniel Kahneman, 2011): the System 1 / System 2 idea this book applies to software
- *AI Engineering* (Chip Huyen, O'Reilly, 2025): products on foundation models; assumes the LLM is the core
- *Hands-On Large Language Models* (Jay Alammar and Maarten Grootendorst, O'Reilly, 2024): includes classification with encoders; aimed at readers ready for ML concepts
- *Designing Machine Learning Systems* (Chip Huyen, O'Reilly, 2022): production ML for engineers with an ML background

---

## Author Fit

Shane Larson is a software engineer, the founder of Grizzly Peak Software and Cortex Agent LLC, and the author of the Peak Grizzly catalog,
including *Fine-Tuning LLMs*, *Loop Engineering* and *Prompt Engineering for Real Work*. He built Kodiak in public in Alaska, starting with
no machine-learning background, on one desktop machine and about $80 of cloud spend, and released Kodiak-v0.2-1B in October 2026. A
technical title, so the bio may cite the engineering background.

---

## Marketing Angles

- **Every chapter becomes content:** a post on cortexagent.com (the v0.2 announcement is the first), an article on grizzlypeaksoftware.com,
  a thread on X (@PeakGrizzly), a Hugging Face post, and a runnable demo
- **Try every example:** the free demo (now GPU-backed) and the Hugging Face weights, with the numbers checkable in the public repo
- **Shareable hooks:** the "Returns Desk: you vs. the Bear" game; a "break the bear" challenge that turns readers' failure reports into
  training data; the outside-reviewer story as proof that publishing everything works
- **Audio:** episodes on the build story for podcast audiences
- **Reader to customer:** the self-hosted model is free; the hosted API and fine-tuning services are the business
- **Launch alignment:** v0.2 launched on 2026-10-02 without the book. Align the book with the **v0.3 announcement** (the wording fix and
  new decision kinds) so each drives the other, while still pinning the text to v0.2 (decision 3) and pointing to the site for what's newer

---

## Risk Notes

- **KDP content risk: expected LOW.** No geopolitics, no living public figures characterised, no quoted translations.
- **Claim risk is the real one.** Benchmark comparisons name other models (Qwen3-8B): describe them factually with the eval version, never
  disparagingly, and include the recalibrated comparison, not just the raw one. Run the `fact-checker` against the repo reports, not the web,
  for Kodiak's numbers, and against the source for the CMU paper. Decision Index standings need Shane's OK.
- **Staleness:** handled by pinning to v0.2 (decision 3), not by updating the interior.
- **Two re-runs needed before print:** the cascade (Ch. 7) and the injection guardrail figures (Ch. 6) were measured on the September
  previews; re-run them on v0.2 so no current-tense figure comes from a superseded model.

---

## Priority Assessment

**Strategic, not catalog-volume.** The book and the model sell each other, and it is the catalog's first title backed by a product the author
ships. **Priority 2, now unblocked:** the v0.2 release eval exists. Remaining gates: the title gate, the imprint and channel decisions, the
naming permissions, the Decision Index decision, and the two v0.2 re-runs.
