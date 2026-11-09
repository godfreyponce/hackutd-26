# LAND fresh-eyes review

- **Code reviewed:** main at c603971, on 2026-11-08.
- **Method:** 6 area reviewers (agent, voice, hub/presence/same, web, eval, README and docs) and one mock rehearsal of the 5 demo paths. Each reviewer worked from the code with no keys set and wrote a reproducer for each bug it confirmed.
- **Coordinator rule:** a fix that changes when an alarm or a check-in fires becomes a PR only if the docs already say what should happen. If the docs do not say, the fix becomes an owner proposal (section 4).
- **Suites on main:** pytest 370 passed (agent 129, voice 82, hub/presence/same 132, eval 27). Node: home 144, dashboard 70.
- **Mock eval:** 9 of 9 runs right.
- **Coordinator log:** coordinators 10, 11, 12 and 13 received the PRs.

## 1. PRs opened

State is from `gh pr view` on 2026-11-08. Merge times are UTC.

| PR | Branch | Head SHA | State | Bug |
|---|---|---|---|---|
| #71 | fe-dash-checkin-carry | 2f7947e | Merged 10:41 | Dashboard: an old ok carries into the next check-in, so H000 shows a green ok dot while its card says no response. The fix stops the answered_ok carry. |
| #72 | fe-dash-alarm-try | 221cd13 | Merged 10:43 | Dashboard: the alarm (sent as try 4) is counted as a 4th try, so the panel prints "Alarm, try 4". A late no_answer then counts 4 misses. A council bug, fixed on the dashboard side. |
| #73 | fe-agent-alarm-stays | e37e077 | Merged 10:46 | Owner proposal (a). After the alarm, a stand-up with no answer now keeps the alarm up. |
| #74 | fe-docs-claims | 24fcf53 | Merged 10:51 | READMEs and help text that disagree with the code: camera help sign, stale #19 notes, `rerank`, Piper vs Kokoro, phone format, eval numbers, dashboard `q` key. |
| #76 | fe-dash-reset-presence | edc5ab2 | Merged 10:57 | Dashboard: H000 starts and resets as "Moving", but the agent and the sim reset presence to none. H000 presence is now none after reset. |
| #77 | fe-eval-missing-event | c1407e0 | Merged 10:57 | Eval: a run whose event never reached the bus crashes the report with KeyError, so `results.md` is never written. |
| #78 | fe-home-fresh-checkin | 8adcf01 | Merged 10:59 | Home: "NO RESPONSE. Asking again." stays after a no-alarm check-in and hides the next check-in. The old Heard row and the old help sign show during the next question. |
| #79 | fe-agent-bad-plan | a888f6e | Merged 11:04 | Agent: a planner reply it cannot read (bad JSON args, a list as `template_id`) kills the check-in task. The agent then ignores every trigger until reset. Follow-up: a crash while an alarm is due still raises no alarm. |
| #80 | fe-voice-reset-stop | 0291644 | Merged 11:13 | Voice: reset now stops the line in flight, the tone and the listen. Before, the next question could be up to one listen window late (rehearsal finding). A council bug. |
| #81 | fe-agent-noalarm-close | 477a2d0 | Open, draft | Agent: a check-in that ends at "nobody + no answer = no alarm" sends no end message, so the screens stay on "Asking again". The fix sends `checkin clear` on the nobody path, and the screens stay true. Owner item: proposal (m). |

## 2. Findings by area

Status values: "fixed in PR #N", "owner proposal (letter)", or "finding only". Line numbers are at c603971.

### Agent (software/agent)

