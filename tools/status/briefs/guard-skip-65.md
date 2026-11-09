# Brief: guard-skip-65 (issue #65)

Thread name: '#65 skip guard on no answer'. Status file name: guard-skip-65. Branch issue-65-guard-skip from origin/main (main is 1c958e2). Report to "HackUTD build coordinator 8" (threadId mcp:d5b5f74a-1ab5-4bbe-b760-aebd7b7f906a).

## Task (owner approved 3:01 AM CST)
In software/agent/checkin.py, every non-empty reply transcript goes to the hosted Nemotron Safety Guard before the rule decides (Safety Guard screening is around checkin.py:500-520 on main; find the real spot). On room noise, ElevenLabs Scribe writes words into silence ("[singing] And I want you to be mine"). The keyword classifier (software/agent/classify.py) still says no_answer, so the decision is right, but the guard call costs 0.5 to 13 s per ask (worst 20 s timeout).

Change: when the classifier already says no_answer for a reply, skip the Safety Guard call for that reply. Everything else stays: help, ok and other classes still go through the guard as today. Decisions must not change in any case.
- Keep the trace honest: write one short trace row that says the guard was skipped because there was no answer (match existing trace wording style). Never say "fall detection".
- Check software/eval (merged in #63): its scoring counts Safety Guard calls and reply waits. Update eval expectations only if a test pins the old behavior; say what you changed. Run `python -m software.eval --runs 1` in mock mode (no key) and report 9 of 9.
- Optional measure (only if no other hosted pass is running; ask the coordinator first): one hosted eval pass with --runs 1 --max-rpm 15 to show the reply wait drops on silent cases.
- Do not edit hardware/. Rafael's branch origin/pi-integration and the '#64 EQW warning tone' thread (branch issue-64-eqw-tone) also edit checkin.py; report `git merge-tree` results against origin/pi-integration.

## Done when
Tests first: a test that a no_answer reply makes no guard call and the decision is the same; a test that a help reply still calls the guard. Full suites of agent, eval and any package you touch pass (raw output). A separate reviewer subagent ran on your diff; you fixed what it found. Committed on issue-65-guard-skip, not pushed. Send the coordinator the SHA, test counts and the owner push + PR commands. Merge waits for the filming take.

## Rules (every thread)
- Team repo godfreyponce/hackutd-26, product LAND, a demo home safety box. Owner Godfrey owns software/. Rafael (GitHub rafael-amador) owns hardware/: do not edit hardware/. Hacking ends Sun 12:00 PM CT; it is Sun about 3:05 AM CST.
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
