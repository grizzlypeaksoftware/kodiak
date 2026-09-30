"""Kodiak as a native engine for the Decision Index benchmark kit (github.com/apolinario/decision-index, MIT).

    python -m decision_index run --engine kodiak_s1.decision_index_engine:KodiakEngine \\
        --option model=cortex-agent-llc/kodiak-xl-v2-preview --rows sample-100.jsonl.gz --out runs/kodiak-xl-sample

The kit sends {state, questions}: each question is `choice` (instructions + criteria {option_key: description}, 2-255 options) or `noul`
(a yes/no probability). Kodiak answers every question of a request in one forward pass (its structured attention mask), with:
- **must answer:** each question is sent with allow_null=false (Kodiak's documented "must answer" setting); the benchmark counts abstentions as
  wrong, and this is declared in the run's provenance. Choice probabilities are Kodiak's calibrated distribution over the options.
- **no truncation:** state, question and option texts are packed whole. A request whose longest position exceeds the backbone's position limit,
  or whose packed length exceeds `max_tokens` (dense attention memory), is refused as `Unsupported` (counted as wrong by the kit).
- our API's 32-option and character limits are request-schema limits, not model limits, so the engine packs the kit's questions directly.
"""

from __future__ import annotations

import json

from decision_index.engines.base import Engine, Unsupported, text


class KodiakEngine(Engine):
    name = "kodiak"
    latency = "Device-synchronized in-process request wall time including tokenization and packing; excludes model loading."

    def __init__(self, model="cortex-agent-llc/kodiak-xl-v2-preview", device=None, max_tokens=12288, **options):
        super().__init__(**options)
        import torch

        from kodiak_s1.hub import Kodiak

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.kodiak = Kodiak.from_pretrained(model, device=self.device)
        self.model = self.kodiak.model
        self.max_tokens = int(max_tokens)
        self.max_position = 7999 if self.model.cfg.encoder.hidden_size == 1792 else 8191  # Ettin-1B / ModernBERT
        self.model_id = model
        self.provenance = {
            "kind": "kodiak",
            "repo": model,
            "device": self.device,
            "context_limit_positions": self.max_position,
            "packed_token_limit": self.max_tokens,
            "policy": "All questions of a request are answered in one forward pass (structured attention: state, then each question with its "
                      "options). Every question is sent with allow_null=false (Kodiak's 'must answer' setting; its 'can't tell' output is "
                      "not used). When the state is empty, the question text is also given as the state (Kodiak reads its state; same rule for every "
                      "benchmark). Choice probabilities are Kodiak's calibrated softmax over the supplied options; noul = p(yes) of a "
                      "yes/no choice. Nothing is truncated: requests beyond the position limit or the packed-token limit are refused as "
                      "unsupported. No prompt tuning; option texts are the kit's criteria verbatim (the key when a description is null).",
        }

    def runtime(self):
        info = {"torch": self.torch.__version__, "device": self.device}
        if self.device == "cuda":
            info.update(cuda=self.torch.version.cuda, gpu=self.torch.cuda.get_device_name())
        return info

    def synchronize(self):
        if self.device == "cuda":
            self.torch.cuda.synchronize()

    def _request(self, state, questions):
        qs, keys = [], []
        for i, (key, q) in enumerate(questions.items()):
            instr = text(q.get("instructions", "")) or "Choose the best option."
            if q["type"] == "choice":
                labels = [{"id": k, "text": k if d is None else text(d)} for k, d in q["criteria"].items()]
            elif q["type"] == "noul":
                labels = [{"id": "yes", "text": "yes"}, {"id": "no", "text": "no"}]
            else:
                raise Unsupported("unsupported question type " + str(q["type"]))
            qs.append({"type": "choice", "id": f"q{i}", "text": instr, "labels": labels, "allow_null": False})
            keys.append(key)
        if state in (None, "", {}, []):
            # Kodiak reads the *state*; its questions are short instructions (every training example has this shape). About a third of
            # the suite sends an empty state and puts the content inside the question ("Classify this request:\n<text>"). Mechanical
            # translation, the same for every benchmark (D50): the question texts become the state as well; the questions are unchanged.
            st = "\n\n".join(q["text"] for q in qs)
        else:
            st = state
        return {"state": st, "questions": qs}, keys

    def __call__(self, state, questions):
        from kodiak_s1.infer import raw_outputs
        from kodiak_s1.packing import Limits, pack_example

        req, keys = self._request(state, questions)
        big = Limits(max_state=10**9, max_question=10**9, max_label=10**9)
        packed = pack_example(req, big, with_targets=False)
        if packed.truncated:
            raise Unsupported("request would need truncation")
        if max(packed.pos) >= self.max_position:
            raise Unsupported(f"needs position {max(packed.pos)} > limit {self.max_position}")
        if len(packed) > self.max_tokens:
            raise Unsupported(f"packed length {len(packed)} tokens > limit {self.max_tokens}")
        try:
            raws = raw_outputs(self.model, [req], max_len=max(len(packed), 16), rows_per_batch=1, limits=big)[0]
        except self.torch.cuda.OutOfMemoryError as e:
            self.torch.cuda.empty_cache()
            raise Unsupported("out of GPU memory for this request") from e
        answers, raw_out = {}, {}
        for key, r, q in zip(keys, raws, questions.values()):
            probs = dict(zip(r["labels"], r["cond_probs"]))
            raw_out[key] = {"probs": probs, "p_null": r["p_null"]}
            if q["type"] == "noul":
                answers[key] = {"type": "noul", "noul": float(probs["yes"])}
            else:
                total = sum(probs.values()) or 1.0
                probs = {k: float(v) / total for k, v in probs.items()}
                answers[key] = {"type": "choice", "choice": max(probs, key=probs.get), "probabilities": probs}
        return {"model": self.model_id, "answers": answers, "usage": {"input_tokens": len(packed)}}, raw_out
