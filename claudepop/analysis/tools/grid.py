"""Beat grid, bar phase, drum hits, crashes and per-beat energy for "I'm Upping My P(doom)".

Inputs (analysis copies under claudepop/out/, never the song itself):
  out/audio/pdoom_44k.wav                         ffmpeg decode of assets/pdoom.mp3 (honours the Xing/LAME gapless
                                                  header, so t=0 is the first sample of the original programme)
  out/audio/stems/htdemucs/pdoom_44k/*.wav        Demucs v4 htdemucs stems (drums, bass, other, vocals)
  out/work/analysis/beat_this.json                beat_this (CPJKU, ISMIR 2024) beats + downbeats, final0 checkpoint
Output: out/work/analysis/grid.json

Method
  * Drum onsets are picked on the Demucs drum stem in three bands (kick < 120 Hz, snare/clap 1.5-7 kHz, hats > 8 kHz)
    with CAUSAL band filters whose group delay at the band centre is subtracted. (A zero-phase filtfilt low-pass rings
    symmetrically and moves low-frequency attacks ~70 ms early; that was the bug in the first draft of this script.)
    Candidates are peaks of a 6 ms log-level rise on a 1 ms envelope; each must reach within 30 dB of the band's loud
    hits. Every onset carries its attack start (envelope crosses 10 % of its rise) and its max-slope time.
  * Kick vs snare body: a kick candidate must have more 35-110 Hz than 150-400 Hz energy in the 40 ms after the attack.
  * Tempo: free least-squares fit of on-beat kick attacks against beat index (checks the song is machine-quantised).
  * Phase t0: circular mean of on-beat kick attack starts on a fixed 132 BPM grid, compared with max-slope times,
    the full-mix spectral-flux comb, and beat_this.
  * Bar phase: votes per beat-in-bar position (snare backbeat, harmonic change on bass+other stems, crash cymbals,
    beat_this downbeats).

usage: python3 grid.py <claudepop_dir>
"""
import sys, json, os
import numpy as np
import soundfile as sf
import scipy.signal as ss
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import librosa

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..")
A = f"{ROOT}/out/audio"
ST = f"{A}/stems/htdemucs/pdoom_44k"
W = f"{ROOT}/out/work/analysis"

mix, sr = sf.read(f"{A}/pdoom_44k.wav")
stems = {k: sf.read(f"{ST}/{k}.wav")[0].mean(1) for k in ("drums", "bass", "other", "vocals")}
N = len(mix)
DUR = N / sr
mixm = mix.mean(1)
drm, bassm, othm, vocm = stems["drums"], stems["bass"], stems["other"], stems["vocals"]

BPM = 132.0
T = 60.0 / BPM
ENV_HOP = 44  # ~1 ms
ENV_FPS = sr / ENV_HOP


# ------------------------------------------------------------------ helpers
def causal(x, kind, f, order):
    sos = ss.butter(order, f, kind, fs=sr, output="sos")
    b, a = ss.sos2tf(sos)
    fc = f if np.isscalar(f) else float(np.sqrt(f[0] * f[1]))
    fc = min(fc, 60.0) if kind == "lowpass" else fc  # kick energy sits around 50-70 Hz
    _, gd = ss.group_delay((b, a), w=[fc], fs=sr)
    return ss.sosfilt(sos, x), float(gd[0]) / sr


def env1ms(y):
    e = maximum_filter1d(np.abs(y), int(0.001 * sr))
    return e[::ENV_HOP]


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-7))


def pick(e, gd, min_gap, rise_min, span_db, look_pre=0.06, look_post=0.05):
    """onsets on a 1 ms envelope. returns dicts with attack (10 %), max-slope, peak time, rise and peak level."""
    L = db(e)
    k = 6
    rise6 = np.zeros_like(L)
    rise6[k:] = L[k:] - L[:-k]
    ref = np.percentile(L, 99.5)
    cand, _ = ss.find_peaks(rise6, height=4.0, distance=int(min_gap * ENV_FPS))
    out = []
    for c in cand:
        a = max(0, c - int(look_pre * ENV_FPS))
        b = min(len(L) - 1, c + int(look_post * ENV_FPS))
        p = c + int(np.argmax(e[c:b + 1]))
        pk = e[p]
        if db(pk) < ref - span_db:
            continue
        fl = np.percentile(e[a:max(a + 1, c - 8)], 30)
        rise = db(pk) - db(fl)
        if rise < rise_min:
            continue
        thr = fl + 0.1 * (pk - fl)
        j = p
        while j > a and e[j] > thr:
            j -= 1
        Ls = uniform_filter1d(L, 3)
        seg = np.diff(Ls[j:p + 1])
        ms = j + (int(np.argmax(seg)) if len(seg) else 0)
        out.append({"t_attack": j / ENV_FPS - gd, "t_ms": ms / ENV_FPS - gd, "t_peak": p / ENV_FPS - gd,
                    "rise_db": float(rise), "peak_db": float(db(pk) - ref)})
    # merge duplicates (two candidates resolving to the same attack)
    out.sort(key=lambda o: o["t_attack"])
    merged = []
    for o in out:
        if merged and o["t_attack"] - merged[-1]["t_attack"] < min_gap * 0.8:
            if o["rise_db"] > merged[-1]["rise_db"]:
                merged[-1] = o
            continue
        merged.append(o)
    return merged


