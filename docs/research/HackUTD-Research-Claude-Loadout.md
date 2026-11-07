---
created: 2026-11-07
status: seed
tags: [hackathon, hackutd, research, claude-code, tooling]
---
Part of [HackUTD-2026](../HackUTD-2026.md).

# Claude Code loadout + cross-account collaboration (HackUTD 2026)

Researched 2026-11-07, ~8:30 AM CT, against official docs fetched the same morning. "[u]" means unverified.

## 1. Cross-account collaboration verdict

**Short answer: no official feature lets two Claude accounts run one orchestrated team.** Every native coordination feature is scoped to **one account**, and usually to one machine. The only official link between people is **GitHub**: any collaborator with write access can trigger `@claude`, which runs on the token owner's subscription. Everything else is DIY over a shared bus.

| Mechanism | Cross-account? | Evidence |
|---|---|---|
| Agent teams (lead + teammates, shared task list, SendMessage) | **No.** Same machine, same session | Mailboxes are local JSON at `~/.claude/teams/{team}/inboxes/`. "One team per session… can't share a team across sessions." Experimental flag. A cross-machine feature request is still open [u] |
| Cross-session messaging (`ListAgents`/`SendMessage`) | **No.** "Your" sessions only | Reaches other machines and cloud sessions only through *your* Remote Control login |
| Remote Control / `--teleport` | **No** | Teleport needs "the same claude.ai account" |
| Cloud sessions (claude.ai/code) sharing | Read-only | Pro/Max sharing is Private/Public; the link "doesn't update in real time." Team plan adds Team visibility, which is still view-only |
| **Claude Code GitHub Action (`@claude`)** | **Yes, the only official path** | Triggered by anyone with write access; auth with `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` (Pro/Max) |
| **Channels (Discord/Telegram plugin)** | Yes, partly | Pushes chat messages into a running local session. You can allowlist the other person's Discord ID. Research preview, needs Bun. **Any allowlisted sender can approve permission prompts** |
| Claude "Projects" (cloud) | No | Coordinates *your* cloud sessions |
| claude-squad / ccmanager / Orca | No | Local tmux and worktree managers; claude-squad (AGPL-3.0) needs tmux, so it won't run on native Windows |
| Third-party relays (claude-code-bridge, claudectl agent bus, Masumi messenger) | Claimed | Unvetted, relay servers over LAN or Tailscale [u]. Skip for a 24 h event |

### Recommended protocol: GitHub as the bus, humans as the orchestrators

It's the same repo protocol you used last time, with three additions: label-based claiming, a pinned STATE issue (no merge conflicts), and `@claude` on Godfrey's subscription for heavy async jobs.

**Setup (≈20 min, before 12 PM):**
1. **Godfrey (repo admin):** in the repo run `/install-github-app`, pick **subscription token**, merge the workflow PR. Then test it with `@claude say hi` on an issue. Usage goes to *his* plan.
2. **Both:** `gh auth login` (scopes `repo`, `workflow`). Godfrey adds Rafael as a collaborator with write access.
3. Create labels: `ready`, `claimed:rafael`, `claimed:godfrey`, `blocked`, `heavy` (meaning "hand to `@claude`"), `hw-test` (needs the physical Pi or MCU).
4. Open an issue named **STATE** and pin it. Live `next_action`s go there as comments, since comments never conflict. `STATE.md` becomes a snapshot that only the integrator updates, and only on `main`.
5. In `CLAUDE.md` (committed), add the protocol rules below so both Claudes follow them.
6. Add `.claude/worktrees/` to `.gitignore`. Each ticket runs in `claude -w issue-<n>`.
7. *Optional:* Discord channel plugin (§2) on each laptop for agent-to-agent notes. A shared human Discord channel is enough on its own.

**Rules for both Claudes (paste into CLAUDE.md):**
- **Claim before work:** `gh issue view <n> --json assignees,labels`. If it's unclaimed, run `gh issue edit <n> --add-assignee @me --add-label claimed:<name> --remove-label ready`, then re-read the issue to confirm you won the claim. If someone else got it, pick another ticket.
- One issue → one branch `issue-<n>` → one PR with `Closes #<n>`. Never push to `main`.
- **Directory ownership** cuts merge conflicts. Proposed split, which Rafael and Godfrey still have to agree on: MCU firmware and stepper code vs. Pi services and the web UI. Shared contracts (serial protocol, API schema) change only through a dedicated PR.
- Merge every 1–2 h and rebase before opening a PR.
- `heavy` tickets (refactors, test suites, UI scaffolds): comment `@claude implement this per the issue; open a PR`. `hw-test` tickets never go to `@claude`, because the Actions runner has no hardware.

