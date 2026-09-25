import json

import torch

from kodiak_s1.hub import Kodiak
from kodiak_s1.model import EncoderConfig, HeadConfig, KodiakModel, ModelConfig

MICRO = EncoderConfig(vocab_size=50368, hidden_size=64, intermediate_size=96, num_layers=3, num_heads=4)
QS = [{"type": "choice", "id": "intent", "text": "What does the customer want?", "labels": ["refund", "track order"]},
      {"type": "score", "id": "urgency", "text": "How urgent?", "min": 0, "max": 10}]


def test_save_load_roundtrip_applies_calibration_and_default_threshold(tmp_path):
    torch.manual_seed(0)
    cal = {"t_choice": 1.5, "t_null": 1.4, "kappa_scale": 0.7, "null_threshold": 0.99}
    k = Kodiak(KodiakModel(ModelConfig(MICRO, HeadConfig())).eval(), cal)
    k.save_pretrained(tmp_path, tokenizer_json=None)
    assert {p.name for p in tmp_path.iterdir()} >= {"model.safetensors", "model_config.json", "calibration.json", "tokenizer.json"}
    k2 = Kodiak.from_pretrained(str(tmp_path), device="cpu")
    assert abs(float(k2.model.heads.t_choice) - 1.5) < 1e-6  # assigned, not multiplied (weights already had it baked in)
    assert k2.default_options == {"null_threshold": 0.99}
    a, b = k.decide("I was charged twice!", QS), k2.decide("I was charged twice!", QS)
    assert a["intent"]["probs"] == b["intent"]["probs"]
    # A per-request option overrides the calibrated default.
    loose = k2.decide("I was charged twice!", QS, null_threshold=1.0)
    assert loose["intent"]["answer"] is not None
    assert json.loads((tmp_path / "calibration.json").read_text())["null_threshold"] == 0.99
