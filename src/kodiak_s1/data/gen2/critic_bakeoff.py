"""Score candidate critic models against Shane's human review of the v2.0 eval candidates.

A good critic flags the questions the human rejected (recall) while keeping the ones the human approved (few false flags,
since each false flag throws away good data).

    uv run python -m kodiak_s1.data.gen2.critic_bakeoff --models do:deepseek-3.2,do:openai-gpt-oss-120b
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor

from kodiak_s1.data.gen2.critic import critique
from kodiak_s1.schema import render_state

REVIEWED = "data/eval/synthetic_reviewed_gen2_v0.1.jsonl"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="do:deepseek-3.2,do:openai-gpt-oss-120b")
    ap.add_argument("--reviewed", default=REVIEWED)
    ap.add_argument("--out", default="reports/critic-bakeoff.json")
    a = ap.parse_args(argv)
    recs = [json.loads(line) for line in open(a.reviewed, encoding="utf-8")]
    report = {}
    for model in a.models.split(","):
        def one(r):
            ex = r["example"]
            try:
                verdicts, _ = critique(render_state(ex["state"]), ex["questions"], ex["answers"], model)
            except (OSError, ValueError, KeyError) as e:
                print(f"  job {r['job']}: {type(e).__name__} {str(e)[:100]}", flush=True)
                verdicts = {q["id"]: "error" for q in ex["questions"]}
            return [(r["job"], q["id"], r["basis"][q["id"]], r["question_reviews"].get(q["id"]), verdicts[q["id"]])
                    for q in ex["questions"]]
        with ThreadPoolExecutor(16) as pool:
            rows = [x for rs in pool.map(one, recs) for x in rs]
        human_bad = [x for x in rows if x[3] == "wrong"]
        human_ok = [x for x in rows if x[3] == "ok"]
        flagged = lambda x: x[4] != "correct"
        kept = [x for x in rows if not flagged(x)]
        m = {"questions": len(rows),
             "caught_of_human_rejected": f"{sum(map(flagged, human_bad))}/{len(human_bad)}",
             "false_flags_of_human_ok": f"{sum(map(flagged, human_ok))}/{len(human_ok)}",
             "precision_before": round(len(human_ok) / max(1, len(human_ok) + len(human_bad)), 3),
             "precision_after": round(sum(x[3] == "ok" for x in kept) / max(1, len(kept)), 3),
             "kept_share": round(len(kept) / len(rows), 3),
             "missed": [x[:3] for x in human_bad if not flagged(x)],
             "false_flags": [x[:3] + (x[4],) for x in human_ok if flagged(x)]}
        report[model] = m
        print(model, json.dumps({k: v for k, v in m.items() if k not in ("false_flags",)}), flush=True)
    with open(a.out, "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
