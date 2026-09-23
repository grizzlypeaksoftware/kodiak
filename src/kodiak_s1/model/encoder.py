"""ModernBERT-compatible bidirectional encoder with Kodiak's structured attention (docs/ARCHITECTURE.md §4, §7).

Same layer layout and parameter names as Hugging Face's ModernBertModel, so ModernBERT weights load
directly (see load_modernbert). What differs is attention: instead of "every token sees every token",
the mask comes from token roles, and position ids come from the packer.

Two attention paths produce the same result:
  "flex"  PyTorch FlexAttention with a block-sparse mask: fast, used for training.
  "sdpa"  standard scaled-dot-product attention with a dense boolean mask: used for ONNX export and tests.
"""

from __future__ import annotations

import math

import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.checkpoint import checkpoint

from kodiak_s1.model.config import EncoderConfig
from kodiak_s1.packing import LABEL, PAD, QUESTION, STATE

try:
    from torch.nn.attention.flex_attention import create_block_mask, flex_attention

    _flex_compiled = torch.compile(flex_attention, dynamic=False)
except ImportError:  # pragma: no cover
    flex_attention = None


# ---------------------------------------------------------------------------
# The attention rule (§4), written once and used by both paths
# ---------------------------------------------------------------------------


def allowed(doc_q, doc_k, role_q, role_k, qi_q, qi_k, li_q, li_k, question_sees_labels: bool = True):
    """May token q attend to token k? Works elementwise on tensors (dense) or scalars-as-tensors (flex)."""
    same_doc = doc_q == doc_k
    k_state = role_k == STATE  # everyone reads the state; state rows read nothing else (see below)
    k_question = (role_k == QUESTION) & ((role_q == QUESTION) | (role_q == LABEL)) & (qi_q == qi_k)
    q_to_labels = (role_q == QUESTION) & question_sees_labels
    k_label = (role_k == LABEL) & (qi_q == qi_k) & (q_to_labels | ((role_q == LABEL) & (li_q == li_k)))
    k_pad = (role_k == PAD) & (role_q == PAD)  # padding only sees padding (no empty rows, no leaks)
    return same_doc & (k_state | k_question | k_label | k_pad)


def dense_masks(meta: dict, window: int, question_sees_labels: bool = True) -> tuple[torch.Tensor, torch.Tensor]:
    """[B, 1, N, N] boolean masks for global and local layers."""
    def pair(x):
        return x[:, :, None], x[:, None, :]

    m = allowed(*pair(meta["doc"]), *pair(meta["role"]), *pair(meta["qi"]), *pair(meta["li"]), question_sees_labels)
    pq, pk = pair(meta["pos"])
    local = m & ((pq - pk).abs() <= window)
    return m[:, None], local[:, None]


def block_masks(meta: dict, window: int, question_sees_labels: bool = True):
    doc, role, qi, li, pos = meta["doc"], meta["role"], meta["qi"], meta["li"], meta["pos"]
    B, N = doc.shape

    def global_mod(b, h, q, k):
        return allowed(doc[b, q], doc[b, k], role[b, q], role[b, k], qi[b, q], qi[b, k], li[b, q], li[b, k],
                       question_sees_labels)

    def local_mod(b, h, q, k):
        return global_mod(b, h, q, k) & ((pos[b, q] - pos[b, k]).abs() <= window)

    g = create_block_mask(global_mod, B, None, N, N, device=doc.device)
    loc = create_block_mask(local_mod, B, None, N, N, device=doc.device)
    return g, loc


# ---------------------------------------------------------------------------
# Rotary position embeddings
# ---------------------------------------------------------------------------


def rope_cos_sin(pos: torch.Tensor, head_dim: int, theta: float) -> tuple[torch.Tensor, torch.Tensor]:
    inv_freq = 1.0 / (theta ** (torch.arange(0, head_dim, 2, device=pos.device, dtype=torch.float32) / head_dim))
    freqs = pos.to(torch.float32)[..., None] * inv_freq  # [B, N, D/2]
    emb = torch.cat([freqs, freqs], dim=-1)
    return emb.cos()[:, None], emb.sin()[:, None]  # [B, 1, N, D]


def _rotate_half(x: torch.Tensor) -> torch.Tensor:
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat([-x2, x1], dim=-1)


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    xf = x.float()  # rotary math in fp32, as in ModernBERT
    return (xf * cos + _rotate_half(xf) * sin).to(x.dtype)


# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------


class Attention(nn.Module):
    def __init__(self, cfg: EncoderConfig):
        super().__init__()
        self.h = cfg.num_heads
        self.d = cfg.hidden_size // cfg.num_heads
        self.Wqkv = nn.Linear(cfg.hidden_size, 3 * cfg.hidden_size, bias=False)
        self.Wo = nn.Linear(cfg.hidden_size, cfg.hidden_size, bias=False)

    def forward(self, x, cos, sin, mask, impl: str):
        B, N, _ = x.shape
        q, k, v = self.Wqkv(x).view(B, N, 3, self.h, self.d).permute(2, 0, 3, 1, 4)  # each [B, H, N, D]
        q, k = apply_rope(q, cos, sin), apply_rope(k, cos, sin)
        if impl == "flex":
            out = _flex_compiled(q, k, v, block_mask=mask)
        else:
            out = F.scaled_dot_product_attention(q, k, v, attn_mask=mask)
        return self.Wo(out.transpose(1, 2).reshape(B, N, -1))


