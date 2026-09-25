"""Specs: a small, explicit recipe for each generation job, sampled deterministically from the job id.

v1 picked a random domain string and let the teacher decide everything else, so the mix drifted toward whatever the
teacher found easy. A spec pins down *what* to make (setting, decision type, scale wording, difficulty, how many
unanswerable questions and of which kind, how many answerable-by-inference questions), which makes the mix measurable
(the coverage map) and steerable (weights now, the planner in v2.2).

Sampling modes (v2.0): 60% "coverage", which walks a shuffled list of every taxonomy cell so each document type is used
before any repeats, and weights the other axes toward values that are thin in the coverage snapshot; 40% "explore",
which samples everything uniformly. Both are pure functions of (seed, job id, taxonomy, coverage snapshot).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from kodiak_s1.data.gen2.taxonomy import cells
from kodiak_s1.data.sources import rng_for

# What kind of decision the question set focuses on (at least one or two questions of this kind per job).
DECISIONS = {
    "classification": "sort the state into one of several categories (its topic, intent, type, or the department it concerns)",
    "extraction_choice": "pick which of several specific candidate values (a date, amount, name, status, ID) is the one the state gives",
    "judgment_score": "rate something about the state on a numeric scale that needs judgment",
    "routing": "choose which tool, team, queue or handler should take this next (options may include asking for missing details)",
    "comparison": "compare things within the state (which is larger, earlier, cheaper, riskier, better supported)",
    "compliance": "check whether the state meets a stated rule, policy or condition (options like yes / no / partially)",
    "next_action": "choose the best next action for whoever has to respond to this state",
    "claim_check": "decide whether a specific claim is supported or contradicted by the text (if the text does not "
                   "address the claim at all, that question is unanswerable)",
}
# Pilot lesson (2026-09-25): routing / next-action / compliance questions about a real web article came out contrived
# ("which processing queue should handle a correction about Nakhichevan?"), so grounded jobs use reader-style decisions.
SYNTHETIC_DECISIONS = [d for d in DECISIONS if d != "claim_check"]
GROUNDED_DECISIONS = ["classification", "extraction_choice", "judgment_score", "comparison", "claim_check"]

# Scale wordings for score questions: the thing being rated. The writer supplies the anchor texts.
SCALES = [
    "urgency", "severity", "priority", "risk", "confidence that the claim is true", "overall quality", "sentiment",
    "customer satisfaction", "frustration", "politeness", "formality", "hostility or toxicity", "relevance to the stated goal",
    "completeness", "clarity", "credibility", "likelihood of the described outcome", "effort required", "financial impact",
    "technical depth", "reading difficulty", "persuasiveness",
]
SCORE_RANGES = [((0, 1), 2), ((1, 5), 3), ((0, 10), 3), ((0, 100), 2), ((1, 10), 1), ((1, 7), 1)]

DIFFICULTY = {"easy": 0.3, "medium": 0.4, "hard": 0.3}

# Why an unanswerable question is unanswerable. v1 had essentially one kind ("the fact is never mentioned"),
# which taught Kodiak "no literal statement -> abstain" and caused over-abstention on inference questions.
NULL_KINDS = {
    "missing_fact": "asks for a specific detail the state never gives (e.g. an order number when none appears)",
    "out_of_scope": "asks about a nearby thing the state does not cover (a different person, period, product or topic), "
                    "while still sounding related",
    "no_option_fits": "a choice question where the state does settle the matter, but none of the offered options matches "
                      "(e.g. the state says Tuesday; the options are Monday, Wednesday and Friday)",
    "underspecified": "the state touches the topic but does not give enough to choose (e.g. it mentions a delay but never "
                      "how long); not a matter of judgment",
    "temporal": "asks about an outcome that is not known yet at the time of the state (a pending decision, a future result)",
}

GROUNDED_SHARE = 0.45  # share of jobs that use a real FineWeb-Edu passage as the state
COVERAGE_SHARE = 0.6


@dataclass
class Spec:
    job: int
    mode: str  # coverage | explore
    source: str  # grounded | synthetic
    sector: str | None
    domain: str | None
    doc_type: str
    format: str  # text | list | json
    decision: str
    difficulty: str
    n_choice: int
    n_score: int
    n_inference: int
    n_null: int
    null_kinds: list[str] = field(default_factory=list)
    scales: list[str] = field(default_factory=list)  # one per score question
    ranges: list[tuple[float, float]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def cell(self) -> dict[str, str]:
        """Coverage-map keys (one count per axis value)."""
        return {"source": self.source, "decision": self.decision, "difficulty": self.difficulty,
                "format": self.format, "sector": self.sector or "grounded"}


def _weighted(rng, items: list, weights: list[float]):
    return rng.choices(items, weights=weights, k=1)[0]


def _balance(values: list[str], base: list[float], counts: dict[str, int] | None) -> list[float]:
    """Coverage weighting ∝ 1 / (0.1 + count / average): a value at twice the average count gets about half the
    weight of an average one, and an empty value gets 10x, so gaps fill fast."""
    if not counts:
        return base
    avg = max(1.0, sum(counts.get(v, 0) for v in values) / len(values))
    return [b / (0.1 + counts.get(v, 0) / avg) for v, b in zip(values, base)]


def sample_spec(job: int, seed: int, tax: dict, coverage: dict | None = None) -> Spec:
    rng = rng_for("gen2-spec", seed, job)
    cov = coverage or {}
    mode = "coverage" if rng.random() < COVERAGE_SHARE else "explore"
    bal = (lambda axis, vals, base: _balance(vals, base, cov.get(axis))) if mode == "coverage" else (lambda a, v, b: b)

    source = _weighted(rng, ["grounded", "synthetic"], bal("source", ["grounded", "synthetic"],
                                                           [GROUNDED_SHARE, 1 - GROUNDED_SHARE]))
    if source == "grounded":
        sector = domain = None
        doc_type, fmt = "real web document excerpt", "text"
    else:
        all_cells = cells(tax)
        if mode == "coverage":
            # Walk a seed-shuffled list of every document type, so each is used once before any repeats.
            order = list(range(len(all_cells)))
            rng_for("gen2-cells", seed).shuffle(order)
            sector, domain, doc_type, fmts = all_cells[order[job % len(order)]]
        else:
            sector, domain, doc_type, fmts = rng.choice(all_cells)
        fmt = rng.choice(list(fmts))

    decisions = GROUNDED_DECISIONS if source == "grounded" else SYNTHETIC_DECISIONS
    decision = _weighted(rng, decisions, bal("decision", decisions, [1.0] * len(decisions)))
    diffs = list(DIFFICULTY)
    difficulty = _weighted(rng, diffs, bal("difficulty", diffs, list(DIFFICULTY.values())))

    n = rng.randint(3, 5)
    n_score = rng.choice([1, 2]) if decision == "judgment_score" else rng.choice([0, 0, 1])
    n_choice = max(1, n - n_score)
    n = n_choice + n_score
    n_null = _weighted(rng, [0, 1, 2], [0.2, 0.55, 0.25])
    n_inference = max(1, min(rng.choice([1, 1, 2]), n - n_null - 1))
    n_null = min(n_null, n - n_inference)
    null_kinds = [_weighted(rng, list(NULL_KINDS), bal("null_kind", list(NULL_KINDS), [1.0] * len(NULL_KINDS)))
                  for _ in range(n_null)]
    scales = [_weighted(rng, SCALES, bal("scale", SCALES, [1.0] * len(SCALES))) for _ in range(n_score)]
    ranges = [_weighted(rng, [r for r, _ in SCORE_RANGES], [w for _, w in SCORE_RANGES]) for _ in range(n_score)]
    return Spec(job=job, mode=mode, source=source, sector=sector, domain=domain, doc_type=doc_type, format=fmt,
                decision=decision, difficulty=difficulty, n_choice=n_choice, n_score=n_score, n_inference=n_inference,
                n_null=n_null, null_kinds=null_kinds, scales=scales, ranges=ranges)


# ---- coverage map ------------------------------------------------------------------------------------------------

def coverage_from_records(paths: list[str | Path]) -> dict[str, dict[str, int]]:
    """Count kept (status ok) gen2 examples per axis value, from generator output files."""
    cov: dict[str, dict[str, int]] = {}

    def bump(axis: str, value: str) -> None:
        cov.setdefault(axis, {})
        cov[axis][value] = cov[axis].get(value, 0) + 1

    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        for line in p.open(encoding="utf-8"):
            r = json.loads(line)
            if r.get("status") != "ok" or "spec" not in r:
                continue
            s = r["spec"]
            for axis in ("source", "decision", "difficulty", "format"):
                bump(axis, s[axis])
            bump("sector", s.get("sector") or "grounded")
            if s.get("domain"):
                bump("domain", s["domain"])
            for k in s.get("null_kinds", []):
                bump("null_kind", k)
            for sc in s.get("scales", []):
                bump("scale", sc)
    return cov
