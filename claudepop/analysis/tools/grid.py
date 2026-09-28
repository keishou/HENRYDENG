"""Beat grid, bar phase, drum hits, per-beat energy for "I'm Upping My P(doom)".

Inputs (analysis copies under claudepop/out/, never the song itself):
  out/audio/pdoom_44k.wav                         ffmpeg decode of assets/pdoom.mp3 (honours the Xing/LAME gapless
                                                  header, so t=0 is the first sample of the original programme)
  out/audio/stems/htdemucs/pdoom_44k/*.wav        Demucs v4 htdemucs stems (drums, bass, other, vocals)
  out/work/analysis/beat_this.json                beat_this (CPJKU, ISMIR 2024) beats + downbeats, final0 checkpoint
Output: out/work/analysis/grid.json

Method
  * Kick / snare-clap / hat onsets are picked on the Demucs drum stem, with zero-phase band filters so no filter delay
    shifts the times. Each onset gets two time stamps: attack start (envelope crosses 15 % of its rise) and max slope.
  * Tempo: free least-squares fit of on-beat kicks against beat index (checks the song is machine-quantised).
  * Phase t0: circular mean of on-beat kick max-slope times on a fixed 132 BPM grid, compared with the attack starts,
    the full-mix spectral-flux comb, and beat_this.
  * Bar phase: four independent votes per beat-in-bar position (clap backbeat, harmonic change on bass+other stems,
    bass-note onsets, crash cymbals) plus beat_this downbeats.

usage: python3 grid.py <claudepop_dir>
"""
import sys, json, os
import numpy as np
import soundfile as sf
import scipy.signal as ss
import librosa

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..")
A = f"{ROOT}/out/audio"
ST = f"{A}/stems/htdemucs/pdoom_44k"
W = f"{ROOT}/out/work/analysis"

mix, sr = sf.read(f"{A}/pdoom_44k.wav")
stems = {k: sf.read(f"{ST}/{k}.wav")[0] for k in ("drums", "bass", "other", "vocals")}
N = len(mix)
DUR = N / sr
mixm = mix.mean(1)
drm = stems["drums"].mean(1)
bassm = stems["bass"].mean(1)
othm = stems["other"].mean(1)

BPM = 132.0
T = 60.0 / BPM

# ------------------------------------------------------------------ helpers
ENV_HOP = 44  # ~1 ms envelope resolution
ENV_FPS = sr / ENV_HOP


def band(x, lo, hi, order=4):
    if lo is None:
        sos = ss.butter(order, hi, "lowpass", fs=sr, output="sos")
    elif hi is None:
        sos = ss.butter(order, lo, "highpass", fs=sr, output="sos")
    else:
        sos = ss.butter(order, [lo, hi], "bandpass", fs=sr, output="sos")
    return ss.sosfiltfilt(sos, x)  # zero phase: no group delay


def envelope(x, win_ms=4.0):
    e = np.abs(ss.hilbert(x)) if len(x) < 2 ** 23 else np.abs(x)
    w = max(1, int(sr * win_ms / 1000))
    e = np.convolve(e, np.ones(w) / w, mode="same")
    return e[::ENV_HOP]


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-7))


def pick_onsets(env, min_gap_s, rise_db_min, look_s=0.03):
    """onsets on a ~1 ms envelope: peaks of the positive log-derivative, kept if the level rises >= rise_db_min dB
    within look_s. returns list of (t_maxslope, t_attack15, t_peak, rise_db, peak_db)."""
    L = db(env)
    Ls = np.convolve(L, np.ones(5) / 5, mode="same")
    d = np.diff(Ls, prepend=Ls[0])
    k = int(look_s * ENV_FPS)
    pk, _ = ss.find_peaks(d, height=0.15, distance=int(min_gap_s * ENV_FPS))
    out = []
    for p in pk:
        a = max(0, p - k)
        b = min(len(L), p + k)
        lo = L[a:p + 1].min()
        ip = p + int(np.argmax(L[p:b]))
        hi = L[ip]
        rise = hi - lo
        if rise < rise_db_min:
            continue
        # attack start: first sample (going back from the max-slope point) where the linear envelope is below
        # floor + 15 % of the rise
        ea, eh = 10 ** (lo / 20), 10 ** (hi / 20)
        thr = ea + 0.15 * (eh - ea)
        j = p
        while j > a and env[j] > thr:
            j -= 1
        out.append((p / ENV_FPS, j / ENV_FPS, ip / ENV_FPS, rise, hi))
    return out


def circ_phase(ts, period):
    ang = 2 * np.pi * (np.asarray(ts) % period) / period
    c = np.mean(np.exp(1j * ang))
    ph = (np.angle(c) % (2 * np.pi)) / (2 * np.pi) * period
    return ph, abs(c)


