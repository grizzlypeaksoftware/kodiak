"""E23 verdict against its pre-set lines (docs/experiments/E23-contrast-groups.md; v0.3 noise lines from docs/NOISE.md).
    uv run python scripts/e23_verdict.py --seeds 1        # after seed 1: exit 3 = stop (3 SD past a guard, or no target gain)
    uv run python scripts/e23_verdict.py --seeds 0,1,2    # final: 3-seed means vs the keep line and guards
    --prefix e22: the same numbers for the v0.3 baseline (test of this script)
"""
import argparse
import json
import re
import statistics as S
import subprocess
import sys
from collections import defaultdict

KEEP, BASE_S1 = 0.452, 0.282
# name, (slice, key) in the eval report or None, 3-seed line, single-run line, higher is better
GUARDS = [("never-seen forced", ("eval:heldout", "forced_accuracy"), 0.666, 0.656, True),
          ("familiar", ("eval:indomain", "accuracy"), 0.868, 0.862, True),
          ("abstain precision", ("overall", "abstain_precision"), 0.855, 0.817, True),
          ("real-anchor score", None, 0.303, 0.276, True), ("wording-trap eval", None, 0.860, 0.840, True),
          ("flip rate (shortcut guard)", None, 0.372, 0.395, False), ("policy contrastive pairs (shortcut guard)", None, 0.499, 0.465, True)]


def rows(path):
    for line in list(open(path))[1:]:
        r = json.loads(line)
        probs = {a: b for a, b in r["probs"].items() if not a.startswith("__")}
        yield r, max(probs, key=probs.get) == r["gold"]["label"], len(probs)


def pairs(path, kinds):
    d = defaultdict(dict)
    for r, ok, _ in rows(path):
        t = lambda p: next(x for x in r["tags"] if x.startswith(p)).split(":", 1)[1]
        if t("probe:") in kinds:
            d[(t("probe:"), t("pair:"))][t("side:")] = ok
    return [all(v.values()) for v in d.values() if len(v) == 2]


def target(seed):
    both = pairs(f"reports/preds_contrastive/{PREFIX}-s{seed}.jsonl", ("step_safety", "refund_eligibility")) + \
        pairs(f"reports/preds_contrastive2/{PREFIX}-s{seed}.jsonl", ("step_safety", "refund_eligibility"))
    return sum(both) / len(both)


def anchor(seed):
    sk = {}
    for r, ok, n in rows(f"reports/preds_anchors/{PREFIX}-s{seed}.jsonl"):
        sk.setdefault(next(t for t in r["tags"] if t.startswith("probe:")), [n, []])[1].append(ok)
    return S.mean(((sum(v) / len(v)) - 1 / n) / (1 - 1 / n) for n, v in sk.values())


def trap(seed):
    hits = [ok for r, ok, _ in rows(f"reports/preds_trap/{PREFIX}-s{seed}.jsonl") if "trap:trap" in r["tags"]]
    return sum(hits) / len(hits)


def flip(seed):
    out = subprocess.run([sys.executable, "scripts/wording_score.py", f"reports/preds_wording/{NAME.format(seed)}.jsonl"],
                         capture_output=True, text=True, check=True).stdout
    return 1 - float(re.search(r"consistency ([0-9.]+)", out).group(1))


ap = argparse.ArgumentParser()
ap.add_argument("--seeds", default="1")
ap.add_argument("--prefix", default="e23")
a = ap.parse_args()
seeds = [int(s) for s in a.seeds.split(",")]
PREFIX = a.prefix
NAME = {"e23": "e23-xl-groups-s{}", "e22": "e22-xl-skills3-s{}"}[PREFIX]
subprocess.run([sys.executable, "-m", "kodiak_s1.eval.run", "report"] + [f"reports/preds_v02/{NAME.format(s)}.jsonl" for s in seeds]
               + ["--out", "reports/e23-verdict-tmp.md"], check=True, capture_output=True)
reps = list(json.load(open("reports/e23-verdict-tmp.json")).values())
vals = {g[0]: [r[g[1][0]][g[1][1]] for r in reps] for g in GUARDS if g[1]}
vals["real-anchor score"] = [anchor(s) for s in seeds]
vals["wording-trap eval"] = [trap(s) for s in seeds]
vals["flip rate (shortcut guard)"] = [flip(s) for s in seeds]
vals["policy contrastive pairs (shortcut guard)"] = [S.mean(pairs(f"reports/preds_contrastive/{PREFIX}-s{s}.jsonl", ("policy_violation",)))
                                                     for s in seeds]
tg = [target(s) for s in seeds]
lines, stop, fail = [f"contrastive pair accuracy, step safety + refund, both tests: {', '.join(f'{x:.3f}' for x in tg)} → mean "
                     f"{S.mean(tg):.3f} (keep ≥ {KEEP}; v0.3 mean 0.302)"], False, False
if len(seeds) == 1:
    if tg[0] <= BASE_S1:
        stop = True
        lines.append(f"  STOP: no target gain over v0.3 seed 1 ({BASE_S1})")
else:
    fail |= S.mean(tg) < KEEP
for name, _, line3, line1, up in GUARDS:
    v = vals[name]
    ok = (lambda x, l: x >= l) if up else (lambda x, l: x <= l)
    sign = "≥" if up else "≤"
    if len(seeds) == 1:
        bad = not ok(v[0], line1)
        stop |= bad
        lines.append(f"{name}: {v[0]:.3f} (single-run reject only past {line1}) {'STOP' if bad else 'ok'}")
    else:
        bad = not ok(S.mean(v), line3)
        fail |= bad
        lines.append(f"{name}: {', '.join(f'{x:.3f}' for x in v)} → mean {S.mean(v):.3f} (line {sign} {line3}) {'FAIL' if bad else 'ok'}")
print("\n".join(lines))
if len(seeds) == 1:
    print("SEED 1: continue to seeds 0 and 2" if not stop else "SEED 1: stop (rule in the proposal)")
    sys.exit(3 if stop else 0)
print("VERDICT: " + ("KILL" if fail else "KEEP") + " (3-seed means vs the pre-set lines)")
