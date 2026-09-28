import librosa, numpy as np
y, sr = librosa.load('/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3', sr=22050, mono=True)
yp = librosa.effects.percussive(y, margin=2.0)
hop = 256; fr = sr / hop
S = np.abs(librosa.stft(yp, n_fft=2048, hop_length=hop))
freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
def band_env(lo, hi):
    b = S[(freqs >= lo) & (freqs < hi)].sum(0); d = np.maximum(0, np.diff(np.log1p(b * 10), prepend=0)); return np.ascontiguousarray(d, dtype=np.float64)
for name, lo, hi in [('kick <150Hz', 30, 150), ('snare/clap 1.5-5k', 1500, 5000), ('hats >7k', 7000, 11000)]:
    e = band_env(lo, hi)
    pk = librosa.util.peak_pick(e, pre_max=6, post_max=6, pre_avg=20, post_avg=20, delta=float(np.percentile(e, 90) * .5), wait=int(.12 * fr))
    ts = pk / fr; ioi = np.diff(ts)
    h, edges = np.histogram(ioi, bins=np.arange(0.1, 1.5, 0.02))
    top = sorted(zip(h, edges[:-1]), reverse=True)[:5]
    # grid scores
    def gscore(P, off):
        ph = ((ts - off) / P) % 1; d = np.minimum(ph, 1 - ph) * P; return np.mean(d < 0.04)
    print(f'{name}: {len(ts)} onsets; top IOIs', [(round(float(b)+.01,2), int(c)) for c, b in top],
          '| frac within 40ms of 132-grid', round(gscore(60/132, 0.2635), 2), '| of 88-grid(0.21)', round(gscore(60/88, 0.21), 2), '| of 88-grid best(0.288)', round(gscore(60/88, 0.288), 2))
    if name.startswith('kick'): print('  first kicks:', np.round(ts[:24], 3).tolist())
