# Loudness map (1 s RMS, dBFS) and percussive/harmonic split, to compare section energy with what the old video shows.
import librosa, numpy as np, json
y, sr = librosa.load('/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3', sr=22050, mono=True)
H, P = librosa.effects.hpss(y)
def db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
rows = []
for a in range(0, 157, 2):
    s, e = int(a * sr), int(min(len(y), (a + 2) * sr))
    if e - s < sr // 2: break
    rows.append((a, round(db(y[s:e]), 1), round(db(P[s:e]), 1), round(db(H[s:e]), 1)))
print('t  total  perc  harm'); [print(*r) for r in rows]
json.dump(rows, open('energy_2s.json', 'w'))
