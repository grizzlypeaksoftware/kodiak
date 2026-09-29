"""Smoke-test gate: is a short run keeping pace with the baseline run at the same step? (docs/GOAL.md)

    uv run python scripts/smoke_check.py runs/<new-run> runs/<baseline-run> [--step 500] [--tolerance 0.02]
Compares validation choice accuracy averaged over the tasks both runs evaluate, at the same step. Passes if the new run is no more than
`tolerance` behind; a full run is off otherwise. (Validation only: it never looks at the eval set.)
"""
import argparse
import json
import sys


def at_step(run: str, step: int) -> dict:
    for line in open(f"{run}/metrics.jsonl"):
        r = json.loads(line)
        if r.get("event") == "eval" and r["step"] == step:
            return {k: v["choice_acc"] for k, v in r.items() if isinstance(v, dict) and v.get("choice_acc")}
    sys.exit(f"{run}: no validation eval at step {step}")


ap = argparse.ArgumentParser()
ap.add_argument("new")
ap.add_argument("baseline")
ap.add_argument("--step", type=int, default=500)
ap.add_argument("--tolerance", type=float, default=0.02)
a = ap.parse_args()
new, base = at_step(a.new, a.step), at_step(a.baseline, a.step)
common = sorted(set(new) & set(base))
n, b = sum(new[k] for k in common) / len(common), sum(base[k] for k in common) / len(common)
print(f"step {a.step}, {len(common)} validation tasks: new {n:.3f} vs baseline {b:.3f} ({n - b:+.3f})")
worst = sorted(common, key=lambda k: new[k] - base[k])[:3]
print("  furthest behind:", ", ".join(f"{k} {new[k] - base[k]:+.3f}" for k in worst))
if n < b - a.tolerance:
    print(f"SMOKE FAIL: more than {a.tolerance} behind the baseline; don't launch the full run")
    sys.exit(1)
print("SMOKE PASS")
