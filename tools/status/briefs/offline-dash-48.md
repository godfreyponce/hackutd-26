# Brief: #48 offline dashboard shows "--"

Status file name: offline-dash-48. Branch issue-48-offline-dash. Worktree from origin/issue-40-ui-polish (head ee70850, PR #45 not merged yet). Before your PR, `git fetch origin && git merge origin/main` (PR #45 will likely be merged by then). Coordinator: "HackUTD build coordinator 5". Report to it.

## Task (owner OK 11:41 PM)
When the hub is offline, software/web/dashboard shows "--" in place of the counters and the box card values (today it keeps the last numbers and mutes them, see app.js ~269-275 and style.css 63-69 offline rules). When the hub reconnects, real values come back on the next state message. Keep the existing offline look (amber pill, gray map, muted card). Home is unchanged. Do not change the "NEARBY 60 OF 500" wording. Nothing else new.

Done means: a dashboard test that goes red first (offline status shows "--" in every counter and box card value; connected status shows real values again), then green; dashboard, home and hub suites pass; headless check with your own hub on a spare port shows "--" offline and values after reconnect, no console errors; reviewer subagent clean; commit (no trailer); owner gets push + `gh pr create --base main` commands (body "Closes #48").

## Rules (every alert thread)
- Team repo godfreyponce/hackutd-26, product LAND, a demo home safety box. Owner Godfrey owns software/. Rafael (GitHub rafael-amador) owns hardware/: do not edit hardware/. Hacking ends Sun 12:00 PM CT; it is Sat about 11:45 PM. Your coordinator is the thread "HackUTD build coordinator 5".
- Commits carry NO Claude co-author trailer and no "Generated with" line (team rule). You cannot push (the owner's hook blocks it). When done, give the owner the push command and a `gh pr create --base main` command (body says "Closes #N"), each alone in its own ```bash fence, one command line per fence.
- Status file: write ~/Developer/hackutd-26/tools/status/threads/<name>.json (name given above) at start and on every state change. Format in ~/Developer/hackutd-26/tools/status/README.md, section "Thread status files". Write a tmp file then mv. States working|blocked|needs-owner|done. Do not commit status files.
- Do not start anything on ports 8765 or 8080 (the live demo loop runs there). Use port 0 in tests.
- Tests are the success criterion: write them first, run the full suite of every package you touch before you finish, and show raw output. Python venv: python3.12 .venv in your worktree (see other worktrees under /Users/geovponce/.t3/worktrees/hackutd-26/ for setup, e.g. issue-15/.venv). JS tests: see software/web/dashboard/package.json and the home tests.
- Before you report done, run a separate reviewer subagent on your diff and fix what it finds.
- Anything NEW beyond this scope (another UI change, a new feature, a contract change) needs the owner's OK: tell the coordinator plainly and wait.
- Token cost is not a concern for this hackathon (owner rule 9:32 PM): use subagents and reviewers freely. Pass this rule on to any thread you launch. Hand off to a fresh session if your context gets too full to work well.
- Wording: plain short sentences, no em dashes, never a middle dot as a separator. Say "no response after an event", never "fall detection" (fall_hint is an internal message name only). The alarm is fake; nothing ever calls 911. Keys only via request_secret; never print a key.

- Never pkill or killall by module or name (HQ rule 11:05 PM). Kill only PIDs you started yourself, by PID. Never touch the 8765/8080 hub, agent or voice.
