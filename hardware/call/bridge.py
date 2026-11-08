"""Live two-way emergency call through the box (issue #87).

After "Do you want me to call emergency services?" -> yes, the agent dials the team phone (never 911) with TwiML:
<Say>LAND's 1-2 sentence summary</Say><Connect><Stream url="wss://<tunnel>/stream"/></Connect>. Twilio then opens a
WebSocket to this bridge, and:
  - the caller's voice (mu-law 8 kHz) plays on the box speaker,
  - the box mics (PipeWire land_mic: echo cancel + noise suppression + gain) go to the caller,
  - both sides are transcribed (ElevenLabs) onto the bus for the demo page and the incident report.
A chime on the box speaker says "you can talk now". Reset hangs the call up.

The public wss URL comes from a Cloudflare quick tunnel (no account) started here; it is announced on the bus as
{"type":"call_bridge","url":"wss://.../stream"} so the agent can put it in the TwiML.
Bus out: {"type":"call","kind":"help","state":"live"|"ended"}, {"type":"call_transcript","who":"caller"|"home","text":...}

Run: HUB_URL=ws://localhost:8765 .venv/bin/python hardware/call/bridge.py   (env: TWILIO_*, ELEVENLABS_API_KEY)
"""
import asyncio
import base64
import json
import os
import re
import sys
import threading
import time
from collections import deque

import numpy as np
import sounddevice as sd

PORT = int(os.environ.get("CALL_BRIDGE_PORT", 8091))
RATE = 16000                 # box side (the PipeWire land_mic / land_speaker run at any rate; PipeWire resamples)
ANNOUNCE_S = 30              # re-announce the tunnel URL this often (agents that start later still learn it)
DUCK = 0.5                   # mic level while the caller is SPEAKING (on top of echo cancel): less echo back
CALLER_SPEECH_RMS = 0.05     # caller frames this loud are speech; phone-line hiss stays below, so it never ducks
VOICE_RMS = 0.02             # speech-ish level for the transcript chunker (after the mic gain below)
MIC_TARGET_RMS, MIC_MAX_GAIN = 0.12, 16.0   # the box mic is quiet: raise speech toward phone level, up to +24 dB
SILENCE_S, MIN_SPEECH_S = 0.7, 0.5


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---- G.711 mu-law (Python 3.13 has no audioop) ----
_EXP = np.array([0, 0, 1, 1, 2, 2, 2, 2] + [3] * 8 + [4] * 16 + [5] * 32 + [6] * 64 + [7] * 128, dtype=np.int32)


def ulaw_decode(b: bytes) -> np.ndarray:
    u = ~np.frombuffer(b, dtype=np.uint8).astype(np.int32) & 0xFF
    sign, exp, man = u & 0x80, (u >> 4) & 7, u & 0x0F
    s = (((man << 3) + 0x84) << exp) - 0x84
    return (np.where(sign, -s, s) / 32768.0).astype(np.float32)


def ulaw_encode(x: np.ndarray) -> bytes:
    s = np.clip(x * 32768.0, -32768, 32767).astype(np.int32)
    sign = np.where(s < 0, 0x80, 0)
    s = np.minimum(np.abs(s), 32635) + 0x84
    exp = _EXP[(s >> 7) & 0xFF]
    man = (s >> (exp + 3)) & 0x0F
    return (~(sign | (exp << 4) | man) & 0xFF).astype(np.uint8).tobytes()


class Resampler:
    """Streaming 2x up/down with a proper low-pass FIR (a phone line is 300-3400 Hz), state kept across frames."""

    TAPS = None

    def __init__(self):
        if Resampler.TAPS is None:
            n = np.arange(-24, 25)
            Resampler.TAPS = (np.sinc(n / 2) / 2 * np.hamming(49)).astype(np.float32)  # half-band, cutoff fs/4
        self.tail = np.zeros(48, np.float32)

    def _filt(self, x):
        y = np.convolve(np.concatenate([self.tail, x]), Resampler.TAPS, mode="valid")
        self.tail = np.concatenate([self.tail, x])[-48:]
        return y.astype(np.float32)

    def down2(self, x):  # 16 kHz -> 8 kHz
        return self._filt(x)[::2]

    def up2(self, x):  # 8 kHz -> 16 kHz
        z = np.zeros(len(x) * 2, np.float32)
        z[::2] = x * 2
        return self._filt(z)


