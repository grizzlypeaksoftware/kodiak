"""Word-counter shortcut check (D67 follow-up). A bag-of-words logistic regression, trained in seconds, that sees only ONE field of each
example. If it predicts the training labels well, the data teaches a shortcut; if it scores near the model on a test, that test can't prove
a skill. Run it on every pilot before buying a batch, and on every new skill test. Free (CPU only).

    uv run python scripts/shortcut_check.py --train data/synthetic/skills3_v1_e22_10k.jsonl [--test eval.jsonl ...]
"""
import argparse
import json
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline


def load(path):
    d = defaultdict(list)
    for line in open(path):
        r = json.loads(line)
        if "example" in r:  # raw generator record
            if r.get("status") != "ok":
                continue
            kind, ex = r["kind"], r["example"]
        else:  # eval file
            ex = r
            kind = next(t for t in ex["meta"]["tags"] if t.startswith("probe:"))[6:]
        d[kind].append((ex["state"], ex["answers"]["decision"]["label"], ex["meta"].get("tags", [])))
    return d


def text(state, field):
    return " ".join(map(str, state.values())) if field == "ALL" else str(state.get(field, ""))


def word_counter():
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2), LogisticRegression(max_iter=2000))


ap = argparse.ArgumentParser()
ap.add_argument("--train", nargs="+", required=True)
ap.add_argument("--test", nargs="*", default=[])
ap.add_argument("--max", type=int, default=3000)
a = ap.parse_args()
train = defaultdict(list)
for p in a.train:
    for k, v in load(p).items():
        train[k] += v
tests = {p: load(p) for p in a.test}
for kind, rows in sorted(train.items()):
    rows = rows[: a.max]
    y = [l for _, l, _ in rows]
    print(f"{kind}  n={len(rows)}  majority={max(y.count(c) for c in set(y)) / len(y):.2f}")
    for field in list(rows[0][0]) + ["ALL"]:
        X = [text(s, field) for s, _, _ in rows]
        line = f"  [{field}] train (5-fold) {cross_val_score(word_counter(), X, y, cv=5).mean():.2f}"
        m = word_counter().fit(X, y)
        for p, d in tests.items():
            t = d.get(kind)
            if not t:
                continue
            right = {i: m.predict([text(s, field)])[0] == lab for i, (s, lab, _) in enumerate(t)}
            line += f" | {p.split('/')[-1]}: {sum(right.values()) / len(t):.2f}"
            pair = defaultdict(list)
            for i, (_, _, tags) in enumerate(t):
                pid = next((g for g in tags if g.startswith("pair:")), None)
                if pid:
                    pair[pid].append(right[i])
            if pair:
                line += f" (pair acc {sum(all(v) for v in pair.values()) / len(pair):.2f})"
        print(line)
