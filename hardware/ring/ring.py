"""NeoPixel status ring: shows the box state from the hub bus. Read-only client; sends nothing.

| Bus state                                 | Ring                          |
|-------------------------------------------|-------------------------------|
| hub not connected                          | dim blue, slow breathe        |
| idle / checkin ok or clear / reset         | dim green, steady             |
| alert level watch / warning                | yellow / orange, steady       |
| quake, fall_hint, help_gesture             | white flash, then check-in    |
| checkin asking or no_answer                | amber, spinning               |
| alert level emergency                      | red, slow pulse               |
| checkin alarm or help                      | red, fast flash               |

Pi 5 driver: Adafruit Blinka Raspberry Pi 5 NeoPixel (RP1 PIO), data on GPIO10 through 330 ohm.
Run: HUB_URL=ws://localhost:8765 python3 hardware/ring/ring.py
"""
import asyncio
import json
import math
import os
import sys
import time

import adafruit_pixelbuf
import board
from adafruit_raspberry_pi5_neopixel_write import neopixel_write

N, BRIGHT = 16, 0.25      # keep <= 30 % (power budget in WIRING.md)


class Ring(adafruit_pixelbuf.PixelBuf):
    def __init__(self):
        super().__init__(N, byteorder="GRB", brightness=BRIGHT, auto_write=False)

    def _transmit(self, buf):
        neopixel_write(board.D10, buf)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


class State:
    def __init__(self):
        self.connected, self.mode, self.flash_until, self.level = False, "idle", 0.0, None

    def on(self, m):
        t = m.get("type")
        if t == "reset":
            self.mode, self.level = "idle", None
        elif t in ("quake", "fall_hint", "help_gesture"):
            self.flash_until = time.monotonic() + 1.0
        elif t == "alert":
            self.level = m.get("level")
        elif t == "checkin":
            s = m.get("state")
            self.mode = {"asking": "asking", "no_answer": "asking", "alarm": "alarm", "help": "alarm",
                         "ok": "idle", "clear": "idle"}.get(s, self.mode)

    def frame(self, now):
        if not self.connected:
            v = int(40 + 40 * math.sin(now * 1.5))
            return [(0, 0, v)] * N
        if now < self.flash_until:
            return [(255, 255, 255)] * N
        if self.mode == "alarm":
            return [(255, 0, 0) if int(now * 4) % 2 else (0, 0, 0)] * N
        if self.mode == "asking":
            head = int(now * 12) % N
            return [(255, 120, 0) if (i - head) % N < 4 else (20, 8, 0) for i in range(N)]
        if self.level == "emergency":
            v = int(120 + 120 * math.sin(now * 3))
            return [(v, 0, 0)] * N
        if self.level in ("watch", "warning"):
            return [(255, 200, 0) if self.level == "watch" else (255, 90, 0)] * N
        return [(0, 60, 0)] * N


async def listen(url, st):
    import websockets
    while True:
        try:
            async with websockets.connect(url) as ws:
                st.connected = True
                log(f"hub connected: {url}")
                async for raw in ws:
                    try:
                        st.on(json.loads(raw))
                    except (ValueError, AttributeError):
                        log(f"skipped non-JSON message: {raw!r:.80}")
        except Exception as e:  # report and retry; never silent
            st.connected = False
            log(f"hub error ({url}): {e!r}; retrying in 2 s")
            await asyncio.sleep(2)


async def main():
    url = os.environ.get("HUB_URL", "ws://localhost:8765")
    ring, st = Ring(), State()
    asyncio.create_task(listen(url, st))
    try:
        while True:
            for i, c in enumerate(st.frame(time.monotonic())):
                ring[i] = c
            ring.show()
            await asyncio.sleep(0.05)
    finally:
        ring.fill(0)
        ring.show()


if __name__ == "__main__":
    asyncio.run(main())
