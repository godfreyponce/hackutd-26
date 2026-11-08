import asyncio
import json
import threading
import time

from websockets.asyncio.client import connect
from websockets.asyncio.server import broadcast, serve

from software.voice.service import VoiceService


class FakeEngine:
    def __init__(self, transcripts, block=None):
        self.transcripts = list(transcripts)
        self.block = block
        self.spoken = []
        self.listens = []

    def speak(self, text, script_id=None):
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


def run_with_service(engine, body, alarm=None, warning=None, log=lambda line: None):
    async def main():
        server, url, clients = await fake_bus()
        service = VoiceService(engine, log=log, alarm=alarm, warning=warning)
        task = asyncio.create_task(service.run(url))
        try:
            async with connect(url) as ws:
                await wait_for(lambda: len(clients) == 2)
                await body(ws, service)
        finally:
            task.cancel()
            server.close()

    asyncio.run(main())


def say(ws, text, listen_s=None, tone=None):
    msg = {"type": "say", "script_id": "test", "text": text}
    if listen_s is not None:
        msg["listen_s"] = listen_s
    if tone is not None:
        msg["tone"] = tone
    return ws.send(json.dumps(msg))


def test_say_with_listen_sends_one_heard_and_say_without_listen_sends_none():
    engine = FakeEngine(["I'm okay", "help me"])

    async def body(ws, service):
        await say(ws, "Alerting your emergency contact now.")
        await say(ws, "Are you okay?", listen_s=6)
        first = await next_heard(ws)
        await say(ws, "Are you okay?", listen_s=4)
        second = await next_heard(ws)
        assert first == {"type": "heard", "answer": "ok", "transcript": "I'm okay"}
        assert second == {"type": "heard", "answer": "help", "transcript": "help me"}
        assert engine.spoken == ["Alerting your emergency contact now.", "Are you okay?", "Are you okay?"]
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

    def speak(self, text, script_id=None):
        super().speak(text)
        if text in self.broken:
            raise OSError("audio device unplugged")


def test_audio_error_answers_no_answer_and_keeps_the_worker_alive():
    engine = BrokenAudioEngine(["yes"], broken={"Alerting your emergency contact now.", "Can you hear me?"})

    async def body(ws, service):
        await say(ws, "Alerting your emergency contact now.")
        await say(ws, "Can you hear me?", listen_s=6)
        assert await next_heard(ws) == {"type": "heard", "answer": "no_answer", "transcript": ""}
        await say(ws, "Are you okay?", listen_s=6)
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}

    run_with_service(engine, body)


class FakeAlarm:
    """Records start and stop instead of playing the tone."""

    def __init__(self, events):
        self.events = events

    def start(self):
        self.events.append("alarm start")

    def stop(self):
        self.events.append("alarm stop")


class OrderedEngine(FakeEngine):
    def __init__(self, transcripts, events):
        super().__init__(transcripts)
        self.events = events

    def speak(self, text, script_id=None):
        super().speak(text)
        self.events.append(f"say {script_id}")


def test_alarm_checkin_plays_the_tone_after_the_line_and_reset_stops_it():
    events = []
    engine = OrderedEngine(["yes"], events)

    async def body(ws, service):
        await say(ws, "Okay. I'm getting help now.")
        await ws.send(json.dumps({"type": "checkin", "state": "alarm", "try": 2}))
        await wait_for(lambda: "alarm start" in events)
        assert events == ["say test", "alarm start"]
        await say(ws, "Are you okay?", listen_s=6)
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: "alarm stop" in events)

    run_with_service(engine, body, alarm=FakeAlarm(events))
    assert events == ["say test", "alarm start", "say test", "alarm stop"]


def test_other_checkin_states_play_no_tone():
    events = []

    async def body(ws, service):
        for state in ("asking", "help", "no_answer", "ok", "clear"):
            await ws.send(json.dumps({"type": "checkin", "state": state, "try": 1}))
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)

    run_with_service(FakeEngine([]), body, alarm=FakeAlarm(events))
    assert events == []


# ---- EQW warning tone (#64) ----

class FakeWarning:
    """Records the warning tone instead of playing it."""

    def __init__(self, events, broken=False, hold=None):
        self.events = events
        self.broken = broken
        self.hold = hold

    def play(self):
        self.events.append("warning tone")
        if self.hold:
            self.hold.wait(5)
        else:
            time.sleep(0.02)
        if self.broken:
            raise OSError("audio device unplugged")
        self.events.append("warning tone end")


def test_say_with_the_warning_tone_plays_the_tone_before_the_line():
    events = []
    engine = OrderedEngine(["yes", ""], events)

    async def body(ws, service):
        await say(ws, "Something just happened. Are you okay?", listen_s=6, tone="warning")
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}
        await say(ws, "I didn't catch that. Are you okay?", listen_s=6)
        await next_heard(ws)

    run_with_service(engine, body, warning=FakeWarning(events))
    assert events == ["warning tone", "warning tone end", "say test", "say test"]


def test_unknown_tone_plays_nothing_and_still_speaks():
    events = []
    engine = OrderedEngine([], events)

    async def body(ws, service):
        await say(ws, "Hello.", tone="siren")
        await wait_for(lambda: engine.spoken)

    run_with_service(engine, body, warning=FakeWarning(events))
    assert events == ["say test"]


def test_text_mode_logs_a_marker_for_the_warning_tone_and_speaks():
    lines = []
    engine = FakeEngine([])

    async def body(ws, service):
        await say(ws, "Something just happened. Are you okay?", tone="warning")
        await wait_for(lambda: engine.spoken)

    run_with_service(engine, body, log=lines.append)
    assert any("WARNING TONE" in line for line in lines)
    assert engine.spoken == ["Something just happened. Are you okay?"]


def test_broken_warning_tone_still_speaks_the_line():
    events = []
    engine = OrderedEngine(["yes"], events)

    async def body(ws, service):
        await say(ws, "Something just happened. Are you okay?", listen_s=6, tone="warning")
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}

    run_with_service(engine, body, warning=FakeWarning(events, broken=True))
    assert events == ["warning tone", "say test"]


def test_reset_during_the_warning_tone_drops_the_line():
    events = []
    hold = threading.Event()
    engine = OrderedEngine([], events)

    async def body(ws, service):
        await say(ws, "Something just happened. Are you okay?", listen_s=6, tone="warning")
        await wait_for(lambda: "warning tone" in events)
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)
        hold.set()
        await say(ws, "After the reset.")
        await wait_for(lambda: engine.spoken)

    run_with_service(engine, body, warning=FakeWarning(events, hold=hold))
    assert engine.spoken == ["After the reset."]
    assert engine.listens == []
