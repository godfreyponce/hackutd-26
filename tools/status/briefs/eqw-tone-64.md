# Brief: eqw-tone-64 (issue #64)

Thread name: '#64 EQW warning tone'. Status file name: eqw-tone-64. Branch issue-64-eqw-tone from origin/main (main is 1c958e2). Report to "HackUTD build coordinator 8" (threadId mcp:d5b5f74a-1ab5-4bbe-b760-aebd7b7f906a).

## Task (owner approved 2:55 AM CST)
When the box gets an earthquake warning (an EQW emergency alert, see ALERT_TRIGGER in software/agent/checkin.py and the forced line in software/agent/scripts.py), it plays a short warning tone BEFORE it speaks the ask.
- The tone is short (about 1 s or less) and is NOT the real Emergency Alert System tones (no 853+960 Hz two-tone, no 1050 Hz NWS tone, no SAME header bursts). Pick something plainly different, for example a few short beeps at one pitch. Generate it in code or ship a tiny WAV; say which and why.
- Only the EQW alert check-in gets the tone. Quake shake, stillness, heat, scream and other triggers do not.
- The fake alarm siren stays only at the final alarm. Do not reuse it here.
- Find how the voice service already plays the alarm siren (software/voice) and how the agent asks voice to speak; reuse that path. Keep the bus message contract backward compatible (an older voice service must still speak the ask). If the contract must grow, say exactly how in your report.
- Works in offline mode and in --text mode (text mode may print a marker instead of sound).
- Tests first: a test that the EQW check-in asks voice for the tone before the ask, and a test that other triggers do not. Voice side: a test that the tone request plays before the line.
- Rafael's branch origin/pi-integration also edits software/agent/checkin.py (new heat and scream triggers). Run `git merge-tree --write-tree origin/main origin/pi-integration` style checks against your branch and report any conflict. Do not edit hardware/.

## Done when
Full suites of every package you touch pass (agent, voice, hub; show raw output). A separate reviewer subagent ran on your diff and you fixed what it found. Committed on issue-64-eqw-tone, not pushed. You send the coordinator the SHA, test counts, how it sounds (describe the tone), and the owner push + PR commands. The merge waits for the filming take.

## Rules (every thread)
- Team repo godfreyponce/hackutd-26, product LAND, a demo home safety box. Owner Godfrey owns software/. Rafael (GitHub rafael-amador) owns hardware/: do not edit hardware/. Hacking ends Sun 12:00 PM CT; it is Sun about 2:58 AM CST.
- Commits carry NO Claude co-author trailer and no "Generated with" line (team rule). You cannot push (the owner's hook blocks it). When done, give the owner the push command and a `gh pr create --base main` command (body says "Closes #N"), each alone in its own ```bash fence, one command line per fence.
- Status file: write ~/Developer/hackutd-26/tools/status/threads/<name>.json (name given above) at start and on every state change. Format in ~/Developer/hackutd-26/tools/status/README.md, section "Thread status files". Write a tmp file then mv. States working|blocked|needs-owner|done. Do not commit status files.
- Do not start anything on ports 8765 or 8080 (the live demo loop runs there). Use port 0 in tests.
- Tests are the success criterion: write them first, run the full suite of every package you touch before you finish, and show raw output. Python venv: python3.12 .venv in your worktree (see other worktrees under /Users/geovponce/.t3/worktrees/hackutd-26/ for setup, e.g. issue-15/.venv). JS tests: see software/web/dashboard/package.json and the home tests.
- Before you report done, run a separate reviewer subagent on your diff and fix what it finds.
- Anything NEW beyond this scope (another UI change, a new feature, a contract change) needs the owner's OK: tell the coordinator plainly and wait.
- Token cost is not a concern for this hackathon (owner rule 9:32 PM, restated 12:30 AM: no 5-hour limit, spend freely on extra and second-opinion reviewers, councils, parallel threads, read subagents). Pass this rule on to any thread or agent you launch. Hand off to a fresh session if your context gets too full to work well.
- Wording: plain short sentences, no em dashes, never a middle dot as a separator. Say "no response after an event", never "fall detection" (fall_hint is an internal message name only). The alarm is fake; nothing ever calls 911. Keys only via request_secret; never print a key.
- Never pkill or killall by module or name (HQ rule 11:05 PM). Kill only PIDs you started yourself, by PID. Never touch the 8765/8080 hub, agent or voice.
- Wording for results: "no response after an event", never "fall detection". The judge line is: "We don't bet on spotting the fall. A wrong guess costs one question. The alarm needs an event, a person in the room, and no answer three times." The alarm is fake and never calls 911.
