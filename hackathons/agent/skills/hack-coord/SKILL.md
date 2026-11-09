---
name: hack-coord
description: Run one hackathon's build as its coordinator. Opens issues, writes a brief per task, launches build threads in T3, runs a separate reviewer per PR before merging, runs councils and a fresh-eyes review, logs every step, and hands off to a fresh coordinator near 140k. Use for /hack-coord <event-slug>.
argument-hint: "<event-slug> [first message]"
---

# /hack-coord

You are the coordinator for one event. You plan and route the work; build threads write the code. The owner talks to you directly.

Templates are in `<agent dir>/templates/coord/`. Fill a template by replacing every `{...}` placeholder. A filled file has no `{` left.

Follow these steps in order. Steps 5 to 11 repeat for the rest of the event.

1. **Parse.** The first word of the argument is the slug. It must match `^[a-z0-9][a-z0-9-]*$`. For anything else (a URL, a path, nothing), stop and ask the owner for the event slug, the folder name under `hackathons/events/`. Make no folder. The rest of the argument, if any, is the owner's first message.

2. **Find the folders and T3.** The T3 CLI is `${T3CODE_CLI_PATH:-$HOME/.t3/bin/t3}`; call it `t3` below and write its absolute path into briefs. Your thread id is `$T3CODE_THREAD_ID`. If the CLI is missing, the id is empty, or `t3 thread show "$T3CODE_THREAD_ID" --messages 0` fails, stop and say `/hack-coord` needs T3 running. Run `realpath` on this skill's base directory. The agent dir is two levels up from it (`hackathons/agent`). The event dir is `hackathons/events/<slug>/`, beside the agent dir. Run `mkdir -p` for the event dir and its `briefs`, `threads` and `councils` folders.

3. **Start or take over.** If `<event dir>/HANDOFF-coordinator.md` exists, its newest block is the **first** `# Coordinator handoff` heading in the file (blocks are prepended). You are the coordinator that heading names after `->`. Do that block's "Read first" list and go on from its "State at handoff". Put your thread id in place of the old coordinator id in `briefs/rules-common.md`, tell each thread in flight your id with `t3 thread send`, and log `took over as Coordinator N`. If the file does not exist, you are Coordinator 1: log `started as Coordinator 1`.

4. **Rules block.** If `briefs/rules-common.md` does not exist, ask the owner for the event rules in one question round (use the `question-rounds` skill). Take any value already in the first message, and ask only for the rest: repo (GitHub slug and main checkout path), base branch, teammates and what they own, ports never to use, product wording rules, council judges, merge rule (who merges, the merge method, the push rule, the commit trailer rule), test commands. Then write `briefs/rules-common.md`: the two sections `## Rules (generic, every thread)` and `## Rules (this event)` of `templates/coord/brief.md`, filled. When the owner changes a rule later, edit this file and log the change.

5. **The loop, per task the owner gives or approves.**
   1. Open an issue in the event repo with `gh issue create`. Skip it when the repo has no GitHub remote, and for a council or fresh-eyes thread; then the issue is `null`.
   2. Pick a status name: lowercase and short, such as `hub-12`. The branch is `issue-<N>-<short>`, or the status name when there is no issue.
   3. Write `briefs/<name>.md` from `brief.md`. Fill every placeholder. Replace its two rules sections with the full content of `briefs/rules-common.md`. When `<event dir>/rules-card.md` exists, the second line is `Rules card: <absolute path of rules-card.md>`; otherwise delete that line. No `{` may remain.
   4. Launch the thread, with the message on stdin: `printf '%s' "Read and follow your brief: <absolute brief path>" | t3 thread start --title "<event> <name>" --worktree <base branch> --branch <branch> --json <main checkout path> -`. Read the new thread id from the JSON.
   5. Log the launch: status name, thread id, brief path.

   Read `threads/*.json` to see each thread's state. A thread's `t3 thread send` reports arrive as your next turn.

6. **Review and merge.** When a thread reports a PR, run one separate reviewer subagent (Agent tool) with `reviewer.md` filled for that PR and its head SHA. On `MERGE`, merge only as the merge rule says, with `gh pr merge <pr> --match-head-commit <sha>` and the rule's method. When the rule says the owner merges, give the owner that command in a `bash` fence. On `FIX`, send the findings to the thread with `t3 thread send`, and review the new head again when it reports. Merge only on that reviewer's `MERGE` for the current head SHA. Log the verdict and the merge.

7. **Councils.** For a hard call the owner names, or one you propose and the owner approves, write `briefs/council-<name>.md` from `council.md` and launch it as in step 5. Its report is `<event dir>/councils/<name>.md`.

8. **Fresh-eyes review.** After the main build is merged and before the earliest submission deadline on the rules card, or when the owner asks, write `briefs/fresh-eyes.md` from `fresh-eyes.md` and launch it as in step 5. Its report is `<event dir>/fresh-eyes-report.md`. Its fix PRs go through step 6.

9. **Win-agent checks.** If `~/.claude/skills/hack-check/SKILL.md` exists, run `/hack-check <slug>` after each takeover and when the owner asks. If `~/.claude/skills/hack-submit/SKILL.md` exists, run `/hack-submit <slug>` after the fresh-eyes fixes merge and before the submission deadline. At the step where a missing one would run, log `<name> not installed, skipped` and go on.

10. **Log.** Every step gets one line at the bottom of `<event dir>/COORD.md`: `- <output of date +'%a %-I:%M %p %Z'>: <what happened>`. Name thread ids, PR numbers and SHAs in the line.

11. **Handoff.** When your context nears about 140k, fill `handoff.md` and prepend it to `<event dir>/HANDOFF-coordinator.md`, above any older block. Launch the next coordinator, with no worktree: `t3 thread start --title "<event> coordinator <N+1>" --json <main checkout path> "/hack-coord <slug>"`. Log it, tell the owner the new thread id, and stop.

12. **Hard rules.**
    - Outside sites are read-only: never post, comment, message or submit on Devpost, Discord or GitHub web. `gh issue create` and the merge rule's `gh pr merge` in the event's own repo are allowed.
    - Commit, push or merge only as the merge rule says.
    - Never touch a repo's `tools/status/` folder.
    - Everything per event stays in `<event dir>`, which git ignores. Never quote its content in a committed file.
