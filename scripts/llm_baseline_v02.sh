#!/bin/bash
# Release criterion 2 (STRATEGY §6): a 7-8B open LLM on eval v0.2, run locally through Ollama after the distill test frees the GPU.
# Qwen3-8B (Apache-2.0) on the full set; Qwen 27B on a fixed 1,500-example sample as the "big LLM" reference point.
set -u
cd "$(dirname "$0")/.."
until grep -qE "distill test complete|training failed" runs/distill-test.log; do sleep 60; done
EVAL=data/eval/kodiak-eval-v0.2.jsonl; OUT=reports/preds_v02
echo "$(date +%H:%M) qwen3-8b on eval v0.2 (full)"
uv run python -m kodiak_s1.eval.run baseline --llm qwen3:8b --name qwen3-8b --eval $EVAL --workers 4 --out $OUT/llm-qwen3-8b.jsonl 2>&1 | tail -3
echo "$(date +%H:%M) qwen3.8-27b on eval v0.2 (1,500 sample)"
uv run python -m kodiak_s1.eval.run baseline --llm qwen3.8:27b --name qwen3.8-27b --eval $EVAL --limit 1500 --workers 2 \
  --out $OUT/llm-qwen3.8-27b-1500.jsonl 2>&1 | tail -3
R="uv run python -m kodiak_s1.eval.run report --choice-only"
$R $OUT/ab-B-v2.jsonl $OUT/large-v2-s0.jsonl $OUT/zs-nli-modernbert-large.jsonl $OUT/llm-qwen3-8b.jsonl \
  --out reports/v02-vs-llm-8b.md > /dev/null 2>&1
$R $OUT/ab-B-v2.jsonl $OUT/large-v2-s0.jsonl $OUT/llm-qwen3-8b.jsonl $OUT/llm-qwen3.8-27b-1500.jsonl \
  --out reports/v02-vs-llm-27b-sample.md > /dev/null 2>&1
grep -A12 "## eval:heldout_v02\|## eval:heldout$" reports/v02-vs-llm-8b.md | head -30
echo "$(date +%H:%M) llm baseline complete"
