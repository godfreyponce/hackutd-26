"""The hand-off note and the why, after an alarm. Nemotron writes them; code checks them.

Code gives the facts. A note or why that adds a number, names an emergency number
or runs long is dropped for a plain template. The alarm rule never depends on this.
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass, field

from .scripts import DEMO_TEXT, HANDOFF_CONTACTS

HOME_ID = "H000"  # the real box (contract addendum v1)
MAX_WORDS = 60  # the brief asks for about 60 words
MAX_WHY_LINES = 3
# Measured on hosted Nemotron 3.5 Lightning: 200 gave 1.8 s and clean lines. No budget took 11 to 18 s.
WHY_REASONING_BUDGET = 200

_NUMBER = re.compile(r"\d+(?:\.\d+)?")
# The short numbers notify.py guards against, as digits or spoken.
_EMERGENCY = re.compile(r"(?<![\w.])(?:911|112|999)(?!\w|\.\d)|nine[\s-]*one[\s-]*one", re.I)
_BANNED_WORDS = re.compile(r"\b(?:fall|falls|fell|fallen|radar)\b", re.I)
_THINK = re.compile(r"<think>.*?</think>", re.S)

RULE_TEXT = ("Nobody detected + no answer = no alarm. Someone detected + no answer after 3 tries = alarm. "
             "Help = alarm. Okay = log it, no alarm.")

NOTE_PROMPT = f"""You write a short hand-off note for responders after a fake alarm from a home safety box.
Use only the facts given. Copy every number exactly as it is in the facts. Add no other number.
Never write a phone number or an emergency number. Say "no response after an event", never "fall detection".
Write 3 or 4 plain short sentences, under {MAX_WORDS} words. Use plain words, not field names.
When the alert has demo true, write "{DEMO_TEXT}." in the note.
Pick who to contact first from the contacts, by id.
Reply with only one JSON object: {{"note": "...", "contact": "<contact id>"}}"""

WHY_PROMPT = f"""A home safety box raised a fake alarm. Code made the decision with a fixed rule; you do not decide.
Explain why the rule raised the alarm, from the facts only, in at most {MAX_WHY_LINES} short lines.
Use plain words, not field names. Copy every number exactly as it is in the facts. Never write a phone number or an emergency number.
Reply with only the lines."""


def build_facts(*, trigger, peak_g, presence, answers, battery_pct, power, alert, reason, at):
    """answers: (try, answer, transcript) in order. alert: the last `alert` message or None."""
    event = {"quake": "earthquake", "fall_hint": "presence sensor saw the person go from moving to still",
             "recheck": "scheduled recheck", "alert": "emergency alert",
             "help_gesture": "camera saw the help sign"}.get(trigger, trigger)
    return {
        "home": HOME_ID,
        "time": at,
        "trigger": {"event": event, **({"peak_g": peak_g} if peak_g is not None else {})},
        "presence": presence,
        "someone_detected": presence in ("moving", "still"),
        "answers": [{"try": n, "answer": a, "transcript": t} for n, a, t in answers],
        "battery_pct": battery_pct,
        "power": power,
        "alert": {**{k: alert.get(k) for k in ("source", "event", "headline")},
                  **{k: alert[k] for k in ("code", "level", "demo") if k in alert}} if alert else None,
        "alarm_reason": reason,
    }


def check_note(text, facts):
    """None when the text is fine, else the problem."""
    words = len(text.split())
    if not words:
        return "empty"
    if words > MAX_WORDS:
        return f"{words} words, over {MAX_WORDS}"
    if _EMERGENCY.search(text):
        return "names an emergency number"
    if _BANNED_WORDS.search(text):
        return "says fall or radar"
    if (facts.get("alert") or {}).get("demo") and DEMO_TEXT.lower() not in text.lower():
        return f"does not say {DEMO_TEXT}"
    known = set(_NUMBER.findall(json.dumps(facts)))
    for number in _NUMBER.findall(text):
        if number not in known:
            return f"{number} is not in the facts"
    return None


def _said_help(facts):
    return bool(facts["answers"]) and facts["answers"][-1]["answer"] == "help"


def template_note(facts, contact_id):
    trigger = facts["trigger"]
    event = trigger["event"] + (f", peak {trigger['peak_g']} g" if "peak_g" in trigger else "")
    what = "the person said help after an event" if _said_help(facts) else "no response after an event"
    who = "someone detected" if facts["someone_detected"] else "nobody detected"
    answers = ", ".join(f"try {a['try']} {a['answer'].replace('_', ' ')}" for a in facts["answers"]) or "none"
    parts = [f"{facts['home']}: {what} ({event}).", f"Presence sensor: {facts['presence']}, {who}.", f"Answers: {answers}."]
    if facts["battery_pct"] is not None:
        parts.append(f"Battery {facts['battery_pct']}%{', on battery power' if facts['power'] == 'battery' else ''}.")
    if facts["alert"]:
        alert = facts["alert"]
        if alert.get("demo"):
            parts.append(f"Alert: {alert['event']} ({alert['source']}). {DEMO_TEXT}.")
        else:
            parts.append(f"Official alert: {alert['event']} ({alert['source']}).")
    contact = HANDOFF_CONTACTS[contact_id]
    parts.append(f"Alarm at {facts['time']}. Contact {contact['name']} ({contact['role']}) first.")
    return " ".join(parts)


def template_why(facts):
    who = "someone detected" if facts["someone_detected"] else "nobody detected"
    answers = ", ".join(a["answer"].replace("_", " ") for a in facts["answers"]) or "none"
    return [f"Rule: {facts['alarm_reason']} = alarm.", f"Presence sensor: {facts['presence']}, {who}.", f"Answers: {answers}."]


@dataclass
class Handoff:
    note: str
    contact: str
    by: str  # "nemotron" | "template"
    why: list
    why_by: str
    rows: list = field(default_factory=list)  # (trace step, text, tool)

    def event(self):
        return {"type": "handoff", "home": HOME_ID, "note": self.note,
                "contact": {"id": self.contact, **HANDOFF_CONTACTS[self.contact]},
                "by": self.by, "why": self.why, "why_by": self.why_by}


class _Refused(Exception):
    pass


class HandoffWriter:
    """`write(facts)` never fails. With no client it returns the templates as MOCK."""

    def __init__(self, client, model, timeout_s, missing="MOCK: no NVIDIA_API_KEY"):
        self.client = client
        self.model = model
        self.timeout_s = timeout_s
        self.missing = missing

    async def write(self, facts):
        default = next(iter(HANDOFF_CONTACTS))
        if self.client is None:
            return Handoff(template_note(facts, default), default, "template", template_why(facts), "template",
                           [("VERIFY", f"{self.missing}. Template hand-off note and why.", "write_handoff")])
        (note, contact, note_row), (why, why_row) = await asyncio.gather(self._note(facts), self._why(facts))
        by, why_by = ("nemotron" if note else "template"), ("nemotron" if why else "template")
        contact = contact or default
        return Handoff(note or template_note(facts, contact), contact, by, why or template_why(facts), why_by,
                       [note_row, why_row])

    async def _ask(self, system, payload, thinking):
        extra = {"chat_template_kwargs": {"enable_thinking": thinking}}
        if thinking:
            extra["reasoning_budget"] = WHY_REASONING_BUDGET
        resp = await asyncio.wait_for(self.client.chat.completions.create(
            model=self.model, temperature=0.6, top_p=0.95,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(payload)}],
            extra_body=extra), self.timeout_s)
        return _THINK.sub("", resp.choices[0].message.content or "").replace("\u2014", ", ").strip()

    async def _timed(self, what, tool, ask, parse):
        start = time.perf_counter()
        try:
            value = parse(await ask())
        except _Refused as e:
            return None, ("VERIFY", f"{what} refused: {e}. Using the template.", tool)
        except Exception as e:  # any failure means: the template takes over
            reason = f"{type(e).__name__}: {e}" if str(e) else f"no reply in {self.timeout_s:g} s"
            return None, ("FALLBACK", f"LLM unreachable for the {what.lower()} ({reason}). "
                                      "Using the template.", tool)
        return value, ("VERIFY", f"{what} check passed: every number from the facts, no emergency number, "
                                 f"under {MAX_WORDS} words. Nemotron took {time.perf_counter() - start:.1f} s.", tool)

    async def _note(self, facts):
        def parse(text):
            match = re.search(r"\{.*\}", text, re.S)
            try:
                data = json.loads(match.group(0)) if match else None
            except ValueError:
                data = None
            if not isinstance(data, dict) or not isinstance(data.get("note"), str):
                raise _Refused("the reply was not JSON with a note and a contact")
            if data.get("contact") not in HANDOFF_CONTACTS:
                raise _Refused(f"contact {data.get('contact')!r} is not in the contact list")
            note = " ".join(data["note"].split())
            if problem := check_note(note, facts):
                raise _Refused(problem)
            return note, data["contact"]

        payload = {"facts": facts, "contacts": HANDOFF_CONTACTS}
        value, row = await self._timed("Hand-off note", "write_handoff", lambda: self._ask(NOTE_PROMPT, payload, False), parse)
        return (*(value or (None, None)), row)

    async def _why(self, facts):
        payload = {"rule": RULE_TEXT, "decision": "alarm",
                   **{k: facts[k] for k in ("presence", "someone_detected", "answers", "alarm_reason")}}

        def parse(text):
            lines = [re.sub(r"^(?:[-*•]|\d+[.)])\s+", "", ln.strip()) for ln in text.splitlines()]
            lines = [ln for ln in lines if ln][:MAX_WHY_LINES]
            if problem := check_note(" ".join(lines), payload):
                raise _Refused(problem)
            return lines

        return await self._timed("Why (reasoning on)", "explain_alarm", lambda: self._ask(WHY_PROMPT, payload, True), parse)
