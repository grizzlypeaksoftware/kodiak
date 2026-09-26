"""Public dataset registry and converters to the Kodiak `Example` schema.

Each source declares where its data comes from, its license (verified against the
upstream source, see data/LICENSES.md), which of its upstream splits feed our
train/val/test, and a converter that maps one upstream row to zero or more examples.

Converters are deterministic: every random choice uses an RNG seeded from the
source id and the row key, so rebuilding produces identical data.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import random
import re
import urllib.request
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any

Row = dict[str, Any]
Split = str  # "train" | "val" | "test"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def stable_hash(*parts: Any) -> int:
    h = hashlib.sha1("\x1f".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(h[:8], "big")


def rng_for(*parts: Any) -> random.Random:
    return random.Random(stable_hash(*parts))


def hash_split(key: str, val: float = 0.03, test: float = 0.05) -> Split:
    """Assign a row to a split from its content, so duplicates always land together."""
    u = (stable_hash("split", key) % 10_000) / 10_000
    return "test" if u < test else "val" if u < test + val else "train"


_WORD_FIXES = {
    "iot": "smart home", "hue": "lights", "qa": "question", "wemo": "smart plug", "quirky": "chit-chat",
    "lightchange": "light change", "lightdim": "dim lights", "lightup": "brighten lights",
    "lightoff": "lights off", "lighton": "lights on", "createoradd": "create or add",
    "addcontact": "add contact", "querycontact": "query contact", "sendemail": "send email",
    "hue_lightchange": "change light color", "ticket": "ticket", "taxi": "taxi", "dj": "DJ",
}


def pretty(name: str) -> str:
    """Turn a dataset label id like 'iot_hue_lightchange' into readable text."""
    return " ".join(_WORD_FIXES.get(w, w) for w in name.split("_")).strip()


def choice_q(qid: str, text: str, labels: list[tuple[str, str]], allow_null: bool = True) -> dict:
    return {"type": "choice", "id": qid, "text": text,
            "labels": [{"id": i, "text": t} for i, t in labels], "allow_null": allow_null}


def score_q(qid: str, text: str, lo: float, hi: float, lo_label: str | None = None,
            hi_label: str | None = None, step: float | None = None, allow_null: bool = True) -> dict:
    q = {"type": "score", "id": qid, "text": text, "min": lo, "max": hi, "allow_null": allow_null}
    if lo_label:
        q["min_label"] = lo_label
    if hi_label:
        q["max_label"] = hi_label
    if step:
        q["step"] = step
    return q


def sample_labels(rng: random.Random, pool: list[str], gold: str | None, k_min: int, k_max: int) -> list[str]:
    """Pick a candidate subset of size k from `pool` that includes `gold` (if not None)."""
    k = min(rng.randint(k_min, k_max), len(pool))
    others = [p for p in pool if p != gold]
    picked = rng.sample(others, k - (1 if gold is not None else 0))
    if gold is not None:
        picked.append(gold)
    rng.shuffle(picked)
    return picked


YES_NO = [("yes", "yes"), ("no", "no")]


@dataclass
class Source:
    id: str
    family: str
    license: str
    url: str
    # Returns {our_split: iterable of upstream rows}. Rows get "__key" (stable id) added by the loader.
    load: Callable[[], dict[Split, Iterable[Row]]]
    convert: Callable[[Row, Split, random.Random], list[dict]]
    heldout: bool = False  # never trained on; used only for zero-shot eval
    notes: str = ""
    labels: list[str] = field(default_factory=list)  # full label inventory, if the task has one


def _ex(src: str, lic: str, split: Split, state: Any, questions: list[dict], answers: dict,
        tags: list[str] | None = None) -> dict:
    return {"state": state, "questions": questions, "answers": answers,
            "meta": {"source": src, "license": lic, "split": split, "tags": tags or []}}


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


# Upstream splits are often sorted (by label, or by sub-source), and we cap how many rows we take,
# so every loader shuffles with a fixed seed first. Otherwise "the first 50k rows" is a biased sample.
SHUFFLE_SEED = 0


def _hf(path: str, config: str | None, split: str, **kw) -> Iterator[Row]:
    from datasets import load_dataset

    ds = load_dataset(path, config, split=split, **kw).shuffle(seed=SHUFFLE_SEED).flatten_indices()
    for i, row in enumerate(ds):
        row["__key"] = f"{split}:{i}"
        yield row


def _hf_parquet(path: str, file: str) -> Iterator[Row]:
    """Read the Hub's auto-converted parquet for datasets whose loading scripts are no longer supported."""
    import pandas as pd
    from huggingface_hub import hf_hub_download

    df = pd.read_parquet(hf_hub_download(path, file, repo_type="dataset", revision="refs/convert/parquet"))
    df = df.sample(frac=1.0, random_state=SHUFFLE_SEED)
    for i, row in enumerate(df.to_dict("records")):
        row["__key"] = f"{file}:{i}"
        yield row


def _csv_url(url: str) -> Iterator[Row]:
    text = urllib.request.urlopen(url, timeout=60).read().decode()
    rows = list(csv.DictReader(io.StringIO(text)))
    random.Random(SHUFFLE_SEED).shuffle(rows)
    for i, row in enumerate(rows):
        row["__key"] = f"{url.rsplit('/', 1)[-1]}:{i}"
        yield row


def _by_hash(rows: Iterable[Row], key: Callable[[Row], str], want: Split) -> Iterator[Row]:
    return (r for r in rows if hash_split(key(r)) == want)


def _carve(train_path: str, config: str | None, test_split: str, key: Callable[[Row], str]):
    """Upstream train -> our train/val by content hash; an upstream labeled split -> our test."""
    return lambda: {
        "train": (r for r in _hf(train_path, config, "train") if hash_split(key(r), val=0.03, test=0) == "train"),
        "val": (r for r in _hf(train_path, config, "train") if hash_split(key(r), val=0.03, test=0) == "val"),
        "test": _hf(train_path, config, test_split),
    }


# ---------------------------------------------------------------------------
# NLI
# ---------------------------------------------------------------------------

NLI3_LABELS = [("entailment", "supported by the text"), ("contradiction", "contradicted by the text"),
               ("neutral", "neither supported nor contradicted by the text")]
NLI3_Q = ['Is this claim supported by the text: "{h}"', 'How does the text relate to this statement: "{h}"',
          'Given the text, what is the status of the claim "{h}"?']
