You are the build thread for issue #36 "Agent: EQW emergency alert starts a check-in". Branch issue-36-agent-alert (your worktree, from origin/main). Status file name: agent-alert-36. The owner approved this plan at 9:55 PM.

## Goal
In software/agent (read README.md, checkin.py, rule.py, scripts.py, tests first): today the agent stores an `alert`. Add: an alert with code "EQW" and level "emergency" (level is added by the hub, see the contract below) starts a check-in the same way an event does, using the ask_event line (check scripts.py for the exact name). Any other alert (other codes, or EQW at a lower level, or missing level) is only stored, as today. Ignore the alert trigger if any incident started in the last 300 s: add Incident.started_at (checkin.py near lines 82, 135, 180; check current lines), and make 300 a named constant. If the alert has demo true, any line the agent speaks or writes about the alert must make clear it is a demo ("DEMO, not a real alert."). Do not change the alarm rule (nobody there + no answer = no alarm; someone there + no answer = alarm; "help" = alarm; "I'm okay" = log only). The alarm is fake and never calls 911.

## Tests
software/agent/tests/test_checkin.py: EQW emergency starts a check-in; EQW warning does not; TOR warning does not; second EQW within 300 s of an incident start is ignored; after 300 s it works again; demo wording. Run the whole agent suite.

Other threads in parallel: #35 (hub adds `level`, home and dashboard), #37 (SAME scripts). Do not edit software/hub or software/web; in tests, build the alert messages with `level` set yourself.

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
