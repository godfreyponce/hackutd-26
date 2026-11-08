---
created: 2026-11-07
status: research
tags: [hackathon, hackutd, research, alerts, sdr, same, cap, noaa]
---
# Research: emergency alerts over the air with our SDR

Part of [HackUTD-2026](../HackUTD-2026.md). Builds on [HackUTD-Research-Disaster-Alert-Feeds](HackUTD-Research-Disaster-Alert-Feeds.md). Agent research, Sat 2026-11-07 evening. [u] = unverified. **Stretch goal.** The core check-in loop comes first (NVIDIA mentor: "focus on one thing").

## For Rafael (5 lines)
1. Our radio listens to NOAA Weather Radio station **KEC56, Dallas, 162.400 MHz**. It covers Dallas County (SAME code 048113) and Collin County (048085). Richardson is in both.
2. On the air there is **no CAP**. There is a voice broadcast plus short digital bursts called **SAME headers**. We decode the header and build a CAP-shaped `alert` ourselves.
3. Chain on the Pi: SDR stick, `rtl_fm` (FM demodulator), `samedec` (SAME decoder), our small script, the hub.
4. The weekly on-air test is on **Wednesday**, so none happens during the hackathon. We test with recorded and generated SAME audio files instead. I ran this whole chain on a laptop with a file and it worked.
5. **Receive only. Never transmit, and never play SAME tones out loud.** The demo alert is fake and never calls 911.

## Setup steps at the table
Do these on the Pi 5 (Raspberry Pi OS 64-bit). Run each command from the repo root unless the step says otherwise.

