import json
import random

import pytest

from kodiak_s1.data import synth
from kodiak_s1.data.gen2 import __main__ as cli
from kodiak_s1.data.gen2 import pipeline, taxonomy
from kodiak_s1.data.gen2.dedupe import NearDupIndex, jaccard
from kodiak_s1.data.gen2.passages import clean_enough, paragraphs, window
from kodiak_s1.data.gen2.prompts import verify_prompt, writer_prompt, writer_schema
from kodiak_s1.data.gen2.specs import DECISIONS, GROUNDED_DECISIONS, NULL_KINDS, SYNTHETIC_DECISIONS, coverage_from_records, sample_spec
from kodiak_s1.schema import Example

TAX = taxonomy.normalize({
    "commerce": [{"name": "online returns", "doc_types": [{"name": "return request", "formats": ["text", "json", "bogus"]},
                                                          {"name": "refund chat", "formats": ["list"]}]},
                 {"name": "Online Returns", "doc_types": [{"name": "dup", "formats": ["text"]}, {"name": "x", "formats": ["text"]}]},
                 {"name": "tiny", "doc_types": [{"name": "only one", "formats": ["text"]}]}],
    "it ops": [{"name": "backups", "doc_types": [{"name": "backup job log", "formats": ["list", "json"]},
                                                 {"name": "restore ticket", "formats": ["text"]}]}],
})


def test_taxonomy_normalize_drops_duplicates_bad_formats_and_thin_domains():
    names = [d["name"] for s in TAX["sectors"] for d in s["domains"]]
    assert names == ["online returns", "backups"]  # case-insensitive duplicate and 1-doc-type domain dropped
    assert TAX["sectors"][0]["domains"][0]["doc_types"][0]["formats"] == ["text", "json"]
    assert len(taxonomy.cells(TAX)) == 4


def test_spec_sampling_is_deterministic_and_consistent():
    specs = [sample_spec(i, 8, TAX) for i in range(400)]
    assert [s.to_dict() for s in specs] == [sample_spec(i, 8, TAX).to_dict() for i in range(400)]
    assert specs[0].to_dict() != sample_spec(0, 9, TAX).to_dict()  # the seed matters
    for s in specs:
        assert s.decision in (GROUNDED_DECISIONS if s.source == "grounded" else SYNTHETIC_DECISIONS) and all(k in NULL_KINDS for k in s.null_kinds)
        assert s.n_choice >= 1 and 3 <= s.n_choice + s.n_score <= 6
        assert s.n_inference >= 1 and s.n_inference + s.n_null <= s.n_choice + s.n_score
        assert len(s.null_kinds) == s.n_null and len(s.scales) == len(s.ranges) == s.n_score
        if s.source == "grounded":
            assert s.format == "text" and s.domain is None
        else:
            assert (s.sector, s.domain, s.doc_type) in {c[:3] for c in taxonomy.cells(TAX)}
    grounded = sum(s.source == "grounded" for s in specs) / len(specs)
    assert 0.3 < grounded < 0.6


def test_coverage_mode_prefers_thin_values():
    cov = {"decision": {d: (1000 if d != "comparison" else 0) for d in DECISIONS}}
    cov_specs = [sample_spec(i, 8, TAX, cov) for i in range(2000)]
    covered = [s for s in cov_specs if s.mode == "coverage"]
    share = sum(s.decision == "comparison" for s in covered) / len(covered)
    assert share > 0.5  # uniform would be 1/7


def test_passage_window_and_filters():
    text = "\n".join(f"Paragraph {i} talks about soil, water and the crops that farmers plant in spring each year here."
                     for i in range(40))
    w = window(text, random.Random(0), 100, 200)
    assert w is not None and 100 <= len(w.split()) <= 200
    assert all(p in paragraphs(text) for p in w.split("\n\n"))  # whole paragraphs only
    assert not clean_enough(["Home", "About", "Contact", "Login | Register"])
    assert window("too short", random.Random(0), 100, 200) is None


def test_minhash_finds_near_duplicates_only():
    base = " ".join(f"word{i}" for i in range(300))
    near = base.replace("word150", "changed")
    other = " ".join(f"other{i}" for i in range(300))
    assert jaccard(base, near) > 0.9
    idx = NearDupIndex(0.8)
    assert idx.check_add("a", base) is None
    dup = idx.check_add("b", near)
    assert dup is not None and dup[0] == "a"
    assert idx.check_add("c", other) is None and len(idx) == 2


