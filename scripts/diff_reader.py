"""Diff reader (D70, after outside feedback): a word-counter that sees ONLY the words that differ between versions of the same case.
If it does well, the test (or the training data) can be passed by the cue words a writer uses to signal an answer ("but" → ask first),
without reading the rest. Leave-one-pair-out on the contrastive tests; grouped 5-fold on contrast-group training data.

    uv run python scripts/diff_reader.py
"""
import json
import re
from collections import Counter, defaultdict

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression

VARY = {"step_safety": "task", "refund_eligibility": "request"}
words = lambda s: set(re.findall(r"[a-z']+", s.lower()))


def test_pairs(path, kind):
    sides = defaultdict(dict)
    for line in open(path):
        e = json.loads(line)
        t = lambda p: next(x for x in e["meta"]["tags"] if x.startswith(p)).split(":", 1)[1]
        if t("probe:") == kind:
            sides[t("pair:")][t("side:")] = (e["state"], e["answers"]["decision"]["label"])
    out = []
    for pid, s in sides.items():
        if len(s) == 2:
            (sa, la), (sb, lb) = s["a"], s["b"]
            fa, fb = words(sa[VARY[kind]]), words(sb[VARY[kind]])
            out.append((pid, [(" ".join(sorted(fa - fb)), la), (" ".join(sorted(fb - fa)), lb)]))
    return out


def reader(train_docs, train_y):
    vec = CountVectorizer(binary=True, token_pattern=r"[a-z']+")
    return vec, LogisticRegression(max_iter=2000, C=1.0).fit(vec.fit_transform(train_docs), train_y)


def leave_one_pair_out(pairs):
    right = {}
    for i, (pid, sides) in enumerate(pairs):
        tr = [s for j, (_, ss) in enumerate(pairs) if j != i for s in ss]
        vec, m = reader([d for d, _ in tr], [y for _, y in tr])
        right[pid] = all(m.predict(vec.transform([d]))[0] == y for d, y in sides)
    return right


def group_diffs(path, kind):
    """Each kept example's changed field, reduced to the words no other version in its group has."""
    out = []
    for line in open(path):
        r = json.loads(line)
        if r.get("status") != "ok" or r["kind"] != kind:
            continue
        ex = r["examples"]
        anchor = r["anchor"]
        other = next(f for f in ex[0]["state"] if f != anchor)
        ws = [words(e["state"][other]) for e in ex]
        for i, e in enumerate(ex):
            rest = set().union(*[w for j, w in enumerate(ws) if j != i])
            out.append((r["job"], anchor, " ".join(sorted(ws[i] - rest)), e["answers"]["decision"]["label"]))
    return out


if __name__ == "__main__":
    print("== Contrastive tests: reader on the changed words only (leave-one-pair-out)")
    for v in ["v0.1", "v0.2"]:
        for kind in VARY:
            pairs = test_pairs(f"data/eval/kodiak-contrastive-{v}.jsonl", kind)
            r = leave_one_pair_out(pairs)
            print(f"  {v} {kind:20s} {sum(r.values())} of {len(r)} pairs")
            json.dump(r, open(f"/tmp/diffreader-{v}-{kind}.json", "w"))
    print("\n== Cue words in the contrast-group TRAINING data (word only in one version of its group → that version's label)")
    for kind in VARY:
        rows = group_diffs("data/synthetic/groups_v1.jsonl", kind)
        c = defaultdict(Counter)
        for _, _, d, y in rows:
            for w in d.split():
                c[w][y] += 1
        top = sorted(c.items(), key=lambda x: -sum(x[1].values()))[:15]
        print(f"  {kind}: " + "; ".join(f"{w} {sum(n.values())} ({n.most_common(1)[0][0]} {n.most_common(1)[0][1] / sum(n.values()):.0%})" for w, n in top))
        # grouped 5-fold: does a reader on the unique words predict the label?
        jobs = sorted({j for j, *_ in rows})
        acc = []
        for f in range(5):
            test = set(jobs[f::5])
            tr = [(d, y) for j, _, d, y in rows if j not in test]
            te = [(d, y) for j, _, d, y in rows if j in test]
            vec, m = reader([d for d, _ in tr], [y for _, y in tr])
            acc.append(sum(m.predict(vec.transform([d]))[0] == y for d, y in te) / len(te))
        lab = Counter(y for *_, y in rows)
        print(f"  {kind}: reader on unique words, grouped 5-fold: {sum(acc) / 5:.2f} (majority {max(lab.values()) / len(rows):.2f}; labels {dict(lab)})")
