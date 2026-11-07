---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, hardware, inventory]
---

# HackUTD 2026: Inventory

Part of [HackUTD-2026](HackUTD-2026.md). Rafael's gear as of 2026-11-07. Godfrey's gear: unknown.

## Compute
| Item | Qty | Planned role |
|---|---|---|
| Laptop | 1 | Dev, training, dashboard, off-board GPU work if any |
| Phone | 1 | Demo video, hotspot backup |
| NXP **FRDM i.MX 95** (8 GB, 6× A55 + M7, ~2 TOPS NPU) | 1 | Spare CPU node / real-time M7. NPU skipped ([HackUTD-Research-Boards](research/HackUTD-Research-Boards.md)) |
| TI **SK-AM62(B)** (4× A53 + M4F, no NPU) | 1 | Networked node (dashboard / second camera). Not the motor controller. Already up from HackEdge-2026 (SSH alias `board`) |
| Raspberry Pi **5** + camera module | 1 | Main AI node |
| Raspberry Pi **4** | 2 | Gate or sensor nodes |
| Raspberry Pi **3** | 1 | Always-on motion or wake gate |
| **ESP32** dev board | 2 | **Stepper controller** (FastAccelStepper; added 2026-11-07) + spare |
| **Arduino Uno** | 2 | Backup stepper controller / sensor node (added 2026-11-07) |

## Motion / mechanical
- NEMA steppers ×4 + drivers ×4 (**driver model: check, A4988, DRV8825 or TMC2209?**)
- Bearings, M3 bolt and screw sets, 3D printer

## Peripherals
- Keyboards ×2, mice ×2, USB microphone, headset
- **Tablet-sized monitor** (added 2026-11-07). Planned role: on-device judge-facing UI (live overlay + metrics). To check: size, resolution, HDMI or USB-C, touch, power.

## Bench
- Breadboards, jumpers, kit modules, capacitor and resistor sets, soldering station, hand tools

## Shopping list (Micro Center Dallas; call to check stock)
- [ ] **Servo supply, 5–6 V ≥ 3 A** (SG90/MG90S) or **≥ 5 A** (MG996R), separate from the Pi, common ground with the ESP32 (servo plan, 2026-11-07)
- [ ] 470–1000 µF electrolytic across the servo rail
- [ ] 12 V supply for steppers: **only if we fall back to steppers** (2 motors: 3 A, 4 motors: 5 A)
- [x] ~~Pico~~: not needed, 2× ESP32 + 2× Arduino Uno owned (2026-11-07). **TMC2209, 12 V 5 A PSU, INA219 and GT2 parts have no Micro Center listing found, so call ahead.**
- [ ] 47–100 µF electrolytic caps (one per driver), if not in the kit
- [ ] Pi 5 official 5 V / 5 A USB-C supply (if not owned)
- [ ] Raspberry Pi **AI HAT+ 26 TOPS (Hailo-8)**, if ≤ $140. NOT the 13 TOPS or the AI HAT+ 2
- [ ] Pi 5 Active Cooler (if not owned)
- [ ] **52Pi 4010 5 V PWM fan, 2-pack** (Micro Center SKU 605634) for the custom Pi 5 + AI HAT+ case. Confirm Dallas stock. Includes M3x16 + nuts.
- [x] M3 heat-set inserts: owned (2026-11-07), for the custom case. Case files: `Documents/3D-Prints/Pi5-AI-HAT-Case/` (PLAN.md)
- [ ] Buck converter, power strip, spare microSD cards (64 GB+)
- [ ] Ethernet switch + cables (venue Wi-Fi will be bad)
- [ ] Optional: INA219 power-measurement module or USB-C inline meter (for the energy demo)
- [ ] **Pan/tilt parts** ([HackUTD-Research-Mechanical](research/HackUTD-Research-Mechanical.md)): GT2 belt + 20T 5 mm-bore pulleys, 608ZZ bearings (if not owned), (M2.5 standoffs not needed: the custom case uses the HAT kit's spacers) Pi 5 camera cable ≥ 300 mm
- [ ] After the idea is locked: limit switches, filament

## Check before leaving
- Pi power supplies, HDMI / micro-HDMI cables, monitor, filament, all model weights downloaded
