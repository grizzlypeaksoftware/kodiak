"""Metrics over per-question prediction records (the same format for Kodiak and LLM baselines).

A record describes one question:
    source, tags, type ("choice" | "score"), allow_null,
    gold:      {"label": id} | {"value": x} | {"null": true}
    probs:     unconditional outcome probabilities over label ids (choice), excluding null
    p_null:    probability of "unanswerable"
    decision:  label id / numeric value, or None when abstaining
    confidence: probability of the decided outcome (choice)
    unit_gold, unit_pred, mu, kappa, interval_unit: score fields, on the [0, 1] scale
    latency_ms: per-example latency (optional)

Choice outcomes include NULL as a class, so accuracy means "made the right call, including when to abstain".
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
from scipy.special import betaln

from kodiak_s1.packing import squeeze_unit

NULL = "__NULL__"


def gold_outcome(r: dict):
    g = r["gold"]
    return NULL if g.get("null") else g.get("label", g.get("value"))


def decided_outcome(r: dict):
    return NULL if r["decision"] is None else r["decision"]


def outcome_dist(r: dict) -> dict:
    d = dict(r["probs"])
    if r.get("allow_null", True):
        d[NULL] = r["p_null"]
    return d


def ece(conf: np.ndarray, correct: np.ndarray, bins: int = 15) -> float:
    """Expected calibration error with equal-mass bins: the average gap between confidence and accuracy."""
    if len(conf) == 0:
        return float("nan")
    order = np.argsort(conf)
    total = 0.0
    for chunk in np.array_split(order, min(bins, len(conf))):
        if len(chunk):
            total += len(chunk) * abs(conf[chunk].mean() - correct[chunk].mean())
    return total / len(conf)


def aurc(conf: np.ndarray, correct: np.ndarray) -> float:
    """Area under the risk-coverage curve: answer the most confident first; lower is better."""
    if len(conf) == 0:
        return float("nan")
    order = np.argsort(-conf)
    errors = 1 - correct[order]
    return float(np.mean(np.cumsum(errors) / np.arange(1, len(errors) + 1)))


def macro_f1(golds: list, preds: list) -> float:
    classes = set(golds) | set(preds)
    f1s = []
    for c in classes:
        tp = sum(g == c and p == c for g, p in zip(golds, preds))
        fp = sum(g != c and p == c for g, p in zip(golds, preds))
        fn = sum(g == c and p != c for g, p in zip(golds, preds))
        if tp + fp + fn:
            f1s.append(2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f1s)) if f1s else float("nan")


def summarize(records: list[dict]) -> dict:
    """All metrics for one slice of records."""
    out: dict = {"n_questions": len(records)}
    ch = [r for r in records if r["type"] == "choice"]
    if ch:
        golds = [gold_outcome(r) for r in ch]
        preds = [decided_outcome(r) for r in ch]
        correct = np.array([g == p for g, p in zip(golds, preds)], dtype=float)
        conf = np.array([r["confidence"] for r in ch], dtype=float)
        briers, nlls = [], []
        for r, g in zip(ch, golds):
            d = outcome_dist(r)
            briers.append(sum((p - (1.0 if k == g else 0.0)) ** 2 for k, p in d.items()) + (0.0 if g in d else 1.0))
            nlls.append(-math.log(max(d.get(g, 0.0), 1e-12)))
        answerable = [i for i, g in enumerate(golds) if g != NULL]
        # Forced: on answerable questions, pick the most likely label even if the system would abstain.
        # Measures pure ranking skill, the fair comparison with baselines that can't abstain.
        f_correct, f_conf = [], []
        for i in answerable:
            probs = ch[i]["probs"]
            if probs:
                best = max(probs, key=probs.get)
                f_correct.append(float(best == golds[i]))
                f_conf.append(probs[best] / (sum(probs.values()) or 1.0))
        if f_correct:
            out.update({"forced_accuracy": float(np.mean(f_correct)),
                        "forced_ece": ece(np.array(f_conf), np.array(f_correct))})
        out.update({
            "choice_n": len(ch),
            "accuracy": float(correct.mean()),
            "answerable_accuracy": float(correct[answerable].mean()) if answerable else float("nan"),
            "macro_f1": macro_f1(golds, preds),
            "ece": ece(conf, correct),
            "brier": float(np.mean(briers)),
            "nll": float(np.mean(nlls)),
            "aurc": aurc(conf, correct),
            "mean_confidence": float(conf.mean()),
        })
    # Abstention across both question types.
    nullable = [r for r in records if r.get("allow_null", True)]
    if nullable:
        gold_null = np.array([gold_outcome(r) == NULL for r in nullable])
        pred_null = np.array([r["decision"] is None for r in nullable])
        tp = float((gold_null & pred_null).sum())
        out.update({
            "null_rate_gold": float(gold_null.mean()),
            "null_rate_pred": float(pred_null.mean()),
            "abstain_precision": tp / pred_null.sum() if pred_null.sum() else float("nan"),
            "abstain_recall": tp / gold_null.sum() if gold_null.sum() else float("nan"),
        })
    sc = [r for r in records if r["type"] == "score" and gold_outcome(r) != NULL]
    if sc:
        # MAE over questions that got a value; `score_answered` shows how many did, so abstaining
        # on hard items can't quietly improve MAE. (Kodiak always has a posterior mean; LLMs may not.)
        given = [r for r in sc if r.get("unit_pred") is not None]
        out.update({"score_n": len(sc), "score_answered": len(given) / len(sc)})
        if given:
            y = np.array([r["unit_gold"] for r in given])
            yhat = np.array([r["unit_pred"] for r in given])
            out["score_mae"] = float(np.abs(y - yhat).mean())
        with_dist = [r for r in sc if r.get("mu") is not None]
        if with_dist:
            yy = np.clip([r["unit_gold"] for r in with_dist], 0.005, 0.995)
            a = np.array([r["mu"] * r["kappa"] for r in with_dist])
            b = np.array([(1 - r["mu"]) * r["kappa"] for r in with_dist])
            logp = (a - 1) * np.log(yy) + (b - 1) * np.log1p(-yy) - betaln(a, b)
            # Gold values are squeezed off exactly 0/1 the same way as in training (packing.squeeze_unit):
            # a Beta interval can never contain an endpoint, and many gold scores sit exactly at 0 or 1.
            cover = [r["interval_unit"][0] <= squeeze_unit(r["unit_gold"]) <= r["interval_unit"][1] for r in with_dist]
            out.update({"score_nll": float(-logp.mean()), "score_interval_coverage": float(np.mean(cover))})
    lat = [r["latency_ms"] for r in records if r.get("latency_ms") is not None]
    if lat:
        out.update({"latency_p50_ms": float(np.percentile(lat, 50)), "latency_p95_ms": float(np.percentile(lat, 95))})
    return out


def slices(records: list[dict]) -> dict[str, list[dict]]:
    """overall, eval:* slices, per source, and per null type."""
    s: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        s["overall"].append(r)
        for t in r["tags"]:
            if t.startswith("eval:"):
                s[t].append(r)
            if t.startswith("null:") and gold_outcome(r) == NULL:
                s[t].append(r)
        s[f"source:{r['source']}"].append(r)
    return dict(s)


def report(records: list[dict]) -> dict:
    return {name: summarize(rs) for name, rs in slices(records).items()}
