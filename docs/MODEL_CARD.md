# Model card draft: Kodiak v0.1 (preview)

> **Draft for the first public release.** Numbers marked ⟨TBD⟩ are filled in from the final model's reports. The
> published card is this file plus the Hugging Face front matter; keep both in sync.

## Kodiak: fast, calibrated decisions in one forward pass

Kodiak (by Cortex Agent LLC) is an open-weights, encoder-only **decision model**. You give it a *state* (text, a list of texts, or
JSON) and *typed questions*; it answers all of them in one forward pass:

- **Choice** questions: pick one of *your* labels (any label set, defined per request). The answer can't be outside the list.
- **Score** questions: a value in *your* range, with a mean, a standard deviation and a 90% interval.
- **Abstention**: every question can come back as "not answerable from this state", with its own calibrated probability.

It is built to be the fast "System 1" in front of an LLM or a human: answer most decisions in milliseconds, and escalate the ones it
isn't sure about. Calibration is what makes that safe: when Kodiak says 90%, it is right about 90% of the time on our eval set.

```python
# pip install "kodiak-s1[infer] @ git+https://github.com/grizzlypeaksoftware/kodiak"
from kodiak_s1.hub import Kodiak

kodiak = Kodiak.from_pretrained("cortex-agent-llc/⟨repo⟩")        # GPU if available, else CPU
kodiak.decide(
    {"order_id": "A-1042", "status": "delivered", "message": "The box arrived crushed and the lamp is broken."},
    [{"type": "choice", "id": "intent", "text": "What does the customer want?",
      "labels": ["refund or replacement", "delivery status", "cancel order", "product question"]},
     {"type": "score", "id": "urgency", "text": "How urgent is this?", "min": 0, "max": 10,
      "min_label": "can wait", "max_label": "act immediately"},
     {"type": "choice", "id": "carrier", "text": "Which carrier delivered it?", "labels": ["UPS", "FedEx", "USPS"]}],
)
# -> intent: an answer with probabilities; urgency: mean, std and interval; carrier: most likely abstains (not in the state)
```

## Model details

| | |
|---|---|
| Developer | Cortex Agent LLC (Shane Larson), with Claude (Anthropic) as pair engineer |
| Architecture | ModernBERT-base encoder (Apache-2.0) with a structured attention mask (state / question / label), per-question and per-label position restarts, and three heads: label matching, null (sigmoid), score (Beta distribution) |
| Parameters | 152M |
| Context | States up to 512 tokens in this version (longer inputs are truncated) |
| Language | English |
| License | Apache-2.0 (weights and code) |
| Training | Joint log-likelihood (a proper scoring rule) on 20 permissively licensed public datasets plus synthetic data; then temperature scaling on validation data |
| Design docs | [ARCHITECTURE.md](ARCHITECTURE.md), [DECISIONS.md](DECISIONS.md), [STRATEGY.md](STRATEGY.md) |

## Intended use

- Routing and triage: intent, category, urgency, which team or tool next.
- Guardrails in front of LLMs: prompt injection, jailbreak and toxicity checks.
- Checks over records and documents: "is this field present?", "does this meet the rule?", with abstention when the answer isn't there.
- A cheap first pass in an LLM cascade: accept confident answers, escalate the rest.

**Out of scope:** open-ended generation; multi-step reasoning or math; facts that aren't in the state; high-stakes decisions about
people (hiring, credit, medical, legal) without human review.

## Training data

- **Public datasets:** 20 sources, all permissively licensed; the full list with licenses is in [data/LICENSES.md](../data/LICENSES.md).
  Four sources are held out of training entirely and used only to test generalization.
- **Synthetic data:** written by open-weight teacher models (gpt-oss-120b, Apache-2.0) and kept only where an independent checker
  (DeepSeek V3.2, MIT) agrees ⟨and critics pass⟩. Generator v2 grounds ~45% of examples in real web passages (FineWeb-Edu, ODC-By);
  the released dataset ships FineWeb ids plus a rebuild script instead of the excerpts. No closed-model outputs are used anywhere.
- Human review of synthetic labels: v1 ≈ 95%, v2.0 92.7% label precision (55 examples, 165 questions).

## Evaluation

Frozen eval set v0.1 (2,902 examples, 4,189 questions; never trained or tuned on). Held-out = tasks never seen in training.

| | Kodiak ⟨size⟩ | Best open zero-shot classifier | Qwen 27B (LLM) |
|---|---|---|---|
| Overall accuracy (choice) | ⟨TBD⟩ | ⟨TBD⟩ | – |
| Held-out forced accuracy | ⟨TBD⟩ | ⟨TBD⟩ | ≈ 0.86 (sample) |
| Calibration error (ECE) | ⟨TBD⟩ | ⟨TBD⟩ | worse |
| Latency, GPU / CPU | ⟨TBD⟩ | ⟨TBD⟩ | ≈ 3.4 s |

Release criteria ([STRATEGY.md §6](STRATEGY.md)) and whether each is met: ⟨TBD⟩.

## Limitations and risks

- **Generalization:** on never-seen *classification* tasks it is roughly on par with open zero-shot classifiers and well behind large LLMs.
- **Judgment scores** can be badly off on some inputs (e.g. urgency of an angry billing complaint in the preview). Use the interval and
  `p_null`, and validate on your own data.
- **Bias:** one held-out task (occupation from biographies) comes from a dataset with known gender bias; we report accuracy by gender ⟨TBD⟩.
  Don't use Kodiak to make decisions about people without review.
- **Synthetic labels** are imperfect (about 5–7% label noise under human review).
- **English only; 512-token states** in this version.

## Citation

```
@software{kodiak2026,
  title  = {Kodiak: a calibrated, encoder-only decision model},
  author = {Larson, Shane and {Cortex Agent LLC}},
  year   = {2026},
  url    = {https://github.com/grizzlypeaksoftware/kodiak}
}
```