# Phrased so that "neither" reads as "can't tell from the text" (null), not as "no".
NLI2_Q = ['According to the text, is it true that "{h}"?', 'Based only on the text, is this true or false: {h}',
          'Assuming the text is accurate, is the following true: {h}']
TRUE_FALSE = [("yes", "true"), ("no", "false")]


def _nli(src: str, lic: str, split: Split, rng: random.Random, premise: str, hyp: str, gold: str,
         two_way_null: bool = True) -> list[dict]:
    """Emit either a 3-way NLI question, or a yes/no question where 'neutral' means unanswerable (null)."""
    premise, hyp = premise.strip(), hyp.strip()
    if not premise or not hyp:
        return []
    if rng.random() < 0.5 or not two_way_null:
        q = choice_q("claim", rng.choice(NLI3_Q).format(h=hyp), NLI3_LABELS)
        return [_ex(src, lic, split, premise, [q], {"claim": {"label": gold}}, ["nli3"])]
    q = choice_q("claim", rng.choice(NLI2_Q).format(h=hyp), rng.choice([YES_NO, TRUE_FALSE]))
    if gold == "neutral":
        return [_ex(src, lic, split, premise, [q], {"claim": {"null": True}}, ["nli2", "null:nli_neutral"])]
    return [_ex(src, lic, split, premise, [q], {"claim": {"label": "yes" if gold == "entailment" else "no"}}, ["nli2"])]


def conv_mnli(row, split, rng):
    if row["label"] not in (0, 1, 2) or row["genre"] == "fiction":
        return []  # fiction genre includes CC-BY-SA text; excluded by license policy
    gold = ["entailment", "neutral", "contradiction"][row["label"]]
    return _nli("mnli", "OANC/CC-BY-3.0", split, rng, row["premise"], row["hypothesis"], gold)


def conv_scitail(row, split, rng):
    gold = {"entailment": "entailment", "neutral": "neutral"}.get(row["gold_label"])
    if gold is None:
        return []
    premise, hyp = row["sentence1"].strip(), row["sentence2"].strip()
    if rng.random() < 0.5:
        q = choice_q("claim", rng.choice(NLI3_Q).format(h=hyp),
                     [("entailment", "supported by the text"), ("neutral", "not supported by the text")])
        return [_ex("scitail", "Apache-2.0", split, premise, [q], {"claim": {"label": gold}}, ["nli2way"])]
    return _nli("scitail", "Apache-2.0", split, rng, premise, hyp, gold)


# ---------------------------------------------------------------------------
# Multiple-choice reasoning
# ---------------------------------------------------------------------------

MC_Q = ["Which answer is correct?", "Which option best answers or completes this?", "Pick the best answer."]


def _mc(src, lic, split, rng, state, ids, texts, gold, tags=None):
    if gold not in ids or len(set(t.strip().casefold() for t in texts)) != len(texts):
        return []
    q = choice_q("answer", rng.choice(MC_Q), list(zip(ids, texts)))
    return [_ex(src, lic, split, state, [q], {"answer": {"label": gold}}, tags)]


def conv_csqa(row, split, rng):
    return _mc("commonsense_qa", "MIT", split, rng, row["question"], row["choices"]["label"],
               row["choices"]["text"], row["answerKey"])


def conv_obqa(row, split, rng):
    return _mc("openbookqa", "Apache-2.0", split, rng, row["question_stem"], row["choices"]["label"],
               row["choices"]["text"], row["answerKey"])


def conv_winogrande(row, split, rng):
    if row["answer"] not in ("1", "2"):
        return []
    q = choice_q("referent", rng.choice(["Who or what does the blank (_) refer to?", "What fills in the blank (_)?"]),
                 [("1", row["option1"]), ("2", row["option2"])])
    if q["labels"][0]["text"].casefold() == q["labels"][1]["text"].casefold():
        return []
    return [_ex("winogrande", "Apache-2.0", split, row["sentence"], [q], {"referent": {"label": row["answer"]}})]


# ---------------------------------------------------------------------------
# Intent
# ---------------------------------------------------------------------------

INTENT_Q = ["What does the user want to do?", "Which intent best matches this request?",
            "Classify the user's request.", "What is the user asking for?"]

CLINC_NAMES: list[str] = []  # filled lazily from dataset features


def conv_clinc(row, split, rng):
    names = CLINC_NAMES
    name = names[row["intent"]]
    pool = [n for n in names if n != "oos"]
    if name == "oos":
        cand = sample_labels(rng, pool, None, 4, 24)
        q = choice_q("intent", rng.choice(INTENT_Q), [(c, pretty(c)) for c in cand])
        return [_ex("clinc_oos", "CC-BY-3.0", split, row["text"], [q], {"intent": {"null": True}}, ["null:oos"])]
    cand = sample_labels(rng, pool, name, 4, 24)
    q = choice_q("intent", rng.choice(INTENT_Q), [(c, pretty(c)) for c in cand])
    return [_ex("clinc_oos", "CC-BY-3.0", split, row["text"], [q], {"intent": {"label": name}})]


MASSIVE_SCENARIOS = ['social', 'transport', 'calendar', 'play', 'news', 'datetime', 'recommendation', 'email',
                     'iot', 'general', 'audio', 'lists', 'qa', 'cooking', 'takeaway', 'music', 'alarm', 'weather']
MASSIVE_INTENTS: list[str] = []  # loaded from the upstream script's label list (see load_massive)


def conv_massive(row, split, rng):
    intent, scen = MASSIVE_INTENTS[row["intent"]], MASSIVE_SCENARIOS[row["scenario"]]
    cand = sample_labels(rng, MASSIVE_INTENTS, intent, 6, 24)
    q1 = choice_q("intent", rng.choice(INTENT_Q), [(c, pretty(c)) for c in cand])
    q2 = choice_q("domain", rng.choice(["Which domain does this request belong to?", "What area is this request about?"]),
                  [(s, pretty(s)) for s in MASSIVE_SCENARIOS])
    return [_ex("massive", "CC-BY-4.0", split, row["utt"], [q1, q2],
                {"intent": {"label": intent}, "domain": {"label": scen}}, ["multiq"])]


