"""Pack requests/examples into token sequences (docs/ARCHITECTURE.md §3-§4).

One example becomes:

    [CLS] state [SEP] | [CHOICE] q1 | [LABEL] l1.1 | [LABEL] l1.2 | [SCORE] q2 | ...

with per-token metadata that the attention mask is built from:
  role   STATE / QUESTION / LABEL (PAD for padding)
  qi     question index within the example (-1 for state)
  li     label index within its question (-1 otherwise)
  pos    position id: every question block starts right after the state, and every
         label of question i starts right after question i, so order doesn't matter.

Several examples are packed into one row; `doc` tells them apart so they never see each other.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch

from kodiak_s1.schema import render_state
from kodiak_s1.tokenizer import MARKERS, get_tokenizer, question_text

PAD, STATE, QUESTION, LABEL = 0, 1, 2, 3
CHOICE, SCORE = 0, 1


@dataclass
class Limits:
    max_state: int = 2048  # incl. [CLS] and [SEP]
    max_question: int = 128  # incl. marker
    max_label: int = 32  # incl. marker


@dataclass
class Packed:
    """One example, tokenized. Offsets are relative to the example's first token."""

    ids: list[int]
    pos: list[int]
    role: list[int]
    qi: list[int]
    li: list[int]
    q_off: list[int]  # marker offset per question
    q_type: list[int]
    q_allow_null: list[bool]
    l_off: list[int]  # marker offset per label
    l_q: list[int]  # owning question index per label
    # Targets (None when packing a request for inference).
    q_null: list[int] | None = None  # 1 null, 0 answerable
    q_score: list[float] | None = None  # unit-interval target (squeezed), nan if not a score answer
    l_gold: list[bool] | None = None
    truncated: bool = False
    qids: list[str] = field(default_factory=list)
    label_ids: list[list[str]] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.ids)


_ids_cache: dict[str, int] = {}


def _special(tok_str: str) -> int:
    if tok_str not in _ids_cache:
        _ids_cache[tok_str] = get_tokenizer().token_to_id(tok_str)
    return _ids_cache[tok_str]


def _encode(text: str) -> list[int]:
    return get_tokenizer().encode(text, add_special_tokens=False).ids


def squeeze_unit(u: float, n: int = 100) -> float:
    """Move targets off exactly 0/1, where the Beta log-density is infinite (Smithson & Verkuilen, 2006)."""
    u = min(max(u, 0.0), 1.0)
    return (u * (n - 1) + 0.5) / n


def pack_example(ex: dict, limits: Limits = Limits(), with_targets: bool = True) -> Packed:
    """Tokenize one Example (or Request, with_targets=False) dict."""
    truncated = False
    state = _encode(render_state(ex["state"]))
    if len(state) > limits.max_state - 2:
        state, truncated = state[: limits.max_state - 2], True
    ids = [_special("[CLS]")] + state + [_special("[SEP]")]
    S = len(ids)
    pos, role, qi, li = list(range(S)), [STATE] * S, [-1] * S, [-1] * S
    p = Packed(ids, pos, role, qi, li, [], [], [], [], [], truncated=truncated)
    if with_targets:
        p.q_null, p.q_score, p.l_gold = [], [], []

    for i, q in enumerate(ex["questions"]):
        marker = _special(MARKERS["[CHOICE]" if q["type"] == "choice" else "[SCORE]"])
        qtoks = [marker] + _encode(question_text(q))
        if len(qtoks) > limits.max_question:
            qtoks, p.truncated = qtoks[: limits.max_question], True
        p.q_off.append(len(p.ids))
        p.q_type.append(CHOICE if q["type"] == "choice" else SCORE)
        p.q_allow_null.append(q.get("allow_null", True))
        p.qids.append(q["id"])
        p.ids += qtoks
        p.pos += list(range(S, S + len(qtoks)))
        p.role += [QUESTION] * len(qtoks)
        p.qi += [i] * len(qtoks)
        p.li += [-1] * len(qtoks)
        label_start = S + len(qtoks)

        target = ex["answers"][q["id"]] if with_targets else None
        labels = q.get("labels", []) if q["type"] == "choice" else []
        p.label_ids.append([lab["id"] for lab in labels])
        for j, lab in enumerate(labels):
            ltoks = [_special(MARKERS["[LABEL]"])] + _encode(lab["text"])
            if len(ltoks) > limits.max_label:
                ltoks, p.truncated = ltoks[: limits.max_label], True
            p.l_off.append(len(p.ids))
            p.l_q.append(i)
            p.ids += ltoks
            p.pos += list(range(label_start, label_start + len(ltoks)))
            p.role += [LABEL] * len(ltoks)
            p.qi += [i] * len(ltoks)
            p.li += [j] * len(ltoks)
            if with_targets:
                p.l_gold.append(target.get("label") == lab["id"])

        if with_targets:
            is_null = bool(target.get("null"))
            p.q_null.append(int(is_null))
            if q["type"] == "score" and not is_null:
                u = (target["value"] - q.get("min", 0.0)) / (q.get("max", 1.0) - q.get("min", 0.0))
                p.q_score.append(squeeze_unit(u))
            else:
                p.q_score.append(math.nan)
    return p


