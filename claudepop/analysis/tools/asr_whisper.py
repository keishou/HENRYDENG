"""Independent transcription of the vocal stem with Whisper large-v3 (faster-whisper / CTranslate2, CPU int8).

Used for two things only: (1) to find sung material that is not in lyrics.js (ad-libs, repeats, oohs, outro), and
(2) as a coarse third opinion on line placement. Its word times (cross-attention DTW) are too coarse (~0.1-0.3 s) to
be used as word timings. No lyric prompt is given, so the model is not steered toward the known text.

Runs in its own venv (out/venv-asr) because faster-whisper pins huggingface_hub < 2, which the main venv has.
Output: out/work/analysis/whisper_<tag>.json

usage: out/venv-asr/bin/python asr_whisper.py <claudepop_dir> [model=large-v3] [tag=vocals] [wav=vocal stem]
"""
import sys, json, time
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

ROOT = sys.argv[1]
MODEL = sys.argv[2] if len(sys.argv) > 2 else "large-v3"
TAG = sys.argv[3] if len(sys.argv) > 3 else "vocals"
WAV = sys.argv[4] if len(sys.argv) > 4 else f"{ROOT}/out/audio/stems/htdemucs/pdoom_44k/vocals.wav"
W = f"{ROOT}/out/work/analysis"

x, sr = sf.read(WAV, always_2d=True)
x = x.mean(1)
if sr != 16000:
    n = int(round(len(x) * 16000 / sr))
    x = np.interp(np.arange(n) * sr / 16000, np.arange(len(x)), x)  # analysis only; whisper is not timing-critical
x = (x / (np.abs(x).max() + 1e-9) * 0.9).astype(np.float32)

t0 = time.time()
m = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=3,
                 download_root=f"{ROOT}/out/work/models")
segs, info = m.transcribe(x, language="en", beam_size=5, temperature=0.0, word_timestamps=True,
                          condition_on_previous_text=False, vad_filter=False, no_speech_threshold=0.9)
out = []
for s in segs:
    out.append({"t": round(s.start, 2), "e": round(s.end, 2), "text": s.text.strip(), "no_speech": round(s.no_speech_prob, 3),
                "avg_logprob": round(s.avg_logprob, 3),
                "words": [{"w": w.word.strip(), "t": round(w.start, 2), "e": round(w.end, 2), "p": round(w.probability, 3)}
                          for w in (s.words or [])]})
    print(f"{s.start:7.2f}-{s.end:7.2f} {s.text.strip()}", flush=True)
json.dump({"model": MODEL, "wav": WAV.split("/claudepop/")[-1], "segments": out, "secs": round(time.time() - t0)},
          open(f"{W}/whisper_{TAG}.json", "w"), indent=1)
print("done", round(time.time() - t0), "s")
