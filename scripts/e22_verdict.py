"""E22 verdict against its pre-set lines (docs/experiments/E22-skills-batch-3.md; noise lines from docs/NOISE.md).
    uv run python scripts/e22_verdict.py --seeds 1        # after seed 1: exit 3 = stop (3 SD past a guard, or no target gain)
    uv run python scripts/e22_verdict.py --seeds 0,1,2    # final: 3-seed means vs the keep line and guards
"""
import argparse
import json
import statistics as S
import subprocess
import sys

BASE = {"anchor": 0.211, "anchor_s1": 0.138}
GUARDS = [("never-seen forced", ("eval:heldout", "forced_accuracy"), 0.673, 0.665), ("familiar", ("eval:indomain", "accuracy"), 0.871, 0.868),
          ("abstain precision", ("overall", "abstain_precision"), 0.854, 0.841), ("ranking", ("eval:heldout", "aurc_gap_closed"), 0.542, 0.535)]


def anchor_score(seed):
    sk = {}
    for line in list(open({"e22": "reports/preds_anchors/e22-s{}.jsonl", "v02": "reports/preds_anchors/v02-s{}.jsonl"}[PREFIX].format(seed)))[1:]:
        r = json.loads(line)
        k = next(t for t in r["tags"] if t.startswith("probe:"))
        probs = {a: b for a, b in r["probs"].items() if not a.startswith("__")}
        sk.setdefault(k, [len(probs), []])[1].append(max(probs, key=probs.get) == r["gold"]["label"])
    return S.mean(((sum(v) / len(v)) - 1 / n) / (1 - 1 / n) for n, v in sk.values())


def trap(seed):
    hits = [0, 0]
    for line in list(open({"e22": "reports/preds_trap/e22-s{}.jsonl", "v02": "reports/preds_trap/e18-s{}.jsonl"}[PREFIX].format(seed)))[1:]:
        r = json.loads(line)
        if "trap:trap" in r["tags"]:
            probs = {a: b for a, b in r["probs"].items() if not a.startswith("__")}
            hits[0] += max(probs, key=probs.get) == r["gold"]["label"]
            hits[1] += 1
    return hits[0] / hits[1]


ap = argparse.ArgumentParser()
ap.add_argument("--seeds", default="1")
ap.add_argument("--prefix", default="e22", help="file prefix (test: v02 files)")
a = ap.parse_args()
seeds = [int(s) for s in a.seeds.split(",")]
PREFIX = a.prefix
V = {"e22": "reports/preds_v02/e22-xl-skills3-s{}.jsonl", "v02": "reports/preds_v02/e18-xl-wording-s{}.jsonl"}[a.prefix]
subprocess.run([sys.executable, "-m", "kodiak_s1.eval.run", "report"] + [V.format(s) for s in seeds]
               + ["--out", "reports/e22-verdict-tmp.md"], check=True, capture_output=True)
rep = json.load(open("reports/e22-verdict-tmp.json"))
reps = list(rep.values())  # same order as the files given
vals = {name: [r[sl][k] for r in reps] for name, (sl, k), *_ in GUARDS}
vals["wording-trap eval"] = [trap(s) for s in seeds]
anc = [anchor_score(s) for s in seeds]
guards = GUARDS + [("wording-trap eval", None, 0.806, 0.775)]
lines, stop, fail = [], False, False
lines.append(f"real-anchor score: {', '.join(f'{x:.3f}' for x in anc)} → mean {S.mean(anc):.3f} (keep ≥ 0.311; v0.2 mean 0.211)")
if len(seeds) == 1:
    if anc[0] <= BASE["anchor_s1"]:
        stop = True
        lines.append(f"  STOP: no target gain over v0.2 seed 1 ({BASE['anchor_s1']})")
else:
    fail |= S.mean(anc) < 0.311
for name, _, line3, line_single in guards:
    v = vals[name]
    if len(seeds) == 1:
        bad = v[0] < line_single
        stop |= bad
        lines.append(f"{name}: {v[0]:.3f} (single-run reject only below {line_single}) {'STOP' if bad else 'ok'}")
    else:
        bad = S.mean(v) < line3
        fail |= bad
        lines.append(f"{name}: {', '.join(f'{x:.3f}' for x in v)} → mean {S.mean(v):.3f} (line ≥ {line3}) {'FAIL' if bad else 'ok'}")
print("\n".join(lines))
if len(seeds) == 1:
    print("SEED 1: continue to seeds 0 and 2" if not stop else "SEED 1: stop (rule in the proposal)")
    sys.exit(3 if stop else 0)
print("VERDICT: " + ("KILL" if fail else "KEEP") + " (3-seed means vs the pre-set lines)")
