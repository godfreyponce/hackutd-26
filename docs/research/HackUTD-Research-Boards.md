---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, hardware, edge-ai]
---

# Research: Edge-AI Board Comparison

Part of [HackUTD-2026](../HackUTD-2026.md) · summary in [Research-Edge-AI-Brief](Research-Edge-AI-Brief.md). Agent research, 2026-11-07.

**Verdict:** the FRDM i.MX 95 is **not** more powerful than the Pi 5 for AI.
- **CPU:** 6× in-order Cortex-A55 at 2.0 GHz, against the Pi's 4× Cortex-A76 at 2.4 GHz.
- **NPU:** about 2 TOPS. The CNN path is mature; the LLM path is fragile.

Its strengths are industrial: safety cores, ISP, TSN networking, ECC.

## Comparison
| Board | CPU | NPU | RAM | Price | AI reality |
|---|---|---|---|---|---|
| **FRDM i.MX 95** (owned) | 6× A55 @ 2.0 + M7 + M33 | eIQ Neutron, about 2 TOPS | 8 GB | $210 | INT8 TFLite, batch 1; attention ops fall back to CPU. No published YOLOv8n FPS. LLM about 9 tok/s (forum, unverified) |
| **Raspberry Pi 5** (owned) | 4× A76 @ 2.4 | none | 8 GB | — | YOLOv8n CPU 5–8 FPS; **Qwen2.5-1.5B 11.7 tok/s, Llama-3.2-3B 4.8 tok/s** |
| Pi 5 + **AI HAT+ 26T (Hailo-8)** | — | 26 TOPS | host | ~$110 | **Vision only**. YOLOv8n about 136 FPS (batch 8). Model-zoo models run in minutes |
| Pi 5 + AI HAT+ 2 (Hailo-10H) | — | 40 TOPS, 8 GB onboard | — | $130 | Runs LLMs and VLMs but **slower than the Pi CPU** (Qwen2.5-1.5B 6.7 vs 11.7 tok/s) |
| **SK-AM62B** (owned) | 4× A53 @ 1.4 + M4F | **none** | ~2 GB | — | Slowest; use it as a controller |
| SK-AM62A | 4× A53 | C7x+MMA, 2 TOPS | — | $249 | CNN vision via TIDL |
| Jetson Orin Nano Super | 6× A78AE | GPU, 67 TOPS sparse | 8 GB | $249 | **Llama-3.2-3B 43 tok/s**; runs everything; TensorRT |

## Key answers
- **i.MX 95 NPU for LLMs:** only through NXP's GenAI Flow (Danube about 500M, INT4/INT8). NXP says time-to-first-token is about half the CPU's. LLM support depends on the silicon revision (A1 vs B0), and the forum reports conflict.
- **llama.cpp, i.MX 95 vs Pi 5 CPU:** the Pi should win. Prompt processing should be about 2–4× faster; token generation is closer because memory bandwidth is similar. This is inferred, not benchmarked.
- **Bring-up risk:** eIQ is **high** (needs an x86 Linux host, a matching BSP and firmware, INT8 calibration, silent CPU fallback). Hailo zoo models are **low**; compiling your own model with the DFC is risky.
- **Recommendation:** Pi 5 + AI HAT+ 26T (YOLO on the Hailo, LLM on the CPU). Jetson only if the build needs a fast VLM or 3D. Use the AM62 as the motor/I-O node.

## Unverified
Micro Center Dallas stock · i.MX 95 YOLO FPS · i.MX 95 llama.cpp numbers · "8 eTOPS" on the PRO board · current Pi and HAT prices.

## Sources
nxp.com/design/design-center/development-boards-and-designs/FRDM-IMX95 · nxp.com/products/i.MX95 · linuxgizmos.com/nxp-frdm-i-mx-95-pro-pairs-six-cortex-a55-cores-with-8-etops-ai-acceleration/ · nxp.com/company/about-nxp/smarter-world-blog/BL-BRINGING-GENERATIVE-AI-EDGE · docs.ultralytics.com/integrations/nxp/ · developer.ridgerun.com/wiki/index.php/NXP_i.MX95_Technical_Guide/eIQ_Neutron_NPU_overview · raspberrypi.com/products/raspberry-pi-5/ · cnx-software.com/2026/01/20/raspberry-pi-ai-hat-2-review-a-40-tops-ai-accelerator-tested-with-computer-vision-llm-and-vlm-workloads/ · sixfab.com/blog/raspberry-pi-5-ai-hat-benchmark-deepx-vs-hailo/ · microcenter.com/product/705302/raspberry-pi-ai-hat-2 · jetson-ai-lab.com/archive/benchmarks.html · ti.com/tool/SK-AM62B
