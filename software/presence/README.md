# Presence: camera to hub (#13)

This service watches for a person with the camera and tells the hub what it sees. It sends the same messages as the simulator keys `m`, `s` and `n`:

```json
{"type":"presence","state":"moving|still|none"}
{"type":"fall_hint"}
```

`fall_hint` is the internal name of the hint that starts a check-in. The service sends it when the person goes from moving to still, at most once per 60 s. The agent then asks the person if they are okay. In anything a user sees or hears, call this "no response after an event".

The service is a normal hub client. It reads `HUB_URL` (default `ws://localhost:8765`) and connects again 1 s after the hub drops. When it sees a `reset` on the bus, it sends the current state again at once. A reset also clears the once per 60 s limit on the check-in hint, so the next change from moving to still sends it again.

## How it decides

The camera gives person boxes as fractions of the frame, so a wide or fisheye lens does not change the rules. The service tracks the largest person box with a score of 0.4 or more.

| State | When |
|---|---|
| `moving` | The box center moves more than 4% of the frame, or the box area changes more than 15%, within 1 s. This must show in 2 or more frames of the last second. |
| `still` | 3 s with no such change. |
| `none` | No person for 5 s after `moving`, or for 60 s after `still`. A check-in takes about 30 s. The longer wait keeps a person lying down from becoming `none` during a check-in. |

- At start, nothing is sent until the state is known. With nobody in view, that is `none` after 5 s.
- One or two frames with no person change nothing.
- One bad box does not make `moving`. The service does not use a frame that is far from the last second of boxes until a second such frame comes within 1 s. A false `moving` right after `still` looks like a stand-up to the agent.
- After a longer gap, the 3 s for `still` start again when the person is back. A person who walks out of view and back does not count as still.
- The service sends each change at once and repeats the current state every 5 s.
- All the numbers are guesses for the demo. They are constants at the top of `tracker.py`. Tune them on the Pi.

## Run with posture.py (the demo setup)

Rafael's `hardware/vision/posture.py` runs the pose model on the AI HAT+. It prints one frame line per camera frame on stdout, in the `--stdin` format below. This service reads those lines and sends the events to the hub. On the Pi, from the repo root:

```bash
python3 hardware/vision/posture.py --hub "" --no-window | tee /tmp/boxes.jsonl | HUB_URL=ws://localhost:8765 .venv/bin/python -m software.presence --stdin
```

- `--hub ""` keeps posture.py off the hub. Only this service sends presence, so the hub never gets two answers. posture.py reads `HUB_URL` when `--hub` is not given, so do not leave it out.
- posture.py also prints its own events as `EVENT {...}`. This service skips those lines without a log line.
- `tee /tmp/boxes.jsonl` saves the run. Copy the file to the Mac and play it with `--replay` (see below) to check the events without the camera.
- Run posture.py the way its README says (the venv and the Wayland lines). Drop `--no-window` to see the overlay.

During the demo, do not press the sim keys `m`, `s` or `n` while the camera is live. They send the same messages as this service and mix two sources.

## Run on the Pi (camera and AI HAT+)

The camera source is not tested on the Pi yet. It uses picamera2's Hailo helper, like the picamera2 `examples/hailo` detect example.

picamera2 comes from Raspberry Pi OS, not from pip, so make the venv with `--system-site-packages`. From the repo root:

```bash
python3 -m venv --system-site-packages .venv && .venv/bin/pip install -r software/presence/requirements.txt
```

```bash
HUB_URL=ws://localhost:8765 .venv/bin/python -m software.presence
```

- Only one program can use the camera. Stop `rpicam-hello` first.
- On the first frame, the service logs the shape of the Hailo output. If the boxes look wrong, that line shows why.
- The default model is `/usr/share/hailo-models/yolov8s_h8.hef`. If the file is not there, look in `/usr/share/hailo-models/` and pass the Hailo-8 YOLOv8 file with `--hef PATH`. Do not use an `_h8l` file. That one is for the Hailo-8L.
- If the hub runs on the Mac, start it with `--host 0.0.0.0` and set `HUB_URL=ws://<mac-ip>:8765` on the Pi.

## Feed it from any detector (`--stdin`)

If the picamera2 source does not work, any detector can feed the service. Print one JSON line per camera frame, also for frames with no person:

```json
{"t": 12.5, "boxes": [[0.31, 0.20, 0.52, 0.88, 0.91]]}
```

- `t`: seconds, from any clock that only goes forward. Without `t`, the service uses the time the line arrives.
- `boxes`: person boxes only, as `[x0, y0, x1, y1, score]`. Each coordinate is a fraction of the frame, from 0 to 1.

```bash
your_detector | .venv/bin/python -m software.presence --stdin
```

The service skips a bad line with a log line. A line that starts with `EVENT ` is skipped without one.

## Run on the Mac (`--replay`)

`--replay FILE` plays a file of the same JSON lines at its own pace. The sample file shows a person who walks in, lies still for 30 s, then gets up:

```bash
.venv/bin/python -m software.hub --sim --ws-port 8767 --http-port 8768
```

```bash
HUB_URL=ws://localhost:8767 .venv/bin/python -m software.presence --replay software/presence/samples/walk_still_getup.jsonl
```

## If the camera fails

Run the hub with `--sim` and use the keys: `m` for moving, `s` for still, `n` for nobody. After `m`, the key `s` also sends `fall_hint`, the same as the camera.

## Flags

- `--stdin`: read frames from stdin.
- `--replay FILE`: read frames from a file.
- No source flag: use the camera.
- `--hef PATH`: the YOLOv8 model for the camera.
- `--no-fall-hint`: never send `fall_hint`. Presence messages still go out.
- `--fall-hint-cooldown S`: at most one `fall_hint` per S seconds. Default 60.

## Tests

```bash
.venv/bin/python -m pytest software/presence
```

The tests cover the tracker rules with made-up box sequences, the input format, and a replay sent through a real hub on a free port.
