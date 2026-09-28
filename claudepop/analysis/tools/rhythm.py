"""Rhythm, drums, energy and event analysis for "I'm Upping My P(doom)".

Inputs (analysis copies, never the song itself):
  <scratch>/pdoom44k.wav            full mix decoded from assets/pdoom.mp3 (ffmpeg, 44.1 kHz)
  <scratch>/stems/instrumental.wav  MDX-Net (Kim_Vocal_2) instrumental
  <scratch>/stems/vocals.wav        MDX-Net vocal stem
  <scratch>/mm_db_34.npy            madmom DBNDownBeatTracker output [time, beat-in-bar]
Output: <out>/rhythm.json

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
T0 = 0.238  # chosen compromise of the three estimates; uncertainty about +-8 ms
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

# ---------------------------------------------------------------- drum hits (instrumental stem)
HOP = 128
fps = sr / HOP
Sx = np.abs(librosa.stft(insm, n_fft=2048, hop_length=HOP))
H, P = librosa.decompose.hpss(Sx, margin=(1.0, 2.0))
fq = librosa.fft_frequencies(sr=sr, n_fft=2048)


def band_flux(M, lo, hi):
    L = np.log1p(1000 * M[(fq >= lo) & (fq < hi)])
    return np.maximum(0, np.diff(L, axis=1, prepend=L[:, :1])).mean(0)


def band_db(M, lo, hi):
    return 10 * np.log10((M[(fq >= lo) & (fq < hi)] ** 2).sum(0) + 1e-10)


fl_kick = band_flux(P, 30, 130)
fl_clap = band_flux(P, 1500, 9000)
fl_hat = band_flux(P, 9000, 15500)
db_kick = band_db(P, 30, 130)
db_clap = band_db(P, 1500, 9000)
db_hat = band_db(P, 9000, 15500)


def pick(fl, thr_k, min_gap):
    # adaptive threshold: median over +-1 s plus k * MAD
    med = ss.medfilt(fl, 2 * int(fps * 0.5) + 1)
    mad = ss.medfilt(np.abs(fl - med), 2 * int(fps * 0.5) + 1)
    th = med + thr_k * mad + 1e-3
    pk, _ = ss.find_peaks(fl, height=th, distance=max(1, int(min_gap * fps)))
    return pk


def grid_pos(t):
    """bar (1-based), beat (1..4), sixteenth (1..4) of time t, plus offset (s) from nearest 16th."""
    q = (t - T0) / (T / 4)
    qi = int(np.round(q))
    return {"bar": qi // 16 + 1, "beat": (qi // 4) % 4 + 1, "six": qi % 4 + 1, "off": round((q - qi) * T / 4, 4)}


hits = []
for name, fl, dbc, kk, gap in [("kick", fl_kick, db_kick, 4.0, 0.09), ("clap", fl_clap, db_clap, 4.0, 0.09),
                               ("hat", fl_hat, db_hat, 5.0, 0.07)]:
    pk = pick(fl, kk, gap)
    for p in pk:
        t = librosa.frames_to_time(p, sr=sr, hop_length=HOP, n_fft=2048)
        # strength = dB rise over the 60 ms before the onset
        a = max(0, p - int(0.06 * fps))
        rise = float(dbc[p:p + 4].max() - dbc[a:p].min()) if p > a else 0.0
        if rise < 3.0:
            continue
        g = grid_pos(t)
        hits.append({"t": round(float(t), 3), "type": name, "rise_db": round(rise, 1), "flux": round(float(fl[p]), 3), **g})
hits.sort(key=lambda h: (h["t"], h["type"]))

# relative strength 0..1 per type
for name in ("kick", "clap", "hat"):
    hs = [h for h in hits if h["type"] == name]
    if not hs:
        continue
    ref = np.percentile([h["flux"] for h in hs], 95)
    for h in hs:
        h["s"] = round(min(1.0, h["flux"] / ref), 2)

# ---------------------------------------------------------------- per-beat drum pattern summary
beat_rows = []
for i, bt in enumerate(beats):
    row = {"i": i, "t": bt, "bar": i // 4 + 1, "beat": i % 4 + 1}
    for name in ("kick", "clap", "hat"):
        row[name] = sum(1 for h in hits if h["type"] == name and bt - 0.03 <= h["t"] < bt + T - 0.03)
    j = int(round(bt * 10))
    row["lufs"] = round(float(lufs[min(j, N10 - 1)]), 1)
    beat_rows.append(row)

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
    "hits": hits,
    "beat_rows": beat_rows,
    "ins_db_beat": [round(float(v), 1) for v in ins_db_beat],
}
json.dump(out, open(f"{OUT}/rhythm.json", "w"))
print("beats", len(beats), "hits", {n: sum(h["type"] == n for h in hits) for n in ("kick", "clap", "hat")},
      "integrated LUFS", integrated)
