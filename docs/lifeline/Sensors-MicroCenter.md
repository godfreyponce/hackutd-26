# Micro Center gas / O2 sensor check (Lifeline, HackUTD 2026-11-07)

**Cheapest in-stock O2 sensor: none.** Micro Center does not list any O2 sensor module (no DFRobot SEN0322/SEN0496, no Grove ME2-O2) — buy O2 online or borrow one; nothing to pick up today.
**Cheapest in-stock CO sensor: none as a bare module.** No MQ-7 or Grove/DFRobot CO board is listed; the only CO sensing is the BME688 on the Pimoroni Enviro Indoor kit (indirect, VOC-type reading, not calibrated ppm) or the MQ-2 in the Inland Smart Home Kit (combustible gas, not CO).
**Stock counts: all UNVERIFIED.** microcenter.com sits behind a Cloudflare bot check that blocked both curl and the browser, so every price and stock figure below comes from search-engine snapshots, not the live store page. Call the store or check the app before driving there.

- **Checked:** 2026-11-07, ~14:15–14:30 CT (search-indexed data only).
- **Store:** Micro Center has no separate Richardson store. The DFW store is "Dallas" at 13929 N Central Expy, Dallas TX 75243 (just south of Richardson, ~10 min from UTD). Store ID 131 (unverified). Use `?storeid=131` on any product URL to see its stock.
- "unverified" = not seen on a live microcenter.com page today.

| # | Product | MC SKU | Price | Stock at Dallas (75243) | Measures | Interface | Supply / 3.3 V ESP32 OK? | URL |
|---|---|---|---|---|---|---|---|---|
| 1 | DFRobot Gravity O2 sensor (SEN0322 / SEN0496) | — | — | not carried | O2 % vol (electrochemical) | I2C | 3.3–5 V / yes | not carried |
| 2 | Seeed Grove ME2-O2 (Grove O2 sensor) | — | — | not carried | O2 % (electrochemical, analog) | analog | 3.3–5 V / yes | not carried |
| 3 | MQ-7 CO module / Grove or DFRobot CO | — | — | not carried | CO ppm | analog (+DO) | 5 V heater / needs 5 V supply; divide AO to ≤3.3 V | not carried |
| 4 | Pimoroni Enviro Indoor (Pico W) — BME688 | unverified | unverified | unverified | temp, RH, pressure, gas resistance (VOC, CO, H2 as an index — not ppm) | I2C (Pico W board; BME688 on I2C) | 3.3 V / yes (or use Pico W itself) | https://www.microcenter.com/product/660381/pimoroni-enviro-indoor-(pico-w-aboard)-enviro-indoor-accessory-kit |
| 5 | Sensirion SCD40/41 NDIR CO2 (any brand) | — | — | not carried | CO2 ppm (true NDIR/photoacoustic) | I2C | 2.4–5.5 V / yes | not carried |
| 6 | MH-Z19 NDIR CO2 | — | — | not carried | CO2 ppm | UART / PWM | 5 V supply, 3.3 V UART / yes with 5 V rail | not carried |
| 7 | Adafruit SGP30 Air Quality Breakout (STEMMA QT) | 212001 | $17.99 (unverified) | unverified ("limited availability" on snapshot) | TVOC ppb + eCO2 ppm (estimated, not NDIR) | I2C | 3.3–5 V / yes | https://www.microcenter.com/product/631790/adafruit-industries-sgp30-air-quality-sensor-breakout-voc-and-eco2-stemma-qt-qwiic |
| 8 | Inland CCS811 Air Quality Sensor Module | unverified | unverified | unverified | TVOC + eCO2 (estimated) | I2C | 3.3 V / yes | https://www.microcenter.com/product/632703/inland-ccs811-air-quality-sensor-module |
| 9 | Adafruit BME680 (temp/RH/pressure/gas) | 007740 | $22.49 (unverified) | unverified ("limited availability") | temp, RH, pressure, VOC gas resistance | I2C / SPI | 3.3–5 V / yes | https://www.microcenter.com/product/613619/adafruit-industries-bme680-temperature,-humidity,-pressure-and-gas-sensor (older listing: /product/503901/) |
| 10 | SGP40 / SGP41 / ENS160 / standalone BME688 | — | — | not carried | VOC index / NOx / eCO2 | I2C | 3.3 V / yes | not carried |
| 11 | Inland Smart Home Kit w/ PLUS Board (KS0085) — includes MQ-2 ("WQ-2") gas sensor | unverified | unverified | unverified | combustible gas / smoke (LPG, propane, H2, CH4); slight CO response, not ppm | analog + digital | 5 V heater / needs 5 V; divide AO for ESP32 ADC | https://www.microcenter.com/product/632699/inland-smart-home-kit-w-plus-board |
| 12 | Inland 37 Assorted Sensors Kit (37IN1SENSORS) | 900852 | unverified | unverified | assorted (flame, DHT11-type temp/RH, IR, tilt…); **no MQ gas sensor** in listed contents | digital / analog | 3.3–5 V / mostly yes | https://www.microcenter.com/product/603752/inland-37-assorted-sensors-kit-for-arduino-and-raspberry-pi |
| 13 | Adafruit BME280 I2C/SPI Temp/Humidity/Pressure | 007625 | $19.95 (unverified) | unverified (one snapshot showed out of stock) | temp, RH, pressure | I2C / SPI | 3.3–5 V / yes | https://www.microcenter.com/product/613614/adafruit-industries-bme280-i2c-spi-temperature-humidity-pressure-sensor |
| 14 | Pimoroni Multi-Sensor Stick (BME280 + LTR559 + LSM6DS3) | unverified | unverified | unverified | temp, RH, pressure, light, IMU | I2C | 3.3 V / yes | https://www.microcenter.com/product/694656/pimoroni-multi-sensor-stick-(bme280-ltr559-lsm6ds3) |
| 15 | DHT22 (standalone) | — | — | not carried (only inside Adafruit Azure IoT Starter Kit) | temp, RH | 1-wire digital | 3.3–5 V / yes | not carried |
| 16 | 4-in-1 Natural Gas Leak + CO Detector (consumer unit, not a module) | 934893 | unverified | unverified | natural gas, CO, temp, RH (alarm, no data out) | none (standalone alarm) | battery/mains / no data link | https://www.microcenter.com/product/702354/4-in-1-natural-gas-leak-detector-and-carbon-monoxide-detectors |

## Notes for the build

- **O2 and CO are the gaps.** Micro Center will not cover either one with a real sensor today. If the demo needs them, simulate them on the ESP32 (scripted values) and say so in the pitch, or source a DFRobot SEN0322 (I2C, ~3.3 V friendly) / MQ-7 from another vendor.
- **Best Micro Center pick for "air quality" today:** BME680 ($22.49, I2C, 3.3 V) gives temp + RH + pressure + a VOC gas reading in one board. SGP30 ($17.99) is cheaper for VOC/eCO2 only. Neither gives real CO2 or CO ppm.
- **MQ-series on a 3.3 V ESP32:** the heater needs 5 V (~150 mA). Power from VIN/5V and put a divider (e.g. 10k/20k) on AO before the ESP32 ADC.
- "not carried" = no microcenter.com listing found via site-restricted search. It was not confirmed against the live catalog because of the Cloudflare block.
