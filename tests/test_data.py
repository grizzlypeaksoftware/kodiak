import random

from kodiak_s1.data.augment import gold_removed, mismatch
from kodiak_s1.data.sources import _nli, conv_glaive, conv_toolace, hash_split, sample_labels
from kodiak_s1.data.synth import agree, build_questions
from kodiak_s1.schema import Example


def test_sample_labels_contains_gold_and_respects_bounds():
    pool = [f"l{i}" for i in range(50)]
    for seed in range(200):
        out = sample_labels(random.Random(seed), pool, "l7", 4, 24)
        assert "l7" in out and 4 <= len(out) <= 24 and len(set(out)) == len(out)
    assert "l7" not in sample_labels(random.Random(0), pool, None, 4, 8)


def test_hash_split_is_deterministic_and_roughly_proportional():
    keys = [f"row {i}" for i in range(20_000)]
    splits = [hash_split(k) for k in keys]
    assert splits == [hash_split(k) for k in keys]
    frac_test = splits.count("test") / len(splits)
    assert 0.04 < frac_test < 0.06


def test_nli_neutral_becomes_null_only_in_two_way_form():
    seen = set()
    for seed in range(50):
        (ex,) = _nli("t", "MIT", "train", random.Random(seed), "The sky is blue.", "It rained.", "neutral")
        Example.model_validate(ex)
        target = ex["answers"]["claim"]
        if "nli2" in ex["meta"]["tags"]:
            assert target == {"null": True}
            seen.add("two")
        else:
            assert target == {"label": "neutral"}
            seen.add("three")
    assert seen == {"two", "three"}


GLAIVE_SYS = ('SYSTEM: You are a helpful assistant with access to the following functions. Use them if required -\n'
              '{"name": "convert_currency", "description": "Convert currency", "parameters": {}}\n'
              '{"name": "get_news", "description": "Get news", "parameters": {}}')


def _glaive(chat):
    exs = conv_glaive({"system": GLAIVE_SYS, "chat": chat}, "train", random.Random(0))
    for ex in exs:
        Example.model_validate(ex)
    return exs[0]["answers"]["tool"]["label"] if exs else None


def test_glaive_first_move_labels():
    call = ('USER: Convert 5 USD to EUR\n\n\nASSISTANT: <functioncall> {"name": "convert_currency", "arguments": \'{}\'} '
            '<|endoftext|>\n\n\nFUNCTION RESPONSE: {}')
    later_call = ('USER: Convert 5 USD to EUR\n\n\nASSISTANT: Sure, one moment. <|endoftext|>\n\n\n'
                  'ASSISTANT: <functioncall> {"name": "convert_currency", "arguments": \'{}\'} <|endoftext|>')
    decline = "USER: Book me a flight\n\n\nASSISTANT: I'm sorry, but I can't book flights. <|endoftext|>"
    clarify = "USER: Convert some money\n\n\nASSISTANT: Sure! Which currencies and how much? <|endoftext|>"
    ambiguous = "USER: Convert some money\n\n\nASSISTANT: Sure, let me help. <|endoftext|>\n\n\nUSER: 5 USD to EUR"
    assert _glaive(call) == "convert_currency"
    assert _glaive(later_call) == "convert_currency"
    assert _glaive(decline) == "__none__"
    assert _glaive(clarify) == "__clarify__"
    assert _glaive(ambiguous) is None


def test_toolace_parses_function_list_and_skips_non_calls():
    system = ('Here is a list of functions in JSON format that you can invoke:\n'
              '[{"name": "Get Fare", "description": "Fare lookup"}, {"name": "Weather", "description": "Forecast"}]. \n'
              'Put it in the format of [func1(params_name=params_value), func2(params)]')
    row = {"system": system, "conversations": [{"from": "user", "value": "fare for train 7?"},
                                               {"from": "assistant", "value": '[Get Fare(train="7")]'}]}
    (ex,) = conv_toolace(row, "train", random.Random(0))
    Example.model_validate(ex)
    assert ex["answers"]["tool"]["label"] == "Get Fare"
    row["conversations"][1]["value"] = "Which train number do you mean?"
    assert conv_toolace(row, "train", random.Random(0)) == []


def _mc_example():
    q = {"type": "choice", "id": "intent", "text": "Intent?", "allow_null": True,
         "labels": [{"id": "a", "text": "alpha"}, {"id": "b", "text": "beta"}, {"id": "c", "text": "gamma"}]}
    return {"state": "s", "questions": [q], "answers": {"intent": {"label": "b"}},
            "meta": {"source": "x", "license": "MIT", "split": "test", "tags": []}}


def test_gold_removed_drops_gold_and_targets_null():
    ex = gold_removed(_mc_example(), "intent", random.Random(0))
    Example.model_validate(ex)
    assert [lab["id"] for lab in ex["questions"][0]["labels"]] == ["a", "c"]
    assert ex["answers"] == {"intent": {"null": True}} and "null:gold_removed" in ex["meta"]["tags"]
    assert gold_removed(_mc_example(), "emotion", random.Random(0)) is None  # near-synonym labels: not allowed
    assert gold_removed(_mc_example(), "tool_routing", random.Random(0)) is None


