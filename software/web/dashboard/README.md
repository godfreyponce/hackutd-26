# 500-home dashboard (#16)

The same quake that hits the real box hits 500 simulated homes around Richardson, TX. A red wave runs across the map, and each white dot turns red when the wave reaches it. After the wave, simulated homes check in. Every hit home is ranked by time to harm, in minutes. Lower is more urgent.

## Run

The hub (#19) serves this page at `/dashboard/`. With the hub running, open:

```
http://localhost:8080/dashboard/
```

To use another hub, add `?hub=ws://host:port`. The default is `ws://localhost:8765`. The page reconnects every second if the hub restarts. It loads nothing from the internet.

Keys on the page:
- `q`: start the wave on this page only. Nothing is sent to the bus.
- `r`: reset this page only.
- `v`: step the map through world, city and home by hand.

The main trigger is a `quake` message on the bus. Quakes that come in while a wave is already running are ignored until `reset`.

## Map

The map has three stages:
1. World: before a quake, a dark globe turns slowly. A marker sits on Richardson, TX.
2. City: on a quake, a red pulse shows at north Texas, the globe turns to face it, and the camera flies down to the Richardson street map. Then the wave plays: red spreads over the streets like a stain, and each white dot turns red as it passes.
3. Home: when H000 raises an alarm or says help, the camera zooms to its block with a callout. On `clear` it goes back to the city.

After an alarm the agent sends a `handoff`. The callout then shows the hand-off note, who to contact first, and the why for the alarm. Each part says who wrote it: "Written by Nemotron", or "Template" when the agent fell back.

With `prefers-reduced-motion`, the map cuts between stages and shows no stain.

## Tests

```
cd software/web/dashboard && node --test
```

Node 24, no dependencies.

## Files

| File | What it does |
|---|---|
| `rank.js` | Time-to-harm math and the rerank guardrail. Pure, no DOM. |
| `homes.js` | Seeded generator: the same 500 homes every run. `H000` is the real box. |
| `sim.js` | Simulated check-ins: calls go out in rank order, and the coverage rule forces a recheck on any hit home with no contact attempt. |
| `box.js` | The real box `H000`, driven by `presence`, `checkin`, `heard` and the other sensor events. |
| `bus.js` | WebSocket client with reconnect. |
| `camera.js` | Map stage (world, city, home) and the eased flight between stages. Pure, no DOM. |
| `basemap.js` | Draws the globe and the street map from `data/`. |
| `app.js` | Map drawing, counters, queue and trace panel. |
| `data/world.json` | Natural Earth 50m land and borders, plus US state lines and Texas. Public domain. |
| `data/richardson.json` | OpenStreetMap roads, rail, water and parks around Richardson. © OpenStreetMap contributors, ODbL. |
| `data/build.mjs` | Downloads and simplifies both data files. Run once at build time: `node data/build.mjs`. |
| `vendor/` | d3-geo 3.1.1 and d3-array 3.2.4 (ISC), loaded as plain scripts. |

## Ranking

From `docs/lifeline/HackUTD-Lifeline-Agent.md`, section 3:

`harm_min = min(device battery min x device weight, cold clock) x presence x response x stale`

- Device weight: O2 x1, dialysis, CPAP and insulin fridge x1.5, wheelchair x3.
- Cold clock: 720 min (240 if vulnerable) at 64 F or warmer (the WHO 18 C minimum). Below that it shrinks in a straight line to 0 at 32 F. The doc leaves this curve open. This is our pick.
- Presence: still x0.5, nobody home x2.
- Response: said help or alarm = 0, one missed call x0.75, two or more x0.5, answered okay x1.5.
- Stale (no sensor message for 5 min): x0.75.

Every queue row shows each of these factors.

## Bus

- Listens to `quake`, `presence`, `fall_hint`, `help_gesture`, `power`, `heartbeat`, `checkin`, `heard`, `agent`, `handoff`, `rerank`, `alert` and `reset`. A `help_gesture` adds "Help sign seen at the box." to the event line until reset.
- Sends `queue` with the top 20 when the order changes, at most once every 2 s.
- Guardrail on `rerank`: a move goes through only if it is at most 3 places and names a factor. A move can never demote a home under 30 min or a home that said help, or push one down. `by` < 0 moves a home up. A blocked move shows on screen with its reason.
