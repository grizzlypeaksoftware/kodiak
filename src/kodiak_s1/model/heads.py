"""Decision heads, the Kodiak model, and the training objective (docs/ARCHITECTURE.md §5-§6)."""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

from kodiak_s1.model.config import ModelConfig
from kodiak_s1.model.encoder import Encoder
from kodiak_s1.packing import CHOICE, SCORE, Batch


def _mlp(d_in: int, d_hidden: int, d_out: int) -> nn.Sequential:
    return nn.Sequential(nn.Linear(d_in, d_hidden), nn.GELU(), nn.Linear(d_hidden, d_out))


class DecisionHeads(nn.Module):
    def __init__(self, d: int, hidden: int = 0, kappa_eps: float = 1e-3):
        super().__init__()
        h = hidden or d
        self.choice = _mlp(3 * d, h, 1)  # [h_l ; h_q ; h_l * h_q] -> logit
        self.null = _mlp(d, h, 1)
        self.score = _mlp(d, h, 2)  # -> (mean logit, concentration pre-activation)
        self.kappa_eps = kappa_eps
        # Post-hoc calibration (stage S3). Identity until fitted.
        self.register_buffer("t_choice", torch.tensor(1.0))
        self.register_buffer("t_null", torch.tensor(1.0))
        self.register_buffer("kappa_scale", torch.tensor(1.0))

    def forward(self, h_q: torch.Tensor, h_l: torch.Tensor, l_q: torch.Tensor) -> dict[str, torch.Tensor]:
        hq_for_l = h_q[l_q]
        z_choice = self.choice(torch.cat([h_l, hq_for_l, h_l * hq_for_l], dim=-1)).squeeze(-1)
        z_null = self.null(h_q).squeeze(-1)
        s = self.score(h_q)
        mu = torch.sigmoid(s[:, 0])
        kappa = F.softplus(s[:, 1]) + self.kappa_eps
        return {"z_choice": z_choice / self.t_choice, "z_null": z_null / self.t_null,
                "mu": mu, "kappa": kappa * self.kappa_scale}


