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

# v2 (D43): three worlds with the same rule *shapes* but different surface, so the lesson is "read the condition", not "wizard letters".
# Per category: kind = normal | consumable (no returns once opened) | special (exchange only, within 7 days); flag = the "store credit only" marker.
WORLDS = {
    "wizard": {"desc": "a wizard shop", "currency": "gold", "weight": 0.35,
               "shops": ["Wyrmwood Potions & Curios", "The Gilded Cauldron", "Mossback Artifacts", "Hollowmere Wand Emporium", "The Crooked Candle",
                         "Starfall Sundries", "Brambleglen Apothecary", "The Quiet Dragon Trading Co."],
               "couriers": ["Owl Post Express", "Broomline Couriers", "Griffin Freight"],
               "catalog": {"potion": (["Draught of Deep Sleep", "Elixir of Borrowed Courage", "Tonic of Tolerable Mornings"], (8, 60), "consumable", "opened"),
                           "scroll": (["Scroll of Weather Bending", "Scroll of Lesser Summoning"], (15, 120), "consumable", "read"),
                           "wand": (["Hawthorn Wand (dragon-scale core)", "Willow Wand (unicorn-hair core)"], (40, 300), "normal", "cursed"),
                           "artifact": (["Self-Stirring Cauldron", "Enchanted Hourglass", "Mirror of Mild Honesty"], (30, 500), "normal", "cursed"),
                           "creature": (["Miniature Dragon Hatchling", "Familiar Owl", "Mimic Chest (house-trained)"], (80, 900), "special", None),
                           "apparel": (["Cloak of Partial Invisibility", "Boots of Brisk Walking"], (20, 200), "normal", "cursed")},
               "rules": {"credit": "Cursed items can only be returned for store credit.", "consumable": "Opened potions and read scrolls cannot be returned.",
                         "special": "Creatures can only be exchanged, and only within 7 days of purchase."},
               "member": "Guild members", "voice": "Sign with an invented wizardly name."},
    "retail": {"desc": "an online home goods store", "currency": "USD", "weight": 0.45,
               "shops": ["Oak & Ember Home", "Northline Living", "Parcel & Pine", "The Walnut Room", "Brightside Goods"],
               "couriers": ["UPS", "FedEx", "USPS"],
               "catalog": {"cosmetics": (["Vitamin C serum", "Lavender body oil", "Clay face mask set"], (12, 90), "consumable", "opened"),
                           "software": (["Photo-editing app license", "Tax software download"], (20, 150), "consumable", "activated"),
                           "furniture": (["Walnut writing desk", "Oak bookshelf", "Linen armchair"], (120, 1400), "normal", "clearance"),
                           "custom": (["Custom-sized dining table", "Monogrammed headboard"], (400, 2500), "special", None),
                           "lighting": (["Brass floor lamp", "Ceramic table lamp"], (35, 300), "normal", "clearance"),
                           "textiles": (["Wool throw blanket", "Linen duvet cover"], (30, 250), "normal", "clearance")},
               "rules": {"credit": "Clearance items can only be returned for store credit.",
                         "consumable": "Opened cosmetics and activated software cannot be returned.",
                         "special": "Custom-made items can only be exchanged, and only within 7 days of purchase."},
               "member": "Plus members", "voice": "Sign with an ordinary first name or initials, or no signature."},
    "outdoor": {"desc": "an outdoor gear co-op in Alaska", "currency": "USD", "weight": 0.20,
                "shops": ["Grizzly Peak Outfitters", "Kenai Trail Co-op", "Denali Basecamp Supply", "Tundra & Timber Gear"],
                "couriers": ["UPS", "Alaska Air Cargo", "USPS"],
                "catalog": {"fuel": (["Isobutane fuel canister (4-pack)", "Freeze-dried meal bundle"], (15, 80), "consumable", "used"),
                            "boots": (["Custom-fitted mountaineering boots"], (300, 700), "special", None),
                            "tents": (["Two-person backpacking tent", "Four-season expedition tent"], (180, 900), "normal", "on_sale"),
                            "packs": (["65-liter backpack", "Bear-resistant food canister"], (60, 400), "normal", "on_sale"),
                            "outerwear": (["Insulated parka", "Rain shell jacket"], (90, 500), "normal", "on_sale")},
                "rules": {"credit": "Sale items can only be returned for store credit.", "consumable": "Used fuel and opened food cannot be returned.",
                          "special": "Custom-fitted boots can only be exchanged, and only within 7 days of purchase."},
                "member": "co-op members", "voice": "Sign with an ordinary name."},
}
WANTS = {  # what the customer wants most -> the intent label (v2 splits "just information" into order status vs a general question)
    "refund": "a refund of their money",
    "replacement": "a replacement or faster delivery",
    "exchange": "an exchange for a different item",
    "credit": "store credit",
    "status": "an update on where their order is",
    "question": "an answer to a general question about the item",
}
OFFERS = ["a full refund or a free replacement", "a full refund", "store credit only", "an exchange only", "nothing: the return isn't allowed"]
ACTIONS = {"refund": "process a refund", "replacement": "ship a replacement or speed up delivery", "exchange": "arrange an exchange",
           "credit": "offer store credit", "decline": "decline and explain the rules", "status": "give a delivery update",
           "question": "answer their question"}


