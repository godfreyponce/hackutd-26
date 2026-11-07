import asyncio
import json
import os

from websockets.asyncio.client import connect

from software.hub.bus import running_hub
from software.hub.serial_reader import open_port, run_serial


def test_serial_forwards_good_json_lines_and_skips_bad_ones():
    master, slave = os.openpty()
    port = os.ttyname(slave)

    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            async with connect(f"ws://127.0.0.1:{hub.ws_port}") as ws:
                reader = asyncio.create_task(run_serial(hub, open_port(port)))
                os.write(master, b'garbage\n[1,2]\n\n{"type":"presence","state":"still"}\n{"t":12345,"type":"quake","peak_g":0.82}\n')
                got = [json.loads(await asyncio.wait_for(ws.recv(), timeout=3)) for _ in range(2)]
                reader.cancel()
                return got

    try:
        still, quake = asyncio.run(scenario())
    finally:
        os.close(master)
        os.close(slave)
    assert still["type"] == "presence" and still["state"] == "still" and isinstance(still["t"], int)
    assert quake == {"t": 12345, "type": "quake", "peak_g": 0.82}
