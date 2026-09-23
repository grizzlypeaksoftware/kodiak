"""The Kodiak contract: requests, responses, and training examples.

These pydantic models are the single source of truth. The JSON Schema files in
`schema/` are generated from them (`python -m kodiak_s1.schema --export schema/`)
so the Node.js server can validate against exactly the same rules.

Abstention ("null") is not a separate question type: it is an answer that any
question may receive, controlled per question by `allow_null`.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# v0.1 limits. Character limits are enforced here; token budgets are enforced
# after tokenization (see docs/ARCHITECTURE.md, "Limits").
MAX_QUESTIONS = 32
MAX_LABELS = 32
MAX_QUESTION_CHARS = 500
MAX_LABEL_CHARS = 200
MAX_ID_CHARS = 64

Id = Annotated[str, Field(min_length=1, max_length=MAX_ID_CHARS, pattern=r"^[A-Za-z0-9_.:\-]+$")]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------


class Label(_Strict):
    """One option in a choice question. `text` is what the model reads; `id` is what it returns."""

    # Free text, since the string shorthand makes the label text its own id.
    id: str = Field(min_length=1, max_length=MAX_LABEL_CHARS)
    text: str = Field(min_length=1, max_length=MAX_LABEL_CHARS)


class ChoiceQuestion(_Strict):
    type: Literal["choice"] = "choice"
    id: Id
    text: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    labels: list[Label] = Field(min_length=2, max_length=MAX_LABELS)
    allow_null: bool = True

    @field_validator("labels", mode="before")
    @classmethod
    def _coerce_labels(cls, v: Any) -> Any:
        # Accept plain strings as shorthand: "positive" -> {"id": "positive", "text": "positive"}.
        if isinstance(v, list):
            return [{"id": x, "text": x} if isinstance(x, str) else x for x in v]
        return v

    @field_validator("labels")
    @classmethod
    def _unique_labels(cls, v: list[Label]) -> list[Label]:
        ids = [lab.id for lab in v]
        if len(set(ids)) != len(ids):
            raise ValueError("label ids must be unique within a question")
        texts = [lab.text.strip().casefold() for lab in v]
        if len(set(texts)) != len(texts):
            raise ValueError("label texts must be distinct within a question")
        return v


class ScoreQuestion(_Strict):
    type: Literal["score"] = "score"
    id: Id
    text: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    min: float = 0.0
    max: float = 1.0
    # Optional anchor descriptions shown to the model, e.g. "not urgent" / "drop everything".
    min_label: str | None = Field(default=None, max_length=MAX_LABEL_CHARS)
    max_label: str | None = Field(default=None, max_length=MAX_LABEL_CHARS)
    # Optional output granularity (e.g. 1 for a 1-5 star rating). Applied to the reported value only.
    step: float | None = Field(default=None, gt=0)
    allow_null: bool = True

    @model_validator(mode="after")
    def _check_range(self) -> ScoreQuestion:
        if not (math.isfinite(self.min) and math.isfinite(self.max)) or self.min >= self.max:
            raise ValueError("score range requires finite min < max")
        return self

    def to_unit(self, value: float) -> float:
        return (value - self.min) / (self.max - self.min)

    def from_unit(self, u: float) -> float:
        return self.min + u * (self.max - self.min)


Question = Annotated[Union[ChoiceQuestion, ScoreQuestion], Field(discriminator="type")]

# A state is plain text, a list of texts (e.g. a conversation or several documents),
# or arbitrary JSON (object or array).
State = Union[str, list[str], dict[str, Any], list[Any]]


def render_state(state: State) -> str:
    """Serialize a state to the exact text the encoder reads.

    Training and inference must use this same function, or the model sees
    a different format at inference than it was trained on.
    """
    if isinstance(state, str):
        return state
    if isinstance(state, list) and all(isinstance(x, str) for x in state):
        return "\n".join(f"[{i + 1}] {x}" for i, x in enumerate(state))
    return json.dumps(state, ensure_ascii=False, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class Options(_Strict):
    # Abstain as "unanswerable" when p_null >= null_threshold.
    null_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    # Abstain as "low_confidence" when the best choice's probability < min_confidence.
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    # Width of the central credible interval reported for score answers.
    interval: float = Field(default=0.9, gt=0.0, lt=1.0)


class Request(_Strict):
    state: State
    questions: list[Question] = Field(min_length=1, max_length=MAX_QUESTIONS)
    options: Options = Options()

    @field_validator("questions")
    @classmethod
    def _unique_ids(cls, v: list[Question]) -> list[Question]:
        ids = [q.id for q in v]
        if len(set(ids)) != len(ids):
            raise ValueError("question ids must be unique")
        return v


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

AbstainReason = Literal["unanswerable", "low_confidence"]


class ChoiceAnswer(_Strict):
    type: Literal["choice"] = "choice"
    # A label id from the request, or None when abstaining. Never anything else.
    answer: str | None
    # The chosen label's probability; p_null if "unanswerable"; the best label's
    # (sub-threshold) probability if "low_confidence". See docs/ARCHITECTURE.md §5.5.
    confidence: float
    # Unconditional probabilities: sum(probs.values()) + p_null == 1.
    probs: dict[str, float]
    p_null: float
    abstain_reason: AbstainReason | None = None


class ScoreAnswer(_Strict):
    type: Literal["score"] = "score"
    # Posterior mean in the question's [min, max] range (rounded to `step` if given), or None.
    answer: float | None
    mean: float | None
    std: float | None
    interval: tuple[float, float] | None
    p_null: float
    abstain_reason: AbstainReason | None = None


Answer = Annotated[Union[ChoiceAnswer, ScoreAnswer], Field(discriminator="type")]


class Response(_Strict):
    model: str
    answers: dict[str, Answer]
    latency_ms: float | None = None


# ---------------------------------------------------------------------------
# Training examples
# ---------------------------------------------------------------------------


class ChoiceTarget(_Strict):
    label: str
    # Optional soft target from a teacher, over label ids (+ "__null__"). Must sum to ~1.
    probs: dict[str, float] | None = None


class ScoreTarget(_Strict):
    value: float


class NullTarget(_Strict):
    null: Literal[True] = True


Target = Union[ChoiceTarget, ScoreTarget, NullTarget]


class Meta(_Strict):
    source: str  # dataset or generator id, must appear in data/LICENSES.md
    license: str  # SPDX id where possible
    split: Literal["train", "val", "test"]
    teacher: str | None = None  # e.g. "qwen3.8:27b" for synthetic labels
    notes: str | None = None


class Example(_Strict):
    """One training/eval record: a request plus gold answers for every question."""

    state: State
    questions: list[Question] = Field(min_length=1, max_length=MAX_QUESTIONS)
    answers: dict[str, Target]
    meta: Meta

    @model_validator(mode="after")
    def _check_answers(self) -> Example:
        qs = {q.id: q for q in self.questions}
        if len(qs) != len(self.questions):
            raise ValueError("question ids must be unique")
        if set(self.answers) != set(qs):
            raise ValueError("answers must cover exactly the question ids")
        for qid, t in self.answers.items():
            q = qs[qid]
            if isinstance(t, NullTarget):
                if not q.allow_null:
                    raise ValueError(f"{qid}: null target but allow_null is false")
            elif isinstance(q, ChoiceQuestion):
                if not isinstance(t, ChoiceTarget):
                    raise ValueError(f"{qid}: choice question needs a label or null target")
                ids = {lab.id for lab in q.labels}
                if t.label not in ids:
                    raise ValueError(f"{qid}: label {t.label!r} not in the question's labels")
                if t.probs is not None:
                    allowed = ids | ({"__null__"} if q.allow_null else set())
                    if not set(t.probs) <= allowed:
                        raise ValueError(f"{qid}: soft target has unknown keys")
                    if abs(sum(t.probs.values()) - 1.0) > 1e-3:
                        raise ValueError(f"{qid}: soft target must sum to 1")
            else:
                if not isinstance(t, ScoreTarget):
                    raise ValueError(f"{qid}: score question needs a value or null target")
                if not (q.min <= t.value <= q.max):
                    raise ValueError(f"{qid}: value {t.value} outside [{q.min}, {q.max}]")
        return self


# ---------------------------------------------------------------------------
# JSON Schema export
# ---------------------------------------------------------------------------

EXPORTS = {"request": Request, "response": Response, "example": Example}


def export_json_schema(out_dir: str | Path) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, model in EXPORTS.items():
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"https://github.com/grizzlypeaksoftware/kodiak/schema/kodiak-{name}.schema.json"
        p = out / f"kodiak-{name}.schema.json"
        p.write_text(json.dumps(schema, indent=2) + "\n")
        paths.append(p)
    return paths


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Export Kodiak JSON Schemas")
    ap.add_argument("--export", default="schema", help="output directory")
    for p in export_json_schema(ap.parse_args().export):
        print(p)
