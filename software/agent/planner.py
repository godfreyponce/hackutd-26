"""Planners pick the next tool calls. The box (checkin.py) checks every call."""

import json
import re
from dataclasses import dataclass, field
from itertools import count

from .scripts import REPLY_SCRIPTS

_ids = count(1)


@dataclass
class ToolCall:
    name: str
    args: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"call_{next(_ids)}")


@dataclass
class Plan:
    calls: list
    text: str = ""
    native: bool = True  # False: JSON mode, results go back as user messages


class PlannerUnavailable(Exception):
    pass


def parse_json_calls(text: str) -> list:
    """JSON mode: read {"tool": ..., "args": ...} (or a list of them) out of a text reply."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    text = re.sub(r"```(?:json)?", "", text)
    for candidate in _json_candidates(text):
        try:
            data = json.loads(candidate)
        except ValueError:
            continue
        items = data if isinstance(data, list) else [data]
        calls = []
        for item in items:
            if not isinstance(item, dict):
                break
            name = item.get("tool") or item.get("name")
            args = item.get("args", item.get("arguments", {}))
            if isinstance(args, str):
                try:
                    args = json.loads(args or "{}")
                except ValueError:
                    break
            if not isinstance(name, str) or not isinstance(args, dict):
                break
            calls.append(ToolCall(name, args))
        else:
            if calls:
                return calls
    return []


def _json_candidates(text):
    yield text.strip()
    for open_, close in (("[", "]"), ("{", "}")):
        start, end = text.find(open_), text.rfind(close)
        if 0 <= start < end:
            yield text[start:end + 1]
    for m in re.finditer(r"\{.*\}", text):
        yield m.group(0)


class LLMPlanner:
    """Any OpenAI-compatible endpoint: hosted Nemotron or local Ollama."""

    def __init__(self, label, client, model, extra_body=None):
        self.label = label
        self.client = client
        self.model = model
        self.extra_body = extra_body

    async def plan(self, messages, tools, box) -> Plan:
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.6,
                top_p=0.95,
                **({"extra_body": self.extra_body} if self.extra_body else {}),
            )
            msg = resp.choices[0].message
            text = (msg.content or "").strip()
            if msg.tool_calls:
                calls = [ToolCall(tc.function.name, _args(tc.function.arguments), tc.id) for tc in msg.tool_calls]
                if not all(isinstance(c.name, str) for c in calls):
                    raise ValueError("a tool call has no name")
                return Plan(calls, text, native=True)
            return Plan(parse_json_calls(text), text, native=False)
        except Exception as e:  # any failure, a reply it cannot read included, means: hand over to the next planner
            raise PlannerUnavailable(f"{type(e).__name__}: {e}") from e


def _args(raw):
    try:
        args = json.loads(raw or "{}")
    except ValueError:
        return {}
    return args if isinstance(args, dict) else {}


class MissingKeyPlanner:
    """Stands in for the hosted planner when NVIDIA_API_KEY is not set."""

    def __init__(self, label, reason):
        self.label = label
        self.reason = reason

    async def plan(self, messages, tools, box) -> Plan:
        raise PlannerUnavailable(self.reason)


class ScriptPlanner:
    """The fixed script. Never fails. Follows the box's own next-step hint."""

    label = "fixed script"

    async def plan(self, messages, tools, box) -> Plan:
        if not box.incident.presence_checked:
            return Plan([ToolCall("get_presence")], "Fixed script: check presence.")
        hint = box.next_hint()
        step = hint["next"]
        if step == "speak" and hint["script_id"] in REPLY_SCRIPTS.values():
            calls = [ToolCall("speak", {"script_id": hint["script_id"]})]
        elif step == "speak":
            calls = [ToolCall("speak", {"script_id": hint["script_id"]}),
                     ToolCall("listen", {"seconds": box.settings.listen_s})]
        elif step == "listen":
            calls = [ToolCall("listen", {"seconds": box.settings.listen_s})]
        elif step == "raise_alarm":
            calls = [ToolCall("raise_alarm", {"reason": box.incident.alarm_reason})]
        else:
            calls = []
        return Plan(calls, f"Fixed script: {step}.")
