import asyncio

import httpx
import pytest

from software.agent import handoff
from software.agent.handoff import HandoffWriter, build_facts, check_note, template_note, template_why
from software.agent.planner import LLMPlanner, ScriptPlanner
from software.agent.scripts import HANDOFF_CONTACTS

from .fakes import FakeBus, FakeClient, FakeWriterClient, make_agent

FACTS = build_facts(
    trigger="quake", peak_g=0.82, presence="still",
    answers=[(1, "no_answer", ""), (2, "no_answer", "mmm"), (3, "no_answer", "")],
    battery_pct=87, power="battery",
    alert={"source": "usgs", "event": "Earthquake", "headline": "DEMO ONLY, NOT A REAL ALERT"},
    reason="someone detected + no answer after 3 tries", at="14:32",
)
GOOD_NOTE = ("H000: no response after an event (earthquake, peak 0.82 g). Presence sensor shows someone still. "
             "No answer on 3 tries. Battery 87%. Alarm at 14:32.")
GOOD_REPLY = '{"note": "%s", "contact": "rafael"}' % GOOD_NOTE
GOOD_WHY = "Someone is there: presence sensor says still.\n- No answer on 3 tries.\n- The rule says that is an alarm.\n- Extra line."


# ---- the note check ----

def test_a_note_built_from_the_facts_passes():
    assert check_note(GOOD_NOTE, FACTS) is None


def test_a_number_not_in_the_facts_fails():
    assert "5" in check_note("No answer on 5 tries.", FACTS)


def test_an_emergency_number_fails_even_when_a_transcript_said_it():
    facts = build_facts(trigger="fall_hint", peak_g=None, presence="still",
                        answers=[(1, "help", "call 911")], battery_pct=None, power=None, alert=None,
                        reason="the answer was help", at="14:32")
    assert check_note("Said help: call 911.", facts) == "names an emergency number"
    assert check_note("Said help. Call nine one one.", facts) == "names an emergency number"


def test_a_long_note_fails():
    assert "over 60" in check_note("word " * 61, FACTS)


def test_an_empty_note_fails():
    assert check_note("  ", FACTS) == "empty"


def test_the_template_note_passes_its_own_check():
    note = template_note(FACTS, "godfrey")
    assert check_note(note, FACTS) is None
    assert "no response after an event" in note
    assert "Godfrey" in note
    assert "fall detection" not in note.lower()


def test_the_template_why_is_three_lines_from_the_rule():
    why = template_why(FACTS)
    assert len(why) <= 3
    assert "someone detected + no answer after 3 tries" in why[0]


# ---- the writer ----

def write(client):
    return asyncio.run(HandoffWriter(client, "fake-model", timeout_s=1).write(FACTS))


