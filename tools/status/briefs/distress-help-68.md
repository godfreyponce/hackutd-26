# Brief: distress-help-68 (issue #68)

Thread name: '#68 distress phrases count as help'. Status file name: distress-help-68. Branch issue-68-distress-help from origin/main (main is 1c958e2). Report to "HackUTD build coordinator 9" (threadId mcp:launch:553b6bb62cef3a8f8a5bfaf0654ec6bcd65a93c938b08dafbf58c02b781c5dcb) with t3_thread_send.

## Task (owner approved via HQ 13, about 3:15 AM CST)
software/voice/classify.py turns a reply transcript into ok, help or no_answer by keyword. The #65 reviewer found it calls these no_answer: "I fell", "I need an ambulance", "cant breathe" (no apostrophe), "I am on the floor". Add these phrases and close variants to the help words. Examples of close variants: "I've fallen", "I fell down", "fell over", "call an ambulance", "can't breathe" / "cannot breathe" / "can not breathe" / "cant breathe", "I'm on the floor", "I'm on the ground", "I'm bleeding", "chest pain". Keep it a short, readable keyword list; no LLM.

Care points:
- Ok replies must stay ok. Think about false help: "I fell asleep", "I'm on the floor doing yoga" are rare in a demo; a false help only means a fake alarm sooner, and the agent planner still has the Safety Guard. State what you chose and why in one line.
- Existing order stays: help words win, then negation, then ok, else no_answer.
- Check software/eval/cases.py and software/eval/tests/test_cases.py and the voice README: if a case or doc lists help words, keep them in sync. Run `python -m software.eval --runs 1` in mock mode (no key) and report 9 of 9.
- Do not edit hardware/. Report `git merge-tree` against origin/pi-integration, origin/issue-64-eqw-tone and origin/issue-65-guard-skip.

## Done when
Tests first in software/voice/tests/test_classify.py: each new phrase is help, the old ok and no_answer cases stay the same, and "I fell asleep" behavior is pinned to what you chose. Full voice and eval suites pass (raw output). A separate reviewer subagent ran on your diff; you fixed what it found. Committed on issue-68-distress-help, not pushed. Send the coordinator the SHA, test counts and the owner push + PR commands. Merge waits for the filming take.

## Rules (every thread)
- Team repo godfreyponce/hackutd-26, product LAND, a demo home safety box. Owner Godfrey owns software/. Rafael (GitHub rafael-amador) owns hardware/: do not edit hardware/. Hacking ends Sun 12:00 PM CT; it is Sun about 3:15 AM CST.
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
