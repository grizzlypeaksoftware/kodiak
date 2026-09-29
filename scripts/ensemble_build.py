"""Build the 'accuracy mode' ensemble (D34/D45): export member runs, tune the abstain threshold on VALIDATION data, score on eval v0.2.

    uv run python scripts/ensemble_build.py --runs runs/b-base-s1-v2-s0,runs/b-base-s1-v2-s1,runs/b-base-s1-v2-s2 \\
        --synthetic data/synthetic/gen2_v20.jsonl --out dist/kodiak-large-v2-ensemble --name large-v2-ensemble
"""
import argparse
import json
import random
from pathlib import Path

from kodiak_s1.data.sources import SOURCES
from kodiak_s1.eval.run import fit_null_threshold, kodiak_records, read_jsonl, synthetic_val_examples
from kodiak_s1.hub import Kodiak, KodiakEnsemble
from kodiak_s1.infer import combine_raw, load, raw_outputs

ap = argparse.ArgumentParser()
ap.add_argument("--runs", required=True)
ap.add_argument("--synthetic", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--name", required=True)
ap.add_argument("--eval", default="data/eval/kodiak-eval-v0.2.jsonl")
ap.add_argument("--per-source", type=int, default=300)
a = ap.parse_args()

members = []
for run in a.runs.split(","):
    run = Path(run)
    ckpt = sorted((run / "checkpoints").glob("step_*.pt"))[-1]
    members.append(Kodiak(load(ckpt), json.loads((run / "calibration-final-thr.json").read_text()), name=run.name))

# Validation data, exactly as `eval.run calibrate` gathers it (never the eval set).
val = []
for sid, src in SOURCES.items():
    p = Path("data/processed") / sid / "val.jsonl.gz"
    if not src.heldout and p.exists():
        rows = read_jsonl(p)
        random.Random(0).shuffle(rows)
        val += rows[: a.per_source]
val += synthetic_val_examples(a.synthetic, a.per_source)
raws = combine_raw([raw_outputs(m.model, val) for m in members])
pairs = [(r, q, ex["answers"][q["id"]]) for ex, rs in zip(val, raws) for r, q in zip(rs, ex["questions"])]
thr = fit_null_threshold(pairs, {})
print("threshold on validation:", thr)

ens = KodiakEnsemble(members, thr["null_threshold"], name=a.name)
ens.save_pretrained(a.out)
Path(a.out, "ensemble_calibration.json").write_text(json.dumps({**thr, "fit_on": f"validation splits, {len(val)} examples"}, indent=2) + "\n")

exs = read_jsonl(a.eval)
recs = kodiak_records(exs, combine_raw([raw_outputs(m.model, exs) for m in members]), None, null_threshold=thr["null_threshold"])
out = Path("reports/preds_v02") / f"{a.name}.jsonl"
with open(out, "w") as f:
    f.write(json.dumps({"_meta": {"system": a.name, "members": a.runs, "eval": a.eval}}) + "\n")
    for r in recs:
        f.write(json.dumps(r) + "\n")
print("eval predictions ->", out)
