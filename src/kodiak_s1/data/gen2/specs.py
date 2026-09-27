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

# Stage 3 (--focus scores): judgment scales with explicit anchors (low, middle, high). The v2.0 model rated "charged twice and
# nobody answers my emails!" 0.9/10 for urgency: public score data is mostly moderation/quality ratings near zero, so it
# learned "scores are low". Target bands (low / medium / high per question) and contrast twins attack that prior directly.
SCORE_FOCUS_SCALES = {
    "urgency": ("can wait weeks", "should be handled today", "act immediately: safety, money or a hard deadline at risk"),
    "severity": ("trivial or cosmetic", "real impact but a workaround exists", "critical: outage, harm or major loss"),
    "priority": ("backlog, nice to have", "this week", "top of the queue right now"),
    "risk": ("negligible risk", "moderate risk worth watching", "high risk of serious harm or loss"),
    "customer frustration": ("calm or pleased", "annoyed", "furious, threatening to leave or escalate"),
    "financial impact": ("no money at stake", "a noticeable amount", "large or business-critical sums"),
    "likelihood of escalation": ("very unlikely", "possible", "almost certain"),
    "confidence that the claim is true": ("clearly false", "uncertain", "clearly true"),
    "sentiment": ("very negative", "neutral", "very positive"),
    "politeness": ("rude or hostile", "neutral", "very courteous"),
    "completeness of the information provided": ("most required details missing", "some details missing", "everything needed is there"),
    "quality of the response": ("unhelpful or wrong", "partly helpful", "excellent and complete"),
    "hostility or toxicity": ("not hostile at all", "somewhat hostile", "extremely hostile or abusive"),
    "credibility": ("not credible", "somewhat credible", "highly credible"),
}
TARGET_BANDS = {"low": "bottom third", "medium": "middle third", "high": "top third"}

# Polarity focus (--focus polarity, GENERATOR_V2 §13): the categorizer demo showed Kodiak calling two-sided reviews "positive";
# the training data barely has "mixed" or "neutral" as answers. Opinionated document types, one target per job. Poems and
# financial posts are left out on purpose: poem_sentiment and fin_tweets_sentiment are never-seen tasks in eval v0.2.
POLARITY_DOCS = [
    ("retail and e-commerce", "product review", ("text",)), ("travel and hospitality", "hotel review", ("text",)),
    ("food service", "restaurant review", ("text",)), ("software", "app store review", ("text",)),
    ("customer support", "customer support email", ("text",)), ("customer support", "live chat transcript", ("list",)),
    ("customer support", "support ticket with customer comments", ("json",)),
    ("human resources", "employee engagement survey response", ("text", "json")), ("education", "course evaluation comment", ("text",)),
    ("healthcare", "patient feedback form", ("text", "json")), ("real estate", "tenant message to a property manager", ("text",)),
    ("procurement", "vendor performance review note", ("text",)), ("events", "post-event attendee feedback", ("text", "json")),
    ("SaaS", "NPS survey comment", ("text", "json")), ("online community", "forum post", ("text", "list")),
    ("media", "comment thread under an article", ("list",)), ("automotive", "car service center review", ("text",)),
    ("professional services", "client email to an agency after a project milestone", ("text",)),
    ("public sector", "resident comment on a city proposal", ("text",)), ("gaming", "video game review", ("text",)),
    ("fitness", "gym member feedback", ("text",)), ("publishing", "book review", ("text",)),
    ("software engineering", "code review comment thread", ("list",)), ("teams", "sprint retrospective notes", ("text", "list")),
    ("logistics", "delivery experience feedback", ("text", "json")), ("banking", "customer letter to a bank branch", ("text",)),
    ("telecom", "internet service provider review", ("text",)), ("home services", "contractor review", ("text",)),
    ("hiring", "candidate feedback about an interview process", ("text",)), ("pets", "veterinary clinic review", ("text",)),
]
# A "review" with no opinion is a contradiction (pilot: critics called such tone questions unanswerable), so neutral targets use
# message-like documents, framed as sentiment or tone rather than satisfaction or stance.
NEUTRAL_OK = {"customer support email", "live chat transcript", "support ticket with customer comments", "tenant message to a property manager",
              "forum post", "comment thread under an article", "client email to an agency after a project milestone",
              "resident comment on a city proposal", "code review comment thread", "customer letter to a bank branch",
              "sprint retrospective notes"}
