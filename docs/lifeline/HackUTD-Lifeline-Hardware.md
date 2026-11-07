---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, lifeline, hardware]
---
Part of [HackUTD-2026](../HackUTD-2026.md) · idea [HackUTD-Idea-Shortlist](../HackUTD-Idea-Shortlist.md) #1.

# Lifeline Grid: hardware + firmware build sheet

Scope: Rafael's side (node hardware, firmware, LoRa path, Pi 5 hub plumbing). The agent side (Nemotron, Twilio) is the teammate's. `[u]` = unverified (price, stock, pin choice). Check it before you rely on it.

**Safety rule (fixed):** no opened or hand-wired 120 VAC. The only mains at the table is UL wall adapters plugged into a **switched power strip**. Flipping the strip switch is the "power outage". Everything after the adapters is low-voltage DC.

## 0. The answer in one screen

**Recommended rig (Rig A):**

```
switched strip ─┬─ 12 V 2 A adapter ─ barrel Y-split ─┬─ mini DC UPS (12 V in) ─ 12 V out ─ INA219 ─ 12 V fan ("concentrator")
                │                                     │                        └ 5 V USB out ─ ESP32 node (holdup)
                │                                     └─ 33k/10k divider ─ ESP32 GPIO34 (mains sense)
                └─ "home Wi-Fi": Pi 4 AP or travel router (dies with the strip)

ESP32 node ─UART─ Heltec V3 #1 (Meshtastic, own LiPo) ~~915 MHz~~ Heltec V3 #2 ─USB─ Pi 5 hub
ESP32 node ─UART 256000─ LD2410C radar
Pi 5 hub: Mosquitto + Python bridge (meshtastic → MQTT) + local queue + kiosk dashboard
```

**One flip of the strip switch does the whole demo:** the fan keeps spinning on the UPS, the node sees mains drop, the home Wi-Fi AP dies with it, MQTT fails, and the alert arrives at the hub over LoRa with a live runtime countdown and "person present, still".

**Guaranteed same-day fallback (Rig B):** USB-C wall charger → USB breakout (tap VBUS for mains sense) → power bank with pass-through → 5 V USB blower. Node on its own second power bank. Everything here is plain Micro Center stock.

## 1. Power: architecture options

### Options for the demo rig

| Rig | Chain | What you can measure | Pros | Cons | Verdict |
|---|---|---|---|---|---|
| **A. Mini DC UPS (router UPS)** | 12 V adapter → mini DC UPS → INA219 → 12 V fan | Load current + voltage (INA219). Mains via divider on the adapter side. Battery SoC **estimated** from rated Wh minus energy used | No-break switchover is what these are built for (routers) [u]. Has 5 V USB out for the node. Looks like a real "concentrator on a UPS" | Battery is sealed. Output is regulated, so the voltage curve tells you nothing until it dies. Amazon only, so arrival tonight is a gamble | **Recommended if it arrives by ~7 PM** |
| **B. Power bank with pass-through** | USB-C charger → USB breakout → power bank → 5 V USB fan | Same as A (load-side INA219, energy counting) | Micro Center has everything today | Many banks blip output on plug/unplug, and some refuse pass-through. Some auto-off below ~50-100 mA load [u]. 5 V fan is less theatrical | **Baseline, buy today** |
| C. DIY diode-OR with a measurable pack | 12 V adapter and 3S Li-ion pack diode-ORed to the fan, INA219 on the pack lead | **True battery-side** current and voltage. Real coulomb counting + voltage curve | Most honest telemetry | Pack charging, protection and the diode-OR float voltage problem (a full 3S pack at 12.6 V beats a 12 V adapter and drains first). Battery safety risk at 3 AM | Skip unless A and B both fail. Say it is the production design |

### Measuring (Rig A wiring)

