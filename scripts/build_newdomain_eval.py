"""New-domains test v0.1 (D76): real, permissively licensed tasks from topics and formats Kodiak has never trained on, the headline
measure for "does it handle new kinds of task?" (the Decision Index's new-domain score is the outside version, D72). Never trained on.

Two slices:
  read       the answer can be read off the text (Kodiak's job): law and policy, contracts, insurance, medicine and science reading,
             workplace safety, sustainability policy, maths topic, formal logic. The headline is the mean chance-corrected skill here.
  knowledge  exam-style questions that mostly test world knowledge (reported, not the headline).

Up to 150 items per task, sampled with balanced answers (so chance = 1 / number of options). Licenses were checked upstream (D76);
everything here is CC BY 4.0, MIT, Apache-2.0 or US public domain. Raw files: data/raw/newdomain/ (downloaded from the Hugging Face Hub).

    uv run python scripts/build_newdomain_eval.py      # -> data/eval/kodiak-newdomain-v0.1.jsonl
"""
import glob
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

R = Path("data/raw/newdomain")
OUT = Path("data/eval/kodiak-newdomain-v0.1.jsonl")
PER_TASK = 150
SDG = ["no poverty", "zero hunger", "good health and well-being", "quality education", "gender equality", "clean water and sanitation",
       "affordable and clean energy", "decent work and economic growth", "industry, innovation and infrastructure", "reduced inequalities",
       "sustainable cities and communities", "responsible consumption and production", "climate action", "life below water", "life on land",
       "peace, justice and strong institutions"]


def load(k):
    p = [x for x in glob.glob(f"{R}/{k}/**/*", recursive=True) if x.endswith((".tsv", ".parquet"))][0]
    return pd.read_csv(p, sep="\t") if p.endswith(".tsv") else pd.read_parquet(p)


def balanced(rows, key, n, rng):
    """Up to n rows, as close to equal per label as the data allows."""
    by = defaultdict(list)
    for r in rows:
        by[key(r)].append(r)
    for v in by.values():
        rng.shuffle(v)
    out, i = [], 0
    while len(out) < n and any(i < len(v) for v in by.values()):
        for lab in sorted(by):
            if i < len(by[lab]) and len(out) < n:
                out.append(by[lab][i])
        i += 1
    rng.shuffle(out)
    return out


def ex(task, slice_, lic, state, questions, answers):
    return {"state": state, "questions": questions, "answers": answers,
            "meta": {"source": f"nd_{task}", "split": "test", "license": lic, "tags": ["eval:newdomain", f"nd:{task}", f"slice:{slice_}"]}}


def choice(qid, text, labels):
    return {"type": "choice", "id": qid, "text": text, "allow_null": False,
            "labels": [{"id": str(i), "text": t} for i, t in enumerate(labels)]}


def simple(task, slice_, lic, rows, n, label_names, text, state_fn, gold_fn, rng):
    picked = balanced(rows, gold_fn, n, rng)
    out = []
    for r in picked:
        q = choice("decision", text(r) if callable(text) else text, label_names)
        out.append(ex(task, slice_, lic, state_fn(r), [q], {"decision": {"label": str(label_names.index(gold_fn(r)))}}))
    return out


