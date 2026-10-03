"""Before trimming a kept run: save its last checkpoint's model weights as runs/<run>/final.pt (no optimizer state) and verify it matches.
    uv run python scripts/extract_final_weights.py runs/<run> [...]"""
import sys
from pathlib import Path

import torch

for run in map(Path, sys.argv[1:]):
    ckpts = sorted((run / "checkpoints").glob("step_*.pt"))
    if not ckpts:
        print(f"{run}: no checkpoints (already trimmed?)")
        continue
    state = torch.load(ckpts[-1], map_location="cpu", weights_only=False)
    out = run / "final.pt"
    torch.save(state["model"], out)
    back = torch.load(out, map_location="cpu", weights_only=False)
    same = back.keys() == state["model"].keys() and all(torch.equal(back[k], state["model"][k]) for k in back)
    (run / "final.txt").write_text(f"final.pt = model weights of {ckpts[-1].name} (step {state['step']}); optimizer state not kept\n")
    print(f"{run}: {ckpts[-1].name} -> final.pt ({out.stat().st_size / 1e9:.1f} GB), identical: {same}")
    if not same:
        sys.exit(1)
