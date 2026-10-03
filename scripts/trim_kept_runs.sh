#!/bin/bash
# Free disk on the runs we keep (approved by Shane 2026-10-01): delete checkpoints/ (weights + optimizer state, last 3 steps) only where a
# verified final.pt exists (scripts/extract_final_weights.py). Keeps final.pt (last-step weights), best.pt (best-validation weights) and the record.
#   scripts/trim_kept_runs.sh          # dry run
#   scripts/trim_kept_runs.sh --delete
set -u
cd "$(dirname "$0")/.."
targets=()
for d in runs/*/; do
  [ -d "${d}checkpoints" ] || continue
  if [ -f "${d}final.pt" ] && [ -f "${d}final.txt" ]; then targets+=("${d}checkpoints"); fi
done
[ ${#targets[@]} -eq 0 ] && { echo "nothing to delete"; exit 0; }
du -shc "${targets[@]}"
if [ "${1:-}" = "--delete" ]; then
  rm -rf "${targets[@]}" && echo "deleted ${#targets[@]} checkpoint folders"; df -h / | tail -1
else
  echo "(dry run; add --delete to remove)"
fi
