#!/bin/bash
# Returns Desk simulator test (GENERATOR_V2 §17): small, public + v2.0 + sim_returns_v1, 3 seeds, vs the small v2 runs.
# Measured on eval v0.2 (must not drop) and on the label-overlap probe (scripts/probe_label_overlap.py, the target).
set -u
cd "$(dirname "$0")/.."
until grep -qE "^done:" data/synthetic/sim_returns_v1.log 2>/dev/null; do sleep 60; done
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/sim_returns_v1.jsonl; EVAL=data/eval/kodiak-eval-v0.2.jsonl; OUT=reports/preds_v02
for seed in 0 1 2; do
  name=simret-s$seed; run=runs/b-small-s1-$name
  echo "$(date +%H:%M) === training $run (seed $seed)"
  uv run python -m kodiak_s1.train --run $run --preset small --init modernbert --synthetic "$SYN" --seed $seed \
    --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
    > $run.log 2>&1 || { echo "training failed: $run"; tail -5 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $EVAL \
    --latency-n 50 --out $OUT/$name.jsonl 2>&1 | grep -v -i warn | tail -1
done
{
  PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "small v2=ab-B-v2,ab-B-v2-s1,ab-B-v2-s2" \
    "small v2 + Returns Desk=simret-s0,simret-s1,simret-s2" 2>/dev/null
  echo; echo "## Label-overlap probe (GENERATOR_V2 §16)"; echo
  uv run python scripts/probe_label_overlap.py runs/b-small-s1-B-v2 runs/b-small-s1-B-v2-s1 runs/b-small-s1-B-v2-s2 \
    runs/b-small-s1-simret-s0 runs/b-small-s1-simret-s1 runs/b-small-s1-simret-s2 2>/dev/null
} > reports/v02-simret.md
cat reports/v02-simret.md
echo "$(date +%H:%M) returns desk test complete"
