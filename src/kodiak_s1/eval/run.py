"""Phase 5 evaluation harness.

    # 1. Fit calibration temperatures on validation data (never on the eval set)
    uv run python -m kodiak_s1.eval.run calibrate --model runs/b-small-s1-v0 --out runs/b-small-s1-v0/calibration.json
    # 2. Predict on the frozen eval set
    uv run python -m kodiak_s1.eval.run predict --model runs/b-small-s1-v0 --calibration runs/b-small-s1-v0/calibration.json \
        --out reports/preds/b-small-s1-v0.jsonl
    # 3. LLM baseline on the same eval set (Ollama, JSON-schema-constrained output)
    uv run python -m kodiak_s1.eval.run baseline --llm qwen3.8:27b --limit 300 --out reports/preds/qwen3.8-27b.jsonl
    # 4. Compare
    uv run python -m kodiak_s1.eval.run report reports/preds/*.jsonl --out reports/eval-report.md
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import random
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import torch
from scipy.optimize import minimize_scalar
from scipy.special import betaln
from scipy.stats import beta as beta_dist

from kodiak_s1.data.sources import SOURCES
from kodiak_s1.eval.metrics import report
from kodiak_s1.infer import load, raw_outputs
from kodiak_s1.schema import render_state

EVAL = "data/eval/kodiak-eval-v0.1.jsonl"


def read_jsonl(p: str | Path) -> list[dict]:
    opener = gzip.open if str(p).endswith(".gz") else open
    with opener(p, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def to_unit(q: dict, v: float) -> float:
    return (v - q.get("min", 0.0)) / (q.get("max", 1.0) - q.get("min", 0.0))


# ---------------------------------------------------------------------------
# Calibration (stage S3): three scalars fit by NLL on validation data
# ---------------------------------------------------------------------------


def apply_calibration(raw: dict, cal: dict | None) -> dict:
    if not cal:
        return raw
    r = dict(raw)
    if r["allow_null"]:
        r["p_null"] = 1 / (1 + math.exp(-r["z_null"] / cal["t_null"]))
    if r["type"] == "choice":
        z = np.array(r["z"]) / cal["t_choice"]
        e = np.exp(z - z.max())
        r["cond_probs"] = (e / e.sum()).tolist()
    else:
        r["kappa"] = r["kappa"] * cal["kappa_scale"]
    return r


def fit_calibration(pairs: list[tuple[dict, dict, dict]]) -> dict:
    """pairs of (raw, question, gold). Minimizes each head's NLL over its single temperature."""
    choice = [(r, g) for r, q, g in pairs if r["type"] == "choice" and "label" in g]
    nulls = [(r, g) for r, q, g in pairs if r["allow_null"]]
    scores = [(r, to_unit(q, g["value"])) for r, q, g in pairs if r["type"] == "score" and "value" in g]

    def choice_nll(t):
        tot = 0.0
        for r, g in choice:
            z = np.array(r["z"]) / t
            z = z - z.max()
            tot -= z[r["labels"].index(g["label"])] - math.log(np.exp(z).sum())
        return tot / max(1, len(choice))

    def null_nll(t):
        tot = 0.0
        for r, g in nulls:
            p = 1 / (1 + math.exp(-r["z_null"] / t))
            tot -= math.log(max(p if g.get("null") else 1 - p, 1e-12))
        return tot / max(1, len(nulls))

    def score_nll(s):
        tot = 0.0
        for r, y in scores:
            y = min(max(y, 0.005), 0.995)
            a, b = r["mu"] * r["kappa"] * s, (1 - r["mu"]) * r["kappa"] * s
            tot -= (a - 1) * math.log(y) + (b - 1) * math.log1p(-y) - betaln(a, b)
        return tot / max(1, len(scores))

    out = {}
    for name, fn, n in [("t_choice", choice_nll, len(choice)), ("t_null", null_nll, len(nulls)),
                        ("kappa_scale", score_nll, len(scores))]:
        res = minimize_scalar(fn, bounds=(0.05, 20.0), method="bounded")
        out[name] = float(res.x)
        out[f"{name}_nll_before"] = float(fn(1.0))
        out[f"{name}_nll_after"] = float(res.fun)
        out[f"{name}_n"] = n
    return out


def cmd_calibrate(a) -> None:
    model = load(a.model)
    exs = []
    for sid, src in SOURCES.items():
        p = Path(a.data) / sid / "val.jsonl.gz"
        if not src.heldout and p.exists():
            rows = read_jsonl(p)
            random.Random(0).shuffle(rows)
            exs += rows[: a.per_source]
    raws = raw_outputs(model, exs)
    pairs = [(r, q, ex["answers"][q["id"]]) for ex, rs in zip(exs, raws) for r, q in zip(rs, ex["questions"])]
    cal = fit_calibration(pairs)
    cal["fit_on"] = f"validation splits, {len(exs)} examples"
    Path(a.out).write_text(json.dumps(cal, indent=2) + "\n")
    print(json.dumps(cal, indent=2))


