"""Fine-tune Kodiak on your own labeled examples (the v0.2 fine-tuning kit, D45).

    uv run python -m kodiak_s1.finetune --csv tickets.csv --text-column text --label-column team \\
        --question "Which team should handle this ticket?" --base cortex-agent-llc/kodiak-small-v2-preview --out my-kodiak

What it does, in order:
1. Reads your CSV: one text column, one label column (every distinct label becomes an answer option).
2. Holds back 20% of the rows as a test set it never trains on, and measures the base model on it (how Kodiak does out of the box).
3. Fine-tunes the base model on the rest (a small slice is kept aside for calibration).
4. Recalibrates the confidence and the "can't tell" threshold on your data, so the percentages stay trustworthy.
5. Measures again on the held-back rows and writes a before/after report, then saves a normal Kodiak model folder
   (works with Kodiak.from_pretrained, the Node server and the ONNX export).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import torch

from kodiak_s1.eval.run import fit_calibration, fit_null_threshold
from kodiak_s1.hub import Kodiak, apply_calibration
from kodiak_s1.infer import raw_outputs
from kodiak_s1.model import decision_loss
from kodiak_s1.packing import Limits, collate, pack_example

IDENTITY = {"t_choice": 1.0, "t_null": 1.0, "kappa_scale": 1.0}


def read_rows(path: str, text_col: str, label_col: str) -> list[tuple[str, str]]:
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        rows = [(r.get(text_col, "").strip(), r.get(label_col, "").strip()) for r in csv.DictReader(f)]
    return [(t, lab) for t, lab in rows if t and lab]


def to_examples(rows, question: str, labels: list[str]) -> list[dict]:
    q = {"type": "choice", "id": "label", "text": question, "labels": [{"id": lab, "text": lab} for lab in labels], "allow_null": True}
    return [{"state": t, "questions": [q], "answers": {"label": {"label": lab}},
             "meta": {"source": "user", "license": "user", "split": "train", "tags": []}} for t, lab in rows]


def evaluate(model, exs: list[dict], threshold: float) -> dict:
    """Accuracy when forced to pick, accuracy with abstention, how often it abstains, and calibration error (ECE, 10 bins)."""
    raws = raw_outputs(model, exs)
    forced = answered = right_answered = 0
    confs, hits = [], []
    for ex, rs in zip(exs, raws):
        r = rs[0]
        gold = ex["answers"]["label"]["label"]
        probs = dict(zip(r["labels"], r["cond_probs"]))
        top = max(probs, key=probs.get)
        forced += top == gold
        p_top = (1 - r["p_null"]) * probs[top]
        confs.append(p_top)
        hits.append(top == gold)
        if r["p_null"] < threshold:
            answered += 1
            right_answered += top == gold
    n = len(exs)
    bins = np.linspace(0, 1, 11)
    ece = 0.0
    c, h = np.array(confs), np.array(hits, dtype=float)
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (c > lo) & (c <= hi)
        if m.any():
            ece += m.mean() * abs(c[m].mean() - h[m].mean())
    return {"n": n, "forced_accuracy": round(forced / n, 4), "answered_share": round(answered / n, 4),
            "accuracy_when_answering": round(right_answered / max(1, answered), 4), "ece": round(float(ece), 4)}


def finetune(a) -> dict:
    rows = read_rows(a.csv, a.text_column, a.label_column)
    labels = sorted({lab for _, lab in rows})
    if len(labels) < 2 or len(rows) < 20:
        raise SystemExit(f"need at least 20 rows and 2 labels (found {len(rows)} rows, {len(labels)} labels)")
    random.Random(a.seed).shuffle(rows)
    n_test = max(10, int(len(rows) * a.test_share))
    test, rest = to_examples(rows[:n_test], a.question, labels), to_examples(rows[n_test:], a.question, labels)
    n_cal = max(10, int(len(rest) * 0.1))
    cal_set, train = rest[:n_cal], rest[n_cal:]
    print(f"{len(rows)} rows, {len(labels)} labels: {len(train)} train / {len(cal_set)} calibration / {len(test)} test (held back)")

    base = Kodiak.from_pretrained(a.base, device=a.device)
    model = base.model
    before = evaluate(model, test, base.default_options["null_threshold"])
    print("before (base model, out of the box):", before)

    apply_calibration(model, IDENTITY)  # train on raw logits; recalibrate afterwards
    model.train()
    enc = [p for n, p in model.named_parameters() if n.startswith("encoder.")]
    head = [p for n, p in model.named_parameters() if not n.startswith("encoder.")]
    opt = torch.optim.AdamW([{"params": enc, "lr": a.lr}, {"params": head, "lr": a.lr * 10}], weight_decay=0.01)
    packed = [pack_example(ex, Limits(max_state=a.max_state), with_targets=True) for ex in train]
    device = next(model.parameters()).device
    steps_per_epoch = math.ceil(len(packed) / a.batch)
    total, step, t0 = steps_per_epoch * a.epochs, 0, time.time()
    rng = random.Random(a.seed)
    for epoch in range(a.epochs):
        order = list(range(len(packed)))
        rng.shuffle(order)
        for i in range(0, len(order), a.batch):
            b = collate([packed[k] for k in order[i:i + a.batch]], 4096).to(device)
            lr_scale = min(1.0, (step + 1) / max(1, total // 10)) * max(0.0, 1 - step / total)  # warmup 10%, linear decay
            for g, base_lr in zip(opt.param_groups, (a.lr, a.lr * 10)):
                g["lr"] = base_lr * lr_scale
            with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
                out = model(b, impl="sdpa")
            loss, stats = decision_loss(out, b)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            step += 1
            if step % max(1, total // 10) == 0 or step == total:
                print(f"  step {step}/{total} (epoch {epoch + 1}) loss {stats['loss']:.3f} acc {stats['choice_acc']:.3f} "
                      f"{time.time() - t0:.0f}s", flush=True)
    model.eval()

    # Recalibrate on the calibration slice (never the test rows).
    raws = raw_outputs(model, cal_set)
    pairs = [(r, q, ex["answers"][q["id"]]) for ex, rs in zip(cal_set, raws) for r, q in zip(rs, ex["questions"])]
    cal = fit_calibration(pairs)
    cal.update(fit_null_threshold(pairs, cal))
    cal["fit_on"] = f"fine-tuning calibration slice, {len(cal_set)} rows"
    tuned = Kodiak(model, cal, name=Path(a.out).name)
    after = evaluate(tuned.model, test, tuned.default_options["null_threshold"])
    print("after (fine-tuned):", after)

    out = tuned.save_pretrained(a.out)
    report = {"base": a.base, "csv": a.csv, "question": a.question, "labels": labels, "rows": len(rows),
              "train": len(train), "calibration": len(cal_set), "test": len(test), "epochs": a.epochs, "lr": a.lr,
              "before": before, "after": after, "seconds": round(time.time() - t0)}
    (out / "finetune_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--text-column", default="text")
    ap.add_argument("--label-column", default="label")
    ap.add_argument("--question", required=True, help="the question your labels answer, e.g. 'Which team should handle this?'")
    ap.add_argument("--base", default="cortex-agent-llc/kodiak-small-v2-preview")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch", type=int, default=16, help="examples per step")
    ap.add_argument("--test-share", type=float, default=0.2)
    ap.add_argument("--max-state", type=int, default=512)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="auto")
    a = ap.parse_args(argv)
    r = finetune(a)
    print(f"\nsaved to {a.out}: forced accuracy {r['before']['forced_accuracy']:.1%} → {r['after']['forced_accuracy']:.1%} "
          f"on {r['test']} held-back rows (report: {a.out}/finetune_report.json)")


if __name__ == "__main__":
    main()