def test_nemotron_note_and_why_pass_the_check():
    client = FakeWriterClient(note=GOOD_REPLY, why=GOOD_WHY)
    h = write(client)
    assert (h.note, h.contact, h.by) == (GOOD_NOTE, "rafael", "nemotron")
    assert h.why == ["Someone is there: presence sensor says still.", "No answer on 3 tries.", "The rule says that is an alarm."]
    assert h.why_by == "nemotron"
    note_req, why_req = sorted(client.requests, key=lambda r: r["extra_body"]["chat_template_kwargs"]["enable_thinking"])
    assert note_req["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
    assert why_req["extra_body"]["chat_template_kwargs"] == {"enable_thinking": True}
    assert why_req["extra_body"]["reasoning_budget"] == handoff.WHY_REASONING_BUDGET
    assert "battery" not in str(why_req["messages"])  # the why sees only what the rule used


def test_a_timeout_names_the_wait():
    async def slow(**kw):
        await asyncio.sleep(1)

    client = FakeWriterClient()
    client.chat.completions.create = slow
    h = asyncio.run(HandoffWriter(client, "fake-model", timeout_s=0.01).write(FACTS))
    assert "no reply in 0.01 s" in h.rows[0][1]


def test_no_client_uses_the_template():
    h = write(None)
    assert (h.by, h.why_by, h.contact) == ("template", "template", next(iter(HANDOFF_CONTACTS)))
    assert h.note == template_note(FACTS, h.contact)
    assert any("MOCK" in row[1] for row in h.rows)


def test_planner_down_uses_the_template():
    h = write(FakeWriterClient(error=httpx.ConnectError("Wi-Fi off")))
    assert (h.by, h.why_by) == ("template", "template")
    assert [row[0] for row in h.rows] == ["FALLBACK", "FALLBACK"]
    assert "Wi-Fi off" in h.rows[0][1]


@pytest.mark.parametrize("reply, problem", [
    ('{"note": "No answer on 5 tries.", "contact": "rafael"}', "5 is not in the facts"),
    ('{"note": "%s", "contact": "mom"}' % GOOD_NOTE, "contact"),
    ("The person did not answer.", "JSON"),
])
def test_a_bad_note_uses_the_template(reply, problem):
    h = write(FakeWriterClient(note=reply, why=GOOD_WHY))
    assert h.by == "template"
    assert h.why_by == "nemotron"
    assert any(problem in row[1] for row in h.rows)


def test_a_why_with_an_invented_number_uses_the_template_why():
    h = write(FakeWriterClient(note=GOOD_REPLY, why="No answer for 10 minutes."))
    assert (h.by, h.why_by) == ("nemotron", "template")
    assert h.why == template_why(FACTS)


# ---- the event on the bus ----

STILL = {"type": "presence", "state": "still"}
QUAKE = {"type": "quake", "peak_g": 0.82}


def run(answers, events, writer=None, planners=None):
    async def scenario():
        bus = FakeBus(answers)
        agent = make_agent(bus, planners=planners, writer=writer)
        for e in events:
            await agent.handle(e)
        await agent.idle()
        return bus

    return asyncio.run(scenario())


def handoffs(bus):
    return [m for m in bus.sent if m["type"] == "handoff"]


def test_alarm_sends_one_handoff_event_after_the_alarm():
    note = "H000: no response after an event, peak 0.82 g. No answer on 3 tries. Battery 87%."
    reply = '{"note": "%s", "contact": "rafael"}' % note
    writer = HandoffWriter(FakeWriterClient(note=reply, why=GOOD_WHY), "fake-model", timeout_s=1)
    events = [{"type": "heartbeat", "battery_pct": 87}, {"type": "power", "state": "battery"}, STILL, QUAKE]
    bus = run(["no_answer"] * 3, events, writer)
    [event] = handoffs(bus)
    assert set(event) == {"type", "home", "note", "contact", "by", "why", "why_by"}
    assert event["home"] == "H000"
    assert event["note"] == note
    assert event["contact"] == {"id": "rafael", **HANDOFF_CONTACTS["rafael"]}
    assert (event["by"], event["why_by"]) == ("nemotron", "nemotron")
    assert 1 <= len(event["why"]) <= 3
    kinds = [m["type"] if m["type"] != "checkin" else m["state"] for m in bus.sent]
    assert kinds.index("alarm") < kinds.index("handoff")
    assert any(r.get("tool") == "write_handoff" and note in r["text"] for r in bus.trace("VERIFY"))


def test_the_facts_carry_battery_peak_g_alert_and_each_transcript():
    client = FakeWriterClient(note=GOOD_REPLY, why=GOOD_WHY)
    alert = {"type": "alert", "source": "usgs", "event": "Earthquake", "headline": "DEMO ONLY"}
    answers = [{"answer": "no_answer", "transcript": "mmm"}, "no_answer", "no_answer"]
    run(answers, [{"type": "heartbeat", "battery_pct": 64}, alert, STILL, QUAKE],
        HandoffWriter(client, "fake-model", timeout_s=1))
    sent = str(client.requests[0]["messages"])
    for fact in ("64", "0.82", "DEMO ONLY", "mmm", "still"):
        assert fact in sent


def test_help_sends_a_handoff_and_keeps_reply_help_before_the_alarm():
    bus = run(["help"], [STILL, QUAKE])
    assert [m.get("script_id") or m["state"] for m in bus.sent if m["type"] in ("say", "checkin")
            and m.get("state") != "asking"] == ["ask_stopped", "help", "reply_help", "alarm"]
    [event] = handoffs(bus)
    assert event["by"] == "template"
    assert "said help" in event["note"]


@pytest.mark.parametrize("answers, events", [(["ok"], [STILL, QUAKE]), (["no_answer"], [QUAKE])])
def test_no_alarm_means_no_handoff(answers, events):
    assert handoffs(run(answers, events)) == []


def test_handoff_also_runs_after_an_llm_planned_checkin():
    planners = [LLMPlanner("fake Nemotron", FakeClient(), "fake-model"), ScriptPlanner()]
    bus = run(["no_answer"] * 3, [STILL, QUAKE], planners=planners)
    assert len(handoffs(bus)) == 1


def test_contacts_have_no_phone_numbers():
    for contact in HANDOFF_CONTACTS.values():
        assert not any(ch.isdigit() for ch in str(contact))
    assert handoff.HOME_ID == "H000"


def test_a_note_that_says_fall_or_radar_fails():
    assert check_note("The person fell and stayed still.", FACTS) == "says fall or radar"
    assert check_note("Possible fall at the box.", FACTS) == "says fall or radar"
    assert check_note("Radar shows the person still.", FACTS) == "says fall or radar"


# ---- demo alerts (#36) ----

DEMO_ALERT = {"type": "alert", "source": "noaa", "event": "Earthquake Warning", "headline": "Earthquake Warning",
              "code": "EQW", "level": "emergency", "station": "HACKDEMO", "demo": True}
DEMO_FACTS = build_facts(trigger="alert", peak_g=None, presence="still", answers=[(1, "help", "help me")],
                         battery_pct=None, power=None, alert=DEMO_ALERT, reason="the answer was help", at="14:32")


def test_demo_alert_facts_and_template_say_demo():
    assert DEMO_FACTS["alert"]["demo"] is True
    assert DEMO_FACTS["alert"]["code"] == "EQW"
    note = template_note(DEMO_FACTS, "godfrey")
    assert "DEMO, not a real alert." in note
    assert "Official" not in note


def test_real_alert_template_stays_official():
    assert "Official alert: Earthquake (usgs)." in template_note(FACTS, "godfrey")


def test_a_note_about_a_demo_alert_must_say_demo():
    assert check_note("H000: help after an Earthquake Warning alert. Alarm at 14:32.", DEMO_FACTS) == \
        "does not say DEMO, not a real alert"
    assert check_note("H000: help after an Earthquake Warning alert. DEMO, not a real alert. Alarm at 14:32.",
                      DEMO_FACTS) is None
