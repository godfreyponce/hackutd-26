---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, edge-ai, efficiency]
---

# Research: Efficient Streaming-Data Techniques

Part of [HackUTD-2026](../HackUTD-2026.md). Agent research, 2026-11-07. Priority (a), speed and efficiency.

**Main point:** on a Pi 5 CPU, ViT cost grows roughly in line with token count, so **dropping tokens gives real wall-clock speed** (GPUs often don't). The **Hailo-8 needs fixed input shapes**, so token dropping must run on the CPU; the Hailo can serve as the dense baseline.

## Techniques
| Technique | Paper | Measured win | Code | 6–10 h? |
|---|---|---|---|---|
| **RLT, "Don't Look Twice"** (drop patches unchanged since the last frame) | NeurIPS 2024 Spotlight, arXiv 2411.05222 | **+35% throughput, no retraining, −0.1% accuracy**; up to 80% fewer tokens on long video | github.com/rccchoudhury/rlt | ✅ about 30 lines on a timm DeiT-Tiny |
| Eventful Transformers (per-layer reuse of tokens) | ICCV 2023, arXiv 2308.13494 | 2–4× compute savings | github.com/WISION-Lab/eventful-transformer | Stretch |
| ReuseViT / Déjà Vu | PVLDB 2025, arXiv 2506.14107 | 2.64× faster embeddings | GPU-heavy | ❌ cite only |
| **ToMe** (token merging) | ICLR 2023 Oral, arXiv 2210.09461 | about 2× throughput, −0.2–0.3% accuracy | github.com/facebookresearch/ToMe | ✅ stack it on RLT |
| FastV / VisionZip (VLM token pruning) | ECCV 2024 / CVPR 2025 | −45% FLOPs / 10% of tokens, 8× prefill | GitHub | ❌ built for 7B+ VLMs on GPU |
| minGRU / minLSTM | arXiv 2410.01201 | 175–1324× faster *training* than GRU; no inference speedup shown | none | ✅ streaming audio state |
| CfC / Liquid networks | Nat. Mach. Intell. 2022 | no measured speedup found | `pip install ncps` | Hype caution |
| MambaLite-Micro | arXiv 2509.05488 | −83% peak memory on ESP32/STM32 | none | ❌ |
| **HDC** (hyperdimensional) | TorchHD (JMLR 2023); DecoHD arXiv 2511.03911 | One-shot learning in milliseconds; accuracy below a CNN on raw pixels | `pip install torch-hd` | ✅ use it on features |
| KAN | "KAN or MLP" arXiv 2407.16674 | **MLPs generally win** at equal parameters and FLOPs | — | ❌ hype |
| Event-camera emulation | Raw2Event arXiv 2509.06767 | real-time on a Pi (no rate given) | anon repo | Use it as the visual for RLT |
| Split computing / feature compression | FrankenSplit arXiv 2302.10681 | −60% bitrate vs prior methods, up to 16× faster than codec offloading | — | Simplified version ✅ |

## Ranked top 4
1. **RLT patch skipping + ToMe on a small ViT (Pi 5 CPU).** On a stepper pan rig: still scene → FPS climbs and the token heatmap goes dark; motion → only the moving patches light up. Shown side by side with the dense model. *Pitch: "Most of a video stream is the same pixels repeated. We stop computing them."*
2. **HDC on-device learning** (TorchHD on MFCCs or frozen embeddings): a judge says a new word 3 times, and the Pi learns it and drives the stepper.
3. **minGRU streaming keyword spotting:** constant per-hop latency, compared with a sliding-window CNN.
4. **Feature compression between boards:** bytes per frame vs JPEG with accuracy held; throttle the link live.

## Sources
arxiv.org/abs/2411.05222 · rccchoudhury.github.io/rlt/ · github.com/rccchoudhury/rlt · arxiv.org/abs/2308.13494 · github.com/WISION-Lab/eventful-transformer · arxiv.org/abs/2506.14107v1 · arxiv.org/abs/2210.09461 · arxiv.org/abs/2403.06764 · arxiv.org/abs/2412.04467 · arxiv.org/abs/2410.01201 · github.com/raminmh/CfC · arxiv.org/abs/2509.05488 · github.com/hyperdimensional-computing/torchhd · arxiv.org/abs/2511.03911 · arxiv.org/abs/2407.16674 · arxiv.org/abs/2509.06767 · arxiv.org/abs/2302.10681
