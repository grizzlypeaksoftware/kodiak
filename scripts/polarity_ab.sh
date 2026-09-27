#!/bin/bash
# Polarity data test (GENERATOR_V2 §13): small, public + v2.0 + the mixed/neutral tone batch, 3 seeds, on eval v0.2.
# Baseline = the existing small v2 runs (ab-B-v2, -s1, -s2). Additive (more data), so read the targeted rows (poem and
# financial-tweet sentiment) together with the never-seen average: a gain on the targets must not cost the rest.
set -u
cd "$(dirname "$0")/.."
until grep -q "llm baseline complete" runs/llm-baseline-v02.log 2>/dev/null; do sleep 60; done
until grep -qE "^done:|budget cap" data/synthetic/gen2_v21_polarity.log && ! pgrep -f "gen2 run .*polarity" >/dev/null; do sleep 60; done
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/gen2_v21_polarity.jsonl; EVAL=data/eval/kodiak-eval-v0.2.jsonl; OUT=reports/preds_v02
for seed in 0 1 2; do
  name=polarity-s$seed; run=runs/b-small-s1-$name
  echo "$(date +%H:%M) === training $run (seed $seed)"
  uv run python -m kodiak_s1.train --run $run --preset small --init modernbert --synthetic "$SYN" --seed $seed \
    --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
    > $run.log 2>&1 || { echo "training failed: $run"; tail -5 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $EVAL \
    --latency-n 50 --out $OUT/$name.jsonl 2>&1 | grep -v -i warn | tail -1
done
PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "small v2=ab-B-v2,ab-B-v2-s1,ab-B-v2-s2" \
  "small v2 + polarity=polarity-s0,polarity-s1,polarity-s2" > reports/v02-polarity.md 2>/dev/null
cat reports/v02-polarity.md
echo "$(date +%H:%M) polarity test complete"
