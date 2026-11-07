---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, risk]
---
Part of [HackUTD-2026](../HackUTD-2026.md). Companion to [HackUTD-Research-Embedded](HackUTD-Research-Embedded.md), [HackUTD-Research-Pi-Stack-Offline](HackUTD-Research-Pi-Stack-Offline.md), [HackUTD-Research-Claude-Loadout](HackUTD-Research-Claude-Loadout.md).

## Risk table

| Failure | Early sign | Prevention | Fix in 5 min |
|---|---|---|---|
| **Pi 5 thermal throttle** (CPU DINOv2 + Hailo + Chromium) | `vcgencmd measure_temp` > 75 C; `get_throttled` bit 3 `0x8` (soft limit) or `0x4` (throttled); `0x80000`/`0x40000` = happened since boot. Arm throttles progressively 80-85 C, Arm+GPU at 85 C | Default fan curve: off < 50, 30% at 50, 50% at 60, 70% at 67.5, 100% at 75 C; tune with `fan_tempN` dtoverlay params. Vent the case over the Active Cooler; run the 40 mm fan off the external 5 V rail, not the Pi header (fan header shares the USB current budget) | Lid off, cap CPU model FPS (run DINOv2 every Nth frame), kill Chromium devtools tabs |
| **Undervoltage / brownout** | `get_throttled` bit 0 `0x1` / bit 16 `0x10000`; kernel log undervoltage entry (trips < 4.63 V ±5%); boot warning "USB current limited to 600 mA" | Official 5 V 5 A USB-PD PSU (unlocks 1.6 A USB budget). Servos on their own 5-6 V supply, never Pi 5 V. **Common ground** between servo PSU, ESP32 and Pi. Bulk cap (470-1000 uF [u]) across servo rail | Unplug servo rail, re-check `get_throttled`; swap to the short thick cable; drop USB peripherals |
| **SD corruption on power loss** | fsck messages at boot, read-only remount, random segfaults | `raspi-config` > Performance > Overlay File System (writes go to RAM, lost on reboot). Enable only after the stack is final. Clone a spare card Sat night (`rpi-clone` [u] or `dd` image on laptop) | Swap in the cloned spare card (30 s). Never `apt upgrade` the spare |
| **Hailo driver breaks after update** | `Driver version (x) is different from library version (y)`; `hailort-pcie-driver` DKMS build fails after a kernel bump | **No `apt upgrade` during the event.** `sudo apt-mark hold hailo-all hailort hailort-pcie-driver linux-image-rpi-2712` [u: package names, check `dpkg -l | grep -E 'hailo|linux-image'`]. All Hailo packages must be the same version | Boot spare card. Last resort: purge all Hailo packages + reinstall `hailo-all`, reboot (>5 min) |
| **ESP32 resets on port open** | Servo homes every time the Pi service restarts; boot banner in serial log | On Espressif dev boards the DTR/RTS transistor circuit usually prevents it; still disable RTS/CTS flow control and set `stty -F /dev/ttyUSB0 -hupcl`. Firmware: idempotent, no homing sweep on boot | Make the Pi side resend last pose after reconnect; use `/dev/serial/by-id/...` path, not `ttyUSB0` |
| **Servo jitter / stall / burnout** | Buzzing at rest, hot case, Pi brownout on fast moves | Separate supply, common ground, rate-limit target angle changes, soft end-stops in firmware, detach PWM when idle [u] | Swap servo (bring spare SG90/MG90S), lower pan range |
| **Camera ribbon damage on moving head** | Intermittent `libcamera` timeouts when the head pans | Strain relief loop, tape ribbon to the static arm, limit pan to < ~150 deg [u]; bring spare cable | Replace ribbon (power off first); fallback: fixed camera, servo disabled |
| **Venue Wi-Fi / Nemotron API limits** | Rising latency, HTTP 429 | Local Gemma path is the default; cloud is an enhancement. Cache last N cloud answers keyed by prompt; UI badge "offline mode". Phone hotspot as backup uplink | Flip `OFFLINE=1` env, restart service |
| **MQTT broker down** | Dashboard tiles go stale; clients log reconnects | Broker (Mosquitto) on the Pi 5 or laptop via systemd `Restart=always`; clients auto-reconnect; retained messages for last state | `sudo systemctl restart mosquitto` |
| **Chromium kiosk crash** | Black screen, "Aw, Snap", memory creep | systemd unit with `Restart=always`, `RestartSec=2`; `--kiosk --noerrdialogs --disable-session-crashed-bubble` [u flags]; reload page on MQTT reconnect | `systemctl --user restart kiosk` or SSH + restart |
| **Git conflicts between two Claude sessions** | Both sessions editing `main`, same file | One branch/worktree per person, file ownership split (Pi vs ESP32 vs UI), pull + commit every ~45 min, PRs merged by one human | `git stash`, `git pull --rebase`, resolve; never `push --force` on `main` |
| **Laptop battery** | < 30% by midnight | Charger + power strip at table; laptop not on the critical demo path at judging | Plug in; move broker to Pi |
| **3D print fails / late** | Print not started by Sat 6 PM | Print case + pan/tilt parts first (before code), on a known profile; zip-tie/cardboard fallback mount | Run demo on open bench with taped camera |
| **Model download size/time** | Venue Wi-Fi at ~MB/s, multi-GB pulls | Download all `.hef`, Gemma, Moonshine, DINOv2 weights **before arrival**; copy to USB stick + laptop | Copy from USB stick, not the internet |

