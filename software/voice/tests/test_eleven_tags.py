"""Audio tags go only into the ElevenLabs request. The bus text and the offline voice never see one."""

from types import SimpleNamespace

import numpy as np
import pytest
import requests

from software.voice import engines
from software.voice.engines import AlarmTone, ElevenLabsEngine, OfflineEngine

LINE = "I didn't catch that. Are you okay? Just say okay, or help."


class FakeHttp:
    def __init__(self, error=None):
        self.error = error
        self.posts = []

    def post(self, url, **kw):
        self.posts.append(kw)
        if self.error:
            raise self.error
        return SimpleNamespace(raise_for_status=lambda: None, content=np.zeros(160, dtype=np.int16).tobytes())


class FakeTTS:
    def __init__(self):
        self.spoken = []

    def speak(self, text):
        self.spoken.append(text)


def make_engines(http):
    offline = OfflineEngine.__new__(OfflineEngine)  # skips loading the voice models
    offline.tts = FakeTTS()
    eleven = ElevenLabsEngine("fake-key", offline, log=lambda line: None)
    eleven.http = http
    return eleven, offline


@pytest.fixture(autouse=True)
def no_audio(monkeypatch):
    monkeypatch.setattr(engines, "play", lambda *a, **kw: None)


@pytest.mark.parametrize("script_id, tag", [("ask_retry_2", "[gently]"), ("escalate", "[calm, firm]")])
def test_eleven_request_gets_the_tag(script_id, tag):
    http = FakeHttp()
    eleven, _ = make_engines(http)
    eleven.speak(LINE, script_id)
    assert http.posts[0]["json"] == {"text": f"{tag} {LINE}", "model_id": "eleven_v4_turbo"}


def test_unknown_id_gets_no_tag():
    http = FakeHttp()
    eleven, _ = make_engines(http)
    eleven.speak(LINE, "something_new")
    assert http.posts[0]["json"]["text"] == LINE


@pytest.mark.parametrize("script_id", list(engines.ELEVEN_TAGS))
def test_offline_voice_never_gets_a_tag(script_id):
    eleven, offline = make_engines(FakeHttp(error=requests.ConnectionError("Wi-Fi off")))
    offline.speak(LINE, script_id)
    eleven.speak(LINE, script_id)  # falls back to the offline voice
    assert offline.tts.spoken == [LINE, LINE]
    assert not any("[" in text for text in offline.tts.spoken)


def test_alarm_tone_loads_the_asset_and_starts_without_waiting(monkeypatch):
    played = []
    monkeypatch.setattr(engines, "play", lambda audio, rate, wait=True: played.append((audio.size / rate, wait)))
    AlarmTone().start()
    [(seconds, wait)] = played
    assert seconds > 1
    assert wait is False
