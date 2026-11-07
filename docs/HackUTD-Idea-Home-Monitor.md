---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, idea, hardware]
---

# Idea v2: Disaster + Home Safety Monitor (working title)

Part of [HackUTD-2026](HackUTD-2026.md). **Replaces the original Lifeline Grid idea** ([HackUTD-Lifeline-Plan](lifeline/HackUTD-Lifeline-Plan.md)) as Rafael's idea, 2026-11-07 ~2:20 PM. GitHub issue #9.
Rafael: "I haven't figured out everything yet." Below: **Decided** = his words; **Proposed** = research suggestions for him and Godfrey to accept or reject; **Open** = undecided.

## Decided (Rafael)
1. **One module, two jobs:** everyday home safety monitoring + natural-disaster monitoring.
2. **Detects bad events with cheap sensors:** earthquakes, screaming, falling, "whatever is easiest to detect".
3. **Mostly plugged in.** The sensors need real power to keep running.
4. **When the power cuts off, it keeps going:** it switches to a low-power mode that saves battery and outlives the outage.
5. **It talks:** a microphone (and speaker) to speak to people.
   - It detects someone → it asks if they're okay.
   - It detects no one → it **still asks "is everyone okay?"**
6. **Alarm rule:**

   | Someone detected? | Answer | Result |
   |---|---|---|
   | No | No answer | **No alarm** (no proof anyone is there) |
   | Yes | No answer | **Alarm** |
   | Yes or No | "Help" / distress | Alarm (proposed; Rafael said "stuff like that") |
   | Yes or No | "I'm okay" | Log it, no alarm (proposed) |

## Proposed: what is easiest to detect with cheap sensors
| Event | Sensor | Cost / source | Difficulty (1 easy–5 hard) | Notes |
|---|---|---|---|---|
| **Earthquake / strong shaking** | Accelerometer (MPU-6050 or ADXL345) on the ESP32 | ~$3, often in kits | **1–2** | Trigger when short-term shaking jumps above the long-term background (STA/LTA). Demo: shake the table. Could confirm with the free USGS earthquake feed when online |
| **Screaming, glass breaking, smoke alarm, crying, shouting** | USB mic (owned) + YAMNet sound classifier on the Pi | $0 | **2** | YAMNet has ready-made classes for these and runs on the Pi CPU. Demo: play a scream or alarm clip |
| **Loud impact / thud** | Same mic (loudness spike) and/or the accelerometer | $0 | **2** | A thud followed by stillness is a fall hint |
| **Person present / moving / still** | LD2410C mmWave radar | ~$5 (Amazon) or PIR from the kit | **1–2** | Answers "is someone here?" for the alarm rule; works through smoke and in the dark, no camera |
| **Fall** | Thud (mic/accel) + radar goes from moving to still | — | **3–4** | The hardest one. Combining two signals is believable; claiming "fall detection" alone isn't |
| **Smoke / gas / CO** | MQ-2 / MQ-7 | ~$3, often in kits | **1–2** | Also covers the cold/CO harm from the clinical research |
| **Flood / water** | Kit water-level sensor | ~$1 | **1** | Easy disaster signal |
| **Temperature (cold/heat)** | DHT22 / DS18B20 | ~$3, kit | **1** | Uri: 158 of 246 deaths were hypothermia ([HackUTD-Lifeline-Clinical](lifeline/HackUTD-Lifeline-Clinical.md)) |
| **Power cut** | Adapter voltage on a GPIO (divider) | $0 | **1** | Triggers low-power mode |

Proposed minimum set for the demo: **accelerometer + mic + radar + power-cut detection**, plus one or two cheap extras (smoke or water) if time allows.

## Proposed: how low-power mode could work
- **Plugged in (full mode):** Pi 5 runs sound classification, voice (offline TTS and speech-to-text), the dashboard and the agent. The ESP32 reads the accelerometer, radar and other sensors.
- **Power cut (low-power mode):**
  - The Pi 5 shuts down cleanly (it draws several watts).
  - The ESP32 runs on the battery: accelerometer + radar + loudness only, with light/deep sleep between checks.
  - It wakes the full system (or sends an alert) only on an event.
  - Alerts go over LoRa (Meshtastic) when Wi-Fi/cell is down.
- **What to show judges:** power draw in each mode (INA219) and the estimated hours left on battery.
- Open: does the Pi stay on a UPS long enough to hold the voice conversation during an outage, or does the ESP32 speak with recorded prompts?

## Proposed: voice check-in
- **Trigger:** any bad event → speaker: "This is your home monitor. Is everyone okay?"
- **Listen** ~10–15 s. Offline speech-to-text (Vosk or whisper.cpp tiny) → "okay" / "help" / no answer.
- **Combine** the answer with radar presence using the alarm rule above. Escalate: SMS/call a contact (Twilio), dashboard alert, LoRa message.
- Repeat the question once before deciding "no answer".

## Tracks (proposed, not decided)
- **State Farm** "The Worst Day, at Scale": disaster detection + "ensure no one is overlooked" (the presence + no-answer rule).
- **Best Hardware:** a sensor-fusion box with real power management.
- **NVIDIA** "Nemotron beyond a chatbot": only if Nemotron does real work. Candidate jobs:
  - decides the escalation plan
  - writes the incident summary for responders
  - runs the follow-up check-ins
  - coordinates many homes in a disaster
- **Open:** decide with Godfrey. NVIDIA needs Nemotron to plan and use tools, not just chat.

## Wording (proposed)
"Surveillance" can sound like spying to judges. Consider **"home safety monitor"**. No camera; audio is classified on the device and not recorded (privacy by design).

## Open questions
- Name.
- Which events are in the demo vs "what's next".
- Battery size + target hours in low-power mode.
- What happens after an alarm: who gets it, how (SMS, call, LoRa, dashboard).
- Single home only, or many homes on a dispatcher map (the Lifeline queue idea)?
- Role of Nemotron / the agent (decides the NVIDIA track).
- How it differs from Godfrey's "Two Clocks" front-runner; merge or replace.

## What carries over from Lifeline research
- Radar (LD2410C), INA219 power measurement, the LoRa fallback, the power-cut detection rig, Twilio calling.
- The temperature/CO clocks and the Uri story.
- See [HackUTD-Lifeline-Hardware](lifeline/HackUTD-Lifeline-Hardware.md) for wiring and the parts list.
