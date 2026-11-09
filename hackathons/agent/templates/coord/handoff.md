# Coordinator handoff (Coordinator {n} -> Coordinator {n_next}), {date and time with zone}

Coordinator {n} ({coordinator_id}) is near 140k. It does nothing more.

Read first: the last 25 lines of `{event_dir}/COORD.md`, `{event_dir}/briefs/rules-common.md`, `{event_dir}/threads/*.json`, `gh pr list` in the event repo.

## State at handoff
- Main: {sha}.
- Owner: {where the owner is, standing OKs and holds, with the time each was given}.
- In flight: {one line per thread: name, thread id, brief path, what comes next}.
- Open PRs: {number, head SHA, reviewer verdict}.
- Owner list: {decisions waiting for the owner}.
