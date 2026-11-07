---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research]
---
Part of [HackUTD-2026](../HackUTD-2026.md).

# Sponsor card: EOG Resources

**Bottom line:** EOG runs the same challenge every year. They hand out field time-series data (a JSON API or CSVs), and teams build a dashboard plus anomaly detection, with a prediction or optimization bonus. The data is the real judging target. Every past winner we found was software only. A device that **produces data in EOG's own schema** and runs the detection at the edge is the open lane.

## Past challenges

| Year | Challenge | Data | EOG winners (Devpost badge) |
|---|---|---|---|
| 2023 (HackUTD X) | Methane leak detection | Files seen in the ch4 us repo: `sensor_readings.csv`, `weather_data.csv`, `leak_locations_and_rate.csv`, sensor coordinates. VaporVision says it covers "24 methane sensors" at a facility near Fort Collins | **ch4 us**, **VaporVision** |
| 2024 (Ripple Effect) | Hydrate formation in gas-injection wells | Per-well time series with three streams: *Inj Gas Meter Volume Instantaneous*, *Inj Gas Meter Volume Setpoint*, *Inj Gas Valve Percent Open*. CSV upload [u: format inferred from team repos] | **PipeBrAIns** (second winner not found) |
| 2025 (Lost in the Pages) | "CauldronWatch" (Poyo's Potion Factory) | REST API `hackutd2025.eog.systems` | **PoyoLabs**, **Enchantress** |

**2023 text:** not found. From the teams' write-ups: show each sensor's trend, detect leaks, and work out which leak set off which sensor.

**2024 text** (from a team README): *"Imagine you are a lease operator at EOG… One of the challenges you face is the formation of hydrates."* Extension: *"Given data from an unseen well… predict when a hydrate is likely to form."*

**2025 text** (the official page is still live): *"Build a real-time dashboard that tracks potion levels, correlates transport tickets with drain events, and flags discrepancies."*
- **`/api/Data`:** minute-by-minute levels for `cauldron_001…012` over about a week. Query by Unix `start_date`/`end_date`.
- **`/api/Tickets`:** `ticket_id, cauldron_id, amount_collected, courier_id, date`. A ticket has a date only, no timestamp.
- **`/api/Information/*`:** cauldron lat/lon and `max_volume`, plus network edges with `travel_time_minutes`. There is also a `/swagger` page.
- **The catch:** *"ticket data … may change during judging."* The bonus is the minimum number of witches plus overflow-free routes.
- **Prizes:** Switch 2 and Ninja Creami.

## Why the winners won
- **Physics, not just ML.**
  - ch4 us and VaporVision built Gaussian plume models with wind. VaporVision split its data by time to stop overfitting (88% accuracy).
  - PipeBrAIns found the Joule-Thomson freeze effect and trained its own scikit-learn model (R² ≈ 0.94). It pitched that against "GPT wrappers."
- **The required features, with polish.**
  - PoyoLabs: a hand-drawn pixel-art dashboard, plus a chatbot and routes.
  - Enchantress: ticket matching that handled inflow during drains, tied back to oil-flow measurement.
  - Alchemetrics, a multi-agent build, won NVIDIA's prize, not EOG's.
- **Takeaway:** a correct core algorithm on *their* data, plus one visible extra. LLM chat alone added nothing.

## EOG's real field problems
- **Methane:** EOG's **iSense** is a "proprietary continuous methane monitoring solution". Facility sensors send alerts to a central control room. It was piloted in 2021 and is rolling out from the Delaware Basin. The 2023 challenge was a toy version of it.
- **Hydrates:** in injection lines, a sudden drop in volume while the setpoint holds (the 2024 challenge).
- **Volume reconciliation:** tank level vs. hauled volume vs. tickets is the 2025 challenge in costume, likely modelled on tank hauling at well pads [u].
- **In-house culture:** 65–100+ proprietary apps, according to trade press and job ads [u: not opened].
- **Not EOG-specific:** remote pads, poor connectivity, manual gauge rounds, OGI and predictive maintenance are general industry problems; no EOG source was opened [u].

## 2026 forecast
Likely shape: **a themed time-series dataset or API (a single-day "Zero Day" theme), detecting an anomaly or discrepancy, a real-time dashboard, and a forecast or optimization bonus**, with the data changing live during judging [u]. Hardware is almost never required. The 5:15 PM Sat workshop is where to ask whether a physical data source counts.

## Prep checklist (to ingest a dataset fast)
- [ ] At noon, open `/swagger` first, note units and timestamp format, then dump all the data to local Parquet.
- [ ] Have a pre-written loader ready: Unix/ISO time → pandas, wide → long, resampled per entity.
- [ ] Plot every series in the first 30 minutes and find the physical event before modelling.
- [ ] Have an event detector ready: slope plus hysteresis, a rolling z-score.
- [ ] Validate on a time split, and re-poll live data, since it changes during judging.
- [ ] Map plus a playback slider: reuse the judge UI.
- [ ] At the workshop, ask whether a physical sensor is judged and how scoring works.

## Build angles (reusing the camera rig)
1. **Edge gauge reader (strongest fit).** The pan/tilt camera sweeps analog gauges and a sight glass. The cheap detector reads the needle, and the VLM or cloud handles only unsure readings. It emits rows **in EOG's own schema** and runs their discrepancy logic live, so their data and our device sit side by side on one dashboard.
2. **Leak watcher.** An MQ-4 methane sensor plus the camera: a spike makes the turret slew and look. Few-shot learning flags frost on a fitting (a hydrate cue). It works offline and sends only exceptions, a "pocket iSense." Check the venue rules before releasing any test gas [u].
3. **Data-only fallback.** Run the cascade on their series: a statistical detector → a small model → an LLM only when unsure, with the escalation funnel on the tablet.

**First pitch line:** "Your data starts as a gauge someone drives out to read. We built the device that reads it at the pad, runs your anomaly check at the edge, and only phones home when it's unsure."

## Sources
- [ch4 us, Devpost (EOG winner, HackUTD X)](https://devpost.com/software/ch4-us)
- [VaporVision, Devpost (EOG winner, HackUTD X)](https://devpost.com/software/vaporvision)
- [ch4 us repo (hacksolutions)](https://github.com/hacksolutions/hacksolutions.github.io)
- [PipeBrAIns, Devpost (EOG winner, 2024)](https://devpost.com/software/pipebrains)
- [HackUTD-RippleEffect README (2024 challenge text)](https://github.com/nihaal419/HackUTD-RippleEffect)
- [CauldronWatch challenge page (EOG 2025)](https://hackutd2025.eog.systems/)
- [HackUTD 2025 API swagger.json](https://hackutd2025.eog.systems/swagger/v1/swagger.json)
- [PoyoLabs, Devpost (EOG winner 2025)](https://devpost.com/software/poyolabs-47n0fz)
- [Enchantress, Devpost (EOG winner 2025)](https://devpost.com/software/enchantress-w2li90)
- [Alchemetrics, Devpost (NVIDIA winner 2025)](https://devpost.com/software/abc-xapnio)
- [Brew67](https://devpost.com/software/brew67) · [Cauldron-FlowGuard AI](https://devpost.com/software/cauldron-flowguard-ai) (non-winning 2025 entries)
- [HackUTD 2025 Devpost (prize list)](https://hackutd-2025.devpost.com/) and [winners gallery](https://hackutd-2025.devpost.com/project-gallery)
- [World Oil, Jan 2023: EOG joins UNEP methane partnership (iSense)](https://www.worldoil.com/news/2023/1/5/eog-resources-joins-unep-s-oil-and-gas-methane-reporting-partnership/)
