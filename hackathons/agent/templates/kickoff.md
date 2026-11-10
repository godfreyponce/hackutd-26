# Kickoff: {event name}

Slug: `{slug}`. Built: {YYYY-MM-DD HH:MM} by /hack-kickoff from `targets.md` and `sponsor-brief.md`.
Idea from: {the /hack-kickoff argument / `idea.md`}.
A rerun keeps your hand edits: the new version goes to `kickoff.new.md`. Delete this file to let the next run replace it.

## Idea
> {idea text, verbatim}

## Verdict
{One plain line: "Fits target 1, {prize}." / "Fits no target." plus the one change most likely to fix it.}

## Targets
| # | Prize | Verdict | Reason (one line, quoting the idea and the brief) | To fit |
|---|---|---|---|---|
| {1} | {prize} | {fits / misses} | {reason} | {change, or "—" when it fits, or "none: why"} |

## Other sponsor prizes in the brief
| Prize | Verdict | Reason (one line) | To fit |
|---|---|---|---|

## Integration bar
The sponsor tool sits in the core path: the demo cannot run without it. No fake backend or mocked data stands in for it.

### {prize}: {tool}
- [ ] Core path call: {user step} runs `{API call}` ({source}), or `API call: not found (looked in {links}); name it before building`.
- [ ] Real data: {what data the call reads or writes, and where that data comes from} ({source}).
- [ ] Counts as faked: {hardcoded or recorded responses, a mock server, a call only in a script the demo never reaches, the tool named only in the write-up or slides, plus any idea-specific fake}.

## Not found
| Item | Looked in |
|---|---|
