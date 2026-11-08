"""Camera posture node: Pi 5 + AI HAT+ (Hailo-8) + Camera Module 3.

Runs YOLOv8s-pose on the Hailo, labels each person STANDING / SITTING / LYING,
tracks motion, shows a full-screen overlay, and sends hub events
(contract #19): presence moving|still|none and fall_hint.

Run on the Pi:  python3 hardware/vision/posture.py [--hub ws://HOST:8765] [--mount wall]
"""
import argparse
import asyncio
import json
import math
import os
import queue
import sys
import threading
import time
from collections import Counter, deque

import cv2
import numpy as np
from picamera2 import Picamera2
from picamera2.devices import Hailo

HEF = "/usr/share/hailo-models/yolov8s_pose_h8.hef"
STRIDES = (8, 16, 32)
SCORE_MIN = 0.5
KP_MIN = 0.4
# COCO keypoint indices
NOSE, L_SH, R_SH, L_HIP, R_HIP, L_KNEE, R_KNEE, L_ANK, R_ANK = 0, 5, 6, 11, 12, 13, 14, 15, 16
SKELETON = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]
COLORS = {"STANDING": (0, 200, 0), "SITTING": (0, 200, 255), "LYING": (0, 0, 255), "UNCLEAR": (200, 200, 200)}


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def decode(outputs):
    """Decode raw YOLOv8-pose heads into (boxes[N,4], scores[N], kpts[N,17,3]) in 640x640 pixels."""
    by_hw = {}
    for arr in outputs.values():
        a = np.asarray(arr, dtype=np.float32)
        by_hw.setdefault(a.shape[0], {})[a.shape[-1]] = a
    boxes, scores, kpts = [], [], []
    for stride in STRIDES:
        h = 640 // stride
        heads = by_hw[h]
        box, cls, kp = heads[64], heads[1], heads[51]
        s = cls.reshape(-1)
        if s.max() > 1.0 or s.min() < 0.0:  # raw logits -> probabilities
            s = sigmoid(s)
        keep = np.where(s > SCORE_MIN)[0]
        if keep.size == 0:
            continue
        gy, gx = np.divmod(keep, h)
        dfl = box.reshape(-1, 4, 16)[keep]
        dfl = np.exp(dfl - dfl.max(-1, keepdims=True))
        dist = (dfl / dfl.sum(-1, keepdims=True) * np.arange(16)).sum(-1)  # l,t,r,b in grid units
        cx, cy = gx + 0.5, gy + 0.5
        b = np.stack([cx - dist[:, 0], cy - dist[:, 1], cx + dist[:, 2], cy + dist[:, 3]], -1) * stride
        k = kp.reshape(-1, 17, 3)[keep].copy()
        k[..., 0] = (k[..., 0] * 2.0 + gx[:, None]) * stride
        k[..., 1] = (k[..., 1] * 2.0 + gy[:, None]) * stride
        k[..., 2] = sigmoid(k[..., 2])
        boxes.append(b), scores.append(s[keep]), kpts.append(k)
    if not boxes:
        return np.zeros((0, 4)), np.zeros(0), np.zeros((0, 17, 3))
    boxes, scores, kpts = np.concatenate(boxes), np.concatenate(scores), np.concatenate(kpts)
    idx = cv2.dnn.NMSBoxes([[*b[:2], *(b[2:] - b[:2])] for b in boxes.tolist()], scores.tolist(), SCORE_MIN, 0.5)
    idx = np.array(idx).reshape(-1)
    return boxes[idx], scores[idx], kpts[idx]


def mid(k, a, b):
    pts = [k[i, :2] for i in (a, b) if k[i, 2] > KP_MIN]
    return np.mean(pts, axis=0) if pts else None


def angle_from_vertical(top, bottom):
    dx, dy = bottom[0] - top[0], bottom[1] - top[1]
    return math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))


def classify(box, k, mount):
    """Posture from torso angle, thigh angle and box shape. Returns (label, torso_deg or None)."""
    w, h = box[2] - box[0], box[3] - box[1]
    aspect = w / max(h, 1.0)
    if mount == "ceiling":  # top-down view: keypoints unreliable, use body elongation only (experimental)
        return ("LYING" if max(aspect, 1 / max(aspect, 1e-6)) > 2.2 else "UNCLEAR"), None
    sh, hip, knee = mid(k, L_SH, R_SH), mid(k, L_HIP, R_HIP), mid(k, L_KNEE, R_KNEE)
    if sh is None or hip is None:
        return ("LYING" if aspect > 1.3 else "UNCLEAR"), None
    torso = angle_from_vertical(sh, hip)
    if torso > 60 or aspect > 1.4:
        return "LYING", torso
    if torso < 35:
        if knee is not None and angle_from_vertical(hip, knee) > 50:
            return "SITTING", torso
        return "STANDING", torso
    return "UNCLEAR", torso


