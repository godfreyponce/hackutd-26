"""Judge one run from the bus messages it produced, and sum up the runs of a case.

A run is a list of (seconds, message) in bus order, from the hub's own publish hook.
"""

import re
from statistics import median

from software.agent.rule import ANSWERS
from software.agent.scripts import RETRY_SCRIPTS, STANDUP_SCRIPT

_OUTCOME = re.compile(r"outcome (\w+)\.$")
HOSTED = "hosted Nemotron"


def _checkins(events, state):
    return [(t, m) for t, m in events if m.get("type") == "checkin" and m.get("state") == state]


def _agent_rows(events, step=None, tool=None):
    return [m for _, m in events if m.get("type") == "agent"
            and (step is None or m.get("step") == step) and (tool is None or m.get("tool") == tool)]


def judge(case, events):
    t0 = next((t for t, m in events if m.get("type") == case.trigger), None)
    if t0 is None:
        return {"case": case.id, "correct": False, "problems": ["the event never reached the bus"],
                "first_ask_s": None, "alarm_s": None, **_counts(events)}
    asks = _checkins(events, "asking")
    answers = [(t, m["state"]) for t, m in events if m.get("type") == "checkin" and m.get("state") in ANSWERS]
    alarms = _checkins(events, "alarm")
    outcomes = tuple(_OUTCOME.search(m["text"]).group(1) for m in _agent_rows(events, "VERIFY", "log_decision")
                     if _OUTCOME.search(m.get("text", "")))
    alarm_after = sum(1 for t, _ in answers if t <= alarms[0][0]) if alarms else None

    problems = []
    voice = sum(1 for _, m in events if m.get("type") == "heard")
    if voice != len(asks):
        problems.append(f"{voice} heard messages from the voice service for {len(asks)} asks")
    for m in _agent_rows(events, "VERIFY"):
        if m["text"].startswith(("No answer from the voice service", "Unknown answer")):
            problems.append(f"agent: {m['text']}")
    if len(alarms) > 1:
        problems.append(f"{len(alarms)} alarms, expected at most 1")
    if "clear" in case.outcomes and not _checkins(events, "clear"):
        problems.append("no checkin clear message")
    got_answers = tuple(a for _, a in answers)
    if got_answers != case.answers:
        problems.append(f"answers {list(got_answers)}, expected {list(case.answers)}")
    if len(asks) != len(case.answers):
        problems.append(f"{len(asks)} asks, expected {len(case.answers)}")
    if outcomes != case.outcomes:
        problems.append(f"outcomes {list(outcomes)}, expected {list(case.outcomes)}")
    if alarm_after != case.alarm_after:
        got = "no alarm" if alarm_after is None else f"alarm after {alarm_after} answers"
        want = "no alarm" if case.alarm_after is None else f"alarm after {case.alarm_after} answers"
        problems.append(f"{got}, expected {want}")
    return {
        "case": case.id,
        "correct": not problems,
        "problems": problems,
        "first_ask_s": round(asks[0][0] - t0, 3) if asks else None,
        "alarm_s": round(alarms[0][0] - t0, 3) if alarms else None,
        "wrong_lines": _wrong_lines(case, events),
        "heard_to_rule_s": _heard_to_rule(events),
        **_counts(events),
    }


def _wrong_lines(case, events):
    """Tries 2 and 3 must use the retry lines, and the stand-up question must be standup_ask.
    checkin.py lets a planner say standup_ask on any try, so a wrong line is counted, not a wrong call."""
    lines = [m.get("script_id") for _, m in events if m.get("type") == "say" and m.get("listen_s")]
    expected = {2: RETRY_SCRIPTS[0], 3: RETRY_SCRIPTS[1]}
    if case.standup:
        expected[len(case.answers)] = STANDUP_SCRIPT
    return [f"ask {n} said {sid}, expected {expected[n]}" for n, sid in enumerate(lines, 1)
            if n in expected and sid != expected[n]]


def _heard_to_rule(events):
    """Seconds from each spoken `heard` to the agent's checkin answer: mostly the Safety Guard check,
    which runs before the rule. Silence and no_answer replies skip the guard, so they are left out."""
    gaps, spoken_at = [], None
    for t, m in events:
        if m.get("type") == "heard":
            spoken_at = t if m.get("transcript") and m.get("answer") != "no_answer" else None
        elif m.get("type") == "checkin" and m.get("state") in ANSWERS and spoken_at is not None:
            gaps.append(round(t - spoken_at, 3))
            spoken_at = None
    return gaps


