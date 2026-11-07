---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, nvidia]
---
Part of [HackUTD-2026](../HackUTD-2026.md).

# NVIDIA prize winners at past hackathons

Method: pulled each Devpost project gallery's winners list (`challenge-winners-json-ld`) and kept only awards whose label names NVIDIA (or an NVIDIA-only prize at an NVIDIA-run event). Then opened every winning project page and confirmed the same winner label is on it. Every row below has a label I saw on both pages. Devpost does not show 1st/2nd/3rd order inside a prize, so placement is `[u]` unless stated.

**Coverage.**
- **HackUTD:** NVIDIA has an awarded prize only in **2025**. The winner lists for 2024 (Ripple), 2023 (X), 2022 (IX), 2021 (VIII), 2020 (VII) and 2019 contain no NVIDIA prize, and their landing pages don't mention one.
- **Other US college hackathons:** scanned about 100 Devpost galleries from 2024–2026: TreeHacks, Cal Hacks 11–13, HackGT 12–13, MHacks 2024–26, TAMUhack 2025–26, HackTX 2024–26, LA Hacks 2024–26, PennApps XXIV–XXVI, HackIllinois, HackPrinceton, Bitcamp, Hacklytics, YHack, DubHacks, HackDavis, BoilerMake, HackRice, IrvineHacks, WildHacks and others.
- **Where NVIDIA-labelled winners turned up:** only TreeHacks 2025, TreeHacks 2026 and the NVIDIA-run NemoClaw hackathon at UCSC (May 2026).
- **HackMIT:** its Devpost (`hackmit.devpost.com`) has no NVIDIA award. Its 2024–25 judging may run off Devpost, so absence there is `[u]`.

Hardware? = a physical build (sensors, actuators, wearable, vehicle) beyond a laptop or cloud/DGX box.

