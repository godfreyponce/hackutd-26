"""The offline voice is one setting, "piper:<voice>" or "kokoro:<voice>". Renders to memory; plays nothing."""

import pytest

from software.voice.engines import make_tts

LINE = "I noticed you stopped moving. Are you okay? Please respond."


@pytest.mark.parametrize("setting", ["piper:en_US-lessac-medium", "kokoro:af_heart"])
def test_each_backend_renders_the_line(setting):
    try:
        tts = make_tts(setting)
    except FileNotFoundError as e:
        pytest.skip(f"voice not downloaded: {e}")
    audio, rate = tts.synthesize(LINE)
    assert rate >= 16000
    assert 2 < audio.size / rate < 8
    assert abs(audio).max() > 0.1


@pytest.mark.parametrize("setting", ["lessac", "espeak:en", "piper:"])
def test_bad_setting_is_rejected(setting):
    with pytest.raises(ValueError):
        make_tts(setting)
