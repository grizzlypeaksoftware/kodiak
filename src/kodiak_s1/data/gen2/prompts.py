"""Writer and checker prompts for Generator v2, built from a spec (and a real passage when grounded).

Lessons carried over from v1 (LEARNING.md, Phase 2): separate choice and score arrays, so every choice question gets
labels; real JSON objects for JSON states; exact-quote evidence; no double quotes inside prose.

New in v2: every question declares its *basis*: "stated", "inferred" or "unanswerable". v1's rule, "if the fact isn't
written down, it's unanswerable", made Kodiak abstain on questions a careful reader can answer by inference (the intent
behind a banking message, the occupation in a bio). v2 requires inference questions, labeled answerable, and the
checker is told that sound inference counts as answering.
"""

from __future__ import annotations

from kodiak_s1.data.gen2.specs import DECISIONS, NULL_KINDS, SCORE_FOCUS_SCALES, TARGET_BANDS, Spec

BASES = ["stated", "inferred", "unanswerable"]

FORMATS = {
    "text": "a single plain-text document",
    "list": "a list of 2-6 separate texts in order (for example messages in a thread, or entries in a log)",
    "json": "a JSON object with realistic nested fields, exactly as a real system would emit it",
}
LENGTH = {"easy": "short (40-120 words)", "medium": "medium (100-250 words)", "hard": "long (250-450 words)"}

DIFFICULTY_STATE = {
    "easy": "Keep it straightforward: the answers are clear once you read the relevant part.",
    "medium": "Include one or two plausible distractor details (another date, amount, name or option that is not the answer).",
    "hard": "Make it demanding: include distractors (similar names, numbers or dates; a value that is later corrected; "
            "an opinion quoted from someone else), and spread the relevant facts across different parts of the state.",
}
DIFFICULTY_QUESTIONS = {
    "easy": "Questions can be direct.",
    "medium": "At least one question should need two details combined, or a small inference.",
    "hard": "At least one question must need details from different parts of the state combined, and choice questions "
            "should include close near-miss options. There must still be exactly one defensible answer.",
}


