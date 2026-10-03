#!/bin/bash
# D55 diagnosis: XL v2 seeds 0/2 and E17 seeds 0/2 on the fixed 12-benchmark sample (seed 1 of each comes from the full runs).
set -u
cd "$(dirname "$0")/.."
DI=$HOME/development/decision-index; PY=$PWD/.venv/bin/python
for m in v2-s0 v2-s2 e17-s0 e17-s2; do
  run=runs/b-xl-s1-$m; out=dist/diag-$m
  [ -f $out/model.safetensors ] || uv run python -m kodiak_s1.hub export --ckpt $(ls $run/checkpoints/step_*.pt | tail -1) \
      --calibration $run/calibration-final-thr.json --out $out 2>&1 | grep exported
  echo "$(date +%H:%M) === $m"
  (cd $DI && $PY -m decision_index run --engine kodiak_s1.decision_index_engine:KodiakEngine --option model=$OLDPWD/$out \
      --rows diag/rows.jsonl.gz --out diag/kodiak-$m 2>&1 | grep '"event":"complete"' | cut -c1-200
   $PY -m decision_index score --results diag/kodiak-$m/results.jsonl > /dev/null 2>&1)
done
uv run python scripts/di_diag_table.py diag/kodiak-xl-r2-subset diag/kodiak-v2-s0 diag/kodiak-v2-s2 \
  diag/kodiak-e17-s1-subset diag/kodiak-e17-s0 diag/kodiak-e17-s2 | tee reports/d55-di-diagnosis-table.md
echo "$(date +%H:%M) DI DIAG COMPLETE"
