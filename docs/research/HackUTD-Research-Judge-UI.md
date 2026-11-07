---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, ui]
---
Part of [HackUTD-2026](../HackUTD-2026.md). Plumbing context: [HackUTD-Research-Embedded](HackUTD-Research-Embedded.md) (mosquitto on the Pi 5, wired switch, static IPs).

## Bottom line
- **One static web page, two views** (`?view=kiosk` on the Pi monitor, `?view=wall` on the laptop), served by the Python pipeline's own small HTTP server.
- **Video:** MJPEG over HTTP, with boxes and the patch heatmap **drawn into the frame on the server** before JPEG encode. Pi 5 has no hardware H.264 path, so WebRTC would mean software H.264 on CPUs the AI pipeline needs.
- **Metrics + slider:** MQTT over WebSockets (mosquitto is already planned) with mqtt.js in the page. The slider publishes `control/threshold`.
- **UI stack:** vanilla JS + hand-written CSS variables + uPlot, **all files vendored locally**. No build step, no CDN at runtime.

## Stack decision table
| Concern | Pick | Runner-up | Why |
|---|---|---|---|
| Kiosk | labwc autostart + Chromium `--kiosk` | Pygame fullscreen app | The official Pi tutorial uses this path, and it's the same page the laptop shows |
| Video | MJPEG `multipart/x-mixed-replace` | go2rtc / MediaMTX WebRTC | Pi 5 "uses software video encoders" with "longer latency". MJPEG needs no codec negotiation and works in a plain `<img>` |
| Overlay | Server-side burn-in (cv2 on the frame before encode) | Client canvas from metadata | Always in sync and only one code path. Do client canvas later if there's time |
| Metrics | MQTT/WS + mqtt.js | FastAPI WebSocket | Broker already exists, many boards can publish, the laptop subscribes for free |
| Charts | uPlot (~48 KB) | ECharts (~1 MB) | Author benchmark: 3,600 points streaming at 60 fps for 10% CPU vs Chart.js 40% and ECharts 70% (Ryzen laptop, not a Pi) |
| Framework | Vanilla JS, one `index.html` + `app.js` + `style.css` | Svelte + Vite | Easy for Claude to edit, nothing to build on the Pi. Use Svelte only if Godfrey already knows it |

