#!/bin/bash
# Seed repeats for the generator A/B: same data (same fixed subset), different training seeds, so the spread between runs
# measures training noise. Seed 0 = the original A-eq / B-v2 runs.
set -u
cd "$(dirname "$0")/.."
V1=data/synthetic/synth_v1.jsonl,data/synthetic/synth_v1_cloud.jsonl
V2=data/synthetic/gen2_v20.jsonl
N=9137
for seed in 1 2; do
  for spec in "B-v2:$V2" "A-eq:$V1"; do
    name=${spec%%:*}-s$seed; syn=${spec#*:}; run=runs/b-small-s1-$name
    echo "$(date +%H:%M) === training $run (seed $seed)"
    uv run python -m kodiak_s1.train --run $run --preset small --init modernbert --synthetic "$syn" --synthetic-max $N --seed $seed \
      --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
      > $run.log 2>&1 || { echo "training failed: $run"; exit 1; }
    ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
    uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$syn" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
    uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --latency-n 50 \
      --out reports/preds/ab-$name.jsonl 2>&1 | grep -v -i warn | tail -1
  done
done
uv run python scripts/seed_summary.py > reports/generator-ab-seeds.md 2>/dev/null
cat reports/generator-ab-seeds.md
echo "$(date +%H:%M) seed repeats complete"