| # | Where | Input | What happens | Demo impact | Status |
|---|---|---|---|---|---|
| A1 | planner.py:47-48, checkin.py:516, checkin.py:258-265 | Local Nemotron replies `{"tool":"speak","args":"{'script_id': 'ask_stopped'}"}`, or sends a list as `template_id` | JSONDecodeError or TypeError kills the task. No fallback, no trace row. The incident stays open, so every later trigger is dropped until reset. | High when a model is used. No question, no alarm. | Fixed in PR #79 (merged). Follow-up: a crash while an alarm is due raises no alarm. |
| A2 | checkin.py:444-447 | Alarm up, stand-up re-ask, person walks out (presence none), no answer | NO_ALARM branch runs before the alarm branch. Outcome `no_alarm`, no `clear`. Screens keep the alarm. A help sign then starts a fresh check-in. Breaks README:51. | Medium | PR #73 (merged), owner proposal (a) |
| A3 | __main__.py:26-29, :69-82 | Hub drops mid check-in | `send` drops messages, the check-in keeps going and raises the alarm where no screen sees it. After reconnect nothing is re-sent and the agent stays stuck. | Medium if the hub restarts on stage | Owner proposal (j) |
| A4 | checkin.py:151-154 | Voice answer arrives after the 21 s wait (ElevenLabs 10 s timeouts on hung wifi) | The late `heard` is taken as the answer to the next try. A "help" can be lost and the box says "escalate". | Low to medium on bad wifi | Owner proposal (j) |
| A5 | checkin.py:420, :429; guard.py:22 | Person says "help" | Box waits for the Safety Guard (up to 20 s, measured 0.5 to 13 s) before `reply_help` and the alarm. The rule never reads the transcript. | Medium with a hosted key | Owner proposal (d) |
| A6 | checkin.py:526-531 | Twilio set, planner calls `notify_contact` early | Any template passes while the outcome is open, with no count. Three texts went out before an ok. | Only with Twilio set | Finding only |
| A7 | checkin.py:205-206 | Planner calls `schedule_recheck(minutes=0.0001)` | Re-opens at once and can loop. Asks `ask_stopped` after a quake. Mutes real EQW alerts for 300 s. | Low, model dependent | Finding only |
| A8 | checkin.py:301-309 | Planner keeps calling `get_presence` | Nothing forces the first question for 19 more turns. | Low | Finding only |
| A9 | checkin.py:501 | An RWT test alert, then a fall_hint alarm | Hand-off note cites "Official alert: Required Weekly Test". No alert ever expires. README:60 says "any active alert". | Low | Finding only |
| A10 | README.md:35, notify.py:25 vs notify.py:14 | Read the doc | Doc says `+1XXXXXXXXXX`; code accepts `\+\d{10,15}`. 911 is still blocked. | None | Fixed in PR #74 (merged) |
| A11 | README.md:48, :53 | Read the doc | Says the camera sends `help_gesture`. On main only sim key `h` does. | Low | Fixed in PR #74 (merged) |
| A12 | checkin.py:3-4, README.md:20 | Read the doc | "Never fails" and "can never skip an alarm" are false while A1 is open. | None after A1 | Fixed in PR #79 (merged) |

Risk, not a bug: if the hosted planner hangs instead of refusing, each check-in waits 20 s before the first question.

### Voice (software/voice)

| # | Where | Input | What happens | Demo impact | Status |
|---|---|---|---|---|---|
| V1 | classify.py:10, :16 | "I'm okay, don't worry", "No worries, I am fine", "Yes, no problem" | Any negation word means `help`, so the alarm fires on the first answer. #69 widens the negation list, so this stays. | High if a judge answers this way | Owner proposal (c) |
| V2 | classify.py:11 | "all good", "I'm good", "sure", "uh-huh", "O.K." | `no_answer`. Three of these with someone in the room raise the alarm. | Medium | Owner proposal (c) |
| V3 | classify.py:15 | "I canʼt get up" with U+02BC, or U+2018 | Only U+2019 is normalized, so this is `no_answer`. | Low | Finding only |
| V4 | service.py:59, :80, :89 | Reset during a line | Log says "dropped queued and in-flight lines", but the line playing and its listen run to the end. | Low | Line, tone and listen fixed in PR #80 (merged). TTS and STT calls already in progress: owner proposal (n). |
| V5 | README.md:48 | Stand-up line within 3 s of the siren | Any later play or record stops `alarm.wav` early. `alarm_on` stays True. | Low | Finding only |
| V6 | README.md:18, :26; __main__.py:39; engines.py:285 | Read the doc and logs | Say Piper; the default offline voice is `kokoro:am_liam` (engines.py:20). | None | Fixed in PR #74 (merged) |
| V7 | README.md:59 | Read the doc | OK list leaves out "yup" and "all right". | None | Fixed in PR #74 (merged) |
| V8 | README.md:74, test_offline_stt.py:1 | Read the doc | Fixtures "all from `say`"; `eleven_long_answer.wav` is ElevenLabs. | None | Fixed in PR #74 (merged), README only |
| V9 | README.md:36 | Read the doc | "Text:" mode bullet sits under "Voice", not "Modes". | None | Finding only |

