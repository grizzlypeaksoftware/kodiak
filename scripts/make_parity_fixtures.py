"""Write server/test/fixtures/parity.json: requests plus the Python package's packing and answers, for the Node parity tests (D35).

    CUDA_VISIBLE_DEVICES="" uv run python scripts/make_parity_fixtures.py runs/onnx/kodiak-small-v2
"""

import json
import random
import sys
from pathlib import Path

from kodiak_s1.hub import Kodiak
from kodiak_s1.onnx_export import FIXTURES, _normalize
from kodiak_s1.packing import Limits, pack_example

folder = sys.argv[1] if len(sys.argv) > 1 else "runs/onnx/kodiak-small-v2"
evalset = [json.loads(line) for line in open("data/eval/kodiak-eval-v0.2.jsonl")]
reqs = list(FIXTURES) + [{"state": e["state"], "questions": e["questions"]} for e in random.Random(7).sample(evalset, 40)]
reqs.append({"state": ["hi there", "I need a refund"],
             "questions": [{"type": "score", "id": "s", "text": "How angry?", "min": 1, "max": 5, "step": 1, "min_label": "calm",
                            "max_label": "furious"},
                           {"type": "choice", "id": "c", "text": "Topic?", "labels": ["billing", "shipping"], "allow_null": False}],
             "options": {"min_confidence": 0.9, "interval": 0.8}})
k = Kodiak.from_pretrained(folder, device="cpu")
k.model.float()
cases = []
for r in reqs:
    p = pack_example(_normalize([r])[0], Limits(), with_targets=False)
    cases.append({"request": r, "ids": p.ids, "pos": p.pos, "role": p.role, "qi": p.qi, "li": p.li,
                  "response": k.answer([r])[0]["answers"]})
out = Path("server/test/fixtures/parity.json")
out.write_text(json.dumps({"model": Path(folder).name, "cases": cases}))
print(f"{len(cases)} cases -> {out}")
