import csv
import json
from types import SimpleNamespace

import torch

from kodiak_s1.hub import Kodiak
from kodiak_s1.model import EncoderConfig, HeadConfig, KodiakModel, ModelConfig

MICRO = EncoderConfig(vocab_size=50368, hidden_size=64, intermediate_size=96, num_layers=2, num_heads=4)


def test_finetune_end_to_end_on_a_tiny_model(tmp_path):
    from kodiak_s1.finetune import finetune

    torch.manual_seed(0)
    base = tmp_path / "base"
    Kodiak(KodiakModel(ModelConfig(MICRO, HeadConfig())).eval(), {"null_threshold": 0.6}).save_pretrained(base)
    rows = [(f"My order {i} never arrived, where is it?", "shipping") if i % 2 else (f"I was charged twice on invoice {i}.", "billing")
            for i in range(40)]
    path = tmp_path / "t.csv"
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows([("text", "team"), *rows])
    a = SimpleNamespace(csv=str(path), text_column="text", label_column="team", question="Which team?", base=str(base),
                        out=str(tmp_path / "out"), epochs=1, lr=1e-4, batch=8, test_share=0.2, max_state=128, seed=0, device="cpu")
    r = finetune(a)
    assert r["labels"] == ["billing", "shipping"] and r["test"] == 10 and r["train"] + r["calibration"] == 30
    assert {"forced_accuracy", "ece", "answered_share"} <= set(r["after"])
    k = Kodiak.from_pretrained(a.out, device="cpu")  # a normal model folder, calibration included
    assert "null_threshold" in k.calibration
    assert json.loads((tmp_path / "out" / "finetune_report.json").read_text())["rows"] == 40
