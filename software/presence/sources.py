"""Frame sources. Each yields (t, boxes) once per camera frame, also when no person is in it.

A box is [x0, y0, x1, y1, score] in frame fractions (0..1).
"""

import asyncio
import json
import logging
import sys
import threading
import time

log = logging.getLogger("presence.sources")

# The Hailo-8 build of YOLOv8s from the hailo-models package. Unverified: check the path on the Pi.
DEFAULT_HEF = "/usr/share/hailo-models/yolov8s_h8.hef"
# The camera stream size from the picamera2 detect example. The model gets a lores copy of the same
# view, scaled to its input size. Unverified: on the 16:9 sensor, 4:3 may cut off the sides.
MAIN_SIZE = (1280, 960)
PERSON_CLASS = 0  # COCO class 0 is "person"
# hardware/vision/posture.py also prints its own hub events on stdout as "EVENT {...}". They are not frames.
POSTURE_EVENT_PREFIX = "EVENT "


def parse_frame(line):
    """One JSON line {"t": seconds, "boxes": [[x0,y0,x1,y1,score], ...]} -> (t, boxes), or None if bad.

    "t" is optional. Without it the frame gets the time it arrived.
    """
    if line.startswith(POSTURE_EVENT_PREFIX):
        return None
    try:
        msg = json.loads(line)
        t = float(msg["t"]) if "t" in msg else time.monotonic()
        boxes = [[float(v) for v in b] for b in msg["boxes"]]
    except (ValueError, TypeError, KeyError) as e:
        log.warning("bad frame line skipped (%s): %.80s", e, line.strip())
        return None
    if any(len(b) != 5 for b in boxes):
        log.warning("bad frame line skipped (a box needs 5 numbers): %.80s", line.strip())
        return None
    return t, boxes


async def stdin_frames():
    while line := await asyncio.to_thread(sys.stdin.readline):
        if line.strip() and (frame := parse_frame(line)):
            yield frame


async def replay_frames(path, sleep=asyncio.sleep):
    """Play a recorded file at its own pace, using the times in the file."""
    prev = None
    with open(path) as f:
        for line in f:
            if not line.strip() or not (frame := parse_frame(line)):
                continue
            if prev is not None:
                await sleep(max(0.0, frame[0] - prev))
            prev = frame[0]
            yield frame


def person_boxes(hailo_output):
    """picamera2's Hailo NMS output is one list per class of [y0, x0, y1, x1, score]."""
    return [[x0, y0, x1, y1, score] for y0, x0, y1, x1, score in hailo_output[PERSON_CLASS]]


async def camera_frames(hef=DEFAULT_HEF):
    """Camera Module 3 + AI HAT+ through picamera2's Hailo helper. Unverified until it runs on the Pi.

    Based on the picamera2 examples/hailo detect example. Needs the Pi's system picamera2,
    so the venv must be made with --system-site-packages.
    """
    from picamera2 import Picamera2
    from picamera2.devices import Hailo

    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()
    stop = threading.Event()

    def put(item):
        try:
            loop.call_soon_threadsafe(queue.put_nowait, item)
        except RuntimeError:  # the event loop is gone: the program is quitting
            stop.set()

    def capture():
        try:
            with Hailo(hef) as hailo, Picamera2() as cam:
                model_h, model_w, _ = hailo.get_input_shape()
                cam.configure(cam.create_preview_configuration(
                    main={"size": MAIN_SIZE, "format": "XRGB8888"},
                    lores={"size": (model_w, model_h), "format": "RGB888"},
                ))
                cam.start()
                log.info("camera on, model input %dx%d, %s", model_w, model_h, hef)
                first = True
                while not stop.is_set():
                    output = hailo.run(cam.capture_array("lores"))
                    if first:
                        log.info("hailo output: %s with %d entries, person entry: %r",
                                 type(output).__name__, len(output), output[PERSON_CLASS])
                        first = False
                    put((time.monotonic(), person_boxes(output)))
        except Exception as e:
            log.exception("camera stopped")
            put(e)

    thread = threading.Thread(target=capture, daemon=True)
    thread.start()
    try:
        while True:
            item = await queue.get()
            if isinstance(item, Exception):
                raise item
            yield item
    finally:
        stop.set()
