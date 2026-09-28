#!/usr/bin/env bash
# Encode the rendered JPEG sequence + score into the deliverables.
#   ./encode.sh FRAMES_DIR SCORE_WAV OUT_DIR
set -euo pipefail
FR=$1; WAV=$2; OUT=$3; mkdir -p "$OUT"
FF=${FFMPEG:-ffmpeg}
IN=(-framerate 24 -i "$FR/%05d.jpg" -i "$WAV")
# master: grain intact
$FF -y -loglevel error "${IN[@]}" -c:v libx264 -preset slow -crf 18 -tune grain -pix_fmt yuv420p \
    -c:a aac -b:a 320k -movflags +faststart -shortest "$OUT/OUTIS_master_1080p.mp4"
# share: light temporal denoise so the grain does not eat the bitrate
$FF -y -loglevel error "${IN[@]}" -vf "hqdn3d=1.5:1.5:6:6" -c:v libx264 -preset slow -crf 22 -pix_fmt yuv420p \
    -c:a aac -b:a 256k -movflags +faststart -shortest "$OUT/OUTIS_1080p.mp4"
# web: fragmented MP4 for streaming in pieces, and a compact single-file fallback
$FF -y -loglevel error "${IN[@]}" -vf "hqdn3d=2:2:8:8" -c:v libx264 -preset slow -b:v 2000k -maxrate 3500k -bufsize 7000k \
    -g 48 -keyint_min 48 -sc_threshold 0 -pix_fmt yuv420p -c:a aac -b:a 160k \
    -movflags +frag_keyframe+empty_moov+default_base_moof -frag_duration 2000000 -shortest "$OUT/web_hd_frag.mp4"
$FF -y -loglevel error "${IN[@]}" -vf "hqdn3d=3:3:9:9,scale=1280:720:flags=lanczos" -c:v libx264 -preset slow -b:v 480k \
    -maxrate 900k -bufsize 1800k -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart -shortest "$OUT/web_compact_720p.mp4"
ls -la "$OUT"
