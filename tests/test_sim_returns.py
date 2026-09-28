from kodiak_s1.data.sim.returns_desk import OFFERS, Case, action, make_case, offer, questions_and_answers


def _case(**kw) -> Case:
    c = make_case(0, 0)
    c.order = {"order_id": "A-1", "item": "Willow Wand", "category": "wand", "price_gold": 50, "purchased": "2026-03-01",
               "delivery": "delivered", "guild_member": False}
    c.today, c.window_days, c.member_bonus, c.want, c.fallback, c.trap = "2026-03-10", 30, 15, "refund", None, None
    for k, v in kw.items():
        setattr(c, k, v)
    return c


def test_rules_in_order():
    assert offer(_case()) == OFFERS[1]
    assert offer(_case(today="2026-05-01")) == OFFERS[4]  # past the window
    c = _case(today="2026-04-10"); c.order["guild_member"] = True
    assert offer(c) == OFFERS[1]  # 40 days old, 45-day member window
    c = _case(); c.order["cursed"] = True
    assert offer(c) == OFFERS[2]
    c = _case(today="2026-05-01"); c.order["delivery"] = "delivered damaged"
    assert offer(c) == OFFERS[0]  # shop's fault beats the window
    c = _case(); c.order.update(category="creature")
    assert offer(c) == OFFERS[4]  # 9 days old creature: no exchange


def test_actions_follow_want_then_fallback_then_alternatives():
    c = _case(); c.order["cursed"] = True
    assert action(c, offer(c)) == "offer store credit"
    c = _case(want="replacement", fallback="refund", today="2026-05-01")
    assert action(c, offer(c)) == "decline and explain the rules"
    c = _case(want="info")
    assert action(c, offer(c)) == "answer their question"
    c = _case(today="2026-03-05"); c.order.update(category="creature")
    assert action(c, offer(c)) == "arrange an exchange"  # wants a refund, only an exchange is allowed


def test_courier_unknown_means_null():
    for j in range(50):
        c = make_case(j, 3)
        _, ans = questions_and_answers(c)
        assert ("null" in ans["courier"]) == (not c.courier_known)
