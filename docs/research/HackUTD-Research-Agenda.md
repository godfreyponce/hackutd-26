---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research]
---

# HackUTD 2026: Research Agenda

Part of [HackUTD-2026](../HackUTD-2026.md). Status: ✅ done · ⏳ running · ⬜ open.

## AI
- ✅ Model cascades → [HackUTD-Research-Cascades](HackUTD-Research-Cascades.md)
- ✅ New edge-AI tools and models (mid-2025 onward) → [HackUTD-Research-Edge-Techniques](HackUTD-Research-Edge-Techniques.md)
- ✅ Techniques for processing streaming data efficiently → [HackUTD-Research-Streaming-Efficiency](HackUTD-Research-Streaming-Efficiency.md)
- ✅ On-device learning and little-data accuracy → [HackUTD-Research-Learning](HackUTD-Research-Learning.md) (adaptation is low priority, per his call)
- ⬜ Quantization basics: INT8/INT4, GGUF, why the NPU needs it (for him to learn)
- ⬜ How to measure accuracy honestly in a demo (labeled clip set, agreement with the full model)

## Hardware / embedded
- ✅ Board comparison → [HackUTD-Research-Boards](HackUTD-Research-Boards.md)
- ✅ Practicals → [HackUTD-Research-Embedded](HackUTD-Research-Embedded.md):
  - Pi 5 GPIO (RP1; RPi.GPIO doesn't work)
  - real-time stepper control (AM62 M4F, i.MX 95 M7, or a microcontroller)
  - driver setup and Vref
  - power budget
  - talking between boards with no Wi-Fi
  - camera-following control loop
  - power logging
- ⬜ Pan/tilt mechanical design: printable mounts, bearing use, belt vs direct drive
- ⬜ Hailo model list: is YOLOE or any open-vocabulary model available?
- ⬜ Check the stepper driver model (A4988 / DRV8825 / TMC2209) and whether a microcontroller (Arduino/RP2040/ESP32) is in the kits

## Winning
- ✅ Judging, past winners, sponsor history, MLH prizes → [HackUTD-Research-Judging](HackUTD-Research-Judging.md) (merge with Godfrey's research)
- ⬜ Pitch structure: 60-second table demo, 2-minute video

## For Rafael to read before hacking (in this order)
1. How a cascade works: [Research-Edge-AI-Brief](Research-Edge-AI-Brief.md) §1 and §5
2. What an NPU does and why it needs quantization
3. Skim the Moondream or SmolVLM model page

## Round 3 (P0 fleet, 2026-11-07): ✅ all done
Track cards (NVIDIA, EOG, Property, Axxess, Niantic, Telecom, InfraDev), MLH prizes, Mechanical, Pi stack + offline, Firmware/wiring/buy, Claude loadout. See the hub Map.

## P1 (✅ done 2026-11-07)
- ✅ [HackUTD-Research-Track-FinanceLaw](../tracks/HackUTD-Research-Track-FinanceLaw.md)
- ✅ [HackUTD-Research-Judge-UI](HackUTD-Research-Judge-UI.md)
- ✅ [HackUTD-Research-Pitch-Demo](HackUTD-Research-Pitch-Demo.md)
- ✅ [HackUTD-Research-Risks](HackUTD-Research-Risks.md)
- ✅ [HackUTD-Research-NVIDIA-Winners](../tracks/HackUTD-Research-NVIDIA-Winners.md)