1. **Check the box.** Read the brand and model name on the SDR box (see [Which SDR we have](#which-sdr-we-have)). Note the antenna connector (SMA or MCX) and which antennas came with it.
2. **Plug in.** Put the stick on the 3 ft USB extension, then into a Pi USB port. Keep the stick away from the Pi, the AI HAT+ and the fan.
3. **Block the TV driver** so it does not grab the stick. The Debian build also detaches it on its own, so this is a safety step (source: [RTL-SDR Blog V4 guide](https://www.rtl-sdr.com/V4)). Then reboot.
   ```bash
   echo 'blacklist dvb_usb_rtl28xxu' | sudo tee --append /etc/modprobe.d/blacklist-dvb_usb_rtl28xxu.conf
   sudo reboot
   ```
4. **Install the radio tools.** This gives `rtl_fm` and `rtl_test` ([Debian package](https://packages.debian.org/bookworm/rtl-sdr)).
   ```bash
   sudo apt update && sudo apt install -y rtl-sdr sox
   ```
   Check the OS with `cat /etc/os-release`. If the box says **RTL-SDR Blog V4** and the OS is **Bookworm**, stop and ask: Bookworm's rtl-sdr 0.6.0 predates V4 support. **Trixie** ships rtl-sdr 2.0.2, and osmocom rtl-sdr added V4 support in 2023, so Trixie should be fine ([V4 guide](https://www.rtl-sdr.com/V4), [osmocom commits](https://github.com/osmocom/rtl-sdr/commits/master)).
5. **Test the stick.** Press Ctrl+C after a few seconds.
   ```bash
   lsusb
   rtl_test
   ```
   `rtl_test` should print "Found Rafael Micro R820T tuner" (it says that for the R820T2 and R860 too). If it says "usb_claim_interface error", another program holds the stick. Run `pkill rtl_fm` and retry. Steps 7 and 12 cannot run at the same time.
6. **Set up the antenna.** Use the telescopic dipole if the kit has one. Pull each arm to about **46 cm** (a quarter wave at 162.4 MHz is 299.8 / 162.4 / 4 = 0.46 m). Stand it vertical [u: NWR polarization]. Put it outside the carbon-fibre shell and near a window if you can.
7. **Listen for 20 seconds.** You should hear a computer voice reading the weather. Copy `nwr.wav` to a laptop and play it. (The Pi 5 has no headphone jack.)
   ```bash
   timeout 20 rtl_fm -f 162.400M -M fm -s 22050 -E dc - | sox -t raw -r 22050 -e signed -b 16 -c 1 - nwr.wav
   ```
   Only hiss: move the antenna, then try a fixed gain such as `-g 30` or `-g 40` after `-E dc`. Still nothing: try **162.550 MHz** (KEC55, Fort Worth).
8. **Install samedec** (prebuilt binary from the [sameold releases](https://github.com/cbs228/sameold/releases), version 0.4.2).
   ```bash
   curl -L -o samedec https://github.com/cbs228/sameold/releases/download/samedec-0.4.2/samedec-aarch64-unknown-linux-gnu && chmod +x samedec && sudo mv samedec /usr/local/bin/
   samedec --version
   ```
9. **Prove the decoder with a real recording.** Download a sample from the sameold repo and decode it.
   ```bash
   curl -L -o svr.bin https://raw.githubusercontent.com/cbs228/sameold/develop/sample/two_and_two.22050.s16le.bin
   samedec -r 22050 --file svr.bin
   ```
   Expected output (I got this on a laptop):
   ```
   NNNN
   ZCZC-WXR-SVR-012079-013019-013027-013075-013185-013173+0130-0462024-N0C4LL  -
   ```
10. **Make the hub venv** if it is not there yet (from `software/hub/README.md`; Pi OS has no python3.12, so use its python3).
    ```bash
    python3 -m venv .venv && .venv/bin/pip install -r software/hub/requirements.txt
    ```
    Then **save the two scripts** from [Script 1](#script-1-same_to_alertpy) and [Script 2](#script-2-make_samepy) as `same_to_alert.py` and `make_same.py` in the repo root on the Pi. Do not commit them yet; they belong in a code ticket.
11. **Make our own demo burst and send it to the hub.** Start the hub first (`.venv/bin/python -m software.hub --sim`). Then:
    ```bash
    python3 make_same.py demo.raw 'ZCZC-WXR-TOR-048113-048085+0030-3112300-HACKDEMO-'
    SEND=1 samedec -r 22050 --file demo.raw -- .venv/bin/python same_to_alert.py
    ```
    The `alert` shows up in `.venv/bin/python -m software.hub.tap`. The headline starts with "DEMO ONLY, NOT A REAL ALERT".
12. **Go live** (leave it running). A real SAME header on 162.400 MHz for Dallas County, Collin County, or the whole nation now becomes an `alert` on the hub. Headers for other counties are dropped (KEC56 serves about 12 counties).
    ```bash
    rtl_fm -f 162.400M -M fm -s 22050 -E dc - | SEND=1 samedec -r 22050 -- .venv/bin/python same_to_alert.py
    ```

## 1. What is on the air, and what is CAP
**NOAA Weather Radio (NWR).** NWS runs VHF FM stations on seven channels from 162.400 to 162.550 MHz. Each one plays a looping voice broadcast. When NWS issues a warning, the station sends a SAME header before the voice message.

**SAME** (Specific Area Message Encoding) is the EAS digital header in [47 CFR 11.31](https://www.law.cornell.edu/cfr/text/47/11.31):
- Format: `ZCZC-ORG-EEE-PSSCCC+TTTT-JJJHHMM-LLLLLLLL-`.
- `ORG` is the originator: `EAS` (EAS Participant, a broadcaster), `CIV` (civil authorities), `WXR` (National Weather Service), `PEP` (United States Government).
- `EEE` is the event code, for example `TOR` (Tornado Warning), `SVR`, `FFW`, `EQW` (Earthquake Warning), `CEM` (Civil Emergency Message), `RWT` (Required Weekly Test).
- `PSSCCC` is a location: P is a county part (0 = all or unspecified), SS the state, CCC the county (FIPS). Up to 31 locations.
- `+TTTT` is the valid time, in 15 minute steps up to one hour, then 30 minute steps.
- `JJJHHMM` is the day of the year and the UTC time of issue. No year.
- `LLLLLLLL` is the sending station, for example `KFWD/NWS`.
- Sent as AFSK at 520.83 bits per second, mark 2083.3 Hz, space 1562.5 Hz. The header goes three times. Then a tone, the voice message, and the end code `NNNN` three times. EAS uses the 853 Hz plus 960 Hz Attention Signal. NWR uses a 1050 Hz Warning Alarm Tone, and only for some products ([NWS](https://www.weather.gov/nwr/nwr_warning)).
- Event code list: [NWS NWR event codes](https://www.weather.gov/nwr/eventcodes) and Table 2 in 11.31.

**EAS** uses the same SAME headers on broadcast radio and TV audio. A DFW FM station that relays an alert carries the header too, and the SDR can tune FM broadcast. We did not check which DFW station is the EAS source for our area [u]. NWR is the simpler target.

**CAP** (Common Alerting Protocol, [OASIS CAP 1.2](http://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html)) is **XML sent over the internet**. It is not on the radio.
- FEMA [IPAWS](https://www.fema.gov/emergency-managers/practitioners/integrated-public-alert-warning-system) takes CAP from alerting authorities and sends it out on several paths.
- NWS publishes CAP 1.2 alerts on [api.weather.gov](https://www.weather.gov/documentation/services-web-alerts), in the IPAWS profile.
- EAS stations turn CAP into SAME before they broadcast it ([47 CFR 11.56](https://www.law.cornell.edu/cfr/text/47/11.56), which adopts the ECIG CAP to EAS guide).
- NWS says its CAP messages "MUST NOT be used as input into EAS encoder/decoder boxes" and that EAS activation should use the NWR SAME audio ([NWS alerts web service](https://www.weather.gov/documentation/services-web-alerts)).

So: **the radio gives us SAME. We build a CAP-shaped event from it.** Never say "CAP over the air".

**Other on-air alerts.** Wireless Emergency Alerts go to phones over LTE and 5G cell broadcast. An RTL-SDR cannot practically decode them [u]. Skip.

### Our local station
| | Value | Source |
|---|---|---|
| Station | **KEC56, Dallas, 162.400 MHz**, 1040 W, about 7 miles from UTD, status NORMAL tonight | [NWS NWR station list for Texas](https://www.weather.gov/nwr/stations?State=TX), also [Broadcastify](https://www.broadcastify.com/listen/feed/46832) |
| Backup | KEC55, Fort Worth (Crowley), 162.550 MHz, about 50 miles away, so beyond the usual range indoors | same NWS list, [Broadcastify](https://www.broadcastify.com/listen/feed/42343) |
| Frequencies for Dallas County (048113) | 162.400, 162.550 | [NWS Fort Worth radio info](https://www.weather.gov/fwd/radioinfo) |
| Frequencies for Collin County (048085) | 162.400, 162.550, 162.475, 162.500 | same page |
| Range | "typically ... 40 miles" | same page |
| Weekly test | "each Wednesday between 10 and Noon (typically around 11 am) and again between 6 pm and 8 pm (typically around 7 pm)". Postponed for severe weather. | [NWS Fort Worth schedule](https://www.weather.gov/fwd/radiosch) |

KEC56 had outages in 2019 and 2021 (NWS statements, [2019](https://mesonet.agron.iastate.edu/api/1/nwstext/201904180831-KFWD-NOUS44-PNSFWD), [2021](https://mesonet.agron.iastate.edu/api/1/nwstext/202104240045-KFWD-NOUS44-PNSFWD)). The NWS list shows NORMAL tonight. Step 7 is the real check.

**The next weekly test is Wed Nov 11, 2026, after the hackathon.** A test postponed for weather moves to "the next available good weather day", so one could fall on the weekend, but do not plan on it. Non-weather codes (CEM, CAE and others) can also air at any time.

## Which SDR we have
**Not certain.** The receipt says Micro Center SKU 051086, "NPD", $59.99 (`docs/HackUTD-Shopping-List.md`). Issue #11 says "likely Nooelec NESDR, SMA antenna". Micro Center blocks automated lookups, so I could not match the SKU. Nooelec's own SKU for the NESDR SMArt v5 is 100701, so the number does not settle it.

If it is a **Nooelec NESDR SMArt v5** ([product page](https://www.nooelec.com/store/sdr/sdr-receivers/nesdr-smart-sdr.html)): RTL2832U plus R820T2 or R860 tuner, 0.5 ppm TCXO, SMA female input. The stick alone has no antenna. The "v5 Bundle" adds 3 antennas. It uses the normal rtl-sdr driver [u: Nooelec does not say this outright, but the chips are the standard ones].

Check on the box:
1. Brand and model (NESDR SMArt v5, NESDR Mini, NESDR Nano, RTL-SDR Blog V4, other).
2. Tuner chip: R820T, R820T2 or R860 is fine. **R828D or "RTL-SDR Blog V4" needs the special driver** ([V4 guide](https://www.rtl-sdr.com/V4)).
3. Connector: SMA or MCX. It decides the case hole and any adapter.
4. Antennas in the box. A telescopic dipole is best for 162 MHz.
5. A "Ham It Up" upconverter or "HF bundle" is for shortwave. We do not need it.

## 2. Receive chain on the Pi 5
`antenna -> SDR stick -> rtl_fm (FM to audio) -> samedec (SAME to text) -> same_to_alert.py (text to JSON) -> hub`

| Part | Choice | Why |
|---|---|---|
| Driver and `rtl_fm` | Debian `rtl-sdr` package. Bookworm has 0.6.0, Trixie has 2.0.2 | Ships a udev rule but no TV driver blacklist, so step 3 adds it ([bookworm file list](https://packages.debian.org/bookworm/arm64/librtlsdr0/filelist)) |
| SAME decoder | **samedec 0.4.2** ([README](https://github.com/cbs228/sameold/tree/develop/crates/samedec)) | Prebuilt arm64 binary. Runs a child program per message with the header already parsed into `SAMEDEC_*` variables. Tested here. |
| Fallback decoder | `multimon-ng -t raw -a EAS /dev/stdin` (in Debian) | Its EAS demodulator needs 22050 Hz input (`FREQ_SAMP 22050` in [demod_eas.c](https://github.com/EliasOenal/multimon-ng/blob/master/demod_eas.c)). Not tested here. dsame's README says it "will not decode the same alert in succession". |
| Skip | dsame | Python 2.7 era. I suspect a bytes and str bug on Python 3 [u: not run]. |

`rtl_fm` flags in steps 7 and 12 ([rtl_fm.c](https://github.com/osmocom/rtl-sdr/blob/master/src/rtl_fm.c)): `-f` frequency, `-M fm` mode, `-s 22050` output rate, `-E dc` DC blocker, `-g` gain in dB (default automatic), `-p` PPM correction (default 0). The samedec README uses `-s 48k -o 4 -g 0 -F 9`. I left out `-o` because rtl_fm prints "Warning: -o is very buggy". The `-s 22050` rate is what dsame's [rtl_fm script](https://github.com/cuppa-joe/dsame/blob/master/scripts/source-rtl-fm-multimon-ng.sh) uses, so the same audio also feeds multimon-ng. samedec takes any rate if `-r` matches.

Pi 5 gotchas:
- The TV driver (`dvb_usb_rtl28xxu`) grabs the stick unless blacklisted (step 3).
- RTL-SDR Blog V4 does not work right with the Debian package ([V4 guide](https://www.rtl-sdr.com/V4)).
- No headphone jack on the Pi 5. Check audio by recording a file (step 7).
- PPM: the SMArt v5 TCXO is 0.5 ppm, about 80 Hz at 162 MHz. No correction needed.
- Keep the stick on the extension cable, away from the Pi and HAT. A generic tip from the RTL-SDR quick start: wavy noise can mean a weak USB port.
- The antenna must be outside the carbon-fibre shell. Test reception inside ECSW early; buildings block VHF.

## 3. SAME to our hub `alert`
The hub contract (`software/hub/README.md`, issue #19) has:
`{"type":"alert","source":"noaa|nws|usgs|gdacs|sensor","event":"...","severity":"...","urgency":"...","certainty":"...","area":"...","headline":"..."}`

samedec sets these for each message ([README](https://github.com/cbs228/sameold/tree/develop/crates/samedec)): `SAMEDEC_MSG` (full header), `SAMEDEC_ORG`, `SAMEDEC_ORIGINATOR` (readable), `SAMEDEC_EVT` (code), `SAMEDEC_EVENT` (readable), `SAMEDEC_SIGNIFICANCE` (T, S, E, A, W), `SAMEDEC_LOCATIONS` (space separated), `SAMEDEC_ISSUETIME` and `SAMEDEC_PURGETIME` (UNIX time, can be empty), `SAMEDEC_IS_NATIONAL`.

| Hub field | From SAME | Rule |
|---|---|---|
| `type` | | always `alert` |
| `source` | | always `noaa` (already in the contract) |
| `event` | EEE | `SAMEDEC_EVENT`, for example "Tornado Warning" |
| `severity` | none | our default by significance (table below) |
| `urgency` | none | our default by significance |
| `certainty` | none | our default by significance |
| `area` | PSSCCC | county names from a small lookup; unknown codes stay as numbers |
| `headline` | EEE, PSSCCC, ORG | built by us. Prefix "DEMO ONLY, NOT A REAL ALERT" for our generated files (station `HACKDEMO`) and "TEST, NOT A REAL ALERT" for tests |

Severity defaults. **SAME has no severity, urgency or certainty.** These are our choice. They copy what NWS CAP used on 2026-11-07 for the same kinds of message (I pulled all active alerts from api.weather.gov): watches were Severe, Future, Possible; warnings were Severe with Immediate or Expected and Observed or Likely; the test message was Unknown for all three.

| Significance | Example codes | severity | urgency | certainty |
|---|---|---|---|---|
| W Warning | TOR, SVR, FFW, EQW, CEM | Severe | Immediate | Likely |
| E Emergency | CAE, LAE | Severe | Immediate | Likely |
| A Watch | TOA, SVA, FFA | Severe | Future | Possible |
| S Statement | SVS, SPS | Moderate | Expected | Likely |
| T Test | RWT, RMT, NPT | Unknown | Unknown | Unknown |

samedec rates **DMO** (Practice/Demo Warning) as a Warning, so Script 1 marks it "DEMO ONLY" by its code. Script 1 also drops any header that names neither 048113 nor 048085 and is not national.

For the full CAP picture, other fields map like this. NWS CAP carries the SAME values in `eventCode` SAME, `geocode` SAME and `parameter` EAS-ORG (seen in tonight's api.weather.gov data).
| CAP field | SAME source |
|---|---|
| `info.eventCode` SAME | EEE |
| `info.area.geocode` SAME | PSSCCC |
| `info.parameter` EAS-ORG | ORG |
| `sent` | JJJHHMM (no year; samedec guesses it) |
| `info.expires` | issue time + TTTT. samedec warns this is the message expiry, not how long the hazard lasts |
| `sender` (partly) | LLLLLLLL |
| `status` | only implied: Test for RWT, RMT, NPT; Exercise for DMO |
| **No SAME source** | `identifier`, `msgType` (no Update or Cancel), `scope`, `category`, `severity`, `urgency`, `certainty`, `headline`, `description`, `instruction` (spoken only, not text), `areaDesc` (needs a lookup), `polygon`, `onset`, `web`, `contact` |

Example. Header `ZCZC-WXR-TOR-048113-048085+0030-3112300-HACKDEMO-` becomes:
```json
{"type": "alert", "source": "noaa", "event": "Tornado Warning", "severity": "Severe", "urgency": "Immediate", "certainty": "Likely", "area": "Dallas County, TX; Collin County, TX", "headline": "DEMO ONLY, NOT A REAL ALERT: Tornado Warning for Dallas County, TX; Collin County, TX (National Weather Service)"}
```
That is the real output of Script 1, and the hub's `tap` printed it (plus its `t` stamp) when I ran the hub on test ports.

Not in the contract, and not added here: `expires`, the raw header, a `status` field. Any of those is a contract change, so it goes to issue #19 first. Open point for the agent owner (#15): should a TEST `alert` start a check-in? It probably should not.

### Script 1: `same_to_alert.py`
samedec runs it once per message. It prints the JSON. With `SEND=1` it also sends it with the hub's own `software.hub.send`, so it must run from the repo root with the hub's venv.
```python
"""samedec child: turn one decoded SAME header into a hub `alert` event.

samedec runs this once per message and passes the header in SAMEDEC_*
environment variables. Prints the JSON line, then sends it with the hub's
send tool if SEND=1. Drops headers for other counties. samedec streams the
message audio on stdin; we drain it.
"""

import json
import os
import subprocess
import sys

# Our defaults by SAME significance letter. Not a standard: chosen to match
# what NWS CAP used for watches, warnings and tests on 2026-11-07.
CAP_BY_SIG = {
    "W": ("Severe", "Immediate", "Likely"),     # Warning
    "E": ("Severe", "Immediate", "Likely"),     # Emergency
    "A": ("Severe", "Future", "Possible"),      # Watch
    "S": ("Moderate", "Expected", "Likely"),    # Statement
    "T": ("Unknown", "Unknown", "Unknown"),     # Test
}
COUNTIES = {"048113": "Dallas County, TX", "048085": "Collin County, TX"}
DEMO_STATION = "HACKDEMO"


def is_ours(env: dict) -> bool:
    codes = set(env.get("SAMEDEC_LOCATIONS", "").split())
    return bool(codes & COUNTIES.keys()) or env.get("SAMEDEC_IS_NATIONAL") == "Y"


def alert_from_env(env: dict) -> dict:
    sig = env.get("SAMEDEC_SIGNIFICANCE", "")
    severity, urgency, certainty = CAP_BY_SIG.get(sig, ("Unknown",) * 3)
    codes = env.get("SAMEDEC_LOCATIONS", "").split()
    area = "; ".join(COUNTIES.get(c, c) for c in codes)
    event = env.get("SAMEDEC_EVENT", "Unknown")
    headline = f"{event} for {area} ({env.get('SAMEDEC_ORIGINATOR', '')})"
    # samedec rates DMO (Practice/Demo Warning) as a Warning, so check it here.
    if DEMO_STATION in env.get("SAMEDEC_MSG", "") or env.get("SAMEDEC_EVT") == "DMO":
        headline = "DEMO ONLY, NOT A REAL ALERT: " + headline
    elif sig == "T":
        headline = "TEST, NOT A REAL ALERT: " + headline
    return {
        "type": "alert",
        "source": "noaa",
        "event": event,
        "severity": severity,
        "urgency": urgency,
        "certainty": certainty,
        "area": area,
        "headline": headline,
    }


def main() -> None:
    if not is_ours(dict(os.environ)):
        sys.stdin.buffer.read()
        return
    msg = alert_from_env(dict(os.environ))
    line = json.dumps(msg)
    print(line, flush=True)
    if os.environ.get("SEND") == "1":
        subprocess.run([sys.executable, "-m", "software.hub.send", line], check=False)
    sys.stdin.buffer.read()


if __name__ == "__main__":
    main()
```

## 4. Testing with no real alert
1. **Recorded samples** from the sameold repo ([sample folder](https://github.com/cbs228/sameold/tree/develop/sample)): `two_and_two` (a WXR SVR), `npt` (a national test), `long_message` (31 locations). Raw 22050 Hz, signed 16-bit. Both short ones decoded correctly here. Wikimedia also has [Same.wav](https://commons.wikimedia.org/wiki/File:Same.wav), which the samedec README uses.
2. **Our own SAME audio** with Script 2. It writes a file with the three header bursts and three `NNNN` bursts, and **no attention tone**. Decoded correctly here at 22050 Hz, and after resampling to 48000 Hz with sox.
3. **`samedec --demo`** fakes a DMO header with no audio (`samedec --demo --file /dev/zero -- ...`). Its location is 999000, so Script 1 drops it. Use it to test samedec only.
4. **Live voice** proves reception any day (step 7). A live SAME header only comes with real weather or the Wednesday test.

**Safety rules.**
- Receive only. Nothing in this project transmits on any frequency.
- 47 CFR 11.45 forbids transmitting "the EAS codes or Attention Signal, or a recording or simulation thereof" outside a real alert or authorized test ([text](https://www.law.cornell.edu/cfr/text/47/11.45)). So generated SAME audio stays in a file and goes straight into the decoder. Never play it into a radio, a stream, or a speaker in a public room.
- Our generated headers use station `HACKDEMO`, and the headline says "DEMO ONLY, NOT A REAL ALERT".
- The box alarm is fake and never calls 911.

### Script 2: `make_same.py`
```python
"""Write a SAME test burst to a raw audio file, for decoder tests only.

Never play this file into a transmitter, a radio, or a public speaker
(47 CFR 11.45). It has no attention tone, only the data bursts.

Usage: python3 make_same.py OUT.raw 'ZCZC-WXR-TOR-048113+0030-3112300-HACKDEMO-'
Output: mono, signed 16-bit little-endian, 22050 Hz.
"""

import math
import struct
import sys

RATE = 22050
BAUD = 520 + 5 / 6     # "520.83 bits per second", 47 CFR 11.31
MARK = 2083 + 1 / 3    # bit 1
SPACE = 1562.5         # bit 0
PREAMBLE = bytes([0xAB] * 16)


def burst(text: str) -> list[int]:
    data = PREAMBLE + text.encode("ascii")
    bits = [(byte >> i) & 1 for byte in data for i in range(8)]  # LSB first
    out, phase = [], 0.0
    for k, bit in enumerate(bits):
        freq = MARK if bit else SPACE
        while len(out) < (k + 1) * RATE / BAUD:
            out.append(int(12000 * math.sin(phase)))
            phase += 2 * math.pi * freq / RATE
    return out


def main(path: str, header: str) -> None:
    silence = [0] * RATE  # one second
    audio = silence[:]
    for text in [header] * 3 + ["NNNN"] * 3:
        audio += burst(text) + silence
    with open(path, "wb") as f:
        f.write(struct.pack(f"<{len(audio)}h", *audio))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```
The preamble (16 bytes of 0xAB) and least-significant-bit-first order are what decoders expect; samedec accepted them. I did not test against multimon-ng [u].

## 5. Demo-safe plan (stretch goal, 1 to 2 hours)
Do this only after the check-in loop works end to end.

**Show (about 1 hour):**
1. Steps 1 to 7: the stick hears KEC56. First check the clip holds no SAME burst: `sox nwr.wav -t raw -r 22050 -e signed -b 16 -c 1 - | samedec -r 22050` must print nothing. Then play 5 seconds of the NWS voice to the judges. This proves a real over-the-air receiver with no internet.
2. Step 11 on stage: feed `demo.raw` into samedec. The decoded header appears, the `alert` appears on the hub, and the agent starts its check-in. Say it plainly: "This alert is a recording we made. A real one arrives the same way from 162.400 MHz."
3. Keep step 12 running in the background during judging, in case real weather sends a header.

**Pitch line:** "Official warnings reach the box over the radio, so they still arrive when the internet is down. The radio carries SAME codes; we turn them into CAP-shaped fields like the ones NWS and FEMA use online, with severity inferred from the event type."

**Skip:**
- Building drivers from source, multimon-ng and dsame, GQRX.
- Shortwave, the upconverter, and EAS on FM broadcast stations.
- Any CAP XML output or IPAWS access (needs a FEMA agreement).
- Any speaker playback of SAME tones.

**Fallback if reception fails in ECSW:** show steps 9 and 11 from files only, and say reception was blocked indoors.

## Open questions
1. Rafael: what exact SDR model, tuner chip, connector and antennas are in the box?
2. Rafael: does step 7 hear KEC56 inside ECSW, and with which antenna spot?
3. Godfrey and the agent owner (#15): should a TEST alert start a check-in? Does the alarm rule key on `severity`?
4. Godfrey: add `expires` or the raw header to the contract (#19)? Not needed for the demo.

## Sources
- [47 CFR 11.31 (EAS protocol)](https://www.law.cornell.edu/cfr/text/47/11.31), [11.45 (false EAS transmissions)](https://www.law.cornell.edu/cfr/text/47/11.45), [11.56 (CAP to EAS)](https://www.law.cornell.edu/cfr/text/47/11.56)
- [NWS NWR event codes](https://www.weather.gov/nwr/eventcodes), [NWS Fort Worth radio info](https://www.weather.gov/fwd/radioinfo), [NWS Fort Worth schedule](https://www.weather.gov/fwd/radiosch), [NWS alerts web service](https://www.weather.gov/documentation/services-web-alerts)
- [NWS Fort Worth on Wikipedia](https://en.wikipedia.org/wiki/National_Weather_Service_Fort_Worth,_Texas), [Broadcastify KEC56](https://www.broadcastify.com/listen/feed/46832), [Broadcastify KEC55](https://www.broadcastify.com/listen/feed/42343)
- [OASIS CAP 1.2](http://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html), [FEMA IPAWS](https://www.fema.gov/emergency-managers/practitioners/integrated-public-alert-warning-system)
- [samedec README](https://github.com/cbs228/sameold/tree/develop/crates/samedec), [sameold samples](https://github.com/cbs228/sameold/tree/develop/sample), [multimon-ng](https://github.com/EliasOenal/multimon-ng), [dsame](https://github.com/cuppa-joe/dsame), [rtl-sdr source](https://github.com/osmocom/rtl-sdr)
- [Nooelec NESDR SMArt v5](https://www.nooelec.com/store/sdr/sdr-receivers/nesdr-smart-sdr.html), [RTL-SDR Blog V4 guide](https://www.rtl-sdr.com/V4), [Debian rtl-sdr](https://packages.debian.org/bookworm/rtl-sdr)
- Local tests, 2026-11-07, macOS arm64 build of samedec 0.4.2: decoded two sameold samples, decoded Script 2 output at 22050 and 48000 Hz, ran Script 1 as the samedec child, and saw the `alert` on the hub `tap` (hub in `--sim` mode on test ports).
