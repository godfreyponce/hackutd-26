You are the build thread for issue #37 "SAME demo alert: make_same, same_to_alert, live decoder (multimon-ng)". Branch issue-37-same-demo (your worktree, from origin/main). Status file name: same-demo-37. The owner approved this plan at 9:55 PM.

## Demo this serves
1. A few seconds of the live NOAA radio (KEC56, 162.400 MHz) through Rafael's SDR (hardware/radio/noaa.sh, his part).
2. We explain faking an alert over the air is illegal, so we don't.
3. A phone plays our locally made SAME earthquake file (EQW, station HACKDEMO, marked demo) into the Pi audio input by cable (USB audio adapter with mic input; Pi 5 has no line-in). The real decoder picks it up live, the hub gets an `alert`, the home screen shows the overlay, the agent starts the check-in.

## Decoder: multimon-ng, not samedec
Rafael's receiver uses `multimon-ng -t raw -a EAS -` on 22050 Hz signed 16-bit mono (read hardware/radio/noaa.sh). Use the same decoder so one parser serves the live radio and the cable. On the Mac: `brew install multimon-ng`. multimon-ng prints lines like `EAS: ZCZC-WXR-EQW-048113-048085+0030-3112300-HACKDEMO-` (check the real output format and how it reports repeats and NNNN end-of-message).

## Goal (new package, suggest software/same/; run from the repo root with the hub venv)
1. make_same.py: writes a SAME message (header 3 times with 1 s gaps, attention tone, a short spoken-free gap or tone, EOM NNNN 3 times) as a WAV (for the phone) and optionally raw. Default header: EQW, counties 048113 and 048085, +0030, current JJJHHMM, station HACKDEMO. Base it on Script 2 in docs/research/HackUTD-SDR-Alerts.md (preamble 16 x 0xAB, LSB first, AFSK 2083.3/1562.5 Hz, 520.83 baud), but it MUST decode with multimon-ng -a EAS (the doc only tested samedec). Commit one ready demo WAV (small) for the phone.
2. same_to_alert.py: reads multimon-ng output lines on stdin, parses each ZCZC header itself, de-duplicates the 3 repeats, drops headers for other counties unless national (keep 048113, 048085 and national), and sends one hub `alert` per message with the shared contract below (source "noaa", event readable name, code, station, area, CAP-like severity/urgency/certainty per the doc's table, demo true when station is HACKDEMO or code is DMO, plain headline). Use software.hub.send (or the hub client the doc uses). A --dry-run flag prints the JSON instead.
3. listen.sh: live wrapper: `arecord` from an ALSA device (flag, default the USB adapter, list with `arecord -l`) at 22050 Hz S16_LE mono | multimon-ng -t raw -a EAS - | same_to_alert.py. Also a --file mode that decodes a WAV through the same chain (sox to raw), and a Mac mode using sox's default input. Also accept stdin so Rafael's `noaa.sh decode` output can feed same_to_alert.py for real alerts.
4. README in the package: Pi steps (USB adapter, cable, phone volume, `arecord -l`), Mac steps, and the never-transmit, never-play-aloud rule.

## Tests
Parser unit tests (sample multimon lines, dedupe, county filter, national, demo flag, field mapping). End-to-end: make_same.py -> sox/raw -> multimon-ng -> same_to_alert.py -> a real hub on port 0 receives exactly one alert with code EQW, station HACKDEMO, demo true (skip with a clear message if multimon-ng is missing). Run the hub suite too.

Other threads in parallel: #35 (hub adds `level`, screens), #36 (agent). Do not edit software/hub (except reading it), software/agent, software/web, or hardware/.

## Shared alert contract (all three alert threads use this exactly)
A hub `alert` message keeps the CAP fields in software/hub/README.md (type, source, event, severity, urgency, certainty, area, headline) and adds:
- `code`: SAME event code, e.g. "EQW", "TOR", "SVR", "RWT". Optional for old senders.
- `station`: sender id, e.g. "HACKDEMO" for our demo file, "KEC56" or "KFWD/NWS" for real ones. Optional.
- `distance_mi`: number, optional. Miles from the home to the event.
- `demo`: true for our locally made demo alerts and the simulator. The headline stays plain (no prefix); screens and speech add "DEMO, not a real alert." when demo is true.
- `level`: added by the HUB before it broadcasts (software/hub/alert_level.py, issue #35). Senders do not set it. Table: tests (RWT, RMT, NPT, DMO) info; watches (code ends in A) watch; other warnings warning; EQW, TOR, CEM, CAE, EVI, SPW emergency; distance_mi > 25 drops one step (not below info). Unknown or missing code falls back to CAP severity (Extreme emergency, Severe warning, Moderate watch, else info).

## Rules (every alert thread)
- Team repo godfreyponce/hackutd-26, product LAND, a demo home safety box. Owner Godfrey owns software/. Rafael (GitHub rafael-amador) owns hardware/: do not edit hardware/. Hacking ends Sun 12:00 PM CT; it is Sat about 10:10 PM. Your coordinator is the thread "HackUTD build coordinator 3".
- Commits carry NO Claude co-author trailer and no "Generated with" line (team rule). You cannot push (the owner's hook blocks it). When done, give the owner the push command and a `gh pr create --base main` command (body says "Closes #N"), each alone in its own ```bash fence, one command line per fence.
- Status file: write ~/Developer/hackutd-26/tools/status/threads/<name>.json (name given above) at start and on every state change. Format in ~/Developer/hackutd-26/tools/status/README.md, section "Thread status files". Write a tmp file then mv. States working|blocked|needs-owner|done. Do not commit status files.
- Do not start anything on ports 8765 or 8080 (the live demo loop runs there). Use port 0 in tests.
- Tests are the success criterion: write them first, run the full suite of every package you touch before you finish, and show raw output. Python venv: python3.12 .venv in your worktree (see other worktrees under /Users/geovponce/.t3/worktrees/hackutd-26/ for setup, e.g. issue-15/.venv). JS tests: see software/web/dashboard/package.json and the home tests.
- Before you report done, run a separate reviewer subagent on your diff and fix what it finds.
- Anything NEW beyond this scope (another UI change, a new feature, a contract change) needs the owner's OK: tell the coordinator plainly and wait.
- Token cost is not a concern for this hackathon (owner rule 9:32 PM): use subagents and reviewers freely. Pass this rule on to any thread you launch. Hand off to a fresh session if your context gets too full to work well.
- Wording: plain short sentences, no em dashes, never a middle dot as a separator. Say "no response after an event", never "fall detection" (fall_hint is an internal message name only). The alarm is fake; nothing ever calls 911. Keys only via request_secret; never print a key.
- Over-the-air rule: we never transmit anything. The SAME demo file is only for an audio cable into the Pi input. Never play it out loud at the venue (47 CFR 11.45 bans simulated EAS tones).

- Never pkill or killall by module or name (HQ rule 11:05 PM). Kill only PIDs you started yourself, by PID. Never touch the 8765/8080 hub, agent or voice.
