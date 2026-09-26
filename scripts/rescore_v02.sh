#!/bin/bash
# Re-score every model on eval set v0.2 (D30), after the backbone test finishes. Predictions -> reports/preds_v02/.
set -u
cd "$(dirname "$0")/.."
until grep -qE "backbone test complete|training failed" runs/backbone-test.log; do sleep 60; done
EVAL=data/eval/kodiak-eval-v0.2.jsonl; OUT=reports/preds_v02; mkdir -p $OUT
kodiak() {  # name run-dir
  ckpt=$(ls $2/checkpoints/step_*.pt | tail -1)
  [ -f $OUT/$1.jsonl ] || uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $1 --calibration $2/calibration-final-thr.json \
    --eval $EVAL --latency-n 50 --out $OUT/$1.jsonl 2>&1 | grep -v -i warn | tail -1
}
echo "$(date +%H:%M) scoring Kodiak models on v0.2"
kodiak recipe-R1-cap3 runs/b-small-s1-R1-cap3
for s in "" -s1 -s2; do kodiak ab-A-eq$s runs/b-small-s1-A-eq$s; kodiak ab-B-v2$s runs/b-small-s1-B-v2$s; done
for s in 0 1 2; do [ -d runs/b-base-s1-v2-s$s/checkpoints ] && kodiak large-v2-s$s runs/b-base-s1-v2-s$s; done
echo "$(date +%H:%M) scoring open zero-shot classifiers on v0.2"
export HF_HUB_DISABLE_PROGRESS_BARS=1
for spec in "MoritzLaurer/deberta-v3-large-zeroshot-v2.0 zs-nli-deberta-v3-large" "MoritzLaurer/deberta-v3-large-zeroshot-v2.0-28heldout zs-nli-deberta-v3-large-28heldout" \
            "MoritzLaurer/ModernBERT-large-zeroshot-v2.0 zs-nli-modernbert-large" "knowledgator/gliclass-large-v3.0 zs-gliclass-large-v3" \
            "knowledgator/gliclass-instruct-large-v1.0 zs-gliclass-instruct-large"; do
  set -- $spec
  [ -f $OUT/$2.jsonl ] || uv run python -m kodiak_s1.eval.zeroshot --model "$1" --name "$2" --eval $EVAL --out $OUT/$2.jsonl 2>&1 | grep -E "choice questions"
done
export PRED_DIR=$OUT
uv run python scripts/seed_summary.py --groups "small v1=ab-A-eq,ab-A-eq-s1,ab-A-eq-s2" "small v2=ab-B-v2,ab-B-v2-s1,ab-B-v2-s2" > reports/v02-data-ab.md 2>/dev/null
uv run python scripts/seed_summary.py --groups "small v2=ab-B-v2,ab-B-v2-s1,ab-B-v2-s2" "large v2=large-v2-s0,large-v2-s1,large-v2-s2" > reports/v02-backbone.md 2>/dev/null
uv run python -m kodiak_s1.eval.run report $OUT/ab-B-v2.jsonl $OUT/large-v2-s0.jsonl $OUT/zs-*.jsonl --choice-only --out reports/v02-vs-baselines.md > /dev/null 2>&1
cat reports/v02-data-ab.md reports/v02-backbone.md
echo "$(date +%H:%M) v0.2 rescore complete"
