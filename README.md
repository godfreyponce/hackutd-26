<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/brand/land-wordmark-white.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/brand/land-wordmark-navy.svg">
  <img alt="LAND: Life Against Natural Disaster" src="docs/brand/land-wordmark-navy.svg" width="360">
</picture>
</p>

# hackutd-26
HackUTD 26: Zero Day · Sat Nov 7 12:00 PM → Sun Nov 8 12:00 PM · ECSW, UTD
Team: Godfrey (software/AI) · Rafael (hardware/embedded)

## Start here
1. **[docs/tracks/HackUTD-Tracks.md](docs/tracks/HackUTD-Tracks.md)**: the official tracks, prizes, briefs and how each fits us.
2. **[docs/research/Research-Edge-AI-Brief.md](docs/research/Research-Edge-AI-Brief.md)**: one-page summary of all the edge-AI research.
3. **[docs/HackUTD-2026.md](docs/HackUTD-2026.md)**: project hub, with links to every note.

## Proposed plan (not locked; decide together)
**Tracks:** the event site says up to **2 company tracks** (Devpost said 3); confirming with an organizer.
- **NVIDIA, "Use Nemotron Beyond a Chatbot":** Nemotron must run as an agent that plans multi-step tasks and calls tools.
- **State Farm, "The Worst Day, at Scale":** in a disaster, find who needs help most urgently and coordinate assistance.
- **HackUTD track:** Best Hardware (track list not announced yet).
- **MLH:** Tiger Data (time-series metrics) and GoDaddy (domain). Gemini only if it has a real job.
- Alternates: Northmark (data center ops) or CBRE (building failures).

**Build: "Look less, think less."** An edge sentry on a servo pan/tilt.
1. **On the device:** the Pi 5 + Hailo-8 runs detection (motion gate → detector → small VLM). It works offline and sends alerts, not video.
2. **Escalation:** only uncertain cases go to **Nemotron**, which acts as an agent. It re-aims the camera, re-checks, ranks who needs help first, sends the dispatch alert, and logs it.
3. **Judge screen:** a live overlay showing frames skipped, how often we escalate, energy per hour, and accuracy compared with always running the VLM.

**Split:**
- Rafael: hardware, ESP32 servo firmware, Pi + Hailo setup, case.
- Godfrey: Nemotron agent, dashboard, Devpost, video.

## Repo layout
```
docs/              hub, event info, ideas, plan, inventory + shopping list
docs/research/     edge AI, cascades, boards, embedded, judging, judge UI, pitch/demo, risks, Claude loadout
docs/tracks/       official tracks + one research card per sponsor + MLH + past NVIDIA winners
docs/brand/        LAND logo SVGs + PNG exports (redo the PNGs: sh docs/brand/export-png.sh)
hardware/case/     custom Pi 5 + AI HAT+ case (build123d source, PLAN.md)
hardware/case/cad/ STEP/STL/3MF exports + interactive assembly viewer (open the .html)
```

## How we coordinate (two Claude accounts)
There's no official way for two accounts to orchestrate each other, so **GitHub issues are the shared queue** ([docs/research/HackUTD-Research-Claude-Loadout.md](docs/research/HackUTD-Research-Claude-Loadout.md)).
- **STATE issue:** current decisions and blockers.
- **One issue per task.** To claim one, assign yourself.
- **Owners:** each person owns their folders. Branch → PR for code.
- **To-do, Godfrey:** run `/install-github-app` so `@claude` works in issues and PRs.

## Deadlines
- **Sat 11:00 PM:** first Devpost submission (required).
- **Sun 12:00 PM:** final submission, with a demo video of 2 minutes or less.
- **Sun 1–4 PM:** judging. Someone stays at the table the whole time.
