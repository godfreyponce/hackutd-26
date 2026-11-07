---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research]
---

Part of [HackUTD-2026](../HackUTD-2026.md). Sponsor card for NVIDIA, researched the morning of 2026-11-07. The 2026 NVIDIA track text was **not on Devpost yet** at 8:30 AM. Re-check at noon. `[u]` marks claims I could not verify.

## Sponsor card
- **2025 prize:** 3 winners. 1st place got 3× RTX 5080 GPUs, 2nd got 2× RTX 5080 plus Brev credits, 3rd got backpacks plus Brev credits. The Devpost page showed no written judging criteria for the prize.
- **What won in 2025:** two pure-software agent apps, both with Nemotron as the "reasoning core". No NVIDIA hardware was involved.
  - **Toyotron** (won Toyota Financial + NVIDIA) is a car-buying concierge. It runs a Nemotron agent with tools for email, calendar and trade-in, plus a phone-style voice flow. The name is "Toyo + (Nemo)tron". It reached Nemotron **through OpenRouter**, not NIM.
  - **DataDriver** (won Northmark + NVIDIA) is a ReAct copilot for data-center technicians, built on `nemotron-nano-9b-v2` with LangChain and a NeMo toolkit.
- **What that tells us:** the 2025 judges rewarded Nemotron being load-bearing and visible in the name, the diagram and the pitch. They did not reward GPU usage. `[u]` The 2026 criteria could differ.

## Current Nemotron family (vision-relevant)
| Model | Size | Vision | Notes |
|---|---|---|---|
| Nemotron Nano 12B v2 VL | 12.6B | image + video | Released 2025-10-28. Hosted id `nvidia/nemotron-nano-12b-v2-vl`. Up to 4–5 images, 12 tiles of 512². `/think` system prompt turns reasoning on. **EVS video-token pruning.** |
| Nemotron 3 Nano Omni 30B-A3B Reasoning | 30B, 3B active | image, video, audio | Released 2026-04-28. Hosted id `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning`. Reasoning on by default; `enable_thinking`. 256k context. |
| Nemotron 3.5 Super VL 120B-A12B | 120B, ~12B active | image, PDF, web | Released 2026-10-15. Available on NIM. The exact hosted id is `[u]`. |
| Nemotron 3 Nano 4B | 4B | text only | Released 2026-03-17. Q4_K_M **GGUF**, 18 tok/s on a Jetson Orin Nano. |
| Nemotron 3.5 Bolt E4B 4GB | 8B (4B effective) | text only | Released 2026-10-23. Built on Gemma 4 E4B. 6.18 GB Q4_K_M GGUF. Ollama/llama.cpp. OpenMDW license. |

Other members are text-only: Nemotron 3 Nano 30B-A3B (Dec 2025), Lightning 30B-A3B (Aug 2026, GGUF), Ultra, and Bolt 74B-A9B.

**On-device on a Pi:** NVIDIA lists **no CPU or Arm target** for any of these models. Every source names Jetson, RTX or DGX. Nemotron 3 Nano 4B GGUF is the realistic Pi 5 candidate through llama.cpp, at an estimated few tok/s `[u]` that we must benchmark ourselves. It is text-only, so use it as a **reasoner over detector labels**, not as a VLM.

## Stage-4 API notes (cloud VLM when unsure)
- **Key:** sign in at build.nvidia.com, open a model, choose "Get API Key", copy the key. Calls from code use up trial credits; the browser playground does not.
- **Endpoint:** `https://integrate.api.nvidia.com/v1/chat/completions`. It is OpenAI-compatible and uses `Authorization: Bearer <key>`.
- **Rate limit:** community-reported at **~40 RPM** per account. An NVIDIA moderator said there is "no official way… to receive a rate limit increase on that same tier." Plan for a 429 and let the cascade *show* that it stays under budget.
- **Images:** a content part with `type: "image_url"` whose `url` is `data:image/jpeg;base64,...`. Send a crop of the uncertain region, not the whole frame (fewer tiles means lower latency).
- Request shape (notes only, not project code):
  - `client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)`
  - `model="nvidia/nemotron-nano-12b-v2-vl"`, `max_tokens≈256`, `messages=[{"role":"system","content":"/no_think"}?, {"role":"user","content":[{"type":"image_url","image_url":{"url":data_uri}}, {"type":"text","text":"Label + confidence JSON"}]}]`
  - The docs only show `/think` to turn reasoning on. Default (no system prompt) = reasoning off `[u]`. For Omni, use `extra_body={"chat_template_kwargs":{"enable_thinking":False}}`.
