# Radio: NOAA Weather Radio receiver (RTL-SDR on the Pi)

Receive-only. Never transmit on these frequencies (licensed service).

## Hardware
- **RTL-SDR Blog V4** (RTL2832U + R828D tuner), USB ID `0bda:2838`, on the Pi 5 via the 3 ft USB extension.
- **Dipole antenna:** each arm about **46 cm** (¼ wave at 162 MHz), mounted **vertically** (NOAA is vertically polarized), near a window.

## What we measured (Green Hall, Sat Nov 7 2026)
| Setup | Result |
|---|---|
| Rods fully extended, 50° V | Nothing on any NOAA channel. FM only +9 dB |
| Rods ~46 cm | **162.400 MHz at +10 dB**. Audio recorded, voice audible (confirmed by Rafael) |
| Data link | `rtl_test`: 2.048 MS/s, 7 samples per million lost |

**162.400 MHz is the station received at UTD.** The other 6 channels are empty here. Signal is weak indoors (concrete and steel), so the demo also needs the fallbacks below.

## Setup (done on `rafhost`)
```bash
sudo apt-get install -y rtl-sdr multimon-ng sox
echo 'blacklist dvb_usb_rtl28xxu' | sudo tee /etc/modprobe.d/blacklist-rtl.conf   # stop the TV driver claiming the stick
```
The tools detach the TV driver on their own even before a reboot ("Detached kernel driver").

## Usage
```bash
hardware/radio/noaa.sh scan            # dB above noise on all 7 NOAA channels
hardware/radio/noaa.sh record 60       # 60 s of 162.400 MHz audio to a WAV
hardware/radio/noaa.sh decode          # live SAME alert decoding (prints ZCZC-... when an alert airs)
hardware/radio/noaa.sh fm              # sanity check: strongest FM stations
```

## How it works
- **`rtl_test`:** identifies the stick and checks the sample stream.
- **`rtl_power`:** sweeps a frequency range and logs power per step. That's how the scan finds which channel is live.
- **`rtl_fm -M fm`:** tunes one channel and demodulates narrow FM to 22.05 kHz audio. `-E deemp` applies de-emphasis; `-l 0` keeps the squelch open.
- **`sox`:** writes that raw audio to a WAV.
- **`multimon-ng -a EAS`:** decodes the SAME/EAS AFSK header (`ZCZC-ORG-EEE-PSSCCC...`) that starts every official alert. Parsing those fields into hub alert events is in `docs/research/` (PR #29).

## Demo plan (closed building)
1. **Live radio** when there's signal (window or vertical antenna).
2. **Internet fallback** (NWS API) when there isn't, with the source shown on screen.
3. **A recorded real broadcast** from tonight (`~/land/recordings/` on the Pi), fed through the same decoder.
4. **A labelled test alert** through the decoder. TODO: generator.
