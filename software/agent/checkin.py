"""The box agent. A planner proposes tool calls; this code checks each one.

Code owns the alarm rule, the 3-try cap, the stand-up re-ask and the spoken
text. The planner can add steps but can never skip an alarm the rule demands.
"""

import asyncio
import json
import logging
from datetime import datetime

from . import rule
from .handoff import HandoffWriter, build_facts
from .planner import LLMPlanner, PlannerUnavailable, ScriptPlanner
from .scripts import (ALARM_CALL_TEXT, ESCALATE_SCRIPT, REPLY_SCRIPTS, RETRY_SCRIPTS, SCRIPTS, SMS_TEMPLATES,
                      STANDUP_SCRIPT)

log = logging.getLogger("agent")

SYSTEM_PROMPT = f"""You are the planner inside a home safety box. After an event (an earthquake, or a person who stopped moving) you run a voice check-in by calling tools.
Rules you cannot change:
- The box only says fixed lines by id. Use speak(script_id). Never write what the box says.
- After each question, call listen. The box asks at most {rule.MAX_TRIES} times and picks the wording for each try.
- After an ok answer, speak reply_ok. After a help answer, speak reply_help before raise_alarm. Do not listen after a reply.
- The alarm rule is code. Every tool result has a "next" field with what the rule needs now. When next is "raise_alarm", call raise_alarm at once.
- You may add steps: notify_contact, schedule_recheck, log_decision.
- When next is "done", reply with no tool call.
If you cannot call tools natively, reply with only one JSON object: {{"tool": "<name>", "args": {{...}}}}"""


def _tool(name, description, props=None, required=()):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": props or {}, "required": list(required)}}}


def build_tools(ask_script):
    return [
        _tool("get_presence", "Latest radar state: moving, still or none."),
        _tool("speak", "Say a fixed line by id. After a question the voice service listens. "
              "reply_ok and reply_help answer an ok or help answer and need no listen.",
              {"script_id": {"type": "string", "enum": [ask_script, STANDUP_SCRIPT, *REPLY_SCRIPTS.values()]}},
              ["script_id"]),
        _tool("listen", "Wait for the answer to the last question: ok, help or no_answer, plus a transcript.",
              {"seconds": {"type": "number"}}),
        _tool("raise_alarm", "Raise the fake alarm: says the escalation line after no answers, on-screen alarm, call to a teammate. Only when the rule demands it.",
              {"reason": {"type": "string"}}, ["reason"]),
        _tool("notify_contact", "Text a contact a fixed template by id.",
              {"template_id": {"type": "string", "enum": list(SMS_TEMPLATES)}}, ["template_id"]),
        _tool("schedule_recheck", "Start a new check-in after this many minutes.",
              {"minutes": {"type": "number"}}, ["minutes"]),
        _tool("log_decision", "Write an audit row: inputs, rule, action.",
              {"reason": {"type": "string"}}, ["reason"]),
    ]


class Incident:
    """One event, from trigger until ok, clear, no alarm, or reset."""

    def __init__(self, trigger, peak_g=None):
        self.trigger = trigger
        self.peak_g = peak_g
        self.goal = "checkin"  # or "standup": one "Are you okay?" after the alarm
        self.tries = 0
        self.answers = []
        self.heard_log = []  # (try, answer, screened transcript) for the hand-off note
        self.pending = None  # script id of a question waiting for its answer
        self.reply_due = None  # reply script id the last answer still needs
        self.reply_due_turn = None
        self.heard = asyncio.Queue()
        self.alarm_due_turn = None
        self.alarm_reason = ""
        self.alarm_raised = False
        self.stood_up = False
        self.standup_pending = False
        self.outcome = None  # ok | clear | no_alarm | alarm
        self.presence_checked = False
        self.run_answered = False

    @property
    def open(self):
        return self.outcome in (None, "alarm")

    @property
    def alarm_due(self):
        return self.alarm_due_turn is not None and not self.alarm_raised

    def finished(self):
        if self.reply_due:
            return False
        if self.outcome in ("ok", "clear", "no_alarm"):
            return True
        if self.goal == "checkin":
            return self.alarm_raised
        return self.run_answered and not self.alarm_due


