"""Label-word-overlap probe (GENERATOR_V2 §16): the demo ticket found by a user, reworded. A model that reads meaning gives similar answers
whatever the wording; one that matches words jumps to "cancel and refund" whenever those words appear.

    uv run python scripts/probe_label_overlap.py runs/b-small-s1-B-v2 runs/b-small-s1-simret-s0 ...   (run dirs or model folders)
"""
import json
import sys
from pathlib import Path

BASE = ("Hi, I ordered the walnut desk (order #A-5521) two weeks ago. Tracking has said 'label created' for 10 days. "
        "I need it before my new job starts on Monday. ")
EXPEDITE, REFUND = "delivery status or expedite", "cancel and refund"
PROBES = [  # (last sentence(s), the better answer)
    ("If it can't arrive by then, please cancel and refund me.", EXPEDITE),        # demo default: conditional refund
    ("If it can't arrive by then, please give me my money back.", EXPEDITE),       # David's rewording
    ("If it can't arrive by then, please cancel my order and refund me.", EXPEDITE),
    ("If it can't arrive by then, I'd like a refund instead.", EXPEDITE),
    ("I do NOT want to cancel or get a refund, I just need it here by Monday.", EXPEDITE),  # trap: label words, negated
    ("Honestly I've given up on it. Please just give me my money back.", REFUND),   # unconditional, no label words
    ("Forget it. Cancel the order and refund me today.", REFUND),                   # unconditional, label words
    ("Can you tell me where it actually is and whether it will make it?", EXPEDITE),
]
Q = [{"type": "choice", "id": "intent", "text": "What does the customer want?",
      "labels": [EXPEDITE, REFUND, "product question", "complaint about staff"]}]


def load(path: str):
    from kodiak_s1.hub import Kodiak

    p = Path(path)
    if (p / "model.safetensors").exists():
        return Kodiak.from_pretrained(str(p))
    from kodiak_s1.infer import load as load_ckpt

    ckpt = sorted((p / "checkpoints").glob("step_*.pt"))[-1]
    cal = json.loads((p / "calibration-final-thr.json").read_text()) if (p / "calibration-final-thr.json").exists() else {}
    return Kodiak(load_ckpt(ckpt), cal, name=p.name)


def probe(path: str) -> dict:
    k = load(path)
    rows = []
    for sent, want in PROBES:
        p = k.decide(BASE + sent, Q, null_threshold=1.0)["intent"]["probs"]
        rows.append({"sentence": sent, "want": want, "p_want": round(p[want], 3), "top": max(p, key=p.get)})
    return {"model": Path(path).name, "correct": sum(r["top"] == r["want"] for r in rows), "mean_p_want": round(sum(r["p_want"] for r in rows) / len(rows), 3),
            "rows": rows}


if __name__ == "__main__":
    results = [probe(p) for p in sys.argv[1:]]
    print(f"| model | right (of {len(PROBES)}) | mean p(right) |\n|---|---|---|")
    for r in results:
        print(f"| {r['model']} | {r['correct']} | {r['mean_p_want']:.2f} |")
    print("\n| sentence | better answer | " + " | ".join(r["model"] for r in results) + " |\n|---|---|" + "---|" * len(results))
    for i, (sent, want) in enumerate(PROBES):
        print(f"| {sent} | {want} | " + " | ".join(f"{r['rows'][i]['p_want']:.2f}" for r in results) + " |")
