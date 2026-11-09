You are the build thread for issue #35 "Alert levels: hub level + home and dashboard overlay". Branch issue-35-alert-level (your worktree, from origin/main). Status file name: alert-level-35. The owner approved this plan at 9:55 PM.

## Goal
1. Hub: new software/hub/alert_level.py with a pure function that maps an alert to its level (table below). The hub adds `level` to every `alert` message before it broadcasts it. Read software/hub/README.md, __main__.py, bus.py, sim.py first. Update the README contract with the new fields. Change sim.py's `a` key alert to carry code "EQW", station "HACKDEMO", demo true, distance_mi a small number (e.g. 3), and a plain headline (move its "DEMO ONLY..." prefix out; the screens add the demo prefix now).
2. Home screen (software/web/home: index.html banner ~line 347, state.js ~89-100, app.js ~396-406, check current lines): the alert banner gets a `data-level` attribute and colors per level (info, watch, warning, emergency). When demo is true, the banner text starts with "DEMO, not a real alert.". Banner time to live: info 2 min, watch 30 min, warning and emergency until reset. A lower level never replaces a higher one that is still showing. The home status word stays driven by the check-in, not by the alert. Keep the LAND look; colors must read well on the portable monitor. This is a UI change the owner approved in this plan; nothing beyond it.
3. Dashboard (software/web/dashboard): the event line for an alert shows its level (and the demo prefix when demo is true). Small change only.

## Tests
software/hub/tests/test_alert_level.py (whole table, distance step-down, unknown code fallback, hub adds level on broadcast, against a real hub on port 0 like the other hub tests). state.test.js for home (level, TTL, no downgrade, demo prefix). Dashboard tests still pass. Run hub, home and dashboard suites.

Other threads in parallel: #36 (agent reads `level` and `code`), #37 (SAME scripts send alerts with code/station/demo). Do not edit software/agent or the SAME scripts.

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
