# Brief: readme-61 (issue #61)

Thread name: '#61 README intro'. Status name: readme-61. Work in the EXISTING worktree /Users/geovponce/.t3/worktrees/hackutd-26/issue-61-readme-center, branch issue-61-readme-center. It already has commit cf48228 (centered logo, reviewed MERGE). Add new commits on top, no amend. Not pushed yet. Report to "HackUTD build coordinator 7".

## Task (owner approved, 2:33 AM via HQ 10)
Rewrite the top of README.md as a short LAND intro. Judges see it when the repo goes public before noon.
- Keep the centered LAND logo (the <p align="center"><picture> block).
- Replace the kickoff content (the "Proposed plan (not locked; decide together)" part and the research/tracks start-here list) with:
  1. What LAND is: one or two plain sentences.
  2. How the loop works: box event, voice check-in, Nemotron agent, alarm rule.
  3. What is real and what is simulated: 499 simulated homes plus 1 real box. The alarm is a demo alarm, and no emergency number is called. The camera person detector runs on the Pi on its own; the control panel sends presence in the demo. Check every claim in code before you write it.
  4. How to run hub, agent, voice and web locally: real commands from the package READMEs and code. Never tell anyone to use a key inline; point to env vars.
- Move the kickoff and research links to a short "Hackathon notes" section at the bottom. Do not delete any docs or files.
- Facts come from ~/Developer/hackutd-26-media/script/LAND-demo-script.md and from the code (software/hub, software/agent, software/voice, software/web, software/presence and so on), never from memory. Where the script and the code disagree, the code wins; tell the coordinator.
- Wording: "no response after an event", never "fall detection". No em dashes. Never a middle dot as a separator (the current tagline line uses them; fix it). Plain short sentences. Run the unslop pass on the prose.
- Check the render: `gh api markdown -f mode=gfm -f context=godfreyponce/hackutd-26 -F text=@README.md`, then screenshot it in headless Chrome, dark and light, at a GitHub-like width (file:// is fine, or a spare port in 19800-19899). The owner sees the screenshot before he pushes.
- Run a separate reviewer subagent that checks EVERY claim against the code (file:line for each) and the wording rules. Fix what it finds.
- Commit with no trailer. Send the coordinator the screenshot paths, a short summary, and the owner push + gh pr create commands (base main, title "README: LAND intro and centered logo", body "Closes #61").

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
