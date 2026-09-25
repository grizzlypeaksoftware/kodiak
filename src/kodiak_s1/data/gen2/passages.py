"""Real-text grounding: deterministic passage windows from the FineWeb-Edu sample already on disk (ODC-By).

Why: in v1 the teacher wrote every state, so Kodiak only ever read "LLM-written" text. Real passages break that
monoculture. The writer only writes questions about the passage; it never edits it.

A passage is a run of whole paragraphs (100-450 words) from one document, chosen by (seed, job id), with cheap filters
against boilerplate (menus, link lists, tables of numbers). Release policy (GENERATOR_V2.md §7): the published dataset
ships a rebuild script and the FineWeb ids, not the excerpts.
"""

from __future__ import annotations

import glob
import re
import threading
from functools import lru_cache

from kodiak_s1.data.sources import rng_for

FINEWEB_GLOB = "data/pretrain/fineweb-edu/sample/10BT/*.parquet"
WORD_RANGE = {"easy": (100, 220), "medium": (150, 320), "hard": (250, 450)}

_local = threading.local()


@lru_cache(maxsize=1)
def _files() -> tuple[str, ...]:
    return tuple(sorted(glob.glob(FINEWEB_GLOB)))


def _parquet(path: str):
    import pyarrow.parquet as pq

    cache = getattr(_local, "files", None)
    if cache is None:
        cache = _local.files = {}
    if path not in cache:
        cache[path] = pq.ParquetFile(path)
    return cache[path]


def paragraphs(text: str) -> list[str]:
    return [re.sub(r"[ \t]+", " ", p).strip() for p in re.split(r"\n+", text) if p.strip()]


def clean_enough(paras: list[str]) -> bool:
    """Reject windows that look like navigation, link lists, tables or code rather than prose."""
    text = " ".join(paras)
    words = text.split()
    if not words:
        return False
    letters = sum(c.isalpha() for c in text) / max(1, len(text))
    short_lines = sum(len(p.split()) < 4 for p in paras) / len(paras)
    return (letters > 0.72 and short_lines < 0.4 and text.count("http") < 2 and "|" not in text
            and sum(len(p.split()) for p in paras) / len(paras) >= 12)


def window(text: str, rng, lo: int, hi: int) -> str | None:
    """A run of whole paragraphs with lo..hi words, starting at a random paragraph."""
    paras = paragraphs(text)
    if not paras:
        return None
    target = rng.randint(lo, hi)
    starts = list(range(len(paras)))
    rng.shuffle(starts)
    for s in starts[:6]:
        chosen, n = [], 0
        for p in paras[s:]:
            w = len(p.split())
            if n + w > hi:
                break
            chosen.append(p)
            n += w
            if n >= target:
                break
        if n >= lo and clean_enough(chosen):
            return "\n\n".join(chosen)
    return None


def passage(seed: int, job: int, difficulty: str = "medium", attempts: int = 25) -> dict | None:
    """Deterministic passage for (seed, job): {"text", "id", "url", "words"} or None if nothing usable was found."""
    files = _files()
    if not files:
        raise FileNotFoundError(f"no FineWeb-Edu parquet files match {FINEWEB_GLOB}")
    rng = rng_for("gen2-passage", seed, job)
    lo, hi = WORD_RANGE[difficulty]
    for _ in range(attempts):
        pf = _parquet(rng.choice(files))
        rg = rng.randrange(pf.metadata.num_row_groups)
        table = pf.read_row_group(rg, columns=["text", "id", "url", "language_score"])
        row = rng.randrange(table.num_rows)
        if table.column("language_score")[row].as_py() < 0.9:
            continue
        w = window(table.column("text")[row].as_py(), rng, lo, hi)
        if w:
            return {"text": w, "id": table.column("id")[row].as_py(), "url": table.column("url")[row].as_py(),
                    "words": len(w.split())}
    return None
