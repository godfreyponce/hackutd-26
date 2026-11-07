---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research]
---
Part of [HackUTD-2026](../HackUTD-2026.md).

# Sponsor card: Axxess

**Bottom line:** No source confirms an Axxess track at HackUTD 2026; that gets settled at noon. If one appears, expect a software challenge about documentation or the workflows of care delivered at home. Our camera wins by turning the box into a privacy-safe **sensor that writes the visit note itself**: it sends structured events, not video, into the workflow a clinician already uses. Don't pitch it as a security camera.

## What Axxess builds
- Software for care delivered at home: **home health, home care, hospice, palliative**. It also offers CAHPS patient surveys, **Axxess CARE** (staffing), revenue-cycle work, Axxess Connect, Business Intelligence and Workforce Management. Its homepage claims "9,000+ organizations." [1]
- **Axxess intelligence** is its AI layer. Features it names include predictive analytics, "Real-Time Monitoring," automated documentation, compliance and telehealth. [1]
  - Named tools in search snippets (pages not opened): **Care Predictor** (spots patients who may qualify for hospice early), a hospice tool that predicts symptom flare-ups within 7 days, **OASIS Scrubber** (QA on OASIS documentation), and **Ask Axxess** (AI search). [u]
  - Its 2026 report says Axxess intelligence can surface patients **flagged for high fall risk**. [2]
- **Remote patient monitoring:** none of the pages I opened describe an RPM product, a device feed or alert thresholds. Telehealth and "Real-Time Monitoring" are the closest they come. [1]
- **Ambient documentation:** I found no Axxess-branded scribe. Search snippets mention a partnership with nVoq (dictation and ambient AI). [u]

## Data / API access
- A third-party directory lists three **ONC-certified APIs**: § 170.315(g)(7) patient selection, (g)(8) data category request and (g)(9) all-data (C-CDA). These are the standard FHIR/C-CDA patient-access endpoints. It gives no developer portal URL and no documented auth. [3]
- A Supergood.ai snippet (a vendor with a reason to say this) says expanded access goes through negotiated order forms, and that Axxess has no public developer portal or SDK. [u]
- **What this means for us:** assume **no live Axxess API** at the event unless they hand out a sandbox at noon. Plan to emit **FHIR-shaped JSON** (an `Observation` for a detected event, a `Flag` or `Communication` for an alert) to a mock endpoint. "Drops into a FHIR pipeline" is a claim we can defend.

## Hackathon history
- Axxess runs its **own Axxess Hackathon** at UTD: 30 hours, "Healthcare Innovation," Feb 21–22, 2026, in ECSW. **No hardware is provided**; it suggests simulators. [4]
- The 2026 winner was **MedScribe** (UTPB), a mobile app that listens during a visit, writes notes, tracks medication changes and flags urgency. The challenge asked for a diagnostic assistant "capable of streamlining documentation during consultations," with telehealth and ER triage, multiple languages and regulatory compliance. [5]
- Axxess was a **HackUTD sponsor** at HackUTD IX (about 2022). The article lists no Axxess challenge or winner for that year. [6]
- **Read:** their judges reward documentation relief plus compliance. Hardware is rare at their events, which helps us stand out.

## Pain points they state
- **Workforce:** 62.5% say recruitment and retention is their top 2026 challenge; 43.8% cite training and 28% cite burnout. [2]
- **Documentation burden:** "AI transforms documentation from a burden into a tool for early risk identification." [2]
- **Remote monitoring:** 37.5% are excited about integrating it; 46.9% see an opportunity in chronic disease. [2]
- **Regulation:** only 18.8% feel very prepared. [2]
- Also: readmissions, rural and low-mobility patients, compliance and audit risk. [1]
- Falls, wandering and medication adherence are **our inference** from the fall-risk flag and the general care-at-home context. Axxess does not state them as pain points in the pages I opened.

## Likely challenge (guess)
In order of likelihood:
1. Reduce clinician documentation and admin time (MedScribe lineage).
2. Spot patient risk early between visits (fall risk, deterioration).
3. Close the staffing gap: one nurse covering more patients.

## Build angles
1. **"Silent visit log" (best fit).** The Pi watches the home. The cheap detector handles person, pose and fall-like events, and the VLM runs only when unsure. The device sends **events only**: "fall detected 14:02," "no movement 6 h," "pill box opened 08:10." These land in a between-visit timeline that pre-fills the nurse's next note and feeds a risk flag. It hits documentation and risk together.
2. **Medication-check assist.** Teach the device a patient's pill bottles from 5 photos. A voice prompt asks for the 8 AM dose, and the camera confirms the bottle was picked up and logs adherence. The tablet UI shows caregivers what was missed. It reuses our speech-therapy voice experience.
3. **Wandering and exit watch for dementia hospice/home care.** Pan/tilt follows the patient toward a door and alerts a family caregiver or agency only past a zone or time threshold. Patch-skipping keeps it at low power and always on.

All three output FHIR-like JSON to a mock "agency inbox."

## First pitch sentence
"Home health nurses see a patient for an hour a week. Our camera watches the other 167, never sends video, and turns what happened into a ready-to-chart event log and a fall-risk alert."

## Privacy talking points
- **Video never leaves the device.** Frames are processed in RAM on the Pi 5 and thrown away. Only text and JSON events go out. Most of the time the cloud is never called at all, because the cascade handles it on the device.
- **Minimum necessary:** each event carries a type, time, confidence and room, with no face crops. Show the judge the actual payload on the tablet.
- **The cloud is opt-in and redacted.** When the device escalates an uncertain case, it sends a blurred or cropped frame or a text description, and logs that it did. We can say the system is "built toward HIPAA minimum-necessary." We cannot say "HIPAA compliant." That is an organizational status, not a device feature.
- **Visible state:** an LED shows when the camera is active. A physical privacy pose (camera tilted to the ceiling) proves it is off.
- **Consent and locality:** the patient or family controls the zones. Data stays local until the agency pulls it.

## Open questions
- Does Axxess have a track at HackUTD 2026, and does it provide a sandbox or API? Check at noon.
- Fall detection from one camera: how reliable is it in our demo lighting? Test it before pitching it.

## Sources
1. Axxess, "Understanding the Power of Axxess intelligence": https://www.axxess.com/blog/operational/understanding-the-power-of-axxess-intelligence/
2. Axxess, "2026 Axxess Industry Growth Insights Report": https://www.axxess.com/blog/hospice/the-2026-axxess-industry-growth-insights-report-understanding-ai-workforce-challenges-and-regulatory-change/
3. APIs.io, Axxess provider profile (third party): https://apis.io/providers/axxess/
4. Axxess Hackathon page: https://www.axxess.com/hackathon
5. UTPB, "From pressure to excellence" (2026 winners): https://utpb.edu/success/2026/04/from-pressure-to-excellence-four-computer-science-students-mastering-a-hackathon
6. UTD CS, "HackUTD Hosts its Largest Hackathon" (HackUTD IX): https://cs.utdallas.edu/?p=26350
