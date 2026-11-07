---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, ideas]
---

# HackUTD 2026: Ideas

Part of [HackUTD-2026](HackUTD-2026.md). Score each against the real tracks at noon. Criteria: prize fit, demo wow, 16-hour risk.

## Leading concept: voice-directed vision cascade on a stepper pan/tilt
```
Stage 0  Pi 3/4: motion gate or wake word                       always on, ~0 cost
Stage 1  Pi 5: Moonshine STT → LFM2.5-230M tool call             "find the red toolbox" → set_target()
Stage 2  Hailo/Pi 5: YOLO every frame → steppers center target   (AM62 drives the motors)
Stage 3  Pi 5: Gemma 4 E2B only on new or uncertain events       confidence 0.35–0.7
Stage 4  Cloud VLM only if Stage 3 is still unsure
```
- **Novelty claim:** no published *measured* escalation rate exists for a detector → VLM cascade on a single-board computer. We show it live ([HackUTD-Research-Cascades](research/HackUTD-Research-Cascades.md)).
- **Overlay:** escalation funnel, cost per frame compared with always running the VLM, joules per hour, threshold slider.
- Fits his priorities: (a) speed and efficiency, (b) accuracy.

## Applications by track
| Track / sponsor | Application |
|---|---|
| CBRE | Facility sentry: checks a room for named objects (blocked exit, spill) |
| State Farm | Offline home-hazard inspector (space heater near curtains → written risk note) |
| Axxess / Healthcare | Bedside assistant that works with the Wi-Fi down; voice → hardware actions |
| EOG | Field gauge reader: points at a named gauge, zooms, reads it |
| Niantic Spatial / NVIDIA | Stretch goal: stepper turntable 3D capture, reconstruction on a laptop GPU |

## Round-2 upgrade: "Look less, think less" (fits his priorities a + b)
Three proven techniques stacked into one pipeline:
| Layer | Technique | Priority | Proven win |
|---|---|---|---|
| **Look less** | RLT temporal patch skipping (+ ToMe): skip computing image patches that didn't change | (a) speed | +35% throughput with no retraining; up to 80% fewer tokens ([HackUTD-Research-Streaming-Efficiency](research/HackUTD-Research-Streaming-Efficiency.md)) |
| **Think less** | Confidence cascade: escalate to Gemma/VLM only when unsure | (a) speed | up to 73% less latency, 77% less energy ([HackUTD-Research-Cascades](research/HackUTD-Research-Cascades.md)) |
| **Know more from less** | Few-shot prototypes on frozen DINOv2: teach a new object with 5 photos; VLM answers become new prototypes | (b) accuracy | ~90% chance it works in 3–5 h ([HackUTD-Research-Learning](research/HackUTD-Research-Learning.md)) |

- Pitch line: *"Most of a video stream is repeated pixels, and most frames don't need a big model. We stop computing both, and the system needs the big model less the longer it runs."*
- Overlay: token heatmap (skipped vs computed patches) · escalation funnel · J/hour vs dense baseline · accuracy vs full-VLM.
- Hardware: Pi 5 (CPU for RLT/DINOv2, Hailo for the dense YOLO baseline) → MCU + AccelStepper pan/tilt ([HackUTD-Research-Embedded](research/HackUTD-Research-Embedded.md)) · Pi 3/4 gate · AM62 / i.MX 95 as networked nodes · INA219 power.
- **Cut order if behind:** the DINOv2 prototypes go first, then RLT. The cascade + pan/tilt is the minimum product.

## Rejected (with reason)
KAN (MLPs win at equal compute) · BitNet (no faster) · speculative decoding (slower on Pi 5) · VLM token pruning (GPU/7B+ only) · MeZO/PockEngine (solve problems a Pi doesn't have) · V-JEPA 2 (too big) · i.MX 95 NPU/M7 (toolchain risk).
