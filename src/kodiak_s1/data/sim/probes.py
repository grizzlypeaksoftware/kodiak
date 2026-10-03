"""Skills-roadmap screening probes: ~50 checked examples per candidate decision kind, to measure where Kodiak-v0.2-1B is weak *before*
spending on training data (docs/SKILLS_ROADMAP.md). Never trained on.

Same recipe as E17: code picks the target answer, the open-weight writer builds the example toward it, and a blind checker must give the
same answer or the job is dropped. Each kind is a small spec (question, labels, the fields the writer fills, optional real passage).

    uv run python -m kodiak_s1.data.sim.probes --per-kind 60 --out data/probes/probes_v1.jsonl --max-usd 2
    uv run python -m kodiak_s1.data.sim.probes --build-eval data/probes/probes_v1.jsonl   # -> data/eval/kodiak-probes-v0.1.jsonl
Seed 21 = probes (never trained on).
"""

from __future__ import annotations

import argparse
import json
import random
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WRITER, CHECKER = "do:openai-gpt-oss-120b", "do:deepseek-3.2"
SOURCE_ID = "kodiak_probes"
STYLE = ("Write naturally, like real text from that setting, not like a test item. Never state or hint at the answer in a label-like way. "
         "Use single quotes inside text, never double quotes. Return JSON only.")

# kind -> spec. fields: what the writer writes (name -> description); slots: short values the question template uses.
KINDS = {
    "aspect_sentiment": {
        "why": "ACOS 0.02 on the Decision Index; opinions about one feature, not the whole product",
        "question": "How does the reviewer feel about the {aspect}?",
        "labels": {"positive": "positive", "negative": "negative", "mixed": "mixed: both good and bad",
                   "not_mentioned": "the review doesn't mention it"},
        "fields": {"review": "a product review of 3 to 6 sentences that discusses several features"},
        "slots": {"aspect": "the one feature the question asks about (2-4 words), e.g. 'battery life'"},
        "rule": "The reviewer's feeling about the asked feature must be exactly: {label}. Their overall opinion of the product should differ "
                "from that or be unclear, so the answer can't be guessed from the general tone.",
    },
    "stance": {
        "why": "VAST barely moved; for/against a named target",
        "question": "What is the author's stance on {target}?",
        "labels": {"favor": "in favor", "against": "against", "neutral": "neutral or no clear stance"},
        "fields": {"text": "a social-media post or short opinion piece of 2 to 5 sentences"},
        "slots": {"target": "the specific policy, idea or proposal the question asks about"},
        "rule": "The author's stance on the target must be: {label}. Mention the target indirectly at least once.",
    },
    "sarcasm": {
        "why": "iSarcasmEval 0.00",
        "question": "Is the writer being sarcastic?",
        "labels": {"yes": "yes", "no": "no"},
        "fields": {"text": "a short message or post (1 to 3 sentences) about an everyday situation"},
        "slots": {},
        "rule": "The answer must be: {label}. If not sarcastic, it may still be emotional or use exaggeration sincerely.",
    },
    "long_hallucination": {
        "why": "RAGTruth 0.00: hallucination anywhere in a long answer",
        "question": "Is everything in the answer supported by the source?",
        "labels": {"supported": "yes: fully supported by the source", "unsupported": "no: something in it isn't supported or is wrong"},
        "passage": True,
        "fields": {"user_question": "a question a reader might ask about the passage",
                   "answer": "a helpful answer of 6 to 9 sentences"},
        "slots": {},
        "rule": "If {label} starts with 'yes': every claim must come from the passage. Otherwise exactly one sentence in the middle of the "
                "answer must add a specific plausible detail the passage doesn't give, or change a fact; the rest must be faithful.",
    },
    "tool_unavailable": {
        "why": "When2Call 0.10-0.17, API-Bank 0.01: knowing when no tool fits",
        "question": "Can any of the available tools do what the user asks?",
        "labels": {"yes": "yes", "no": "no"},
        "fields": {"available_tools": "a list of 3 to 5 tools, each 'name: one-line description'",
                   "user_message": "one user request"},
        "slots": {},
        "rule": "The answer must be: {label}. If no, the request must sound related to the tools' domain but need something none of them "
                "does.",
    },
    "policy_violation": {
        "why": "guardrails: does a message break a written rule",
        "question": "Which rule of the policy does the message break?",
        "labels": {"rule_1": "rule 1", "rule_2": "rule 2", "rule_3": "rule 3", "rule_4": "rule 4", "none": "it doesn't break any rule"},
        "fields": {"policy": "a numbered list of exactly 4 short rules for a community, company chat or marketplace (1. ... 4.)",
                   "message": "one message posted there"},
        "slots": {},
        "rule": "The correct answer must be: {label}. If a rule is broken, break it clearly but without quoting its wording; the message must "
                "not break any other rule.",
    },
    "pii": {
        "why": "guardrails: personal or sensitive data",
        "question": "What kind of sensitive information does the text contain?",
        "labels": {"none": "none", "contact": "contact details (phone, email, home address)", "financial": "financial (card or bank numbers)",
                   "health": "health or medical details", "gov_id": "a government ID number (passport, SSN, license)"},
        "fields": {"text": "a support message, form note or chat message of 2 to 4 sentences"},
        "slots": {},
        "rule": "It must contain exactly this kind of sensitive information and no other kind: {label}. If 'none', it may mention topics "
                "like money or doctors without any actual sensitive detail.",
    },
    "duplicate": {
        "why": "triage: are two tickets the same issue",
        "question": "Are these two tickets about the same problem?",
        "labels": {"same": "yes, the same problem", "related": "related, but a different problem", "unrelated": "unrelated"},
        "fields": {"ticket_a": "a support ticket of 2 to 3 sentences", "ticket_b": "a second support ticket of 2 to 3 sentences"},
        "slots": {},
        "rule": "The relationship must be: {label}. Use different wording in the two tickets in every case.",
    },
    "task_done": {
        "why": "agent checks: is the user's task complete",
        "question": "Is the user's request fully completed?",
        "labels": {"complete": "yes, fully completed", "partial": "partly done", "failed": "no, it failed"},
        "fields": {"conversation": "a short exchange: 'User: ...' then 1 to 3 assistant steps with tool results, ending with the "
                                   "assistant's last message"},
        "slots": {},
        "rule": "The outcome must be: {label}. The assistant's last message should sound positive in every case.",
    },
    "tool_result": {
        "why": "agent checks: did a tool call actually succeed",
        "question": "Did the tool call succeed?",
        "labels": {"success": "yes", "error": "no, it returned an error", "wrong": "it ran, but returned the wrong thing"},
        "fields": {"tool_call": "a tool call with its arguments, e.g. get_weather(city='Lyon')", "tool_result": "the raw JSON or text result"},
        "slots": {},
        "rule": "The outcome must be: {label}. If 'wrong', the result must be valid-looking data that doesn't match the call's arguments.",
    },
    "pairwise_judge": {
        "why": "cheap LLM judge: which of two answers is better",
        "question": "Which answer is better?",
        "labels": {"first": "the first answer", "second": "the second answer", "tie": "they are about equally good"},
        "fields": {"question": "a user's question", "answer_1": "the first answer (2 to 5 sentences)", "answer_2": "the second answer (2 to 5 sentences)"},
        "slots": {},
        "rule": "The correct verdict must be: {label}. When one is better, make it more correct or complete, not longer; the worse one should "
                "still sound confident.",
    },
    "escalation": {
        "why": "triage: does this need a human now",
        "question": "Does this message need to go to a person, and why?",
        "labels": {"no": "no, routine", "legal": "yes: a legal threat", "safety": "yes: a safety risk",
                   "churn": "yes: the customer is about to leave"},
        "fields": {"message": "a customer message of 2 to 4 sentences"},
        "slots": {},
        "rule": "The correct answer must be: {label}. Routine messages may still sound annoyed.",
    },
}


