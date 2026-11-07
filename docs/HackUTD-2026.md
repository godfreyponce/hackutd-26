---
created: 2026-11-07
status: seed
tags: [project, hackathon, hardware, embedded, edge-ai, utd, fall-2026]
thread: active
next: "pick the idea within 30 min of the noon track reveal; buy the stepper PSU (+ AI HAT+ 26T if ≤$140)"
due: 2026-11-08
as_of: 2026-11-07
priority: high
---

# HackUTD 2026 ("Zero Day")

24-hour hackathon at UTD, **Sat Nov 7 12:00 PM → Sun Nov 8 12:00 PM**. Team: Rafael (hardware/embedded) +
Godfrey (software/AI), the same pair as HackEdge-2026. Direction: **hardware + edge AI**.
This note is the hub; everything for the event lives in this folder.

## Now
- **Leading concept: "Look less, think less."** RLT patch skipping + a confidence cascade + few-shot DINOv2 prototypes, on a stepper pan/tilt driven by an MCU, with a live efficiency overlay. The application gets picked once the tracks are announced at noon ([HackUTD-Ideas](HackUTD-Ideas.md)).
- **Stepping:** use a cheap MCU with AccelStepper. The Pi 5 can't step cleanly, and the AM62 M4F / i.MX 95 M7 are too risky ([HackUTD-Research-Embedded](research/HackUTD-Research-Embedded.md)).
- **Priorities he set:** (a) speed and efficiency, (b) accuracy from little or messy data. Device adaptation (c) is low priority.
- **Board decision:** the i.MX 95 is *weaker* than the Pi 5 for AI, so skip its NPU. Buy the AI HAT+ 26 TOPS (Hailo-8) if it costs $140 or less ([HackUTD-Research-Boards](research/HackUTD-Research-Boards.md)).
- Repo: Godfrey's (not visible on GitHub as of 7:13 AM). Godfrey's agents are researching past winners.
- **Tracks: up to 3 sponsor + 1 HackUTD track (Best Hardware) + any MLH** (Devpost rules; supersedes "up to 2"). $60k+ prizes. Demo video ≤ 2 min ([HackUTD-Research-Judging](research/HackUTD-Research-Judging.md)).
- **Official tracks are out ([HackUTD-Tracks](tracks/HackUTD-Tracks.md)). Event site says enter up to TWO company tracks** (Devpost said 3; ask an organizer). No Axxess, Niantic or AT&T track. Best fits: **NVIDIA "Nemotron beyond a chatbot"** + **State Farm "catastrophe response"**; Northmark/CBRE as alternates.
- **Old shortlist (superseded by the official tracks):** NVIDIA (Nemotron cloud stage) · EOG (gauge reader) · CBRE (occupancy sentry) · Axxess if it runs a track · + Best Hardware + MLH Tiger Data/GoDaddy. Conditional: State Farm (only if home risk), Niantic, T-Mobile.
- **Cross-account Claude:** no official way to orchestrate between accounts; use GitHub issues as the shared queue + `@claude` Action on Godfrey's plan ([HackUTD-Research-Claude-Loadout](research/HackUTD-Research-Claude-Loadout.md)).
- **All research done (P0 + P1 + NVIDIA winners).** Pan/tilt likely **servos + ESP32** (his idea; servo model to confirm); custom Pi 5 + AI HAT+ case designed (`Documents/3D-Prints/Pi5-AI-HAT-Case/`). Still open (physical checks for Rafael): the stepper driver model, whether a microcontroller is in the kits ([HackUTD-Research-Agenda](research/HackUTD-Research-Agenda.md)).

