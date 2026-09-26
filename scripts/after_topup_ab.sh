#!/bin/bash
# Wait for the gen2 top-up run to finish (a second "done:" line in the log), then start the generator A/B.
cd "$(dirname "$0")/.."
until [ "$(grep -c '^done:' data/synthetic/gen2_v20.log)" -ge 2 ]; do sleep 60; done
echo "$(date +%H:%M) top-up finished: $(grep '^done:' data/synthetic/gen2_v20.log | tail -1)"
exec scripts/ab_test.sh