def band_energy_db(x, t, a_ms, b_ms):
    seg = x[int((t + a_ms / 1000) * sr):int((t + b_ms / 1000) * sr)]
    return 10 * np.log10(np.mean(seg ** 2) + 1e-14)


def circ_phase(ts, period):
    ang = 2 * np.pi * (np.asarray(ts) % period) / period
    c = np.mean(np.exp(1j * ang))
    return (np.angle(c) % (2 * np.pi)) / (2 * np.pi) * period, abs(c)


# ------------------------------------------------------------------ drum onsets
y_kick, gd_kick = causal(drm, "lowpass", 120, 4)
y_snare, gd_snare = causal(drm, "bandpass", [1500, 7000], 2)
y_hat, gd_hat = causal(drm, "highpass", 8000, 4)
y_crash, gd_crash = causal(drm, "highpass", 5000, 2)
# zero-phase bands are used only for energies in windows AFTER an attack (their pre-ringing cannot move a time stamp)
lo_band = ss.sosfiltfilt(ss.butter(4, [35, 110], "bandpass", fs=sr, output="sos"), drm)
hi_band = ss.sosfiltfilt(ss.butter(4, [1500, 7000], "bandpass", fs=sr, output="sos"), drm)
clap_band = ss.sosfiltfilt(ss.butter(4, [1500, 4000], "bandpass", fs=sr, output="sos"), drm)
air_band = ss.sosfiltfilt(ss.butter(4, [8000, 16000], "bandpass", fs=sr, output="sos"), drm)
e_broad = env1ms(drm)


def refine_broadband(t_band, back=0.03):
    """attack start on the unfiltered drum stem: last 1 ms frame before the band peak where the broadband envelope is
    below 10 % of its rise. No filter is involved, so no delay to compensate."""
    c = int(t_band * ENV_FPS)
    a = max(0, c - int(back * ENV_FPS))
    b = min(len(e_broad) - 1, c + int(0.02 * ENV_FPS))
    p = a + int(np.argmax(e_broad[a:b + 1]))
    fl = np.percentile(e_broad[max(0, a - int(0.04 * ENV_FPS)):a + 1], 30)
    thr = fl + 0.1 * (e_broad[p] - fl)
    j = p
    while j > a and e_broad[j] > thr:
        j -= 1
    return j / ENV_FPS


kc = pick(env1ms(y_kick), gd_kick, 0.09, 6.0, 40.0)
for k in kc:
    k["lo_rise"] = band_energy_db(lo_band, k["t_attack"], 0, 50) - band_energy_db(lo_band, k["t_attack"], -50, -5)
    k["lo_abs"] = band_energy_db(lo_band, k["t_attack"], 0, 50)
ref_lo = np.percentile([k["lo_abs"] for k in kc], 99)
kicks = [k for k in kc if k["lo_rise"] >= 15 and k["lo_abs"] >= ref_lo - 24]
for k in kicks:
    k["t_band"] = k["t_attack"]
    k["t_attack"] = refine_broadband(k["t_band"])
    k["rise_db"], k["peak_db"] = k["lo_rise"], k["lo_abs"] - ref_lo

sc = pick(env1ms(y_snare), gd_snare, 0.07, 6.0, 40.0)
for s_ in sc:
    s_["sus"] = band_energy_db(hi_band, s_["t_attack"], 8, 60)
    # pre-window ends 25 ms early: claps here are flammed, with 1-2 pre-bursts 10-20 ms before the main hit
    s_["sus_rise"] = s_["sus"] - band_energy_db(hi_band, s_["t_attack"], -80, -25)
    # claps/snares are darker than open hats: 1.5-4 kHz vs 8-16 kHz energy after the attack
    s_["dark"] = band_energy_db(clap_band, s_["t_attack"], 8, 60) - band_energy_db(air_band, s_["t_attack"], 8, 60)
ref_hi = np.percentile([s_["sus"] for s_ in sc], 99)
snares = [s_ for s_ in sc if s_["sus"] >= ref_hi - 12 and s_["sus_rise"] >= 3 and s_["dark"] >= -2]
for s_ in snares:
    s_["t_band"] = s_["t_attack"]
    s_["t_attack"] = refine_broadband(s_["t_band"], 0.02)
    s_["rise_db"], s_["peak_db"] = s_["sus_rise"], s_["sus"] - ref_hi

