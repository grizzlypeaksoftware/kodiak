"""Load, use and publish Kodiak models: the release-facing API.

    from kodiak_s1.hub import Kodiak

    kodiak = Kodiak.from_pretrained("cortex-agent-llc/kodiak-small-r1-preview")   # or a local folder
    kodiak.decide(
        "I was charged twice for my order and nobody answers my emails!",
        [{"type": "choice", "id": "intent", "text": "What does the customer want?", "labels": ["refund", "track order", "cancel"]},
         {"type": "score", "id": "urgency", "text": "How urgent is this?", "min": 0, "max": 10}],
    )

A model folder holds `model.safetensors`, `model_config.json`, `calibration.json` and `tokenizer.json`.
Calibration (three temperatures fit on validation data) is *assigned* to the model's buffers on load, so loading
weights that already contain it is harmless. The tuned abstain threshold becomes the default for every request;
a request's own `options.null_threshold` still wins.

Export a trained checkpoint to a model folder (and optionally push it to the Hub):

    uv run python -m kodiak_s1.hub export --ckpt runs/b-small-s1-R1-cap3/checkpoints/step_0006000.pt \\
        --calibration runs/b-small-s1-R1-cap3/calibration-final-thr.json --out dist/kodiak-small-r1
    uv run python -m kodiak_s1.hub push --folder dist/kodiak-small-r1 --repo cortex-agent-llc/kodiak-small-r1-preview --private
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import torch

from kodiak_s1.infer import answer
from kodiak_s1.model import KodiakModel, ModelConfig

FILES = ("model.safetensors", "model_config.json", "calibration.json", "tokenizer.json")
CAL_KEYS = ("t_choice", "t_null", "kappa_scale")


def _resolve(name_or_path: str, revision: str | None, token: str | None) -> Path:
    p = Path(name_or_path)
    if p.is_dir():
        return p
    from huggingface_hub import snapshot_download

    return Path(snapshot_download(name_or_path, revision=revision, token=token, allow_patterns=list(FILES) + ["README.md"]))


def apply_calibration(model: KodiakModel, cal: dict) -> None:
    for k in CAL_KEYS:
        if k in cal:
            getattr(model.heads, k).fill_(float(cal[k]))


class Kodiak:
    def __init__(self, model: KodiakModel, calibration: dict | None = None, name: str = "kodiak"):
        self.model = model
        self.calibration = calibration or {}
        self.name = name
        self.default_options = {"null_threshold": float(self.calibration.get("null_threshold", 0.5))}

    @classmethod
    def from_pretrained(cls, name_or_path: str, device: str = "auto", revision: str | None = None,
                        token: str | None = None) -> Kodiak:
        from safetensors.torch import load_file

        folder = _resolve(name_or_path, revision, token)
        model = KodiakModel(ModelConfig.load(folder / "model_config.json"))
        model.load_state_dict(load_file(folder / "model.safetensors"))
        cal = json.loads((folder / "calibration.json").read_text()) if (folder / "calibration.json").exists() else {}
        apply_calibration(model, cal)
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        return cls(model.to(device).eval(), cal, name=Path(name_or_path).name)

    def answer(self, requests: list[dict]) -> list[dict]:
        """Full Request dicts (see kodiak_s1.schema) in, Response dicts out."""
        reqs = [{**r, "options": {**self.default_options, **(r.get("options") or {})}} for r in requests]
        return answer(self.model, reqs, model_name=self.name)

    def decide(self, state: Any, questions: list[dict], **options) -> dict:
        """One state, its questions -> {question id: answer}."""
        req = {"state": state, "questions": questions}
        if options:
            req["options"] = options
        return self.answer([req])[0]["answers"]

    def save_pretrained(self, out: str | Path, tokenizer_json: str | Path | None = None) -> Path:
        from safetensors.torch import save_file

        from kodiak_s1.tokenizer import TOKENIZER_REPO

        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        apply_calibration(self.model, self.calibration)  # bake the temperatures into the weights too
        save_file({k: v.detach().cpu().contiguous() for k, v in self.model.state_dict().items()},
                  out / "model.safetensors", metadata={"format": "pt"})
        self.model.cfg.save(out / "model_config.json")
        (out / "calibration.json").write_text(json.dumps(self.calibration, indent=2) + "\n")
        if tokenizer_json is None:
            from huggingface_hub import hf_hub_download

            tokenizer_json = hf_hub_download(TOKENIZER_REPO, "tokenizer.json")
        shutil.copy(tokenizer_json, out / "tokenizer.json")
        return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export", help="training checkpoint + calibration -> model folder")
    e.add_argument("--ckpt", required=True)
    e.add_argument("--calibration", required=True)
    e.add_argument("--out", required=True)
    p = sub.add_parser("push", help="upload a model folder to the Hugging Face Hub (token from $HF_TOKEN)")
    p.add_argument("--folder", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--private", action="store_true")
    p.add_argument("--message", default="Upload Kodiak model")
    a = ap.parse_args(argv)
    if a.cmd == "export":
        from kodiak_s1.infer import load

        k = Kodiak(load(a.ckpt, device="cpu"), json.loads(Path(a.calibration).read_text()))
        out = k.save_pretrained(a.out)
        print(f"exported to {out}: {sorted(f.name for f in out.iterdir())}")
    else:
        from huggingface_hub import HfApi

        api = HfApi()
        api.create_repo(a.repo, private=a.private, exist_ok=True)
        api.upload_folder(repo_id=a.repo, folder_path=a.folder, commit_message=a.message)
        print(f"pushed {a.folder} -> https://huggingface.co/{a.repo}")


if __name__ == "__main__":
    main()