def _question_rules(spec: Spec, grounded: bool) -> str:
    n = spec.n_choice + spec.n_score
    focus = min(2, n) if spec.decision != "judgment_score" else spec.n_score
    kinds = "\n".join(f"    - {k}: {NULL_KINDS[k]}" for k in dict.fromkeys(spec.null_kinds))
    scores = ""
    if spec.n_score and spec.targets:  # Stage 3: anchored scales with target bands
        parts = []
        for sc, (lo, hi), t in zip(spec.scales, spec.ranges, spec.targets):
            a_lo, a_mid, a_hi = SCORE_FOCUS_SCALES[sc]
            parts.append(f"{sc} from {lo:g} to {hi:g} (anchors: {lo:g} = {a_lo}; middle = {a_mid}; {hi:g} = {a_hi}); "
                         f"design the state so the correct rating is {t.upper()}, in the {TARGET_BANDS[t]} of the range")
        scores = (f"- {spec.n_score} \"score\" question(s), in this order:\n" + "\n".join(f"    - {x}" for x in parts) +
                  "\n  Set min and max exactly and use the anchor phrases for min_label and max_label. The rating must follow from "
                  "concrete details in the state (deadlines, amounts, consequences, tone), judged against the anchors. Use the whole "
                  "range: a high rating means high, not a cautious middle.\n")
    elif spec.n_score:
        parts = [f"{s} on a scale from {lo:g} to {hi:g}" for s, (lo, hi) in zip(spec.scales, spec.ranges)]
        scores = (f"- {spec.n_score} \"score\" question(s), in this order: {'; '.join(parts)}. Set min and max exactly, "
                  "and write min_label and max_label: short phrases for the two ends of that same dimension (for urgency: 'can wait' / "
                  "'act immediately'). Pick what is being rated so the state gives a real basis for the rating.\n")
    null_rule = (f"""- "unanswerable": exactly {spec.n_null} question(s). The state lacks what is needed to answer. Use these kinds:
{kinds}
  An unanswerable question must still sound relevant to this state (not obviously off-topic), and its evidence is empty.
""" if spec.n_null else "- \"unanswerable\": none in this set: every question must be answerable from the state.\n")
    who = "a careful reader, researcher or content classifier" \
        if grounded else f"a real decision system working with {spec.doc_type} records"
    return f"""Write {n} questions that {who} would ask about this state.
- {spec.n_choice} "choice" question(s): 2-8 labels each. Label ids are short snake_case; label texts are short phrases.
  Labels are mutually exclusive; when the question is answerable, exactly one is correct. Use plausible options.
{scores}- Focus: at least {focus} of the questions should {DECISIONS[spec.decision]}.
- {DIFFICULTY_QUESTIONS[spec.difficulty]}

Give every question a "basis":
- "stated": the answer is written in the state.
- "inferred": the answer is not written word for word, but a careful reader would confidently conclude it from what the
  state says (for example the intent behind a complaint, the tone of a message, which team should handle a request,
  whether the numbers given meet a rule, what kind of document this is). Exactly {spec.n_inference} question(s) must be
  inferred. Inferred questions ARE answerable: never mark them unanswerable. Score questions are usually inferred.
{null_rule}
For stated and inferred questions: give answer_label (a label id) or answer_value (a number within the range), and copy
into evidence a short quote from the state that supports the answer, character for character, not a paraphrase
(for a JSON state, copy a fragment exactly as written, e.g. "status": "shipped"). For unanswerable ones, leave evidence
empty and put any placeholder in answer_label / answer_value.

Each question must have exactly one defensible answer. Before finalizing, check every option: if a second option also
fits, rewrite the question. In particular:
- Do not ask negative or set-membership questions ("which is NOT listed", "which of these is mentioned/defined"):
  several options usually qualify.
- Make each question refer to exactly one thing (one person, item, stop, date or event), named so it cannot be confused.
- When the state contains updates or corrections, the answer must reflect the latest information.
- Inferred answers must be conclusions a careful reader would reach with confidence, not guesses about audience,
  motives or what will probably happen.

Never offer options that mean "unknown", "not stated", "cannot be determined", "none of the above" or "other":
Kodiak says "I don't know" by abstaining, so such an option would make an unanswerable question look answerable.
Avoid: questions that need outside knowledge; questions where two options are defensible; question texts that give away
the answer; options that are obviously silly. Vary the phrasing; do not start every question the same way."""


PAIR_RULES = """
Finally, write a VARIANT of the state for the first score question: copy the state and change as little as possible (one or
two phrases, same format and length, all other facts identical) so that the correct rating for that question moves to the
OPPOSITE end of its scale (low to high, high to low; from medium, to whichever end is more natural). Put it in "variant":
"state" is the full edited state, and "score_answers" gives, for every score question (same ids), the rating on the variant
with an exact evidence quote copied from the variant."""


def writer_prompt(spec: Spec, passage: str | None = None) -> str:
    head = ("You are creating training data for Kodiak, a small model that reads a \"state\" and answers typed questions "
            "with calibrated confidence, or abstains when the state does not contain the answer.\n\n")
    if passage is not None:
        return head + f"""The state is this real document excerpt. Do not rewrite it; only write questions about it.

STATE:
{passage}

{DIFFICULTY_QUESTIONS[spec.difficulty]}
{_question_rules(spec, grounded=True)}
Return JSON only."""
    return head + f"""Setting: {spec.sector} / {spec.domain}. Document type: {spec.doc_type}.

Write ONE realistic state: {FORMATS[spec.format]}, a real {spec.doc_type}. Length: {LENGTH[spec.difficulty]}.
Invent specific, plausible details (names, numbers, dates). It should read like the real artifact, not a summary of it
or a story about it. Do not mention that it is synthetic. Do not use double quote characters inside prose; use single quotes.
{DIFFICULTY_STATE[spec.difficulty]}

{_question_rules(spec, grounded=False)}{PAIR_RULES if spec.pair else ""}
Return JSON only."""