hats = pick(env1ms(y_hat), gd_hat, 0.05, 6.0, 30.0, look_pre=0.04, look_post=0.03)
sn_t = np.array([s_["t_band"] for s_ in snares])
hats = [h for h in hats if not len(sn_t) or np.min(np.abs(sn_t - h["t_attack"])) > 0.02]

# ------------------------------------------------------------------ tempo and phase from kicks
# claps on beats 2 and 4 start ~15-20 ms before the kick (a flam layer), so beats with a clap are left out of the phase
sn_att = np.array([s_["t_attack"] for s_ in snares])
clean = [k for k in kicks if not len(sn_att) or np.min(np.abs(sn_att - k["t_band"])) > 0.04]
k_at = np.array([k["t_attack"] for k in clean])
k_ms = np.array([k["t_ms"] for k in clean])
ph_first, _ = circ_phase(k_at, T)
idx = np.round((k_at - ph_first) / T)
res = k_at - (ph_first + idx * T)
on = np.abs(res) < 0.025
fit = np.polyfit(idx[on], k_at[on], 1)
free_bpm = 60 / fit[0]
free_res = k_at[on] - np.polyval(fit, idx[on])
ph_at, R_at = circ_phase(k_at[on], T)
ph_ms, R_ms = circ_phase(k_ms[on], T)
drift = []
for a, b in [(0, 52), (52, 104), (104, DUR)]:
    m = on & (k_at >= a) & (k_at < b)
    drift.append({"from": a, "to": round(b, 1), "n": int(m.sum()),
                  "phase_attack": round(float(circ_phase(k_at[m], T)[0]), 4)})

# full-mix spectral-flux comb (librosa onset strength, hop 1.45 ms)
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

T0 = float(round(ph_at, 4))  # kick attack start; rationale in REPORT.md
nb = int(np.floor((DUR - T0) / T)) + 1
beats = T0 + np.arange(nb) * T


def nearest_beat(t):
    return int(np.round((t - T0) / T))


def offs_ms(ts):
    ts = np.asarray(ts)
    o = ts - (T0 + np.round((ts - T0) / T) * T)
    o = o[np.abs(o) < 0.04] * 1000
    return {"n": int(len(o)), "median": round(float(np.median(o)), 1), "p10": round(float(np.percentile(o, 10)), 1),
            "p90": round(float(np.percentile(o, 90)), 1)} if len(o) else {}


onset_offsets = {"kick_clap_free_attack": offs_ms(k_at), "kick_all_attack": offs_ms([k["t_attack"] for k in kicks]),
                 "kick_maxslope": offs_ms(k_ms), "snare_clap_attack": offs_ms(sn_att)}


# ------------------------------------------------------------------ bar phase votes (beat index mod 4)
vote_snare = np.zeros(4)
for s in snares:
    i = nearest_beat(s["t_attack"])
    if 0 <= i < nb and abs(s["t_attack"] - beats[i]) < 0.03 and s["peak_db"] > -12:
        vote_snare[i % 4] += 1

HOPC = 512
C = librosa.feature.chroma_cqt(y=bassm + othm, sr=sr, hop_length=HOPC, bins_per_octave=36)
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

# crash cymbals: high-band onsets whose level is still within 12 dB of the peak 400 ms later
e_cr = env1ms(y_crash)
crashes = []
for c in pick(e_cr, gd_crash, 0.25, 10.0, 18.0, look_post=0.04):
    p = int((c["t_peak"] + gd_crash) * ENV_FPS)
    q = min(len(e_cr) - 1, p + int(0.4 * ENV_FPS))
    lvl = db(uniform_filter1d(e_cr, 30))
    decay = lvl[p] - lvl[q]
    if decay < 12:
        crashes.append({"t": round(c["t_attack"], 3), "rise_db": round(c["rise_db"], 1), "decay400_db": round(float(decay), 1)})
vote_crash = np.zeros(4)
for c in crashes:
    i = nearest_beat(c["t"])
    if 0 <= i < nb:
        vote_crash[i % 4] += 1

vote_bt = np.zeros(4)
for d in bt_d:
    vote_bt[nearest_beat(d) % 4] += 1