@dataclass
class Case:
    job: int
    world: str
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
    rng = random.Random(f"returns-desk-v2:{seed}:{job}")
    wname = rng.choices(list(WORLDS), [w["weight"] for w in WORLDS.values()])[0]
    W = WORLDS[wname]
    cat = rng.choice(list(W["catalog"]))
    items, (lo, hi), kind, flag = W["catalog"][cat]
    today = dt.date(2026, 1, 1) + dt.timedelta(days=rng.randrange(0, 365))
    window = rng.choice([14, 30, 60])
    bonus = rng.choice([0, 15, 30])
    days_ago = rng.choice([rng.randint(1, 10), rng.randint(5, window + bonus + 25)])
    purchase = today - dt.timedelta(days=days_ago)
    status = rng.choices(["delivered", "delivered damaged", "in transit", "in transit, overdue"], [0.55, 0.15, 0.12, 0.18])[0]
    order = {"order_id": f"{rng.choice('ABCDEFGHJK')}-{rng.randint(1000, 9999)}", "item": rng.choice(items), "category": cat,
             f"price_{'gold' if W['currency'] == 'gold' else 'usd'}": rng.randint(lo, hi), "purchased": purchase.isoformat(), "delivery": status,
             "member": rng.random() < 0.35}
    if status.startswith("in transit"):
        order["expected_by"] = (today + dt.timedelta(days=rng.randint(1, 6)) if status == "in transit"
                                else today - dt.timedelta(days=rng.randint(3, 12))).isoformat()
    if kind == "consumable" and status.startswith("delivered"):
        order[flag] = rng.random() < 0.4
    if kind == "normal" and flag and status.startswith("delivered"):
        order[flag] = rng.random() < 0.25
    courier_known = rng.random() < 0.6
    if courier_known:
        order["courier"] = rng.choice(W["couriers"])
    want = rng.choices(list(WANTS), [0.28, 0.22, 0.13, 0.1, 0.14, 0.13])[0]
    if status.startswith("in transit") and want in ("exchange", "credit"):
        want = rng.choice(["replacement", "refund", "status"])
    if want == "status" and not status.startswith("in transit") and rng.random() < 0.7:
        want = rng.choice(["refund", "question"])  # "where is it?" mostly comes with orders still on their way
    fallback = rng.choice([w for w in ("refund", "credit", "exchange") if w != want]) if want in ("replacement", "exchange", "status") and rng.random() < 0.45 else None
    trap = rng.choice([w for w in ("refund", "credit", "exchange", "replacement") if w not in (want, fallback)]) if rng.random() < 0.3 else None
    member = W["member"]
    rules = [f"Returns are accepted within {window} days of purchase" + (f" ({window + bonus} days for {member})." if bonus else "."),
             "If an order arrives damaged, or is more than 2 days past its expected delivery date, the customer may choose a full refund or a free replacement, whatever the other rules say.",
             W["rules"]["credit"], W["rules"]["consumable"], W["rules"]["special"]]
    rng.shuffle(rules)
    return Case(job=job, world=wname, shop=rng.choice(W["shops"]), window_days=window, member_bonus=bonus, today=today.isoformat(), order=order,
                want=want, fallback=fallback, trap=trap, avoid_words=rng.random() < 0.5,
                tone=rng.choice(["polite", "frazzled", "grumpy", "overly formal", "chatty", "terse"]),
                letter_format=rng.choice(["email", "short note", "chat message"] if wname != "wizard" else ["letter", "short note", "message sent by owl"]),
                courier_known=courier_known, rules=rules)


def _kind(c: Case) -> tuple[str, str | None]:
    _, _, kind, flag = WORLDS[c.world]["catalog"][c.order["category"]]
    return kind, flag


# ---- the rules, in code ------------------------------------------------------------------------------------------------------------

