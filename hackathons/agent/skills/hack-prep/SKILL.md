---
name: hack-prep
description: Before a hackathon, read the event's Devpost pages, sponsor docs, past winners and any notes in its event folder, and write a rules card, a sponsor-tool brief, 1 or 2 ranked prize targets, and a winner bar measured from a past winner's Devpost pages, with a source for every item. Use for /hack-prep <devpost url>.
argument-hint: "<devpost url>"
---

# /hack-prep

Write four files for one event: a rules card, a sponsor-tool brief, 1 or 2 ranked prize targets, and a winner bar. Every item has a verbatim quote and the source it came from. A rule or fact you cannot find is written as not found, never guessed.

Follow these steps in order.

1. **Parse the argument.** It must match `https?://<slug>.devpost.com/...`. The slug is the subdomain. The base is `https://<slug>.devpost.com`. For any other URL (for example `devpost.com/software/...` or an MLH page), stop and ask the owner for the event's Devpost URL. Do not make up a slug.

2. **Find the folders.** Run `realpath` on this skill's base directory. The agent dir is two levels up from it (`hackathons/agent`). The event dir is `hackathons/events/<slug>/`, beside the agent dir. Run `mkdir -p <event dir>/pasted <event dir>/.drafts`. This keeps cards in the gitignored events folder of the checkout the skill link points at, whatever repo you run from.

3. **Read the sources.** Run `<skill dir>/page-text.sh` on each of `<base>/`, `<base>/rules`, `<base>/updates` and `<base>/details/dates` (the schedule page, which holds the submission times). The overview page `<base>/` also holds the prize list; Devpost has no separate prizes page. Record each page as `read`, or as `fetch failed (exit N)` when the script exits non-zero. Do not use WebFetch for Devpost: it gets HTTP 403. For the rules card, do not follow links off Devpost. When a rule points to an outside page, list that page under Not found's "Looked in". Then read every file in `<event dir>/pasted/` (Discord announcements, MLH or sponsor rules the owner pasted by hand). An empty folder goes in Sources as `pasted/: no files`.

4. **Rules card.** Copy `<agent dir>/templates/rules-card.md` and replace each `{...}` placeholder. Add one row per item. Every row has a verbatim quote and its source: the page URL, or `pasted/<file>`. When a rule is a range, the rule to follow is the upper end, with the full quote beside it. Remove a template example row that has no data.
    - **Conflicts.** When two sources disagree on an item, add a Conflicts row with what each source says and mark the stricter one under "Follow". Stricter means the shorter video max, the earlier deadline, the smaller track cap, and for required fields, the union of both lists. Put the stricter rule in that item's own section too.
    - **Not found.** When one of the four items (video max length, required submission fields, tracks and prizes, deadlines) has no source, add a Not found row that lists every source you read or tried. Never fill it from memory, from Devpost defaults, or from another event.
    - Write the result to `<event dir>/.drafts/rules-card.md`.

5. **Sponsor brief.** Copy `<agent dir>/templates/sponsor-brief.md`. Add one section per sponsor prize: a prize owned by one named company or tool (for example "Capital One Challenge" or "[MLH] Best Use of Gemini API"). Skip organizer prizes (overall, design, beginner, hardware or software hack). For each sponsor prize:
    - **Tool or API.** Quote the prize text. Write "none named" when the text names no tool.
    - **Docs.** Use a link from the prize text first. When the prize text has no link, or its link cannot be read, also find the sponsor's own docs site with WebSearch (keep only a result on the sponsor's own domain or its GitHub org), and read the READMEs of the sponsor's GitHub org with `gh`. List every link you tried. Read the link with `page-text.sh`. If that returns little more than the page title, try WebFetch once. If the page is still unreadable, keep the link with status `not readable (JS app)`, or `fetch failed (exit N)` when the fetch failed. `gh` may read the public READMEs of a sponsor's GitHub org.
    - **Access (keys, sandbox).** Take it only from a page you read. Else write "not found".
    - **Past winners.** Find the previous edition with `curl -fsSL 'https://devpost.com/api/hackathons?search=<name>&status[]=ended&page=<n>'` (GET only), where `<name>` is the event name without its year or edition number (for example `HackUTA` for "HackUTA 8"). Read pages 1, 2, and so on until you have `total_count` results (`meta.per_page` per page). The previous edition is the result with the same name and the latest `submission_period_dates` before this event. When there is none, the brief's Past winners rows name only this event's gallery and the API search. Run `<skill dir>/awards.sh` on `<base>/project-gallery` and on the previous edition's `/project-gallery`. Each output line is `<award>\t<project>\t<project url>`. An award matches this prize when it names the same sponsor or tool; prize names drift between editions. For each match, run `page-text.sh` on the project URL, then quote its "Built With" tools and one sentence from "How we built it" that names the tool. When no award matches, add a Not found row that names the galleries you read. A gallery with no output goes in Sources as `no winners listed`.
    - Write the result to `<event dir>/.drafts/sponsor-brief.md`.

6. **Targets.** This step needs `<event dir>/team.md`, which the owner writes by hand. If it is missing, skip this step. In the reply, ask the owner to write `team.md` (who is on the team, what each person has shipped and with which tools, hardware yes or no) and rerun. Otherwise copy `<agent dir>/templates/targets.md` and score each prize in the brief on the template's Scale, with one line of reasoning per score. Drop a prize whose integration depth is low. Rank by the lower of the two levels, and break ties by integration depth. List at most 2 targets, and no more than the sponsor track cap on the rules card. When no prize is left, write one line that says no sponsor prize meets the bar, and why. Write the result to `<event dir>/.drafts/targets.md`.

7. **Measure the winner reference.** Run `python3 -I <skill dir>/winner-facts.py adamFabsa`. Devpost user `adamFabsa` is the winner reference. Read his public pages only, and never contact him.

8. **If the script exits non-zero,** write the bar with every Target cell `not measured` and one Not measured row: `winner-facts.py exit N` plus its stderr line. Never fill a number from memory or from an earlier bar.

9. **Set the video target from the rules card.** Read the Rule to follow in the `## Video max length` section of the rules card draft from step 4 (`<event dir>/.drafts/rules-card.md`). If there is a max, the target is "aim {smaller of the measured median and the max}, never over {max}", and its From cell names `rules-card.md` and the video links. If the video max is under Not found, the target is "not set: the rules card has no video max", and the median stays in the Measured table only.

10. **Fill the winner bar.** Copy `<agent dir>/templates/winner-bar.md`. Put the script's two tables in place unchanged. Fill the four Bar rows, in order, from the Measured rows Write-up words, Video length, Repo in Try it out and Prizes shown under Submitted to, and copy their From links. Write the result to `<event dir>/.drafts/winner-bar.md`.

11. **Write.** For each draft, run `<skill dir>/save-output.sh <event dir>/.drafts/<name>.md <event dir>/<name>.md`. Never write the event files directly: the script keeps a file the owner edited by hand and puts the new version beside it as `<name>.new.md`. Fix an error in the draft before this step. After it, report an error in the reply instead of editing the event file: an edit after the write makes the next run treat the file as edited by hand. Reply with each line the script printed, the video max line, the winner bar's Video length target line, and the names of the targets (or the `team.md` ask).

12. **Read-only.** Send only GET requests: `page-text.sh`, `awards.sh`, `winner-facts.py`, the Devpost hackathons API, WebFetch and WebSearch on sponsor docs, and `gh` reads, plus `yt-dlp --skip-download` to read video lengths. Never log in, post, comment, message or submit anywhere.