class Agent:
    def __init__(self, bus, settings, planners, guard, notifier, ranker=None, writer=None):
        self.bus = bus
        self.settings = settings
        if not isinstance(planners[-1], ScriptPlanner):
            planners = [*planners, ScriptPlanner()]
        self.planners = planners
        self.guard = guard
        self.notifier = notifier
        self.ranker = ranker
        self.writer = writer or HandoffWriter(None, None, settings.planner_timeout_s)
        self.tools = build_tools(settings.ask_script)
        self.presence = "none"
        self.battery_pct = None
        self.power = None
        self.alert = None
        self.incident = None
        self.task = None
        self.rechecks = []
        self._handlers = {
            "get_presence": self._get_presence, "speak": self._speak, "listen": self._listen,
            "raise_alarm": self._raise_alarm_tool, "notify_contact": self._notify_contact,
            "schedule_recheck": self._schedule_recheck, "log_decision": self._log_decision,
        }

    # ---- bus ----

    async def handle(self, msg):
        kind = msg.get("type")
        if kind == "presence":
            await self._on_presence(msg.get("state"))
        elif kind in ("quake", "fall_hint"):
            self._start_checkin(kind, msg.get("peak_g"))
        elif kind == "heartbeat":
            self.battery_pct = msg.get("battery_pct")
        elif kind == "power":
            self.power = msg.get("state")
        elif kind == "alert":
            self.alert = msg
        elif kind == "heard":
            inc = self.incident
            if inc and inc.pending:
                inc.heard.put_nowait(msg)
        elif kind == "reset":
            self.reset()
        elif kind == "queue" and self.ranker:
            asyncio.get_running_loop().create_task(self.ranker.handle(msg))

    async def send(self, msg):
        await self.bus.send(msg)

    async def trace(self, step, text, tool=None):
        log.info("%-8s %s", step, text)
        msg = {"type": "agent", "step": step, "text": text}
        if tool:
            msg["tool"] = tool
        await self.send(msg)

    async def idle(self):
        """Wait until no check-in is running (tests and the CLI use this)."""
        while self.task is not None and not self.task.done():
            task = self.task
            try:
                await task
            except asyncio.CancelledError:
                if not task.cancelled():
                    raise

    def reset(self):
        if self.task and not self.task.done():
            self.task.cancel()
        for handle in self.rechecks:
            handle.cancel()
        self.rechecks.clear()
        self.incident = None
        self.presence = "none"
        self.battery_pct = self.power = self.alert = None
        log.info("reset: check-in cleared")

    # ---- triggers ----

    def _start_checkin(self, trigger, peak_g=None):
        if self.incident and self.incident.open:
            log.info("%s while a check-in is open, ignored", trigger)
            return
        self.incident = Incident(trigger, peak_g)
        self._launch("checkin")

    def _launch(self, goal):
        inc = self.incident
        inc.goal = goal
        inc.presence_checked = False
        inc.run_answered = False
        self.task = asyncio.get_running_loop().create_task(self._run(inc))

    async def _on_presence(self, state):
        prev, self.presence = self.presence, state
        inc = self.incident
        if not (inc and inc.open and prev == "still" and state == "moving"):
            return
        inc.stood_up = True
        await self.trace("VERIFY", "Stand-up: radar went from still to moving. Next question: \"Are you okay?\"")
        if inc.alarm_raised:
            if self.task and not self.task.done():
                inc.standup_pending = True
            else:
                self._launch("standup")

    # ---- the loop ----

    async def _run(self, inc):
        chain = list(self.planners)
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": self._brief(inc)}]
        turn = 0
        while not inc.finished():
            planner = chain[0]
            if turn >= self.settings.max_planner_turns and len(chain) > 1:
                await self.trace("VERIFY", f"{planner.label} hit the turn cap. The fixed script finishes the check-in.")
                chain = chain[-1:]
                continue
            try:
                plan = await asyncio.wait_for(planner.plan(messages, self.tools, self), self.settings.planner_timeout_s)
            except (PlannerUnavailable, TimeoutError) as e:
                reason = str(e) or f"no reply in {self.settings.planner_timeout_s:g} s"
                chain.pop(0)
                text = reason if reason.startswith("MOCK") else f"LLM unreachable: {planner.label} ({reason})"
                await self.trace("FALLBACK", f"{text}. Next: {chain[0].label}.")
                continue
            names = ", ".join(c.name for c in plan.calls) or "no tool call"
            mode = " (JSON mode)" if isinstance(planner, LLMPlanner) and not plan.native else ""
            await self.trace("PLAN", f"{planner.label}{mode}: {names}")
            if plan.calls:
                messages.append(_assistant_msg(plan))
                for call in plan.calls:
                    result = await self._execute(call, inc, turn)
                    messages.append(_result_msg(call.name, call.id, result, plan.native))
            await self._enforce(inc, turn)
            if not plan.calls and not inc.finished():
                await self.trace("VERIFY", f"{planner.label} stopped before the check-in finished. The fixed script takes over.")
                chain = chain[-1:]
            turn += 1
        if inc.goal == "checkin" and inc.alarm_raised:
            await self._handoff(inc)
        if isinstance(chain[0], LLMPlanner):
            await self._follow_up(chain[0], messages, inc, turn)
        await self.trace("VERIFY", self._decision_text(inc), "log_decision")
        if inc.standup_pending and inc.open:
            inc.standup_pending = False
            self._launch("standup")

    async def _follow_up(self, planner, messages, inc, turn):
        """One more planner turn after the outcome, for added steps like notify_contact."""
        result = {"outcome": inc.outcome, "next": "done",
                  "may_add": ["notify_contact", "schedule_recheck", "log_decision"]}
        messages.append({"role": "user", "content": f"Result of check-in: {json.dumps(result)}"})
        try:
            plan = await asyncio.wait_for(planner.plan(messages, self.tools, self), self.settings.planner_timeout_s)
        except (PlannerUnavailable, TimeoutError) as e:
            log.info("follow-up skipped: %s", e)
            return
        for call in plan.calls:
            await self._execute(call, inc, turn)

    async def _enforce(self, inc, turn):
        if inc.reply_due and inc.reply_due_turn < turn:
            await self.trace("VERIFY", f"Rule override: the answer needs {inc.reply_due} and the planner skipped it. "
                             "Speaking it in code.", "speak")
            await self._say_reply(inc)
        elif inc.alarm_due and inc.alarm_due_turn < turn:
            await self.trace("VERIFY", "Rule override: the rule demands an alarm and the planner skipped it. Raising it in code.",
                             "raise_alarm")
            await self._raise_alarm(inc, inc.alarm_reason)

    async def _execute(self, call, inc, turn):
        await self.trace("ACT", f"{call.name}({_fmt(call.args)})", call.name)
        handler = self._handlers.get(call.name)
        result = await handler(inc, turn, call.args) if handler else {"error": f"unknown tool {call.name}"}
        if "error" in result:
            await self.trace("VERIFY", f"Refused {call.name}: {result['error']}", call.name)
        return {**result, **self.next_hint()}

    def next_hint(self):
        inc = self.incident
        if inc.reply_due:
            return {"next": "speak", "script_id": inc.reply_due}
        if inc.alarm_due:
            return {"next": "raise_alarm"}
        if inc.finished():
            return {"next": "done"}
        if inc.pending:
            return {"next": "listen"}
        return {"next": "speak", "script_id": self._question_id(inc)}

    def _question_id(self, inc):
        return STANDUP_SCRIPT if inc.goal == "standup" or inc.stood_up else self.settings.ask_script

    def _brief(self, inc):
        if inc.goal == "standup":
            return ("The person stood up after the alarm (radar went from still to moving). "
                    f"Ask {STANDUP_SCRIPT} once and listen. An ok answer clears the alarm.")
        return (f"Event: {inc.trigger}. Radar presence now: {self.presence}. Start the check-in. "
                "Tool results tell you what the rule needs next.")

    def _decision_text(self, inc):
        someone = "someone detected" if rule.someone_detected(self.presence) else "nobody detected"
        answers = ", ".join(inc.answers) or "none"
        return (f"Decision: trigger {inc.trigger}; radar {self.presence} ({someone}); "
                f"answers {answers}; outcome {inc.outcome}.")

    # ---- tools ----

    async def _get_presence(self, inc, turn, args):
        inc.presence_checked = True
        return {"presence": self.presence}

    async def _speak(self, inc, turn, args):
        sid = args.get("script_id")
        allowed = (STANDUP_SCRIPT,) if inc.goal == "standup" else (self.settings.ask_script, STANDUP_SCRIPT)
        if inc.finished():
            return {"error": "the check-in is over"}
        if sid in REPLY_SCRIPTS.values() or inc.reply_due:
            return await self._speak_reply(inc, turn, sid)
        if inc.alarm_due:
            return {"error": "the rule demands an alarm. Call raise_alarm."}
        if sid not in allowed:
            return {"error": f"script_id must be one of {list(allowed)}. The escalation line is said by raise_alarm."}
        if inc.pending:
            return {"error": "a question is waiting for its answer. Call listen."}
        if inc.goal == "standup":
            if inc.run_answered:
                return {"error": "one stand-up question per re-ask"}
            try_n = 1
        else:
            if inc.tries >= rule.MAX_TRIES:
                return {"error": f"the box asks at most {rule.MAX_TRIES} times"}
            inc.tries += 1
            try_n = inc.tries
            if sid == self.settings.ask_script:
                sid = (sid, *RETRY_SCRIPTS)[try_n - 1]
        while not inc.heard.empty():
            inc.heard.get_nowait()
        inc.pending = sid
        await self.send({"type": "checkin", "state": "asking", "try": try_n})
        await self.send({"type": "say", "script_id": sid, "text": SCRIPTS[sid], "listen_s": self.settings.listen_s})
        return {"spoken": sid, "try": try_n}

    async def _speak_reply(self, inc, turn, sid):
        if sid != inc.reply_due:
            if inc.reply_due:
                return {"error": f"the last answer needs {inc.reply_due} first"}
            return {"error": "reply_ok only follows an ok answer and reply_help only a help answer"}
        await self._say_reply(inc)
        if inc.alarm_due:
            inc.alarm_due_turn = turn  # one more turn to call raise_alarm, counted from the reply
        return {"spoken": sid}

    async def _say_reply(self, inc):
        sid, inc.reply_due = inc.reply_due, None
        await self.send({"type": "say", "script_id": sid, "text": SCRIPTS[sid]})

    async def _listen(self, inc, turn, args):
        if not inc.pending:
            return {"error": "ask a question with speak first"}
        wait = self.settings.listen_s + self.settings.heard_grace_s
        try:
            msg = await asyncio.wait_for(inc.heard.get(), wait)
        except TimeoutError:
            await self.trace("VERIFY", f"No answer from the voice service in {wait:g} s. Counting it as no_answer.", "listen")
            msg = {"answer": "no_answer", "transcript": ""}
        inc.pending = None
        answer = msg.get("answer")
        if answer not in rule.ANSWERS:
            await self.trace("VERIFY", f"Unknown answer {answer!r}. Counting it as no_answer.", "listen")
            answer = "no_answer"
        transcript = await self._screen(msg.get("transcript") or "")
        try_n = 1 if inc.goal == "standup" else inc.tries
        inc.answers.append(answer)
        inc.heard_log.append((try_n, answer, transcript))
        inc.run_answered = True
        await self.send({"type": "checkin", "state": answer, "try": try_n})
        if answer in REPLY_SCRIPTS:
            inc.reply_due = REPLY_SCRIPTS[answer]
            inc.reply_due_turn = turn
        await self._apply_rule(inc, turn, answer, try_n)
        return {"answer": answer, "transcript": transcript, "presence": self.presence, "stood_up": inc.stood_up}

    async def _apply_rule(self, inc, turn, answer, try_n):
        someone = rule.someone_detected(self.presence)
        verdict = rule.decide(someone, answer)
        who = "someone detected" if someone else "nobody detected"
        if verdict == rule.LOG_OK:
            if inc.stood_up or inc.goal == "standup":
                inc.outcome = "clear"
                await self.send({"type": "checkin", "state": "clear", "try": try_n})
                await self.trace("VERIFY", "Rule: answer ok after stand-up. Log it, clear the alert.")
            else:
                inc.outcome = "ok"
                await self.trace("VERIFY", "Rule: answer ok. Log it, no alarm.")
        elif verdict == rule.NO_ALARM:
            inc.outcome = "no_alarm"
            await self.trace("VERIFY", "Rule: nobody detected + no answer = no alarm.")
        elif inc.alarm_raised:
            await self.trace("VERIFY", f"Rule: {who} + {answer}. The alarm stays up.")
        elif answer == "help":
            await self._alarm_due(inc, turn, "the answer was help")
        elif inc.tries < rule.MAX_TRIES:
            await self.trace("VERIFY", f"Rule: {who} + no answer, try {inc.tries} of {rule.MAX_TRIES}. Ask again.")
        else:
            await self._alarm_due(inc, turn, f"{who} + no answer after {rule.MAX_TRIES} tries")

    async def _alarm_due(self, inc, turn, reason):
        inc.alarm_due_turn = turn
        inc.alarm_reason = reason
        await self.trace("VERIFY", f"Rule: {reason} = alarm. Next: raise_alarm.")

    async def _screen(self, transcript):
        """Safety Guard on every transcript before it enters the planner context."""
        if not transcript:
            return ""
        safe, note = await self.guard.check(transcript)
        if note.startswith("MOCK"):
            await self.trace("VERIFY", note, "safety_guard")
        else:
            await self.trace("VERIFY", f"Safety Guard: {'safe' if safe else 'unsafe, withheld from the planner'} ({note}).",
                             "safety_guard")
        return transcript if safe else "[withheld by Safety Guard]"

    async def _raise_alarm_tool(self, inc, turn, args):
        if not inc.alarm_due:
            return {"error": "the alarm rule does not call for an alarm now"}
        await self._raise_alarm(inc, str(args.get("reason") or inc.alarm_reason))
        return {"alarm": "raised"}

    async def _raise_alarm(self, inc, reason):
        if inc.reply_due:
            await self.trace("VERIFY", f"Rule override: {inc.reply_due} comes before the alarm and the planner "
                             "skipped it. Speaking it in code.", "speak")
            await self._say_reply(inc)
        inc.alarm_raised = True
        inc.outcome = "alarm"
        # After a help answer, reply_help already told the person; "I haven't heard back" would be wrong.
        if inc.answers[-1] != "help":
            await self.send({"type": "say", "script_id": ESCALATE_SCRIPT, "text": SCRIPTS[ESCALATE_SCRIPT]})
        await self.send({"type": "checkin", "state": "alarm", "try": inc.tries + 1})
        how = await self.notifier.call(ALARM_CALL_TEXT)
        await self.trace("VERIFY", f"Fake alarm raised ({reason}). On-screen alarm sent. {how}", "raise_alarm")

    async def _handoff(self, inc):
        """After the alarm: Nemotron's note for responders and its why. Code checks both."""
        facts = build_facts(trigger=inc.trigger, peak_g=inc.peak_g, presence=self.presence, answers=inc.heard_log,
                            battery_pct=self.battery_pct, power=self.power, alert=self.alert,
                            reason=inc.alarm_reason, at=datetime.now().strftime("%H:%M"))
        await self.trace("ACT", f"write_handoff(home={facts['home']!r})", "write_handoff")
        await self.trace("ACT", "explain_alarm(reasoning='on')", "explain_alarm")
        h = await self.writer.write(facts)
        for step, text, tool in h.rows:
            await self.trace(step, text, tool)
        await self.send(h.event())
        contact = h.event()["contact"]
        await self.trace("VERIFY", f"Hand-off note by {h.by}: {h.note} Contact first: {contact['name']} "
                         f"({contact['role']}).", "write_handoff")
        await self.trace("VERIFY", f"Why by {h.why_by}: {' '.join(h.why)}", "explain_alarm")

    async def _notify_contact(self, inc, turn, args):
        tid = args.get("template_id")
        if tid not in SMS_TEMPLATES:
            return {"error": f"template_id must be one of {list(SMS_TEMPLATES)}"}
        expected = self._contact_template(inc)
        if expected and tid != expected:
            await self.trace("VERIFY", f"Rule override: the contact text must say what happened ({expected}), "
                             f"not {tid}.", "notify_contact")
            tid = expected
        return {"sms": await self.notifier.send_sms(SMS_TEMPLATES[tid])}

    @staticmethod
    def _contact_template(inc):
        if inc.outcome == "alarm":
            return "said_help" if inc.answers and inc.answers[-1] == "help" else "no_response"
        if inc.outcome in ("ok", "clear"):
            return "answered_ok"
        return None

    async def _schedule_recheck(self, inc, turn, args):
        minutes = args.get("minutes")
        if not isinstance(minutes, (int, float)) or minutes <= 0:
            return {"error": "minutes must be a positive number"}
        delay = minutes * self.settings.recheck_unit_s
        self.rechecks.append(asyncio.get_running_loop().call_later(delay, self._start_checkin, "recheck"))
        return {"recheck_in_min": minutes}

    async def _log_decision(self, inc, turn, args):
        return {"logged": True}


def _fmt(args):
    return ", ".join(f"{k}={v!r}" for k, v in args.items())


def _assistant_msg(plan):
    if not plan.native:
        return {"role": "assistant", "content": plan.text}
    return {"role": "assistant", "content": plan.text or None, "tool_calls": [
        {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(c.args)}}
        for c in plan.calls]}


def _result_msg(name, call_id, result, native):
    if native:
        return {"role": "tool", "tool_call_id": call_id, "content": json.dumps(result)}
    return {"role": "user", "content": f"Result of {name}: {json.dumps(result)}"}
