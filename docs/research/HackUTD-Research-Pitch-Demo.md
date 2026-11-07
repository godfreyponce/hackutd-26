---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, pitch]
---

Part of [HackUTD-2026](../HackUTD-2026.md). Agent research, 2026-11-07. Builds on [HackUTD-Research-Judging](HackUTD-Research-Judging.md) and [HackUTD-Research-NVIDIA-Winners](../tracks/HackUTD-Research-NVIDIA-Winners.md). Fill every `[ ]`; no number goes in unless it was measured.

## 1. What winning hardware write-ups looked like
I opened 5 winner pages. Note that `devpost.com/software/sprout` is an unrelated 2015 app; the NVIDIA winner is `greenguardian-microfarm`.

| Project (award) | Words | Headings | Gallery | Built-with |
|---|---|---|---|---|
| Roomie (HackUTD General + Hardware) | ~340 | Devpost default (merged "Inspiration and Function") | 3 (phone UI, whiteboard) | 7: c++, esp32, mongodb, node.js… |
| Guardian Wheels (HackUTD General + Toyota) | ~410 | Default + "What's next" | 1 | 12, incl. arduino, twilio, laptop-camera |
| Portable Braille (NVIDIA Robo + TreeHacks 3rd) | ~510 | Default, all 7 | 3 (parts, glasses→Jetson stream) | 7: esp32, arduino, bluetooth… |
| Sprout/GreenGuardian (NVIDIA Edge AI) | ~580 | Default minus Challenges | **10** captioned build-progress photos | 13: jetson-nano, cuda, ollama, qwen, i2c… |
| TORQ (NVIDIA Edge AI) | ~1,500 | Custom: tagline H1, How We Built It, Challenges, **Safety**, What We Learned, Next steps | 4 (hardware mounts, power) | 8: cuda, holoscan, thor… |

**Patterns:**
- They are short (340–580 words), use the Devpost default headings, and embed a YouTube video.
- The gallery is **photos of the real hardware**, not renders.
- **None had an architecture diagram or a measured-results table.** That gap is cheap for us to fill and maps to Technical Complexity.
- Guardian Wheels' embed is a placeholder video, with a heading saying "Bad wifi – video in Google Drive". **Upload the video by Sun 10 AM.**
- Tags are specific chips and libraries (`jetson-nano`, `holoscan`), which helps sponsor judges searching the gallery.
- Advice from dev.to: keep the template headings, put what a 5-minute judge needs at the top, and for each sponsor tech say what it does in the project.

### Devpost template (target ~500 words)
- **Name / tagline (≤60 chars):** `[ ]`, e.g. "A camera that only thinks when it has to."
- **Gallery (in order):**
  1. Hero photo of the pan/tilt rig with the tablet UI.
  2. Architecture diagram: camera → RLT patch skip → Hailo detector → Gemma VLM → Nemotron, with the confidence thresholds on the arrows.
  3. Results table as an image.
  4. Escalation-funnel screenshot.
  5. Few-shot "teach it" sequence (3 frames).
  6. 2–4 build-progress photos with timestamps (proves it was built in 24 h).