class Agc:
    """Slow automatic gain for the box mic: speech toward MIC_TARGET_RMS, never boosts silence."""

    def __init__(self):
        self.gain = 4.0

    def __call__(self, x):
        rms = float(np.sqrt((x ** 2).mean()))
        if rms * self.gain > 0.01:  # only adapt on speech-level frames
            want = min(MIC_MAX_GAIN, max(1.0, MIC_TARGET_RMS / max(rms, 1e-6)))
            self.gain += (want - self.gain) * (0.3 if want < self.gain else 0.05)  # fast down, slow up
        return np.tanh(x * self.gain).astype(np.float32)


def chime():
    """Two rising tones: 'you can talk now'."""
    t = np.arange(int(0.18 * RATE)) / RATE
    env = np.minimum(1, np.minimum(t, t[::-1]) * 40)
    tone = lambda f: (0.35 * np.sin(2 * np.pi * f * t) * env).astype(np.float32)  # noqa: E731
    return np.concatenate([tone(660), np.zeros(int(0.05 * RATE), np.float32), tone(990)])


class Chunker:
    """Cuts one side of the call into utterances for the transcript."""

    def __init__(self, who, emit):
        self.who, self.emit, self.buf, self.speech, self.quiet = who, emit, [], 0.0, 0.0

    def push(self, x):
        loud = float(np.sqrt((x ** 2).mean())) > VOICE_RMS
        dt = len(x) / RATE
        if loud or self.buf:
            self.buf.append(x)
        self.speech += dt if loud else 0
        self.quiet = 0.0 if loud else self.quiet + dt
        if self.buf and self.quiet >= SILENCE_S:
            audio, enough = np.concatenate(self.buf), self.speech >= MIN_SPEECH_S
            self.buf, self.speech, self.quiet = [], 0.0, 0.0
            if enough:
                threading.Thread(target=self.emit, args=(self.who, audio), daemon=True).start()


