---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, edge-ai]
---
Part of [HackUTD-2026](../HackUTD-2026.md). Companion to [Research-Edge-AI-Brief](Research-Edge-AI-Brief.md), [HackUTD-Research-Embedded](HackUTD-Research-Embedded.md), [HackUTD-Research-Streaming-Efficiency](HackUTD-Research-Streaming-Efficiency.md).

**Bottom line:** flash the current Trixie 64-bit image, confirm `hailo-all` builds on its kernel *before noon*, and run every model once while online. Several tools fetch things on first use: Hailo apps fetch HEFs, YOLOE pip-installs CLIP from GitHub, Moonshine downloads its models.

## 1. Hailo-8 model zoo: what is precompiled
- **Open-vocab detection: no.** On Hailo-8, Model Zoo `master` lists "Zero-shot Object Detection" as **NA**. No YOLOE. YOLO-World V2-S came in the v5.1.0 release, which is the Hailo-10H toolchain (DFC 5.x). I found no Hailo-8 HEF for it [u]. **YOLOE stays on the CPU** (or export fixed classes to ONNX).
- **CLIP: yes, image encoders only, on Hailo-8.** The HEFs are compiled with DFC v2.20.0. Batch-1 FPS from the zoo: clip_resnet_50 74, clip_vit_b_32 34 (used by hailo-apps), clip_vit_b_16 29, tinyclip_vit_8m_16 100, siglip2_b_32 16. The text side runs on the CPU (the standalone `hailo-CLIP` repo does this; [u] for hailo-apps). **Use:** Hailo CLIP with fixed text prompts is a credible open-vocab fallback that puts no load on the CPU.
- **Zero-shot segmentation:** fast_sam_s (640², about 40–65 FPS).
- **Detectors ready (COCO):** yolov8n/s/m/l/x, yolov11n–x, yolo26n/s/m, yolov10, yolov5/6/7/9, yolox, nanodet, ssd_mobilenet, efficientdet_lite.
- **Pose:** yolov8s_pose 393 FPS, yolov8m_pose 69, centerpose.
- **Instance segmentation:** yolov8n_seg 528, yolov11n_seg 132, yolov11s_seg 91, yolo26s_seg 65, yolov5n_seg 464.
- Also listed for Hailo-8: depth, face recognition, Re-ID, MOT, and others.
- The camera stack has built-in Hailo post-process JSONs in `/usr/share/rpi-camera-assets/` (`hailo_yolov8_inference.json`, `hailo_yolov8_pose.json`, `hailo_yolov5_segmentation.json`).

## 2. hailo-all on current Pi OS
- **The current image is Trixie (Debian 13), kernel 6.18, released 6 Oct 2026.** A Legacy Bookworm image (kernel 6.12) is also published.
- Raspberry Pi docs give the AI HAT+ install on **64-bit Trixie**:
  1. `apt full-upgrade`
  2. `rpi-eeprom-update -a`
  3. `sudo apt install dkms`, then `sudo apt install hailo-all`
  4. Reboot.
  5. Check with `hailortcli fw-control identify`.
- Since Dec 2025 the driver is **built by DKMS**, not shipped in the kernel. `hailo-all` (Hailo-8) and `hailo-h10-all` (AI HAT+ 2) cannot coexist.
- **Known breakage pattern:** in May–Aug 2026, kernels ≥6.15 broke the DKMS build of Hailo's **10H** driver 5.3.0 (`del_timer_sync` was removed). Hailo said only 5.1.1 is supported on the Pi, and that mixing 5.1 and 5.3 packages breaks it.
- Older threads report other failures: DKMS and userspace version mismatch (4.19 vs 4.20), stale in-kernel `hailo_pci` modules (fix: delete them and run `depmod -a`), and unreleased 4.21 drivers.
- **I found no report on Hailo-8 `hailo-all` against kernel 6.18 [u].**
- **Mitigation:**
  - After installing, check that `dkms status` shows the module built, and look at `dmesg | grep -i hailo`.
  - Never `apt upgrade` at the venue.
  - Keep a second SD card with Legacy Bookworm 64-bit (kernel 6.12) as a fallback.