@dataclass
class Batch:
    """Rows of packed examples plus flat question/label tables for the heads and loss."""

    input_ids: torch.Tensor  # [B, N]
    pos: torch.Tensor  # [B, N]
    doc: torch.Tensor  # [B, N] example id within row (-1 = padding)
    role: torch.Tensor  # [B, N]
    qi: torch.Tensor  # [B, N]
    li: torch.Tensor  # [B, N]
    q_row: torch.Tensor  # [Q]
    q_col: torch.Tensor  # [Q]
    q_type: torch.Tensor  # [Q]
    q_allow_null: torch.Tensor  # [Q] bool
    l_row: torch.Tensor  # [L]
    l_col: torch.Tensor  # [L]
    l_q: torch.Tensor  # [L] index into the Q table
    q_null: torch.Tensor | None = None  # [Q]
    q_score: torch.Tensor | None = None  # [Q]
    l_gold: torch.Tensor | None = None  # [L] bool
    q_example: list[int] = field(default_factory=list)  # which input example each question came from
    n_tokens: int = 0

    def to(self, device) -> Batch:
        for k, v in self.__dict__.items():
            if isinstance(v, torch.Tensor):
                setattr(self, k, v.to(device, non_blocking=True))
        return self


def collate(packed: list[Packed], max_len: int, pad_to: int | None = None) -> Batch:
    """Greedy sequential packing into rows of at most max_len tokens (each example must fit in one row)."""
    rows: list[list[int]] = [[]]
    used = [0]
    for k, p in enumerate(packed):
        if len(p) > max_len:
            raise ValueError(f"example {k} has {len(p)} tokens > row length {max_len}")
        if used[-1] + len(p) > max_len:
            rows.append([])
            used.append(0)
        rows[-1].append(k)
        used[-1] += len(p)
    N = pad_to or max(used)
    B = len(rows)
    t = {name: torch.full((B, N), fill, dtype=torch.long)
         for name, fill in [("input_ids", _special("[PAD]")), ("pos", 0), ("doc", -1), ("role", PAD), ("qi", -1), ("li", -1)]}
    q_rows, q_cols, q_type, q_null_ok, l_rows, l_cols, l_q = [], [], [], [], [], [], []
    q_null, q_score, l_gold, q_example = [], [], [], []
    has_targets = packed[0].q_null is not None
    for r, members in enumerate(rows):
        off = 0
        for d, k in enumerate(members):
            p = packed[k]
            n = len(p)
            sl = slice(off, off + n)
            t["input_ids"][r, sl] = torch.tensor(p.ids)
            t["pos"][r, sl] = torch.tensor(p.pos)
            t["doc"][r, sl] = d
            t["role"][r, sl] = torch.tensor(p.role)
            t["qi"][r, sl] = torch.tensor(p.qi)
            t["li"][r, sl] = torch.tensor(p.li)
            q_base = len(q_rows)
            for i, o in enumerate(p.q_off):
                q_rows.append(r)
                q_cols.append(off + o)
                q_type.append(p.q_type[i])
                q_null_ok.append(p.q_allow_null[i])
                q_example.append(k)
            for j, o in enumerate(p.l_off):
                l_rows.append(r)
                l_cols.append(off + o)
                l_q.append(q_base + p.l_q[j])
            if has_targets:
                q_null += p.q_null
                q_score += p.q_score
                l_gold += p.l_gold
            off += n
    # Padding tokens get their own position ids so they never fall inside a real token's local window.
    pad = t["doc"] < 0
    t["pos"][pad] = 10**6
    b = Batch(**t, q_row=torch.tensor(q_rows), q_col=torch.tensor(q_cols), q_type=torch.tensor(q_type),
              q_allow_null=torch.tensor(q_null_ok, dtype=torch.bool), l_row=torch.tensor(l_rows, dtype=torch.long),
              l_col=torch.tensor(l_cols, dtype=torch.long), l_q=torch.tensor(l_q, dtype=torch.long),
              q_example=q_example, n_tokens=int(sum(used)))
    if has_targets:
        b.q_null = torch.tensor(q_null, dtype=torch.float)
        b.q_score = torch.tensor(q_score, dtype=torch.float)
        b.l_gold = torch.tensor(l_gold, dtype=torch.bool)
    return b
