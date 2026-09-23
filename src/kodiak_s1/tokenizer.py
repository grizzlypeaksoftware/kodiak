"""The shared Kodiak tokenizer: ModernBERT's, with [unused*] slots reserved as marker tokens.

Both tracks use it (docs/ARCHITECTURE.md §7.3).
"""

from __future__ import annotations

from functools import lru_cache

TOKENIZER_REPO = "answerdotai/ModernBERT-base"

# Marker tokens (docs/ARCHITECTURE.md §3.1), mapped onto unused vocabulary slots.
MARKERS = {"[CHOICE]": "[unused0]", "[SCORE]": "[unused1]", "[LABEL]": "[unused2]"}


@lru_cache(maxsize=1)
def get_tokenizer():
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer

    return Tokenizer.from_file(hf_hub_download(TOKENIZER_REPO, "tokenizer.json"))


def count_tokens(text: str) -> int:
    """Token count without special tokens."""
    return len(get_tokenizer().encode(text, add_special_tokens=False).ids)


def question_text(q: dict) -> str:
    """The text of a question block after its type marker (docs/ARCHITECTURE.md §3.1)."""
    if q["type"] == "score" and (q.get("min_label") or q.get("max_label")):
        return f'{q["text"]} (min: {q.get("min_label") or "lowest"}; max: {q.get("max_label") or "highest"})'
    return q["text"]


def packed_lengths(state_text: str, questions: list[dict]) -> tuple[int, int]:
    """(state tokens incl. [CLS], total packed tokens) for one request."""
    state = 1 + count_tokens(state_text)
    total = state
    for q in questions:
        total += 1 + count_tokens(question_text(q))
        for lab in q.get("labels", []):
            total += 1 + count_tokens(lab["text"])
    return state, total
