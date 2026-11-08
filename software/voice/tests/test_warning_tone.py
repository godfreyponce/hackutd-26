import numpy as np

from software.voice.engines import WarningTone

# Real Emergency Alert System tones the warning tone must stay clear of:
# the 853 + 960 Hz attention signal, the 1050 Hz NWS tone, and the SAME header's
# AFSK bursts (mark 2083.3 Hz, space 1562.5 Hz).
EAS_HZ = (853, 960, 1050, 1562.5, 2083.3)


def test_warning_tone_is_short():
    tone = WarningTone()
    assert len(tone.audio) / tone.rate <= 1.0


def test_warning_tone_is_one_pitch_far_from_the_eas_tones():
    tone = WarningTone()
    spectrum = np.abs(np.fft.rfft(tone.audio))
    freqs = np.fft.rfftfreq(len(tone.audio), 1 / tone.rate)
    peak = freqs[np.argmax(spectrum)]
    assert all(abs(peak - hz) > 150 for hz in EAS_HZ)
    near_eas = sum(spectrum[np.abs(freqs - hz) < 30].sum() for hz in EAS_HZ)
    assert near_eas < 0.02 * spectrum.sum()


def test_warning_tone_is_a_few_beeps_not_one_long_tone():
    tone = WarningTone()
    frame = int(0.01 * tone.rate)
    frames = tone.audio[: len(tone.audio) // frame * frame].reshape(-1, frame)
    rms = np.sqrt((frames**2).mean(axis=1))
    loud = rms > 0.1 * rms.max()
    onsets = int(loud[0]) + int((loud[1:] & ~loud[:-1]).sum())
    assert 2 <= onsets <= 4
