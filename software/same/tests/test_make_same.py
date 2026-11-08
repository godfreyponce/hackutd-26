import wave
from datetime import datetime, timezone

from software.same.make_same import RATE, default_header, main


def test_default_header_uses_utc_day_of_year_and_time():
    now = datetime(2026, 11, 8, 4, 10, tzinfo=timezone.utc)
    assert default_header(now) == "ZCZC-WXR-EQW-048113-048085+0030-3120410-HACKDEMO-"


def test_writes_a_mono_16_bit_wav_at_the_decoder_rate(tmp_path):
    out = tmp_path / "demo.wav"
    assert main([str(out)]) == 0
    with wave.open(str(out)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, RATE)
        assert w.getnframes() > 10 * RATE


def test_raw_output_is_the_wav_audio_without_the_header(tmp_path):
    header = "ZCZC-WXR-EQW-048113+0030-3120410-HACKDEMO-"
    main([str(tmp_path / "a.wav"), "--header", header])
    main([str(tmp_path / "a.raw"), "--header", header])
    with wave.open(str(tmp_path / "a.wav")) as w:
        frames = w.readframes(w.getnframes())
    assert (tmp_path / "a.raw").read_bytes() == frames


def test_rejects_a_header_that_is_not_same(tmp_path):
    for header in ["hello", "ZCZC-WXR-EQW-048113+0030-3120410-HACKDÉMO-"]:
        assert main([str(tmp_path / "x.wav"), "--header", header]) == 2
    assert not (tmp_path / "x.wav").exists()


def test_rejects_an_output_that_is_not_wav_or_raw(tmp_path):
    assert main([str(tmp_path / "x.mp3")]) == 2
    assert not (tmp_path / "x.mp3").exists()