def load_massive():
    import ast
    from huggingface_hub import hf_hub_download

    src = open(hf_hub_download("AmazonScience/massive", "massive.py", repo_type="dataset")).read()
    m = re.search(r"^_INTENTS\s*=\s*(\[.*?\])", src, re.S | re.M)
    MASSIVE_INTENTS[:] = ast.literal_eval(m.group(1))
    return {s: _hf_parquet("AmazonScience/massive", f"en-US/{u}/0000.parquet")
            for s, u in [("train", "train"), ("val", "validation"), ("test", "test")]}


BANKING_URL = "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/{}.csv"
BANKING_LABELS: list[str] = []


def load_banking():
    rows = list(_csv_url(BANKING_URL.format("test")))
    BANKING_LABELS[:] = sorted({r["category"] for r in _csv_url(BANKING_URL.format("train"))})
    return {"test": rows}


def conv_banking(row, split, rng):
    cand = sample_labels(rng, BANKING_LABELS, row["category"], 6, 24)
    q = choice_q("intent", rng.choice(INTENT_Q), [(c, pretty(c)) for c in cand])
    return [_ex("banking77", "CC-BY-4.0", split, row["text"], [q], {"intent": {"label": row["category"]}}, ["heldout"])]


# ---------------------------------------------------------------------------
# Emotion / sentiment
# ---------------------------------------------------------------------------

GOEMO_NAMES = ['admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring', 'confusion', 'curiosity',
               'desire', 'disappointment', 'disapproval', 'disgust', 'embarrassment', 'excitement', 'fear',
               'gratitude', 'grief', 'joy', 'love', 'nervousness', 'optimism', 'pride', 'realization', 'relief',
               'remorse', 'sadness', 'surprise', 'neutral']
# Sentiment grouping published with GoEmotions (Demszky et al., 2020).
GOEMO_SENTIMENT = {
    **{e: "positive" for e in ["admiration", "amusement", "approval", "caring", "desire", "excitement", "gratitude",
                               "joy", "love", "optimism", "pride", "relief"]},
    **{e: "negative" for e in ["anger", "annoyance", "disappointment", "disapproval", "disgust", "embarrassment",
                               "fear", "grief", "nervousness", "remorse", "sadness"]},
    **{e: "ambiguous" for e in ["confusion", "curiosity", "realization", "surprise"]},
    "neutral": "neutral",
}


def conv_goemotions(row, split, rng):
    if len(row["labels"]) != 1:
        return []  # multi-label rows don't have a single correct choice
    emo = GOEMO_NAMES[row["labels"][0]]
    cand = sample_labels(rng, GOEMO_NAMES, emo, 6, 28)
    q1 = choice_q("emotion", rng.choice(["What emotion does the writer express?", "Which emotion best fits this comment?"]),
                  [(c, c) for c in cand])
    q2 = choice_q("sentiment", rng.choice(["What is the overall sentiment?", "Is the tone positive or negative?"]),
                  [("positive", "positive"), ("negative", "negative"), ("neutral", "neutral"), ("ambiguous", "mixed or ambiguous")])
    return [_ex("go_emotions", "Apache-2.0", split, row["text"], [q1, q2],
                {"emotion": {"label": emo}, "sentiment": {"label": GOEMO_SENTIMENT[emo]}}, ["multiq"])]


# ---------------------------------------------------------------------------
# Moderation / safety / spam
# ---------------------------------------------------------------------------

CIVIL_ATTRS = {
    "insult": "How insulting is this comment?", "threat": "How threatening is this comment?",
    "obscene": "How obscene is this comment?", "identity_attack": "How much does this comment attack someone's identity?",
    "sexual_explicit": "How sexually explicit is this comment?",
}


def load_civil():
    # 1.8M rows; keep every clearly toxic-leaning row plus a random sample of the rest.
    def pick(split):
        for r in _hf("google/civil_comments", None, split):
            if len(r["text"]) > 3000:
                continue
            if r["toxicity"] >= 0.3 or stable_hash("civil", r["__key"]) % 10 == 0:
                yield r
    return {"train": pick("train"), "val": pick("validation"), "test": pick("test")}


def conv_civil(row, split, rng):
    qs = [score_q("toxicity", rng.choice(["How toxic is this comment?", "Rate the toxicity of this comment."]),
                  0, 1, "not toxic at all", "extremely toxic")]
    ans = {"toxicity": {"value": float(row["toxicity"])}}
    attr = rng.choice(list(CIVIL_ATTRS))
    qs.append(score_q(attr, CIVIL_ATTRS[attr], 0, 1, "not at all", "extremely"))
    ans[attr] = {"value": float(row[attr])}
    return [_ex("civil_comments", "CC0-1.0", split, row["text"], qs, ans, ["multiq", "score"])]


def conv_sms(row, split, rng):
    if rng.random() < 0.5:
        q = choice_q("spam", "Is this message spam?", YES_NO)
        a = "yes" if row["label"] == 1 else "no"
    else:
        q = choice_q("spam", "What kind of message is this?", [("spam", "spam"), ("ham", "legitimate message")])
        a = "spam" if row["label"] == 1 else "ham"
    return [_ex("sms_spam", "CC-BY-4.0", split, row["sms"].strip(), [q], {"spam": {"label": a}})]


_GERMAN = re.compile(r"\b(und|nicht|ist|der|die|das|ich|wie|sind|mit|für|auf|eine|einen|dem)\b", re.I)


def conv_injection(row, split, rng):
    text = row["text"].strip()
    if len(_GERMAN.findall(text)) >= 2:
        return []  # dataset is partly German; v0.1 is English-only
    q = choice_q("injection", rng.choice(["Is this text a prompt injection attempt?",
                                          "Does this input try to override an AI system's instructions?"]), YES_NO)
    return [_ex("prompt_injections", "Apache-2.0", split, text, [q], {"injection": {"label": "yes" if row["label"] == 1 else "no"}})]


def conv_jailbreak(row, split, rng):
    q = choice_q("jailbreak", "Is this prompt an attempt to jailbreak an AI assistant?", YES_NO)
    return [_ex("jailbreak_classification", "Apache-2.0", split, row["prompt"].strip(), [q],
                {"jailbreak": {"label": "yes" if row["type"] == "jailbreak" else "no"}}, ["heldout"])]


