"""Demo runner: runs REAL pipelines when the demo page asks, and narrates them on the bus.

Bus in ({"type":"demo", ...}):
  {"cmd":"radio_eqw"}            demo EQW recording -> real SAME decoder (multimon-ng -> same_to_alert) -> hub alert.
                                 A file into the decoder: nothing is played out loud or transmitted (47 CFR 11.45).
  {"cmd":"volume","value":0.8}   box speaker volume (PipeWire default sink), 0.0-1.5
  {"cmd":"mic_test","seconds":5} record from the box mics through the SAME path as a check-in answer, save it for
                                 playback (/demo/mic_test.wav), transcribe (ElevenLabs, Moonshine fallback), classify
  {"cmd":"ask","text":"..."}     ask the box what is going on: Nemotron answers from the recent bus events
  {"cmd":"ask_voice"}            same, but the question is spoken into the box mics
  {"cmd":"net","online":false}   cut the internet for the demo (every service switches to its on-board model)
Bus out: {"type":"demo_log","text":...}, {"type":"mic_test",...}, {"type":"assistant",...},
         {"type":"say","script_id":"assistant","text":...} (the voice service speaks the answer, no listening)
         {"type":"net","online":bool,"internet":bool,"cut":bool}  every NET_EVERY_S and on change: the real
             internet check AND the demo switch. The agent, voice and this runner skip cloud calls while offline.
         {"type":"engine","part":"ask"|"stt","name":...}  which model ran (cloud or on-board)
         {"type":"system","services":{...},"cpu_c":..,"mem_pct":..,"load":..}  box health every SYSTEM_EVERY_S

Run: HUB_URL=ws://localhost:8765 .venv/bin/python hardware/demo/runner.py   (env: NVIDIA_API_KEY, ELEVENLABS_API_KEY)
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
URL = os.environ.get("HUB_URL", "ws://localhost:8765")
MIC_WAV = ROOT / "software/web/demo/mic_test.wav"
NOISY = {"indoor", "pir", "presence", "people", "heartbeat", "demo_log", "assistant", "mic_test", "demo", "net",
         "system", "engine", "demo_state"}
CLOUD_URL = "https://integrate.api.nvidia.com/v1"
CLOUD_MODEL = os.environ.get("ASSISTANT_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
LOCAL_URL = os.environ.get("AGENT_OLLAMA_URL", "http://localhost:11434/v1")
LOCAL_MODEL = os.environ.get("ASSISTANT_LOCAL_MODEL", os.environ.get("AGENT_LOCAL_MODEL", "nemotron-3-nano:4b"))
NET_EVERY_S, SYSTEM_EVERY_S = 10, 5
SERVICES = ("hub", "agent", "voice", "camera", "sensors", "ring", "radio", "scream", "demo")
ASSISTANT_PROMPT = """You are LAND, a home safety box in the user's home in Richardson, Texas. The person in the room
is talking to you. Answer in at most 3 short spoken sentences, plain words, no lists, no markdown.
Use ONLY the event log you are given (official alerts heard on NOAA weather radio, sensor events, the check-in,
the camera). If the log does not say, say you have not heard anything about it. Never invent alerts or numbers.
If someone may be in danger, tell them to call 911 themselves; you never call emergency services.
If an alert has demo=true, say it is a demo, not a real alert."""


def log(*a):
    print(*a, file=sys.stderr, flush=True)


class Runner:
    def __init__(self, ws):
        self.ws, self.events, self.latest, self.stt = ws, deque(maxlen=60), {}, None
        self.internet, self.cut = True, False

    async def send(self, msg):
        await self.ws.send(json.dumps(msg))

    async def say(self, text):
        log(text)
        await self.send({"type": "demo_log", "text": text})

    def remember(self, m):
        t = m.get("type")
        if t in ("indoor", "presence", "people", "heartbeat", "power"):
            self.latest[t] = {k: v for k, v in m.items() if k != "t"}
        if t not in NOISY:
            self.events.append({"at": time.strftime("%H:%M:%S"), **{k: v for k, v in m.items() if k != "t"}})

    # ---- internet ----
    @property
    def online(self):
        return self.internet and not self.cut

    async def net_status(self):
        await self.send({"type": "net", "online": self.online, "internet": self.internet, "cut": self.cut})

    async def net(self, m):
        self.cut = m.get("online") is False
        await self.say("INTERNET CUT for the demo: every AI part now runs on the box" if self.cut
                       else "internet switch back on")
        await self.net_status()

    async def watch_net(self):
        """Real internet check: an HTTPS request to the Nemotron API host every NET_EVERY_S."""
        import requests
        while True:
            try:
                await asyncio.to_thread(requests.head, "https://integrate.api.nvidia.com", timeout=4)
                up = True
            except requests.RequestException:
                up = False
            if up != self.internet:
                self.internet = up
                await self.say("internet is back" if up else "INTERNET LOST: switching to the on-board models")
            await self.net_status()
            await asyncio.sleep(NET_EVERY_S)

    async def warm_local(self):
        """Load the on-board model into memory now (Ollama keeps it: OLLAMA_KEEP_ALIVE=-1), so the first
        offline answer or check-in plan does not also pay the load time."""
        t0 = time.monotonic()
        try:
            await self._chat(LOCAL_URL, "ollama", LOCAL_MODEL, "Say ready.", [], 180)
            log(f"on-board model {LOCAL_MODEL} loaded in {time.monotonic() - t0:.0f} s")
        except Exception as e:  # report; answers still try it later
            await self.say(f"on-board model {LOCAL_MODEL} did not load: {type(e).__name__}: {e}")

    async def watch_system(self):
        """Box health for the demo page: service states, CPU temperature, memory, load."""
        def sample():
            r = subprocess.run(["systemctl", "--user", "is-active", *(f"land-{n}" for n in SERVICES)],
                               capture_output=True, text=True)
            states = dict(zip(SERVICES, r.stdout.split()))
            o = subprocess.run(["systemctl", "is-active", "ollama"], capture_output=True, text=True)
            states["ollama"] = o.stdout.strip() or "missing"
            mem = dict(line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines())
            kb = lambda k: int(mem[k].split()[0])  # noqa: E731
            return {"type": "system", "services": states,
                    "cpu_c": round(int(Path("/sys/class/thermal/thermal_zone0/temp").read_text()) / 1000, 1),
                    "mem_pct": round(100 * (1 - kb("MemAvailable") / kb("MemTotal"))),
                    "load": round(os.getloadavg()[0], 2)}
        while True:
            try:
                await self.send(await asyncio.to_thread(sample))
            except OSError as e:  # not on the Pi (no /proc, /sys or systemctl): report once, stop
                return await self.say(f"box health unavailable here: {e!r}")
            await asyncio.sleep(SYSTEM_EVERY_S)

    # ---- radio ----
    async def radio_eqw(self, m):
        await self.say("RADIO: NOAA weather radio 162.400 MHz, decoding a SAME header (demo recording)")
        proc = await asyncio.create_subprocess_exec(
            str(ROOT / "software/same/listen.sh"), "--file", str(ROOT / "software/same/demo_eqw.wav"),
            cwd=ROOT, env={**os.environ, "HUB_URL": URL}, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        async for raw in proc.stdout:
            line = raw.decode(errors="replace").strip()
            if line.startswith("{"):
                try:
                    a = json.loads(line)
                    await self.say(f"DECODED: {a.get('code')} {a.get('event')} for {a.get('area')} (station {a.get('station')}) -> hub alert")
                    continue
                except ValueError:
                    pass
            if line:
                await self.say(f"decoder: {line[:160]}")
        if (rc := await proc.wait()) != 0:
            await self.say(f"decoder exited with code {rc}")

    # ---- speaker ----
    async def volume(self, m):
        v = max(0.0, min(1.5, float(m.get("value", 1.0))))
        r = subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{v:.2f}"], capture_output=True, text=True)
        if r.returncode:
            return await self.say(f"volume change failed: {r.stderr.strip()}")
        await self.send({"type": "demo_state", "volume": round(v, 2)})

    # ---- mic ----
    def _record(self, seconds):
        import numpy as np
        from software.voice.engines import record, trim_to_voice, wav_bytes
        audio = record(seconds, log)
        if audio is None:
            return None, {"error": "the mic returned pure silence (no audio from the I2S card)"}
        MIC_WAV.write_bytes(wav_bytes(audio))
        rms = float(np.sqrt((audio ** 2).mean()))
        voiced = trim_to_voice(audio)
        stats = {"rms_dbfs": round(20 * np.log10(rms + 1e-9), 1), "peak_dbfs": round(20 * np.log10(float(np.abs(audio).max()) + 1e-9), 1),
                 "voice_s": round(voiced.size / 16000, 2)}
        return audio, stats

    def _transcribe(self, audio):
        """ElevenLabs when online (the cloud check-in path), Moonshine on the box otherwise, like software.voice."""
        from software.voice.engines import ELEVEN_STT_MODEL, ELEVEN_URL, wav_bytes
        key = os.environ.get("ELEVENLABS_API_KEY")
        if key and self.online:
            import requests
            try:
                r = requests.post(f"{ELEVEN_URL}/speech-to-text", headers={"xi-api-key": key},
                                  data={"model_id": ELEVEN_STT_MODEL}, timeout=15,
                                  files={"file": ("answer.wav", wav_bytes(audio), "audio/wav")})
                r.raise_for_status()
                return r.json()["text"].strip(), "ElevenLabs Scribe (cloud)"
            except Exception as e:  # report, then fall back
                log(f"ElevenLabs speech-to-text failed: {e!r}")
        if self.stt is None:
            from software.voice.engines import MoonshineSTT
            self.stt = MoonshineSTT()
        return self.stt.transcribe(audio), "Moonshine (on-board)"

    async def mic_test(self, m):
        from software.voice.classify import classify
        secs = max(2.0, min(10.0, float(m.get("seconds", 5))))
        await self.say(f"MIC TEST: recording {secs:g} s now, speak to the box")
        audio, stats = await asyncio.to_thread(self._record, secs)
        if audio is None:
            return await self.send({"type": "mic_test", **stats})
        text, engine = await asyncio.to_thread(self._transcribe, audio)
        await self.send({"type": "engine", "part": "stt", "name": engine})
        await self.send({"type": "mic_test", **stats, "transcript": text, "engine": engine,
                         "answer": classify(text), "wav": f"/demo/mic_test.wav?{int(time.time())}"})

    # ---- assistant ----
    async def _chat(self, base_url, key, model, question, events, timeout):
        from openai import AsyncOpenAI
        ctx = {"recent_events_oldest_first": events, "latest_sensor_state": self.latest}
        client = AsyncOpenAI(base_url=base_url, api_key=key, max_retries=0)
        r = await asyncio.wait_for(client.chat.completions.create(
            model=model, temperature=0.3, max_tokens=160,
            messages=[{"role": "system", "content": ASSISTANT_PROMPT},
                      {"role": "user", "content": f"Event log JSON:\n{json.dumps(ctx)}\n\nQuestion: {question}"}],
            extra_body={"chat_template_kwargs": {"enable_thinking": False}, "reasoning_effort": "none"}), timeout)
        return (r.choices[0].message.content or "").strip()

    async def answer(self, question):
        """Cloud Nemotron when online; the on-board model (Ollama) when offline or when the cloud call fails."""
        key, text, engine, t0 = os.environ.get("NVIDIA_API_KEY"), "", "none", time.monotonic()
        if key and self.online:
            try:
                text = await self._chat(CLOUD_URL, key, CLOUD_MODEL, question, list(self.events), 20)
                engine = "Nemotron 30B (cloud)"
            except Exception as e:  # report, then the on-board model answers
                await self.say(f"cloud Nemotron failed ({type(e).__name__}); the on-board model answers")
        if not text:
            await self.send({"type": "engine", "part": "ask", "name": f"{LOCAL_MODEL} (on-board, thinking)"})
            try:  # small CPU model: only the last 12 events, so the prompt stays short
                text = await self._chat(LOCAL_URL, "ollama", LOCAL_MODEL, question, list(self.events)[-12:], 90)
                engine = f"{LOCAL_MODEL} (on-board)"
            except Exception as e:  # report, answer plainly
                await self.say(f"on-board model failed: {type(e).__name__}: {e}")
                text = "I can't think right now. If anyone is hurt, call 911."
        text = text or "I don't have an answer for that."
        await self.send({"type": "engine", "part": "ask", "name": engine, "seconds": round(time.monotonic() - t0, 1)})
        await self.send({"type": "assistant", "question": question, "answer": text, "engine": engine})
        await self.send({"type": "say", "script_id": "assistant", "text": text})

    async def ask(self, m):
        q = str(m.get("text", "")).strip()
        if q:
            await self.answer(q)

    async def ask_voice(self, m):
        await self.say("ASK: listening 5 s for your question")
        audio, stats = await asyncio.to_thread(self._record, 5)
        if audio is None:
            return await self.say("ASK: the mic heard nothing")
        q, engine = await asyncio.to_thread(self._transcribe, audio)
        await self.send({"type": "engine", "part": "stt", "name": engine})
        await self.say(f"ASK: heard \"{q}\" ({engine})")
        if q:
            await self.answer(q)


COMMANDS = ("radio_eqw", "volume", "mic_test", "ask", "ask_voice", "net")


async def main():
    import websockets
    while True:
        try:
            async with websockets.connect(URL, max_size=None) as ws:
                log(f"hub connected: {URL}")
                r, running = Runner(ws), set()
                bg = [asyncio.create_task(r.watch_net()), asyncio.create_task(r.watch_system()),
                      asyncio.create_task(r.warm_local())]
                try:
                    async for raw in ws:
                        try:
                            m = json.loads(raw)
                        except ValueError:
                            continue
                        r.remember(m)
                        if m.get("type") == "reset" and r.cut:  # reset brings the internet switch back on
                            r.cut = False
                            await r.net_status()
                        if m.get("type") != "demo":
                            continue
                        cmd = m.get("cmd")
                        fn = getattr(r, cmd, None) if cmd in COMMANDS else None
                        if fn is None:
                            await r.say(f"unknown demo command: {cmd!r}")
                        elif cmd in running:
                            await r.say(f"{cmd} is already running")
                        else:
                            running.add(cmd)

                            async def guarded(c=cmd, f=fn, msg=m):
                                try:
                                    await f(msg)
                                except Exception as e:  # show the failure on the demo page; never silent
                                    await r.say(f"{c} failed: {e!r}")
                                finally:
                                    running.discard(c)

                            asyncio.create_task(guarded())
                finally:
                    for t in bg:
                        t.cancel()
        except Exception as e:  # report and retry; never silent
            log(f"hub error ({URL}): {e!r}; retrying in 2 s")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