- **Inspiration (2–3 sentences):** `[ ]` Always-on vision runs a big model on every frame, but most frames don't change.
- **What it does (bullets):** look less (skip unchanged patches), think less (cascade), learn new objects from 5 photos, and an honest live energy meter.
- **Results (put near the top):** paste the §5 table with clip count, conditions and "measured / estimated" labels.
- **How we built it:** hardware (Pi 5, Hailo `[8L/26T]`, `[servo/stepper]` pan/tilt, INA219), models, thresholds, and the UI stack. One line per sponsor tech saying *why* it is used.
- **Challenges:** 2–3 real ones, e.g. calibrating thresholds and VLM latency.
- **Limitations (TORQ's "Safety" equivalent; builds trust):** small eval set, a single room, and how energy was measured.
- **What's next:** `[ ]`
- **Built with:** `raspberry-pi-5, hailo, [hailo-8l], python, [gemma], nemotron, nvidia-nim [if used], [opencv], [dinov2], ina219, [react], [fastapi]`
- **Try it out:** repo link (public, clean README, commit history visible).

## 2. Two-minute demo video
| Time | Shot | Content |
|---|---|---|
| 0:00–0:10 | Hook: tablet funnel ticking up close, then pull back to the rig | Overlay: "This camera skipped 9 of 10 frames. It still caught [X]." |
| 0:10–0:25 | Problem | Talking head or b-roll: always-on AI vision burns power and bandwidth and sends everything to the cloud. |
| 0:25–1:05 | Live demo, one take if possible | Empty scene, so cheap path only. Object enters: detector fires. Ambiguous object: escalates to Gemma, then Nemotron, with funnel and energy updating. Teach a new object with 5 photos, then it's recognized. |
| 1:05–1:25 | How it works | Animate the architecture diagram, one stage per beat. |
| 1:25–1:45 | Numbers | Results table: agreement %, escalation %, p50/p95 latency, J/frame vs always-big. State the clip count on screen. |
| 1:45–2:00 | Impact + close | Use case (`[track app]`), team names, project name. End by 1:58. |

**Filming:**
- Use landscape 1080p30, lock exposure and focus (long-press), use a tripod or a propped phone, and keep the phone 1–2 ft from the tablet with screen brightness at max.
- Record a screen capture of the UI separately and composite it, rather than filming a glossy screen.
- Use a lav or phone mic near the speaker, in a quiet hallway; the hack floor is loud. Voiceover recorded separately is safer.
- **Burn in captions:** judges often watch muted [u]. CapCut auto-captions are fastest.
- **Tools:**
  - **CapCut** (default): fast, auto-captions, templates.
  - **DaVinci Resolve**: if someone already knows it.
  - **Canva**: for the diagram, title cards and table card.
- Split the roles: script, capture, edit.

**Backup footage to record overnight (each as its own clip, named by timestamp):**
- Every first success: first detection, first escalation, first few-shot recognition.
- A clean full demo run as soon as one works; re-shoot after each improvement.
- UI screen recordings during the eval run.
- Build b-roll: soldering, mounting, the rig panning.
- The INA219 readout.
- A wide shot of the table setup.

If the live demo breaks Sunday, this footage is the video.

## 3. 60-second table pitch (≈150 words spoken)
> **[0–10 s]** "Hi! Watch this camera. Right now it's barely working. [point at funnel] 90-some percent of patches skipped."
> **[10–20 s]** "Always-on AI cameras run a giant model on every frame. Most frames don't change, so that's wasted energy, latency and privacy."
> **[20–45 s]** "We do three things. **Look less:** skip image patches that didn't change. **Think less:** a tiny detector on the Hailo chip answers first, a local Gemma VLM only if it's unsure, and cloud Nemotron only if *that's* unsure. [hold up object] Here, this escalates, see the funnel. **Learn fast:** five photos and it knows a new object. [do it]"
> **[45–60 s]** "On `[N]` labeled clips we agreed with the big model `[X]`% of the time, using `[Y]`× less energy per frame. Everything except the last stage runs on this Pi. Want to try teaching it something?"

End on the handover, so the judge touches the demo and remembers it. Use the leftover ~4 minutes for questions.

**Likely questions:**
- **Why not a Jetson?**
  - "The cascade is the contribution, not the chip; it ports to Jetson unchanged."
  - "A Pi plus Hailo is the cheap, low-power tier where skipping work matters most."
  - Quote the measured W, not spec-sheet TOPS.
- **Really on-device?**
  - "Stages 1–2 run here. Pull the Ethernet [do it]; it keeps working and marks cloud cases 'deferred'."
  - Only say this if it's true. Show the Wi-Fi-off state if it is.
- **How accurate?**
  - "We measured agreement with the full model on our `[N]` clips: `[X]`%. It's not a benchmark; it's one room and our objects."
  - Never say "accuracy" without the set size.
- **What's novel?**
  - "Combining temporal patch skipping, a three-tier confidence cascade and few-shot prototypes on a $`[ ]` edge box, with live energy accounting."
  - Each piece is from the literature; the integration and the measurement are ours.
- **Privacy?**
  - "Frames never leave the device unless both local models are unsure. Even then only the crop is sent `[if true]`, and the UI shows every upload."
- **How do you measure energy?**
  - "An INA219 on the 5 V input measures the whole board, Hailo included." Or say "estimated from `[method]`".
  - Hailo's own power-measure command isn't supported on the AI Kit/HAT.
- **What breaks it?** Have one honest answer ready, e.g. low light or fast motion defeating the patch skipping.

## 4. Table checklist
- [ ] **Sign readable at ~3 m:** project name, a one-line hook, a big live metric, and track logos. Print it or show it on a second screen.
- [ ] Tablet on a stand at eye level, brightness at max, auto-lock off, charger connected.
- [ ] **Power:** power strip, official 27 W Pi 5 PSU, spare USB-C cables, labeled.
- [ ] Battery backup for the tablet. Check `vcgencmd get_throttled` = `0x0` (no undervoltage).
- [ ] **Lighting:** a desk lamp on the scene so the detector isn't at the mercy of the hall lights. Test it at the actual table.
- [ ] **Demo props:** 3 known objects, 1 deliberately ambiguous object (forces escalation), and 1 "teach me" object with its 5 photos pre-staged.
- [ ] **One-tap reset** button (clears counters and few-shot classes) plus a written reset script. Rehearse 30-second demo → reset → demo.
- [ ] **Network fallback:** phone hotspot. Offline mode demonstrable.
- [ ] Backup video queued on a laptop.
- [ ] Printed results card plus a QR code to the Devpost.
- [ ] Someone at the table at all times (3 absent skips hide the project). Rotate breaks.
- [ ] The cable mess is hidden but the hardware is visible. Judges want to see the Pi and the HAT.

## 5. One-hour evaluation protocol
1. **Data (20 min):**
   - Record ~20 short clips (10–20 s each) at the demo table: ~8 static, ~8 with objects entering, ~4 hard (ambiguous, low light).
   - Sample 1 fps, giving ~300 frames. Hand-label ~100 frames for presence/class, or skip labels and use the reference model.
2. **Reference:** run the big model (Nemotron, or local Gemma if offline) on every sampled frame. This is the "always-run-big" baseline.
3. **Run the cascade** on the same frames, logging per frame: the stage that answered, the answer, latency, and the INA219 mW (avg over the stage's window).
4. **Metrics:**
   - **Agreement with the big model**: % of frames with the same answer. Also report it vs hand labels on the labeled subset.
   - **Escalation rate** per stage, which is the funnel.
   - **p50/p95 end-to-end latency** for the cascade vs always-big.
   - **J/frame:** mean power × time per frame, minus idle power or not (state which), vs always-big.
   - **Patch-skip %** on static vs moving clips.
5. **Presenting it:**
   - One table showing N clips/frames, conditions, and measured vs estimated per column.
   - Use ranges or "on our set" wording, and show the hard-clip results separately.
   - Use "×" only as a ratio of two things you measured.
   - Never call agreement "accuracy" unless it is against hand labels.

| Metric | Always-big | Cascade | Notes |
|---|---|---|---|
| Agreement w/ big model | 100% (ref) | `[ ]`% | N=`[ ]` frames |
| Escalated to VLM / cloud | 100% | `[ ]`% / `[ ]`% | |
| Latency p50 / p95 (ms) | `[ ]` / `[ ]` | `[ ]` / `[ ]` | |
| Energy (J/frame) | `[ ]` | `[ ]` | INA219 whole board / est. |

## Sources
- Devpost pages opened (via curl):
  - https://devpost.com/software/roomie-vp4m6t
  - https://devpost.com/software/guardian-wheels
  - https://devpost.com/software/portable-braille-cdq8v5
  - https://devpost.com/software/greenguardian-microfarm
  - https://devpost.com/software/torq
  - https://devpost.com/software/sprout (unrelated 2015 project)
- https://dev.to/jacklynbiggin/how-to-make-your-devpost-submissions-not-suck-37i0
- https://community.hailo.ai/t/measuring-power-consumption-on-hailo8l-with-rp5-ai-kit/5234 (AI Kit lacks power measurement)
- https://raspberry.tips/en/faq/raspberry-pi-power-consumption-update-2026-all-models-compared: `vcgencmd pmic_read_adc` measures the board only; AI HAT+ adds about 2–3 W during inference [u, third-party blog]
- Captions-muted claim and video-tool picks are [u], from practice rather than a source.
