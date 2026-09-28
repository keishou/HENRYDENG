"""Visual review of the word alignment: vocal-stem spectrogram + pitch + onsets with each method's word starts.

For every 8-second window: mel spectrogram of the vocal stem (60 Hz - 5 kHz), pYIN f0 (white), SuperFlux onsets
(ticks at the bottom), lyrics.js subtitle spans (grey bars), word starts of MMS (cyan), wav2vec2 (yellow), Whisper
(green, text) and the final song.json words (red, text). Beat grid as faint lines, downbeats stronger.

Output: out/work/analysis/plots/review_<start>.png (face-free audio plots, still kept out of git with other media)

usage: python3 review_plots.py <claudepop_dir> <lyrics.js> [win=8] [from=0] [to=157]
"""
import sys, os, json
import numpy as np
import soundfile as sf
import librosa
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from lyrics_lex import load_lines

ROOT, LY = sys.argv[1:3]
WIN = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
T_FROM = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
T_TO = float(sys.argv[5]) if len(sys.argv) > 5 else 157.0
W = f"{ROOT}/out/work/analysis"
os.makedirs(f"{W}/plots", exist_ok=True)
lines = load_lines(LY)

v, sr = sf.read(f"{ROOT}/out/audio/stems/htdemucs/pdoom_44k/vocals.wav", always_2d=True)
x = librosa.resample(v.mean(1), orig_sr=sr, target_sr=16000)
HOP = 80
M = librosa.power_to_db(librosa.feature.melspectrogram(y=x, sr=16000, n_fft=1024, hop_length=HOP, n_mels=160, fmin=60, fmax=5000), ref=np.max)
F = np.load(f"{W}/vocal_feats.npz")
ons = json.load(open(f"{W}/vocal_onsets.json"))
grid = json.load(open(f"{W}/grid.json"))


def words_of(model):
    p = f"{W}/align_{model}.json"
    if not os.path.exists(p):
        return {}
    a = json.load(open(p))
    out = {}
    for li, L in enumerate(lines):
        for wi in range(len(L["words"])):
            ts = [s["words"][f"{li}:{wi}"]["t"] for s in a["shifts"] if f"{li}:{wi}" in s["words"]]
            if ts:
                out[(li, wi)] = float(np.median(ts))
    return out


MMS, W2V = words_of("mms"), words_of("w2v")
WH = []
if os.path.exists(f"{W}/whisper_vocals.json"):
    for s in json.load(open(f"{W}/whisper_vocals.json"))["segments"]:
        WH += s["words"]
FINAL = []
sj = f"{ROOT}/analysis/song.json"
if os.path.exists(sj):
    for L in json.load(open(sj))["lines"]:
        FINAL += L["words"]

mel_f = librosa.mel_frequencies(n_mels=160, fmin=60, fmax=5000)
for a in np.arange(T_FROM, T_TO, WIN):
    b = a + WIN
    fig, ax = plt.subplots(figsize=(22, 7))
    i0, i1 = int(a * 16000 / HOP), int(b * 16000 / HOP)
    ax.imshow(M[:, i0:i1], origin="lower", aspect="auto", extent=[a, b, 0, 160], cmap="magma", vmin=-75, vmax=0)
    f0 = F["f0"]
    t10 = F["t10"]
    m = (t10 >= a) & (t10 < b)
    yb = np.interp(f0[m], mel_f, np.arange(160))
    ax.plot(t10[m], yb, ".", c="w", ms=1.5)
    for bt in grid["beats"]:
        if a <= bt < b:
            i = round((bt - grid["t0"]) / grid["beat_period"])
            ax.axvline(bt, c="w", lw=1.2 if i % 4 == 0 else 0.3, alpha=0.5)
    for t, s in ons["onsets_flux"]:
        if a <= t < b:
            ax.plot([t, t], [0, 6 + 8 * min(1, s)], c="lime", lw=1)
    for li, L in enumerate(lines):
        if L["end"] >= a and L["start"] <= b:
            ax.plot([L["start"], L["end"]], [150, 150], c="grey", lw=6, alpha=0.7)
            ax.text(max(a, L["start"]), 153, f"{li}: {L['text']}", color="w", fontsize=8)
    for (li, wi), t in MMS.items():
        if a <= t < b:
            ax.plot([t, t], [100, 145], c="cyan", lw=1)
    for (li, wi), t in W2V.items():
        if a <= t < b:
            ax.plot([t, t], [55, 100], c="yellow", lw=1)
            ax.text(t, 101, lines[li]["words"][wi][0], color="yellow", fontsize=9, rotation=90, va="bottom")
    for w in WH:
        if a <= w["t"] < b:
            ax.plot([w["t"], w["t"]], [20, 45], c="springgreen", lw=1)
            ax.text(w["t"], 22, w["w"], color="springgreen", fontsize=9, rotation=90, va="bottom")
    for w in FINAL:
        if a <= w["t"] < b:
            ax.plot([w["t"], w["t"]], [0, 160], c="red", lw=0.8, alpha=0.8)
            ax.text(w["t"], 125, w["w"], color="red", fontsize=10, rotation=90, va="bottom")
    ax.set_xlim(a, b)
    ax.set_xticks(np.arange(np.ceil(a * 4) / 4, b, 0.25), minor=True)
    ax.set_xticks(np.arange(np.ceil(a), b + 0.01, 1))
    ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(f"{W}/plots/review_{a:06.1f}.png", dpi=80)
    plt.close()
print("ok")
