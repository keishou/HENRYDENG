"""Drum-hit transcription on the MDX instrumental stem.

1. madmom CNNOnsetProcessor + peak picking on the instrumental stem (10 ms resolution) -> onsets
2. per onset, band features on the HPSS percussive spectrum (rise vs. the 12-45 ms before, peak level, 120 ms decay)
3. rule-based classification: kick (sub/low rise + level), clap/snare (sustained 5-9 kHz noise tail + 1.5-5 kHz level),
   hat (9-16 kHz rise, not kick/clap), perc (anything else: plucks, stabs, bass notes)
Thresholds were set by inspecting the four-on-the-floor sections (kick on every beat, clap on 2 and 4, open hat on
the off-beat 8ths) - see REPORT.md.

usage: python3 hits.py <scratch> <out.json>
"""
import sys, json
import numpy as np
import soundfile as sf
import librosa

SP, OUT = sys.argv[1:3]
T, T0 = 60 / 132, 0.235
x, sr = sf.read(f"{SP}/stems/instrumental.wav")
x = x.mean(1)
on = np.load(f"{SP}/mm_onsets_instrumental.npy")
HOP, NF = 64, 1024
S = np.abs(librosa.stft(x, n_fft=NF, hop_length=HOP))
_, P = librosa.decompose.hpss(S, margin=(1.0, 1.5))
fq = librosa.fft_frequencies(sr=sr, n_fft=NF)
bands = [(20, 150), (150, 400), (400, 1500), (1500, 5000), (5000, 9000), (9000, 16000)]


def bdb(M, lo, hi):
    return 10 * np.log10((M[(fq >= lo) & (fq < hi)] ** 2).sum(0) + 1e-10)


BP = np.array([bdb(P, lo, hi) for lo, hi in bands])
BS = np.array([bdb(S, lo, hi) for lo, hi in bands])
fps = sr / HOP
hits = []
for t in on:
    i = int(round(t * fps))
    a, b, c = max(0, i - int(0.045 * fps)), max(1, i - int(0.012 * fps)), i + int(0.035 * fps)
    rise = BP[:, max(0, i - 3):c].max(1) - BP[:, a:b].mean(1)
    lvl = BS[:, i:c].max(1)
    dec = BS[:, min(BS.shape[1] - 1, i + int(0.12 * fps))] - lvl
    types = []
    if rise[0] >= 12 and lvl[0] >= 33:
        types.append("kick")
    if dec[4] >= -11 and lvl[3] >= 23 and rise[3] >= 8:
        types.append("clap")
    if not types and rise[5] >= 10 and lvl[5] >= 12:
        types.append("hat")
    if not types:
        types.append("perc")
    q = (t - T0) / (T / 4)
    qi = int(round(q))
    for ty in types:
        lv = {"kick": lvl[0], "clap": lvl[3], "hat": lvl[5], "perc": lvl[2]}[ty]
        hits.append({"t": round(float(t), 3), "type": ty, "bar": qi // 16 + 1, "beat": (qi // 4) % 4 + 1, "six": qi % 4 + 1,
                     "off_ms": int(round((q - qi) * T / 4 * 1000)), "_lvl": float(lv)})
# strength 0..1 per type (level relative to the type's 5th..98th percentile)
for ty in ("kick", "clap", "hat", "perc"):
    hs = [h for h in hits if h["type"] == ty]
    if not hs:
        continue
    lo, hi = np.percentile([h["_lvl"] for h in hs], [5, 98])
    for h in hs:
        h["s"] = round(float(np.clip((h["_lvl"] - lo) / (hi - lo + 1e-9), 0, 1)), 2)
for h in hits:
    del h["_lvl"]
json.dump(hits, open(OUT, "w"))
from collections import Counter
print(Counter(h["type"] for h in hits))
