import librosa, numpy as np
y, sr = librosa.load('/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3', sr=22050, mono=True)
yp = librosa.effects.percussive(y, margin=2.0); hop = 128; fr = sr / hop
S = np.abs(librosa.stft(yp, n_fft=2048, hop_length=hop)); f = librosa.fft_frequencies(sr=sr, n_fft=2048)
res = {}
for name, lo, hi in [('kick', 30, 150), ('snare', 1500, 5000), ('full', 30, 11000)]:
    b = S[(f >= lo) & (f < hi)].sum(0); e = np.maximum(0, np.diff(np.log1p(b * 10), prepend=0))
    e = e - e.mean(); ac = np.correlate(e, e, 'full')[len(e) - 1:]; ac /= ac[0]
    P = 0.22727
    # refine pulse from autocorrelation peak near 8 pulses
    row = []
    for k in [2, 3, 4, 6, 8, 12, 16, 24, 32]:
        lag = int(round(k * P * fr)); w = ac[lag - 3:lag + 4].max(); row.append((k, round(float(w), 3)))
    print(name, row)
# per-pulse accent profile inside a 16-pulse (132bpm 2-bar / 88bpm 1.33 bar) vs 12-pulse window
b = S[(f >= 30) & (f < 150)].sum(0); ek = np.maximum(0, np.diff(np.log1p(b * 10), prepend=0))
b = S[(f >= 1500) & (f < 5000)].sum(0); es = np.maximum(0, np.diff(np.log1p(b * 10), prepend=0))
P = 60 / 264; off = 0.209
def prof(e, n, t0=23.0, t1=58.0):
    acc = np.zeros(n); cnt = np.zeros(n)
    k0 = int(np.ceil((t0 - off) / P)); k1 = int((t1 - off) / P)
    for k in range(k0, k1):
        i = int(round((off + k * P) * fr)); acc[k % n] += e[max(0, i - 3):i + 4].max(); cnt[k % n] += 1
    v = acc / cnt; return np.round(v / v.max(), 2).tolist()
for n in [8, 12, 16, 24]:
    print('pulse-profile mod', n, 'kick', prof(ek, n)); print('pulse-profile mod', n, 'snare', prof(es, n))
