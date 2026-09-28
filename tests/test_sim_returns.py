import collections

from kodiak_s1.data.sim.returns_desk import OFFERS, WORLDS, Case, action, make_case, offer, questions_and_answers


def _case(world="wizard", category="wand", **kw) -> Case:
    c = make_case(0, 0)
    c.world = world
    c.order = {"order_id": "A-1", "item": "x", "category": category, "price_usd": 50, "purchased": "2026-03-01",
               "delivery": "delivered", "member": False}
    c.today, c.window_days, c.member_bonus, c.want, c.fallback, c.trap = "2026-03-10", 30, 15, "refund", None, None
    for k, v in kw.items():
        setattr(c, k, v)
    return c


def test_rules_in_order_in_every_world():
    assert offer(_case()) == OFFERS[1]
    assert offer(_case(today="2026-05-01")) == OFFERS[4]  # past the window
    c = _case(today="2026-04-10"); c.order["member"] = True
    assert offer(c) == OFFERS[1]  # 40 days old, 45-day member window
    for world, cat, flag in (("wizard", "wand", "cursed"), ("retail", "furniture", "clearance"), ("outdoor", "tents", "on_sale")):
        c = _case(world, cat); c.order[flag] = True
        assert offer(c) == OFFERS[2], world
    for world, cat, flag in (("wizard", "potion", "opened"), ("retail", "software", "activated"), ("outdoor", "fuel", "used")):
        c = _case(world, cat); c.order[flag] = True
        assert offer(c) == OFFERS[4], world
    c = _case(today="2026-05-01"); c.order["delivery"] = "delivered damaged"
    assert offer(c) == OFFERS[0]  # shop's fault beats the window
    assert offer(_case("retail", "custom", today="2026-03-05")) == OFFERS[3]
    assert offer(_case("outdoor", "boots")) == OFFERS[4]  # 9 days: too late to exchange


def test_actions():
    c = _case(); c.order["cursed"] = True
    assert action(c, offer(c)) == "offer store credit"
    assert action(_case(want="status"), OFFERS[1]) == "give a delivery update"
    assert action(_case(want="question"), OFFERS[1]) == "answer their question"
    c = _case("retail", "custom", today="2026-03-05")
    assert action(c, offer(c)) == "arrange an exchange"  # wants a refund, only an exchange is allowed
    c = _case(want="replacement", fallback="refund", today="2026-05-01")
    assert action(c, offer(c)) == "decline and explain the rules"


def test_generated_cases_are_consistent():
    worlds, wants = collections.Counter(), collections.Counter()
    for j in range(400):
        c = make_case(j, 3)
        qs, ans = questions_and_answers(c)
        worlds[c.world] += 1
        wants[c.want] += 1
        assert ("null" in ans["courier"]) == (not c.courier_known)
        assert c.order["category"] in WORLDS[c.world]["catalog"]
    assert set(worlds) == set(WORLDS) and len(wants) == 6
