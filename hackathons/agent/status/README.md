# Live status page for any event

A local page that shows what is happening on one event's repo, what changed, and what the owner needs to do.

## Start it

From the root of the repo that holds `hackathons/agent/`:

```bash
python3 hackathons/agent/status/collector.py <slug>
```

`<slug>` is the event folder name under `hackathons/events/`. Then open `http://localhost:<port>`, with the port from the event config. The collector writes `status.json` every 60 s. The page reads it every 10 s. Stop it with Ctrl-C.

To write `status.json` once and exit, add `--once`. It prints the collector errors as a JSON list.

It needs Python 3 (stdlib only) and the `gh` CLI, logged in with access to the event repo.

## Event config

Each event has one config file, `hackathons/events/<slug>/status-config.json`. The `hackathons/events/` folder is gitignored, so teammate logins stay off GitHub.

```json
{
  "repo": "owner/name",
  "checkout": "~/Developer/name",
  "port": 8100,
  "teammates": [{"github": "teammate-login", "git": "teammate|their-email-user"}]
}
```

| Field | Required | Rule |
|---|---|---|
| `repo` | yes | The event repo on GitHub, as `owner/name`. |
| `checkout` | yes | The path of your local clone of that repo. `~` is allowed. The collector runs `git` there. |
| `port` | yes | The local port the page uses. |
| `teammates` | no | A list of teammates, one section each on the page. Default: none. |
| `teammates[].github` | yes | The teammate's GitHub login. Matched against issue comments. |
| `teammates[].git` | yes | A regular expression, matched case-insensitively against the commit author name and email. |

When the file or a required key is missing, the collector prints one line that names the file and the key, and exits before it serves anything.

## What it reads

- Issues, PRs and check state, through `gh`.
- Remote branches and their latest commits, after `git fetch --prune` in the checkout.
- Local worktree branches named `issue-*` that have commits not on origin. The page shows them as "waiting for you to push", with the push command.
- Each teammate's pushes (matched by `git`) and issue comments (matched by `github`).
- Thread status files in `hackathons/events/<slug>/threads/` (format below).

It writes `hackathons/events/<slug>/status.json`. The page serves only `/`, `/index.html` and `/status.json`.

## Thread status files (for build threads)

Each build thread owns one file:

```
<agent repo>/hackathons/events/<slug>/threads/<name>.json
```

`<agent repo>` is the main checkout of the repo that holds `hackathons/agent/`. Always use this absolute path, in the main checkout, even when the thread works in a worktree. Do not commit these files.

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
- `needs-owner`: the thread waits for the owner, for example a key, a decision or a push. The note says what to do.
- `done`: the work is finished and pushed or in a PR.

Write the file in one step so the page never reads half a file:

```bash
printf '%s' '{"name":"hub-19","issue":19,"state":"working","note":"Simulator works.","updated":"'"$(date -Iseconds)"'"}' > /tmp/hub-19.json && mv /tmp/hub-19.json <agent repo>/hackathons/events/<slug>/threads/hub-19.json
```

A file the collector cannot read shows as a `blocked` thread with the note "Unreadable status file".

Name branches `issue-<number>-<slug>`, for example `issue-19-hub`. The page uses the number to place the work on the build map.

## Build map colors

The map shows every issue in the repo, ordered by number.

| State | When |
|---|---|
| Not started | No branch, no thread file, no PR. |
| Working | A branch `issue-N-*` exists, or a thread file says `working` or `done`. |
| Blocked | A thread file for the issue says `blocked` or `needs-owner`. |
| PR open | An open PR names the issue in its branch, title or body. |
| Merged | A PR for the issue is merged, or the issue is closed. |