## 3. Reported Pi 5 CPU speeds
| Model | Reported | Source quality |
|---|---|---|
| DeiT-Tiny 224² | **26.4 ms** p50 INT8, 35.3 ms FP32 (ExecuTorch with XNNPACK) | Arm model card |
| DINOv2 ViT-S/14 | **unknown**: no Pi 5 number found. It has about 4× the parameters of DeiT-Tiny, so expect roughly 100–200 ms at 224² [u] | none |
| SmolVLM-256M / 500M | **unknown on Pi 5**. Benchmark with `llama-bench` | none |
| Moondream 2 (2B) | load 21 s, image encode 29 s, answer 41 s (8 GB Pi 5, Feb 2026) | forum post |
| Gemma 4 E2B (LiteRT-LM, CPU) | prefill 133 tok/s, decode 7.6–8 tok/s, TTFT 7.8 s, 1.5 GB RAM | Google and HF card |
| Moonshine Tiny Streaming | 237 ms; Small Streaming 527 ms | README via search [u] |

**Implication:** Moondream 2 is too slow to be the "unsure" tier. Gemma 4 E2B or SmolVLM fits that tier better.

## 4. Offline download checklist
**Weights** (all ungated as far as the pages show):

| Item | Repo / file | Size |
|---|---|---|
| Gemma 4 E2B | `litert-community/gemma-4-E2B-it-litert-lm` → `gemma-4-E2B-it.litertlm` | 2.59 GB, Apache-2.0, **no gate shown** (the licence-accept step is likely not needed [u]) |
| SmolVLM-256M | `ggml-org/SmolVLM-256M-Instruct-GGUF` → Q8_0 gguf + `mmproj-…-Q8_0.gguf` | 175 MB + 104 MB |
| SmolVLM-500M | `ggml-org/SmolVLM-500M-Instruct-GGUF` → Q8_0 gguf + mmproj Q8_0 | 437 MB + 109 MB |
| Moondream 2 (optional) | `vikhyatk/moondream2`, rev `2025-06-21`, needs `trust_remote_code` | about 3.7 GB BF16 [u] |
| DINOv2-S | `facebook/dinov2-small` → `model.safetensors` + configs | 88 MB |
| DeiT-Tiny | timm `deit_tiny_patch16_224.fb_in1k` | about 22 MB [u] |
| LFM2.5-230M | `LiquidAI/LFM2.5-230M-GGUF` → Q4_K_M | 153 MB (Q8_0 247 MB), licence lfm1.0 |
| YOLOE | `yoloe-26s-seg.pt` (+ `-pf`), `yoloe-11s-seg.pt`, and **`mobileclip2_b.ts` (about 254 MB)** | Ultralytics assets |
| YOLO CPU fallback | `yolo11n.pt` / `yolo26n.pt` | small [u] |
| Moonshine | `python -m moonshine_voice.download --language en` (Tiny Streaming about 34 MB [u]) | |
| Hailo HEFs | `yolov8s/m`, `yolov8s_pose`, `yolov11n_seg`, `clip_vit_b_32_image_encoder` (DFC 2.20 links on zoo pages) | |

**Packages to download:**
- **apt:**
  - `dkms hailo-all rpicam-apps python3-picamera2 mosquitto mosquitto-clients chromium`
  - Build tools for llama.cpp: `git cmake build-essential libcurl4-openssl-dev`
  - Pre-cache the debs with `sudo apt install --download-only …` (they land in `/var/cache/apt/archives`).
- **pip:**
  - `torch torchvision` (the PyPI aarch64 wheels are CPU builds [u]), `timm transformers accelerate huggingface_hub ultralytics>=8.4.0 onnxruntime moonshine-voice paho-mqtt pillow numpy`
  - Also `git+https://github.com/ultralytics/CLIP.git`, which YOLOE otherwise installs from the network on its first `set_classes()`.
- **LiteRT-LM:** `uv tool install litert-lm`. The docs give only the uv route; a pip route is unconfirmed [u].
- **llama.cpp:** clone and build on the Pi this morning. Build `llama-server`, `llama-cli`, `llama-mtmd-cli`, and `llama-bench`.
- **hailo-apps:** clone it and run `./install.sh`. Run each app once, because HEFs "are downloaded automatically on first use".

**Wheelhouse (do it on the Pi itself so you get aarch64 / cp313 wheels):**
- `pip download -d ~/wheelhouse -r requirements.txt`
- At the venue: `pip install --no-index --find-links ~/wheelhouse -r requirements.txt`

**HF cache:**
- `hf download <repo> <files>` while online, into `HF_HOME=~/hf`.
- Then at the venue: `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`.
- Copy `~/.cache/moonshine_voice` and the Ultralytics weights folder to a USB stick as a backup.