## Map
| Note | What's in it |
|---|---|
| [HackUTD-Tracks](tracks/HackUTD-Tracks.md) | **Official challenge tracks, prizes, briefs, fit** |
| [HackUTD-Event-Info](HackUTD-Event-Info.md) | Schedule, deadlines, sponsors, rules |
| [HackUTD-Inventory](HackUTD-Inventory.md) | Hardware we own + shopping list |
| [HackUTD-Plan](HackUTD-Plan.md) | 24-hour workflow, roles, repo structure, Claude setup |
| [HackUTD-Ideas](HackUTD-Ideas.md) | Candidate builds and the current recommendation |
| [HackUTD-Research-Agenda](research/HackUTD-Research-Agenda.md) | What to research, status of each item |
| [Research-Edge-AI-Brief](research/Research-Edge-AI-Brief.md) | **One-page merged summary of all research. Read this first** |
| [HackUTD-Research-Cascades](research/HackUTD-Research-Cascades.md) | Model cascades: papers, numbers, demo metrics |
| [HackUTD-Research-Boards](research/HackUTD-Research-Boards.md) | i.MX 95 vs Pi 5 vs Hailo vs Jetson vs AM62 |
| [HackUTD-Research-Edge-Techniques](research/HackUTD-Research-Edge-Techniques.md) | Edge-AI tools and models released mid-2025 to now |
| [HackUTD-Research-Streaming-Efficiency](research/HackUTD-Research-Streaming-Efficiency.md) | Frame-reuse (RLT), token merging, SSMs, HDC, KAN verdict |
| [HackUTD-Research-Learning](research/HackUTD-Research-Learning.md) | Few-shot prototypes, TTA, federated, anomaly detection |
| [HackUTD-Research-Embedded](research/HackUTD-Research-Embedded.md) | Pi 5 GPIO, stepper drivers, power, comms, servo loop, Hailo setup |
| [HackUTD-Research-Judging](research/HackUTD-Research-Judging.md) | Jury judging mechanics, past winners, sponsor history, MLH prizes, playbook |
| [HackUTD-Research-Track-NVIDIA](tracks/HackUTD-Research-Track-NVIDIA.md) | Nemotron VL as the cloud stage; API setup; 2025 winners |
| [HackUTD-Research-Track-EOG](tracks/HackUTD-Research-Track-EOG.md) | Dataset challenges 2023–25; edge gauge reader angle |
| [HackUTD-Research-Track-Property](tracks/HackUTD-Research-Track-Property.md) | State Farm + CBRE cards; occupancy sentry / hazard mode |
| [HackUTD-Research-Track-Axxess](tracks/HackUTD-Research-Track-Axxess.md) | Home health; "silent visit log" angle; privacy wording |
| [HackUTD-Research-Track-Niantic](tracks/HackUTD-Research-Track-Niantic.md) | Mobile-only SDK; scan booth + pin detections (partial fit) |
| [HackUTD-Research-Track-Telecom](tracks/HackUTD-Research-Track-Telecom.md) | T-Mobile/AT&T; events-not-video angle (conditional) |
| [HackUTD-Research-Track-InfraDev](tracks/HackUTD-Research-Track-InfraDev.md) | Northmark, 8090, Spacetime, Photon |
| [HackUTD-Research-MLH-Prizes](tracks/HackUTD-Research-MLH-Prizes.md) | Gemini, Tiger Data, GoDaddy, Vultr, MongoDB quick-starts |
| [HackUTD-Research-Mechanical](research/HackUTD-Research-Mechanical.md) | Pan/tilt designs, 3:1 belt pan, print plan |
| [HackUTD-Research-Pi-Stack-Offline](research/HackUTD-Research-Pi-Stack-Offline.md) | Pi OS + Hailo setup, offline download list, smoke test |
| [HackUTD-Research-Firmware-Wiring-Buy](research/HackUTD-Research-Firmware-Wiring-Buy.md) | Pico + FastAccelStepper, serial protocol, wiring, shopping |
| [HackUTD-Research-Claude-Loadout](research/HackUTD-Research-Claude-Loadout.md) | Cross-account workflow (GitHub queue), tool loadout, Pro vs Max |
| [HackUTD-Research-NVIDIA-Winners](tracks/HackUTD-Research-NVIDIA-Winners.md) | 14 past NVIDIA prize winners with links + patterns |
| [HackUTD-Research-Track-FinanceLaw](tracks/HackUTD-Research-Track-FinanceLaw.md) | PNC, Toyota FS, Goldman, Capital One, Winstead (Toyota conditional) |
| [HackUTD-Research-Judge-UI](research/HackUTD-Research-Judge-UI.md) | Kiosk config, MJPEG + MQTT-over-WebSocket, vanilla JS + uPlot, layout |
| [HackUTD-Research-Pitch-Demo](research/HackUTD-Research-Pitch-Demo.md) | Devpost template, 2-min video shot list, 60-s pitch + Q&A, eval protocol |
| [HackUTD-Research-Risks](research/HackUTD-Research-Risks.md) | Failure table, demo insurance, Sun 12–1 PM checklist, cut-over rule |

## Log
- 2026-11-07 — Official tracks read from the event site: up to 2 company tracks (supersedes 2026-11-07: 3, from Devpost rules; unconfirmed); no Axxess/Niantic/AT&T track; NVIDIA + State Farm best fit ([HackUTD-Tracks](tracks/HackUTD-Tracks.md)).
- 2026-11-07 — P1 research done (finance/law, judge UI, pitch/demo, risks) + NVIDIA winners list; servo pan/tilt proposed (supersedes 2026-11-07: steppers).
- 2026-11-07 — P0 research fleet done (12 notes: 7 sponsor cards, MLH, mechanical, Pi stack, firmware/buy, Claude loadout); track shortlist set.
- 2026-11-07 — Track limit is 3 sponsor + 1 HackUTD + MLH (supersedes 2026-11-07: up to 2, from the event site).
- 2026-11-07 — Research round 2 done (streaming efficiency, learning, embedded); concept upgraded to "Look less, think less" (supersedes 2026-11-07: voice-directed cascade alone).
- 2026-11-07 — Research round 1 done (cascades, boards, techniques); leading concept chosen; i.MX 95 NPU dropped.
- 2026-11-07 — He set priorities: speed + accuracy over adaptation.
- 2026-11-07 — Project opened; inventory recorded; moved into folder `20-Projects/HackUTD-2026/`.
