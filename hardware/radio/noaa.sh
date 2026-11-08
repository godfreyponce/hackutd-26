#!/usr/bin/env bash
# NOAA Weather Radio with the RTL-SDR Blog V4 on the Pi.
# Usage: noaa.sh scan | record [SECONDS] [FREQ] | decode [FREQ] | fm
set -euo pipefail
FREQ_DEFAULT=162.400M   # strongest NOAA channel at UTD (measured 2026-11-07)
GAIN=49.6
CHANNELS="162.400 162.425 162.450 162.475 162.500 162.525 162.550"

case "${1:-}" in
  scan)  # signal strength on the 7 NOAA channels, dB above the noise floor
    rtl_power -f 162.375M:162.575M:12.5k -g "$GAIN" -i 5 -1 /tmp/noaa.csv >/dev/null 2>&1
    python3 - "$CHANNELS" <<'PY'
import csv, sys
pts = []
for r in csv.reader(open('/tmp/noaa.csv')):
    lo, step = float(r[2]), float(r[4])
    pts += [(lo + i * step, float(v)) for i, v in enumerate(r[6:])]
floor = sorted(v for _, v in pts)[len(pts) // 2]
for c in map(float, sys.argv[1].split()):
    near = [v for f, v in pts if abs(f / 1e6 - c) < 0.008]
    print(f"{c:.3f} MHz  +{max(near) - floor:5.1f} dB")
PY
    ;;
  record)  # narrow-FM audio to a WAV file
    SECS="${2:-60}"; FREQ="${3:-$FREQ_DEFAULT}"; OUT="noaa_${FREQ%M}_$(date +%Y%m%d_%H%M%S).wav"
    # timeout stops rtl_fm too: it can outlive sox and keep the stick busy
    timeout $((SECS + 5)) rtl_fm -M fm -f "$FREQ" -s 22050 -g "$GAIN" -E deemp -l 0 2>/dev/null \
      | sox -t raw -r 22050 -e signed -b 16 -c 1 - "$OUT" trim 0 "$SECS" || true
    echo "saved $OUT"
    ;;
  decode)  # live SAME/EAS alert decoding; prints ZCZC-... headers when an alert airs
    FREQ="${2:-$FREQ_DEFAULT}"
    rtl_fm -M fm -f "$FREQ" -s 22050 -g "$GAIN" -E deemp -l 0 2>/dev/null \
      | multimon-ng -t raw -a EAS -
    ;;
  fm)  # sanity check: strongest FM broadcast stations
    rtl_power -f 88M:108M:100k -g 30 -i 4 -1 /tmp/fm.csv >/dev/null 2>&1
    sort -t, -k7 -gr /tmp/fm.csv | head -3 | cut -d, -f3
    ;;
  *) echo "usage: $0 scan | record [SECONDS] [FREQ] | decode [FREQ] | fm"; exit 2 ;;
esac
