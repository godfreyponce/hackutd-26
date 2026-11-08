from software.eval.cases import CASES
from software.eval.score import judge, summarize, table

CASE = {c.id: c for c in CASES}


def agent(step, text, tool=None):
    msg = {"type": "agent", "step": step, "text": text}
    if tool:
        msg["tool"] = tool
    return msg


EVENT = {"type": "fall_hint"}
ASK = {"type": "checkin", "state": "asking", "try": 1}
VOICE_SILENT = {"type": "heard", "answer": "no_answer", "transcript": ""}


def heard(answer, n):
    return {"type": "checkin", "state": answer, "try": n}


def decision(outcome):
    return agent("VERIFY", f"Decision: trigger fall_hint; presence sensor still (someone detected); answers x; "
                           f"outcome {outcome}.", "log_decision")


def silence_run():
    """A clean silence x3 run: asks at 1 s, 3 s, 5 s, alarm at 6 s."""
    return [
        (0.0, EVENT),
        (0.5, agent("PLAN", "hosted Nemotron 30B: get_presence")),
        (1.0, ASK), (1.9, VOICE_SILENT), (2.0, heard("no_answer", 1)),
        (3.0, {**ASK, "try": 2}), (3.9, VOICE_SILENT), (4.0, heard("no_answer", 2)),
        (5.0, {**ASK, "try": 3}), (5.4, VOICE_SILENT), (5.5, heard("no_answer", 3)),
        (6.0, {"type": "checkin", "state": "alarm", "try": 4}),
        (7.0, decision("alarm")),
    ]


def test_clean_silence_run_is_correct_with_times():
    r = judge(CASE["silence"], silence_run())
    assert r["correct"], r["problems"]
    assert r["first_ask_s"] == 1.0
    assert r["alarm_s"] == 6.0
    assert r["planner_calls"] == 1


def test_early_alarm_is_wrong():
    events = silence_run()
    events.insert(4, (2.1, {"type": "checkin", "state": "alarm", "try": 2}))
    r = judge(CASE["silence"], events)
    assert not r["correct"]
    assert any("alarm after 1 answers" in p for p in r["problems"])


def test_missing_alarm_is_wrong():
    events = [e for e in silence_run() if e[1].get("state") != "alarm"]
    r = judge(CASE["silence"], events)
    assert not r["correct"]
    assert r["alarm_s"] is None


def test_alarm_when_none_expected_is_wrong():
    events = [(0.0, {"type": "quake"}), (1.0, ASK), (1.5, {"type": "heard", "answer": "ok", "transcript": "okay"}),
              (2.0, heard("ok", 1)), (2.5, {"type": "checkin", "state": "alarm", "try": 2}), (3.0, decision("ok"))]
    r = judge(CASE["ok"], events)
    assert not r["correct"]


def test_no_decision_is_wrong():
    r = judge(CASE["ok"], [(0.0, {"type": "quake"}), (1.0, ASK)])
    assert not r["correct"]
    assert any("outcomes" in p for p in r["problems"])


def test_counts_fallbacks_takeovers_overrides_and_guard():
    events = silence_run() + [
        (1.1, agent("FALLBACK", "LLM unreachable: hosted Nemotron 30B (APITimeoutError: x). Next: local Nemotron 4B.")),
        (1.2, agent("FALLBACK", "LLM unreachable: local Nemotron 4B (APIConnectionError: x). Next: fixed script.")),
        (1.3, agent("VERIFY", "hosted Nemotron 30B stopped before the check-in finished. The fixed script takes over.")),
        (1.4, agent("VERIFY", "Rule override: the rule demands an alarm and the planner skipped it. Raising it in code.",
                    "raise_alarm")),
        (1.5, agent("VERIFY", "Safety Guard: safe (Nemotron Safety Guard says safe).", "safety_guard")),
        (1.6, agent("VERIFY", "Safety Guard: unsafe, withheld from the planner (guard unreachable: X).", "safety_guard")),
    ]
    r = judge(CASE["silence"], sorted(events, key=lambda e: e[0]))
    assert r["fallbacks"] == 2
    assert r["to_script"] == 2  # one FALLBACK into the fixed script, one takeover
    assert r["overrides"] == 1
    assert r["guard"] == {"safe": 1, "unsafe": 0, "unreachable": 1, "mock": 0}


