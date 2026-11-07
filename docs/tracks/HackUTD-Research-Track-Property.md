---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research]
---
Part of [HackUTD-2026](../HackUTD-2026.md).

# Track cards: State Farm + CBRE

Sponsor cards for "Look less, think less" (pan/tilt Pi 5 edge-AI cascade). Winner lists come from the Devpost winners JSON on each year's project gallery. The 2026 challenge text is unknown until noon. Everything under "likely challenge" is inference.

## Correction to the brief
- `cbre-project` = **TrustEstate AI**, a CBRE winner in **2025**, not 2024. The 2024 CBRE winners were Eco Fast Track, Greenify and EcoVerse.
- **Roomie** (2023) won HackUTD General + Hardware Track, **not** a sponsor track. It finds empty UTD study rooms using motion sensors plus Coursebook data, an ESP32 board and an occupancy LED.

## State Farm

**History**
- **2023 (HackUTD X), 3 winners:** Asset Angel (small-business risk score and premium-reduction tips, also won General), **Rate My Drivers** (a dashboard camera tracks eye and face behaviour with OpenCV and grades each delivery-driver trip) and JakeBot (Dialogflow/Vertex claims assistant with document processing for property-damage reports). Theme: risk reduction plus claims.
- **2024 (Ripple Effect):** State Farm is not in the prize list.
- **2025 (Lost in the Pages), 3 winners:** MirrorAPI, UpGuardian and qAPIbara. **All three compare API versions and catch breaking changes**, using Nemotron/Gemini for test generation and explanations. That year's prompt was dev-tooling, not insurance. [u: inferred from all three winners solving the same problem]
- Prizes: 2025 1st place was a HOVERair X1 drone; 2023 1st place was a PS5.

**Current themes (primary)**
- **Ting (Whisker Labs):** a plug-in sensor that detects electrical arcing, "the precursor to most electrical fires". It is free for eligible homeowners. In April 2024 it expanded to more than 2M sensors, with about 700k homes already enrolled. It also gives outage warnings, dangerous-utility-power alerts and frozen-pipe prevention. Whisker Labs claims about 10k homes were "saved" (vendor claim). State Farm's posture is **prevent, don't just pay**.
- Driver safety (Drive Safe & Save telematics). [u: not opened]

**Data / APIs**
- State Farm's developer portal (developer.statefarm.com) appears to be partner-only: Coverage, Policies and Quotes APIs, no public access. [u: aggregator listings only; the portal redirected and was not read] **Assume no State Farm API** and expect sponsor data or mock JSON at noon.
- Bring our own data: camera frames plus event logs.

**Likely challenge** [u]: either (a) a repeat of 2025-style dev/API tooling, which fits us badly, or (b) risk prevention / claims automation for home or auto. If (a) shows up, skip State Farm.

**Build angles**
1. **Home Hazard Sentry.** The pan/tilt sweeps a room and patch-skipping ignores static pixels. The cheap detector flags changes such as smoke or haze, water pooling under a sink, space heaters near fabric, stove-on-unattended or an open flame. The Pi VLM confirms. The cloud is called only when the Pi is unsure. Output: a **hazard event** (photo crop, class, confidence) plus a "would have filed claim $X" estimate. This is the visual counterpart to Ting, which hears arcing.
2. **Claims-in-five-photos / self-inspection.** A homeowner teaches the system a new item from 5 photos, using the few-shot path. The rig builds a timestamped, before/after **inventory and condition log**. After damage, the diff becomes first-notice-of-loss evidence. This links to JakeBot's claims angle and EstateSense's condition scoring.

**First pitch sentence:** "Ting listens to your wiring; we watch the room. A camera that only thinks when something changes catches the leak, the space heater and the unattended pan before they become a State Farm claim, and it never streams your living room to the cloud."

## CBRE

**History** (CBRE has sponsored every year; prizes are $250, $150 and $75 Amazon gift cards)
- **2023:** Sharewood (fractional property investing plus **image-based home valuation**), Value Proposition Generator (photo classification + VQA → listing copy) and **EstateSense** (CV + GenAI **property condition** assessment and environmental susceptibility). Theme: **AI on property images**.
- **2024:** **Eco Fast Track** (smart water-gauge sensors for apartments, a 3D-printed enclosure, AI water-saving tips; won **CBRE + Veolia**), Greenify (emissions calculator and score, GPT-4 chatbot, map of CBRE sites) and EcoVerse (VR digital twin of offices with energy and water metrics, SambaNova/Llama). Theme: **building sustainability and operations**. A hardware entry won.
- **2025:** TrustEstate AI (verified property analytics), Cura (CRE forecasting, CrewAI/MCP/Ollama) and Pact (Solana contract management). Theme: **CRE data and decision tools**.

