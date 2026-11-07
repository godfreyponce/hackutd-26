---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, lifeline, plan]
---

# Lifeline Grid: Build Plan (synthesis)

Part of [HackUTD-2026](../HackUTD-2026.md) · idea [HackUTD-Idea-Shortlist](../HackUTD-Idea-Shortlist.md) #1 · GitHub issue #9.
Deep dives: [HackUTD-Lifeline-Clinical](HackUTD-Lifeline-Clinical.md) · [HackUTD-Lifeline-Hardware](HackUTD-Lifeline-Hardware.md) · [HackUTD-Lifeline-Agent](HackUTD-Lifeline-Agent.md) · [HackUTD-Lifeline-Pitch](HackUTD-Lifeline-Pitch.md).
Not locked: the team decides on issue #9.

## The one-sentence pitch
In a mass outage, utilities and emergency managers only have static lists of who depends on power. **We give every at-risk home a live harm clock, and a Nemotron agent that works the list until everyone is reached.**

## What the research changed
1. **The harm clock is the minimum of 3 clocks, not just the battery.**
   - In Winter Storm Uri (Feb 2021), **158 of 246 Texas deaths were hypothermia**. Only 25 involved worsened illness, which includes device or oxygen loss.
   - Half of Harris County's Beryl deaths were heat.
   - So each node tracks **device battery minutes + indoor temperature + CO**, and time-to-harm = the smallest of the three. Adds a temperature sensor and a CO sensor (~$3; the kit may have DHT/MQ modules).
2. **The radar's strongest signal: "home, cold, and not moving."** The LD2410C reports moving / still / absent. Say "still, consistent with breathing", never a breathing rate (only the MR60BHA2 does that, and it can't be bought same-day).
3. **Device tiers for the score:**
   - **Minutes:** ventilator, suction, concentrator with no oxygen tank.
   - **Hours:** tank or portable concentrator, BiPAP for respiratory failure.
   - **Days:** home dialysis, insulin.
   - **Low:** CPAP for sleep apnea.
4. **The gap is real:**
   - Texas: about 237,692 Medicare users of powered medical equipment vs about 10,530 critical-care registrations, roughly 20× under-registered.
   - emPOWER, STEAR, utility critical-care lists and PG&E's medical baseline program are all static, and "registration does not guarantee" anything.
   - Oncor said it could not prioritize critical-care customers during Uri.
   - No product or Devpost project found that estimates each person's battery runtime and triages them.
5. **Name:** "Lifeline" collides with the Lifeline medical-alert button (formerly Philips) and the FCC Lifeline phone subsidy, which serve the same people. Suggested: **Breathing Room** (backup: **Last Watt**). The team decides.

## Architecture
```
[switched power strip = "the grid"] ── 12 V adapter ──┬── divider → ESP32 GPIO34 (mains-loss detect)
        │                                             └── mini DC UPS ── 12 V → INA219 → 12 V fan ("oxygen concentrator")
        │                                                              └── 5 V USB → ESP32 (keeps running after outage)
        └── home Wi-Fi AP (dies with the grid, so the alert MUST go over LoRa)
ESP32 node: INA219 (I²C) · LD2410C radar (UART 256000) · temp + CO · → UART → Heltec V3 (Meshtastic)
        ~~~ LoRa 915 MHz ~~~> Heltec V3 on the Pi 5 hub → Python bridge → MQTT (mosquitto)
Pi 5 hub / laptop: FastAPI + WebSocket · Leaflet map · ranked queue · agent trace panel · Tiger Data (telemetry + decisions audit table)
Agent: NVIDIA API (OpenAI-compatible, integrate.api.nvidia.com/v1)
  planner = nvidia/nemotron-3-nano-30b-a3b (thinking on) · reply classifier = same (thinking off)
  guard = nvidia/llama-3.1-nemotron-safety-guard-8b-v3
Calls: Twilio Voice + speech gather (trial = verified numbers only, ~75 min) · simulated calls for the other 499 homes
```

## Ranking rule (safety-first)
- A **deterministic harm clock in minutes** sets the order.
- The LLM can move a home **at most 3 places**, must state a reason, and can **never demote a home under 30 minutes**.
- A human dispatcher approves every responder escalation.
- Every decision is written to the audit table.

## Agent loop (what NVIDIA judges must SEE)
No chat box. A telemetry event triggers the loop: **plan → act (tool calls) → verify → re-plan**, shown live as a ticking checklist with each tool call and result.
Tools: get_queue · get_home_telemetry · place_call · send_sms · classify_reply · escalate_to_responder (needs approval) · mark_status · schedule_recheck · broadcast_lora · explain_decision · (+1 in [HackUTD-Lifeline-Agent](HackUTD-Lifeline-Agent.md)).

## 60-second table demo
1. The map is calm: 500 simulated homes plus our real node.
2. **The judge flips the power strip.** Wi-Fi dies, the fan keeps running on the UPS, and the node reports over LoRa.
3. The queue re-ranks in about 2 s. The trace panel shows the agent planning.
4. **The judge's phone rings** (a verified number): "Hi, this is ___, are you okay?"
5. No answer → the agent escalates and asks the dispatcher to approve.

Each step has a fallback in [HackUTD-Lifeline-Pitch](HackUTD-Lifeline-Pitch.md).

## Tracks and framing
- **State Farm:** "Ting for people on life support." State Farm already gives policyholders the free Ting fire sensor and receives only aggregate data. Never mention pricing, claims denial or surveillance.
- **NVIDIA:** Nemotron plans and acts with tools, a safety model guards it, and the trace is visible.
- **Best Hardware + MLH Tiger Data.**

## Must-buy (call or order NOW; stock unverified)
| Where | Part | Fallback if it doesn't arrive |
|---|---|---|
| Amazon same-day | **LD2410C** radar (pack) | PIR from the kit |
| Amazon same-day | **Heltec WiFi LoRa 32 V3** ×2 | ESP-NOW between the 2 ESP32s |
| Amazon same-day | **INA219** (pack) | voltage-only estimate |
| Amazon same-day | **mini DC UPS** (12 V + 5 V USB out) | pass-through power bank |
| Micro Center | 12 V adapter, barrel Y-splitter + pigtails, 12 V fan, switched power strip, pass-through power bank, USB breakouts | — |
| Kit / cheap | temperature sensor (DHT/DS18B20), CO sensor (MQ-7) | temperature only |

Already owned and still used: Pi 5 (hub), 2× ESP32, kit sensors, 3D printer (node enclosure + mock concentrator), monitor (kiosk).
**Dropped for this idea:** AI HAT+, servos, pan/tilt, long camera cable. Buy the AI HAT+ only if we pick Second Look (#10).

## Owners
- **Rafael:** node rig, firmware (MQTT JSON: home_id, mains, battery_v, current_a, est_minutes_left, presence, motion, temp_c, co_ppm, ts), LoRa bridge, enclosures.
- **Godfrey:** agent loop + tools, ranking, Twilio, 500-home simulation, dashboard, Tiger Data, Devpost and video.
- Hour-by-hour plans: [HackUTD-Lifeline-Hardware](HackUTD-Lifeline-Hardware.md) (Rafael) and [HackUTD-Lifeline-Agent](HackUTD-Lifeline-Agent.md) (Godfrey).

## Open (fill in during the build)
- Built vs simulated split
- Battery-estimate error band
- Seconds from the switch flip to the phone ringing
- Final name
- Confirm the Nemotron IDs and that tool calling works on the hosted endpoint (hour 0)
