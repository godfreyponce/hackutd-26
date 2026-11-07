---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, embedded, firmware]
---

Part of [HackUTD-2026](../HackUTD-2026.md). Agent research, 2026-11-07. [u] = unverified. Formulas and driver specs are in [HackUTD-Research-Embedded](HackUTD-Research-Embedded.md); this note doesn't repeat them. No firmware code here (MLH rule): only config, wiring and checklists.

## 1. MCU pick: Raspberry Pi Pico (RP2040)

| | Nano/Uno (AVR) | **Pico (RP2040)** | ESP32 dev board |
|---|---|---|---|
| AccelStepper | Works. The author's notes say max speed is "about 4kHz", shared across all motors [u: conditions not stated] | Works (arduino-pico core) | Works |
| FastAccelStepper | 50 kSteps/s, 1–3 steppers | **200 kSteps/s, 4 steppers** | 200 kSteps/s, up to 14 |
| Logic level | 5 V | 3.3 V | 3.3 V |
| USB to Pi | Bridge chip. Opening the port resets the board [u] | **Native USB, no reset when the port opens [u]** | Bridge chip. Resets on open [u] |
| Wokwi simulation | Yes | **Yes** | Stepper page doesn't list it |

**3.3 V logic is fine for all three drivers.** A4988 logic supply is 3–5.5 V. The DRV8825 "can interface directly with 3.3 V and 5 V systems". TMC2209 VIO is 3–5 V [u]. Rule: power the driver's VDD/VIO from the **same rail as the MCU's logic** (Pico 3V3 pin).

**Recommendation: Pico + AccelStepper first.** Switch to FastAccelStepper if 4 motors at 1/16 microstepping stutter. Fallback is an ESP32 with FastAccelStepper. Both cover 4 steppers. AVR is the weak pick for 3–4 axes.

## 2. Toolchain

**PlatformIO (`platformio.ini`):**
- Pico (arduino-pico core, needed for FastAccelStepper on RP2040 [u]):
  - `platform = https://github.com/maxgerhardt/platform-raspberrypi.git`
  - `board = pico`
  - `framework = arduino`
  - `board_build.core = earlephilhower` (required with `board = pico`)
- ESP32: `platform = espressif32`, `board = esp32dev`, `framework = arduino`.
- Libraries (`lib_deps`) [u: registry names]:
  - `waspinator/AccelStepper`
  - `gin66/FastAccelStepper`
  - `teemuatlut/TMCStepper` (only for UART mode)
- First Pico upload: **hold BOOTSEL while plugging in**. Later uploads auto-reset; if the board hangs, repeat BOOTSEL.

**arduino-cli alternative:**
1. Add the board manager URL `https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json` to the CLI config.
2. Run `core update-index`, then `arduino-cli core install rp2040:rp2040`.
3. Find the FQBN with `board listall | grep -i rp2040`. It's probably `rp2040:rp2040:rpipico` [u].

## 3. Which driver do you have, and TMC2209 mode

**Identify it (phone camera, macro):**
- Read the chip marking: "A4988" is Allegro, "DRV8825" is TI, "TMC2209" is Trinamic/ADI.
- Pololu DRV8825 boards are **purple**. The pot is in a different spot from the A4988.
- TMC2209 modules [u]:
  - The chip usually sits on the underside under a cooling pad.
  - Pins are labeled PDN_UART, VIO/VCC_IO, DIAG, INDEX.
  - Max motor voltage is 28 V on BTT's module.
- Pinouts are "nearly identical". Check each pin before swapping one driver for another.

**TMC2209: run it standalone (STEP/DIR/EN).**
- MS1/MS2 straps set microstepping.
- The Vref pot sets current. On BTT modules the default is 1.2 V, about 0.9 A RMS.
- UART needs:
  - one TX/RX line through a 1 kΩ resistor to PDN_UART
  - MS1/MS2 as the address (0–3)
  - TMCStepper
  - a debugging session. One forum user got "no responses" on a v1.3 board.
- **Use UART only if you need software current control or StallGuard homing.** The 24 h clock says no.

## 4. Serial protocol spec (Pi 5 to MCU)

- **Transport:** USB CDC at 115200 8N1. ASCII lines ending in `\n`. Max 48 characters. Discard overlong or unparseable lines and reply `ERR PARSE`.
- **Units:** absolute **microsteps** per axis. The Pi does angle-to-steps; the MCU never sees degrees.

| Pi to MCU | Meaning | MCU reply |
|---|---|---|
| `M <seq> <pan> <tilt> [<turn>]` | New absolute targets | `OK <seq>` or `ERR <seq> LIMIT` (clamped) |
| `H` | Heartbeat | `OK H` |
| `S` | Controlled stop (decelerate) | `OK S` |
| `X` | E-stop: EN high, outputs off | `OK X` |
| `Z` | Set current position as zero | `OK Z` |
| `?` | Status | `ST <pan> <tilt> <turn> <flags>` |

**MCU rules:**
- **Boot:** print `READY <fw-ver>`. Motors stay disabled until the first `M` or `Z`.
- **Watchdog:** if no valid line arrives for **500 ms**, do a controlled stop and set the `TIMEOUT` flag. If none arrives for 2 s, disable outputs. Any valid line clears the flag.
- **Soft limits:** compiled-in min/max per axis. **Clamp every target** to them. The Pi can't widen them.
- **Latest wins:** a new `M` replaces the target mid-move. There's no queue.
- **`<seq>`:** an increasing integer, so the Pi can spot drops and stale acks.