- **Pick:** use **12B v2 VL** as the default Stage 4 (smallest, fastest, images). Use **Omni** as the optional "hard case" tier, since it also accepts mic audio as a voice query.
- **Offline fallback:** if Wi-Fi drops, Stage 4 degrades to the on-Pi tier. Log it on the funnel.

## Judging angle
1. **Name the stages after NVIDIA models.** Make Nemotron the brain of the escalation. Say this out loud: "Stage 4 is Nemotron Nano VL. It's called on X% of frames."
2. **The thesis matches NVIDIA's own design.** The 12B VL ships *Efficient Video Sampling*, which prunes redundant video tokens (0.75 rate at "minimal accuracy impact"). Our RLT patch-skipping applies the same idea *before* the network. Tell the judges we do on the edge what NVIDIA does in the datacenter.
3. **Show a "Nemotron calls/hour + J/hour" counter** next to accuracy. Budget-aware use of their API reads as production thinking.
4. **Optional NVIDIA-native few-shot:** swap DINOv2 for NVIDIA's C-RADIO encoder (the vision tower of the 12B VL). License, size and Pi speed are `[u]`, so only try it if the swap takes under an hour.
5. **Can a Pi build win NVIDIA? Yes, plausibly.** Neither 2025 winner used NVIDIA hardware; Nemotron was the scored element. The risk is a judge asking "why not Jetson?" Answer: "The cascade is hardware-agnostic. Cheap edge plus a Nemotron cloud tier is exactly the deployment Jetson-less fleets need, and it ports to Orin Nano unchanged." `[u]` The 2026 rubric may favor GPU/Jetson use, so re-read the track at noon.

## First pitch sentence
"Our camera only asks Nemotron when it's actually confused. It skips unchanged pixels, settles easy objects on a Raspberry Pi, and escalates just the hard few percent to Nemotron Nano VL, which cuts cloud calls and energy by an order of magnitude `[u: fill with measured numbers]` at the same accuracy."

## Sources
- [HackUTD 2025 Devpost (prizes)](https://hackutd-2025.devpost.com/)
- [Toyotron](https://devpost.com/software/toyotron) · [DataDriver](https://devpost.com/software/datadriver)
- [HackUTD Zero Day Devpost](https://hackutd-zeroday.devpost.com/)
- [HF: Nemotron Nano 12B v2 VL BF16](https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-BF16)
- [NIM VLM docs: Nemotron Nano 12B v2 VL API (1.6.0)](https://docs.nvidia.com/nim/vision-language-models/1.6.0/examples/nemotron-nano-12b-v2-vl/api.html)
- [API reference: nemotron-nano-12b-v2-vl infer](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-nano-12b-v2-vl-infer) · [model overview](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-nano-12b-v2-vl)
- [API reference: nemotron-3-nano-omni infer](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-nano-omni-30b-a3b-reasoning-infer) · [build.nvidia.com Omni card](https://build.nvidia.com/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning.md)
- [build.nvidia.com explore/reasoning](https://build.nvidia.com/explore/reasoning)
- [API Catalog Quickstart](https://docs.api.nvidia.com/nim/docs/api-quickstart) · [NIM FAQ](https://docs.api.nvidia.com/nim/docs/faq)
- [NVIDIA forum: rate limit 40 RPM thread](https://forums.developer.nvidia.com/t/request-for-nvidia-build-api-rate-limit-increase-40-rpm-200-rpm/377433)
- [NVIDIA Nemotron 3 family](https://research.nvidia.com/labs/nemotron/Nemotron-3) · [NGC: Nemotron 3.5 Lightning](https://catalog.ngc.nvidia.com/orgs/nim/nvidia/models/nemotron-3.5-lightning/-)
- [NVIDIA blog: Super VL and Bolt (2026-10-15)](https://blogs.nvidia.com/blog/nemotron)
- [Bolt E4B research page](https://research.nvidia.com/labs/nemotron/Nemotron-3.5-Bolt-E4B-4GB/) · [HF: Bolt E4B GGUF](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-E4B-4GB)
- [HF blog: Nemotron 3 Nano 4B](https://huggingface.co/blog/nvidia/nemotron-3-nano-4b)
