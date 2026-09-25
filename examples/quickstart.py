"""Kodiak quickstart: one state, three typed questions, one forward pass.

    uv run python examples/quickstart.py [model]     # default: the private preview (needs HF_TOKEN) or a local folder
"""

import json
import sys

from kodiak_s1.hub import Kodiak

model = sys.argv[1] if len(sys.argv) > 1 else "cortex-agent-llc/kodiak-small-r1-preview"
kodiak = Kodiak.from_pretrained(model)

state = {"order_id": "A-1042", "status": "delivered", "message": "The box arrived crushed and the lamp is broken."}
questions = [
    {"type": "choice", "id": "intent", "text": "What does the customer want?",
     "labels": ["refund or replacement", "delivery status", "cancel order", "product question"]},
    {"type": "score", "id": "urgency", "text": "How urgent is this?", "min": 0, "max": 10,
     "min_label": "can wait", "max_label": "act immediately"},
    {"type": "choice", "id": "carrier", "text": "Which carrier delivered it?", "labels": ["UPS", "FedEx", "USPS"]},
]
print(json.dumps(kodiak.decide(state, questions), indent=2, default=float))
