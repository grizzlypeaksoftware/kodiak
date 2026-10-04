#!/bin/bash
# E21 confirmation (Shane: option B, D63): seeds 0 and 2, identical recipe; guards judged on 3-seed means (rule in the proposal, written first).
set -u
cd "$(dirname "$0")/.."
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/skills_v1_e17_10k.jsonl,data/synthetic/skills2_v1_e21_7k5.jsonl; OUT=reports/preds_v02
cat data/eval/kodiak-skills2-eval-v0.1.jsonl data/eval/kodiak-skills2-anchor-mtbench-v0.1.jsonl > /tmp/e21-skills2-all.jsonl
for seed in 0 2; do
  name=e21-xl-skills2-s$seed; run=runs/b-xl-s1-e21-s$seed; base=runs/b-xl-s1-e18-s$seed
  echo "$(date +%H:%M) === training $run"
  uv run python -m kodiak_s1.train --run $run --preset xl --init modernbert --synthetic "$SYN" --seed $seed \
    --option-wordings data/wordings/train.json --p-option-wording 0.5 \
    --steps 6000 --lr 3e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 > $run.log 2>&1 &
  TP=$!
  until grep -q '"event": "eval", "step": 500' $run/metrics.jsonl 2>/dev/null || ! kill -0 $TP 2>/dev/null; do sleep 30; done
  uv run python scripts/smoke_check.py $run $base --step 500 || { echo "SMOKE FAILED: $run"; kill $TP; echo "E21 CONFIRM STOPPED"; exit 1; }
  wait $TP || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  for ev in "data/eval/kodiak-eval-v0.2.jsonl $OUT" "data/eval/kodiak-skills-eval-v0.1.jsonl reports/preds_skills" \
            "data/eval/kodiak-wording-eval-v0.1.jsonl reports/preds_wording" "/tmp/e21-skills2-all.jsonl reports/preds_skills2"; do
    set -- $ev
    uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $1 \
      --out $2/$name.jsonl 2>&1 | grep -v -i warn | tail -1
  done
  echo "$(date +%H:%M) seed $seed done"
done
{
  echo "# E21 confirmation: v0.2 + skills-2, 3 seeds vs Kodiak-v0.2-1B 3 seeds"; echo
  echo "Rule (written before these seeds ran, D63 option B): every line judged on 3-seed means; see docs/experiments/E21-skills-batch-2.md."; echo
  echo "## Skills-2 eval (+ MT-Bench anchor)"; echo; echo '```'
  uv run python scripts/skills2_score.py reports/preds_skills2/v02-s1-baseline.jsonl reports/preds_skills2/e21-xl-skills2-s{0,1,2}.jsonl
  echo '```'; echo
  PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "v0.2 (3 seeds)=e18-xl-wording-s0,e18-xl-wording-s1,e18-xl-wording-s2" \
    "E21 (3 seeds)=e21-xl-skills2-s0,e21-xl-skills2-s1,e21-xl-skills2-s2" 2>/dev/null
  echo; echo "## Skills eval"; echo; echo '```'
  uv run python scripts/skills_score.py reports/preds_skills/e21-xl-skills2-s{0,1,2}.jsonl
  echo '```'; echo; echo "## Wording eval"; echo; echo '```'
  uv run python scripts/wording_score.py reports/preds_wording/e18-xl-wording-s{0,1,2}.jsonl reports/preds_wording/e21-xl-skills2-s{0,1,2}.jsonl
  echo '```'; echo; echo "## Ranking (never-seen aurc_gap_closed)"; echo
  uv run python -m kodiak_s1.eval.run report $OUT/e18-xl-wording-s{0,1,2}.jsonl $OUT/e21-xl-skills2-s{0,1,2}.jsonl --out reports/e21-confirm-tmp.md > /dev/null 2>&1
  python3 -c "
import json; d=json.load(open('reports/e21-confirm-tmp.json'))
for k, v in d.items():
    def f(o, p=''):
        if isinstance(o, dict):
            if 'aurc_gap_closed' in o and p.endswith('eval:heldout'): print(f'- {k}: {o[\"aurc_gap_closed\"]:.3f}')
            for kk, vv in o.items(): f(vv, p + '/' + kk)
    f(v)"
  echo; echo "## Label-overlap probe"; echo
  uv run python scripts/probe_label_overlap.py runs/b-xl-s1-e18-s0 runs/b-xl-s1-e18-s1 runs/b-xl-s1-e18-s2 runs/b-xl-s1-e21-s0 runs/b-xl-s1-e21-s1 runs/b-xl-s1-e21-s2 2>/dev/null
} > reports/e21-xl-skills2-3seeds.md
cat reports/e21-xl-skills2-3seeds.md
echo "$(date +%H:%M) E21 CONFIRM COMPLETE"
