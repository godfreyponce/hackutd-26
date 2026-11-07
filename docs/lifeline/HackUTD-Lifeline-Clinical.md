---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, lifeline, research]
---
Part of [HackUTD-2026](../HackUTD-2026.md) · idea [HackUTD-Idea-Shortlist](../HackUTD-Idea-Shortlist.md) #1.

# Lifeline Grid: clinical and domain truth

Research pass for the "time until harm" ranking. Sibling note: HackUTD-Research-Lifeline-Competitors.
Confidence labels: **Sourced** (primary or reputable source linked), **Vendor** (manufacturer or vendor claim), **Estimate** (our own arithmetic or judgment, not a source).

## 1. Headline findings (read this first)

1. **Cold and heat killed more people than device failure.** In Winter Storm Uri, 158 of 246 official deaths were hypothermia; only 25 were "exacerbation of pre-existing illness" (which includes dialysis and oxygen disruption and loss of power to life-sustaining equipment). Most hypothermia victims were 60+. ([DSHS mortality report, Dec 2021](https://www.dshs.texas.gov/sites/default/files/news/updates/SMOC_FebWinterStorm_MortalitySurvReport_12-30-21.pdf)). After Beryl, half of Harris County storm deaths were heat related ([AP via ABC13](https://abc13.com/post/hurricane-beryl-related-deaths-texas-rise-36/15096054/)). **Decision:** the node must measure indoor temperature, and the ranking must treat indoor temperature as a harm clock alongside the device battery. The radar (presence, motion) matters most here: an older person who is still in a cold house and not moving is the Uri death pattern.
2. **Nobody monitors the device battery today.** Every existing system is a static registry (who is on equipment, where). None reports live battery state or presence. Utilities say plainly that registration does not guarantee power or priority. That is the gap.
3. **Registries badly undercount.** Texas has ~237,692 Medicare beneficiaries on electricity-dependent equipment ([KHOU, June 2023 emPOWER data](https://www.khou.com/article/news/investigations/texans-power-outage-map/285-437f1ff7-5cd1-4407-b5a5-6845803cacdc)) versus 10,530 utility critical-care registrations in competitive-retail areas cited in 2022 ([KUT](https://www.kut.org/health/2022-01-13/medically-vulnerable-texans-tell-the-state-to-keep-their-power-on-in-the-next-emergency)). Not apples to apples (partial geography), but the order-of-magnitude gap is the pitch line.
4. **Ventilator and suction are the only true "minutes" devices.** Concentrators are fast if there is no tank. CPAP for sleep apnea is not an emergency for a night or two. Insulin is days unless the house is hot.

## 2. Time-to-harm table (use this to seed the ranking)

"Battery" = typical backup before the device stops. "Reserve after stop" = how long until the patient is at risk once the device is off. Ranking clock ≈ battery remaining + reserve, shortened by indoor temperature extremes.

| Device class | Typical draw | Typical backup | Reserve after device stops | Severity | Tier | Confidence / source |
|---|---|---|---|---|---|---|
| Home ventilator, invasive / 24h dependent (trach) | Low tens of W (Estimate) | ResMed Astral internal ~8 h; up to 24 h with two external packs. Older Trilogy ~3 h internal + 3 h external | **Minutes** (apnea, hypoxia) | Death | 1 | Vendor: [ResMed Astral vs Trilogy](https://ap.resmed.com/knowledge/what-is-the-difference-between-astral-and-trilogy-for-battery-support-internal-and-external), [Astral external battery](https://resmed.com.au/healthcare-professionals/products/accessories/astral-external-battery). Internal battery degrades; replace every 2 years |
| Suction machine (trach, secretions) | Low (Estimate) | 30 to 60 min continuous on internal battery; vendors claim up to 1 to 2 h | **Minutes** once airway obstructs; need is intermittent | Death | 1 | Hospital family guides: [AboutKidsHealth](https://www.aboutkidshealth.ca/suction-machines-and-manual-suction); Vendor: [SSCOR](https://blog.sscor.com/whats-the-runtime-of-most-rechargeable-batteries-of-portable-suction-units). Manual suction kit is the standard fallback |
| Stationary oxygen concentrator, no tank | 290 to 350 W at 5 L/min (Drive 525KS ~312 W at 5 L/min; Philips EverFlo 350 W) | **None** (stops instantly) | Minutes to hours, depends on baseline lung function and flow | Death possible | 1 to 2 | Vendor specs: [Drive 525KS](https://au.healthcare.airliquide.com/sites/alh_au/files/2026-03/drive_oxygen_concentrator_5l_525ks_spec_sheet.pdf), [Philips EverFlo](https://www.philips.com.au/healthcare/product/HC0044000/everflo-home-oxygen-system/specifications) |
| Concentrator with tank backup | n/a (compressed gas) | E cylinder (~680 L) ≈ 5.5 h at 2 L/min, ≈ 2.3 h at 5 L/min | Same as above once tank is empty | Death possible | 2 | Estimate: litres ÷ flow. Tank size and fill level must be user-entered |
| Portable oxygen concentrator (POC) | Battery only | 4 to 8 h at setting 1 to 2 (e.g., Inogen G3 ~4.5 h at setting 2; CAIRE FreeStyle Comfort 8 h / 4 h at setting 1 / 2). Many are pulse-only, max ~1 L/min continuous equivalent | Same as concentrator | Death possible | 2 | Vendor: [Inogen](https://www.inogen.com/resources/oxygen-concentrators/how-long-do-oxygen-concentrators-last), [Vitality CAIRE listing](https://www.vitalitymedical.com/caire-freestyle-comfort-portable-oxygen-concentrator-as200-xxx.html) |
| BiPAP for respiratory failure (ALS, neuromuscular, COPD hypercapnia) | ~30 to 90 W (Estimate) | Usually none unless a battery pack was bought | Hours; worst during sleep. No published safe duration | Severe | 2 | [American Thoracic Society](https://site.thoracic.org/patient-resources/emergency-or-disaster-preparedness), [Sonoma County EM](https://socoemergency.org/ufaq/information-for-cpap-and-bipap-users) (respiratory failure users "may need a generator") |
| CPAP for obstructive sleep apnea | ~30 to 60 W (Estimate) | Usually none | **A night or two** is generally tolerable | Low | 4 | Clinician quote in [NPR/WHYY 2024](https://whyy.org/articles/medical-devices-power-outages-preparation); [Sonoma County EM](https://socoemergency.org/ufaq/information-for-cpap-and-bipap-users) |
| Home hemodialysis | Machine + water treatment | ~30 min battery, only enough to end the run safely | **Days** (missed sessions: fluid overload, high potassium). Uri deaths included dialysis disruption | Severe | 3 | [Kidney Care UK](https://kidneycareuk.org/kidney-disease-information/treatments/haemodialysis-hd/managing-home-dialysis-during-a-power-cut-or-energy-blackout/), [NKF](https://www.kidney.org/kidney-topics/planning-emergencies-guide-people-kidney-disease), [DSHS](https://www.dshs.texas.gov/sites/default/files/news/updates/SMOC_FebWinterStorm_MortalitySurvReport_12-30-21.pdf) |
| Infusion pump (TPN, inotropes, pain) | Battery | Ambulatory pumps run on batteries; hours to days | Drug-dependent: inotrope-dependent heart failure is fast; TPN is slow | Variable | 2 to 3 | **Unverified**: no source pulled. Treat as user-entered "drug criticality" field |
| Insulin refrigerator | Fridge ~100 to 200 W (Estimate) | n/a | **Days to weeks**: most insulins are labelled ~28 days unrefrigerated (some 31 to 56) below ~86°F. Hot house (Beryl) shortens this; frozen insulin is discarded | Moderate | 4 (rises if indoor >86°F) | [Wisconsin DHS label table](https://dhs.wisconsin.gov/publications/p01904.pdf), [Mount Sinai emergency guidelines](https://www.mountsinai.org/files/MSHealth/Assets/HS/Care/Diabetes/Treatment%20Care/Emergency-Guidelines.pdf). FDA emergency insulin storage page is the primary to cite in the pitch (not pulled this pass) |
| Power wheelchair / powered mattress / lift | Battery | ~1 day on chair battery (Estimate) | Not direct harm; person **cannot self-evacuate** from heat, cold, flood or CO | Moderate, multiplier | 3 | Estimate. Treat as a mobility flag that raises any other risk |

**Environment clocks (apply to everyone, biggest real killer):**

| Factor | Why | Source |
|---|---|---|
| Indoor cold | 158/246 Uri deaths were hypothermia; 67.7% of those were 60+ | [DSHS](https://www.dshs.texas.gov/sites/default/files/news/updates/SMOC_FebWinterStorm_MortalitySurvReport_12-30-21.pdf) |
| Indoor heat | Half of Harris County Beryl deaths heat related; ~3 M Texans lost power, some > 1 week | [ABC13/AP](https://abc13.com/post/hurricane-beryl-related-deaths-texas-rise-36/15096054/) |
| Carbon monoxide | 19 Uri deaths from generators, grills, cars; Beryl: 2 deaths and ~400 hospitalized for CO | [DSHS](https://www.dshs.texas.gov/sites/default/files/news/updates/SMOC_FebWinterStorm_MortalitySurvReport_12-30-21.pdf); [RTO Insider tag page](https://www.rtoinsider.com/tag/hurricane-beryl) (secondary) |

**Build implication (Estimate):** a $3 CO sensor and a temperature sensor on the ESP32 cover more real deaths than the battery reading does. Pitch "time until harm" as min(device clock, temperature clock, CO alarm).

## 3. Real disasters with numbers

| Event | Numbers | Device-relevant detail | Source |
|---|---|---|---|
| Winter Storm Uri, TX, Feb 2021 | 246 official deaths, 77 counties; 148 direct, 92 indirect, 6 possible. BuzzFeed analysis estimated 700+ | 25 deaths from exacerbated illness incl. dialysis/oxygen disruption, frozen devices and meds, loss of power to life-sustaining equipment. No separate oxygen count published | [DSHS report](https://www.dshs.texas.gov/sites/default/files/news/updates/SMOC_FebWinterStorm_MortalitySurvReport_12-30-21.pdf); [KERA](https://www.keranews.org/texas-news/2022-01-03/texas-puts-final-estimate-of-winter-storm-death-toll-at-246) |
| Uri, individual cases | 75-year-old Crosby veteran died after power loss stopped his oxygen; COVID-recovering Texans on home oxygen lost power | Officials said home oxygen use was at an "all-time high" | [KERA, Mar 2021](https://www.keranews.org/news/2021-03-10/texans-recovering-from-covid-19-relied-on-machines-to-help-them-breathe-then-the-power-went-out) |
| Uri, survey | Disability Rights Texas: ~2/3 of respondents lost power > 24 h | Could not charge DME batteries | [DRTX survey PDF](https://development.disabilityrightstx.org/wp-content/uploads/2021/04/apr-5-2021-DRTX-winter-survey-report-FINAL.pdf) |
| Hurricane Beryl, Houston, Jul 2024 | ≥36 Texas deaths by Jul 25; half of Harris County deaths heat related; ~3 M without power | Galveston County woman on oxygen counted as a Beryl death after losing power | [ABC13/AP](https://abc13.com/post/hurricane-beryl-related-deaths-texas-rise-36/15096054/) |
| Beryl, utility | PUCT review: CenterPoint mobile generation deployment inefficient; communication was the top customer problem; CenterPoint does not use Medicare data to locate DME users | | [Houston Chronicle](https://preview-prod.w.houstonchronicle.com/news/investigations/article/centerpoint-hurricane-beryl-reforms-takeaways-20390428.php); [KHOU](https://khou.com/article/news/investigations/medical-devices-power-outage-data/285-275759d6-4422-4701-87fd-7c24e2481bf9) |
| Hurricane Maria, PR, 2017 | 4,645 excess deaths (95% CI 793 to 8,498) vs official 64; ~1/3 from interrupted medical care; homes averaged 84 days without power | Need for electrically powered respiratory equipment was among the top reported access problems | [Kishore et al., NEJM 2018](https://dash.harvard.edu/bitstream/1/37309252/1/nejmsa1803972.pdf) |
| PG&E PSPS, CA, Oct 2019 | 67-year-old oxygen-dependent Pollock Pines man reported dead ~12 min after shutoff | **Causation unconfirmed** by PG&E or officials; use carefully | [GV Wire/AP](https://gvwire.com/2019/10/11/california-power-outages-ease-first-linked-death-reported) |
| Helene + Milton, 2024 | >250 deaths combined; ~4.5 M customers out | ≥540,000 people in FL, GA, SC, TN, NC use electricity-powered home equipment (AP Medicare analysis). Oxygen-device deaths only in secondary tallies | [Direct Relief](https://www.directrelief.org/2025/08/lights-out-intro-the-scope-and-impact-of-storm-driven-power-loss-on-safety-net-clinics/); [PAHO sitrep](https://paho.org/sites/default/files/2024-09/hurricane-helene-sitrep-1-updated-930_0.pdf); [GWU](https://mediarelations.gwu.edu/node/12916) |
| 2003 NE blackout, NYC | Respiratory device failure (vents, nebulizers, O2) drove 65 ED visits, 37 admissions at one hospital, vs zero before and after | Classic evidence that outages convert DME users into ED surge | [PubMed 15640685](https://pubmed.ncbi.nlm.nih.gov/15640685/) |
| US outage exposure | ~17,500 outages ≥ 8 h in 2018 to 2020; longer outages hit poorer counties; ≥ 2.9 M Medicare DME users | 8 h chosen because most DME batteries last only a few hours | Casey et al., Nature Communications, via [PopSci](https://www.popsci.com/environment/power-outages-weather-climate-health/) |

## 4. Existing systems and their gaps

| System | What data | Who sees it | Cadence | What it does in an outage | Gap Lifeline fills |
|---|---|---|---|---|---|
| **HHS emPOWER Map** | De-identified counts of Medicare FFS + Medicare Advantage beneficiaries with claims for electricity-dependent DME, to ZIP level. 4.6 M+ at-risk beneficiaries, 3 M+ with DME claims | Public | Monthly | Situational awareness, restoration prioritization by area | Aggregate only; no person, no live status; misses non-Medicare (kids, Medicaid-only, private) ([about](https://empowerprogram.hhs.gov/about.html), [map](https://empowerprogram.hhs.gov/empowermap)) |
| **emPOWER Emergency Planning Dataset** | Restricted, more granular beneficiary-level data for planning and response | State, territorial and certain metro public health authorities; partners as appropriate | Monthly | Outreach, shelters, evacuation, restoration priority | Still a list, not a live clock; one month stale ([ASPR TRACIE](https://asprtracie.hhs.gov/technical-resources/resource/13313/hhs-empower-emncy-planning-dataset)) |
| **Texas STEAR** | Voluntary self-registration: medical, mobility, communication needs | Local emergency planners and responders | Must re-register every year; no confirmation sent | Planning; may inform checks | "Does not guarantee assistance"; services vary by community ([TDEM](https://tdem.texas.gov/stear), [Jan 2025 upgrade, 211 registration](https://tdem.texas.gov/press-release/1-16-25)) |
| **Texas critical care / chronic condition designation** (Oncor, CenterPoint etc., PUCT rule) | Physician-certified form | Utility | Renewal required | Outage notifications; "may" prioritize restoration | PUCT rule: designation "does not guarantee the uninterrupted supply of electricity." Oncor said it was not possible to prioritize these customers in Uri ([ERCOT TDSP FAQ](https://www.ercot.com/files/docs/2022/06/14/TDSP%20EOP%20Q&A%202021.docx), [PUC form](https://www.ercot.com/files/docs/2024/01/17/PUC-Critical-Care-Form.pdf), [NBC DFW](https://www.nbcdfw.com/news/nbc-5-responds/is-there-a-way-to-prioritize-medically-fragile-texans-in-a-power-disaster/2590136/)) |
| **PG&E Medical Baseline (CA)** | Enrolled medical customers | Utility | Ongoing | Before planned shutoffs: calls, texts, then **door knocks** if no "positive contact." 2020: notified 10,218 of 10,383 in scope | Works only for *planned* outages; no live status; scaled back door knocks later ([PG&E PSPS report Oct 2019](https://webproda.cpuc.ca.gov/-/media/cpuc-website/divisions/safety-and-enforcement-division/reports/psps-post-event-reports/2019-and-earlier/pge-public-safety-power-shutoff-oct-2325-2019-report.pdf), [PG&E Sept 2020 letter](https://PGe.com/assets/pge/docs/outages-and-safety/safety/PSPS-Report-Letter-09.07.20.pdf)) |
| **Austin Energy Medically Vulnerable Registry** | Certified customers | Utility, city | Ongoing | Outreach | Audit: ~70% of applications denied in 2022 to 2023 ([City Auditor, Mar 2024](https://austintexas.gov/sites/default/files/files/Auditor/Audit_Reports/Austin_Energy_Medically_Vulnerable_Registry_March_2024.pdf)) |
| **AES Indiana Medical Alert** (typical utility program) | Enrolled customers | Utility | Ongoing | Advance notice of planned outages | "Cannot contact Medical Alert customers and cannot guarantee how quickly power will be restored during unplanned outages" ([AES Indiana](https://www.aesindiana.com/es/node/15341)) |
| **211 / Smart911** | Self-entered profile | 911 call-takers (Smart911) | Whenever user updates | Shown when the person calls | Passive: helps only if the person can call. (Smart911 not researched in depth this pass) |
| **Commercial** | UPS units with phone-dial outage alerts; power stations (Anker, Bluetti) marketed for medical use | Owner | n/a | Alert that mains failed | No device-battery-per-person estimate, no triage, no presence ([Labrepco UPS](https://www.labrepco.com/product/custom-ups-battery-backup-systems/)) |

**Prior art check (shallow, 1 pass):** no product, Devpost project or paper found that estimates per-person device battery runtime and triages a population live. Closest: Elevance Solutions Lab 2026 to 2027 challenge to "identify, prioritize, and support electricity-dependent members before, during, and after power outages" ([UVA](https://environment.virginia.edu/elevance-solutions-lab-challenge)) and Casey et al.'s county-level risk mapping. See HackUTD-Research-Lifeline-Competitors for a deeper competitor sweep. Say "we found no system that..." not "first ever."

## 5. What responders need (design recommendation, partly Estimate)

Sources say emPOWER is used for welfare checks, shelter and evacuation planning and restoration priority ([ASPR TRACIE DME in disasters](https://files.asprtracie.hhs.gov/documents/aspr-tracie-durable-medical-equipment-in-disasters.pdf)). Published welfare-check protocols were not found this pass; the field list below is our synthesis from STEAR intake categories and the utility programs above.

| Field | Why the responder needs it |
|---|---|
| Rank + time until harm (minutes) + which clock drives it (battery, cold, heat, CO) | Order of dispatch |
| Device class + backup (tank litres, POC battery %) | Bring the right thing: tank, battery, generator, or transport |
| Presence + motion (radar) + last motion time | "Home and moving" vs "home and still" vs "not home" (do not send a crew to an empty house) |
| Indoor temperature, CO | Hazard to patient and to crew |
| Contact attempts: last call time, answered or not | Avoid duplicate calls, escalate non-responders |
| Address, access notes (gate code, floor, key), mobility | Cuts on-scene time |
| Caregiver / DME supplier phone, language | Someone else may already be handling it |
| Consent timestamp | Legal basis to share |

**How they would consume it:** a single sorted list plus map, exportable as CSV, with a one-line "action" per row (deliver O2 tank, transport to shelter, welfare check). County OEM runs welfare checks; utilities want ZIP or feeder rollups for restoration priority (emPOWER is already used this way). Keep the agent's role as *recommend and explain the rank*, human dispatches.

## 6. Ethics, privacy, legal wording

| Topic | Finding | Wording to use |
|---|---|---|
| HIPAA | HIPAA applies to covered entities (providers, plans, clearinghouses) and their business associates. A consumer-installed node is not a covered entity. Health apps and connected devices outside HIPAA fall under the **FTC Health Breach Notification Rule**, expanded in 2024 (effective Jul 29, 2024) | "Not a HIPAA covered entity today; built toward HIPAA-grade controls (encryption, consent, minimum necessary) and compliant with the FTC Health Breach Notification Rule." Sources: [Federal Register 2024](https://www.federalregister.gov/documents/2024/05/30/2024-10855/health-breach-notification-rule), [Morrison Foerster](https://www.mofo.com/resources/insights/240514-ftc-issues-final-rule-to-expand) |
| Consent | STEAR model: registration = consent to share with responders during a disaster ([TDEM](https://tdem.texas.gov/stear)) | Explicit opt-in naming who sees what; revocable; share only during a declared outage |
| Not a medical device | Do not claim to diagnose or to keep anyone alive | "Decision support for responders. Does not replace your device alarms, your backup plan, or 911." Mirror the utilities' "does not guarantee" language |
| Radar privacy | mmWave gives presence and motion without cameras | "No camera, no audio. Presence and motion only." |
| False alarms | Radar can miss a still sleeper or flag a pet; battery estimate drifts with age (ResMed: internal batteries degrade, replace every 2 years) | Show confidence, require call attempt before escalation, show "last verified" time |
| Equity | Registries miss most people (Texas: ~237 K Medicare DME users vs ~10.5 K critical-care registrations in competitive areas); Austin denied ~70% of applications; longer outages hit poorer counties; emPOWER excludes non-Medicare | Pitch: "the people not on any list." Mention low-cost node, 211 enrollment path, Spanish support, LoRa for areas where cell fails |

## Open questions (not researched)
- Exact FDA insulin storage wording (pull fda.gov page before pitch).
- Smart911 coverage in Dallas County.
- Real CPAP / BiPAP / ventilator wattages for the demo label (check device labels).
- Infusion pump battery norms by pump type.