## Demo insurance

1. **Backup video**: 60-90 s screen + phone recording of the full loop, recorded Sat night once it works, re-recorded Sun AM if features changed. On the laptop and a phone, offline.
2. **Replay mode**: `REPLAY=path/` env makes the capture node publish saved frames (and saved audio clips) instead of the live camera, at normal rate, through the same Hailo/CPU/MQTT/UI pipeline. Record 2-3 min of good frames Sat night. Lets you demo if the camera, ribbon or servo dies; say so honestly to judges.
3. **One-command restart** `demo-restart.sh` (notes only): stop services → `vcgencmd get_throttled` + temp print → restart mosquitto, inference, ESP32 bridge, kiosk in order → wait for MQTT heartbeat → print PASS/FAIL per node. Put it on the Pi desktop and in the README.

## Pre-judging checklist (Sun 12-1 PM)

- [ ] Code freeze at 12:00: tag `demo-final`, no `apt`, no new pulls
- [ ] Spare SD cloned from the final card, labeled, tested boot
- [ ] `get_throttled` = `0x0` after 15 min under full load; temp < 75 C
- [ ] Servo PSU + common ground checked; spare servo + ribbon in bag
- [ ] Ethernet switch, all nodes ping; broker up; kiosk auto-recovers after `kill`
- [ ] `OFFLINE=1` path tested; `REPLAY` path tested
- [ ] Backup video plays offline on laptop and phone
- [ ] Laptop + Pi on wall power, power strip, cables taped
- [ ] 30 s pitch + who answers which judge question
- [ ] Device runs 3 h: plan a quiet restart every ~60 min between judges [u]

## Go / no-go cut-over rule

At a judge's arrival: **if the live loop has not produced a correct result within 60 s, or `demo-restart.sh` already failed once in the last 10 min, cut to replay mode; if replay also fails, play the backup video.** Say what failed in one sentence. Restart the live system after the judge leaves, never in front of them. Decide this rule before judging; don't debate it at the table.

## Sources

- [Raspberry Pi docs: OS / vcgencmd get_throttled bits](https://www.raspberrypi.com/documentation/computers/os.html)
- [Raspberry Pi docs: Raspberry Pi hardware (thermal limits, Pi 5 fan curve, 5 A PSU, 600 mA vs 1.6 A, 4.63 V undervoltage)](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [Hailo community: PCIe drivers broken after RPi5 update](https://community.hailo.ai/t/hailo-10l-pcie-drivers-broken-after-recent-rpi5-update/19301)
- [Espressif esptool: boot mode selection / DTR-RTS auto-reset](https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/boot-mode-selection.html)
- Overlay FS steps from search summary of Adafruit "Read-Only Raspberry Pi" guide (page not opened) [u]