def _counts(events):
    fallbacks = _agent_rows(events, "FALLBACK")
    takeovers = [m for m in _agent_rows(events, "VERIFY") if "fixed script takes over" in m["text"]
                 or "fixed script finishes" in m["text"]]
    guard = {"safe": 0, "unsafe": 0, "unreachable": 0, "mock": 0}
    for m in _agent_rows(events, tool="safety_guard"):
        text = m["text"]
        kind = ("mock" if text.startswith("MOCK") else "unreachable" if "unreachable" in text
                else "unsafe" if "unsafe" in text else "safe")
        guard[kind] += 1
    handoff = [m["text"].split(":", 1)[0].removeprefix("Hand-off note by ") for m in _agent_rows(events, "VERIFY")
               if m["text"].startswith("Hand-off note by ")]
    overrides = sum(1 for m in _agent_rows(events, "VERIFY") if m["text"].startswith("Rule override"))
    refused = sum(1 for m in _agent_rows(events, "VERIFY") if m["text"].startswith("Refused "))
    return {
        # Nemotron planned the whole run: no fallback, no fixed-script take-over, no code override, no refusal.
        "clean": not fallbacks and not takeovers and not overrides and not refused,
        "planner_calls": sum(1 for m in _agent_rows(events, "PLAN") if m["text"].startswith(HOSTED)),
        "fallbacks": len(fallbacks),
        "hosted_failures": sum(1 for m in fallbacks if m["text"].startswith(f"LLM unreachable: {HOSTED}")),
        "to_script": sum(1 for m in fallbacks if m["text"].endswith("Next: fixed script.")) + len(takeovers),
        "overrides": overrides,
        "refused": refused,
        "guard": guard,
        "handoff_by": handoff,
    }


def _stat(values, fn):
    values = [v for v in values if v is not None]
    return round(fn(values), 2) if values else None


def summarize(case, runs):
    guard = {k: sum(r["guard"][k] for r in runs) for k in ("safe", "unsafe", "unreachable", "mock")}
    return {
        "case": case.id,
        "title": case.title,
        "runs": len(runs),
        "correct": sum(r["correct"] for r in runs),
        "clean": sum(r["clean"] for r in runs),
        "fallback_runs": sum(r["fallbacks"] > 0 for r in runs),
        "first_ask_median_s": _stat([r["first_ask_s"] for r in runs], median),
        "first_ask_worst_s": _stat([r["first_ask_s"] for r in runs], max),
        "alarm_median_s": _stat([r["alarm_s"] for r in runs], median),
        "alarm_worst_s": _stat([r["alarm_s"] for r in runs], max),
        "planner_calls": sum(r["planner_calls"] for r in runs),
        "fallbacks": sum(r["fallbacks"] for r in runs),
        "to_script": sum(r["to_script"] for r in runs),
        "overrides": sum(r["overrides"] for r in runs),
        "refused": sum(r["refused"] for r in runs),
        "wrong_lines": sum(len(r["wrong_lines"]) for r in runs),
        "heard_to_rule_median_s": _stat([g for r in runs for g in r["heard_to_rule_s"]], median),
        "heard_to_rule_worst_s": _stat([g for r in runs for g in r["heard_to_rule_s"]], max),
        "guard": guard,
        "problems": sorted({p for r in runs for p in r["problems"]}),
    }


def _s(v):
    return "-" if v is None else f"{v:g} s"


def table(summaries):
    rows = ["| Case | Right call | Planned by Nemotron end to end | First ask median / worst | Alarm median / worst | Nemotron plans | "
            "Runs with a fallback | Code overrides / refused calls | Wrong ask line | Safety Guard safe / unsafe / unreachable | "
            "Reply to rule median / worst |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in summaries:
        g = s["guard"]
        rows.append(f"| {s['case']}: {s['title']} | {s['correct']} of {s['runs']} | {s['clean']} of {s['runs']} | "
                    f"{_s(s['first_ask_median_s'])} / {_s(s['first_ask_worst_s'])} | "
                    f"{_s(s['alarm_median_s'])} / {_s(s['alarm_worst_s'])} | {s['planner_calls']} | "
                    f"{s['fallback_runs']} | {s['overrides']} / {s['refused']} | {s['wrong_lines']} | "
                    f"{g['safe']} / {g['unsafe']} / {g['unreachable']} | "
                    f"{_s(s['heard_to_rule_median_s'])} / {_s(s['heard_to_rule_worst_s'])} |")
    return "\n".join(rows)
