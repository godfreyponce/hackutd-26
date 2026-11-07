---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, plan]
---

# HackUTD 2026: 24-Hour Plan

Part of [HackUTD-2026](HackUTD-2026.md).

## Principles
- **One sharp problem with a working demo** beats a pile of parts. Use our gear first and buy whatever the wow needs.
- **Sponsor tracks decide the idea.** Lock it within 30 minutes of the reveal. Pick a build that qualifies for 2 tracks at once.
- **Measure the win on screen.** Judges remember numbers they watched change live.

## Timeline
| Clock | Phase | Done when |
|---|---|---|
| 12:00–2:00 PM | **Idea lock** | Tracks read, 3 ideas scored (prize fit / demo wow / risk), one-page spec |
| 2:00–4:00 | **Plan + de-risk** | Parts list, wiring diagram, issues, prints started; benchmark the models on the Pi 5 |
| 4:00 PM–12:00 AM | **Build the core** | Each stage works on its own (motion, vision, voice, LLM) |
| 11:00 PM | **Devpost v1** | Required first submission |
| 12:00–6:00 AM | **Integrate** | The whole demo runs once. **No new features after 6 AM** |
| 6:00–9:00 AM | **Harden** | 5 rehearsals, backup video recorded |
| 9:00 AM–12:00 PM | **Present** | Devpost final, slides, 2-minute video, pitch practice |
| 1:00–4:00 PM | **Judging** | Table demo |

## Roles
- **Rafael:** hardware, wiring, steppers, board bring-up, power, mechanical/3D prints.
- **Godfrey:** software, AI pipeline, UI/overlay, pitch materials.
- **Claude:** parallel sessions, one per issue, each on its own branch. A separate session drafts the Devpost and pitch.

## Repo
- Godfrey's GitHub repo (get the invite). The HackEdge protocol carries over: `STATE.md` holds `next_action`, and each ticket gets a plan session then a build session.
- Proposed layout: `00-ideas/ 01-plan/ 02-hardware/ 03-software/ 04-demo/ STATE.md CLAUDE.md README.md`.
- Research lives in the vault (this folder); copy the relevant parts into the repo.

## Claude plan
- Godfrey: Max 20x. Rafael: Pro annual. Recommendation: **upgrade for this month** if he drives Claude Code himself. Check how upgrading partway through an annual plan is billed.
