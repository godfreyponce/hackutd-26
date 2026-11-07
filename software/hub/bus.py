import json
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from websockets.asyncio.server import ServerConnection, broadcast, serve

from software.hub.web import start_static

log = logging.getLogger("hub")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class BadMessage(ValueError):
    pass


def now_ms() -> int:
    return int(time.time() * 1000)


def parse_message(raw: str | bytes, now_ms: int) -> dict:
    try:
        msg = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise BadMessage(f"not JSON: {e}") from None
    if not isinstance(msg, dict):
        raise BadMessage(f"not a JSON object: {type(msg).__name__}")
    msg.setdefault("t", now_ms)
    return msg


class Hub:
    def __init__(self):
        self.clients: set[ServerConnection] = set()
        self.listeners = []
        self.ws_port = 0
        self.http_port = 0

    def publish(self, msg: dict) -> dict:
        msg.setdefault("t", now_ms())
        broadcast(self.clients, json.dumps(msg))
        for listener in self.listeners:
            listener(msg)
        return msg

    async def handle(self, ws: ServerConnection):
        self.clients.add(ws)
        log.info("client connected: %s (%d total)", ws.remote_address, len(self.clients))
        try:
            async for raw in ws:
                try:
                    self.publish(parse_message(raw, now_ms()))
                except BadMessage as e:
                    log.warning("dropped message from %s: %s: %.200r", ws.remote_address, e, raw)
        finally:
            self.clients.discard(ws)
            log.info("client left: %s (%d total)", ws.remote_address, len(self.clients))


@asynccontextmanager
async def running_hub(host: str, ws_port: int, http_port: int, web_dir: Path = WEB_DIR):
    hub = Hub()
    async with serve(hub.handle, host, ws_port) as server:
        httpd = start_static(host, http_port, web_dir)
        hub.ws_port = server.sockets[0].getsockname()[1]
        hub.http_port = httpd.server_address[1]
        log.info("bus on ws://%s:%d, web on http://%s:%d/ (%s)", host, hub.ws_port, host, hub.http_port, web_dir)
        try:
            yield hub
        finally:
            httpd.shutdown()
            httpd.server_close()
