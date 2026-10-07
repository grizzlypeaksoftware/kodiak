"""Contrastive eval v0.1 (rule 7, D67): minimal pairs for the skills that have no real-data anchor. Each pair is two versions of one example,
identical except for ONE detail in one field, with different correct answers. A shortcut that reads the other fields (a keyword in the step,
the product in the request) gets at most one of the two right. Writer + blind checker (each version checked separately); seed 61; never
trained on. Metric: pair accuracy (both versions right) and item accuracy.

    uv run python scripts/build_contrastive_eval.py --pairs 70   # -> data/eval/kodiak-contrastive-v0.1.jsonl
v0.3 (E24): as v0.2, but every answer pair is attempted equally often and capped equally in the file ("never" balanced); then
scripts/filter_cue_hard.py keeps only pairs a changed-words reader trained on our training data gets wrong (D70).
v0.2 (E23): the writer and checker swap (DeepSeek-V3.2 writes, gpt-oss-120b checks), so the test doesn't share the training writer's style:
    uv run python scripts/build_contrastive_eval.py --version v0.2 --kinds step_safety,refund_eligibility --pairs 400
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
            "meta": {"source": "kodiak_contrastive" + ("" if VERSION == "v0.1" else f"_{VERSION}"), "split": "test", "license": "Apache-2.0", "teacher": f"{WRITER} (checked by {CHECKER})",
                     "tags": ["eval:contrastive", f"probe:{kind}", f"pair:{pair_id}", f"side:{side}"]}}


def job(kind, i):
    rng = random.Random(f"contrastive:{SEED}:{kind}:{i}")
    perms = list(itertools.permutations(KINDS[kind]["labels"], 2))
    la, lb = perms[i % len(perms)] if VERSION == "v0.3" else rng.choice(perms)  # v0.3: every answer pair equally often
    rec = {"kind": kind, "job": i, "writer": WRITER, "verifier": CHECKER, "status": "error"}
    try:
        g = synth.teacher(prompt(kind, la, lb), schema(kind), 0.9, WRITER, 1500)
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"))
        norm = lambda d: {k: ("\n".join(map(str, v)) if isinstance(v, list) else str(v)) for k, v in d.items() if k in KINDS[kind]["fields"]}
        a, b = norm(g["content"]["a"]), norm(g["content"]["b"])
        a, b = ({k: " ".join(x.split()) for k, x in d.items()} for d in (a, b))  # ignore whitespace-only differences
        v = VARY[kind]
        if any(a[k].strip() != b[k].strip() for k in a if k != v) or a[v].strip() == b[v].strip():
            diff = {k: [a[k][:300], b[k][:300]] for k in a if k != v and a[k].strip() != b[k].strip()}
            rec.update(status="not_minimal", why="other fields differ or varied field equal", diff=diff)  # other fields must match exactly and the varied field must differ
            return rec
        ratio = difflib.SequenceMatcher(None, a[v], b[v]).ratio()
        if ratio < (0.45 if kind == "sarcasm" else 0.6):
            rec.update(status="not_minimal", why=f"ratio {ratio:.2f}")  # the varied field changed too much
            return rec
        pid = f"{kind}-{i}"
        exs = [example(kind, a, la, pid, "a"), example(kind, b, lb, pid, "b")]
        vt, vp = 0, 0
        for ex in exs:
            q = ex["questions"]
            r = synth.teacher(verify_prompt(render_state(ex["state"]), q), synth.verify_schema(q), 0.0, CHECKER, CHECK_TOKENS)
            vt += r["tokens"]
            vp += r.get("prompt_tokens") or 0
            got = synth.parse_verdict(q[0], r["content"].get("decision"))
            if (got or {}).get("label") != ex["answers"]["decision"]["label"]:
                rec.update(status="checker_disagrees", why={"side": ex["meta"]["tags"][-1], "want": ex["answers"]["decision"]["label"], "got": got, "raw": str(r["content"])[:200]}, verify_tokens=vt, verify_prompt_tokens=vp)
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
ap.add_argument("--version", default="v0.1", choices=["v0.1", "v0.2", "v0.3"])
ap.add_argument("--per-kind", type=int, default=50)
a = ap.parse_args()
SEED, VERSION, CHECK_TOKENS = 61, a.version, 600
if a.version in ("v0.2", "v0.3"):
    WRITER, CHECKER, SEED, CHECK_TOKENS = "do:deepseek-3.2", "do:openai-gpt-oss-120b", 62 if a.version == "v0.2" else 63, 1500  # gpt-oss reasons first
raw = Path("data/eval/contrastive_raw.jsonl" if a.version == "v0.1" else f"data/eval/contrastive_raw_{a.version}.jsonl")
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
with open(f"data/eval/kodiak-contrastive-{a.version}" + ("-all" if a.version == "v0.3" else "") + ".jsonl", "w") as f:
    for r in sorted(recs, key=lambda r: (r["kind"], r["job"])):
        lab = tuple(e["answers"]["decision"]["label"] for e in r.get("examples", []))
        cap = (a.per_kind + 5) // 6 if VERSION == "v0.3" else a.per_kind
        if r["status"] == "ok" and n[r["kind"]] < a.per_kind and n[(r["kind"], lab)] < cap:
            n[(r["kind"], lab)] += 1
            for ex in r["examples"]:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            n[r["kind"]] += 1
print(Counter((r["kind"], r["status"]) for r in recs), "-> pairs per kind", {k: v for k, v in n.items() if isinstance(k, str)},
      {k: v for k, v in n.items() if not isinstance(k, str)}, file=sys.stderr)
