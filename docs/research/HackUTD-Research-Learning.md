---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, edge-ai, few-shot]
---

# Research: On-Device Learning and Little-Data Accuracy

Part of [HackUTD-2026](../HackUTD-2026.md). Agent research, 2026-11-07. He ranked device adaptation (c) low. The **few-shot prototype** item still serves (b), accuracy from little data.

**Constraint:** the Hailo-8 is inference-only (from general knowledge, unverified). All learning happens on the Pi 5 CPU or the laptop.

## Techniques
| Technique | Key paper | Result | Code | Verdict |
|---|---|---|---|---|
| Tiny training / PockEngine / TinyTrain | NeurIPS 2022 (2206.15472), MICRO 2023 (2310.17752), ICML 2024 (2307.09988) | 256 KB training; up to 15× faster on a Pi; TinyTrain +3.6–5.0%, −1,098× backward memory | TinyTrain repo | ❌ solves MCU memory limits a Pi doesn't have |
| MeZO zeroth-order | arXiv 2511.11362 | no numbers in the abstract | princeton-nlp/MeZO | ❌ too slow |
| **Forward-only TTA (FOA)** | ICML 2024 Oral, arXiv 2404.01650 | 8-bit ViT + FOA beats full-precision TENT; −24× memory | github.com/mr-eggplant/FOA | Highest novelty, about 45% chance it works |
| LeanTTA / ELaTTA | arXiv 2503.15889 / 2510.11068 | 11.2 MB peak; −64.7× compute vs MEMO, ran on a Pi 5 | none | Cite only |
| **Few-shot prototypes on frozen DINOv2** | 12 mJ/class FSCIL, DATE 2024 (2403.07851); DINOv2 (2304.07193) | 68.62% CIFAR100 FSCIL on a 60 mW MCU | facebookresearch/dinov2 | ✅ about 90%, 3–5 h |
| Federated learning across the Pis (Flower) | Flower Pi 5 blog, Dec 2023 | Pi 5 about 2× the Pi 4; 53M-param ViT trains on 1k images in about 12 min | adap/flower | ✅ federate the *prototypes* (KB per round) |
| **Continual anomaly detection** (PatchCore-style) | EEAI 2025, arXiv 2512.13497 | +12% AUROC, −80% memory | Anomalib | ✅ about 85%; learns "normal" in seconds |
| Teacher → student auto-labeling | arXiv 2411.16196, 2609.20441 (not opened) | — | — | ✅ as an add-on to the prototypes |
| V-JEPA 2 world model | arXiv 2506.09985 | zero-shot robot pick-and-place | facebookresearch/vjepa2 | ❌ about 1B params, slides only |

## Ranked top 4
1. **DINOv2 few-shot prototypes + laptop-VLM auto-labeling when unsure:** show it 5 photos of an object and it sorts that object correctly; a counter shows teacher queries dropping.
2. **Federated prototype sharing across 4 Pis:** teach Pi 1 an object, and Pi 4 recognizes it after one round.
3. **Continual anomaly detection** with a heatmap: steppers present parts, and defective ones get rejected.
4. **FOA test-time adaptation:** fog the camera, and accuracy crashes then recovers. Hard 4-hour cap.

## Sources
arxiv.org/abs/2206.15472 · hanlab.mit.edu/projects/pockengine · arxiv.org/abs/2307.09988v2 · arxiv.org/abs/2511.11362 · arxiv.org/abs/2404.01650 · github.com/mr-eggplant/FOA · arxiv.org/abs/2503.15889 · arxiv.org/abs/2510.11068 · arxiv.org/abs/2403.07851 · arxiv.org/abs/2304.07193 · flower.ai/blog/2023-12-07-raspberrypi-is-ready-for-fl · github.com/jafermarq/federated-embedded-vision · arxiv.org/abs/2512.13497 · arxiv.org/abs/2506.09985 · arxiv.org/abs/2604.22783
