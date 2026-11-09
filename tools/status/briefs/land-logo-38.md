You are the build thread for issue #38 "LAND logo everywhere". Branch issue-38-land-logo (your worktree, from origin/main). Status file name: land-logo-38. The owner asked for this at 10:13 PM (via HQ) and approved it.

## Context
The logo is the settled LAND "Horizon Cut" mark. Files on main in docs/brand/: land-mark-navy.svg, land-mark-white.svg, land-wordmark-navy.svg, land-wordmark-white.svg, land-wordmark-print.svg, land-favicon-16.svg. The home screen and dashboard already use it (PR #33; see software/web/brand/ and how software/web/home and software/web/dashboard reference it). Copy their approach; do not redesign the mark.

## Goal
1. software/web/index.html (the hub landing page the hub serves on :8080; see software/hub/web.py for what it serves and from where): the title still says "Home Safety Box". Make it LAND, add the favicon, and show the mark or wordmark like home and dashboard do.
2. README.md at the repo root: put the LAND wordmark at the top with a <picture> and prefers-color-scheme sources, so navy shows on light GitHub and white on dark (img fallback navy). Use repo-relative paths to docs/brand/.
3. PNG exports in docs/brand/: a GitHub social preview 1280x640 (land-social-1280x640.png) and a Devpost thumbnail at 3:2 (land-devpost-1500x1000.png or similar 3:2 size). Render from the SVGs (rsvg-convert, cairosvg, or a headless browser; whatever is installed or brew-installable). Keep generous margins: GitHub crops the social preview edges. Look at the PNGs yourself (Read the image) before committing. Add a small script or a README line that says how they were made, so they can be redone.
4. Any other software/ screen or doc page that shows a product name or tab icon and lacks the logo: add it (check software/web, the dashboard README, docs pages a judge would open). List what you changed and what you skipped.
Do NOT touch hardware/ (Rafael owns it). If Rafael's hardware/vision/posture.py monitor window should show LAND, do not edit it; tell the coordinator and it will ask the owner about a suggestion for Rafael.

## Tests
Home and dashboard test suites and the hub suite still pass (hub tests may check what web.py serves). If the hub serves the landing page, add or extend a hub test that the page at / says LAND and links the favicon. Show raw output.
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

- Never pkill or killall by module or name (HQ rule 11:05 PM). Kill only PIDs you started yourself, by PID. Never touch the 8765/8080 hub, agent or voice.
