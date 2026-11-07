# HackUTD 2026: Edge-AI Research Brief (2026-11-07, 7:45 AM)

Three research agents, merged. Every number below has a source in the list at the bottom. **(unverified)** marks claims nobody opened a source for.

## 1. Main findings
- **Model cascades are proven.** Peer-reviewed results: **up to 73% lower latency and 77% lower energy** at the same accuracy (IMDEA, IEEE IoT-J 2025).
  - Adding early exit cuts a further ~60%.
  - Confidence-based escalation gets close to the large model's accuracy at **20–40% less compute** (EACL 2026).
  - Edge-to-cloud VLM routers handle **>80% of queries on the small model** (ECVL-Router, Oct 2025).
- **Gap we can fill:** no paper reports a *measured escalation rate* for a detector-to-VLM cascade on a single-board computer. Showing that number live is our novelty claim.
- **Speculative decoding on a Pi 5 is a net slowdown** (0.72–0.85×; FlexSpec, Jan 2026). Skip it.
- **The FRDM i.MX 95 is NOT stronger than a Pi 5 for AI.**
  - CPU: 6× Cortex-A55 (in-order, 2.0 GHz) vs the Pi's 4× Cortex-A76 (2.4 GHz).
  - NPU: about 2 TOPS, and only the CNN/vision path is mature. LLM support (GenAI Flow) is narrow and depends on the silicon revision.
  - Toolchain risk for a hackathon is high.
- **3D reconstruction (VGGT, Gaussian-splat training) does not run on these boards.** It needs a laptop GPU or a Jetson.

## 2. Board roles
| Board | Role |
|---|---|
| Pi 5 (8 GB) | Main AI node: detector + small LLM/VLM on CPU |
| Pi 5 + AI HAT+ (Hailo-8, 26 TOPS, ~$110) | Optional buy. YOLO runs at 30+ FPS from the model zoo. **For vision only** |
| AI HAT+ 2 (Hailo-10H) | **Don't buy for LLMs.** It is slower than the Pi CPU (6.7 vs 11.7 tok/s) |
| Jetson Orin Nano Super (~$249) | Only worth buying if we want 3D or a fast VLM. Llama-3.2-3B runs at ~43 tok/s. Dallas stock unverified |
| i.MX 95 | Skip its NPU unless eIQ is already working. Could serve as a CPU node |
| AM62 | I/O and stepper controller. It has no NPU |
| Pi 3 / Pi 4 | Always-on gate (motion or wake word), or a sensor node |

## 3. Verified building blocks (Pi 5 CPU numbers)
| Block | What it does | Pi 5 number | Setup |
|---|---|---|---|
| **Moonshine Voice** (Feb 2026) | Streaming speech-to-text | **237 ms** (Tiny) vs Whisper Tiny 5,863 ms | `pip install moonshine-voice` |
| **YOLO26n** | Detector | 101 ms/frame CPU; 36.6 ms with Arm's runtime | `pip install ultralytics` |
| **YOLOE-26** | Open-vocabulary detector: you name the classes in text | 3–5 FPS at 320 px | `set_classes([...])`. **Download the 254 MB text encoder before going offline** |
| **Gemma 4 E2B on LiteRT-LM** (Aug 2026) | Small multimodal model (text, image, audio) | **9 tok/s**, 1.4 GB RAM | `pip install litert-cli`; needs an HF token |
| **LFM2.5-230M** (Jun 2026) | Tiny tool-calling model | **42 tok/s**, 293 MB | GGUF + llama.cpp |
| FunctionGemma (Dec 2025) | 270M function-calling model | ~22 tok/s | Ollama / llama.cpp; best after fine-tuning |
| Qwen2.5-1.5B | General small LLM | ~11.7 tok/s | Ollama |
| Moondream 2 | VLM with `detect` and `point` | **No Pi speed published.** Expect it to be slow | pip |

