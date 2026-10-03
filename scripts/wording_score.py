"""E18 metric on the wording eval: consistency (same forced answer under all 3 wordings) and forced accuracy per wording.
    uv run python scripts/wording_score.py reports/preds_wording/<name>.jsonl [...]"""
import json
import sys
from collections import defaultdict

for path in sys.argv[1:]:
    groups = defaultdict(dict)  # (wgroup, qid) -> style -> (forced label, correct)
    for line in list(open(path))[1:]:
        r = json.loads(line)
        g = next(t for t in r["tags"] if t.startswith("wgroup:"))
        style = next(t for t in r["tags"] if t.startswith("wording:"))[8:]
        if "label" not in (r.get("gold") or {}):
            continue  # gold is "can't tell": not a wording question
        probs = {k: v for k, v in r["probs"].items() if not k.startswith("__")}
        pick = max(probs, key=probs.get)
        groups[(g, r["qid"], r["source"])][style] = (pick, pick == r["gold"]["label"])
    full = {k: v for k, v in groups.items() if len(v) == 3}
    cons = sum(len({p for p, _ in v.values()}) == 1 for v in full.values()) / len(full)
    acc = {s: sum(v[s][1] for v in full.values()) / len(full) for s in ("original", "description", "paraphrase")}
    by_src = defaultdict(list)
    for (g, q, src), v in full.items():
        by_src[src].append(len({p for p, _ in v.values()}) == 1)
    print(f"{path}: consistency {cons:.3f} | accuracy original {acc['original']:.3f}, description {acc['description']:.3f}, "
          f"paraphrase {acc['paraphrase']:.3f}, reworded mean {(acc['description'] + acc['paraphrase']) / 2:.3f} | n={len(full)}")
    print("  consistency by task: " + ", ".join(f"{s} {sum(x) / len(x):.2f}" for s, x in sorted(by_src.items())))
