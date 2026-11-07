"""Print every bus message, one JSON object per line. Reads HUB_URL."""

import asyncio
import sys

from websockets.asyncio.client import connect

from software.hub import hub_url


async def tap(url: str):
    async with connect(url) as ws:
        print(f"tapping {url}", file=sys.stderr, flush=True)
        async for raw in ws:
            print(raw, flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(tap(hub_url()))
    except KeyboardInterrupt:
        pass
