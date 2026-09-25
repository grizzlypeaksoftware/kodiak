import math
import random

import numpy as np

from kodiak_s1.eval.metrics import NULL, aurc, ece, macro_f1, summarize
from kodiak_s1.eval.run import fit_calibration, kodiak_records, llm_records
from kodiak_s1.infer import decide
from kodiak_s1.schema import Options, Response


def test_ece_zero_when_calibrated_and_large_when_overconfident():
    rng = np.random.default_rng(0)
    conf = rng.uniform(0.2, 1.0, 20000)
    correct = (rng.uniform(size=conf.size) < conf).astype(float)
    assert ece(conf, correct) < 0.02
    assert ece(np.full(1000, 0.99), np.r_[np.ones(500), np.zeros(500)]) > 0.45


def test_aurc_prefers_confidence_that_ranks_errors_last():
    correct = np.array([1, 1, 1, 0, 0], dtype=float)
    good = aurc(np.array([0.9, 0.8, 0.7, 0.2, 0.1]), correct)
    bad = aurc(np.array([0.1, 0.2, 0.3, 0.8, 0.9]), correct)
    assert good < bad


def test_macro_f1():
    assert macro_f1(["a", "b", "a"], ["a", "b", "a"]) == 1.0
    assert 0 < macro_f1(["a", "b", "a"], ["a", "a", "a"]) < 1


def _raw_choice(z, z_null, labels=("x", "y", "z")):
    e = np.exp(np.array(z) - max(z))
    return {"type": "choice", "labels": list(labels), "z": list(z), "cond_probs": (e / e.sum()).tolist(),
            "z_null": z_null, "p_null": 1 / (1 + math.exp(-z_null)), "allow_null": True, "qid": "q"}


def test_decide_rules_and_schema():
    q = {"type": "choice", "id": "q", "text": "?", "labels": [{"id": i, "text": i} for i in "xyz"]}
    confident = decide(_raw_choice([5, 0, 0], -5), q, Options())
    assert confident["answer"] == "x" and confident["abstain_reason"] is None
    assert abs(sum(confident["probs"].values()) + confident["p_null"] - 1) < 1e-4
    unanswerable = decide(_raw_choice([5, 0, 0], 3), q, Options())
    assert unanswerable["answer"] is None and unanswerable["abstain_reason"] == "unanswerable"
    unsure = decide(_raw_choice([0.1, 0, 0], -5), q, Options(min_confidence=0.6))
    assert unsure["answer"] is None and unsure["abstain_reason"] == "low_confidence"
    sq = {"type": "score", "id": "s", "text": "?", "min": 1, "max": 5, "step": 1}
    s = decide({"type": "score", "mu": 0.62, "kappa": 30.0, "p_null": 0.1, "z_null": -2.2, "allow_null": True},
               sq, Options())
    assert s["answer"] == 3.0 and 1 <= s["interval"][0] < s["mean"] < s["interval"][1] <= 5
    Response.model_validate({"model": "t", "answers": {"q": confident, "s": s}})


def test_calibration_recovers_temperature():
    rng = random.Random(0)
    pairs = []
    for _ in range(3000):
        true_z = [rng.gauss(0, 1.5) for _ in range(3)]
        e = np.exp(true_z) / np.exp(true_z).sum()
        gold = rng.choices("xyz", weights=e)[0]
        raw = _raw_choice([3 * v for v in true_z], -4)  # the "model" is 3x overconfident
        pairs.append((raw, {"type": "choice"}, {"label": gold}))
    cal = fit_calibration(pairs)
    assert 2.5 < cal["t_choice"] < 3.5
    assert cal["t_choice_nll_after"] < cal["t_choice_nll_before"]


