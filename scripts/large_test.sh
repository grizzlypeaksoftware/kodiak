#!/bin/bash
# Backbone test (D29 next lever): ModernBERT-large vs base, public + v2.0 data (9,137 synthetic), D25 recipe, 3 seeds.
# Compare against the small v2 runs (ab-B-v2, -s1, -s2).
set -u
cd "$(dirname "$0")/.."
V2=data/synthetic/gen2_v20.jsonl
for seed in 0 1 2; do
  name=large-v2-s$seed; run=runs/b-base-s1-v2-s$seed
  echo "$(date +%H:%M) === training $run (ModernBERT-large, seed $seed)"
  uv run python -m kodiak_s1.train --run $run --preset base --init modernbert --synthetic $V2 --synthetic-max 9137 --seed $seed \
    --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
    > $run.log 2>&1 || { echo "training failed: $run"; tail -5 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic $V2 --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --latency-n 50 \
    --out reports/preds/$name.jsonl 2>&1 | grep -v -i warn | tail -1
done
uv run python scripts/seed_summary.py --groups "small v2=ab-B-v2,ab-B-v2-s1,ab-B-v2-s2" "large v2=large-v2-s0,large-v2-s1,large-v2-s2" \
  > reports/backbone-test.md 2>/dev/null
cat reports/backbone-test.md
echo "$(date +%H:%M) backbone test complete"
