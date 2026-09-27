"""Cascade simulation (STRATEGY §5, D37): Kodiak answers when its confidence clears a threshold, otherwise the question goes to an LLM.
Uses existing eval v0.2 predictions only (no new runs). Choice questions with a gold label; "correct" = the system's top label (forced).

    uv run python scripts/cascade_sim.py --kodiak large-v2-s0 --llm llm-qwen3-8b > reports/v02-cascade.md
"""
import argparse
import json

ap = argparse.ArgumentParser()
ap.add_argument("--kodiak", default="large-v2-s0")
ap.add_argument("--llm", default="llm-qwen3-8b")
ap.add_argument("--dir", default="reports/preds_v02")
a = ap.parse_args()


def load(name):
    out = {}
    for line in open(f"{a.dir}/{name}.jsonl"):
        r = json.loads(line)
        if "ex" in r and r["type"] == "choice" and "label" in r["gold"]:
            out[(r["ex"], r["qid"])] = r
    return out


K, L = load(a.kodiak), load(a.llm)
keys = [k for k in K if k in L]
top = lambda r: max(r["probs"], key=r["probs"].get) if r["probs"] else None  # noqa: E731


def row(sub, t):
    n = len(sub)
    esc = [k for k in sub if max(K[k]["probs"].values()) < t]
    esc_set = set(esc)
    correct = sum((top(L[k]) if k in esc_set else top(K[k])) == K[k]["gold"]["label"] for k in sub)
    return len(esc) / n, correct / n


slices = {"all": keys, "never-seen": [k for k in keys if "eval:heldout" in K[k]["tags"]],
          "familiar": [k for k in keys if "eval:indomain" in K[k]["tags"]]}
print(f"# Cascade: {a.kodiak} first, {a.llm} when Kodiak's top probability < t\n")
print("Eval v0.2, choice questions with a gold label; accuracy = top label (forced). t = 0 is Kodiak alone, t > 1 is the LLM alone.\n")
for name, sub in slices.items():
    print(f"## {name} ({len(sub)} questions)\n\n| t | sent to LLM | accuracy |\n|---|---|---|")
    for t in [0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.01]:
        e, acc = row(sub, t)
        label = "Kodiak only" if t == 0 else "LLM only" if t > 1 else f"{t:.2f}"
        print(f"| {label} | {e:.0%} | {acc:.3f} |")
    print()
