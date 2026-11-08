import asyncio
import json
import sys
import threading
import time

import numpy as np
import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import broadcast, serve

from software.voice import engines
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


def run_with_service(engine, body, alarm=None, warning=None, log=lambda line: None, line_cut=None):
    async def main():
        server, url, clients = await fake_bus()
        service = VoiceService(engine, log=log, alarm=alarm, warning=warning, line_cut=line_cut)
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


# ---- a reset cuts the line in progress ----

@pytest.fixture(autouse=True)
def clear_line_cut():
    yield
    engines.line_cut.clear()


class FakeSoundDevice:
    """Stands in for sounddevice: a sound or a recording lasts its full length unless stop() cuts it."""

    def __init__(self, stop_s=0):
        self.started = []
        self.cut = threading.Event()
        self.length = 0
        self.stop_s = stop_s  # a real stop waits for the audio buffer to drain
        self.stopping = 0
        self.overlapped = False

    def _start(self, what, seconds):
        self.started.append(what)
        self.cut = threading.Event()
        self.length = seconds

    def play(self, audio, rate):
        self._start("play", len(audio) / rate)

    def rec(self, frames, samplerate, channels, dtype):
        self._start("rec", frames / samplerate)
        return np.full((frames, channels), 0.1, dtype=dtype)

    def wait(self):
        self.cut.wait(self.length)

    def stop(self):
        self.stopping += 1
        self.overlapped |= self.stopping > 1
        time.sleep(self.stop_s)
        self.cut.set()
        self.stopping -= 1


class SpeakerEngine:
    """Speaks and listens through engines.play and engines.record, as the real engines do."""

    def __init__(self, transcripts, line_s):
        self.transcripts = list(transcripts)
        self.line_s = line_s
        self.spoken = []

    def speak(self, text, script_id=None):
        self.spoken.append(script_id)
        engines.play(np.zeros(int(self.line_s[script_id] * engines.SAMPLE_RATE), dtype=np.float32),
                     engines.SAMPLE_RATE)

    def listen(self, seconds):
        audio = engines.record(seconds, lambda line: None)
        return "" if audio is None else self.transcripts.pop(0)


LONG_S = 3  # a line, a listen or a tone that a reset must cut short
CUT_S = 1.5  # the next ask starts well before the long one would have ended


def ask(ws, script_id, listen_s=None, tone=None):
    msg = {"type": "say", "script_id": script_id, "text": script_id}
    if listen_s is not None:
        msg["listen_s"] = listen_s
    if tone is not None:
        msg["tone"] = tone
    return ws.send(json.dumps(msg))


def test_reset_cuts_the_line_in_progress_and_the_next_ask_starts_at_once(monkeypatch):
    sd = FakeSoundDevice()
    monkeypatch.setitem(sys.modules, "sounddevice", sd)
    engine = SpeakerEngine(["yes"], {"escalate": LONG_S, "ask_stopped": 0.05})
    events = []

    async def body(ws, service):
        await ask(ws, "escalate")
        await ws.send(json.dumps({"type": "checkin", "state": "alarm", "try": 3}))
        await wait_for(lambda: sd.started == ["play"])
        await asyncio.sleep(0.2)
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)
        cut_at = time.monotonic()
        await ask(ws, "ask_stopped", listen_s=0.05)
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}
        assert time.monotonic() - cut_at < CUT_S

    run_with_service(engine, body, alarm=FakeAlarm(events), line_cut=engines.line_cut)
    assert engine.spoken == ["escalate", "ask_stopped"]
    assert events == []


def test_reset_cuts_the_listen_in_progress_and_drops_its_answer(monkeypatch):
    sd = FakeSoundDevice()
    monkeypatch.setitem(sys.modules, "sounddevice", sd)
    engine = SpeakerEngine(["yes"], {"ask_stopped": 0.05, "ask_retry_2": 0.05})

    async def body(ws, service):
        await ask(ws, "ask_retry_2", listen_s=LONG_S)
        await wait_for(lambda: "rec" in sd.started)
        await asyncio.sleep(0.2)
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)
        cut_at = time.monotonic()
        await ask(ws, "ask_stopped", listen_s=0.05)
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}
        assert time.monotonic() - cut_at < CUT_S

    run_with_service(engine, body, line_cut=engines.line_cut)
    assert engine.spoken == ["ask_retry_2", "ask_stopped"]


def test_reset_cuts_the_warning_tone_in_progress(monkeypatch):
    sd = FakeSoundDevice()
    monkeypatch.setitem(sys.modules, "sounddevice", sd)
    engine = SpeakerEngine(["yes"], {"ask_event": 0.05, "ask_stopped": 0.05})
    warning = engines.WarningTone()
    warning.audio = np.zeros(LONG_S * warning.rate, dtype=np.float32)

    async def body(ws, service):
        await ask(ws, "ask_event", listen_s=0.05, tone="warning")
        await wait_for(lambda: sd.started == ["play"])
        await asyncio.sleep(0.2)
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)
        cut_at = time.monotonic()
        await ask(ws, "ask_stopped", listen_s=0.05)
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}
        assert time.monotonic() - cut_at < CUT_S

    run_with_service(engine, body, warning=warning, line_cut=engines.line_cut)
    assert engine.spoken == ["ask_stopped"]


