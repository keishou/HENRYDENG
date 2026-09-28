"""Rhythm, drums, energy and event analysis for "I'm Upping My P(doom)".

Inputs (analysis copies, never the song itself):
  <scratch>/pdoom44k.wav            full mix decoded from assets/pdoom.mp3 (ffmpeg, 44.1 kHz)
  <scratch>/stems/instrumental.wav  MDX-Net (Kim_Vocal_2) instrumental
  <scratch>/stems/vocals.wav        MDX-Net vocal stem
  <scratch>/mm_db_34.npy            madmom DBNDownBeatTracker output [time, beat-in-bar]
Output: <out>/rhythm.json (grid, 10 Hz loudness/brightness curves, per-beat instrumental level).
Drum hits are transcribed separately by hits.py.

usage: python3 rhythm.py <scratch_dir> <out_dir>
"""
import sys, json, os
import numpy as np
import soundfile as sf
import scipy.signal as ss
import librosa
import pyloudnorm as pyln

SCR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

mix, sr = sf.read(f"{SCR}/pdoom44k.wav")
ins, _ = sf.read(f"{SCR}/stems/instrumental.wav")
voc, _ = sf.read(f"{SCR}/stems/vocals.wav")
DUR = len(mix) / sr
mixm, insm, vocm = mix.mean(1), ins.mean(1), voc.mean(1)

# ---------------------------------------------------------------- beat grid
# The song is machine-quantised: a free linear fit to madmom's 341 beats gives 132.002 BPM with 5.7 ms residual std,
# and a comb search over the onset envelope peaks sharply at exactly 132.000 BPM. So the grid is a fixed-tempo grid.
BPM = 132.0
T = 60.0 / BPM
mm = np.load(f"{SCR}/mm_db_34.npy")
# phase estimates: madmom linear fit (0.2351), broadband flux comb (0.2435), kick-attack max-rise (0.229-0.240)
k = np.arange(len(mm))
fit = np.polyfit(k, mm[:, 0], 1)
T0 = 0.235  # consensus of madmom fit (0.2351), onset-envelope comb (0.243), kick attacks (0.229-0.240), CNN onsets (0.231); +-8 ms
first_db_beat = int(mm[0, 1])  # madmom says the first detected beat is beat 1 of a bar
nbeats = int(np.floor((DUR - T0) / T)) + 1
beats = [round(T0 + i * T, 4) for i in range(nbeats)]
downbeats = beats[::4]

# ---------------------------------------------------------------- loudness / energy curves at 10 Hz
meter = pyln.Meter(sr)  # BS.1770 K-weighting


def kweight(x):
    y = x.copy()
    for f in meter._filters.values():
        y = f.apply_filter(y)
    return y


def momentary_lufs(x2ch, hop_s=0.1, win_s=0.4):
    y = np.stack([kweight(x2ch[:, c]) for c in range(x2ch.shape[1])], 1)
    p = (y ** 2).sum(1)
    hop, win = int(hop_s * sr), int(win_s * sr)
    c = np.concatenate([[0], np.cumsum(p)])
    out = []
    for i in range(int(np.ceil(len(p) / hop))):
        ctr = i * hop
        a, b = max(0, ctr - win // 2), min(len(p), ctr + win // 2)
        out.append(-0.691 + 10 * np.log10((c[b] - c[a]) / max(1, b - a) + 1e-12))
    return np.array(out)


lufs = momentary_lufs(mix)
lufs_voc = momentary_lufs(voc)
lufs_ins = momentary_lufs(ins)
N10 = len(lufs)
t10 = np.arange(N10) * 0.1

hop10 = int(0.1 * sr)
S = np.abs(librosa.stft(mixm, n_fft=4096, hop_length=hop10, center=True))[:, :N10]
freqs = librosa.fft_frequencies(sr=sr, n_fft=4096)
cent = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
lowE = 10 * np.log10((S[(freqs < 150)] ** 2).sum(0) + 1e-9)
highE = 10 * np.log10((S[(freqs > 5000)] ** 2).sum(0) + 1e-9)
integrated = meter.integrated_loudness(mix)

# ---------------------------------------------------------------- instrumental level per beat (for stops/drops)
ins_db_beat = []
for bt in beats:
    a, b = int(bt * sr), int(min(DUR, bt + T) * sr)
    ins_db_beat.append(10 * np.log10(np.mean(insm[a:b] ** 2) + 1e-12))
ins_db_beat = np.array(ins_db_beat)

out = {
    "source": "assets/pdoom.mp3 decoded with ffmpeg to PCM; t=0 is the first decoded sample",
    "duration": round(DUR, 3),
    "bpm": BPM,
    "beat_period": T,
    "t0": T0,
    "madmom_free_fit": {"bpm": 60 / fit[0], "t0": fit[1]},
    "time_signature": "4/4",
    "beats": beats,
    "downbeats": downbeats,
    "integrated_lufs": round(float(integrated), 2),
    "curves10hz": {
        "t0": 0.0, "dt": 0.1,
        "lufs": [round(float(v), 1) for v in lufs],
        "lufs_vocal": [round(float(v), 1) for v in lufs_voc],
        "lufs_inst": [round(float(v), 1) for v in lufs_ins],
        "centroid_hz": [int(v) for v in cent],
        "low_db": [round(float(v), 1) for v in lowE],
        "high_db": [round(float(v), 1) for v in highE],
    },
    "ins_db_beat": [round(float(v), 1) for v in ins_db_beat],
}
json.dump(out, open(f"{OUT}/rhythm.json", "w"))
print("beats", len(beats), "integrated LUFS", integrated)
