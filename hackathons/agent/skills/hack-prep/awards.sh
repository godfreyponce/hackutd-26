#!/usr/bin/env bash
# Print the winners of one Devpost project gallery, one award per line:
#   <award text>\t<project name>\t<project url>
# Devpost names which prize a project won only in the page's JSON-LD ItemList,
# which page-text.sh drops with the other <script> blocks.
# No ItemList means no winners yet: prints nothing, exits 0.
# GET only. Exits non-zero when the fetch fails (HTTP 4xx/5xx, network error).
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: awards.sh <gallery url>" >&2
  exit 2
fi

ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"

# --max-time 30 is a guess, not a measured figure.
curl -fsSL --max-time 30 -A "$ua" "$1" | python3 -I -c '
import json, re, sys
s = sys.stdin.read()
seen = set()
for block in re.findall(r"(?is)<script[^>]*application/ld\+json[^>]*>(.*?)</script\s*>", s):
    data = json.loads(block)
    if not isinstance(data, dict) or data.get("@type") != "ItemList":
        continue
    for item in data.get("itemListElement", []):
        # Collapse whitespace so a tab or newline in a name cannot split a TSV row.
        name = " ".join(str(item.get("name", "")).split())
        url = str(item.get("url", "")).strip()
        for award in item.get("award", []):
            row = (" ".join(str(award).split()), name, url)
            if row not in seen:
                seen.add(row)
                print("\t".join(row))
'
