#!/bin/bash
# Model check (2026-10-07, after D72): is the encoder the ceiling? Small open LLMs (Qwen3 0.6B and 1.7B, Apache-2.0), zero-shot through
# Ollama with the same prompt as the Qwen3-8B baseline, on the never-seen part of eval v0.2 and on the real-data tests. Compared with
# Kodiak-v0.3-1B (trained) on the same items. A zero-shot LLM near or above Kodiak would mean a trained LLM backbone likely generalizes better.
set -u
cd "$(dirname "$0")/.."
mkdir -p reports/model_check
echo "$(date +%H:%M) MODEL_CHECK_START"
for m in qwen3:1.7b qwen3:0.6b; do
  n=${m/:/-}
  for ev in "data/eval/heldout-v02-only.jsonl heldout" "data/eval/kodiak-real-anchors-v0.1.jsonl anchors" "data/eval/kodiak-probes-real-v0.1.jsonl probes"; do
    set -- $ev
    echo "$(date +%H:%M) $m on $2"
    uv run --no-sync python -m kodiak_s1.eval.run baseline --llm $m --name $n --eval $1 --workers 4 --out reports/model_check/$n-$2.jsonl 2>&1 | tail -1
  done
done
echo "$(date +%H:%M) MODEL_CHECK_DONE"
