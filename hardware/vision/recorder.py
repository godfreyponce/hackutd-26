"""Incident recorder: what responders see when they arrive.

Keeps the last PRE_S seconds of the camera AI view (the overlay stream, faces already blurred). When a check-in
starts (shaking, fall, help sign, heat, scream, or an EQW radio alert) it saves every frame from PRE_S before the
event, plus the event timeline, the AI hand-off note (Nemotron) and the phone-call lines. It keeps recording while the
alarm is up (help is on the way) until reset, or until the room has been quiet for IDLE_S with no alarm.

Saved to software/web/incidents/<id>/ and listed in incidents/list.json; the hub serves /incidents/ to any screen.
Bus out: {"type":"recording","state":"on"|"saved","id":...,"frames":N}

Run: HUB_URL=ws://localhost:8765 .venv/bin/python hardware/vision/recorder.py
"""
import asyncio
import json
import os
import sys
import threading
import time
import urllib.request
from collections import deque
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "software/web/incidents"
STREAM = os.environ.get("CAMERA_STREAM", "http://localhost:8090/stream.mjpg")
FPS, PRE_S, IDLE_S, MAX_S = 5, 20, 45, 600
TRIGGERS = {"quake", "fall_hint", "help_gesture", "heat", "scream"}
QUIET = {"indoor", "pir", "presence", "people", "heartbeat", "system", "net", "engine", "shake", "demo_log",
         "demo_state", "recording", "radio_live", "speaker", "demo", "call_bridge"}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


class Incident:
    def __init__(self, first, pre):
        self.start = time.time()
        self.id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.dir = OUT / self.id
        (self.dir / "frames").mkdir(parents=True, exist_ok=True)
        self.meta = {"id": self.id, "started": datetime.now().strftime("%b %d %I:%M:%S %p"), "fps": FPS,
                     "trigger": first.get("type") if first.get("type") != "alert" else f"{first.get('code')} alert",
                     "frames": [], "events": [], "handoff": None, "calls": [], "status": "recording"}
        self.last_event, self.alarm = self.start, False
        for t, jpg in pre:
            self.add(t, jpg)

    def add(self, t, jpg):
        n = len(self.meta["frames"])
        (self.dir / "frames" / f"{n:06d}.jpg").write_bytes(jpg)
        self.meta["frames"].append(round(t - self.start, 2))

    def event(self, m):
        t = m.get("type")
        if t in QUIET:
            return
        self.last_event = time.time()
        row = {"t": round(time.time() - self.start, 1), **{k: v for k, v in m.items() if k not in ("source",)}}
        self.meta["events"].append(row)
        if t == "handoff":
            self.meta["handoff"] = {k: m.get(k) for k in ("note", "why", "contact", "by", "why_by")}
        if t == "call" and m.get("state") == "dialing":
            self.meta["calls"].append({"kind": m.get("kind"), "text": m.get("summary")})
        if t == "checkin":
            self.alarm = m.get("state") in ("alarm", "help") or (self.alarm and m.get("state") not in ("ok", "clear"))
        self.save()

    def done(self, now):
        if now - self.start > MAX_S:
            return True
        return not self.alarm and now - self.last_event > IDLE_S

    def save(self, status=None):
        if status:
            self.meta["status"] = status
        tmp = self.dir / "incident.json.tmp"
        tmp.write_text(json.dumps(self.meta))
        tmp.replace(self.dir / "incident.json")


class Recorder:
    def __init__(self):
        self.pre, self.inc, self.lock, self.out = deque(maxlen=PRE_S * FPS), None, threading.Lock(), None

    def frame(self, jpg):
        with self.lock:
            if self.inc:
                self.inc.add(time.time(), jpg)
            else:
                self.pre.append((time.time(), jpg))

    def on(self, m):
        t = m.get("type")
        with self.lock:
            if t == "reset" and self.inc:
                return self._close("reset")
            if self.inc is None and (t in TRIGGERS or (t == "alert" and m.get("code") == "EQW")):
                self.inc = Incident(m, list(self.pre))
                self.pre.clear()
                self._list()
                self._tell({"type": "recording", "state": "on", "id": self.inc.id})
                log(f"recording incident {self.inc.id} ({t})")
            if self.inc:
                self.inc.event(m)

    def tick(self):
        with self.lock:
            if self.inc and self.inc.done(time.time()):
                self._close("idle" if time.time() - self.inc.start <= MAX_S else "max length")

    def _close(self, why):
        inc, self.inc = self.inc, None
        inc.save("saved")
        self._list()
        self._tell({"type": "recording", "state": "saved", "id": inc.id, "frames": len(inc.meta["frames"])})
        log(f"saved incident {inc.id}: {len(inc.meta['frames'])} frames, {len(inc.meta['events'])} events ({why})")

    def _list(self):
        rows = []
        for d in sorted(OUT.glob("*/incident.json"), reverse=True):
            try:
                m = json.loads(d.read_text())
            except ValueError:
                continue
            rows.append({k: m.get(k) for k in ("id", "started", "trigger", "status")})
        (OUT / "list.json").write_text(json.dumps(rows))

    def _tell(self, msg):
        if self.out:
            self.out(msg)


def read_stream(rec):
    """Pull the camera AI's MJPEG stream; keep FPS frames per second. Reconnects; reports failures."""
    while True:
        try:
            with urllib.request.urlopen(STREAM, timeout=10) as r:
                log(f"camera stream connected: {STREAM}")
                buf, next_t = b"", 0.0
                while chunk := r.read(16384):
                    buf += chunk
                    while (a := buf.find(b"\xff\xd8")) >= 0 and (b := buf.find(b"\xff\xd9", a)) >= 0:
                        jpg, buf = buf[a:b + 2], buf[b + 2:]
                        if time.time() >= next_t:
                            rec.frame(jpg)
                            next_t = time.time() + 1 / FPS
        except Exception as e:  # report and retry; never silent
            log(f"camera stream error ({STREAM}): {e!r}; retrying in 3 s")
            time.sleep(3)


async def bus(rec, url):
    import websockets
    while True:
        try:
            async with websockets.connect(url) as ws:
                log(f"hub connected: {url}")
                loop = asyncio.get_running_loop()
                rec.out = lambda m: asyncio.run_coroutine_threadsafe(ws.send(json.dumps(m)), loop)
                async for raw in ws:
                    try:
                        m = json.loads(raw)
                    except ValueError:
                        continue
                    if isinstance(m, dict):
                        await asyncio.to_thread(rec.on, m)
        except Exception as e:  # report and retry; never silent
            rec.out = None
            log(f"hub error ({url}): {e!r}; retrying in 2 s")
            await asyncio.sleep(2)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rec = Recorder()
    rec._list()
    threading.Thread(target=read_stream, args=(rec,), daemon=True).start()
    asyncio.create_task(bus(rec, os.environ.get("HUB_URL", "ws://localhost:8765")))
    while True:
        await asyncio.sleep(1)
        rec.tick()


if __name__ == "__main__":
    asyncio.run(main())
