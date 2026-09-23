import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from kodiak_s1.schema import (
    ChoiceQuestion,
    Example,
    Request,
    Response,
    ScoreQuestion,
    export_json_schema,
    render_state,
)

ROOT = Path(__file__).resolve().parents[1]


def test_example_files_validate():
    Request.model_validate_json((ROOT / "schema/examples/request.json").read_text())
    Response.model_validate_json((ROOT / "schema/examples/response.json").read_text())


def test_string_labels_are_shorthand():
    q = ChoiceQuestion(id="s", text="Sentiment?", labels=["pos", "neg"])
    assert [(lab.id, lab.text) for lab in q.labels] == [("pos", "pos"), ("neg", "neg")]


@pytest.mark.parametrize(
    "labels",
    [["a"], ["a", "a"], ["A", "a "], [{"id": "x", "text": "same"}, {"id": "y", "text": "Same"}]],
)
def test_bad_label_sets_rejected(labels):
    with pytest.raises(ValidationError):
        ChoiceQuestion(id="q", text="?", labels=labels)


def test_score_range_and_unit_mapping():
    q = ScoreQuestion(id="r", text="Stars?", min=1, max=5, step=1)
    assert q.to_unit(3) == 0.5 and q.from_unit(0.5) == 3
    with pytest.raises(ValidationError):
        ScoreQuestion(id="r", text="?", min=1, max=1)


def test_duplicate_question_ids_rejected():
    q = {"id": "a", "type": "choice", "text": "?", "labels": ["x", "y"]}
    with pytest.raises(ValidationError):
        Request(state="s", questions=[q, q])


def test_unknown_fields_rejected():
    with pytest.raises(ValidationError):
        Request.model_validate({"state": "s", "questions": [], "temperature": 0.7})


def test_render_state():
    assert render_state("hi") == "hi"
    assert render_state(["a", "b"]) == "[1] a\n[2] b"
    assert render_state({"b": 1, "a": [1, 2]}) == '{"b":1,"a":[1,2]}'
    assert render_state([{"x": 1}, "y"]) == '[{"x":1},"y"]'


def _example(answers, allow_null=True):
    return {
        "state": "The package arrived crushed.",
        "questions": [
            {"id": "sent", "type": "choice", "text": "Sentiment?", "labels": ["pos", "neg"], "allow_null": allow_null},
            {"id": "sev", "type": "score", "text": "Severity?", "min": 1, "max": 5, "allow_null": allow_null},
        ],
        "answers": answers,
        "meta": {"source": "unit-test", "license": "Apache-2.0", "split": "train"},
    }


def test_example_targets_validate():
    Example.model_validate(_example({"sent": {"label": "neg"}, "sev": {"value": 4}}))
    Example.model_validate(_example({"sent": {"null": True}, "sev": {"null": True}}))
    Example.model_validate(
        _example({"sent": {"label": "neg", "probs": {"neg": 0.9, "pos": 0.05, "__null__": 0.05}}, "sev": {"value": 1}})
    )


@pytest.mark.parametrize(
    "answers,allow_null",
    [
        ({"sent": {"label": "meh"}, "sev": {"value": 4}}, True),  # label not in set
        ({"sent": {"label": "neg"}, "sev": {"value": 9}}, True),  # out of range
        ({"sent": {"value": 1}, "sev": {"value": 4}}, True),  # wrong target type
        ({"sent": {"label": "neg"}}, True),  # missing answer
        ({"sent": {"null": True}, "sev": {"value": 4}}, False),  # null not allowed
        ({"sent": {"label": "neg", "probs": {"neg": 0.5}}, "sev": {"value": 4}}, True),  # probs don't sum to 1
    ],
)
def test_bad_example_targets_rejected(answers, allow_null):
    with pytest.raises(ValidationError):
        Example.model_validate(_example(answers, allow_null))


def test_exported_json_schema_is_current(tmp_path):
    for p in export_json_schema(tmp_path):
        committed = ROOT / "schema" / p.name
        assert committed.exists(), f"run: python -m kodiak_s1.schema --export schema/ ({p.name} missing)"
        assert json.loads(committed.read_text()) == json.loads(p.read_text()), f"{p.name} is stale; re-export"
