#!/usr/bin/env bash
# Link each skill folder in hackathons/agent/skills/ into ~/.claude/skills/.
# Safe to run twice; a run from another checkout repoints the links to it.
set -euo pipefail

agent_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
target="$HOME/.claude/skills"
status=0

for skill in "$agent_dir"/skills/*/; do
  skill="${skill%/}"
  name="$(basename "$skill")"
  link="$target/$name"
  if [[ -e $link && ! -L $link ]]; then
    echo "refusing: $link exists and is not a symlink; move it away first" >&2
    status=1
    continue
  fi
  ln -sfn "$skill" "$link"
  echo "linked $link -> $skill"
done

exit "$status"
