"""Bus client: on `say`, speak; with `listen_s`, listen, classify and send one `heard`.

The agent (#15) owns the tries, the alarm rule and the script text. This client never
decides an alarm.
"""

import asyncio
import json

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from software.voice.classify import classify


class VoiceService:
    def __init__(self, engine, log=print):
        self.engine = engine
        self.log = log
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
        elif msg.get("type") == "reset":
            self.resets += 1
            while not self.queue.empty():
                self.queue.get_nowait()
            self.log("reset: dropped queued and in-flight lines")

    async def _work(self, ws):
        while True:
            msg = await self.queue.get()
            reset_mark = self.resets
            text = msg.get("text", "")
            self.log(f"SAY [{msg.get('script_id')}] {text}")
            await asyncio.to_thread(self.engine.speak, text)
            listen_s = msg.get("listen_s")
            if not listen_s:
                continue
            transcript = await asyncio.to_thread(self.engine.listen, listen_s)
            if self.resets != reset_mark:
                continue
            heard = {"type": "heard", "answer": classify(transcript), "transcript": transcript}
            self.log(f"HEARD {heard['answer']}: {transcript!r}")
            await ws.send(json.dumps(heard))
