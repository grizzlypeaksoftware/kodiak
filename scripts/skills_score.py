"""Skills score on the skills eval: mean forced accuracy of the four main questions (E17 kill line metric; reports/e17-skills-baseline.md).

    uv run python scripts/skills_score.py reports/preds_skills/<name>.jsonl [...]
"""
import json
import sys
from collections import defaultdict

MAIN = {"grounding": "grounded", "tools": "next", "claims": "verdict", "relevance": "relevance"}
for path in sys.argv[1:]:
    acc = defaultdict(list)
    for line in list(open(path))[1:]:
        r = json.loads(line)
        kind = next(t for t in r["tags"] if t.startswith("skill:"))[6:]
        probs = {k: v for k, v in r["probs"].items() if not k.startswith("__")}
        acc[(kind, r["qid"])].append(max(probs, key=probs.get) == r["gold"]["label"])
    main = {k: sum(acc[(k, q)]) / len(acc[(k, q)]) for k, q in MAIN.items()}
    other = {f"{k}/{q}": round(sum(v) / len(v), 3) for (k, q), v in sorted(acc.items()) if MAIN.get(k) != q}
    print(f"{path}: skills score {sum(main.values()) / 4:.3f}  " + "  ".join(f"{k} {v:.2f}" for k, v in main.items()) + f"  | {other}")
