"""Release audit (D69): one report card per release candidate, per decision kind, from checks that don't share our generator's blind spots.

  1. Reading:     drop each field; if the answer rarely changes, the model isn't using that field
  2. Meaningful:  contrastive pairs (one detail changes the answer); from the contrastive tests where they exist
  3. Meaningless: reversed option order, an unrelated sentence appended, pairwise answers swapped; the answer should not move
  4. Overconfident mistakes: the most confident wrong answers, to read by hand
  5. Test strength: a word-counter trained on our training data, reading one field; if it scores near the model, the test can't prove a skill
  6. Red team (optional, ~$0.5): an LLM writes examples meant to fool a shallow model; a blind checker confirms the answer; we count
     how often Kodiak is fooled

    uv run python scripts/audit.py build                       # -> data/audit/audit-items.jsonl (variants of every skills/real test item)
    uv run python -m kodiak_s1.eval.run predict --model ... --eval data/audit/audit-items.jsonl --out reports/audit/<name>-items.jsonl
    uv run python scripts/audit.py redteam --per-kind 40       # -> data/audit/redteam.jsonl (paid)
    uv run python scripts/audit.py report --name <name>        # -> reports/audit-<name>.md
"""
import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

SOURCES = {  # file -> "synthetic" or "real"
    "data/eval/kodiak-skills-eval-v0.1.jsonl": "synthetic", "data/eval/kodiak-skills2-eval-v0.1.jsonl": "synthetic",
    "data/eval/kodiak-skills3-eval-v0.1.jsonl": "synthetic", "data/eval/kodiak-real-anchors-v0.1.jsonl": "real",
    "data/eval/kodiak-probes-real-v0.1.jsonl": "real",
}
TRAIN = ["data/synthetic/skills_v1_e17_10k.jsonl", "data/synthetic/skills2_v1_e21_7k5.jsonl", "data/synthetic/skills3_v1_e22_10k.jsonl"]
FILLER = ["Unrelated note: the office kitchen will be cleaned on Friday afternoon.", "P.S. The weather has been mild this week.",
          "Side note: our team photo is scheduled for next month.", "(Reminder: the parking garage closes at 9 pm.)"]
OUT = Path("data/audit")


def kind_of(ex):
    for t in ex["meta"]["tags"]:
        if t.startswith(("probe:", "skill:")):
            return t.split(":", 1)[1]
    return "?"


def tagged(ex, aid, variant, origin):
    ex = json.loads(json.dumps(ex))
    ex["meta"]["tags"] = [t for t in ex["meta"]["tags"] if not t.startswith(("audit", "aid:"))] + \
        [f"audit:{variant}", f"aid:{aid}", f"origin:{origin}", f"akind:{kind_of(ex)}"]
    return ex


def build(_):
    OUT.mkdir(parents=True, exist_ok=True)
    rng, seen, n, aid = random.Random(69), set(), Counter(), 0
    with open(OUT / "audit-items.jsonl", "w", encoding="utf-8") as f:
        for path, origin in SOURCES.items():
            for line in open(path, encoding="utf-8"):
                ex = json.loads(line)
                key = json.dumps(ex["state"], sort_keys=True)
                if key in seen:  # real anchors and real probes share items
                    continue
                seen.add(key)
                aid += 1
                out = [tagged(ex, aid, "orig", origin)]
                st = ex["state"]
                strs = [k for k, v in st.items() if isinstance(v, str)] if isinstance(st, dict) else []
                if len(st) > 1:
                    for k in st:
                        v = tagged(ex, aid, f"drop:{k}", origin)
                        v["state"][k] = ""
                        out.append(v)
                v = tagged(ex, aid, "reorder", origin)
                for q in v["questions"]:
                    if q.get("labels"):
                        q["labels"] = q["labels"][::-1]
                out.append(v)
                if strs:
                    v = tagged(ex, aid, "filler", origin)
                    k = max(strs, key=lambda k: len(st[k]))
                    v["state"][k] = st[k].rstrip() + " " + rng.choice(FILLER)
                    out.append(v)
                if kind_of(ex) == "pairwise_judge":
                    v = tagged(ex, aid, "swap", origin)
                    v["state"]["answer_1"], v["state"]["answer_2"] = st["answer_2"], st["answer_1"]
                    lab = v["answers"]["decision"]["label"]
                    v["answers"]["decision"]["label"] = {"first": "second", "second": "first"}.get(lab, lab)
                    out.append(v)
                for v in out:
                    f.write(json.dumps(v, ensure_ascii=False) + "\n")
                    n[v["meta"]["tags"][-4]] += 1
    print(f"{aid} items -> {sum(n.values())} variants", dict(n))