def load_mhs():
    # One row per (comment, annotator): aggregate to one example per comment.
    agg: dict[int, dict] = {}
    for r in _hf("ucberkeley-dlab/measuring-hate-speech", None, "train"):
        a = agg.setdefault(r["comment_id"], {"text": r["text"], "hs": [], "insult": [], "__key": str(r["comment_id"])})
        a["hs"].append(r["hatespeech"])
        a["insult"].append(r["insult"])
    return {"test": (a for a in agg.values() if len(a["hs"]) >= 2)}


def conv_mhs(row, split, rng):
    hs = sum(row["hs"]) / (2 * len(row["hs"]))  # hatespeech item is 0/1/2 per annotator
    ins = sum(row["insult"]) / (4 * len(row["insult"]))  # insult item is 0..4
    qs = [score_q("hate", "How hateful is this comment?", 0, 1, "not hate speech", "clearly hate speech"),
          score_q("insult", "How insulting is this comment?", 0, 1, "not insulting", "extremely insulting")]
    return [_ex("measuring_hate_speech", "CC-BY-4.0", split, row["text"], qs,
                {"hate": {"value": hs}, "insult": {"value": ins}}, ["heldout", "score", "multiq"])]


# ---------------------------------------------------------------------------
# Response quality (scores)
# ---------------------------------------------------------------------------

HS2_ATTRS = {
    "helpfulness": ("How helpful is the assistant's response?", "not helpful", "extremely helpful"),
    "correctness": ("How factually correct is the assistant's response?", "mostly wrong", "fully correct"),
    "coherence": ("How clear and coherent is the assistant's response?", "incoherent", "perfectly clear"),
    "complexity": ("How much expertise does the response require to write?", "basic", "expert level"),
    "verbosity": ("How verbose is the response relative to what was asked?", "very terse", "very verbose"),
}


def _turns(prompt: str, response: str) -> list[str]:
    prompt = re.sub(r"<extra_id_1>(User|Assistant)\n?", lambda m: f"\n{m.group(1)}: ", prompt).strip()
    return [f"User: {prompt}" if not prompt.startswith(("User:", "Assistant:")) else prompt, f"Assistant: {response.strip()}"]


def conv_helpsteer2(row, split, rng):
    if len(row["prompt"]) + len(row["response"]) > 8000:
        return []
    qs, ans = [], {}
    for k, (text, lo, hi) in HS2_ATTRS.items():
        qs.append(score_q(k, text, 0, 4, lo, hi, step=1))
        ans[k] = {"value": float(row[k])}
    return [_ex("helpsteer2", "CC-BY-4.0", split, _turns(row["prompt"], row["response"]), qs, ans, ["multiq", "score"])]


UF_ASPECTS = {
    "helpfulness": "How helpful and informative is the response?",
    "honesty": "How honest is the response, including expressing uncertainty where appropriate?",
    "instruction_following": "How well does the response follow the user's instructions?",
    "truthfulness": "How free of hallucinations and factual errors is the response?",
}


def load_ultrafeedback():
    key = lambda r: r["instruction"]  # noqa: E731
    rows = lambda: _hf("openbmb/UltraFeedback", None, "train")  # noqa: E731
    return {s: _by_hash(rows(), key, s) for s in ("train", "val", "test")}


def conv_ultrafeedback(row, split, rng):
    out = []
    comps = [c for c in row["completions"] if len(c.get("response") or "") < 6000]
    for c in rng.sample(comps, min(2, len(comps))):
        qs, ans = [], {}
        for k, text in UF_ASPECTS.items():
            rating = (c["annotations"].get(k) or {}).get("Rating")
            qs.append(score_q(k, text, 1, 5, "very poor", "excellent", step=1))
            ans[k] = {"value": float(rating)} if rating and rating.isdigit() else {"null": True}
        out.append(_ex("ultrafeedback", "MIT", split, [f"User: {row['instruction'].strip()}", f"Assistant: {c['response'].strip()}"],
                       qs, ans, ["multiq", "score"]))
    return out


# ---------------------------------------------------------------------------
# Tool routing
# ---------------------------------------------------------------------------

NO_TOOL = ("__none__", "no tool: reply to the user directly")
CLARIFY = ("__clarify__", "ask the user for missing details first")
TOOL_Q = ["Which tool should the assistant call next?", "Which function best handles the user's message?",
          "What should the assistant do with this message?"]


def _tool_labels(funcs: list[dict]) -> list[tuple[str, str]]:
    out = []
    for f in funcs:
        name, desc = str(f.get("name", "")).strip(), str(f.get("description", "")).strip()
        if name:
            out.append((name, f"{name}: {desc}"[:200] if desc else name))
    return out


def _json_objects(s: str) -> list[dict]:
    dec, i, out = json.JSONDecoder(), 0, []
    while (j := s.find("{", i)) != -1:
        try:
            obj, i = dec.raw_decode(s, j)
            out.append(obj)
        except json.JSONDecodeError:
            i = j + 1
    return out


_DECLINE = re.compile(r"(I'm sorry|I am sorry|I apologize|I'm unable|I am unable|I can't|I cannot|"
                      r"don't have the (capability|ability)|not able to)")


def conv_glaive(row, split, rng):
    """Label the assistant's first move: call a tool, ask for missing details, or answer without tools."""
    if "Use them if required" not in row["system"]:
        return []
    funcs = [f for f in _json_objects(row["system"].split("Use them if required", 1)[1]) if "name" in f]
    turns = re.split(r"\n\n\n(?=USER:|ASSISTANT:|FUNCTION RESPONSE:)", row["chat"].strip())
    if not funcs or len(funcs) > 30 or len(turns) < 2 or not turns[0].startswith("USER:"):
        return []
    user = turns[0][len("USER:"):].strip()
    # Everything the assistant does before the user speaks again.
    reply = []
    for t in turns[1:]:
        if t.startswith("USER:"):
            break
        reply.append(t)
    first = reply[0] if reply else ""
    call = re.search(r'<functioncall>\s*\{"name":\s*"([^"]+)"', "\n".join(reply))
    if call:
        gold, tag = call.group(1), "tool:call"
    elif _DECLINE.search(first):
        gold, tag = NO_TOOL[0], "tool:none"
    elif first.replace("<|endoftext|>", "").strip().endswith("?"):
        gold, tag = CLARIFY[0], "tool:clarify"
    else:
        return []  # ambiguous first move
    labels = _tool_labels(funcs) + [NO_TOOL, CLARIFY]
    if gold not in {i for i, _ in labels}:
        return []
    q = choice_q("tool", rng.choice(TOOL_Q), labels)
    return [_ex("glaive_fc_v2", "Apache-2.0", split, [f"User: {user}"], [q], {"tool": {"label": gold}}, ["tool", tag])]


