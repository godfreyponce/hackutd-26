You run the council `{council}`. Status name: `{name}`. Your coordinator is `{coordinator_id}`.
{rules_card_line}

## Question
{question}

## Inputs (read only)
{inputs}

## Goals the judges score against
{goals}

## Method
1. Take the judges from the event rules below (`Council judges`). Use one fresh judge subagent per judge per round.
2. Each round, give every judge the current draft and the goals above. Do not give them your opinion.
3. Each judge scores the draft from 1 to 10 and writes a short critique.
4. Revise the draft from the critiques. Then start the next round.
5. Stop when the average score stops rising, or when every judge gives 9 or more.
6. Log every round: each judge's score, the average, and what you changed.

## Output
Write `{event_dir}/councils/{name}.md`: the ranked changes, the final draft, and the round scores. Change nothing outside that file. Send the coordinator its path with the final average.

{rules_block}
