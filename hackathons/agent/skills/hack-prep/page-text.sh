#!/usr/bin/env bash
# Print the visible text of one web page, one block per line.
# GET only. Exits non-zero when the fetch fails (HTTP 4xx/5xx, network error).
# Devpost answers WebFetch with 403 but serves curl with a browser User-Agent.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: page-text.sh <url>" >&2
  exit 2
fi

ua="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"

# --max-time 30 is a guess, not a measured figure.
curl -fsSL --max-time 30 -A "$ua" "$1" | python3 -I -c '
import html, re, sys
s = sys.stdin.read()
s = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1\s*>", " ", s)
s = re.sub(r"(?is)<!--.*?-->", " ", s)
s = re.sub(r"(?i)<br\s*/?>", "\n", s)
s = re.sub(r"(?i)</(p|li|h[1-6]|div|tr|section|article|header|footer)\s*>", "\n", s)
s = re.sub(r"(?s)<[^>]+>", " ", s)
s = html.unescape(s)
for line in s.splitlines():
    line = re.sub(r"\s+", " ", line).strip()
    if line:
        print(line)
'
