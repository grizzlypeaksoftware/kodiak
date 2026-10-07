"""Label-overlap audit (D67): would a pure word-matching rule ("pick the option whose words appear most in the state") get the answer right?
If it beats chance by a lot on training data, the data teaches the shortcut behind the wording trap. Compared across synthetic and public
training data and our evals. uv run python scripts/audit_label_overlap.py"""
import gzip
import json
import random
import re
from collections import defaultdict
from pathlib import Path

STOP = set("the a an and or of to in on for with is are be it this that not no yes by as at from about".split())


def words(t):
    return {w for w in re.findall(r"[a-z0-9]+", str(t).lower()) if len(w) > 2 and w not in STOP}


def score(ex):
    """Per choice question with a gold label: (overlap-rule correct, chance, tie-free)."""
    st = words(json.dumps(ex["state"], ensure_ascii=False))
    out = []
    for q in ex["questions"]:
        g = (ex.get("answers") or {}).get(q["id"], {}).get("label")
        if q.get("type") != "choice" or not g or len(q["labels"]) < 2:
            continue
        ov = {l["id"]: len(words(l["text"]) & st) / max(1, len(words(l["text"]))) for l in q["labels"]}
        best = max(ov.values())
        if best == 0:
            continue  # no option's words appear: the shortcut can't fire
        top = [k for k, v in ov.items() if v == best]
        out.append((g in top and len(top) == 1, 1 / len(q["labels"]), len(top) == 1))
    return out


def synth(path, n=4000):
    rows = [json.loads(l) for l in open(path)]
    rows = [r["example"] for r in rows if r.get("status") == "ok" and r.get("example")]
    random.Random(0).shuffle(rows)
    return rows[:n]


def processed(sid, n=2000):
    p = Path("data/processed") / sid / "train.jsonl.gz"
    with gzip.open(p, "rt") as f:
        return [json.loads(l) for _, l in zip(range(n), f)]


groups = {"synthetic: generator v2.0": synth("data/synthetic/gen2_v20.jsonl"), "synthetic: E17 skills": synth("data/synthetic/skills_v1_e17_10k.jsonl"),
          "synthetic: E21 skills-2": synth("data/synthetic/skills2_v1_e21_7k5.jsonl"), "synthetic: E22 skills-3": synth("data/synthetic/skills3_v1_e22_10k.jsonl")}
by_kind = defaultdict(list)
for r in [json.loads(l) for l in open("data/synthetic/skills3_v1_e22_10k.jsonl")] + [json.loads(l) for l in open("data/synthetic/skills2_v1_e21_7k5.jsonl")]:
    if r.get("status") == "ok":
        by_kind["  kind: " + r["kind"]].append(r["example"])
for sid in ["mnli", "clinc_oos", "massive", "go_emotions", "toolace", "commonsense_qa"]:
    try:
        groups["public: " + sid] = processed(sid)
    except FileNotFoundError:
        pass
groups["eval v0.2 never-seen"] = [json.loads(l) for l in open("data/eval/kodiak-eval-v0.2.jsonl") if "eval:heldout" in l]
groups["real anchors (RAGBench, MT-Bench, SemEval)"] = [json.loads(l) for l in open("data/eval/kodiak-real-anchors-v0.1.jsonl")]
groups.update({k: v[:2000] for k, v in sorted(by_kind.items())})
print(f"{'data':45s} {'questions':>9s} {'fires':>6s} {'rule acc':>8s} {'chance':>7s} {'lift':>6s}")
for name, exs in groups.items():
    res, total = [], 0
    for ex in exs:
        for q in ex["questions"]:
            total += q.get("type") == "choice"
        res += score(ex)
    if not res:
        print(f"{name:45s} {total:9d}   (shortcut never fires)")
        continue
    acc = sum(r[0] for r in res) / len(res)
    ch = sum(r[1] for r in res) / len(res)
    print(f"{name:45s} {total:9d} {len(res) / max(1, total):6.0%} {acc:8.2f} {ch:7.2f} {acc - ch:+6.2f}")
