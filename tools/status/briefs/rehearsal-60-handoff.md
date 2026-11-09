# Handoff: rehearsal-60 (issue #60), from session 1

Read the brief first: tools/status/briefs/rehearsal-60.md. Its Task and Rules still apply.
Worktree: /Users/geovponce/.t3/worktrees/hackutd-26/issue-60-rehearsal (branch issue-60-rehearsal, on 6393a11).
Venv: .venv in the worktree (python3.12, hub+agent+voice requirements installed).
Token use is not a problem (owner rule). Pass that on.

## Done (uncommitted in the worktree)
- software/eval/run.py: run_cases takes optional `engine` and `settle` (default behavior unchanged).
- software/eval/rehearsal.py: `python -m software.eval.rehearsal --out DIR --runs 10 [--cut-internet] [--listen-s S] [--voice online|offline]`.
  Real voice engines (ElevenLabs/Kokoro TTS, Scribe/Moonshine STT); only engines.play/record/stop_audio are
  replaced by SoundDevice (sleeps the audio length; replies are fixture WAVs over room noise). No sound plays.
  --cut-internet sets a dead proxy (127.0.0.1:9) in this process and the agent child only. Nothing global.
  Cases: standup (the demo run) and help. Step times from hub bus publish times; first/last word from the device.
- software/eval/tests/test_rehearsal.py: 5 tests, all pass (the cut e2e test takes ~43 s).
- software/eval/README.md: new section "Judge-table rehearsal timing (issue #60)". It points to
  software/eval/rehearsal-results.md, which does not exist yet.
- ElevenLabs key is scoped: it cannot read its quota (missing_permissions). Online pass is small (~4,400 chars TTS, ~5 min STT).

## Running at handoff
Internet-cut pass, real keys but network cut for my processes:
out = /private/tmp/claude-501/-Users-geovponce--t3-worktrees-hackutd-26-issue-60-rehearsal/ba45e143-d1ac-4f51-93b2-44c10a91fe95/scratchpad/cut
(rehearsal.md and rehearsal.json appear there when it ends; progress in ../cut.stdout). Run 1 of the demo was right, alarm 33.9 s.

## Next
1. When the cut pass ends, read cut/rehearsal.md. Check the agent.log shows "LLM unreachable: hosted Nemotron" then "fixed script".
2. Online pass ONLY after #55's paced pass is done (tools/status/threads/eval-55.json, or ask "HackUTD build coordinator 7"):
   NVIDIA_API_KEY="$(cat ~/.t3/userdata/secrets/files/8e0261a9*)" ELEVENLABS_API_KEY="$(cat ~/.t3/userdata/secrets/files/0e581591*)" .venv/bin/python -m software.eval.rehearsal --out <scratch>/online --runs 10
   (paced to 15 hosted calls/min by default). Do not run tests at the same time: CPU load skews timings.
3. If the demo run's last word is over ~45 s, rerun with --listen-s 4 (env override only, AGENT_LISTEN_S) and propose it. Do not edit settings.py.
4. Write software/eval/rehearsal-results.md (the passes' tables, failed runs with why, real vs simulated, rerun commands).
5. Run `.venv/bin/python -m pytest software/eval` (full suite), show raw output. Commit with NO trailer.
6. Separate reviewer subagent on the diff; fix findings.
7. Send the coordinator the results table, the rerun command, and the owner commands, each in its own bash fence:
   git -C /Users/geovponce/.t3/worktrees/hackutd-26/issue-60-rehearsal push -u origin issue-60-rehearsal
   gh pr create --base main --head issue-60-rehearsal --title "..." --body "Closes #60. Builds on #55 (based on issue-55-eval)."
8. Update tools/status/threads/rehearsal-60.json on every state change.
