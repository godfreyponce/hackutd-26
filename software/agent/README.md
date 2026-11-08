# Box agent (#15)

Runs the check-in after an event. A planner (Nemotron) picks tool calls. Code checks every call. Code owns the alarm rule, the 3 tries, the stand-up re-ask and the spoken text.

## Run

```
python3.12 -m venv .venv
.venv/bin/pip install -r software/agent/requirements.txt
HUB_URL=ws://localhost:8765 .venv/bin/python -m software.agent
.venv/bin/python -m pytest software/agent
```

Run only one agent per hub. Two agents both answer every event.

## Planner chain

1. Hosted `nvidia/nemotron-3.5-lightning-30b-a3b` (needs `NVIDIA_API_KEY`). Thinking off, temp 0.6, top_p 0.95.
2. Local `nemotron-3-nano:4b` on Ollama (`ollama pull nemotron-3-nano:4b`). Thinking off.
3. The fixed script. It never fails.

Each hop writes an `agent` FALLBACK row with the reason. A text reply with no `tool_calls` is read as JSON mode: `{"tool": ..., "args": ...}`.

## Guardrails in code

- Alarm rule (`rule.py`): nobody + no answer = no alarm. Someone + no answer = alarm after 3 tries. "Help" = alarm. "Okay" = log it.
- If the rule demands an alarm and the planner skips it for one turn, code raises it (VERIFY "Rule override").
- `raise_alarm` is refused when the rule does not call for it.
- `speak` takes a script id from `scripts.py`, never text. A 4th ask is refused.
- Each try has its own line. The planner asks with the ask id; code picks `ask_stopped` (or `ask_event`), then `ask_retry_2`, then `ask_retry_3` by try number. The planner cannot skip or reorder them.
- After 3 no-answers the box says `escalate` ("I haven't heard back, so I'm contacting emergency services now."), then the alarm.
- An ok answer gets `reply_ok`. A help answer gets `reply_help` before the alarm, and no `escalate`. Replies do not listen.
- `reply_ok` is refused unless the last answer was ok. `reply_help` is refused unless it was help. If the planner skips a due reply for one turn, code speaks it (VERIFY "Rule override").
- Safety Guard (`nvidia/llama-3.1-nemotron-safety-guard-8b-v3`) screens every transcript before the planner sees it. No key: MOCK pass-through row. Guard error: the transcript is withheld.
- `raise_alarm` always sends `checkin alarm`. It calls `TWILIO_TO` only when all `TWILIO_*` vars are set and `TWILIO_TO` is a full `+1XXXXXXXXXX` number. Never 911.

## Hand-off note and why

When the outcome is alarm, the agent asks Nemotron for two things, in parallel:

- A hand-off note for responders, written from facts the code gives it: the trigger (quake peak g, or radar going from moving to still), presence, each answer with its transcript, battery, any active alert, the time. Nemotron also picks who to contact first from `HANDOFF_CONTACTS` in `scripts.py`. Thinking off.
- A why for the alarm decision, at most 3 lines. Reasoning on, with a budget of 200 reasoning tokens. It sees only the rule, presence and the answers. The rule still decides; the why only explains.

Code checks both. Every number must come from the facts. No emergency number. Under 60 words. A check that fails, or a planner that is down, gets a plain template instead. The agent then sends:

```json
{"type":"handoff","home":"H000","note":"...","contact":{"id":"godfrey","name":"Godfrey","role":"family contact, demo"},"by":"nemotron","why":["...","..."],"why_by":"nemotron"}
```

`by` and `why_by` are `nemotron` or `template`. The demo contacts are labels only. Nothing texts them.

## Settings (env)

| Var | Default | Does |
|---|---|---|
| `HUB_URL` | `ws://localhost:8765` | The bus |
| `NVIDIA_API_KEY` | none | Hosted planner and Safety Guard. None: MOCK |
| `AGENT_ASK_SCRIPT` | `ask_stopped` | `ask_event` uses the originally agreed line |
| `AGENT_LISTEN_S` | `6` | `listen_s` sent with each question |
| `AGENT_HEARD_GRACE_S` | `15` | Extra wait for `heard` before counting no_answer |
| `AGENT_PLANNER_TIMEOUT_S` | `20` | Per planner call, then fall back |
| `AGENT_OLLAMA_URL` / `AGENT_LOCAL_MODEL` | `http://localhost:11434/v1` / `nemotron-3-nano:4b` | Local planner |
