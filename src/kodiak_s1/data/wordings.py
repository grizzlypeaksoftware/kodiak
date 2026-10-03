"""E18: alternative wordings for answer options (same meaning, different words), written by the open-weight writer and blind-checked.

For each task with a fixed label vocabulary (the labels recur across examples; one-off multiple-choice options are skipped), the writer gives
every label two rewordings: a one-sentence `description` and a short `paraphrase`. The checker then sees the original labels and all the
rewordings shuffled, and must map each rewording back to its label; a rewording is kept only if it maps to the right one.

    uv run python -m kodiak_s1.data.wordings --split train --out data/wordings/train.json   # training tasks + skills labels
    uv run python -m kodiak_s1.data.wordings --split eval  --out data/wordings/eval.json    # never-seen eval tasks only (never trained on)
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import string
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WRITER, CHECKER = "do:openai-gpt-oss-120b", "do:deepseek-3.2"
STYLES = ("description", "paraphrase")
CHUNK = 20
SKILLS = "data/synthetic/skills_v1_e17_10k.jsonl"
EVAL = "data/eval/kodiak-eval-v0.2.jsonl"
# Options that recur but are names, not meanings (people in WinoGrande sentences, function names): rewording them makes no sense.
ENTITY_OPTIONS = {"winogrande", "glaive_fc_v2", "toolace", "commonsense_qa", "openbookqa"}


def _norm(t: str) -> str:
    return re.sub(r"\W+", " ", t.lower()).strip()


def vocab(examples: list[dict], min_count: int, min_coverage: float = 0.8) -> tuple[list[list[str]], list[str]] | None:
    """The recurring label texts of one task, grouped into the option sets they are asked in, plus a few sample question texts; None if the
    options are mostly one-off. Labels that only appear together in one question are written and checked together, so synonyms from
    different question formats (MNLI's 'yes' / 'true' / 'supported by the text') never sit side by side."""
    texts, sets, questions = Counter(), Counter(), []
    for ex in examples:
        for q in ex["questions"]:
            if q.get("type") == "choice":
                labs = [lab["text"] for lab in q["labels"]]
                texts.update(labs)
                sets[tuple(sorted(labs))] += 1
                if len(questions) < 3 and q["text"] not in questions:
                    questions.append(q["text"])
    total = sum(texts.values())
    keep = sorted(t for t, n in texts.items() if n >= min_count)
    if not total or sum(texts[t] for t in keep) / total < min_coverage:
        return None
    n_q = sum(sets.values())
    fixed = [list(k) for k, n in sets.items() if n >= min_count]
    if len(fixed) > 8 or sum(sets[tuple(k)] for k in fixed) < 0.2 * n_q:
        fixed = []  # options are subsets sampled from one large label list (intents, emotions): batch the list instead
    in_fixed = {t for k in fixed for t in k}
    rest = [t for t in keep if t not in in_fixed]
    return fixed + [rest[i:i + CHUNK] for i in range(0, len(rest), CHUNK)], questions


def collect(split: str) -> dict[str, tuple[list[list[str]], list[str]]]:
    from kodiak_s1.data.sources import SOURCES

    out = {}
    if split == "train":
        for sid, src in SOURCES.items():
            p = Path("data/processed") / sid / "train.jsonl.gz"
            if src.heldout or not p.exists() or sid in ENTITY_OPTIONS:
                continue
            with gzip.open(p, "rt", encoding="utf-8") as f:
                exs = [json.loads(line) for _, line in zip(range(20000), f)]
            v = vocab(exs, min_count=5)
            if v:
                out[sid] = v
        from kodiak_s1.data.sim.skills import ASK, CLAIM, DIRECT, ESCI, GROUND

        # The skills' fixed answer sets only (tool names, parameter values and yes/no are per-example or generic).
        groups = [list(GROUND.values()), list(CLAIM.values()), list(ESCI.values()), [ASK, DIRECT]]
        out["kodiak_synth_v1"] = (groups, ["Is every claim in the response supported by the source?", "Does the text support the claim?",
                                           "How relevant is this product to the shopper's search?", "What should the assistant do next?"])
    else:
        by = defaultdict(list)
        for line in open(EVAL, encoding="utf-8"):
            ex = json.loads(line)
            if "eval:heldout" in ex["meta"]["tags"]:
                by[ex["meta"]["source"]].append(ex)
        for sid, exs in by.items():
            v = vocab(exs, min_count=3)
            if v:
                out[sid] = v
    return out


def write_prompt(questions: list[str], labels: list[str]) -> str:
    qs = "\n".join(f"- {q[:300]}" for q in questions)
    opts = "\n".join(f"o{i}: {t}" for i, t in enumerate(labels))
    return ("A decision task asks questions like these:\n" + qs + "\n\nIts answer options include:\n" + opts + "\n\nFor every option, write two "
            "alternative wordings that mean exactly the same thing in this task: `description`, one plain statement of 8 to 20 words "
            "saying what is true when this option is the right answer (for example 'The text shows the claim is false.'), not an "
            "instruction or an action, and keeping any yes/no the option starts with; and `paraphrase`, 1 to 5 words that use different words from the original where "
            "possible. Each wording must still be clearly different from every other option. Don't mention other options, don't add "
            "conditions, and don't change the meaning. Use single quotes inside text, never double quotes. Return JSON only.")


def write_schema(n: int) -> dict:
    item = {"type": "object", "properties": {"id": {"type": "string"}, "description": {"type": "string"}, "paraphrase": {"type": "string"}},
            "required": ["id", "description", "paraphrase"]}
    return {"type": "object", "properties": {"options": {"type": "array", "items": item, "minItems": n, "maxItems": n}}, "required": ["options"]}


def check_prompt(questions: list[str], labels: list[str], alts: list[tuple[str, str]]) -> str:
    qs = "\n".join(f"- {q[:300]}" for q in questions)
    opts = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(labels))
    rew = "\n".join(f"{code}: {text}" for code, text in alts)
    return ("A decision task asks questions like these:\n" + qs + "\n\nIts answer options:\n" + opts + "\n\nEach line below rewords exactly "
            "one of those options. For each code, give the number of the option it means. If a line could mean more than one option, or "
            "none, give 0.\n\n" + rew + "\n\nReturn JSON only: an object mapping every code to a number.")


