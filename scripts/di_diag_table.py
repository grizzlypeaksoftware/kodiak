"""D55 diagnosis table: chance-corrected skill per benchmark on the fixed sample, for each scored diag run.
    uv run python scripts/di_diag_table.py diag/<run>-subset ... (paths relative to ../decision-index)"""
import json
import sys
from pathlib import Path

DI = Path.home() / "development/decision-index"
full = json.loads((DI / "runs/kodiak-xl-r2/scores.json").read_text())
chance = {v["dataset"]: full["index_benchmarks"][k]["random"] for k, v in full["benchmarks"].items() if k in full["index_benchmarks"]}
cols = {}
for d in sys.argv[1:]:
    s = json.loads((DI / d / "benchmark-summary.json").read_text())
    cols[Path(d).name.replace("-subset", "")] = {b["dataset"]: b["score"] for b in s["benchmarks"] if b.get("scored_requests")}
names = sorted({n for c in cols.values() for n in c})
print("| Benchmark | " + " | ".join(cols) + " |")
print("|---|" + "---|" * len(cols))
for n in names:
    ch = chance.get(n, 0.0)
    cells = []
    for c in cols.values():
        v = c.get(n)
        cells.append("–" if v is None else f"{max(0.0, (v - ch) / (1 - ch)):.3f}")
    print(f"| {n} | " + " | ".join(cells) + " |")
