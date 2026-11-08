"""Speak and listen. Each engine has speak(text, script_id) and listen(seconds) -> transcript."""

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
# The offline voice, one setting: "piper:<voice>" or "kokoro:<voice>". Both run on a Pi 5.
OFFLINE_VOICE = os.environ.get("OFFLINE_VOICE", "kokoro:am_liam")  # picked by Godfrey from 18 samples
# Godfrey picked the 90% speed sample. The research target is 130 to 150 words a minute.
OFFLINE_SPEED = 0.9
KOKORO_SENTENCE_PAUSE_S = 0.4  # the pause in the sample Godfrey picked; Kokoro's default is 0.25
KOKORO_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
KOKORO_FILES = ("kokoro-v1.0.int8.onnx", "voices-v1.0.bin")  # int8 is 88 MB, the Pi-sized build
# moonshine/tiny returned nothing for the "help me" fixture; base got it.
MOONSHINE_MODEL = "moonshine/base"
# Moonshine returns nothing when an answer sits after ~2 s of quiet, so we cut the quiet off.
# The gate is relative to the room's floor, the 10th percentile of frame volume. Not the median:
# when speech fills most of the window the median is speech, and a 3.2 s answer was cut to 0.51 s.
# On this MacBook (input volume 27%), room noise averaged over 150 ms peaked at 4.5x the floor
# (fixture room_noise_real_mic.wav); a faint voice reached about 7x (3.5x the room median).
FRAME = 480  # 30 ms at 16 kHz
SMOOTH_FRAMES = 5
FLOOR_PERCENTILE = 10
VOICE_OVER_FLOOR = 5.5
MIN_VOICE_RMS = 0.003  # above this Mac's room median (0.002), so near-silence never counts as voice
PAD = SAMPLE_RATE * 3 // 10
TOKENS_PER_SECOND = 6.5  # Moonshine's own default (core/moonshine-model.cpp); stops runaway repeats

ELEVEN_URL = "https://api.elevenlabs.io/v1"
ELEVEN_VOICE = os.environ.get("ELEVEN_VOICE_ID", "ljX1ZrXuDIIRVcmiVSyR")  # picked by Godfrey from the Voice Library
ELEVEN_TTS_MODEL = "eleven_v4_turbo"
ELEVEN_STT_MODEL = "scribe_v2"
ELEVEN_TIMEOUT_S = 10  # a guess: long enough for a short line, short enough to fall back fast
# Audio tags by the agent's script id. Only the ElevenLabs request gets them, so a tag never
# reaches the bus, the home screen or the offline voice (which would read it out loud).
ELEVEN_TAGS = {
    "ask_stopped": "[warm]",
    "ask_event": "[warm]",
    "ask_gesture": "[warm]",
    "ask_retry_2": "[gently]",
    "ask_retry_3": "[concerned]",
    "escalate": "[calm, firm]",
    "reply_help": "[calm, reassuring]",
    "reply_ok": "[warm]",
    "standup_ask": "[warm]",
}
ALARM_WAV = Path(__file__).parent / "assets" / "alarm.wav"


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


def play(audio: np.ndarray, rate: int, wait: bool = True):
    import sounddevice as sd

    sd.play(audio, rate)
    if wait:
        sd.wait()


def stop_audio():
    import sounddevice as sd

    sd.stop()


class AlarmTone:
    """The fake alarm's tone on the box speaker. start() returns at once; stop() cuts it off."""

    def __init__(self, path: Path = ALARM_WAV):
        with wave.open(str(path)) as w:
            self.rate = w.getframerate()
            self.audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

    def start(self):
        play(self.audio, self.rate, wait=False)

    def stop(self):
        stop_audio()


# The EQW alert's warning tone: a few short beeps at one pitch, made in code, so there is no WAV
# to ship and the tests can check the pitch. Owner rule: never the real EAS tones (853 + 960 Hz,
# the 1050 Hz NWS tone, SAME bursts at 1562.5 and 2083.3 Hz). 1320 Hz is a pick, far from all of them.
WARNING_HZ = 1320
WARNING_BEEPS = 3
WARNING_BEEP_S = 0.12
WARNING_GAP_S = 0.08  # also the pause after the last beep, before the line
WARNING_FADE_S = 0.01  # no click at each beep's edges


