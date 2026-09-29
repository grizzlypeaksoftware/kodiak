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

    return Path(snapshot_download(name_or_path, revision=revision, token=token,
                                  allow_patterns=list(FILES) + ["README.md", "ensemble.json"] + [f"*/{f}" for f in FILES]))


def apply_calibration(model: KodiakModel, cal: dict) -> None:
    for k in CAL_KEYS:
        if k in cal:
            getattr(model.heads, k).fill_(float(cal[k]))


class Kodiak:
    def __init__(self, model: KodiakModel, calibration: dict | None = None, name: str = "kodiak"):
        self.model = model
        self.calibration = calibration or {}
        apply_calibration(self.model, self.calibration)  # assigned, so applying twice is harmless
        self.name = name
        self.default_options = {"null_threshold": float(self.calibration.get("null_threshold", 0.5))}

    @classmethod
    def from_pretrained(cls, name_or_path: str, device: str = "auto", revision: str | None = None,
                        token: str | None = None) -> Kodiak:
        from safetensors.torch import load_file

        folder = _resolve(name_or_path, revision, token)
        if (folder / "ensemble.json").exists():  # accuracy mode: several models, answers averaged
            return KodiakEnsemble.from_folder(folder, device)
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
        # Inference Endpoints support: a custom handler plus its install requirements.
        release = Path(__file__).resolve().parents[2] / "release"
        for name in ("handler.py", "requirements.txt"):
            if (release / name).exists():
                shutil.copy(release / name, out / name)
        return out


class KodiakEnsemble(Kodiak):
    """'Accuracy mode' (D34): several independently trained models; their calibrated answers are averaged, which cancels much of each
    model's overconfidence. A folder holds ensemble.json ({"members": [...subfolders], "null_threshold": ...}) and one model folder per
    member. Same API as Kodiak; about len(members) times the compute."""

    def __init__(self, members: list[Kodiak], null_threshold: float = 0.5, name: str = "kodiak-ensemble"):
        self.members = members
        self.model = members[0].model
        self.calibration = {"null_threshold": null_threshold, "members": len(members)}
        self.name = name
        self.default_options = {"null_threshold": float(null_threshold)}

    @classmethod
    def from_folder(cls, folder: Path, device: str = "auto") -> KodiakEnsemble:
        spec = json.loads((folder / "ensemble.json").read_text())
        members = [Kodiak.from_pretrained(str(folder / m), device=device) for m in spec["members"]]
        return cls(members, spec.get("null_threshold", 0.5), name=folder.name)

    def answer(self, requests: list[dict]) -> list[dict]:
        import time as _time

        from kodiak_s1.infer import combine_raw, decide, raw_outputs
        from kodiak_s1.schema import Options, Request

        reqs = [Request.model_validate({**r, "options": {**self.default_options, **(r.get("options") or {})}}).model_dump()
                for r in requests]
        t0 = _time.perf_counter()
        raws = combine_raw([raw_outputs(m.model, reqs) for m in self.members])
        ms = (_time.perf_counter() - t0) * 1000 / max(1, len(reqs))
        out = []
        for req, raw in zip(reqs, raws):
            opts = Options(**req.get("options", {}))
            qs = {q["id"]: q for q in req["questions"]}
            out.append({"model": self.name, "latency_ms": round(ms, 2),
                        "answers": {r["qid"]: decide(r, qs[r["qid"]], opts) for r in raw}})
        return out

    def save_pretrained(self, out: str | Path, tokenizer_json: str | Path | None = None) -> Path:
        out = Path(out)
        names = []
        for i, m in enumerate(self.members):
            m.save_pretrained(out / f"m{i}", tokenizer_json)
            names.append(f"m{i}")
        (out / "ensemble.json").write_text(json.dumps({"members": names, "null_threshold": self.default_options["null_threshold"]},
                                                      indent=2) + "\n")
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

        from huggingface_hub import CommitOperationAdd

        api = HfApi()
        api.create_repo(a.repo, private=a.private, exist_ok=True)
        folder = Path(a.folder)
        # Small files (model card, config, calibration, handler) first, in their own commit, so a public repo never sits
        # empty while a large weights file uploads (upload_folder commits everything at the very end).
        small = [f for f in sorted(folder.iterdir()) if f.is_file() and f.suffix != ".safetensors"]
        api.create_commit(a.repo, operations=[CommitOperationAdd(path_in_repo=f.name, path_or_fileobj=str(f)) for f in small],
                          commit_message=f"{a.message}: model card and config")
        for f in sorted(folder.glob("*.safetensors")):
            api.upload_file(path_or_fileobj=str(f), path_in_repo=f.name, repo_id=a.repo, commit_message=f"{a.message}: weights")
        print(f"pushed {a.folder} -> https://huggingface.co/{a.repo}")


if __name__ == "__main__":
    main()