class MLP(nn.Module):
    def __init__(self, cfg: EncoderConfig):
        super().__init__()
        self.Wi = nn.Linear(cfg.hidden_size, 2 * cfg.intermediate_size, bias=False)
        self.Wo = nn.Linear(cfg.intermediate_size, cfg.hidden_size, bias=False)

    def forward(self, x):
        inp, gate = self.Wi(x).chunk(2, dim=-1)
        return self.Wo(F.gelu(inp) * gate)  # GeGLU


class Layer(nn.Module):
    def __init__(self, cfg: EncoderConfig, idx: int):
        super().__init__()
        self.is_global = idx % cfg.global_every == 0
        # Layer 0 reads the already-normalized embeddings, so it has no attention norm (as in ModernBERT).
        self.attn_norm = nn.Identity() if idx == 0 else nn.LayerNorm(cfg.hidden_size, eps=cfg.norm_eps, bias=False)
        self.attn = Attention(cfg)
        self.mlp_norm = nn.LayerNorm(cfg.hidden_size, eps=cfg.norm_eps, bias=False)
        self.mlp = MLP(cfg)

    def forward(self, x, rope_g, rope_l, mask_g, mask_l, impl):
        cos, sin = rope_g if self.is_global else rope_l
        x = x + self.attn(self.attn_norm(x), cos, sin, mask_g if self.is_global else mask_l, impl)
        return x + self.mlp(self.mlp_norm(x))


class Embeddings(nn.Module):
    def __init__(self, cfg: EncoderConfig):
        super().__init__()
        self.tok_embeddings = nn.Embedding(cfg.vocab_size, cfg.hidden_size)
        self.norm = nn.LayerNorm(cfg.hidden_size, eps=cfg.norm_eps, bias=False)

    def forward(self, ids):
        return self.norm(self.tok_embeddings(ids))


class Encoder(nn.Module):
    def __init__(self, cfg: EncoderConfig, question_sees_labels: bool = True):
        super().__init__()
        self.cfg = cfg
        self.question_sees_labels = question_sees_labels
        self.embeddings = Embeddings(cfg)
        self.layers = nn.ModuleList([Layer(cfg, i) for i in range(cfg.num_layers)])
        self.final_norm = nn.LayerNorm(cfg.hidden_size, eps=cfg.norm_eps, bias=False)
        self.gradient_checkpointing = False
        self.reset_parameters()

    @torch.no_grad()
    def reset_parameters(self, std: float = 0.02) -> None:
        """Random init for training from scratch (Track A): truncated normal, output projections scaled
        down by sqrt(2 * layers) so the residual stream doesn't grow with depth."""
        out_std = std / math.sqrt(2 * self.cfg.num_layers)
        for name, p in self.named_parameters():
            if p.dim() == 1:
                nn.init.ones_(p)
            else:
                s = out_std if name.endswith("Wo.weight") else std
                nn.init.trunc_normal_(p, std=s, a=-2 * s, b=2 * s)

    def forward(self, input_ids: torch.Tensor, meta: dict, impl: str = "flex") -> torch.Tensor:
        cfg = self.cfg
        hd = cfg.hidden_size // cfg.num_heads
        rope_g = rope_cos_sin(meta["pos"], hd, cfg.global_rope_theta)
        rope_l = rope_cos_sin(meta["pos"], hd, cfg.local_rope_theta)
        if impl == "flex":
            mask_g, mask_l = block_masks(meta, cfg.local_window, self.question_sees_labels)
        else:
            mask_g, mask_l = dense_masks(meta, cfg.local_window, self.question_sees_labels)
        x = self.embeddings(input_ids)
        for layer in self.layers:
            if self.gradient_checkpointing and self.training:
                x = checkpoint(layer, x, rope_g, rope_l, mask_g, mask_l, impl, use_reentrant=False)
            else:
                x = layer(x, rope_g, rope_l, mask_g, mask_l, impl)
        return self.final_norm(x)


def load_modernbert(encoder: Encoder, repo: str = "answerdotai/ModernBERT-base") -> list[str]:
    """Load Hugging Face ModernBERT weights (Track B). Returns the checkpoint keys we didn't use (the MLM head)."""
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file

    sd = load_file(hf_hub_download(repo, "model.safetensors"))
    encoder.load_state_dict({k.removeprefix("model."): v for k, v in sd.items() if k.startswith("model.")}, strict=True)
    return [k for k in sd if not k.startswith("model.")]