def _rng(kind: str, seed: int, job: int) -> random.Random:
    return random.Random(f"probes:{kind}:{seed}:{job}")


def make_case(kind: str, seed: int, job: int) -> dict | None:
    spec = KINDS[kind]
    rng = _rng(kind, seed, job)
    target = list(spec["labels"])[job % len(spec["labels"])]  # balanced across labels
    pas = None
    if spec.get("passage"):
        from kodiak_s1.data.gen2.passages import passage

        pas = passage(seed * 10 + 7, job, rng.choice(["easy", "medium"]))
        if pas is None:
            return None
    fields = {**spec["fields"], **spec["slots"]}
    desc = "\n".join(f"- {k}: {v}" for k, v in fields.items())
    prompt = (("Here is a source passage:\n\n" + pas["text"] + "\n\n") if pas else "") + \
        "Write one realistic example for a decision task. Fields:\n" + desc + "\n\nThe question about it will be: " + spec["question"] + \
        "\nThe answer options will be: " + "; ".join(spec["labels"].values()) + ".\n\n" + spec["rule"].format(label=spec["labels"][target]) + \
        " " + STYLE
    schema = {"type": "object", "properties": {k: {"type": "string"} for k in fields}, "required": list(fields)}
    return {"kind": kind, "target": target, "prompt": prompt, "schema": schema, "passage": pas}


