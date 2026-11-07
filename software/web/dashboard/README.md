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

The main trigger is a `quake` message on the bus. Quakes that come in while a wave is already running are ignored until `reset`.

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
| `app.js` | Canvas map, counters, queue and trace panel. |

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

- Listens to `quake`, `presence`, `fall_hint`, `power`, `heartbeat`, `checkin`, `heard`, `agent`, `rerank`, `alert` and `reset`.
- Sends `queue` with the top 20 when the order changes, at most once every 2 s.
- Guardrail on `rerank`: a move goes through only if it is at most 3 places and names a factor. A move can never demote a home under 30 min or a home that said help, or push one down. `by` < 0 moves a home up. A blocked move shows on screen with its reason.
