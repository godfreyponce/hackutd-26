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

## Results (Sun Nov 8, 2026, about 1:20 to 2:25 AM CT)

Hosted Nemotron planner and Safety Guard, real key, one run at a time, paced to 15 hosted calls per minute.

**10 runs per case, 1 s listen window** (`--runs 10 --listen-s 1`):

- 90 of 90 runs made the right call. 87 of 90 were planned by hosted Nemotron end to end.
- After "Help": alarm on screen 5.1 s median from the event (worst 7.0 s).
- No answer 3 times: alarm on the 3rd miss, 5.1 s median from the event (worst 9.0 s).
- 3 runs were not planned by Nemotron end to end. All 3 still made the right call:
  - One hosted planner turn got no reply in 20 s, and the fixed script finished the check-in. Alarm on the 3rd miss at 23.8 s.
  - One hand-off "why" got no reply in 20 s and used the template.
  - In one run, code refused a planner call (no fallback).
- Safety Guard: 56 safe, 2 unsafe (withheld from the planner), 2 unreachable. The decision uses the classified answer, so it was right in all of them.

| Case | Right call | Planned by Nemotron end to end | First ask median / worst | Alarm median / worst | Nemotron plans | Runs with a fallback | Code overrides / refused calls | Wrong ask line | Safety Guard safe / unsafe / unreachable | Reply to rule median / worst |
|---|---|---|---|---|---|---|---|---|---|---|
| ok: Event, someone there, says "I'm okay" | 10 of 10 | 10 of 10 | 0.6 s / 2.26 s | - / - | 31 | 0 | 0 / 0 | 0 | 10 / 0 / 0 | 0.38 s / 8.02 s |
| help: Event, someone there, says "Help" | 10 of 10 | 10 of 10 | 0.56 s / 1.06 s | 5.11 s / 7.01 s | 40 | 0 | 0 / 0 | 0 | 10 / 0 / 0 | 1.5 s / 4.34 s |
| silence: Event, someone there (still), silent 3 times | 10 of 10 | 10 of 10 | 0.56 s / 4.5 s | 5.09 s / 8.98 s | 70 | 0 | 0 / 0 | 0 | 0 / 0 / 0 | - / - |
| nobody: Event, nobody there, silent | 10 of 10 | 9 of 10 | 0.54 s / 0.95 s | - / - | 21 | 0 | 0 / 1 | 0 | 0 / 0 / 0 | - / - |
| unclear_then_ok: Unclear reply, then "yeah, I'm fine" | 10 of 10 | 10 of 10 | 0.56 s / 2.27 s | - / - | 50 | 0 | 0 / 0 | 0 | 19 / 1 / 0 | 6.36 s / 16.67 s |
| hedge: Hedged reply "I'm not sure" | 10 of 10 | 9 of 10 | 0.51 s / 0.82 s | 8.18 s / 12.9 s | 40 | 1 | 0 / 0 | 0 | 10 / 0 / 0 | 4.81 s / 10.36 s |
| still_vs_moving_still: Quake, presence still, silent 3 times | 10 of 10 | 10 of 10 | 0.62 s / 0.94 s | 5.06 s / 5.81 s | 73 | 0 | 0 / 0 | 0 | 0 / 0 / 0 | - / - |
| still_vs_moving_moving: Quake, presence moving, silent 3 times | 10 of 10 | 9 of 10 | 0.61 s / 0.9 s | 5.21 s / 23.78 s | 69 | 1 | 0 / 0 | 0 | 0 / 0 / 0 | - / - |
| standup: Alarm, then the person stands up and says "I'm okay" | 10 of 10 | 10 of 10 | 0.56 s / 0.87 s | 5.29 s / 8.22 s | 100 | 0 | 0 / 0 | 0 | 7 / 1 / 2 | 13.28 s / 20.02 s |

**One run per case at demo timing, 6 s listen window** (`--runs 1 --listen-s 6`):

- 9 of 9 right, 9 of 9 planned by hosted Nemotron end to end.
- After "Help": alarm 17.4 s from the event. No answer 3 times: alarm on the 3rd miss at 20.2 s.
- Speaking time is not simulated, so on the real box add the time to say each line.

The Safety Guard check runs before the rule, so a spoken reply waits for it. That wait was 0.4 to 13.3 s
(per-case medians), worst 20 s when the guard timed out.

Times are measured from the hub's publish time of the event to the hub's publish time of the
`checkin` message, so they include the planner and Safety Guard calls but not text to speech.