EQW tone path: no bug. Real hub, real agent and real voice give tone, then demo line, then ask, with one tone per alert.

### Hub, presence, SAME (software/hub, software/presence, software/same)

| # | Where | Input | What happens | Demo impact | Status |
|---|---|---|---|---|---|
| H1 | presence/tracker.py:23-28, :31-33 | Two still people with boxes of about the same area | The tracked box jumps between them each frame. State stays `moving`, never `still`, so no `fall_hint`. A bigger person walking in reads as a stand-up. | High if a presenter stands in frame | Owner proposal (e) |
| H2 | hub/serial_reader.py:30-37 | USB unplug in serial mode | SerialException ends `run_serial`, and the whole hub, bus and web go down. | Low, the demo uses `--sim` | Finding only |
| H3 | hub/serial_reader.py:27, :34 | A line split across the 0.5 s readline timeout | Both halves are dropped as not JSON. About 1% of lines. | Low | Finding only |
| H4 | same/same_to_alert.py:127-136 | `ZCZC-CIV-CEM-048000+...` (statewide Texas) | Dropped as "not our area". A test pins this on purpose. | Low, the stage file uses county codes | Finding only (spec question) |
| H5 | hub/alert_level.py:27 vs agent/checkin.py:211, home/state.js:168 | `{"type":"alert","code":"eqw"}` hand-typed | Hub gives a red banner; agent and home start no check-in. | Low | Finding only |
| H6 | hub/README.md:74, :82 | Read the doc | "Not in #19 yet" for `tone` and hand-off. #19 has both now. | None | Fixed in PR #74 (merged) |
| H7 | hub/README.md:56, :62 | Read the doc | Says the camera sends `help_gesture`. That code is only on pi-integration. | Low | Fixed in PR #74 (merged) |
| H8 | hub/README.md:3, :24, :44; hub/__main__.py:24 | Read the doc | Describes the ESP32 over serial. Rafael's #19 comment says the ESP32 is out. | None | Finding only (update when pi-integration lands) |
| H9 | hub/README.md:88, agent/handoff.py:30, agent/README.md:60 | Read the doc | `note` is "a short note for responders". The contact is family. | Wording | Owner proposal (f) |

### Web (software/web home and dashboard)

| # | Where | Input | What happens | Demo impact | Status |
|---|---|---|---|---|---|
| W1 | home/state.js:82, :95-111 | Presence none, quake, no answer, then a new fall_hint | Home stays on "NO RESPONSE. Asking again." after the box stops asking. The next check-in shows that too on try 1. | High, breaks the beat after the "nobody home" beat | Fixed in PR #78 (merged). PR #81 (draft) sends the missing end message. |
| W2 | home/state.js:128 | Check-in answered ok, then a new check-in | Old "I'm okay" chip and transcript show next to the new question. | Medium | Fixed in PR #78 (merged) |
| W3 | dashboard/box.js:11, index.html:33 | Reset, then quake | H000 shows "Presence: Moving" and ranks as moving while the agent says nobody detected. | Medium | Fixed in PR #76 (merged) |
| W4 | dashboard/box.js:28-33, app.js:127 | Quake, check-in 1 ok, check-in 2 no answer | Green ok dot next to a red card that says "No response after an event". Counters wrong. | Medium | Fixed in PR #71 (merged) |
| W5 | dashboard/box.js (`checkin` case) | 3 misses, then `checkin alarm try 4` | Box panel prints "Alarm, try 4" and a late no_answer counts 4. Found while triaging W4. | Low | Fixed in PR #72 (merged) |
| W6 | dashboard/app.js:154, :187 | Help sign or fall_hint, then alarm, with no quake | Camera flies to H000, but rank says "Not hit" and the queue says "No event yet". `box.event` is never read. | Medium | Owner proposal (g) |
| W7 | dashboard/app.js:136 | A second quake after the first wave ends | Dropped until reset. Home shows it, so the screens disagree. | Medium on a second take without `r` | Owner proposal (g). README wording fixed in PR #74 (merged). |
| W8 | home/app.js:489, dashboard/bus.js:15 | `?hub=localhost:8765` (no scheme) | WebSocket throws. Home never retries; dashboard draws no map. | Low | Finding only |
| W9 | dashboard/app.js:405, :915 | Twilio variables set | "Demo only, no real call." shows while the teammate's phone rings. | Medium with Twilio | Owner proposal (h) |
| W10 | dashboard/README.md:16 | Press `q` | README says nothing is sent; the page sends `queue` messages. | None | Fixed in PR #74 (merged) |
| W11 | home/app.js:8 | Read the comment | "Change it here only" is false; LAND is hard-coded in 3 HTML files and tests. | None | Finding only |
| W12 | home/state.js:110 | Help sign or EQW check-in, no shaking | Neighborhood card says "This home was hit." | Low | Finding only |
| W13 | home/state.js:80 | Help sign during an open quake check-in | Home says "Help sign seen. Asking if you are okay." while the agent ignores the sign. | Low | Finding only |
| W14 | agent `ALARM_CALL_TEXT` | "help" answer | Call text says "no response after an event" even after "help". | Only with Twilio | Finding only |
| W15 | dashboard/sim.js:2, test/sim.test.js:18 | Read the code | "never dispatched" comment and a "dispatcher" test name. Not user facing. | None | Finding only |

