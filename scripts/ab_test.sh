#!/bin/bash
# Generator A/B (GENERATOR_V2.md §9 step 5): same recipe (D25 defaults), same seed, same steps; only the synthetic data differs.
#   A      public + v1 (existing run b-small-s1-R1-cap3; retrained as A-eq at N if v2 has fewer training examples)
#   B-v2   public + v2.0 (N examples)
#   C-v1v2 public + v1 + v2.0 (everything)
# N = the number of v2.0 *training* examples (after the 3% synthetic validation split), so A and B see equal amounts.
set -u
cd "$(dirname "$0")/.."
V1=data/synthetic/synth_v1.jsonl,data/synthetic/synth_v1_cloud.jsonl
V2=data/synthetic/gen2_v20.jsonl
count_train() {  # synthetic training examples a run would use from these files
  uv run python -c "
import json, sys
from kodiak_s1.data.sources import hash_split
from kodiak_s1.schema import render_state
n = 0
for p in sys.argv[1].split(','):
    for line in open(p):
        r = json.loads(line)
        if r.get('status') == 'ok' and hash_split(render_state(r['example']['state']), val=0.03, test=0) != 'val':
            n += 1
print(n)" "$1" 2>/dev/null | tail -1
}
N1=$(count_train $V1); N2=$(count_train $V2)
echo "$(date +%H:%M) training examples: v1=$N1 v2=$N2"
evaluate() {  # model name calibration-out synthetic-files
  uv run python -m kodiak_s1.eval.run calibrate --model "$1" --synthetic "$4" --tune-threshold --out "$3" 2>&1 | grep -E '"null_threshold"'
  uv run python -m kodiak_s1.eval.run predict --model "$1" --name "$2" --calibration "$3" --latency-n 50 \
    --out reports/preds/ab-$2.jsonl 2>&1 | grep -v -i warn | tail -1
}
train() {  # name synthetic-files synthetic-max
  run=runs/b-small-s1-$1
  echo "$(date +%H:%M) === training $run (synthetic=$2, max=$3)"
  uv run python -m kodiak_s1.train --run $run --preset small --init modernbert --synthetic "$2" --synthetic-max "$3" \
    --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
    > $run.log 2>&1 || { echo "training failed: $run"; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  echo "$(date +%H:%M) evaluating $ckpt"
  evaluate $ckpt $1 $run/calibration-final-thr.json "$2"
}
N=$(( N1 < N2 ? N1 : N2 ))
train B-v2 $V2 $N
if [ "$N" -lt "$N1" ]; then train A-eq $V1 $N; A=reports/preds/ab-A-eq.jsonl; else A=reports/preds/recipe-R1-cap3.jsonl; fi
train C-v1v2 $V1,$V2 -1
uv run python -m kodiak_s1.eval.run report $A reports/preds/ab-B-v2.jsonl reports/preds/ab-C-v1v2.jsonl \
  --out reports/generator-ab.md 2>&1 | grep -v -i warn | head -14
uv run python -m kodiak_s1.eval.run report $A reports/preds/ab-B-v2.jsonl reports/preds/ab-C-v1v2.jsonl reports/preds/zs-*.jsonl \
  --choice-only --out reports/generator-ab-vs-baselines.md > /dev/null 2>&1
echo "$(date +%H:%M) A/B complete"
