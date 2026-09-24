"""Architecture properties from docs/ARCHITECTURE.md §4, checked on a micro model."""

import copy
import os

import pytest
import torch

from kodiak_s1.model import EncoderConfig, HeadConfig, KodiakModel, ModelConfig, decision_loss
from kodiak_s1.model.heads import group_log_softmax
from kodiak_s1.packing import LABEL, QUESTION, STATE, collate, pack_example

# 3 layers: layer 0 global, layers 1-2 local (window 4, so locality actually matters on short inputs).
MICRO = EncoderConfig(hidden_size=64, num_layers=3, num_heads=4, intermediate_size=96, local_window=4)


@pytest.fixture(scope="module")
def model():
    torch.manual_seed(0)
    m = KodiakModel(ModelConfig(MICRO, HeadConfig()))
    m.eval()
    return m


EX = {
    "state": "Customer: my card was charged twice for order 4411, please refund it before Friday.",
    "questions": [
        {"type": "choice", "id": "intent", "text": "What does the customer want?",
         "labels": [{"id": "refund", "text": "a refund"}, {"id": "status", "text": "order status"},
                    {"id": "cancel", "text": "cancel the order"}]},
        {"type": "score", "id": "urgency", "text": "How urgent?", "min": 0, "max": 1,
         "min_label": "not urgent", "max_label": "very urgent"},
        {"type": "choice", "id": "brand", "text": "Which card brand?",
         "labels": [{"id": "visa", "text": "Visa"}, {"id": "mc", "text": "Mastercard"}]},
    ],
    "answers": {"intent": {"label": "refund"}, "urgency": {"value": 0.8}, "brand": {"null": True}},
}


def run(model, exs, impl="sdpa", max_len=512):
    b = collate([pack_example(e) for e in exs], max_len=max_len)
    with torch.no_grad():
        return model(b, impl=impl), b


def per_question(out, b, ex_index=0):
    """{qid: (z_null, mu, kappa, [z_choice...])} for one example in the batch."""
    exs = [i for i, k in enumerate(b.q_example) if k == ex_index]
    res = {}
    for n, qidx in enumerate(exs):
        labels = (b.l_q == qidx).nonzero().flatten()
        res[n] = (out["z_null"][qidx], out["mu"][qidx], out["kappa"][qidx], out["z_choice"][labels])
    return res


def close(a, b):
    return all(torch.allclose(x, y, atol=1e-5) for x, y in zip(a, b))


def test_packing_layout():
    p = pack_example(EX)
    S = p.role.count(STATE)
    assert p.pos[:S] == list(range(S))
    # every question block starts right after the state
    assert [p.pos[o] for o in p.q_off] == [S, S, S]
    # every label of question 0 starts at the same position
    q0_len = sum(1 for r, q in zip(p.role, p.qi) if r == QUESTION and q == 0)
    starts = [p.pos[o] for o, q in zip(p.l_off, p.l_q) if q == 0]
    assert starts == [S + q0_len] * 3
    assert p.role[p.l_off[0]] == LABEL and p.q_null == [0, 0, 1] and p.l_gold[:3] == [True, False, False]


def test_questions_are_independent_of_each_other(model):
    out, b = run(model, [EX])
    together = per_question(out, b)
    for i, q in enumerate(EX["questions"]):
        alone_ex = {**EX, "questions": [q], "answers": {q["id"]: EX["answers"][q["id"]]}}
        o, bb = run(model, [alone_ex])
        assert close(per_question(o, bb)[0], together[i]), f"question {q['id']} changed when asked alone"


def test_question_order_does_not_matter(model):
    out, b = run(model, [EX])
    rev = {**EX, "questions": EX["questions"][::-1]}
    o, bb = run(model, [rev])
    a, r = per_question(out, b), per_question(o, bb)
    for i in range(3):
        assert close(a[i], r[2 - i])


def test_label_order_does_not_matter(model):
    out, b = run(model, [EX])
    shuffled = copy.deepcopy(EX)
    shuffled["questions"][0]["labels"] = shuffled["questions"][0]["labels"][::-1]
    o, bb = run(model, [shuffled])
    z = per_question(out, b)[0][3]
    zs = per_question(o, bb)[0][3]
    assert torch.allclose(z, zs.flip(0), atol=1e-5)
    assert torch.allclose(per_question(out, b)[0][0], per_question(o, bb)[0][0], atol=1e-5)  # null head too


