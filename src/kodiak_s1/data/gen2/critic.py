"""Critic: one extra call per kept example that looks for answers a careful human would reject.

Why (human review of the v2.0 eval candidates, 2026-09-25): 12 of 165 kept questions were wrong even though writer and checker
agreed, and most had *more than one defensible answer* ("which is NOT listed?" with two unlisted options; "the next stop" in a
thread with two stops). Agreement between two models doesn't catch that: both pick the same plausible option. The critic is
shown the proposed answer and asked to attack it, which is a different task from answering.
"""

from __future__ import annotations

from kodiak_s1.data import synth

VERDICTS = ["correct", "wrong", "ambiguous"]


def critic_prompt(state_text: str, questions: list[dict], answers: dict) -> str:
    items = []
    for q in questions:
        a = answers[q["id"]]
        if q["type"] == "choice":
            opts = "; ".join(f'{lab["id"]} = {lab["text"]}' for lab in q["labels"])
            prop = "UNANSWERABLE" if a.get("null") else a["label"]
            items.append(f'- id={q["id"]} (choice): {q["text"]}\n  Options: {opts}\n  Proposed answer: {prop}')
        else:
            prop = "UNANSWERABLE" if a.get("null") else f'{a["value"]:g}'
            items.append(f'- id={q["id"]} (score {q["min"]:g} to {q["max"]:g}; {q["min"]:g} = {q.get("min_label", "")}, '
                         f'{q["max"]:g} = {q.get("max_label", "")}): {q["text"]}\n  Proposed answer: {prop}')
    return f"""You are auditing training data. Each question below comes with a proposed answer about the state.
Be strict, like a careful human reviewer. For each question, first explain your reasoning briefly in "reason", then give a verdict:
- "correct": the proposed answer is the single clearly best one, supported by the state (or, if UNANSWERABLE, the state really
  does not give enough to answer). Confident, reasonable inference is fine.
- "wrong": the state supports a different answer (check the latest information, exact numbers and which entity is meant).
- "ambiguous": more than one option is defensible, the question is unclear about what it refers to, or the scale's end labels
  don't fit the question.

STATE:
{state_text}

QUESTIONS:
{chr(10).join(items)}

Return JSON only."""


def critic_schema(questions: list[dict]) -> dict:
    props = {q["id"]: {"type": "object", "properties": {"reason": {"type": "string"},
                                                       "verdict": {"type": "string", "enum": VERDICTS}},
                       "required": ["reason", "verdict"]} for q in questions}
    return {"type": "object", "properties": props, "required": list(props)}


def critique(state_text: str, questions: list[dict], answers: dict, model: str) -> tuple[dict[str, str], dict]:
    """{question id: verdict} (missing or malformed -> "ambiguous", i.e. not kept), plus token usage."""
    r = synth.teacher(critic_prompt(state_text, questions, answers), critic_schema(questions), 0.0, model,
                      300 + 250 * len(questions))
    out = {}
    for q in questions:
        v = r["content"].get(q["id"])
        out[q["id"]] = v.get("verdict") if isinstance(v, dict) and v.get("verdict") in VERDICTS else "ambiguous"
    return out, {"tokens": r["tokens"], "prompt_tokens": r.get("prompt_tokens", 0), "raw": r["content"]}