def build():
    rng = random.Random(76)
    T = []
    yn = ["yes", "no"]
    # ---- read slice ----------------------------------------------------------------------------------------------------------------
    d = load("lb_fods").to_dict("records")
    secs = ["Facts", "Procedural History", "Issue", "Rule", "Analysis", "Conclusion", "Decree"]
    T += simple("court_opinion_section", "read", "CC-BY-4.0", d, PER_TASK, secs, "Which part of a court opinion is this paragraph?",
                lambda r: {"paragraph": r["Paragraph"]}, lambda r: r["answer"], rng)
    d = load("lb_lobby").to_dict("records")
    T += simple("bill_relevance", "read", "CC-BY-4.0", d, PER_TASK, yn, "Is this proposed bill relevant to this company?",
                lambda r: {"bill_title": r["bill_title"], "bill_summary": r["bill_summary"], "company": r["company_name"],
                           "company_description": r["company_description"]}, lambda r: r["answer"].lower(), rng)
    d = load("lb_privacy").to_dict("records")
    T += simple("privacy_policy_relevance", "read", "MIT", d, PER_TASK, ["relevant", "irrelevant"],
                "Is this privacy-policy sentence relevant to the user's question?",
                lambda r: {"user_question": r["question"], "policy_sentence": r["text"]}, lambda r: r["answer"].lower(), rng)
    d = load("lb_sara").to_dict("records")
    T += simple("tax_statute_entailment", "read", "MIT", d, PER_TASK, ["yes, it follows", "no, it is contradicted"],
                "Applying the statute to the facts, does the statement follow?",
                lambda r: {"statute": str(r["statute"]).strip(), "facts": r["description"], "statement": r["question"]},
                lambda r: "yes, it follows" if r["answer"] == "Entailment" else "no, it is contradicted", rng)
    d = load("lb_supply").to_dict("records")
    T += simple("supply_chain_audits", "read", "CC-BY-4.0", d, PER_TASK, yn,
                "Does this statement disclose whether the seller or manufacturer performs any type of audit of its suppliers, or reserves "
                "the right to audit?", lambda r: {"supply_chain_disclosure": r["text"]}, lambda r: r["answer"].lower(), rng)
    d = load("lb_tos").to_dict("records")
    tos = ["Other", "Limitation of liability", "Unilateral termination", "Unilateral change", "Contract by using", "Jurisdiction",
           "Choice of law", "Content removal", "Arbitration"]
    tos_txt = ["none of these (an ordinary clause)", "limitation of liability", "unilateral termination by the provider",
               "unilateral change of terms by the provider", "agreement by merely using the service", "jurisdiction for disputes",
               "choice of governing law", "removal of user content", "arbitration of disputes"]
    T += simple("tos_unfair_term", "read", "CC-BY-4.0", d, PER_TASK, tos_txt,
                "Which kind of potentially unfair term, if any, is this Terms of Service sentence?", lambda r: {"terms_of_service_sentence": r["text"]},
                lambda r: tos_txt[tos.index(r["answer"])], rng)
    d = load("lb_insur").to_dict("records")
    ins = ["yes, it is covered", "no, it is not covered", "it's ambiguous"]
    T += simple("insurance_coverage", "read", "CC-BY-4.0", d, PER_TASK, ins, "Is the claim covered under the policy?",
                lambda r: {"policy": r["policy"], "claim": r["claim"]}, lambda r: ins["ABC".index(r["answer"])], rng)
    d = load("cuad").to_dict("records")
    cl = sorted(l for l, _ in Counter(r["label"] for r in d).most_common(30))  # Kodiak allows at most 32 options
    d = [r for r in d if r["label"] in cl]
    T += simple("contract_clause_type", "read", "CC-BY-4.0", d, PER_TASK, cl, "What type of contract clause is this?",
                lambda r: {"clause": r["clause"]}, lambda r: r["label"], rng)
    d = load("pubmedqa").to_dict("records")
    T += simple("pubmed_answer", "read", "MIT", d, PER_TASK, ["yes", "no", "maybe"], "Based on the abstract, what is the answer to the question?",
                lambda r: {"question": r["question"], "abstract": "\n".join(r["context"]["contexts"])}, lambda r: r["final_decision"], rng)
    d = load("medmcqa").to_dict("records")
    subj = sorted({r["subject_name"] for r in d})
    T += simple("medical_exam_subject", "read", "MIT", d, PER_TASK, subj, "Which medical subject is this exam question from?",
                lambda r: {"exam_question": r["question"]}, lambda r: r["subject_name"], rng)
    d = load("scicite").to_dict("records")
    cit = ["background", "method", "result"]
    T += simple("citation_intent", "read", "Apache-2.0", d, PER_TASK,
                ["background information", "using the cited method, tool or data", "comparing with the cited result"],
                "Why does the author cite the other work in this sentence?", lambda r: {"citation_sentence": r["string"]},
                lambda r: ["background information", "using the cited method, tool or data", "comparing with the cited result"][cit.index(r["label"])], rng)
    d = load("osdg").to_dict("records")  # labels are 0-based (0 = SDG 1); this release has goals 1-15 only
    goals = [SDG[i] for i in sorted({int(r["labels"]) for r in d})]
    T += simple("sustainability_goal", "read", "CC-BY-4.0", d, PER_TASK, goals, "Which UN Sustainable Development Goal is this text mainly about?",
                lambda r: {"text": r["text"]}, lambda r: SDG[int(r["labels"])], rng)
    d = load("mathqa").to_dict("records")
    mcat = {"general": "general arithmetic", "physics": "rates, speed, time and work", "gain": "profit, interest and percentages",
            "geometry": "geometry", "probability": "probability and counting", "other": "other"}
    T += simple("math_problem_topic", "read", "Apache-2.0", d, PER_TASK, list(mcat.values()), "What kind of maths problem is this?",
                lambda r: {"problem": r["Problem"]}, lambda r: mcat[r["category"]], rng)
    d = load("fallacy").to_dict("records")
    T += simple("formal_logic_validity", "read", "Apache-2.0", d, PER_TASK, ["valid", "invalid"], "Is the argument, given the explicitly stated premises, deductively valid?",
                lambda r: {"argument": r["inputs"].split("Is the argument")[0].strip()}, lambda r: list(r["targets"])[0], rng)
    # OSHA: several questions about one narrative (a format Kodiak rarely trains on). US federal work, public domain.
    o = load("osha")
    o = o[o["final_narrative"].astype(str).str.len() > 60]
    top = lambda c, k: list(o[c].value_counts().head(k).index)
    ev, body, sec = top("event_title", 20), top("part_of_body_title", 15), top("naics_sector_name", 12)
    rows = [r for r in o.to_dict("records") if r["event_title"] in ev and r["part_of_body_title"] in body and r["naics_sector_name"] in sec]
    for r in balanced(rows, lambda r: r["event_title"], PER_TASK, rng):
        qs = [choice("event", "What kind of event caused the injury?", ev), choice("body_part", "Which part of the body was injured?", body),
              choice("industry", "Which industry sector is the employer in?", sec)]
        T.append(ex("osha_injury_report", "read", "Public-Domain-US-Gov", {"incident_report": r["final_narrative"]}, qs,
                    {"event": {"label": str(ev.index(r["event_title"]))}, "body_part": {"label": str(body.index(r["part_of_body_title"]))},
                     "industry": {"label": str(sec.index(r["naics_sector_name"]))}}))
    # ---- knowledge slice (reported, not the headline) -------------------------------------------------------------------------------
    d = load("lb_ethics").to_dict("records")
    T += simple("judicial_ethics", "knowledge", "MIT", d, PER_TASK, yn, "Under New York judicial ethics rules, is the answer to this question yes?",
                lambda r: {"question": r["question"]}, lambda r: r["answer"].lower(), rng)
    d = load("medmcqa").to_dict("records")
    d = [r for r in d if r["choice_type"] == "single" and all(0 < len(str(r[c])) <= 200 for c in ("opa", "opb", "opc", "opd"))]
    for r in balanced(d, lambda r: r["cop"], PER_TASK, rng):
        opts = [r[c] for c in ("opa", "opb", "opc", "opd")]
        if len(set(opts)) < 4:
            continue
        T.append(ex("medical_exam_answer", "knowledge", "MIT", {"exam_question": r["question"]},
                    [choice("decision", "Which option is correct?", opts)], {"decision": {"label": str(int(r["cop"]))}}))
    return T


if __name__ == "__main__":
    from kodiak_s1.schema import Example
    T = build()
    for e in T:
        Example.model_validate(e)
    OUT.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in T) + "\n")
    c = Counter(next(t for t in e["meta"]["tags"] if t.startswith("nd:")) + " " + e["meta"]["tags"][-1] for e in T)
    for k, v in sorted(c.items()):
        print(f"{v:4d} {k}")
    print(len(T), "items ->", OUT)