### Eval (software/eval)

| # | Where | Input | What happens | Demo impact | Status |
|---|---|---|---|---|---|
| E1 | score.py:27-29, :146 | A run whose event never reaches the bus | `judge()` leaves out `wrong_lines` and `heard_to_rule_s`; `summarize()` raises KeyError. Only `raw.jsonl` survives. | Low, loses a long hosted run's report | Fixed in PR #77 (merged) |
| E2 | run.py:194-197 | `standup` case where the alarm never comes | Waits twice the run timeout, about 480 s. README says 240 s. | Low | Finding only |
| E3 | __main__.py:40-41 | Mock run | Headline says the wait is "mostly the Safety Guard check"; in mock the guard is instant. | None | Fixed in PR #74 (merged) |
| E4 | README.md:95 | Re-score #55 data with current `score.py` | `unclear_then_ok` reply-to-rule median is 7.05 s, not 6.36 s, since #65. | None | Fixed in PR #74 (merged) |
| E5 | README.md:72 | Run `test_loop.py` | Takes about 5 s, not 15 s. | None | Fixed in PR #74 (merged) |
| E6 | rehearsal-results.md:88-89 | Read the doc | Says the wait is counted from the say; code counts from the `listen` call. | Low | Finding only |
| E7 | cases.py | Read the cases | No EQW case. No "help with nobody in the room" case. Nothing after the last Decision row is judged. | None | Finding only |
| E8 | run.py shutdown | Any eval run | Two websockets tracebacks on stderr at shutdown. Results are fine. | None | Finding only |
| E9 | README.md:4 | Read the doc | "We don't bet on spotting the fall." This is the approved judge line. | None | Finding only (approved) |

### README and docs

| # | Where | Input | What happens | Demo impact | Status |
|---|---|---|---|---|---|
| D1 | agent/settings.py:19, checkin.py:203 | README.md:100 quick start: `m`, then `q` | Box says "Hey, I noticed you stopped moving" while presence says moving. The filming panel sends the same order. | Medium, a judge hears a false line | Owner proposal (b) |
| D2 | hub/README.md:134 | Read the doc | Says the agent sends `rerank`. `build_agent` passes no ranker. | None | Fixed in PR #74 (merged) |
| D3 | README.md:139, docs/HackUTD-2026.md | Read the doc | Hub note skips 13 notes and still describes the old idea. | None | Finding only (owner notes) |
| D4 | eval/README.md:50, :137 vs README.md:65 | Read the doc | Eval shows `NVIDIA_API_KEY=... <command>`; root says never put a key on a command line. | Low | Finding only |
| D5 | dashboard/README.md:3 vs README.md:49 | Read the doc | "500 simulated homes" vs 499 simulated plus H000. | None | Finding only |
| D6 | README.md:120-133 | Read the layout | Leaves out `software/eval/`, `docs/lifeline/`, `docs/ui/` and `panel.js`. | None | Finding only |
| D7 | docs/research/HackUTD-SDR-Alerts.md:17-72 | Read the doc | Describes `samedec` and a "DEMO ONLY" headline; code uses multimon-ng and a plain headline. | None | Finding only |
| D8 | docs/HackUTD-Hardware-Status.md:19 | Read the doc | SDR "not tested yet"; hardware/radio now decodes. | None | Finding only |
| D9 | docs/ (tracks, lifeline, 35 files) | Read the docs | Rule breaks: middle dots, em dashes, the banned phrase, a dispatch flow. | Low | Owner proposal (i) |

