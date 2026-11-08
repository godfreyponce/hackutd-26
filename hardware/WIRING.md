# Wiring: Pi 5 + AI HAT+ box (Sat Nov 7 2026)

Physical pin numbers are on the 40-pin header, reached through the AI HAT+ stacking header.
- **Pin 1** (3.3V) is the header end **farthest from the USB/Ethernet ports**.
- **Odd pins** are in the row toward the middle of the board; **even pins** are along the board edge.

Don't use pins 27/28 (GPIO0/1): the HAT's ID EEPROM uses them. The Active Cooler has its own FAN connector.

## Power rails (share them on a small breadboard or a soldered bus)
| Rail | Pi pins | Feeds |
|---|---|---|
| **3.3V** | 1, 17 | BMP280, MPU-6050, OLED, 2× I2S mic |
| **5V** | 2, 4 | MAX98357A, NeoPixel ring, PIR, 30 mm fan |
| **GND** | 6, 9, 14, 20, 25, 30, 34, 39 | everything |

## Signals
| Part | Part pin | → Pi | GPIO | Notes |
|---|---|---|---|---|
| **BMP280** (temp + pressure) | VCC / GND / SCL / SDA | 3.3V / GND / **5** / **3** | 3 / 2 | I2C 0x76. CSB, SDO unconnected |
| **MPU-6050** (accelerometer) | VCC / GND / SCL / SDA | 3.3V / GND / **5** / **3** | 3 / 2 | I2C 0x68. Same bus |
| **OLED 0.91"** | VCC / GND / SCL / SDA | 3.3V / GND / **5** / **3** | 3 / 2 | I2C 0x3C. Same bus |
| **I2S mic 1** (SPH0645) | 3V / GND / BCLK / LRCL / DOUT / **SEL** | 3.3V / GND / **12** / **35** / **38** / **GND** | 18 / 19 / 20 | SEL→GND = left channel |
| **I2S mic 2** (SPH0645) | 3V / GND / BCLK / LRCL / DOUT / **SEL** | 3.3V / GND / **12** / **35** / **38** / **3.3V** | 18 / 19 / 20 | SEL→3.3V = right channel. DOUT shares pin 38 with mic 1 |
| **MAX98357A** amp | Vin / GND / BCLK / LRC / DIN | **5V** / GND / **12** / **35** / **40** | 18 / 19 / 21 | GAIN, SD unconnected (9 dB, mono mix). Speaker on the + / − screw terminal |
| **NeoPixel ring** | 5V / GND / DIN | 5V / GND / **19** | 10 (SPI MOSI) | **330 Ω** in series on DIN; **470–1000 µF** across 5V/GND at the ring. Not GPIO18 (I2S uses it). Keep brightness ≤30 % |
| **PIR** (HC-SR501) | VCC / OUT / GND | 5V / **11** / GND | 17 | Output is 3.3 V, safe. Jumper H, time knob minimum, 60 s warm-up |
| **30 mm fan** (4-wire) | red 5V / black GND / PWM / tach | 5V / GND / **33** / (opt.) **31** | 13 / 6 | Simplest: red + black only = full speed. PWM on GPIO13 (hardware PWM1) for speed control; tach needs a pull-up |

## Software switches (`/boot/firmware/config.txt`)
- `dtparam=i2c_arm=on`: I2C for the BMP280, MPU-6050 and OLED.
- `dtparam=spi=on`: SPI for the NeoPixel ring on GPIO10.
- I2S: 2 mics + MAX98357A on GPIO18/19/20/21 is the **Google Voice HAT layout**, so `dtoverlay=googlevoicehat-soundcard` should cover the mics and the amp together. **[unverified on the Pi 5: test with `arecord -l` / `aplay -l`]**

## Power budget (45 W supply, 5 V)
| Load | Current |
|---|---|
| Pi 5 + AI HAT+ + camera | ~2–3 A |
| Amp peaks | ~0.6 A |
| NeoPixel ring | ~0.3 A at 30 % |
| Fan + PIR | ~0.2 A |

Total about **3.5–4 A, inside 5 A**. Check `vcgencmd get_throttled` = `0x0` under full load.
