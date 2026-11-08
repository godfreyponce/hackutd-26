"""Camera node: Pi 5 + AI HAT+ (Hailo-8) + Camera Module 3 (NoIR).

YOLOv8s-pose on the Hailo, for every person in view:
  posture STANDING / SITTING / LYING, people count, how many are down,
  person-down timer, HELP gesture (both arms raised), privacy face blur.
Whole-scene: camera shake (earthquake cross-check) and lights out/on.
Full-screen overlay + hub events (contract #19; new types proposed on #19).

Run on the Pi:  python3 hardware/vision/posture.py [--hub ws://HOST:8765] [--mount wall|ceiling]
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
HOLD_S = 0.8             # a presence state must hold this long before it is sent
FALL_COOLDOWN_S = 20     # at most one fall_hint per 20 s
HELP_HOLD_S = 1.0        # arms up this long = HELP
HELP_COOLDOWN_S = 15
SHAKE_PX = 6.0           # whole-frame shift (px at 320x180) that counts as a shake
SHAKE_FRAMES = 4         # ... for this many frames in the last 10
DARK_LEVEL = 35          # mean brightness (0-255) below this = dark
# COCO keypoints
NOSE, L_EYE, R_EYE, L_EAR, R_EAR, L_SH, R_SH = 0, 1, 2, 3, 4, 5, 6
L_WR, R_WR, L_HIP, R_HIP, L_KNEE, R_KNEE = 9, 10, 11, 12, 13, 14
SKELETON = [(5, 6), (5, 7), (7, 9), (6, 8), (8, 10), (5, 11), (6, 12), (11, 12),
            (11, 13), (13, 15), (12, 14), (14, 16), (0, 5), (0, 6)]
COLORS = {"STANDING": (0, 200, 0), "SITTING": (0, 200, 255), "LYING": (0, 0, 255),
          "UNCLEAR": (200, 200, 200), "HELP": (0, 0, 255)}


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def decode(outputs):
    """Raw YOLOv8-pose heads -> (boxes[N,4], scores[N], kpts[N,17,3]) in 640x640 pixels."""
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
    xywh = np.concatenate([boxes[:, :2], boxes[:, 2:] - boxes[:, :2]], axis=1)
    idx = np.array(cv2.dnn.NMSBoxes(xywh.tolist(), scores.tolist(), SCORE_MIN, 0.5)).reshape(-1)
    return boxes[idx], scores[idx], kpts[idx]


def mid(k, a, b):
    pts = [k[i, :2] for i in (a, b) if k[i, 2] > KP_MIN]
    return np.mean(pts, axis=0) if pts else None


def angle_from_vertical(top, bottom):
    dx, dy = bottom[0] - top[0], bottom[1] - top[1]
    return math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))


def classify(box, k, mount):
    """Posture from torso angle, thigh angle and box shape."""
    w, h = box[2] - box[0], box[3] - box[1]
    aspect = w / max(h, 1.0)
    if mount == "ceiling":  # top-down: keypoints unreliable, body elongation only (experimental)
        return "LYING" if max(aspect, 1 / max(aspect, 1e-6)) > 2.2 else "UNCLEAR"
    sh, hip, knee = mid(k, L_SH, R_SH), mid(k, L_HIP, R_HIP), mid(k, L_KNEE, R_KNEE)
    if sh is None or hip is None:
        return "LYING" if aspect > 1.3 else "UNCLEAR"
    torso = angle_from_vertical(sh, hip)
    if torso > 60 or aspect > 1.4:
        return "LYING"
    if torso < 35:
        return "SITTING" if knee is not None and angle_from_vertical(hip, knee) > 50 else "STANDING"
    return "UNCLEAR"


def arms_up(k):
    """Both wrists clearly above the head (nose, or shoulders if no nose)."""
    ref = k[NOSE, 1] if k[NOSE, 2] > KP_MIN else min(k[L_SH, 1], k[R_SH, 1])
    return all(k[w, 2] > KP_MIN and k[w, 1] < ref for w in (L_WR, R_WR))


def blur_faces(img, kpts):
    """Privacy: blur a square around each visible head (eyes/ears/nose)."""
    H, W = img.shape[:2]
    for k in kpts:
        head = k[[NOSE, L_EYE, R_EYE, L_EAR, R_EAR]]
        head = head[head[:, 2] > KP_MIN][:, :2]
        if not len(head):
            continue
        sh = [k[i, :2] for i in (L_SH, R_SH) if k[i, 2] > KP_MIN]
        size = max(np.ptp(head[:, 0]) * 2.2, (math.dist(*sh) * 0.9 if len(sh) == 2 else 40), 30)
        cx, cy = head.mean(0)
        x0, y0 = int(max(cx - size / 2, 0)), int(max(cy - size / 2, 0))
        x1, y1 = int(min(cx + size / 2, W)), int(min(cy + size / 2, H))
        if x1 > x0 and y1 > y0:
            img[y0:y1, x0:x1] = cv2.GaussianBlur(img[y0:y1, x0:x1], (0, 0), 15)


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
                    print(f"hub connected: {self.url}", file=sys.stderr, flush=True)
                    while True:
                        msg = await asyncio.get_running_loop().run_in_executor(None, self.q.get)
                        await ws.send(json.dumps({**msg, "source": "camera"}))
            except Exception as e:  # report and retry; never silent
                self.connected = False
                print(f"hub error ({self.url}): {e!r}; retrying in 3 s", file=sys.stderr, flush=True)
                await asyncio.sleep(3)


class Mjpeg:
    """Latest overlay frame as an MJPEG stream (privacy blur already applied). Any browser on the network can watch."""

    def __init__(self, port):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        self.cond, self.jpg = threading.Condition(), None
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                if self.path.split("?")[0] != "/stream.mjpg":
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                try:
                    while True:
                        with owner.cond:
                            owner.cond.wait(timeout=2)
                            jpg = owner.jpg
                        if jpg:
                            self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n" % len(jpg)
                                             + jpg + b"\r\n")
                except (BrokenPipeError, ConnectionResetError):
                    pass  # viewer closed the page

        srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        print(f"MJPEG stream on :{port}/stream.mjpg", file=sys.stderr, flush=True)

    def publish(self, img):
        ok, buf = cv2.imencode(".jpg", cv2.resize(img, (960, 540)), [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ok:
            with self.cond:
                self.jpg = buf.tobytes()
                self.cond.notify_all()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default=os.environ.get("HUB_URL", ""), help="ws://HOST:8765 (empty = no hub)")
    ap.add_argument("--mount", choices=["wall", "ceiling"], default="wall")
    ap.add_argument("--no-blur", action="store_true", help="show faces (privacy blur is on by default)")
    ap.add_argument("--no-window", action="store_true")
    ap.add_argument("--boxes", action="store_true",
                    help="print one JSON box line per frame on stdout for software.presence --stdin")
    ap.add_argument("--stream-port", type=int, default=0,
                    help="serve the overlay as MJPEG on http://<pi>:PORT/stream.mjpg (0 = off)")
    ap.add_argument("--no-presence", action="store_true",
                    help="do not send presence/fall_hint (software.presence owns them); camera-only events still go out")
    args = ap.parse_args()

    hub = Hub(args.hub)
    stream = Mjpeg(args.stream_port) if args.stream_port else None
    with Hailo(HEF) as hailo:
        mh, mw, _ = hailo.get_input_shape()
        cam = Picamera2()
        W, H = 1280, 720
        cam.configure(cam.create_preview_configuration(
            main={"size": (W, H), "format": "XRGB8888"}, lores={"size": (mw, mh), "format": "RGB888"},
            controls={"FrameRate": 30}))
        cam.start()
        sx, sy = W / mw, H / mh
        if not args.no_window:
            cv2.namedWindow("LAND camera", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("LAND camera", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        votes = deque(maxlen=8)                 # main-person posture smoothing
        counts = deque(maxlen=10)               # (people, down) smoothing
        track = deque(maxlen=30)                # (center, box_h) of the main person, ~1 s
        shifts = deque(maxlen=10)               # whole-frame shift per frame
        last_seen, presence, posture = 0.0, "none", None
        candidate, candidate_since = "none", 0.0
        upright_until = last_fall = last_help = last_shake = 0.0
        down_since = None                       # someone lying + still since
        help_since = None
        prev_gray, dark, people_sent = None, False, None
        fps_t, fps_n, fps = time.time(), 0, 0.0

        while True:
            req = cam.capture_request()  # main + lores from the same frame
            frame, lores = req.make_array("main"), req.make_array("lores")
            req.release()
            boxes, scores, kpts = decode(hailo.run(lores))
            now = time.time()
            if args.boxes:  # input format of software.presence --stdin: [x0, y0, x1, y1, score] as frame fractions
                print(json.dumps({"t": now, "boxes": [[*(b / [mw, mh, mw, mh]).round(4).tolist(), round(float(s), 3)]
                                                      for b, s in zip(boxes, scores)]}), flush=True)
            img = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            kpts_px = kpts.copy()
            kpts_px[..., 0] *= sx
            kpts_px[..., 1] *= sy
            boxes_px = boxes * [sx, sy, sx, sy]

            # --- scene: camera shake (earthquake cross-check) and lights ---
            gray = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (320, 180)).astype(np.float32)
            brightness = float(gray.mean())
            textured = brightness >= DARK_LEVEL and float(gray.std()) > 12  # black/flat frames give random shifts
            if prev_gray is not None and textured:
                (dx, dy), response = cv2.phaseCorrelate(prev_gray, gray)
                shifts.append(math.hypot(dx, dy) if response > 0.2 else 0.0)  # ignore low-confidence matches
            elif not textured:
                shifts.clear()
            prev_gray = gray
            shaking = sum(s > SHAKE_PX for s in shifts) >= SHAKE_FRAMES
            if shaking and now - last_shake > 10:
                hub.send({"type": "camera_shake", "frames": int(sum(s > SHAKE_PX for s in shifts))})
                last_shake = now
            if (brightness < DARK_LEVEL) != dark:
                dark = brightness < DARK_LEVEL
                hub.send({"type": "lights", "state": "off" if dark else "on", "level": round(brightness)})

            # --- people ---
            labels = [classify(b, k, args.mount) for b, k in zip(boxes, kpts)]
            n_down = labels.count("LYING")
            counts.append((len(boxes), n_down))
            people = int(np.median([c[0] for c in counts]))
            down = int(np.median([c[1] for c in counts]))
            if (people, down) != people_sent:
                hub.send({"type": "people", "count": people, "down": down})
                people_sent = (people, down)

            help_now = any(arms_up(k) for k in kpts)
            if help_now:
                help_since = help_since or now
            else:
                help_since = None
            helping = help_since is not None and now - help_since >= HELP_HOLD_S
            if helping and now - last_help > HELP_COOLDOWN_S:
                hub.send({"type": "help_gesture"})
                last_help = now

            if not args.no_blur:
                blur_faces(img, kpts_px)
            if len(boxes):
                i = int(np.argmax((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])))  # main person
                votes.append(labels[i])
                for j, (bb, kk, lab) in enumerate(zip(boxes_px.astype(int), kpts_px, labels)):
                    lab = "HELP" if arms_up(kpts[j]) and helping else lab
                    color = COLORS[lab]
                    cv2.rectangle(img, tuple(bb[:2]), tuple(bb[2:]), color, 3)
                    cv2.putText(img, lab, (bb[0], max(bb[1] - 8, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    for a, c in SKELETON:
                        if kk[a, 2] > KP_MIN and kk[c, 2] > KP_MIN:
                            cv2.line(img, tuple(kk[a, :2].astype(int)), tuple(kk[c, :2].astype(int)), (255, 0, 255), 3)
                b = boxes[i]
                track.append((((b[0] + b[2]) / 2, (b[1] + b[3]) / 2), b[3] - b[1]))
                last_seen = now
            posture = Counter(votes).most_common(1)[0][0] if votes and now - last_seen < 1.5 else None

            # --- motion + presence (hysteresis) ---
            moving = False
            if len(track) >= 2 and now - last_seen < 1.5:
                (c0, _), (c1, h1) = track[0], track[-1]
                moving = math.dist(c0, c1) / max(h1, 1.0) > 0.06
            observed = "none" if now - last_seen > 1.5 else ("moving" if moving else "still")
            if observed != candidate:
                candidate, candidate_since = observed, now
            if posture in ("STANDING", "SITTING"):
                upright_until = now
            if candidate != presence and now - candidate_since >= HOLD_S:
                presence = candidate
                if not args.no_presence:
                    hub.send({"type": "presence", "state": presence})
                if (not args.no_presence and presence == "still" and posture == "LYING" and now - upright_until < 6
                        and now - last_fall > FALL_COOLDOWN_S):
                    hub.send({"type": "fall_hint"})
                    last_fall = now

            # --- person-down timer ---
            if posture == "LYING" and presence == "still":
                down_since = down_since or now
            else:
                down_since = None
            down_s = int(now - down_since) if down_since else 0

            # --- overlay ---
            fps_n += 1
            if now - fps_t >= 1:
                fps, fps_t, fps_n = fps_n / (now - fps_t), now, 0
            cv2.rectangle(img, (0, 0), (W, 60), (0, 0, 0), -1)
            main_label = "HELP!" if helping else (posture or "NO PERSON")
            cv2.putText(img, f"{main_label}  |  {presence.upper()}", (20, 43), cv2.FONT_HERSHEY_SIMPLEX, 1.3,
                        COLORS.get(posture if not helping else "HELP", (255, 255, 255)), 3)
            cv2.putText(img, f"people {people}  down {down}", (640, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                        (0, 0, 255) if down else (255, 255, 255), 2)
            hub_txt = "hub: off" if not args.hub else ("hub: on" if hub.connected else "hub: retry")
            cv2.putText(img, f"{fps:4.1f}fps {hub_txt}", (1000, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            alerts = []
            if down_s:
                alerts.append(f"DOWN {down_s // 60}:{down_s % 60:02d}")
            if shaking:
                alerts.append("SHAKING")
            if dark:
                alerts.append("LIGHTS OUT")
            if alerts:
                cv2.rectangle(img, (0, H - 60), (W, H), (0, 0, 160), -1)
                cv2.putText(img, "   ".join(alerts), (20, H - 18), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 3)

            if stream and fps_n % 3 == 0:  # ~10 fps to the browser
                stream.publish(img)
            if not args.no_window:
                cv2.imshow("LAND camera", cv2.resize(img, (1920, 1080)))  # fill the monitor
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            elif fps_n == 0:  # headless: refresh a snapshot once a second
                cv2.imwrite("/tmp/posture_latest.jpg", img)
        cam.stop()


if __name__ == "__main__":
    main()
