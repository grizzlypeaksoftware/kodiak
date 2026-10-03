"""E21: a balanced training sample of the skills-2 batch: 2,500 kept examples per kind (fixed seed); the rest is banked.
Job numbers repeat across kinds, and the trainer dedupes synthetic records by (file, job), so each record gets a unique job id here.
    uv run python scripts/e21_subsample.py"""
import json
import random
from collections import defaultdict

SRC, OUT, PER = "data/synthetic/skills2_v1.jsonl", "data/synthetic/skills2_v1_e21_7k5.jsonl", 2500
KINDS = ["pairwise_judge", "sarcasm", "policy_violation"]
last = {}
for line in open(SRC, encoding="utf-8"):
    r = json.loads(line)
    last[(r["kind"], r["job"])] = r
by = defaultdict(list)
for (kind, job), r in sorted(last.items()):
    if r["status"] == "ok":
        by[kind].append(r)
rng, n = random.Random(21), {}
with open(OUT, "w", encoding="utf-8") as f:
    for i, kind in enumerate(KINDS):
        rows = by[kind]
        rng.shuffle(rows)
        n[kind] = (min(PER, len(rows)), len(rows))
        for r in rows[:PER]:
            f.write(json.dumps({**r, "job": i * 1_000_000 + r["job"]}, ensure_ascii=False) + "\n")
print({k: f"{u} used of {t} kept" for k, (u, t) in n.items()}, "->", OUT)
