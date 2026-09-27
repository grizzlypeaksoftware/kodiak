"""Generator v2.1: student screen and selection (hard-example mining, GENERATOR_V2 §3.6).

A Kodiak model (the "student") answers every kept example. A question is **hard** when the student gets it wrong or is unsure:
  choice   top answer isn't the gold label (abstaining counts as wrong), or its probability < 0.6
  null     the student doesn't abstain, or p(null) < 0.6
  score    the student abstains, or its mean is more than 0.2 of the range away from the gold value
An example is hard if any of its questions is. Selection keeps every hard example plus a quota of easy ones per spec cell (default 30%),
so the data doesn't drift entirely to edge cases. A random selection of the same size is the control for the ablation.

    uv run python -m kodiak_s1.data.gen2 screen --in data/synthetic/gen2_v20.jsonl --student runs/b-small-s1-R1-cap3 \\
        --out data/synthetic/screen_v20_R1.jsonl
    uv run python -m kodiak_s1.data.gen2 select --in data/synthetic/screen_v20_R1.jsonl --out data/synthetic/gen2_v21_mined.jsonl
    uv run python -m kodiak_s1.data.gen2 select --in data/synthetic/screen_v20_R1.jsonl --random --out data/synthetic/gen2_v21_random.jsonl
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

HARD_CONF = 0.6
SCORE_TOL = 0.2


def _student(run: str):
    from kodiak_s1.infer import load

    run = Path(run)
    ckpt = sorted((run / "checkpoints").glob("step_*.pt"))[-1] if (run / "checkpoints").exists() else run
    cal_path = run / "calibration-final-thr.json"
    cal = json.loads(cal_path.read_text()) if cal_path.exists() else {}
    return load(ckpt), cal, str(ckpt)


def question_hard(rec: dict) -> bool:
    gold = rec["gold"]
    if gold.get("null"):
        return rec["decision"] is not None or rec["p_null"] < HARD_CONF
    if rec["type"] == "choice":
        return rec["decision"] != gold.get("label") or rec["confidence"] < HARD_CONF
    return rec["decision"] is None or abs(rec["unit_pred"] - rec["unit_gold"]) > SCORE_TOL


def screen(inp: str, student: str, out: str, batch: int = 64) -> dict:
    from kodiak_s1.eval.run import kodiak_records
    from kodiak_s1.infer import raw_outputs

    model, cal, ckpt = _student(student)
    recs = [r for r in (json.loads(line) for line in open(inp, encoding="utf-8")) if r.get("status") == "ok"]
    thr = float(cal.get("null_threshold", 0.5))
    counts = defaultdict(int)
    with open(out, "w", encoding="utf-8") as f:
        for i in range(0, len(recs), batch):
            chunk = recs[i:i + batch]
            exs = [r["example"] for r in chunk]
            raws = raw_outputs(model, [{"state": e["state"], "questions": e["questions"]} for e in exs])
            qrecs = kodiak_records(exs, raws, cal, null_threshold=thr)
            by_ex = defaultdict(list)
            for q in qrecs:
                by_ex[q["ex"]].append(q)
            for k, r in enumerate(chunk):
                hard_q = [q["qid"] for q in by_ex[k] if question_hard(q)]
                r["screen"] = {"student": ckpt, "hard": bool(hard_q), "hard_questions": hard_q, "n_questions": len(by_ex[k])}
                counts["hard" if hard_q else "easy"] += 1
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return dict(counts)


def cell(r: dict) -> str:
    s = r["spec"]
    return f'{s["source"]}|{s["decision"]}|{s["difficulty"]}'


def select(inp: str, out: str, easy_share: float = 0.3, random_control: bool = False, n: int | None = None, seed: int = 0) -> dict:
    """Mined: all hard + `easy_share` of the easy ones per cell. Random: the same number of examples (or `n`), drawn uniformly."""
    recs = [json.loads(line) for line in open(inp, encoding="utf-8")]
    rng = random.Random(seed)
    if random_control:
        mined_n = n if n is not None else len(_mined(recs, easy_share, random.Random(seed)))
        chosen = rng.sample(recs, min(mined_n, len(recs)))
    else:
        chosen = _mined(recs, easy_share, rng)
        if n is not None:
            chosen = chosen[:n]
    chosen.sort(key=lambda r: r["job"])
    with open(out, "w", encoding="utf-8") as f:
        for r in chosen:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {"pool": len(recs), "selected": len(chosen), "hard": sum(r["screen"]["hard"] for r in chosen)}


def _mined(recs: list[dict], easy_share: float, rng: random.Random) -> list[dict]:
    by_cell = defaultdict(list)
    for r in recs:
        by_cell[cell(r)].append(r)
    chosen = []
    for key in sorted(by_cell):
        group = by_cell[key]
        easy = [r for r in group if not r["screen"]["hard"]]
        chosen += [r for r in group if r["screen"]["hard"]]
        chosen += rng.sample(easy, round(easy_share * len(easy)))
    rng.shuffle(chosen)
    return chosen
