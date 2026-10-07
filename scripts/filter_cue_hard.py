"""Contrastive v0.3 (E24, D70): keep only the pairs a changed-words reader gets wrong. The reader is trained on our contrast-group TRAINING
data (E23 + E24 groups; each version reduced to the words no other version in its group has), never on test pairs, then reads each test
side's changed words. A pair it gets fully right is solvable by cue words and is dropped. Also reports the label balance.

    uv run python scripts/filter_cue_hard.py      # data/eval/kodiak-contrastive-v0.3-all.jsonl -> data/eval/kodiak-contrastive-v0.3.jsonl
"""
import json
from collections import Counter, defaultdict

from diff_reader import VARY, group_diffs, reader, test_pairs

GROUPS = ["data/synthetic/groups_v1.jsonl", "data/synthetic/groups_cb_pilot.jsonl", "data/synthetic/groups_cb_v1.jsonl"]
SRC, OUT = "data/eval/kodiak-contrastive-v0.3-all.jsonl", "data/eval/kodiak-contrastive-v0.3.jsonl"
keep = set()
for kind in VARY:
    rows = []
    for g in GROUPS:
        try:
            rows += group_diffs(g, kind)
        except FileNotFoundError:
            pass
    vec, m = reader([d for _, _, d, _ in rows], [y for *_, y in rows])
    pairs = test_pairs(SRC, kind)
    solved = {pid for pid, sides in pairs if all(m.predict(vec.transform([d]))[0] == y for d, y in sides)}
    keep |= {(kind, pid) for pid, _ in pairs if pid not in solved}
    print(f"{kind}: {len(pairs)} pairs, {len(solved)} solvable by the changed-words reader (trained on {len(rows):,} training versions) -> keep {len(pairs) - len(solved)}")
n, lab = 0, defaultdict(Counter)
with open(OUT, "w", encoding="utf-8") as f:
    for line in open(SRC, encoding="utf-8"):
        e = json.loads(line)
        t = lambda p: next(x for x in e["meta"]["tags"] if x.startswith(p)).split(":", 1)[1]
        if (t("probe:"), t("pair:")) in keep:
            f.write(line)
            n += 1
            lab[t("probe:")][e["answers"]["decision"]["label"]] += 1
print(n, "items ->", OUT, {k: dict(v) for k, v in lab.items()})
