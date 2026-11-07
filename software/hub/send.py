"""Send one JSON object to the bus: python -m software.hub.send '{"type":"reset"}'. Reads HUB_URL."""

import asyncio
import json
import sys

from websockets.asyncio.client import connect

from software.hub import hub_url


async def send(url: str, msg: dict):
    async with connect(url) as ws:
        await ws.send(json.dumps(msg))


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m software.hub.send '<json object>'", file=sys.stderr)
        return 2
    try:
        msg = json.loads(argv[0])
    except json.JSONDecodeError as e:
        print(f"not JSON: {e}", file=sys.stderr)
        return 2
    if not isinstance(msg, dict):
        print("not a JSON object", file=sys.stderr)
        return 2
    asyncio.run(send(hub_url(), msg))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
