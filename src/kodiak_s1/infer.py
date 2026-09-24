"""Inference: requests in, answers out (docs/ARCHITECTURE.md §5.5).

    model = load("runs/b-small-s1-v0")            # best.pt, or a checkpoint file
    responses = answer(model, [request_dict, ...])

The network returns logits; everything that turns them into an answer lives here: grouped softmax over
each question's labels, the null probability, the decision rule, and Beta summaries for scores.
The same rules are re-implemented in JavaScript for the Node server (Phase 6) and tested against this.
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import torch
from scipy.stats import beta as beta_dist

from kodiak_s1.model import KodiakModel, ModelConfig
from kodiak_s1.packing import CHOICE, Limits, collate, pack_example
from kodiak_s1.schema import Options, Request


def load(path: str | Path, device: str = "cuda") -> KodiakModel:
    """Load a run directory (uses best.pt) or a checkpoint / state-dict file."""
    path = Path(path)
    run = path if path.is_dir() else path.parent.parent if path.parent.name == "checkpoints" else path.parent
    model = KodiakModel(ModelConfig.load(run / "model_config.json"))
    state = torch.load(path / "best.pt" if path.is_dir() else path, map_location="cpu", weights_only=False)
    model.load_state_dict(state["model"] if "model" in state and "opt" in state else state)
    return model.to(device).eval()


@torch.no_grad()
def raw_outputs(model: KodiakModel, requests: list[dict], max_len: int = 4096, rows_per_batch: int = 8,
                limits: Limits = Limits()) -> list[list[dict]]:
    """Per request, per question: probabilities before the decision rule."""
    device = next(model.parameters()).device
    packed = [pack_example(r, limits, with_targets=False) for r in requests]
    out: list[list[dict]] = [[] for _ in requests]
    # Batch by rows: collate packs greedily, so feed a slice of examples that fits `rows_per_batch` rows.
    i = 0
    while i < len(packed):
        j, tokens = i, 0
        while j < len(packed) and tokens + len(packed[j]) <= rows_per_batch * max_len:
            tokens += len(packed[j])
            j += 1
        j = max(j, i + 1)
        b = collate(packed[i:j], max_len).to(device)
        with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
            o = model(b, impl="sdpa")
        z_null = o["z_null"].float().cpu()
        p_null = torch.sigmoid(z_null)
        z = o["z_choice"].float().cpu()
        l_q = b.l_q.cpu()
        mu, kappa = o["mu"].float().cpu(), o["kappa"].float().cpu()
        for qidx, k in enumerate(b.q_example):
            ex = k + i
            p = packed[ex]
            n = len(out[ex])  # question index within the request
            allow = p.q_allow_null[n]
            rec = {"qid": p.qids[n], "type": "choice" if p.q_type[n] == CHOICE else "score",
                   "p_null": float(p_null[qidx]) if allow else 0.0, "z_null": float(z_null[qidx]), "allow_null": allow}
            if p.q_type[n] == CHOICE:
                zq = z[l_q == qidx]
                cond = torch.softmax(zq, 0)
                rec["labels"] = p.label_ids[n]
                rec["cond_probs"] = cond.tolist()
                rec["z"] = zq.tolist()
            else:
                rec["mu"], rec["kappa"] = float(mu[qidx]), float(kappa[qidx])
            out[ex].append(rec)
        i = j
    return out


def decide(raw: dict, q: dict, opts: Options) -> dict:
    """Apply the decision rule to one question's raw output -> a schema Answer dict."""
    p_null = raw["p_null"]
    if raw["type"] == "choice":
        probs = {lab: (1 - p_null) * c for lab, c in zip(raw["labels"], raw["cond_probs"])}
        best = max(probs, key=probs.get)
        ans = {"type": "choice", "probs": {k: round(v, 6) for k, v in probs.items()}, "p_null": round(p_null, 6)}
        if q.get("allow_null", True) and p_null >= opts.null_threshold:
            return {**ans, "answer": None, "confidence": round(p_null, 6), "abstain_reason": "unanswerable"}
        if q.get("allow_null", True) and probs[best] < opts.min_confidence:
            return {**ans, "answer": None, "confidence": round(probs[best], 6), "abstain_reason": "low_confidence"}
        return {**ans, "answer": best, "confidence": round(probs[best], 6), "abstain_reason": None}

    lo, hi = q.get("min", 0.0), q.get("max", 1.0)
    a, b = raw["mu"] * raw["kappa"], (1 - raw["mu"]) * raw["kappa"]
    mean_u = raw["mu"]
    std_u = math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))
    tail = (1 - opts.interval) / 2
    ilo, ihi = float(beta_dist.ppf(tail, a, b)), float(beta_dist.ppf(1 - tail, a, b))
    value = lo + mean_u * (hi - lo)
    if q.get("step"):
        value = lo + round((value - lo) / q["step"]) * q["step"]
    ans = {"type": "score", "mean": lo + mean_u * (hi - lo), "std": std_u * (hi - lo),
           "interval": (lo + ilo * (hi - lo), lo + ihi * (hi - lo)), "p_null": round(p_null, 6)}
    if q.get("allow_null", True) and p_null >= opts.null_threshold:
        return {**ans, "answer": None, "abstain_reason": "unanswerable"}
    return {**ans, "answer": value, "abstain_reason": None}


def answer(model: KodiakModel, requests: list[dict], model_name: str = "kodiak") -> list[dict]:
    """Full Request dicts in, Response dicts out (see kodiak_s1.schema)."""
    # Validate and normalize first (e.g. expands the "labels": ["a", "b"] shorthand into {id, text} objects).
    requests = [Request.model_validate(r).model_dump() for r in requests]
    t0 = time.perf_counter()
    raws = raw_outputs(model, requests)
    ms = (time.perf_counter() - t0) * 1000 / max(1, len(requests))
    responses = []
    for req, raw in zip(requests, raws):
        opts = Options(**req.get("options", {}))
        qs = {q["id"]: q for q in req["questions"]}
        responses.append({"model": model_name, "latency_ms": round(ms, 2),
                          "answers": {r["qid"]: decide(r, qs[r["qid"]], opts) for r in raw}})
    return responses
