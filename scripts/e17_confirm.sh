#!/bin/bash
# E17 confirming seeds (approved plan: 2 confirm seeds only if the full run clears the bar; seed 1 did on 2026-09-30).
# Same recipe as scripts/e17_run.sh, seeds 0 and 2 (as XL v2), then a 3-seed vs 3-seed summary.
set -u
cd "$(dirname "$0")/.."
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/skills_v1_e17_10k.jsonl; OUT=reports/preds_v02
for seed in 0 2; do
  name=e17-xl-skills-s$seed; run=runs/b-xl-s1-e17-s$seed
  echo "$(date +%H:%M) === training $run"
  uv run python -m kodiak_s1.train --run $run --preset xl --init modernbert --synthetic "$SYN" --seed $seed \
    --steps 6000 --lr 3e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 \
    > $run.log 2>&1 || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json \
    --eval data/eval/kodiak-eval-v0.2.jsonl --latency-n 50 --out $OUT/$name.jsonl 2>&1 | grep -v -i warn | tail -1
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json \
    --eval data/eval/kodiak-skills-eval-v0.1.jsonl --out reports/preds_skills/$name.jsonl 2>&1 | grep -v -i warn | tail -1
  echo "$(date +%H:%M) seed $seed done"
done
{
  echo "# E17 confirmation: XL v2 vs XL v2 + skills, 3 seeds each"; echo
  echo "## Skills eval"; echo; echo '```'
  uv run python scripts/skills_score.py reports/preds_skills/xl-s1-baseline.jsonl reports/preds_skills/e17-xl-skills-s{0,1,2}.jsonl
  echo '```'; echo
  PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "xl v2=xl-v2-s0,xl-v2-s1,xl-v2-s2" \
    "xl v2 + skills (E17)=e17-xl-skills-s0,e17-xl-skills-s1,e17-xl-skills-s2" 2>/dev/null
  echo; echo "## Label-overlap probe"; echo
  uv run python scripts/probe_label_overlap.py runs/b-xl-s1-v2-s0 runs/b-xl-s1-v2-s1 runs/b-xl-s1-v2-s2 runs/b-xl-s1-e17-s0 runs/b-xl-s1-e17-s1 runs/b-xl-s1-e17-s2 2>/dev/null
} > reports/e17-xl-skills-3seeds.md
cat reports/e17-xl-skills-3seeds.md
echo "$(date +%H:%M) E17 CONFIRM COMPLETE"
