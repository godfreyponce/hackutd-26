---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, mlh]
---

# Research: MLH Prize Cheat-Sheet

Part of [HackUTD-2026](../HackUTD-2026.md). Agent research, 2026-11-07, 8:30 AM. Read with [HackUTD-Research-Judging](../research/HackUTD-Research-Judging.md). `[u]` = unverified (not on a page opened).

## Confirmed list (Devpost, fetched today)
There are 7 MLH prizes, 1 winner each. MLH entries stack on top of the 3 sponsor tracks + 1 HackUTD track.

| Prize | Award |
|---|---|
| Best Use of Gemini API | MLH swag kits |
| Best Use of MongoDB Atlas | M5Stack IoT kit per member |
| Best Use of Tiger Data | Stream Deck Mini |
| Best Use of Vultr | "Assorted prizes" |
| Best Domain Name from GoDaddy Registry | Digital gift card |
| Best Use of Solana | Hardware wallets per member |
| Build Your Hackathon A-Team with SpaceXSI (raffle) | Cursor mechanical keyboard per member |

## Ranking by fit × effort
1. **Gemini**: high fit, low effort. It is the cloud tier of the cascade.
2. **Tiger Data**: high fit, medium effort. Its blurb names "real-time IoT monitoring" and our metrics are a time series.
3. **GoDaddy domain**: low-medium fit, very low effort. Point it at the judge UI.
4. **Vultr**: medium fit, medium effort. Host the dashboard and MQTT broker.
5. **MongoDB Atlas**: medium fit, medium effort. Only worth it if it has a distinct job (see Conflicts).
6. **Solana**: skip. Nothing in our build needs transactions, and forcing it in would be padding.
7. **SpaceXSI**: skip. It requires Cursor as the *core* coding agent plus a Grok Bot automation, both described in the write-up. That isn't our workflow, so claiming it would be dishonest.

## Gemini API (cascade Stage 4)
- **Criteria:** open-ended "Best Use". In 2025 a Pi device (Kori) won it.
- **Key:** create one in Google AI Studio (MLH link: mlh.link/gemini). No credit card is needed for the free tier.
- **Models (AI Studio docs, today):**
  - **`gemini-3.5-flash-lite`**: stable, free tier, priced for image input. **Use this.**
  - **`gemini-3.8-flash`** (new) or `gemini-3.6-flash` (stable): free tier, for hard frames. Image input isn't stated on the page `[u]`.
  - **Avoid `gemini-2.5-flash`**: deprecated, and it reroutes to 3.5 Flash-Lite on Dec 1.
  - Preview models have tighter limits.
- **Free-tier limits:**
  - Google no longer publishes per-model numbers. Check your project at aistudio.google.com/rate-limit.
  - Limits are **per project, not per key**. Daily quota resets at midnight Pacific.
  - Older third-party figures were about 5–10 RPM for Flash models `[u]`.
  - **Design for it:** escalations must stay rare (confidence gate + cooldown), and show the escalation count on the UI. That count is our pitch anyway.
  - Free-tier data may be used by Google, so don't send faces of people who haven't consented.
- **Setup:**
  1. `pip install google-genai`
  2. Set `GEMINI_API_KEY`
  3. Send the JPEG crop + prompt and ask for JSON output (label, confidence, reason).
- **Genuine use:** Stage 4 adjudicates frames the local VLM is unsure about. The write-up says "Gemini only sees N% of frames".

## Tiger Data / TimescaleDB (metrics)
- **Criteria (Devpost):** "most innovative, impactful, and performance-driven use". The blurb touts hypertables, **continuous aggregates for real-time dashboards**, and compression.
- **Account:** tigerdata.com, then Tiger Cloud. Every plan includes **two free services (beta)**, and there's a 30-day Performance trial with no card needed. Free storage is about 750 MB `[u]`, which is plenty.
- **Setup:**
  1. Create a free service and copy the Postgres connection string.
  2. `CREATE TABLE metrics(ts timestamptz, device text, fps real, watts real, stage int, escalated bool);`
  3. `SELECT create_hypertable('metrics','ts');` (newer syntax may differ `[u]`)
  4. Add a continuous aggregate per minute.
  5. A small MQTT → Postgres bridge does the inserts.
- **Genuine use:** every MQTT metric lands in the hypertable. The judge UI reads the continuous aggregates to show fps, power, and escalations per minute. Show the query latency.

## Vultr (hosting)
- **Criteria:** open-ended. HealthSense (Pi 5 + sensors) won it in 2025.
- **Credits:** **$100, no card** (MLH partner page):
  1. Register at mlh.link/vultr-discover for the promo code. Use "Student" + UTD.
  2. Verify your email.
  3. Sign up at mlh.link/vultr-signup.
  4. Billing → Gift Code.
  - If you miss the opening ceremony, ask the MLH Coach for the code `[u for this event]`.
- **Genuine use (no conflict):** one small VM running the MQTT broker (Mosquitto), the MQTT→Tiger bridge, and the judge UI, reached by the GoDaddy domain.
- **Riskier option:** host our own VLM on a Vultr Cloud GPU. That competes with Gemini for Stage 4, and $100 of GPU time goes fast `[u]`.

## MongoDB Atlas (events/prototypes)
- **Credits:** free-forever cluster with no card, or $50 student credits (mlh.link/mongodb-benefits or the GitHub Student Pack).
- **Free cluster limits:** 0.5 GB storage, 100 ops/s, 500 connections, one free cluster per project. It pauses after 30 days idle.
- **Setup:**
  1. Create the free cluster.
  2. Add a DB user and an IP allowlist entry.
  3. `pip install pymongo`
  4. Insert one doc per escalation event.
- **Genuine use:** an event log (crop thumbnail ref, each stage's verdict, final label) and per-class "prototype" embeddings. Only enter if this is a real feature, such as a "review past escalations" page.

## GoDaddy Registry domain
- **What it is:** a free domain for 1 year (MLH software page). The prize goes to the best domain name.
- **Claim:** MLH's guide links (hackp.ac/GoDaddyRegistry, /GoDaddy-medium) didn't render for me. The code is usually given at the opening ceremony or on the MLH page `[u]`. Eligible TLDs are unknown `[u]`; ask the MLH Coach at noon.
- **Genuine use:** a short, funny name pointing at the Vultr-hosted judge UI. Put it on the table sign.

## Solana / SpaceXSI
- **Solana:** devnet faucet, Anchor and an MCP server are available. There's no honest fit, so **skip**.
- **SpaceXSI:** it's a raffle, but qualifying requires Cursor + Grok Bot and opting in. **Skip** unless the team actually works that way.

## Conflicts
- **One cloud VLM:** Gemini *or* a Vultr-hosted VLM as Stage 4, not both. Pick Gemini (free, zero ops) and give Vultr the hosting job.
- **Two databases:**
  - Tiger Data (time-series) + MongoDB (events) is defensible only if each has a clear job. Otherwise judges read it as prize padding.
  - If time is short, drop MongoDB. Tiger's prize text matches us; Mongo's is generic.
- **Effort budget:** only the Gemini and domain entries are near-free. Tiger + Vultr cost about 1–2 h together `[u estimate]`.

## Sources
- hackutd-zeroday.devpost.com (prize list + MLH prize text)
- mlh.com/resources/software · mlh.com/partners/vultr · mlh.com/partners/mongodb · mlh.com/partners/solana
- aistudio.google.com/docs/models · /docs/rate-limits · /docs/pricing
- tigerdata.com/docs/about/latest/pricing-and-account-management · tigerdata.com/pricing
- mongodb.com/docs/atlas/reference/free-shared-limitations/