class Bridge:
    def __init__(self):
        self.url, self.bus, self.loop = None, None, None
        self.call = None  # {"ws", "stream", "call_sid", "out": deque of float32 16 kHz chunks}

    # ---- bus ----
    def tell(self, msg):
        if self.bus and self.loop:
            asyncio.run_coroutine_threadsafe(self.bus.send(json.dumps(msg)), self.loop)

    def transcribe(self, who, audio):
        key = os.environ.get("ELEVENLABS_API_KEY")
        if not key:
            return
        import requests

        from software.voice.engines import ELEVEN_STT_MODEL, ELEVEN_URL, wav_bytes
        try:
            r = requests.post(f"{ELEVEN_URL}/speech-to-text", headers={"xi-api-key": key}, timeout=15,
                              data={"model_id": ELEVEN_STT_MODEL},
                              files={"file": ("call.wav", wav_bytes(audio), "audio/wav")})
            r.raise_for_status()
            text = r.json()["text"].strip()
        except Exception as e:  # report; the call itself goes on
            log(f"call transcript failed ({who}): {e!r}")
            return
        if text and not re.fullmatch(r"\(.*\)|\[.*\]", text):  # skip "(silence)" / "[noise]" tags
            log(f"CALL {who}: {text}")
            self.tell({"type": "call_transcript", "who": who, "text": text})

    async def run_bus(self, url):
        import websockets
        while True:
            try:
                async with websockets.connect(url) as ws:
                    self.bus = ws
                    log(f"hub connected: {url}")
                    if self.url:
                        self.tell({"type": "call_bridge", "url": self.url})
                    async for raw in ws:
                        try:
                            m = json.loads(raw)
                        except ValueError:
                            continue
                        if isinstance(m, dict) and m.get("type") == "reset" and self.call:
                            await asyncio.to_thread(self.hang_up, "reset")
            except Exception as e:  # report and retry; never silent
                self.bus = None
                log(f"hub error ({url}): {e!r}; retrying in 2 s")
                await asyncio.sleep(2)

    # ---- tunnel ----
    async def run_tunnel(self):
        """Cloudflare quick tunnel to this bridge; restarts if it dies. The URL changes on every start."""
        while True:
            proc = await asyncio.create_subprocess_exec(
                "cloudflared", "tunnel", "--no-autoupdate", "--url", f"http://localhost:{PORT}",
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
            async for raw in proc.stderr:
                if m := re.search(r"https://([a-z0-9-]+\.trycloudflare\.com)", raw.decode(errors="replace")):
                    self.url = f"wss://{m.group(1)}/stream"
                    log(f"tunnel up: {self.url}")
                    self.tell({"type": "call_bridge", "url": self.url})
            self.url = None
            log(f"tunnel exited with code {await proc.wait()}; restarting in 3 s")
            await asyncio.sleep(3)

    async def announce(self):
        while True:
            await asyncio.sleep(ANNOUNCE_S)
            if self.url:
                self.tell({"type": "call_bridge", "url": self.url})

    # ---- one call ----
    def hang_up(self, why):
        c = self.call
        if not c or not c.get("call_sid"):
            return
        import requests
        sid, tok = os.environ.get("TWILIO_ACCOUNT_SID"), os.environ.get("TWILIO_AUTH_TOKEN")
        try:
            r = requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls/{c['call_sid']}.json",
                              auth=(sid, tok), data={"Status": "completed"}, timeout=10)
            r.raise_for_status()
            log(f"hung up ({why})")
        except Exception as e:  # report; the call ends when the phone hangs up anyway
            log(f"hang up failed: {e!r}")

    async def handle(self, ws):
        """One Twilio Media Stream (bidirectional)."""
        if self.call:
            log("second stream while a call is live: refused")
            return await ws.close()
        out, chunkers, rs_in, rs_out, agc = deque(), {}, Resampler(), Resampler(), Agc()
        call = {"ws": ws, "stream": None, "call_sid": None, "out": out, "caller_loud_until": 0.0}
        loop = asyncio.get_running_loop()
        emit = lambda who, a: self.transcribe(who, a)  # noqa: E731
        chunkers["caller"], chunkers["home"] = Chunker("caller", emit), Chunker("home", emit)
        pending = np.zeros(0, np.float32)

        def speaker(outdata, frames, t, status):
            nonlocal pending
            while len(pending) < frames and out:
                pending = np.concatenate([pending, out.popleft()])
            n = min(frames, len(pending))
            outdata[:n, 0], outdata[n:, 0] = pending[:n], 0
            pending = pending[n:]

        def mic(indata, frames, t, status):
            x = agc(indata[:, 0].copy())
            if time.monotonic() < call["caller_loud_until"]:
                x *= DUCK  # the caller is speaking: less of their voice echoes back
            else:
                chunkers["home"].push(x)
            if call["stream"]:
                payload = base64.b64encode(ulaw_encode(rs_out.down2(x))).decode()
                msg = json.dumps({"event": "media", "streamSid": call["stream"], "media": {"payload": payload}})
                asyncio.run_coroutine_threadsafe(ws.send(msg), loop)

        streams = []
        try:
            async for raw in ws:
                m = json.loads(raw)
                ev = m.get("event")
                if ev == "start":
                    call["stream"], call["call_sid"] = m["start"]["streamSid"], m["start"].get("callSid")
                    self.call = call
                    log(f"call live: {call['call_sid']}")
                    self.tell({"type": "call", "kind": "help", "state": "live"})
                    out.append(chime())
                    streams = [sd.OutputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=320,
                                               callback=speaker),
                               sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=320,
                                              callback=mic)]
                    for s in streams:
                        s.start()
                elif ev == "media" and m["media"].get("track", "inbound") == "inbound":
                    x = rs_in.up2(ulaw_decode(base64.b64decode(m["media"]["payload"])))
                    out.append(x)
                    if float(np.sqrt((x ** 2).mean())) > CALLER_SPEECH_RMS:
                        call["caller_loud_until"] = time.monotonic() + 0.3
                    chunkers["caller"].push(x)
                elif ev == "stop":
                    break
        except Exception as e:  # report; the call is over either way
            log(f"stream error: {e!r}")
        finally:
            for s in streams:
                s.stop()
                s.close()
            self.call = None
            log("call ended")
            self.tell({"type": "call", "kind": "help", "state": "ended"})


async def main():
    import websockets
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    b = Bridge()
    b.loop = asyncio.get_running_loop()

    async def route(ws):
        if ws.request.path.split("?")[0] != "/stream":
            return await ws.close(1008, "not found")
        await b.handle(ws)

    async with websockets.serve(route, "0.0.0.0", PORT, max_size=None):
        log(f"bridge listening on :{PORT}/stream")
        await asyncio.gather(b.run_bus(os.environ.get("HUB_URL", "ws://localhost:8765")), b.run_tunnel(),
                             b.announce())


if __name__ == "__main__":
    asyncio.run(main())
