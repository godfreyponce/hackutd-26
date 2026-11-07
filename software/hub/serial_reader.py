import asyncio
import logging

import serial

from software.hub.bus import BadMessage, now_ms, parse_message

log = logging.getLogger("hub.serial")

BAUD = 115200


def forward_line(hub, line: bytes) -> None:
    line = line.strip()
    if not line:
        return
    try:
        msg = hub.publish(parse_message(line, now_ms()))
    except BadMessage as e:
        log.warning("skipped serial line: %s: %.200r", e, line)
        return
    log.info("serial -> %s", msg)


async def run_serial(hub, port: str):
    ser = serial.Serial(port, BAUD, timeout=0.5)
    log.info("reading JSON lines from %s at %d baud", port, BAUD)
    try:
        while True:
            line = await asyncio.to_thread(ser.readline)
            forward_line(hub, line)
    finally:
        ser.close()
