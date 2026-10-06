"""Predictions from a saved accuracy-mode folder on any eval file (same record format as eval.run predict).
    uv run python scripts/ensemble_predict.py --folder dist/kodiak-v0.3-1b-accuracy --eval data/eval/X.jsonl --out reports/preds_X/name.jsonl"""
import argparse
import json
from pathlib import Path

from kodiak_s1.eval.run import kodiak_records, read_jsonl
from kodiak_s1.hub import KodiakEnsemble
from kodiak_s1.infer import combine_raw, raw_outputs

ap = argparse.ArgumentParser()
ap.add_argument("--folder", required=True)
ap.add_argument("--eval", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
ens = KodiakEnsemble.from_folder(Path(a.folder), device="cuda")
exs = read_jsonl(a.eval)
recs = kodiak_records(exs, combine_raw([raw_outputs(m.model, exs) for m in ens.members]), None, null_threshold=ens.default_options["null_threshold"])
Path(a.out).parent.mkdir(parents=True, exist_ok=True)
with open(a.out, "w") as f:
    f.write(json.dumps({"_meta": {"system": Path(a.folder).name, "eval": a.eval}}) + "\n")
    for r in recs:
        f.write(json.dumps(r) + "\n")
print(len(recs), "records ->", a.out)
