# Judge-table rehearsal results (issue #60)

Sun Nov 8, 2026, about 2:00 to 3:10 AM CT, on the MacBook, on spare ports. Four passes of 10 runs per case,
one run at a time: 80 runs, 80 right calls, no failed runs. Hosted passes were paced to 15 Nemotron calls
per minute and ran only after #55's hosted passes ended.

- Demo run (case `standup`): event, 3 asks with no answer, alarm, dashboard zoom, the person stands up,
  "Are you okay?", "I'm okay", stand-down.
- Help fast path (case `help`): help sign, one ask, "Help", alarm.

Times are seconds from the event on the bus, median / worst of 10 runs.

## Demo run

| Step | Internet cut, listen 6 s | Internet cut, listen 4 s | Online, listen 6 s | Online, listen 4 s |
|---|---|---|---|---|
| First ask sent | 0.01 / 0.11 | 0 / 0.04 | 0.51 / 0.75 | 0.57 / 4.22 |
| First word spoken | 0.52 / 5.7 | 0.46 / 1.21 | 1.16 / 1.48 | 1.2 / 5.75 |
| Alarm on the bus | 30.31 / 41.11 | 24.06 / 24.77 | 47.17 / 73.12 | 42.45 / 64.03 |
| Dashboard zoom landed | 31.91 / 42.71 | 25.66 / 26.37 | 48.77 / 74.72 | 44.05 / 65.63 |
| Stand-down (clear) | 42.58 / 54.87 | 34.13 / 34.88 | 68.17 / 95.55 | 57.22 / 84.83 |
| Last word spoken | 46.25 / 59.55 | 37.82 / 38.57 | 73.59 / 100.77 | 62.68 / 89.87 |
| Right call | 10 of 10 | 10 of 10 | 10 of 10 | 10 of 10 |

## Help fast path

| Step | Internet cut, listen 6 s | Internet cut, listen 4 s | Online, listen 6 s | Online, listen 4 s |
|---|---|---|---|---|
| First ask sent | 0.01 / 0.01 | 0 / 0.01 | 0.52 / 0.69 | 0.59 / 1.74 |
| First word spoken | 0.49 / 0.58 | 0.52 / 0.57 | 1.36 / 1.54 | 1.39 / 2.83 |
| Dashboard zoom landed | 11.55 / 11.8 | 9.56 / 9.68 | 13.88 / 13.94 | 12 / 13.64 |
| Alarm on the bus | 9.96 / 10.21 | 7.96 / 8.08 | 15.61 / 22.29 | 15.52 / 30.78 |
| Last word spoken | 13.49 / 14.14 | 11.56 / 11.68 | 22.03 / 36.51 | 20.25 / 35.51 |
| Right call | 10 of 10 | 10 of 10 | 10 of 10 | 10 of 10 |

Online, the zoom starts on the "help" answer, before the Safety Guard check, so it lands before the alarm.

## Does the demo run fit about 45 s?

- Internet cut, listen 6 s: no. 46.3 s median, 59.6 s worst.
- Internet cut, listen 4 s: yes. 37.8 s median, 38.6 s worst.
- Online, listen 6 s: no. 73.6 s median, 100.8 s worst.
- Online, listen 4 s: no. 62.7 s median, 89.9 s worst.

## Where the online time goes

Read from `raw.jsonl` (hub publish times):

- Voice. Each ask takes about 11 s from `say` to `heard` with a 6 s listen (ElevenLabs line, its audio,
  the listen, Scribe), and about 9 s with a 4 s listen. That is 45 s and 37 s for the 4 asks.
- Safety Guard. On the room-noise listens, Scribe returned words instead of nothing:
  "[singing] And I want you to be mine", "[singing]", "[outro jingle]". The classifier still said
  no_answer each time, so every call was right. But a non-empty transcript goes to the hosted Safety Guard
  before the rule runs, and each check took 0.5 to 19.7 s. Per demo run that added 17.3 s median
  (45.5 s worst) with a 6 s listen, and 15.5 s median (43.3 s worst) with a 4 s listen.
  These online numbers describe the agent before #65 (PR #67), which removes the guard wait on no_answer.
- Without the guard wait, the online demo run would be 55.3 s median (6 s listen) and 47.4 s median (4 s
  listen). Measured per run as the last word minus that run's guard waits.
- With the internet cut, the guard fails at once and the transcript is withheld. Kokoro and Moonshine
  take every line, and Moonshine heard nothing in the noise.

The noise is a real MacBook mic recording (`software/voice/tests/fixtures/room_noise_real_mic.wav`).
So at the table, Scribe may write words into silence, and each unanswered ask may wait for a hosted
guard check. That is runtime behavior. This issue does not change it; the owner decides.

