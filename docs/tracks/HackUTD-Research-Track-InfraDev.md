---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research]
---

Part of [HackUTD-2026](../HackUTD-2026.md).

# Sponsor cards: Northmark, 8090, Spacetime, Photon

Researched 2026-11-07, about 8:30 AM. The actual challenges are announced at noon, so every "likely challenge" below is a guess `[u]`. Identities were checked against the sponsor links on zeroday.hackutd.co.

| Sponsor | Identity | Fit with an edge hardware build (1–5) |
|---|---|---|
| Northmark (Gold) | Confirmed: nmc2.com | **3** |
| 8090 (Platinum) | Confirmed: 8090.ai | **2** |
| Spacetime (Silver) | Confirmed: Clockwork Labs / SpacetimeDB | **2** |
| Photon (Other) | Confirmed: photon.codes, an iMessage agent framework (not Photon Engine) | **3** |

## 1. Northmark Compute & Cloud (NMC²), Gold, workshop 4:20 PM
- **What they do:** NMC² is part of NorthMark Strategies and builds AI and HPC compute infrastructure. Its site describes an HPC facility in Spartanburg, SC, with "one of the most sophisticated GPU clusters in the world," and calls it "a world-leading platform for advanced ML and simulation." Atlassian Williams Racing is its launch partner. The site lists no products or public APIs. A third-party report says the Spartanburg facility cost $2.8B and comes online in Q3 2026 `[u]`.
- **2025 challenge, data-center ops.** The winner was **DataDriver**, which won both the Northmark and NVIDIA prizes at HackUTD 2025 ("Lost in the Pages"). It is an agentic copilot for data-center technicians. It generates step-by-step maintenance workflows, checks parts inventory, and replans when an unexpected issue comes up. Its pitch: maintenance "still utilizes clipboards and manual procedures." Stack: Flask, MongoDB, React/Vite, LangChain, and NVIDIA `nemotron-nano-9b-v2`. **The winner had no hardware.**
- **Likely 2026 challenge `[u]`:** more data-center operations, such as technician tooling, monitoring, or compute efficiency.
- **APIs:** none public. Expect to use NVIDIA models or NIM (the 2025 winner did).
- **Build angle:** point the camera at a server rack as a "physical observability" sensor. It reads status LEDs, spots an open panel or a person at the rack, and escalates only when something changes. The pitch writes itself for a compute company: the efficiency overlay shows **GPU-seconds and cloud calls avoided**. If the track also targets NVIDIA, that would repeat DataDriver's double win.

## 2. 8090 Solutions, Platinum, workshop 3:30 PM
- **What they do:** 8090 sells **Software Factory**, which it calls an "AI-native SDLC platform." It has four stages: Requirements (plain English), Blueprints (technical design that engineers approve), Work Orders (tasks for engineers and their agents), and Feedback. 8090 Enterprise is a managed build-and-host service with named customers including BISSELL and CMS. It also offers legacy modernization (COBOL to readable rules) and MCP layers over existing ERPs. Third-party claims that Chamath Palihapitiya leads it and that it raised $135M are `[u]`.
- **Likely challenge `[u]`:** use Software Factory or agents to build or modernize an enterprise app. It could also be "agent access to legacy systems."
- **APIs and quick-start:** there is no public API. Try it at factory.8090.ai, with docs at docs.8090.ai. Work Orders reach coding agents **through MCP in Cursor, VS Code or Claude Code**. The site doesn't say whether a free tier exists `[u]`.
- **Build angle (weak):** write the project's spec in Software Factory, and let Godfrey's agents take Work Orders over MCP to build the tablet UI and backend. That makes it a process story, not a hardware one. Use it as a third track only if the challenge text rewards *how* you built.

## 3. Spacetime, Silver, bot tournament 10:45–11:45 PM Sat
- **Identity:** confirmed. HackUTD's sponsor link goes to clockworklabs.com/join. Clockwork Labs (founded 2019) builds **SpacetimeDB** and BitCraft Online.
- **What it is:** SpacetimeDB is a relational database that also acts as the server. App logic runs inside it as **reducers**, which work like RPCs. Clients **subscribe** to queries, and the server pushes changes into a local cache, with optional row-level filters.
- **Tournament:** the event page lists only the time slot. No format, rules or prize were found online `[u]`. It is probably a bot game hosted on SpacetimeDB `[u]`. **It overlaps the required 11:00 PM first Devpost submission.** Ask at the sponsor fair.
- **Quick-start:** install the CLI (spacetimedb.com/install), run `spacetime login` (GitHub or Google), then `spacetime start` for a local server on :3000. Quickstarts exist for TypeScript, Rust, C#, C++, React and Node. There's a Maincloud hosted option, but its free tier is unconfirmed `[u]`. The docs page doesn't list a Python client `[u]`, so the Pi would need TS/Node or Rust.
- **Build angle:** **replace MQTT with SpacetimeDB** as the real-time state bus. Each board calls reducers like `report_detection` and `report_metrics`, and the tablet judge UI subscribes. That adds a live multi-board dashboard plus replayable history. The risk is learning a new tool at 2 AM, when MQTT already works.

## 4. Photon, "Other" sponsor
- **Identity:** confirmed **photon.codes**, not Photon Engine (Exit Games) or any other Photon. It's an open-source framework that connects AI agents to iMessage, WhatsApp, Telegram, Slack and Discord. Version 2.0 (beta) adds email and voice. It claims under 1 s end-to-end latency, SOC 2 Type II and HIPAA support.
- **SDK and quick-start:** the TypeScript SDK is **`spectrum-ts`** (GitHub photon-hq/spectrum-ts). Sign up at app.photon.codes and set `PROJECT_ID` and `PROJECT_SECRET`. Then call `Spectrum({providers:[imessage.config()]})` and loop over `app.messages`, replying with `space.send(...)`. Webhooks are available too. Search results quote its builders page as promising to **double the prize** for Spectrum projects that win at hackathons it doesn't sponsor `[u]`; the page itself returned 404. There's no listed pricing, and an anecdotal report says the free plan includes an iMessage number `[u]`.
- **Likely challenge `[u]`:** "best agent on iMessage or messaging using Spectrum." It might not have a formal track, since it's an "Other" sponsor.
- **Build angle (strong for the cascade):** **the top tier of the cascade is a human over iMessage.** When the cloud model is still unsure, the Pi texts a snapshot to the owner ("Is this a person or a coat?"). The reply becomes a labeled few-shot prototype. That covers human-in-the-loop, learning from messy data, and a live demo judges can join from their own phones. It's about 20 lines of TS on the Pi or a laptop.

## Recommendation
Rank these behind the hardware-native tracks (NVIDIA, EOG, State Farm, Niantic). Among these four, **Northmark** fits the efficiency story best, and **Photon** is the cheapest add-on that makes the demo interactive. Skip 8090 unless the noon text surprises. Treat Spacetime as an MQTT swap only if Godfrey wants it.

## Sources
- https://zeroday.hackutd.co (sponsor links, schedule)
- https://devpost.com/software/datadriver
- https://nmc2.com
- https://www.8090.ai · https://docs.8090.ai
- https://clockworklabs.com/join · https://spacetimedb.com/docs/ · https://spacetimedb.com/docs/intro/what-is-spacetimedb
- https://photon.codes/ · https://photon.codes/docs
- Search-snippet only `[u]`: photon.codes/builders (returned 404 when opened); job-board and aggregator pages for the NorthMark $2.8B figure and 8090's leadership and funding.
