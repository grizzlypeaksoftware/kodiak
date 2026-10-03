"""E17: build the held-out skills eval (seed 7, never trained on) and a spot-check page for Shane.

    uv run python scripts/build_skills_eval.py
Takes 100 kept examples per skill, spread across the target answers as evenly as the pool allows (round-robin, fixed order).
"""
import json
import random
from collections import defaultdict
from pathlib import Path

from kodiak_s1.data.sim.skills import tool_spec

# grounding/claims from the first generation; tools regenerated with skills-v1.1 and relevance with v1.2 (varied "answer directly" messages, listings whose
# details match their title, no leaked field names), found while preparing this spot-check.
RAW = {"grounding": "data/synthetic/skills_eval_raw.jsonl", "claims": "data/synthetic/skills_eval_raw.jsonl",
       "tools": "data/synthetic/skills_eval_raw_v11.jsonl", "relevance": "data/synthetic/skills_eval_raw_v12.jsonl"}
OUT, REPORT = Path("data/eval/kodiak-skills-eval-v0.1.jsonl"), Path("reports/skills-eval-review.md")
PER_KIND, SHOW = 100, 10

last = {}
for kind, path in RAW.items():
    for line in Path(path).open():
        r = json.loads(line)
        if r["kind"] == kind:
            last[(r["job"], r["kind"])] = r
pools = defaultdict(lambda: defaultdict(list))
for r in last.values():
    if r["status"] == "ok":
        pools[r["kind"]][r["case"]["target"]].append(r)

def show(state, cap=1500):
    """Long passages are shortened (middle cut) so the claim/response after them stays visible."""
    def cut(v):
        return v if not isinstance(v, str) or len(v) <= cap else v[:cap // 2] + " [...] " + v[-cap // 2:]
    if isinstance(state, dict):
        state = {k: cut(v) for k, v in state.items()}
    return json.dumps(cut(state), ensure_ascii=False, indent=1)


rng, picked = random.Random(7), {}
for kind, by_target in sorted(pools.items()):
    for rows in by_target.values():
        rng.shuffle(rows)
    out, targets = [], sorted(by_target)
    while len(out) < PER_KIND and any(by_target[t] for t in targets):
        for t in targets:
            if by_target[t] and len(out) < PER_KIND:
                out.append(by_target[t].pop())
    picked[kind] = out

with OUT.open("w", encoding="utf-8") as f:
    for kind, rows in picked.items():
        for r in rows:
            ex = r["example"]
            if kind == "tools":  # same normalization the generator now applies (duplicate top-level "required" removed)
                ex["state"]["available_tools"] = [tool_spec(t) for t in ex["state"]["available_tools"]]
            ex["meta"] = {**ex["meta"], "split": "test", "tags": ex["meta"]["tags"] + ["eval:skills"]}
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

md = ["# Skills eval v0.1: spot-check (E17)", "",
      f"Held-out test for E17: {PER_KIND} examples per skill from the seed-7 generators, never trained on. Below are {SHOW} random examples per "
      "skill with the answer the generator built toward and the checker confirmed. **Check: is the marked answer right?** Note any job number "
      "that looks wrong.", ""]
for kind, rows in picked.items():
    counts = defaultdict(int)
    for r in rows:
        counts[r["case"]["target"]] += 1
    md += [f"## {kind} ({len(rows)} examples: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + ")", ""]
    for r in random.Random(1).sample(rows, SHOW):
        ex = r["example"]
        md += [f"### job {r['job']} (target: {r['case']['target']})", "", "```", show(ex["state"]), "```", ""]
        for q in ex["questions"]:
            gold = ex["answers"].get(q["id"], {}).get("label")
            opts = "; ".join(("**" + l["text"] + "** ✓" if l["id"] == gold else l["text"]) for l in q["labels"])
            md += [f"- **{q['text']}** {opts}"]
        md += [""]
REPORT.write_text("\n".join(md), encoding="utf-8")
print({k: len(v) for k, v in picked.items()}, "->", OUT, REPORT)
