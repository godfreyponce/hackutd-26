---
name: hack-kickoff
description: After the team picks a hackathon idea, check it against the event's prize targets and sponsor brief, and write kickoff.md with fits or misses per prize and a real-integration bar (sponsor API calls in the core path, real data, what counts as faked). Use for /hack-kickoff <event-slug> [idea].
argument-hint: "<event-slug> [idea text]"
---

# /hack-kickoff

Check one picked idea against the event's prizes and set the bar that `/hack-check` holds the team to. Every verdict quotes the idea and the brief. A call or fact you cannot find is written as not found, never guessed.

Follow these steps in order.

1. **Parse.** The first word is the slug. It must match `^[a-z0-9][a-z0-9-]*$`. For anything else (a URL, a path, nothing), stop and ask the owner for the event slug, the folder name under `hackathons/events/`. The rest of the argument, if any, is the idea text.

2. **Find the folders and the idea.** Run `realpath` on this skill's base directory. The agent dir is two levels up from it (`hackathons/agent`). The event dir is `hackathons/events/<slug>/`, beside the agent dir. The idea is the argument text. If there is none, it is `<event dir>/idea.md`. If both are present, use the argument and note it in "Idea from". If neither is present, stop, write nothing, and ask the owner to give the idea as text after the slug or to paste it into `<event dir>/idea.md`.

3. **Read the inputs.** Read `<event dir>/targets.md` and `<event dir>/sponsor-brief.md`, never their `.new.md` files. If either one is missing, stop, write nothing, and tell the owner to run `/hack-prep <devpost url>` first (targets also need `team.md`). A `targets.md` that says no sponsor prize meets the bar is not missing: it has no targets. Read `<event dir>/rules-card.md` if it exists, for the sponsor track cap only.

4. **Core path.** From the idea text, write down its core user path: the steps that the demo cannot run without, and where each step gets its data. Quote the idea for each step. This is what every verdict is measured against.

5. **Verdict per prize.** For each target in `targets.md`, then each other sponsor prize section in `sponsor-brief.md`, decide one of the following:
    - `fits`: the idea as written has that prize's tool in a core path step.
    - `misses`: it does not. That includes a tool used only as a side feature, and an idea whose data comes from elsewhere (its own database, manual entry, a hardcoded list) when the tool could supply it.

    The reason is one line and quotes both the idea and the brief's Tool row. Every `misses` row has a "To fit" cell: one change that puts the tool in a core path step, or `none: <why>` when the tool cannot carry this idea. A `fits` row has `—` in that cell.

6. **Verdict line.** If the idea fits at least one target, write `Fits target <n>, <prize>.`, listing each target it fits. If it fits none, write `Fits no target.` and the single change most likely to fix that, taken from a target's To fit cell. A sponsor prize outside `targets.md` that the idea fits goes in the line too, as "also fits <prize> (not a target)".

7. **Integration bar.** Write one bar block for each target the idea fits. If it fits none, the section is one line: `No bar set: the idea fits no target. Pick a change from To fit, update the idea, and rerun /hack-kickoff.` For each block:
    - **Core path call.** Name the user step and the sponsor API call it runs. Take the call name only from a page that you read: the brief's Docs link read with `<agent dir>/skills/hack-prep/page-text.sh`, WebFetch once when that returns little more than the title, or the public READMEs of the sponsor's GitHub org read with `gh`. If no page names a call, write `API call: not found (looked in <links>); name it before building` and add a Not found row.
    - **Real data.** Name the data that the call reads or writes, and where it comes from (for example a sponsor sandbox account created through the API, or the user's own input sent to the API). Write it with the source of how to get that data.
    - **Counts as faked.** List what fails the bar: hardcoded or recorded responses in place of the call, a mock server, a call made only in a script that the demo does not reach, the tool named only in the write-up or slides, and any fake that is specific to this idea.

8. **Write.** Copy `<agent dir>/templates/kickoff.md`, fill it, and write it to `<event dir>/.drafts/kickoff.md` (`mkdir -p <event dir>/.drafts`). Remove a template example row that has no data. Run `<agent dir>/skills/hack-prep/save-output.sh <event dir>/.drafts/kickoff.md <event dir>/kickoff.md`. Never write `kickoff.md` directly: the script keeps a file the owner edited by hand and puts the new version beside it as `kickoff.new.md`. Reply with the line that the script printed, the Verdict line, and the first item of each bar block.

9. **Read-only.** Send only GET requests: `page-text.sh`, WebFetch, and `gh` reads. Never log in, post, comment, message or submit anywhere.