POLARITY_TARGETS = {"mixed": 0.35, "neutral": 0.30, "positive": 0.175, "negative": 0.175}
# Concept sets for the overall-tone question (the writer words the labels). Each must contain the target.
POLARITY_LABEL_SETS = [
    ("positive", "negative", "mixed", "neutral"), ("positive", "negative", "mixed", "neutral"),
    ("positive", "negative", "neutral"), ("positive", "negative", "mixed"),
    ("very positive", "somewhat positive", "mixed", "neutral", "somewhat negative", "very negative"),
]
POLARITY_FRAMES = ["overall sentiment", "overall tone toward the product, service or proposal", "the writer's overall satisfaction",
                   "the writer's stance"]

# Unfamiliar-input focus (--focus unfamiliar, D32 2a): formats and domains far from the public datasets and the v2.0 taxonomy, with questions
# that look answerable but aren't mixed with ones that are. Teaches "unsure when lost" without teaching "refuse whatever is unusual".
UNFAMILIAR_DOCS = [
    ("games", "text adventure game transcript with the current room and inventory (an original game, not a published one)", ("text", "list")),
    ("games", "board game position described move by move", ("text", "list")), ("games", "tabletop RPG character sheet", ("json",)),
    ("games", "video game save file", ("json",)), ("software", "YAML-like configuration file rendered as JSON", ("json",)),
    ("software", "unified diff of a code change with its commit message", ("text",)), ("software", "stack trace with surrounding log lines", ("list",)),
    ("software", "cron schedule and job definitions", ("json",)), ("software", "shell session transcript", ("list",)),
    ("data", "CSV excerpt with a header row, written as text", ("text",)), ("data", "SQL query with its result rows", ("text",)),
    ("IoT", "sensor telemetry readings over an hour", ("json", "list")), ("IoT", "smart home automation event log", ("list",)),
    ("science", "lab notebook entry with measurements", ("text",)), ("science", "astronomy observation log", ("list",)),
    ("music", "setlist with song keys and tempos", ("json", "text")), ("music", "guitar tab with annotations", ("text",)),
    ("transport", "train timetable excerpt with platform changes", ("json", "text")), ("transport", "ship's log entries", ("list",)),
    ("aviation", "decoded weather report (METAR) with remarks", ("text",)), ("sports", "play-by-play commentary excerpt", ("list",)),
    ("cooking", "recipe with scaled quantities and substitutions", ("text",)), ("gardening", "planting calendar and bed layout", ("json",)),
    ("hobbies", "knitting pattern with row instructions", ("text",)), ("hobbies", "model railway layout inventory", ("json",)),
    ("agents", "AI agent tool-call trace with tool results", ("list", "json")), ("agents", "multi-agent chat where agents hand off a task", ("list",)),
    ("manufacturing", "CNC machine job sheet", ("json",)), ("genealogy", "family tree record with uncertain dates", ("json", "text")),
    ("chess", "chess game in algebraic notation with comments", ("text",)),
]
UNFAMILIAR_NULL_KINDS = ["missing_fact", "underspecified", "temporal", "out_of_scope", "no_option_fits"]

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
    focus: str | None = None  # "scores" = Stage 3 judgment-score batch
    targets: list[str] = field(default_factory=list)  # per score question: low | medium | high
    pair: bool = False  # also write a minimal-edit contrast twin that moves the first score to the other end
    polarity: str | None = None  # --focus polarity: the correct overall tone (mixed | neutral | positive | negative)
    polarity_labels: list[str] = field(default_factory=list)  # concepts the tone question's labels must cover
    polarity_frame: str | None = None

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


def sample_spec(job: int, seed: int, tax: dict, coverage: dict | None = None, focus: str | None = None) -> Spec:
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
    spec = Spec(job=job, mode=mode, source=source, sector=sector, domain=domain, doc_type=doc_type, format=fmt,
                decision=decision, difficulty=difficulty, n_choice=n_choice, n_score=n_score, n_inference=n_inference,
                n_null=n_null, null_kinds=null_kinds, scales=scales, ranges=ranges)
    if focus == "scores":  # drawn from a separate RNG stream so the default specs above are unchanged
        _score_focus(spec, rng_for("gen2-spec-scores", seed, job), tax)
    elif focus == "unfamiliar":
        _unfamiliar_focus(spec, rng_for("gen2-spec-unfamiliar", seed, job))
    elif focus == "polarity":
        _polarity_focus(spec, rng_for("gen2-spec-polarity", seed, job))
    return spec


