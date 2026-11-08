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

## Bring list (Rafael, 2026-11-07 ~6:45 PM, his words)
| Item | Notes |
|---|---|
| Soldering station + accessories | |
| Raspberry Pi 5 + Camera Module 3 | |
| Raspberry Pi 45 W USB-C power supply | bought |
| AI HAT+ 26 TOPS | bought |
| Active Cooler | bought |
| Case fan | bought; **size to measure** (the case session needs width, thickness, hole spacing) |
| Software defined radio kit | bought |
| Adafruit NeoPixel ring(s) | bought (status display) |
| Adafruit I2S mic | bought |
| Arduino Uno R3 + servo motors | **Uno R3 uses a USB-A to USB-B cable, not micro-USB** |
| All kit modules (accelerometer, OLED, temperature, etc.) | see [HackUTD-Inventory](HackUTD-Inventory.md) |
| Jumper wires, wire cutters/strippers | |
| USB to micro-USB cable | |
| HDMI to micro-HDMI cable | Pi 5 → monitor |
| Screwdriver set, multimeter | |
| Keyboard, mouse | |
| 9 V batteries | |
| Capacitors, diodes, heat sinks, bolts and screws | include the M3 screws/nuts + heat-set inserts the case needs |

**Not on his list (suggested checks):**
- microSD card with Pi OS (+ a spare)
- heat-set insert tip
- M2.5 screws (getting later)
- laptop + charger
- the tablet monitor + its power cable
- phone
- USB headset or speaker (voice output still open)
- power bank (outage power still open)
- filament (owned)
- USB-A to USB-B cable for the Uno

## BOUGHT (Micro Center, Sat 2026-11-07 ~6 PM): the actual purchase
Rafael: "everything else on the buy list we won't have."

| Bought | MC SKU | Price | vs the plan |
|---|---|---|---|
| Raspberry Pi 45 W USB-C power supply | 829002 | $14.99 | Replaces the 27 W supply / the "45 W charger if needed" line |
| USB 3.0 A-to-A extension, 3 ft, male/female | 601583 | $9.99 | The SDR extension (longer than planned) |
| **Raspberry Pi AI HAT+ 26 TOPS** | 772574 | $109.99 | **Was dropped from the plan**; now owned |
| Software defined radio ("NPD", likely a **Nooelec NESDR**) | 051086 | $59.99 | Replaces the Adafruit stick. Nooelec sticks normally use an **SMA** antenna connector (check) |
| Adafruit I2S MEMS microphone | 837724 | $8.99 | **1 bought** (the plan had 2) |
| Adafruit NeoPixel ring (LED count: check the bag) | 466599 | $8.99 | As planned |
| Raspberry Pi Active Cooler | 620310 | $9.99 | As planned |
| Fan (receipt reads "Raspberry Pi 4 case"; Rafael: it's the fan) | 188631 | $4.99 | Case cooling |

**Owned / later (Rafael):** filament (owned), M2.5 screws (getting later), Camera Module 3 (owned, **back in**).
**NOT bought (won't have):** PiPower 5 UPS, 5 A USB-C cable, DFRobot SEN0395 radar, MAX98357A amp, 40 mm speaker, power strip, Command strips.

## Buy list, by priority (plan before the purchase) (Micro Center only; exact names to look for)
**Micro Center only** (Rafael can't order from Amazon, 2026-11-07). MC numbers come from research and are unverified, so match the name on the box.

### Priority 1: the demo doesn't work without these
| # | Exact part | What it does | MC # | ~Price |
|---|---|---|---|---|
| 1 | **SunFounder PiPower 5** (UPS / battery backup board for Raspberry Pi 5, 5 V 5 A output) | Keeps the Pi on when the power is cut (the core demo) | 708124 | $36 |
| 2 | **Battery pack for the PiPower 5**: SunFounder's own 7.4 V 2-cell 18650 pack (XH2.54 3-pin plug). Very likely in the PiPower 5 box (the PiPower 3 kit included one); **check the box. Loose 18650s won't plug in** | The backup battery | — | only if missing |
| 3 | **USB-C (male) to USB-C (male) cable, rated 5 A / 100 W ("e-marked"), 1 ft (0.3 m) or shorter**; one 90° right-angle end if they have it | PiPower 5 output → Pi 5 power input. A normal 3 A cable makes the Pi brown out | — | $10 |
| 4 | **Raspberry Pi Active Cooler for Raspberry Pi 5** (official clip-on heatsink + fan); skip if you own one | Stops the Pi overheating inside the closed case | 671930 | $5 |
| 5 | **DFRobot SEN0395 24 GHz mmWave human presence sensor** | Detects a person even when they're lying still (drives the alarm rule) | 668867 | $29 |
| 6 | **Adafruit I2S 3 W Class D amplifier breakout, MAX98357A** | Drives the speaker (the Pi 5 has no headphone jack) | 613583 | $6 |
| 7 | **Adafruit mono enclosed speaker, 3 W 4 Ω, 40 mm** (or any 40 mm 4 Ω 3 W speaker) | Says "Are you okay?" | 612826 | $6 |
| 8 | **Power strip / surge protector with a lighted on/off rocker switch**; skip if you own one | The judge flips it to cut the power | — | $10 |

### Priority 2: needed for the case as designed and the decided features
| # | Exact part | What it does | MC # | ~Price |
|---|---|---|---|---|
| 9 | **2 × Adafruit I2S MEMS microphone breakout, SPH0645LM4H** (or **INMP441 I2S microphone module**, same pocket) | Hears the answer; two mics handle a noisy room. **Fallback:** your USB mic | 613585 | $7 each |
| 10 | **Adafruit NeoPixel ring, 16 × 5050 RGB LED** (must say **RGB**, not RGBW) | Status light: green OK, amber on battery, red alarm | 655358 | $10 |
| 11 | **1.75 mm PLA filament, black, 1 kg** + **1.75 mm PLA, white or clear (natural)**; plain PLA, **not** PLA-CF; skip what you own | The case (~300 g black, ~8 g white for the light diffuser + radar window) | — | $20 a roll |
| 12 | **Adafruit Software Defined Radio receiver USB stick, RTL2832 with R820T** (Adafruit #1497) | Hears NOAA Weather Radio alerts with no internet (decision 7) | 656639 | ~$25 |
| 13 | **USB-A (male) to USB-A (female) extension cable, USB 2.0 or 3.0, 6–12 in (15–30 cm)** | Male end into the Pi's black USB 2.0 port; the radio stick plugs into the female end, away from the Pi's noise | — | $5 |

### Priority 3: only if needed (check first)
| # | Exact part | Buy it when… | MC # | ~Price |
|---|---|---|---|---|
| 14 | **USB-C PD wall charger, 45 W or higher** + **USB-C (male) to USB-C (male) cable, 60 W or higher** | The PiPower 5 box says it needs more than 27 W input (your laptop's USB-C charger also works) | — | $25–35 |
| 15 | **Adafruit black nylon screw and stand-off set, M2.5** | You have **no M2.5 screws** at home. The case holds the Pi 5 and the PiPower 5 with 8 × M2.5x6 screws + 8 M2.5 nuts | 503925 | ~$15 |
| 16 | **3M Command strips or VHB double-sided mounting tape** | You want the box stuck to the table or a wall for the demo | — | $5 |

**Priority 1 + 2 total ≈ $175–200.**

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