# ---------------------------------------------------------------------------
# Kodiak predictions
# ---------------------------------------------------------------------------


def kodiak_records(exs: list[dict], raws: list[list[dict]], cal: dict | None, null_threshold: float = 0.5,
                   interval: float = 0.9) -> list[dict]:
    recs = []
    for i, (ex, rs) in enumerate(zip(exs, raws)):
        for raw, q in zip(rs, ex["questions"]):
            r = apply_calibration(raw, cal)
            gold = ex["answers"][q["id"]]
            rec = {"ex": i, "qid": q["id"], "source": ex["meta"]["source"], "tags": ex["meta"]["tags"],
                   "type": r["type"], "allow_null": r["allow_null"], "gold": gold, "p_null": r["p_null"], "probs": {}}
            abstain = r["allow_null"] and r["p_null"] >= null_threshold
            if r["type"] == "choice":
                probs = {lab: (1 - r["p_null"]) * c for lab, c in zip(r["labels"], r["cond_probs"])}
                best = max(probs, key=probs.get)
                rec.update(probs=probs, decision=None if abstain else best,
                           confidence=r["p_null"] if abstain else probs[best])
            else:
                a_, b_ = r["mu"] * r["kappa"], (1 - r["mu"]) * r["kappa"]
                tail = (1 - interval) / 2
                rec.update(decision=None if abstain else r["mu"], mu=r["mu"], kappa=r["kappa"], unit_pred=r["mu"],
                           interval_unit=[float(beta_dist.ppf(tail, a_, b_)), float(beta_dist.ppf(1 - tail, a_, b_))],
                           unit_gold=to_unit(q, gold["value"]) if "value" in gold else None)
            recs.append(rec)
    return recs


def cmd_predict(a) -> None:
    model = load(a.model)
    exs = read_jsonl(a.eval)
    cal = json.loads(Path(a.calibration).read_text()) if a.calibration else None
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    raws = raw_outputs(model, exs)
    torch.cuda.synchronize()
    batched_ms = (time.perf_counter() - t0) * 1000 / len(exs)
    # Latency at batch size 1, on a fixed sample of examples.
    lat = {}
    sample = random.Random(0).sample(range(len(exs)), min(a.latency_n, len(exs)))
    raw_outputs(model, [exs[sample[0]]])  # warm up
    for i in sample:
        torch.cuda.synchronize()
        t = time.perf_counter()
        raw_outputs(model, [exs[i]])
        torch.cuda.synchronize()
        lat[i] = (time.perf_counter() - t) * 1000
    recs = kodiak_records(exs, raws, cal)
    for r in recs:
        r["latency_ms"] = lat.get(r["ex"])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w") as f:
        f.write(json.dumps({"_meta": {"system": a.name or Path(a.model).name, "model": a.model, "calibration": cal,
                                      "batched_ms_per_example": batched_ms, "eval": a.eval}}) + "\n")
        for r in recs:
            f.write(json.dumps(r) + "\n")
    print(f"{len(recs)} question records -> {a.out}; batched {batched_ms:.2f} ms/example; "
          f"batch-1 p50 {np.percentile(list(lat.values()), 50):.1f} ms")


# ---------------------------------------------------------------------------
# LLM baseline (Ollama, JSON-schema-constrained output)
# ---------------------------------------------------------------------------

UNANSWERABLE = "UNANSWERABLE"


def llm_schema(questions: list[dict]) -> dict:
    props = {}
    for q in questions:
        if q["type"] == "choice":
            ans = {"type": "string", "enum": [lab["id"] for lab in q["labels"]] + [UNANSWERABLE]}
        else:
            # A number or the literal UNANSWERABLE. A free string let Qwen answer things like ">= 0.8".
            ans = {"anyOf": [{"type": "number"}, {"type": "string", "enum": [UNANSWERABLE]}]}
        props[q["id"]] = {"type": "object", "properties": {"quote": {"type": "string"}, "answer": ans,
                                                            "confidence": {"type": "number"}},
                          "required": ["quote", "answer", "confidence"]}
    return {"type": "object", "properties": props, "required": list(props)}