**Failure modes:**
- **Duplicate work:** claim races are rare with 2 people. The re-read after claiming catches them.
- **Merge conflicts:** caused by shared files (package.json, the protocol header). Mitigate with the ownership split, small PRs and frequent merges.
- **Rate limits:** Rafael's Pro will likely hit its 5-hour window in a long sprint. Route bulk work to `@claude` on Godfrey's plan. That draws on Godfrey's limits **plus GitHub Actions minutes** (free on public repos; private repos get a monthly quota [u]).
- **`@claude` can't reach the Pi:** cloud runners can't touch local hardware. Keep hardware loops local.
- **Channels risk:** if you allowlist each other, either person can approve tool calls in the other's session. Don't run `--dangerously-skip-permissions` alongside it.
- **Agent teams on Pro:** "significantly more tokens". Don't use them for the core build.

## 2. Loadout table

Rafael already has GitHub MCP (read-only), context7, Playwright, chrome-devtools, Onshape and Vercel. These are the gaps, sorted by verdict.

| Tool | Unlocks | Install | Min | Risk | Verdict |
|---|---|---|---|---|---|
| **gh CLI** (instead of GitHub MCP write token) | Issues, labels, PRs and claims on the private repo | `winget install GitHub.cli` → `gh auth login` | 5 | Low (OAuth stays in gh's keyring) | **Install now** |
| **Claude GitHub App + `@claude` workflow** (Godfrey) | Heavy async jobs on Max/Ultra | `/install-github-app` | 10 | Low; app gets broad repo permissions | **Install now** |
| **Worktrees** (built in) | Parallel sessions without collisions | `claude -w issue-12`; `.worktreeinclude` for `.env` | 2 | None | **Install now** |
| **Plain OpenSSH to the Pi** (not an MCP) | Claude runs `ssh pi@<host> '<cmd>'` and `scp` via Bash | `ssh-keygen -t ed25519`, `ssh-copy-id` (or append to `authorized_keys`) | 10 | Low with a key | **Install now** |
| SSH MCP servers (li3/ssh-mcp, netixc, lgariv…) | The same, as tools | varies | 10 | Unvetted; most give an unrestricted shell; some take passwords in env vars | **Skip** (plain ssh is enough) |
| **PlatformIO Core / arduino-cli** (CLI) | Build, flash, serial from Bash | `pip install platformio` / `winget install ArduinoSA.CLI` [u id] | 10 | Low | **Install now** (whichever the MCU uses) |
| Serial monitor | Reading MCU logs | `pio device monitor` run in **background**, or a pyserial script with a timeout logging to a file | 5 | Low; an interactive monitor hangs the agent | **Install now** (script) |
| platformio-mcp / arduino-mcp | Flashing and serial as MCP tools | `uvx arduino-mcp` [u] | 15 | Unvetted, young | **If track needs** |
| **Hugging Face MCP (official)** | Model, dataset and Space search for the edge model | `claude mcp add hf-mcp-server -t http "https://huggingface.co/mcp?login"` | 5 | Low (OAuth) | **Install now** |
| Discord channel plugin (official) | Agent-to-agent and phone→session notes | `/plugin install discord@claude-plugins-official`; needs Bun; token → `~/.claude/channels/discord/.env` (move a copy to `~/.secrets/`) | 15 | Allowlisted senders can approve prompts; research preview | **If track needs** |
| Notification hook | Windows toast when Claude waits on you | `Notification` hook → PowerShell toast via `/update-config` | 5 | None | **Install now** |
| Push-guard hook | Blocks `git push` to `main` / `--force` | `PreToolUse` Bash matcher, exit 2 | 10 | None | **Install now** |
| Secret scan | Blocks commits containing tokens | `gitleaks` pre-commit (`winget install gitleaks` [u id]) | 10 | Low | **Install now** (repo is shared) |
| Format hook | Auto-format after edits | `PostToolUse` → prettier / ruff | 5 | Noisy diffs if Godfrey's formatter config differs | **If repo has a formatter config** |
| KiCad MCP (lamaalrajih) | Netlist, BOM, DRC | `uv` + `KICAD_SEARCH_PATHS` | 15+ | KiCad version unclear (7 vs 9) | **Skip** (no PCB in 24 h) |
| MQTT MCP | Pub/sub tools | none vetted found | – | – | **Skip**; use `mosquitto_pub/sub` CLI if MQTT is used |
| Bambu MCP (synman, schwarztim) | LAN printer control | Developer Mode + local MQTT | 20 | schwarztim's README describes bypassing firmware auth with a cert; unofficial | **Skip** (use Bambu Studio) |
| Devpost MCP | – | none found [u] | – | – | **Skip**; Claude-in-Chrome covers the submission |
| 21st.dev magic | Generated UI components | new key from 21st.dev/mcp → `~/.secrets/` | 5 | Paid key; overlaps the frontend skills | **Skip** unless the UI is the judged surface |
| Agent teams flag | Local multi-agent | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | 1 | Token burn on Pro | **Skip** (Godfrey may use it on his plan) |

## 3. Pro vs Max note

- **Current tiers** (claude.com/pricing, fetched today): **Pro** $20/mo or $200/yr. **Max** $100/mo gives 5× Pro every 5 h and every week. **Ultra** $200/mo has no 5-hour limit for verified accounts and 10× Pro weekly. Max and Ultra are monthly only. "Max 20x" isn't on today's page; Godfrey's plan may be a legacy 20x tier or Ultra [u]. Claude Code, cloud sessions and the GitHub Action all draw from the same pool.
- **Mid-annual upgrade is possible** (Help Center). It resets the billing cycle and invoices immediately: one full cycle of the new plan minus the unused value of Pro. If the unused annual balance is bigger than the new plan's price, the excess becomes account credit. The billing address must match the existing subscription.
- **Rough math [u]:** Aug 2026 annual, ~9 of 12 months left ≈ $150 unused. Max ($100) → ~$0 due plus ~$50 credit. Ultra ($200) → ~$50 due. You also **give up annual billing**, so going back to Pro later is a new subscription.
- **Recommendation:** don't upgrade before the event. Run on Pro, push bulk work to `@claude` on Godfrey's plan, and upgrade to **Max** only if you hit the 5-hour wall before Saturday night. The credit makes that nearly free.

## Sources
- Agent teams: https://code.claude.com/docs/en/agent-teams
- Cross-session messaging: https://code.claude.com/docs/en/cross-session-messaging
- Remote Control: https://code.claude.com/docs/en/remote-control
- Cloud sessions and sharing: https://code.claude.com/docs/en/claude-code-on-the-web
- GitHub Actions: https://code.claude.com/docs/en/github-actions · https://github.com/anthropics/claude-code-action
- Channels: https://code.claude.com/docs/en/channels
- Worktrees: https://code.claude.com/docs/en/worktrees
- Pricing: https://claude.com/pricing
- Plans / annual Pro→Max: https://support.claude.com/en/articles/11049741-choosing-a-claude-plan
- Invoices / proration: https://support.claude.com/en/articles/16607638-understanding-your-pro-max-or-ultra-plan-invoices
- HF MCP: https://github.com/huggingface/hf-mcp-server
- claude-squad: https://github.com/smtg-ai/claude-squad
- Arduino/PlatformIO MCPs: https://github.com/niradler/arduino-mcp · https://dev.to/tonythehacker/i-built-an-mcp-server-so-ai-agents-can-flash-1000-embedded-boards-5bbd
- SSH MCPs: https://github.com/li3/ssh-mcp · https://github.com/InfraMCP/ssh-mcp-server
- KiCad MCP: https://github.com/lamaalrajih/kicad-mcp
- Bambu MCPs: https://github.com/synman/bambu-mcp · https://github.com/schwarztim/bambu-mcp
- Relays [u]: https://pypi.org/project/claude-code-bridge · https://mercurialsolo.github.io/claudectl/agent-bus/
