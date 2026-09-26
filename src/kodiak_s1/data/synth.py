"""Synthetic examples from a local teacher LLM (Ollama), with independent verification.

Pipeline per job (deterministic seed -> domain, state format, question mix):
  1. GENERATE: the teacher writes a realistic state and 3-5 typed questions,
     including 1-2 that sound relevant but cannot be answered from the state,
     with an answer and a supporting quote for each.
  2. CHECK: every answerable question's evidence quote must appear in the state.
  3. VERIFY: a second call answers the same questions *without* seeing the first
     answers. Only questions where both agree are kept (self-consistency filter).

The teacher labels data; it is never part of the Kodiak model.

    uv run python -m kodiak_s1.data.synth --n 200 --workers 4 --out data/synthetic/pilot.jsonl

Resumable: finished job ids are read from the output file and skipped.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pydantic import ValidationError

from kodiak_s1.data.sources import rng_for
from kodiak_s1.schema import ChoiceQuestion, Example, render_state

OLLAMA = "http://localhost:11434/api/chat"
TEACHER = "qwen3.8:27b"

DOMAINS = [
    "customer support chat about a billing problem", "e-commerce order record", "bank transaction history",
    "IT helpdesk ticket", "web server error log lines", "CI/CD pipeline run result", "pull request description",
    "code review comment thread", "product review", "restaurant review", "local news article excerpt",
    "company press release", "work email thread", "meeting notes", "calendar event details", "travel itinerary",
    "clinic appointment reminder (no diagnosis)", "insurance claim submission", "real estate listing", "job posting",
    "candidate resume summary", "software license clause", "website terms of service excerpt", "social media post",
    "online forum thread", "board game or chess position description", "video game match state", "sports match report",
    "weather forecast", "IoT sensor readings", "smart home event log", "recipe", "fitness tracker daily summary",
    "teacher feedback on a student essay", "scientific paper abstract", "quarterly earnings summary",
    "stock price alert", "package shipping tracking history", "HR policy excerpt", "customer satisfaction survey response",
    "chatbot conversation that includes a tool call result", "API response from a third-party service",
    "web search results list", "security alert from a monitoring system", "suspicious email that may be phishing",
    "mobile app store review", "software bug report", "feature request", "podcast transcript snippet",
    "text message conversation between friends", "apartment maintenance request", "flight status notification",
    "grant application summary", "museum exhibit description", "car repair invoice", "school cafeteria menu",
    "volunteer sign-up form submission", "legal demand letter", "parking ticket appeal", "pet adoption application",
]
FORMATS = {
    "text": "a single plain-text document",
    "list": "a list of 2-6 separate texts (e.g. messages in order, or several short documents)",
    "json": "a JSON object with realistic nested fields, like a real system would emit",
}
SCORE_RANGES = [(0, 1), (1, 5), (0, 10), (0, 100)]


def _gen_schema(fmt: str, n_choice: int, n_score: int) -> dict:
    """Separate choice and score lists, so the grammar can require labels on every choice question.

    With a single mixed list, the teacher sometimes wrote choice questions with no options at all.
    """
    state = {"text": {"type": "string"},
             "list": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 6},
             "json": {"type": "object"}}[fmt]  # a real object: asking for an escaped JSON string broke often
    common = {"id": {"type": "string"}, "text": {"type": "string"}, "unanswerable": {"type": "boolean"},
              "evidence": {"type": "string"}}
    label = {"type": "object", "properties": {"id": {"type": "string"}, "text": {"type": "string"}}, "required": ["id", "text"]}
    choice = {"type": "object", "properties": {
        **common, "labels": {"type": "array", "items": label, "minItems": 2, "maxItems": 8}, "answer_label": {"type": "string"}},
        "required": ["id", "text", "labels", "unanswerable", "evidence", "answer_label"]}
    score = {"type": "object", "properties": {
        **common, "min": {"type": "number"}, "max": {"type": "number"}, "min_label": {"type": "string"},
        "max_label": {"type": "string"}, "answer_value": {"type": "number"}},
        "required": ["id", "text", "min", "max", "min_label", "max_label", "unanswerable", "evidence", "answer_value"]}
    return {"type": "object", "properties": {
        "state": state,
        "choice_questions": {"type": "array", "items": choice, "minItems": n_choice, "maxItems": n_choice},
        "score_questions": {"type": "array", "items": score, "minItems": n_score, "maxItems": n_score}},
        "required": ["state", "choice_questions", "score_questions"]}


UNANSWERABLE = "UNANSWERABLE"


def verify_schema(questions: list[dict]) -> dict:
    """Per-question fields, quote first: the model finds its evidence before committing to an answer.

    Putting a boolean "unanswerable" field first made the teacher (with thinking off) default to true.
    """
    props = {}
    for q in questions:
        if q["type"] == "choice":
            ans = {"type": "string", "enum": [lab["id"] for lab in q["labels"]] + [UNANSWERABLE]}
        else:
            ans = {"type": "string", "description": f"a number from {q['min']} to {q['max']}, or {UNANSWERABLE}"}
        props[q["id"]] = {"type": "object", "properties": {"quote": {"type": "string"}, "answer": ans},
                          "required": ["quote", "answer"]}
    return {"type": "object", "properties": props, "required": list(props)}


def parse_verdict(q: dict, v: dict | None) -> dict | None:
    """Verifier output -> {"unanswerable": bool, "label"/"value": ...} (the shape `agree` expects)."""
    if not isinstance(v, dict) or "answer" not in v:
        return None
    a = str(v["answer"]).strip()
    if a == UNANSWERABLE:
        return {"unanswerable": True}
    if q["type"] == "choice":
        return {"unanswerable": False, "label": a}
    try:
        return {"unanswerable": False, "value": float(a)}
    except ValueError:
        return None


def gen_prompt(domain: str, fmt: str, n_choice: int, n_score: int, n_null: int, rng) -> str:
    lo, hi = rng.choice(SCORE_RANGES)
    return f"""You are creating training data for a model that answers typed questions about a "state".

