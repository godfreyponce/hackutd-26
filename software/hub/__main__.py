import argparse
import asyncio
import logging

from software.hub.bus import running_hub


async def main(args):
    async with running_hub(args.host, args.ws_port, args.http_port) as hub:
        if args.sim:
            from software.hub.sim import run_sim

            await run_sim(hub)
        else:
            from software.hub.serial_reader import open_port, run_serial

            await run_serial(hub, open_port(args.serial))


def cli():
    p = argparse.ArgumentParser(prog="python -m software.hub", description="Event hub: WebSocket bus + static web.")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sim", action="store_true", help="the Mac pretends to be the box (keyboard)")
    mode.add_argument("--serial", metavar="PORT", help="read JSON lines from the ESP32, e.g. /dev/tty.usbserial-XXXX")
    p.add_argument("--ws-port", type=int, default=8765)
    p.add_argument("--http-port", type=int, default=8080)
    p.add_argument("--host", default="localhost", help="bind address (0.0.0.0 to reach the hub from another device)")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    cli()