def test_prompts_mention_spec_and_verifier_accepts_inference():
    spec = next(s for s in (sample_spec(i, 8, TAX) for i in range(100)) if s.source == "synthetic" and s.n_null)
    p = writer_prompt(spec)
    assert spec.doc_type in p and "inferred" in p and NULL_KINDS[spec.null_kinds[0]] in p
    sch = writer_schema(spec, grounded=False)
    assert "state" in sch["properties"] and sch["properties"]["choice_questions"]["minItems"] == spec.n_choice
    assert "state" not in writer_schema(spec, grounded=True)["properties"]
    assert "inferred" in verify_prompt("s", [{"type": "choice", "id": "q", "text": "t", "labels": [{"id": "a", "text": "A"}]}])


def _fake_teacher(spec_by_prompt):
    """Writer returns a fixed state and questions; checker agrees on all but one."""
    def teacher(prompt, schema, temperature, model, max_tokens):
        if "choice_questions" in schema["properties"]:
            props = schema["properties"]
            n_c, n_s = props["choice_questions"]["minItems"], props["score_questions"]["minItems"]
            state = "Order 4412 was delivered on May 3. The customer writes: I was charged twice, please fix this now!"
            cq = [{"id": f"c{j}", "text": f"What is the customer asking for? ({j})", "basis": "inferred",
                   "labels": [{"id": "refund", "text": "a refund of the duplicate charge"}, {"id": "track", "text": "tracking"}],
                   "evidence": "I was charged twice", "answer_label": "refund"} for j in range(n_c)]
            sq = [{"id": f"s{j}", "text": "How urgent is it?", "min": 0, "max": 10, "min_label": "not urgent",
                   "max_label": "drop everything", "basis": "inferred", "evidence": "please fix this now", "answer_value": 7}
                  for j in range(n_s)]
            content = {"choice_questions": cq, "score_questions": sq}
            if "state" in props:
                content["state"] = {"text": state, "list": [state, "Thanks."], "json": {"note": state}}[
                    "json" if props["state"].get("type") == "object" else "list" if props["state"].get("type") == "array" else "text"]
            return {"content": content, "tokens": 1000, "prompt_tokens": 800}
        ans = {qid: {"quote": "", "answer": ("refund" if qid.startswith("c") else "7")} for qid in schema["properties"]}
        ans["c0"] = {"quote": "", "answer": "track"}  # one disagreement
        return {"content": ans, "tokens": 100, "prompt_tokens": 500}
    return teacher


def test_pipeline_with_mocked_teacher(monkeypatch):
    monkeypatch.setattr(synth, "teacher", _fake_teacher({}))
    monkeypatch.setattr(pipeline.passages, "passage", lambda seed, job, diff: {
        "text": "Order 4412 was delivered on May 3. The customer writes: I was charged twice, please fix this now!",
        "id": "fw1", "url": "http://x", "words": 18})
    recs = [pipeline.run_job(i, 8, TAX) for i in range(12)]
    ok = [r for r in recs if r["status"] == "ok"]
    assert ok, [r.get("error") or r["status"] for r in recs]
    for r in ok:
        Example.model_validate(r["example"])
        assert "c0" not in r["example"]["questions"] and r["disagreements"][0]["id"] == "c0"
        assert r["disagreements"][0]["basis"] == "inferred"
        assert "gen2" in r["example"]["meta"]["tags"] and "inference" in r["example"]["meta"]["tags"]
        assert set(r["basis"].values()) == {"inferred"}
        grounded = r["spec"]["source"] == "grounded"
        assert ("ODC-By" in r["example"]["meta"]["license"]) == grounded
        assert pipeline.cost(r, pipeline.DEFAULT_PRICES) > 0


