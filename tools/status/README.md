# Live status page

A local page that shows what is happening on hackutd-26, what changed, and what Godfrey needs to do.

## Start it

```bash
python3 ~/Developer/hackutd-26/tools/status/collector.py
```

Then open http://localhost:8099. The collector writes `status.json` every 60 s. The page reads it every 10 s. Stop it with Ctrl-C.

It needs Python 3 (stdlib only) and the `gh` CLI, logged in with access to `godfreyponce/hackutd-26`.

## What it reads

- Issues, PRs and check state, through `gh`.
- Remote branches and their latest commits, after `git fetch --prune`.
- Local worktree branches named `issue-*` that have commits not on origin. The page shows them as "waiting for you to push", with the push command.
- Rafael's pushes (git author `rafael amador`) and his issue comments (GitHub `rafael-amador`).
- Thread status files in `threads/` (format below).

## Thread status files (for build threads)

Each build thread owns one file:

```
~/Developer/hackutd-26/tools/status/threads/<name>.json
```

Always use this absolute path, in the main checkout, even when the thread works in a worktree. Do not commit these files.

Write the file when the thread starts and every time its state changes. Write a new note when something worth knowing happens, such as a test passing.

```json
{
  "name": "hub-19",
  "issue": 19,
  "state": "working",
  "note": "Simulator sends events. WebSocket server is next.",
  "updated": "2026-11-07T18:05:00-06:00"
}
```

| Field | Type | Rule |
|---|---|---|
| `name` | string | Same as the file name without `.json`. Lowercase, short, for example `agent-15`. |
| `issue` | number | The GitHub issue the thread builds. Use `null` for a thread with no issue. |
| `state` | string | One of `working`, `blocked`, `needs-owner`, `done`. |
| `note` | string | One plain sentence. Say what the owner must do when the state is `needs-owner` or `blocked`. |
| `updated` | string | ISO 8601 time with a time zone, when you wrote the file. |

States:

- `working`: the thread is building. No action from the owner.
- `blocked`: the thread cannot go on, for example a dependency is not ready. The note says on what.
- `needs-owner`: the thread waits for Godfrey, for example a key, a decision or a push. The note says what to do.
- `done`: the work is finished and pushed or in a PR.

Write the file in one step so the page never reads half a file:

```bash
printf '%s' '{"name":"hub-19","issue":19,"state":"working","note":"Simulator works.","updated":"'"$(date -Iseconds)"'"}' > /tmp/hub-19.json && mv /tmp/hub-19.json ~/Developer/hackutd-26/tools/status/threads/hub-19.json
```

Name branches `issue-<number>-<slug>`, for example `issue-19-hub`. The page uses the number to place the work on the build map.

## Build map colors

| State | When |
|---|---|
| Not started | No branch, no thread file, no PR. |
| Working | A branch `issue-N-*` exists, or a thread file says `working` or `done`. |
| Blocked | A thread file for the issue says `blocked` or `needs-owner`. |
| PR open | An open PR names the issue in its branch, title or body. |
| Merged | A PR for the issue is merged, or the issue is closed. |
