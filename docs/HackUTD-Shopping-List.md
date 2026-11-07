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
**The enclosure session's own parts list hasn't come back yet.** Add its fasteners and any other case parts when it replies.

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
| 9 | **Switched power strip** (skip if owned) | The "power cut" demo: flip the switch | MC or anywhere | ~$10 |
| 10 | **RTL-SDR Blog V4 (or V3) + dipole antenna kit** | Rafael's decision 7: hear NOAA Weather Radio alerts with no internet. Not a generic TV-tuner stick | Amazon / rtl-sdr.com (likely not at MC) | ~$30–40 |

**Must-buy total ≈ $150–175** (≈ $115–135 at Micro Center + the RTL-SDR online).

## Check first (may change the list)
- **UPS input power:** the risk register says the PiPower 5 may need ≥ 32 W USB-C PD input for a Pi 5 [unverified]. The 27 W Pi supply might not keep it charged. Read the spec in store; if it's true, bring a ≥ 45 W USB-C laptop charger.
- **Microphones:**
  - #11 / the case use **2 × I2S mics (SPH0645, MC #613585, $6.95 each)** to focus on a voice in a noisy room.
  - Godfrey's #18 uses the **USB mic you own**.
  - The SPH0645 may be ship-only, not in store.
  - **Recommendation:** buy the I2S mics only if they're on the shelf; otherwise use the USB mic and tell the case session.
- **Filament:**
  - Venue printers are PLA only and run by organizers.
  - If you print on your own Bambu in PLA-CF, you need a **hardened-steel 0.4 nozzle**.
  - You also need ~5 g of **white/clear non-carbon PLA/PETG** for the LED diffuser and the radar window (carbon fibre can block the radar).
  - You own PETG (colour unknown).

## Nice to have (team call)
| Part | Why | Where | ~Price |
|---|---|---|---|
| LILYGO LoRa32 915 MHz ×2 | Alerts still get out when Wi-Fi/cell is down | MC #699324 | ~$27 each |
| INA219 power monitor | Shows power draw in each mode (low-power story) | MC / online | ~$10 |
| Consumer CO alarm (Kidde/First Alert) | Godfrey's CO plan: the mic hears its beep (use its test button) | Walmart / Home Depot | ~$23–40 |
| Sensirion SCD41 (CO2 + temp + RH) | Safe live "breathe on it" gas demo | Amazon / Adafruit | ~$15–80 |
| Right-angle USB-A extension 15–30 cm + SMA bulkhead pigtail ~10 cm | Mount the RTL-SDR and antenna inside/through the case (skip the pigtail if the SDR kit has one) | Amazon / MC | ~$10 |
| 52Pi 4010 fan | Only if the Pi runs hot in the case | MC SKU 605634 | ~$10 |
| Spare microSD 64 GB+, small Ethernet switch | Clone the working card; wired network at the venue | MC | — |

## Already owned: don't buy
Pi 5 + 27 W supply · 2× ESP32 · USB mic · **gyro/accelerometer (MPU-6050, earthquake)** · SW-420 vibration · PIR · DHT11 / BME280-class / DS18B20 temperature · MQ-2 · flame · water level · raindrop · passive buzzer · small OLED · I2C LCD 1602 · RTC · ADC · buttons · resistors · jumpers · PETG filament. Full list: [HackUTD-Inventory](HackUTD-Inventory.md).

## Not buying (dropped)
AI HAT+ (no camera vision; #18 dropped it), camera + long cable, servos/pan-tilt parts, 12 V supply, GT2 belt, 52Pi fan (unless hot), SHT41 / BME680 (temperature and gas already owned), MQ-7 (not life-safety grade).

## Open (Rafael's call, not a purchase yet)
- **Wall tablet** for the home UI (decision 8): an old tablet/phone in kiosk mode vs a Pi touchscreen.
