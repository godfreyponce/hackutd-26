"""Live radio tap, between rtl_fm and the SAME decoder (see noaa.sh decode).

Passes the 22050 Hz radio audio through to multimon-ng untouched. While the demo page turns it on
({"type":"radio_live","on":true} on the bus), it also plays the same audio on the box speaker, so the
room hears NOAA Weather Radio live off the antenna. {"type":"reset"} or on:false stops it.
Receive only: nothing here transmits.
"""
import asyncio
import json
import os
import subprocess
import sys
import threading

RATE, CHUNK = 22050, 2205 * 2  # 0.1 s of 16-bit mono
player = None


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def set_live(on):
    global player
    p = player
    if on and p is None:
        player = subprocess.Popen(["aplay", "-q", "-t", "raw", "-f", "S16_LE", "-r", str(RATE), "-c", "1"],
                                  stdin=subprocess.PIPE)
    elif not on and p is not None:
        player = None
        p.terminate()
    log(f"radio live audio {'ON' if on else 'off'}")


async def listen(url):
    import websockets
    while True:
        try:
            async with websockets.connect(url) as ws:
                log(f"hub connected: {url}")
                async for raw in ws:
                    try:
                        m = json.loads(raw)
                    except ValueError:
                        continue
                    if not isinstance(m, dict):
                        continue
                    if m.get("type") == "radio_live":
                        set_live(m.get("on") is True)
                    elif m.get("type") == "reset" and player:
                        set_live(False)
        except Exception as e:  # report and retry; never silent
            log(f"hub error ({url}): {e!r}; retrying in 2 s")
            await asyncio.sleep(2)


def main():
    threading.Thread(target=asyncio.run, args=(listen(os.environ.get("HUB_URL", "ws://localhost:8765")),),
                     daemon=True).start()
    out = sys.stdout.buffer
    while data := sys.stdin.buffer.read(CHUNK):
        out.write(data)
        out.flush()
        p = player
        if p:
            try:
                p.stdin.write(data)
                p.stdin.flush()
            except (BrokenPipeError, OSError) as e:  # the player died: report and turn live audio off
                log(f"radio live player stopped: {e!r}")
                set_live(False)


if __name__ == "__main__":
    main()