| Signal | Part | Wiring | Notes |
|---|---|---|---|
| Load current + bus voltage | INA219 breakout (0.1 Ω shunt, 26 V, ±3.2 A) | High side: UPS 12 V out → VIN+, VIN- → fan +. Fan - → common GND. INA219 VCC 3.3 V, GND, SDA GPIO21, SCL GPIO22 (I2C 0x40) | INA219 GND **must** share ground with the 12 V system or bus voltage reads garbage. INA226 is the upgrade (36 V, 16-bit), not needed here |
| Mains present | 33 kΩ / 10 kΩ divider on the adapter side of the Y-split | 12 V × 10/43 = 2.79 V → GPIO34 (ADC1, input-only) | Use ADC1 pins only (32-39). ADC2 does not work while Wi-Fi is on. Add 100 nF to GND for noise. Threshold: below 9 V for 300 ms = mains lost |
| Mains present (Rig B) | 10 kΩ / 15 kΩ divider on the USB breakout VBUS | 5 V × 15/25 = 3.0 V → GPIO34 | Same logic |

### Battery estimate (what the firmware computes)

- **Energy counting** (sealed battery, Rig A/B): `E_used += V_bus × I × dt / η` integrated at 10 Hz while mains is off. `E_left = E_rated × 0.8 - E_used` (0.8 = usable fraction, η ≈ 0.85 for the boost stage) [u]. `est_minutes_left = E_left / P_avg(60 s)`.
- **Coulomb counting + voltage curve** (only when you can see the cell, Rig C or a real product): integrate amp-hours for the short term, re-anchor SoC from the open-circuit voltage curve when the load is light. Coulomb counting drifts. The voltage curve is flat in the middle for Li-ion, so you need both.
- **Peukert:** only matters for lead-acid (most home UPS units). Li-ion is close to 1.0. Mention it in one sentence to judges if asked "why not just Ah / A".
- **Demo mode:** set `E_rated` tiny (for example 0.5 Wh) via an MQTT config topic so the countdown visibly moves on stage. Say so on the slide ("time-compressed").
- **Calibration tonight:** run one full discharge of the real UPS on the fan while logging. That gives the true usable Wh and a defensible number.

### How a real product would do it (what to say to judges)

| Approach | How | Honest limits |
|---|---|---|
| **Smart plug with energy metering** (best real answer) | Shelly Plug US class device: local HTTP/MQTT API reports watts. The concentrator plugs into it | Plug loses power in an outage too, so mains-loss is "plug went silent + node's own sense". Shelly API: https://shelly-api-docs.shelly.cloud/ |
| **CT clamp** (non-invasive) | SCT-013-030 (30 A → 1 V) on **one** conductor. Clamping the whole cord reads zero because the currents cancel, so it needs a line-splitter adapter | Needs burden/bias circuit and RMS sampling. OpenEnergyMonitor docs: https://docs.openenergymonitor.org/electricity-monitoring/ct-sensors/ |
| **Read the device's own battery** | Some portable concentrators, CPAPs and ventilators expose data (USB, BLE, SD card) | Mostly closed, proprietary protocols. FDA-regulated. Don't claim you can do this generally |
| **The node's own UPS sense** (what we built) | Node sits on the same UPS as the device, measures DC side | Requires a DC device or a UPS with a data port (many home UPSes have USB HID: `upsc` / NUT on the Pi reads charge % and runtime directly) |

Pitch line: *"In a home we'd read the UPS over USB with NUT, or meter the plug with a smart plug. On the table we use a DC stand-in so nobody touches mains. The estimator is the same math."* Real numbers for context: a stationary home oxygen concentrator draws roughly 300-600 W [u], so a consumer UPS lasts minutes, not hours. That is the whole reason the alert matters.

## 2. Radar: which module

