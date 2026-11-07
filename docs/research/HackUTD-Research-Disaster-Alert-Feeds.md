---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, alerts, earthquake, disaster, cap, same]
---
# Research: official disaster alert feeds the node can listen to

Part of [HackUTD-2026](../HackUTD-2026.md), for [HackUTD-Idea-Home-Monitor](../HackUTD-Idea-Home-Monitor.md). Agent research, 2026-11-07 evening. [u] = unverified.
Builds on HackUTD-Research-Lifeline-Seismic (vault note) (sensing, USGS feed, ShakeAlert licence).

## Bottom line
- **Nobody, public or secret, detects earthquakes long before they happen.** Prediction does not exist (USGS). The fastest real signal is **early warning**: seconds, from P-waves, regional only. In the US that is **ShakeAlert**, West Coast only, and third parties need a USGS licence. Texas has none.
- **"Trusted channels" is the right instinct.** Almost every official warning in the world is published in one format: **CAP** (Common Alerting Protocol, OASIS XML). If the node parses CAP, it can read the NWS, FEMA, GDACS and many national feeds with one parser.
- **The node can only listen.** Public alert systems are one-way. Transmitting on NOAA Weather Radio, EAS or SAME frequencies is illegal for us. "Talking back" means our own channels: SMS/call, dashboard, Meshtastic LoRa between homes.
- **Best find for this project: NOAA Weather Radio (SAME) via a ~$30 RTL-SDR.** It is a **radio broadcast**, so it keeps working when Wi-Fi and internet are down (the outage is the point of the box). It carries NWS warnings and, nationally, civil/EAS alerts relayed through NWR [u for which non-weather alerts reach DFW].

## The menu
| Source | What it covers | How you get it | Needs internet? | Access | Fit for us |
|---|---|---|---|---|---|
| **NOAA Weather Radio + SAME** | All NWS warnings (tornado, flood, severe storm, winter, heat) + relayed civil alerts | RTL-SDR on 162.400–162.550 MHz → `rtl_fm` → `samedec` (Rust) or `multimon-ng` + `dsame` (Python). SAME headers are sent 3 times; filter by FIPS county + event code (TOR, FFW, SVR, EQW…) | **No** | Free, receive-only | **Top pick.** Works in the outage; real decoded alert on stage |
| **NWS API** `api.weather.gov/alerts/active?area=TX` | Same NWS warnings, with polygons | HTTPS GeoJSON, CAP fields in `properties` | Yes | Free; **must send a User-Agent** naming the app + contact | Easy online path; use for the dashboard map |
| **FEMA IPAWS-OPEN All-Hazards feed** | Everything in IPAWS: NWS + state/local emergency managers (evacuations, shelter-in-place, AMBER, civil) | CAP XML, PIN-controlled | Yes | Free, but **MOA with FEMA + User Portal approval**. Not doable in 24 h | Production path; say so in the pitch |
| **USGS earthquake GeoJSON** `earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson` | Confirmed quakes worldwide (minutes after) | Poll every 60 s | Yes | Free | Confirms/labels our accelerometer triggers |
| **EMSC websocket** `wss://www.seismicportal.eu/standing_order/websocket` | Quakes worldwide, push on insert/update | Websocket JSON (official Python sample) | Yes | Free, CC BY 4.0; EMSC warns data may be delayed or wrong | Faster push than polling USGS |
| **GDACS** `gdacs.org/xml/gdacs_cap.xml` (UN/EC) | Global: earthquakes, cyclones, floods, volcanoes, wildfires, drought, with Green/Orange/Red levels | RSS with embedded CAP | Yes | Free | "Works anywhere in the world" slide |
| **ShakeAlert** (USGS) | Earthquake early warning, seconds | Message server | Yes | **Licence** (pilot → licensed operator), CA/OR/WA only | Not for us; mention only |
| **WEA / cell broadcast** | The alerts phones get (presidential, imminent threat, AMBER) | An LTE modem *may* receive them (`AT+CSCB`) | Cell network | Free | **Unproven** [u]: no SIM7600/Quectel docs confirm it; skip |
| **Galileo EWSS** (EU) | Civil alerts over GNSS, in E1-B I/NAV (works with existing Galileo receivers) | Raw nav frames from the GNSS chip | **No** | Free | Europe only, operational status unconfirmed [u]. Pitch "what's next" |
| **QZSS DC Report** (Japan) | JMA quake/tsunami alerts over satellite L1S, ~every 4 s | u-blox M8 `RXM-SFRBX` → decoder (`unagi`, `QZQSM` lib) | **No** | Free | Asia-Oceania only. Good proof that satellite alerting is real |

## How this plugs into the box
1. **Online:** poll NWS (TX, Dallas county) + USGS + EMSC websocket → one CAP-shaped event object → same alarm rule as local sensors.
2. **Outage:** RTL-SDR + SAME decoder keeps the warnings flowing with no internet. [u: whether the RTL-SDR fits the low-power budget on the ESP32 side; it needs the Pi or a USB host.]
3. **Fusion:** a local trigger (accelerometer) + a confirming feed event = high confidence. Feed only = "warning for your area, check in now". Local only = "something shook *here*" (USGS later confirms or not).
4. **Relay:** forward a decoded warning to neighbouring nodes over Meshtastic so one radio covers a street.
5. **Demo:** NWS sends a **weekly test (RWT)** on NWR [u: Dallas day/time], or replay a recorded SAME burst into the decoder; show it parsed live.

## Open
- Buy an RTL-SDR (~$30–40) for the build? Rafael/Godfrey to decide.
- Which NWR transmitter covers UTD/Richardson and its frequency [u].
- IPAWS MOA as a post-hackathon step, if the project continues.

## Sources
- [NWS API docs](https://www.weather.gov/documentation/services-web-API)
- [FEMA IPAWS-OPEN developers](https://fema.gov/hy/emergency-managers/practitioners/integrated-public-alert-warning-system/technology-developers/alert-origination-software-providers) · [IPAWS-OPEN v4.02.06 interface guide (draft, 2024)](https://content.govdelivery.com/attachments/USDHSFEMA/2024/09/11/file_attachments/2994434/IPAWS-OPEN-v4-02-06_InterfaceDesignGuide_Draft.pdf) · [REC Networks IPAWS poller](https://recnet.com/node/3729)
- [samedec](https://docs.rs/crate/samedec/0.4.2) · [dsame](https://github.com/A-c0rN/dsame)
- [EMSC web services](https://seismicportal.eu/webservices.html) · [EMSC realtime](https://www.seismicportal.eu/realtime.html)
- [gdacs-api (unofficial)](https://pypi.org/project/gdacs-api) · [CAP alert extractor listing GDACS CAP URL](https://apify.com/datamule/cap-alert-extractor.md)
- [EUSPA Galileo EWSS](https://www.euspa.europa.eu/galileo-ewss) · [CNES EWSS poster 2025](https://cnes.fr/sites/default/files/2025-12/RTN-2025_Poster_61_Emergency_Warning_Satellite_Service.pdf)
- [QZSS DC Report](https://qzss.go.jp/en/overview/services/sv08_dc-report.html) · [unagi decoder](https://awesome.ecosyste.ms/projects/github.com%2Fdarashi%2Funagi) · [QZQSM library](https://www.arduinolibraries.info/libraries/qzqsm)
- [PinePhone forum: EG25-G and WEA](https://forum.pine64.org/showthread.php?tid=10480)
