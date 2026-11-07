---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, lifeline, agent]
---
Part of [HackUTD-2026](../HackUTD-2026.md) · idea [HackUTD-Idea-Shortlist](../HackUTD-Idea-Shortlist.md) #1.

Agent and software stack for **Lifeline Grid**, scoped to what Godfrey can build tonight. Researched 2026-11-07 with about 21 hours left. `[u]` = not verified; check it in the first hour. Related: [HackUTD-Research-Track-NVIDIA](../tracks/HackUTD-Research-Track-NVIDIA.md), [HackUTD-Research-Judge-UI](../research/HackUTD-Research-Judge-UI.md), [HackUTD-Research-Pi-Stack-Offline](../research/HackUTD-Research-Pi-Stack-Offline.md).

## Decisions at a glance
| Question | Recommendation |
|---|---|
| Planner LLM | `nvidia/nemotron-3-nano-30b-a3b` on the NVIDIA API catalog, tool calling, thinking ON |
| Classifier / summarizer | Same model with thinking OFF (fast). Fallback: `nvidia/nvidia-nemotron-nano-9b-v2` `[u]` |
| Guardrail | `nvidia/llama-3.1-nemotron-safety-guard-8b-v3` on outbound call/SMS text |
| Agent framework | Plain Python tool-calling loop (OpenAI SDK). NeMo Agent Toolkit only as a stretch wrapper |
| Ranking | Deterministic time-to-harm math decides. LLM may only reorder inside a band, with a cited reason |
| Calls | Twilio Voice outbound + `<Gather input="speech">`, Nemotron classifies the reply. Simulated call is the fallback |
| Backend | FastAPI + WebSocket + paho-mqtt. Sim and real nodes publish on the same MQTT topics |
| Frontend | Single page, Leaflet map + queue table + agent trace + transcripts |
| Data | Tiger Data (Timescale) hypertable for telemetry, plus a `decisions` audit table |

## 1. Nemotron access
**Endpoint:** `https://integrate.api.nvidia.com/v1` (OpenAI-compatible, `Authorization: Bearer nvapi-...`). Get the key at build.nvidia.com: open any model, click "Get API Key". Code calls use trial credits; the playground does not.

| Model id (hosted) | Role | Tool calling | Notes |
|---|---|---|---|
| `nvidia/nemotron-3-nano-30b-a3b` | **Planner** | Yes (trained on multi-step tool use) | MoE, 3B active, so fast. Reasoning on by default; turn off with `extra_body={"chat_template_kwargs":{"enable_thinking": False}}`. Tool-call sampling: temp 0.6, top_p 0.95. This exact id is used in NeMo Agent Toolkit's own NIM example. |
| `nvidia/nvidia-nemotron-nano-9b-v2` `[u]` | Backup planner / classifier | Yes `[u]` | What 2025 winner DataDriver used. `/think` or `/no_think` in the system prompt. |
| `nvidia/llama-3.3-nemotron-super-49b-v1.5` `[u]` | "Explain decision" writer if Nano feels weak | Yes `[u]` | Slower. Use for the 1-paragraph audit summary only. |
| `nvidia/llama-3.1-nemotron-safety-guard-8b-v3` | Guardrail | No (classifier) | Labels a prompt/response safe or unsafe across 23 categories. |
| `nvidia/nemotron-nano-12b-v2-vl` | Not needed | | Only if you add a photo-of-meter feature. |

- **Rate limit:** about **40 requests/min per account** (community-reported, no official increase). Both teammates should create a key. Design the loop to use few calls: one planner call per re-rank cycle, not one per home.
- **Latency:** not published. Smoke-test in hour 0 and write the number here. Expect a few seconds with thinking on `[u]`.
- **Tool-calling smoke test (do first):** send one request with `tools=[...]` and `tool_choice="auto"`. If the hosted endpoint returns text instead of `tool_calls`, switch to JSON mode: ask for `{"tool": ..., "args": ...}` and parse it. The loop below works either way.
- **Brev:** NVIDIA's GPU cloud with launchables. Only worth it if the hosted API rate-limits you during judging. Self-hosting a NIM tonight is a time sink. Skip unless credits are handed out at the booth.

## 2. Agent architecture
**Pick: a plain tool-calling loop.** It is about 150 lines, every step is yours to log, and nothing hides the trace. LangGraph adds a graph abstraction you do not need for one agent. NeMo Agent Toolkit (`pip install nvidia-nat`, YAML workflow, `nat run`) is NVIDIA-native and could earn a nod from judges, but it is a new tool at 2 AM. If the core works by hour 14, wrap the same tool functions as NAT functions and say "also runs under NeMo Agent Toolkit".

