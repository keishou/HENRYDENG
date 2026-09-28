# Beat/tempo audit of the song vs. the previous video's hard-coded grid (BPM 88, OFF 0.21 s).
import librosa, numpy as np, json
y, sr = librosa.load('/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3', sr=22050, mono=True)
dur = len(y) / sr
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time', tightness=100)
tempo = float(np.atleast_1d(tempo)[0])
onset_env = librosa.onset.onset_strength(y=y, sr=sr)
# fit a straight line to the tracked beats (global grid)
n = np.arange(len(beats)); A = np.vstack([n, np.ones_like(n)]).T
period, off = np.linalg.lstsq(A, beats, rcond=None)[0]
res = beats - (n * period + off)
# compare against the old grid
BEAT = 60 / 88; OFF = 0.21
old = (beats - OFF) / BEAT; old_err = (old - np.round(old)) * BEAT
# RMS energy per 2-bar window for section map
hop = 512; rms = librosa.feature.rms(y=y, hop_length=hop)[0]; tt = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
bar = 4 * period; sections = []
for k in range(int(dur / (2 * bar)) + 1):
    a, b = k * 2 * bar + off, (k + 1) * 2 * bar + off
    m = (tt >= a) & (tt < b)
    if m.any(): sections.append((round(a, 2), round(float(rms[m].mean()), 4)))
out = dict(duration=round(dur, 3), librosa_tempo=round(tempo, 2), fitted_bpm=round(60 / period, 3), fitted_period=round(period, 4),
           fitted_offset=round(off % period, 3), n_beats=len(beats), fit_resid_ms_p95=round(float(np.percentile(np.abs(res), 95) * 1000), 1),
           old_grid_err_ms_median=round(float(np.median(np.abs(old_err)) * 1000), 1), old_grid_err_ms_p95=round(float(np.percentile(np.abs(old_err), 95) * 1000), 1),
           old_grid_err_first=round(float(np.median(old_err[:40]) * 1000), 1), old_grid_err_last=round(float(np.median(old_err[-40:]) * 1000), 1),
           energy_per_2bars=sections)
print(json.dumps(out, indent=1))
json.dump(out, open('/home/user/HENRYDENG/claudepop/audit/tools/beats.json', 'w'), indent=1)
