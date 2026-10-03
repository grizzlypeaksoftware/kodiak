#!/usr/bin/env bash
# E17 held-out skills eval: seed 7, never trained on. Reruns until no overloaded (retry) jobs remain.
set -u
cd "$(dirname "$0")/.."
eval "$(grep -E '^\s*export DO_INFERENCE_KEY=' ~/.bashrc | tail -1)" && export DO_INFERENCE_KEY
OUT=${OUT:-data/synthetic/skills_eval_raw.jsonl}
for i in 1 2 3 4 5 6; do
  uv run --no-sync python -m kodiak_s1.data.sim.skills ${ARGS:---n 640 --start 0} --seed 7 --workers 8 --out $OUT --max-usd 2 2>&1 | tail -1
  left=$(python3 -c "
import json; last={}
for l in open('$OUT'): r=json.loads(l); last[r['job']]=r
print(sum(r['status']=='retry' for r in last.values()))")
  echo "pass $i: $left retry left"; [ "$left" = 0 ] && break; sleep 30
done
echo SKILLS_EVAL_DONE
