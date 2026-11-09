# Brief: #52 home side screens (Alerts, Disasters, Security, System)

Status file name: home-screens-52. Branch issue-52-home-screens, worktree from origin/main (a25a1f7 or newer). Coordinator: "HackUTD build coordinator 6" (threadId mcp:6d12986d-12e1-4ffe-99ff-36dbe5ebf066). Report to it with t3_thread_send.

## Task (owner YES 12:50 AM: "add those really quick, since we have the time... spin up subagents, matching it with similar UI")
The home nav buttons Alerts, Disasters, Security, System are dead href="#" links (software/web/home/index.html:337-345). Build four real screens in the same LAND home UI style (same fonts, colors, cards, nav, header, footer). Web only (software/web/home). Read-only views of data the hub ALREADY sends (see software/web/home/state.js reduce cases: quake, fall_hint, help_gesture, checkin, say, heard, alert, power, heartbeat, queue, reset, presence etc., and the hub contract in software/hub). No new hub messages, no changes in software/hub, software/agent, software/voice, software/web/dashboard.

Starting scope (refine if the data says otherwise, keep it honest):
- Alerts: log of NOAA/EQW alerts and check-ins with their outcomes (okay, no response, contacting help), newest first, with times.
- Disasters: the active quake or hazard, with location, magnitude or level, and status; history of earlier ones this session.
- Security: presence and camera state (moving, still, nobody there) and the last event.
- System: hub, agent, voice and sensor heartbeat and battery, online or offline, last seen times.
Every screen shows "--" or an honest empty state ("No alerts yet") when there is no data. Never invent data. Overview stays exactly as it is today (pixel-identical at 1920x1080). The target is the 1920x1080 box monitor; also check 2560x1440 and 1280x720 do not break.

Architecture: keep one page and one WebSocket so history survives switching screens (hash routes like #alerts, or similar). State and history live in state.js as pure functions with node tests. The nav marks the active screen. Suggested plan: first build the routing shell and the shared history in state.js yourself, then run four subagents in parallel, one per screen, each in its own view file and CSS block, then a UI council (2 or 3 reviewer subagents scoring look and fit against Overview) and fix what they find. Wording follows the Rules below.

Done means: state.js tests first (red then green) for the new history; home, dashboard and hub suites pass; a headless check with your own hub in --sim mode on SPARE ports (never 8765/8080) sends real events (quake, alert, presence, help_gesture, checkin outcomes, power, offline hub) and screenshots each screen at 1920x1080 in empty and filled states, no console errors; screenshots saved to your scratchpad with paths listed (the owner sees them before merge); two separate reviewer subagents clean; `git merge origin/main` before the PR (#51 also touches home/index.html); commit (no trailer). Owner gets push + `gh pr create --base main` commands (body "Closes #52"). Do NOT merge: the coordinator merges after the filming take is done.

## Rules (every thread)
- Team repo godfreyponce/hackutd-26, product LAND, a demo home safety box. Owner Godfrey owns software/. Rafael (GitHub rafael-amador) owns hardware/: do not edit hardware/. Hacking ends Sun 12:00 PM CT; it is Sun about 12:55 AM.
- Commits carry NO Claude co-author trailer and no "Generated with" line (team rule). You cannot push (the owner's hook blocks it). When done, give the owner the push command and a `gh pr create --base main` command (body says "Closes #N"), each alone in its own ```bash fence, one command line per fence.
- Status file: write ~/Developer/hackutd-26/tools/status/threads/<name>.json (name given above) at start and on every state change. Format in ~/Developer/hackutd-26/tools/status/README.md, section "Thread status files". Write a tmp file then mv. States working|blocked|needs-owner|done. Do not commit status files.
- Do not start anything on ports 8765 or 8080 (the live demo loop runs there). Use port 0 in tests.
- Tests are the success criterion: write them first, run the full suite of every package you touch before you finish, and show raw output. Python venv: python3.12 .venv in your worktree (see other worktrees under /Users/geovponce/.t3/worktrees/hackutd-26/ for setup, e.g. issue-15/.venv). JS tests: see software/web/dashboard/package.json and the home tests.
- Before you report done, run a separate reviewer subagent on your diff and fix what it finds.
- Anything NEW beyond this scope (another UI change, a new feature, a contract change) needs the owner's OK: tell the coordinator plainly and wait.
- Token cost is not a concern for this hackathon (owner rule 9:32 PM, restated 12:30 AM: no 5-hour limit, spend freely on extra and second-opinion reviewers, councils, parallel threads, read subagents). Pass this rule on to any thread or agent you launch. Hand off to a fresh session if your context gets too full to work well.
- Wording: plain short sentences, no em dashes, never a middle dot as a separator. Say "no response after an event", never "fall detection" (fall_hint is an internal message name only). The alarm is fake; nothing ever calls 911. Keys only via request_secret; never print a key.
- Never pkill or killall by module or name (HQ rule 11:05 PM). Kill only PIDs you started yourself, by PID. Never touch the 8765/8080 hub, agent or voice.
