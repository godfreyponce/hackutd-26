---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, hardware, status]
---

# HackUTD 2026: Hardware Status (Sat 2026-11-07 ~9:30 PM)

Part of [HackUTD-2026](HackUTD-2026.md). Idea: [HackUTD-Idea-Home-Monitor](HackUTD-Idea-Home-Monitor.md). Purchases: [HackUTD-Shopping-List](HackUTD-Shopping-List.md). Kit modules: [HackUTD-Inventory](HackUTD-Inventory.md).

## Hardware on hand
| Part | Status | Notes |
|---|---|---|
| Raspberry Pi 5 (8 GB) | ✅ running | hostname `rafhost` |
| Raspberry Pi 45 W USB-C power supply | ✅ in use | bought |
| Raspberry Pi Active Cooler | ✅ installed | bought |
| **AI HAT+ 26 TOPS (Hailo-8)** | ✅ **working** | bought; on the 16 mm stack |
| **Camera Module 3 NoIR** (imx708_noir) | ✅ working | Owned. NoIR = no IR filter: pinkish colours by day, sees in the dark with IR light |
| Software defined radio stick ("NPD", likely Nooelec NESDR) | not tested yet | bought |
| Adafruit I2S MEMS mic (SPH0645) | bought, 2nd on the partner run | headers to solder |
| Adafruit NeoPixel ring | bought, not wired | LED count to confirm |
| Fan (Argon POLY+ 5 30 mm via the partner run; Pi 4 case fan bought) | not mounted | measure the hole spacing for the case |
| USB 3.0 A-A 3 ft M/F extension | bought | for the SDR |
| Partner run (Godfrey): MAX98357A amp, 3 W 4 Ω speaker, 2nd I2S mic, M3 × 1/4" screws, Argon POLY+ 5 case (for its fan), micro-HDMI adapter kit | arrived | |
| Kit modules (MPU-6050 accelerometer, 0.91" OLED, BME280-class temp, MQ-2, PIR, buzzer, RTC, ADC, …) | owned | see [HackUTD-Inventory](HackUTD-Inventory.md) |
| Tools | owned | soldering station, wire cutters/strippers, multimeter, screwdrivers, calipers (battery dead) |
| Not bought / not available | — | PiPower 5 UPS (not stocked at MC Dallas), radar (replaced by camera + AI HAT+), 5 A cable, power strip |

## Pi 5 software state
- **OS:** Raspberry Pi OS 64-bit (Trixie), kernel **6.18.60+rpt-rpi-2712**. Flashed with Imager 2026-11-07: user `rafael`, SSH on, Raspberry Pi Connect enabled.
- **Network:** joins Rafael's iPhone hotspot (`172.20.10.6`, `rafhost.local`) and the HackUTD Wi-Fi. The SSID has a curly apostrophe; the card has both spellings.
- **Remote access:** Rafael's laptop key `id_ed25519_board` is in `authorized_keys`. sudo still asks for the password.
- **AI HAT+ software:** `hailo-all` 5.1.1 = HailoRT **4.23.0** + `hailo-tappas-core` 5.1.0 + `rpicam-apps-hailo-postprocess`.
  - ⚠️ **Gotcha (fixed):** kernel 6.18.60 no longer ships the built-in `hailo_pci` driver (6.18.50 did). Fix: `sudo apt install dkms && sudo apt install --reinstall hailort-pcie-driver && sudo dkms autoinstall && reboot`.
  - Result: `hailo_pci/4.23.0` built for 6.18.60, `/dev/hailo0` present, `hailortcli fw-control identify` reports **Hailo-8**, FW 4.23.0.
  - PCIe link is already Gen 3 (8 GT/s x1).
- **Verified:**
  - plain capture (`rpicam-still`)
  - live Hailo YOLOv8 detection (`rpicam-hello -n --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json`): objects detected
  - `throttled=0x0`, 35–45 °C
- **Known issue:** `rpicam-still` + a Hailo post-process file → "Device timeout". Use `rpicam-hello`/`rpicam-vid` (video pipeline) for AI.
- **Next:**
  - hold packages (`apt-mark hold` on the kernel + Hailo packages)
  - person test standing/lying
  - SDR `rtl_test`
  - I2S mic + amp overlays

## Open problems
1. **GPIO access through the AI HAT+:** the stacking header pins barely poke through the HAT.
   - The extra-tall 2x20 header (52Pi kit, MC 608950) is sold out and Micro Center is closed (opens Sun 11 AM).
   - Options: venue MLH/HARP/Help Desk; solder wires to ~12 pins and share I2C/power on a mini breadboard.
2. **Outage power:** no UPS. Options: pass-through power bank (must test for a reboot glitch) or a simulated outage.
3. **Fan size** for the case (30 mm Argon fan: measure the hole spacing).

## Pins needed (~12)
3V3, 5V, GND · I2C SDA GPIO2 / SCL GPIO3 (accelerometer 0x68, OLED 0x3C, temperature) · I2S BCLK GPIO18, LRCLK GPIO19, mic DOUT GPIO20, amp DIN GPIO21 · NeoPixel DIN GPIO10 (SPI) via 330 Ω.