# ------------------------------------------------------------------ drum onsets on the drum stem
kick_env = envelope(band(drm, 30, 120))
clap_env = envelope(band(drm, 1500, 7000))
hat_env = envelope(band(drm, 8000, 16000), 2.0)
crash_env = envelope(band(drm, 5000, 16000), 10.0)
kicks = pick_onsets(kick_env, 0.1, 9.0)
claps = pick_onsets(clap_env, 0.1, 8.0)
hats = pick_onsets(hat_env, 0.06, 6.0, 0.02)
kick_ms = np.array([k[0] for k in kicks])
kick_at = np.array([k[1] for k in kicks])
kick_pk = np.array([k[2] for k in kicks])

# ------------------------------------------------------------------ tempo and phase from kicks
ph0, R0 = circ_phase(kick_ms, T)
t_first = ph0
idx = np.round((kick_ms - t_first) / T)
res = kick_ms - (t_first + idx * T)
on = np.abs(res) < 0.035
fit = np.polyfit(idx[on], kick_ms[on], 1)
free_bpm = 60 / fit[0]
free_res = kick_ms[on] - np.polyval(fit, idx[on])
# drift check: phase in thirds of the song
drift = []
for a, b in [(0, 52), (52, 104), (104, DUR)]:
    m = on & (kick_ms >= a) & (kick_ms < b)
    drift.append({"from": a, "to": round(b, 1), "n": int(m.sum()), "phase_maxslope": round(float(circ_phase(kick_ms[m], T)[0]), 4),
                  "phase_attack": round(float(circ_phase(kick_at[m], T)[0]), 4)})
ph_ms, R_ms = circ_phase(kick_ms[on], T)
ph_at, R_at = circ_phase(kick_at[on], T)
ph_pk, _ = circ_phase(kick_pk[on], T)

# full-mix spectral flux comb (librosa onset strength, hop 1.45 ms)
HOPF = 64
oenv = librosa.onset.onset_strength(y=mixm, sr=sr, hop_length=HOPF, n_fft=2048, center=True)
tf = librosa.frames_to_time(np.arange(len(oenv)), sr=sr, hop_length=HOPF)
phases = np.arange(0, T, 0.001)
comb = [np.interp(np.arange(p, DUR, T), tf, oenv).mean() for p in phases]
ph_flux = float(phases[int(np.argmax(comb))])

bt = json.load(open(f"{W}/beat_this.json"))
bt_b = np.array(bt["beats"])
bt_d = np.array(bt["downbeats"])
ph_bt, _ = circ_phase(bt_b, T)

# chosen t0: kick max-slope phase. Rationale in REPORT.md.
T0 = float(round(ph_ms, 4))
nb = int(np.floor((DUR - T0) / T)) + 1
beats = T0 + np.arange(nb) * T

# ------------------------------------------------------------------ bar phase votes (beat index mod 4)
def nearest_beat(t):
    return int(np.round((t - T0) / T))


clap_ms = np.array([c[0] for c in claps])
clap_rise = np.array([c[3] for c in claps])
vote_clap = np.zeros(4)
for t, r in zip(clap_ms, clap_rise):
    i = nearest_beat(t)
    if abs(t - beats[min(max(i, 0), nb - 1)]) < 0.04:
        vote_clap[i % 4] += 1

# harmonic change per beat: chroma of bass+other, beat-synchronous
harm = bassm + othm
HOPC = 512
C = librosa.feature.chroma_cqt(y=harm, sr=sr, hop_length=HOPC, bins_per_octave=36)
tc = librosa.frames_to_time(np.arange(C.shape[1]), sr=sr, hop_length=HOPC)
cb = np.zeros((12, nb))
for i in range(nb):
    m = (tc >= beats[i]) & (tc < beats[i] + T)
    if m.any():
        cb[:, i] = C[:, m].mean(1)
cbn = cb / (np.linalg.norm(cb, axis=0, keepdims=True) + 1e-9)
hchange = np.zeros(nb)
hchange[1:] = 1 - (cbn[:, 1:] * cbn[:, :-1]).sum(0)
vote_harm = np.array([hchange[k::4].mean() for k in range(4)])

# bass note onsets (bass stem, 40-300 Hz)
bass_env = envelope(band(bassm, 35, 300), 6.0)
bass_on = pick_onsets(bass_env, 0.12, 8.0, 0.05)
vote_bass = np.zeros(4)
for o in bass_on:
    i = nearest_beat(o[0])
    if 0 <= i < nb and abs(o[0] - beats[i]) < 0.05:
        vote_bass[i % 4] += o[3]

# crash cymbals: high-band onsets with long decay (level still within 10 dB of peak 400 ms later)
crashes = []
for c in pick_onsets(crash_env, 0.25, 10.0, 0.04):
    p = int(c[2] * ENV_FPS)
    q = min(len(crash_env) - 1, p + int(0.4 * ENV_FPS))
    decay = db(crash_env[p]) - db(crash_env[q])
    if decay < 10 and c[3] > 12:
        crashes.append({"t": round(c[0], 3), "rise_db": round(c[3], 1), "decay400_db": round(float(decay), 1)})