def test_cli_run_budget_cap_resume_dedupe_and_queue(monkeypatch, tmp_path):
    monkeypatch.setattr(synth, "teacher", _fake_teacher({}))
    monkeypatch.setattr(pipeline.passages, "passage", lambda seed, job, diff: {
        "text": "Order 4412 was delivered on May 3. The customer writes: I was charged twice, please fix this now!",
        "id": "fw1", "url": "http://x", "words": 18})
    tax_path = tmp_path / "tax.json"
    tax_path.write_text(json.dumps(TAX))
    monkeypatch.setattr(cli, "COVERAGE_PATH", tmp_path / "coverage.json")
    out = tmp_path / "pilot_gen2_test.jsonl"
    base = ["run", "--taxonomy", str(tax_path), "--out", str(out), "--workers", "1", "--against", "none"]
    # Each mocked job costs ~$0.0013, so a $0.004 cap stops after a few jobs, cleanly and with a message.
    with pytest.raises(SystemExit, match="budget cap"):
        cli.main(base + ["--n", "20", "--max-usd", "0.004"])
    first = [json.loads(line) for line in out.open()]
    assert 2 <= len(first) <= 4
    cli.main(base + ["--n", "20", "--max-usd", "100"])  # resume: only the missing jobs run
    recs = [json.loads(line) for line in out.open()]
    assert sorted(r["job"] for r in recs) == list(range(20))
    # The mocked writer repeats itself, so everything after the first kept example per state shape is a near-duplicate.
    assert sum(r["status"] == "near_duplicate" for r in recs) >= 10
    q = pipeline.review_queue([out], n=5)
    assert len(q) == 5 and all(set(r["example"]["answers"]) == {"c0"} for r in q)
    assert coverage_from_records([out])["source"]


def test_stats_summarizes_yield_and_basis(monkeypatch):
    monkeypatch.setattr(synth, "teacher", _fake_teacher({}))
    monkeypatch.setattr(pipeline.passages, "passage", lambda seed, job, diff: {
        "text": "Order 4412 was delivered on May 3. The customer writes: I was charged twice, please fix this now!",
        "id": "fw1", "url": "http://x", "words": 18})
    s = cli.stats([pipeline.run_job(i, 8, TAX) for i in range(10)], pipeline.DEFAULT_PRICES)
    assert s["jobs"] == 10 and s["inferred_share"] == 1.0 and s["disagree_rate_by_basis"]["inferred"] > 0
    assert s["usd_per_1k_jobs"] > 0


def test_unknown_options_are_detected():
    from kodiak_s1.data.gen2.pipeline import has_unknown_option

    def q(*texts):
        return {"labels": [{"id": t.lower().replace(" ", "_"), "text": t} for t in texts]}

    for bad in (q("Yes", "No", "Not known"), q("2028", "Result is not yet known"), q("A", "Other"), q("a", "Unknown"),
                q("x", "None of the above"), q("x", "Cannot be determined"), q("x", "N/A")):
        assert has_unknown_option(bad), bad
    for good in (q("Yes", "No"), q("Known issue", "New issue"), q("Otherwise fine", "Broken"), q("Unknown caller ID", "Known")):
        pass
    assert not has_unknown_option(q("Yes", "No", "Partially"))
    assert not has_unknown_option(q("Energy Team", "Other team's backlog is full"))


def test_critics_drop_flagged_questions_and_count_cost(monkeypatch):
    base = _fake_teacher({})

    def teacher(prompt, schema, temperature, model, max_tokens):
        if prompt.startswith("You are auditing"):
            v = {qid: {"reason": "fine", "verdict": "correct"} for qid in schema["properties"]}
            if model == "critic-b" and "c1" in v:
                v["c1"] = {"reason": "two options fit", "verdict": "ambiguous"}
            return {"content": v, "tokens": 50, "prompt_tokens": 400}
        return base(prompt, schema, temperature, model, max_tokens)

    monkeypatch.setattr(synth, "teacher", teacher)
    monkeypatch.setattr(pipeline.passages, "passage", lambda seed, job, diff: {
        "text": "Order 4412 was delivered on May 3. The customer writes: I was charged twice, please fix this now!",
        "id": "fw1", "url": "http://x", "words": 18})
    prices = {**pipeline.DEFAULT_PRICES, "critic-a": (1.0, 1.0), "critic-b": (1.0, 1.0)}
    for i in range(12):
        plain = pipeline.run_job(i, 8, TAX)
        r = pipeline.run_job(i, 8, TAX, critics=["critic-a", "critic-b"])
        if r["status"] == "ok":
            assert "c1" not in {q["id"] for q in r["example"]["questions"]}
            had_c1 = "c1" in {q["id"] for q in plain["example"]["questions"]}
            assert [f["model"] for f in r["critic_flags"]] == (["critic-b"] if had_c1 else [])
            assert pipeline.cost(r, prices) > pipeline.cost(plain, prices)
