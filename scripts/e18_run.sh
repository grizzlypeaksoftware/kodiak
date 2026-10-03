#!/bin/bash
# E18 full run (approved): E17's recipe and data + options swapped for checker-verified rewordings (p = 0.5). One variable.
# Smoke = the first 500 steps (same schedule) vs E17 seed 1. Keep line (set before the run): wording consistency >= 0.721 (baseline 0.621)
# and reworded accuracy >= 0.711 (0.681); guards: never-seen >= 0.645, familiar >= 0.87, abstain precision >= 0.86, skills >= 0.95, probe >= 4/8.
set -u
cd "$(dirname "$0")/.."
uv run python scripts/gate.py docs/experiments/E18-option-wording.md --full || exit 1
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/skills_v1_e17_10k.jsonl; OUT=reports/preds_v02
seed=1; name=e18-xl-wording-s$seed; run=runs/b-xl-s1-e18-s$seed; base=runs/b-xl-s1-e17-s1
echo "$(date +%H:%M) === training $run (smoke check at step 500)"
uv run python -m kodiak_s1.train --run $run --preset xl --init modernbert --synthetic "$SYN" --seed $seed \
  --option-wordings data/wordings/train.json --p-option-wording 0.5 \
  --steps 6000 --lr 3e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 > $run.log 2>&1 &
TP=$!
until grep -q '"event": "eval", "step": 500' $run/metrics.jsonl 2>/dev/null || ! kill -0 $TP 2>/dev/null; do sleep 30; done
if ! uv run python scripts/smoke_check.py $run $base --step 500; then
  echo "SMOKE FAILED: stopping $run"; kill $TP; echo "E18 STOPPED"; exit 1
fi
echo "$(date +%H:%M) smoke passed; full run continues"
wait $TP || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
for ev in "data/eval/kodiak-eval-v0.2.jsonl $OUT" "data/eval/kodiak-skills-eval-v0.1.jsonl reports/preds_skills" \
          "data/eval/kodiak-wording-eval-v0.1.jsonl reports/preds_wording"; do
  set -- $ev
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $1 \
    --out $2/$name.jsonl 2>&1 | grep -v -i warn | tail -1
done
{
  echo "# E18 result: option-wording robustness (seed $seed) vs E17 seed 1"; echo
  echo "Keep line (set before the run): wording consistency >= 0.721 (baseline 0.621) and reworded accuracy >= 0.711 (0.681); guards:"
  echo "never-seen >= 0.645, familiar >= 0.87, abstain precision >= 0.86, skills score >= 0.95, label-overlap probe >= 4 of 8."; echo
  echo "## Wording eval"; echo; echo '```'
  uv run python scripts/wording_score.py reports/preds_wording/e17-s1-baseline.jsonl reports/preds_wording/$name.jsonl
  echo '```'; echo; echo "## Skills eval"; echo; echo '```'
  uv run python scripts/skills_score.py reports/preds_skills/e17-xl-skills-s1.jsonl reports/preds_skills/$name.jsonl
  echo '```'; echo; echo "## Eval v0.2"; echo
  PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "E17 (seed 1)=e17-xl-skills-s1" "E18 (seed 1)=$name" 2>/dev/null
  echo; echo "## Label-overlap probe"; echo
  uv run python scripts/probe_label_overlap.py $base $run 2>/dev/null
} > reports/e18-xl-wording.md
cat reports/e18-xl-wording.md
echo "$(date +%H:%M) E18 COMPLETE"
