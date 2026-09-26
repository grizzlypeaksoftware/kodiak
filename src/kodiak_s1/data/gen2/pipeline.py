"""One Generator v2 job: spec -> (real passage) -> writer -> mechanical checks -> blind checker -> agreement.

Reuses v1's proven parts (synth.teacher, build_questions, verify_schema, parse_verdict, agree). Records have the same
shape as v1 records (status, example, token counts), so training, the dashboard and tools/review.html read them as-is;
v2 adds "spec", "basis" (per kept question), "passage" (grounded jobs) and basis on each disagreement.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from pydantic import ValidationError

from kodiak_s1.data import synth
from kodiak_s1.data.gen2 import passages
from kodiak_s1.data.gen2.critic import critique
from kodiak_s1.data.gen2.prompts import verify_prompt, writer_prompt, writer_schema
from kodiak_s1.data.gen2.specs import SCORE_FOCUS_SCALES, sample_spec
from kodiak_s1.data.sources import rng_for
from kodiak_s1.schema import Example, render_state

WRITER = "do:openai-gpt-oss-120b"
CHECKER = "do:deepseek-3.2"
SOURCE_ID = "kodiak_gen2"
# USD per 1M tokens (input, output); docs/progress.json overrides. DeepSeek V3.2 from DO's pricing page, 2026-09-25.
DEFAULT_PRICES = {"do:openai-gpt-oss-120b": (0.10, 0.70), "do:deepseek-3.2": (0.50, 1.60)}


def cost(rec: dict, prices: dict) -> float:
    """USD spent on one job record (0 for local models)."""
    total = 0.0
    for model, i, o in ((rec.get("writer"), "gen_prompt_tokens", "gen_tokens"),
                        (rec.get("verifier"), "verify_prompt_tokens", "verify_tokens")):
        if model in prices:
            p_in, p_out = prices[model]
            total += (rec.get(i) or 0) / 1e6 * p_in + (rec.get(o) or 0) / 1e6 * p_out
    for u in rec.get("critic_usage", []) + rec.get("extra_usage", []):
        if u["model"] in prices:
            p_in, p_out = prices[u["model"]]
            total += u["prompt_tokens"] / 1e6 * p_in + u["tokens"] / 1e6 * p_out
    return total


# Options that mean "I don't know" duplicate the null answer: the checker picks them for unanswerable questions, and a
# model trained on them learns two conflicting ways to abstain (pilot 2026-09-25: most null disagreements).
UNKNOWN_OPTION = re.compile(r"\b(unknown|not (?:yet )?(?:known|stated|mentioned|specified|provided|given|determined|"
                            r"available|clear|enough)|cannot be (?:determined|known)|can't (?:tell|say)|unclear|"
                            r"none of (?:the|these)|n/?a|insufficient)\b|^other$", re.IGNORECASE)


def has_unknown_option(q: dict) -> bool:
    return any(UNKNOWN_OPTION.search(str(lab.get(k, "")).replace("_", " ").strip())
               for lab in q.get("labels") or [] for k in ("id", "text"))


def anchor_scores(raw_qs: list[dict], spec) -> None:
    """Stage 3: write the scale's anchors into each score question's text, so the writer, the blind checker and Kodiak all
    judge against the same scale (pilot 2026-09-26: without them the checker disagreed on 69% of scores)."""
    for q in raw_qs:
        scale = q.get("scale")
        if q["type"] != "score" or scale not in SCORE_FOCUS_SCALES or "min" not in q or "max" not in q:
            continue
        lo, hi = float(q["min"]), float(q["max"])
        a_lo, a_mid, a_hi = SCORE_FOCUS_SCALES[scale]
        q["text"] = f"{q['text'].rstrip()} ({lo:g} = {a_lo}; {(lo + hi) / 2:g} = {a_mid}; {hi:g} = {a_hi})"
        q["min_label"], q["max_label"] = a_lo, a_hi


def best_fragment(evidence: str, state_text: str) -> str:
    """Judgment scores often cite several fragments joined by '...' or ';'. Keep the evidence if any fragment is a real quote."""
    if synth.evidence_supported(evidence, state_text):
        return evidence
    frags = [f.strip(" \"'") for f in re.split(r"\.\.\.|…|;|\|", evidence) if len(f.strip()) >= 8]
    ok = [f for f in frags if synth.evidence_supported(f, state_text)]
    return max(ok, key=len) if ok else evidence


def _state(raw: dict, fmt: str):
    state = raw["state"]
    if fmt == "json" and (not isinstance(state, dict) or not state):
        raise ValueError("json state is not a non-empty object")
    if fmt == "list":
        state = [x for x in state if isinstance(x, str) and x.strip()]
        if len(state) < 2:
            raise ValueError("list state has fewer than 2 non-empty items")
    if fmt == "text" and (not isinstance(state, str) or len(state.split()) < 15):
        raise ValueError("text state is empty or too short")
    return state


def run_job(i: int, seed: int, tax: dict, coverage: dict | None = None,
            writer: str = WRITER, verifier: str = CHECKER, critics: list[str] | tuple = (), focus: str | None = None) -> dict:
    """critics: models that audit the agreed answers; a question any critic calls wrong or ambiguous is dropped.
    Human review (2026-09-25) found writer+checker agreement still let through ~7% bad labels, mostly ambiguous questions."""
    spec = sample_spec(i, seed, tax, coverage, focus)
    grounded = spec.source == "grounded"
    rec: dict = {"job": i, "seed": seed, "gen": "v2.0c", "spec": spec.to_dict(), "writer": writer, "verifier": verifier,
                 "status": "error"}
    t0 = time.time()
    try:
        passage = None
        if grounded:
            p = passages.passage(seed, i, spec.difficulty)
            if p is None:
                rec["status"] = "no_passage"
                return rec
            passage = p["text"]
            rec["passage"] = {"id": p["id"], "url": p["url"], "words": p["words"]}
        g = synth.teacher(writer_prompt(spec, passage), writer_schema(spec, grounded), 0.9, writer, 3000)
        raw = g["content"]
        state = passage if grounded else _state(raw, spec.format)
        state_text = render_state(state)
        raw_qs = [{**q, "type": "choice"} for q in raw["choice_questions"]] + \
            [{**q, "type": "score"} for q in raw["score_questions"]]
        if spec.targets:
            anchor_scores(raw_qs, spec)
            for q in raw_qs:
                if q["type"] == "score" and q.get("evidence"):
                    q["evidence"] = best_fragment(q["evidence"], state_text)
        pre_drops = ["unknown_option"] * sum(q["type"] == "choice" and has_unknown_option(q) for q in raw_qs)
        raw_qs = [q for q in raw_qs if not (q["type"] == "choice" and has_unknown_option(q))]
        basis = {}
        for q in raw_qs:
            q["unanswerable"] = q.get("basis") == "unanswerable"
            basis.setdefault(synth._slug(q.get("id", "")), q.get("basis"))
        qs, answers, drops = synth.build_questions(raw_qs, state_text,
                                                   quote_free=frozenset({"score"}) if spec.targets else frozenset())
        drops = pre_drops + drops
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"), drops=drops,
                   writer_basis=[q.get("basis") for q in raw_qs], q_basis={q["id"]: basis.get(q["id"]) for q in qs},
                   debug={"state": state, "questions": qs, "answers": answers})
        if len(qs) < 2:
            rec["status"] = "too_few_questions"
            return rec
        v = synth.teacher(verify_prompt(state_text, qs), synth.verify_schema(qs), 0.0, verifier, 400 + 250 * len(qs))
        by_id = {q["id"]: synth.parse_verdict(q, v["content"].get(q["id"])) for q in qs}
        rec.update(verify_tokens=v["tokens"], verify_prompt_tokens=v.get("prompt_tokens"))
        rec["debug"]["verify"] = v["content"]
        second = {}
        if spec.targets:
            # Stage 3: the writer aimed each rating at a target band, so its own rating is biased toward the target (pilot #4:
            # "frustration 9" for a calm email because the target was high). Scores are graded by two BLIND raters instead:
            # the checker plus a fresh writer-model call that never saw the target; the kept value is their mean.
            v2 = synth.teacher(verify_prompt(state_text, qs), synth.verify_schema(qs), 0.0, writer, 400 + 250 * len(qs))
            rec.setdefault("extra_usage", []).append({"model": writer, "tokens": v2["tokens"], "prompt_tokens": v2.get("prompt_tokens", 0)})
            second = {q["id"]: synth.parse_verdict(q, v2["content"].get(q["id"])) for q in qs}
            rec["debug"]["verify2"] = v2["content"]
        kept_q, kept_a, disagreements = [], {}, []
        for q in qs:
            gold = answers[q["id"]]
            if spec.targets and q["type"] == "score":
                b = second.get(q["id"])
                gold = None if b is None else ({"null": True} if b.get("unanswerable") else {"value": b["value"]} if "value" in b else None)
                if gold is None:
                    disagreements.append({"id": q["id"], "basis": basis.get(q["id"]), "gen": answers[q["id"]], "ver": by_id.get(q["id"]),
                                          "blind2": b})
                    continue
            ok, target = synth.agree(q, gold, by_id.get(q["id"]), step_tolerance=bool(spec.targets))
            if ok:
                kept_q.append(q)
                kept_a[q["id"]] = target
            else:
                disagreements.append({"id": q["id"], "basis": basis.get(q["id"]), "gen": answers[q["id"]],
                                      "ver": by_id.get(q["id"])})
        rec["disagreements"] = disagreements
        if critics and len(kept_q) >= 2:
            rec["critic_usage"], rec["critic_flags"] = [], []
            flagged = set()
            for model in critics:
                verdicts, usage = critique(state_text, kept_q, kept_a, model)
                rec["critic_usage"].append({"model": model, "tokens": usage["tokens"], "prompt_tokens": usage["prompt_tokens"]})
                for qid, v in verdicts.items():
                    if v != "correct":
                        flagged.add(qid)
                        rec["critic_flags"].append({"id": qid, "model": model, "verdict": v,
                                                    "reason": str((usage["raw"].get(qid) or {}).get("reason", ""))[:300]})
            kept_q = [q for q in kept_q if q["id"] not in flagged]
            kept_a = {k: v for k, v in kept_a.items() if k not in flagged}
        if len(kept_q) < 2:
            rec["status"] = "too_few_agreed"
            return rec
        rec["basis"] = {q["id"]: basis.get(q["id"]) for q in kept_q}
        kept_bases = set(rec["basis"].values())
        tags = ["synthetic", "gen2", f"fmt:{spec.format}", f"src:{spec.source}", f"decision:{spec.decision}",
                f"diff:{spec.difficulty}", "multiq"]
        tags += ["inference"] * ("inferred" in kept_bases)
        if any("null" in a for a in kept_a.values()):
            tags += ["null:synthetic"] + [f"nullkind:{k}" for k in dict.fromkeys(spec.null_kinds)]
        if any(q["type"] == "score" for q in kept_q):
            chosen = [q.get("scale") for q in raw_qs if q["type"] == "score" and q.get("scale")]
            tags += [f"scale:{s}" for s in dict.fromkeys(spec.scales or chosen)]
        notes = f"fineweb-edu {rec['passage']['id']}" if grounded else f"{spec.sector} / {spec.domain} / {spec.doc_type}"
        ex = {"state": state, "questions": kept_q, "answers": kept_a,
              "meta": {"source": SOURCE_ID, "license": "ODC-By-1.0 AND Apache-2.0" if grounded else "Apache-2.0",
                       "split": "train", "teacher": f"{writer} (verified by {verifier})", "tags": tags, "notes": notes}}
        Example.model_validate(ex)
        rec.update(status="ok", example=ex)
        if spec.pair and isinstance(raw.get("variant"), dict):
            _variant(rec, raw["variant"], spec, state_text, kept_q, kept_a, verifier, critics, ex["meta"], f"gen2:{seed}:{i}", writer)
    except (ValidationError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    except OSError as e:  # network / timeout: leave the job undone so a rerun retries it
        rec["status"] = "retry"
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    finally:
        rec["seconds"] = round(time.time() - t0, 1)
    return rec


PAIR_MIN_DELTA = 0.3  # the twin must move at least one score by 30% of its range, per the checker's reading


def _variant(rec: dict, var: dict, spec, state_text: str, kept_q: list[dict], kept_a: dict, verifier: str,
             critics, meta: dict, pair_id: str, writer: str = WRITER) -> None:
    """Stage 3 contrast twin: the same state with a minimal edit that should move the first score to the other end.

    Kept only if the blind checker agrees with the writer on the twin *and* the agreed score moved by >= PAIR_MIN_DELTA of the
    range (otherwise the "minimal pair" teaches nothing). Critics audit it like any example. Both twins share a pair id,
    so training puts them in the same split.
    """
    rec["variant_status"] = "dropped"
    try:
        vstate = _state({"state": var.get("state")}, spec.format)
        vtext = render_state(vstate)
        if vtext.strip() == state_text.strip():
            rec["variant_status"] = "identical"
            return
        sq = [q for q in kept_q if q["type"] == "score" and "value" in kept_a[q["id"]]]
        by_id = {synth._slug(a.get("id", "")): a for a in var.get("score_answers") or []}
        vqs, vans = [], {}
        for q in sq:
            a = by_id.get(q["id"])
            if a is None:
                continue
            v = float(a["answer_value"])
            if q["min"] <= v <= q["max"]:
                vqs.append(q)
                vans[q["id"]] = {"value": v}
        if not vqs:
            rec["variant_status"] = "no_supported_answers"
            return
        # Two blind raters for the twin too (see run_job); the writer's own twin ratings are not used as labels.
        ratings = []
        for model in (verifier, writer):
            v = synth.teacher(verify_prompt(vtext, vqs), synth.verify_schema(vqs), 0.0, model, 400 + 250 * len(vqs))
            rec.setdefault("extra_usage", []).append({"model": model, "tokens": v["tokens"], "prompt_tokens": v.get("prompt_tokens", 0)})
            ratings.append({q["id"]: synth.parse_verdict(q, v["content"].get(q["id"])) for q in vqs})
        agreed_q, agreed_a = [], {}
        for q in vqs:
            b = ratings[1].get(q["id"])
            if not b or "value" not in b:
                continue
            ok, target = synth.agree(q, {"value": b["value"]}, ratings[0].get(q["id"]), step_tolerance=True)
            if ok:
                agreed_q.append(q)
                agreed_a[q["id"]] = target
        moved = [abs(agreed_a[q["id"]]["value"] - kept_a[q["id"]]["value"]) / (q["max"] - q["min"]) for q in agreed_q]
        if not moved or max(moved) < PAIR_MIN_DELTA:
            rec["variant_status"] = "not_contrasting" if agreed_q else "checker_disagreed"
            return
        if critics:
            flagged = set()
            for model in critics:
                verdicts, usage = critique(vtext, agreed_q, agreed_a, model)
                rec["extra_usage"].append({"model": model, "tokens": usage["tokens"], "prompt_tokens": usage["prompt_tokens"]})
                flagged |= {qid for qid, verdict in verdicts.items() if verdict != "correct"}
            agreed_q = [q for q in agreed_q if q["id"] not in flagged]
            agreed_a = {k: x for k, x in agreed_a.items() if k not in flagged}
            if not agreed_q:
                rec["variant_status"] = "critic_flagged"
                return
        tags = sorted(set(meta["tags"]) | {"pair:score_flip"})
        vex = {"state": vstate, "questions": agreed_q, "answers": agreed_a,
               "meta": {**meta, "tags": tags, "notes": (meta.get("notes") or "") + " [contrast twin]"}}
        Example.model_validate(vex)
        rec["example"]["meta"]["tags"] = tags
        rec.update(variant_example=vex, pair_id=pair_id, variant_status="ok", variant_delta=round(max(moved), 3))
    except (ValidationError, ValueError, KeyError, TypeError) as e:
        rec["variant_status"] = f"error: {type(e).__name__}"


def review_queue(paths: list[str | Path], n: int = 50, seed: int = 0) -> list[dict]:
    """Writer/checker disagreements for a human, in tools/review.html's format.

    Jobs are sampled with weight = the disagreement rate of their (decision type, basis) cell, so review time goes where
    the pipeline is least sure. The reviewer judges the *writer's* answer; the checker's answer is kept alongside.
    """
    recs = []
    for p in paths:
        recs += [json.loads(line) for line in Path(p).open(encoding="utf-8")]
    recs = [r for r in recs if "spec" in r and r.get("debug", {}).get("questions") and "disagreements" in r]
    asked: dict[tuple, int] = {}
    disputed: dict[tuple, int] = {}
    for r in recs:  # rates over every checked question, not just disputed jobs
        ids = {d["id"] for d in r["disagreements"]}
        for q in r["debug"]["questions"]:
            cell = (r["spec"]["decision"], r.get("q_basis", {}).get(q["id"]))
            asked[cell] = asked.get(cell, 0) + 1
            disputed[cell] = disputed.get(cell, 0) + (q["id"] in ids)
    rate = {c: disputed[c] / asked[c] for c in asked}
    recs = [r for r in recs if r["disagreements"]]
    rng = rng_for("gen2-review", seed)
    keyed = []
    for r in recs:
        w = max(rate.get((r["spec"]["decision"], d["basis"]), 0.0) for d in r["disagreements"]) + 1e-3
        keyed.append((rng.random() ** (1.0 / w), r))  # weighted sampling without replacement (Efraimidis-Spirakis)
    keyed.sort(key=lambda t: -t[0])
    out = []
    for _, r in keyed[:n]:
        ids = {d["id"] for d in r["disagreements"]}
        qs = [q for q in r["debug"]["questions"] if q["id"] in ids]
        out.append({"job": r["job"], "seed": r["seed"], "status": "ok", "review_reason": "writer/checker disagreement",
                    "spec": r["spec"], "checker": {d["id"]: d["ver"] for d in r["disagreements"]},
                    "basis": {d["id"]: d["basis"] for d in r["disagreements"]},
                    "example": {"state": r["debug"]["state"], "questions": qs,
                                "answers": {q["id"]: r["debug"]["answers"][q["id"]] for q in qs}}})
    return out
