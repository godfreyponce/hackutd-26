"""Offline speech-to-text on fixtures made with macOS `say`. Needs the Moonshine model in the
local cache (see software/voice/README.md); runs with no network."""

import os
import wave
from pathlib import Path

import numpy as np
import pytest

from software.voice.classify import classify

os.environ["HF_HUB_OFFLINE"] = "1"
FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    with wave.open(str(FIXTURES / name)) as w:
        assert (w.getframerate(), w.getnchannels()) == (16000, 1)
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


@pytest.fixture(scope="module")
def stt():
    from software.voice.engines import MoonshineSTT

    try:
        return MoonshineSTT()
    except Exception as e:
        pytest.skip(f"Moonshine model not cached: {e}")


@pytest.mark.parametrize(
    "fixture,answer",
    [("im_okay.wav", "ok"), ("help.wav", "help"), ("help_me.wav", "help"), ("silence.wav", "no_answer")],
)
def test_fixture_classifies(stt, fixture, answer):
    transcript = stt.transcribe(load(fixture))
    assert classify(transcript) == answer, transcript


def test_speech_inside_a_long_quiet_recording(stt):
    """A real listen window is mostly room noise with a short answer in it."""
    quiet = np.zeros(16000 * 3, dtype=np.float32)
    for name, answer in [("im_okay.wav", "ok"), ("help_me.wav", "help")]:
        audio = np.concatenate([quiet, load(name), quiet])
        audio += np.random.default_rng(0).normal(0, 0.003, audio.size).astype(np.float32)
        assert classify(stt.transcribe(audio)) == answer


def test_real_mic_room_noise_is_silence(stt):
    assert stt.transcribe(load("room_noise_real_mic.wav")) == ""


def test_silence_is_an_empty_transcript(stt):
    assert stt.transcribe(load("silence.wav")) == ""