## 3. Rehearsal

### Setup

- Worktree detached at c603971. No tracked file changed, no commit, no push. The worktree was removed after.
- Bus on 18765, web on 18080, both checked free with lsof first. The live hub on 8765 and 8080 (PID 77787) was never touched.
- Keys unset for every process: `env -u NVIDIA_API_KEY -u ELEVENLABS_API_KEY -u TWILIO_ACCOUNT_SID -u TWILIO_AUTH_TOKEN -u TWILIO_FROM -u TWILIO_TO -u HUB_URL`. A count of key names in each process environment gave 0.
- Ollama pointed at closed port 127.0.0.1:9, so every check-in fell back to the fixed script.
- Hub ran with the real `--sim` keyboard through a pty wrapper. Voice ran in `--text` mode so nothing played aloud. A driver sent sim keys and typed answers when a `say` with `listen_s` appeared.
- Listen window 6 s, the demo default.
- Cleanup: PIDs 77020, 36877, 36871, 36589, 36585 and 36874 were killed by PID. A stray `sleep` from a failed first launch (PID 33380) was also killed by PID. Nothing listens on 18765 or 18080 now.

### Results

| # | Path | Expected | Observed | Result |
|---|---|---|---|---|
| 1 | `s` still, `q` quake, silent 3 times | Alarm after the 3rd miss | ask_stopped, ask_retry_2, ask_retry_3, escalate, `checkin alarm` at +18.09 s. Template hand-off. | PASS |
| 2 | `m`, `q`, "help" | Alarm at once | `heard help`, reply_help, `checkin alarm` at +0.01 s. No escalate. | PASS |
| 3 | `m`, `q`, "I'm okay" | No alarm | `heard ok`, reply_ok, outcome ok. | PASS |
| 4 | `n` none, `q`, silent | No alarm | One ask, then "nobody detected + no answer = no alarm". No second ask. | PASS |
| 5 | `s`, `a` sim EQW (demo), silent 3 times | Tone on the first say only | `alert_demo` carries `"tone":"warning"`, one WARNING TONE in the voice log. Retries have no tone. Alarm at +18.03 s. | PASS |
| 5b | `m`, real SAME chain `listen.sh --file demo_eqw.wav`, silent then "I'm okay" | Same as 5 | Decoded and published at level `emergency`. Tone only on alert_demo. Outcome ok. | PASS |
| 5c | `m`, bus EQW with `demo:false`, silent then "I'm okay" | Tone on the first say | Tone sits on `ask_event` (no demo line). Ask 2 has no tone. | PASS |

| Extra check | Observed |
|---|---|
| E1: quake, then EQW 1 s later | "Alert ignored: a check-in started 1 s ago, under 300 s." |
| E3: help sign `h`, then "help" | ask_gesture, then alarm at once. |
| E4: `m` then `s` fall_hint, 3 misses, alarm, then `m` | Stand-up, standup_ask, "I'm okay", `checkin clear`. |
| Mock eval, `--runs 1` | 9 of 9 right. |

### Raw bus excerpts

Path 1:
```
04:27:13.122  +  0.00s {"type": "quake", "peak_g": 0.82}
04:27:13.192  +  0.07s {"type": "say", "script_id": "ask_stopped", ..., "listen_s": 6.0}
04:27:19.196  +  6.08s {"type": "heard", "answer": "no_answer", "transcript": ""}
04:27:19.197  +  6.08s {"type": "agent", "step": "VERIFY", "text": "Rule: someone detected + no answer, try 1 of 3. Ask again."}
04:27:25.204  + 12.08s {"type": "say", "script_id": "ask_retry_3", ...}
04:27:31.206  + 18.09s {"type": "agent", "step": "VERIFY", "text": "Rule: someone detected + no answer after 3 tries = alarm. Next: raise_alarm."}
04:27:31.206  + 18.09s {"type": "say", "script_id": "escalate", ...}
04:27:31.207  + 18.09s {"type": "checkin", "state": "alarm", "try": 4}
voice: [voice] ALARM tone (fake alarm, local only, nothing is called)
```

