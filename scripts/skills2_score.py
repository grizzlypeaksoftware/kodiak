"""E21 metric: per-kind forced accuracy and chance-corrected skill on the skills-2 eval (and the real-data anchor), plus the skills-2 score
(mean skill over the three kinds). uv run python scripts/skills2_score.py reports/preds_skills2/<name>.jsonl [...]"""
import json
import sys
from collections import defaultdict

for path in sys.argv[1:]:
    acc, nl = defaultdict(list), {}
    for line in list(open(path))[1:]:
        r = json.loads(line)
        k = next(t for t in r["tags"] if t.startswith("probe:"))[6:] + (" (MT-Bench anchor)" if "anchor:mtbench" in r["tags"] else "")
        probs = {a: b for a, b in r["probs"].items() if not a.startswith("__")}
        acc[k].append(max(probs, key=probs.get) == r["gold"]["label"])
        nl[k] = len(probs)
    skill = {k: (sum(v) / len(v) - 1 / nl[k]) / (1 - 1 / nl[k]) for k, v in acc.items()}
    main = [s for k, s in skill.items() if "anchor" not in k]
    print(f"{path}: skills-2 score {sum(main) / len(main):.3f}" if main else path)
    for k in sorted(acc):
        print(f"  {k:34s} n={len(acc[k]):3d} acc={sum(acc[k]) / len(acc[k]):.3f} skill={skill[k]:+.3f}")
