---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, hardware, shopping]
---

# HackUTD 2026: Final Shopping List (idea v2 home safety box)

Part of [HackUTD-2026](HackUTD-2026.md). Merged 2026-11-07 ~3:50 PM from:
- GitHub #11 (hardware run + 3 update comments)
- #18 (Godfrey's agreed-demo parts list)
- the alert-feeds session (RTL-SDR)
- the sensors research (`docs/lifeline/Sensors-*.md`)
- the node risk register
- Rafael's own decisions: camera out, Pi stays on a UPS, kit accelerometer

**Stock and prices are unverified** (Micro Center blocks bots). Call or check the app before driving. Micro Center Dallas, 13929 N Central Expy, open until 9 PM.
The case session's parts list (rafam-ca, ~3:55 PM) is merged in.

## Must buy
| # | Part | Why | Where | ~Price |
|---|---|---|---|---|
| 1 | **SunFounder PiPower 5** (Pi 5 UPS, 5 V/5 A) | Keeps the Pi on when the power is cut (decided) and tells it "mains lost". 3 A boards brown out | MC #708124 | $35.99 |
| 2 | **2 × 18650 cells** (only if not included with #1); flat or button top to fit the holder | UPS battery | MC | ~$10–20 |
| 3 | **Short USB-C ↔ USB-C cable, 5 A e-marked** (right-angle if possible) | UPS → Pi; a 3 A cable causes brownouts | MC | ~$10 |
| 4 | **Raspberry Pi 5 Active Cooler** (skip if owned) | The Pi overheats in a closed case | MC #671930 | ~$5 |
| 5 | **mmWave presence radar**: DFRobot SEN0395 (24 GHz) or HLK-LD2410C | Sees a still person. Drives the alarm rule and "goes still after a fall" | MC #668867 (LD2410C is not at MC) | ~$29 |
| 6 | **MAX98357A I2S amp** | Voice output (the Pi 5 has no headphone jack) | MC #613583 | $5.95 |
| 7 | **Speaker, 40 mm, 4 Ω, 3 W** | Speaks "Are you okay?" | MC #612826 (in store only) | $5.95 |
| 8 | **NeoPixel ring, 16 LED, RGB not RGBW** | Status light (green / amber on battery / red alarm); the case is designed around it | MC #655358 | $9.95 |
| 9 | **Switched power strip** (skip if owned) | The "power cut" demo: flip the switch | MC | ~$10 |
| 10 | **Adafruit Software Defined Radio USB stick (RTL2832U + R820T, Adafruit #1497)** | Rafael's decision 7: hear NOAA Weather Radio (162.4–162.55 MHz, inside its 24–1850 MHz range) with no internet. Only RTL-SDR found at Micro Center. It's the cheaper generic-style stick the alert session warned can drift and run hot, so set a ppm correction in `rtl_fm` and give it airflow. Its small antenna likely uses an **MCX** plug, not SMA [u] | MC product 656639 (SKU 495903 / 025270) | ~$25 [u] |
| 11 | **Short USB-A extension** (right-angle if the shelf has one) | Lets the stick sit inside the case away from the Pi | MC (Inland) | ~$5 |
| 12 | **2 × I2S MEMS mic** (SPH0645 or INMP441) | The case has 17.5 × 14.5 mm pockets for them. Fallback: the owned USB mic (tell the case session) | MC #613585 | $6.95 each |
| 13 | **Black PLA ~300 g + white/clear PLA ~8 g** (skip whatever you own) | Whole case + faceplate; the white goes in the status-light diffuser and the radar window | MC | ~$20 per roll |
| 14 | **Mounting:** 4 × #8 wood screws + drywall anchors, OR VHB / Command strips for the demo table | Wall/ceiling twist-lock plate | MC | ~$5 |

**Micro Center only (Rafael can't order from Amazon, 2026-11-07).** Must-buy total ≈ $175–200.

## Check first (may change the list)
- **UPS input power:** the PiPower 5 may need ≥ 32 W USB-C PD input for a Pi 5 [unverified]. If the box says so, **a ≥ 45 W USB-C PD charger becomes a must** (use your laptop charger if it's USB-C PD).
- **I2S mics:** the SPH0645 may be ship-only. If it isn't on the shelf, the INMP441 fits the same pocket; otherwise use the USB mic.
- **Use plain PLA, not PLA-CF.**
  - It removes the risk of carbon fibre blocking the radar or Wi-Fi.
  - It removes the need for a hardened-steel nozzle.
  - It matches the venue printers (PLA only, organizer-run).
- **Print time:**
  - The core is **~9.5 h of printing in 4 big parts** + 1–3 h for the faceplate. Start early or split it across printers.
  - Parts are 150 × 150 mm; the P1S bed (256 mm) is fine.
  - The faceplate's colour logos need a filament-change pause; ask the venue if they allow that, or print it on your own Bambu.

## Nice to have (team call)
| Part | Why | Where | ~Price |
|---|---|---|---|
| LILYGO LoRa32 915 MHz ×2 | Alerts still get out when Wi-Fi/cell is down | MC #699324 | ~$27 each |
| INA219 power monitor | Shows power draw in each mode (low-power story) | MC / online | ~$10 |
| **52Pi 4010 5 V fan** (case session: strongly recommended) | Pushes room air onto the Pi in the closed box; the case already has its socket + grille. Run it on 5 V | MC SKU 605634 | ~$10 |
| Thin double-sided foam tape, zip ties/velcro | Mic gaskets; hold the SDR. Hot glue is free at the venue | MC | ~$5 |
| Spare microSD 64 GB+, small Ethernet switch | Clone the working card; wired network at the venue | MC | — |

## Already owned: don't buy
Pi 5 + 27 W supply · 2× ESP32 · USB mic · **gyro/accelerometer (MPU-6050, earthquake)** · SW-420 vibration · PIR · DHT11 / BME280-class / DS18B20 temperature · MQ-2 · flame · water level · raindrop · passive buzzer · 0.91" 128×32 I2C OLED (Hosyond) · M3 heat-set inserts (19 used; keep 30) · M3 screws (4× M3x12, 3× M3x10, 6× M3x8, 4× M3x6–8, 2× M3x10 + nuts: check lengths) · I2C LCD 1602 · RTC · ADC · buttons · resistors · jumpers · PETG filament. Full list: [HackUTD-Inventory](HackUTD-Inventory.md).

## Not buying (dropped)
- **M2 camera screws:** not needed (camera out).
- **M2.5:** Rafael says not needed. **Caveat:** the case session now mounts the Pi 5 and the PiPower 5 with 8 × M2.5x6 screws + 8 × M2.5 hex nuts in printed nut traps, because their holes are 2.7 mm and M3 won't pass. If Rafael has no M2.5 screws at home, buy the Adafruit nylon M2.5 set (MC 503925).
- **Amazon-only parts:** RTL-SDR Blog V4 (replaced by the Adafruit stick at MC), SMA bulkhead pigtail (the case now uses a plain 7 mm cable hole for the stick's MCX antenna), SCD41, consumer CO alarm (Walmart/Home Depot; ask whether MC carries one).
AI HAT+ (no camera vision; #18 dropped it), camera + long cable, servos/pan-tilt parts, 12 V supply, GT2 belt, magnets, light pipes, metal standoffs (the case uses printed bosses + inserts), SHT41 / BME680 (temperature and gas already owned), MQ-7 (not life-safety grade).

## Open (Rafael's call, not a purchase yet)
- **Wall tablet** for the home UI (decision 8): an old tablet/phone in kiosk mode vs a Pi touchscreen.
