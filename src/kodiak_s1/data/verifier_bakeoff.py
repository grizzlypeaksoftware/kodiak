"""Compare candidate verifier models against human review (data/eval/synthetic_reviewed_v0.1.jsonl).

For every human-reviewed synthetic question we know the teacher's answer and whether a human judged it correct.
A good verifier *agrees* with the teacher on human-approved answers (keeps good data) and *disagrees* on
human-rejected ones (filters bad data).

    uv run python -m kodiak_s1.data.verifier_bakeoff --models qwen3.8:27b do:openai-gpt-oss-120b do:deepseek-3.2

Caveat: these examples were originally *selected* by agreement with qwen3.8:27b, so that model's numbers here are
biased (it agreed with every one of them, including the three a human later rejected). Compare the other models to each other.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor

from kodiak_s1.data.synth import agree, parse_verdict, teacher, verify_prompt, verify_schema
from kodiak_s1.schema import render_state

REVIEWED = "data/eval/synthetic_reviewed_v0.1.jsonl"


def run_model(model: str, recs: list[dict], workers: int) -> dict:
    def one(rec):
        ex = rec["example"]
        t = time.perf_counter()
        try:
            v = teacher(verify_prompt(render_state(ex["state"]), ex["questions"]), verify_schema(ex["questions"]), 0.0,
                        model, 400 + 250 * len(ex["questions"]))
            content, err = v["content"], None
            toks = (v.get("prompt_tokens") or 0, v.get("tokens") or 0)
        except Exception as e:  # noqa: BLE001 - record and continue
            content, err, toks = {}, f"{type(e).__name__}: {str(e)[:120]}", (0, 0)
        out = []
        for q in ex["questions"]:
            verdict = parse_verdict(q, content.get(q["id"]))
            ok, _ = agree(q, ex["answers"][q["id"]], verdict)
            out.append({"human": rec["question_reviews"].get(q["id"]), "agree": ok, "parsed": verdict is not None})
        return out, err, time.perf_counter() - t, toks

    with ThreadPoolExecutor(workers) as pool:
        results = list(pool.map(one, recs))
    qs = [q for out, _, _, _ in results for q in out]
    good = [q for q in qs if q["human"] == "ok"]
    bad = [q for q in qs if q["human"] == "wrong"]
    errors = [e for _, e, _, _ in results if e]
    return {
        "model": model,
        "keeps_good": sum(q["agree"] for q in good) / max(1, len(good)),
        "rejects_bad": sum(not q["agree"] for q in bad) / max(1, len(bad)),
        "n_good": len(good), "n_bad": len(bad),
        "unparsed": sum(not q["parsed"] for q in qs),
        "errors": len(errors), "first_error": errors[0] if errors else None,
        "sec_per_example": sum(t for _, _, t, _ in results) / len(results),
        "prompt_tokens": sum(p for _, _, _, (p, _) in results), "completion_tokens": sum(c for _, _, _, (_, c) in results),
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--reviewed", default=REVIEWED)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    recs = [json.loads(line) for line in open(a.reviewed)]
    recs = [r for r in recs if r.get("question_reviews")]
    rows = []
    for m in a.models:
        r = run_model(m, recs, 1 if not m.startswith("do:") else a.workers)
        rows.append(r)
        print(json.dumps(r), flush=True)
    print("\n| verifier | keeps human-approved | rejects human-rejected | unparsed | errors | s/example | tokens in/out |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['model']} | {r['keeps_good']:.0%} ({r['n_good']}) | {r['rejects_bad']:.0%} ({r['n_bad']}) | {r['unparsed']} | "
              f"{r['errors']} | {r['sec_per_example']:.1f} | {r['prompt_tokens']}/{r['completion_tokens']} |")


if __name__ == "__main__":
    main()
