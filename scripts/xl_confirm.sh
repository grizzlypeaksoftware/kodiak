#!/bin/bash
# E15 confirmation (approved plan: 2 confirming seeds after the full run cleared 0.629). Same recipe as scripts/xl_test.sh.
set -u
cd "$(dirname "$0")/.."
V2=data/synthetic/gen2_v20.jsonl; EVAL=data/eval/kodiak-eval-v0.2.jsonl; OUT=reports/preds_v02
for seed in 0 2; do
  name=xl-v2-s$seed; run=runs/b-xl-s1-v2-s$seed
  echo "$(date +%H:%M) === training $run (Ettin-1B, seed $seed)"
  uv run python -m kodiak_s1.train --run $run --preset xl --init modernbert --synthetic $V2 --synthetic-max 9137 --seed $seed \
    --steps 6000 --lr 3e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
    > $run.log 2>&1 || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic $V2 --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $EVAL \
    --latency-n 50 --out $OUT/$name.jsonl 2>&1 | grep -v -i warn | tail -1
done
PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "large v2 (400M)=large-v2-s0,large-v2-s1,large-v2-s2" \
  "xl v2 (Ettin-1B)=xl-v2-s0,xl-v2-s1,xl-v2-s2" > reports/v02-xl-3seeds.md 2>/dev/null
cat reports/v02-xl-3seeds.md
echo "$(date +%H:%M) xl confirm complete"
