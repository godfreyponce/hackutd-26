import asyncio
import json
import urllib.request

from websockets.asyncio.client import connect

from software.hub.bus import running_hub


async def recv_json(ws):
    return json.loads(await asyncio.wait_for(ws.recv(), timeout=2))


def test_rebroadcast_reaches_both_clients_including_sender():
    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            url = f"ws://127.0.0.1:{hub.ws_port}"
            async with connect(url) as a, connect(url) as b:
                await a.send('{"type":"heard","answer":"ok","transcript":"I am okay"}')
                got_a, got_b = await recv_json(a), await recv_json(b)
        assert got_a == got_b
        assert got_a["type"] == "heard" and isinstance(got_a["t"], int)

    asyncio.run(scenario())


def test_bad_messages_are_dropped_and_the_bus_keeps_working():
    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            url = f"ws://127.0.0.1:{hub.ws_port}"
            async with connect(url) as a, connect(url) as b:
                await a.send("not json")
                await a.send("[1,2]")
                await a.send('{"type":"reset"}')
                return await recv_json(b)

    assert asyncio.run(scenario())["type"] == "reset"


def test_publish_from_inside_the_hub_reaches_clients():
    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            async with connect(f"ws://127.0.0.1:{hub.ws_port}") as a:
                hub.publish({"type": "quake", "peak_g": 0.82})
                return await recv_json(a)

    got = asyncio.run(scenario())
    assert got["type"] == "quake" and "t" in got


def test_static_server_serves_web_dir(tmp_path):
    (tmp_path / "index.html").write_text("<h1>hello hub</h1>")

    async def scenario():
        async with running_hub("127.0.0.1", 0, 0, web_dir=tmp_path) as hub:
            url = f"http://127.0.0.1:{hub.http_port}/"
            return await asyncio.to_thread(lambda: urllib.request.urlopen(url, timeout=2).read())

    assert b"hello hub" in asyncio.run(scenario())
