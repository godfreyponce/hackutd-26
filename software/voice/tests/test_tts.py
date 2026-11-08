"""The offline voice is one setting, "piper:<voice>" or "kokoro:<voice>". Renders to memory; plays nothing."""

import pytest

from software.voice.engines import make_tts

LINE = "I noticed you stopped moving. Are you okay? Please respond."


@pytest.mark.parametrize("setting", ["piper:en_US-lessac-medium", "kokoro:am_liam"])
def test_each_backend_renders_the_line(setting):
    try:
        tts = make_tts(setting)
    except FileNotFoundError as e:
        pytest.skip(f"voice not downloaded: {e}")
    audio, rate = tts.synthesize(LINE)
    assert rate >= 16000
    assert 2 < audio.size / rate < 8
    assert abs(audio).max() > 0.1


@pytest.mark.parametrize("setting", ["piper:en_US-lessac-medium", "kokoro:am_liam"])
def test_slower_speed_makes_a_longer_line(setting):
    try:
        # Half speed, not 0.9: Piper's length varies about 2.5% per render, and 0.9 adds only about 6%.
        normal, slow = make_tts(setting, speed=1.0), make_tts(setting, speed=0.5)
    except FileNotFoundError as e:
        pytest.skip(f"voice not downloaded: {e}")
    normal_audio, rate = normal.synthesize(LINE)
    slow_audio, _ = slow.synthesize(LINE)
    assert slow_audio.size / normal_audio.size > 1.3


@pytest.mark.parametrize("setting", ["lessac", "espeak:en", "piper:"])
def test_bad_setting_is_rejected(setting):
    with pytest.raises(ValueError):
        make_tts(setting)
