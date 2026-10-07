"""E23 training data: contrast groups. One writer call makes a group of examples that share one field exactly (the anchor) and differ in the
other, one example per answer, so the anchor alone can't predict the label (the word-counter check, scripts/shortcut_check.py, D67). The
anchor alternates by job: step safety anchors the next step (three tasks) or the task (three next steps); refund eligibility anchors the
request (three policies) or the policy (three requests). Each example is checked blind (DeepSeek-V3.2); a group is kept when at least two
of its examples pass, and only the passing examples are written.

    uv run python scripts/build_groups.py --per-kind 60 --seed 71 --out data/synthetic/groups_pilot.jsonl --max-usd 1
"""
import argparse
import json
import random
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from kodiak_s1.data import synth
from kodiak_s1.data.gen2.__main__ import load_prices
from kodiak_s1.data.gen2.pipeline import cost
from kodiak_s1.data.gen2.prompts import verify_prompt
from kodiak_s1.data.sim.probes import KINDS
from kodiak_s1.schema import Example, render_state

WRITER, CHECKER = "do:openai-gpt-oss-120b", "do:deepseek-3.2"
ANCHORS = {"step_safety": ["next_step", "task"], "refund_eligibility": ["request", "policy"]}
DOMAINS = {
    "step_safety": ["git and code review", "files and folders", "email and messages", "a production database", "cloud servers and DNS",
                    "payments and invoices", "calendar and meetings", "package installs and builds", "docker and kubernetes", "a CRM",
                    "shared documents and permissions", "user accounts and passwords", "spreadsheets and reports", "social media posting",
                    "backups and logs", "an online store's catalog"],
    "refund_eligibility": ["clothing", "electronics", "software subscriptions", "airline tickets", "concert tickets", "furniture",
                           "online courses", "meal kits", "gym memberships", "hotel bookings", "phone plans", "video games",
                           "cosmetics", "car rentals", "event workshops", "home appliances"],
}
GUIDE = {
    "step_safety": {
        "safe": "running it without asking is clearly what the user wants and does no harm in this situation",
        "confirm": "it's reasonable but has a real side effect or ambiguity the user should confirm first",
        "never": "it's destructive or clearly goes against what the user asked or wants in this situation",
    },
    "refund_eligibility": {
        "yes": "the request clearly meets every condition of the policy",
        "no": "the request clearly breaks at least one condition of the policy",
        "need_info": "a condition can't be checked because the request leaves out a fact the policy depends on",
    },
}


def prompt(kind, anchor, rng):
    spec = KINDS[kind]
    other = next(f for f in spec["fields"] if f != anchor)
    labels = list(spec["labels"])
    lines = "\n".join(f"- \"{l}\": the correct answer is '{spec['labels'][l]}' because {GUIDE[kind][l]}" for l in labels)
    return (f"Domain: {rng.choice(DOMAINS[kind])}.\nA decision task has two fields:\n- {anchor}: {spec['fields'][anchor]}\n- {other}: "
            f"{spec['fields'][other]}\nThe question: {spec['question']}\nOptions: {'; '.join(spec['labels'].values())}.\n\n"
            f"Write ONE {anchor} and {len(labels)} different versions of the {other}, one per answer:\n{lines}\n\n"
            f"The {anchor} is shared word for word by all versions, so the answer must depend on the {other}: someone who reads only the "
            f"{anchor} must not be able to tell the answer. Make the versions similar in length and style; don't put the option words or "
            "obvious giveaways (like 'dangerous', 'eligible', 'please confirm') in them; let the facts decide. Write naturally. Use single "
            f"quotes inside text, never double quotes. Return JSON only: {{\"{anchor}\": \"...\", " + ", ".join(f'"{l}": "..."' for l in labels) + "}")


def schema(kind, anchor):
    props = {k: {"type": "string"} for k in [anchor] + list(KINDS[kind]["labels"])}
    return {"type": "object", "properties": props, "required": list(props)}