## 5. Bring-up order and layout
**Image:** Raspberry Pi OS (64-bit) **Trixie, 6 Oct 2026, kernel 6.18**. Use Lite if the demo UI runs on a laptop, Desktop if Chromium kiosk runs on the Pi. Keep a Bookworm card as the fallback.

**Order:**
1. Flash the image and run `full-upgrade`.
2. Check the camera with `rpicam-hello`.
3. Install `dkms` and `hailo-all`, then reboot and run `identify`.
4. Freeze updates with `apt-mark hold hailo-all hailort hailo-dkms` (exact package names [u]).
5. Run the rpicam Hailo demos.
6. Set up hailo-apps (first run fetches the HEFs).
7. Create the CPU venv and pull the weights.
8. Build llama.cpp.
9. Install LiteRT-LM.
10. Install Moonshine.
11. Set up Mosquitto.

**venvs:**
- `~/venv-hailo`: hailo-apps' own `venv_hailo_apps` (uses `--system-site-packages` for hailort and picamera2).
- `~/venv-cpu`: created with `--system-site-packages` so picamera2 works. Holds torch, timm, transformers, ultralytics, and moonshine.
- llama.cpp and litert-lm run as **separate processes** (HTTP or CLI). MQTT connects the processes.

**30-minute smoke test (offline, Wi-Fi off):**
1. (0–3 min) `hailortcli fw-control identify` and `rpicam-hello -t 5000`.
2. (3–6) `rpicam-hello --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json`
3. (6–9) hailo-apps `hailo-detect-simple`, then `hailo-pose`.
4. (9–13) In venv-cpu: one frame each through DeiT-Tiny, DINOv2-S, and YOLOE with `set_classes`. Print ms for each.
5. (13–17) `llama-mtmd-cli` with SmolVLM-256M on one JPEG, timed.
6. (17–21) `litert-lm run` on the local `.litertlm` with a text prompt. Note the TTFT.
7. (21–24) Moonshine mic transcriber, then LFM2.5 through `llama-server` with one tool call.
8. (24–27) Run `mosquitto_sub` / `mosquitto_pub` round-trip.
9. (27–30) Run the full pipeline for 3 minutes while watching `vcgencmd measure_temp` and `get_throttled`. The active cooler is required.

## Sources
- https://github.com/hailo-ai/hailo_model_zoo/blob/master/docs/PUBLIC_MODELS.rst
- https://github.com/hailo-ai/hailo_model_zoo/blob/master/docs/public_models/HAILO8/HAILO8_object_detection.rst
- https://github.com/hailo-ai/hailo_model_zoo/blob/master/docs/public_models/HAILO8/HAILO8_zero_shot_classification.rst
- https://github.com/hailo-ai/hailo_model_zoo/blob/master/docs/public_models/HAILO8/HAILO8_zero_shot_instance_segmentation.rst
- https://github.com/hailo-ai/hailo_model_zoo/blob/master/docs/public_models/HAILO8/HAILO8_pose_estimation.rst
- https://github.com/hailo-ai/hailo_model_zoo/blob/master/docs/public_models/HAILO8/HAILO8_instance_segmentation.rst
- https://newreleases.io/project/github/hailo-ai/hailo_model_zoo/release/v5.1.0
- https://github.com/hailo-ai/hailo-apps and https://github.com/hailo-ai/hailo-apps/blob/main/doc/user_guide/installation.md
- https://raspberrypi.com/documentation/computers/ai.html
- https://www.raspberrypi.com/news/software-updates-for-raspberry-pi-ai-products/
- https://www.raspberrypi.com/software/operating-systems/
- https://community.hailo.ai/t/hailo-10l-pcie-drivers-broken-after-recent-rpi5-update/19301
- https://huggingface.co/Arm/deit-tiny-int8-xnnpack-executorch
- https://forum.dexterindustries.com/t/moondream-vision-language-assistant-on-gopigo3-robot-kilted-dave/10750
- https://developers.google.com/edge/litert-lm/models/gemma-4.md.txt
- https://huggingface.co/litert-community/gemma-4-E2B-it-litert-lm
- https://huggingface.co/blog/smolervlm
- https://huggingface.co/ggml-org/SmolVLM-256M-Instruct-GGUF/tree/main
- https://huggingface.co/ggml-org/SmolVLM-500M-Instruct-GGUF/tree/main
- https://huggingface.co/vikhyatk/moondream2
- https://huggingface.co/facebook/dinov2-small/tree/main
- https://huggingface.co/LiquidAI/LFM2.5-230M-GGUF
- https://docs.ultralytics.com/models/yoloe/
- https://github.com/moonshine-ai/moonshine
