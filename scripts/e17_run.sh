#!/bin/bash
# E17 full run (approved): XL v2 seed-1 recipe + ~10k skills examples (2,500 per skill). One variable: the data mix.
# Smoke = the first 500 steps of this same run (same schedule): at step 500, scripts/smoke_check.py vs the XL v2 seed-1 run; if it fails,
# training is stopped. Keep line (set before the run): skills score >= 0.618 (baseline 0.518); guards: never-seen >= 0.645, familiar >= 0.87,
# abstain precision >= 0.86, label-overlap probe >= 4 of 8.
set -u
cd "$(dirname "$0")/.."
until grep -q SKILLS_BATCH_DONE data/synthetic/skills_v1.log; do sleep 60; done
echo "$(date +%H:%M) batch done: $(grep '^pass' data/synthetic/skills_v1.log | tail -1)"
uv run python scripts/e17_subsample.py || exit 1
uv run python scripts/gate.py docs/experiments/E17-in-purpose-skills.md --full || exit 1
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/skills_v1_e17_10k.jsonl; OUT=reports/preds_v02
seed=1; name=e17-xl-skills-s$seed; run=runs/b-xl-s1-e17-s$seed; base=runs/b-xl-s1-v2-s1
echo "$(date +%H:%M) === training $run (smoke check at step 500)"
uv run python -m kodiak_s1.train --run $run --preset xl --init modernbert --synthetic "$SYN" --seed $seed \
  --steps 6000 --lr 3e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 > $run.log 2>&1 &
TP=$!
until grep -q '"event": "eval", "step": 500' $run/metrics.jsonl 2>/dev/null || ! kill -0 $TP 2>/dev/null; do sleep 30; done
if ! uv run python scripts/smoke_check.py $run $base --step 500; then
  echo "SMOKE FAILED: stopping $run"; kill $TP; echo "E17 STOPPED"; exit 1
fi
echo "$(date +%H:%M) smoke passed; full run continues"
wait $TP || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json \
  --eval data/eval/kodiak-eval-v0.2.jsonl --latency-n 50 --out $OUT/$name.jsonl 2>&1 | grep -v -i warn | tail -1
uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json \
  --eval data/eval/kodiak-skills-eval-v0.1.jsonl --out reports/preds_skills/$name.jsonl 2>&1 | grep -v -i warn | tail -1
{
  echo "# E17 result: XL + skills data (seed $seed)"; echo
  echo "Keep line (set before the run): skills score >= 0.618 (baseline 0.518); guards: never-seen >= 0.645, familiar >= 0.87,"
  echo "abstain precision >= 0.86, label-overlap probe >= 4 of 8."; echo
  echo "## Skills eval"; echo; echo '```'
  uv run python scripts/skills_score.py reports/preds_skills/xl-s1-baseline.jsonl reports/preds_skills/$name.jsonl
  echo '```'; echo; echo "## Eval v0.2 (never-seen, familiar, calibration, abstain precision)"; echo
  PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "xl v2 (seed 1)=xl-v2-s1" "xl v2 + skills (E17)=$name" 2>/dev/null
  echo; echo "## Label-overlap probe"; echo
  uv run python scripts/probe_label_overlap.py $base $run 2>/dev/null
} > reports/e17-xl-skills.md
cat reports/e17-xl-skills.md
echo "$(date +%H:%M) E17 COMPLETE"