def job(kind, i, seed):
    rng = random.Random(f"groups:{seed}:{kind}:{i}")
    anchor = ANCHORS[kind][i % 2]
    other = next(f for f in KINDS[kind]["fields"] if f != anchor)
    rec = {"kind": kind, "job": i, "seed": seed, "anchor": anchor, "writer": WRITER, "verifier": CHECKER, "status": "error"}
    try:
        g = synth.teacher(prompt(kind, anchor, rng), schema(kind, anchor), 0.9, WRITER, 2000)
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"))
        c = {k: (" ".join(map(str, v)) if isinstance(v, list) else str(v or "")).strip() for k, v in g["content"].items()}
        labels = list(KINDS[kind]["labels"])
        if not c.get(anchor) or not all(c.get(l) for l in labels) or len({c[l] for l in labels}) < len(labels):
            rec["status"] = "bad_output"
            return rec
        spec, kept, vt, vp = KINDS[kind], [], 0, 0
        q = [{"type": "choice", "id": "decision", "text": spec["question"],
              "labels": [{"id": k, "text": t} for k, t in spec["labels"].items()]}]
        for l in labels:
            state = {f: (c[anchor] if f == anchor else c[l]) for f in spec["fields"]}
            v = synth.teacher(verify_prompt(render_state(state), q), synth.verify_schema(q), 0.0, CHECKER, 650)
            vt += v["tokens"]
            vp += v.get("prompt_tokens") or 0
            if (synth.parse_verdict(q[0], v["content"].get("decision")) or {}).get("label") == l:
                ex = {"state": state, "questions": q, "answers": {"decision": {"label": l}},
                      "meta": {"source": "kodiak_groups", "split": "train", "license": "Apache-2.0",
                               "teacher": f"{WRITER} (checked by {CHECKER})",
                               "tags": ["synthetic", "groups", f"probe:{kind}", f"target:{l}", f"group:{kind}-{seed}-{i}", f"anchor:{anchor}"]}}
                Example.model_validate(ex)
                kept.append(ex)
        rec.update(verify_tokens=vt, verify_prompt_tokens=vp, n_kept=len(kept))
        rec.update(status="ok", examples=kept) if len(kept) >= 2 else rec.update(status="checker_disagrees")
    except OSError as e:
        rec.update(status="retry", error=str(e)[:200])
    except (ValueError, KeyError, TypeError, AttributeError) as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    return rec


ap = argparse.ArgumentParser()
ap.add_argument("--per-kind", type=int, default=60)
ap.add_argument("--kinds", default=",".join(ANCHORS))
ap.add_argument("--seed", type=int, default=71)
ap.add_argument("--start", type=int, default=0)
ap.add_argument("--out", default="data/synthetic/groups_pilot.jsonl")
ap.add_argument("--max-usd", type=float, default=1.0)
ap.add_argument("--workers", type=int, default=16)
a = ap.parse_args()
out, prices = Path(a.out), load_prices()
done, spent = set(), 0.0
if out.exists():
    for line in out.open():
        r = json.loads(line)
        spent += cost(r, prices)
        if r["status"] != "retry":
            done.add((r["kind"], r["job"]))
todo = [(k, j) for j in range(a.start, a.start + a.per_kind) for k in a.kinds.split(",") if (k, j) not in done]
lock, stats, state = threading.Lock(), Counter(), {"spent": spent}


def work(kj):
    with lock:
        if state["spent"] >= a.max_usd:
            return
    rec = job(kj[0], kj[1], a.seed)
    with lock:
        state["spent"] += cost(rec, prices)
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        stats[f"{rec['kind']}:{rec['status']}"] += 1


with ThreadPoolExecutor(a.workers) as ex:
    list(ex.map(work, todo))
print(f"done: {dict(sorted(stats.items()))}, ${state['spent']:.2f} spent in total", flush=True)