def preds(path):
    for line in list(open(path))[1:]:
        r = json.loads(line)
        if r.get("type") != "choice":
            continue
        probs = {a: b for a, b in r["probs"].items() if not a.startswith("__")}
        top = max(probs, key=probs.get)
        tag = lambda p: next((t.split(":", 1)[1] for t in r["tags"] if t.startswith(p)), None)
        yield {"aid": tag("aid:"), "variant": tag("audit:"), "kind": tag("akind:"), "origin": tag("origin:"), "qid": r["qid"],
               "top": top, "conf": probs[top], "gold": r["gold"]["label"], "ex": r["ex"]}


def word_counter_scores():
    """Per kind: best single-field word-counter accuracy on the synthetic test (first question), trained on our training data."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    def rows(path, train):
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            ex = r.get("example") if train else r
            if not ex or (train and r.get("status") != "ok"):
                continue
            q = ex["questions"][0]
            yield kind_of(ex), ex["state"], ex["answers"].get(q["id"], {}).get("label")
    tr, te = defaultdict(list), defaultdict(list)
    for p in TRAIN:
        for k, s, y in rows(p, True):
            if y is not None and isinstance(s, dict):
                tr[k].append((s, y))
    for p, origin in SOURCES.items():
        if origin == "synthetic":
            for k, s, y in rows(p, False):
                if y is not None and isinstance(s, dict):
                    te[k].append((s, y))
    out = {}
    for k in te:
        if k not in tr:
            continue
        best = (0, None)
        for field in te[k][0][0]:
            txt = lambda s: s[field] if isinstance(s.get(field), str) else json.dumps(s.get(field))
            m = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2), LogisticRegression(max_iter=2000))
            m.fit([txt(s) for s, _ in tr[k][:3000]], [y for _, y in tr[k][:3000]])
            acc = sum(m.predict([txt(s)])[0] == y for s, y in te[k]) / len(te[k])
            best = max(best, (acc, field))
        out[k] = best
    return out


def contrastive(name):
    from collections import defaultdict as dd
    res = {}
    for path in [f"reports/preds_contrastive/{name}.jsonl", f"reports/preds_contrastive2/{name}.jsonl"]:
        if not Path(path).exists():
            continue
        d = dd(dict)
        for line in list(open(path))[1:]:
            r = json.loads(line)
            t = lambda p: next(x for x in r["tags"] if x.startswith(p)).split(":", 1)[1]
            probs = {a: b for a, b in r["probs"].items() if not a.startswith("__")}
            d[(t("probe:"), t("pair:"))][t("side:")] = max(probs, key=probs.get) == r["gold"]["label"]
        for (k, _), v in d.items():
            if len(v) == 2:
                res.setdefault(k, []).append(all(v.values()))
    return {k: (sum(v) / len(v), len(v)) for k, v in res.items()}


def report(a):
    items = [json.loads(l) for l in open(OUT / "audit-items.jsonl", encoding="utf-8")]
    P = list(preds(f"reports/audit/{a.name}-items.jsonl"))
    by = defaultdict(dict)  # (aid, qid) -> variant -> pred
    for p in P:
        by[(p["aid"], p["qid"])][p["variant"]] = p
    kinds = defaultdict(lambda: defaultdict(list))
    wrong = defaultdict(list)
    for (aid, qid), v in by.items():
        o = v.get("orig")
        if not o:
            continue
        K = kinds[(o["kind"], o["origin"])]
        K["acc"].append(o["top"] == o["gold"])
        if o["top"] != o["gold"]:
            K["conf_wrong"].append(o["conf"] >= 0.9)
            wrong[(o["kind"], o["origin"])].append((o["conf"], o["ex"], qid, o["top"], o["gold"]))
        for var, p in v.items():
            if var.startswith("drop:"):
                K[var].append(p["top"] != o["top"])
            elif var in ("reorder", "filler"):
                K[var].append(p["top"] != o["top"])
            elif var == "swap":
                mirror = {"first": "second", "second": "first"}.get(o["top"], o["top"])
                K["swap"].append(p["top"] != mirror)
    wc = word_counter_scores() if not a.no_wc else {}
    con = contrastive(a.contrastive_name) if a.contrastive_name else {}
    rt = redteam_scores(a) if Path(OUT / "redteam.jsonl").exists() and Path(f"reports/audit/{a.name}-redteam.jsonl").exists() else {}
    pct = lambda xs: sum(xs) / len(xs) if xs else None
    lines = [f"# Release audit: {a.name}", "",
             "One row per decision kind and test source. ✅ fine · ⚠️ look at it · ❌ a real problem. Thresholds: reading ⚠️ if dropping a "
             "field changes < 20% of answers; meaningless changes ⚠️ > 10%, ❌ > 20%; test strength ❌ if a word-counter is within 0.05 of "
             "Kodiak, ⚠️ within 0.15; contrastive pairs ❌ < 0.30, ⚠️ < 0.50; red team ❌ > 50% fooled, ⚠️ > 25%; overconfident ⚠️ if > 30% "
             "of mistakes are at ≥ 0.9 confidence.", "",
             "| Kind | Source | n | Accuracy | 1. Reading (answers changed when a field is dropped) | 2. Contrastive pairs | 3. Meaningless changes "
             "(answers moved) | 4. Mistakes at ≥ 0.9 conf | 5. Word-counter (best field) | 6. Red team fooled | Flags |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    flagged = []
    for (k, origin), K in sorted(kinds.items(), key=lambda x: (x[0][1] != "synthetic", x[0][0])):
        acc, flags = pct(K["acc"]), []
        drops = {v[5:]: pct(x) for v, x in K.items() if v.startswith("drop:")}
        for f, c in drops.items():
            if c is not None and c < 0.2:
                flags.append(f"⚠️ barely reads `{f}` ({c:.0%})")
        mm = {v: pct(K[v]) for v in ("reorder", "filler", "swap") if K.get(v)}
        for v, c in mm.items():
            if c > 0.2:
                flags.append(f"❌ {v} moves {c:.0%}")
            elif c > 0.1:
                flags.append(f"⚠️ {v} moves {c:.0%}")
        cw = pct(K["conf_wrong"])
        if cw is not None and cw > 0.3 and len(K["conf_wrong"]) >= 5:
            flags.append(f"⚠️ {cw:.0%} of mistakes very confident")
        w = wc.get(k) if origin == "synthetic" else None
        if w and acc is not None:
            if w[0] >= acc - 0.05:
                flags.append(f"❌ test passable by a word-counter ({w[0]:.2f} on `{w[1]}`)")
            elif w[0] >= acc - 0.15:
                flags.append(f"⚠️ word-counter close ({w[0]:.2f} on `{w[1]}`)")
        c = con.get(k) if origin == "synthetic" else None
        if c:
            flags.append(("❌" if c[0] < 0.3 else "⚠️" if c[0] < 0.5 else "✅") + f" contrastive pairs {c[0]:.2f}")
        r = rt.get(k) if origin == "synthetic" else None
        if r:
            if r[0] > 0.5:
                flags.append(f"❌ red team fools it {r[0]:.0%}")
            elif r[0] > 0.25:
                flags.append(f"⚠️ red team fools it {r[0]:.0%}")
        flags = [x for x in flags if not x.startswith("✅")] or ["✅"]
        if flags != ["✅"]:
            flagged.append((k, origin, flags))
        lines.append(f"| {k} | {origin} | {len(K['acc'])} | {acc:.2f} | " + (", ".join(f"{f} {c:.0%}" for f, c in drops.items()) or "single field")
                     + f" | {f'{c[0]:.2f} ({c[1]} pairs)' if c else '–'} | " + (", ".join(f"{v} {x:.0%}" for v, x in mm.items()) or "–")
                     + f" | {f'{cw:.0%} of {len(K[chr(99)+'onf_wrong'])}' if cw is not None else '–'} | {f'{w[0]:.2f} ({w[1]})' if w else '–'}"
                     + f" | {f'{r[0]:.0%} of {r[1]}' if r else '–'} | {'; '.join(flags)} |")
    lines += ["", "## The most confident mistakes (read these)", ""]
    for (k, origin), ws in sorted(wrong.items()):
        ws.sort(reverse=True)
        lines.append(f"**{k} ({origin})**")
        for conf, ex, qid, top, gold in ws[: a.show]:
            st = items_by_ex(items, ex)
            lines.append(f"- {conf:.2f} said `{top}`, answer `{gold}`: " + json.dumps(st, ensure_ascii=False)[:400])
        lines.append("")
    if rt:
        lines += ["## Red team: examples that fooled it", ""]
        for k, (_, _, fooled) in sorted(rt.items()):
            for s in fooled[: a.show]:
                lines.append(f"- **{k}**: {s}")
    Path("reports").mkdir(exist_ok=True)
    Path(f"reports/audit-{a.name}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:len(kinds) + 6]))
    print(f"-> reports/audit-{a.name}.md")


def items_by_ex(items, ex):
    return items[ex]["state"] if ex < len(items) else None


# ---- red team ------------------------------------------------------------------------------------------------------------------------
RT_KINDS = ["step_safety", "refund_eligibility", "policy_violation", "sarcasm", "pairwise_judge", "long_hallucination", "stance"]


def redteam(a):
    import itertools
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from kodiak_s1.data import synth
    from kodiak_s1.data.gen2.__main__ import load_prices
    from kodiak_s1.data.gen2.pipeline import cost
    from kodiak_s1.data.gen2.prompts import verify_prompt
    from kodiak_s1.data.sim.probes import KINDS
    from kodiak_s1.schema import render_state

    writer, checker = "do:deepseek-3.2", "do:openai-gpt-oss-120b"  # not the training writer
    prices, out = load_prices(), OUT / "redteam.jsonl"
    OUT.mkdir(parents=True, exist_ok=True)

    def job(kind, i):
        spec = KINDS[kind]
        rng = random.Random(f"redteam:{kind}:{i}")
        want, lure = rng.choice(list(itertools.permutations(spec["labels"], 2)))
        rec = {"kind": kind, "job": i, "writer": writer, "verifier": checker, "status": "error", "want": want, "lure": lure}
        fields = "\n".join(f"- {k}: {v}" for k, v in {**spec["fields"], **spec["slots"]}.items())
        p = (f"You are red-teaming a small classifier that may rely on shallow cues: keywords, which option's words appear in the text, "
             f"tone, length, or the position of things. Write ONE realistic example for this decision task. Fields:\n{fields}\n\n"
             f"Question: {spec['question']}\nOptions: {'; '.join(spec['labels'].values())}.\n\nThe correct answer must clearly be "
             f"'{spec['labels'][want]}' for a careful reader, but the surface cues should point to '{spec['labels'][lure]}'. Also give "
             "one sentence naming the trap. Use single quotes inside text. Return JSON only: {fields..., \"trap\": \"...\"}.")
        try:
            sch = {"type": "object", "properties": {k: {"type": "string"} for k in [*spec["fields"], *spec["slots"], "trap"]},
                   "required": [*spec["fields"], *spec["slots"], "trap"]}
            g = synth.teacher(p, sch, 0.9, writer, 1500)
            rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"))
            c = {k: str(v).strip() for k, v in g["content"].items()}
            if not all(c.get(k) for k in [*spec["fields"], *spec["slots"]]):
                rec["status"] = "bad_output"
                return rec
            state = {k: c[k] for k in spec["fields"]}
            q = [{"type": "choice", "id": "decision", "text": spec["question"].format(**{k: c[k] for k in spec["slots"]}),
                  "labels": [{"id": k, "text": t} for k, t in spec["labels"].items()]}]
            v = synth.teacher(verify_prompt(render_state(state), q), synth.verify_schema(q), 0.0, checker, 1500)
            rec.update(verify_tokens=v["tokens"], verify_prompt_tokens=v.get("prompt_tokens"))
            if (synth.parse_verdict(q[0], v["content"].get("decision")) or {}).get("label") != want:
                rec["status"] = "checker_disagrees"
                return rec
            rec.update(status="ok", trap=c.get("trap", ""), example={
                "state": state, "questions": q, "answers": {"decision": {"label": want}},
                "meta": {"source": "kodiak_redteam", "split": "test", "license": "Apache-2.0", "teacher": f"{writer} (checked by {checker})",
                         "tags": ["eval:redteam", f"probe:{kind}", f"rt:{i}"]}})
        except OSError as e:
            rec.update(status="retry", error=str(e)[:200])
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            rec["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        return rec

    lock, spent = threading.Lock(), {"usd": 0.0}

    def work(kj):
        with lock:
            if spent["usd"] >= a.max_usd:
                return
        rec = job(*kj)
        with lock:
            spent["usd"] += cost(rec, prices)
            with out.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with ThreadPoolExecutor(12) as ex:
        list(ex.map(work, [(k, i) for i in range(a.per_kind) for k in RT_KINDS]))
    recs = [json.loads(l) for l in out.open()]
    with open(OUT / "redteam-items.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            if r["status"] == "ok":
                f.write(json.dumps(r["example"], ensure_ascii=False) + "\n")
    print(Counter((r["kind"], r["status"]) for r in recs), f"${spent['usd']:.2f}")


def redteam_scores(a):
    traps = {}
    for l in open(OUT / "redteam.jsonl"):
        r = json.loads(l)
        if r["status"] == "ok":
            traps[f"{r['kind']}:{r['job']}"] = r["trap"]
    res = defaultdict(list)
    for line in list(open(f"reports/audit/{a.name}-redteam.jsonl"))[1:]:
        r = json.loads(line)
        k = next(t for t in r["tags"] if t.startswith("probe:"))[6:]
        i = next(t for t in r["tags"] if t.startswith("rt:"))[3:]
        probs = {x: y for x, y in r["probs"].items() if not x.startswith("__")}
        top = max(probs, key=probs.get)
        res[k].append((top != r["gold"]["label"], f"said `{top}` at {probs[top]:.2f}, answer `{r['gold']['label']}`; trap: {traps.get(f'{k}:{i}', '')}"))
    return {k: (sum(f for f, _ in v) / len(v), len(v), [s for f, s in v if f]) for k, v in res.items()}


ap = argparse.ArgumentParser()
sub = ap.add_subparsers(dest="cmd", required=True)
sub.add_parser("build")
r = sub.add_parser("report")
r.add_argument("--name", required=True)
r.add_argument("--contrastive-name", default="")
r.add_argument("--show", type=int, default=3)
r.add_argument("--no-wc", action="store_true")
t = sub.add_parser("redteam")
t.add_argument("--per-kind", type=int, default=40)
t.add_argument("--max-usd", type=float, default=2.0)
a = ap.parse_args()
{"build": build, "report": report, "redteam": redteam}[a.cmd](a)