| Module | Band | Outputs | Stationary person | Breathing rate | Interface | Price / availability |
|---|---|---|---|---|---|---|
| **HLK-LD2410C** | 24 GHz | Target state: 0 none, 1 moving, 2 still, 3 both. Moving + still distance (cm) and energy (0-100) per target. OUT pin = presence | **Yes**, this is its job (micro-motion incl. breathing) | No rate. "Still energy" fluctuates with breathing but no validated rate | UART 256000 8N1. VCC **5 V**, IO is 3.3 V TTL. BLE config app (HLKRadarTool) | ~$5-8 each, 2-3 packs on Amazon [u] |
| HLK-LD2450 | 24 GHz | Up to 3 targets with x, y, speed | **Weak**: tracks moving targets; a still person can drop out | No | UART 256000, 5 V | ~$10-15 [u] |
| Seeed MR24HPC1 | 24 GHz | Presence, "someone moving / still", body-movement parameter | Yes | No | UART 115200, 5 V | ~$30 [u], Seeed only |
| **Seeed MR60BHA2** (kit with XIAO ESP32C6) | 60 GHz | Breathing rate, heart rate, distance, presence | Yes | **Yes, conditionally**: person still, within ~1.5 m, chest facing the sensor [u]. Heart rate is rough | Runs ESPHome on the XIAO out of the box | ~$30-40 [u]. Not same-day |

**Honest answer on breathing:** the only cheap module that outputs a breathing **rate** is the 60 GHz MR60BHA2, and only for a still person close to the sensor. Not a medical measurement. None of these can be sold as respiration monitoring. For tonight: **LD2410C**, and present the output as "present / moving / still (micro-motion consistent with breathing) / absent". If an MR60BHA2 is ever on hand, it is a drop-in upgrade for the "breathing" tile.

**LD2410C wiring to classic ESP32:**

| LD2410C pin | ESP32 |
|---|---|
| VCC | 5 V (VIN). Do not run it on 3.3 V |
| GND | GND |
| TX | GPIO16 (Serial2 RX) |
| RX | GPIO17 (Serial2 TX) |
| OUT | GPIO27 (optional, presence interrupt) |

- `Serial2.begin(256000, SERIAL_8N1, 16, 17);` Classic ESP32 hardware UART handles 256000 fine.
- Library: ncmreynolds/ld2410 (Arduino). `radar.presenceDetected()`, `movingTargetDetected()`, `stationaryTargetDetected()`, `movingTargetDistance()`, `stationaryTargetEnergy()`. https://github.com/ncmreynolds/ld2410
- ESPHome alternative: built-in `ld2410` component (binary sensors for has_target / moving / still, distances, energies). https://esphome.io/components/sensor/ld2410/
- Range: moving up to ~6 m, still ~4-5 m, in 0.75 m gates (configurable to 0.2 m on newer firmware) [u]. Datasheet: https://www.hlktech.net/index.php?id=1095
- Limits: fans and curtains cause false "moving" (**point the radar away from the demo fan**). It sees through thin PLA but not metal. Mount it ~1 m from the "bed" (a teammate in a chair).

**Node logic:** `motion = moving`, `still = stationary && !moving`, `absent = !presence for 10 s`. Alert condition: "present but no movement for N minutes" (demo N = 20 s), or "absent" during an outage.

## 3. LoRa: Meshtastic path

**Hardware:** 2× Heltec WiFi LoRa 32 **V3** (ESP32-S3 + SX1262, 915 MHz, OLED, onboard LiPo charger). ~$26-30 each [u] (Amazon, Rokland, Ameridroid). No Micro Center listing found. Alternatives: RAK WisBlock 4631 (nRF52, lower power, pricier), LilyGO T-Beam (GPS, 18650 holder). **Screw the antenna on before powering**, or you can damage the SX1262.

**Topology:** Heltec #1 sits in the home node (own LiPo, so it outlives everything). Heltec #2 is USB-attached to the Pi 5 hub ("community hub" at a fire station or community center with backup power and uplink).

**How the ESP32 talks into the mesh (simplest first):**

