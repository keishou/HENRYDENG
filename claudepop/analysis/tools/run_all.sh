#!/usr/bin/env bash
# Regenerates claudepop/analysis/song.json and the audition wavs from the untouched song.
# All media and intermediates go to claudepop/out/ (gitignored). Each step skips work whose output exists
# (delete the file to redo it). CPU only; about 15 minutes on 4 cores, dominated by Demucs and the CTC emissions.
set -euo pipefail
CP="$(cd "$(dirname "$0")/../.." && pwd)"            # claudepop/
SONG="${SONG:-/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3}"
LY="${LY:-/home/user/johnheibel/pdoomvideo/src/lyrics.js}"
PY="$CP/out/venv/bin/python"                           # torch 2.5.1 cpu, torchaudio, demucs 4.1.0, beat-this 1.1.0, librosa
PYASR="$CP/out/venv-asr/bin/python"                    # faster-whisper (needs huggingface_hub < 2, hence its own venv)
FF="$($PY -c 'import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())')"
T="$CP/analysis/tools"
mkdir -p "$CP/out/audio" "$CP/out/work/analysis/plots"

# 1. decode (ffmpeg honours the LAME gapless header, so t=0 is the first programme sample)
for sr in 44100 48000; do
  o="$CP/out/audio/pdoom_$((sr / 1000))k.wav"
  [ -f "$o" ] || "$FF" -hide_banner -loglevel error -i "$SONG" -ar $sr -c:a pcm_f32le "$o"
done
# 2. stems: Demucs v4 htdemucs
[ -f "$CP/out/audio/stems/htdemucs/pdoom_44k/vocals.wav" ] || \
  nice -n 5 "$CP/out/venv/bin/demucs" -n htdemucs -o "$CP/out/audio/stems" "$CP/out/audio/pdoom_44k.wav"
# 3. beat grid, drum hits, bar phase, per-beat levels
[ -f "$CP/out/work/analysis/beat_this.json" ] || nice -n 5 "$PY" "$T/beats_bt.py" "$CP"
nice -n 5 "$PY" "$T/grid.py" "$CP"
# 4. vocal onsets / pitch
nice -n 5 "$PY" "$T/vocal_feats.py" "$CP"
# 5. CTC emissions (MMS_FA, wav2vec2 large lv60k 960h) at 4 sub-frame shifts, then whole-song forced alignment
nice -n 5 "$PY" "$T/emissions.py" "$CP" 4 mms,w2v
for m in mms w2v; do nice -n 5 "$PY" "$T/align_fa.py" "$CP" "$LY" $m 4 -3 1.5; done
# 6. independent transcript for sung material missing from lyrics.js
[ -f "$CP/out/work/analysis/whisper_vocals.json" ] || nice -n 5 "$PYASR" "$T/asr_whisper.py" "$CP" large-v3 vocals
# 7. combine (+ word_overrides.json, structure.json) -> analysis/song.json, click-track wavs
nice -n 5 "$PY" "$T/build_song.py" "$CP" "$LY"
# review plots (optional): zoom_post.py <cp> <t0> <t1>, zoom_plot.py <cp> <lyrics.js> <t0> <t1>, review_plots.py
