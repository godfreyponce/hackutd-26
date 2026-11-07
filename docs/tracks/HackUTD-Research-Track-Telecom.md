---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research]
---

Part of [HackUTD-2026](../HackUTD-2026.md). Sponsor card for **T-Mobile** (title sponsor) and **AT&T** (listed as "Other"; they host Saturday dinner, 7:30 PM). Researched 2026-11-07 ~8:30 AM, before the noon track reveal. See [HackUTD-Event-Info](../HackUTD-Event-Info.md), [HackUTD-Research-Judging](../research/HackUTD-Research-Judging.md), [HackUTD-Ideas](../HackUTD-Ideas.md).

## Bottom line
- **The T-Mobile track will probably be a software or data problem, not a hardware one.** In 2025 every T-Mobile-track project I could find built a **customer-sentiment or "happiness index" dashboard** (T-Pulse's README says it was "created for the T-Mobile track at HackUTD 2025"). I could not open the 2025 challenge text or the winners list: Devpost and HackUTD's Notion block automated fetches.
- **Expect no AT&T track.** AT&T is a dinner sponsor in the "Other" tier [u: confirm at noon].
- **If T-Mobile's 2026 prompt is customer experience again,** our camera fits only weakly. Pitch it as a connected-device or network story, and enter T-Mobile only if the prompt mentions devices, IoT, the network, edge or AI efficiency.
- **Do not build around a live carrier API.** Every network API I could find (Aduna, DevEdge) needs a business agreement, kit hardware or a portal login, so none is a 24-hour quick start. Simulate the network side and say so.

## Likely challenge (guesses, ranked)
1. **Customer experience or sentiment with AI** (a repeat of 2025) [u]. Fit: weak. Possible angle: "network-aware" status reporting from the device.
2. **AI-native network or connected devices.** T-Mobile's 2026 T Challenge was framed around speeding the shift to an **"AI-native telco"**, with winners in network intelligence, automation and customer experience. Fit: strong.
3. **Security or "Zero Day" themed** (the event name) [u]. Fit: medium (on-device processing keeps raw video private).

## Usable APIs and resources
| Resource | What it is | Access for a 24 h build |
|---|---|---|
| **Aduna** (backed by AT&T, T-Mobile and Verizon) | CAMARA-standard network APIs. First ones: **Number Verification** and **SIM Swap**. AT&T launched them via Aduna in Feb 2026; a single cross-carrier number-verification API arrived around Jul 2026. | Business contact or partner platforms only. **No sandbox found.** Not worth it. |
| **T-Mobile DevEdge IoT Dev Kit** | CAT-M kit on a Zephyr SDK with a SIM (500 MB) and free location/SMS APIs. Sold for $99 at its 2022 launch. **CAT-M only, not 5G.** | Needs the physical kit. Only if T-Mobile hands kits out at the fair [u]. |
| **DevEdge / CAMARA Quality on Demand** | Requests better bandwidth or latency for a device session (DT/T-Mobile launch, 2023). | Early-access program in 2023; current status unknown [u]. |
| **Nokia Network as Code** (third party) | CAMARA-style SDK (`pip install network_as_code`) with **simulated devices** (`name@testcsp.net`). Covers QoD, device reachability and roaming status. | Portal plus "Subscribe to Test". Whether it is free is **unverified** [u]. Best candidate if we want a real QoD call. |

Quick-start links: networkascode.nokia.io/docs/getting-started · devedge.t-mobile.com/documentation/iot-dev-kit (both blocked my fetch, so read them in a browser).

## Fireside chat (1:30 PM Sat)
I found no details. **Go to it.** It is the best source for what T-Mobile judges actually reward. Questions to ask:
- Does a hardware or edge-device build fit your track?
- Do you score on use of T-Mobile's network or APIs, or on the problem itself?
- Do any judges come from IoT/T-IoT or network engineering?

## Build angles mapped to "Look less, think less"
1. **Events, not video (bandwidth and data cost).** The cascade sends a cloud request only when the device is unsure, and otherwise uploads a small JSON event or a single crop. Add a **"bytes over the air / hour"** tile next to J/hour and convert it into cellular data cost and per-device plan size. This is the clearest carrier-relevant number.
2. **Network-aware cascade.** Add a link-state input (good / congested / down) to the escalation policy. When the link is congested, raise the on-device confidence bar; when it is down, queue escalations and replay them later. Demo it by pulling the Wi-Fi or hotspot mid-run while the funnel keeps working. Optional: a "request QoD" step when escalating something critical (simulated, or a Network-as-Code simulator call).
3. **A fleet over 5G.** Run the camera on a **T-Mobile hotspot or phone tether** for the demo and show uplink usage per device. Use it to argue that one cell can serve N cameras, against M cameras streaming video. Must be measured live, not estimated.

## Proposed first pitch sentence
"For T-Mobile's challenge: a camera that looks less and thinks less. It sends the network a few events instead of a video stream, keeps working when the link drops, and only spends cellular bytes and cloud compute when it is genuinely unsure."

## Checklist
- [ ] 8–10 AM sponsor fair: ask T-Mobile whether hardware builds fit, whether they have IoT kits or SIMs, and who the judges are.
- [ ] Noon: read the T-Mobile prompt. Enter only if it mentions devices, network, edge, AI efficiency or security.
- [ ] Bring or borrow a T-Mobile hotspot or phone for angle 3.
- [ ] 1:30 PM fireside: take notes and update this card.
- [ ] Log bytes uplinked per hour next to J/hour in the judge UI.

## Sources
- T-Pulse repo (HackUTD 2025 T-Mobile track): https://github.com/axdyv/T-Pulse
- Search snippets of the 2025 HackUTD Devpost entries (MagentaMind CHI, "Cool Project" customer intelligence, T-Time). The pages returned 403, so these are snippet only [u]: https://devpost.com/software/magentamind · https://devpost.com/software/cool-project-w4h7ob
- Deutsche Telekom, 2026 T Challenge winners (AI-native telco): https://www.telekom.com/en/newsroom/latest-updates/media-information/2026/4/t-mobile-and-deutsche-telekom-name-2026-t-challenge-winners
- TelecomTV, Aduna milestone (26 Feb 2026): https://www.telecomtv.com/content/apis/aduna-reaches-milestone-as-a-leading-provider-of-us-network-apis-54933
- SDxCentral, Aduna number verification (Jul 2026): https://www.sdxcentral.com/news/att-t-mobile-us-and-verizon-ditch-sms-for-network-based-authentication/
- DevEdge IoT Dev Kit facts come from search snippets of the DevEdge docs, Hackster and RCR (2022) [u]: https://devedge.t-mobile.com/documentation/iot-dev-kit
- The QoD and T-DevEdge launch (2023) and Nokia Network as Code SDK and simulator facts come from search snippets [u]: https://networkascode.nokia.io/docs/getting-started
- Event schedule and sponsor tiers: [HackUTD-Event-Info](../HackUTD-Event-Info.md) (zeroday.hackutd.co)