def test_state_encoding_ignores_questions(model):
    one = {**EX, "questions": EX["questions"][:1], "answers": {"intent": EX["answers"]["intent"]}}
    hs = []
    for ex in (one, EX):
        b = collate([pack_example(ex)], max_len=512)
        meta = {"doc": b.doc, "role": b.role, "qi": b.qi, "li": b.li, "pos": b.pos}
        with torch.no_grad():
            h = model.encoder(b.input_ids, meta, "sdpa")
        hs.append(h[0, b.role[0] == STATE])
    assert torch.allclose(hs[0], hs[1], atol=1e-5)


def test_packed_examples_do_not_see_each_other(model):
    other = {"state": "The package arrived crushed and the box was wet.", "questions": EX["questions"][:1],
             "answers": {"intent": {"label": "status"}}}
    alone, b1 = run(model, [EX])
    packed, b2 = run(model, [other, EX])  # both in one row
    assert b2.input_ids.shape[0] == 1
    a, p = per_question(alone, b1, 0), per_question(packed, b2, 1)
    for i in range(3):
        assert close(a[i], p[i])


def test_group_log_softmax_matches_per_group():
    z = torch.randn(7)
    g = torch.tensor([0, 0, 0, 2, 2, 1, 1])
    out = group_log_softmax(z, g, 3)
    for k in range(3):
        idx = (g == k).nonzero().flatten()
        assert torch.allclose(out[idx], torch.log_softmax(z[idx], 0), atol=1e-6)


def test_loss_is_finite_and_has_gradients(model):
    m = copy.deepcopy(model).train()
    b = collate([pack_example(EX)], max_len=512)
    loss, stats = decision_loss(m(b, impl="sdpa"), b)
    loss.backward()
    assert torch.isfinite(loss) and stats["n_q"] == 3
    assert all(p.grad is not None for p in m.heads.parameters())


@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs CUDA for FlexAttention")
def test_flex_matches_sdpa(model):
    m = copy.deepcopy(model).cuda()
    other = {"state": "Short state.", "questions": EX["questions"][:2],
             "answers": {"intent": {"label": "cancel"}, "urgency": {"value": 0.1}}}
    b = collate([pack_example(e) for e in (EX, other, EX)], max_len=256, pad_to=256).to("cuda")
    with torch.no_grad():
        o_flex, o_sdpa = m(b, impl="flex"), m(b, impl="sdpa")
    for k in o_flex:
        assert torch.allclose(o_flex[k], o_sdpa[k], atol=1e-4), k


@pytest.mark.skipif(not os.environ.get("KODIAK_SLOW"), reason="downloads ModernBERT; set KODIAK_SLOW=1")
def test_modernbert_weights_reproduce_hf():
    from transformers import AutoModel

    from kodiak_s1.model.encoder import Encoder, load_modernbert

    torch.manual_seed(0)
    ref = AutoModel.from_pretrained("answerdotai/ModernBERT-base", attn_implementation="sdpa").eval()
    enc = Encoder(EncoderConfig()).eval()
    assert load_modernbert(enc) == ["decoder.bias", "head.dense.weight", "head.norm.weight"]
    N = 300  # longer than the local window, so local layers are exercised
    ids = torch.randint(0, 50000, (1, N))
    meta = {"doc": torch.zeros(1, N, dtype=torch.long), "role": torch.full((1, N), STATE),
            "qi": torch.full((1, N), -1), "li": torch.full((1, N), -1), "pos": torch.arange(N)[None]}
    with torch.no_grad():
        ours = enc(ids, meta, "sdpa")
        theirs = ref(input_ids=ids).last_hidden_state
    assert torch.allclose(ours, theirs, atol=1e-3), (ours - theirs).abs().max()


def test_answer_accepts_shorthand_labels_and_returns_valid_response(model):
    import json
    from pathlib import Path

    from kodiak_s1.infer import answer
    from kodiak_s1.schema import Response

    req = json.loads((Path(__file__).resolve().parents[1] / "schema/examples/request.json").read_text())
    (res,) = answer(model, [req])
    Response.model_validate(res)
    assert set(res["answers"]) == {"intent", "urgency", "card_brand"}
    intent = res["answers"]["intent"]
    assert intent["answer"] is None or intent["answer"] in {"refund or billing fix", "order status", "cancel order", "technical support"}