def build(kind: str, c: dict, raw: dict) -> tuple[dict, list[dict], dict] | None:
    spec = KINDS[kind]
    vals = {k: (raw.get(k) or "").strip() for k in {**spec["fields"], **spec["slots"]}}
    if not all(vals.values()):
        return None
    state = {k: vals[k] for k in spec["fields"]}
    if c.get("passage"):
        state = {"source": c["passage"]["text"], **state}
    text = spec["question"].format(**{k: vals[k] for k in spec["slots"]})
    q = {"type": "choice", "id": "decision", "text": text, "labels": [{"id": k, "text": v} for k, v in spec["labels"].items()]}
    return state, [q], {"decision": {"label": c["target"]}}


def run_job(kind: str, job: int, seed: int) -> dict:
    from kodiak_s1.data import synth
    from kodiak_s1.data.gen2.prompts import verify_prompt
    from kodiak_s1.schema import Example, render_state

    rec = {"job": job, "kind": kind, "seed": seed, "writer": WRITER, "verifier": CHECKER, "status": "error"}
    try:
        c = make_case(kind, seed, job)
        if c is None:
            rec["status"] = "no_passage"
            return rec
        rec["target"] = c["target"]
        g = synth.teacher(c["prompt"], c["schema"], 0.9, WRITER, 2000)
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"))
        built = build(kind, c, g["content"])
        if built is None:
            rec["status"] = "bad_output"
            return rec
        state, qs, ans = built
        v = synth.teacher(verify_prompt(render_state(state), qs), synth.verify_schema(qs), 0.0, CHECKER, 650)
        rec.update(verify_tokens=v["tokens"], verify_prompt_tokens=v.get("prompt_tokens"))
        got = synth.parse_verdict(qs[0], v["content"].get("decision"))
        if (got or {}).get("label") != c["target"]:
            rec.update(status="checker_disagrees", checker=got)
            return rec
        ex = {"state": state, "questions": qs, "answers": ans,
              "meta": {"source": SOURCE_ID, "split": "test", "license": "ODC-By-1.0 AND Apache-2.0" if c.get("passage") else "Apache-2.0",
                       "teacher": f"{WRITER} (checked by {CHECKER})", "tags": ["eval:probe", f"probe:{kind}", f"target:{c['target']}"]}}
        Example.model_validate(ex)
        rec.update(status="ok", example=ex)
    except OSError as e:
        rec.update(status="retry", error=str(e)[:300])
    except (ValueError, KeyError, TypeError) as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    return rec


def main(argv: list[str] | None = None) -> None:
    from kodiak_s1.data.gen2.__main__ import load_prices
    from kodiak_s1.data.gen2.pipeline import cost

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-kind", type=int, default=60)
    ap.add_argument("--seed", type=int, default=21)
    ap.add_argument("--kinds", default=",".join(KINDS))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default="data/probes/probes_v1.jsonl")
    ap.add_argument("--max-usd", type=float, default=2.0)
    ap.add_argument("--build-eval", default="", help="turn a probes file into data/eval/kodiak-probes-v0.1.jsonl (up to 50 per kind)")
    a = ap.parse_args(argv)
    if a.build_eval:
        last = {}
        for line in open(a.build_eval, encoding="utf-8"):
            r = json.loads(line)
            last[(r["kind"], r["job"])] = r
        out, n = Path("data/eval/kodiak-probes-v0.1.jsonl"), Counter()
        with out.open("w", encoding="utf-8") as f:
            for (kind, job), r in sorted(last.items()):
                if r["status"] == "ok" and n[kind] < 50:
                    f.write(json.dumps(r["example"], ensure_ascii=False) + "\n")
                    n[kind] += 1
        print(dict(n), "->", out)
        return
    out, prices = Path(a.out), load_prices()
    out.parent.mkdir(parents=True, exist_ok=True)
    done, spent = set(), 0.0
    if out.exists():
        for line in out.open():
            r = json.loads(line)
            spent += cost(r, prices)
            if r["status"] != "retry":
                done.add((r["kind"], r["job"]))
    todo = [(k, j) for k in a.kinds.split(",") for j in range(a.per_kind) if (k, j) not in done]
    lock, stats, state = threading.Lock(), Counter(), {"spent": spent}

    def work(kj):
        with lock:
            if state["spent"] >= a.max_usd:
                return
        rec = run_job(kj[0], kj[1], a.seed)
        with lock:
            state["spent"] += cost(rec, prices)
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats[f"{rec['kind']}:{rec['status']}"] += 1

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, todo))
    print(f"done: {dict(sorted(stats.items()))}, ${state['spent']:.2f} spent in total", flush=True)


if __name__ == "__main__":
    main()