| Hackathon (year) | Prize won | Project | Link | What it does (1 line) | NVIDIA tech used | Hardware? |
|---|---|---|---|---|---|---|
| HackUTD (2025) | Nvidia track (place `[u]`); also won Toyota Financial Services | Toyotron | [devpost.com/software/toyotron](https://devpost.com/software/toyotron) | Agentic car-buying concierge that finds your Toyota and handles email, calendar and voice follow-up | Nemotron as the agent's reasoning core, accessed through OpenRouter (not NIM) | N |
| HackUTD (2025) | Nvidia track (place `[u]`); also won Northmark Compute & Cloud | DataDriver (DataPilot) | [devpost.com/software/datadriver](https://devpost.com/software/datadriver) | ReAct copilot that writes step-by-step work plans for data-center techs, checks inventory, and replans when something fails | `nemotron-nano-9b-v2` + LangChain; NeMo toolkit | N |
| HackUTD (2025) | Nvidia track (place `[u]`) | Alchemetrics | [devpost.com/software/abc-xapnio](https://devpost.com/software/abc-xapnio) | Real-time dashboard for the "Poyo's Potion Factory" challenge: tracks cauldrons, matches tickets, forecasts overflows | Nemotron as the multi-agent planner (picks which agent/tool runs next, logs its reasoning) | N |
| TreeHacks (2025) | NVIDIA: Robo Prize (Jetson dev kit per member); also Grand Prize 3rd | Portable Braille | [devpost.com/software/portable-braille-cdq8v5](https://devpost.com/software/portable-braille-cdq8v5) | Device that teaches young blind users Braille; adds facial-expression cues from smart glasses | Jetson Orin Nano runs facial-expression recognition on video from Ray-Ban Meta glasses | Y (ESP32, Arduino, Bluetooth, glasses wired to Jetson) |
| TreeHacks (2025) | NVIDIA: Best Accelerated Compute (1st or 2nd `[u]`) | Ranger | [devpost.com/software/ranger-6jkv5s](https://devpost.com/software/ranger-6jkv5s) | Wearable AR that shows deaf users where sounds are coming from | Jetson Orin Nano processes mic-array audio on the edge (CUDA); feeds a Meta Quest | Y (hat-mounted mic array, Jetson, power bank, Quest) |
| TreeHacks (2025) | NVIDIA: Best Accelerated Compute (1st or 2nd `[u]`) | WiiWork | [devpost.com/software/wiiwork-8u1x62](https://devpost.com/software/wiiwork-8u1x62) | Website built from the ground up for AI agents to use; routes each task to a suitable model | NVIDIA-hosted DeepSeek handles the "complex logic" route of the model router; no NVIDIA hardware | N |
| TreeHacks (2026) | [NVIDIA] Edge AI Track (place `[u]`) | TORQ | [devpost.com/software/torq](https://devpost.com/software/torq) | Retrofit kit that turns any car into a self-driving vehicle, with rideshare and AI driving feedback | Jetson AGX Thor; Holoscan Sensor Bridge streams camera video straight to the GPU; CUDA/TensorRT; Alpamayo R1 reasoning model | Y (car, cameras, Lattice sensor bridge, Jetson Thor) |
| TreeHacks (2026) | [NVIDIA] Edge AI Track (place `[u]`) | Sprout (GreenGuardian Microfarm) | [devpost.com/software/greenguardian-microfarm](https://devpost.com/software/greenguardian-microfarm) | Mini robotic microfarm: a gantry-mounted camera watches the plant bed and the robot tends it | Jetson Nano as on-board vision + local LLM (Ollama/Qwen) brain, CUDA | Y (sheet-metal gantry, Arduino, GPIO/I2C, camera) |
| TreeHacks (2026) | [NVIDIA] Edge AI Track (place `[u]`) | Detour | [devpost.com/software/detour-64kpds](https://devpost.com/software/detour-64kpds) | On-board AI agents that autonomously steer satellites around orbital debris | DGX Spark (ASUS Ascent GX10) running Nemotron-3-Nano-30B-A3B (NVFP4) via vLLM | N (DGX only) |
| TreeHacks (2026) | [NVIDIA] Edge AI Track (place `[u]`) | CalTrack | [devpost.com/software/caltrack-i0pq3n](https://devpost.com/software/caltrack-i0pq3n) | Disaster tool that predicts fire impact and affected areas, then coordinates emergency response | NVIDIA Earth-2 (Earth2Studio) for fire-weather risk on DGX Spark; Nemotron-class Personaplex attempted | N (DGX only) |
| NemoClaw NVIDIA x ASUS @ UCSC (2026) | Best Use of DGX Spark | FactoryMind | [devpost.com/software/factorymind](https://devpost.com/software/factorymind) | Multi-agent factory sim: a leader agent assigns pickup/dropoff jobs to worker robots | Nemotron Super 49B leader + Nemotron Nano 9B workers on local NIM endpoints on a GX10 (DGX Spark); TensorRT-LLM | N (simulated robots) |
| NemoClaw NVIDIA x ASUS @ UCSC (2026) | Best Use of Brev | ClawForge | [devpost.com/software/clawforge](https://devpost.com/software/clawforge) | No-code builder that lets small businesses create AI agents for calls, bookings and support | Nemotron generates the agent blueprints; NemoClaw safety layer; NIMs; deployed on Brev | N |
| NemoClaw NVIDIA x ASUS @ UCSC (2026) | Best Use of NemoClaw | MonkeyClaw | [devpost.com/software/monkeyclaw](https://devpost.com/software/monkeyclaw) | Autonomous red/purple/blue-team security agent that probes and patches the NemoClaw ecosystem | Nemotron end to end; custom Nemotron-3-Nano-4B LoRA fine-tuned on Brev (A100); Nemotron judge ensemble | N |
| NemoClaw NVIDIA x ASUS @ UCSC (2026) | Best for UCSC (non-NVIDIA prize at an NVIDIA-run event) | HydroClawnics | [devpost.com/software/hydroclawnics](https://devpost.com/software/hydroclawnics) | Autonomous agent that monitors hydroponic pods (temp, pH, EC, water) and fixes problems in real time | NemoClaw + Nemotron 3 Super on Brev | Y `[u]` (Arduino listed; the 500-pod scale may be simulated) |

Adjacent, not NVIDIA-sponsored: **TreeHacks 2024**, *Coframe: Best AI Hack (NVIDIA RTX 4080 GPU)*, was won by **Synthesis** ([devpost.com/software/synthesis-ag1djb](https://devpost.com/software/synthesis-ag1djb)). It is a news personalization app built on GPT-4 + Pinecone, with no NVIDIA tech; the prize was just an NVIDIA GPU. TreeHacks 2026 also listed *[NVIDIA] Open Models Hit Different on DGX Spark* (1 winner, Jetson Orin Nano Super), but no project carries that label on Devpost.

## Patterns
- **HackUTD's NVIDIA judges rewarded Nemotron-as-agent-brain, not hardware.** All 3 HackUTD 2025 winners are software-only agent apps with Nemotron as the planner/reasoner. Two of them also won another sponsor's track (Toyota, Northmark) by solving that sponsor's problem with Nemotron. That double-dip ("sponsor problem + Nemotron core") is the proven HackUTD formula. Nobody used NIM directly; Toyotron went through OpenRouter.
- **Hardware share depends on how the prize is framed.** Overall, 5 of 14 winners are physical builds: 0/3 at HackUTD, 2/3 at TreeHacks 2025, 2/4 at TreeHacks 2026, 1/4 `[u]` at NemoClaw. When the prize says "Edge AI" or "Robo", Jetson builds win (Portable Braille, Ranger, TORQ, Sprout). When it says "accelerated compute", "Brev" or "best use of NVIDIA", software agents win.
- **Edge AI winners put real inference on the device and show the physical loop.** Examples: a camera on a gantry going to a Jetson, a mic array going to a Jetson and then a headset, cameras going to a Thor and then steering. Two Edge AI winners (Detour, CalTrack) still won with only a DGX Spark and no sensors. A visible NVIDIA box plus a named NVIDIA model seems to count as "edge" for these judges.
- **Naming the exact NVIDIA model and how it is deployed recurs in winning write-ups.** Examples: `nemotron-nano-9b-v2`, Nemotron-3-Nano-30B NVFP4 via vLLM, Super 49B leader + Nano 9B workers, a LoRA on Brev. Vague "uses NVIDIA AI" write-ups are absent from the winners.
- **Impact-first problems dominate.** Most winners target accessibility (Braille, deaf AR), safety or disaster response (CalTrack, debris), or operations (data-center techs, factories, farms). That matches NVIDIA's "AI that acts in the physical world" framing even when the build is software.
- **The 2026 shift is toward DGX Spark + open models + agent safety.** TreeHacks 2026 and the NemoClaw event both handed out DGX Sparks and Jetson Orin Nano Supers as prizes and scored Nemotron/NemoClaw use. Expect HackUTD 2026's NVIDIA track to lean the same way (`[u]`, re-read the track at kickoff).

## Sources
- HackUTD 2025 prizes + winners: https://hackutd-2025.devpost.com/ · https://hackutd-2025.devpost.com/project-gallery
- HackUTD past galleries, no NVIDIA award: https://hackutd-ripple.devpost.com/project-gallery · https://hackutd-x.devpost.com/project-gallery · https://hackutd-ix.devpost.com/project-gallery · https://hackutd-viii.devpost.com/project-gallery · https://hackutd-vii.devpost.com/project-gallery · https://hackutd2019.devpost.com/project-gallery
- TreeHacks: https://treehacks-2025.devpost.com/ · https://treehacks-2026.devpost.com/ · https://treehacks-2024.devpost.com/project-gallery
- NemoClaw NVIDIA x ASUS @ UCSC: https://nemoclaw.devpost.com/
- Project pages: linked in the table (each one shows the winner label quoted above)
- Related: [HackUTD-Research-Track-NVIDIA](HackUTD-Research-Track-NVIDIA.md) (it lists 2 of the 3 HackUTD 2025 NVIDIA winners and misses Alchemetrics)