Path 2:
```
04:27:53.549  +  0.01s {"type": "heard", "answer": "help", "transcript": "help"}
04:27:53.550  +  0.01s {"type": "agent", "step": "VERIFY", "text": "Rule: the answer was help = alarm. Next: raise_alarm."}
04:27:53.550  +  0.01s {"type": "say", "script_id": "reply_help", ...}
04:27:53.550  +  0.01s {"type": "checkin", "state": "alarm", "try": 2}
```

Path 4:
```
04:28:25.229  +  6.00s {"type": "heard", "answer": "no_answer", "transcript": ""}
04:28:25.230  +  6.01s {"type": "agent", "step": "VERIFY", "text": "Rule: nobody detected + no answer = no alarm."}
04:28:25.230  +  6.01s {"type": "agent", ... "Decision: trigger quake; presence sensor none (nobody detected); answers no_answer; outcome no_alarm."}
```

Path 5, bus then voice:
```
04:28:43.084 {"type": "alert", ..., "code": "EQW", "station": "HACKDEMO", "demo": true, "level": "emergency"}
04:28:43.091 {"type": "say", "script_id": "alert_demo", "text": "DEMO, not a real alert.", "tone": "warning"}
04:28:43.091 {"type": "say", "script_id": "ask_event", "text": "Something just happened. Are you okay? Please respond.", "listen_s": 6.0}
04:28:49.100 {"type": "say", "script_id": "ask_retry_2", ..., "listen_s": 6.0}        <- no tone
04:28:55.108 {"type": "say", "script_id": "ask_retry_3", ..., "listen_s": 6.0}        <- no tone
voice: [voice] WARNING TONE (EQW alert, not the alarm)
       [voice] SAY [alert_demo] DEMO, not a real alert.
       [voice] SAY [ask_event] Something just happened. ...
```

Path 5c:
```
04:29:47.296 {"type": "say", "script_id": "ask_event", ..., "listen_s": 6.0, "tone": "warning"}
04:29:53.312 {"type": "say", "script_id": "ask_retry_2", ..., "listen_s": 6.0}
```

### Finding: the next question is late after a reset

Status: fixed in PR #80 (merged).

- **Case:** reset while the box is listening, then trigger a new event at once.
- **What happens:** `software/voice/service.py:55-59` clears the queue on reset but does not stop the listen in progress. Lines 84-85 run it to the end, and line 89 throws away its result. The new question waits for the old window to end, so it can be up to 6 s late. An answer given in that gap goes into the old listen and is lost.
- **Reproducer:** sim keys `m`, `q`, wait 2 s, `r`, wait 1 s, `s`, `q`. Answer "help" 1 s after the new `say`.
- **R1 and R2:** "help" went into the old listen and was lost. The new ask was spoken late, then 3 silences, then the alarm (+23.35 s in R1).
- **R3:** answer sent 4 s late. The ask was spoken 1.77 s after its bus `say`, then "help" was heard and the alarm was right.
- **Demo impact:** with a real mic people answer after the question, so the visible effect is the late question. It matters when filming presses `r` and retriggers fast.

R1, bus then voice:
```
04:32:03.193  +  0.01s {"type": "say", "script_id": "ask_stopped", ..., "listen_s": 6.0}
04:32:05.586  +  2.40s {"type": "reset"}
04:32:07.395  +  4.21s {"type": "quake", "peak_g": 0.82}
04:32:07.397  +  4.22s {"type": "say", "script_id": "ask_stopped", ..., "listen_s": 6.0}
04:32:08.398           [driver] wrote 'help' to voice stdin after 1s
04:32:14.410  + 11.23s {"type": "heard", "answer": "no_answer", "transcript": ""}

04:32:03.238 [voice] SAY [ask_stopped] Hey, I noticed you stopped moving. Are you okay?
04:32:05.598 [voice] reset: dropped queued and in-flight lines
04:32:08.412 [voice] SAY [ask_stopped] Hey, I noticed you stopped moving. Are you okay?
04:32:14.452 [voice] HEARD no_answer: ''
```

### Mock eval

`python -m software.eval --runs 1` with all keys unset. Exit 0. 9 of 9 runs right (ok, help, silence, nobody, unclear_then_ok, hedge, still_vs_moving_still, still_vs_moving_moving, standup). The fixed script planned every run. `pytest software/eval`: 27 passed.

## 4. Owner proposals

### (a) The alarm stays on screen after the agent closes it

