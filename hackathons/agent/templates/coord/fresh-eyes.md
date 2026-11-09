You run the fresh-eyes review of `{base}` at `{sha}`. Status name: `{name}`. Your coordinator is `{coordinator_id}`.
{rules_card_line}

## Areas
Run one separate reviewer subagent per area, all in parallel. Give each one only its area and the "Look for" list.
{areas}

## Look for
- Real bugs. Each one needs a concrete input that fails and what happens on it.
- Claims in the README and docs that the code does not back.
- Breaks of the event's wording rules.

## Rehearsal
Make a worktree of `{base}` at `{sha}`. Run the demo path end to end there, on spare ports that are not in the event's list. Record the raw results: the commands, the output, and what failed.

## Fixes
Each real bug gets its own small branch and PR. Write the failing test first. Then tell the coordinator the PR number and head SHA. A new feature is a proposal only: list it in the report and do not build it.

## Output
Write `{event_dir}/fresh-eyes-report.md`: the findings per area (bugs first), the rehearsal results, the fix PRs, and the proposals. Send the coordinator its path.

{rules_block}
