"""Wording-trap eval v0.1: ~100 checked items replacing the 8-sentence label-overlap probe as a gate (rule 2: no tiny tests as gates).

Trap items: the message contains the words of a WRONG option inside a condition, negation, hypothetical, quote or past event, while the
writer means another option ("if it can't arrive by Monday, cancel and refund me" -> delivery status). Control items: the message plainly asks
for the right option in its own words, so a model that merely avoids options whose words appear fails them. Writer + blind checker, answer
fixed by construction (seed 31; never trained on).

    uv run python scripts/build_trap_eval.py --per-type 75   # -> data/eval/kodiak-trap-eval-v0.1.jsonl (up to 50 + 50)
"""
import argparse
import json
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from kodiak_s1.data import synth
from kodiak_s1.data.gen2.prompts import verify_prompt
from kodiak_s1.schema import render_state

WRITER, CHECKER = "do:openai-gpt-oss-120b", "do:deepseek-3.2"
DOMAINS = ["online orders and delivery", "a software subscription", "hotel and travel bookings", "a bank card", "a phone and internet plan",
           "an IT helpdesk", "a gym membership", "a food delivery app", "car insurance claims", "a utility bill", "a SaaS account and billing",
           "event tickets", "an apartment rental", "a school or course enrollment", "a doctor's office appointments"]
FRAMES = ["a condition ('if X doesn't happen, then ...')", "an explicit negation ('I do NOT want ...')", "a hypothetical or question about "
          "policy ('what would happen if I ...?')", "a past event ('last time I ... and it was fine')", "someone else's request quoted"]


def prompt(kind: str, domain: str, frame: str) -> str:
    base = (f"Setting: customer messages for {domain}. Write 3 short answer options (2 to 5 words each) for the question 'What does the "
            "customer want?': three clearly different intents. Then write one customer message (1 to 3 sentences). ")
    if kind == "trap":
        return base + (f"The message must contain the exact key words of one WRONG option (name it in trap_option) inside {frame}, while what "
                       "the customer actually wants is a different option (name it in gold_option). A careful reader must pick gold_option; a "
                       "reader who matches words would pick trap_option. Return JSON only.")
    return base + ("The message must plainly ask for one option (gold_option), using some of that option's own words, with no conditions or "
                   "negations. Leave trap_option empty. Return JSON only.")


SCHEMA = {"type": "object", "properties": {"options": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3},
                                           "message": {"type": "string"}, "gold_option": {"type": "string"}, "trap_option": {"type": "string"}},
          "required": ["options", "message", "gold_option", "trap_option"]}


def _words(t: str) -> set[str]:
    import re
    return {w for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 2 and w not in {"the", "and", "for", "you", "your", "with", "this", "that", "not"}}


def job(i: int, kind: str) -> dict:
    rng = random.Random(f"trap:31:{kind}:{i}")
    rec = {"job": i, "type": kind, "writer": WRITER, "verifier": CHECKER, "status": "error"}
    try:
        g = synth.teacher(prompt(kind, rng.choice(DOMAINS), rng.choice(FRAMES)), SCHEMA, 0.9, WRITER, 800)
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"))
        o = g["content"]
        opts = [x.strip() for x in o["options"]]
        if len(set(map(str.lower, opts))) != 3 or o["gold_option"].strip() not in opts or not o["message"].strip():
            rec["status"] = "bad_output"
            return rec
        if kind == "trap" and (o["trap_option"].strip() not in opts or o["trap_option"].strip() == o["gold_option"].strip()
                               or len(_words(o["trap_option"]) & _words(o["message"])) / max(1, len(_words(o["trap_option"]))) < 0.6):
            rec["status"] = "bad_output"  # a trap must actually contain the wrong option's key words
            return rec
        rng.shuffle(opts)
        labels = [{"id": f"o{k}", "text": t} for k, t in enumerate(opts)]
        gold = f"o{opts.index(o['gold_option'].strip())}"
        q = {"type": "choice", "id": "intent", "text": "What does the customer want?", "labels": labels}
        state = f"Customer: {o['message'].strip()}"
        v = synth.teacher(verify_prompt(render_state(state), [q]), synth.verify_schema([q]), 0.0, CHECKER, 500)
        rec.update(verify_tokens=v["tokens"], verify_prompt_tokens=v.get("prompt_tokens"))
        got = synth.parse_verdict(q, v["content"].get("intent"))
        if (got or {}).get("label") != gold:
            rec["status"] = "checker_disagrees"
            return rec
        rec.update(status="ok", example={"state": state, "questions": [q], "answers": {"intent": {"label": gold}},
                   "meta": {"source": "kodiak_trap", "split": "test", "license": "Apache-2.0", "teacher": f"{WRITER} (checked by {CHECKER})",
                            "tags": ["eval:trap", f"trap:{kind}"]}})
    except OSError as e:
        rec.update(status="retry", error=str(e)[:200])
    except (ValueError, KeyError, TypeError) as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    return rec


ap = argparse.ArgumentParser()
ap.add_argument("--per-type", type=int, default=75)
ap.add_argument("--trap-extra", type=int, default=0, help="additional trap jobs (indices after per-type), appended to the raw file")
a = ap.parse_args()
raw = Path("data/eval/trap_eval_raw.jsonl")
recs = [json.loads(l) for l in raw.open()] if raw.exists() else []
for attempt in range(3):
    done = {(r["type"], r["job"]) for r in recs if r["status"] != "retry"}
    todo = [(i, k) for k in ("trap", "control") for i in range(a.per_type + (a.trap_extra if k == "trap" else 0)) if (k, i) not in done]
    if not todo:
        break
    with ThreadPoolExecutor(12) as ex:
        recs = [r for r in recs if r["status"] != "retry"] + list(ex.map(lambda t: job(*t), todo))
raw.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n")
out, n = Path("data/eval/kodiak-trap-eval-v0.1.jsonl"), {"trap": 0, "control": 0}
with out.open("w") as f:
    for r in sorted(recs, key=lambda r: (r["type"], r["job"])):
        ex = r.get("example") or {}
        if r["type"] == "trap" and r["status"] == "ok":  # re-check older records with the same rule
            labs = {l["id"]: l["text"] for l in ex["questions"][0]["labels"]}
            g = ex["answers"]["intent"]["label"]
            if not any(len(_words(t) & _words(ex["state"])) / max(1, len(_words(t))) >= 0.6 for i2, t in labs.items() if i2 != g):
                continue
        if r["status"] == "ok" and n[r["type"]] < 50:
            f.write(json.dumps(r["example"], ensure_ascii=False) + "\n")
            n[r["type"]] += 1
from collections import Counter
print(Counter((r["type"], r["status"]) for r in recs), "->", out, n, file=sys.stderr)