def test_after_a_reset_the_next_line_and_the_alarm_tone_play_and_a_reset_stops_the_tone(monkeypatch):
    sd = FakeSoundDevice()
    monkeypatch.setitem(sys.modules, "sounddevice", sd)
    engine = SpeakerEngine([], {"escalate": 0.05})

    async def body(ws, service):
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)
        await ask(ws, "escalate")
        await ws.send(json.dumps({"type": "checkin", "state": "alarm", "try": 3}))
        await wait_for(lambda: service.alarm_on)
        assert sd.started == ["play", "play"]
        assert not sd.cut.is_set()
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 2)
        assert sd.cut.is_set()

    run_with_service(engine, body, alarm=engines.AlarmTone(), line_cut=engines.line_cut)


def test_reset_during_the_standup_ask_with_the_alarm_on_never_stops_audio_twice_at_once(monkeypatch):
    # sounddevice's stop() closes the stream with no lock: two at once would close it twice.
    sd = FakeSoundDevice(stop_s=0.05)
    monkeypatch.setitem(sys.modules, "sounddevice", sd)
    engine = SpeakerEngine([], {"escalate": 0.05, "standup_ask": 0.05})

    async def body(ws, service):
        await ask(ws, "escalate")
        await ws.send(json.dumps({"type": "checkin", "state": "alarm", "try": 3}))
        await wait_for(lambda: service.alarm_on)
        await ask(ws, "standup_ask", listen_s=LONG_S)
        await wait_for(lambda: "rec" in sd.started)
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)
        await asyncio.sleep(0.3)

    run_with_service(engine, body, alarm=engines.AlarmTone(), line_cut=engines.line_cut)
    assert not sd.overlapped


class TailSoundDevice(FakeSoundDevice):
    """The next wait() holds in the line's tail, past its length, until the test ends it. Notes a stop
    from another thread while a wait runs: on macOS that hung PortAudio."""

    def __init__(self):
        super().__init__()
        self.hold = False
        self.in_tail = threading.Event()
        self.end_tail = threading.Event()
        self.waiter = None
        self.stopped_during_wait = False

    def wait(self):
        self.waiter = threading.get_ident()
        try:
            if self.hold:
                self.hold = False
                self.in_tail.set()
                self.end_tail.wait(5)
            else:
                super().wait()
        finally:
            self.waiter = None

    def stop(self):
        self.stopped_during_wait |= self.waiter not in (None, threading.get_ident())
        super().stop()


def test_reset_in_the_tail_of_a_line_with_the_alarm_on_never_stops_audio_from_another_thread(monkeypatch):
    sd = TailSoundDevice()
    monkeypatch.setitem(sys.modules, "sounddevice", sd)
    engine = SpeakerEngine(["yes"], {"escalate": 0.05, "standup_ask": 0.05, "ask_stopped": 0.05})

    async def body(ws, service):
        await ask(ws, "escalate")
        await ws.send(json.dumps({"type": "checkin", "state": "alarm", "try": 3}))
        await wait_for(lambda: service.alarm_on)
        sd.hold = True
        await ask(ws, "standup_ask")
        await wait_for(sd.in_tail.is_set)
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)
        sd.end_tail.set()
        await ask(ws, "ask_stopped", listen_s=0.05)
        assert await next_heard(ws) == {"type": "heard", "answer": "ok", "transcript": "yes"}

    run_with_service(engine, body, alarm=engines.AlarmTone(), line_cut=engines.line_cut)
    assert not sd.stopped_during_wait


def test_reset_while_the_next_line_is_still_being_made_stops_the_alarm_tone_at_once(monkeypatch):
    # A reset must not wait for the busy voice worker to stop the alarm: a slow line keeps it sounding.
    sd = FakeSoundDevice()
    monkeypatch.setitem(sys.modules, "sounddevice", sd)
    making = threading.Event()
    made = threading.Event()

    class SlowEngine(SpeakerEngine):
        def speak(self, text, script_id=None):
            if script_id == "standup_ask":
                making.set()
                made.wait(5)
            super().speak(text, script_id)

    engine = SlowEngine([], {"escalate": 0.05, "standup_ask": 0.05})

    async def body(ws, service):
        await ask(ws, "escalate")
        await ws.send(json.dumps({"type": "checkin", "state": "alarm", "try": 3}))
        await wait_for(lambda: service.alarm_on)
        await ask(ws, "standup_ask")
        await wait_for(making.is_set)
        await ws.send(json.dumps({"type": "reset"}))
        await wait_for(lambda: service.resets == 1)
        assert sd.cut.is_set()
        made.set()

    run_with_service(engine, body, alarm=engines.AlarmTone(), line_cut=engines.line_cut)
    assert sd.started == ["play", "play"]