# ------------------------------------------------------------------ hit list with grid positions
def grid_pos(t):
    q = (t - T0) / (T / 4)
    qi = int(np.round(q))
    return {"bar": qi // 16 + 1, "beat": (qi // 4) % 4 + 1, "six": qi % 4 + 1, "off_ms": round((q - qi) * T / 4 * 1000, 1)}


def hitlist(name, lst):
    if not lst:
        return []
    ref = np.percentile([h["rise_db"] + h["peak_db"] for h in lst], 90)
    lo = np.percentile([h["rise_db"] + h["peak_db"] for h in lst], 5)
    out = []
    for h in lst:
        v = h["rise_db"] + h["peak_db"]
        out.append({"t": round(h["t_attack"], 3), "t_ms": round(h["t_ms"], 3), "type": name,
                    "rise_db": round(h["rise_db"], 1), "peak_db": round(h["peak_db"], 1),
                    "s": round(float(np.clip((v - lo) / max(1e-6, ref - lo), 0.05, 1.0)), 2), **grid_pos(h["t_attack"])})
    return out


hits = hitlist("kick", kicks) + hitlist("snare", snares) + hitlist("hat", hats)
hits.sort(key=lambda h: (h["t"], h["type"]))


# ------------------------------------------------------------------ per-beat energy
def rms_db(x, a, b):
    seg = x[int(max(0, a) * sr):int(min(b, DUR) * sr)]
    return float(10 * np.log10(np.mean(seg ** 2) + 1e-12)) if len(seg) else -120.0


per_beat = []
for i in range(nb):
    a, b = beats[i], min(beats[i] + T, DUR)
    row = {"i": i, "t": round(float(beats[i]), 4), "bar": i // 4 + 1, "beat": i % 4 + 1,
           "mix_db": round(rms_db(mixm, a, b), 1), "drums_db": round(rms_db(drm, a, b), 1),
           "bass_db": round(rms_db(bassm, a, b), 1), "other_db": round(rms_db(othm, a, b), 1),
           "vocal_db": round(rms_db(vocm, a, b), 1)}
    for name in ("kick", "snare", "hat"):
        row[name] = int(sum(1 for h in hits if h["type"] == name and a - 0.03 <= h["t"] < b - 0.03))
    per_beat.append(row)
mdb = np.array([r["mix_db"] for r in per_beat])
top = np.percentile(mdb, 99)
for r, v in zip(per_beat, mdb):
    r["energy"] = round(float(np.clip((v - (top - 24)) / 24, 0, 1)), 3)

# pre-roll before beat 0 (intro pickup) as its own row
pre = {"t": 0.0, "t_end": round(T0, 4), "mix_db": round(rms_db(mixm, 0, T0), 1)}

out = {
    "source": "assets/pdoom.mp3 decoded by ffmpeg 7.0.2 with the LAME gapless header honoured; t=0 = first output sample",
    "duration": round(DUR, 4),
    "bpm": BPM,
    "beat_period": T,
    "t0": T0,
    "filter_group_delay_ms": {"kick": round(gd_kick * 1000, 2), "snare": round(gd_snare * 1000, 3), "hat": round(gd_hat * 1000, 3)},
    "phase_estimates": {
        "kick_attack10": round(float(ph_at), 4), "kick_attack10_R": round(float(R_at), 4),
        "kick_maxslope": round(float(ph_ms), 4), "kick_maxslope_R": round(float(R_ms), 4),
        "mix_flux_comb": round(ph_flux, 4), "beat_this": round(float(ph_bt), 4),
    },
    "tempo_check": {"free_fit_bpm": round(float(free_bpm), 4), "free_fit_t0": round(float(fit[1]), 4),
                    "resid_ms_std": round(float(free_res.std() * 1000), 2),
                    "resid_ms_p95": round(float(np.percentile(np.abs(free_res), 95) * 1000), 2),
                    "n_onbeat_kicks": int(on.sum()), "n_kicks": len(kicks), "n_clap_free_kicks": len(clean),
                    "drift_by_third": drift},
    "onset_offsets_ms_from_grid": onset_offsets,
    "bar_phase_votes": {"snare_backbeat": vote_snare.tolist(), "harmonic_change": np.round(vote_harm, 4).tolist(),
                        "crash": vote_crash.tolist(), "beat_this_downbeats": vote_bt.tolist()},
    "beat_this": {"n_beats": len(bt_b), "n_downbeats": len(bt_d),
                  "beat_dev_ms_median": round(float(np.median(bt_b - (T0 + np.round((bt_b - T0) / T) * T)) * 1000), 1),
                  "beat_dev_ms_mad": round(float(np.median(np.abs(bt_b - (T0 + np.round((bt_b - T0) / T) * T))) * 1000), 1)},
    "beats": [round(float(b), 4) for b in beats],
    "pre_roll": pre,
    "crashes": crashes,
    "hits": hits,
    "per_beat": per_beat,
    "harmonic_change": np.round(hchange, 4).tolist(),
}
json.dump(out, open(f"{W}/grid.json", "w"))
print(json.dumps({k: out[k] for k in ("duration", "t0", "filter_group_delay_ms", "phase_estimates", "tempo_check", "onset_offsets_ms_from_grid",
                                      "bar_phase_votes", "beat_this")}, indent=1))
print("hits", {n: sum(h["type"] == n for h in hits) for n in ("kick", "snare", "hat")}, "crashes", len(crashes))