def check_schema(codes: list[str]) -> dict:
    return {"type": "object", "properties": {c: {"type": "integer"} for c in codes}, "required": codes}


def run_chunk(sid: str, questions: list[str], labels: list[str], seed: int) -> dict:
    from kodiak_s1.data import synth

    rec = {"source": sid, "labels": labels, "writer": WRITER, "verifier": CHECKER, "status": "error"}
    try:
        g = synth.teacher(write_prompt(questions, labels), write_schema(len(labels)), 0.9, WRITER, 300 + 90 * len(labels))
        rec.update(gen_tokens=g["tokens"], gen_prompt_tokens=g.get("prompt_tokens"))
        got = {o["id"]: o for o in g["content"]["options"]}
        rng = random.Random(f"{seed}:{sid}:{labels[0]}")
        alts, truth = [], {}
        for i, t in enumerate(labels):
            o = got.get(f"o{i}") or {}
            for style in STYLES:
                text = re.sub(r"^\s*o\d+\s*[:.)-]\s*", "", (o.get(style) or "")).strip()  # writer sometimes echoes the option id
                if text and _norm(text) != _norm(t):
                    alts.append((style, i, text))
        rng.shuffle(alts)
        codes = ["".join(rng.choices(string.ascii_uppercase, k=3)) + str(k) for k in range(len(alts))]
        for code, (style, i, text) in zip(codes, alts):
            truth[code] = (style, i, text)
        v = synth.teacher(check_prompt(questions, labels, [(c, truth[c][2]) for c in codes]), check_schema(codes), 0.0, CHECKER,
                          200 + 12 * len(codes))
        rec.update(verify_tokens=v["tokens"], verify_prompt_tokens=v.get("prompt_tokens"))
        out = defaultdict(dict)
        for code, (style, i, text) in truth.items():
            if v["content"].get(code) == i + 1:
                out[labels[i]][style] = text
        rec.update(status="ok", wordings=dict(out), offered=len(alts), kept=sum(len(x) for x in out.values()))
    except OSError as e:
        rec.update(status="retry", error=str(e)[:300])
    except (ValueError, KeyError, TypeError) as e:
        rec["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    return rec


def main(argv: list[str] | None = None) -> None:
    from kodiak_s1.data.gen2.__main__ import load_prices
    from kodiak_s1.data.gen2.pipeline import cost

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", choices=["train", "eval"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=18)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--max-usd", type=float, default=3.0)
    ap.add_argument("--only", default="", help="comma-separated sources (pilot)")
    ap.add_argument("--fill", action="store_true", help="keep the existing --out table; rerun only tasks with labels missing a style, merge")
    a = ap.parse_args(argv)
    tasks = collect(a.split)
    if a.only:
        tasks = {k: v for k, v in tasks.items() if k in a.only.split(",")}
    old = json.loads(Path(a.out).read_text()) if a.fill and Path(a.out).exists() else {"table": {}, "usd": 0.0}
    if a.fill:  # only the option groups that still have a label without both styles
        tasks = {sid: ([g for g in groups if any(len(old["table"].get(sid, {}).get(t, {})) < 2 for t in g)], qs)
                 for sid, (groups, qs) in tasks.items()}
        tasks = {k: v for k, v in tasks.items() if v[0]}
    jobs = [(sid, qs, group) for sid, (groups, qs) in tasks.items() for group in groups]
    n_lab = len({(sid, t) for sid, (groups, _) in tasks.items() for g in groups for t in g})
    print(f"{len(tasks)} tasks, {n_lab} labels, {len(jobs)} writer calls: "
          + ", ".join(f"{k} {sum(map(len, v[0]))}" for k, v in tasks.items()), flush=True)
    prices, spent, recs = load_prices(), 0.0, []
    for attempt in range(4):
        todo = [j for j in jobs if not any(r["source"] == j[0] and r["labels"] == j[2] and r["status"] == "ok" for r in recs)]
        if not todo or spent >= a.max_usd:
            break
        with ThreadPoolExecutor(a.workers) as ex:
            new = list(ex.map(lambda j: run_chunk(j[0], j[1], j[2], a.seed), todo))
        spent += sum(cost(r, prices) for r in new)
        recs += new
        print(f"pass {attempt + 1}: " + str(Counter(r["status"] for r in new)) + f", ${spent:.3f}", flush=True)
        if any(r["status"] == "retry" for r in new):
            time.sleep(20)
    table = defaultdict(dict, {k: dict(v) for k, v in old["table"].items()})  # source -> label -> {style: text}; keeps the most complete
    for r in recs:
        if r["status"] == "ok":
            for lab, w in r["wordings"].items():
                if len(w) > len(table[r["source"]].get(lab, {})):
                    table[r["source"]][lab] = w
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    spent += old.get("usd", 0.0)
    out.write_text(json.dumps({"split": a.split, "seed": a.seed, "writer": WRITER, "checker": CHECKER, "usd": round(spent, 4),
                               "table": table}, ensure_ascii=False, indent=1))
    full = sum(1 for s in table.values() for w in s.values() if len(w) == 2)
    print(f"done: {sum(len(v) for v in table.values())} of {n_lab} labels reworded ({full} with both styles), ${spent:.3f} -> {out}")
    with out.with_suffix(".log.jsonl").open("a" if a.fill else "w") as f:
        f.write("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n")


if __name__ == "__main__":
    main()


def reword(ex: dict, table: dict[str, dict[str, str]], rng: random.Random) -> dict:
    """Training-time augmentation (E18): swap every option of each choice question for one rewording style (the same style for the whole
    question), when every option has it. Option ids and answers are unchanged, so the gold answer is the same by construction."""
    style = rng.choice(STYLES)
    for q in ex["questions"]:
        if q.get("type") != "choice" or not q.get("labels"):
            continue
        alts = [table.get(lab["text"], {}).get(style) for lab in q["labels"]]
        if all(alts):
            for lab, alt in zip(q["labels"], alts):
                lab["text"] = alt
    return ex
