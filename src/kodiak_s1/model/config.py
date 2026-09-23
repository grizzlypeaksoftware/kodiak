"""Model configuration and size presets (docs/ARCHITECTURE.md §7.4)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class EncoderConfig:
    """ModernBERT-compatible encoder shape. Defaults are ModernBERT-base."""

    vocab_size: int = 50368
    hidden_size: int = 768
    num_layers: int = 22
    num_heads: int = 12
    intermediate_size: int = 1152  # GeGLU: Wi projects to 2x this
    global_every: int = 3  # layer i is global if i % global_every == 0, else local
    local_window: int = 64  # local layers attend to |pos_q - pos_k| <= local_window
    global_rope_theta: float = 160_000.0
    local_rope_theta: float = 10_000.0
    norm_eps: float = 1e-5
    pad_token_id: int = 50283
    cls_token_id: int = 50281
    sep_token_id: int = 50282


@dataclass
class HeadConfig:
    hidden: int = 0  # 0 -> same as encoder hidden size
    kappa_eps: float = 1e-3  # Beta concentration floor
    question_sees_labels: bool = True  # ablation flag (§4)


@dataclass
class ModelConfig:
    encoder: EncoderConfig = field(default_factory=EncoderConfig)
    heads: HeadConfig = field(default_factory=HeadConfig)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2) + "\n")

    @classmethod
    def load(cls, path: str | Path) -> ModelConfig:
        d = json.loads(Path(path).read_text())
        return cls(EncoderConfig(**d["encoder"]), HeadConfig(**d["heads"]))


PRESETS: dict[str, EncoderConfig] = {
    # Phase 3 plumbing test only. Most parameters are the (shared-vocab) embedding table.
    "tiny": EncoderConfig(hidden_size=256, num_layers=4, num_heads=4, intermediate_size=384),
    # Track A first model (~50M).
    "mini": EncoderConfig(hidden_size=512, num_layers=12, num_heads=8, intermediate_size=768),
    # ModernBERT-base shape: Track B b-small, and Track A a-small (from scratch).
    "small": EncoderConfig(),
    # ModernBERT-large shape.
    "base": EncoderConfig(hidden_size=1024, num_layers=28, num_heads=16, intermediate_size=2624),
}
