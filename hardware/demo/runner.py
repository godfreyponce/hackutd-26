"""Demo runner: runs the REAL pipelines when the demo page asks, and narrates them on the bus.

Bus in:  {"type":"demo","cmd":"radio_eqw"}
         The demo earthquake-warning recording (software/same/demo_eqw.wav) goes through the real
         decoder chain, multimon-ng -> same_to_alert -> hub "alert", exactly like a broadcast from the SDR.
         A file into the decoder: nothing is played out loud and nothing is transmitted (47 CFR 11.45,
         see software/same/README.md).
Bus out: {"type":"demo_log","text":"..."} lines so the page shows each stage as it happens.

Run: HUB_URL=ws://localhost:8765 .venv/bin/python hardware/demo/runner.py
"""
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = os.environ.get("HUB_URL", "ws://localhost:8765")


def log(*a):
    print(*a, file=sys.stderr, flush=True)


async def radio_eqw(say):
    await say("RADIO: NOAA weather radio channel 162.400 MHz, decoding a SAME header (demo recording)")
    proc = await asyncio.create_subprocess_exec(
        str(ROOT / "software/same/listen.sh"), "--file", str(ROOT / "software/same/demo_eqw.wav"),
        cwd=ROOT, env={**os.environ, "HUB_URL": URL},
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    async for raw in proc.stdout:
        line = raw.decode(errors="replace").strip()
        if not line:
            continue
        if line.startswith("{"):
            try:
                a = json.loads(line)
                await say(f"DECODED: {a.get('code')} {a.get('event')} for {a.get('area')} (station {a.get('station')}) -> hub alert")
                continue
            except ValueError:
                pass
        await say(f"decoder: {line[:160]}")
    rc = await proc.wait()
    if rc != 0:
        await say(f"decoder exited with code {rc}")


CMDS = {"radio_eqw": radio_eqw}


async def main():
    import websockets
    while True:
        try:
            async with websockets.connect(URL) as ws:
                log(f"hub connected: {URL}")

                async def say(text):
                    log(text)
                    await ws.send(json.dumps({"type": "demo_log", "text": text}))

                running = set()
                async for raw in ws:
                    try:
                        m = json.loads(raw)
                    except ValueError:
                        continue
                    if m.get("type") != "demo":
                        continue
                    cmd = m.get("cmd")
                    if cmd not in CMDS:
                        await say(f"unknown demo command: {cmd!r}")
                    elif cmd in running:
                        await say(f"{cmd} is already running")
                    else:
                        running.add(cmd)
                        t = asyncio.create_task(CMDS[cmd](say))
                        t.add_done_callback(lambda _t, c=cmd: running.discard(c))
        except Exception as e:  # report and retry; never silent
            log(f"hub error ({URL}): {e!r}; retrying in 2 s")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