def _unfamiliar_focus(spec: Spec, rng) -> None:
    """D32 (2a): unusual states; 3-5 choice questions, 1-2 of them unanswerable (looking answerable), at least one answerable by inference."""
    spec.source, spec.mode, spec.focus = "synthetic", "unfamiliar", "unfamiliar"
    spec.sector, spec.doc_type, fmts = rng.choice(UNFAMILIAR_DOCS)
    spec.domain = spec.doc_type
    spec.format = rng.choice(list(fmts))
    spec.decision = rng.choice(["classification", "extraction_choice", "comparison", "next_action", "compliance"])
    spec.n_score, spec.scales, spec.ranges, spec.targets, spec.pair = 0, [], [], [], False
    spec.n_choice = rng.choice([3, 4, 4, 5])
    spec.n_null = _weighted(rng, [1, 2], [0.5, 0.5])
    spec.null_kinds = [rng.choice(UNFAMILIAR_NULL_KINDS) for _ in range(spec.n_null)]
    spec.n_inference = 1


def _polarity_focus(spec: Spec, rng) -> None:
    """GENERATOR_V2 §13: an opinionated document whose overall tone is the target, a tone question whose options include the
    target, and aspect questions (for mixed documents: which parts are praised and which criticized)."""
    spec.source, spec.mode = "synthetic", "polarity"
    spec.focus, spec.decision = "polarity", "classification"
    spec.polarity = _weighted(rng, list(POLARITY_TARGETS), list(POLARITY_TARGETS.values()))
    docs = [d for d in POLARITY_DOCS if d[1] in NEUTRAL_OK] if spec.polarity == "neutral" else POLARITY_DOCS
    spec.sector, spec.doc_type, fmts = rng.choice(docs)
    spec.domain = spec.doc_type
    spec.format = rng.choice(list(fmts))
    sets = [ls for ls in POLARITY_LABEL_SETS if spec.polarity in ls or (spec.polarity in ("positive", "negative") and len(ls) == 6)]
    labels = list(rng.choice(sets))
    if spec.polarity in ("positive", "negative") and len(labels) == 6:
        spec.polarity = rng.choice([f"very {spec.polarity}", f"somewhat {spec.polarity}"])
    spec.polarity_labels = labels
    spec.polarity_frame = rng.choice(POLARITY_FRAMES[:2] if spec.polarity == "neutral" else POLARITY_FRAMES)
    spec.n_score, spec.scales, spec.ranges, spec.targets, spec.pair = 0, [], [], [], False
    spec.n_choice = rng.choice([2, 3, 3])
    spec.n_null = _weighted(rng, [0, 1], [0.6, 0.4])
    spec.null_kinds = [rng.choice(["missing_fact", "out_of_scope", "underspecified"]) for _ in range(spec.n_null)]
    spec.n_inference = max(1, min(2, spec.n_choice - spec.n_null))


def _score_focus(spec: Spec, rng, tax: dict) -> None:
    """Stage 3: 2-3 anchored score questions with target bands, few nulls, and a contrast twin on ~half the jobs."""
    if spec.source == "grounded":  # ratings like urgency or frustration need a situation, not an encyclopedia passage
        spec.source = "synthetic"
        spec.sector, spec.domain, spec.doc_type, fmts = rng.choice(cells(tax))
        spec.format = rng.choice(list(fmts))
    spec.focus, spec.decision = "scores", "judgment_score"
    spec.n_score = rng.choice([2, 2, 3])
    spec.n_choice = rng.choice([1, 1, 2])
    n = spec.n_choice + spec.n_score
    spec.n_null = _weighted(rng, [0, 1], [0.65, 0.35])
    spec.null_kinds = [rng.choice(["missing_fact", "underspecified", "temporal"]) for _ in range(spec.n_null)]
    spec.n_inference = max(1, min(spec.n_score, n - spec.n_null - 1))
    spec.scales = []  # the writer picks dimensions that fit the document (pilot #3: random scales made nonsense questions)
    spec.ranges = [_weighted(rng, [r for r, _ in SCORE_RANGES], [w for _, w in SCORE_RANGES]) for _ in range(spec.n_score)]
    spec.targets = [rng.choice(list(TARGET_BANDS)) for _ in range(spec.n_score)]
    spec.pair = spec.source == "synthetic" and rng.random() < 0.5


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
