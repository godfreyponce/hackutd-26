---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research]
---
Part of [HackUTD-2026](../HackUTD-2026.md).

# Finance + law sponsors (low-fit group): PNC, Toyota FS, Goldman, Capital One, Winstead

**Bottom line:** none of these sponsors has ever given a prize to a hardware-first build, with one exception: **Toyota**, which did so once (Guardian Wheels, 2023). Enter **Toyota only if its noon challenge text mentions the vehicle, the cabin, or inspection**. Keep **Winstead** as a possible third slot if its prize turns out to be "best startup / viability". Skip PNC, Goldman, and Capital One unless the challenge text surprises us.

Past winners were taken from the Devpost galleries: every project page with a winner ribbon was opened and its prize labels were read.

## PNC Bank (Platinum; workshop 2:30 PM)
- **Past winners.** 2025: AutoPM, Prodify (built with Nemotron and React), and ProDuh (a multi-agent "PM lifecycle" tool that works across Jira, ADO, and Confluence). 2024 (Ripple): Data Pattern Observatory, FinnAI (budgeting), and Hermes (investing access for the underbanked). PNC did not sponsor in 2023.
- **Pattern.** 2025 was clearly a product-manager productivity / agentic-tooling challenge. 2024 was consumer finance and data.
- **Likely 2026 challenge.** Agentic workflow automation for internal teams [u].
- **API/data.** None found.
- **Hardware fit: 1/5.**
- **Angle.** A weak one: an ATM or branch "tamper sentry" that watches the card slot cheaply and escalates only when something is unusual. This only works if the challenge text mentions fraud or physical security. Go to the 2:30 workshop only if we are undecided.

## Toyota Financial Services (Gold)
- **Past winners.** 2025 (TFS): Toyotron (a phone-agent car-buying concierge, also won NVIDIA), Car Thing / "Kachow" (car-purchase research using Nemotron), and Hingine (a swipe-to-match car finder with financing lessons). 2024 (Toyota): Fuelicient, ToyoTrends, and an unnamed fuel and emissions data app. 2023 (Toyota): **Guardian Wheels** (also won General) and Toyota EdVenture (in-drive learning). 2022 (HackUTD IX) challenge: "build a solution to improve the end-to-end vehicle experience."
- **Pattern.** Since the sponsor became *TFS* (2025), every winner has been about car buying, financing, or trade-in, built as an AI agent plus a web app. Hardware has not won since 2023.
- **Guardian Wheels as a precedent.** It was an Arduino Grove board plus a *laptop camera*. Motion or sound triggers a snapshot, Twilio alerts the owner and police, and it had a drone that could not be programmed. Its own write-up says the team lacked hardware experience. So the bar for hardware is low, and a physical demo that works end to end beat software entries. That precedent comes from before the TFS rebrand, though.
- **Hardware fit: 3/5** (only if the challenge text allows anything beyond buying and financing).
- **Credible edge-camera angles:**
  1. **Lease-return / trade-in inspection camera.** The pan/tilt head sweeps a vehicle (a toy car works on the demo table) and logs dents and scratches against a reference set built few-shot. Patch-skipping means it re-examines only areas that changed. Uncertain damage escalates to Nemotron along with a cost estimate. This ties to TFS's actual business (lease-end wear-and-tear charges and trade-in valuation) [u]. **Strongest angle.**
  2. **Parked-car in-cabin sentry** (Guardian Wheels redone properly). It detects a child, pet, or bag left behind, or an intruder. "Look less" becomes a *battery-drain* story: a parked car cannot run a GPU all night. It fits a vehicle-experience challenge but not a finance one.
- **Recommendation.** Enter if the challenge mentions inspection, condition, the vehicle experience, or "any solution". Skip if it reads "AI car-shopping assistant".

