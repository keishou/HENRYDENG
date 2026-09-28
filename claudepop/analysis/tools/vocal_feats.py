"""Vocal-stem features used to snap and check word timings.

  onsets_flux   SuperFlux-style onsets (log-mel flux with a frequency max-filter, lag 2 frames, 5 ms hop), which
                ignores most vibrato; times are the flux peak minus half the analysis hop
  onsets_energy energy onsets: 5 ms RMS rising >= 10 dB within 60 ms out of a local dip (>= 12 dB under the loud level)
  onsets_pitch  pYIN note changes: median pitch jumps >= 0.8 semitone that hold for >= 50 ms
  onsets_voice  pYIN unvoiced -> voiced transitions
  f0, voiced probability, RMS (10 ms hop) for vocal activity and phrase detection

Input : out/audio/stems/htdemucs/pdoom_44k/vocals.wav
Output: out/work/analysis/vocal_feats.npz and vocal_onsets.json

usage: python3 vocal_feats.py <claudepop_dir>
"""
import sys, json
import numpy as np
import soundfile as sf
import librosa
import scipy.signal as ss
from scipy.ndimage import maximum_filter1d, median_filter

ROOT = sys.argv[1]
W = f"{ROOT}/out/work/analysis"
v, sr0 = sf.read(f"{ROOT}/out/audio/stems/htdemucs/pdoom_44k/vocals.wav", always_2d=True)
SR = 16000
x = librosa.resample(v.mean(1), orig_sr=sr0, target_sr=SR, res_type="soxr_hq").astype(np.float32)
DUR = len(x) / SR

# ---------------------------------------------------------------- SuperFlux onsets (5 ms hop)
HOP = 80
M = librosa.feature.melspectrogram(y=x, sr=SR, n_fft=1024, hop_length=HOP, n_mels=138, fmin=60, fmax=8000, center=True)
LM = np.log10(1 + 100 * M)
LMf = maximum_filter1d(LM, 3, axis=0)
lag = 2
flux = np.zeros(LM.shape[1])
flux[lag:] = np.maximum(0, LM[:, lag:] - LMf[:, :-lag]).sum(0)
tflux = np.arange(len(flux)) * HOP / SR
# adaptive threshold: local mean over +-100 ms + delta; local max over +-30 ms; min gap 60 ms
w_mean = int(0.1 * SR / HOP)
w_max = int(0.03 * SR / HOP)
mean_ = np.convolve(flux, np.ones(2 * w_mean + 1) / (2 * w_mean + 1), mode="same")
mx = maximum_filter1d(flux, 2 * w_max + 1)
delta = 0.35 * np.percentile(flux, 95)
cand = np.where((flux == mx) & (flux >= mean_ + delta))[0]
keep = []
for c in cand:
    if keep and (c - keep[-1]) * HOP / SR < 0.06:
        if flux[c] > flux[keep[-1]]:
            keep[-1] = c
        continue
    keep.append(c)
on_flux = tflux[keep] - lag * HOP / SR / 2
on_flux_s = flux[keep] / np.percentile(flux[keep], 95)

# ---------------------------------------------------------------- RMS (5 ms) energy onsets (the stem is rarely silent:
# reverb and bleed keep it within ~25 dB of its loud level, so onsets are rises out of local dips)
H5 = 80
rms5 = librosa.feature.rms(y=x, frame_length=320, hop_length=H5, center=True)[0]
r5 = 20 * np.log10(rms5 + 1e-7)
t5 = np.arange(len(r5)) * H5 / SR
ref = np.percentile(r5, 95)
on_en = []
# rise of >= 10 dB within 60 ms out of a local level minimum that sits at least 12 dB under the 95th percentile
look = int(0.06 * SR / H5)
r5s = np.convolve(r5, np.ones(3) / 3, mode="same")
mins = ss.argrelmin(r5s, order=int(0.03 * SR / H5))[0]
for i in mins:
    if r5s[i] > ref - 12 or i + look >= len(r5s):
        continue
    seg = r5s[i:i + look]
    if seg.max() - r5s[i] >= 10:
        j = i + int(np.argmax(seg > r5s[i] + 3))  # first frame 3 dB above the minimum
        on_en.append(t5[j])
on_en = np.array(on_en)

# ---------------------------------------------------------------- pYIN pitch (10 ms)
H10 = 160
f0, vflag, vprob = librosa.pyin(x, fmin=110, fmax=1100, sr=SR, frame_length=1024, hop_length=H10, center=True)
t10 = np.arange(len(f0)) * H10 / SR
rms10 = librosa.feature.rms(y=x, frame_length=640, hop_length=H10, center=True)[0][:len(f0)]
midi = 69 + 12 * np.log2(np.where(np.isfinite(f0), f0, np.nan) / 440)
ms = median_filter(np.nan_to_num(midi, nan=0.0), 5)
pc = []
k = 5
for i in range(k, len(midi) - k):
    a, b = midi[i - k:i], midi[i:i + k]
    if np.sum(np.isfinite(a)) >= 3 and np.sum(np.isfinite(b)) >= 5:
        if abs(np.nanmedian(b) - np.nanmedian(a)) >= 0.8:
            pc.append(t10[i])
pc2 = []
for t in pc:
    if not pc2 or t - pc2[-1] > 0.08:
        pc2.append(t)
on_pitch = np.array(pc2)
vo = t10[1:][(vprob[1:] > 0.5) & (vprob[:-1] <= 0.5)]
on_voice = np.array(vo)

np.savez(f"{W}/vocal_feats.npz", f0=f0, vprob=vprob, rms10=rms10, t10=t10, r5=r5, t5=t5, flux=flux, tflux=tflux)
json.dump({"ref_db_5ms": float(ref),
           "onsets_flux": [[round(float(t), 4), round(float(s), 3)] for t, s in zip(on_flux, on_flux_s)],
           "onsets_energy": [round(float(t), 4) for t in on_en],
           "onsets_pitch": [round(float(t), 3) for t in on_pitch],
           "onsets_voice": [round(float(t), 3) for t in on_voice]}, open(f"{W}/vocal_onsets.json", "w"))
print("flux", len(on_flux), "energy", len(on_en), "pitch", len(on_pitch), "voice", len(on_voice))