## (1) Kiosk config (Bookworm/Trixie, labwc)
`~/.config/labwc/autostart` (the official tutorial's flags, plus a pause so the server can start):
```
sleep 5 && chromium http://localhost:8000/?view=kiosk --kiosk --noerrdialogs --disable-infobars --no-first-run --enable-features=OverlayScrollbar --start-maximized &
```
- Binary name: the tutorial uses `chromium`. Older Bookworm images used `chromium-browser` [u]. Check with `which chromium chromium-browser`.
- **Screen blanking:** `sudo raspi-config` → `2 Display Options > D2 Screen Blanking` → No. GUI path: Control Centre → Display → Screen Blanking off.
- **Rotation:** Control Centre → Screens → right-click the output → Orientation. To script it: `wlr-randr --output HDMI-A-1 --transform 90` [u, not in the Pi docs] in autostart.
- **Touch on HDMI monitors:** in `~/.config/labwc/rc.xml`, map the touch panel to the output, or touches land on the wrong place when rotated:
```xml
<touch deviceName="<from libinput list-devices>" mapToOutput="HDMI-A-1" mouseEmulation="no"/>
```
(The labwc sample shows these as child elements. Use whichever form your labwc version parses [u].) A DSI Touch Display 2 instead takes `dtoverlay=...,swapxy,invx,invy` in config.txt, but the docs say that's only needed outside the desktop.
- **Hide cursor:** the Pi docs say "There is no global setting". Two layers: (a) CSS `* { cursor: none }` on the kiosk view, (b) labwc's `HideCursor` action (cursor comes back on pointer motion). `WarpCursor` can move it off-screen.
- **Exit kiosk:** keep an SSH session open. `pkill chromium` relaunches nothing, so re-run the autostart line manually.

## (2) Video transport
- **Recommended:** the pipeline already holds each frame. Draw boxes and heatmap with cv2, `cv2.imencode('.jpg', q=70)` at **640×360 or 640×480**, and serve multipart MJPEG from FastAPI/Flask `/stream`. If Picamera2 serves directly, its official `mjpeg_server.py` example uses the software JPEG encoder.
- **Expected:** about 100–200 ms glass-to-glass on a wired LAN at 15–30 fps, with a JPEG encode cost of a few ms per frame at 640p [u, measure it]. Cap the stream at 15 fps if CPU is tight. Judges can't tell 15 from 30 on an overlay.
- **Bandwidth:** about 30–60 KB per frame, so 0.5–2 MB/s per viewer [u]. Fine for two viewers on gigabit.
- **WebRTC (go2rtc/MediaMTX):** go2rtc rates WebRTC "best" latency, but on Pi 5 it needs software H.264 encode, the overlay would have to be client-side, and setup risks ICE/codec debugging. Skip it.
- **Heatmap:** alpha-blend a precomputed patch grid (green = computed, dark/grey = skipped). It's cheap with numpy at grid resolution, then `cv2.resize` with nearest interpolation.

## (3) Live metrics
`/etc/mosquitto/conf.d/ws.conf`:
```
listener 1883
listener 9001
protocol websockets
allow_anonymous true
```
- `allow_anonymous` defaults to false once any listener is defined, so this line is required. Use an isolated LAN only.
- Browser: `mqtt.connect('ws://10.0.0.10:9001')`. Browsers support only ws/wss. Vendor `mqtt.min.js` (unpkg `mqtt/dist/mqtt.min.js`) and serve it locally.
- Topics: one retained JSON blob `ui/state` at about 5 Hz (fps, W, J/h, funnel counts, accuracy, baseline, threshold) is simpler than ten topics. Slider → `control/threshold` (retained), and the pipeline subscribes.
- **FastAPI WebSocket alternative:** one fewer moving part if mosquitto misbehaves. Same JSON, so the page swap is about 10 lines.

## (4) Polished look, fast
- Dark background `#0b0f14`, one accent (cyan or lime) for "computed/saved", amber for "escalated", red only for cloud.
- Big numbers in a tabular-figures font (`font-variant-numeric: tabular-nums`) so digits don't jitter. Bundle Inter or JetBrains Mono locally.
- Funnel = 5 horizontal bars with counts and percent survived. It's CSS widths, no chart lib needed.
- uPlot only for two sparklines: fps and watts over the last 60 s.
- Budget for 2 people + Claude, about 6 h: skeleton + MQTT (1 h), MJPEG + overlay (1.5 h), funnel/tiles (1 h), slider round-trip (0.5 h), kiosk boot (0.5 h), polish (1.5 h).

## (5) Layouts
**Kiosk, 7–10" landscape (1024×600 to 1280×800):**
| Region | Content |
|---|---|
| Top band, full width, ~12% height | One-line problem statement, 28–36 px bold, max about 8 words |
| Left ~62% | Live video with overlay, legend chips below it (computed / skipped / escalated) |
| Right ~38%, stacked | Big tile **J/hour vs baseline (−xx %)** · fps · accuracy vs baseline · funnel bars |
| Bottom band | Threshold slider, full width, thumb ≥ 48 px, value shown large |

**Laptop wall view (1080p):** video at 2× size top-left. The funnel gets its own wide panel with live counts. Sparklines for fps and W, an A/B toggle "baseline (everything to the detector) vs ours", and a log of the last 10 VLM/cloud escalations with thumbnails.

**Aisle readability:**
- About 1 in. of letter height per 10 ft is a common signage rule of thumb [u]. On a 7" screen, only the headline and one hero number will read from the aisle, so pick **one hero metric** (energy saved %).
- No text under 18 px on the kiosk, high contrast, no thin weights.
- Motion draws the eye: let funnel counts tick live.

## (6) No-touch fallback
- The slider works with a mouse, but that needs a mouse on the table. Better: **2 physical buttons** (± threshold) on the ESP32/Arduino or Pi GPIO, publishing to `control/threshold`. They're tactile and judges like them.
- Also add keyboard shortcuts (`←/→` threshold, `H` heatmap, `B` baseline mode) for a USB keypad.
- If even that fails, put the slider on the laptop view. Both views share the retained topic, so the Pi screen follows.

## Risks
- **No internet at the venue:** any CDN font/script breaks the page. Vendor everything and test with the Ethernet unplugged.
- **CPU contention:** Chromium on the same Pi 5 competes with the pipeline. Measure fps with the kiosk open vs closed. If it costs too much, show the kiosk from the laptop's second output or the AM62 instead.
- **Touch mis-mapped after rotation:** fix with `mapToOutput` and test at the venue.
- **Monitor unknown** (HDMI vs USB-C, touch?): bring a mouse and the button fallback.
- **MJPEG stall on reconnect:** add an `onerror` handler that reloads `<img>` with a cache-busting query string.
- **Honesty:** baseline numbers must come from a real run. Label any estimated value "est."

## Sources
- Raspberry Pi docs, configuration (screen blanking, labwc autostart, rotation, cursor): https://www.raspberrypi.com/documentation/computers/configuration.html
- Raspberry Pi kiosk tutorial: https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/
- Raspberry Pi Touch Display 2 docs: https://www.raspberrypi.com/documentation/accessories/touch-display-2.html
- Raspberry Pi camera software (Pi 5 software encoders): https://www.raspberrypi.com/documentation/computers/camera_software.html
- labwc rc.xml.all (touch mapping): https://github.com/labwc/labwc/blob/master/docs/rc.xml.all
- labwc actions (HideCursor): https://labwc.github.io/labwc-actions.5.html
- mosquitto.conf(5): https://mosquitto.org/man/mosquitto-conf-5.html
- MQTT.js README: https://github.com/mqttjs/MQTT.js
- uPlot README: https://github.com/leeoniya/uPlot
- go2rtc README: https://github.com/AlexxIT/go2rtc
- MediaMTX README: https://github.com/bluenviron/mediamtx
- picamera2 mjpeg_server.py (via search snippet; the file itself didn't load): https://raw.githubusercontent.com/raspberrypi/picamera2/main/examples/mjpeg_server.py
