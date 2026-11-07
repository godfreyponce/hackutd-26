---
created: 2026-11-07
status: research
tags: [hackathon, hackutd, lifeline, hardware, sensors]
---
Part of [HackUTD-Lifeline-Hardware](HackUTD-Lifeline-Hardware.md) · clinical basis in [HackUTD-Lifeline-Clinical](HackUTD-Lifeline-Clinical.md).

# Breathing Room: which gas sensors fit the build

Node = classic ESP32 (3.3 V logic, I2C on GPIO21 SDA / GPIO22 SCL, **INA219 already at 0x40**), reporting over MQTT with LoRa fallback. The "oxygen concentrator" is a 12 V fan. `[u]` = unverified (price, stock, delivery). `[est]` = my estimate, not from a datasheet.

## 0. The answer in one screen

- **Skip the O2 sensor.** A real concentrator does not measure room O2 depletion: it barely changes room O2. On our rig the fan blows room air, so an O2 sensor reads a flat 20.9 % all night. Output-purity monitoring needs a 0-100 % cell (~$96) and a real concentrator. Not worth it tonight.
- **Buy CO + CO2/temperature instead.** The clinical note's point holds: CO and indoor temperature cover more real deaths than the battery reading.
- **Tonight's set:** **Sensirion SCD41** (true NDIR CO2 + temperature + RH, I2C 0x62) **+ DFRobot SEN0466** (factory-calibrated electrochemical CO, I2C 0x74). Both run on 3.3 V I2C and share the bus with the INA219. **No address conflicts.**
- **On-stage trigger:** breathe on the SCD41 (CO2 jumps from ~450 to thousands of ppm in seconds). **Never make real CO.** The CO channel is shown live at ~0 ppm and its alarm path is demoed with a labeled test injection.

## 1. What would an O2 sensor actually add?