### Tool set
| Tool | Args | Does | Side effect |
|---|---|---|---|
| `get_queue` | `limit` | Ranked homes with score breakdown | read |
| `get_home_telemetry` | `home_id` | Battery %, draw, minutes left, presence, last seen, power state | read |
| `get_home_profile` | `home_id` | Device class, vulnerability flags, contacts, consent level | read |
| `place_call` | `home_id`, `script_id` | Twilio or simulated call, returns `call_id` | external |
| `get_call_result` | `call_id` | `ok` / `needs_help` / `no_answer` + transcript | read |
| `send_sms` | `home_id`, `template_id` | SMS fallback | external |
| `escalate_to_responder` | `home_id`, `reason` | **Creates a dispatch request that a human must approve** | gated |
| `mark_status` | `home_id`, `status`, `reason` | Updates case state | write |
| `schedule_recheck` | `home_id`, `minutes` | Puts the home back in the plan at T+N | write |
| `broadcast_lora` | `group`, `msg_id` | Sends a canned message over Meshtastic when internet is down | external |
| `explain_decision` | `home_id` | Writes the audit reason (inputs, rule, action) | write |

Scripts and SMS are **templates by id**, not free text, so the LLM cannot invent what is said to a vulnerable person.

### Plan, act, verify loop
1. **Observe:** server computes the deterministic queue (section 3).
2. **Plan:** one Nemotron call gets the top 15 homes plus open cases and returns a numbered plan (for example "1. call H-0231, 2. recheck H-0107 in 10 min, 3. escalate H-0412").
3. **Act:** the loop executes tool calls one at a time, max 8 per cycle.
4. **Verify:** after each external action, call `get_call_result` or re-read telemetry. If the result contradicts the plan (call says ok but presence shows no motion for 2 h), the agent must revise and log why.
5. **Record:** `explain_decision` for every home whose status changed.
6. Repeat every cycle or on any event.

```python
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=KEY)
MODEL = "nvidia/nemotron-3-nano-30b-a3b"
def run_cycle(state):
    msgs = [{"role":"system","content":SYSTEM},
            {"role":"user","content":json.dumps(state)}]
    for step in range(8):
        r = client.chat.completions.create(model=MODEL, messages=msgs,
              tools=TOOLS, tool_choice="auto", temperature=0.6, top_p=0.95)
        m = r.choices[0].message
        trace("think", getattr(m, "reasoning_content", None) or m.content)
        if not m.tool_calls: break
        msgs.append(m)
        for tc in m.tool_calls:
            args = json.loads(tc.function.arguments)
            out = guard_and_run(tc.function.name, args)   # policy checks here
            trace("act", tc.function.name, args, out)
            msgs.append({"role":"tool","tool_call_id":tc.id,"content":json.dumps(out)})
```

### Agent trace panel (what judges must see)
A right-hand column that streams over WebSocket, newest at top, one card per step:

| Field | Example |
|---|---|
| Cycle + clock | `Cycle 14 · 02:41 sim time · re-rank trigger: feeder F3 down` |
| PLAN | Numbered plan from Nemotron, shown as a checklist that ticks off |
| THINK | Collapsed reasoning text (expand on click) |
| ACT | `place_call(H-0231, script=wellness_v1)` with tool icon |
| RESULT | `no_answer (2nd attempt)` in amber |
| VERIFY | `presence: no motion 47 min, battery 38 min left` |
| DECISION | `escalate_to_responder → awaiting human approval` with Approve button |
| WHY | One line: "O2 concentrator, 38 min battery, 2 missed calls, no motion" |
| Counters | Nemotron calls this hour, tool calls, homes contacted, homes unreached |

Also show an "LLM vs math" diff badge when the agent reorders the queue, so judges see the guard working.

## 3. Ranking: time to harm
Every home gets a **harm clock in minutes**. Lower = more urgent. All math, no LLM.

| Input | Rule |
|---|---|
| Battery minutes left | `battery_Wh_left / device_W * 60` (from measured current), for homes with a powered critical device |
| No critical device | Exposure clock by vulnerability: 240 min if elderly/medical flag in heat or cold, 720 otherwise `[u: pick and state]` |
| Device class weight | Life-sustaining (O2, ventilator) ×1.0 · important (CPAP, dialysis, insulin fridge) ×1.5 · comfort ×3.0 |
| Presence | Motion in last 15 min: no change. Person present but **no motion 30+ min**: clock ×0.5. No one home: clock ×2 |
| Call status | `needs_help`: clock = 0 (top). `no_answer` once ×0.75, twice ×0.5. `ok`: ×1.5 and recheck in 30 min |
| Stale data | Node silent > 5 min: flag "unknown", clock ×0.75 (silence during an outage is itself a signal) |

