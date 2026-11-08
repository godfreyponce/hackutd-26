"""Camera presence for the hub: python -m software.presence"""

import argparse
import asyncio
import json
import logging

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidHandshake

from software.hub import hub_url
from software.presence.sources import DEFAULT_HEF, camera_frames, replay_frames, stdin_frames
from software.presence.tracker import FALL_HINT_COOLDOWN_S, Tracker

log = logging.getLogger("presence")

RETRY_S = 1.0  # same retry as the agent


class HubLink:
    """Stays connected to the hub and reads everything it broadcasts. Calls on_reset() for each reset."""

    def __init__(self, url, on_reset):
        self.url = url
        self.on_reset = on_reset
        self.ws = None
        self.connected = asyncio.Event()

    async def run(self):
        while True:
            try:
                async with connect(self.url) as ws:
                    self.ws = ws
                    self.connected.set()
                    log.info("connected to %s", self.url)
                    async for raw in ws:
                        if _type(raw) == "reset":
                            await self.on_reset()
            except (OSError, ConnectionClosed, InvalidHandshake) as e:
                log.warning("hub %s: %s. Retrying in %.0f s.", self.url, e, RETRY_S)
            self.ws = None
            self.connected.clear()
            await asyncio.sleep(RETRY_S)

    async def send(self, msg):
        if self.ws is None:
            log.warning("hub not connected, dropped %s", json.dumps(msg))
            return
        try:
            await self.ws.send(json.dumps(msg))
            log.info("-> %s", json.dumps(msg))
        except ConnectionClosed:
            log.warning("hub closed, dropped %s", json.dumps(msg))


def _type(raw):
    try:
        msg = json.loads(raw)
    except ValueError:
        return None
    return msg.get("type") if isinstance(msg, dict) else None


async def run(url, frames, tracker):
    async def resend_state():
        # A reset puts every piece's presence back to none. Restore it now, not at the next 5 s repeat.
        tracker.hub_reset()
        if tracker.state is not None:
            await link.send({"type": "presence", "state": tracker.state})

    link = HubLink(url, resend_state)
    reader = asyncio.create_task(link.run())
    try:
        connected = asyncio.create_task(link.connected.wait())
        await asyncio.wait({connected, reader}, return_when=asyncio.FIRST_COMPLETED)
        if reader.done():
            connected.cancel()
            reader.result()  # a bad HUB_URL raises here instead of waiting forever
        async for t, boxes in frames:
            for event in tracker.update(t, boxes):
                await link.send(event)
    finally:
        reader.cancel()


def cli():
    p = argparse.ArgumentParser(prog="python -m software.presence",
                                description="Camera presence: person boxes in, presence events to the hub (HUB_URL).")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--stdin", action="store_true",
                     help='read JSON lines {"t": seconds, "boxes": [[x0,y0,x1,y1,score], ...]} from stdin')
    src.add_argument("--replay", metavar="FILE", help="play a file of the same JSON lines at its own pace")
    p.add_argument("--hef", default=DEFAULT_HEF, help="YOLOv8 model for the camera source (default %(default)s)")
    p.add_argument("--no-fall-hint", action="store_true", help="never send fall_hint")
    p.add_argument("--fall-hint-cooldown", type=float, default=FALL_HINT_COOLDOWN_S, metavar="S",
                   help="at most one fall_hint per S seconds (default %(default)s)")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("websockets").setLevel(logging.WARNING)

    if args.stdin:
        frames = stdin_frames()
    elif args.replay:
        frames = replay_frames(args.replay)
    else:
        frames = camera_frames(args.hef)
    tracker = Tracker(fall_hint=not args.no_fall_hint, fall_hint_cooldown_s=args.fall_hint_cooldown)
    try:
        asyncio.run(run(hub_url(), frames, tracker))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    cli()