- **Case:** the alarm is up. Presence goes still to moving, so the agent asks `standup_ask`. The person walks out (presence none) and nobody answers.
- **Now:** the agent sets outcome `no_alarm` and sends no `clear` (`checkin.py:444-447`). Both screens keep the alarm. A help sign then starts a new check-in during the alarm, which README:51 says cannot happen.
- **Choices:**
  1. Keep it as is.
  2. Keep the alarm up until an ok answer or a reset. This is PR #73 (branch `fe-agent-alarm-stays`, fix and test), merged.
- **Risk:** choice 1 leaves the screens and the agent out of step. Choice 2 changes when an alarm ends; a person who leaves keeps the alarm until someone presses reset.

### (b) A quake asks "I noticed you stopped moving"

- **Case:** presence moving, then a quake.
- **Now:** the default `AGENT_ASK_SCRIPT=ask_stopped` (`settings.py:19`, `checkin.py:203`) says "Hey, I noticed you stopped moving. Are you okay?" while presence says moving. The quick start and the filming panel both hit this.
- **Choices:**
  1. Code: a quake asks with `ask_event`, like an EQW alert.
  2. No code: set `AGENT_ASK_SCRIPT=ask_event` for the demo.
- **Risk:** choice 1 changes a spoken line in code and its tests. Choice 2 also changes the fall_hint and recheck line to "Something just happened", which is still true.

### (c) The answer classifier

- **Case:** a judge says "I'm fine, don't worry", or "all good".
- **Now:** "I'm fine, don't worry", "No worries, I am fine" and "Yes, no problem" are `help` and fire the alarm at once. "all good", "I'm good", "sure" and "uh-huh" are `no_answer`; three of those with someone home fire the alarm.
- **Note:** #69 handles the help-word lists. It widens the negation list, so this case stays.
- **Choices:**
  1. Keep the documented rule and tell judges to answer "okay" or "help".
  2. Check OK words before negation for "no worries", "no problem" and "don't worry".
  3. Add "all good" and "I'm all good" to OK, still leaving out plain "good".
  4. Ask once to confirm when the help came only from a negation.
- **Risk:** each loosening can let a real "no" through as ok. Choice 4 adds a question before the alarm.

### (d) A help answer waits for the Safety Guard

- **Case:** the person says "help" with a hosted key set.
- **Now:** `_listen` awaits the guard (`checkin.py:420`) before the rule (`:429`). The box is silent for the whole guard call, timeout 20 s, measured 0.5 to 13 s.
- **Choices:**
  1. Keep it.
  2. Apply the rule first on a help answer (it does not read the transcript), then screen the transcript for the planner.
- **Risk:** choice 2 changes when the alarm fires. The guard would then run after the alarm, so only the planner's view of the transcript stays screened.

### (e) Presence follows the largest box

- **Case:** two people in frame with boxes of about the same size, for example a presenter standing next to the person lying down.
- **Now:** `tracker.py:23-28` picks the largest box each frame. The tracked center jumps half the frame, so the state stays `moving` and never `still`, and no fall_hint is sent. A bigger person walking in reads as a stand-up.
- **Choices:**
  1. Keep it and keep presenters out of frame.
  2. Follow the box nearest the last tracked one.
- **Risk:** choice 1 depends on stage discipline. Choice 2 changes presence behavior late and needs the real camera to test.

### (f) Lines that promise help

- **Case:** the spoken and written lines after an alarm.
- **Now:** `reply_help` says "I'm getting help now". `ask_retry_3` says "I'll get help". The hub and agent READMEs and `handoff.py:30` call the note "a note for responders". In the demo only a family contact is reached, and with Twilio unset nobody is.
- **Choices:**
  1. Keep them.
  2. Reword to name the contact, for example "I'm alerting your contact now" and "a note for your contact".
- **Risk:** choice 1 can read as a promise of emergency help. Choice 2 changes spoken lines and any test that checks them.

### (g) Dashboard ranking misses some events

- **Case 1:** a help sign or fall_hint ends in an alarm with no quake first.
- **Now:** `boxHitAt` is set only by the quake wave (`app.js:154`), so H000 never ranks (`app.js:187`). Rank says "Not hit", the queue says "No event yet".
- **Case 2:** a second quake after the first wave ends.
- **Now:** `startQuake` returns while `quake` is set (`app.js:136`), so it is ignored until reset. The home screen shows it.
- **Choices:**
  1. Keep it and always press `r` between takes.
  2. Rank H000 on any alarm or check-in, and start a new wave for a quake after the first wave ends.
