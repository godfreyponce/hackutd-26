# Brief: header-mark-56 (issue #56)

Thread name: '#56 header mark only'. Status name: header-mark-56. Branch issue-56-header-mark from origin/main. Report to "HackUTD build coordinator 7".

## Task (owner approved, 1:35 AM)
The dashboard header shows the stacked LAND mark AND the word "LAND" next to it, so it reads as two logos.
- Dashboard: software/web/dashboard/index.html:12. Keep the square mark (img.mark). Drop the bare word "LAND". Keep the subtitle "Richardson, TX, 500 homes". Set the mark's alt="LAND" (it is alt="" today) so screen readers still get the name.
- Home: software/web/home/index.html:318-323 pairs the mark with div#product-name (filled by app.js:20 with PRODUCT_NAME) above "Home safety monitor". Apply the same: keep the mark, drop the product-name word, keep "Home safety monitor", mark alt="LAND". Remove the app.js line that fills product-name only if nothing else needs it; check tests that read product-name or PRODUCT_NAME and update them honestly. Keep the document <title> as it is.
- Fix spacing so the header still looks balanced (mark + subtitle aligned, no empty gap where the word was). Smallest change that works. Nothing else in the UI changes.
- Screenshots for the owner, before and after, both headers, at 1920x1080 and 1280x720, using your own --sim hub on spare ports (pick ports in 19500-19599, check they are free). Stop your processes by PID.
- Run home, dashboard and hub suites. Run a separate reviewer subagent on the diff. Commit with no trailer, then send the coordinator the screenshot paths and the owner push + gh pr create commands (body "Closes #56").
- Other branches also touch these files (#52 home screens on home/index.html, #53 on dashboard, #54 on home/index.html). Keep the diff tight so merges stay easy. Do not merge; the coordinator merges after the filming take.

## Rules (every thread)
- Team repo godfreyponce/hackutd-26, product LAND, a demo home safety box. Owner Godfrey owns software/. Rafael (GitHub rafael-amador) owns hardware/: do not edit hardware/. Hacking ends Sun 12:00 PM CT; it is Sun about 1:05 AM.
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
