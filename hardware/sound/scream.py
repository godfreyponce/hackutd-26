"""Scream / loud-crash trigger from the box mics -> hub {"type":"scream","db":-12.3}.

What it detects: a LOUD, SUSTAINED sound well above the room's own noise: a scream, a shout for help,
something heavy falling. It is a loudness rule, not a trained scream classifier: a loud clap burst can
also trip it. The agent then asks "are you okay?", and the alarm rule decides; a false trigger costs one question.

It stays deaf while the box itself talks or a check-in is open (it listens to say/checkin/reset on the bus),
so the box never triggers itself.

Audio: PipeWire default source (the I2S mics), 16 kHz mono, shared with the voice service.
Run: HUB_URL=ws://localhost:8765 .venv/bin/python hardware/sound/scream.py   (--dry-run: print only)
"""
import argparse
import asyncio
import json
import os
import sys
import time
from collections import deque

import numpy as np
import sounddevice as sd

RATE, BLOCK_S = 16000, 0.1
ABOVE_FLOOR_DB = 22     # this much louder than the room's noise floor ...
MIN_DBFS = -32          # ... and at least this loud in absolute terms
LOUD_BLOCKS = 4         # loud in >= 4 of the last 6 blocks (~0.4 s): a single knock does not count
COOLDOWN_S = 30
FLOOR_WINDOW_S = 30


def log(*a):
    print(*a, file=sys.stderr, flush=True)


class Mute:
    """Deaf while the box speaks or a check-in is open."""

    def __init__(self):
        self.until, self.open = 0.0, False

    def on(self, m):
        t = m.get("type")
        if t == "say":
            self.until = max(self.until, time.monotonic() + 1.5 + 0.08 * len(m.get("text", "")) + float(m.get("listen_s") or 0))
        elif t == "checkin":
            self.open = m.get("state") in ("asking", "no_answer", "alarm", "help")
            if m.get("state") == "alarm":
                self.until = max(self.until, time.monotonic() + 6)  # siren
        elif t == "reset":
            self.until, self.open = 0.0, False

    def deaf(self):
        return self.open or time.monotonic() < self.until


async def hub(url, out, mute, dry):
    import websockets
    while True:
        try:
            async with websockets.connect(url) as ws:
                log(f"hub connected: {url}")

                async def rx():
                    async for raw in ws:
                        try:
                            mute.on(json.loads(raw))
                        except (ValueError, AttributeError):
                            pass  # not JSON: not a bus event

                rxt = asyncio.create_task(rx())
                try:
                    while True:
                        msg = await out.get()
                        if not dry:
                            await ws.send(json.dumps(msg))
                finally:
                    rxt.cancel()
        except Exception as e:  # report and retry; never silent
            log(f"hub error ({url}): {e!r}; retrying in 2 s")
            await asyncio.sleep(2)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    out, mute, loop = asyncio.Queue(), Mute(), asyncio.get_running_loop()
    asyncio.create_task(hub(os.environ.get("HUB_URL", "ws://localhost:8765"), out, mute, args.dry_run))
    levels = deque(maxlen=int(FLOOR_WINDOW_S / BLOCK_S))
    recent, last = deque(maxlen=6), 0.0
    blocks = asyncio.Queue()

    def cb(indata, frames, t, status):
        if status:
            log(f"audio status: {status}")
        loop.call_soon_threadsafe(blocks.put_nowait, indata[:, 0].copy())

    with sd.InputStream(samplerate=RATE, channels=1, dtype="float32", blocksize=int(RATE * BLOCK_S), callback=cb):
        log("listening (default PipeWire source)")
        while True:
            x = await blocks.get()
            db = 20 * np.log10(np.sqrt(np.mean(x * x)) + 1e-9)
            if mute.deaf():
                recent.clear()
                continue
            floor = np.percentile(levels, 20) if len(levels) > 20 else -60.0
            levels.append(db)
            recent.append(db > max(floor + ABOVE_FLOOR_DB, MIN_DBFS))
            if sum(recent) >= LOUD_BLOCKS and time.monotonic() - last > COOLDOWN_S:
                msg = {"type": "scream", "db": round(float(db), 1), "floor_db": round(float(floor), 1)}
                print(json.dumps(msg), flush=True)
                out.put_nowait(msg)
                last = time.monotonic()
                recent.clear()


if __name__ == "__main__":
    asyncio.run(main())
