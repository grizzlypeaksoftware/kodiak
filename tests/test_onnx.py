import pytest
import torch

from kodiak_s1.hub import Kodiak
from kodiak_s1.model import EncoderConfig, HeadConfig, KodiakModel, ModelConfig

pytest.importorskip("onnxruntime")
pytest.importorskip("onnxscript")

MICRO = EncoderConfig(vocab_size=50368, hidden_size=64, intermediate_size=96, num_layers=3, num_heads=4)


def test_export_matches_pytorch_with_dynamic_shapes(tmp_path):
    from kodiak_s1.onnx_export import check, export

    torch.manual_seed(0)
    Kodiak(KodiakModel(ModelConfig(MICRO, HeadConfig())).eval(), {"t_choice": 1.3, "t_null": 0.8}).save_pretrained(tmp_path)
    out = export(tmp_path, tmp_path / "model.onnx")
    # Requests with other lengths, question counts and label counts than the export trace, alone and packed together.
    extra = [{"state": ["first message", "second, much longer message " * 20],
              "questions": [{"type": "choice", "id": f"q{i}", "text": "Which one?", "labels": [f"option {j}" for j in range(2 + i)]}
                            for i in range(5)]},
             {"state": {"a": 1, "b": [1, 2, 3]}, "questions": [{"type": "score", "id": "s", "text": "How much?", "min": -5, "max": 5}]}]
    assert check(tmp_path, out, extra) < 1e-3
