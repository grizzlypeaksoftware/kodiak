#!/bin/bash
cd "$(dirname "$0")/.."
until grep -qE "A/B complete|training failed" runs/generator-ab.log; do sleep 60; done
grep -q "training failed" runs/generator-ab.log && { echo "A/B failed; not starting seed repeats"; exit 1; }
exec scripts/seed_repeats.sh
