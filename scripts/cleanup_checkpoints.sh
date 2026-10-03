#!/bin/bash
# Free disk: delete model weights (checkpoints/ and best.pt) from abandoned or superseded small-model runs (approved by Shane 2026-10-01).
# Keeps every run's record (config, metrics.jsonl, logs, calibration, best.json) and the published small runs (B-v2, R1-cap3).
#   scripts/cleanup_checkpoints.sh          # dry run: list what would be deleted, with sizes
#   scripts/cleanup_checkpoints.sh --delete # delete
set -u
cd "$(dirname "$0")/.."
KEEP=" b-small-s1-B-v2 b-small-s1-R1-cap3 "
targets=()
for d in runs/b-small-s1-*/ runs/p3-overfit-*/; do
  r=$(basename "$d")
  [[ "$KEEP" == *" $r "* ]] && continue
  for t in "$d"checkpoints "$d"best.pt; do [ -e "$t" ] && targets+=("$t"); done
done
[ ${#targets[@]} -eq 0 ] && { echo "nothing to delete"; exit 0; }
du -shc "${targets[@]}" | tail -1
if [ "${1:-}" = "--delete" ]; then
  rm -rf "${targets[@]}" && echo "deleted ${#targets[@]} items"; df -h / | tail -1
else
  printf '%s\n' "${targets[@]}" | sed 's#/checkpoints$# (checkpoints)#; s#/best.pt$# (best.pt)#' | sort | uniq | head -100
  echo "(dry run; add --delete to remove)"
fi