Write ONE realistic state: {FORMATS[fmt]} for this setting: {domain}.
Length: {rng.choice(["short (40-100 words)", "medium (100-250 words)", "long (250-450 words)"])}. Invent specific,
plausible details (names, numbers, dates). Do not mention that it is synthetic.
Do not use double quote characters inside the state text; use single quotes instead.

Then write {n_choice + n_score} questions about it:
- {n_choice} "choice" question(s): 2-8 labels each. Label ids are short snake_case; label texts are short phrases.
  Labels must be mutually exclusive, and exactly one should be correct when the question is answerable.
- {n_score} "score" question(s): a judgment on a numeric scale from min={lo} to max={hi}, with min_label and max_label
  describing what the ends mean.
- Exactly {n_null} of these questions must be UNANSWERABLE: it sounds relevant to this state and uses plausible labels,
  but the state does not contain the information needed (for example it asks about a detail that is never mentioned).
  Set unanswerable=true, leave evidence empty, and still fill answer_label/answer_value with any placeholder.
  Do not make it obviously off-topic.
- For answerable questions set unanswerable=false, give answer_label (a label id) or answer_value (a number in range),
  and copy a short exact quote from the state into evidence that supports the answer: character for character,
  not a paraphrase (for a JSON state, copy a fragment of the JSON exactly as written, e.g. "status": "shipped").
- Vary question phrasing. Questions must be answerable by reading, not by outside knowledge.
Return JSON only."""


def verify_prompt(state_text: str, questions: list[dict]) -> str:
    qs = []
    for q in questions:
        if q["type"] == "choice":
            opts = "; ".join(f'{lab["id"]} = {lab["text"]}' for lab in q["labels"])
            qs.append(f'- id={q["id"]} (choice): {q["text"]} Options: {opts}')
        else:
            qs.append(f'- id={q["id"]} (score {q["min"]} to {q["max"]}; {q["min"]} = {q.get("min_label", "")}, '
                      f'{q["max"]} = {q.get("max_label", "")}): {q["text"]}')
    return f"""Read the state and answer each question using ONLY information in the state.
For each question, first copy the exact part of the state that answers it into "quote" (empty if there is none),
then give "answer": the option id for choice questions, or a number for score questions.
If the state does not contain the information needed, answer {UNANSWERABLE}.

