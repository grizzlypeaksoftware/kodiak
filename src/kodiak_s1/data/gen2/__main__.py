"""Generator v2 command line (design: docs/GENERATOR_V2.md).

    uv run python -m kodiak_s1.data.gen2 taxonomy                       # generate data/gen2/taxonomy_v2.json (once)
    uv run python -m kodiak_s1.data.gen2 show --seed 8 --n 8            # taxonomy summary + sample specs
    uv run python -m kodiak_s1.data.gen2 run --n 50 --seed 8 --workers 16 --out data/synthetic/pilot_gen2.jsonl --max-usd 1
    uv run python -m kodiak_s1.data.gen2 queue --in data/synthetic/pilot_gen2.jsonl --n 50 --out data/gen2/review_queue.jsonl
    uv run python -m kodiak_s1.data.gen2 stats --in data/synthetic/pilot_gen2.jsonl   # yield, mix, cost
    uv run python -m kodiak_s1.data.gen2 coverage                       # refresh data/gen2/coverage.json

Seeds: 6 = training data, 7 = eval candidates (human review; never train on them), 8 = pilots.
File names: training output data/synthetic/gen2_*.jsonl (counted in the coverage map); pilots pilot_gen2_*; eval eval_gen2_*.
`run` is resumable (finished job ids are skipped; "retry" jobs rerun) and stops cleanly at --max-usd.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from kodiak_s1.data.gen2 import taxonomy
from kodiak_s1.data.gen2.dedupe import NearDupIndex, example_text
from kodiak_s1.data.gen2.pipeline import CHECKER, DEFAULT_PRICES, WRITER, cost, review_queue, run_job
from kodiak_s1.data.gen2.specs import coverage_from_records, sample_spec

COVERAGE_PATH = Path("data/gen2/coverage.json")
TRAIN_GLOB = "data/synthetic/gen2_*.jsonl"
V1_FILES = ["data/synthetic/synth_v1.jsonl", "data/synthetic/synth_v1_cloud.jsonl"]


def load_prices() -> dict:
    prices = dict(DEFAULT_PRICES)
    try:
        cfg = json.loads(Path("docs/progress.json").read_text())
        prices.update({k: tuple(v) for k, v in cfg.get("synthetic", {}).get("prices_per_million", {}).items()})
    except (OSError, json.JSONDecodeError):
        pass
    return prices


def cmd_taxonomy(a) -> None:
    out = Path(a.out)
    if out.exists() and not a.force:
        sys.exit(f"{out} exists (it is versioned); pass --force to regenerate")
    tax = taxonomy.generate(a.model, a.domains)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(tax, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(taxonomy.summary(tax))


def cmd_show(a) -> None:
    tax = taxonomy.load(a.taxonomy)
    print(taxonomy.summary(tax), "\n")
    for s in tax["sectors"]:
        d = s["domains"][0] if s["domains"] else None
        if d:
            print(f"- {s['name']} -> {d['name']}: " + "; ".join(f"{dt['name']} [{'/'.join(dt['formats'])}]" for dt in d["doc_types"]))
    print()
    for i in range(a.n):
        s = sample_spec(i, a.seed, tax, focus=a.focus or None)
        where = "real FineWeb passage" if s.source == "grounded" else f"{s.domain} / {s.doc_type} ({s.format})"
        print(f"job {i} [{s.mode}] {where} | focus {s.decision}, {s.difficulty} | {s.n_choice} choice + {s.n_score} score, "
              f"{s.n_inference} inferred, {s.n_null} null {s.null_kinds} {s.scales} {s.targets}{' +twin' if s.pair else ''}")


def cmd_run(a) -> None:
    tax = taxonomy.load(a.taxonomy)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # The coverage snapshot is frozen per output file, so specs stay deterministic across resumes.
    snap = out.with_suffix(".coverage.json")
    if snap.exists():
        coverage = json.loads(snap.read_text())
    else:
        coverage = json.loads(COVERAGE_PATH.read_text()) if COVERAGE_PATH.exists() else {}
        snap.write_text(json.dumps(coverage, indent=1) + "\n")
    prices = load_prices()
    critics = [c for c in a.critics.split(",") if c]

    index = NearDupIndex(a.dedupe_threshold)
    against = [p for p in (a.against.split(",") if a.against else V1_FILES + sorted(glob.glob(TRAIN_GLOB))) if p]
    for p in dict.fromkeys(against):
        if Path(p).exists() and Path(p).resolve() != out.resolve():
            for line in open(p, encoding="utf-8"):
                r = json.loads(line)
                if r.get("status") == "ok":
                    index.add(f"{p}:{r['job']}", example_text(r["example"]))
    done, spent = set(), 0.0
    if out.exists():
        for line in out.open(encoding="utf-8"):
            r = json.loads(line)
            spent += cost(r, prices)
            if r.get("status") != "retry":
                done.add(r["job"])
            if r.get("status") == "ok":
                index.add(f"{out}:{r['job']}", example_text(r["example"]))
    todo = [i for i in range(a.start, a.start + a.n) if i not in done]
    print(f"{len(done)} jobs already done (${spent:.2f} spent); {len(todo)} to run with {a.workers} workers; "
          f"dedupe index {len(index)} examples; budget ${a.max_usd:.2f}", flush=True)
    lock, stats, t0 = threading.Lock(), {}, time.time()
    state = {"spent": spent, "stopped": False}

    def work(i: int) -> None:
        with lock:
            if state["spent"] >= a.max_usd:
                state["stopped"] = True
                return
        rec = run_job(i, a.seed, tax, coverage, a.writer, a.verifier, critics, a.focus or None)
        with lock:
            if rec["status"] == "ok":
                dup = index.check_add(f"{out}:{i}", example_text(rec["example"]))
                if dup:
                    rec.update(status="near_duplicate", dup_of=dup[0], dup_sim=round(dup[1], 3))
            state["spent"] += cost(rec, prices)
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats[rec["status"]] = stats.get(rec["status"], 0) + 1
            n = sum(stats.values())
            if n % 10 == 0 or n == len(todo):
                rate = n / (time.time() - t0) * 3600
                print(f"[{time.strftime('%H:%M:%S')}] {n}/{len(todo)} {stats} ~{rate:.0f} jobs/h ${state['spent']:.2f}",
                      flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, todo))
    if out.name.startswith("gen2_"):
        COVERAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        COVERAGE_PATH.write_text(json.dumps(coverage_from_records(sorted(glob.glob(TRAIN_GLOB))), indent=1) + "\n")
    print(f"done: {stats}, ${state['spent']:.2f} spent in total", flush=True)
    if state["stopped"]:
        sys.exit(f"budget cap ${a.max_usd:.2f} reached; raise --max-usd and rerun the same command to continue")
    if stats.get("retry"):
        sys.exit(f"{stats['retry']} jobs need retry; rerun the same command")


def cmd_queue(a) -> None:
    q = review_queue(a.inp.split(","), a.n, a.seed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in q:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(q)} disagreement jobs to {a.out} (open it in tools/review.html)")


def stats(recs: list[dict], prices: dict) -> dict:
    """Pilot health: yield, question mix, where the checker disagrees, and cost."""
    from collections import Counter

    done = [r for r in recs if r.get("status") != "retry"]
    ok = [r for r in done if r["status"] == "ok"]
    kept_basis = Counter(b for r in ok for b in r.get("basis", {}).values())
    asked, disputed = Counter(), Counter()
    for r in done:
        ids = {d["id"] for d in r.get("disagreements", [])}
        for qid, b in (r.get("q_basis") or {}).items():
            if "disagreements" in r:
                asked[b] += 1
                disputed[b] += qid in ids
    n_q = sum(kept_basis.values())
    usd = sum(cost(r, prices) for r in recs)
    return {
        "jobs": len(done), "status": dict(Counter(r["status"] for r in done)),
        "yield": round(len(ok) / max(1, len(done)), 3),
        "grounded_share_kept": round(sum(r["spec"]["source"] == "grounded" for r in ok) / max(1, len(ok)), 3),
        "kept_questions": n_q, "kept_basis": dict(kept_basis),
        "inferred_share": round(kept_basis["inferred"] / max(1, n_q), 3),
        "null_share": round(kept_basis["unanswerable"] / max(1, n_q), 3),
        "disagree_rate_by_basis": {b: round(disputed[b] / asked[b], 3) for b in asked},
        "drops": dict(Counter(d for r in done for d in r.get("drops", []))),
        "errors": dict(Counter((r.get("error") or "")[:60] for r in done if r["status"] == "error")),
        "usd": round(usd, 4), "usd_per_1k_jobs": round(usd / max(1, len(done)) * 1000, 2),
        "usd_per_1k_kept": round(usd / max(1, len(ok)) * 1000, 2),
    }


def cmd_stats(a) -> None:
    recs = [json.loads(line) for p in a.inp.split(",") for line in open(p, encoding="utf-8")]
    print(json.dumps(stats(recs, load_prices()), indent=1))


def cmd_coverage(a) -> None:
    files = a.inp.split(",") if a.inp else sorted(glob.glob(TRAIN_GLOB))
    cov = coverage_from_records(files)
    COVERAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_PATH.write_text(json.dumps(cov, indent=1) + "\n")
    print(json.dumps({k: dict(sorted(v.items(), key=lambda t: -t[1])[:8]) for k, v in cov.items()}, indent=1))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("taxonomy", help="generate the taxonomy with the writer model")
    t.add_argument("--model", default=WRITER)
    t.add_argument("--domains", type=int, default=20, help="domains per sector")
    t.add_argument("--out", default=str(taxonomy.TAXONOMY_PATH))
    t.add_argument("--force", action="store_true")
    s = sub.add_parser("show", help="taxonomy summary and sample specs")
    s.add_argument("--taxonomy", default=str(taxonomy.TAXONOMY_PATH))
    s.add_argument("--seed", type=int, default=8)
    s.add_argument("--n", type=int, default=10)
    s.add_argument("--focus", default="")
    r = sub.add_parser("run", help="generate examples")
    r.add_argument("--n", type=int, default=50, help="number of jobs (job ids start..start+n-1)")
    r.add_argument("--start", type=int, default=0)
    r.add_argument("--seed", type=int, default=8)
    r.add_argument("--workers", type=int, default=16)
    r.add_argument("--writer", default=WRITER)
    r.add_argument("--verifier", default=CHECKER)
    r.add_argument("--taxonomy", default=str(taxonomy.TAXONOMY_PATH))
    r.add_argument("--out", required=True)
    r.add_argument("--max-usd", type=float, default=5.0, help="stop cleanly once this much has been spent (whole file)")
    r.add_argument("--against", default="", help="comma-separated files to dedupe against (default: v1 + gen2 training files)")
    r.add_argument("--dedupe-threshold", type=float, default=0.8)
    r.add_argument("--focus", default="", help="'scores' = Stage 3: anchored judgment scores with target bands and contrast twins")
    r.add_argument("--critics", default="", help="comma-separated critic models (e.g. do:deepseek-3.2,do:openai-gpt-oss-120b); "
                   "a kept question any critic calls wrong/ambiguous is dropped")
    q = sub.add_parser("queue", help="build a human review queue from writer/checker disagreements")
    q.add_argument("--in", dest="inp", required=True)
    q.add_argument("--n", type=int, default=50)
    q.add_argument("--seed", type=int, default=0)
    q.add_argument("--out", default="data/gen2/review_queue.jsonl")
    st = sub.add_parser("stats", help="yield, question mix, disagreement by basis, cost")
    st.add_argument("--in", dest="inp", required=True)
    c = sub.add_parser("coverage", help="recompute the coverage map")
    c.add_argument("--in", dest="inp", default="")
    a = ap.parse_args(argv)
    {"taxonomy": cmd_taxonomy, "show": cmd_show, "run": cmd_run, "queue": cmd_queue, "stats": cmd_stats,
     "coverage": cmd_coverage}[a.cmd](a)


if __name__ == "__main__":
    main()
