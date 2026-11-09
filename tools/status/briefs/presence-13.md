You are the fresh build thread for issue #13 camera presence (software/presence), taking over from the thread "#13 camera presence: software/presence" whose context filled. Worktree /Users/geovponce/.t3/worktrees/hackutd-26/issue-13-presence, branch issue-13-presence, last commit 4883d0f (194 tests passed). Status file name: presence-13.

## Owner decision (10:17 PM): pick (b), fixes 1 to 3 YES
Rafael's hardware/vision/posture.py (on main) will print one JSON line per frame `{"t": seconds, "boxes": [[x0,y0,x1,y1,score], ...]}` (fractions of the frame) and pipe into `python -m software.presence --stdin`, run with no --hub. His stdout may also carry lines starting with `EVENT {...}`: those must be skipped quietly (check they are). The ask is posted on #13.

Build these 3 tracker fixes (tests first, each number a named constant):
1. Call it moving only when 2 or more frames in the last second show the motion. One noisy frame must not flip still to moving (that reads as a false stand-up in software/agent/checkin.py).
2. Clear the 60 s fall_hint cooldown when a `reset` appears on the bus, so a demo right after a reset still gets a check-in.
3. Wait 60 s (was 20 s) after still before sending `none`, because a full check-in takes about 30 s.
Also: first, `git fetch origin && git merge origin/main` (main moved: #34 posture.py and maybe others), and update software/presence/README.md for the posture.py pipe (command above, plus `| tee /tmp/boxes.jsonl` to save a run for --replay on the Mac). Do not edit hardware/. Hub and agent stay unchanged. Demo note for the README: do not press the sim keys m, s or n while the camera is live.

Run the full python suite and show raw output. Then a separate reviewer subagent on the whole branch diff vs origin/main; fix what it finds. Then give the owner the push and `gh pr create --base main` commands (body "Closes #13" is wrong since #13 also covers hardware; use "Part of #13").
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
