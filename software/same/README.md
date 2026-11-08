# SAME alerts: radio and demo file to hub `alert` (#37)

NOAA Weather Radio sends a SAME header before each warning. This package decodes SAME audio with multimon-ng and sends one hub `alert` per message. The live radio and our demo file go through the same decoder and the same parser.

```
audio -> multimon-ng -t raw -a EAS -> same_to_alert.py -> hub alert
```

## The rule: never transmit, never play it out loud

- Nothing in this project transmits on any frequency.
- 47 CFR 11.45 bans transmitting EAS codes, the attention signal, or a simulation of them outside a real alert or an authorized test. So `demo_eqw.wav` goes only through an audio cable into our own decoder.
- Never play the file on a speaker, at the venue or anywhere else. Keep the phone on the cable.
- The demo file uses station `HACKDEMO`, so every alert from it has `"demo": true`.

## Files

- `make_same.py`: writes a SAME message as audio. It has the header 3 times, an 8 second 1050 Hz warning tone, 2 seconds of silence, then `NNNN` 3 times. Mono, 22050 Hz, 16-bit. A `.raw` name writes headerless audio.
- `demo_eqw.wav`: the ready demo file for the phone, for the stage. Header `ZCZC-WXR-EQW-048113-048085+0030-3120410-HACKDEMO-` (earthquake warning, Dallas and Collin counties).
- `rehearsal_eqw.wav`: the same alert with a different time (`3120420`), for the cable check before the demo. See "Restart before a replay".
- `same_to_alert.py`: reads multimon-ng lines on stdin and sends the alerts. `--dry-run` prints the JSON and sends nothing.
- `listen.sh`: runs the whole chain from the Pi audio input, a file, the Mac input, or stdin.

Run everything from the repo root with the hub venv (`.venv`, see `software/hub/README.md`). The alert goes to `HUB_URL` (default `ws://localhost:8765`). If the hub runs on another machine, start it with `--host 0.0.0.0` and set `HUB_URL=ws://<that machine's IP>:8765`.

## The alert

`ZCZC-WXR-EQW-048113-048085+0030-3120410-HACKDEMO-` becomes:

```json
{"type": "alert", "source": "noaa", "event": "Earthquake Warning", "code": "EQW", "station": "HACKDEMO", "severity": "Severe", "urgency": "Immediate", "certainty": "Likely", "area": "Dallas County, TX; Collin County, TX", "headline": "Earthquake Warning for Dallas County, TX; Collin County, TX", "demo": true}
```

- One alert per message. The header comes 3 times, and `same_to_alert.py` drops the repeats until `NNNN`.
- Kept: Dallas County (048113), Collin County (048085), and national (000000). It drops other headers and prints a line on stderr for each. A header with our county and others says "and N other areas".
- SAME has no severity, urgency or certainty. We set them by the kind of message: warnings and emergencies Severe, Immediate, Likely; watches Severe, Future, Possible; statements Moderate, Expected, Likely; tests Unknown. These copy what NWS used online (`docs/research/HackUTD-SDR-Alerts.md`, section 3).
- `demo` is true for station `HACKDEMO` or code `DMO`. The headline stays plain; the screens and speech add the demo notice.
- The hub adds `level` itself. We do not send it.
- If the hub is down, `same_to_alert.py` still prints the alert, prints the error on stderr, and keeps listening.

## Demo on the Pi

You need a USB audio adapter with a mic input (the Pi 5 has no audio input), a 3.5 mm cable, and a phone with `demo_eqw.wav` and `rehearsal_eqw.wav` on it. A phone with no headphone jack also needs its USB-C or Lightning to 3.5 mm adapter. Put the phone in Do Not Disturb and turn off its Bluetooth, so no notification sound goes down the cable and the audio does not go to a Bluetooth device.

1. Install the tools:

   ```bash
   sudo apt install multimon-ng sox alsa-utils
   ```

2. Plug in the USB adapter. Check that it shows up as a capture card:

   ```bash
   arecord -l
   ```

3. Connect the phone's headphone output to the adapter's mic input with the cable. Do not use a speaker.
4. Set the phone volume to about half. A mic input is loud; if nothing decodes, try lower and higher volume, or set the capture level in `alsamixer` (F4 for capture).
5. Check the chain with no hub first. Start the listener, play the file on the phone, and look for one JSON line:

   ```bash
   software/same/listen.sh --dry-run
   ```

6. For the demo, run it without `--dry-run`. The hub gets the `alert`:

   ```bash
   software/same/listen.sh
   ```

`listen.sh` picks the first USB card in `arecord -l` and prints its line. If the box also has a USB microphone, check that the line names the adapter. To choose a card, pass its name, for example `--device plughw:CARD=Device,DEV=0`. The name is the word after `card N:` in `arecord -l`. Card numbers can change between boots; names do not.

`listen.sh` stops at once with a message if the venv or multimon-ng is missing.

After you plug in the adapter, check that the voice service still uses the box speaker and mic (`wpctl status`). Pi OS can switch the default device to a new USB card.

**Restart before a replay.** multimon-ng prints a header only once per run. Playing the same file again in the same run gives nothing, with no error. So:

- Check the cable with `rehearsal_eqw.wav`, and play `demo_eqw.wav` on stage. They have different times, so both decode in one run.
- The cable check sends a real `alert` to the hub, so the overlay shows and the agent starts a check-in. After the check, send a reset:

  ```bash
  .venv/bin/python -m software.hub.send '{"type":"reset"}'
  ```

- To play the same file again, press Ctrl-C and start `listen.sh` again first.
- A file made with `make_same.py` gets the current minute in its header. Two files made in the same minute have the same header.

## Real alerts from the radio

Rafael's receiver (`hardware/radio/noaa.sh decode`) prints the same multimon-ng lines. Feed them in:

```bash
hardware/radio/noaa.sh decode | software/same/listen.sh --stdin
```

## On the Mac

Homebrew has no multimon-ng formula. Build it once and put it on the PATH. If `cp` says permission denied, run it with `sudo`.

```bash
brew install cmake sox
```

```bash
git clone --depth 1 https://github.com/EliasOenal/multimon-ng.git /tmp/multimon-ng && cmake -S /tmp/multimon-ng -B /tmp/multimon-ng/build && make -C /tmp/multimon-ng/build && cp /tmp/multimon-ng/build/multimon-ng /usr/local/bin/
```

Decode a file:

```bash
software/same/listen.sh --file software/same/demo_eqw.wav --dry-run
```

Listen on the Mac's default input (allow the terminal to use the microphone). Use a cable or a USB adapter, never a speaker:

```bash
software/same/listen.sh --mac
```

sox reads `AUDIODEV`, so `AUDIODEV="<adapter name>" software/same/listen.sh --mac` listens on a USB adapter instead of the built-in mic. The adapter name is the one in System Settings, Sound, Input.

Make a new demo file with the current time:

```bash
.venv/bin/python -m software.same.make_same demo.wav
```

## Tests

```bash
.venv/bin/python -m pytest software/same
```

The parser tests need nothing extra. The end-to-end tests run `listen.sh` into a real hub on a free port. They play `demo_eqw.wav` and a fresh 48 kHz file and expect exactly one alert each. They play the rehearsal file then the demo file in one run and expect two. They run Pi mode with a fake `arecord` and `--stdin` with radio lines. They skip with a message if multimon-ng or sox is missing.
