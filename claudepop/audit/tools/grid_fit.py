# Fit the true beat grid from kick onsets and score both grids. Writes beatgrid.json for reuse.
import librosa, numpy as np, json
y, sr = librosa.load('/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3', sr=44100, mono=True)
yp = librosa.effects.percussive(y, margin=2.0); hop = 128; fr = sr / hop
S = np.abs(librosa.stft(yp, n_fft=4096, hop_length=hop)); f = librosa.fft_frequencies(sr=sr, n_fft=4096)
b = S[(f >= 30) & (f < 150)].sum(0); e = np.maximum(0, np.diff(np.log1p(b * 10), prepend=0))
e = np.ascontiguousarray(e, dtype=np.float64)
pk = librosa.util.peak_pick(e, pre_max=8, post_max=8, pre_avg=40, post_avg=40, delta=float(np.percentile(e, 90) * .5), wait=int(.15 * fr))
ts = pk / fr
# robust fit: assign each kick to nearest index of a 0.4545 grid starting 0.209, then least squares
P0, O0 = 60 / 132, 0.209
for _ in range(3):
    k = np.round((ts - O0) / P0); r = ts - (O0 + k * P0); m = np.abs(r) < 0.05
    A = np.vstack([k[m], np.ones(m.sum())]).T; P0, O0 = np.linalg.lstsq(A, ts[m], rcond=None)[0]
k = np.round((ts - O0) / P0); r = ts - (O0 + k * P0)
def hit(P, O, tol=.035):
    g = np.arange(O, 156.6, P); d = np.min(np.abs(g[:, None] - ts[None, :]), axis=1); return float(np.mean(d < tol))
out = dict(kick_onsets=len(ts), fitted_bpm=round(60 / P0, 3), period=round(float(P0), 5), offset=round(float(O0), 4),
           kicks_on_grid_frac=round(float(np.mean(np.abs(r) < .035)), 3), resid_ms_median=round(float(np.median(np.abs(r[np.abs(r) < .05])) * 1000), 1),
           grid132_beats_with_kick=round(hit(P0, O0), 3), old88_beats_with_kick=round(hit(60 / 88, .21), 3),
           old88_even_beats_with_kick=round(hit(2 * 60 / 88, .21), 3), old88_odd_beats_with_kick=round(hit(2 * 60 / 88, .21 + 60 / 88), 3))
print(json.dumps(out, indent=1)); json.dump(out, open('beatgrid.json', 'w'), indent=1)
# strength-weighted: mean low-band onset strength at grid points (max within +-25 ms), relative to the 132 grid
def strength(P, O):
    g = np.arange(O, 156.6, P); idx = np.round(g * fr).astype(int); w = int(.025 * fr)
    return float(np.mean([e[max(0, i - w):i + w + 1].max() for i in idx if i < len(e)]))
s132 = strength(P0, O0)
st = dict(s132=1.0, s132_offbeat=round(strength(P0, O0 + P0 / 2) / s132, 3), old88_all=round(strength(60 / 88, .21) / s132, 3),
          old88_even=round(strength(2 * 60 / 88, .21) / s132, 3), old88_odd=round(strength(2 * 60 / 88, .21 + 60 / 88) / s132, 3))
print('strength-weighted (low band):', st); out['strength_low_band'] = st; json.dump(out, open('beatgrid.json', 'w'), indent=1)
Pp = P0 / 2
def prof(t0, t1, n=4):
    acc = np.zeros(n); c = np.zeros(n); w = int(.02 * fr)
    for k in range(int(np.ceil((t0 - O0) / Pp)), int((t1 - O0) / Pp)):
        i = int(round((O0 + k * Pp) * fr)); acc[k % n] += e[max(0, i - w):i + w + 1].max(); c[k % n] += 1
    v = acc / c; return np.round(v / v.max(), 2).tolist()
for a, b in [(0, 23), (23, 38.5), (38.5, 59), (59, 73), (73, 95.4), (95.4, 109.4), (109.4, 123.5), (123.5, 140.5), (140.5, 156.6)]:
    print(f'{a:6.1f}-{b:6.1f}  pulse profile [beat, &, beat, &] (132 grid)', prof(a, b))
