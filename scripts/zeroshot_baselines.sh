#!/usr/bin/env bash
# Open zero-shot classifier baselines on the frozen eval set (choice questions). See src/kodiak_s1/eval/zeroshot.py.
set -u
cd "$(dirname "$0")/.."
export HF_HUB_DISABLE_PROGRESS_BARS=1
for spec in \
  "MoritzLaurer/deberta-v3-large-zeroshot-v2.0 zs-nli-deberta-v3-large" \
  "MoritzLaurer/ModernBERT-large-zeroshot-v2.0 zs-nli-modernbert-large" \
  "knowledgator/gliclass-large-v3.0 zs-gliclass-large-v3" \
  "knowledgator/gliclass-instruct-large-v1.0 zs-gliclass-instruct-large"; do
  set -- $spec
  echo "=== $1 ($(date +%H:%M:%S))"
  uv run python -m kodiak_s1.eval.zeroshot --model "$1" --name "$2" --out "reports/preds/$2.jsonl" 2>&1 | grep -vE "FutureWarning|warnings.warn"
done
echo "ALL DONE $(date +%H:%M:%S)"
