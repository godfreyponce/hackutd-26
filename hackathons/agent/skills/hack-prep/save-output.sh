#!/usr/bin/env bash
# Move a /hack-prep draft onto its event file, unless the owner edited that file by hand.
#   save-output.sh <draft file> <dest file>
# <dest dir>/.hack-prep.sha256 holds the hash of what this script last wrote to each file.
# dest missing, or unchanged since the last write: replace it and record the new hash.
# Otherwise (edited, or never recorded): leave dest alone and write <dest>.new.md beside it.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: save-output.sh <draft file> <dest file>" >&2
  exit 2
fi

draft=$1
dest=$2
if [[ ! -f $draft ]]; then
  echo "save-output.sh: draft not found: $draft" >&2
  exit 1
fi

dir=$(dirname "$dest")
name=$(basename "$dest")
record="$dir/.hack-prep.sha256"

hash_of() { shasum -a 256 "$1" | cut -d' ' -f1; }

recorded=""
if [[ -f $record ]]; then
  recorded=$(awk -v n="$name" '$2 == n { print $1 }' "$record")
fi

if [[ -e $dest && ( -z $recorded || $(hash_of "$dest") != "$recorded" ) ]]; then
  new="${dest%.md}.new.md"
  mv "$draft" "$new"
  echo "kept $dest (edited by hand); new version at $new"
  exit 0
fi

mv "$draft" "$dest"
tmp=$(mktemp "$dir/.hack-prep.sha256.XXXXXX")
if [[ -f $record ]]; then
  awk -v n="$name" '$2 != n' "$record" > "$tmp"
fi
echo "$(hash_of "$dest")  $name" >> "$tmp"
mv "$tmp" "$record"
echo "wrote $dest"