class Hub:
    """Sends JSON events to the hub WebSocket from a background thread; reconnects and logs failures."""

    def __init__(self, url):
        self.url, self.q, self.connected = url, queue.Queue(), False
        if url:
            threading.Thread(target=lambda: asyncio.run(self._run()), daemon=True).start()

    def send(self, msg):
        print("EVENT", json.dumps(msg), flush=True)
        if self.url:
            self.q.put(msg)

    async def _run(self):
        import websockets
        while True:
            try:
                async with websockets.connect(self.url) as ws:
                    self.connected = True
                    print(f"hub connected: {self.url}", flush=True)
                    while True:
                        msg = await asyncio.get_running_loop().run_in_executor(None, self.q.get)
                        await ws.send(json.dumps({**msg, "source": "camera"}))
            except Exception as e:  # report and retry; never silent
                self.connected = False
                print(f"hub error ({self.url}): {e!r}; retrying in 3 s", file=sys.stderr, flush=True)
                await asyncio.sleep(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default=os.environ.get("HUB_URL", ""), help="ws://HOST:8765 (empty = no hub)")
    ap.add_argument("--mount", choices=["wall", "ceiling"], default="wall")
    ap.add_argument("--no-window", action="store_true")
    args = ap.parse_args()

    hub = Hub(args.hub)
    with Hailo(HEF) as hailo:
        mh, mw, _ = hailo.get_input_shape()
        cam = Picamera2()
        main_wh = (1280, 720)
        cam.configure(cam.create_preview_configuration(
            main={"size": main_wh, "format": "XRGB8888"}, lores={"size": (mw, mh), "format": "RGB888"},
            controls={"FrameRate": 30}))
        cam.start()
        sx, sy = main_wh[0] / mw, main_wh[1] / mh
        if not args.no_window:
            cv2.namedWindow("LAND camera", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("LAND camera", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        votes = deque(maxlen=8)          # posture smoothing
        track = deque(maxlen=15)         # (t, center, box_h) for motion
        last_seen, presence, posture = 0.0, "none", None
        upright_until = 0.0              # last time the person was upright
        fps_t, fps_n, fps = time.time(), 0, 0.0

        while True:
            req = cam.capture_request()  # main + lores from the same frame
            frame, lores = req.make_array("main"), req.make_array("lores")
            req.release()
            boxes, scores, kpts = decode(hailo.run(lores))
            now = time.time()
            img = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            if len(boxes):
                i = int(np.argmax((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])))  # largest person
                for j, (b, k) in enumerate(zip(boxes, kpts)):
                    label, torso = classify(b, k, args.mount)
                    if j == i:
                        votes.append(label)
                    bb = (b * [sx, sy, sx, sy]).astype(int)
                    kk = k.copy(); kk[:, 0] *= sx; kk[:, 1] *= sy
                    color = COLORS[Counter(votes).most_common(1)[0][0] if j == i else label]
                    cv2.rectangle(img, tuple(bb[:2]), tuple(bb[2:]), color, 3)
                    for a, c in SKELETON:
                        if kk[a, 2] > KP_MIN and kk[c, 2] > KP_MIN:
                            cv2.line(img, tuple(kk[a, :2].astype(int)), tuple(kk[c, :2].astype(int)), (255, 0, 255), 3)
                b = boxes[i]
                track.append((now, ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2), b[3] - b[1]))
                last_seen = now
            posture = Counter(votes).most_common(1)[0][0] if votes and now - last_seen < 1.5 else None

            # motion: centre travel over the window, normalised by body height
            moving = False
            if len(track) >= 2 and now - last_seen < 1.5:
                (t0, c0, h0), (t1, c1, h1) = track[0], track[-1]
                travel = math.dist(c0, c1) / max(h1, 1.0)
                moving = travel > 0.08 or posture == "UNCLEAR"
            new_presence = "none" if now - last_seen > 1.5 else ("moving" if moving else "still")

            if posture in ("STANDING", "SITTING"):
                upright_until = now
            if new_presence != presence:
                hub.send({"type": "presence", "state": new_presence})
                # fall hint: lying and still within 5 s of being upright (contract: a hint, not a diagnosis)
                if new_presence == "still" and posture == "LYING" and now - upright_until < 5:
                    hub.send({"type": "fall_hint"})
                presence = new_presence

            fps_n += 1
            if now - fps_t >= 1:
                fps, fps_t, fps_n = fps_n / (now - fps_t), now, 0
            banner = f"{posture or 'NO PERSON'}  |  {presence.upper()}"
            cv2.rectangle(img, (0, 0), (main_wh[0], 60), (0, 0, 0), -1)
            cv2.putText(img, banner, (20, 43), cv2.FONT_HERSHEY_SIMPLEX, 1.4,
                        COLORS.get(posture, (255, 255, 255)), 3)
            hub_txt = "hub: off" if not args.hub else ("hub: connected" if hub.connected else "hub: retrying")
            cv2.putText(img, f"{fps:4.1f} fps  {args.mount}  {hub_txt}", (main_wh[0] - 470, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            if not args.no_window:
                cv2.imshow("LAND camera", img)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            elif fps_n == 0:  # headless: refresh a snapshot once a second
                cv2.imwrite("/tmp/posture_latest.jpg", img)
        cam.stop()


if __name__ == "__main__":
    main()