STATE:
{state_text}

QUESTIONS:
{chr(10).join(qs)}

Return JSON only."""


DO_INFERENCE = "https://inference.do-ai.run/v1/chat/completions"


def teacher(prompt: str, schema: dict, temperature: float, model: str, max_tokens: int) -> dict:
    """Route a teacher call: "do:<model>" -> DigitalOcean serverless inference, anything else -> local Ollama."""
    if model.startswith("do:"):
        return do_inference(prompt, schema, temperature, model[3:], max_tokens)
    return ollama(prompt, schema, temperature, model, max_tokens)


def do_inference(prompt: str, schema: dict, temperature: float, model: str, max_tokens: int, timeout: int = 600) -> dict:
    """DigitalOcean serverless inference (OpenAI-compatible). The key comes only from $DO_INFERENCE_KEY.

    Reasoning models (gpt-oss) spend completion tokens thinking before they answer, so the token budget is
    generous and reasoning effort is set low. Usage is returned for cost tracking.
    """
    key = os.environ.get("DO_INFERENCE_KEY")
    if not key:
        raise OSError("DO_INFERENCE_KEY is not set")
    body = {"model": model, "temperature": temperature, "max_completion_tokens": max_tokens + 3000,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "answer", "schema": schema}}}
    if "gpt-oss" in model:
        body["reasoning_effort"] = "low"  # only reasoning models accept this

    def post(b: dict) -> dict:
        req = urllib.request.Request(DO_INFERENCE, json.dumps(b).encode(),
                                     {"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        return json.load(urllib.request.urlopen(req, timeout=timeout))

    for attempt in range(4):
        try:
            d = post(body)
            break
        except urllib.error.HTTPError as e:
            if e.code == 400 and body["response_format"]["type"] == "json_schema":
                # Model doesn't support JSON-schema output: fall back to JSON mode, with the schema in the prompt.
                # Our own validation (build_questions / parse_verdict) still rejects anything malformed.
                body["response_format"] = {"type": "json_object"}
                body["messages"] = [{"role": "user", "content": prompt + "\n\nReturn a JSON object matching this JSON Schema:\n"
                                     + json.dumps(schema)}]
                continue
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:  # rate limits and server errors
                time.sleep(5 * 2 ** attempt)
                continue
            raise OSError(f"DO inference HTTP {e.code}: {e.read()[:200]!r}") from e
    else:
        raise OSError("DO inference: retries exhausted")
    text = d["choices"][0]["message"].get("content")
    if not text:  # thinking models can spend the whole token budget reasoning and return no answer
        raise ValueError(f"empty response from {model} (finish_reason={d['choices'][0].get('finish_reason')})")
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)  # tolerate code fences
    usage = d.get("usage", {})
    return {"content": json.loads(text), "tokens": usage.get("completion_tokens", 0),
            "prompt_tokens": usage.get("prompt_tokens", 0)}


def ollama(prompt: str, schema: dict, temperature: float, model: str, max_tokens: int, timeout: int = 900) -> dict:
    body = {"model": model, "stream": False, "think": False, "format": schema,
            "messages": [{"role": "user", "content": prompt}],
            # num_predict caps runaway generations (constrained JSON can loop on whitespace).
            "options": {"temperature": temperature, "num_ctx": 8192, "num_predict": max_tokens}}
    req = urllib.request.Request(OLLAMA, json.dumps(body).encode(), {"Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=timeout))
    return {"content": json.loads(d["message"]["content"]), "tokens": d.get("eval_count", 0)}


def _norm(s: str) -> str:
    """Normalize for evidence matching. JSON punctuation becomes spaces, because the teacher quotes
    '"status": "done"' while the rendered state is compact ('"status":"done"')."""
    s = re.sub(r'[{}\[\]":,]', " ", s)
    return re.sub(r"\s+", " ", s).strip().casefold()


def evidence_supported(evidence: str, state_text: str, min_overlap: float = 0.8) -> bool:
    """Is the teacher's evidence really in the state? An exact (normalized) match passes. Otherwise at least 80% of
    the evidence's content words must appear in the state: this tolerates rewording like 'Commenter: Jane Doe' for
    '"author":"Jane Doe"' but still rejects invented evidence. The blind verifier remains the main correctness check."""
    ev, st = _norm(evidence), _norm(state_text)
    if len(ev) < 3:
        return False
    if ev in st:
        return True
    words = [w for w in re.findall(r"[a-z0-9][a-z0-9.@%$/-]*", ev) if len(w) > 2 or w.isdigit()]
    if len(words) < 2:
        return False
    state_words = set(re.findall(r"[a-z0-9][a-z0-9.@%$/-]*", st))
    return sum(w in state_words for w in words) / len(words) >= min_overlap


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:\-]+", "_", s).strip("_")[:64] or "q"


def build_questions(raw: list[dict], state_text: str, quote_free: frozenset[str] = frozenset()) -> tuple[list[dict], dict, list[str]]:
    """quote_free: question types exempt from the exact-quote evidence check (Stage 3 judgment scores rest on the whole
    document, so the writer summarizes rather than quotes; the blind checker and critics are the safeguard there)."""
    """Turn generator output into schema questions + answers; drop malformed or unsupported ones."""
    qs, answers, drops, seen = [], {}, [], set()
    for r in raw:
        qid = _slug(r.get("id", ""))
        if qid in seen:
            drops.append("dup_id")
            continue
        seen.add(qid)
        null = bool(r.get("unanswerable"))
        if r["type"] == "choice":
            labels = [{"id": str(lab["id"]).strip(), "text": str(lab["text"]).strip()} for lab in r.get("labels") or []]
            if len(labels) < 2:
                drops.append("choice_too_few_labels")
                continue
            q = {"type": "choice", "id": qid, "text": r["text"].strip(), "labels": labels}
            try:
                ChoiceQuestion.model_validate(q)
            except ValidationError:
                drops.append("invalid_labels")  # e.g. duplicate or over-long option texts
                continue
            ans = {"null": True} if null else {"label": str(r.get("answer_label", "")).strip()}
            if not null and ans["label"] not in {lab["id"] for lab in labels}:
                drops.append("answer_not_in_labels")
                continue
        else:
            if "min" not in r or "max" not in r:
                drops.append("score_no_range")
                continue
            q = {"type": "score", "id": qid, "text": r["text"].strip(), "min": float(r["min"]), "max": float(r["max"])}
            for k in ("min_label", "max_label"):
                if r.get(k):
                    q[k] = str(r[k]).strip()[:200]
            if not null and "answer_value" not in r:
                drops.append("score_no_value")
                continue
            ans = {"null": True} if null else {"value": float(r["answer_value"])}
        if not null and r["type"] not in quote_free and not evidence_supported(r.get("evidence") or "", state_text):
            drops.append("evidence_not_in_state")
            continue
        qs.append(q)
        answers[qid] = ans
    return qs, answers, drops


def agree(q: dict, gold: dict, v: dict | None, step_tolerance: bool = False) -> tuple[bool, dict]:
    """Does the verifier agree with the generator? Returns (agree, final target).

    step_tolerance (Stage 3): on short integer scales (range <= 10) allow one full step, since 15% of a 1-5 scale is less than
    one step and any one-point difference would otherwise count as disagreement. The target is the mean either way."""
    if v is None:
        return False, gold
    if "null" in gold or v.get("unanswerable"):
        return ("null" in gold and bool(v.get("unanswerable"))), gold
    if q["type"] == "choice":
        return str(v.get("label", "")).strip() == gold["label"], gold
    if "value" not in v:
        return False, gold
    tol = 0.15 * (q["max"] - q["min"])
    if step_tolerance and (q["max"] - q["min"]) <= 10:
        tol = max(tol, 1.0)
    ok = abs(float(v["value"]) - gold["value"]) <= tol
    mean = min(max((float(v["value"]) + gold["value"]) / 2, q["min"]), q["max"])
    return ok, {"value": mean}


def run_job(i: int, seed: int, model: str, verifier: str) -> dict:
    rng = rng_for("synth", seed, i)
    domain, fmt = rng.choice(DOMAINS), rng.choice(list(FORMATS))
    n_null = rng.choice([1, 1, 2])
    n_score = rng.choice([0, 1, 1])
    n_choice = rng.randint(max(1, 3 - n_score), 4 - n_score)
    rec: dict = {"job": i, "seed": seed, "domain": domain, "format": fmt, "status": "error"}
    t0 = time.time()
    try:
        g = teacher(gen_prompt(domain, fmt, n_choice, n_score, n_null, rng), _gen_schema(fmt, n_choice, n_score), 0.9, model, 2500)
        raw = g["content"]
        state = raw["state"]
        if fmt == "json" and (not isinstance(state, dict) or not state):
            raise ValueError("json state is not a non-empty object")
        if fmt == "list":
            state = [x for x in state if isinstance(x, str) and x.strip()]  # gpt-oss sometimes emits blank items
            if len(state) < 2:
                raise ValueError("list state has fewer than 2 non-empty items")
        state_text = render_state(state)
        raw_qs = [{**q, "type": "choice"} for q in raw["choice_questions"]] + \
            [{**q, "type": "score"} for q in raw["score_questions"]]
        qs, answers, drops = build_questions(raw_qs, state_text)
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"), drops=drops, debug={"state": state, "questions": qs, "answers": answers})
        if len(qs) < 2:
            rec["status"] = "too_few_questions"
            return rec
        v = teacher(verify_prompt(state_text, qs), verify_schema(qs), 0.0, verifier, 400 + 250 * len(qs))
        by_id = {q["id"]: parse_verdict(q, v["content"].get(q["id"])) for q in qs}
        rec["verify_tokens"] = v["tokens"]
        rec["verify_prompt_tokens"] = v.get("prompt_tokens")
        rec["debug"]["verify"] = v["content"]
        kept_q, kept_a, disagreements = [], {}, []
        for q in qs:
            ok, target = agree(q, answers[q["id"]], by_id.get(q["id"]))
            if ok:
                kept_q.append(q)
                kept_a[q["id"]] = target
            else:
                disagreements.append({"id": q["id"], "gen": answers[q["id"]], "ver": by_id.get(q["id"])})
        rec["disagreements"] = disagreements
        if len(kept_q) < 2:
            rec["status"] = "too_few_agreed"
            return rec
        tags = ["synthetic", f"fmt:{fmt}"] + (["multiq"] if len(kept_q) > 1 else [])
        tags += ["null:synthetic"] * any("null" in a for a in kept_a.values())
        ex = {"state": state, "questions": kept_q, "answers": kept_a,
              "meta": {"source": "kodiak_synth_v1", "license": "Apache-2.0", "split": "train",
                       "teacher": model if model == verifier else f"{model} (verified by {verifier})", "tags": tags,
                       "notes": domain}}
        Example.model_validate(ex)
        rec.update(status="ok", example=ex)
    except (ValidationError, ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    except OSError as e:  # network / timeout: leave the job undone so a rerun retries it
        rec["status"] = "retry"
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    finally:
        rec["seconds"] = round(time.time() - t0, 1)
    return rec


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=100, help="number of jobs (job ids 0..n-1)")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--model", default=TEACHER)
    ap.add_argument("--verifier", default=TEACHER)
    ap.add_argument("--out", default="data/synthetic/synth_v1.jsonl")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.open():
            r = json.loads(line)
            if r.get("status") != "retry":
                done.add(r["job"])
    todo = [i for i in range(a.start, a.start + a.n) if i not in done]
    print(f"{len(done)} jobs already done; {len(todo)} to run with {a.workers} workers", flush=True)
    lock, stats, t0 = threading.Lock(), {}, time.time()

    def work(i: int) -> None:
        rec = run_job(i, a.seed, a.model, a.verifier)
        with lock:
            with out.open("a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats[rec["status"]] = stats.get(rec["status"], 0) + 1
            n = sum(stats.values())
            if n % 10 == 0 or n == len(todo):
                rate = n / (time.time() - t0) * 3600
                print(f"[{time.strftime('%H:%M:%S')}] {n}/{len(todo)} {stats} ~{rate:.0f} jobs/h", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, todo))
    if stats.get("retry"):
        sys.exit(f"{stats['retry']} jobs need retry; rerun the same command")


if __name__ == "__main__":
    main()
