"""Hugging Face Inference Endpoints handler for Kodiak (copied into every exported model folder).

Deploy: model page -> Deploy -> Inference Endpoints (CPU is enough; ~80 ms per request on 8 cores). The endpoint installs
`requirements.txt` from the repo, then calls EndpointHandler for each request.

Request body (one request or a list):
    {"inputs": {"state": "...", "questions": [...], "options": {...}}}
    {"inputs": [{"state": ..., "questions": [...]}, ...]}
Response: the Kodiak Response for each request (see the repo's schema/ folder).
"""

from typing import Any

from kodiak_s1.hub import Kodiak


class EndpointHandler:
    def __init__(self, path: str = ""):
        self.kodiak = Kodiak.from_pretrained(path or ".")

    def __call__(self, data: dict[str, Any]) -> list[dict]:
        inputs = data.get("inputs", data)
        requests = inputs if isinstance(inputs, list) else [inputs]
        return self.kodiak.answer(requests)