| Possible use | Physics | Does it fit the real problem? | Does it fit our demo? |
|---|---|---|---|
| **Room O2 depletion** (the patient's air "running out") | A concentrator takes room air, keeps the O2 and vents the N2 back into the room. Net room O2 barely changes: "an oxygen concentrator does not reduce the oxygen in the room air because of the small amount of oxygen required" ([Hackensack Meridian at Home](https://wp.hackensackmeridianhealth.org/meridianathome.com/www.meridianathome.com/MAH/resourcesandtips/OxygenEquipment.html)). In a power outage the patient's problem is *their blood* O2, not the room's. | **No.** The harm comes from the patient no longer getting enriched O2, which a room sensor cannot see. Generator CO kills long before room O2 drops measurably [est]. | **No.** Reads 20.9 % flat. |
| **Room O2 *enrichment*** (fire risk near the concentrator) | OSHA thresholds: < 19.5 % deficient, > 23.5 % enriched ([CO2Meter summary](https://co2meter.com/blogs/news/oxygen-enrichment-hazards)). Enrichment builds up under blankets and near the cannula. | Real, but it is a fire-safety product, not an outage alert. | No. The fan does not enrich anything. |
| **Concentrator output purity** (is the device still delivering 90-95 % O2?) | Concentrators deliver 90-95 % O2 ([CO2Meter](https://co2meter.com/blogs/news/oxygen-enrichment-hazards)). Clinical units already have an internal OCSI purity alarm [est]. Needs a **0-100 %** sensor: the SEN0322 tops out at 25-30 %. | Partly. It shows "O2 flow stopped" directly, which a power reading only infers. | **No.** We have no O2 source. Faking 90 % on stage is dishonest. |
| **Breath demo** | Exhaled air is ~16 % O2 / ~4 % CO2 (textbook physiology [est]). Breathing on the cell drops the reading a couple of points. Response ≤ 15 s (SEN0322 wiki). | n/a | It works, but it is slow and does the same job as the SCD41 breath trick for $54 more. |

**Verdict:** an O2 sensor adds no real signal to "Breathing Room" as built. In a production version it belongs **inside the concentrator line** (0-100 % cell, e.g. DFRobot SEN0496 at $95.90 from [DFRobot](https://www.dfrobot.com/product-2510.html)) as a "flow stopped / purity low" confirmation. Say that in one line to judges. Spend the money and the I2C slot on CO and temperature.

## 2. Options per gas

All supply and logic levels are checked against 3.3 V. **0x40 conflict check:** none of the parts below use 0x40. **But** many cheap temperature/RH boards do (HDC1080, Si7021, HTU21D/SHT21 are fixed at 0x40 [est, from common breakout docs]). **Do not buy those as the temperature sensor.** AHT20/21 (0x38), SHT3x/SHT4x (0x44/0x45) and the SCD41's built-in sensor are fine.

### 2a. Oxygen (for completeness; not recommended tonight)

| Part | Price | Interface / address | 3.3 V? | Warm-up | Calibration | Accuracy | Notes |
|---|---|---|---|---|---|---|---|
| **DFRobot SEN0322** Gravity I2C O2, 0-25 %Vol | $53.90 ([DFRobot](https://www.dfrobot.com/product-2052.html)); RobotShop $67 | I2C, 0x70-0x73 by dial, **default 0x73** (`ADDRESS_3`). Wiki history says only 0x72/0x73 are selectable on some revisions [u] | Yes, 3.3-5.5 V | ~10 min to stabilize (wiki note) | One-point in fresh air = 20.9 % (library `calibrate(20.9)` or a button) | Resolution 0.15 %Vol, repeatability < 2 %, no absolute accuracy given. Life > 2 yr | [Wiki / datasheet](https://wiki.dfrobot.com/Gravity_I2C_Oxygen_Sensor_SKU_SEN0322) · lib `DFRobot_OxygenSensor` |
| **DFRobot SEN0496** O2 0-100 %Vol (AO2 CiTiceL) | $95.90 ([DFRobot](https://www.dfrobot.com/product-2510.html)) | I2C, default 0x70 | Yes, 3.3-5.5 V | ≥ 3 min after removing the seal cap (wiki) | Factory + air | n/a here | The one you'd use for concentrator output purity. [Wiki](https://wiki.dfrobot.com/SEN0496) |
| **Seeed Grove ME2-O2-Ф20** (analog) | ~$40-60 [u] | Analog. ~120 µA cell current × 100 Ω × gain 121 ≈ **1.45 V at 20.9 %** | Yes (onboard XC6206 3.3 V LDO) | Minutes [est] | Read the fresh-air voltage at boot and scale. Cell current varies 80-160 µA unit to unit | Limited by the ESP32 ADC (nonlinear, noisy) [est] | [Seeed wiki](https://wiki.seeedstudio.com/Grove-Gas_Sensor-O2/). Successor MIX8410 uses gain 241 ([wiki](https://wiki.seeedstudio.com/Grove-Gas_Sensor-O2-MIX8410/)). Use ADC1 pins only (Wi-Fi on) |
| DFRobot SEN0465 (factory-calibrated O2, I2C/UART) | ~$50-70 [u] | I2C 0x74-0x77 dial (same family as SEN0466) [u] | Yes | > 5 min, 24 h if stored long (series wiki) | Factory | n/a | [Series wiki](https://wiki.dfrobot.com/SKU_SEN0465toSEN0476_Gravity_Gas_Sensor_Calibrated_I2C_UART). **Same address range as SEN0466**: set different dials if you ever run both |

### 2b. Carbon monoxide (the one that matters)

| Part | Price | Interface / address | 3.3 V? | Warm-up / burn-in | Calibration | Accuracy | Verdict |
|---|---|---|---|---|---|---|---|
| **DFRobot SEN0466** Gravity factory-calibrated electrochemical CO, 0-1000 ppm | ~$40-55 [u] | I2C **0x74 default** (dial, SEL=0 for I2C) or UART 0-3 V. Also a raw analog V0 output (0.6-3 V) | **Yes**, 3.3-5.5 V, < 5 mA | First power-on > 5 min. **24 h recommended** if stored long (series wiki). Forum FAQ says 24 h first use | **Factory calibrated.** Do not run the calibrate command without a standard gas (FAQ) | ±10 % of reading or ±5 % FS, whichever is greater (so ±50 ppm floor). Resolution 1 ppm. T90 ≤ 30 s. Life > 2 yr | **Pick.** Real ppm, no heater, 3.3 V native. [Wiki/specs](https://wiki.dfrobot.com/sen0466/) · [series wiki](https://wiki.dfrobot.com/SKU_SEN0465toSEN0476_Gravity_Gas_Sensor_Calibrated_I2C_UART) · lib `DFRobot_MultiGasSensor` |
| **Winsen ZE07-CO** electrochemical module, 0-500 ppm | ~$20-35 [u] | UART (9600 [u]) or DAC/analog. **No I2C** | **Supply is 5-12 V.** UART logic is 0-3.0 V, so it reads fine on 3.3 V RX. No reverse-polarity protection | ≤ 3 min | Factory | Resolution 0.1 ppm, response ≤ 60 s | Good runner-up. Needs a UART (Serial2 is the radar's, so use a free pin pair) and 5 V. [Datasheet v1.3](https://www.winsen-sensor.com/d/files/PDF/Gas%20Sensor%20Module/CO%20Detection%20Module/ZE07%20CO%20Module%201.3V.pdf) · [manual](https://www.winsen-sensor.com/d/files/manual/ze07-co.pdf) |
| **Seeed Grove Multichannel Gas V2** (GM-102B NO2, GM-302B ethanol, GM-502B VOC, GM-702B CO) | ~$30-40 [u] | I2C **0x08** (STM32 front end) | Yes, 3.3-5 V | Must preheat. Element datasheets cite < 48 h | **None.** Raw counts capped at 999 | Seeed: "can only be used as a result of qualitative measurements and not for quantitative measurements" | **No.** Cannot give ppm, and a CO alarm without ppm is not defensible. [Seeed wiki](https://wiki.seeedstudio.com/Grove-Multichannel-Gas-Sensor-V2/) |
| **MQ-7** (Hanwei MOS, 20-2000 ppm) | ~$3-8 on Amazon [u] | Analog (+ a comparator D-out on modules) | **Heater needs 5 V.** AO swings to ~5 V, so use a 10k/20k divider into ADC1 | **Preheat ≥ 48 h** (datasheet). Needs a heater cycle: **60 s at 5 V (clean), 90 s at 1.4 V (measure)**. A GPIO cannot do this, so add a MOSFET + PWM or a resistor mod | Needs a known-gas Rs/R0 calibration. Cross-sensitive to H2, alcohol | Trend only at best [est] | **No for tonight.** No burn-in time, and readings in the 5 V phase are useless. [Datasheet (SparkFun mirror)](https://sparkfun.com/datasheets/Sensors/Biometric/MQ-7.pdf) · [ESPHome discussion](https://github.com/esphome/feature-requests/issues/159) |

Alarm thresholds to code against (UL 2034 home CO alarm curve, from memory [u]: 70 ppm alarms within 60-240 min, 150 ppm within 10-50 min, 400 ppm within 4-15 min). For the dashboard: **≥ 35 ppm = warn, ≥ 70 ppm = alert, ≥ 150 ppm = critical** [est].

### 2c. CO2 (NDIR / photoacoustic): the safe on-stage trigger

| Part | Price | Address | 3.3 V? | Warm-up | Calibration | Accuracy | Notes |
|---|---|---|---|---|---|---|---|
| **Sensirion SCD41** (photoacoustic NDIR, 400-5000 ppm, + T + RH) | Adafruit 5190 ~$50-80, SparkFun SEN-22396 $74.95 ([SparkFun](https://www.sparkfun.com/products/22396)). Generic Amazon modules ~$15-30 [u] | **0x62** (fixed) | Yes, 2.4-5.5 V | First reading ~5 s after `startPeriodicMeasurement()`. Best accuracy after minutes [est] | **ASC** (needs weekly 400 ppm fresh air) or **FRC** (forced recal to a known value outdoors). FRC/ASC fully restore accuracy ≥ 5 days after assembly (datasheet) | ±(50 ppm + 2.5 %) at 400-1000 ppm; ±(40 ppm + 5 %) at 2001-5000 ppm (per 7Semi copy of the table [u]) | **Pick.** Also gives indoor **temperature** (reads warm from self-heating: set `setTemperatureOffset`). Peak current is high, so feed it a clean 3.3 V rail. [Sensirion datasheet](https://sensirion.com/resource/datasheet/scd40/scd41) · [SparkFun PDF mirror](https://cdn.sparkfun.com/assets/9/7/5/7/0/Sensirion_SCD4x_Datasheet.pdf) · lib `Sensirion I2C SCD4x` |
| Sensirion SCD40 | ~$10 cheaper [est] | 0x62 | Yes | Same | Same | Same, but range only 400-2000 ppm | Fine for a breath demo (it saturates either way). Lacks single-shot mode |

**On-stage trigger:** breathe on the SCD41 from ~10 cm. Exhaled breath is ~4 % CO2 (~40,000 ppm, textbook [est]), so the reading jumps to the top of its range within one or two 5 s measurement cycles and recovers over ~1-2 min [est]. It is visible, safe and honest ("this is a real sensor responding to a real gas").

### 2d. VOC / air-quality (optional; not tonight)

| Part | Price | Address | 3.3 V? | Warm-up | Output | Notes |
|---|---|---|---|---|---|---|
| **Sensirion SGP41** (VOC + NOx index) | Adafruit ~$15-20 [u] | **0x59** | Yes | ~10 s conditioning at start (Adafruit example), then the index algorithm learns. ESPHome default learning time 12 h | Index 1-500, relative to the recent baseline. **Not ppm** | [Adafruit guide](https://learn.adafruit.com/adafruit-sgp41-multi-pixel-gas-sensor-breakout) · [ESPHome sgp4x](https://esphome.io/components/sensor/sgp4x.html) |
| **ScioSense ENS160** (often sold with an AHT21 on the same board) | ~$8-15 on Amazon [u] | **0x53** default (0x52 with ADDR low). AHT21 at 0x38 | Yes | **1 h** initial start-up on first power-up, then **3 min** warm-up each boot ([ESPHome](https://esphome.io/components/sensor/ens160/)) | TVOC ppb, **eCO2 (estimated, not measured)**, AQI 1-5 | [Datasheet](https://cdn.sparkfun.com/assets/3/c/7/5/5/SC-001224-DS-7-ENS160-Datasheet.pdf). Breath raises "eCO2" too, but it's inferred from VOCs. Don't call it CO2 |
| **Bosch BME688** (gas resistance + T + RH + P) | ~$20-35 [u] | **0x76** or 0x77 (SDO pin; board defaults differ: SparkFun BME688 = 0x76, BME680 = 0x77) | Yes | Gas heater stabilises over minutes; BSEC IAQ needs hours to calibrate [est] | Raw gas Ω, or IAQ via Bosch BSEC (closed blob) | [SparkFun hookup guide](https://learn.sparkfun.com/tutorials/sparkfun-environmental-sensor-breakout---bme68x-qwiic-hookup-guide/all) · [Bosch datasheet (Farnell)](https://www.farnell.com/datasheets/4558778.pdf) |

None of these detect CO specifically. A VOC tile would be "air quality" color, not a life-safety signal. Skip.

## 3. Amazon same-day / next-day to Richardson TX (all `[u]`)

I could not check Amazon delivery dates from here: the searches returned no amazon.com listings at all. Treat this as a search plan. Check the "Today/Tomorrow" delivery badge for ZIP **75080** before ordering.

| Pick | Search on Amazon | Likely status [u] | If not same-day |
|---|---|---|---|
| SCD41 (or SCD40) breakout | "SCD41 CO2 sensor module I2C", "SCD40 CO2 sensor" | Generic boards are common, so same-day/overnight is **plausible** [u]. Prefer listings that show the Sensirion part number | Adafruit 5190 / SparkFun SEN-22396 ship 1-3 days. MLH hardware lab. Micro Center Dallas (call) |
| DFRobot SEN0466 | "DFRobot Gravity CO sensor calibrated", "SEN0466" | DFRobot sells on Amazon, but this SKU is often **ship-from-seller, 2-5 days** [u] | **ZE07-CO** ("Winsen ZE07 CO module", UART) if it is same-day. Otherwise run the CO tile with test injection only and say so |
| (if O2 is wanted anyway) SEN0322 | "DFRobot Gravity I2C oxygen sensor" | Unknown [u] | Skip |
| AHT20/21 temp-RH (only if the SCD41 doesn't arrive) | "AHT20 I2C temperature humidity" | Cheap multi-packs, same-day plausible [u] | DS18B20 from a kit (1-Wire on GPIO4) |

## 4. Recommendation for tonight: one set

**SCD41 (CO2 + indoor temperature + RH) + DFRobot SEN0466 (calibrated CO), both on the existing I2C bus.**

Why this set:
- It covers the two killers from the clinical note: **CO** (19 Uri deaths, ~400 Beryl hospitalizations) and **indoor temperature** (158 of 246 Uri deaths were hypothermia).
- **Real units.** ppm CO and °C, not a "gas index", so the "time until harm = min(device, temperature, CO)" clock is defensible.
- 3.3 V native, no heater cycling, no 48 h burn-in, and no new UART (Serial2 is the radar, Serial1 is the Heltec).
- The SCD41 gives a safe live demo (breath). The CO channel stays honest: live reading on screen, alarm path shown with a labeled test.

### Bus map (after adding the set)

| Device | Address | Conflict? |
|---|---|---|
| INA219 | 0x40 | — |
| SCD41 | 0x62 | No |
| SEN0466 | 0x74 (dial A0=0 A1=0, SEL=0) [u: confirm silkscreen] | No |

### ESP32 wiring

```
ESP32 3V3  → SCD41 VDD (VIN)     → SEN0466 VCC (+)   → INA219 VCC
ESP32 GND  → SCD41 GND           → SEN0466 GND (-)   → INA219 GND   (and the 12 V system ground, as before)
ESP32 GPIO21 (SDA) → SCD41 SDA   → SEN0466 pin 1 "SDA/TX" (D)  → INA219 SDA
ESP32 GPIO22 (SCL) → SCD41 SCL   → SEN0466 pin 2 "SCL/RX" (C)  → INA219 SCL
SEN0466 dip switch: SEL = 0 (I2C), A0/A1 = 0/0 → 0x74
```

- Wire by **silkscreen labels**, not cable colors. Gravity and Qwiic cables use different color codes.
- Three breakouts each bring their own pull-ups (~10k each in parallel ≈ 3.3k). That's fine at 100 kHz. Keep the bus wires < 30 cm. Use `Wire.begin(21, 22); Wire.setClock(100000);`.
- If the 3V3 rail sags when the SCD41 measures (its peaks are high [est]), power the SCD41 from the 5 V VIN pin. It accepts 2.4-5.5 V, and most breakouts level-shift or are 5 V-safe on I2C [u: check your board].
- Firmware: `SensirionI2cScd4x` (`startPeriodicMeasurement()`, read every 5 s, `setTemperatureOffset(~2-4 °C)` [est]) and `DFRobot_MultiGasSensor` (`begin()`, `changeAcquireMode(PASSIVITY)`, `readGasConcentrationPPM()`, `setTempCompensation(ON)`). Add `co_ppm`, `co2_ppm`, `temp_c`, `rh` to the telemetry JSON and to the compact LoRa CSV (`c=3,k=612,t=21.4`).
- **Warm-up plan:** power the SEN0466 **as soon as it arrives** and leave it on (it wants > 5 min, ideally 24 h). Ignore CO readings for the first 5 min after boot (`co_valid=false`).

### Demo script for the sensors (safe)

1. Dashboard shows CO 0-3 ppm, CO2 ~450-700 ppm, indoor 22 °C.
2. **Breathe on the SCD41** → CO2 tile spikes live. Line: "Real sensor, real gas."
3. **CO alarm path:** publish a **labeled** test value (`lifeline/{home}/test co_ppm=180`, banner "TEST INJECTION") → ranking jumps, agent calls. Line: "We never make CO on stage. In a home this is the generator-in-the-garage case."
4. **Never** use a flame, a lighter, car exhaust or a candle to trigger CO indoors. A UL-style CO detector test aerosol exists [u], but it is not worth the risk at the venue. Skip it.
5. Optional cold demo: an ice pack against the SCD41 drops "indoor temp" over ~1 min [est]. This is the hypothermia clock.

### Fallback if SEN0466 can't be had tonight

Order a ZE07-CO if one is same-day (5 V supply; its TX → a free GPIO such as 32 or 33 as `Serial`-on-pins, set via the ESP32 UART pin matrix [u]). If not, ship SCD41 alone and show CO as "sensor slot, test injection only". Do not substitute an MQ-7 and call it ppm.

## Sources

- DFRobot SEN0322 wiki: https://wiki.dfrobot.com/Gravity_I2C_Oxygen_Sensor_SKU_SEN0322 · store: https://www.dfrobot.com/product-2052.html
- DFRobot SEN0496 (0-100 % O2): https://wiki.dfrobot.com/SEN0496 · https://www.dfrobot.com/product-2510.html
- DFRobot SEN0466 CO: https://wiki.dfrobot.com/sen0466/ · series SEN0465-0476: https://wiki.dfrobot.com/SKU_SEN0465toSEN0476_Gravity_Gas_Sensor_Calibrated_I2C_UART · I2C list: https://github.com/DFRobot/I2C_Addresses
- Seeed Grove O2 (ME2-O2): https://wiki.seeedstudio.com/Grove-Gas_Sensor-O2/ · MIX8410: https://wiki.seeedstudio.com/Grove-Gas_Sensor-O2-MIX8410/
- Seeed Grove Multichannel Gas V2: https://wiki.seeedstudio.com/Grove-Multichannel-Gas-Sensor-V2/
- Winsen ZE07-CO datasheet: https://www.winsen-sensor.com/d/files/PDF/Gas%20Sensor%20Module/CO%20Detection%20Module/ZE07%20CO%20Module%201.3V.pdf · product page: https://www.winsen-sensor.com/sensors/co-sensor/ze07-co.html
- Hanwei MQ-7 datasheet (mirror): https://sparkfun.com/datasheets/Sensors/Biometric/MQ-7.pdf · ESPHome MQ-7 thread: https://github.com/esphome/feature-requests/issues/159
- Sensirion SCD4x datasheet: https://sensirion.com/resource/datasheet/scd40/scd41 · mirror: https://cdn.sparkfun.com/assets/9/7/5/7/0/Sensirion_SCD4x_Datasheet.pdf · SparkFun SEN-22396: https://www.sparkfun.com/products/22396
- Sensirion SGP41: https://learn.adafruit.com/adafruit-sgp41-multi-pixel-gas-sensor-breakout · https://esphome.io/components/sensor/sgp4x.html
- ScioSense ENS160 datasheet: https://cdn.sparkfun.com/assets/3/c/7/5/5/SC-001224-DS-7-ENS160-Datasheet.pdf · ESPHome: https://esphome.io/components/sensor/ens160/
- Bosch BME688: https://www.farnell.com/datasheets/4558778.pdf · SparkFun BME68x guide: https://learn.sparkfun.com/tutorials/sparkfun-environmental-sensor-breakout---bme68x-qwiic-hookup-guide/all
- Concentrator and room O2: https://wp.hackensackmeridianhealth.org/meridianathome.com/www.meridianathome.com/MAH/resourcesandtips/OxygenEquipment.html · O2 enrichment thresholds: https://co2meter.com/blogs/news/oxygen-enrichment-hazards
