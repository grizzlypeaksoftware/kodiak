"""D55 diagnosis: are the Decision Index swings between XL v2 and E17 real or seed noise?

Builds a fixed sample (up to 1,000 rows per benchmark, chosen by a hash of the row id) of the benchmarks that moved most, and turns
the two existing seed-1 full runs into results files on exactly those rows, so they can be scored next to the new seeds.
    uv run python scripts/di_diag.py sample      # -> ../decision-index/diag/rows.jsonl.gz
    uv run python scripts/di_diag.py subset RUN   # runs/RUN/results.jsonl -> diag/RUN-subset/results.jsonl
"""
import gzip
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

DI = Path.home() / "development/decision-index"
WANT = ["PhishNChips", "FinEntity", "BPoMP", "BANKING77", "VAST", "Humicroedit", "When2Call", "Amazon ESCI", "HoVer", "BFCL", "CLINC150",
        "ANLI"]
PER = 1000


def h(s):
    return hashlib.sha256(s.encode()).hexdigest()


if sys.argv[1] == "sample":
    by = defaultdict(list)
    for f in ("suite-0.2/selected-rows.jsonl.gz", "suite-0.2/added-rows.jsonl.gz"):
        for line in gzip.open(DI / f, "rt"):
            r = json.loads(line)
            d = r["_evaluation"]["dataset"]
            if any(w.lower() in d.lower() for w in WANT):
                by[d].append((h(r["id"]), line))
    n = 0
    with gzip.open(DI / "diag/rows.jsonl.gz", "wt") as out:
        for d, rows in sorted(by.items()):
            for _, line in sorted(rows)[:PER]:
                out.write(line)
                n += 1
    ids = {json.loads(l)["_evaluation"]["run_id"] for l in gzip.open(DI / "diag/rows.jsonl.gz", "rt")}
    (DI / "diag/run_ids.json").write_text(json.dumps(sorted(ids)))
    print(n, "rows,", len(ids), "run ids", {d: min(len(r), PER) for d, r in sorted(by.items())})
else:
    run = sys.argv[2]
    ids = set(json.loads((DI / "diag/run_ids.json").read_text()))
    out = DI / f"diag/{run}-subset"
    out.mkdir(parents=True, exist_ok=True)
    k = 0
    with open(out / "results.jsonl", "w") as f:
        for line in open(DI / f"runs/{run}/results.jsonl"):
            if json.loads(line)["run_id"] in ids:
                f.write(line)
                k += 1
    print(run, k, "results ->", out)
