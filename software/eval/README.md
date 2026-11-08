# Decision-layer eval (issue #55)

Answers the judge question "how accurate is it?" for the decision layer, not the camera.
We don't bet on spotting the fall. A wrong guess costs one question. The alarm needs an event,
a person in the room, and no answer three times. The alarm is fake and never calls 911.

## What runs

- The real hub (`software/hub`), in the eval process, on a free port picked by the OS.
- The real agent (`python -m software.agent`) as a child process, with the hosted Nemotron planner
  and Safety Guard when `NVIDIA_API_KEY` is set.
- The real voice service class (`software/voice/service.py`) with a scripted engine in place of
  the microphone and speaker. It sends `heard` exactly as the live voice service does, with the
  answer from `software/voice/classify.py`. Silence is an empty transcript, so `no_answer`.
- Events (`quake`, `fall_hint`, `help_gesture`) and `presence` go in as bus messages, the same
  shapes the box and the presence service send.

The eval never uses ports 8765 or 8080. It points the agent's local Ollama URL at a closed port,
so a hosted failure goes straight to the fixed script and never loads the live loop's model.
It removes the Twilio and ElevenLabs variables from the agent's environment, so nothing calls or texts anyone.

## Cases

Every expected outcome comes from the code (`software/agent/rule.py`, `software/agent/checkin.py`,
`software/voice/classify.py`). `software/eval/tests/test_cases.py` checks the table against
`classify` and `rule.decide`.

| Case | Setup | Expected |
|---|---|---|
| `ok` | quake, presence moving, "I'm okay" | 1 ask, outcome ok, no alarm |
| `help` | help sign, presence moving, "Help" | alarm right after the 1st answer |
| `silence` | fall_hint, presence still, silent 3 times | 3 asks, alarm after the 3rd miss |
| `nobody` | quake, presence none, silent | 1 ask, outcome no_alarm (the box does not ask again) |
| `unclear_then_ok` | fall_hint, still, "um, what was that", then "yeah, I'm fine" | the unclear reply counts as a miss, 2nd ask, outcome ok |
| `hedge` | fall_hint, still, "I'm not sure" | any negation counts as help, so alarm after the 1st answer |
| `still_vs_moving_still` | quake, still, silent 3 times | alarm after the 3rd miss |
| `still_vs_moving_moving` | quake, moving, silent 3 times | alarm after the 3rd miss (still and moving both count as someone) |
| `standup` | the `silence` case, then presence moving after the alarm, "I'm okay" | alarm, then one "Are you okay?", outcome clear |

A run is right only when the answers, the number of asks, every decision outcome, and the
answer count before the alarm all match. A timeout is a wrong run.

## Run

```bash
.venv/bin/python -m software.eval --out /tmp/land-eval --runs 1
```

With no key the agent runs in mock mode and the fixed script plans. For the real planner, pass the
key in the environment of the same command (`NVIDIA_API_KEY=... .venv/bin/python -m software.eval ...`).
The eval gives the key only to the agent process and removes it from the saved agent log.

Flags:

- `--runs N`: runs per case. One run at a time.
- `--cases a,b`: only these case ids.
- `--listen-s S`: sets the agent's `AGENT_LISTEN_S` (demo default 6). The scripted engine waits
  that long per listen. Speaking time is not simulated, so real demo times are longer by the spoken lines.
- `--max-rpm R` (default 15): after each run, wait until its estimated hosted calls average out to
  at most R per minute. Basis: the hosted API allows about 40 requests per minute per key (NVIDIA
  forum moderator, May 2026; no published SLA), and the live loop shares the key.

Output in `--out`: `results.md` (the table and the rerun command), `results.json` (every run),
`raw.jsonl` (every bus message with the hub's publish time), `agent.log`, `voice.log`.

## Tests

```bash
.venv/bin/python -m pytest software/eval
```

`test_loop.py` runs every case once end to end in mock mode (about 15 s).
