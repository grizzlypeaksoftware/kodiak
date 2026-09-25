#!/bin/bash
# Recipe ablation (after the scaling test):
#   R0  existing 9,411-synthetic model, final checkpoint, + abstain threshold tuned on validation (no retraining)
#   R1  repeat cap (max 3 passes per source) + full LR schedule (no early stopping) + tuned threshold
#   R2  full LR schedule without the cap (isolates the cap's effect)
set -u
cd "$(dirname "$0")/.."
SYN=data/synthetic/synth_v1.jsonl,data/synthetic/synth_v1_cloud.jsonl
evaluate() {  # model name out
  uv run python -m kodiak_s1.eval.run calibrate --model "$1" --synthetic $SYN --tune-threshold --out "$3" 2>&1 | grep -E '"null_threshold"|decision_acc'
  uv run python -m kodiak_s1.eval.run predict --model "$1" --name "$2" --calibration "$3" --latency-n 50 \
    --out reports/preds/recipe-$2.jsonl 2>&1 | grep -v -i warn | tail -1
}
echo "$(date +%H:%M) R0: threshold tuning on the existing syn9411 final checkpoint"
evaluate runs/b-small-s1-syn9411/checkpoints/step_0004250.pt R0-syn9411-thr runs/b-small-s1-syn9411/calibration-final-thr.json
for spec in "R1-cap3 --max-epochs 3" "R2-fullsched --max-epochs 0"; do
  name=${spec%% *}; extra=${spec#* }
  run=runs/b-small-s1-$name
  echo "$(date +%H:%M) === training $run ($extra, no early stopping)"
  uv run python -m kodiak_s1.train --run $run --preset small --init modernbert --synthetic $SYN $extra --patience 0 \
    --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
    > $run.log 2>&1 || { echo "training failed: $run"; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  echo "$(date +%H:%M) evaluating $ckpt"
  evaluate $ckpt $name $run/calibration-final-thr.json
done
uv run python -m kodiak_s1.eval.run report reports/preds/scaling-syn9411-final.jsonl reports/preds/recipe-*.jsonl \
  --out reports/recipe-test.md 2>&1 | grep -v -i warn | head -12
echo "$(date +%H:%M) recipe test complete"
