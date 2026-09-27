#!/bin/bash
# Generator v2.1 ablation (GENERATOR_V2 §6): hard-example mining vs. a random selection of the same size, from the v2.0 pool.
# Student = the v1-trained small model (never saw v2.0). Small, 3 seeds per arm, eval v0.2.
set -u
cd "$(dirname "$0")/.."
EVAL=data/eval/kodiak-eval-v0.2.jsonl; OUT=reports/preds_v02
for seed in 0 1 2; do
  for arm in mined random; do
    syn=data/synthetic/sel_v21_$arm.jsonl; name=v21-$arm-s$seed; run=runs/b-small-s1-$name
    echo "$(date +%H:%M) === training $run"
    uv run python -m kodiak_s1.train --run $run --preset small --init modernbert --synthetic $syn --seed $seed \
      --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
      > $run.log 2>&1 || { echo "training failed: $run"; tail -5 $run.log; exit 1; }
    ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
    uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic $syn --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
    uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $EVAL \
      --latency-n 50 --out $OUT/$name.jsonl 2>&1 | grep -v -i warn | tail -1
  done
done
PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "random selection=v21-random-s0,v21-random-s1,v21-random-s2" \
  "mined (v2.1)=v21-mined-s0,v21-mined-s1,v21-mined-s2" > reports/v02-v21-mining.md 2>/dev/null
cat reports/v02-v21-mining.md
echo "$(date +%H:%M) v2.1 mining test complete"