| Path | How | Effort |
|---|---|---|
| **ESP32 UART → Meshtastic Serial Module (TEXTMSG)** | Enable the Serial Module on Heltec #1. Any line the ESP32 writes on that UART goes out as a text message on the primary channel | **~30 min. Recommended** |
| Pi/host → Python `meshtastic` lib | `iface = meshtastic.serial_interface.SerialInterface("/dev/ttyUSB0"); iface.sendText(msg)`. Receive: `pub.subscribe(on_rx, "meshtastic.receive.text")` | Used on the **hub** side |
| Meshtastic MQTT module | Built-in gateway to a broker | Designed for internet uplink. More config. Skip |
| Node-RED | Has Meshtastic nodes | Extra moving part. Skip |

**Config (Meshtastic CLI over USB, once per board):**

```
meshtastic --set lora.region US
meshtastic --set lora.modem_preset SHORT_FAST
meshtastic --ch-set psk random --ch-index 0        # private channel; then copy the URL
meshtastic --info                                  # grab the channel URL
meshtastic --seturl "<url>"                         # on the second board
# Heltec #1 only:
meshtastic --set serial.enabled true --set serial.mode TEXTMSG \
  --set serial.rxd 47 --set serial.txd 48 --set serial.baud BAUD_38400   # pins [u]: verify free GPIOs on the V3 pinout
```

Wire ESP32 GPIO25 (TX, Serial1) → Heltec GPIO47 (rxd), ESP32 GPIO26 (RX) ← Heltec GPIO48, common GND. Both 3.3 V logic.

- **Payload:** max ~237 bytes per packet, keep text under ~200 chars [u]. Send compact CSV, not JSON: `LG,h=07,m=0,p=2,b=11.9,i=0.42,t=38,s=1` (~40 bytes).
- **Latency:** SHORT_FAST across a room is ~0.5-3 s end to end [u]. LONG_FAST (default) works too but uses more airtime. Don't send more than one packet every ~5-10 s; on LoRa, send on **state change + 30-60 s heartbeat** only.
- **US 915 MHz:** region `US` (902-928 MHz) is legal unlicensed. Avoid the public default channel so you don't spam the real Dallas mesh.
- Docs: https://meshtastic.org/docs/configuration/module/serial/ · https://meshtastic.org/docs/software/python/cli/ · https://github.com/meshtastic/python

**Hub bridge (`lora_bridge.py`, ~30 lines):** on each received text starting with `LG,`, parse CSV → JSON, add `"via":"lora"` and `rssi/snr`, publish to `lifeline/{home_id}/telemetry` (or `/event`) on the local Mosquitto. The dashboard and the agent never care which link it came on.

