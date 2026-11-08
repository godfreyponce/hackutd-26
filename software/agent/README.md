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
- `speak` takes a script id from `scripts.py`, never text. A 4th ask is refused. The 4th try is "Alerting your emergency contact now.", then the alarm.
- Safety Guard (`nvidia/llama-3.1-nemotron-safety-guard-8b-v3`) screens every transcript before the planner sees it. No key: MOCK pass-through row. Guard error: the transcript is withheld.
- `raise_alarm` always sends `checkin alarm`. It calls `TWILIO_TO` only when all `TWILIO_*` vars are set and `TWILIO_TO` is a full `+1XXXXXXXXXX` number. Never 911.

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