**Pi rules:**
- Send `M` at no more than 30 Hz, and only when the target changes.
- Send `H` at 5 Hz.
- If a reply takes more than 200 ms, log it and resend.
- When the USB port disappears, re-open it, wait for `READY`, then send `Z` or home.

## 5. Wiring checklist (power OFF throughout)

1. Check the PSU label: 12 V, ≥3 A for 2 motors or ≥5 A for 4. Check the barrel polarity (center-positive is typical) with a meter.
2. Bring 12 V to a screw-terminal or barrel-to-terminal adapter. Run a red and black bus along the breadboard rail, separate from the logic rail.
3. Put **≥47 µF electrolytic across VMOT–GND at each driver**, observing polarity.
4. Wire driver GND (motor side) to PSU minus.
5. Wire driver VDD/VIO to Pico 3V3(OUT), and logic GND to Pico GND. **Common ground:** PSU minus, every driver GND and Pico GND are tied together.
6. STEP and DIR from each driver to its own Pico GPIO. EN goes to a shared GPIO, active low.
   - A4988: tie RESET to SLEEP.
   - DRV8825: drive RESET and SLEEP high.
7. Set the microstep straps (MS pins) the same on every driver. Note the values in the README.
8. Find coil pairs with a meter (a few Ω means the same coil). Connect A1/A2 and B1/B2. **Never plug or unplug a motor while powered.**
9. Set Vref with the PSU on and motors disconnected, using a ceramic screwdriver. Then power off.
10. INA219 in series on the 12 V line (high side): VIN+ toward the PSU, VIN– toward the drivers. I2C goes to the Pi. Its range is 26 V / ±3.2 A.
11. Pico USB to Pi 5. The Pico is powered from USB only; never connect 12 V to VSYS.
12. First power-up:
    1. Only one motor connected.
    2. Fingers near the PSU switch.
    3. Feel the driver temperature after 2 minutes.

**Simulate before hardware:**
- **Wokwi** has an A4988 part that pairs with its stepper part, and it supports Pico, Uno and Nano with AccelStepper.
- Wokwi limits:
  - It doesn't use VMOT.
  - It doesn't model coil current.
  - Below half-step, it only shows half-step resolution.
  - There's no DRV8825 or TMC2209 part.
- It's good enough to test the serial protocol and limit logic.
- Fritzing is for diagrams only, not simulation [u].

## 6. Micro Center Dallas (13929 N Central Expy)

**Hours today:** Sat 10 AM–9 PM. Micro Center pages say so in search snippets; I couldn't open them [u].

**Stock:** microcenter.com returned HTTP 403 and a bot check to every fetch. **No stock was confirmed for Dallas.** The prices below come from search-result snippets [u]. Call before driving, or check the site in your own browser with the Dallas store selected.

| Item | MC listing (ID) | Price [u] | Dallas stock |
|---|---|---|---|
| 12 V 5 A barrel PSU | None found | ~$15–25 generic [u]. StarTech SVA12M5NA is $75+ elsewhere | Unconfirmed. Ask the parts desk |
| **Raspberry Pi Pico** (×2) | 661033 / 520767 | $2.99–3.99 | Unconfirmed. A snippet showed Pico 2 "25+ in stock at Dallas", $4.99 |
| ESP32 (Inland WROOM-32D) | 613822 | $9.99 | Unconfirmed |
| Inland Nano / Uno R3 | 615097 / 486544 | $9.99 / $12.99 | Unconfirmed |
| AI HAT+ 26 TOPS | 687348 | Not shown. MSRP $110 | Unconfirmed |
| Pi 5 Active Cooler | 671930 | Not shown (~$10 elsewhere) | Unconfirmed |
| Pi 27 W USB-C PSU | 671926 / 671927 | $11.99 | Unconfirmed |
| INA219 breakout | None found | Adafruit #904 | Unconfirmed |
| TMC2209 module | 649273 (BTT EZ) | "No longer available" | **No**. EZ form factor ≠ StepStick [u] |
| GT2 belt + 20T 5 mm pulley | None found | Adafruit pulley $7.95 | Unconfirmed |
| 5-port gigabit switch (TP-Link) | 693922 / 693931 | $13–25 | Unconfirmed |

**Buy order:** Pico ×2 (one spare), 12 V 5 A PSU, a barrel-to-screw-terminal adapter, a gigabit switch, and the 27 W PSU if you don't own one. Get the AI HAT+ only if it's ≤ $140.

## Sources
- AccelStepper: https://www.airspayce.com/mikem/arduino/AccelStepper/
- FastAccelStepper: https://github.com/gin66/FastAccelStepper
- Pololu A4988: https://www.pololu.com/product/1182 and /faq
- Pololu DRV8825: https://www.pololu.com/product/2133 and /faq
- BTT TMC2209 wiki: https://global.bttwiki.com/TMC2209.html
- TMCStepper: https://github.com/teemuatlut/TMCStepper
- arduino-pico PlatformIO: https://arduino-pico.readthedocs.io/en/latest/platformio.html
- arduino-pico install: https://arduino-pico.readthedocs.io/en/latest/install.html
- PlatformIO pico: https://docs.platformio.org/en/latest/boards/raspberrypi/pico.html
- PlatformIO esp32dev: https://docs.platformio.org/en/latest/boards/espressif32/esp32dev.html
- Wokwi A4988: https://docs.wokwi.com/parts/wokwi-a4988
- Wokwi stepper: https://docs.wokwi.com/parts/wokwi-stepper-motor
- microcenter.com (403 on fetch). Hours, prices and IDs come from search snippets only [u].