def llm_prompt(ex: dict) -> str:
    lines = []
    for q in ex["questions"]:
        if q["type"] == "choice":
            opts = "; ".join(f'{lab["id"]} = {lab["text"]}' for lab in q["labels"])
            lines.append(f'- id={q["id"]} (choice): {q["text"]} Options: {opts}')
        else:
            anchors = f'; {q.get("min_label", "")} .. {q.get("max_label", "")}' if q.get("min_label") else ""
            lines.append(f'- id={q["id"]} (score from {q["min"]} to {q["max"]}{anchors}): {q["text"]}')
    # v2 prompt. v1 said "using only information in the state", and Qwen then abstained on most judgment
    # questions ("how toxic is this?") and general-knowledge multiple choice: an unfair handicap.
    return f"""Answer each question about the STATE.
- Judgment questions (ratings, tone, quality, intent, category, which option best fits or completes something) are
  answerable: apply your own judgment and general knowledge to the state.
- Answer {UNANSWERABLE} only when the question asks for a specific fact about this situation that the state does not
  provide, or when none of the offered options fits.
For each question: copy the most relevant part of the state into "quote" (empty if none), then give "answer"
(an option id for choice questions, a number for score questions, or {UNANSWERABLE}), then "confidence": the
probability (0 to 1) that your answer is correct.

STATE:
{render_state(ex["state"])}

QUESTIONS:
{chr(10).join(lines)}"""


