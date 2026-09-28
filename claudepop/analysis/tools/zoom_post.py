"""Close-up with evidence panels for manual word-start verification:
  1 vocal stem spectrogram 50 Hz - 8 kHz (log frequency), final word starts (red), 16th grid
  2 'other' stem spectrogram (to tell vocal notes from synth bleed)
  3 wav2vec2 per-frame character posteriors (non-blank labels, 20 ms, shift 0) with the top label printed
  4 MMS character posteriors
usage: python3 zoom_post.py <claudepop_dir> <t_from> <t_to> [name]
"""
import sys, os, json
import numpy as np
import soundfile as sf
import librosa
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = sys.argv[1]
a, b = float(sys.argv[2]), float(sys.argv[3])
name = sys.argv[4] if len(sys.argv) > 4 else f"post_{a:06.2f}"
W = f"{ROOT}/out/work/analysis"
g = json.load(open(f"{W}/grid.json"))
fig, ax = plt.subplots(4, 1, figsize=(22, 14), gridspec_kw={"height_ratios": [3, 2, 2, 2]}, sharex=True)
for i, stem in enumerate(("vocals", "other")):
    v, sr = sf.read(f"{ROOT}/out/audio/stems/htdemucs/pdoom_44k/{stem}.wav", always_2d=True, start=int(a * 44100), stop=int(b * 44100))
    x = librosa.resample(v.mean(1), orig_sr=sr, target_sr=16000)
    S = librosa.amplitude_to_db(np.abs(librosa.stft(x, n_fft=1024, hop_length=80)), ref=np.max if i == 0 else 1.0)
    fr = librosa.fft_frequencies(sr=16000, n_fft=1024)
    ax[i].pcolormesh(a + np.arange(S.shape[1]) * 80 / 16000, fr[1:], S[1:], cmap="magma", vmin=S.max() - 70, vmax=S.max(), shading="auto")
    ax[i].set_yscale("log")
    ax[i].set_ylim(60, 8000)
for j, m in enumerate(("w2v", "mms")):
    lab = json.load(open(f"{W}/emis_{m}_labels.json"))
    lp = np.load(f"{W}/emis_{m}_s0.npy").astype(np.float32)
    meta = json.load(open(f"{W}/emis_{m}_s0.json"))
    t_first = meta["first_frame_start_s"] + 0.0125
    i0, i1 = int((a - t_first) / 0.02), int((b - t_first) / 0.02)
    P = np.exp(lp[i0:i1]).T
    keep = [k for k, c in enumerate(lab) if c not in ("-",)]
    ax[2 + j].imshow(P[keep], origin="lower", aspect="auto", extent=[t_first + i0 * 0.02 - 0.01, t_first + i1 * 0.02 - 0.01, 0, len(keep)],
                     cmap="Greys", vmin=0, vmax=1)
    ax[2 + j].set_yticks(np.arange(len(keep)) + 0.5)
    ax[2 + j].set_yticklabels([lab[k] for k in keep], fontsize=6)
    for fi in range(P.shape[1]):
        k = int(np.argmax(P[:, fi]))
        if lab[k] != "-" and P[k, fi] > 0.25:
            t = t_first + (i0 + fi) * 0.02
            ax[2 + j].text(t, len(keep) + 0.3, lab[k], fontsize=9, color="red", ha="center")
    ax[2 + j].set_ylim(0, len(keep) + 2)
T4 = g["beat_period"] / 4
for k in range(int(np.ceil((a - g["t0"]) / T4)), int((b - g["t0"]) / T4) + 1):
    t = g["t0"] + k * T4
    for axx in ax:
        axx.axvline(t, c="c", lw=1.6 if k % 16 == 0 else (0.9 if k % 4 == 0 else 0.25), alpha=0.7)
ons = json.load(open(f"{W}/vocal_onsets.json"))
for t, st in ons["onsets_flux"]:
    if a <= t < b:
        ax[0].plot([t, t], [60, 60 * (1.5 + 3 * min(1, st))], c="lime", lw=2.5)
sj = f"{ROOT}/analysis/song.json"
if os.path.exists(sj):
    S_ = json.load(open(sj))
    for L in S_["lines"]:
        for w in L["words"]:
            if a <= w["t"] < b:
                ax[0].axvline(w["t"], c="red", lw=1.3)
                ax[0].text(w["t"], 5000, w["w"], color="red", fontsize=11, rotation=90, va="top", backgroundcolor="white")
    for x in S_.get("extra_vocals", []):
        for w in x.get("words", []):
            if a <= w["t"] < b:
                ax[0].axvline(w["t"], c="lime", lw=1.3)
                ax[0].text(w["t"], 5000, w["w"], color="green", fontsize=11, rotation=90, va="top", backgroundcolor="white")
ax[3].set_xticks(np.arange(np.ceil(a * 10) / 10, b, 0.1), minor=True)
ax[3].set_xticks(np.arange(np.ceil(a * 2) / 2, b + 0.01, 0.5))
plt.tight_layout()
plt.savefig(f"{W}/plots/{name}.png", dpi=66)
print(f"{W}/plots/{name}.png")
