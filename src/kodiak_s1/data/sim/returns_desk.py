"""The Enchanted Returns Desk: a simulator whose right answers are computed by code (GENERATOR_V2 §16-17).

Code invents a wizard shop, its returns rules, an order record and what the customer really wants (sometimes with a conditional fallback,
sometimes with word traps like "I do NOT want store credit"). The writer model only writes the customer's letter from that brief; a blind
checker must read the letter's intent back correctly, or the example is dropped. Every other answer (what the rules allow, what the clerk
should do next, a detail the record may not contain) comes from the code, so it carries no teacher label noise.

    uv run python -m kodiak_s1.data.sim.returns_desk --n 40 --seed 8 --out data/synthetic/pilot_sim_returns.jsonl --max-usd 1
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

WRITER, CHECKER = "do:openai-gpt-oss-120b", "do:deepseek-3.2"
SOURCE_ID = "kodiak_sim_returns"

SHOPS = ["Wyrmwood Potions & Curios", "The Gilded Cauldron", "Mossback Artifacts", "Hollowmere Wand Emporium", "The Crooked Candle",
         "Starfall Sundries", "Brambleglen Apothecary", "The Quiet Dragon Trading Co."]
COURIERS = ["Owl Post Express", "Broomline Couriers", "Griffin Freight"]
# (category, items, price range in gold)
CATALOG = {
    "potion": (["Draught of Deep Sleep", "Elixir of Borrowed Courage", "Tonic of Tolerable Mornings", "Philter of Minor Luck"], (8, 60)),
    "scroll": (["Scroll of Weather Bending", "Scroll of Lesser Summoning", "Scroll of Perfect Recall"], (15, 120)),
    "wand": (["Hawthorn Wand (dragon-scale core)", "Willow Wand (unicorn-hair core)", "Ebony Wand (phoenix-ash core)"], (40, 300)),
    "artifact": (["Self-Stirring Cauldron", "Enchanted Hourglass", "Mirror of Mild Honesty", "Lantern of Unfailing Light"], (30, 500)),
    "creature": (["Miniature Dragon Hatchling", "Familiar Owl", "Mimic Chest (house-trained)"], (80, 900)),
    "apparel": (["Cloak of Partial Invisibility", "Boots of Brisk Walking", "Hat of Warm Ears"], (20, 200)),
}
WANTS = {  # what the customer wants most -> the intent label
    "refund": "a refund of their gold",
    "replacement": "a replacement or faster delivery",
    "exchange": "an exchange for a different item",
    "credit": "store credit",
    "info": "just information (a question, no request)",
}
OFFERS = ["a full refund or a free replacement", "a full refund", "store credit only", "an exchange only", "nothing: the return isn't allowed"]
ACTIONS = {"refund": "process a refund", "replacement": "ship a replacement or speed up delivery", "exchange": "arrange an exchange",
           "credit": "offer store credit", "decline": "decline and explain the rules", "info": "answer their question"}


@dataclass
class Case:
    job: int
    shop: str
    window_days: int
    member_bonus: int
    today: str
    order: dict
    want: str
    fallback: str | None
    trap: str | None  # a want the customer mentions but explicitly does NOT want
    avoid_words: bool  # write the true want without its label's words
    tone: str
    letter_format: str
    courier_known: bool
    rules: list[str] = field(default_factory=list)


def make_case(job: int, seed: int) -> Case:
    rng = random.Random(f"returns-desk:{seed}:{job}")
    cat = rng.choice(list(CATALOG))
    items, (lo, hi) = CATALOG[cat]
    today = dt.date(2026, 1, 1) + dt.timedelta(days=rng.randrange(0, 365))
    window = rng.choice([14, 30, 60])
    bonus = rng.choice([0, 15, 30])
    days_ago = rng.choice([rng.randint(1, 10), rng.randint(5, window + bonus + 25)])
    purchase = today - dt.timedelta(days=days_ago)
    status = rng.choices(["delivered", "delivered damaged", "in transit", "in transit, overdue"], [0.55, 0.15, 0.12, 0.18])[0]
    order = {"order_id": f"{rng.choice('ABCDEFGHJK')}-{rng.randint(1000, 9999)}", "item": rng.choice(items), "category": cat,
             "price_gold": rng.randint(lo, hi), "purchased": purchase.isoformat(), "delivery": status,
             "guild_member": rng.random() < 0.35}
    if status.startswith("in transit"):
        order["expected_by"] = (today + dt.timedelta(days=rng.randint(1, 6)) if status == "in transit"
                                else today - dt.timedelta(days=rng.randint(3, 12))).isoformat()
    if cat in ("potion", "scroll") and status.startswith("delivered"):
        order["opened" if cat == "potion" else "read"] = rng.random() < 0.4
    if cat in ("wand", "artifact", "apparel") and status.startswith("delivered"):
        order["cursed"] = rng.random() < 0.25
    courier_known = rng.random() < 0.6
    if courier_known:
        order["courier"] = rng.choice(COURIERS)
    want = rng.choices(list(WANTS), [0.3, 0.25, 0.15, 0.12, 0.18])[0]
    if status.startswith("in transit") and want in ("exchange", "credit"):
        want = rng.choice(["replacement", "refund", "info"])
    fallback = rng.choice([w for w in ("refund", "credit", "exchange") if w != want]) if want in ("replacement", "exchange") and rng.random() < 0.45 else None
    trap = rng.choice([w for w in ("refund", "credit", "exchange", "replacement") if w not in (want, fallback)]) if rng.random() < 0.3 else None
    rules = [f"Returns are accepted within {window} days of purchase" + (f" ({window + bonus} days for Guild members)." if bonus else "."),
             "If an order arrives damaged, or is more than 2 days past its expected delivery date, the customer may choose a full refund or a free replacement, whatever the other rules say.",
             "Cursed items can only be returned for store credit.",
             "Opened potions and read scrolls cannot be returned.",
             "Creatures can only be exchanged, and only within 7 days of purchase."]
    rng.shuffle(rules)
    return Case(job=job, shop=rng.choice(SHOPS), window_days=window, member_bonus=bonus, today=today.isoformat(), order=order, want=want,
                fallback=fallback, trap=trap, avoid_words=rng.random() < 0.5,
                tone=rng.choice(["polite", "frazzled", "grumpy", "overly formal", "chatty", "terse"]),
                letter_format=rng.choice(["letter", "short note", "message sent by owl"]), courier_known=courier_known, rules=rules)


# ---- the rules, in code ------------------------------------------------------------------------------------------------------------

def offer(c: Case) -> str:
    o, today = c.order, dt.date.fromisoformat(c.today)
    overdue = o["delivery"] == "in transit, overdue" and (today - dt.date.fromisoformat(o["expected_by"])).days > 2
    if o["delivery"] == "delivered damaged" or overdue:
        return OFFERS[0]
    age = (today - dt.date.fromisoformat(o["purchased"])).days
    if o["category"] == "creature":
        return OFFERS[3] if age <= 7 else OFFERS[4]
    if age > c.window_days + (c.member_bonus if o["guild_member"] else 0):
        return OFFERS[4]
    if o.get("cursed"):
        return OFFERS[2]
    if o.get("opened") or o.get("read"):
        return OFFERS[4]
    return OFFERS[1]


def action(c: Case, off: str) -> str:
    if c.want == "info":
        return ACTIONS["info"]
    allowed = {OFFERS[0]: {"refund", "replacement"}, OFFERS[1]: {"refund", "replacement", "exchange", "credit"},
               OFFERS[2]: {"credit"}, OFFERS[3]: {"exchange"}, OFFERS[4]: set()}[off]
    for w in (c.want, c.fallback):
        if w and w in allowed:
            return ACTIONS[w]
    # Neither is allowed: a good clerk offers what the rules do allow (store credit, else an exchange) before declining.
    return ACTIONS["credit"] if "credit" in allowed else ACTIONS["exchange"] if "exchange" in allowed else ACTIONS["decline"]


def questions_and_answers(c: Case) -> tuple[list[dict], dict]:
    off = offer(c)
    qs = [{"type": "choice", "id": "want", "text": "What does the customer want most?",
           "labels": [{"id": k, "text": v} for k, v in WANTS.items()]},
          {"type": "choice", "id": "allowed", "text": "Under the shop's rules, what can the shop offer for this item?",
           "labels": [{"id": f"o{i}", "text": t} for i, t in enumerate(OFFERS)]},
          {"type": "choice", "id": "next", "text": "What should the returns clerk do next? (Grant what the customer wants most if the rules allow it, "
                                                   "else their stated fallback, else offer what the rules do allow, else decline.)",
           "labels": [{"id": k, "text": v} for k, v in ACTIONS.items()]},
          {"type": "choice", "id": "courier", "text": "Which courier handled this order?", "labels": [{"id": f"c{i}", "text": t} for i, t in enumerate(COURIERS)]}]
    ans = {"want": {"label": c.want}, "allowed": {"label": f"o{OFFERS.index(off)}"},
           "next": {"label": next(k for k, v in ACTIONS.items() if v == action(c, off))},
           "courier": {"label": f"c{COURIERS.index(c.order['courier'])}"} if c.courier_known else {"null": True}}
    return qs, ans


# ---- the letter ---------------------------------------------------------------------------------------------------------------------

def letter_prompt(c: Case) -> str:
    o = c.order
    facts = {k: v for k, v in o.items() if k not in ("courier",)}
    want = WANTS[c.want]
    lines = [f"Write a customer's {c.letter_format} to the returns desk of {c.shop}, a wizard shop. Tone: {c.tone}. 40-140 words.",
             f"Order facts (the letter may mention some of them, must not contradict any): {json.dumps(facts)}",
             f"Today is {c.today}.",
             f"What the customer wants most: {want}."]
    if c.fallback:
        lines.append(f"They also say what they'd accept if that isn't possible: {WANTS[c.fallback]}. Make clear that is only a fallback.")
    if c.trap:
        lines.append(f"They explicitly say they do NOT want {WANTS[c.trap]}.")
    if c.avoid_words and c.want != "info":
        words = {"refund": "refund", "replacement": "replace/replacement", "exchange": "exchange", "credit": "credit"}[c.want]
        lines.append(f"Express what they want without using the word(s) '{words}': paraphrase naturally (e.g. 'I'd like my gold back').")
    if c.want == "info":
        lines.append("They are only asking a question about the item or the order; they are not requesting any return or remedy.")
    lines.append("Do not mention the courier's name. Do not mention the shop's rules. Sign with an invented wizardly name. Return JSON only.")
    return "\n".join(lines)


def state_for(c: Case, letter: str) -> dict:
    return {"shop": c.shop, "today": c.today, "returns_rules": c.rules, "order": c.order, "customer_message": letter}


def run_job(job: int, seed: int, writer: str, checker: str) -> dict:
    from kodiak_s1.data import synth
    from kodiak_s1.schema import Example

    c = make_case(job, seed)
    rec = {"job": job, "seed": seed, "gen": "sim-returns-v1", "writer": writer, "verifier": checker, "case": asdict(c), "status": "error"}
    t0 = time.time()
    try:
        g = synth.teacher(letter_prompt(c), {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
                          0.9, writer, 800)
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"))
        letter = str(g["content"].get("message", "")).strip()
        if len(letter) < 30:
            rec["status"] = "bad_letter"
            return rec
        qs, ans = questions_and_answers(c)
        # The blind checker reads only the letter and must recover the customer's main want; the other answers are computed.
        want_q = [qs[0]]
        v = synth.teacher(synth.verify_prompt(letter, want_q) if hasattr(synth, "verify_prompt") else _verify_prompt(letter, want_q),
                          synth.verify_schema(want_q), 0.0, checker, 600)
        rec.update(verify_tokens=v["tokens"], verify_prompt_tokens=v.get("prompt_tokens"))
        got = synth.parse_verdict(qs[0], v["content"].get("want"))
        rec["checker_want"] = got
        if not got or got.get("label") != c.want:
            rec["status"] = "letter_mismatch"
            return rec
        ex = {"state": state_for(c, letter), "questions": qs, "answers": ans,
              "meta": {"source": SOURCE_ID, "license": "Apache-2.0", "split": "train", "teacher": f"{writer} (letter; checked by {checker})",
                       "tags": ["synthetic", "sim:returns_desk", "computed_labels", "multiq", f"want:{c.want}"]
                       + (["fallback"] if c.fallback else []) + (["trap"] if c.trap else []) + (["paraphrase"] if c.avoid_words else [])
                       + ([] if c.courier_known else ["null:synthetic"]), "notes": f"{c.shop}; offer={offer(c)}"}}
        Example.model_validate(ex)
        rec.update(status="ok", example=ex)
    except OSError as e:
        rec.update(status="retry", error=str(e)[:300])
    except (ValueError, KeyError, TypeError) as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    finally:
        rec["seconds"] = round(time.time() - t0, 1)
    return rec


def _verify_prompt(letter: str, qs: list[dict]) -> str:
    q = qs[0]
    opts = "; ".join(f'{lab["id"]} = {lab["text"]}' for lab in q["labels"])
    return (f"Read this customer message and answer as a careful reader. First copy the most relevant part into \"quote\", then give "
            f"\"answer\".\n\nMESSAGE:\n{letter}\n\nQUESTION id=want: {q['text']} Options: {opts}\nReturn JSON only.")


def main(argv: list[str] | None = None) -> None:
    from kodiak_s1.data.gen2.pipeline import cost
    from kodiak_s1.data.gen2.__main__ import load_prices

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--seed", type=int, default=8)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--writer", default=WRITER)
    ap.add_argument("--checker", default=CHECKER)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-usd", type=float, default=1.0)
    a = ap.parse_args(argv)
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
        rec = run_job(i, a.seed, a.writer, a.checker)
        with lock:
            state["spent"] += cost(rec, prices)
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats[rec["status"]] = stats.get(rec["status"], 0) + 1
            n = sum(stats.values())
            if n % 10 == 0 or n == len(todo):
                print(f"[{time.strftime('%H:%M:%S')}] {n}/{len(todo)} {stats} ${state['spent']:.2f}", flush=True)

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, todo))
    print(f"done: {stats}, ${state['spent']:.2f} spent in total", flush=True)


if __name__ == "__main__":
    main()