## 4. Recommended core: a voice-directed vision cascade on a stepper pan/tilt
```
Stage 0  Pi 3/4: motion gate (frame difference) or wake word      always on, ~0 cost
Stage 1  Pi 5: Moonshine STT → LFM2.5-230M tool call               "find the red toolbox" → set_target()
Stage 2  Pi 5: YOLOE/YOLO26n every frame → steppers center target  (AM62 or Pi GPIO drives the motors)
Stage 3  Pi 5: Gemma 4 E2B only on new or uncertain events         confidence 0.35–0.7 → describe / judge
Stage 4  Cloud VLM only when Stage 3 is still unsure
```
- The application framing gets chosen at noon, once the tracks are announced: CBRE facility sentry, State Farm home-hazard inspector, Axxess home-health assistant, or EOG gauge reader.
- **Stretch goal:** a stepper turntable for 3D capture, with reconstruction on a laptop GPU (Niantic Spatial). Tell judges the 3D runs off the board.

## 5. How to show the win (on-screen overlay)
- **Escalation funnel:** frames → passed gate → detector → VLM → cloud, as live counts and percentages. This is the headline.
- **Cost per frame:** the cascade compared with "always run the VLM", which is 30+ s per frame on a Pi 5.
- **Energy:** USB-C inline power meter, joules per hour for the cascade vs the always-on VLM.
- **Accuracy kept:** 50–100 labeled clips, measuring agreement with the full-VLM answer.
- **Live threshold slider:** escalation rate against accuracy.
- **Per-stage latency:** p50 and p95.

## 6. Do in the first 2 hours (de-risk)
1. Benchmark on the Pi 5: Gemma 4 E2B, SmolVLM-256M and Moondream 2. Keep the fastest that gives acceptable quality.
2. Moonshine running from the USB mic.
3. YOLOE `set_classes` working. Cache all weights locally, because venue Wi-Fi will be slow.
4. Steppers turning from Python on the AM62 or Pi, **with the 12–24 V supply**.

## Sources
Cascades: arxiv.org/html/2601.00644 · arxiv.org/abs/2602.22090 · arxiv.org/abs/2510.27256 · arxiv.org/abs/2502.19335 · dspace.networks.imdea.org/handle/20.500.12761/1958 · arxiv.org/abs/2503.04865 · edgeimpulse.com/blog/coming-soon-in-edge-ai-model-cascading-with-vlms/ · arxiv.org/html/2511.07425v1 · raspberrypi.com/news/seeing-understanding-and-responding-low-power-cnn-vlm-and-slm-workloads-on-raspberry-pi-5/ · learn.arm.com/learning-paths/embedded-and-microcontrollers/yolo26-arm-runtime/compare-performance/

Boards: nxp.com/design/design-center/development-boards-and-designs/FRDM-IMX95 · docs.ultralytics.com/integrations/nxp/ · developer.ridgerun.com/wiki/index.php/NXP_i.MX95_Technical_Guide/eIQ_Neutron_NPU_overview · cnx-software.com/2026/01/20/raspberry-pi-ai-hat-2-review-a-40-tops-ai-accelerator-tested-with-computer-vision-llm-and-vlm-workloads/ · jetson-ai-lab.com/archive/benchmarks.html · microcenter.com/product/705302/raspberry-pi-ai-hat-2

Techniques: raspberrypi.com/news/mastering-edge-ai-on-raspberry-pi-with-litert-and-gemma · liquid.ai/blog/lfm2-5-230m · github.com/moonshine-ai/moonshine · gigazine.net/gsc_news/en/20260225-moonshine-voice · docs.ultralytics.com/models/yoloe/ · docs.sunfounder.com/projects/ai-lab-kit/en/latest/yolo/yolo_yoloe.html · blog.google/technology/developers/functiongemma/ · arxiv.org/html/2601.20317v1 · moondream.ai/models · huggingface.co/LiquidAI/LFM2.5-VL-1.6B
