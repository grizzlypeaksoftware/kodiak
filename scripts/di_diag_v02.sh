#!/bin/bash
# Model-card numbers: the three v0.2 models (E18 recipe, seeds 0-2) on the fixed 12-benchmark Decision Index sample (D56 method).
set -u
cd "$(dirname "$0")/.."
DI=$HOME/development/decision-index; PY=$PWD/.venv/bin/python
for s in 0 1 2; do
  m=v02-s$s; out=dist/diag-$m; run=runs/b-xl-s1-e18-s$s
  [ -f $out/model.safetensors ] || uv run python -m kodiak_s1.hub export --ckpt $(ls $run/checkpoints/step_*.pt | tail -1) \
      --calibration $run/calibration-final-thr.json --out $out 2>&1 | grep exported
  echo "$(date +%H:%M) === $m"
  (cd $DI && $PY -m decision_index run --engine kodiak_s1.decision_index_engine:KodiakEngine --option model=$OLDPWD/$out \
      --rows diag/rows.jsonl.gz --out diag/kodiak-$m 2>&1 | grep '"event":"complete"' | cut -c1-160
   $PY -m decision_index score --results diag/kodiak-$m/results.jsonl > /dev/null 2>&1)
done
uv run python scripts/di_diag_table.py diag/kodiak-xl-r2-subset diag/kodiak-v2-s0 diag/kodiak-v2-s2 diag/kodiak-e17-s1-subset diag/kodiak-e17-s0 \
  diag/kodiak-e17-s2 diag/kodiak-v02-s0 diag/kodiak-v02-s1 diag/kodiak-v02-s2 | tee reports/v02-di-sample.md
echo "$(date +%H:%M) V02 DIAG COMPLETE"
