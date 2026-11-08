#!/usr/bin/env bash
# Decode SAME alerts from audio and send them to the hub (HUB_URL).
# Receive only: never transmit SAME audio over the air (47 CFR 11.45). The demo plays it on the box speaker only.
#
#   listen.sh [--device DEV]   Pi: USB audio input (default: first USB card in `arecord -l`)
#   listen.sh --file AUDIO     decode a WAV or any file sox reads
#   listen.sh --mac            Mac: sox default input
#   listen.sh --stdin          multimon-ng lines on stdin, e.g. `noaa.sh decode | listen.sh --stdin`
#   add --dry-run to print the alerts and send nothing
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
RAW="-t raw -r 22050 -e signed -b 16 -c 1"   # multimon-ng's EAS decoder reads 22050 Hz

usage() { sed -n '5,9p' "$0" | sed 's/^# *//'; exit 2; }

mode=pi device="" file="" dry=""
while [ $# -gt 0 ]; do
  case "$1" in
    --device) device="${2:?}"; shift 2 ;;
    --file) mode=file; file="${2:?}"; shift 2 ;;
    --mac) mode=mac; shift ;;
    --stdin) mode=stdin; shift ;;
    --dry-run) dry=--dry-run; shift ;;
    *) usage ;;
  esac
done

to_alert() ( cd "$ROOT" && exec "$PYTHON" -m software.same.same_to_alert $dry )
decode() { multimon-ng -q -t raw -a EAS -; }

# A dead decoder or Python step would leave the audio side running with no sign.
( cd "$ROOT" && "$PYTHON" -c 'import software.same.same_to_alert' ) \
  || { echo "cannot run same_to_alert with $PYTHON; set up .venv (see software/hub/README.md)" >&2; exit 1; }
[ "$mode" = stdin ] || command -v multimon-ng >/dev/null \
  || { echo "multimon-ng not found (see software/same/README.md)" >&2; exit 1; }

case "$mode" in
  pi)
    if [ -z "$device" ]; then
      line=$(arecord -l | grep -m1 -E '^card [0-9]+:.*USB' || true)
      [ -n "$line" ] || { echo "no USB audio input found; check arecord -l and pass --device" >&2; exit 1; }
      card=${line#card }
      device="plughw:${card%%:*},0"
      echo "using $line" >&2
    fi
    echo "listening on $device" >&2
    arecord -q -D "$device" -f S16_LE -r 22050 -c 1 -t raw | decode | to_alert
    ;;
  file) sox -q "$file" $RAW - | decode | to_alert ;;
  mac) sox -q -d $RAW - | decode | to_alert ;;
  stdin) to_alert ;;
esac
