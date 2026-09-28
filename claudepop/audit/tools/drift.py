# Local tempo/phase tracking in 8 s windows: best period near 132 BPM and best phase, plus where the old 88 grid falls.
import librosa, numpy as np, json
y, sr = librosa.load('/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3', sr=22050, mono=True)
hop = 128; fr = sr / hop
env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
yp = librosa.effects.percussive(y, margin=2.0)
S = np.abs(librosa.stft(yp, n_fft=2048, hop_length=hop)); f = librosa.fft_frequencies(sr=sr, n_fft=2048)
b = S[(f >= 30) & (f < 150)].sum(0); ek = np.maximum(0, np.diff(np.log1p(b * 10), prepend=0))
def score(e, P, O, a, b_):
    g = np.arange(O + np.ceil((a - O) / P) * P, b_, P); idx = np.round(g * fr).astype(int); w = 2
    return np.mean([e[max(0, i - w):i + w + 1].max() for i in idx if i < len(e)])
rows = []
for a in np.arange(0, 150, 6.0):
    b_ = a + 8
    best = max(((score(env, P, O, a, b_) + score(ek, P, O, a, b_) * env.mean() / ek.mean(), P, O) for P in np.linspace(.448, .461, 27) for O in np.linspace(0, .4545, 60, endpoint=False)))
    _, P, O = best
    # phase of this local grid, expressed relative to global grid (0.2186 + k*0.45453)
    k = np.round((a + 4 - O) / P); tb = O + k * P  # a beat near window centre
    dphase = ((tb - 0.2186) / 0.45453) % 1
    rows.append((round(a, 1), round(60 / P, 2), round(float(dphase), 2)))
for r in rows: print(r)
json.dump(rows, open('local_tempo.json', 'w'))
