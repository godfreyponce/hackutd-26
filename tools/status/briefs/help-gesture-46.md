# Brief: help-gesture-46 (issue #46)

Thread name "#46 help_gesture: agent asks at once". Branch issue-46-help-gesture from origin/main. Status file name help-gesture-46.

## Goal
Owner OK 10:40 PM. Rafael's hardware/vision/posture.py (branch vision-posture, line ~247) sends {"type": "help_gesture"} to the hub when it sees the HELP sign. Make that start a check-in at once. Read `gh issue view 46`.

## Scope
1. Hub (software/hub): it already passes any type through. Add help_gesture to the README message contract. Add a sim key (see sim.py and hub.send) so the demo can show it without the camera. Test.
2. Agent (software/agent, checkin.py ~line 137 routes quake/fall_hint): help_gesture starts a check-in at once, with no wait for a still period. It asks first ("Do you need help?" style; add a script line in scripts.py if one fits, plain words). It never raises the alarm by itself: after the ask, the normal alarm rule decides (nobody there + no answer = no alarm; someone there + no answer = alarm; "help" = alarm; "I'm okay" = log only). Use the existing guard so repeated gestures do not stack check-ins. The hand-off note and why-lines must not say "fall" or "radar" (existing check). Tests first.
3. Dashboard and home (software/web): show the event as one plain line, for example "Help sign seen". No other UI change. Tests.
Out of scope: people.down, camera_shake, lights, any hardware/ edit. Do not touch posture.py.

Note: the "UI polish council" thread (branch issue-40-ui-polish, PR #45) is also editing software/web/dashboard and home. Keep web edits small and merge origin/main before you finish.

## Rules 
- Team repo godfreyponce/hackutd-26, product LAND, a demo home safety box. Owner Godfrey owns software/. Rafael (GitHub rafael-amador) owns hardware/: do not edit hardware/. Hacking ends Sun 12:00 PM CT; it is Sat about 10:45 PM. Your coordinator is the thread "HackUTD build coordinator 4".
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
