import asyncio
import json
import threading

from websockets.asyncio.client import connect
from websockets.asyncio.server import broadcast, serve

from software.voice.service import VoiceService


class FakeEngine:
    def __init__(self, transcripts, block=None):
        self.transcripts = list(transcripts)
        self.block = block
        self.spoken = []
        self.listens = []

    def speak(self, text):
        self.spoken.append(text)

    def listen(self, seconds):
        self.listens.append(seconds)
        if self.block:
            self.block.wait(5)
        return self.transcripts.pop(0)


async def fake_bus():
    """Test-only stand-in for the #19 hub: re-broadcast every message to every client."""
    clients = set()

    async def handler(ws):
        clients.add(ws)
        try:
            async for msg in ws:
                broadcast(clients, msg)
        finally:
            clients.discard(ws)

    server = await serve(handler, "localhost", 0)
    port = server.sockets[0].getsockname()[1]
    return server, f"ws://localhost:{port}", clients


async def wait_for(cond, timeout=5):
    async with asyncio.timeout(timeout):
        while not cond():
            await asyncio.sleep(0.01)


async def next_heard(ws, timeout=5):
    async with asyncio.timeout(timeout):
        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == "heard":
                return msg


def run_with_service(engine, body):
    async def main():
        server, url, clients = await fake_bus()
        service = VoiceService(engine, log=lambda line: None)
        task = asyncio.create_task(service.run(url))
        try:
            async with connect(url) as ws:
                await wait_for(lambda: len(clients) == 2)
                await body(ws, service)
        finally:
            task.cancel()
            server.close()

    asyncio.run(main())


def say(ws, text, listen_s=None):
    msg = {"type": "say", "script_id": "test", "text": text}
    if listen_s is not None:
        msg["listen_s"] = listen_s
    return ws.send(json.dumps(msg))


def test_say_with_listen_sends_one_heard_and_say_without_listen_sends_none():
    engine = FakeEngine(["I'm okay", "help me"])

    async def body(ws, service):
        await say(ws, "Contacting emergency services now.")
        await say(ws, "Are you okay?", listen_s=6)
        first = await next_heard(ws)
        await say(ws, "Are you okay?", listen_s=4)
        second = await next_heard(ws)
        assert first == {"type": "heard", "answer": "ok", "transcript": "I'm okay"}
        assert second == {"type": "heard", "answer": "help", "transcript": "help me"}
        assert engine.spoken == ["Contacting emergency services now.", "Are you okay?", "Are you okay?"]
        assert engine.listens == [6, 4]

    run_with_service(engine, body)


def test_silence_gives_no_answer():
    engine = FakeEngine([""])

    async def body(ws, service):
        await say(ws, "Are you okay?", listen_s=6)
        assert await next_heard(ws) == {"type": "heard", "answer": "no_answer", "transcript": ""}

    run_with_service(engine, body)


def test_reset_drops_the_answer_in_flight():
    release = threading.Event()
    engine = FakeEngine(["help", "yes"], block=release)

    async def body(ws, service):
        await say(ws, "Are you okay?", listen_s=6)
        await wait_for(lambda: engine.listens)
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)
        release.set()
        await say(ws, "Are you okay?", listen_s=6)
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}

    run_with_service(engine, body)


class BrokenAudioEngine(FakeEngine):
    def __init__(self, transcripts, broken):
        super().__init__(transcripts)
        self.broken = broken

    def speak(self, text):
        super().speak(text)
        if text in self.broken:
            raise OSError("audio device unplugged")


def test_audio_error_answers_no_answer_and_keeps_the_worker_alive():
    engine = BrokenAudioEngine(["yes"], broken={"Contacting emergency services now.", "Can you hear me?"})

    async def body(ws, service):
        await say(ws, "Contacting emergency services now.")
        await say(ws, "Can you hear me?", listen_s=6)
        assert await next_heard(ws) == {"type": "heard", "answer": "no_answer", "transcript": ""}
        await say(ws, "Are you okay?", listen_s=6)
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}

    run_with_service(engine, body)
