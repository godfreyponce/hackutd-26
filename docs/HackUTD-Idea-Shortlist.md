---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, ideas, decision]
---

# HackUTD 2026: Idea Shortlist (5-agent research, 2026-11-07 ~1:30 PM)

Part of [HackUTD-2026](HackUTD-2026.md). Five research angles: unmet needs, novelty audit, new tech, sponsor priorities, ideation + red-team. Tracks: [HackUTD-Tracks](tracks/HackUTD-Tracks.md).
Judge bar (Rafael): never done before · real positive impact · hard engineering that is still doable in ~22 h.

## What the research agreed on
- **Overdone at hackathons:** fall-detection cameras, sign-language gloves, YOLO glasses for the blind, trash sorters, camera + LLM alerts, software-only data-center dashboards.
- **Recent winners made devices that act** (Shepherd cane steers its user, TreeHacks 2026 grand prize), not ones that only alert.
- **Rare at hackathons:**
  - cheap mmWave radar (HLK-LD2410/LD2450, ~$5, UART into an ESP32)
  - ESP32 Wi-Fi sensing
  - LoRa/Meshtastic mesh with no cell network
  - acoustic or vibration fault sensing
  - **an agent whose tools are motors and sensors**
- **Sponsors:**
  - NVIDIA rewards a visible plan → act → verify loop, real tool calls, and several Nemotron models (the VL model is "Nemotron Nano 2 VL"). Nemotron runs in the cloud (NIM), never on the Hailo.
  - State Farm rewards urgency ranking, nobody overlooked, auditable reasons and a human in the loop. It stopped flying drones over homes.
- Two agents independently picked the same idea: **#1 below**.

## Ranked ideas
| # | Idea | One line | Tracks | I/Im/E/F/D (each /5) |
|---|---|---|---|---|
| 1 | **Lifeline Grid** | Outage triage for people on powered medical equipment: per-home node knows the device's battery time left + whether the person is present/moving (radar) → Nemotron agent ranks by time-to-harm, calls, escalates, re-ranks; LoRa when cell is down | State Farm + NVIDIA + Best Hardware + Tiger Data | 4/5/4/4/4 |
| 2 | **Second Look** | Survivor-finding sentry: radar + mic detect people cameras miss; the agent re-aims the servo camera and rewrites the Hailo CLIP watch list to confirm before it reports | NVIDIA + State Farm + Best Hardware | 4/4/5/3/5 |
| 3 | **Rack Sentinel / Right-Hands** | A camera patrols a mock rack, catches LED faults the software misses and checks each technician step against the work order; iOS handoff (Godfrey's TechAssist experience) | Northmark + NVIDIA | 4/3/4/3/5 |
| 4 | **Ripple** | Building leak-spread predictor: sensors + pipe/room graph → agent closes servo valves in order of consequence | CBRE + NVIDIA + Tiger Data | 3/3/4/3/5 |
| 5 | **X-Code** | Reads FEMA search markings + HELP signs from a vehicle camera, geotags, merges with 911 texts, keeps an "unvisited blocks" list | State Farm + NVIDIA | 4/4/4/3/4 |
| 6 | **Pause Button** | In-home device: on-device scam-pattern detection during a call → delays the payment, asks a trusted contact | T-Mobile + NVIDIA | 3/4/3/3/4 |

### #1 Lifeline Grid in detail
- **Problem:**
  - About 2.5–2.7 M Medicare beneficiaries depend on powered equipment (HHS emPOWER).
  - emPOWER only gives de-identified counts per ZIP code. Utilities' medical lists are static and can't contact anyone.
  - Nobody knows whose battery runs out first.
- **Hardware (Rafael):** per-home ESP32 node.
  - Mains-loss detect, plus load current via **INA219 on a DC/battery-backed "device"** or a non-invasive CT clamp. No mains wiring at the table.
  - The battery estimate is calculated from the current drawn.
  - **LD2410 radar:** is the person present and moving.
  - Report over Wi-Fi/MQTT, fall back to **Meshtastic LoRa**.
  - Pi 5 hub runs the dashboard and the local queue.
- **Agent (Godfrey):** Nemotron plans → ranks by time-to-harm → calls with Twilio/ElevenLabs ("Is Mrs. Diaz okay?") → no answer = escalate to a responder → re-ranks as batteries drain. Every decision gets an auditable reason. A simulated 500-home city shows scale.
- **Table moment:** the judge flips the power strip off → the queue re-ranks in about 2 s → the judge's phone rings.
- **Risk:** the engineering looks too simple. **Fix:** the radar fusion, the battery-time estimate, the LoRa fallback and the scale simulation.
- **What carries over from earlier work:** the Pi 5 + case and the dashboard research. The pan/tilt camera cascade drops unless we pick #2.

## Broad subject areas (if none of the ideas land)
1. Disaster resilience when power or networks fail (off-grid sensing, mesh comms)
2. Vulnerable people at home: medical devices, heat, CO, isolation
3. Agents with physical bodies: an AI that moves, aims, closes valves and verifies
4. Privacy-first sensing without cameras: radar, Wi-Fi CSI, sound, vibration
5. Infrastructure health from cheap signals: current draw, vibration, sound, gauge reading
6. Data-center physical operations: the gap between what the software says and what the hardware shows; technician error
7. Building operations: water, HVAC, predicting how failures spread
8. Scams and fraud in the physical world: in-home, at the moment it happens
9. Accessibility devices that act rather than alert
10. Field workers in the field: inspection, readings, handoffs

## Sources
Agent outputs (verbatim: session fc1e3648). Key links: ASTHO emPOWER brief; FTC 2025 older-adult fraud report; Maricopa 2024 heat deaths; Uptime/DPS 2025 outage report; Stanford Daily TreeHacks 2025/2026; esp-csi; Meshtastic; hailo-apps CLIP; NVIDIA Nemotron 3 agents blog; Insurance Journal 2026-02-27 (State Farm CAT).
