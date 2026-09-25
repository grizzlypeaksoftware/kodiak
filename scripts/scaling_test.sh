#!/bin/bash
# Data-scaling test: identical training runs that differ only in how many synthetic examples they see.
# Each run is calibrated on validation data and evaluated on the frozen eval set; one report compares all three.
set -u
cd "$(dirname "$0")/.."
SYN=data/synthetic/synth_v1.jsonl,data/synthetic/synth_v1_cloud.jsonl
for n in 0 3300 9411; do
  run=runs/b-small-s1-syn$n
  echo "$(date +%H:%M) === training $run (synthetic_max=$n)"
  uv run python -m kodiak_s1.train --run $run --preset small --init modernbert --synthetic $SYN --synthetic-max $n \
    --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
    > $run.log 2>&1 || { echo "training failed: $run"; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)   # final checkpoint (early stopping keeps best.pt too)
  echo "$(date +%H:%M) calibrating + evaluating $run (best.pt and final $ckpt)"
  for which in best final; do
    model=$run; [ $which = final ] && model=$ckpt
    uv run python -m kodiak_s1.eval.run calibrate --model $model --out $run/calibration-$which.json > /dev/null 2>&1
    uv run python -m kodiak_s1.eval.run predict --model $model --name "syn$n-$which" --calibration $run/calibration-$which.json \
      --latency-n 50 --out reports/preds/scaling-syn$n-$which.jsonl 2>&1 | grep -v -i warn | tail -1
  done
done
uv run python -m kodiak_s1.eval.run report reports/preds/scaling-syn*-*.jsonl --out reports/scaling-test.md 2>&1 | grep -v -i warn | head -20
echo "$(date +%H:%M) scaling test complete"