## Slow runs, with the reason from the logs

- Internet cut, listen 6 s, demo run 8 (alarm 41.1 s, last word 59.6 s): the agent was not slow. The fixed
  script put each ask on the bus at once. Every voice step was slower: the first line started 5.7 s after
  the event (median 0.5 s), and the 3 asks took 14.6, 14.2 and 12.1 s from `say` to `heard` (9.3 to
  10.9 s in runs 7 and 10). No error, and the same 6 agent fallback rows as every run. So the time went to local
  Kokoro synthesis and Moonshine transcription. The logs do not say why they were slower in that run.
  Other work shared the laptop then: #55's hosted pass was still running. Run 1 shows a smaller delay
  on its first line (4.3 s).
- Online, listen 6 s, demo run 5 (last word 100.8 s): the 4 Safety Guard checks took 45.5 s in all.
- Online, listen 6 s, help run 10 (last word 36.5 s): the reply line's audio began 19 s after its `say`
  message. `engine.log` has no error and no fallback. The ElevenLabs timeout (10 s) bounds each network
  read, not the whole request, so a slow reply is not cut off.
- Online, listen 4 s, help runs 3 and 10 (alarm 30.8 s and 28.1 s): Safety Guard checks of 17.2 s and 16.8 s.
- Online, listen 4 s, demo run 9 (first ask 4.2 s): the first hosted planner turn was slow.

## Settings proposal (for the owner, after the filming take)

Set `AGENT_LISTEN_S=4` (env override, demo default 6). With the internet cut, the demo run drops from
46.3 s to 37.8 s median and fits. Online it drops from 73.6 s to 62.7 s median and still does not fit,
because of the Safety Guard waits above. The cost: the person has 4 s, not 6 s, to answer. In these runs
the reply starts 0.5 s into the window (a guess), so a slow speaker is not tested.
Keep `AGENT_HEARD_GRACE_S` at 15 s, and do not lower it. The agent waits the listen window plus this
grace for each answer, counted from its `say`. So the voice has the grace (15 s) for everything except the
listen: any line still queued ahead, then making and speaking the question, then the speech-to-text. For
"Are you okay?" after the alarm, the alarm line is queued ahead. In these passes that work took 2 to 10 s per ask,
but there are two warnings:

- Online, help run 10 above, one ElevenLabs line started 19 s after its `say`. A stall like that on the
  alarm line would use up the grace, the "I'm okay" would count as no answer, and the alarm would stay up.
- In the end-to-end test, on this laptop with a load average near 80, Kokoro was slow enough that the
  stand-up answer missed the window twice in 5 tries. The test now gives the agent a 60 s grace.

No setting or runtime code was changed.

## What was real and what was simulated

- Real: the hub, the agent process and its planner chain (hosted Nemotron and the Safety Guard online,
  the fixed script with the internet cut), the voice service, the text-to-speech of every line
  (ElevenLabs online, Kokoro offline), the speech-to-text of every reply (Scribe online, Moonshine
  offline), and the classifier.
- Simulated: the speaker and the microphone. A line waits its synthesized audio's real length instead of
  playing. A listen waits the listen window, then gives the speech-to-text a recorded reply (macOS `say`
  voice, from the voice test fixtures) 0.5 s into the real room-noise recording.
- Not run: the local Nemotron 4B tier. It shares the live loop's Ollama, so its URL points at a closed port.
- Dashboard zoom: 1.6 s after the alarm or "help" message on the bus (`camera.js` `NEAR_FLIGHT_MS`, the
  flight from the city view). No browser was driven.
- The person stands up as soon as the alarm reaches the bus.
- The voice service ran in the hub's process, not in its own process as in the live loop.
- Internet cut: a dead proxy (a closed local port) for the rehearsal process and the agent child only.
  Nothing global changed. A refused connection fails at once, so these times are the best case. A
  network that hangs instead waits out the ElevenLabs timeout on each line and the planner timeout on
  each turn. The logs show the chain: "LLM unreachable: hosted Nemotron 30B", then the fixed script plans,
  and every ElevenLabs call fails with a proxy error, so Kokoro and Moonshine take over.

## Rerun

Run from the repo root. The keys come from the environment; they are redacted from the saved logs.

```bash
NVIDIA_API_KEY=... ELEVENLABS_API_KEY=... .venv/bin/python -m software.eval.rehearsal --out /tmp/land-rehearsal --runs 10
```

Add `--cut-internet` for the internet-cut passes and `--listen-s 4` for the proposal reruns.
