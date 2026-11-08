# Hub: event bus and box simulator (#19)

Every software piece talks only to this hub. The agent (#15), voice (#14), dashboard (#16) and home screen (#20) connect to one WebSocket bus. Box events come from the keyboard simulator today and from the ESP32 over USB serial later. Moving from the simulator to the real box changes one flag.

## Run

From the repo root, with Python 3.12:

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r software/hub/requirements.txt
```

```bash
.venv/bin/python -m software.hub --sim
```

```bash
.venv/bin/python -m software.hub --serial /dev/tty.usbserial-XXXX
```

Flags:

- `--sim`: the Mac pretends to be the box. Keys below.
- `--serial PORT`: read JSON lines from the ESP32 at 115200 baud.
- `--ws-port` (default 8765): the bus, `ws://localhost:8765`.
- `--http-port` (default 8080): static files from `software/web/`, `http://localhost:8080/`.
- `--host` (default `localhost`): bind address. Use `0.0.0.0` to reach the hub from another device on the network.

Each parallel thread uses its own ports so hubs don't collide, for example `--ws-port 8767`.

## The bus

- One JSON object per WebSocket message.
- The hub re-broadcasts everything a client sends to **all** clients, the sender included. Ignore your own messages, for example by their `type`.
- The hub adds `"t"` (ms since the Unix epoch) if the message has none. A message that already has `t` keeps it. The ESP32 sends `t` as ms since boot.
- The hub drops non-JSON and non-object messages (arrays, strings, numbers) with a log line. It never crashes on them.
- Python clients read `HUB_URL` (default `ws://localhost:8765`).
- Web pages read `?hub=ws://host:port` (default `ws://localhost:8765`). The index page at `/` passes `?hub=` through to `/dashboard/` and `/home/`.

## Messages (the contract)

This list copies #19 and its "Contract addendum v1". The issue wins on any doubt. Change the contract on #19 first, never in a branch.

**Sensor events.** Sent by the ESP32 or the simulator.

```json
{"type":"quake","peak_g":0.82}
{"type":"presence","state":"moving|still|none"}
{"type":"fall_hint"}
{"type":"power","state":"mains|battery"}
{"type":"heartbeat","battery_pct":87}
```

`fall_hint` means presence went from moving to still. It is a hint, not a diagnosis. Say "no response after an event".

**Camera events.** Meant for the camera on the Pi (`hardware/vision/posture.py`, #46). The camera part is on the pi-integration branch, not on main yet. On main, the simulator key `h` sends `help_gesture`.

```json
{"type":"help_gesture","source":"camera"}
```

`help_gesture` means the camera saw the HELP sign. The agent asks at once; the alarm rule decides. On the pi-integration branch, the camera sends it again while the sign is held, after a cooldown.

**Check-in.** The agent (#15) sends `checkin` and `say`. The voice service (#14) sends `heard`.

```json
{"type":"checkin","state":"asking|ok|help|no_answer|alarm|clear","try":1}
{"type":"say","script_id":"fall_q1","text":"...","listen_s":6}
{"type":"heard","answer":"ok|help|no_answer","transcript":"..."}
```

`listen_s` is optional. With it, the voice service speaks the text, listens that many seconds, then sends one `heard`. Without it, the voice service only speaks.

`tone` is optional (#64). The agent sets `"tone":"warning"` only on the first `say` of an EQW alert check-in. The voice service plays a short warning tone, then speaks the text. A voice service without this field ignores it and still speaks the line.

**Agent trace.** Sent by the agent.

```json
{"type":"agent","step":"PLAN|ACT|VERIFY|FALLBACK","text":"...","tool":"get_presence"}
```

**Hand-off.** Sent by the agent once, after an alarm.

```json
{"type":"handoff","home":"H000","note":"...","contact":{"id":"godfrey","name":"Godfrey","role":"family contact, demo"},"by":"nemotron|template","why":["..."],"why_by":"nemotron|template"}
```

`note` is a short note for responders. `contact` is who to contact first, from a fixed demo list. `why` is at most 3 lines on why the rule raised the alarm. `by` and `why_by` say who wrote each: Nemotron, or the code template when the check failed or the model was down.

**Official alerts.** CAP-shaped, with the SAME fields from #35.

```json
{"type":"alert","source":"noaa|nws|usgs|gdacs|sensor","event":"Earthquake","severity":"Severe","urgency":"Immediate","certainty":"Observed","area":"Richardson, TX","headline":"...","code":"EQW","station":"HACKDEMO","distance_mi":3,"demo":true,"level":"emergency"}
```

- `code`: SAME event code, for example `EQW`, `TOR`, `SVR`, `RWT`. Optional for old senders.
- `station`: sender id, for example `HACKDEMO` for our demo file, `KEC56` or `KFWD/NWS` for real ones. Optional.
- `distance_mi`: miles from the home to the event. Optional.
- `demo`: `true` for our locally made demo alerts and the simulator. The headline stays plain. Screens and speech add "DEMO, not a real alert." when `demo` is true.
- `level`: `info|watch|warning|emergency`. The hub adds it before the broadcast (`alert_level.py`) and overwrites any value a sender set. Senders do not set it.

| Code | Level |
|---|---|
| Tests: `RWT`, `RMT`, `NPT`, `DMO` | info |
| Watches: code ends in `A` | watch |
| Other warnings: code ends in `W`, and `SVR` | warning |
| `EQW`, `TOR`, `CEM`, `CAE`, `EVI`, `SPW` | emergency |
| Missing or other code | CAP severity: `Extreme` emergency, `Severe` warning, `Moderate` watch, else info |

`distance_mi` over 25 drops the level one step, never below info.

**Reset.** Every piece goes back to its start state. The simulator resets too, whoever sends it.

```json
{"type":"reset"}
```

**Ranking.** The real box is home `H000`. After a quake the dashboard (#16) sends its top 20:

```json
{"type":"queue","homes":[{"id":"H042","harm_min":38,"factors":{"battery_min":38,"indoor_f":51,"unresponsive":true,"still":false,"stale":false,"said_help":false}}]}
```

The agent may reply:

```json
{"type":"rerank","moves":[{"id":"H042","by":-2,"factor":"battery_min"}],"reason":"..."}
```

The dashboard enforces the guardrail. A move goes at most 3 places and names a factor. It never demotes a home under 30 min or one that said help. The dashboard drops a bad move and shows why.

**Who owns what.**

- Agent (#15): the alarm rule, the 3 tries, the stand-up re-ask, the script text by id. Sends `checkin`, `say`, `agent`, `handoff`. It does not send `rerank` yet: `build_agent` passes no ranker.
- Voice (#14): speaks, listens, classifies the answer. Sends `heard`.
- Home screen (#20): only listens.
- Dashboard (#16): listens and sends `queue`.
- Hub (#19): sends sensor events and `heartbeat` in `--sim` mode. Forwards ESP32 lines in `--serial` mode.

**Alarm rule.** Code, never the LLM.

| Someone detected? | Answer | Result |
|---|---|---|
| No | No answer | No alarm |
| Yes | No answer | Alarm |
| Either | "Help" | Alarm |
| Either | "I'm okay" | Log it, no alarm |

The alarm is fake. Nothing calls or texts 911 or any emergency number.

## Simulator keys (`--sim`)

| Key | Sends |
|---|---|
| `q` | `quake` with `peak_g` 0.82 |
| `m` | `presence` moving |
| `s` | `presence` still, then `fall_hint` if the last presence was moving |
| `n` | `presence` none |
| `p` | `power`, toggles mains and battery |
| `a` | a fake USGS earthquake `alert`: code `EQW`, station `HACKDEMO`, 3 miles away, `demo` true, so level emergency |
| `h` | `help_gesture` from the camera, as if it saw the HELP sign |
| `r` | `reset` |
| Ctrl-C | quit |

The simulator prints each event it sends. It sends a `heartbeat` every 5 seconds. Battery starts at 100% and drops 1% per heartbeat while power is on battery. A reset puts it back to 100% on mains with nobody present.

Without a terminal on stdin (run from a script or in the background), the keyboard is off and only the heartbeat runs. Use `send` to inject events.

## Helpers

Print every bus message, one JSON object per line:

```bash
HUB_URL=ws://localhost:8765 .venv/bin/python -m software.hub.tap
```

Send one message:

```bash
HUB_URL=ws://localhost:8765 .venv/bin/python -m software.hub.send '{"type":"presence","state":"moving"}'
```

`send` exits with code 2 and sends nothing if the argument is not a JSON object.

## Serial mode

The ESP32 sends one JSON object per line at 115200 baud (format in #13). The hub skips bad lines with a log line and forwards good ones to the bus. Opening the port flushes its input buffer, so lines sent before the hub starts are lost.

## Tests

```bash
.venv/bin/python -m pytest software/hub
```

The tests cover the key mapping, message parsing, the alert level table, re-broadcast between two clients, static serving, and serial over a fake pty (`os.openpty`).
