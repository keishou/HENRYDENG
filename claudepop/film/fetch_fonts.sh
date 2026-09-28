#!/usr/bin/env bash
# Fetch the SIL-OFL fonts used by src/hud.js into claudepop/out/fonts/ (gitignored). Source: github.com/google/fonts (main).
set -euo pipefail
OUT="$(cd "$(dirname "$0")/.." && pwd)/out/fonts"; mkdir -p "$OUT"
F=https://raw.githubusercontent.com/google/fonts/main/ofl
get() { [ -s "$OUT/$2" ] || curl -sSf -o "$OUT/$2" "$F/$1"; }
get "intertight/InterTight%5Bwght%5D.ttf" InterTight.ttf
get ibmplexmono/IBMPlexMono-Regular.ttf IBMPlexMono-Regular.ttf
get ibmplexmono/IBMPlexMono-Medium.ttf IBMPlexMono-Medium.ttf
get barlowcondensed/BarlowCondensed-Medium.ttf BarlowCondensed-Medium.ttf
get barlowcondensed/BarlowCondensed-SemiBold.ttf BarlowCondensed-SemiBold.ttf
get instrumentserif/InstrumentSerif-Regular.ttf InstrumentSerif-Regular.ttf
get instrumentserif/InstrumentSerif-Italic.ttf InstrumentSerif-Italic.ttf
for f in intertight ibmplexmono barlowcondensed instrumentserif; do get "$f/OFL.txt" "OFL-$f.txt"; done
ls -1 "$OUT"