vote_crash = np.zeros(4)
for c in crashes:
    i = nearest_beat(c["t"])
    if 0 <= i < nb:
        vote_crash[i % 4] += 1

vote_bt = np.zeros(4)
for d in bt_d:
    vote_bt[nearest_beat(d) % 4] += 1

# ------------------------------------------------------------------ drum hits list with grid position
def grid_pos(t):
    q = (t - T0) / (T / 4)
    qi = int(np.round(q))
    return {"bar": qi // 16 + 1, "beat": (qi // 4) % 4 + 1, "six": qi % 4 + 1, "off_ms": round((q - qi) * T / 4 * 1000, 1)}


def hitlist(name, lst):
    if not lst:
        return []
    ref = np.percentile([h[3] for h in lst], 90)
    return [{"t": round(h[0], 3), "t_attack": round(h[1], 3), "type": name, "rise_db": round(h[3], 1),
             "s": round(min(1.0, h[3] / ref), 2), **grid_pos(h[0])} for h in lst]


hits = hitlist("kick", kicks) + hitlist("snare", claps) + hitlist("hat", hats)
hits.sort(key=lambda h: (h["t"], h["type"]))

# ------------------------------------------------------------------ per-beat energy
def rms_db(x, a, b):
    seg = x[int(a * sr):int(min(b, DUR) * sr)]
    return float(10 * np.log10(np.mean(seg ** 2) + 1e-12)) if len(seg) else -120.0


vocm = stems["vocals"].mean(1)
per_beat = []
edges = np.append(beats, DUR)
if T0 > 0:
    pass
for i in range(nb):
    a, b = beats[i], min(beats[i] + T, DUR)
    row = {"i": i, "t": round(float(beats[i]), 4), "bar": i // 4 + 1, "beat": i % 4 + 1,
           "mix_db": round(rms_db(mixm, a, b), 1), "drums_db": round(rms_db(drm, a, b), 1),
           "bass_db": round(rms_db(bassm, a, b), 1), "other_db": round(rms_db(othm, a, b), 1),
           "vocal_db": round(rms_db(vocm, a, b), 1)}
    for name, arr in (("kick", kick_ms), ("snare", clap_ms)):
        row[name] = int(np.sum((arr >= a - 0.03) & (arr < b - 0.03)))
    per_beat.append(row)
# normalised 0..1 energy (mix RMS dB mapped from -40..max)
mdb = np.array([r["mix_db"] for r in per_beat])
top = np.percentile(mdb, 99)
for r, v in zip(per_beat, mdb):
    r["energy"] = round(float(np.clip((v - (top - 24)) / 24, 0, 1)), 3)

out = {
    "source": "assets/pdoom.mp3 decoded by ffmpeg 7.0.2 (gapless header honoured: 1105 priming samples skipped), t=0 = first output sample",
    "duration": round(DUR, 4),
    "bpm": BPM,
    "beat_period": T,
    "t0": T0,
    "phase_estimates": {
        "kick_maxslope": round(float(ph_ms), 4), "kick_maxslope_R": round(float(R_ms), 3),
        "kick_attack15": round(float(ph_at), 4), "kick_env_peak": round(float(ph_pk), 4),
        "mix_flux_comb": round(ph_flux, 4), "beat_this": round(float(ph_bt), 4),
    },
    "tempo_check": {"free_fit_bpm": round(float(free_bpm), 4), "free_fit_t0": round(float(fit[1]), 4),
                    "resid_ms_std": round(float(free_res.std() * 1000), 2),
                    "resid_ms_p95": round(float(np.percentile(np.abs(free_res), 95) * 1000), 2),
                    "n_onbeat_kicks": int(on.sum()), "n_kicks": len(kicks), "drift_by_third": drift},
    "bar_phase_votes": {"clap": vote_clap.tolist(), "harmonic_change": np.round(vote_harm, 4).tolist(),
                        "bass_onsets": np.round(vote_bass, 1).tolist(), "crash": vote_crash.tolist(),
                        "beat_this_downbeats": vote_bt.tolist()},
    "beat_this": {"n_beats": len(bt_b), "n_downbeats": len(bt_d),
                  "beat_dev_ms_median": round(float(np.median(np.abs(bt_b - (T0 + np.round((bt_b - T0) / T) * T))) * 1000), 1)},
    "beats": [round(float(b), 4) for b in beats],
    "crashes": crashes,
    "hits": hits,
    "per_beat": per_beat,
    "harmonic_change": np.round(hchange, 4).tolist(),
}
json.dump(out, open(f"{W}/grid.json", "w"))
print(json.dumps({k: out[k] for k in ("duration", "t0", "phase_estimates", "tempo_check", "bar_phase_votes", "beat_this")}, indent=1))
print("hits", {n: sum(h["type"] == n for h in hits) for n in ("kick", "snare", "hat")}, "crashes", len(crashes))