`harm_clock = base_minutes * device_weight * presence_factor * response_factor`. Sort ascending. Show every factor in the queue row so the number is auditable.

**LLM guardrails on ranking**
- The LLM can move a home **at most 3 places** and must cite a factor by name. Anything else is rejected by `guard_and_run` and logged as "override blocked".
- Hard floor: any home with clock < 30 min or `needs_help` can never be demoted or skipped.
- Coverage rule (State Farm "no one overlooked"): every affected home gets a contact attempt within N minutes; the server, not the LLM, forces a `schedule_recheck` on anything untouched.
- If the LLM response fails to parse or times out, the cycle runs on pure math and the trace says so.

**Re-rank cadence:** recompute math every 10 s (cheap). Call the planner on events (power loss, call result, a home crossing 60/30/15 min) and at least every 60 s. That stays well under 40 RPM.

## 4. Calls
**Path A, Twilio Voice + Gather (recommended).** Godfrey knows Twilio and it is the least moving parts.
1. Sign up at twilio.com, get a trial number with Voice.
2. Verify both teammates' phones (Console → Phone Numbers → Verified Caller IDs). **Trial can only call verified numbers.**
3. Expose FastAPI with `cloudflared tunnel --url http://localhost:8000` or ngrok.
4. Outbound: `client.calls.create(to=..., from_=TWILIO_NUM, url=f"{PUBLIC}/twiml/{call_id}", status_callback=f"{PUBLIC}/status/{call_id}")`.
5. TwiML: `<Say>` the template, then `<Gather input="speech" speechTimeout="auto" action="/gather/{call_id}" actionOnEmptyResult="true">`.
6. `/gather` gets `SpeechResult`. Nemotron (thinking off) classifies into `ok / needs_help / unclear`. Empty result or status `no-answer` / `busy` = `no_answer`.

| Trial limit | Value |
|---|---|
| Recipients | Verified numbers only, from a verified or Twilio caller id |
| Voice quota | 75 minutes total, 10 min per call, 5 concurrent |
| Country | Domestic only |
| Trial notice | A trial message plays before your TwiML; pressing a key may be needed `[u]` |
| Paid cost after upgrade | about $0.014/min US outbound, number about $1.15/month `[u]` |

**Path B, ElevenLabs agent over Twilio.** `POST /v1/convai/twilio/outbound-call` with `agent_id`, `agent_phone_number_id`, `to_number`. Better voice, real conversation, but the LLM in that call is not Nemotron unless you point ElevenLabs at a custom LLM URL `[u]`. That weakens the NVIDIA story. Use only if Path A is done early.

**Path C, simulated call (always build it).** Same `place_call` interface; returns a scripted outcome after 4 s with a transcript card. The 500 sim homes all use this. Only 1 to 2 real numbers get real calls. Demo line: "the agent just called Rafael's phone live; the other 499 are simulated with the same code path."

## 5. Simulation and UI
**Synthetic homes (500).** Random points in a box around Richardson/UTD (lat 32.95 to 33.02, lon -96.80 to -96.70). Assign each to one of 8 feeders by grid cell. Outage spreads feeder by feeder every 2 to 3 sim minutes from one substation.

Device mix (demo weights; real prevalence is lower and should be said honestly) `[u]` numbers:
| Device | Demo share | Draw | Battery |
|---|---|---|---|
| Oxygen concentrator | 6% | 90 to 300 W | 1 to 4 h portable pack |
| CPAP | 15% | 30 to 60 W | 95 to 150 Wh pack |
| Powered wheelchair / lift | 4% | charge only | hours to days |
| Insulin fridge | 8% | 50 to 80 W | none (thermal clock) |
| Home dialysis | 1% | 300+ W | 30 to 60 min |
| None | 66% | | |

Plus vulnerability flags (age 75+, lives alone, heat risk) at about 20%, and a `consent` level per home. Run the sim at 10× to 30× speed with a slider.

**Real nodes.** Sim and ESP32 nodes publish the same topic: `lifeline/{home_id}/telemetry` JSON `{ts, power_ok, battery_pct, current_ma, presence, motion}`. Backend subscribes once; the map marks real nodes with a ring icon.

**Stack**
- Backend: FastAPI, `paho-mqtt` to the Pi 5 Mosquitto, asyncio sim task, one WebSocket `/ws` that pushes `queue`, `trace`, `call`, `home` events.
- Frontend: one HTML page (or Vite + React if Godfrey prefers). Leaflet with OSM tiles; cache tiles for the demo area beforehand or fall back to a plain dark canvas with dots if Wi-Fi dies. Panels: map (color by harm clock), queue table, agent trace, call transcripts, "Approve dispatch" box.