- **Risk:** choice 2 touches ranking and the wave, which the map beat depends on.

### (h) "Demo only, no real call." on the dashboard

- **Case:** the `TWILIO_*` variables are set.
- **Now:** `dashboard/app.js:405, :915` show "Demo only, no real call." while the agent places a real call to the teammate's phone.
- **Choice:** reuse the home screen's line, "Demo alarm. No emergency number is called." (`home/state.js:87`), which is true either way.
- **Risk:** low. One UI string.

### (i) docs/ rule breaks

- **Case:** owner notes in `docs/`.
- **Now:** 141 lines with a middle dot across 35 files, and 45 lines with an em dash. The lists are `/private/tmp/claude-501/-Users-geovponce--t3-worktrees-hackutd-26-fresh-eyes-review/688099e6-6e30-40a7-ba7d-938d076aaeba/scratchpad/docs/middle-dots.txt` and `em-dashes.txt` in the same folder. `docs/tracks/HackUTD-Research-Track-Axxess.md:46` has `"fall detected 14:02,"` and `:64` has "Fall detection from one camera". `docs/lifeline/HackUTD-Lifeline-Agent.md:51, :183` and `HackUTD-Lifeline-Plan.md:52, :64` describe a dispatch flow.
- **Choices:** edit them, or leave them as private notes. No edit was made because these are owner notes.
- **Risk:** only matters if judges open `docs/`.

### (j) Hub drop and late answers

- **Case 1:** the hub drops mid check-in.
- **Now:** messages are dropped while disconnected, the alarm is raised where no screen sees it, and after reconnect the agent ignores every trigger until reset.
- **Case 2:** a voice answer arrives after the 21 s wait.
- **Now:** `heard` carries no try id, so the late answer counts for the next try. A "help" can be lost.
- **Choices:**
  1. Keep both and restart the whole loop if the hub drops.
  2. Re-send the current check-in state on reconnect, and tag each `say` and `heard` with a try id.
- **Risk:** choice 2 changes the bus contract (#19) and three services.

### (k) Home help-sign note promises a repeat

- **Case:** the home Security view, help sign tile.
- **Now:** `home/views/security.js:55` says "The camera repeats it while the sign is held". That only happens on pi-integration. On main, only sim key `h` sends `help_gesture`, once per press.
- **Choices:**
  1. Keep it, since pi-integration will land.
  2. Reword it on main until pi-integration lands.
- **Risk:** choice 1 is a false line if main is shown. Choice 2 is one UI string to change back later.

### (l) H000 "Cleared" vs home "No response"

- **Case:** nobody home, an event, no answer.
- **Now:** for the same check-in, the dashboard H000 shows "Cleared" and the home Alerts list shows "No response".
- **Choices:**
  1. Keep both.
  2. Use one word on both screens.
- **Risk:** choice 1 shows two screens that disagree on camera. Choice 2 is a UI string on one screen.

### (m) "All okay at home" with an official alert and nobody home

- **Case:** an official alert is active, nobody is home, and nobody answers. PR #81 (draft) sends `checkin clear` on this path.
- **Now:** with #81, home ends on "All okay at home. Official alert active." though nobody said okay.
- **Choices:**
  1. Keep it.
  2. Show a line for the nobody path that does not say okay.
- **Risk:** choice 1 tells a viewer the home is okay with no answer. Choice 2 adds a home state and its tests. #81 stays a draft until the owner picks.

### (n) Reset does not cancel speech or listening calls

- **Case:** reset while the box speaks or listens.
- **Now:** PR #80 stops the line in flight, the tone and the listen. A TTS or STT call already in progress is not cancelled.
- **Choices:**
  1. Keep it.
  2. Cancel the engine call on reset.
- **Risk:** choice 1 leaves the call running after a reset. Choice 2 touches each voice engine.

## 5. Demo notes

- Reset sets the agent's presence to "none" (`checkin.py:186`). After every reset, the panel must send "Someone is home" before the next event, or the agent decides "nobody detected, no alarm".
- The help-sign sender from the camera lives only on the pi-integration branch. On main, only sim key `h` sends `help_gesture`.