## Goldman Sachs (Gold; workshop 6:10 PM)
- **Past winners.** 2025: 404 Not Found (vendor onboarding on AWS), TrustIssues.AI (multi-agent due diligence using Nemotron), and Stamped (client and vendor onboarding). 2024: AllBank, Pay Your Daddy (also General), and TalkTuahBank (a voice bank agent, also General). 2023: Gold Mine and TrendSent (earnings forecasting) and StoryStocks. 2022: a "tool for U.S. investors".
- **Likely 2026 challenge.** Document or agentic financial workflows (onboarding, KYC, forecasting) [u].
- **API/data.** None found.
- **Hardware fit: 1/5.**
- **Angle.** None that is genuine. The cascade's "escalate only when unsure, with a human approving" idea mirrors TrustIssues.AI's human-in-the-loop design, but bolting a camera onto a KYC challenge would read as forced. **Skip.**

## Capital One (Silver; "Switch competition" 6:45 PM)
- **Past winners.** 2025, a single prize ($300): **Spendy**, a kids' money-management app built with Expo and React (it also won Best Design). 2022: e-val. No Capital One prize was listed in 2023 or 2024.
- **What the "Switch competition" is.** Searches found no Capital One program by that name, and the event site does not describe it. Most likely it is an on-site side activity (a mini-game or raffle, possibly for a Nintendo Switch) and not a project track [u]. **Ask at the Capital One table.** It costs nothing to drop in if we are not mid-integration.
- **API/data.** Capital One's old hackathon API, "Nessie", appears in coverage of its DevExchange hackathons. Whether it is live now is [u].
- **Hardware fit: 1/5.**
- **Angle.** None for this build. **Skip the track.** The 6:45 event is optional.

## Winstead PC (law firm, Gold)
- **Past HackUTD presence.** None found. This appears to be its first year.
- **Pattern elsewhere.** Winstead sponsors *startup* competitions: it has judged the Texas A&M New Ventures Competition (and awarded a Winstead prize there), and it partners with MassChallenge Texas and Texas Health Catalyst. Its prize is therefore likely judged on business viability, IP, or a legal-tech theme [u].
- **Hardware fit: 1/5 as a technical match. Up to 3/5 if the prize is "best startup".**
- **Angle.** Two framings:
  - **Privacy by design:** raw video never leaves the device, and only uncertain crops escalate to the cloud. That is a real compliance argument for camera products under biometric/privacy rules [u on any specific statute].
  - **A defensible-IP story:** the combination of patch-skip, cascade, and few-shot learning is something a startup lawyer can evaluate.
- **Recommendation.** Use as the third track **only** if its text is "best startup / most viable / legal-tech". Have one slide ready on privacy and IP.

## Recommendation
1. **Toyota FS:** enter conditionally, using the lease-return inspection angle (fallback: the in-cabin sentry). Decide at noon from the exact wording.
2. **Winstead:** a conditional third slot if its prize is about startup viability.
3. **PNC, Goldman, Capital One:** do not enter. Our sponsor slots are worth more on NVIDIA, EOG, or CBRE ([HackUTD-Ideas](../HackUTD-Ideas.md)).

## Sources
- https://hackutd-2025.devpost.com/ · https://hackutd-ripple.devpost.com/ · https://hackutd-x.devpost.com/ (prize lists) and their `/project-gallery` pages 1–2 (winner ribbons)
- Winner pages: https://devpost.com/software/guardian-wheels · https://devpost.com/software/toyotron · https://devpost.com/software/car-thing-1dsxyk · https://devpost.com/software/hingine · https://devpost.com/software/produh · https://devpost.com/software/coffee-overflow · https://devpost.com/software/spendingwithspendy · https://devpost.com/software/talktuahbank · https://devpost.com/software/toyota-edventure · https://devpost.com/software/gold-mine
- HackUTD IX recap (2022 Goldman/Toyota/Capital One challenges): https://cs.utdallas.edu/?p=26350
- https://hackutd.co (sponsor list; no Switch details)
- Winstead startup sponsorships: https://m.winstead.com/News/Firm-News/349605/Winstead-Sponsors-Texas-AM-New-Ventures-Competition · https://winstead.com/News/Firm-News/352804/Winstead-Partners-with-MassChallenge-Texas (search-result summaries only; not opened [u])
