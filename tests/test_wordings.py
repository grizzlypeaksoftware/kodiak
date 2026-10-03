import random

from kodiak_s1.data.wordings import reword, vocab

TABLE = {"positive": {"description": "The text expresses a favorable feeling.", "paraphrase": "upbeat"},
         "negative": {"description": "The text expresses an unfavorable feeling.", "paraphrase": "downbeat"}}


def ex(labels):
    return {"state": "x", "questions": [{"type": "choice", "id": "q", "text": "Sentiment?",
                                         "labels": [{"id": l, "text": l} for l in labels]}], "answers": {"q": {"label": labels[0]}}}


def test_reword_keeps_ids_and_answer():
    e = reword(ex(["positive", "negative"]), TABLE, random.Random(0))
    q = e["questions"][0]
    assert [l["id"] for l in q["labels"]] == ["positive", "negative"]
    assert e["answers"] == {"q": {"label": "positive"}}
    texts = [l["text"] for l in q["labels"]]
    assert texts in (["upbeat", "downbeat"], [TABLE["positive"]["description"], TABLE["negative"]["description"]])


def test_reword_skips_question_with_an_uncovered_option():
    e = reword(ex(["positive", "neutral"]), TABLE, random.Random(0))
    assert [l["text"] for l in e["questions"][0]["labels"]] == ["positive", "neutral"]


def test_vocab_groups_fixed_sets_and_skips_one_off_options():
    fixed = [ex(["yes", "no"]) for _ in range(10)] + [ex(["true", "false"]) for _ in range(10)]
    groups, _ = vocab(fixed, min_count=5)
    assert sorted(map(sorted, groups)) == [["false", "true"], ["no", "yes"]]
    one_off = [ex([f"a{i}", f"b{i}"]) for i in range(50)]
    assert vocab(one_off, min_count=5) is None
