#!/bin/bash
# E25 (needs "Approved: Shane"): task variety at matched data. Four ModernBERT-large (396M) runs, seed 0, 6,000 steps, the v0.4 recipe's data:
# A7, B7 (7 random kinds, all their data), all28-matched (28 kinds at 86k unique examples), all28-full. Each is scored on the new-domains test
# (headline), eval v0.2 and the wording eval. Verdict: scripts/e25_verdict.py. Smoke rule: validation choice accuracy at step 500 >= 0.60.
set -u
cd "$(dirname "$0")/.."
uv run python scripts/gate.py docs/experiments/E25-task-variety.md --full || exit 1
SYN=data/synthetic/gen2_v20.jsonl,data/synthetic/skills_v1_e17_10k.jsonl,data/synthetic/skills2_v1_e21_7k5.jsonl,data/synthetic/skills3_v1_e23_5k.jsonl,data/synthetic/groups_cb_v1_e24_5k.jsonl
kinds() { python3 -c "import json;print(','.join(json.load(open('docs/experiments/E25-arms.json'))['$1']))"; }
for arm in A7 B7 all28m all28; do
  case $arm in
    A7|B7) K=$(kinds $arm); BUD=0 ;;
    all28m) K=$(kinds all28); BUD=110000 ;;
    all28) K=$(kinds all28); BUD=0 ;;
  esac
  run=runs/b-base-e25-$arm
  echo "$(date +%H:%M) === training $run"
  uv run python -m kodiak_s1.train --run $run --preset base --init modernbert --synthetic "$SYN" --seed 0 --kinds "$K" --kind-budget $BUD \
    --option-wordings data/wordings/train.json --p-option-wording 0.5 \
    --steps 6000 --lr 5e-5 --head-lr 5e-4 --warmup 300 --eval-every 250 --log-every 50 --ckpt-every 500 > $run.log 2>&1 &
  TP=$!
  until grep -q '"event": "eval", "step": 500' $run/metrics.jsonl 2>/dev/null || ! kill -0 $TP 2>/dev/null; do sleep 30; done
  ok=$(python3 -c "
import json
for l in open('$run/metrics.jsonl'):
    r=json.loads(l)
    if r.get('event')=='eval' and r.get('step')==500:
        a=[v['choice_acc'] for v in r.values() if isinstance(v,dict) and v.get('choice_acc')]
        print('%.3f'%(sum(a)/len(a)))" 2>/dev/null)
  echo "step 500 validation choice accuracy: ${ok:-none}"
  if [ -z "$ok" ] || ! python3 -c "import sys;sys.exit(0 if float('$ok')>=0.60 else 1)"; then echo "SMOKE FAILED: $run"; kill $TP; echo "E25 STOPPED"; exit 1; fi
  echo "SMOKE PASS ($arm)"
  wait $TP || { echo "training failed: $run"; tail -8 $run.log; exit 1; }
  ckpt=$(ls $run/checkpoints/step_*.pt | tail -1)
  uv run python -m kodiak_s1.eval.run calibrate --model $ckpt --synthetic "$SYN" --tune-threshold --out $run/calibration-final-thr.json 2>&1 | grep '"null_threshold"'
  for ev in "data/eval/kodiak-newdomain-v0.1.jsonl reports/preds_newdomain/e25-$arm" "data/eval/kodiak-eval-v0.2.jsonl reports/preds_v02/e25-$arm" \
            "data/eval/kodiak-wording-eval-v0.1.jsonl reports/preds_wording/e25-$arm"; do
    set -- $ev
    uv run python -m kodiak_s1.eval.run predict --model $ckpt --name e25-$arm --calibration $run/calibration-final-thr.json --eval $1 \
      --out $2.jsonl 2>&1 | grep -v -i warn | tail -1
  done
  echo "$(date +%H:%M) $arm done"
done
uv run python scripts/e25_verdict.py | tee reports/e25-task-variety.md
echo "$(date +%H:%M) E25 COMPLETE"
