"""Open zero-shot classifier baselines on the frozen eval set: "is Kodiak the best in its own class?"

Beating a 27B LLM on speed says little about whether Kodiak beats the *open models built for the same job*. Two families:

- NLI zero-shot (MoritzLaurer/*-zeroshot-v2.0): each (state, "question + candidate answer") pair is scored for
  entailment; the label with the highest entailment probability wins.
- GLiClass (knowledgator/gliclass-*): a label-matching encoder that scores all labels in one pass; the question is passed
  as its task prompt.

Fairness rules (also written into each output's _meta):
- Choice questions only. Neither family produces numeric scores, so compare with `report --choice-only`.
- Neither family can abstain by design. Each gets its *natural* rule: abstain when the best label's independent
  probability is below 0.5 (p_null = 1 - best). "Forced" metrics (argmax on answerable questions) compare pure ranking.
- Latency: one eval example (all its choice questions) per forward batch, CUDA-synchronized, same GPU as Kodiak.
These models are used for evaluation only, never for training data.

    uv run python -m kodiak_s1.eval.zeroshot --model MoritzLaurer/deberta-v3-large-zeroshot-v2.0 --out reports/preds/zs-nli-deberta-large.jsonl
    uv run python -m kodiak_s1.eval.zeroshot --model knowledgator/gliclass-large-v3.0 --out reports/preds/zs-gliclass-large.jsonl
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch

from kodiak_s1.eval.run import EVAL, read_jsonl
from kodiak_s1.schema import render_state


def hypothesis(q: dict, label_text: str) -> str:
    return f"{q['text'].strip()} The answer is: {label_text.strip()}."


class NLIScorer:
    """Binary entailment models (entailment vs. not_entailment)."""

    kind = "nli"

    def __init__(self, name: str, device: str = "cuda", max_length: int = 512):
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(name)
        dtype = torch.bfloat16 if "ModernBERT" in name else torch.float32  # DeBERTa-v3 is unstable in half precision
        self.model = AutoModelForSequenceClassification.from_pretrained(name, dtype=dtype).to(device).eval()
        labels = {v.lower(): k for k, v in self.model.config.id2label.items()}
        self.entail = labels["entailment"]
        self.device, self.max_length = device, max_length

    @torch.no_grad()
    def score(self, state: str, questions: list[dict]) -> list[list[float]]:
        pairs, spans = [], []
        for q in questions:
            spans.append((len(pairs), len(pairs) + len(q["labels"])))
            pairs += [(state, hypothesis(q, lab["text"])) for lab in q["labels"]]
        enc = self.tok([p for p, _ in pairs], [h for _, h in pairs], truncation="only_first", max_length=self.max_length,
                       padding=True, return_tensors="pt").to(self.device)
        probs = torch.softmax(self.model(**enc).logits.float(), dim=-1)[:, self.entail].tolist()
        return [probs[a:b] for a, b in spans]


class GLiClassScorer:
    """GLiClass: all labels scored in one pass, independent sigmoid per label; the question is the task prompt."""

    kind = "gliclass"

    def __init__(self, name: str, device: str = "cuda", max_length: int = 1024):
        from gliclass import GLiClassModel, ZeroShotClassificationPipeline
        from transformers import AutoTokenizer

        model = GLiClassModel.from_pretrained(name)
        tok = AutoTokenizer.from_pretrained(name, add_prefix_space=True)
        self.pipe = ZeroShotClassificationPipeline(model, tok, classification_type="multi-label", device=f"{device}:0",
                                                   max_classes=64, max_length=max_length, progress_bar=False)

    @torch.no_grad()
    def score(self, state: str, questions: list[dict]) -> list[list[float]]:
        texts = [state] * len(questions)
        labels = [[lab["text"] for lab in q["labels"]] for q in questions]
        out = self.pipe(texts, labels, threshold=0.0, batch_size=len(questions), prompt=[q["text"] for q in questions])
        res = []
        for q, preds in zip(questions, out):
            by_text = {p["label"]: p["score"] for p in preds}
            res.append([float(by_text.get(lab["text"], 0.0)) for lab in q["labels"]])
        return res


def records(i: int, ex: dict, questions: list[dict], scores: list[list[float]], ms: float) -> list[dict]:
    recs = []
    for q, s in zip(questions, scores):
        ids = [lab["id"] for lab in q["labels"]]
        best = max(range(len(ids)), key=lambda k: s[k])
        p_answer = s[best]  # independent probability that the best label is right
        p_null = 1.0 - p_answer if q.get("allow_null", True) else 0.0
        total = sum(s) or 1.0
        probs = {lid: (1 - p_null) * v / total for lid, v in zip(ids, s)}
        abstain = q.get("allow_null", True) and p_null >= 0.5
        recs.append({"ex": i, "qid": q["id"], "source": ex["meta"]["source"], "tags": ex["meta"]["tags"], "type": "choice",
                     "allow_null": q.get("allow_null", True), "gold": ex["answers"][q["id"]], "probs": probs,
                     "p_null": p_null, "decision": None if abstain else ids[best],
                     "confidence": p_null if abstain else probs[ids[best]], "latency_ms": ms})
    return recs


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--eval", default=EVAL)
    ap.add_argument("--name", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    scorer = GLiClassScorer(a.model) if "gliclass" in a.model.lower() else NLIScorer(a.model)
    exs = read_jsonl(a.eval)[: a.limit or None]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    n_q, t_all = 0, time.perf_counter()
    with open(a.out, "w") as f:
        f.write(json.dumps({"_meta": {"system": a.name or a.model.split("/")[-1], "model": a.model, "kind": scorer.kind,
                                      "eval": a.eval, "types": "choice only",
                                      "abstain_rule": "abstain if best label's independent probability < 0.5",
                                      "latency": "one example (all choice questions) per batch, CUDA-synchronized"}}) + "\n")
        for i, ex in enumerate(exs):
            qs = [q for q in ex["questions"] if q["type"] == "choice"]
            if not qs:
                continue
            state = render_state(ex["state"])
            torch.cuda.synchronize()
            t = time.perf_counter()
            scores = scorer.score(state, qs)
            torch.cuda.synchronize()
            ms = (time.perf_counter() - t) * 1000
            for r in records(i, ex, qs, scores, ms):
                f.write(json.dumps(r) + "\n")
            n_q += len(qs)
            if (i + 1) % 250 == 0:
                print(f"{i + 1}/{len(exs)} examples", flush=True)
    print(f"{n_q} choice questions -> {a.out} in {time.perf_counter() - t_all:.0f} s")


if __name__ == "__main__":
    main()
