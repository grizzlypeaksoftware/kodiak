---
title: "Kodiak v0.2: an open 1B decision model you can download today"
summary: "Kodiak-v0.2-1B is out: an open 1B encoder that answers typed questions with calibrated confidence. On never-seen tasks it matches Qwen3-8B in our tests at about 40× the speed. Weights, demo and limits inside."
tags: [kodiak, release, decision models, calibration, encoders]
publish: false
---

Today we're releasing **Kodiak-v0.2-1B**, the first real release of Kodiak, our open decision model. The weights are on Hugging Face under
Apache-2.0, there's a live demo you can try in the browser, and the full build log, including the experiments that failed, is on GitHub.

- Model: [cortex-agent-llc/kodiak-v0.2-1b](https://huggingface.co/cortex-agent-llc/kodiak-v0.2-1b)
- Accuracy mode (three models averaged): [cortex-agent-llc/kodiak-v0.2-1b-accuracy](https://huggingface.co/cortex-agent-llc/kodiak-v0.2-1b-accuracy)
- Demo: [huggingface.co/spaces/comgen42/kodiak-demo](https://huggingface.co/spaces/comgen42/kodiak-demo)
- Code and build log: [github.com/grizzlypeaksoftware/kodiak](https://github.com/grizzlypeaksoftware/kodiak)

## What Kodiak is

Most of what software asks an LLM to do isn't writing. It's deciding: which intent this is, how urgent, which tool to call, whether it's
safe. Kodiak answers those questions directly. You send it a state (text, a list of texts or JSON) and typed questions. You get back a
calibrated answer for each one in a single forward pass. A choice is always one of your labels, and any question can come back as
"can't tell" with its own probability, so the model doesn't have to guess.

```python
from kodiak_s1.hub import Kodiak

kodiak = Kodiak.from_pretrained("cortex-agent-llc/kodiak-v0.2-1b")
kodiak.decide(
    "Hi, I ordered the walnut desk two weeks ago. Tracking has said 'label created' for 10 days.",
    [{"type": "choice", "id": "intent", "text": "What does the customer want?",
      "labels": ["delivery status or expedite", "cancel and refund", "product question"]},
     {"type": "choice", "id": "carrier", "text": "Which carrier is shipping it?", "labels": ["UPS", "FedEx", "USPS"]}],
)
# intent: delivery status or expedite (0.94); carrier: can't tell
```

The point is the pattern: automate the decisions Kodiak is sure about, and send the rest to a person or a larger LLM.

## How it compares

We measure on a frozen eval set (v0.2, choice questions). "Never-seen" means tasks and label sets the model was never trained on. The
Kodiak-v0.2-1B figures with ± are the mean of three training runs. We ran the Qwen3-8B baseline ourselves on the same eval set.

| | Kodiak-v0.2-1B | v0.2 accuracy mode | Qwen3-8B (LLM) |
|---|---|---|---|
| Never-seen tasks, accuracy | 0.689 ± 0.008 | 0.706 | 0.688 |
| Calibration error, never-seen (lower is better) | 0.085 | 0.062 | 0.293 |
| When it says "can't tell", it's right | 0.88 | 0.905 | – |
| Latency (GPU, one request) | ~38 ms | ~3× the single model | ~1,500 ms |

On decisions it has never been trained for, a 1B encoder matches an 8B LLM in our tests and is much better calibrated, at about 40× the
speed. Accuracy mode, which averages three independently trained models, does better still, at about three times the compute.

## What changed since the previews

Two experiments made it into v0.2. Each passed a bar we set before it ran, over three training runs.

**Four new kinds of decision.** These are: checking whether an answer is supported by its source (and which sentence isn't); picking an
assistant's next step from full API specs (call a tool, ask the user for missing information, or answer directly); verifying a claim
against a text; and judging product relevance for a search. We generated the training data with open-weight models (gpt-oss-120b
writing, DeepSeek-V3.2 checking), with every answer fixed by construction and confirmed by a blind checker. On a held-out skills test,
never trained on, the score went from 0.52 to 0.98. On public benchmarks the gains carry over, more modestly: for example, product
relevance (Amazon ESCI) went from 0.04 to 0.23 and claim verification (HoVer) from 0.12 to 0.23, chance-corrected so that 0 means random,
as three-run means.

**Reading options by meaning, not by wording.** We noticed that Kodiak's answer could change when the same options were worded
differently. So during training we sometimes show each question's options in a different wording, such as a short label, a sentence or a
paraphrase, with the answer unchanged. As a wording fix it fell short of the bar we set: consistency across wordings rose from 0.62 to
0.68, against a target of 0.72. But it had a side effect we then tested properly. Never-seen accuracy rose from 0.662 to 0.689 and
calibration error fell from 0.109 to 0.085, across three runs. That was our largest gain since moving to the 1B backbone, so it shipped.

## What didn't work

We keep an append-only experiment log, and most ideas die there. Before v0.2 we killed or parked:
- more of the same synthetic data at small scale;
- re-weighting and hard-example mining;
- a "can't tell" data batch aimed at calibration;
- distilling an ensemble into a small model;
- int8 quantization (it flipped too many answers).

The lesson that held up is that big gains came from changing the *kind* of data or the model, never from more of the same.

## Known limits

- **Option wording still matters.** Reworded options get the same answer about 68% of the time on never-seen tasks. Long, sentence-style
  options can tilt it toward one answer. Keep labels short and distinct, and test a few wordings on your own data. This is the main goal
  for v0.3.
- Detecting hallucination across a whole long response, and some API-call benchmarks, are still near chance.
- Ratings ("how urgent is this?") are rough. Prefer choice questions.
- Inputs are limited to about 8,000 tokens in total. Longer requests are refused rather than truncated.
- Validate it on your own data, and don't use it for decisions about people without human review.

## Try it

The [demo](https://huggingface.co/spaces/comgen42/kodiak-demo) lets you edit a state and questions and see every probability. It also has
a categorizer for pasting in a list, and a small game. To teach Kodiak your own labels, the repository has a fine-tuning kit: a CSV in,
and a before-and-after report on held-out rows out. If you'd rather not run it yourself, the hosted API is coming. Join the waitlist on
this site.
