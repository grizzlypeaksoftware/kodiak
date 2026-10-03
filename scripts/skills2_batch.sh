#!/usr/bin/env bash
# E21 training batch: 10k jobs per kind (seed 24, --split train); ~$12 at the pilot's $0.0004/job; cap $15 (Shane approved E21). Retries
# overloaded jobs. E21 trains on 2,500 kept per kind; the rest is banked.
set -u
cd "$(dirname "$0")/.."
eval "$(grep -E '^\s*export DO_INFERENCE_KEY=' ~/.bashrc | tail -1)" && export DO_INFERENCE_KEY
OUT=data/synthetic/skills2_v1.jsonl
for i in 1 2 3 4 5 6; do
  uv run --no-sync python -m kodiak_s1.data.sim.probes --per-kind 10000 --seed 24 --split train --workers 16 \
    --kinds pairwise_judge,sarcasm,policy_violation --out $OUT --max-usd 15 2>&1 | tail -1
  left=$(python3 -c "
import json; last={}
for l in open('$OUT'): r=json.loads(l); last[(r['kind'],r['job'])]=r
print(sum(r['status']=='retry' for r in last.values()))")
  echo "pass $i: $left retry left"; [ "$left" = 0 ] && break; sleep 60
done
echo SKILLS2_BATCH_DONE
