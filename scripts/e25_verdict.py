"""E25 verdict (docs/experiments/E25-task-variety.md, rules written before the run).
    uv run python scripts/e25_verdict.py                                   # arms A7, B7, all28m, all28
    uv run python scripts/e25_verdict.py --names v04-s0,v04-s1,v04-s2,v04-s0 --v02 e22-xl-skills3-s0   # test of this script on old files
"""
import argparse
import json
import re
import statistics as S
import subprocess
import sys

sys.path.insert(0, "scripts")
from newdomain_score import score  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--names", default="e25-A7,e25-B7,e25-all28m,e25-all28")
ap.add_argument("--v02", default="")
a = ap.parse_args()
names = a.names.split(",")
labels = ["A7 (7 kinds)", "B7 (7 kinds)", "all28-matched (28 kinds, same data)", "all28-full (28 kinds, all data)"]
nd = {}
for n in names:
    sk, sl, _, _ = score(f"reports/preds_newdomain/{n}.jsonl")
    nd[n] = (S.mean(v for t, v in sk.items() if sl[t] == "read"), S.mean(v for t, v in sk.items() if sl[t] == "knowledge"), sk, sl)


def v02(n):
    f = f"reports/preds_v02/{a.v02 or n}.jsonl"
    try:
        subprocess.run([sys.executable, "-m", "kodiak_s1.eval.run", "report", f, "--out", "reports/e25-verdict-tmp.md"], check=True, capture_output=True)
        r = list(json.load(open("reports/e25-verdict-tmp.json")).values())[0]
        return r["eval:heldout"]["forced_accuracy"], r["eval:indomain"]["accuracy"]
    except Exception:
        return None, None


def flip(n):
    try:
        out = subprocess.run([sys.executable, "scripts/wording_score.py", f"reports/preds_wording/{n}.jsonl"], capture_output=True, text=True).stdout
        return 1 - float(re.search(r"consistency ([0-9.]+)", out).group(1))
    except Exception:
        return None


f = lambda x: "–" if x is None else f"{x:.3f}"
print("# E25 result: task variety at matched data (lines set before the run)\n")
print("| Arm | New-domains read slice (headline) | Knowledge slice | Never-seen forced (eval v0.2) | Familiar | Flip rate |")
print("|---|---|---|---|---|---|")
for n, lab in zip(names, labels):
    ns, fam = v02(n)
    print(f"| {lab} | **{nd[n][0]:.3f}** | {nd[n][1]:.3f} | {f(ns)} | {f(fam)} | {f(flip(n))} |")
a7, b7, m28, full = (nd[n][0] for n in names)
mean7 = (a7 + b7) / 2
gain = m28 - mean7
if m28 >= mean7 + 0.03 and m28 > a7 and m28 > b7:
    verdict = "VARIETY HELPS (keep): all28-matched beats both 7-kind runs and their mean by at least 0.03"
elif m28 < mean7 + 0.01:
    verdict = "VARIETY DOESN'T HELP at this scale (kill): all28-matched is less than 0.01 above the 7-kind mean"
else:
    verdict = "INCONCLUSIVE: between the lines"
print(f"\nall28-matched {m28:.3f} vs 7-kind mean {mean7:.3f} (A7 {a7:.3f}, B7 {b7:.3f}): gain {gain:+.3f}; keep line +0.030, kill below +0.010")
print(f"More data at 28 kinds (report only): all28-full {full:.3f} vs all28-matched {m28:.3f}: {full - m28:+.3f}")
print(f"\nVERDICT: {verdict}\n")
print("## New-domains test by task (report only)\n")
print("| Task | slice | " + " | ".join(labels) + " |")
print("|---|---|" + "---|" * len(names))
sk0, sl0 = nd[names[0]][2], nd[names[0]][3]
for t in sorted(sk0, key=lambda t: (sl0[t] != "read", t)):
    print(f"| {t} | {sl0[t]} | " + " | ".join(f"{nd[n][2][t]:+.3f}" for n in names) + " |")
