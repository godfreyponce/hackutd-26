---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research]
---

Part of [HackUTD-2026](../HackUTD-2026.md). Niantic Spatial is a Bronze sponsor ([HackUTD-Event-Info](../HackUTD-Event-Info.md)). Their track prompt is unknown until noon. Researched 2026-11-07 at about 8:30 AM. Tags: [u] = unverified, (p) = primary source.

## Sponsor card
| Item | What I found |
|---|---|
| Platform | Reconstruct / Localize / Understand, all built on the **Large Geospatial Model** (trained on 30B+ posed images) (p, llms.txt). LGM API access to developers is **not confirmed**, so treat the LGM as pitch language, not a tool. |
| VPS 2.0 | **Coarse:** global lat/long/heading with no map, either on-device fusion or a cloud geofix that sends about 4 requests/s and can take 60 s or more on the first fix. **Precise:** 6DoF pose against a **processed VPS Site**, which you build from a Scaniverse capture (p, VPS2 docs). |
| NSDK 4.1 | Downloads for **Unity, Swift, and Kotlin** only, each with a sample repo (`nsdk-samples-csharp/-swift/-kotlin`). It **requires a Scaniverse business account** (p, downloads). ROS 2 support is "early access, on request" [u, secondary]. |
| Python / Linux | **No official NSDK for Python or Linux.** The one open Python piece is **SPZ**, their MIT-licensed compressed splat format (C++ core, Python via `pip install .`, WASM, plus a browser converter between PLY and SPZ) (p, GitHub). |
| Scaniverse | Captures on a phone (iOS/Android) or a 360° camera. Exports splats as PLY/SPZ/USDZ and meshes as GLB/USDZ. **Uploads accept only 360° video** (.insv or equirectangular .mp4), and the Free plan can't generate 360° assets (p, 360 docs). I found no path for uploading ordinary video or images. |
| Free tier | $0 plan: 20k credits/month, about 10 min of processed mobile capture, about 1,500 VPS queries, 5 seats. Includes splats, meshes, VPS maps, and FBX/SPZ/PLY export. **"Custom API integration" is Enterprise-only**, so there is no public REST API (p, pricing). |
| Time to a key | Sign up for Scaniverse business → NSDK auth. The docs now offer a token-based alternative to API keys (p, 3.17 docs). Estimated 15–30 min [u]. Any approval gate is unknown. |
| 8th Wall | **Dead for new work.** Logins, editor, and exports ended Feb 28, 2026. Hosted projects run until Feb 28, 2027. Open-sourcing is only "being explored", and VPS-for-web is excluded (p, blog). |
| Past challenges | **#SplatYourWorld** (Jul 2026, $4k, Plus/Pro users only): Reconstruction Quality 50%, Scale & Coverage 25%, Real-World Value 25%. Splats from non-Scaniverse pipelines were **ineligible** (p). **Explore Together** (year not stated, $15k): VPS usage, innovation, the "explore together" mission, and completeness (p). |

**What they reward:** real-world spatial capture with practical value, plus creative use of VPS. Their current marketing is about robotics and physical AI (USDZ export to Isaac Sim) [u, secondary].

## Feasibility verdict
**Partial.** A Pi camera **cannot feed their cloud directly.** Scaniverse ingests only phone captures or 360° video, and NSDK has no Linux or Python build. Every real Niantic integration has to go through **a phone running Scaniverse or an NSDK sample app**. The Pi rig then works *in the coordinate frame Niantic produces*. That is honest and doable in 24 h, but the Niantic part is a supporting layer, not the core.

**Exact steps (about 3–4 h of Godfrey's time, done in parallel):**
1. At 12:05, make a free Scaniverse business account on a phone and confirm NSDK auth works (token or key). Stop if there's an approval wait.
2. Scan the booth/table area with Scaniverse mobile. Under 10 min of capture stays within the free tier. Include the calibration-board trick if it's offered for mobile [u].
3. Process the scan in the cloud and export the **splat (PLY/SPZ) and mesh (GLB)**. Also generate a **VPS map** of the same space if the free tier allows it (it should, per the pricing page).
4. On the laptop or Pi: load the mesh with Python (trimesh [u]) and splats with `spz`. Register the pan/tilt base in that frame with 3–4 measured points or a printed tag.
5. For each detection: (pan, tilt) step counts + bbox center → a ray → ray-cast against the mesh → a 3D point in Niantic's frame. Log it.
6. Tablet UI: a web splat viewer (any open three.js splat viewer [u]) showing the scan with 3D pins at each detection.
7. Optional VPS stretch: an Android phone running the `nsdk-samples-kotlin` VPS sample localizes against the Site. The judge holds the phone and sees the same pins. Expect this to break: Unity/Kotlin build time plus first-fix latency.

**Cut line:** if step 1 or 3 stalls by 3 PM, drop the Niantic track. A turntable splat built off-pipeline doesn't count for them, by their own SplatYourWorld rule.

## Build angles
1. **Spatial memory sentry (best fit).** The "Look less, think less" pan/tilt cascade from [HackUTD-Ideas](../HackUTD-Ideas.md) stays the core. Niantic supplies the *world model*: a Scaniverse scan of the room. Every detection is anchored as a 3D pin in the scan, so the camera **knows where things are, not just what it saw**. It can then skip looking at regions that haven't changed, which ties straight back into the efficiency story. Angle for judges: "physical AI with a geospatial memory", matching their robotics push.
2. **Stepper turntable digitizer → Niantic-format assets.** A stepper turntable with the Pi camera, where known angles act as known poses (no SfM needed). Reconstruct on the laptop and export **SPZ via Niantic's open library**. A Scaniverse phone scan of the same object serves as the ground-truth comparison. This is weaker for the track: it uses their *format* but not their platform, and their own challenge rules excluded outside pipelines. Use it only if the noon prompt is about splats or capture.

## First pitch sentence
"Our camera doesn't just see objects, it remembers where they are: every detection from our edge-AI pan/tilt is pinned into a Niantic Scaniverse scan of this room, so the system knows the world well enough to stop looking at what hasn't changed."

## Sources
- https://nianticspatial.com/llms.txt
- https://ardk-dev-documentation.eng.nianticspatial.com/docs/nsdk/features/vps2/
- https://ardk-dev-documentation.eng.nianticspatial.com/docs/nsdk/downloads/
- https://www.nianticspatial.com/docs/
- https://www.nianticspatial.com/pricing
- https://nianticspatial.com/docs/scaniverse/360camera/
- https://github.com/nianticlabs/spz
- https://info.nianticspatial.com/blog/next-chapter
- https://nianticspatial.com/splat-your-world-challenge
- https://info.nianticspatial.com/blog/introducing-the-explore-together-challenge
- ROS 2 early access and the LGM prototype status come from search snippets only (robotics.press, kushyanth-portfolio blog), not opened [u]
