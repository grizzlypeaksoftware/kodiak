#!/bin/bash
# E21 (approved): v0.2 recipe (E19) + skills batch 2 (pairwise judge, sarcasm, policy violation; 2,500 each). One variable: the data mix.
# Waits for the skills-2 batch, samples it, smoke at step 500 vs E18 seed 1 (= v0.2 seed 1), full run, then scores: skills-2 eval + MT-Bench
# anchor, eval v0.2, E17 skills, wording eval, ranking, probe. Keep line in docs/experiments/E21-skills-batch-2.md.
set -u
cd "$(dirname "$0")/.."
P=docs/experiments/E21-skills-batch-2.md
uv run python scripts/gate.py $P || exit 1
until grep -q SKILLS2_BATCH_DONE data/synthetic/skills2_v1.log; do sleep 60; done
uv run python scripts/e21_subsample.py || exit 1
echo "$(date +%H:%M) GPU free"
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/skills_v1_e17_10k.jsonl,data/synthetic/skills2_v1_e21_7k5.jsonl; OUT=reports/preds_v02
seed=1; name=e21-xl-skills2-s$seed; run=runs/b-xl-s1-e21-s$seed; base=runs/b-xl-s1-e18-s1
echo "$(date +%H:%M) === training $run (smoke check at step 500)"
uv run python -m kodiak_s1.train --run $run --preset xl --init modernbert --synthetic "$SYN" --seed $seed \
  --option-wordings data/wordings/train.json --p-option-wording 0.5 \
  --steps 6000 --lr 3e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 >> $run.log 2>&1 &
TP=$!
until grep -q '"event": "eval", "step": 500' $run/metrics.jsonl 2>/dev/null || ! kill -0 $TP 2>/dev/null; do sleep 30; done
if ! uv run python scripts/smoke_check.py $run $base --step 500; then
  echo "SMOKE FAILED: stopping $run"; kill $TP; echo "E21 STOPPED"; exit 1
fi
echo "$(date +%H:%M) SMOKE PASS"
if ! uv run python scripts/gate.py $P --full; then
  until [ -f $run/checkpoints/step_0000500.pt ] || ! kill -0 $TP 2>/dev/null; do sleep 10; done; sleep 30
  kill $TP; echo "$(date +%H:%M) waiting for Shane's approval; rerun scripts/e21_run.sh to resume from step 500"; echo "E21 PAUSED"; exit 0
fi
echo "$(date +%H:%M) approved; full run continues"
wait $TP || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
cat data/eval/kodiak-skills2-eval-v0.1.jsonl data/eval/kodiak-skills2-anchor-mtbench-v0.1.jsonl > /tmp/e21-skills2-all.jsonl
for ev in "data/eval/kodiak-eval-v0.2.jsonl $OUT" "data/eval/kodiak-skills-eval-v0.1.jsonl reports/preds_skills" \
          "data/eval/kodiak-wording-eval-v0.1.jsonl reports/preds_wording" "/tmp/e21-skills2-all.jsonl reports/preds_skills2"; do
  set -- $ev
  uv run python -m kodiak_s1.eval.run predict --model $ckpt --name $name --calibration $run/calibration-final-thr.json --eval $1 \
    --out $2/$name.jsonl 2>&1 | grep -v -i warn | tail -1
done
{
  echo "# E21 result: skills batch 2 (seed $seed) vs Kodiak-v0.2-1B (seed 1)"; echo
  echo "Keep line (set before the run): skills-2 score >= 0.392 (0.142), each kind +0.10, MT-Bench anchor >= +0.040; guards: never-seen >= 0.679,"
  echo "familiar >= 0.87, abstain precision >= 0.86, E17 skills >= 0.95, ranking >= 0.541, wording consistency >= 0.66, probe >= 5 of 8."; echo
  echo "## Skills-2 eval (+ MT-Bench anchor)"; echo; echo '```'''
  uv run python scripts/skills2_score.py reports/preds_skills2/v02-s1-baseline.jsonl reports/preds_skills2/$name.jsonl
  echo '```'; echo; echo "## Wording eval"; echo; echo '```'
  uv run python scripts/wording_score.py reports/preds_wording/e18-xl-wording-s1.jsonl reports/preds_wording/$name.jsonl
  echo '```'; echo; echo "## Skills eval"; echo; echo '```'
  uv run python scripts/skills_score.py reports/preds_skills/e18-xl-wording-s1.jsonl reports/preds_skills/$name.jsonl
  echo '```'; echo; echo "## Eval v0.2"; echo
  PRED_DIR=$OUT uv run python scripts/seed_summary.py --groups "v0.2 (seed 1)=e18-xl-wording-s1" "E21 (seed 1)=$name" 2>/dev/null
  echo; echo "## Ranking (never-seen aurc_gap_closed)"; echo
  uv run python -m kodiak_s1.eval.run report $OUT/e18-xl-wording-s1.jsonl $OUT/$name.jsonl --out reports/e21-report-tmp.md > /dev/null 2>&1
  python3 -c "
import json; d=json.load(open('reports/e21-report-tmp.json'))
for k, v in d.items():
    def f(o, p=''):
        if isinstance(o, dict):
            if 'aurc_gap_closed' in o and p.endswith('eval:heldout'): print(f'- {k}: {o[\"aurc_gap_closed\"]:.3f}')
            for kk, vv in o.items(): f(vv, p + '/' + kk)
    f(v)"
  echo; echo "## Label-overlap probe"; echo
  uv run python scripts/probe_label_overlap.py $base $run 2>/dev/null
} > reports/e21-xl-skills2.md
cat reports/e21-xl-skills2.md
echo "$(date +%H:%M) E21 COMPLETE"
