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

> **Status: pre-alpha (Phase 4: first training runs in progress).** No models are released yet. Every result in this repo is measured
> on this project's own eval set, and the reports say how it was measured.

## Why

Much of what software asks LLMs to do isn't generation; it's *decisions*. Which intent? How urgent? Which tool?
Can this even be answered? Kodiak answers those directly with a small encoder instead of generating and parsing text.
It's inspired by TypeSafe AI's "System One" model Jev (announced September 2026), built independently in the open, and
it doubles as a learning project whose reasoning is documented at every step. The full story is in [docs/STORY.md](docs/STORY.md).

**The goal: a frontier-class open-weights decision model.** Not a smaller chatbot, but the best open model *in its class*:
near-LLM accuracy on decisions at 100×+ the speed, better-calibrated than the alternatives, and honest about what it can't tell.
The definition, the measurable release bar and the plan are in [docs/STRATEGY.md](docs/STRATEGY.md).

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

## Backbone

Kodiak v0.1 builds on **ModernBERT** (Apache-2.0), an open *encoder*. It reads text but can't generate it. Kodiak adds
the decision layer: the packed request format, the structured attention mask, the choice/null/score heads, the training
objective, and the data. Kodiak is compared honestly against a local LLM (Qwen via Ollama) using constrained JSON output.

The original plan also had a "Track A" encoder pretrained from scratch; it's deferred (see
[docs/DECISIONS.md](docs/DECISIONS.md), D19). A custom encoder is a candidate for a later version.

Checkpoints are named `kodiak-{track}-{size}-v{n}`, for example `kodiak-b-small-v0.1`.

## Docs

| Doc | Read it for |
|---|---|
| [docs/STRATEGY.md](docs/STRATEGY.md) | The goal (frontier-class open decision model), the competition, the release bar, and the levers |
| [docs/STORY.md](docs/STORY.md) | Why Kodiak exists and how it was built, including the dead ends |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | The model design and the reasoning behind it |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Every significant decision, the alternatives, and why |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | How to build data, run the teacher, and train on a DGX Spark |
| [docs/GENERATOR_V2.md](docs/GENERATOR_V2.md) | Generator v2: design, implementation plan and build log |
| [LEARNING.md](LEARNING.md) | The technical journal: concepts, experiments, and results, phase by phase |
| [data/README.md](data/README.md) | How the training and eval data are built, and what the build guarantees |
| [data/LICENSES.md](data/LICENSES.md) | The source and license of every dataset, and what we excluded |

## Development

```bash
uv sync --extra data --extra train        # create .venv and install (PyTorch CUDA 13 wheels)
uv run pytest                             # run tests (KODIAK_SLOW=1 adds the ModernBERT parity test)
uv run python -m kodiak_s1.status --serve # progress dashboard at http://localhost:8787
uv run python -m kodiak_s1.train --run runs/overfit-tiny --preset tiny --overfit 32 --steps 400 --lr 1e-3 --head-lr 1e-3
uv run python -m kodiak_s1.schema --export schema/   # regenerate JSON Schemas
```

Developed on an NVIDIA DGX Spark (GB10, aarch64, 128 GB unified memory).

## License

Apache-2.0. Copyright 2026 Cortex Agent LLC. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
Dataset and model-weight licenses are tracked in [data/LICENSES.md](data/LICENSES.md).
The Python package is published as `kodiak-s1` (`import kodiak_s1`) because `kodiak` is already taken on PyPI.
