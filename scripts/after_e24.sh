#!/bin/bash
# Runs the model check once E24 has finished (taking turns on the GPU).
cd "$(dirname "$0")/.."
until grep -qE "E24 COMPLETE|E24 STOPPED|training failed" runs/e24-run.log; do sleep 120; done
bash scripts/model_check.sh
