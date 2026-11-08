# Camera posture node (Pi 5 + AI HAT+ + Camera Module 3)

`posture.py` runs YOLOv8s-pose on the AI HAT+ (Hailo-8), labels the largest person **STANDING / SITTING / LYING**, tracks motion, draws a live overlay on the monitor, and sends hub events (contract #19).

## Status (Sat Nov 7, ~10 PM)
- ✅ Runs on the Pi at **~30 fps** with the overlay window.
- ⏳ **Posture labels:** not yet validated on a fixed mount (the stock Hailo pose demo detected standing, bending and lying people, including partly hidden behind a table).
- ⏳ **Hub link:** untested (needs the hub reachable from the Pi).
- ⚠️ **Known issue:** the window isn't full screen on Wayland (labwc ignores the full-screen request).

## Setup on the Pi (done on `rafhost`)
1. The Hailo stack is `hailo-all`: HailoRT 4.23, plus `/usr/share/hailo-models/yolov8s_pose_h8.hef`.
2. ⚠️ **On kernel 6.18.60 the built-in `hailo_pci` driver is gone.** Rebuild it once:
   ```bash
   sudo apt install dkms && sudo apt install --reinstall hailort-pcie-driver && sudo dkms autoinstall && sudo reboot
   ```
3. Create the Python environment. Picamera2, OpenCV and the Hailo bindings come from the system:
   ```bash
   python3 -m venv --system-site-packages ~/land/.venv && ~/land/.venv/bin/pip install websockets
   ```

## Run
```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u) WAYLAND_DISPLAY=wayland-0 QT_QPA_PLATFORM=wayland  # only when started over SSH
~/land/.venv/bin/python hardware/vision/posture.py --hub ws://HUB_HOST:8765   # --mount wall|ceiling, --no-window
```
- Press `q` to quit.
- Every event is also printed as `EVENT {...}`.
- If the hub is unreachable, the program logs it and retries every 3 s.

## Events sent (contract #19)
- `{"type":"presence","state":"moving|still|none","source":"camera"}`, sent on change.
  - `none`: no person for 1.5 s.
  - `moving` vs `still`: the person's box centre moved more than 8 % of body height over the last ~0.5 s.
- `{"type":"fall_hint","source":"camera"}`: the person became **LYING + still** within 5 s of being upright. A hint, not a diagnosis: say "no response after an event".

## How posture is decided
- **Torso angle** (shoulder midpoint to hip midpoint, measured from vertical): over 60°, or a box wider than 1.4× its height, means **LYING**. Under 35° means **STANDING**, or **SITTING** when the thigh (hip to knee) is over 50° from vertical. Anything else is UNCLEAR.
- The label is smoothed by majority vote over the last 8 frames.

## Mount
- **Wall / corner (default):** about 2 m high, tilted down 20–30°. The pose model was trained on front and side views, so this is the supported mount.
- **Ceiling (`--mount ceiling`):** experimental. From above, keypoints are unreliable, so it falls back to body elongation only.

## How the model output is decoded
The HEF returns 9 raw heads, one set per stride 8/16/32:
- **Box:** 64 channels = 4 sides × 16 DFL bins. Softmax over the bins, then the expected value, times the stride.
- **Score:** 1 channel, sigmoid applied if needed.
- **Keypoints:** 51 channels = 17 × (x, y, visibility). `x = (raw·2 + grid_x)·stride`, and visibility gets a sigmoid.

Then NMS at IoU 0.5. The input is the 640×640 `lores` stream; boxes and keypoints are scaled back to the 1280×720 `main` stream.