def conv_toolace(row, split, rng):
    start = row["system"].find("[", row["system"].find("invoke:"))
    try:
        funcs = json.JSONDecoder().raw_decode(row["system"], start)[0] if start != -1 else []
    except json.JSONDecodeError:
        return []
    conv = row["conversations"]
    if not funcs or len(funcs) > 30 or len(conv) < 2 or conv[0]["from"] != "user" or conv[1]["from"] != "assistant":
        return []
    reply = conv[1]["value"].strip()
    names = set(re.findall(r"(?:^\[|,\s*)([A-Za-z0-9_ .\-]+?)\(", reply)) if reply.startswith("[") else set()
    if len(names) > 1:
        return []  # parallel calls to different tools have no single correct choice
    if not names:
        return []  # non-call replies mix "no tool fits" with "missing parameters"; can't tell which
    labels = _tool_labels(funcs) + [NO_TOOL, CLARIFY]
    gold = names.pop().strip()
    if gold not in {i for i, _ in labels} or len({t.casefold() for _, t in labels}) != len(labels):
        return []
    q = choice_q("tool", rng.choice(TOOL_Q), labels)
    return [_ex("toolace", "Apache-2.0", split, [f"User: {conv[0]['value'].strip()}"], [q], {"tool": {"label": gold}},
                ["tool", "tool:call"])]


def load_toolace():
    key = lambda r: r["conversations"][0]["value"] if r["conversations"] else r["__key"]  # noqa: E731
    return {s: _by_hash(_hf("Team-ACE/ToolACE", None, "train"), key, s) for s in ("train", "val", "test")}


def load_glaive():
    # Split on the first user message: Glaive reuses the same queries under many system prompts.
    key = lambda r: r["chat"].split("ASSISTANT:", 1)[0]  # noqa: E731
    return {s: _by_hash(_hf("glaiveai/glaive-function-calling-v2", None, "train"), key, s) for s in ("train", "val", "test")}


# ---------------------------------------------------------------------------
# Occupation (held out)
# ---------------------------------------------------------------------------

BIOS_NAMES = ['accountant', 'architect', 'attorney', 'chiropractor', 'comedian', 'composer', 'dentist', 'dietitian',
              'dj', 'filmmaker', 'interior_designer', 'journalist', 'model', 'nurse', 'painter', 'paralegal', 'pastor',
              'personal_trainer', 'photographer', 'physician', 'poet', 'professor', 'psychologist', 'rapper',
              'software_engineer', 'surgeon', 'teacher', 'yoga_teacher']


def conv_bios(row, split, rng):
    prof = BIOS_NAMES[row["profession"]]
    cand = sample_labels(rng, BIOS_NAMES, prof, 5, 28)
    q = choice_q("occupation", rng.choice(["What is this person's occupation?", "What does this person do for a living?"]),
                 [(c, pretty(c)) for c in cand])
    return [_ex("bias_in_bios", "MIT", split, row["hard_text"].strip(), [q], {"occupation": {"label": prof}}, ["heldout"])]


# ---------------------------------------------------------------------------
# Scientific QA with unanswerable questions (long states)
# ---------------------------------------------------------------------------


def conv_qasper(row, split, rng):
    paras = [(i, p) for i, p in enumerate(p for sec in row["full_text"]["paragraphs"] for p in sec) if p and len(p) > 80]
    text_to_idx = {p: i for i, p in paras}
    qas = row["qas"]
    out = []
    for qi, question in enumerate(qas["question"]):
        answers = list(qas["answers"][qi]["answer"])
        if not answers:
            continue
        if all(a["unanswerable"] for a in answers):
            target, evidence, tags = {"null": True}, [], ["null:unanswerable", "long"]
        else:
            yn = {a["yes_no"] for a in answers if not a["unanswerable"]}
            if len(yn) != 1 or None in yn or any(a["unanswerable"] for a in answers):
                continue  # keep only unanimous yes/no or unanimous unanswerable
            evidence = [text_to_idx[e] for a in answers for e in a["evidence"] if e in text_to_idx]
            if not evidence:
                continue
            target, tags = {"label": "yes" if yn.pop() else "no"}, ["long"]
        # Evidence paragraphs plus random filler up to ~700 words, kept in document order.
        # Unanswerable questions were judged against the whole paper, so any excerpt is also unanswerable.
        by_idx = dict(paras)
        chosen = set(evidence)
        words = sum(len(by_idx[i].split()) for i in chosen)
        for i, p in rng_for("qasper", row["id"], qi).sample(paras, len(paras)):
            if words > 700:
                break
            if i not in chosen:
                chosen.add(i)
                words += len(p.split())
        body = [by_idx[i] for i in sorted(chosen)]
        state = {"title": row["title"], "abstract": row["abstract"], "excerpts": body}
        q = choice_q("answer", f"{question.strip()} (Answer from the paper excerpts.)", YES_NO)
        out.append(_ex("qasper", "CC-BY-4.0", split, state, [q], {"answer": target}, tags))
    return out


def load_qasper():
    return {s: _hf_parquet("allenai/qasper", f"qasper/{u}/0000.parquet")
            for s, u in [("train", "train"), ("val", "validation"), ("test", "test")]}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def load_clinc():
    from datasets import load_dataset_builder

    CLINC_NAMES[:] = load_dataset_builder("clinc/clinc_oos", "plus").info.features["intent"].names
    return {s: _hf("clinc/clinc_oos", "plus", u) for s, u in [("train", "train"), ("val", "validation"), ("test", "test")]}



# ---------------------------------------------------------------------------
# Eval v0.2 held-out sources (never trained on; test only). Added 2026-09-26 (D30).
# Licenses verified at the upstream source; see data/LICENSES.md.
# ---------------------------------------------------------------------------

RAW = "data/raw"


def _download(url: str, path: str) -> str:
    import os

    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return path


def _shuffled(rows: list[Row], tag: str) -> Iterator[Row]:
    random.Random(SHUFFLE_SEED).shuffle(rows)
    for i, r in enumerate(rows):
        r.setdefault("__key", f"{tag}:{i}")
        yield r