def llm_call(model: str, ex: dict) -> tuple[dict, float]:
    body = {"model": model, "stream": False, "think": False, "format": llm_schema(ex["questions"]),
            "messages": [{"role": "user", "content": llm_prompt(ex)}],
            "options": {"temperature": 0.0, "num_ctx": 8192, "num_predict": 300 + 200 * len(ex["questions"])}}
    req = urllib.request.Request("http://localhost:11434/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    t = time.perf_counter()
    d = json.load(urllib.request.urlopen(req, timeout=900))
    return json.loads(d["message"]["content"]), (time.perf_counter() - t) * 1000


def llm_records(i: int, ex: dict, out: dict, ms: float) -> list[dict]:
    recs = []
    for q in ex["questions"]:
        o = out.get(q["id"]) or {}
        ans = str(o.get("answer", UNANSWERABLE)).strip()
        try:
            conf = float(min(max(float(o.get("confidence", 0.5)), 0.0), 1.0))
        except (TypeError, ValueError):
            conf = 0.5
        gold = ex["answers"][q["id"]]
        rec = {"ex": i, "qid": q["id"], "source": ex["meta"]["source"], "tags": ex["meta"]["tags"], "type": q["type"],
               "allow_null": q.get("allow_null", True), "gold": gold, "latency_ms": ms}
        abstain = ans == UNANSWERABLE
        if q["type"] == "choice":
            ids = [lab["id"] for lab in q["labels"]]
            # Verbalized confidence goes to the chosen outcome; the rest is spread evenly (documented in the report).
            outcomes = ids + ([UNANSWERABLE] if rec["allow_null"] else [])
            chosen = ans if ans in outcomes else UNANSWERABLE
            rest = (1 - conf) / max(1, len(outcomes) - 1)
            dist = {k: (conf if k == chosen else rest) for k in outcomes}
            rec.update(probs={k: v for k, v in dist.items() if k != UNANSWERABLE}, p_null=dist.get(UNANSWERABLE, 0.0),
                       decision=None if chosen == UNANSWERABLE else chosen, confidence=conf)
        else:
            m = None if abstain else re.search(r"-?\d+(?:\.\d+)?", ans)  # lenient: take the first number
            if m:
                unit = min(max(to_unit(q, float(m.group())), 0.0), 1.0)
            else:
                abstain, unit = True, None
            rec.update(probs={}, p_null=conf if abstain else 1 - conf, decision=None if abstain else unit, unit_pred=unit,
                       unit_gold=to_unit(q, gold["value"]) if "value" in gold else None)
        recs.append(rec)
    return recs


def cmd_baseline(a) -> None:
    exs = read_jsonl(a.eval)
    idx = list(range(len(exs)))
    if a.limit and a.limit < len(exs):
        idx = sorted(random.Random(0).sample(idx, a.limit))
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out_path.exists():  # resumable
        for line in open(out_path):
            r = json.loads(line)
            if "ex" in r:
                done.add(r["ex"])
    else:
        out_path.write_text(json.dumps({"_meta": {"system": a.name or a.llm, "llm": a.llm, "eval": a.eval, "limit": a.limit,
                                                  "confidence": "verbalized", "prompt": "v3: judgments answerable; numeric score schema; quote, answer, confidence"}}) + "\n")
    todo = [i for i in idx if i not in done]
    print(f"{len(done)} done, {len(todo)} to run")

    def work(i):
        try:
            out, ms = llm_call(a.llm, exs[i])
        except Exception as e:  # count as abstentions, but record the failure
            print(f"ex {i}: {type(e).__name__}: {e}")
            out, ms = {}, None
        return llm_records(i, exs[i], out, ms)

    with ThreadPoolExecutor(a.workers) as pool, open(out_path, "a") as f:
        for n, recs in enumerate(pool.map(work, todo), 1):
            for r in recs:
                f.write(json.dumps(r) + "\n")
            f.flush()
            if n % 25 == 0:
                print(f"{n}/{len(todo)}", flush=True)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

COLS = [("n_questions", "n", "{:.0f}"), ("accuracy", "acc", "{:.3f}"), ("macro_f1", "macro-F1", "{:.3f}"),
        ("ece", "ECE", "{:.3f}"), ("brier", "Brier", "{:.3f}"), ("abstain_precision", "abst-P", "{:.2f}"),
        ("abstain_recall", "abst-R", "{:.2f}"), ("score_mae", "score MAE", "{:.3f}"), ("score_answered", "score given", "{:.2f}"),
        ("score_interval_coverage", "90%-int cov", "{:.2f}"), ("latency_p50_ms", "p50 ms", "{:.0f}")]


def load_preds(p: str) -> tuple[dict, list[dict]]:
    rows = read_jsonl(p)
    meta = rows[0].get("_meta", {}) if rows else {}
    return meta, [r for r in rows if "ex" in r]


def cmd_report(a) -> None:
    systems = [load_preds(p) for p in a.preds]
    # Compare on the common subset of examples, so baselines evaluated on a sample are compared fairly.
    common = set.intersection(*[{r["ex"] for r in recs} for _, recs in systems])
    lines = [f"# Kodiak eval report\n", f"Eval set: `{systems[0][0].get('eval', EVAL)}`; examples compared: {len(common)}\n"]
    results = {}
    for meta, recs in systems:
        name = meta.get("system", "?")
        results[name] = report([r for r in recs if r["ex"] in common])
    slice_names = [s for s in ["overall", "eval:indomain", "eval:heldout", "eval:null_construct", "eval:synthetic"]
                   if any(s in res for res in results.values())]
    for s in slice_names + sorted({k for res in results.values() for k in res if k.startswith("null:")}):
        lines.append(f"\n## {s}\n")
        lines.append("| system | " + " | ".join(c[1] for c in COLS) + " |")
        lines.append("|---|" + "---|" * len(COLS))
        for name, res in results.items():
            m = res.get(s, {})
            cells = [(fmt.format(m[k]) if k in m and m[k] == m[k] else "–") for k, _, fmt in COLS]
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines.append("\n## Per source (accuracy / ECE / score MAE)\n")
    lines.append("| source | " + " | ".join(results) + " |")
    lines.append("|---|" + "---|" * len(results))
    for src in sorted({k for res in results.values() for k in res if k.startswith("source:")}):
        cells = []
        for res in results.values():
            m = res.get(src, {})
            acc = f"{m['accuracy']:.3f}" if "accuracy" in m else "–"
            e = f"{m['ece']:.3f}" if "ece" in m else "–"
            mae = f" / MAE {m['score_mae']:.3f}" if "score_mae" in m else ""
            cells.append(f"{acc} / {e}{mae}")
        lines.append(f"| {src[7:]} | " + " | ".join(cells) + " |")
    lines.append("\n## Systems\n")
    for meta, _ in systems:
        lines.append(f"- **{meta.get('system')}**: `{json.dumps({k: v for k, v in meta.items() if k != 'calibration'})}`")
    text = "\n".join(lines) + "\n"
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(text)
    Path(a.out).with_suffix(".json").write_text(json.dumps(results, indent=2) + "\n")
    print(text)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("calibrate")
    c.add_argument("--model", required=True)
    c.add_argument("--data", default="data/processed")
    c.add_argument("--per-source", type=int, default=300)
    c.add_argument("--out", required=True)
    p = sub.add_parser("predict")
    p.add_argument("--model", required=True)
    p.add_argument("--calibration", default=None)
    p.add_argument("--eval", default=EVAL)
    p.add_argument("--name", default=None)
    p.add_argument("--latency-n", type=int, default=200)
    p.add_argument("--out", required=True)
    b = sub.add_parser("baseline")
    b.add_argument("--llm", default="qwen3.8:27b")
    b.add_argument("--eval", default=EVAL)
    b.add_argument("--limit", type=int, default=0)
    b.add_argument("--workers", type=int, default=1)
    b.add_argument("--name", default=None)
    b.add_argument("--out", required=True)
    r = sub.add_parser("report")
    r.add_argument("preds", nargs="+")
    r.add_argument("--out", default="reports/eval-report.md")
    a = ap.parse_args(argv)
    {"calibrate": cmd_calibrate, "predict": cmd_predict, "baseline": cmd_baseline, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
