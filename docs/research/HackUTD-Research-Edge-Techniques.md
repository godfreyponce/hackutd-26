---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, edge-ai]
---

# Research: Edge-AI Tools and Models (mid-2025 → now)

Part of [HackUTD-2026](../HackUTD-2026.md) · summary in [Research-Edge-AI-Brief](Research-Edge-AI-Brief.md). Agent research, 2026-11-07.

## Usable this weekend (Pi 5 CPU numbers)
| Tool | Date | Pi 5 result | Setup |
|---|---|---|---|
| **Moonshine Voice** (streaming STT) | Feb 2026 | **237 ms** Tiny / 527 Small / 802 Medium; Whisper Tiny 5,863 ms. WER 12.0 / 7.84 / 6.65% | `pip install moonshine-voice` |
| **Gemma 4 E2B on LiteRT-LM** (multimodal) | Aug 2026 | 9 tok/s decode, 99 tok/s prefill, 1.4 GB | `pip install litert-cli`; HF token |
| **LFM2.5-230M** (tool calling) | Jun 2026 | **42 tok/s**, 293 MB | GGUF / llama.cpp |
| **YOLO26n** | 2026 | 101 ms/frame CPU | `pip install ultralytics` |
| **YOLOE-26** (open vocabulary) | 2025–26 | 3–5 FPS at 320 px | `set_classes([...])`; cache the 254 MB text encoder |
| FunctionGemma (270M) | Dec 2025 | about 22 tok/s; 58% → 85% after fine-tuning | Ollama / llama.cpp |
| Gemma 3n E2B | 2025 | about 6 tok/s, 2.5 GB | Ollama |
| Moondream 2 / 0.5B | Jun 2025 | No Pi speed published; 2B int4 about 2 GB RAM | pip |

## Real but skip
- **Moondream 3/3.1** (9B MoE): too big.
- **BitNet b1.58**: 6.4 tok/s, no faster than Q4, painful build.
- **AI HAT+ 2 for LLMs**: slower than the CPU.
- **Qwen3-VL-2B**: needs an AX8850 card.
- **LFM2.5-VL-1.6B**: no Pi numbers.
- **FastVLM**: Apple-focused.

## GPU only
- **VGGT** (feed-forward 3D, >1.2B params): struggles even on a Jetson Orin NX 16 GB; laptop GPU only.
- **Gaussian splatting on a Pi**: render-only at about 3.6 FPS.

## Trends
- Speech-to-text on small boards is solved (Moonshine).
- Sub-300M models now do tool calling, which makes offline voice → hardware agents possible.
- Multimodal models fit in under 1.5 GB but stay slow, so they need gating (that is why cascades matter).
- 3D understanding hasn't reached small boards yet.

## Top 5 ideas from this round
1. Moonshine + YOLOE voice-retargeted pan/tilt detector (CBRE)
2. Offline speech → LFM2.5/FunctionGemma tool calls → motors and GPIO (Axxess)
3. YOLO26n-gated Gemma 4 E2B hazard describer (State Farm)
4. Moondream `point` aims a laser or camera with the steppers (EOG); test its speed first
5. Stretch: turntable capture → VGGT on a laptop (Niantic / NVIDIA)

## Sources
raspberrypi.com/news/mastering-edge-ai-on-raspberry-pi-with-litert-and-gemma · electronicsforu.com/news/google-toolkit-brings-local-ai-to-raspberry-pi-5 · moondream.ai/blog/moondream-3-1-beyond-benchmarks · moondream.ai/models · liquid.ai/blog/lfm2-5-230m · huggingface.co/LiquidAI/LFM2.5-VL-1.6B · kunalganglani.com/blog/gemma-3-raspberry-pi-5-benchmark.md · gigazine.net/gsc_news/en/20260225-moonshine-voice · github.com/moonshine-ai/moonshine · arxiv.org/html/2601.20317v1 · cnx-software.com/2026/01/20/raspberry-pi-ai-hat-2-review-a-40-tops-ai-accelerator-tested-with-computer-vision-llm-and-vlm-workloads/ · blog.google/technology/developers/functiongemma/ · docs.ultralytics.com/models/yoloe/ · docs.sunfounder.com/projects/ai-lab-kit/en/latest/yolo/yolo_yoloe.html · learn.adafruit.com/local-llms-on-raspberry-pi/bitnet · docs.m5stack.com/en/compute/llm_8850_card/m5_llm_8850_qwen3_vl_2b
