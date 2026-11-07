---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, edge-ai, cascades]
---

# Research: Model Cascades on the Edge

Part of [HackUTD-2026](../HackUTD-2026.md) · summary in [Research-Edge-AI-Brief](Research-Edge-AI-Brief.md). Agent research, 2026-11-07.

**Bottom line:** build a **detector-gated VLM cascade**. A cheap detector runs on every frame; the VLM runs only on new or uncertain events. It is cheap to build and easy to show. A VLM on a bare Pi 5 takes **tens of seconds per image**, so the escalation rate is the whole point of the demo. Skip speculative decoding and learned routers.

## Variants
- **Confidence-threshold cascade:** the small model answers when its confidence ≥ τ; otherwise it escalates. ✅ Core build.
- **Router / learned deferral:** a separate classifier predicts when the small model will be wrong. Stretch only (needs labeled data).
- **Early-exit network:** one network with intermediate heads. ❌ Needs training.
- **Edge-cloud split:** the big model lives in the cloud. ✅ Last stage.
- **Speculative decoding:** a small draft model and a big verifier; speedup only. ❌ It is a **slowdown on a Pi 5**.

## Papers and results
| Work | Result |
|---|---|
| FlexSpec, arXiv 2601.00644 (Jan 2026) | Jetson AGX Orin 1.88–2.10× faster; **Raspberry Pi 5 0.72–0.85× (slower)** |
| Confidence-Driven Multi-Scale Model Selection, EACL 2026, arXiv 2602.22090 | Near-largest-model accuracy on MMLU at **20–40% less compute**; GPT-4o tokens −60% |
| ECVL-Router, arXiv 2510.27256 (Oct 2025) | **>80% of queries on the small model**, <10% drop |
| Gatekeeper (Google), arXiv 2502.19335, NeurIPS 2025 poster | Fine-tuning that teaches the small model to know when it is unsure; deferral performance about 2× (TinyImageNet), 7–10× (ARC) |
| When Tiny Falls Short, Go Hierarchical (IMDEA), IEEE IoT-J Jul 2025 | **Up to 73% less latency, 77% less device energy** at equal accuracy; early exit adds −59.7% latency / −60.4% energy |
| E4, AAAI 2025, arXiv 2503.04865 | Early exit + DVFS: up to 2.8× speedup, about 26% energy saved |
| Edge Impulse cascading with VLMs (Jul 2025 blog) | YOLO → tracker → LLaVA only on a new vehicle; no numbers |
| Dual-Model Distillation, arXiv 2410.12165 | Switcher model offloads uncertain cases; no numbers in the abstract |
| dev.to practitioner post (unverified) | SSD detector → cloud VLM, about 3% of frames escalated |

**Gap = our novelty:** no paper reports a measured escalation rate for a detector → VLM cascade on a single-board computer.

## Stage latencies found
- YOLO26n on Pi 5: **36.6 ms** (Arm runtime) / 67.2 ms (NCNN). TI AM62A (2 TOPS) YOLOX-Nano: 8.69 ms vs 321 ms on a plain AM625.
- Moondream 2B on Pi 5 8 GB: about **29 s encode + 41 s answer**. SmolVLM-256M: no Pi number, so benchmark it in hour 1.
- LLMs on Pi 5 CPU: ≤1.5B at 5–15 tok/s; 3B at 2–5 tok/s; <360M at >20 tok/s; about 10 W (arXiv 2511.07425).
- Pi 5 + DEEPX NPU HAT: Qwen3-1.7B time-to-first-token about 0.55–0.60 s (Raspberry Pi blog, Oct 2026).
- i.MX 95 GenAI Flow: about 9 tok/s (forum, unverified).

## Demo metrics for judges
- **Escalation funnel** (frames → gate → detector → VLM → cloud). This is the headline.
- Effective cost per frame vs always-VLM (30+ s/frame on a Pi 5).
- Energy from a USB-C meter or INA219: J/hour, cascade vs always-on.
- Accuracy kept: 50–100 labeled clips, agreement with the full-VLM answer.
- Live τ slider (escalation vs accuracy) · p50/p95 latency per stage · cloud calls avoided.

## Sources
arxiv.org/html/2601.00644 · arxiv.org/abs/2602.22090 · arxiv.org/abs/2510.27256 · arxiv.org/abs/2502.19335 · dspace.networks.imdea.org/handle/20.500.12761/1958 · arxiv.org/abs/2503.04865 · edgeimpulse.com/blog/coming-soon-in-edge-ai-model-cascading-with-vlms/ · arxiv.org/abs/2410.12165 · arxiv.org/html/2511.07425v1 · raspberrypi.com/news/seeing-understanding-and-responding-low-power-cnn-vlm-and-slm-workloads-on-raspberry-pi-5/ · learn.arm.com/learning-paths/embedded-and-microcontrollers/yolo26-arm-runtime/compare-performance/ · ti.com/technologies/edge-ai/use-cases/object-detection-vision-systems.html · forum.dexterindustries.com/t/moondream-vision-language-assistant-on-gopigo3-robot-kilted-dave/10750
