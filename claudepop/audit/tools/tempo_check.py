import librosa, numpy as np
y, sr = librosa.load('/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3', sr=22050, mono=True)
hop = 256
env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop, aggregate=np.median)
fr = sr / hop; t = np.arange(len(env)) / fr
def comb(bpm, phases=64):
    P = 60 / bpm; best = (0, 0)
    for ph in np.linspace(0, P, phases, endpoint=False):
        g = np.arange(ph, t[-1], P); idx = np.round(g * fr).astype(int); idx = idx[idx < len(env)]
        # max within +-20 ms window
        s = np.mean([env[max(0, i - 5):i + 6].max() for i in idx])
        if s > best[0]: best = (s, ph)
    return best
base = env.mean()
for bpm in [66, 88, 99, 110, 120, 129.2, 132, 176, 264]:
    s, ph = comb(bpm); print(f'{bpm:6.1f} BPM  score {s/base:5.2f}x mean   best phase {ph:.3f}s')
# old grid score explicitly
P = 60/88; g = np.arange(0.21, t[-1], P); idx = np.round(g*fr).astype(int); idx = idx[idx < len(env)]
print('old grid (88, 0.21) score', np.mean([env[max(0,i-5):i+6].max() for i in idx]) / base)
P = 60/132; g = np.arange(0.271, t[-1], P); idx = np.round(g*fr).astype(int); idx = idx[idx < len(env)]
print('fitted grid (132, 0.271) score', np.mean([env[max(0,i-5):i+6].max() for i in idx]) / base)
# which of the 88-grid beats coincide with 132-grid beats (every 2nd 88 beat = every 3rd 132 beat)
