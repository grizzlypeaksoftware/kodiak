#!/bin/bash
# Distillation test (D34): small student trained on public + v2 data, soft targets from the 3 calibrated large runs (alpha 0.5), 3 seeds.
# Compared on eval v0.2 against small v2 (no distillation) and the large 3-run ensemble.
set -u
cd "$(dirname "$0")/.."
V2=data/synthetic/gen2_v20.jsonl; EVAL=data/eval/kodiak-eval-v0.2.jsonl; OUT=reports/preds_v02
T=""
for s in 0 1 2; do T="$T${T:+,}runs/b-base-s1-v2-s$s/checkpoints/step_0006000.pt|runs/b-base-s1-v2-s$s/calibration-final-thr.json"; done
for seed in 0 1 2; do
  name=distill-s$seed; run=runs/b-small-s1-distill-s$seed
  echo "$(date +%H:%M) === training $run (distilled from 3 large, seed $seed)"
  uv run python -m kodiak_s1.train --run $run --preset small --init modernbert --synthetic $V2 --synthetic-max 9137 --seed $seed \
    --distill-from "$T" --distill-alpha 0.5 --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 \
    --ckpt-every 500 > $run.log 2>&1 || { echo "training failed: $run"; tail -5 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic $V2 --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $EVAL \
    --latency-n 50 --out $OUT/$name.jsonl 2>&1 | grep -v -i warn | tail -1
done
PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "small v2=ab-B-v2,ab-B-v2-s1,ab-B-v2-s2" "small distilled=distill-s0,distill-s1,distill-s2" \
  > reports/v02-distill.md 2>/dev/null
cat reports/v02-distill.md
echo "$(date +%H:%M) distill test complete"
