"""Speak and listen. Each engine has speak(text) and listen(seconds) -> transcript."""

import io
import math
import os
import select
import sys
import termios
import wave
from pathlib import Path

# With Wi-Fi off, a Hugging Face cache check would stall or fail. Models load from disk only.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np

SAMPLE_RATE = 16000
MODEL_DIR = Path.home() / ".cache" / "hackutd-voice"
PIPER_VOICE = "en_US-lessac-medium"
# moonshine/tiny returned nothing for the "help me" fixture; base got it.
MOONSHINE_MODEL = "moonshine/base"
# Moonshine returns nothing when an answer sits after ~2 s of quiet, so we cut the quiet off.
# The gate is relative to the room: on this MacBook (input volume 27%), room noise averaged over
# 150 ms peaked at 2.2x its median (fixture room_noise_real_mic.wav); a faint voice reached 3.5x.
FRAME = 480  # 30 ms at 16 kHz
SMOOTH_FRAMES = 5
VOICE_OVER_FLOOR = 2.5
MIN_VOICE_RMS = 0.003  # above this Mac's room median (0.002), so near-silence never counts as voice
PAD = SAMPLE_RATE * 3 // 10
TOKENS_PER_SECOND = 6.5  # Moonshine's own default (core/moonshine-model.cpp); stops runaway repeats

ELEVEN_URL = "https://api.elevenlabs.io/v1"
ELEVEN_VOICE = "JBFqnCBsd6RMkjVDRZzb"  # "George", the voice in ElevenLabs' API examples
ELEVEN_TTS_MODEL = "eleven_flash_v2_5"
ELEVEN_STT_MODEL = "scribe_v2"
ELEVEN_TIMEOUT_S = 10  # a guess: long enough for a short line, short enough to fall back fast


def mic_blocked_message() -> str:
    app = os.environ.get("__CFBundleIdentifier") or os.environ.get("TERM_PROGRAM") or "the app that runs this terminal"
    return (
        f"MIC BLOCKED: the recording is pure digital silence. macOS is blocking the microphone for {app}. "
        f"Fix: System Settings, Privacy & Security, Microphone, turn on {app}, then restart it."
    )


def record(seconds: float, log) -> np.ndarray | None:
    import sounddevice as sd

    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    audio = audio[:, 0]
    if not np.any(audio):
        log(mic_blocked_message())
        return None
    return audio


def play(audio: np.ndarray, rate: int):
    import sounddevice as sd

    sd.play(audio, rate)
    sd.wait()


def download_models():
    from piper.download_voices import download_voice

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    download_voice(PIPER_VOICE, MODEL_DIR)
    MoonshineSTT()


def trim_to_voice(audio: np.ndarray) -> np.ndarray:
    frames = audio[: len(audio) // FRAME * FRAME].reshape(-1, FRAME)
    rms = np.sqrt((frames**2).mean(axis=1))
    smooth = np.convolve(rms, np.ones(SMOOTH_FRAMES) / SMOOTH_FRAMES, mode="same")
    voiced = np.flatnonzero(smooth > max(VOICE_OVER_FLOOR * np.median(rms), MIN_VOICE_RMS))
    if voiced.size == 0:
        return audio[:0]
    start = max(voiced[0] * FRAME - PAD, 0)
    end = min((voiced[-1] + 1) * FRAME + PAD, len(audio))
    return audio[start:end]


class MoonshineSTT:
    def __init__(self):
        from moonshine_onnx.model import MoonshineOnnxModel
        from moonshine_onnx.transcribe import load_tokenizer

        self.model = MoonshineOnnxModel(model_name=MOONSHINE_MODEL)
        self.tokenizer = load_tokenizer()

    def transcribe(self, audio: np.ndarray) -> str:
        audio = trim_to_voice(audio.astype(np.float32))
        if audio.size == 0:
            return ""
        max_len = math.ceil(audio.size / SAMPLE_RATE * TOKENS_PER_SECOND)
        tokens = self.model.generate(audio[None, :], max_len=max_len)
        return self.tokenizer.decode_batch(tokens)[0].strip()


class PiperTTS:
    def __init__(self):
        from piper import PiperVoice

        self.voice = PiperVoice.load(MODEL_DIR / f"{PIPER_VOICE}.onnx")

    def speak(self, text: str):
        chunks = list(self.voice.synthesize(text))
        play(np.concatenate([c.audio_float_array for c in chunks]), chunks[0].sample_rate)


class OfflineEngine:
    """Piper speaks, Moonshine listens. No network."""

    def __init__(self, log=print):
        self.log = log
        self.tts = PiperTTS()
        self.stt = MoonshineSTT()

    def speak(self, text: str):
        self.tts.speak(text)

    def listen(self, seconds: float) -> str:
        audio = record(seconds, self.log)
        return "" if audio is None else self.stt.transcribe(audio)


def wav_bytes(audio: np.ndarray) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
    return buf.getvalue()


class ElevenLabsEngine:
    """ElevenLabs text-to-speech and speech-to-text. On any network or API error, the
    offline engine takes that line, so losing the internet mid-demo still works."""

    def __init__(self, api_key: str, offline: OfflineEngine, log=print):
        import requests

        self.http = requests.Session()
        self.http.headers["xi-api-key"] = api_key
        self.offline = offline
        self.log = log

    def speak(self, text: str):
        import requests

        try:
            r = self.http.post(
                f"{ELEVEN_URL}/text-to-speech/{ELEVEN_VOICE}",
                params={"output_format": f"pcm_{SAMPLE_RATE}"},
                json={"text": text, "model_id": ELEVEN_TTS_MODEL},
                timeout=ELEVEN_TIMEOUT_S,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            self.log(f"FALLBACK: ElevenLabs text-to-speech failed ({e}); Piper speaks this line")
            return self.offline.speak(text)
        play(np.frombuffer(r.content, dtype=np.int16).astype(np.float32) / 32768, SAMPLE_RATE)

    def listen(self, seconds: float) -> str:
        import requests

        audio = record(seconds, self.log)
        if audio is None:
            return ""
        try:
            r = self.http.post(
                f"{ELEVEN_URL}/speech-to-text",
                data={"model_id": ELEVEN_STT_MODEL},
                files={"file": ("answer.wav", wav_bytes(audio), "audio/wav")},
                timeout=ELEVEN_TIMEOUT_S,
            )
            r.raise_for_status()
            return r.json()["text"].strip()
        except (requests.RequestException, KeyError, ValueError) as e:
            self.log(f"FALLBACK: ElevenLabs speech-to-text failed ({e}); Moonshine transcribes this answer")
            return self.offline.stt.transcribe(audio)


class TextEngine:
    """No audio: print the line, read a typed answer. Timeout means silence."""

    def speak(self, text: str):
        print(f"\nBOX SAYS: {text}", flush=True)

    def listen(self, seconds: float) -> str:
        if sys.stdin.isatty():
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
        print(f"(type an answer and press Enter within {seconds:g} s)", flush=True)
        ready, _, _ = select.select([sys.stdin], [], [], seconds)
        if not ready:
            print("(silence)", flush=True)
            return ""
        return sys.stdin.readline().strip()
