#!/usr/bin/env bash
# E17 training batch: ~20k kept skills examples (E17 trains on ~10k; the rest is banked) (seed 6 = training; the skills eval is seed 7). Cap $35 (Shane, 2026-09-30). Retries overloaded jobs.
set -u
cd "$(dirname "$0")/.."
eval "$(grep -E '^\s*export DO_INFERENCE_KEY=' ~/.bashrc | tail -1)" && export DO_INFERENCE_KEY
OUT=data/synthetic/skills_v1.jsonl
for i in 1 2 3 4 5 6; do
  uv run --no-sync python -m kodiak_s1.data.sim.skills --n 30000 --start 0 --seed 6 --workers 16 --out $OUT --max-usd 35
  left=$(python3 -c "
import json; last={}
for l in open('$OUT'): r=json.loads(l); last[r['job']]=r
print(sum(r['status']=='retry' for r in last.values()))")
  echo "pass $i: $left retry left"; [ "$left" = 0 ] && break; sleep 60
done
echo SKILLS_BATCH_DONE
