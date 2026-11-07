---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, judging, pitch]
---

# Research: Judging, Past Winners, Prizes

Part of [HackUTD-2026](../HackUTD-2026.md). Agent research, 2026-11-07. Godfrey's agents are also researching past winners; merge with his.

## 2026 rules (Devpost: hackutd-zeroday.devpost.com/rules)
- **Up to 3 sponsor tracks + 1 HackUTD track** (Best Hardware / Best Design / Virality), plus any number of MLH tracks. Every team is automatically in General.
- **$60k+ in prizes**, $20k cash for 1st, 2nd and 3rd overall.
- Final submission **Sun 12:00 PM**, with a **demo video of 2 minutes or less**. Nothing built before noon Sat. Attendance required at judging and closing.

## How Jury works (science fair style)
- Each judge is handed a random project and walks to the table. A timer runs (**5 min default**; HackUTD's actual setting unverified).
- Afterwards the judge writes notes, can star the project (about 3 stars per judge), then **drag-ranks every project they've seen**.
- **Scoring:** each judge's ranking becomes pairwise wins and losses (Copeland/Borda), summed across judges, then organizers deliberate. The target is **3–5 views per project**.
- Judges can skip a team as **absent or busy**. **Three absent skips hide the project** until an organizer checks.
- Judges can flag a team that "can't demo" or a project that looks "too complex for 24 h".
- **Criteria:** Innovation, Technical Complexity (hardware named), Completeness, Design, Impact, Presentation.
- **Implications:**
  - Judges compare you against the other projects they saw, so be **memorable**.
  - Keep **someone at the table at all times**.
  - Make the demo work within **30–60 s**.
  - Make the table readable from the aisle.
  - Have the git history ready.

## Past winners
- **2025:** Best Hardware went to **VisionScout** (YOLO smart glasses).
  - **Kori** (Pi + sensors) won Best Use of Gemini.
  - **HealthSense** (Arduino → Pi 5 sensors + Nemotron agent) won Vultr.
  - **Toyotron** won Toyota + NVIDIA; **DataDriver** won Northmark + NVIDIA.
  - The General winners were all software.
- **2024:** **Backtracc** (Pi lost-item tracker) won Hardware + Cloudflare + SambaNova.
  - **Eco Fast Track** (Arduino, 3D printing, IoT) won Veolia + CBRE.
  - EcoVerse (haptics) won CBRE.
- **2023:** **Roomie** (ESP32 occupancy sensors) won **General + Hardware**.
  - **Guardian Wheels** (Arduino car alarm with camera) won **General + Toyota**.
- **Patterns:**
  - Hardware teams **stack prizes** (track + sponsor + MLH).
  - Winners name the sponsor challenge in their first sentence.
  - Problems are concrete and personal.
  - NVIDIA Nemotron showed up across many 2025 winners.

## What sponsors asked before (inferred from winners, unverified)
- **EOG:** a **real dataset** every year (2023 methane sensors, 2024 pipeline hydrate blockage, 2025 cauldron fill/drain anomalies). Rewards analysis plus visualization.
- **State Farm:** API migration tools (2025); small-business risk and driver ratings (2023).
- **T-Mobile:** customer-sentiment intelligence for PMs (2025).
- **Toyota / TFS:** car buying, financing and trade-in; in-car learning.
- **CBRE:** property data, valuation, sustainability.
- **Goldman:** onboarding due diligence (2025).
- **NVIDIA:** use Nemotron (2025).
- **Northmark:** data-center operations.
- **Capital One:** a kids' NFC spending card won (2025).
- Axxess, Niantic Spatial, PNC: no evidence found.
- **Lesson:** sponsor challenges skew toward **data and software**. A hardware build has to connect to the sponsor's own problem or data.

## MLH prizes to stack (2026 page)
- **Gemini API** (a Pi device won it in 2025)
- **MongoDB Atlas** (prize is an M5Stack IoT kit)
- **Tiger Data** (time-series, explicitly invites IoT; fits our live metrics)
- **Vultr**
- **GoDaddy domain** (cheap to enter)
- Solana
- SpaceXSI raffle (Cursor + Grok bot)

## Playbook
1. 2–3 sponsor tracks + **Best Hardware** + every MLH prize we genuinely use.
2. Build on the sponsor's data or API and say so in the first sentence.
3. One concrete, personal problem.
4. The device reacts to the judge within 10 s.
5. 60-s pitch: problem → live demo → how it works → impact, then questions.
6. Staff the table all of Sun 1–4 PM.
7. Readable sign, screen facing out, hardware lit.
8. Git history + architecture diagram ready.
9. Devpost v1 by Sat 11 PM; final by Sun noon with a demo-only video of 2 minutes or less.
10. Polish the UI (Design is scored).

## Sources
github.com/hackutd/jury · jury.mikz.dev/docs (details, usage, judge, tips, admin/scoring) · hackutd-zeroday.devpost.com (+ /rules) · hackutd-2025.devpost.com/project-gallery · hackutd-ripple.devpost.com/project-gallery · hackutd-x.devpost.com/project-gallery · devpost.com/software/{kori, healthsense-0qxrs4, toyotron, datadriver, roomie-vp4m6t, guardian-wheels, mirror-api, spendingwithspendy, poyolabs-47n0fz, pipebrains, ch4-us}
