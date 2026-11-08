#!/bin/sh
# Redo the PNG exports from the SVGs. Needs rsvg-convert and magick (brew install librsvg imagemagick).
# Run from anywhere: sh docs/brand/export-png.sh
set -eu
cd "$(dirname "$0")"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

export_png() {
  out=$1 canvas=$2 wordmark_width=$3
  rsvg-convert -w "$wordmark_width" land-wordmark-white.svg -o "$tmp/mark.png"
  magick -size "$canvas" xc:'#0b1a33' "$tmp/mark.png" -gravity center -composite -depth 8 -strip "$out"
}

export_png land-social-1280x640.png 1280x640 640
export_png land-devpost-1500x1000.png 1500x1000 780
