#!/bin/bash
# v0.2 backbone test (D45): Ettin-encoder-1B (jhu-clsp, MIT; ModernBERT architecture + tokenizer) vs ModernBERT-large, same data.
# One seed first. Pass bar, written before the run: never-seen forced accuracy >= 0.629 on eval v0.2 (large v2 3-seed mean 0.609 + 2 points)
# -> confirm with two more seeds; otherwise drop the 1B backbone. lr 3e-5 (vs 5e-5 for large): bigger models are less stable at the same rate.
set -u
cd "$(dirname "$0")/.."
V2=data/synthetic/gen2_v20.jsonl; EVAL=data/eval/kodiak-eval-v0.2.jsonl; OUT=reports/preds_v02
seed=1; name=xl-v2-s$seed; run=runs/b-xl-s1-v2-s$seed
echo "$(date +%H:%M) === training $run (Ettin-1B, seed $seed)"
uv run python -m kodiak_s1.train --run $run --preset xl --init modernbert --synthetic $V2 --synthetic-max 9137 --seed $seed \
  --steps 6000 --lr 3e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
  > $run.log 2>&1 || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic $V2 --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $EVAL \
  --latency-n 50 --out $OUT/$name.jsonl 2>&1 | grep -v -i warn | tail -1
{
  PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "large v2 (ModernBERT-large, 400M)=large-v2-s0,large-v2-s1,large-v2-s2" \
    "xl v2 (Ettin-1B)=$name" 2>/dev/null
  echo; echo "Pass bar (set before the run): never-seen forced >= 0.629."; echo
  echo "## Label-overlap probe"; echo
  uv run python scripts/probe_label_overlap.py runs/b-base-s1-v2-s1 $run 2>/dev/null
} > reports/v02-xl.md
cat reports/v02-xl.md
echo "$(date +%H:%M) xl test complete"
