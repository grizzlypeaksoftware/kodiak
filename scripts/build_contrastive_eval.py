"""Contrastive eval v0.1 (rule 7, D67): minimal pairs for the skills that have no real-data anchor. Each pair is two versions of one example,
identical except for ONE detail in one field, with different correct answers. A shortcut that reads the other fields (a keyword in the step,
the product in the request) gets at most one of the two right. Writer + blind checker (each version checked separately); seed 61; never
trained on. Metric: pair accuracy (both versions right) and item accuracy.

    uv run python scripts/build_contrastive_eval.py --pairs 70   # -> data/eval/kodiak-contrastive-v0.1.jsonl
"""
import argparse
import difflib
import itertools
import json
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from kodiak_s1.data import synth
from kodiak_s1.data.gen2.prompts import verify_prompt
from kodiak_s1.data.sim.probes import KINDS
from kodiak_s1.schema import render_state

WRITER, CHECKER = "do:openai-gpt-oss-120b", "do:deepseek-3.2"
# kind -> the one field allowed to differ between the two versions
VARY = {"step_safety": "task", "refund_eligibility": "request", "policy_violation": "message", "sarcasm": "text"}


def prompt(kind, la, lb):
    spec = KINDS[kind]
    fields = "\n".join(f"- {k}: {v}" for k, v in spec["fields"].items())
    v = VARY[kind]
    keep = [k for k in spec["fields"] if k != v]
    return (f"Write TWO versions of one realistic example for a decision task. Fields:\n{fields}\n\nThe question: {spec['question']}\n"
            f"Options: {'; '.join(spec['labels'].values())}.\n\nVersion A's correct answer must be: {spec['labels'][la]}. Version B's correct "
            f"answer must be: {spec['labels'][lb]}. " + (f"The fields {', '.join(keep)} must be IDENTICAL in both versions (copy them exactly). " if keep else "")
            + f"The field '{v}' must differ by ONE small detail only (a few words: a fact, a number, a condition), so that the answer changes "
            "for a careful reader while a reader who skims or matches keywords would answer both the same. Write naturally. Use single quotes "
            "inside text, never double quotes. Return JSON only: {\"a\": {fields...}, \"b\": {fields...}}.")


def schema(kind):
    props = {k: {"type": "string"} for k in KINDS[kind]["fields"]}
    one = {"type": "object", "properties": props, "required": list(props)}
    return {"type": "object", "properties": {"a": one, "b": one}, "required": ["a", "b"]}


def example(kind, fields, label, pair_id, side):
    spec = KINDS[kind]
    q = {"type": "choice", "id": "decision", "text": spec["question"], "labels": [{"id": k, "text": t} for k, t in spec["labels"].items()]}
    return {"state": fields, "questions": [q], "answers": {"decision": {"label": label}},
            "meta": {"source": "kodiak_contrastive", "split": "test", "license": "Apache-2.0", "teacher": f"{WRITER} (checked by {CHECKER})",
                     "tags": ["eval:contrastive", f"probe:{kind}", f"pair:{pair_id}", f"side:{side}"]}}


def job(kind, i):
    rng = random.Random(f"contrastive:61:{kind}:{i}")
    la, lb = rng.choice(list(itertools.permutations(KINDS[kind]["labels"], 2)))
    rec = {"kind": kind, "job": i, "writer": WRITER, "verifier": CHECKER, "status": "error"}
    try:
        g = synth.teacher(prompt(kind, la, lb), schema(kind), 0.9, WRITER, 1500)
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"))
        norm = lambda d: {k: ("\n".join(map(str, v)) if isinstance(v, list) else str(v)) for k, v in d.items()}
        a, b = norm(g["content"]["a"]), norm(g["content"]["b"])
        v = VARY[kind]
        if any(a[k].strip() != b[k].strip() for k in a if k != v) or a[v].strip() == b[v].strip():
            rec["status"] = "not_minimal"  # other fields must match exactly and the varied field must differ
            return rec
        if difflib.SequenceMatcher(None, a[v], b[v]).ratio() < (0.45 if kind == "sarcasm" else 0.6):
            rec["status"] = "not_minimal"  # the varied field changed too much
            return rec
        pid = f"{kind}-{i}"
        exs = [example(kind, a, la, pid, "a"), example(kind, b, lb, pid, "b")]
        vt, vp = 0, 0
        for ex in exs:
            q = ex["questions"]
            r = synth.teacher(verify_prompt(render_state(ex["state"]), q), synth.verify_schema(q), 0.0, CHECKER, 600)
            vt += r["tokens"]
            vp += r.get("prompt_tokens") or 0
            if (synth.parse_verdict(q[0], r["content"].get("decision")) or {}).get("label") != ex["answers"]["decision"]["label"]:
                rec.update(status="checker_disagrees", verify_tokens=vt, verify_prompt_tokens=vp)
                return rec
        rec.update(status="ok", examples=exs, verify_tokens=vt, verify_prompt_tokens=vp)
    except OSError as e:
        rec.update(status="retry", error=str(e)[:200])
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    return rec


ap = argparse.ArgumentParser()
ap.add_argument("--pairs", type=int, default=70)
ap.add_argument("--kinds", default=",".join(VARY))
ap.add_argument("--start", type=int, default=0)
a = ap.parse_args()
raw = Path("data/eval/contrastive_raw.jsonl")
recs = [json.loads(l) for l in raw.open()] if raw.exists() else []
for attempt in range(3):
    done = {(r["kind"], r["job"]) for r in recs if r["status"] != "retry"}
    todo = [(k, i) for k in a.kinds.split(",") for i in range(a.start, a.start + a.pairs) if (k, i) not in done]
    if not todo:
        break
    with ThreadPoolExecutor(12) as ex:
        recs = [r for r in recs if r["status"] != "retry"] + list(ex.map(lambda t: job(*t), todo))
raw.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n")
n = Counter()
with open("data/eval/kodiak-contrastive-v0.1.jsonl", "w") as f:
    for r in sorted(recs, key=lambda r: (r["kind"], r["job"])):
        if r["status"] == "ok" and n[r["kind"]] < 50:
            for ex in r["examples"]:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            n[r["kind"]] += 1
print(Counter((r["kind"], r["status"]) for r in recs), "-> pairs per kind", dict(n), file=sys.stderr)
