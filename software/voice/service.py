"""Bus client: on `say`, speak; with `listen_s`, listen, classify and send one `heard`.
A `say` with `tone` "warning" (EQW alert) plays the warning tone first, then the line.
On `checkin` alarm, play the alarm tone after the line in progress; `reset` stops it.

The agent (#15) owns the tries, the alarm rule and the script text. This client never
decides an alarm.
"""

import asyncio
import json

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from software.voice.classify import classify

WARNING_TONE = "warning"


class VoiceService:
    def __init__(self, engine, log=print, alarm=None, warning=None):
        self.engine = engine
        self.log = log
        self.alarm = alarm  # None in text mode: no speaker
        self.warning = warning  # None in text mode: the log line is the marker
        self.alarm_on = False
        self.resets = 0
        self.queue: asyncio.Queue = asyncio.Queue()

    async def run(self, url: str):
        worker = None
        async for ws in connect(url):
            self.log(f"connected to {url}")
            worker = asyncio.create_task(self._work(ws))
            try:
                async for raw in ws:
                    self._on_message(raw)
            except ConnectionClosed:
                self.log("hub connection lost, reconnecting")
            finally:
                worker.cancel()

    def _on_message(self, raw):
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return
        if not isinstance(msg, dict):
            return
        if msg.get("type") == "say":
            self.queue.put_nowait(msg)
        elif msg.get("type") == "checkin" and msg.get("state") == "alarm":
            # Queued, so the tone starts after the line being spoken (the agent's last words).
            self.queue.put_nowait(msg)
        elif msg.get("type") == "reset":
            self.resets += 1
            while not self.queue.empty():
                self.queue.get_nowait()
            self.log("reset: dropped queued and in-flight lines")
            if self.alarm_on:
                self.alarm_on = False
                self._audio("stop alarm tone", self.alarm.stop)

    async def _work(self, ws):
        while True:
            msg = await self.queue.get()
            if msg.get("type") == "checkin":
                self.log("ALARM tone (fake alarm, local only, nothing is called)")
                if self.alarm:
                    self.alarm_on = True
                    self._audio("start alarm tone", self.alarm.start)
                continue
            reset_mark = self.resets
            text = msg.get("text", "")
            listen_s = msg.get("listen_s")
            if msg.get("tone") == WARNING_TONE:
                self.log("WARNING TONE (EQW alert, not the alarm)")
                if self.warning:
                    await asyncio.to_thread(self._audio, "warning tone", self.warning.play)
                if self.resets != reset_mark:
                    continue
            self.log(f"SAY [{msg.get('script_id')}] {text}")
            try:
                await asyncio.to_thread(self.engine.speak, text, msg.get("script_id"))
                transcript = await asyncio.to_thread(self.engine.listen, listen_s) if listen_s else ""
            except Exception as e:
                self.log(f"audio error on [{msg.get('script_id')}], worker continues: {e!r}")
                transcript = ""
            if not listen_s or self.resets != reset_mark:
                continue
            heard = {"type": "heard", "answer": classify(transcript), "transcript": transcript}
            self.log(f"HEARD {heard['answer']}: {transcript!r}")
            await ws.send(json.dumps(heard))

    def _audio(self, what, fn):
        try:
            fn()
        except Exception as e:
            self.log(f"audio error on {what}, worker continues: {e!r}")