CONTRACT_NLI_ZIP = "https://stanfordnlp.github.io/contract-nli/resources/contract-nli.zip"
CONTRACT_WINDOW = 320  # words; the model reads states of ~512 tokens, contracts run to thousands


def load_contract_nli():
    """One row per (contract, hypothesis) from the official test split, with a word window of the contract.

    Entailment / contradiction: a window that contains the first evidence span (at a random offset). NotMentioned: a random
    window (if the contract never mentions it, no window does). Hypotheses become yes/no questions; NotMentioned is null.
    """
    import zipfile

    z = zipfile.ZipFile(_download(CONTRACT_NLI_ZIP, f"{RAW}/contract_nli/contract-nli.zip"))
    data = json.loads(z.read("contract-nli/test.json"))
    hyps = {k: v["hypothesis"] for k, v in data["labels"].items()}
    rows = []
    for doc in data["documents"]:
        text, spans = doc["text"], doc["spans"]
        for hid, ann in doc["annotation_sets"][0]["annotations"].items():
            ev = [spans[i] for i in ann["spans"]]
            rows.append({"text": text, "hyp": hyps[hid], "choice": ann["choice"], "evidence": ev[0] if ev else None,
                         "__key": f"{doc['id']}:{hid}"})
    return {"test": _shuffled(rows, "contract_nli")}


def _word_window(text: str, rng: random.Random, n: int, must: tuple[int, int] | None) -> str:
    starts = [m.start() for m in re.finditer(r"\S+", text)]
    if len(starts) <= n:
        return text.strip()
    if must is None:
        i = rng.randrange(0, len(starts) - n)
    else:
        first = next(k for k, c in enumerate(starts) if c >= must[0]) if starts[-1] >= must[0] else len(starts) - 1
        last = max(k for k, c in enumerate(starts) if c < must[1])
        span_words = last - first + 1
        lo = max(0, last - n + 1) if span_words <= n else first
        hi = min(first, len(starts) - n)
        i = rng.randint(min(lo, hi), max(lo, hi))
    end = starts[i + n] if i + n < len(starts) else len(text)
    return ("... " if i > 0 else "") + text[starts[i]:end].strip() + (" ..." if end < len(text) else "")


def conv_contract_nli(row, split, rng):
    state = _word_window(row["text"], rng, CONTRACT_WINDOW, tuple(row["evidence"]) if row["evidence"] else None)
    hyp = row["hyp"].rstrip(".")
    q = choice_q("clause", f"Does this contract excerpt state the following? {hyp}.", YES_NO)
    gold = {"Entailment": {"label": "yes"}, "Contradiction": {"label": "no"}, "NotMentioned": {"null": True}}[row["choice"]]
    tags = ["heldout", "eval:heldout_v02"] + (["null:not_mentioned"] if row["choice"] == "NotMentioned" else [])
    return [_ex("contract_nli", "CC-BY-4.0", split, state, [q], {"clause": gold}, tags)]


def conv_ethics(row, split, rng):
    q = choice_q("wrong", rng.choice(["Is the narrator's action clearly morally wrong?",
                                      "By ordinary moral standards, did the narrator do something clearly wrong?"]), YES_NO)
    return [_ex("ethics_commonsense", "MIT", split, row["input"].strip(), [q],
                {"wrong": {"label": "yes" if int(row["label"]) == 1 else "no"}}, ["heldout", "eval:heldout_v02"])]


FIN_TOPICS = ["Analyst Update", "Fed | Central Banks", "Company | Product News", "Treasuries | Corporate Debt", "Dividend",
              "Earnings", "Energy | Oil", "Financials", "Currencies", "General News | Opinion", "Gold | Metals | Materials", "IPO",
              "Legal | Regulation", "M&A | Investments", "Macro", "Markets", "Politics", "Personnel Change", "Stock Commentary",
              "Stock Movement"]


def conv_fin_topic(row, split, rng):
    gold = FIN_TOPICS[int(row["label"])]
    cand = sample_labels(rng, FIN_TOPICS, gold, 6, 20)
    q = choice_q("topic", rng.choice(["What is this financial news post about?", "Which topic best fits this post?"]),
                 [(c, c.replace(" | ", " / ")) for c in cand])
    return [_ex("fin_tweets_topic", "MIT", split, row["text"].strip(), [q], {"topic": {"label": gold}},
                ["heldout", "eval:heldout_v02"])]


def conv_fin_sentiment(row, split, rng):
    gold = ["bearish", "bullish", "neutral"][int(row["label"])]
    q = choice_q("sentiment", "What market sentiment does this post express?",
                 [("bearish", "bearish"), ("bullish", "bullish"), ("neutral", "neutral")])
    return [_ex("fin_tweets_sentiment", "MIT", split, row["text"].strip(), [q], {"sentiment": {"label": gold}},
                ["heldout", "eval:heldout_v02"])]


ARXIV_GROUPS = {  # label id -> (readable name, OAI-PMH set, primary-category prefixes)
    "cs": ("computer science", "cs", ("cs.",)),
    "math": ("mathematics", "math", ("math.",)),
    "stat": ("statistics", "stat", ("stat.",)),
    "q-bio": ("quantitative biology", "q-bio", ("q-bio.",)),
    "q-fin": ("quantitative finance", "q-fin", ("q-fin.",)),
    "econ": ("economics", "econ", ("econ.",)),
    "eess": ("electrical engineering and systems science", "eess", ("eess.",)),
    "astro-ph": ("astrophysics", "physics:astro-ph", ("astro-ph",)),
    "cond-mat": ("condensed matter physics", "physics:cond-mat", ("cond-mat",)),
    "hep": ("high energy physics", "physics:hep-ph", ("hep-",)),
    "gr-qc": ("general relativity and quantum cosmology", "physics:gr-qc", ("gr-qc",)),
    "nucl": ("nuclear physics", "physics:nucl-th", ("nucl-",)),
    "quant-ph": ("quantum physics", "physics:quant-ph", ("quant-ph",)),
    "physics": ("physics (applied, optics, fluids and other)", "physics:physics", ("physics.",)),
    "nlin": ("nonlinear sciences", "physics:nlin", ("nlin.",)),
}
ARXIV_CACHE = f"{RAW}/arxiv/sample.jsonl"
# arXiv's official metadata snapshot (CC0 per arXiv's terms), via the Hugging Face mirror. One shard is plenty.
# (Sep 2026: the legacy query API returned HTTP 406, and OAI-PMH throttled after one large response.)
ARXIV_SNAPSHOT = ("librarian-bots/arxiv-metadata-snapshot", "data/train-00009-of-00010.parquet")