class KodiakModel(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.cfg = cfg
        self.encoder = Encoder(cfg.encoder, cfg.heads.question_sees_labels)
        self.heads = DecisionHeads(cfg.encoder.hidden_size, cfg.heads.hidden, cfg.heads.kappa_eps)

    def forward(self, b: Batch, impl: str = "flex") -> dict[str, torch.Tensor]:
        meta = {"doc": b.doc, "role": b.role, "qi": b.qi, "li": b.li, "pos": b.pos}
        h = self.encoder(b.input_ids, meta, impl)
        # Heads run in fp32: they are tiny, and the logits feed probabilities we want calibrated.
        h_q = h[b.q_row, b.q_col].float()
        h_l = h[b.l_row, b.l_col].float()
        with torch.autocast(device_type=h.device.type, enabled=False):
            return self.heads(h_q, h_l, b.l_q)


# ---------------------------------------------------------------------------
# Probabilities and loss
# ---------------------------------------------------------------------------


def group_log_softmax(z: torch.Tensor, group: torch.Tensor, n_groups: int) -> torch.Tensor:
    """log_softmax of z within each group (labels grouped by their question)."""
    zmax = torch.full((n_groups,), float("-inf"), device=z.device, dtype=z.dtype)
    zmax = zmax.scatter_reduce(0, group, z, reduce="amax", include_self=True)
    ex = torch.exp(z - zmax[group])
    denom = torch.zeros(n_groups, device=z.device, dtype=z.dtype).index_add(0, group, ex)
    return z - (zmax[group] + torch.log(denom[group]))


def beta_log_prob(y: torch.Tensor, mu: torch.Tensor, kappa: torch.Tensor) -> torch.Tensor:
    a, b = mu * kappa, (1 - mu) * kappa
    return ((a - 1) * torch.log(y) + (b - 1) * torch.log1p(-y)
            - (torch.lgamma(a) + torch.lgamma(b) - torch.lgamma(a + b)))


def decision_loss(out: dict[str, torch.Tensor], b: Batch) -> tuple[torch.Tensor, dict[str, float]]:
    """Negative log-likelihood of the correct outcome under the model's full answer distribution (§6).

    = BCE on the null head (when null is allowed) + CE over labels / Beta NLL (when answerable).
    """
    Q = b.q_type.shape[0]
    is_null = b.q_null
    allow = b.q_allow_null.float()
    logp_null = F.logsigmoid(out["z_null"])
    logp_ans = F.logsigmoid(-out["z_null"])
    null_term = -allow * (is_null * logp_null + (1 - is_null) * logp_ans)

    logq = group_log_softmax(out["z_choice"], b.l_q, Q)
    gold_logq = torch.zeros(Q, device=logq.device).index_add(0, b.l_q, torch.where(b.l_gold, logq, 0.0))
    choice_mask = (b.q_type == CHOICE) & (is_null == 0)
    score_mask = (b.q_type == SCORE) & (is_null == 0)
    y = torch.nan_to_num(b.q_score, nan=0.5)
    score_nll = -beta_log_prob(y, out["mu"], out["kappa"])
    ans_term = torch.where(choice_mask, -gold_logq, 0.0) + torch.where(score_mask, score_nll, 0.0)
    per_q = null_term + ans_term
    loss = per_q.mean()

    with torch.no_grad():
        # Choice accuracy on answerable questions: is the gold label the argmax within its group?
        zmax = torch.full((Q,), float("-inf"), device=logq.device).scatter_reduce(
            0, b.l_q, out["z_choice"].float(), reduce="amax", include_self=True)
        gold_z = torch.full((Q,), float("-inf"), device=logq.device).scatter_reduce(
            0, b.l_q, torch.where(b.l_gold, out["z_choice"].float(), float("-inf")), reduce="amax", include_self=True)
        pred_null = out["z_null"] > 0
        stats = {
            "loss": loss.item(),
            "null_bce": (null_term.sum() / allow.sum().clamp(min=1)).item(),
            "choice_ce": (torch.where(choice_mask, -gold_logq, 0.0).sum() / choice_mask.sum().clamp(min=1)).item(),
            "score_nll": (torch.where(score_mask, score_nll, 0.0).sum() / score_mask.sum().clamp(min=1)).item(),
            "choice_acc": ((gold_z >= zmax) & choice_mask).sum().item() / max(1, choice_mask.sum().item()),
            "null_acc": ((pred_null == (is_null > 0)) & (allow > 0)).sum().item() / max(1, allow.sum().item()),
            "score_mae": (torch.where(score_mask, (out["mu"] - y).abs(), 0.0).sum() / score_mask.sum().clamp(min=1)).item(),
            "n_q": Q,
        }
    return loss, stats


def distill_loss(out: dict[str, torch.Tensor], teachers: list[dict[str, torch.Tensor]], b: Batch
                 ) -> tuple[torch.Tensor, dict[str, float]]:
    """Cross-entropy against the *averaged* distribution of calibrated teacher models (knowledge distillation, D34).

    Null: soft BCE toward the teachers' mean p(null). Choice: soft CE toward the teachers' mean label distribution (on every choice
    question, including the "dark knowledge" of how plausible each wrong option is). Score: mean Beta NLL of each teacher's mean, so the
    student's concentration reflects how much the teachers disagree. Teachers are expected to carry their calibration temperatures.
    """
    Q = b.q_type.shape[0]
    allow = b.q_allow_null.float()
    p_null_t = torch.stack([torch.sigmoid(t["z_null"].float()) for t in teachers]).mean(0)
    null_soft = -allow * (p_null_t * F.logsigmoid(out["z_null"]) + (1 - p_null_t) * F.logsigmoid(-out["z_null"]))
    q_t = torch.stack([group_log_softmax(t["z_choice"].float(), b.l_q, Q).exp() for t in teachers]).mean(0)
    logq = group_log_softmax(out["z_choice"], b.l_q, Q)
    choice_soft = -torch.zeros(Q, device=logq.device).index_add(0, b.l_q, q_t * logq)
    score_mask = b.q_type == SCORE
    score_soft = torch.stack([-beta_log_prob(t["mu"].float().clamp(0.005, 0.995), out["mu"], out["kappa"]) for t in teachers]).mean(0)
    per_q = null_soft + torch.where(b.q_type == CHOICE, choice_soft, 0.0) + torch.where(score_mask, score_soft, 0.0)
    loss = per_q.mean()
    return loss, {"distill": loss.item()}
