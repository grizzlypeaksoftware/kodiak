"""Build the small, frozen Kodiak eval set from processed test splits (+ reviewed synthetic data).

    uv run python -m kodiak_s1.data.evalset --processed data/processed --out data/eval/kodiak-eval-v0.1.jsonl

Slices (every example carries an `eval:*` tag):
  eval:indomain     test rows of trained-on sources
  eval:heldout      sources never trained on (zero-shot)
  eval:null_construct  null:mismatch and null:gold_removed built from test rows
  eval:synthetic    teacher-generated, human-reviewed examples (only if --synthetic is given)

All examples fit the v0.1 limits (state <= 2048 tokens, packed <= 4096). States that
appear in any training shard are excluded.
"""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path

from kodiak_s1.data.augment import gold_removed, mismatch
from kodiak_s1.data.build import state_key
from kodiak_s1.data.sources import SOURCES, rng_for
from kodiak_s1.schema import Example, render_state
from kodiak_s1.tokenizer import packed_lengths

MAX_STATE, MAX_TOTAL = 2048, 4096


def read_jsonl(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def fits(ex: dict) -> bool:
    s, t = packed_lengths(render_state(ex["state"]), ex["questions"])
    return s <= MAX_STATE and t <= MAX_TOTAL


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--processed", default="data/processed")
    ap.add_argument("--synthetic", default=None, help="reviewed synthetic eval JSONL (examples with review=ok)")
    ap.add_argument("--out", default="data/eval/kodiak-eval-v0.1.jsonl")
    ap.add_argument("--per-indomain", type=int, default=100)
    ap.add_argument("--per-heldout", type=int, default=250)
    ap.add_argument("--n-mismatch", type=int, default=150)
    ap.add_argument("--n-gold-removed", type=int, default=150)
    a = ap.parse_args(argv)
    proc = Path(a.processed)

    train_states: set[int] = set()
    for p in proc.glob("*/train.jsonl.gz"):
        train_states.update(state_key(ex) for ex in read_jsonl(p))

    out: list[dict] = []
    pools: dict[str, list[dict]] = {}
    for sid, src in SOURCES.items():
        p = proc / sid / "test.jsonl.gz"
        if not p.exists():
            print(f"skip {sid}: no test split")
            continue
        rows = [ex for ex in read_jsonl(p) if state_key(ex) not in train_states and fits(ex)]
        rng_for("eval", sid).shuffle(rows)
        n = a.per_heldout if src.heldout else a.per_indomain
        take = rows[:n]
        for ex in take:
            ex["meta"]["split"] = "test"
            ex["meta"]["tags"] = sorted(set(ex["meta"]["tags"]) | {"eval:heldout" if src.heldout else "eval:indomain"})
        out += take
        pools[sid] = rows[n:]  # unused test rows feed the null constructions, so slices don't share examples

    # Null constructions from in-domain test rows not already used above.
    rng = rng_for("eval", "null")
    donors = [ex for ex in pools.get("mnli", []) + pools.get("scitail", []) if ex["questions"][0]["id"] == "claim"]
    hosts = [ex for sid, rows in pools.items() if not SOURCES[sid].heldout and sid not in ("mnli", "scitail") for ex in rows]
    rng.shuffle(hosts)
    made = 0
    for host in hosts:
        if made >= a.n_mismatch or not donors:
            break
        ex = mismatch(host, rng.choice(donors), rng)
        if ex and fits(ex):
            ex["meta"]["tags"] = sorted(set(ex["meta"]["tags"]) | {"eval:null_construct"})
            out.append(ex)
            made += 1
    made = 0
    gr_hosts = [(sid, ex) for sid, rows in pools.items() if not SOURCES[sid].heldout for ex in rows]
    rng.shuffle(gr_hosts)
    for sid, host in gr_hosts:
        if made >= a.n_gold_removed:
            break
        ex = gold_removed(host, SOURCES[sid].family, rng)
        if ex and fits(ex):
            ex["meta"]["tags"] = sorted(set(ex["meta"]["tags"]) | {"eval:null_construct"})
            out.append(ex)
            made += 1

    if a.synthetic:
        for rec in read_jsonl(Path(a.synthetic)):  # exported from tools/review.html
            if rec.get("review") != "ok":
                continue
            ex = rec["example"]
            ok = {qid for qid, v in rec["question_reviews"].items() if v == "ok"}
            ex["questions"] = [q for q in ex["questions"] if q["id"] in ok]
            ex["answers"] = {k: v for k, v in ex["answers"].items() if k in ok}
            if ex["questions"] and fits(ex):
                ex["meta"]["split"] = "test"
                ex["meta"]["tags"] = sorted(set(ex["meta"]["tags"]) | {"eval:synthetic"})
                out.append(ex)

    for ex in out:
        Example.model_validate(ex)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for ex in out:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    by_slice = Counter(t for ex in out for t in ex["meta"]["tags"] if t.startswith("eval:"))
    by_source = Counter(ex["meta"]["source"] for ex in out)
    nulls = Counter(t for ex in out for t in ex["meta"]["tags"] if t.startswith("null:"))
    n_q = sum(len(ex["questions"]) for ex in out)
    stats = {"examples": len(out), "questions": n_q, "slices": dict(by_slice), "null_types": dict(nulls),
             "sources": dict(sorted(by_source.items()))}
    Path(a.out).with_suffix(".stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
