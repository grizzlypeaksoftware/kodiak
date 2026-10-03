"""E18: the held-out wording eval. Never-seen eval v0.2 questions, each asked three ways: the original options, a one-sentence description
of each option, and a short paraphrase (data/wordings/eval.json: written for eval tasks only, checker-verified, never trained on).
Only questions whose every option has both rewordings are used. Writes the eval file and a spot-check page.
    uv run python scripts/build_wording_eval.py"""
import copy
import json
import random
from collections import Counter
from pathlib import Path

EVAL, TABLE = Path("data/eval/kodiak-eval-v0.2.jsonl"), Path("data/wordings/eval.json")
OUT, REPORT = Path("data/eval/kodiak-wording-eval-v0.1.jsonl"), Path("reports/wording-eval-review.md")
STYLES = ("original", "description", "paraphrase")
PER_SOURCE = 80  # so no single task (ethics: 400 yes/no questions) dominates

table = json.loads(TABLE.read_text())["table"]
rows, per_source, n_q = [], Counter(), 0
for i, line in enumerate(EVAL.open()):
    ex = json.loads(line)
    if "eval:heldout" not in ex["meta"]["tags"]:
        continue
    t = table.get(ex["meta"]["source"], {})
    qs = [q for q in ex["questions"] if q["type"] == "choice" and all(len(t.get(lab["text"], {})) == 2 for lab in q["labels"])]
    if not qs or per_source[ex["meta"]["source"]] >= PER_SOURCE:
        continue
    for style in STYLES:
        v = copy.deepcopy(ex)
        v["questions"] = copy.deepcopy(qs)
        v["answers"] = {q["id"]: ex["answers"][q["id"]] for q in qs if q["id"] in ex["answers"]}
        if style != "original":
            for q in v["questions"]:
                for lab in q["labels"]:
                    lab["text"] = t[lab["text"]][style]
        v["meta"] = {**ex["meta"], "tags": ex["meta"]["tags"] + ["eval:wording", f"wording:{style}", f"wgroup:{i}"]}
        rows.append(v)
    per_source[ex["meta"]["source"]] += 1
    n_q += len(qs)
with OUT.open("w", encoding="utf-8") as f:
    for v in rows:
        f.write(json.dumps(v, ensure_ascii=False) + "\n")

md = ["# Wording eval v0.1: spot-check (E18)", "",
      f"{n_q} never-seen questions ({sum(per_source.values())} examples) from eval v0.2, each asked with three wordings of the same options. "
      "Per source: " + ", ".join(f"{k} {v}" for k, v in per_source.most_common()) + ".", "",
      "**Check: does each rewording mean the same as the original, and is it still clearly different from the other options?** Every "
      "rewording used in the eval is listed below.", ""]
for sid in per_source:
    md += [f"## {sid}", "", "| Original | Description | Paraphrase |", "|---|---|---|"]
    for orig, w in sorted(table[sid].items()):
        if len(w) == 2:
            md.append(f"| {orig} | {w['description']} | {w['paraphrase']} |")
    md.append("")
ex = random.Random(1).choice([r for r in rows if "wording:original" in r["meta"]["tags"]])
md += ["## One question, three ways", ""]
for v in rows:
    if v["meta"]["tags"][-1] == ex["meta"]["tags"][-1]:
        q = v["questions"][0]
        md.append(f"- **{v['meta']['tags'][-2]}**: {q['text'][:150]} → " + " / ".join(lab["text"] for lab in q["labels"]))
REPORT.write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"{n_q} questions x 3 wordings = {len(rows)} examples -> {OUT}; per source {dict(per_source)}")
