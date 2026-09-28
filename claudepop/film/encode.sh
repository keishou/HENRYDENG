#!/usr/bin/env bash
# encode.sh - master and deliveries from a rendered frame sequence (BIBLE 9.10; lane A).
#
#   film/encode.sh [RES=1080] [master|chat|artifact|all] [NAME=latent_image]
#   film/encode.sh 720 all latent_image_animatic        # stage 1: the 720p animatic (render it with --previs-tags)
#
# master    out/film/master/<NAME>_<RES>p.mp4: x264 slow CRF 16 -tune grain, yuv420p, the MP3 stream COPIED (never
#           re-encoded, no -shortest), +faststart. Then the A/V offset check (tools/av_offset.py, +-5 ms against the gapless
#           decode); if it fails, re-mux with the video delayed by the measured offset (-itsoffset, both streams copied)
#           and check again.
# chat      out/film/deliver/<NAME>_chat.mp4 < 30 MiB: two-pass x264 at 1380 kb/s video (30 MiB minus the 3.3 MiB audio
#           over 156.67 s, with margin), audio copied. Look at frame grabs of the hook, the hall and the climax
#           (out/film/deliver/grabs_<NAME>/); if blocky, rerun with CHAT_SCALE=1280:720 (lanczos from the frames).
# artifact  out/film/deliver/<NAME>_artifact/: fragmented MP4 at CRF 18 split into <= 15 MB parts + manifest.json (mime
#           with the real codec strings) for a MediaSource player.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; CP="$(dirname "$HERE")"
RES="${1:-1080}"; WHAT="${2:-all}"; NAME="${3:-latent_image}"
PY="$CP/out/venv/bin/python"; [ -x "$PY" ] || PY=python3
FF="${FFMPEG:-$("$PY" -c 'import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())')}"
MP3=/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3
FR="$CP/out/film/frames/$RES"
N=$(python3 -c "import json; print(json.load(open('$CP/shots.json'))['frames'])")
for ((f=0; f<N; f+=1)); do [ -f "$FR/$(printf %05d $f).jpg" ] || { echo "missing frame $f in $FR (render first)" >&2; exit 1; }; done
mkdir -p "$CP/out/film/master" "$CP/out/film/deliver"
IN=(-framerate 24 -i "$FR/%05d.jpg" -i "$MP3" -map 0:v:0 -map 1:a:0 -frames:v "$N")

offset_ms() { "$PY" "$HERE/tools/av_offset.py" "$1" | tee /dev/stderr | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["offset_ms"])'; }
fix_offset() {   # $1 file: check, and re-mux with the video delayed if the sound is late (or early) by more than 5 ms
  local off; off=$(offset_ms "$1" || true)
  if "$PY" -c "import sys; sys.exit(0 if abs(float('$off')) <= 5 else 1)"; then echo "A/V offset ${off} ms: ok"; return; fi
  local s; s=$("$PY" -c "print(f'{float(\"$off\")/1000:.4f}')")
  echo "A/V offset ${off} ms: re-muxing with -itsoffset $s on the video"
  "$FF" -y -v error -itsoffset "$s" -i "$1" -i "$1" -map 0:v:0 -map 1:a:0 -c copy -movflags +faststart "${1%.mp4}_av.mp4"
  mv "${1%.mp4}_av.mp4" "$1"; off=$(offset_ms "$1"); echo "after re-mux: ${off} ms"
}

if [[ "$WHAT" == master || "$WHAT" == all ]]; then
  OUT="$CP/out/film/master/${NAME}_${RES}p.mp4"
  "$FF" -y -v error -stats "${IN[@]}" -c:v libx264 -preset slow -crf 16 -tune grain -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT"
  fix_offset "$OUT"; ls -la "$OUT"
fi
if [[ "$WHAT" == chat || "$WHAT" == all ]]; then
  OUT="$CP/out/film/deliver/${NAME}_chat.mp4"; TMP="$(mktemp -d)"
  VF=(); [ -n "${CHAT_SCALE:-}" ] && VF=(-vf "scale=${CHAT_SCALE}:flags=lanczos")
  CV=(-c:v libx264 -preset slow -b:v 1380k -maxrate 2400k -bufsize 4800k -g 48 -pix_fmt yuv420p "${VF[@]}")
  ( cd "$TMP" && "$FF" -y -v error -framerate 24 -i "$FR/%05d.jpg" -frames:v "$N" "${CV[@]}" -pass 1 -an -f mp4 /dev/null \
    && "$FF" -y -v error -stats "${IN[@]}" "${CV[@]}" -pass 2 -c:a copy -movflags +faststart "$OUT" ); rm -rf "$TMP"
  fix_offset "$OUT"
  SZ=$(stat -c %s "$OUT"); echo "chat: $((SZ / 1048576)) MiB"; [ "$SZ" -lt 31457280 ] || { echo "chat delivery over 30 MiB" >&2; exit 1; }
  G="$CP/out/film/deliver/grabs_${NAME}"; mkdir -p "$G"
  for t in 2.9 5.6 26.0 45.0 97.5 142.0 150.0 152.2; do "$FF" -y -v error -ss "$t" -i "$OUT" -frames:v 1 -q:v 2 "$G/chat_${t}.jpg"; done
  echo "frame grabs to inspect: $G"
fi
if [[ "$WHAT" == artifact || "$WHAT" == all ]]; then
  D="$CP/out/film/deliver/${NAME}_artifact"; mkdir -p "$D"; FRAG="$D/full_frag.mp4"
  "$FF" -y -v error -stats "${IN[@]}" -c:v libx264 -preset slow -crf 18 -g 48 -keyint_min 48 -sc_threshold 0 -pix_fmt yuv420p \
    -c:a copy -movflags +frag_keyframe+empty_moov+default_base_moof -frag_duration 2000000 "$FRAG"
  "$PY" "$HERE/tools/split_fmp4.py" "$FRAG" "$D" 15 --prefix "$NAME"; rm -f "$FRAG"
fi
