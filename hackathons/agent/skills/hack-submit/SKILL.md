---
name: hack-submit
description: In the last hours of a hackathon, audit the pasted Devpost draft, the repo and the video against the event's rules card and winner bar, and report pass or fail item by item with a fix for each fail. Never submits. Use for /hack-submit <event-slug>.
argument-hint: "<event-slug>"
---

# /hack-submit

Audit one event's submission before the deadline. Check the Devpost draft the owner pasted, the repo it links and its video against the rules card and the winner bar. Print one row per item with `pass`, `fail` or `by hand`, and a fix for each fail. Every number in the table comes from a command, never from a count by eye. This skill only reports: it never submits and never edits the draft.

Follow these steps in order.

1. **Parse.** The argument is the event slug and must match `^[a-z0-9][a-z0-9-]*$`. For anything else, stop and ask the owner for the event slug, the folder name under `hackathons/events/`.

2. **Find the folders.** Run `realpath` on this skill's base directory. The agent dir is two levels up from it (`hackathons/agent`). The event dir is `hackathons/events/<slug>/`, beside the agent dir. Do not create it.

3. **Required inputs.**
    - If `<event dir>/submission-draft.md` is missing, reply with how to paste it and stop. Give this command in a `bash` fence: `cp <agent dir>/templates/submission-draft.md <event dir>/submission-draft.md`. List the field lines of the form (every line that starts `=== `). Say: paste each field from the Devpost edit pages under its line, then rerun. Do not copy the form yourself, and write no audit.
    - If `<event dir>/rules-card.md` is missing, reply "run /hack-prep first" and stop.
    - If `<event dir>/winner-bar.md` is missing, or its `## Bar` Targets read `not measured`, skip every winner-bar row. Add one Skipped row with the reason.
    - Check for `targets.md` (#92), `kickoff.md` (#95) and `check-log.md` (#96) in the event dir. Add each missing one to Skipped as `<file> missing (made by #N)`.

4. **Cut the draft fields.** Get each field with `sed -n '/^=== <Field> ===$/,/^=== /{/^=== /!p;}' <event dir>/submission-draft.md`, where `<Field>` is the exact marker text, for example `Write-up`. Keep the command in this form: Claude Code replaces a dollar sign followed by a digit in a skill with an argument, so an awk field variable would break. Count the write-up words with the `Write-up` cut piped to `tr -s '[:space:]' '\n' | grep -c '[[:alnum:]]'`. A word holds a letter or digit, the same rule as `winner-facts.py`. If every field cut is empty or blank, start the reply with "the draft looks empty: paste each field under its line" and go on. Every row that reads the draft then fails.

5. **Repo.** The repo is the first `https://github.com/<owner>/<repo>` in the `Try it out links` field, else the first one in any field. Strip a trailing `.git` and any deeper path. Never fall back to the repo of the folder you run in. Rows, each with From `gh`:
    - **Repo linked in draft:** pass when a repo was found. Draft-has names the repo and the field it was in.
    - **Repo exists:** `gh repo view <owner>/<repo> --json nameWithOwner,visibility,url` exits 0.
    - **Repo is public:** the `visibility` from that call is `PUBLIC`. A judge cannot open a private repo.
    - **Repo has a README:** `gh api repos/<owner>/<repo>/readme --jq .path` exits 0.

    With no repo found, all four rows fail. The last three say "no repo link in the draft" in Draft-has, and every fix says to add the repo link to Try it out.

6. **Video.** Read the `Video demo link` field.
    - A local file path: run `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "<path>"`.
    - A YouTube or Vimeo URL: run `yt-dlp --print duration --skip-download "<url>"`. Quote the URL, because the shell globs a `?`.
    - A non-zero exit, an output of `NA`, a path that does not exist, or any other host: ask the owner to type the video length as m:ss, and stop. When the owner answers, go on with that length and write it in Draft-has as `m:ss (owner typed)`. Never guess a length.
    - An empty field: there is no length. Every video row fails with "no video link in the draft".

    Round the seconds down and write the length as m:ss. The rules row compares it with the Rule to follow in the rules card's `## Video max length` section. It fails when the video is over the max, or under the low end when the rule gives a range. The fix says how much to cut or add, in m:ss. When video max length is under `## Not found`, the row is `by hand`: Draft-has shows the measured length, and the fix names the Not found row. Never use a limit that is not on the card, and never use the winner bar's aim in its place.

7. **Rules-card rows**, in the card's order. From names the card section, for example `rules card: Video max length`.
    - The video row from step 6.
    - One row per Required submission fields row. Pass when the draft holds the field. A repo field takes the result of the matching step 5 row, and a video field takes the result of the step 6 row. A field a pasted draft cannot show (for example a rule about commit times or reused ideas) is `by hand`, and the fix says what to check.
    - **Track cap:** when the card states a cap, count the opted-in tracks whose Limit says they count toward it. Match a track by name, ignoring case and the bracket tag. Fail when the count is over the cap. Draft-has shows the count against the cap.
    - **Deadlines:** one row for the submission close. Take the year from the card's event dates when the close line has none. Pass when the output of `date` is before the close, and Draft-has shows the time left in hours and minutes. When the close is past, fail. When the card gives no close time you can read, the row is `by hand`.
    - Each other row under `## Not found`: a `by hand` row that names the item.

8. **Winner-bar rows**, one per `## Bar` row. From names the bar row, for example `winner bar: Write-up words`.
    - **Write-up words:** pass at or above the floor. The fix gives the words needed to reach the floor and the aim.
    - **Video length:** pass at or under the aim. A fail here is a bar miss, not a rule break: say so in the fix. When the Target reads `not set`, the row is `by hand`.
    - **Repo linked in Try it out:** pass when step 5 found the repo in the `Try it out links` field. When the repo is only in another field, the fix is "move the link to Try it out".
    - **Tracks listed:** pass when at least one track is opted into.

9. **Optional rows.** Only for the files step 3 found.
    - `targets.md`: one row per `## N. <prize name>` heading. Pass when the opted-in tracks name that prize.
    - `kickoff.md`: one row per item of its integration bar. Pass when the write-up names that sponsor API or call.
    - `check-log.md`: one row for its last line. Pass when the line has no `fix-now`.

10. **Write.** Copy `<agent dir>/templates/submit-audit.md` and fill it: every row in steps 5 to 9 under `## Audit`, numbered in order, rules rows first, then repo, bar and optional rows. `Fix` is empty on a pass. Fill the not-opted-into line with the rules-card tracks the draft did not opt into (not the Track cap row); this line is not pass or fail. Fill Skipped. Count the results with a command, never by eye: pass the Result cell of every row, in order, to `printf '%s\n' <result 1> <result 2> ... | sort | uniq -c`, quoting `"by hand"`, and fill the Result line from its output. Then write the file once, to `<event dir>/submit-audit.md`, overwriting it. Reply with the Result line and the Audit table as written in the file, all six columns, then each fail in order with its fix, then the path of the audit file.

11. **Read-only.** Run only `gh repo view`, `gh api` GET calls (no `-X`, `-f` or `-F`), `ffprobe`, `yt-dlp --skip-download`, `date`, and file reads. Write only `<event dir>/submit-audit.md`. Never edit `submission-draft.md`. Never log in, post, comment, message or submit anywhere.