def test_mismatch_uses_only_two_way_claims():
    two_way = {"questions": [{"type": "choice", "id": "claim", "text": "Is it true that X?", "allow_null": True,
                              "labels": [{"id": "yes", "text": "true"}, {"id": "no", "text": "false"}]}],
               "meta": {"source": "mnli"}}
    three_way = {"questions": [{"type": "choice", "id": "claim", "text": "Status of X?", "allow_null": True,
                                "labels": [{"id": "entailment", "text": "s"}, {"id": "neutral", "text": "n"},
                                           {"id": "contradiction", "text": "c"}]}], "meta": {"source": "mnli"}}
    ex = mismatch(_mc_example(), two_way, random.Random(0))
    Example.model_validate(ex)
    assert ex["answers"] == {"claim": {"null": True}}
    assert mismatch(_mc_example(), three_way, random.Random(0)) is None


def test_synth_evidence_must_be_in_state():
    state = "Order #4411 shipped via UPS on May 3."
    raw = [
        {"id": "carrier", "type": "choice", "text": "Carrier?", "unanswerable": False, "answer_label": "ups",
         "labels": [{"id": "ups", "text": "UPS"}, {"id": "fedex", "text": "FedEx"}], "evidence": "shipped via UPS"},
        {"id": "made_up", "type": "choice", "text": "Paid?", "unanswerable": False, "answer_label": "yes",
         "labels": [{"id": "yes", "text": "yes"}, {"id": "no", "text": "no"}], "evidence": "payment received"},
        {"id": "weight", "type": "score", "text": "Weight?", "min": 0, "max": 10, "unanswerable": True, "evidence": ""},
    ]
    qs, answers, drops = build_questions(raw, state)
    assert [q["id"] for q in qs] == ["carrier", "weight"]
    assert answers == {"carrier": {"label": "ups"}, "weight": {"null": True}}
    assert drops == ["evidence_not_in_state"]


def test_synth_agreement_rules():
    choice = {"type": "choice"}
    score = {"type": "score", "min": 0, "max": 10}
    assert agree(choice, {"label": "a"}, {"label": "a", "unanswerable": False})[0]
    assert not agree(choice, {"label": "a"}, {"label": "b", "unanswerable": False})[0]
    assert agree(choice, {"null": True}, {"unanswerable": True})[0]
    assert not agree(choice, {"null": True}, {"label": "a", "unanswerable": False})[0]
    assert not agree(choice, {"label": "a"}, {"unanswerable": True})[0]
    ok, target = agree(score, {"value": 6.0}, {"value": 7.0, "unanswerable": False})
    assert ok and target == {"value": 6.5}
    assert not agree(score, {"value": 2.0}, {"value": 7.0, "unanswerable": False})[0]
    assert not agree(choice, {"label": "a"}, None)[0]


def test_verifier_schema_and_parse():
    from kodiak_s1.data.synth import UNANSWERABLE, parse_verdict, verify_schema

    choice = {"type": "choice", "id": "c", "labels": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}]}
    score = {"type": "score", "id": "s", "min": 0, "max": 10}
    schema = verify_schema([choice, score])
    assert schema["properties"]["c"]["properties"]["answer"]["enum"] == ["a", "b", UNANSWERABLE]
    assert list(schema["properties"]["c"]["properties"]) == ["quote", "answer"]  # evidence before answer
    assert parse_verdict(choice, {"quote": "x", "answer": "b"}) == {"unanswerable": False, "label": "b"}
    assert parse_verdict(score, {"quote": "", "answer": UNANSWERABLE}) == {"unanswerable": True}
    assert parse_verdict(score, {"quote": "x", "answer": "7.5"}) == {"unanswerable": False, "value": 7.5}
    assert parse_verdict(score, {"quote": "x", "answer": "high"}) is None
    assert parse_verdict(choice, None) is None


def test_synth_drops_malformed_choice_questions():
    raw = [
        {"id": "nolabels", "type": "choice", "text": "Team?", "unanswerable": False, "answer_label": "alpha",
         "labels": [], "evidence": "Alpha"},
        {"id": "badanswer", "type": "choice", "text": "Team?", "unanswerable": False, "answer_label": "gamma",
         "labels": [{"id": "alpha", "text": "Alpha"}, {"id": "beta", "text": "Beta"}], "evidence": "Alpha"},
    ]
    qs, _, drops = build_questions(raw, "Alpha holds zone A.")
    assert qs == [] and drops == ["choice_too_few_labels", "answer_not_in_labels"]


def test_synth_evidence_matches_compact_json_state():
    from kodiak_s1.schema import render_state

    state = render_state({"order": {"status": "shipped", "items": [1, 2]}})
    raw = [{"id": "s", "type": "choice", "text": "Status?", "unanswerable": False, "answer_label": "shipped",
            "labels": [{"id": "shipped", "text": "shipped"}, {"id": "pending", "text": "pending"}],
            "evidence": '"status": "shipped"'}]
    qs, _, drops = build_questions(raw, state)
    assert len(qs) == 1 and drops == []
