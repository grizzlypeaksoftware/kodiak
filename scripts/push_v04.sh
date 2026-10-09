#!/bin/bash
# v0.4 release upload (Shane approved the cards, 2026-10-08). Public repos under cortex-agent-llc.
set -u
cd "$(dirname "$0")/.."
eval "$(grep -E '^\s*export HUGGINGFACE_API_KEY=' ~/.bashrc | tail -1)" && export HF_TOKEN="$HUGGINGFACE_API_KEY"
export HF_HUB_DISABLE_XET=1  # the Xet upload stalled at 48 MB (2026-10-02); plain LFS upload instead
uv run --no-sync python -m kodiak_s1.hub push --folder dist/kodiak-v0.4-1b --repo cortex-agent-llc/kodiak-v0.4-1b --message "Kodiak-v0.4-1B" \
  || { echo "PUSH FAILED single"; exit 1; }
uv run --no-sync python - <<'PY' || { echo "PUSH FAILED accuracy"; exit 1; }
from huggingface_hub import HfApi
a = HfApi()
a.create_repo("cortex-agent-llc/kodiak-v0.4-1b-accuracy", exist_ok=True)
a.upload_folder(repo_id="cortex-agent-llc/kodiak-v0.4-1b-accuracy", folder_path="dist/kodiak-v0.4-1b-accuracy",
                commit_message="Kodiak-v0.4-1B accuracy mode (3 models)")
print("pushed accuracy mode")
PY
echo "PUSH V04 COMPLETE"
