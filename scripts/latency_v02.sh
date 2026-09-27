#!/bin/bash
# Clean single-stream latency (release criterion 2's speed half): Qwen3-8B one request at a time vs Kodiak batch-1, idle GPU.
# The accuracy run used 4 concurrent requests, which inflates per-request latency. Waits for the polarity test to free the GPU.
set -u
cd "$(dirname "$0")/.."
until grep -qE "polarity test complete|training failed" runs/polarity-ab.log 2>/dev/null; do sleep 60; done
EVAL=data/eval/kodiak-eval-v0.2.jsonl; OUT=runs/latency; mkdir -p $OUT
uv run python -m kodiak_s1.eval.run baseline --llm qwen3:8b --name qwen3-8b-latency --eval $EVAL --limit 200 --workers 1 \
  --out $OUT/qwen3-8b-w1.jsonl 2>&1 | tail -1
for m in large-v2-s1:runs/b-base-s1-v2-s1 small-v2:runs/b-small-s1-B-v2; do
  name=${m%%:*}; run=${m#*:}; ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $EVAL \
    --latency-n 200 --out $OUT/$name.jsonl 2>&1 | grep -v -i warn | tail -1
done
uv run python - <<'PY'
import json, statistics as st
lat = {}
for l in open("runs/latency/qwen3-8b-w1.jsonl"):
    r = json.loads(l)
    if r.get("latency_ms"): lat[r["ex"]] = r["latency_ms"]
v = sorted(lat.values()); print(f"qwen3-8b single-stream: p50 {v[len(v)//2]:.0f} ms, mean {st.mean(v):.0f} ms over {len(v)} examples")
PY
echo "$(date +%H:%M) latency complete"