**Tiger Data (about 1 hour)**
```sql
CREATE TABLE telemetry(ts timestamptz NOT NULL, home_id text, power_ok bool,
  battery_pct real, current_ma real, presence bool, motion bool);
SELECT create_hypertable('telemetry', by_range('ts'));   -- older: create_hypertable('telemetry','ts')
CREATE MATERIALIZED VIEW drain_1m WITH (timescaledb.continuous) AS
  SELECT time_bucket('1 minute', ts) b, home_id, avg(current_ma) ma, min(battery_pct) pct
  FROM telemetry GROUP BY b, home_id;
CREATE TABLE decisions(ts timestamptz, home_id text, action text, factors jsonb, reason text, model text);
```
Free plan, no card. Batch inserts (every 2 s) so 500 homes do not hammer it. The `decisions` table is the audit trail; show "query any decision" in the demo.

## 6. Privacy and guardrails
- **Consent first:** homes enroll with a level (contact me / contact my caregiver / contact responders). No consent = no call.
- **Minimal data:** store device class and power draw, not diagnosis. Presence is a boolean, never audio or video.
- **Human in the loop:** `escalate_to_responder` only creates a request. A dispatcher clicks Approve. Say this in the pitch.
- **Template-only speech:** the agent picks a script id; it cannot write free text to a resident.
- **Safety model:** run Nemotron Safety Guard on (a) transcripts before they enter the agent context (prompt-injection by voice) and (b) any generated summary sent to a responder. NeMo Guardrails is optional; calling the guard model directly is 20 lines.
- **Audit:** every decision row stores inputs, factors, model id and reason.

## 7. Hour plan for Godfrey
| Hours from now | Task | Fallback if stuck |
|---|---|---|
| 0 to 1 | NVIDIA keys (both), tool-call smoke test, Twilio trial, verify phones, tunnel up | JSON-mode tools; ngrok if cloudflared fails |
| 1 to 3 | FastAPI skeleton, sim of 500 homes, MQTT publish/subscribe, harm-clock math, queue over WS | Skip MQTT for sim; inject in-process |
| 3 to 6 | Agent loop with tools, simulated calls, trace events | Run planner every 60 s only |
| 6 to 8 | Frontend: map, queue, trace panel | Table-only UI, map later |
| 8 to 10 | Twilio real call + Gather + Nemotron classify | Simulated call with live transcript |
| 10 to 12 | Guard checks, approval button, decisions table | Local Postgres or SQLite with same schema |
| 12 to 14 | Sleep 2 h (stagger with Rafael) | |
| 14 to 16 | Wire real ESP32 node from Rafael, Tiger Data hypertable + aggregate | Real node replays recorded data |
| 16 to 18 | Demo script: outage, drain, missed calls, escalation, approval. Record a backup video | |
| 18 to 20 | Stretch: NeMo Agent Toolkit wrapper, ElevenLabs voice, LoRa broadcast | Cut stretch |
| 20 to 21 | Devpost write-up, architecture diagram naming Nemotron at every step, submit | |

## Sources
- [Nemotron 3 Nano 30B-A3B API reference](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-nano-30b-a3b) · [model card](https://build.nvidia.com/nvidia/nemotron-3-nano-30b-a3b/modelcard)
- [Nemotron Safety Guard 8B v3 API](https://docs.api.nvidia.com/nim/reference/nvidia-llama-3_1-nemotron-safety-guard-8b-v3) · [NeMo Guardrails safety guard tutorial](https://docs.nvidia.com/nemo/guardrails/latest/get-started/tutorials/nemotron-safety-guard-deployment)
- [NeMo Agent Toolkit GitHub](https://github.com/NVIDIA/NeMo-Agent-Toolkit) · [install docs](https://docs.nvidia.com/nemo/agent-toolkit/latest/quick-start/installing.html)
- [NVIDIA forum: 40 RPM rate limit](https://forums.developer.nvidia.com/t/request-for-nvidia-build-api-rate-limit-increase-40-rpm-200-rpm/377433)
- [Twilio trial account](https://www.twilio.com/docs/usage/trials) · [Try out Voice (trial limits)](https://www.twilio.com/docs/usage/trials/try-out-voice) · [error 32100](https://www.twilio.com/docs/api/errors/32100)
- [ElevenLabs Twilio outbound call API](https://elevenlabs.io/docs/api-reference/twilio/outbound-call) · [Twilio + ElevenLabs handoff tutorial](https://www.twilio.com/en-us/blog/developers/tutorials/integrations/ai-agent-to-human-agent-elevenlabs-call-handoffs-twilio)
- [Tiger Data continuous aggregates](https://www.tigerdata.com/docs/use-timescale/latest/continuous-aggregates) · [Tiger free plan](https://www.tigerdata.com/blog/introducing-agentic-postgres-free-plan-experiment-ai-on-postgres)
