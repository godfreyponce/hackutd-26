"""Run the box agent against the hub: python -m software.agent"""

import asyncio
import json
import logging
import os

from openai import AsyncOpenAI
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from .checkin import Agent
from .guard import SafetyGuard
from .handoff import HandoffWriter
from .notify import Notifier
from .planner import LLMPlanner, MissingKeyPlanner, ScriptPlanner
from .settings import Settings

log = logging.getLogger("agent")


class HubBus:
    def __init__(self):
        self.ws = None

    async def send(self, msg):
        if self.ws is None:
            log.warning("hub not connected, dropped %s", msg.get("type"))
            return
        try:
            await self.ws.send(json.dumps(msg))
        except ConnectionClosed:
            log.warning("hub closed, dropped %s", msg.get("type"))


def build_agent(settings, bus, env=os.environ):
    hosted_label = "hosted Nemotron 30B"
    if settings.nvidia_api_key:
        hosted = AsyncOpenAI(base_url=settings.nvidia_base_url, api_key=settings.nvidia_api_key,
                             max_retries=0, timeout=settings.planner_timeout_s)
        first = LLMPlanner(hosted_label, hosted, settings.planner_model,
                           extra_body={"chat_template_kwargs": {"enable_thinking": False}})
        guard = SafetyGuard(hosted, settings.guard_model, settings.planner_timeout_s)
        writer = HandoffWriter(hosted, settings.planner_model, settings.planner_timeout_s)
    else:
        log.warning("MOCK: no NVIDIA_API_KEY. Hosted Nemotron and Safety Guard run in mock mode.")
        first = MissingKeyPlanner(hosted_label, "MOCK: no NVIDIA_API_KEY, hosted Nemotron skipped")
        guard = SafetyGuard(None, settings.guard_model, settings.planner_timeout_s)
        writer = HandoffWriter(None, None, settings.planner_timeout_s)
    local = AsyncOpenAI(base_url=settings.local_base_url, api_key="ollama",
                        max_retries=0, timeout=settings.planner_timeout_s)
    planners = [
        first,
        LLMPlanner("local Nemotron 4B", local, settings.local_model, extra_body={"reasoning_effort": "none"}),
        ScriptPlanner(),
    ]
    notifier = Notifier(env)
    if notifier.mock:
        log.warning(notifier.mock)
    return Agent(bus, settings, planners, guard, notifier, writer=writer)


async def run(settings):
    bus = HubBus()
    agent = build_agent(settings, bus)
    log.info("ask line: %s", settings.ask_script)
    while True:
        try:
            async with connect(settings.hub_url) as ws:
                bus.ws = ws
                log.info("connected to %s", settings.hub_url)
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except ValueError:
                        continue
                    if isinstance(msg, dict):
                        await agent.handle(msg)
        except (OSError, ConnectionClosed) as e:
            log.warning("hub %s: %s. Retrying in 1 s.", settings.hub_url, e)
        bus.ws = None
        await asyncio.sleep(1)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    for noisy in ("httpx", "openai", "websockets"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    try:
        asyncio.run(run(Settings.from_env()))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
