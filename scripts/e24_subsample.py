"""E24: as E23 (e23_subsample.py), with the contrast groups replaced by cue-balanced groups (D70). Unique job ids from 40,000,000."""
import json
import random
from collections import defaultdict

PER = 2500
with open("data/synthetic/skills3_v1_e23_5k.jsonl", "w", encoding="utf-8") as f:
    n = 0
    for line in open("data/synthetic/skills3_v1_e22_10k.jsonl", encoding="utf-8"):
        if json.loads(line)["kind"] in ("long_hallucination", "stance"):
            f.write(line)
            n += 1
    print("skills-3 kept (long_hallucination + stance):", n)
groups = defaultdict(list)
for line in open("data/synthetic/groups_cb_v1.jsonl", encoding="utf-8"):
    r = json.loads(line)
    if r["status"] == "ok":
        groups[r["kind"]].append(r)
rng, short = random.Random(24), False
with open("data/synthetic/groups_cb_v1_e24_5k.jsonl", "w", encoding="utf-8") as f:
    for i, kind in enumerate(["step_safety", "refund_eligibility"]):
        rows, used = groups[kind], 0
        rng.shuffle(rows)
        for r in rows:
            if used >= PER:
                break
            for j, ex in enumerate(r["examples"][: PER - used]):
                f.write(json.dumps({"kind": kind, "job": 40_000_000 + i * 1_000_000 + r["job"] * 10 + j, "status": "ok", "example": ex},
                                   ensure_ascii=False) + "\n")
                used += 1
        print(kind, used, "examples from", len(rows), "kept groups")
        short = short or used < PER
if short:
    raise SystemExit("not enough contrast-group examples yet")