def fetch_arxiv(per_group: int = 70) -> None:
    import os

    import pandas as pd
    from huggingface_hub import hf_hub_download

    df = pd.read_parquet(hf_hub_download(ARXIV_SNAPSHOT[0], ARXIV_SNAPSHOT[1], repo_type="dataset"),
                         columns=["id", "title", "abstract", "categories"])
    df = df.sample(frac=1.0, random_state=SHUFFLE_SEED)
    out, counts = [], {g: 0 for g in ARXIV_GROUPS}
    for r in df.itertuples(index=False):
        cats = str(r.categories).split()
        if not cats:
            continue
        gid = next((g for g, (_, _, pre) in ARXIV_GROUPS.items() if cats[0].startswith(pre)), None)
        if gid is None or counts[gid] >= per_group:
            continue
        counts[gid] += 1
        out.append({"id": str(r.id), "group": gid, "primary": cats[0], "title": " ".join(str(r.title).split()),
                    "abstract": " ".join(str(r.abstract).split())})
        if all(c >= per_group for c in counts.values()):
            break
    os.makedirs(os.path.dirname(ARXIV_CACHE), exist_ok=True)
    with open(ARXIV_CACHE, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def load_arxiv():
    import os

    if not os.path.exists(ARXIV_CACHE):
        fetch_arxiv()
    rows = [json.loads(line) for line in open(ARXIV_CACHE, encoding="utf-8")]
    for r in rows:
        r["__key"] = r["id"]
    return {"test": _shuffled(rows, "arxiv")}


def conv_arxiv(row, split, rng):
    cand = sample_labels(rng, list(ARXIV_GROUPS), row["group"], 5, 15)
    q = choice_q("field", rng.choice(["Which research field does this paper belong to?", "What is the primary subject area of this paper?"]),
                 [(c, ARXIV_GROUPS[c][0]) for c in cand])
    return [_ex("arxiv_field", "CC0-1.0", split, f"{row['title']}\n\n{row['abstract']}", [q], {"field": {"label": row["group"]}},
                ["heldout", "eval:heldout_v02"])]


def conv_casehold(row, split, rng):
    labels = [(f"h{i}", str(row[f"holding_{i}"]).strip()[:200]) for i in range(5)]
    if len({t.casefold() for _, t in labels}) < 5:
        return []
    q = choice_q("holding", "Which holding does the citation marked <HOLDING> most likely stand for?", labels)
    return [_ex("casehold", "Apache-2.0", split, row["citing_prompt"].strip(), [q], {"holding": {"label": f"h{int(row['label'])}"}},
                ["heldout", "eval:heldout_v02"])]


CLICKBAIT_ZIP = "https://zenodo.org/records/5530410/files/clickbait17-train-170331.zip?download=1"


def load_clickbait():
    import zipfile

    z = zipfile.ZipFile(_download(CLICKBAIT_ZIP, f"{RAW}/clickbait17/clickbait17-train-170331.zip"))
    names = z.namelist()
    inst = next(n for n in names if n.endswith("instances.jsonl"))
    truth = next(n for n in names if n.endswith("truth.jsonl"))
    # split("\n"), not splitlines(): tweets contain Unicode line separators inside JSON strings.
    t = {j["id"]: j for j in map(json.loads, filter(None, z.read(truth).decode().split("\n")))}
    rows = []
    for j in map(json.loads, filter(None, z.read(inst).decode().split("\n"))):
        post = " ".join(j.get("postText") or []).strip()
        if post and j["id"] in t:
            rows.append({"text": post, "score": float(t[j["id"]]["truthMean"]), "__key": j["id"]})
    return {"test": _shuffled(rows, "clickbait")}


def conv_clickbait(row, split, rng):
    q = score_q("clickbait", "How clickbait-y is this social media post?", 0, 1, "not clickbait", "heavy clickbait")
    return [_ex("clickbait17", "CC-BY-4.0", split, row["text"], [q], {"clickbait": {"value": row["score"]}},
                ["heldout", "eval:heldout_v02", "score"])]


POEM_LABELS = [("negative", "negative"), ("positive", "positive"), ("no_impact", "no emotional impact"), ("mixed", "mixed")]


def load_poems():
    rows = [r for sp in ("train", "validation", "test") for r in _hf("google-research-datasets/poem_sentiment", None, sp)]
    return {"test": _shuffled(rows, "poems")}


def conv_poems(row, split, rng):
    q = choice_q("sentiment", "What sentiment does this line of poetry express?", POEM_LABELS)
    return [_ex("poem_sentiment", "CC-BY-4.0", split, row["verse_text"].strip(), [q],
                {"sentiment": {"label": POEM_LABELS[int(row["label"])][0]}}, ["heldout", "eval:heldout_v02"])]

def _std(path, config=None, val="validation", test="test"):
    return lambda: {"train": _hf(path, config, "train"), "val": _hf(path, config, val), "test": _hf(path, config, test)}


SOURCES: dict[str, Source] = {s.id: s for s in [
    Source("mnli", "nli", "OANC + CC-BY-3.0 (fiction genre excluded)", "https://huggingface.co/datasets/nyu-mll/multi_nli",
           lambda: {"train": (r for r in _hf("nyu-mll/multi_nli", None, "train") if hash_split(r["premise"], 0.02, 0) == "train"),
                    "val": (r for r in _hf("nyu-mll/multi_nli", None, "train") if hash_split(r["premise"], 0.02, 0) == "val"),
                    "test": _hf("nyu-mll/multi_nli", None, "validation_matched")},
           conv_mnli),
    Source("scitail", "nli", "Apache-2.0", "https://huggingface.co/datasets/allenai/scitail",
           _std("allenai/scitail", "snli_format"), conv_scitail),
    Source("commonsense_qa", "mc_reasoning", "MIT", "https://huggingface.co/datasets/tau/commonsense_qa",
           _carve("tau/commonsense_qa", None, "validation", lambda r: r["question"]), conv_csqa),
    Source("openbookqa", "mc_reasoning", "Apache-2.0", "https://huggingface.co/datasets/allenai/openbookqa",
           _std("allenai/openbookqa", "main"), conv_obqa),
    Source("winogrande", "mc_reasoning", "Apache-2.0", "https://huggingface.co/datasets/allenai/winogrande",
           _carve("allenai/winogrande", "winogrande_xl", "validation", lambda r: r["sentence"]), conv_winogrande),
    Source("clinc_oos", "intent", "CC-BY-3.0", "https://huggingface.co/datasets/clinc/clinc_oos", load_clinc, conv_clinc,
           notes="out-of-scope queries become null"),
    Source("massive", "intent", "CC-BY-4.0", "https://huggingface.co/datasets/AmazonScience/massive", load_massive, conv_massive,
           notes="en-US only; two questions per state"),
    Source("banking77", "intent", "CC-BY-4.0", "https://github.com/PolyAI-LDN/task-specific-datasets", load_banking, conv_banking,
           heldout=True),
    Source("go_emotions", "emotion", "Apache-2.0", "https://huggingface.co/datasets/google-research-datasets/go_emotions",
           _std("google-research-datasets/go_emotions", "simplified"), conv_goemotions),
    Source("civil_comments", "moderation", "CC0-1.0", "https://huggingface.co/datasets/google/civil_comments", load_civil, conv_civil),
    Source("sms_spam", "moderation", "CC-BY-4.0", "https://archive.ics.uci.edu/dataset/228/sms+spam+collection",
           lambda: {s: _by_hash(_hf("ucirvine/sms_spam", None, "train"), lambda r: r["sms"], s) for s in ("train", "val", "test")},
           conv_sms),
    Source("prompt_injections", "safety", "Apache-2.0", "https://huggingface.co/datasets/deepset/prompt-injections",
           lambda: {"train": _hf("deepset/prompt-injections", None, "train"), "test": _hf("deepset/prompt-injections", None, "test")},
           conv_injection),
    Source("jailbreak_classification", "safety", "Apache-2.0", "https://huggingface.co/datasets/jackhhao/jailbreak-classification",
           lambda: {"test": _hf("jackhhao/jailbreak-classification", None, "test")}, conv_jailbreak, heldout=True),
    Source("measuring_hate_speech", "moderation", "CC-BY-4.0", "https://huggingface.co/datasets/ucberkeley-dlab/measuring-hate-speech",
           load_mhs, conv_mhs, heldout=True),
    Source("helpsteer2", "quality_score", "CC-BY-4.0", "https://huggingface.co/datasets/nvidia/HelpSteer2",
           lambda: {"train": (r for r in _hf("nvidia/HelpSteer2", None, "train") if hash_split(r["prompt"], 0.03, 0) == "train"),
                    "val": (r for r in _hf("nvidia/HelpSteer2", None, "train") if hash_split(r["prompt"], 0.03, 0) == "val"),
                    "test": _hf("nvidia/HelpSteer2", None, "validation")},
           conv_helpsteer2),
    Source("ultrafeedback", "quality_score", "MIT", "https://huggingface.co/datasets/openbmb/UltraFeedback",
           load_ultrafeedback, conv_ultrafeedback, notes="ratings are GPT-4 annotations; 'N/A' ratings become null"),
    Source("glaive_fc_v2", "tool_routing", "Apache-2.0", "https://huggingface.co/datasets/glaiveai/glaive-function-calling-v2",
           load_glaive, conv_glaive),
    Source("toolace", "tool_routing", "Apache-2.0", "https://huggingface.co/datasets/Team-ACE/ToolACE", load_toolace, conv_toolace),
    Source("bias_in_bios", "occupation", "MIT", "https://huggingface.co/datasets/LabHC/bias_in_bios",
           lambda: {"test": _hf("LabHC/bias_in_bios", None, "test")}, conv_bios, heldout=True),
    Source("qasper", "doc_qa", "CC-BY-4.0", "https://huggingface.co/datasets/allenai/qasper", load_qasper, conv_qasper,
           notes="unanimous yes/no and unanimous unanswerable questions; excerpts of ~700 words"),
    Source("contract_nli", "legal_nli", "CC-BY-4.0", "https://stanfordnlp.github.io/contract-nli/", load_contract_nli, conv_contract_nli,
           heldout=True, notes="eval v0.2; Hitachi America, Ltd.; 320-word windows; NotMentioned becomes null"),
    Source("ethics_commonsense", "moral_judgment", "MIT", "https://github.com/hendrycks/ethics",
           lambda: {"test": _hf_parquet("hendrycks/ethics", "commonsense/test/0000.parquet")}, conv_ethics, heldout=True,
           notes="eval v0.2; Reddit-sourced, culturally biased (per the authors)"),
    Source("fin_tweets_topic", "topic", "MIT", "https://huggingface.co/datasets/zeroshot/twitter-financial-news-topic",
           lambda: {"test": _hf("zeroshot/twitter-financial-news-topic", None, "validation")}, conv_fin_topic, heldout=True,
           notes="eval v0.2; underlying tweets are subject to X's terms"),
    Source("fin_tweets_sentiment", "sentiment", "MIT", "https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment",
           lambda: {"test": _hf("zeroshot/twitter-financial-news-sentiment", None, "validation")}, conv_fin_sentiment, heldout=True,
           notes="eval v0.2; underlying tweets are subject to X's terms"),
    Source("arxiv_field", "topic", "CC0-1.0", "https://info.arxiv.org/help/api/tou.html", load_arxiv, conv_arxiv, heldout=True,
           notes="eval v0.2; recent abstracts snapshot via the arXiv API (metadata is CC0); primary category only"),
    Source("casehold", "legal_mc", "Apache-2.0", "https://github.com/reglab/casehold",
           lambda: {"test": _hf_parquet("casehold/casehold", "all/test/0000.parquet")}, conv_casehold, heldout=True,
           notes="eval v0.2; court opinions are public domain (Caselaw Access Project); holdings truncated to 200 chars"),
    Source("clickbait17", "score", "CC-BY-4.0", "https://zenodo.org/records/5530410", load_clickbait, conv_clickbait, heldout=True,
           notes="eval v0.2; Webis Clickbait Corpus 2017 (train-170331 file); mean of 5 annotators, 0..1"),
    Source("poem_sentiment", "sentiment", "CC-BY-4.0", "https://github.com/google-research-datasets/poem-sentiment", load_poems,
           conv_poems, heldout=True, notes="eval v0.2; all splits used (held out)"),
]}
