---
name: hack-prep
description: Before a hackathon, read the event's Devpost pages and any rules pasted into its event folder, and write a rules card (video max length, required submission fields, tracks and prizes, deadlines) with a source for every item. Use for /hack-prep <devpost url>.
argument-hint: "<devpost url>"
---

# /hack-prep

Write one rules card for one event. Every item on the card has a verbatim quote and the source it came from. A rule you cannot find is written as not found, never guessed.

Follow these steps in order.

1. **Parse the argument.** It must match `https?://<slug>.devpost.com/...`. The slug is the subdomain. The base is `https://<slug>.devpost.com`. For any other URL (for example `devpost.com/software/...` or an MLH page), stop and ask the owner for the event's Devpost URL. Do not make up a slug.

2. **Find the folders.** Run `realpath` on this skill's base directory. The agent dir is two levels up from it (`hackathons/agent`). The event dir is `hackathons/events/<slug>/`, beside the agent dir. Run `mkdir -p <event dir>/pasted`. This keeps cards in the gitignored events folder of the checkout the skill link points at, whatever repo you run from.

3. **Read the sources.** Run `<skill dir>/page-text.sh` on each of `<base>/`, `<base>/rules` and `<base>/updates`. Record each page as `read`, or as `fetch failed (exit N)` when the script exits non-zero. Do not use WebFetch for Devpost: it gets HTTP 403. Do not follow links off Devpost. When a rule points to an outside page, list that page under Not found's "Looked in". Then read every file in `<event dir>/pasted/` (Discord announcements, MLH or sponsor rules the owner pasted by hand). An empty folder goes in Sources as `pasted/: no files`.

4. **Fill the template.** Copy `<agent dir>/templates/rules-card.md` and replace each `{...}` placeholder. Add one row per item. Every row has a verbatim quote and its source: the page URL, or `pasted/<file>`. When a rule is a range, the rule to follow is the upper end, with the full quote beside it. Remove a template example row that has no data.

5. **Conflicts.** When two sources disagree on an item, add a Conflicts row with what each source says and mark the stricter one under "Follow". Stricter means the shorter video max, the earlier deadline, the smaller track cap, and for required fields, the union of both lists. Put the stricter rule in that item's own section too.

6. **Not found.** When one of the four items (video max length, required submission fields, tracks and prizes, deadlines) has no source, add a Not found row that lists every source you read or tried. Never fill it from memory, from Devpost defaults, or from another event.

7. **Write** `<event dir>/rules-card.md`, overwriting any card already there. Reply with its path and the video max line.

8. **Read-only.** Send only GET requests, through `page-text.sh`. Never log in, post, comment, message or submit anywhere.
