# Brief: #55 decision-layer accuracy eval

Status file name: eval-55. Branch issue-55-eval, worktree from origin/main. Coordinator: "HackUTD build coordinator 6" (threadId mcp:6d12986d-12e1-4ffe-99ff-36dbe5ebf066). Report to it with t3_thread_send.

## Task (owner YES about 1:03 AM)
Judge question: "how accurate is it?". Build a repeatable eval that measures the DECISION layer (not the camera). Put it under software/ (for example software/eval/), with a README section.

It runs the full check-in loop: the real hub and the real agent with the real hosted Nemotron planner, on SPARE ports only. Voice replies are injected as bus messages exactly the way the voice service sends them (read software/voice and the hub contract to match the message shape). Events (quake, fall_hint, help_gesture as fits) and presence (moving, still, none) are injected the way the box and presence services send them. Scripted cases, each replayed many times:
1. event + someone there + "I'm okay": expect log only, no alarm.
2. event + someone there + "Help": expect alarm right away.
3. event + someone there + silence x3: expect alarm on the 3rd miss.
4. event + nobody there + silence: expect no alarm.
5. an unclear reply (say what the expected outcome is per software/agent/rule.py, and test that).
6. presence still vs moving (expected outcomes from rule.py).
The alarm is decided by code (software/agent/rule.py), never by the LLM. Read rule.py, checkin.py and planner.py first and derive every expected outcome from the code. If the code's real behavior differs from the list above, report that plainly, do not change the code.

Per case record: runs, correct decisions, time from event to first ask and from event to alarm (median and worst). Count planner fallbacks to the ScriptPlanner (Nemotron unavailable or timed out) and Safety Guard results. Output a short results table the owner can quote, for example "N of N runs made the right call; help on screen in X s median", plus the exact command to rerun it. Silence waits make runs slow: if the agent has timing settings you can set by env or flags for the eval run, use them and say so in the results (and also report one run at real demo timing).

NVIDIA key: the agent reads NVIDIA_API_KEY from the environment (software/agent/settings.py). Get the key only via request_secret (delivery "file"), pass it to the agent process by env, never print it, never commit it. Mind NVIDIA API rate limits: find the documented or observed limit, pick the run count from it, and state the basis in the results. Do not burn the live loop's quota: keep concurrency low.

Constraints: no changes to hub, agent or voice runtime code. If the eval truly needs one, stop and ask the coordinator. The owner is FILMING on the live loop: never 8765/8080, never touch the live hub, agent or voice processes.

Done means: eval code + any unit tests for its own helpers; hub, agent, voice suites still pass; the eval run done with results table and raw output saved to your scratchpad (paths listed); two separate reviewer subagents (one checks the expected outcomes against rule.py, one checks the measurement is honest: no cherry-picking, failures counted, fallbacks counted); commit with no trailer. Send the coordinator: head SHA, the results table, the rerun command, owner push + `gh pr create --base main` commands (body "Closes #55").

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
