#!/usr/bin/env bash
# E22 training batch (Shane approved, $20 cap): jobs per kind sized from the pilot keep rates to reach ~4k+ kept each; seed 54, --split train.
set -u
cd "$(dirname "$0")/.."
eval "$(grep -E '^\s*export DO_INFERENCE_KEY=' ~/.bashrc | tail -1)" && export DO_INFERENCE_KEY
OUT=data/synthetic/skills3_v1.jsonl
for i in 1 2 3 4; do
  for kn in long_hallucination:10000 refund_eligibility:8000 step_safety:8000 stance:4000; do
    uv run --no-sync python -m kodiak_s1.data.sim.probes --per-kind ${kn#*:} --seed 54 --split train --workers 16 --kinds ${kn%%:*} \
      --out $OUT --max-usd 18 2>&1 | tail -1 | cut -c1-300
  done
  left=$(python3 -c "
import json; last={}
for l in open('$OUT'): r=json.loads(l); last[(r['kind'],r['job'])]=r
print(sum(r['status']=='retry' for r in last.values()))")
  echo "pass $i: $left retry left"; [ "$left" = 0 ] && break; sleep 60
done
echo SKILLS3_BATCH_DONE
