"""Near-duplicate filter: MinHash over word 5-shingles, with LSH banding for fast candidate lookup.

Why: at scale a generator repeats itself ("100k jobs are mostly 10k"). Exact-hash dedupe misses a state that differs by
a name or a number. MinHash estimates the Jaccard similarity of two texts' shingle sets; anything above 0.8 against the
v1 files or earlier gen2 output is dropped. This makes repetition measurable instead of invisible.

64 hash functions in 16 bands of 4 rows: two texts with Jaccard 0.8 share at least one band with probability
1 - (1 - 0.8^4)^16 ≈ 0.9999, and a pair at 0.3 only ≈ 0.12 (and is then rejected by the full signature check).
"""

from __future__ import annotations

import hashlib
import re

import numpy as np

NUM_PERM, BANDS = 64, 16
ROWS = NUM_PERM // BANDS
_SEEDS = np.random.default_rng(20260925).integers(1, 2**63, size=NUM_PERM, dtype=np.uint64)
_MUL1, _MUL2 = np.uint64(0xBF58476D1CE4E5B9), np.uint64(0x94D049BB133111EB)


def shingles(text: str, k: int = 5) -> set[str]:
    words = re.findall(r"\w+", text.casefold())
    if len(words) < k:
        return {" ".join(words)}
    return {" ".join(words[i:i + k]) for i in range(len(words) - k + 1)}


def signature(text: str) -> np.ndarray:
    """64 MinHash values: for each seed, the minimum of a mixed 64-bit hash over all shingles (splitmix64-style)."""
    h = np.fromiter((int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "little")
                     for s in shingles(text)), dtype=np.uint64)
    with np.errstate(over="ignore"):
        x = h[None, :] ^ _SEEDS[:, None]
        x = (x ^ (x >> np.uint64(30))) * _MUL1
        x = (x ^ (x >> np.uint64(27))) * _MUL2
        x = x ^ (x >> np.uint64(31))
    return x.min(axis=1)


def jaccard(a: str, b: str) -> float:
    sa, sb = shingles(a), shingles(b)
    return len(sa & sb) / max(1, len(sa | sb))


class NearDupIndex:
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self.sigs: list[np.ndarray] = []
        self.keys: list[str] = []
        self.buckets: dict[tuple[int, bytes], list[int]] = {}

    def __len__(self) -> int:
        return len(self.keys)

    def query(self, text: str, sig: np.ndarray | None = None) -> tuple[str, float] | None:
        """The most similar indexed key above the threshold (estimated Jaccard), or None."""
        sig = signature(text) if sig is None else sig
        best = None
        for c in {i for b in range(BANDS) for i in self.buckets.get((b, sig[b * ROWS:(b + 1) * ROWS].tobytes()), [])}:
            sim = float((self.sigs[c] == sig).mean())
            if sim >= self.threshold and (best is None or sim > best[1]):
                best = (self.keys[c], sim)
        return best

    def add(self, key: str, text: str, sig: np.ndarray | None = None) -> None:
        sig = signature(text) if sig is None else sig
        i = len(self.keys)
        self.keys.append(key)
        self.sigs.append(sig)
        for b in range(BANDS):
            self.buckets.setdefault((b, sig[b * ROWS:(b + 1) * ROWS].tobytes()), []).append(i)

    def check_add(self, key: str, text: str) -> tuple[str, float] | None:
        """Add the text unless it near-duplicates something already indexed; return the duplicate if so."""
        sig = signature(text)
        dup = self.query(text, sig)
        if dup is None:
            self.add(key, text, sig)
        return dup


def example_text(ex: dict) -> str:
    """What counts for duplication: the rendered state plus the question texts."""
    from kodiak_s1.schema import render_state

    return render_state(ex["state"]) + "\n" + "\n".join(q["text"] for q in ex["questions"])
