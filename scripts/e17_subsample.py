"""E17: a balanced ~10k training subsample of the skills batch (2,500 kept examples per skill, fixed seed). The rest stays banked.

    uv run python scripts/e17_subsample.py [--per-kind 2500]
"""
import argparse
import json
import random
from collections import defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--src", default="data/synthetic/skills_v1.jsonl")
ap.add_argument("--out", default="data/synthetic/skills_v1_e17_10k.jsonl")
ap.add_argument("--per-kind", type=int, default=2500)
a = ap.parse_args()
last = {}
for line in open(a.src, encoding="utf-8"):
    r = json.loads(line)
    last[r["job"]] = r
by = defaultdict(list)
for r in last.values():
    if r["status"] == "ok":
        by[r["kind"]].append(r)
rng, n = random.Random(17), {}
with open(a.out, "w", encoding="utf-8") as f:
    for kind in sorted(by):
        rows = sorted(by[kind], key=lambda r: r["job"])
        rng.shuffle(rows)
        n[kind] = (min(a.per_kind, len(rows)), len(rows))
        for r in rows[: a.per_kind]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
print({k: f"{u} used of {t} kept" for k, (u, t)in n.items()}, "->", a.out)
