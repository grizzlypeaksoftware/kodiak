"""E17: four in-purpose skills from the Decision Index report card (docs/experiments/E17-in-purpose-skills.md).

Each job's answer is fixed by construction: code chooses the target (e.g. "the response adds one unsupported detail", "the user leaves out a
required parameter"), the writer model builds text toward it, and a blind checker must reach the same answer on the checked questions, or the
job is dropped. Kinds (job % 4): grounding (real passage + response), tools (API specs + user message), claims (real passage + claim),
relevance (shopping query + product).

    uv run python -m kodiak_s1.data.sim.skills --n 40 --seed 8 --out data/synthetic/pilot_skills.jsonl --max-usd 1
Seeds: 6 = training, 7 = the held-out skills eval (never trained on), 8 = pilots.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WRITER, CHECKER = "do:openai-gpt-oss-120b", "do:deepseek-3.2"
SOURCE_ID = "kodiak_skills"
KINDS = ["grounding", "tools", "claims", "relevance"]


def _rng(kind: str, seed: int, job: int) -> random.Random:
    return random.Random(f"skills:{kind}:{seed}:{job}")


def _pick(rng: random.Random, weights: dict) -> str:
    return rng.choices(list(weights), list(weights.values()))[0]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def _norm(s: str) -> str:
    return re.sub(r"\W+", " ", s).strip().lower()


# ---- S1 grounding ------------------------------------------------------------------------------------------------------------------

GROUND = {"supported": "yes: fully supported by the source",
          "unsupported": "no: adds details the source never mentions (nothing in the source conflicts with them)",
          "contradicts": "no: says something the source states differently (conflicts with the source)"}
GROUND_RULES = {
    "supported": "Every claim in the response must be directly supported by the passage: no outside facts, no numbers or names that are not in "
                 "the passage. Leave offending_sentence empty.",
    "unsupported": "Exactly one sentence of the response must add a specific, plausible detail that the passage does NOT mention (a date, number, "
                   "name, cause or outcome) without contradicting the passage; every other claim must be supported. Copy that sentence exactly "
                   "into offending_sentence.",
    "contradicts": "Exactly one sentence of the response must state something the passage contradicts (a changed number, a reversed relation, a "
                   "wrong person or place); every other claim must be supported. Copy that sentence exactly into offending_sentence.",
}


def grounding_case(seed, job, rng):
    from kodiak_s1.data.gen2.passages import passage

    p = passage(seed * 10 + 1, job, rng.choice(["easy", "medium", "hard"]))
    if p is None:
        return None
    target = _pick(rng, {"supported": 0.4, "unsupported": 0.3, "contradicts": 0.3})
    prompt = (f"Here is a source passage:\n\n{p['text']}\n\nWrite a natural question a user might ask about this passage, and a response of "
              f"2 to 4 sentences that answers it. {GROUND_RULES[target]} Write the response like a helpful assistant, not like a test item. "
              "Use single quotes inside text, never double quotes. Return JSON only.")
    schema = {"type": "object", "properties": {"question": {"type": "string"}, "response": {"type": "string"},
                                               "offending_sentence": {"type": "string"}}, "required": ["question", "response", "offending_sentence"]}
    return {"kind": "grounding", "target": target, "passage": p, "prompt": prompt, "schema": schema}


def grounding_build(c, raw):
    resp, sents = raw["response"].strip(), _sentences(raw["response"])
    if not 2 <= len(sents) <= 8:
        return None
    state = {"source": c["passage"]["text"], "user_question": raw["question"].strip(), "response": resp}
    qs = [{"type": "choice", "id": "grounded", "text": "Is every claim in the response supported by the source?",
           "labels": [{"id": k, "text": v} for k, v in GROUND.items()]}]
    ans = {"grounded": {"label": c["target"]}}
    if c["target"] != "supported" and all(len(x) <= 190 for x in sents):  # option texts are capped at 200 characters
        off = _norm(raw.get("offending_sentence", ""))
        idx = [i for i, s in enumerate(sents) if off and (_norm(s) == off or off in _norm(s) or _norm(s) in off)]
        if len(idx) != 1:
            return None
        qs.append({"type": "choice", "id": "which", "text": "Which sentence of the response is the problem?",
                   "labels": [{"id": f"s{i + 1}", "text": s} for i, s in enumerate(sents)]})
        ans["which"] = {"label": f"s{idx[0] + 1}"}
    return state, qs, ans, [q["id"] for q in qs]


# ---- S2 tool selection --------------------------------------------------------------------------------------------------------------

TOOL_DOMAINS = ["travel booking", "customer relationship management", "smart home control", "calendar and email", "online store administration",
                "weather and maps", "personal banking", "project management", "HR and payroll", "IT helpdesk", "restaurant reservations",
                "fitness tracking", "music streaming", "real estate listings", "shipping and logistics", "healthcare appointments"]
ASK, DIRECT = "ask the user for missing information", "answer directly without calling a tool"
TOOL_RULES = {
    "call": "The user message must clearly need the tool you name in target_tool and must state the value of every required parameter of that "
            "tool. In param, name one required parameter of that tool; in value, give its value exactly as written in the message; in "
            "distractor_values, give 3 plausible but wrong values of the same type (not mentioned in the message). Leave missing_param empty.",
    "ask": "The user message must clearly need the tool you name in target_tool but must NOT give the value of one of its required parameters; "
           "name that parameter in missing_param. Leave param and value empty and distractor_values an empty list.",
    "direct": "The user message must be something an assistant answers without any tool: {style}. It must fit the setting and must not "
              "need live data, an account or any action. Don't start with 'Thanks' or use 'by the way' unless the style asks for it. Leave "
              "target_tool, param, value and missing_param empty and distractor_values an empty list.",
}
DIRECT_STYLES = ["a general how-does-it-work question the assistant can answer from general knowledge",
                 "a request for advice or a rule of thumb, with no specific data needed", "a request to explain a term or concept",
                 "a question about what the assistant can do", "brief thanks or small talk after finishing a task",
                 "a hypothetical question ('what usually happens if ...')", "a request to reword or summarize something the user wrote in the message"]


def tools_case(seed, job, rng):
    target = _pick(rng, {"call": 0.55, "ask": 0.25, "direct": 0.2})
    n, domain = rng.randint(3, 7), rng.choice(TOOL_DOMAINS)
    prompt = (f"Design {n} realistic API tools for a {domain} assistant. Each tool: a snake_case name, a one-sentence description, parameters "
              "(each with a type and a description) and the list of required parameters. Names must be distinct, and at least two tools must "
              f"sound related so that choosing between them needs care. Then write one user message. "
              f"{TOOL_RULES[target].format(style=rng.choice(DIRECT_STYLES))} "
              "Return JSON only.")
    tool = {"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"},
                                             "parameters": {"type": "object"}, "required": {"type": "array", "items": {"type": "string"}}},
            "required": ["name", "description", "parameters", "required"]}
    schema = {"type": "object", "properties": {"tools": {"type": "array", "items": tool, "minItems": n, "maxItems": n},
                                               "user_message": {"type": "string"}, "target_tool": {"type": "string"},
                                               "param": {"type": "string"}, "value": {"type": "string"},
                                               "distractor_values": {"type": "array", "items": {"type": "string"}},
                                               "missing_param": {"type": "string"}},
              "required": ["tools", "user_message", "target_tool", "param", "value", "distractor_values", "missing_param"]}
    return {"kind": "tools", "target": target, "domain": domain, "prompt": prompt, "schema": schema}


def tool_spec(t: dict) -> dict:
    """The standard function-calling shape: required lives inside parameters, once (the writer returns it at both levels)."""
    params = dict(t.get("parameters") or {})
    params.setdefault("type", "object")
    params["required"] = params.get("required") or t.get("required") or []
    return {"name": t["name"], "description": t.get("description", ""), "parameters": params}


def tools_build(c, raw):
    tools, msg = raw["tools"], raw["user_message"].strip()
    names = [t["name"] for t in tools]
    if len(set(names)) != len(names) or not msg:
        return None
    by = {t["name"]: t for t in tools}
    t = c["target"]
    rng = random.Random(msg)
    labels = [{"id": f"call:{n}", "text": f"call {n}"} for n in names] + [{"id": "ask", "text": ASK}, {"id": "direct", "text": DIRECT}]
    qs = [{"type": "choice", "id": "next", "text": "What should the assistant do next?", "labels": labels}]
    if t == "direct":
        ans = {"next": {"label": "direct"}}
    else:
        tt = raw["target_tool"]
        if tt not in by:
            return None
        req = by[tt].get("required") or []
        if t == "call":
            p, v, ds = raw["param"], raw["value"].strip(), [d.strip() for d in raw["distractor_values"] if d.strip()]
            if p not in req or not v or v.lower() not in msg.lower() or len(set(ds) - {v}) < 2:
                return None
            opts = [v] + [d for d in dict.fromkeys(ds) if d != v and d.lower() not in msg.lower()][:3]
            if len(opts) < 3:
                return None
            rng.shuffle(opts)
            qs.append({"type": "choice", "id": "value", "text": f"Which value should be passed as '{p}' to {tt}?",
                       "labels": [{"id": f"v{i}", "text": o} for i, o in enumerate(opts)]})
            ans = {"next": {"label": f"call:{tt}"}, "value": {"label": f"v{opts.index(v)}"}}
        else:
            if raw["missing_param"] not in req:
                return None
            ans = {"next": {"label": "ask"}}
        qs.append({"type": "choice", "id": "missing", "text": "Is a required parameter for this request missing from the user's message?",
                   "labels": [{"id": "yes", "text": "yes"}, {"id": "no", "text": "no"}]})
        ans["missing"] = {"label": "yes" if t == "ask" else "no"}
    state = {"available_tools": [tool_spec(x) for x in tools], "conversation": [f"User: {msg}"]}
    return state, qs, ans, [q["id"] for q in qs if q["id"] != "missing"]


# ---- S3 claim verification ----------------------------------------------------------------------------------------------------------

CLAIM = {"supported": "supported by the text", "refuted": "refuted by the text", "nei": "not enough information in the text"}
SWAPS = ["a changed number or quantity", "a swapped person, place or organization", "an added or removed negation",
         "a changed date or time order", "a reversed cause and effect or comparison"]


def claims_case(seed, job, rng):
    from kodiak_s1.data.gen2.passages import passage

    p = passage(seed * 10 + 3, job, rng.choice(["easy", "medium", "hard"]))
    if p is None:
        return None
    target = _pick(rng, {"supported": 0.35, "refuted": 0.35, "nei": 0.3})
    swap = rng.choice(SWAPS)
    rule = {"supported": "The claim must follow from the passage, ideally combining two facts from different sentences, paraphrased rather than "
                         "copied.",
            "refuted": f"The claim must be clearly false according to the passage because of {swap}: take a fact from the passage and change it. "
                       "Keep the wording close to the passage so it is tempting.",
            "nei": "The claim must be on the same topic and sound plausible, but the passage must neither support nor contradict it."}[target]
    prompt = (f"Here is a passage:\n\n{p['text']}\n\nWrite ONE claim, a single sentence. {rule} Use single quotes inside text, never double "
              "quotes. Return JSON only.")
    schema = {"type": "object", "properties": {"claim": {"type": "string"}}, "required": ["claim"]}
    return {"kind": "claims", "target": target, "swap": swap if target == "refuted" else None, "passage": p, "prompt": prompt, "schema": schema}


def claims_build(c, raw):
    claim = raw["claim"].strip()
    if not claim or len(claim) > 400:
        return None
    state = {"text": c["passage"]["text"], "claim": claim}
    qs = [{"type": "choice", "id": "verdict", "text": "Does the text support the claim?", "labels": [{"id": k, "text": v} for k, v in CLAIM.items()]}]
    return state, qs, {"verdict": {"label": c["target"]}}, ["verdict"]


# ---- S4 relevance -------------------------------------------------------------------------------------------------------------------

ESCI = {"exact": "exact match: it is what the shopper searched for",
        "substitute": "substitute: not quite what was asked, but could be used instead",
        "complement": "complement: a different product, but an accessory or add-on for what was searched",
        "irrelevant": "irrelevant: unrelated to the search, and not used with it either"}
CATEGORIES = ["kitchen appliances", "running shoes", "laptops and accessories", "camping gear", "baby products", "office furniture",
              "phone cases and chargers", "skincare", "power tools", "board games", "pet supplies", "bicycle parts", "coffee and tea",
              "home lighting", "women's clothing", "men's clothing", "audio equipment", "gardening tools", "car accessories", "books"]


FIELD_LEAK = re.compile(r"^\W*(search_?query|query|product_?title|title|bullet_?points?|bullets|price)\W*:", re.I)


LEAK_WORDS = re.compile(r"you searched|search(ed)? for|shopper|search query|combined price|^\W*price\b", re.I)


def _words(t: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if len(w) > 2}


def relevance_case(seed, job, rng):
    target = _pick(rng, {"exact": 0.3, "substitute": 0.25, "complement": 0.2, "irrelevant": 0.25})
    cat = rng.choice(CATEGORIES)
    hint = {"exact": "meets every specification in the query (brand, size, color, feature) that the query states",
            "substitute": "is the same kind of product but misses one stated specification (e.g. another size, color, brand or capacity), so it "
                          "could still be used instead",
            "complement": "is a different product that people use together with what the query asks for (an accessory, refill or add-on)",
            "irrelevant": "shares a word or topic with the query but is not usable for it at all (hard negative)"}[target]
    prompt = (f"First decide two things: searched_item (what the shopper wants, in a few words) and listed_product (the product in the "
              f"listing, in a few words; it {hint}). Then write a realistic online shopping search query for {cat} for the searched_item, "
              f"specific enough to have 1 to 3 stated requirements, and a product listing for the listed_product only. The listing has a product title, 3 to 5 bullets that are real product facts about the product in the title (materials, size, capacity, features, what's included) and a price such as '$24.99'. The bullets describe the listed product, never the searched item. Don't label or explain the relationship anywhere, and don't put field names in the text. "
              "Use single quotes inside text, never double quotes. Return JSON only.")
    schema = {"type": "object", "properties": {"searched_item": {"type": "string"}, "listed_product": {"type": "string"},
                                               "query": {"type": "string"}, "title": {"type": "string"},
                                               "bullets": {"type": "array", "items": {"type": "string"}}, "price": {"type": "string"}},
              "required": ["searched_item", "listed_product", "query", "title", "bullets", "price"]}
    return {"kind": "relevance", "target": target, "category": cat, "prompt": prompt, "schema": schema}


def relevance_build(c, raw):
    bullets = [b.strip() for b in raw["bullets"] if len(b.split()) >= 3]
    if not raw["query"].strip() or not raw["title"].strip() or len(bullets) < 3 or not re.search(r"\d", raw["price"]):
        return None  # pilot: some listings came back as placeholders ("bulb", "nothing special")
    if any(FIELD_LEAK.match(b) or LEAK_WORDS.search(b) for b in bullets):
        return None  # e.g. 'search_query: ...', 'product_title: ...' copied into a bullet
    q = _words(raw["query"])
    if c["target"] in ("complement", "irrelevant") and q and len(q & _words(" ".join(bullets))) / len(q) >= 0.6:
        return None  # bullets describe the searched item, not the listed product (title and details disagree)
    if len(_words(raw["title"]) & _words(" ".join(bullets))) < 2:
        return None  # details don't describe the titled product (e.g. a 'cable clip' listing with office-chair details)
    raw = {**raw, "bullets": bullets}
    state = {"query": raw["query"].strip(), "product": {"title": raw["title"].strip(), "details": raw["bullets"], "price": raw["price"]}}
    qs = [{"type": "choice", "id": "relevance", "text": "How relevant is this product to the shopper's search?",
           "labels": [{"id": k, "text": v} for k, v in ESCI.items()]}]
    return state, qs, {"relevance": {"label": c["target"]}}, ["relevance"]


CASES = {"grounding": (grounding_case, grounding_build), "tools": (tools_case, tools_build),
         "claims": (claims_case, claims_build), "relevance": (relevance_case, relevance_build)}


def run_job(job: int, seed: int, writer: str, checker: str, kinds: list[str]) -> dict:
    from kodiak_s1.data import synth
    from kodiak_s1.data.gen2.prompts import verify_prompt
    from kodiak_s1.schema import Example, render_state

    kind = kinds[job % len(kinds)]
    rec = {"job": job, "seed": seed, "gen": "skills-v1.2", "kind": kind, "writer": writer, "verifier": checker, "status": "error"}
    t0 = time.time()
    try:
        make, build = CASES[kind]
        c = make(seed, job, _rng(kind, seed, job))
        if c is None:
            rec["status"] = "no_passage"
            return rec
        rec["case"] = {k: v for k, v in c.items() if k not in ("prompt", "schema", "passage")}
        if "passage" in c:
            rec["passage"] = {"id": c["passage"]["id"], "url": c["passage"]["url"]}
        g = synth.teacher(c["prompt"], c["schema"], 0.9, writer, 2500)
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"))
        built = build(c, g["content"])
        if built is None:
            rec["status"] = "bad_output"
            return rec
        state, qs, ans, checked = built
        cq = [q for q in qs if q["id"] in checked]
        v = synth.teacher(verify_prompt(render_state(state), cq), synth.verify_schema(cq), 0.0, checker, 400 + 250 * len(cq))
        rec.update(verify_tokens=v["tokens"], verify_prompt_tokens=v.get("prompt_tokens"))
        got = {q["id"]: synth.parse_verdict(q, v["content"].get(q["id"])) for q in cq}
        rec["checker"] = got
        if any((got[q["id"]] or {}).get("label") != ans[q["id"]]["label"] for q in cq):
            rec["status"] = "checker_disagrees"
            return rec
        grounded = kind in ("grounding", "claims")
        ex = {"state": state, "questions": qs, "answers": ans,
              "meta": {"source": SOURCE_ID, "license": "ODC-By-1.0 AND Apache-2.0" if grounded else "Apache-2.0", "split": "train",
                       "teacher": f"{writer} (checked by {checker})",
                       "tags": ["synthetic", "skills", f"skill:{kind}", f"target:{c['target']}", "constructed_labels", "multiq"],
                       "notes": f"fineweb-edu {c['passage']['id']}" if grounded else kind}}
        Example.model_validate(ex)
        rec.update(status="ok", example=ex)
    except OSError as e:
        rec.update(status="retry", error=str(e)[:300])
    except (ValueError, KeyError, TypeError) as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    finally:
        rec["seconds"] = round(time.time() - t0, 1)
    return rec


def main(argv: list[str] | None = None) -> None:
    from kodiak_s1.data.gen2.__main__ import load_prices
    from kodiak_s1.data.gen2.pipeline import cost

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--seed", type=int, default=8)
    ap.add_argument("--kinds", default=",".join(KINDS))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--writer", default=WRITER)
    ap.add_argument("--checker", default=CHECKER)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-usd", type=float, default=1.0)
    a = ap.parse_args(argv)
    kinds = a.kinds.split(",")
    out, prices = Path(a.out), load_prices()
    done, spent = set(), 0.0
    if out.exists():
        for line in out.open():
            r = json.loads(line)
            spent += cost(r, prices)
            if r["status"] != "retry":
                done.add(r["job"])
    todo = [i for i in range(a.start, a.start + a.n) if i not in done]
    lock, stats, state = threading.Lock(), {}, {"spent": spent}

    def work(i: int) -> None:
        with lock:
            if state["spent"] >= a.max_usd:
                return
        rec = run_job(i, a.seed, a.writer, a.checker, kinds)
        with lock:
            state["spent"] += cost(rec, prices)
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            key = f"{rec['kind']}:{rec['status']}"
            stats[key] = stats.get(key, 0) + 1
            n = sum(stats.values())
            if n % 20 == 0 or n == len(todo):
                print(f"[{time.strftime('%H:%M:%S')}] {n}/{len(todo)} ${state['spent']:.2f}", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, todo))
    print(f"done: {dict(sorted(stats.items()))}, ${state['spent']:.2f} spent in total", flush=True)


if __name__ == "__main__":
    main()
