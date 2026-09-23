"""Augmentations that teach the Kodiak *contract* rather than any single dataset.

Null construction (docs/ARCHITECTURE.md §9). Each kind is tagged so eval can report it separately:
  - null:mismatch      a claim question from another text, asked about this state (the claim is unrelated)
  - null:gold_removed  the correct label is removed from the options, so "none of these" is the answer

Both only use question types where the result is unambiguously unanswerable:
mismatch donors must be claim-style questions (they carry their own specific content), and
gold removal is limited to task families whose labels are distinct (no near-synonyms).
"""

from __future__ import annotations

import copy
import random

# Families whose labels are distinct enough that removing the gold label leaves no correct option.
# Not tool routing: with the called tool removed, "no tool" or "ask for details" may become correct.
GOLD_REMOVAL_FAMILIES = {"intent", "occupation", "mc_reasoning"}


def gold_removed(ex: dict, family: str, rng: random.Random) -> dict | None:
    """Drop the gold label from one choice question; the target becomes null. None if not applicable."""
    if family not in GOLD_REMOVAL_FAMILIES:
        return None
    cands = [q for q in ex["questions"]
             if q["type"] == "choice" and q.get("allow_null", True) and "label" in ex["answers"][q["id"]]
             and len(q["labels"]) >= 3]
    if not cands:
        return None
    q = rng.choice(cands)
    gold = ex["answers"][q["id"]]["label"]
    out = copy.deepcopy(ex)
    oq = next(x for x in out["questions"] if x["id"] == q["id"])
    oq["labels"] = [lab for lab in oq["labels"] if lab["id"] != gold]
    out["questions"] = [oq]
    out["answers"] = {q["id"]: {"null": True}}
    out["meta"]["tags"] = sorted(set(out["meta"]["tags"]) | {"null:gold_removed"})
    return out


def mismatch(ex: dict, donor: dict, rng: random.Random) -> dict | None:
    """Ask `donor`'s claim question about `ex`'s state. The donor's claim is about a different text."""
    # Only two-way (yes/no, true/false) claims: the 3-way form offers "neither", which would be the right answer.
    claim_qs = [q for q in donor["questions"] if q["id"] == "claim" and q.get("allow_null", True)
                and {lab["id"] for lab in q["labels"]} == {"yes", "no"}]
    if not claim_qs:
        return None
    q = copy.deepcopy(rng.choice(claim_qs))
    return {"state": copy.deepcopy(ex["state"]), "questions": [q], "answers": {q["id"]: {"null": True}},
            "meta": {**copy.deepcopy(ex["meta"]), "tags": ["null:mismatch"],
                     "notes": f"claim from {donor['meta']['source']} asked about a {ex['meta']['source']} state"}}