**"Cell down, alert still arrives" in 2-3 h:** flash Meshtastic via web flasher (https://flasher.meshtastic.org, 10 min) → config both (20 min) → test `sendText` from laptop to the other board (10 min) → serial module + ESP32 UART (40 min) → Pi bridge (30 min) → kill Wi-Fi and verify (20 min).

## 4. Holdup

| Option | Math | Verdict |
|---|---|---|
| **Node on the UPS's 5 V USB out** (Rig A) / its own power bank (Rig B) | Hours | **Use this.** Same as a real install on the device's UPS |
| Heltec V3 + 1S LiPo on its JST 1.25 | 500 mAh at ~100 mA avg ≈ 5 h | **Use this** for the LoRa radio. **Check connector polarity** before plugging; many hobby LiPos are reversed |
| Supercap (1 F, 5.5 V) on the ESP32 5 V rail | t = C·ΔV / I = 1 × 0.7 / 0.2 ≈ 3.5 s before the AMS1117 drops out | Last-gasp message only. Not continued reporting |
| 1S LiPo into a classic ESP32 dev board | AMS1117 dropout (~1 V) leaves ~3.2 V at full charge, then brownouts | Don't. Needs a buck-boost or LDO swap |

Real product: one 18650 + protected charger + low-dropout regulator, Wi-Fi off after mains loss (the router is dead anyway), LoRa-only reporting. Days of runtime.

## 5. Firmware plan

**Recommendation: Arduino core on PlatformIO (C++).** Libraries exist for everything (ld2410, Adafruit_INA219, PubSubClient, ArduinoJson), and the state machine, estimator and LoRa failover are custom logic that is painful in ESPHome lambdas at 3 AM. **ESPHome is the fallback** if radar or MQTT plumbing eats more than an hour (ld2410 + ina219 + adc + mqtt are all built-in YAML). **MicroPython: no** (256000-baud frame parsing and weaker libraries).

**FreeRTOS tasks (classic ESP32, dual core):**

| Task | Core | Rate | Job |
|---|---|---|---|
| `radarTask` | 1 | continuous `radar.read()` | Update presence / moving / still / distances. Debounce absent (10 s) |
| `powerTask` | 1 | 10 Hz | INA219 V, I; ADC mains sense with 300 ms debounce; energy integrator; `est_minutes_left` |
| `netTask` | 0 | event + periodic | Wi-Fi/MQTT non-blocking reconnect. Telemetry every 5 s (mains on) / 2 s (mains off). If MQTT has been down > 10 s or mains just dropped: switch to LoRa (state change + 30 s heartbeat). Keep a 20-entry RAM ring buffer and flush on reconnect |
| loop | 1 | 1 Hz | `esp_task_wdt_reset()`, LED status |

- Watchdog: `esp_task_wdt_init(10, true)`; add each task. Brownout detector stays **on**.
- `client.setBufferSize(512)` for PubSubClient (default 256 truncates JSON).
- MQTT LWT: `lifeline/{home_id}/status` = `offline`, retained. Publish `online` retained on connect.
- Config via `lifeline/{home_id}/config` (capacity Wh, demo mode, still-alert seconds).

**MQTT topic schema:**

| Topic | QoS / retain | When |
|---|---|---|
| `lifeline/{home_id}/telemetry` | 0 / no | every 5 s (2 s on outage) |
| `lifeline/{home_id}/event` | 1 / no | mains_lost, mains_restored, no_motion, absent, battery_low (<15 min) |
| `lifeline/{home_id}/status` | 1 / retained | online / offline (LWT) |
| `lifeline/{home_id}/config` | 1 / retained | hub → node |

**Telemetry payload:**

```json
{"home_id":"H07","ts":1762540000,"mains":false,"battery_v":12.04,"current_a":0.42,
 "power_w":5.06,"est_minutes_left":38,"presence":true,"motion":"still",
 "still_energy":41,"distance_cm":110,"via":"wifi","seq":1832,"fw":"0.1.0"}
```

`motion` ∈ `moving | still | absent`. `battery_v` in Rig A/B is the regulated output voltage (label it `bus_v` if a judge digs in). `ts` from NTP while Wi-Fi works, else `millis()` offset and the hub stamps receive time. `seq` lets the hub dedupe Wi-Fi vs LoRa copies.

## 6. Bill of materials

Fry's Electronics closed in 2021, so it's not an option. Micro Center does not list INA219, LD2410 or Heltec boards (search 2026-11-07). Those come from **Amazon same-day/overnight (order before you leave)**, the HackUTD/MLH hardware lab (ask at check-in), or Tanner Electronics in Carrollton (surplus store, call first [u]). Prices are approximate [u].

| # | Item | Qty | ~Price | Where | Must? |
|---|---|---|---|---|---|
| 1 | HLK-LD2410C mmWave radar (2-3 pack) | 1 pack | $15-20 | Amazon same-day | **MUST** (fallback: PIR from kit) |
| 2 | Heltec WiFi LoRa 32 V3, 915 MHz, with antennas (2-pack) | 2 | $45-60 | Amazon same-day | **MUST** (fallback: ESP-NOW) |
| 3 | INA219 breakout (multi-pack) | 1 pack | $8-12 | Amazon; Adafruit #904 | **MUST** (fallback: shunt + ADC) |
| 4 | Mini DC UPS for router, 12 V in/out + 5 V USB | 1 | $25-45 | Amazon | Rig A |
| 5 | 12 V 2 A barrel adapter + barrel Y-splitter + barrel-to-screw-terminal pigtails | 1 set | $15-20 | Micro Center | **MUST** for Rig A |
| 6 | 12 V 120 mm PC case fan (the "concentrator") | 1 | $5-10 | Micro Center | **MUST** for Rig A |
| 7 | USB power bank that explicitly supports **pass-through charging** | 1 | $20-30 | Micro Center | **MUST** (Rig B baseline + node holdup) |
| 8 | 5 V USB fan/blower + USB-A/USB-C breakout boards | 1 each | $10-15 | Micro Center | **MUST** for Rig B |
| 9 | Switched power strip | 1 | $8-12 | Micro Center | **MUST** (the "outage" switch) |
| 10 | 1S LiPo 500-1000 mAh, JST 1.25 (check polarity) | 1-2 | $8-12 | Amazon / Micro Center hobby aisle | Nice |
| 11 | Travel router (GL.iNet class) | 1 | $25-35 | Micro Center | Optional (else Pi 4 as AP, or phone hotspot) |
| 12 | Resistors 10k/15k/33k, 100 nF, jumper wires, perfboard | assorted | $10 | Micro Center | Likely owned |
| 13 | Seeed MR60BHA2 kit | 1 | $30-40 | Seeed / online only | Post-hackathon |

Known Micro Center IDs from [HackUTD-Research-Firmware-Wiring-Buy](../research/HackUTD-Research-Firmware-Wiring-Buy.md): Inland ESP32 WROOM-32D **613822** ($9.99) if a third ESP32 is needed. Dallas store: 13929 N Central Expy, Sat until 9 PM [u]. Call to confirm stock.

## 7. Hour-by-hour plan (Sat 1:30 PM → Sun 9 AM)

| Time | Rafael does | Done when | Fallback if it slips |
|---|---|---|---|
| 1:30-1:45 | **Order Amazon now**: LD2410C pack, Heltec V3 2-pack, INA219 pack, mini DC UPS (same-day to venue or Locker). Ask the hardware lab for radar/LoRa/INA219 | Orders placed | If no same-day option, Tanner Electronics call; plan Rig B + ESP-NOW |
| 1:45-3:15 | Micro Center run: items 5-9, 12. Test pass-through on the power bank **in the store** if they allow it | Parts in hand | Different bank model; keep receipts |
| 3:15-4:30 | Pi 5 hub: Mosquitto, Python venv (`meshtastic`, `paho-mqtt`), stub dashboard subscribing to `lifeline/#`. Agree topic schema with teammate | `mosquitto_sub -t 'lifeline/#'` shows a hand-published test message | Teammate's agent subscribes to the same broker; schema is the contract |
| 4:30-6:00 | ESP32 PlatformIO skeleton: Wi-Fi + MQTT + LWT + WDT; INA219 + mains divider on Rig B; energy estimator; publish telemetry | Fan current and `mains` flip on the dashboard when you unplug the charger | Arduino IDE single-file sketch, no tasks |
| 6:00-7:00 | Dinner + start 3D prints (node box, mock concentrator) | Printing | Cardboard + tape; judges care about the demo |
| 7:00-8:30 | Radar (when it arrives): wire, ncmreynolds lib, moving/still/absent, no-motion timer. Aim away from fan | Dashboard shows moving → still → absent as a teammate moves | ESPHome ld2410 YAML on the second ESP32 publishing to MQTT. No radar at all: PIR from kit = "motion", label it honestly |
| 8:30-11:00 | LoRa: flash Meshtastic, config both Heltecs, laptop `sendText` test, Serial Module TEXTMSG from ESP32, `lora_bridge.py` on Pi | Wi-Fi off → CSV lands on hub as JSON with `via:"lora"` | Heltec never came: **ESP-NOW** from node ESP32 to second ESP32 on the Pi's USB (no AP needed; long-range mode). Call it "radio fallback link", don't call it LoRa |
| 11:00-12:30 | Failover logic: MQTT down > 10 s or mains lost → LoRa; dedupe by `seq` on hub; ring buffer flush | Flip strip: fan stays on, alert arrives over LoRa in < 5 s | Manual: failover on mains-loss only |
| 12:30-1:30 AM | Rig A swap if UPS arrived: Y-split, 12 V divider, INA219 on 12 V. Start the **full calibration discharge** with logging | Logged Wh number | Stay on Rig B; demo-mode capacity |
| 1:30-3:00 | Integration with teammate: event → agent → Twilio call. Run the full story 3 times | Phone rings from a strip flip | Agent triggers off a hand-published MQTT event |
| 3:00-4:30 | **Sleep** (90 min, one cycle) | | |
| 4:30-6:30 | Assemble into enclosures, cable management, labels, strain relief. Hot glue everything that can fall off | Rig survives being carried | Open-frame on a board with labels |
| 6:30-8:00 | Record a backup demo video. Write the "how a real product would do it" slide (section 1 table) | Video saved locally | |
| 8:00-9:00 | Freeze firmware (git tag). Spare charged power bank, spare ESP32 flashed with the same build | Nothing changes after 8:30 | |

### 3D-printed parts

- **Home node box** (~100 × 70 × 40 mm, PETG or PLA): ESP32 + Heltec on standoffs, LD2410C behind a **1-1.5 mm thin wall window** on the front face (no metal, no wires in front of the radar, ~2 cm clear), Heltec antenna through a top hole (SMA bulkhead or u.FL pigtail), OLED window, USB-C pass-through slot, three LEDs (mains / link / alert). Use a parametric box (Ultimate Box Maker on Printables or an OpenSCAD box) to skip CAD. ~2.5 h print [u].
- **Mock oxygen concentrator** (~150 × 150 × 200 mm, can be printed as a sleeve in two halves or just a front panel on a cardboard box): 120 mm fan grille on the side, a nozzle that takes a short piece of clear tubing as a "cannula", a "flow" LED, a label "Stand-in: 12 V DC". Mini UPS hides in the base. ~3-4 h for panels [u].

## Sources

- INA219 datasheet: https://www.ti.com/lit/ds/symlink/ina219.pdf · Adafruit guide: https://learn.adafruit.com/adafruit-ina219-current-sensor-breakout
- LD2410 Arduino lib: https://github.com/ncmreynolds/ld2410 · ESPHome LD2410: https://esphome.io/components/sensor/ld2410/ · HLK product page: https://www.hlktech.net/index.php?id=1095
- LD2450: https://www.hlktech.net/index.php?id=1157 [u]
- Seeed MR60BHA2: https://wiki.seeedstudio.com/getting_started_with_mr60bha2_mmwave_kit/ · MR24HPC1: https://wiki.seeedstudio.com/Radar_MR24HPC1/
- Meshtastic Serial Module: https://meshtastic.org/docs/configuration/module/serial/ · CLI/Python: https://meshtastic.org/docs/software/python/cli/ · https://github.com/meshtastic/python · Web flasher: https://flasher.meshtastic.org
- Heltec V3 listings: https://ameridroid.com/products/heltec-wifi-lora-32-v3-esp32-sx1262-lora-node-915-mhz · https://store.rokland.com/products/heltec-wifi-lora-32v3
- CT clamps: https://docs.openenergymonitor.org/electricity-monitoring/ct-sensors/ · Shelly API: https://shelly-api-docs.shelly.cloud/
- ESP32 ADC2/Wi-Fi limit and task WDT: https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/peripherals/adc.html · https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/wdts.html
- NUT (read a home UPS over USB): https://networkupstools.org/