def offer(c: Case) -> str:
    o, today = c.order, dt.date.fromisoformat(c.today)
    overdue = o["delivery"] == "in transit, overdue" and (today - dt.date.fromisoformat(o["expected_by"])).days > 2
    if o["delivery"] == "delivered damaged" or overdue:
        return OFFERS[0]
    age = (today - dt.date.fromisoformat(o["purchased"])).days
    kind, flag = _kind(c)
    if kind == "special":
        return OFFERS[3] if age <= 7 else OFFERS[4]
    if age > c.window_days + (c.member_bonus if o["member"] else 0):
        return OFFERS[4]
    if kind == "normal" and flag and o.get(flag):
        return OFFERS[2]
    if kind == "consumable" and o.get(flag):
        return OFFERS[4]
    return OFFERS[1]


def action(c: Case, off: str) -> str:
    if c.want in ("status", "question"):
        return ACTIONS[c.want]
    allowed = {OFFERS[0]: {"refund", "replacement"}, OFFERS[1]: {"refund", "replacement", "exchange", "credit"},
               OFFERS[2]: {"credit"}, OFFERS[3]: {"exchange"}, OFFERS[4]: set()}[off]
    for w in (c.want, c.fallback):
        if w and w in allowed:
            return ACTIONS[w]
    # Neither is allowed: a good clerk offers what the rules do allow (store credit, else an exchange) before declining.
    return ACTIONS["credit"] if "credit" in allowed else ACTIONS["exchange"] if "exchange" in allowed else ACTIONS["decline"]


def questions_and_answers(c: Case) -> tuple[list[dict], dict]:
    off = offer(c)
    couriers = WORLDS[c.world]["couriers"]
    qs = [{"type": "choice", "id": "want", "text": "What does the customer want most?",
           "labels": [{"id": k, "text": v} for k, v in WANTS.items()]},
          {"type": "choice", "id": "allowed", "text": "Under the shop's rules, what can the shop offer for this item?",
           "labels": [{"id": f"o{i}", "text": t} for i, t in enumerate(OFFERS)]},
          {"type": "choice", "id": "next", "text": "What should the clerk do next? (Grant what the customer wants most if the rules allow it, "
                                                   "else their stated fallback, else offer what the rules do allow, else decline.)",
           "labels": [{"id": k, "text": v} for k, v in ACTIONS.items()]},
          {"type": "choice", "id": "courier", "text": "Which courier handled this order?", "labels": [{"id": f"c{i}", "text": t} for i, t in enumerate(couriers)]}]
    ans = {"want": {"label": c.want}, "allowed": {"label": f"o{OFFERS.index(off)}"},
           "next": {"label": next(k for k, v in ACTIONS.items() if v == action(c, off))},
           "courier": {"label": f"c{couriers.index(c.order['courier'])}"} if c.courier_known else {"null": True}}
    return qs, ans


# ---- the letter ---------------------------------------------------------------------------------------------------------------------

def letter_prompt(c: Case) -> str:
    W = WORLDS[c.world]
    facts = {k: v for k, v in c.order.items() if k != "courier"}
    lines = [f"Write a customer's {c.letter_format} to the returns desk of {c.shop}, {W['desc']}. Tone: {c.tone}. 40-140 words.",
             f"Order facts (the message may mention some of them, must not contradict any): {json.dumps(facts)}",
             f"Today is {c.today}.",
             f"What the customer wants most: {WANTS[c.want]}."]
    if c.fallback:
        lines.append(f"They also say what they'd accept if that isn't possible: {WANTS[c.fallback]}. Make clear that is only a fallback.")
    if c.trap:
        lines.append(f"They explicitly say they do NOT want {WANTS[c.trap]}.")
    if c.avoid_words and c.want in ("refund", "replacement", "exchange", "credit"):
        words = {"refund": "refund", "replacement": "replace/replacement", "exchange": "exchange", "credit": "credit"}[c.want]
        lines.append(f"Express what they want without using the word(s) '{words}': paraphrase naturally (e.g. 'I'd like my money back').")
    if c.want == "status":
        lines.append("Their main point is asking where the order is or when it will arrive (phrase it as a question).")
    if c.want == "question":
        lines.append("They only ask a general question about using or caring for the item; they are not asking about delivery or requesting any remedy.")
    lines.append(f"Do not mention the courier's name. Do not mention the shop's rules. {W['voice']} Return JSON only.")
    return "\n".join(lines)


def state_for(c: Case, letter: str) -> dict:
    return {"shop": c.shop, "today": c.today, "returns_rules": c.rules, "order": c.order, "customer_message": letter}


def run_job(job: int, seed: int, writer: str, checker: str) -> dict:
    from kodiak_s1.data import synth
    from kodiak_s1.schema import Example

    c = make_case(job, seed)
    rec = {"job": job, "seed": seed, "gen": "sim-returns-v2", "writer": writer, "verifier": checker, "case": asdict(c), "status": "error"}
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
                       "tags": ["synthetic", "sim:returns_desk", f"world:{c.world}", "computed_labels", "multiq", f"want:{c.want}"]
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
