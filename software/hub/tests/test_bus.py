import asyncio
import json
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

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


class BrandRefs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if (tag == "link" and a.get("rel") == "icon") or tag == "img":
            self.refs.append(a.get("href") or a.get("src"))


def test_landing_page_says_land_and_every_brand_file_it_points_to_is_served():
    def get(url):
        with urllib.request.urlopen(url, timeout=2) as r:
            return r.headers["Content-Type"], r.read().decode()

    async def scenario():
        async with running_hub("127.0.0.1", 0, 0) as hub:
            root = f"http://127.0.0.1:{hub.http_port}/"
            _, page = await asyncio.to_thread(get, root)
            parser = BrandRefs()
            parser.feed(page)
            served = [await asyncio.to_thread(get, urljoin(root, ref)) for ref in parser.refs]
            return page, parser.refs, served

    page, refs, served = asyncio.run(scenario())
    assert "<title>LAND</title>" in page
    assert "brand/land-favicon-16.svg" in refs and "brand/land-wordmark-white.svg" in refs
    assert all(ctype == "image/svg+xml" and body.startswith("<svg") for ctype, body in served)
