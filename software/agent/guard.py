"""Nemotron Safety Guard on transcripts before they enter the planner context."""

import json
import logging

log = logging.getLogger("agent")


class SafetyGuard:
    """`check(text)` returns (safe, note). With no client it passes text through as MOCK."""

    def __init__(self, client, model, timeout_s):
        self.client = client
        self.model = model
        self.timeout_s = timeout_s

    async def check(self, text):
        if self.client is None:
            return True, "MOCK: no NVIDIA_API_KEY. Safety Guard pass-through."
        try:
            resp = await self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": text}], timeout=self.timeout_s)
            verdict = _user_safety(resp.choices[0].message.content or "")
        except Exception as e:  # fail closed: the transcript stays out of the context
            log.warning("Safety Guard failed: %s", e)
            return False, f"guard unreachable: {type(e).__name__}"
        return verdict == "safe", f"Nemotron Safety Guard says {verdict}"


def _user_safety(content):
    try:
        value = json.loads(content).get("User Safety", "")
    except (ValueError, AttributeError):
        value = content
    return "unsafe" if "unsafe" in str(value).lower() else "safe"
