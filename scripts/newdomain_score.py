"""Score predictions on the new-domains test (D76): per task, chance-corrected skill (0 = random, 1 = perfect; answers are balanced so
chance = 1 / number of options), and the headline = mean skill over the read slice's tasks (each question of a multi-question task counts
as its own task).
    uv run python scripts/newdomain_score.py reports/preds_newdomain/<name>.jsonl [...]
"""
import json
import statistics as S
import sys
from collections import defaultdict


def score(path):
    acc, nopt, sl = defaultdict(list), {}, {}
    for line in list(open(path))[1:]:
        r = json.loads(line)
        task = next(t for t in r["tags"] if t.startswith("nd:"))[3:] + ("" if r["qid"] == "decision" else f".{r['qid']}")
        probs = {a: b for a, b in r["probs"].items() if not a.startswith("__")}
        acc[task].append(max(probs, key=probs.get) == r["gold"]["label"])
        nopt[task], sl[task] = len(probs), next(t for t in r["tags"] if t.startswith("slice:"))[6:]
    skill = {t: ((sum(v) / len(v)) - 1 / nopt[t]) / (1 - 1 / nopt[t]) for t, v in acc.items()}
    return skill, sl, {t: len(v) for t, v in acc.items()}, nopt


if __name__ == "__main__":
    res = {p: score(p) for p in sys.argv[1:]}
    tasks = sorted(next(iter(res.values()))[0], key=lambda t: (next(iter(res.values()))[1][t] != "read", t))
    name = lambda p: p.split("/")[-1].replace(".jsonl", "")
    print(f"{'task':42s} {'slice':9s} {'n':>4s} {'opts':>4s} " + " ".join(f"{name(p)[:12]:>12s}" for p in res))
    sk0, sl0, n0, o0 = next(iter(res.values()))
    for t in tasks:
        print(f"{t:42s} {sl0[t]:9s} {n0[t]:4d} {o0[t]:4d} " + " ".join(f"{res[p][0][t]:+12.3f}" for p in res))
    for s in ("read", "knowledge"):
        print(f"{'MEAN ' + s:42s} {'':9s} {'':4s} {'':4s} " + " ".join(f"{S.mean(v for t, v in res[p][0].items() if res[p][1][t] == s):+12.3f}" for p in res))
