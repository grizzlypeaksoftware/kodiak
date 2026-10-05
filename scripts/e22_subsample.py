"""E22: 2,500 kept examples per new kind from the skills-3 batch (unique job ids, see e21_subsample.py); the rest is banked."""
import json
import random
from collections import defaultdict

SRC, OUT, PER = "data/synthetic/skills3_v1.jsonl", "data/synthetic/skills3_v1_e22_10k.jsonl", 2500
KINDS = ["long_hallucination", "stance", "refund_eligibility", "step_safety"]
last = {}
for line in open(SRC, encoding="utf-8"):
    r = json.loads(line)
    last[(r["kind"], r["job"])] = r
by = defaultdict(list)
for (kind, job), r in sorted(last.items()):
    if r["status"] == "ok":
        by[kind].append(r)
rng = random.Random(22)
with open(OUT, "w", encoding="utf-8") as f:
    for i, kind in enumerate(KINDS):
        rows = by[kind]
        rng.shuffle(rows)
        for r in rows[:PER]:
            f.write(json.dumps({**r, "job": 10_000_000 + i * 1_000_000 + r["job"]}, ensure_ascii=False) + "\n")
        print(kind, min(PER, len(rows)), "used of", len(rows), "kept")
