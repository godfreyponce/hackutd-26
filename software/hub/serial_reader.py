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


def open_port(port: str) -> serial.Serial:
    """Opening flushes the input buffer, so lines sent before this returns are lost."""
    return serial.Serial(port, BAUD, timeout=0.5)


async def run_serial(hub, ser: serial.Serial):
    log.info("reading JSON lines from %s at %d baud", ser.port, BAUD)
    try:
        while True:
            line = await asyncio.to_thread(ser.readline)
            forward_line(hub, line)
    finally:
        ser.close()
