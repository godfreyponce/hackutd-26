---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, embedded, hardware, steppers]
---

# Research: Embedded Cheat-Sheet (pan/tilt + multi-board)

Part of [HackUTD-2026](../HackUTD-2026.md). Agent research, 2026-11-07. [u] = unverified.

**Bottom line:**
- **Perception:** Pi 5 + Hailo.
- **Motion:** a **cheap MCU (Arduino/RP2040/ESP32) running AccelStepper** on TMC2209 (stealthChop) at 12 V.
- **Comms:** UDP for commands, MQTT for metrics, wired switch with static IPs.
- **Power:** INA219 per rail.
- **AM62 / i.MX 95:** networked nodes, not motor controllers.

## 1. Pi 5 GPIO (RP1 chip)
- **RPi.GPIO doesn't work.** Use **gpiozero** (lgpio backend) or lgpio. `rpi-lgpio` is a drop-in [u]. pigpio isn't supported [u].
- lgpio pulses are software-timed and jitter ("the servo will fidget").
- Hardware PWM: GPIO12 (pin 32) and GPIO13 (pin 33); reports conflict, so check with a scope. It can't count steps.
- Python stepping: about a few hundred to 2,000 steps/s, rough and loses steps under AI load [u estimate]. **Don't step from the Pi.**

## 2. Real-time stepper control
| Option | Effort | Verdict |
|---|---|---|
| **Arduino/RP2040/ESP32 + AccelStepper over USB serial** | 1–2 h | **Use this** |
| Pi 5 lgpio | 1 h | Fallback only |
| AM62 M4F via remoteproc/RPMsg | 4–10 h | Only with prior TI SDK experience (CCS + MCU+ SDK, rpmsg-char version issues, MCU pinmux) |
| i.MX 95 M7 | unbounded | Avoid (upstream remoteproc still in patch review, Jan 2026) |

**Pattern:**
- The Pi sends absolute **target positions** every frame: `P<pan>,T<tilt>\n` at 115200 baud.
- The MCU runs `moveTo()` + `run()`.
- Pitch line: "the SoC does perception, the MCU does real-time control."

## 3. Drivers
| | A4988 | DRV8825 | TMC2209 |
|---|---|---|---|
| VMOT | 8–35 V | 8.2–45 V | about 4.75–29 V [u] |
| Current | `Vref = 8·I·Rcs` (0.068 Ω → 1 A = 0.54 V) | `Vref = I/2` (1 A = 0.5 V) | BTT: Rs = 0.11 Ω; Vref 1.2 V ≈ 0.9 A rms |
| Microstep | MS1/2/3 HHH = 1/16 | MODE HLH = 1/32 | MS1/MS2 LL = 1/8 (check your board) |

**Wiring:**
- At least 47–100 µF electrolytic across VMOT–GND, close to the driver.
- **Never plug or unplug a motor while it's powered.**
- DRV8825: tie RESET and SLEEP high.
- Find coil pairs with a multimeter: a few Ω means the same coil, open means different coils.

**Running it:**
- **12 V** is fine for a slow pan/tilt.
- Keep the current at or below 70% of the motor rating for a 24-hour run.
- TMC2209 stealthChop is near-silent, which suits the demo floor.

## 4. Power
- **Pi 5:** 5 V / 5 A USB-PD. On 3 A, the USB ports are capped at 600 mA. `PSU_MAX_CURRENT=5000` only if the supply really delivers 5 A.
- **Hailo-8:** about 2.5 W typical, 8.6 W peak.
- **Steppers:** 2 motors on 12 V / 3 A; 4 motors on 12 V / 5 A or 24 V / 3 A.
- **Common ground** everywhere. Don't power a Pi 5 from a cheap buck; if you must, use one rated 5 A or more.

## 5. Comms (bad venue Wi-Fi)
- Unmanaged gigabit switch with static IPs: Pi 5 .10 · Pi 4 .11/.12 · AM62 .20 · i.MX 95 .21 · laptop dashboard.
  - Bookworm: `nmcli con mod "Wired connection 1" ipv4.method manual ipv4.addresses 10.0.0.11/24` [u]
- **Commands:** plain UDP, latest-wins, with sequence number + timestamp.
- **Metrics:** MQTT via mosquitto on the Pi 5. Topics `metrics/<board>/fps|power|temp`. A browser can subscribe over WebSockets.

## 6. Visual-servo loop
- **Error:** `ex = (cx − W/2)/W` with a deadband of 0.03.
- **Steps:** `steps = ex·HFOV·(200·µstep/360)·gear` (HFOV about 66° on Cam Module 3 [u]).
- **Controller:**
  - P-control on the target, Kp 0.3–0.6.
  - Smooth the box with an EMA, α ≈ 0.5.
  - AccelStepper: `setMaxSpeed(2000); setAcceleration(4000)`.
- **Homing:** microswitches, or skip them: center by hand at boot, call that 0, and enforce soft limits (±90° pan / ±30° tilt).

## 7. Power measurement
- **INA219** (26 V, ±3.2 A), wired high-side, address 0x40 [u]. `pip install adafruit-circuitpython-ina219` [u]. **INA226** for 24 V.
- Sample at 10–50 Hz, compute `E += V·I·dt`, publish over MQTT, and show **J per inference** or **Wh per hour** in A/B modes.
- A USB-C inline meter (5 A PD) is the easy visual.

## 8. Pi 5 camera + Hailo
```
sudo apt update && sudo apt full-upgrade -y && sudo rpi-eeprom-update -a && sudo reboot
sudo apt install dkms hailo-all rpicam-apps && sudo reboot
hailortcli fw-control identify
rpicam-hello -t 0 --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json
```
- **Python:** `picamera2.devices.Hailo` [u].
  - **main** stream at 1280×720 + **lores** stream at 640×640, format **RGB888** (YUV420 errors).
  - The init order of Picamera2 vs Hailo matters.
- **Speed:** run inference on lores only, fix the exposure, and drop the frame backlog.
- **Fallback:** `hailo-rpi5-examples` (GStreamer `detection.py`).

## Sources
raspberrypi.com/documentation/computers/raspberry-pi.html · raspberrypi.com/documentation/computers/ai.html · pololu.com/product/1182 · pololu.com/product/2133 · abyz.me.uk/lg/py_lgpio.html · learn.adafruit.com/adafruit-ina219-current-sensor-breakout · github.com/Pioreactor/rpi_hardware_pwm · linuxcnc.org/docs/devel/html/en/motion/tweaking-steppers.html · global.bttwiki.com/TMC2209.html · dev.ti.com/tirex (AM62x academy IPC tour) · e2e.ti.com/support/processors-group/processors/f/processors-forum/1290311/am625-ipc-error · patchew.org/linux/20260109-imx95-rproc-2026-1-8-v6-0-d2fefb36263d@nxp.com · community.hailo.ai/t/hailo-8-power-consumption/2879 · community.hailo.ai/t/picamera2-python-code-example-with-hailo/14618 · github.com/hailo-ai/hailo-rpi5-examples
