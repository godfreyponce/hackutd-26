"""Twilio call and SMS, only to TWILIO_TO (a verified teammate phone). Never an emergency number."""

import logging
import os
import re
from xml.sax.saxutils import escape

import httpx

log = logging.getLogger("agent")

TWILIO_VARS = ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM", "TWILIO_TO")
# E.164 with at least 10 digits. Short numbers like 911, 112 or 999 can never match.
_PHONE = re.compile(r"\+\d{10,15}")
# A clear US English neural voice for the call (twilio.com/docs/voice/twiml/say/text-speech).
CALL_VOICE = os.environ.get("TWILIO_VOICE", "Polly.Matthew-Neural")


class Notifier:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        missing = [v for v in TWILIO_VARS if not env.get(v)]
        self.sid, self.token, self.from_, self.to = (env.get(v) for v in TWILIO_VARS)
        if missing:
            self.mock = f"MOCK: no {', '.join(missing)}. On-screen alarm only."
        elif not _PHONE.fullmatch(self.to):
            self.mock = "MOCK: TWILIO_TO is not a full phone number in +1XXXXXXXXXX form. On-screen alarm only."
        else:
            self.mock = None

    async def call(self, text, stream_url=None):
        """Say the text. With stream_url (hardware/call/bridge.py), the call then stays open as a live two-way
        audio stream through the box speaker and mics."""
        twiml = f'<Response><Say voice="{CALL_VOICE}">{escape(text)}</Say>'
        if stream_url:
            twiml += f'<Connect><Stream url="{escape(stream_url)}"/></Connect>'
        return await self._post("Calls.json", {"Twiml": twiml + "</Response>"}, "call")

    async def send_sms(self, text):
        return await self._post("Messages.json", {"Body": text}, "SMS")

    async def _post(self, path, data, what):
        if self.mock:
            return self.mock
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/{path}"
        try:
            # 10 s is a guess; the alarm is already on screen before this call.
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(url, auth=(self.sid, self.token), data={"To": self.to, "From": self.from_, **data})
            r.raise_for_status()
        except httpx.HTTPError as e:
            log.warning("Twilio %s failed: %s", what, e)
            return f"Twilio {what} failed ({type(e).__name__})."
        return f"Twilio {what} placed to the teammate phone ending {self.to[-4:]}."
