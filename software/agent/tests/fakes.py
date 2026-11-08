"""Test doubles: a fake bus with a scripted voice, a fake LLM client, a fake guard."""

import asyncio
import json
from types import SimpleNamespace

from software.agent.checkin import Agent
from software.agent.planner import ScriptPlanner
from software.agent.settings import Settings

FAST = Settings(listen_s=0.01, heard_grace_s=0.1, recheck_unit_s=0.01)


class FakeBus:
    """Records what the agent sends. Plays the voice service: each question
    `say` pops the next scripted answer and sends back a `heard`.
    An answer is "ok" / "help" / "no_answer", None (voice stays silent),
    or a dict {answer, transcript, before: [messages sent first]}."""

    def __init__(self, answers=()):
        self.sent = []
        self.answers = list(answers)
        self.agent = None

    async def send(self, msg):
        self.sent.append(msg)
        if msg["type"] == "say" and "listen_s" in msg and self.answers:
            asyncio.get_running_loop().create_task(self._reply(self.answers.pop(0)))

    async def _reply(self, entry):
        if entry is None:
            return
        if isinstance(entry, str):
            entry = {"answer": entry}
        for m in entry.get("before", []):
            await self.agent.handle(m)
        transcript = entry.get("transcript", {"ok": "I'm okay", "help": "help me"}.get(entry["answer"], ""))
        await self.agent.handle({"type": "heard", "answer": entry["answer"], "transcript": transcript})

    def checkins(self):
        return [(m["state"], m.get("try")) for m in self.sent if m["type"] == "checkin"]

    def states(self):
        return [m["state"] for m in self.sent if m["type"] == "checkin"]

    def says(self):
        return [m["script_id"] for m in self.sent if m["type"] == "say"]

    def events(self):
        """Says and check-in states in bus order, e.g. ["ask_stopped", "help", "reply_help", "alarm"]."""
        return [m.get("script_id") or m["state"] for m in self.sent if m["type"] in ("say", "checkin")
                and m.get("state") != "asking"]

    def trace(self, step=None):
        return [m for m in self.sent if m["type"] == "agent" and (step is None or m["step"] == step)]


class FakeGuard:
    def __init__(self, unsafe=()):
        self.seen = []
        self.unsafe = set(unsafe)

    async def check(self, text):
        self.seen.append(text)
        return text not in self.unsafe, "fake guard"


class FakeNotifier:
    def __init__(self):
        self.calls = []
        self.sms = []

    async def call(self, text):
        self.calls.append(text)
        return "fake call"

    async def send_sms(self, text):
        self.sms.append(text)
        return "fake sms"


def make_agent(bus, planners=None, guard=None, settings=FAST):
    agent = Agent(
        bus=bus,
        settings=settings,
        planners=planners or [ScriptPlanner()],
        guard=guard or FakeGuard(),
        notifier=FakeNotifier(),
    )
    bus.agent = agent
    return agent


# ---- fake OpenAI-style client ----

def _tool_call(i, name, args):
    return SimpleNamespace(id=f"call_{i}", type="function",
                           function=SimpleNamespace(name=name, arguments=json.dumps(args)))


def tool_reply(*calls, content=None):
    tcs = [_tool_call(i, n, a) for i, (n, a) in enumerate(calls)]
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=tcs or None))])


def text_reply(text):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text, tool_calls=None))])


def last_result(messages):
    """The JSON object in the latest tool result, or None at the start."""
    for m in reversed(messages):
        if m["role"] == "tool" or (m["role"] == "user" and m["content"].startswith("Result of")):
            c = m["content"]
            return json.loads(c[c.index("{"):])
        if m["role"] == "user":
            return None
    return None


def cooperative(messages):
    """Follows the `next` hint the box puts in every tool result."""
    r = last_result(messages)
    if r is None:
        return [("get_presence", {})]
    nxt = r["next"]
    if nxt == "speak" and r["script_id"].startswith("reply_"):
        return [("speak", {"script_id": r["script_id"]})]
    if nxt == "speak":
        return [("speak", {"script_id": r["script_id"]}), ("listen", {"seconds": 6})]
    if nxt == "listen":
        return [("listen", {"seconds": 6})]
    if nxt == "raise_alarm":
        return [("raise_alarm", {"reason": "rule demands it"})]
    return []


class FakeClient:
    """Stands in for AsyncOpenAI. `policy(messages)` returns a list of (tool, args)."""

    def __init__(self, policy=cooperative, mode="native", error=None):
        self.policy = policy
        self.mode = mode
        self.error = error
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kw):
        self.requests.append(kw)
        if self.error:
            raise self.error
        calls = self.policy(kw["messages"])
        if self.mode == "json":
            if not calls:
                return text_reply("Done.")
            name, args = calls[0]
            return text_reply("```json\n" + json.dumps({"tool": name, "args": args}) + "\n```")
        return tool_reply(*calls, content=None if calls else "Done.")
