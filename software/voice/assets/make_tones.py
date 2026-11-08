"""Generates the alarm tones: python make_tones.py <out_dir>."""

import sys
import wave

import numpy as np

RATE = 44100
OUT = sys.argv[1]


def tone(freq, dur, vol=0.5):
    t = np.arange(int(RATE * dur)) / RATE
    wave_ = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * 2 * freq * t)
    env = np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.03)
    return vol * wave_ * env / 1.3


def bell(freq, dur, vol=0.5):
    t = np.arange(int(RATE * dur)) / RATE
    partials = sum(a * np.sin(2 * np.pi * freq * m * t) for m, a in [(1, 1), (2.76, 0.4), (5.4, 0.2)])
    return vol * partials * np.exp(-t * 3) * np.minimum(1, t / 0.005) / 1.6


def gap(dur):
    return np.zeros(int(RATE * dur))


def save(name, parts, loops):
    one = np.concatenate(parts)
    audio = np.tile(one, loops)
    data = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(f"{OUT}/{name}.wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())


save("alarm_1_two_tone", [tone(880, 0.35), tone(660, 0.35)], 4)
save("alarm_2_triple_beep", [tone(1000, 0.12), gap(0.08), tone(1000, 0.12), gap(0.08), tone(1000, 0.12), gap(0.5)], 4)
save("alarm_3_rising_chime", [bell(523, 0.35), bell(659, 0.35), bell(784, 0.6), gap(0.3)], 3)
save("alarm_4_soft_pulse", [tone(740, 0.5, 0.35), gap(0.4)], 5)