class WarningTone:
    """The EQW alert's warning tone, about 0.6 s. play() returns when it ends, so the line comes after."""

    def __init__(self):
        self.rate = SAMPLE_RATE
        t = np.arange(int(self.rate * WARNING_BEEP_S)) / self.rate
        fade = np.minimum(1, np.minimum(t, WARNING_BEEP_S - t) / WARNING_FADE_S)
        beep = 0.5 * np.sin(2 * np.pi * WARNING_HZ * t) * fade
        gap = np.zeros(int(self.rate * WARNING_GAP_S))
        self.audio = np.concatenate([beep, gap] * WARNING_BEEPS).astype(np.float32)

    def play(self):
        play(self.audio, self.rate)


def download_models():
    import urllib.request

    from piper.download_voices import download_voice

    backend, voice = parse_voice(OFFLINE_VOICE)
    if backend == "piper":
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        download_voice(voice, MODEL_DIR)
    else:
        (MODEL_DIR / "kokoro").mkdir(parents=True, exist_ok=True)
        for name in KOKORO_FILES:
            if not (MODEL_DIR / "kokoro" / name).exists():
                urllib.request.urlretrieve(f"{KOKORO_URL}/{name}", MODEL_DIR / "kokoro" / name)
    MoonshineSTT()


def trim_to_voice(audio: np.ndarray) -> np.ndarray:
    frames = audio[: len(audio) // FRAME * FRAME].reshape(-1, FRAME)
    rms = np.sqrt((frames**2).mean(axis=1))
    smooth = np.convolve(rms, np.ones(SMOOTH_FRAMES) / SMOOTH_FRAMES, mode="same")
    voiced = np.flatnonzero(smooth > max(VOICE_OVER_FLOOR * np.percentile(rms, FLOOR_PERCENTILE), MIN_VOICE_RMS))
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


def parse_voice(setting: str) -> tuple[str, str]:
    backend, _, voice = setting.partition(":")
    if backend not in ("piper", "kokoro") or not voice:
        raise ValueError(f'voice setting must be "piper:<voice>" or "kokoro:<voice>", got {setting!r}')
    return backend, voice


def require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing; run python -m software.voice --download")
    return path


def make_tts(setting: str, speed: float = OFFLINE_SPEED):
    backend, voice = parse_voice(setting)
    return PiperTTS(voice, speed) if backend == "piper" else KokoroTTS(voice, speed)


class PiperTTS:
    def __init__(self, voice: str, speed: float):
        from piper import PiperVoice, SynthesisConfig

        self.voice = PiperVoice.load(require(MODEL_DIR / f"{voice}.onnx"))
        self.config = SynthesisConfig(length_scale=1 / speed)

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        chunks = list(self.voice.synthesize(text, syn_config=self.config))
        return np.concatenate([c.audio_float_array for c in chunks]), chunks[0].sample_rate

    def speak(self, text: str):
        play(*self.synthesize(text))


class KokoroTTS:
    def __init__(self, voice: str, speed: float):
        from kokoro_onnx import Kokoro

        model, voices = (require(MODEL_DIR / "kokoro" / name) for name in KOKORO_FILES)
        self.kokoro = Kokoro(str(model), str(voices))
        self.voice = voice
        self.speed = speed
        self.lang = "en-gb" if voice.startswith("b") else "en-us"  # Kokoro names British voices b*

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        return self.kokoro.create(
            text, voice=self.voice, speed=self.speed, lang=self.lang, sentence_pause=KOKORO_SENTENCE_PAUSE_S
        )

    def speak(self, text: str):
        play(*self.synthesize(text))


class OfflineEngine:
    """Piper or Kokoro speaks, Moonshine listens. No network."""

    def __init__(self, log=print):
        self.log = log
        self.tts = make_tts(OFFLINE_VOICE)
        self.stt = MoonshineSTT()

    def speak(self, text: str, script_id: str | None = None):
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

    def speak(self, text: str, script_id: str | None = None):
        import requests

        tag = ELEVEN_TAGS.get(script_id)
        try:
            r = self.http.post(
                f"{ELEVEN_URL}/text-to-speech/{ELEVEN_VOICE}",
                params={"output_format": f"pcm_{SAMPLE_RATE}"},
                json={"text": f"{tag} {text}" if tag else text, "model_id": ELEVEN_TTS_MODEL},
                timeout=ELEVEN_TIMEOUT_S,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            self.log(f"FALLBACK: ElevenLabs text-to-speech failed ({e}); the offline voice speaks this line")
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

    def speak(self, text: str, script_id: str | None = None):
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
