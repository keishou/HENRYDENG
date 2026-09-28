"""Close-up of the vocal stem for manual verification of word starts: linear spectrogram 0-4 kHz (5 ms hop),
SuperFlux curve, 5 ms RMS, pYIN f0, 16th-note grid (beats bold), and per-model word starts.

usage: python3 zoom_plot.py <claudepop_dir> <lyrics.js> <t_from> <t_to> [out_name]
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
a, b = float(sys.argv[3]), float(sys.argv[4])
name = sys.argv[5] if len(sys.argv) > 5 else f"zoom_{a:06.2f}"
W = f"{ROOT}/out/work/analysis"
lines = load_lines(LY)
v, sr = sf.read(f"{ROOT}/out/audio/stems/htdemucs/pdoom_44k/vocals.wav", always_2d=True, start=int(a * 44100), stop=int(b * 44100))
x = librosa.resample(v.mean(1), orig_sr=sr, target_sr=16000)
S = librosa.amplitude_to_db(np.abs(librosa.stft(x, n_fft=1024, hop_length=80)), ref=np.max)
F = np.load(f"{W}/vocal_feats.npz")
g = json.load(open(f"{W}/grid.json"))
ons = json.load(open(f"{W}/vocal_onsets.json"))
fig, ax = plt.subplots(3, 1, figsize=(22, 11), gridspec_kw={"height_ratios": [4, 1, 1]}, sharex=True)
ax[0].imshow(S[:257], origin="lower", aspect="auto", extent=[a, b, 0, 4000], cmap="magma", vmin=-70)
m = (F["t10"] >= a) & (F["t10"] < b)
ax[0].plot(F["t10"][m], F["f0"][m], ".", c="w", ms=2)
T4 = g["beat_period"] / 4
k0 = int(np.ceil((a - g["t0"]) / T4))
for k in range(k0, int((b - g["t0"]) / T4) + 1):
    t = g["t0"] + k * T4
    for axx in ax:
        axx.axvline(t, c="c", lw=1.6 if k % 16 == 0 else (0.9 if k % 4 == 0 else 0.25), alpha=0.8)
mt = (F["tflux"] >= a) & (F["tflux"] < b)
ax[1].plot(F["tflux"][mt], F["flux"][mt], c="k", lw=0.8)
m5 = (F["t5"] >= a) & (F["t5"] < b)
ax[2].plot(F["t5"][m5], F["r5"][m5], c="k", lw=0.8)
for t, s in ons["onsets_flux"]:
    if a <= t < b:
        ax[1].axvline(t, c="lime", lw=1.2)
for t in ons["onsets_energy"]:
    if a <= t < b:
        ax[2].axvline(t, c="orange", lw=1.2)
for t in ons["onsets_pitch"]:
    if a <= t < b:
        ax[0].plot([t, t], [0, 250], c="w", lw=2)
cols = {"mms": "cyan", "w2v": "yellow"}
for mi, model in enumerate(("mms", "w2v")):
    A = json.load(open(f"{W}/align_{model}.json"))
    for li, L in enumerate(lines):
        for wi, (dw, _) in enumerate(L["words"]):
            ts = [s_["words"][f"{li}:{wi}"]["t"] for s_ in A["shifts"] if f"{li}:{wi}" in s_["words"]]
            if ts and a <= np.median(ts) < b:
                t = float(np.median(ts))
                y0 = 2600 + 700 * mi
                ax[0].plot([t, t], [y0, y0 + 600], c=cols[model], lw=1.5)
                ax[0].text(t, y0 + 20, dw, color=cols[model], fontsize=10, rotation=90, va="bottom")
sj = f"{ROOT}/analysis/song.json"
if os.path.exists(sj):
    for L in json.load(open(sj))["lines"]:
        for w in L["words"]:
            if a <= w["t"] < b:
                ax[0].plot([w["t"], w["t"]], [0, 2500], c="red", lw=1.3)
                ax[0].text(w["t"], 1900, w["w"], color="red", fontsize=11, rotation=90, va="bottom")
ax[2].set_xticks(np.arange(np.ceil(a * 10) / 10, b, 0.1), minor=True)
ax[2].set_xticks(np.arange(np.ceil(a * 2) / 2, b + 0.01, 0.5))
ax[2].grid(which="minor", axis="x", lw=0.2)
plt.tight_layout()
plt.savefig(f"{W}/plots/{name}.png", dpi=70)
print(f"{W}/plots/{name}.png")
