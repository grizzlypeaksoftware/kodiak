# Kodiak

**Kodiak by Cortex Agent LLC** is an open-source, encoder-only "System One" decision model.
You give it a *state* (text, a list of texts, or JSON) and a set of *typed questions*.
It answers every question in **one forward pass**. Each answer comes with a calibrated
probability, and it's always inside the answer space you defined.

- **No token generation.** There's no text output and nothing to parse. A choice answer is always one of your labels,
  and a score is always inside your range.
- **Zero-shot labels.** Choice labels are defined per request and matched by meaning, so new label sets work without retraining.
- **First-class abstention.** Every question can come back as "not answerable from this state"
  with its own probability.
- **Calibrated.** Trained with proper scoring rules and evaluated on ECE and Brier score, not only accuracy.

> **Status: pre-alpha (Phase 1).** There are no trained models yet. Every result in this repo is measured
> on this project's own eval set, and the reports say how it was measured.

## The contract

Request:

```json
{
  "state": ["Customer: My card was charged twice for order #4411 and I need it fixed before Friday."],
  "questions": [
    { "id": "intent", "type": "choice", "text": "What does the customer want?",
      "labels": ["refund or billing fix", "order status", "cancel order", "technical support"] },
    { "id": "urgency", "type": "score", "text": "How urgent is this?", "min": 0, "max": 1,
      "min_label": "no time pressure", "max_label": "needs resolution immediately" },
    { "id": "card_brand", "type": "choice", "text": "Which card brand?",
      "labels": ["Visa", "Mastercard", "Amex", "Discover"] }
  ]
}
```

Response (illustrative; the numbers are made up, not model output):

```json
{
  "answers": {
    "intent":     { "type": "choice", "answer": "refund or billing fix", "confidence": 0.94, "p_null": 0.02, "probs": {"...": 0} },
    "urgency":    { "type": "score", "answer": 0.78, "interval": [0.57, 0.93], "p_null": 0.03 },
    "card_brand": { "type": "choice", "answer": null, "abstain_reason": "unanswerable", "p_null": 0.91 }
  }
}
```

Full examples: [schema/examples/](schema/examples/). JSON Schemas: [schema/](schema/).
Source of truth: [src/kodiak_s1/schema.py](src/kodiak_s1/schema.py).

## Two tracks

| Track | Backbone | Purpose |
|---|---|---|
| **A: pure** | Small encoder pretrained from scratch (MLM) on permissive data | Measure what we can build from nothing on one machine |
| **B: pragmatic** | Open pretrained encoder weights (ModernBERT, Apache-2.0) | The practical model |

Both tracks share the same decision heads, training data, and evaluation, and both are compared honestly against
a local LLM (Qwen via Ollama) using constrained JSON output.

Checkpoints are named `kodiak-{track}-{size}-v{n}`, for example `kodiak-b-small-v0.1`.

## Docs

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): the model design and the reasoning behind it
- [LEARNING.md](LEARNING.md): the project journal (concepts, decisions, results)
- [data/LICENSES.md](data/LICENSES.md): the source and license of every dataset

## Development

```bash
uv sync                                   # create .venv and install
uv run pytest                             # run tests
uv run python -m kodiak_s1.schema --export schema/   # regenerate JSON Schemas
```

Developed on an NVIDIA DGX Spark (GB10, aarch64, 128 GB unified memory).

## License

Apache-2.0. Copyright 2026 Cortex Agent LLC. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
Dataset and model-weight licenses are tracked in [data/LICENSES.md](data/LICENSES.md).
The Python package is published as `kodiak-s1` (`import kodiak_s1`) because `kodiak` is already taken on PyPI.
