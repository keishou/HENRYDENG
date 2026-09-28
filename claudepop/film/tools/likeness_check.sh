#!/usr/bin/env bash
# likeness_check.sh - face_similarity (ArcFace, avatar venv) on PRE-GRADE frames of the frontal shots, to catch light that
# destroys the likeness (BIBLE 9.8.5). Scores and thresholds stay under claudepop/out/ (the repo is public).
#
#   film/tools/likeness_check.sh [--res 720] [--every 6] S02 S05 S06 S41 S01     render pregrade frames, score every 6th
#   film/tools/likeness_check.sh FILE_OR_DIR ...                                 score images / dirs / videos directly
#
# Shot ids render with: node film/render.mjs --layer pregrade --res <res> --shots <ids> (cached like any render) into
# out/film/frames/<res>_pregrade/, then every Nth frame of each shot is linked into out/film/data/likeness/<stamp>/<shot>/
# and scored by claudepop/avatar/tools/face_similarity.py (verdicts from out/avatar/identity/scorer_calibration.json).
# The JSON report: out/film/data/likeness/<stamp>/scores.json.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; FILM="$(dirname "$HERE")"; CP="$(dirname "$FILM")"
PY="$CP/out/venv-avatar/bin/python"; SIM="$CP/avatar/tools/face_similarity.py"
RES=720; EVERY=6; SHOTS=(); FILES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --res) RES="$2"; shift 2;;
    --every) EVERY="$2"; shift 2;;
    S[0-9]*) SHOTS+=("$1"); shift;;
    *) FILES+=("$1"); shift;;
  esac
done
STAMP=$(date +%Y%m%d-%H%M%S); OUT="$CP/out/film/data/likeness/$STAMP"; mkdir -p "$OUT"
if [ ${#SHOTS[@]} -gt 0 ]; then
  IDS=$(IFS=,; echo "${SHOTS[*]}")
  export PLAYWRIGHT_DISABLE_FORCED_CHROMIUM_PROXIED_LOOPBACK=1
  node "$FILM/render.mjs" --res "$RES" --layer pregrade --shots "$IDS"
  for S in "${SHOTS[@]}"; do
    read -r F0 F1 < <(python3 -c "import json,sys; s=[x for x in json.load(open('$CP/shots.json'))['shots'] if x['id']=='$S'][0]; print(*s['frames'])")
    mkdir -p "$OUT/$S"
    for ((f=F0; f<F1; f+=EVERY)); do ln -sf "$CP/out/film/frames/${RES}_pregrade/$(printf %05d $f).jpg" "$OUT/$S/"; done
    FILES+=("$OUT/$S")
  done
fi
[ ${#FILES[@]} -gt 0 ] || { echo "usage: $0 [--res 720] [--every 6] SHOT... | FILE_OR_DIR..." >&2; exit 2; }
"$PY" "$SIM" "${FILES[@]}" --json "$OUT/scores.json"
echo "report: $OUT/scores.json"