def writer_schema(spec: Spec, grounded: bool) -> dict:
    common = {"id": {"type": "string"}, "text": {"type": "string"},
              "basis": {"type": "string", "enum": BASES}, "evidence": {"type": "string"}}
    label = {"type": "object", "properties": {"id": {"type": "string"}, "text": {"type": "string"}}, "required": ["id", "text"]}
    choice = {"type": "object", "properties": {
        "id": common["id"], "text": common["text"],
        "labels": {"type": "array", "items": label, "minItems": 2, "maxItems": 8},
        "basis": common["basis"], "evidence": common["evidence"], "answer_label": {"type": "string"}},
        "required": ["id", "text", "labels", "basis", "evidence", "answer_label"]}
    score = {"type": "object", "properties": {
        "id": common["id"], "text": common["text"], "min": {"type": "number"}, "max": {"type": "number"},
        "min_label": {"type": "string"}, "max_label": {"type": "string"},
        "basis": common["basis"], "evidence": common["evidence"], "answer_value": {"type": "number"}},
        "required": ["id", "text", "min", "max", "min_label", "max_label", "basis", "evidence", "answer_value"]}
    props = {
        "choice_questions": {"type": "array", "items": choice, "minItems": spec.n_choice, "maxItems": spec.n_choice},
        "score_questions": {"type": "array", "items": score, "minItems": spec.n_score, "maxItems": spec.n_score}}
    if spec.pair and not grounded:
        state_t = {"text": {"type": "string"}, "list": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 6},
                   "json": {"type": "object"}}[spec.format]
        props["variant"] = {"type": "object", "properties": {
            "state": state_t,
            "score_answers": {"type": "array", "minItems": spec.n_score, "maxItems": spec.n_score, "items": {
                "type": "object", "properties": {"id": {"type": "string"}, "evidence": {"type": "string"},
                                                 "answer_value": {"type": "number"}},
                "required": ["id", "evidence", "answer_value"]}}},
            "required": ["state", "score_answers"]}
    if not grounded:
        props = {"state": {"text": {"type": "string"},
                           "list": {"type": "array", "items": {"type": "string"}, "minItems": 2, "maxItems": 6},
                           "json": {"type": "object"}}[spec.format], **props}
    return {"type": "object", "properties": props, "required": list(props)}


def verify_prompt(state_text: str, questions: list[dict]) -> str:
    """Blind check: the checker answers without seeing the writer's answers or bases.

    Unlike v1's checker prompt ("using ONLY information in the state"), sound inference counts as answering. Otherwise
    the checker vetoes exactly the inference questions v2 exists to add.
    """
    qs = []
    for q in questions:
        if q["type"] == "choice":
            opts = "; ".join(f'{lab["id"]} = {lab["text"]}' for lab in q["labels"])
            qs.append(f'- id={q["id"]} (choice): {q["text"]} Options: {opts}')
        else:
            qs.append(f'- id={q["id"]} (score {q["min"]:g} to {q["max"]:g}; {q["min"]:g} = {q.get("min_label", "")}, '
                      f'{q["max"]:g} = {q.get("max_label", "")}): {q["text"]}')
    return f"""Read the state and answer each question as a careful reader would.
Answers can be stated in the state, or confidently inferred from what it says (for example the intent behind a message,
its tone, or which option a policy's numbers imply). Do not use outside facts about the specific people or events.
For each question, first copy into "quote" the exact part of the state your answer rests on (empty if there is none),
then give "answer": the option id for choice questions, or a number for score questions.
Answer UNANSWERABLE only if the state does not give enough to answer, or if none of the options fits.

STATE:
{state_text}

QUESTIONS:
{chr(10).join(qs)}

Return JSON only."""
