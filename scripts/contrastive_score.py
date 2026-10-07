"""Rule 7 (D67) metric on the contrastive eval: per kind, item accuracy (forced), pair accuracy (both versions right) and the same-answer
rate (the model gives one answer to both versions; a shortcut that ignores the changed detail does this every time). A pure shortcut scores
pair accuracy 0 and item accuracy ~0.5. uv run python scripts/contrastive_score.py reports/preds_contrastive/<name>.jsonl [...]"""
import json
import sys
from collections import defaultdict

for path in sys.argv[1:]:
    pairs = defaultdict(dict)
    for line in list(open(path))[1:]:
        r = json.loads(line)
        tag = lambda p: next(t for t in r["tags"] if t.startswith(p)).split(":", 1)[1]
        probs = {a: b for a, b in r["probs"].items() if not a.startswith("__")}
        pairs[(tag("probe:"), tag("pair:"))][tag("side:")] = (max(probs, key=probs.get), r["gold"]["label"])
    print(path)
    for kind in sorted({k for k, _ in pairs}):
        ps = [v for (k, _), v in pairs.items() if k == kind and len(v) == 2]
        item = sum(p == g for v in ps for p, g in v.values()) / (2 * len(ps))
        both = sum(all(p == g for p, g in v.values()) for v in ps) / len(ps)
        same = sum(v["a"][0] == v["b"][0] for v in ps) / len(ps)
        print(f"  {kind:20s} pairs={len(ps):3d} item acc={item:.3f} pair acc={both:.3f} same answer={same:.3f}")
