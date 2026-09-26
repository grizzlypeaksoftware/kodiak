"""Eval set v0.2 = v0.1 (unchanged) + 8 new held-out sources (D30).

    uv run python -m kodiak_s1.data.evalset_v02

v0.1 held out only 4 tasks (1,000 questions), and one of them (jailbreak) swings ±10 points between identical training runs,
so held-out results were too noisy to steer by. v0.2 adds up to 400 examples from each new never-trained-on source. Tags:
  eval:heldout      all held-out examples (old + new)
  eval:heldout_v01  the original four held-out tasks (so v0.1 numbers stay comparable)
  eval:heldout_v02  the new sources only
Everything else in v0.1 is copied verbatim. Frozen once written: never train or tune on it.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from kodiak_s1.data.build import state_key
from kodiak_s1.data.evalset import fits, read_jsonl
from kodiak_s1.data.sources import SOURCES, rng_for
from kodiak_s1.schema import Example

NEW = ["contract_nli", "ethics_commonsense", "fin_tweets_topic", "fin_tweets_sentiment", "arxiv_field", "casehold",
       "clickbait17", "poem_sentiment"]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="data/eval/kodiak-eval-v0.1.jsonl")
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--per-source", type=int, default=400)
    ap.add_argument("--out", default="data/eval/kodiak-eval-v0.2.jsonl")
    a = ap.parse_args(argv)
    if Path(a.out).exists():
        raise SystemExit(f"{a.out} exists and is frozen; delete it deliberately if you really mean to rebuild")
    proc = Path(a.processed)
    out = read_jsonl(Path(a.base))
    for ex in out:
        if "eval:heldout" in ex["meta"]["tags"]:
            ex["meta"]["tags"] = sorted(set(ex["meta"]["tags"]) | {"eval:heldout_v01"})
    train_states: set[int] = set()
    for p in proc.glob("*/train.jsonl.gz"):
        train_states.update(state_key(ex) for ex in read_jsonl(p))
    seen = {state_key(ex) for ex in out}
    for sid in NEW:
        assert SOURCES[sid].heldout, sid
        rows = [ex for ex in read_jsonl(proc / sid / "test.jsonl.gz")
                if state_key(ex) not in train_states and state_key(ex) not in seen and fits(ex)]
        rng_for("eval-v02", sid).shuffle(rows)
        for ex in rows[: a.per_source]:
            ex["meta"]["split"] = "test"
            ex["meta"]["tags"] = sorted(set(ex["meta"]["tags"]) | {"eval:heldout", "eval:heldout_v02"})
            seen.add(state_key(ex))
            out.append(ex)
    for ex in out:
        Example.model_validate(ex)
    with open(a.out, "w", encoding="utf-8") as f:
        for ex in out:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    stats = {"examples": len(out), "questions": sum(len(ex["questions"]) for ex in out),
             "slices": dict(Counter(t for ex in out for t in ex["meta"]["tags"] if t.startswith("eval:"))),
             "sources": dict(sorted(Counter(ex["meta"]["source"] for ex in out).items())), "based_on": a.base}
    Path(a.out).with_suffix(".stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