def test_summary_medians_worst_and_table():
    runs = [judge(CASE["silence"], silence_run()) for _ in range(2)]
    slow = silence_run()
    slow[-2] = (10.0, slow[-2][1])
    runs.append(judge(CASE["silence"], slow))
    s = summarize(CASE["silence"], runs)
    assert (s["runs"], s["correct"]) == (3, 3)
    assert s["alarm_median_s"] == 6.0 and s["alarm_worst_s"] == 10.0
    text = table([s])
    assert "3 of 3" in text
    assert "silence" in text


def say(sid, listen=True):
    msg = {"type": "say", "script_id": sid, "text": "x"}
    if listen:
        msg["listen_s"] = 1
    return msg


def test_wrong_retry_line_is_counted_but_not_a_wrong_call():
    events = silence_run()
    events += [(1.0, say("ask_stopped")), (3.0, say("ask_retry_2")), (5.0, say("standup_ask"))]
    r = judge(CASE["silence"], sorted(events, key=lambda e: e[0]))
    assert r["correct"]
    assert r["wrong_lines"] == ["ask 3 said standup_ask, expected ask_retry_3"]


def test_second_alarm_is_wrong():
    events = silence_run() + [(6.5, {"type": "checkin", "state": "alarm", "try": 4})]
    r = judge(CASE["silence"], sorted(events, key=lambda e: e[0]))
    assert not r["correct"]


def test_standup_needs_the_clear_message():
    case = CASE["standup"]
    events = silence_run() + [(8.0, {**ASK, "try": 1}), (8.5, {"type": "heard", "answer": "ok", "transcript": "ok"}),
                              (9.0, heard("ok", 1)), (10.0, decision("clear"))]
    assert not judge(case, events)["correct"]
    events.insert(-1, (9.5, {"type": "checkin", "state": "clear", "try": 1}))
    assert judge(case, events)["correct"], judge(case, events)["problems"]


def test_heard_to_rule_time_for_spoken_answers_only():
    events = [(0.0, {"type": "quake"}), (1.0, ASK), (2.0, {"type": "heard", "answer": "ok", "transcript": "okay"}),
              (11.0, heard("ok", 1)), (12.0, decision("ok"))]
    assert judge(CASE["ok"], events)["heard_to_rule_s"] == [9.0]
    assert judge(CASE["silence"], silence_run())["heard_to_rule_s"] == []


def test_heard_to_rule_leaves_out_a_no_answer_reply_with_words():
    events = [(0.0, EVENT), (1.0, ASK), (1.5, {"type": "heard", "answer": "no_answer", "transcript": "um, what"}),
              (1.6, heard("no_answer", 1)), (3.0, {**ASK, "try": 2}),
              (3.5, {"type": "heard", "answer": "ok", "transcript": "yeah, I'm fine"}), (6.0, heard("ok", 2)),
              (7.0, decision("ok"))]
    assert judge(CASE["unclear_then_ok"], events)["heard_to_rule_s"] == [2.5]


def test_missing_heard_is_wrong():
    events = [(t, m) for t, m in silence_run() if m is not VOICE_SILENT]
    r = judge(CASE["silence"], events)
    assert not r["correct"]
    assert any("heard" in p for p in r["problems"])


def test_clean_run_has_no_fallback_takeover_override_or_refusal():
    events = silence_run()
    assert judge(CASE["silence"], events)["clean"]
    events.append((1.1, agent("VERIFY", "Refused speak: x", "speak")))
    assert not judge(CASE["silence"], events)["clean"]