**Current themes (primary)**
- **Smart FM on the Nexus platform:** covers more than 20k sites and 1B sq ft. CBRE claims up to 20% lower maintenance cost and energy use, and 25% fewer technician dispatches. The goal is reactive → proactive → predictive maintenance (2023, vendor claims).
- CBRE's 2025 "10 ways" article highlights **occupancy-driven HVAC and lighting** (dim unoccupied areas, set room temperature by headcount), space-utilization analytics, predictive maintenance, digital twins and energy management. Privacy appears only as a guideline mention.
- **Ellis AI:** CBRE's enterprise AI platform; CBRE says it manages 8B sq ft.

**Data / APIs**
- CBRE has no public API that we found. CBRE winners used sponsor-provided data or their own. [u]
- **EIA CBECS 2018** public microdata (CSV) for commercial buildings. Space heating ≈ ⅓ of end-use energy. Use it to turn "empty room detected" into kWh and $ estimates.
- Our own occupancy and event stream.

**Likely challenge** [u]: AI for property/facility operations, sustainability, or CRE decision support. 2024 is the best fit for hardware.

**Build angles**
1. **Privacy-first occupancy sentry.** One pan/tilt unit sweeps an open office or lecture hall. It counts people per zone and **sends events, never video** (`zone 3: 0 people, 14 min`). The dashboard shows HVAC/lighting setback opportunities and kWh saved, using CBECS-based estimates. The escalation funnel shows that most frames never leave the Pi. This is the camera version of Roomie and fits CBRE's "dim unoccupied areas" item directly.
2. **Facility inspection rover-cam (Smart FM).** The rig patrols a room and flags maintenance faults: a ceiling stain or leak, a blocked fire exit, a burnt-out light, clutter on egress paths. Each fault becomes a **work order** with a photo crop. The 5-photo teach step lets a facility manager add a new fault type on site. Measure "technician walk-throughs avoided" against CBRE's 25%-fewer-dispatches figure.

**First pitch sentence:** "CBRE says occupancy-aware buildings cut energy by up to 20%. We built the sensor that makes that possible without putting a video feed in every room: it only thinks when the room changes, and it reports counts, not faces."

## Overlap
Both companies reward **prevention and fewer truck rolls**. One rig can serve both pitches with two modes: hazard (State Farm) and occupancy/fault (CBRE). Stack Best Hardware on top. Precedent: Eco Fast Track won two sponsor tracks with a single sensor build.

## Sources
- https://hackutd-x.devpost.com/project-gallery (2023 winners JSON) · https://hackutd-x.devpost.com/ (prizes)
- https://hackutd-ripple.devpost.com/project-gallery (2024 winners) · https://hackutd-ripple.devpost.com/ (prizes)
- https://hackutd-2025.devpost.com/project-gallery (2025 winners) · https://hackutd-2025.devpost.com/ (prizes)
- Devpost projects: https://devpost.com/software/mirror-api · https://devpost.com/software/upguard · https://devpost.com/software/in-progress-2awbie · https://devpost.com/software/risk-navigator · https://devpost.com/software/team-registration-ctr1qh · https://devpost.com/software/jakebot · https://devpost.com/software/cbre-project · https://devpost.com/software/tbd-58ftpr · https://devpost.com/software/autotract · https://devpost.com/software/sharewood · https://devpost.com/software/value-proposition-generator-aljgry · https://devpost.com/software/estate-sense · https://devpost.com/software/apartment-monitoring · https://devpost.com/software/greenwise-y6o4bu · https://devpost.com/software/ecoverse-5dczmp · https://devpost.com/software/roomie-vp4m6t
- https://newsroom.statefarm.com/state-farm-expands-ting-fire-safety-program-to-2-million-homes/
- https://www.facilitiesdive.com/news/cbre-smart-facilities-management-maintenance-billion-square-feet/693274/
- https://www.cbre.com/insights/articles/the-role-of-ai-in-workplace-technology-10-ways-companies-are-maximizing-its-impact
- https://www.cbre.com/about-us/technology/artificial-intelligence
- https://www.eia.gov/consumption/commercial/
