#!/bin/bash
# E19 (approved): E18's exact recipe, seeds 0 and 2, each with a step-500 smoke check vs E17's same seed; then 3 seeds vs E17's 3 seeds.
# Keep line (set before the runs): never-seen forced 3-seed mean >= 0.682 and never-seen ECE mean <= 0.109; guards: familiar >= 0.87,
# abstain precision mean >= 0.86, skills >= 0.95, probe mean >= 4 of 8.
set -u
cd "$(dirname "$0")/.."
uv run python scripts/gate.py docs/experiments/E19-confirm-rewording-never-seen.md --full || exit 1
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/skills_v1_e17_10k.jsonl; OUT=reports/preds_v02
for seed in 0 2; do
  name=e18-xl-wording-s$seed; run=runs/b-xl-s1-e18-s$seed; base=runs/b-xl-s1-e17-s$seed
  echo "$(date +%H:%M) === training $run (smoke check at step 500 vs $base)"
  uv run python -m kodiak_s1.train --run $run --preset xl --init modernbert --synthetic "$SYN" --seed $seed \
    --option-wordings data/wordings/train.json --p-option-wording 0.5 \
    --steps 6000 --lr 3e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 > $run.log 2>&1 &
  TP=$!
  until grep -q '"event": "eval", "step": 500' $run/metrics.jsonl 2>/dev/null || ! kill -0 $TP 2>/dev/null; do sleep 30; done
  if ! uv run python scripts/smoke_check.py $run $base --step 500; then
    echo "SMOKE FAILED: stopping $run"; kill $TP; echo "E19 STOPPED"; exit 1
  fi
  echo "$(date +%H:%M) smoke passed (seed $seed)"
  wait $TP || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  for ev in "data/eval/kodiak-eval-v0.2.jsonl $OUT" "data/eval/kodiak-skills-eval-v0.1.jsonl reports/preds_skills" \
            "data/eval/kodiak-wording-eval-v0.1.jsonl reports/preds_wording"; do
    set -- $ev
    uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $1 \
      --out $2/$name.jsonl 2>&1 | grep -v -i warn | tail -1
  done
  echo "$(date +%H:%M) seed $seed done"
done
{
  echo "# E19: E17 vs E17 + reworded options (E18 recipe), 3 seeds each"; echo
  echo "Keep line (set before the runs): never-seen forced 3-seed mean >= 0.682 and never-seen ECE mean <= 0.109; guards: familiar >= 0.87,"
  echo "abstain precision mean >= 0.86, skills >= 0.95, label-overlap probe mean >= 4 of 8."; echo
  PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "E17=e17-xl-skills-s0,e17-xl-skills-s1,e17-xl-skills-s2" \
    "E17 + reworded options=e18-xl-wording-s0,e18-xl-wording-s1,e18-xl-wording-s2" 2>/dev/null
  echo; echo "## Skills eval"; echo; echo '```'
  uv run python scripts/skills_score.py reports/preds_skills/e18-xl-wording-s{0,1,2}.jsonl
  echo '```'; echo; echo "## Wording eval"; echo; echo '```'
  uv run python scripts/wording_score.py reports/preds_wording/e17-s1-baseline.jsonl reports/preds_wording/e18-xl-wording-s{0,1,2}.jsonl
  echo '```'; echo; echo "## Label-overlap probe"; echo
  uv run python scripts/probe_label_overlap.py runs/b-xl-s1-e17-s0 runs/b-xl-s1-e17-s1 runs/b-xl-s1-e17-s2 runs/b-xl-s1-e18-s0 runs/b-xl-s1-e18-s1 runs/b-xl-s1-e18-s2 2>/dev/null
} > reports/e19-rewording-3seeds.md
cat reports/e19-rewording-3seeds.md
echo "$(date +%H:%M) E19 COMPLETE"