def test_records_and_summary_end_to_end():
    ex = {"state": "s", "meta": {"source": "t", "tags": ["eval:indomain"]},
          "questions": [{"type": "choice", "id": "q", "text": "?", "labels": [{"id": i, "text": i} for i in "xyz"]},
                        {"type": "score", "id": "s", "text": "?", "min": 0, "max": 10}],
          "answers": {"q": {"label": "x"}, "s": {"value": 6.0}}}
    raws = [[_raw_choice([4, 0, 0], -4),
             {"type": "score", "mu": 0.6, "kappa": 20.0, "p_null": 0.02, "z_null": -4, "allow_null": True, "qid": "s"}]]
    recs = kodiak_records([ex], raws, None)
    m = summarize(recs)
    assert m["accuracy"] == 1.0 and m["score_mae"] < 1e-9 and m["score_interval_coverage"] == 1.0
    assert m["abstain_recall"] != m["abstain_recall"]  # nan: no gold nulls


def test_llm_records_parse_and_abstain():
    ex = {"meta": {"source": "t", "tags": []},
          "questions": [{"type": "choice", "id": "q", "text": "?", "labels": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}]},
                        {"type": "score", "id": "s", "text": "?", "min": 0, "max": 10}],
          "answers": {"q": {"null": True}, "s": {"value": 5}}}
    out = {"q": {"quote": "", "answer": "UNANSWERABLE", "confidence": 0.8}, "s": {"quote": "x", "answer": "7", "confidence": 0.6}}
    q, s = llm_records(0, ex, out, 1000.0)
    assert q["decision"] is None and abs(q["p_null"] - 0.8) < 1e-9
    assert abs(s["unit_pred"] - 0.7) < 1e-9 and s["decision"] == 0.7
    assert summarize([q])["accuracy"] == 1.0
    garbage = llm_records(0, ex, {}, None)
    assert garbage[0]["decision"] is None  # a failed call counts as abstaining, never as a free answer


def test_interval_coverage_counts_gold_at_the_boundary():
    rec = {"source": "t", "tags": [], "type": "score", "allow_null": True, "gold": {"value": 0.0}, "p_null": 0.0,
           "probs": {}, "decision": 0.01, "mu": 0.01, "kappa": 50.0, "unit_pred": 0.01, "unit_gold": 0.0,
           "interval_unit": [0.0001, 0.06]}
    assert summarize([rec])["score_interval_coverage"] == 1.0


def test_score_mae_ignores_missing_values_but_reports_them():
    base = {"source": "t", "tags": [], "type": "score", "allow_null": True, "probs": {}, "p_null": 0.0}
    recs = [{**base, "gold": {"value": 1}, "unit_gold": 0.5, "unit_pred": 0.6, "decision": 0.6},
            {**base, "gold": {"value": 1}, "unit_gold": 0.5, "unit_pred": None, "decision": None}]
    m = summarize(recs)
    assert abs(m["score_mae"] - 0.1) < 1e-9 and m["score_answered"] == 0.5


def test_llm_score_parsing_is_lenient_and_schema_is_numeric():
    from kodiak_s1.eval.run import llm_schema

    q = {"type": "score", "id": "s", "text": "?", "min": 0, "max": 1}
    assert "anyOf" in llm_schema([q])["properties"]["s"]["properties"]["answer"]
    ex = {"meta": {"source": "t", "tags": []}, "questions": [q], "answers": {"s": {"value": 0.8}}}
    (r,) = llm_records(0, ex, {"s": {"answer": ">= 0.8", "confidence": "0.9"}}, 10.0)
    assert r["decision"] == 0.8 and abs(r["unit_pred"] - 0.8) < 1e-9


def test_null_threshold_moves_up_when_model_over_abstains():
    from kodiak_s1.eval.run import fit_null_threshold

    pairs = []
    for i in range(200):
        # answerable questions where the model wrongly puts p_null ~0.6 (over-abstaining), and true nulls at ~0.9
        answerable = i % 4 != 0
        z_null = math.log(0.6 / 0.4) if answerable else math.log(0.9 / 0.1)
        raw = _raw_choice([3, 0, 0], z_null)
        pairs.append((raw, {"type": "choice"}, {"label": "x"} if answerable else {"null": True}))
    cal = {"t_choice": 1.0, "t_null": 1.0, "kappa_scale": 1.0}
    out = fit_null_threshold(pairs, cal)
    assert 0.6 < out["null_threshold"] <= 0.9
    assert out["decision_acc_at_best"] > out["decision_acc_at_0.5"]
