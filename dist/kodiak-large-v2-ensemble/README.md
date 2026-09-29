---
license: apache-2.0
language: en
library_name: kodiak
inference: false
tags: [kodiak, decision-model, calibration, abstention, encoder, modernbert, ensemble, research-preview]
base_model: answerdotai/ModernBERT-large
---

# Kodiak large v2, accuracy mode (research preview)

**The recommended large Kodiak.** Three independently trained Kodiak large v2 models (ModernBERT-large, ~400M parameters each) answer every
question, and their calibrated answers are averaged. Each model is overconfident in different places, so averaging cancels much of it: more
accurate, better calibrated, and a more trustworthy "can't tell." The cost is about 3× the compute of one large model.

Kodiak is an open decision model by Cortex Agent LLC: a state (text, a list of texts, or JSON) and typed questions in; calibrated choice, score
or "can't tell" answers out, in one forward pass per model. Code, docs and the full build log: https://github.com/grizzlypeaksoftware/kodiak

```python
# pip install "kodiak-s1[infer] @ git+https://github.com/grizzlypeaksoftware/kodiak"
from kodiak_s1.hub import Kodiak

kodiak = Kodiak.from_pretrained("cortex-agent-llc/kodiak-large-v2-ensemble-preview")   # loads all three members
kodiak.decide(
    "Hi, I ordered the walnut desk two weeks ago. Tracking has said 'label created' for 10 days.",
    [{"type": "choice", "id": "intent", "text": "What does the customer want?",
      "labels": ["delivery status or expedite", "cancel and refund", "product question"]},
     {"type": "choice", "id": "carrier", "text": "Which carrier is shipping it?", "labels": ["UPS", "FedEx", "USPS"]}],
)
# -> intent: delivery status or expedite (0.81); carrier: can't tell (0.98)
```

## Accuracy mode vs. one large model (eval set v0.2, choice questions)

| | One large model (mean of 3 runs) | Accuracy mode |
|---|---|---|
| Never-seen tasks, forced accuracy | 0.609 | **0.623** |
| Familiar tasks | 0.855 | **0.869** |
| Calibration error (ECE), overall | 0.087 | **0.059** |
| Calibration error, never-seen tasks | 0.128 | **0.098** |
| When it says "can't tell", it's right | 0.84 | **0.94** |
| Latency, GPU / 8 CPU cores | ~16 ms / ~80 ms | ~48 ms / ~250 ms |

The default abstain threshold (0.75) was chosen on **validation** data only, by a rule fixed before scoring: the most accurate threshold whose
validation abstain precision is at least 90% (decision D45). Override per request with `null_threshold`.

## Files

`ensemble.json` lists the members (`m0`, `m1`, `m2`: the three large v2 training runs, seeds 0-2; `m1` is the same weights as
[kodiak-large-v2-preview](https://huggingface.co/cortex-agent-llc/kodiak-large-v2-preview)) and the threshold. Each member folder is a normal
Kodiak model folder with its own calibration.

## Known weaknesses

- **World knowledge.** On never-seen tasks that need outside knowledge (academic fields, legal holdings), an 8B LLM still leads by several points.
- **Ratings** ("how urgent is this?") are weak; use the interval and treat scores as rough.
- **Wording traps.** When a message repeats an option's exact words in a conditional ("if it can't arrive, cancel and refund me"), Kodiak can
  over-weight those words. Being fixed with simulator data in v0.2.
- Research preview: validate on your own data; don't use for decisions about people without human review.
