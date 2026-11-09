# Brief: #51 home heat bar overlaps "Indoor temperature" subtitle

Status file name: heat-overlap-51. Branch issue-51-heat-overlap, worktree from origin/main (4f30b17 or newer). Coordinator: "HackUTD build coordinator 6" (threadId mcp:6d12986d-12e1-4ffe-99ff-36dbe5ebf066). Report to it with one message when done: head SHA, test counts, screenshot paths, owner push + PR commands.

## Task (owner OK 12:10 AM, fix only)
On the home screen (software/web/home), with the alert banner showing, the heat scale bar draws over the "Indoor temperature" subtitle: about 6 px at 1280x800, 9 to 16 px at 1280x720 and 1366x768 (also on main at 720 and 768). Cause per the #45 reviewer: the banner grew (`.what` min 24px, `.headline` min 22px, home/index.html:117-118) and `.heat-body` is bottom-aligned with no min height (index.html:206). Bug screenshots: /private/tmp/claude-501/-Users-geovponce-Developer-hackutd-26/f2dc3f6f-be57-490e-8fb4-f7b750dd0191/scratchpad/ev-pr-1280.png and crop-pr.png.

The venue monitor is unknown. It must not overlap at 1280x720, 1280x800, 1366x768, 1920x1080 and 2560x1440, banner on AND off. Keep the look otherwise the same: no new UI, no wording change, no layout change beyond what the fix needs. If a clean fix needs a visible change (for example a smaller banner or hiding the subtitle at small heights), stop and tell the coordinator in plain words first.

Done means: a headless check (Playwright or similar, your own hub on a spare port or a static load with injected state) that measures the subtitle box vs the heat bar box at each of the 5 sizes, banner on and off, and fails on overlap. Red on main first, then green. Save before/after screenshots at each size to your scratchpad and list the paths. Home, dashboard and hub suites pass. Reviewer subagent clean (give it the no-pkill rule). Commit (no trailer). Owner gets push + `gh pr create --base main` commands (body "Closes #51").

## Rules (every thread)
- Team repo godfreyponce/hackutd-26, product LAND, a demo home safety box. Owner Godfrey owns software/. Rafael (GitHub rafael-amador) owns hardware/: do not edit hardware/. Hacking ends Sun 12:00 PM CT; it is Sun about 12:25 AM.
- Commits carry NO Claude co-author trailer and no "Generated with" line (team rule). You cannot push (the owner's hook blocks it). When done, give the owner the push command and a `gh pr create --base main` command (body says "Closes #N"), each alone in its own ```bash fence, one command line per fence.
- Status file: write ~/Developer/hackutd-26/tools/status/threads/<name>.json (name given above) at start and on every state change. Format in ~/Developer/hackutd-26/tools/status/README.md, section "Thread status files". Write a tmp file then mv. States working|blocked|needs-owner|done. Do not commit status files.
- Do not start anything on ports 8765 or 8080 (the live demo loop runs there). Use port 0 in tests.
- Tests are the success criterion: write them first, run the full suite of every package you touch before you finish, and show raw output. Python venv: python3.12 .venv in your worktree (see other worktrees under /Users/geovponce/.t3/worktrees/hackutd-26/ for setup, e.g. issue-15/.venv). JS tests: see software/web/dashboard/package.json and the home tests.
- Before you report done, run a separate reviewer subagent on your diff and fix what it finds.
- Anything NEW beyond this scope (another UI change, a new feature, a contract change) needs the owner's OK: tell the coordinator plainly and wait.
- Token cost is not a concern for this hackathon (owner rule 9:32 PM, restated 12:30 AM: no 5-hour limit, spend freely on extra and second-opinion reviewers, councils, parallel threads, read subagents). Pass this rule on to any thread or agent you launch. Hand off to a fresh session if your context gets too full to work well.
- Wording: plain short sentences, no em dashes, never a middle dot as a separator. Say "no response after an event", never "fall detection" (fall_hint is an internal message name only). The alarm is fake; nothing ever calls 911. Keys only via request_secret; never print a key.
- Never pkill or killall by module or name (HQ rule 11:05 PM). Kill only PIDs you started yourself, by PID. Never touch the 8765/8080 hub, agent or voice.
