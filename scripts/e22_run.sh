#!/bin/bash
# E22 (approved): v0.2 recipe + skills-2 sample + skills-3 sample. Seed 1 first (smoke at step 500), stop rule after seed 1, then seeds 0 and 2;
# verdict on 3-seed means (scripts/e22_verdict.py). Waits for the skills-3 batch.
set -u
cd "$(dirname "$0")/.."
uv run python scripts/gate.py docs/experiments/E22-skills-batch-3.md --full || exit 1
until grep -q SKILLS3_BATCH_DONE data/synthetic/skills3_v1.log; do sleep 60; done
uv run python scripts/e22_subsample.py || exit 1
echo "$(date +%H:%M) GPU free"
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/skills_v1_e17_10k.jsonl,data/synthetic/skills2_v1_e21_7k5.jsonl,data/synthetic/skills3_v1_e22_10k.jsonl
OUT=reports/preds_v02
cat data/eval/kodiak-skills2-eval-v0.1.jsonl data/eval/kodiak-skills3-eval-v0.1.jsonl > /tmp/e22-skills-synth.jsonl
for seed in 1 0 2; do
  name=e22-xl-skills3-s$seed; run=runs/b-xl-s1-e22-s$seed; base=runs/b-xl-s1-e18-s$seed
  echo "$(date +%H:%M) === training $run"
  uv run python -m kodiak_s1.train --run $run --preset xl --init modernbert --synthetic "$SYN" --seed $seed \
    --option-wordings data/wordings/train.json --p-option-wording 0.5 \
    --steps 6000 --lr 3e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 > $run.log 2>&1 &
  TP=$!
  until grep -q '"event": "eval", "step": 500' $run/metrics.jsonl 2>/dev/null || ! kill -0 $TP 2>/dev/null; do sleep 30; done
  uv run python scripts/smoke_check.py $run $base --step 500 || { echo "SMOKE FAILED: $run"; kill $TP; echo "E22 STOPPED"; exit 1; }
  echo "SMOKE PASS (seed $seed)"
  wait $TP || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  for ev in "data/eval/kodiak-eval-v0.2.jsonl $OUT/$name" "data/eval/kodiak-real-anchors-v0.1.jsonl reports/preds_anchors/e22-s$seed" \
            "data/eval/kodiak-trap-eval-v0.1.jsonl reports/preds_trap/e22-s$seed" "/tmp/e22-skills-synth.jsonl reports/preds_skills3/$name" \
            "data/eval/kodiak-skills-eval-v0.1.jsonl reports/preds_skills/$name" "data/eval/kodiak-wording-eval-v0.1.jsonl reports/preds_wording/$name" \
            "data/eval/kodiak-probes-real-v0.1.jsonl reports/preds_probes/e22-s$seed-real"; do
    set -- $ev
    uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $1 \
      --out $2.jsonl 2>&1 | grep -v -i warn | tail -1
  done
  echo "$(date +%H:%M) seed $seed done"
  if [ $seed = 1 ]; then
    uv run python scripts/e22_verdict.py --seeds 1 | tee runs/e22-seed1-check.txt
    [ ${PIPESTATUS[0]} = 0 ] || { echo "E22 STOPPED after seed 1 (stop rule)"; echo "E22 COMPLETE"; exit 0; }
  fi
done
{
  echo "# E22 result: 3 seeds vs Kodiak-v0.2-1B (lines set before the run)"; echo; echo '```'
  uv run python scripts/e22_verdict.py --seeds 0,1,2
  echo '```'; echo; echo "## Synthetic held-out skills (report only)"; echo; echo '```'
  uv run python scripts/skills2_score.py reports/preds_skills3/e22-xl-skills3-s{0,1,2}.jsonl
  echo '```'; echo; echo "## Real-data probes incl. aspect sentiment (report only)"; echo; echo '```'
  uv run python scripts/skills2_score.py reports/preds_probes/e22-s{0,1,2}-real.jsonl
  echo '```'; echo
  PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "v0.2 (3 seeds)=e18-xl-wording-s0,e18-xl-wording-s1,e18-xl-wording-s2" \
    "E22 (3 seeds)=e22-xl-skills3-s0,e22-xl-skills3-s1,e22-xl-skills3-s2" 2>/dev/null
} > reports/e22-xl-skills3.md
cat reports/e22-xl-skills3.md
echo "$(date +%H:%M) E22 COMPLETE"
