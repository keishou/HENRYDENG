"""ΟΥΤΙΣ — the score. Every sound is synthesized here (numpy/scipy), cued from
film/timeline.json so picture and music share one clock.

Palette (Nolan / Zimmer / Göransson vocabulary, re-voiced for Japan):
  pocket-watch ticks · Shepard tone · pipe organ fused with shō (gagaku mouth organ)
  taiko + low brass hits · spiccato strings · koto (Karplus-Strong) · shakuhachi
  bonshō temple bells (and their reversal) · sea, rain, thunder, smoke
  hard cuts to silence.

usage: python3 score.py ../film/timeline.json out.wav
"""
import json
import sys

import numpy as np
import scipy.signal as sg
import soundfile as sf

SR = 48000
TL = json.load(open(sys.argv[1]))
DUR = TL["duration"]
N = int(DUR * SR)
rng = np.random.default_rng(1212)

# ---------------------------------------------------------------- buses
bus = {k: np.zeros((N, 2), np.float32) for k in ("dry", "room", "hall", "cave")}


def add(sig, t, gain=1.0, pan=0.0, to="hall", dry=0.35):
    """Place a mono/stereo signal at time t (s). pan -1..1. Part goes dry, part to a reverb send."""
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l, sig * r], 1) * np.sqrt(2)
    i0 = int(round(t * SR))
    if i0 >= N:
        return
    j0 = max(0, -i0)
    i0 = max(0, i0)
    n = min(len(sig) - j0, N - i0)
    if n <= 0:
        return
    s = sig[j0:j0 + n] * gain
    bus["dry"][i0:i0 + n] += s * dry
    if to:
        bus[to][i0:i0 + n] += s * (1 - dry)


def tt(d):
    return np.arange(int(d * SR)) / SR


def env_adsr(n, a, d, s, r, sus_len=None):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    sus = n - a - d - r if sus_len is None else int(sus_len * SR)
    sus = max(sus, 0)
    e = np.concatenate([np.linspace(0, 1, max(a, 1)) ** 1.5, np.linspace(1, s, max(d, 1)),
                        np.full(sus, s), np.linspace(s, 0, max(r, 1)) ** 1.3])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def lp(x, fc, order=2):
    return sg.sosfilt(sg.butter(order, min(fc, SR * .45), "low", fs=SR, output="sos"), x, axis=0)


def hp(x, fc, order=2):
    return sg.sosfilt(sg.butter(order, fc, "high", fs=SR, output="sos"), x, axis=0)


def bp(x, f1, f2, order=2):
    return sg.sosfilt(sg.butter(order, [f1, min(f2, SR * .45)], "band", fs=SR, output="sos"), x, axis=0)


def noise(d, color="white"):
    x = rng.standard_normal(int(d * SR)).astype(np.float64)
    if color == "brown":
        x = np.cumsum(x); x = hp(x, 15); x /= np.abs(x).max() + 1e-9
    elif color == "pink":
        b, a = [0.049922, -0.095993, 0.050612, -0.004408], [1, -2.494956, 2.017265, -0.522189]
        x = sg.lfilter(b, a, x); x /= np.abs(x).max() + 1e-9
    return x


NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"])}


def hz(name):
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[n] + 12 * (o + 1) - 69) / 12)


def partials(f, d, amps, detune=0.0, phase=None):
    t = tt(d); x = np.zeros_like(t)
    for k, a in amps:
        fk = f * k * (1 + detune * rng.uniform(-1, 1))
        if fk < SR * .45:
            x += a * np.sin(2 * np.pi * fk * t + (rng.uniform(0, 6.28) if phase is None else phase))
    return x


# ---------------------------------------------------------------- instruments
def tick(kind=0):
    t = tt(.06)
    click = noise(.06) * np.exp(-t * 900)
    ping = np.sin(2 * np.pi * (3300 if kind == 0 else 2650) * t) * np.exp(-t * 160)
    body = np.sin(2 * np.pi * 950 * t) * np.exp(-t * 90) * .4
    return hp(click * .8 + ping * .5 + body, 400)


def organ(notes, d, a=.35, r=2.0, bright=1.0):
    """Flue pipes: 16' 8' 4' 2' + a quiet mixture, with pipe 'chiff'."""
    n = int(d * SR); x = np.zeros(n)
    for nm in notes:
        f = hz(nm) if isinstance(nm, str) else nm
        amps = [(.5, .35 if f < 150 else .15), (1, 1), (2, .55 * bright), (3, .22 * bright), (4, .28 * bright),
                (6, .08 * bright), (8, .06 * bright), (5, .05 * bright)]
        v = partials(f, d, amps, detune=.0007)
        v *= 1 + .004 * np.sin(2 * np.pi * 5.1 * tt(d) + rng.uniform(0, 6))
        chiff = bp(noise(.12), f * 1.5, f * 6) * np.exp(-tt(.12) * 30) * .25
        v[:len(chiff)] += chiff[:n]
        x += v / (1 + .15 * len(notes))
    return x * env_adsr(n, a, .5, .85, r)


def sho(notes, d, swell=True):
    """Free-reed cluster: bright, beating, breathed (it swells like an inhale)."""
    n = int(d * SR); x = np.zeros(n)
    for nm in notes:
        f = hz(nm)
        amps = [(k, 1 / k ** .75) for k in range(1, 12)]
        v = partials(f, d, amps, detune=.0012) + partials(f * 1.0015, d, amps[:4], detune=.0005) * .6
        x += v
    x /= len(notes) * 3
    t = tt(d)
    e = env_adsr(n, min(1.2, d * .3), .1, 1, min(1.5, d * .3))
    if swell:
        e *= .55 + .45 * np.clip(t / d, 0, 1) ** 1.5
    return lp(x * e, 5200)


def koto(f, d=3.0, bright=.5):
    """Karplus-Strong string: y[n] = x[n] + g/2 (y[n-L] + y[n-L-1]), pitch = SR / (L + 1/2)."""
    n = int(d * SR); Li = max(2, int(round(SR / f - .5)))
    exc = np.zeros(n); burst = lp(noise(Li / SR + .002), 2000 + 6000 * bright)
    exc[:len(burst)] = burst[:n]
    g = .996
    a = np.zeros(Li + 2); a[0] = 1; a[Li] = -g / 2; a[Li + 1] = -g / 2
    y = sg.lfilter([1], a, exc) * np.exp(-tt(d) * .6)
    return y / (np.abs(y).max() + 1e-9)


def taiko(size=1.0, d=3.0):
    t = tt(d)
    f = 48 / size + 70 * np.exp(-t * 22)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2 / size)
    modes = sum(np.sin(2 * np.pi * (48 / size) * r * t) * np.exp(-t * (6 + 3 * r)) * a
                for r, a in ((1.59, .3), (2.14, .18), (2.65, .1)))
    hit = lp(noise(d), 1400) * np.exp(-t * 40) * .6
    return np.tanh((body + modes + hit) * 1.6) * .8


def braam(root="D1", d=4.0):
    """Low brass stack: detuned saws, a filter that opens and closes, tube drive."""
    t = tt(d); x = np.zeros_like(t)
    for nm, a in ((root, 1), (root[:-1] + str(int(root[-1]) + 1), .8), ("A" + str(int(root[-1]) + 1), .55)):
        f0 = hz(nm)
        for det in (-.004, 0, .005):
            f = f0 * (1 + det)
            for k in range(1, int(2400 / f)):
                x += a * np.sin(2 * np.pi * f * k * t + k * det * 50) / k
    cut = 180 + 1800 * np.exp(-((t - .35) / .45) ** 2) + 250 * np.exp(-t)
    # time-varying low-pass by blending three fixed filters
    lo, mid, hi = lp(x, 250, 4), lp(x, 800, 4), lp(x, 2200, 4)
    w = np.clip((cut - 250) / 1950, 0, 1)
    y = np.where(w < .5, lo + (mid - lo) * w * 2, mid + (hi - mid) * (w - .5) * 2)
    y = np.tanh(y * .6) * env_adsr(len(t), .08, .6, .55, d - .8)
    return y / (np.abs(y).max() + 1e-9)


def bell(f0=110.0, d=12.0, bright=1.0):
    """Bonshō: inharmonic, beating partials, a wooden-beam strike."""
    t = tt(d); x = np.zeros_like(t)
    for r, a, dec in ((.5, .8, .12), (1, 1, .22), (1.19, .45, .35), (1.56, .5, .45), (2.0, .38, .55),
                      (2.51, .25 * bright, .8), (2.66, .2 * bright, .9), (3.01, .18 * bright, 1.1), (4.1, .1 * bright, 1.6)):
        f = f0 * r
        x += a * (np.sin(2 * np.pi * f * t) + .7 * np.sin(2 * np.pi * (f + .6 + r * .3) * t)) * np.exp(-t * dec)
    strike = lp(noise(.2), 900) * np.exp(-tt(.2) * 25) * .8
    x[:len(strike)] += strike
    return x / np.abs(x).max()


def shakuhachi(notes, d_total):
    """notes: [(t_rel, name, dur)]. Breath + tone with meri bends and growing vibrato."""
    n = int(d_total * SR)
    f = np.zeros(n); amp = np.zeros(n)
    for (t0, nm, du) in notes:
        i0, i1 = int(t0 * SR), min(n, int((t0 + du) * SR))
        tn = np.arange(i1 - i0) / SR
        target = hz(nm)
        bend = target * 2 ** (-.9 / 12 * np.exp(-tn * 5))                   # meri → kari
        vib = 1 + .008 * np.sin(2 * np.pi * 5.2 * tn) * np.clip((tn - .35) / .8, 0, 1)
        f[i0:i1] = bend * vib
        a = np.minimum(1, tn / .12) * np.clip((du - tn) / .25, 0, 1) * (.8 + .2 * np.sin(np.pi * tn / du))
        amp[i0:i1] = np.maximum(amp[i0:i1], a)
    f = np.where(f > 0, f, np.maximum.accumulate(np.where(f > 0, f, 1)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + .22 * np.sin(2 * ph) + .08 * np.sin(3 * ph)
    breath = bp(noise(d_total), 600, 4200) * (.18 + .1 * (amp > 0))
    chiff = hp(noise(d_total), 2500) * np.clip(np.diff(amp, prepend=0) * 400, 0, 1) * .5
    y = (tone * .9 + breath) * amp + chiff
    return lp(y, 7000)


def spiccato(pattern, t0, t1, bpm0, bpm1):
    """Göransson-style bowed ostinato; tempo glides from bpm0 to bpm1. pattern: list of note names."""
    out = []; t = t0; i = 0
    while t < t1:
        bpm = bpm0 + (bpm1 - bpm0) * (t - t0) / (t1 - t0)
        step = 60 / bpm / 4
        f = hz(pattern[i % len(pattern)])
        d = .16
        v = partials(f, d, [(k, 1 / k) for k in range(1, 14)], detune=.001)
        v = lp(v, 3500) * env_adsr(len(v), .006, .05, .3, .09)
        out.append((t, v, (i % 4 == 0)))
        t += step; i += 1
    return out


def swell_noise(d, f1, f2, shape=2.0):
    t = tt(d)
    x = bp(noise(d, "pink"), f1, f2)
    return x * (t / d) ** shape


def reverse_cymbal(d=2.5):
    t = tt(d)
    x = hp(noise(d), 3500) * (t / d) ** 3.5
    return x


# ---------------------------------------------------------------- the cue sheet
ev = TL["events"]

# ticks: the watch that runs through the film --------------------------------
tick_times = [t + .5 for t in range(0, 20)] + [t + .5 for t in range(20, 31)] + [t + .5 for t in range(31, 45, 2)]
for i, t in enumerate(tick_times):
    add(tick(i % 2), t, .32 if t < 7 else .2, 0, "room", .6)
# the palace: accelerating ticks, each a year above
pt = ev["palace_ticks"]; t = pt["t0"]; k = 0
while t < pt["t1"]:
    x = bell(1760, .5, .4) * .08; tk = tick(k % 2); x[:len(tk)] += tk * 1.2
    add(x, t, .28, .15 * np.sin(k), "cave", .5)
    f = (t - pt["t0"]) / (pt["t1"] - pt["t0"])
    t += pt["start_interval"] * (pt["end_interval"] / pt["start_interval"]) ** f; k += 1
for t in range(161, 168):
    add(tick(t % 2), t + .0, .3, 0, "room", .6)
for t in (173.5, 175.5, 177.5):
    add(tick(1), t, .1, 0, "room", .5)
add(tick(0), 179.5, .35, 0, "room", .7)
# inversion: reversed ticks
for t in np.arange(102.5, 117, 1.0):
    add(tick(int(t) % 2)[::-1], t, .18, 0, "room", .5)

# sub drone -----------------------------------------------------------------
for (t0, t1, g, nm) in ((1.5, 20, .07, "D1"), (20, 45, .11, "D1"), (87, 102, .1, "D1"), (117, 124.6, .11, "D1"),
                        (168.3, 172.6, .09, "D1")):
    d = t1 - t0
    x = partials(hz(nm), d, [(1, 1), (2, .4), (3, .1)]) * env_adsr(int(d * SR), 2.5, .1, 1, 2.5)
    add(x, t0, g, 0, None, 1)

# Shepard tone (Dunkirk): an endlessly rising glissando -----------------------
def shepard(t0, t1, octave_period, gain_curve):
    d = t1 - t0; t = tt(d); x = np.zeros_like(t)
    ph = (t / octave_period) % 1.0
    for k in range(7):
        oct_pos = k + ph                                       # 0..7 octaves above base
        f = 55.0 * 2 ** oct_pos
        a = np.exp(-((oct_pos - 3.2) / 1.5) ** 2)
        x += a * (np.sin(2 * np.pi * np.cumsum(f) / SR) + .25 * np.sin(4 * np.pi * np.cumsum(f) / SR))
    return x * gain_curve(t / d)


add(shepard(7, 31, 11.0, lambda u: .05 + .25 * u ** 1.5), 7, .18, 0, "hall", .5)
add(shepard(31, 45, 9.0, lambda u: .3 + .1 * u), 31, .12, 0, "hall", .5)
add(shepard(59, 70.9, 5.5, lambda u: (.15 + .85 * u ** 1.3)), 59, .3, 0, "hall", .45)

# organ + shō harmony ---------------------------------------------------------
def chord(t0, d, notes, g=.4, a=.4, r=2.5, bright=1.0, pan=0.0):
    add(organ(notes, d + r, a, r, bright), t0, g, pan, "hall", .3)


chord(22, 9.4, ["D3", "A3", "E4", "F4"], .12, 3.0, 2.0, .6)
for i, (notes) in enumerate([["D2", "A2", "D3", "F3", "A3", "E4"], ["Bb1", "F2", "D3", "F3", "A3"],
                             ["F2", "C3", "G3", "A3", "C4"], ["C2", "G2", "D3", "G3", "C4", "E4"]]):
    chord(31 + 3.5 * i, 3.5, notes, .3, .25, 2.2)
add(sho(["D5", "E5", "A5", "B5", "E6"], 8.0), 45.3, .55, -.2, "cave", .4)
add(sho(["C5", "D5", "G5", "A5", "D6"], 7.5), 52.0, .55, .2, "cave", .4)
for t0, d, notes, g in ((59, 4, ["D2", "A2", "D3", "F3", "A3"], .28), (63, 3.2, ["Bb1", "F2", "D3", "F3", "Bb3"], .32),
                        (66.2, 2.8, ["G1", "D2", "G2", "Bb2", "D3", "G3"], .36), (69, 1.9, ["A1", "E2", "A2", "C#3", "E3", "A3"], .42)):
    chord(t0, d, notes, g, .15, .6, 1.2)
chord(79, 7.5, ["D1", "D2", "A2", "D3", "F3", "A3", "D4"], .45, .05, 3.5, 1.1)
add(sho(["D4", "A4", "E5", "G5", "A5"], 14.5), 87.5, .35, 0, "cave", .35)
# inversion: chords that swell toward an abrupt stop (reversed organ)
for t0, d, notes in ((102, 4, ["Bb2", "F3", "D4", "A4"]), (106, 4.5, ["F2", "C3", "A3", "G4"]),
                     (110.5, 3.5, ["G2", "D3", "Bb3", "F4"]), (114, 3, ["A2", "E3", "A3", "D4"])):
    x = organ(notes, d, .05, .05, .7)[::-1] * np.linspace(0, 1, int(d * SR)) ** 2
    add(x, t0, .35, 0, "hall", .4)
chord(117.2, 7.2, ["D2", "A2", "Eb3"], .16, 2.5, 1.0, .5)
chord(124.6, 3.6, ["D2", "A2", "D3", "F3", "A3", "D4", "E4"], .45, .08, 2.0, 1.2)
add(sho(["D5", "E5", "A5", "B5", "E6", "F#6"], 4.0), 124.8, .5, 0, "hall", .3)
for i, notes in enumerate([["Bb1", "F2", "D3", "F3", "A3"], ["F2", "C3", "A3", "C4", "G4"],
                           ["C2", "G2", "E3", "G3", "D4"], ["D2", "A2", "F3", "A3", "E4"]]):
    chord(128.5 + 2.4 * i, 2.4, notes, .2, .6, 1.6, .7)
# return: the resolution
for i, notes in enumerate([["D2", "A2", "D3", "F#3", "A3"], ["C#2", "A2", "E3", "A3", "C#4"], ["B1", "F#2", "D3", "F#3", "B3"],
                           ["G1", "D2", "B2", "D3", "G3"], ["F#2", "A2", "D3", "F#3", "A3", "D4"], ["G2", "D3", "F#3", "B3", "D4"]]):
    g = [.3, .32, .36, .4, .34, .28][i]
    chord(138 + 3.5 * i, 3.5, notes, g, .3, 2.0, .9 + .1 * i)
chord(159, 1.2, ["A1", "E2", "A2", "D3", "E3"], .22, .3, 1.5)
add(sho(["D5", "E5", "A5", "B5", "E6", "F#6"], 21.0), 138.5, .3, 0, "hall", .3)
chord(160.2, 6.5, ["D2", "A2", "E3", "F3", "A3"], .16, 1.0, 2.2, .5)
add(sho(["D5", "A5", "E6"], 4.0), 168.4, .18, 0, "hall", .3)
chord(172.6, 5.0, ["D1", "D2", "A2", "E3", "A3", "D4"], .4, .05, 3.0, 1.0)
add(sho(["D5", "E5", "A5", "E6"], 7.0), 172.8, .3, 0, "hall", .3)

# strings: sustained pads under the return, spiccato under palace → wave -------
for t0, d, root in ((138, 21, "D3"),):
    pad = sum(partials(hz(n), d, [(k, 1 / k) for k in range(1, 12)], detune=.002) for n in ("D3", "A3", "F#4"))
    add(lp(pad, 2400) * env_adsr(int(d * SR), 4, 1, .8, 5) * .12, t0, 1.0, 0, "hall", .3)
for (t, v, acc) in spiccato(["D3", "A3", "D4", "A3", "F3", "A3", "D4", "E4"], 52, 58.9, 104, 118):
    add(v, t, .06 * (1.3 if acc else 1), .3, "hall", .6)
for (t, v, acc) in spiccato(["D3", "A3", "D4", "A3", "Bb2", "F3", "Bb3", "F3", "G2", "D3", "G3", "D3", "A2", "E3", "A3", "C#4"],
                            59, 70.9, 118, 168):
    frac = (t - 59) / 11.9
    add(v, t, (.07 + .18 * frac) * (1.35 if acc else 1), -.3 if int(t * 8) % 2 else .3, "hall", .6)

# koto -------------------------------------------------------------------------
for t, nm in ((8.0, "D4"), (9.6, "A4"), (10.4, "Bb4"), (12.2, "G4"), (14.0, "D5"), (15.1, "Eb5"), (17.3, "A4"),
              (117.6, "D4"), (118.9, "Eb4"), (120.4, "A4"), (121.2, "G4"), (122.6, "D5"), (123.4, "Bb4"), (124.0, "A4"),
              (168.9, "D4"), (170.2, "A4")):
    add(koto(hz(nm), 3.5, .5), t, .22, rng.uniform(-.4, .4), "room", .5)
# inversion: reversed koto
for t, nm in ((103.0, "A4"), (104.7, "D5"), (107.2, "G4"), (108.6, "Bb4"), (111.5, "Eb5"), (113.1, "D5"), (115.0, "A4")):
    x = koto(hz(nm), 2.2, .6)[::-1]
    add(x, t, .2, rng.uniform(-.5, .5), "room", .5)

# shakuhachi -------------------------------------------------------------------
yomi = [(1.5, "A4", 2.2), (3.9, "G4", .9), (4.9, "Eb4", 1.3), (6.4, "D4", 2.4), (9.2, "Bb4", 1.2), (10.5, "A4", .8),
        (11.4, "G4", .7), (12.2, "A4", 2.6)]
add(shakuhachi(yomi, 15.5), 87, .5, -.15, "cave", .45)
ret = [(2.0, "A4", 1.6), (3.7, "B4", .8), (4.6, "D5", 2.2), (7.2, "E5", 1.0), (8.3, "F#5", 1.8), (10.4, "E5", .9),
       (11.4, "D5", 1.2), (12.8, "B4", 1.6), (14.8, "A4", 2.8), (18.0, "D5", 3.0)]
add(shakuhachi(ret, 22.0), 138, .42, .1, "hall", .45)
add(bp(noise(4.5), 600, 3000) * env_adsr(int(4.5 * SR), 1.5, .5, .6, 2) * .12, 1.8, 1, 0, "hall", .5)   # a breath

# percussion: impacts, heartbeat, taiko ------------------------------------------
for t in ev["impacts"]:
    big = t in (31.0, 70.6, 79.0, 124.6, 172.6)
    add(taiko(1.25 if big else 1.0), t, .9 if big else .6, 0, "hall", .5)
    if t in (31.0, 70.6, 79.0, 124.6):
        add(braam("D1", 4.5), t, .5, 0, "hall", .45)
    if t in (79.0, 124.6, 70.6):
        add(reverse_cymbal(2.4), t - 2.4, .12, 0, "hall", .6)
for t in np.arange(20.0, 31.0, 1.0):
    for dt, g in ((0, 1), (.28, .6)):
        add(taiko(2.2, 1.0) * np.exp(-tt(1.0) * 6), t + dt, .35 * g * (.5 + .5 * (t - 20) / 11), 0, "room", .7)
for t in np.arange(62.0, 70.6, .75):
    add(taiko(1.4, 2.0), t, .35 + .35 * (t - 62) / 8.6, rng.uniform(-.3, .3), "hall", .5)
for t in np.arange(88.0, 101.0, 2.0):
    add(taiko(1.7, 2.5), t, .25, 0, "cave", .5)

# bells ---------------------------------------------------------------------
for t in ev["bells"]:
    add(bell(73.4, 14), t, .42, 0, "hall", .5)
for t in ev["reverse_bells"]:
    add(bell(98.0, 5)[::-1], t, .35, 0, "hall", .5)
add(bell(73.4, 12), 128.3, .4, 0, "hall", .5)

# textures: sea, rain, thunder, underwater, smoke, cracks, gold ----------------
def sea(d, level, calm=False):
    x = lp(noise(d, "brown"), 900) + bp(noise(d, "pink"), 300, 2500) * .3
    t = tt(d)
    m = .55 + .45 * np.sin(2 * np.pi * t / (7.5 if calm else 4.3)) * np.sin(2 * np.pi * t / 11.1 + 1)
    return x * m * level


for t0, t1, lvl, calm in ((31, 45, .5, False), (59, 70.9, .6, False), (138, 160, .25, True)):
    x = np.stack([sea(t1 - t0, lvl, calm), sea(t1 - t0, lvl, calm)], 1)
    x *= env_adsr(len(x), .05, .1, 1, 1.5)[:, None]
    add(x, t0, .55, 0, None, 1)
rain = np.stack([hp(noise(14, "pink"), 2500), hp(noise(14, "pink"), 2500)], 1) * .22
add(rain * env_adsr(len(rain), .05, .1, 1, 1.0)[:, None], 31, 1, 0, None, 1)
for t in ev["lightning"]:
    d = 5.0; x = lp(noise(d, "brown"), 180) * np.exp(-tt(d) * .8) * (1 - np.exp(-tt(d) * 6))
    crack = hp(noise(.4), 1200) * np.exp(-tt(.4) * 12)
    add(x * 1.4, t + .45, .9, rng.uniform(-.4, .4), "hall", .6)
    add(crack, t + .02, .3, rng.uniform(-.6, .6), "hall", .5)
# the wave: a roar that grows until the cut
d = 11.9; roar = lp(noise(d, "brown"), 400) + bp(noise(d, "pink"), 200, 1800) * .6
add(roar * (tt(d) / d) ** 2.2 * 1.2, 59, .8, 0, "hall", .7)
add(hp(noise(.6), 200) * np.exp(-tt(.6) * 4), 70.6, .8, 0, "hall", .4)       # the crash
# underwater
d = 14; uw = lp(noise(d, "brown"), 260) * .6
add(uw * env_adsr(int(d * SR), 1, .1, 1, 1), 45, .7, 0, "cave", .6)
for t in rng.uniform(45.5, 58.5, 26):
    dd = rng.uniform(.04, .12); f0 = rng.uniform(500, 1400)
    tb = tt(dd); b = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 3 * tb / dd)) / SR) * np.sin(np.pi * tb / dd)
    add(b, t, .08, rng.uniform(-.7, .7), "cave", .4)
# scan (12–17)
d = 5.2; tsc = tt(d); fsw = 180 * 2 ** (3.4 * tsc / d)
scan = np.sin(2 * np.pi * np.cumsum(fsw) / SR) * .3 + bp(noise(d), 2000, 9000) * .2
add(scan * np.sin(np.pi * tsc / d) ** 2, 12.0, .25, 0, "hall", .5)
# wire glitter (21–25)
for t in rng.uniform(21, 25.2, 60):
    f = hz(rng.choice(["D6", "Eb6", "G6", "A6", "Bb6", "D7"])); dd = .09
    add(np.sin(2 * np.pi * f * tt(dd)) * np.exp(-tt(dd) * 40), t, .05, rng.uniform(-.8, .8), "hall", .4)
# ensō brush (73.8–77.2)
d = 3.6; tb = tt(d)
brush = bp(noise(d), 1200, 7000) * (np.sin(np.pi * tb / d) ** .5) * (.6 + .4 * np.abs(np.sin(2 * np.pi * 9 * tb)))
add(brush, 73.7, .13, 0, "room", .6)
# accretion shimmer (80–87)
for t in np.sort(rng.uniform(80, 86.5, 140)):
    f = hz(rng.choice(["D6", "F6", "A6", "E6", "D7", "A5"])); dd = rng.uniform(.3, .9)
    g = np.sin(2 * np.pi * f * tt(dd)) * np.sin(np.pi * tt(dd) / dd) ** 2
    add(g, t, .035, np.sin(t * 3.1), "hall", .3)
# yomi → white (99.5–102)
add(swell_noise(2.6, 500, 9000, 3.0), 99.4, .4, 0, "hall", .5)
# smoke (124.6–128)
d = 4.0; sm = swell_noise(d, 150, 3000, .6) * np.exp(-((tt(d) - 2.4) / 1.6) ** 2)
add(np.stack([sm, swell_noise(d, 150, 3000, .6) * np.exp(-((tt(d) - 2.4) / 1.6) ** 2)], 1), 124.7, .9, 0, "hall", .5)
# cracks (129.2–135.5) and the gold
for t in np.sort(rng.uniform(129.2, 135.5, 90)):
    dd = .05; c = bp(noise(dd), rng.uniform(1500, 5000), 9000) * np.exp(-tt(dd) * 90)
    add(c, t, .12 * rng.uniform(.3, 1), rng.uniform(-.7, .7), "room", .6)
for t in np.sort(rng.uniform(129.5, 137.5, 50)):
    f = hz(rng.choice(["A6", "D7", "E7", "F#6"])); dd = 1.2
    add(np.sin(2 * np.pi * f * tt(dd)) * np.exp(-tt(dd) * 4), t, .03, rng.uniform(-.6, .6), "hall", .3)
# snow chimes (140–159)
for t in np.sort(rng.uniform(140, 159, 36)):
    f = hz(rng.choice(["D7", "A6", "E7", "F#7", "B6"])); dd = 1.5
    add(np.sin(2 * np.pi * f * tt(dd)) * np.exp(-tt(dd) * 3.5), t, .025, rng.uniform(-.8, .8), "hall", .3)

# ---------------------------------------------------------------- reverbs + master
def ir(rt60, predelay=.02, damp=3500, er=True):
    L = int(rt60 * 1.2 * SR); t = np.arange(L) / SR
    out = []
    for ch in range(2):
        n = rng.standard_normal(L)
        tail = lp(n, damp) * np.exp(-6.9 * t / rt60) + hp(n, 3000) * np.exp(-6.9 * t / (rt60 * .35)) * .3
        tail[:int(predelay * SR)] = 0
        if er:
            for dly, g in ((.011, .5), (.019, .38), (.027, .3), (.041, .22), (.053, .18)):
                tail[int((dly + ch * .003) * SR)] += g
        out.append(tail / np.sqrt((tail ** 2).sum()))
    return np.stack(out, 1)


mix = bus["dry"].astype(np.float64).copy()
for name, rt, damp, g in (("room", 1.1, 5000, .9), ("hall", 4.8, 3200, 1.0), ("cave", 6.5, 1400, 1.0)):
    h = ir(rt, damp=damp)
    for ch in range(2):
        mix[:, ch] += sg.fftconvolve(bus[name][:, ch], h[:, ch])[:N] * g

# the palace is heard from under water
a, b = int(45 * SR), int(59 * SR)
mix[a:b] = mix[a:b] * .35 + lp(mix[a:b], 700, 2) * .9

# hard cuts to silence (Nolan): gate the master, 4 ms ramps
gate = np.ones(N)
for t0, t1 in ev["silence"]:
    i0, i1 = int(t0 * SR), int(t1 * SR); r = int(.004 * SR)
    gate[i0:i1] = 0
    gate[i0 - r:i0] = np.linspace(1, 0, r); gate[i1:i1 + r] = np.minimum(gate[i1:i1 + r], np.linspace(0, 1, r))
mix *= gate[:, None]
# the shutter lives inside its own silence
d = .12; ts = tt(d)
shutter = (hp(noise(d), 1500) * np.exp(-ts * 160) + np.sin(2 * np.pi * 1900 * ts) * np.exp(-ts * 90) * .5)
sh2 = shutter.copy(); sh2[:int(.05 * SR)] *= 0
click = shutter + np.roll(sh2, int(.055 * SR)) * .7
i0 = int(ev["shutter"] * SR)
mix[i0:i0 + len(click)] += np.stack([click, click], 1) * .45

# gentle master: low shelf lift, soft limiter, fades
mix = mix + lp(mix, 90, 2) * .12
peak = np.percentile(np.abs(mix), 99.95)
mix = np.tanh(mix / peak * 1.1) / np.tanh(1.1)
fade = np.ones(N); fi = int(.5 * SR); fade[:fi] = np.linspace(0, 1, fi)
fo0 = int(179.2 * SR); fade[fo0:] = np.linspace(1, 0, N - fo0) ** 2
mix *= fade[:, None] * .89
# keep the last tick audible over the fade
i0 = int(179.5 * SR); tk = tick(0) * .5
mix[i0:i0 + len(tk)] += np.stack([tk, tk], 1)[: N - i0]
sf.write(sys.argv[2], np.clip(mix, -1, 1).astype(np.float32), SR, subtype="PCM_24")
print("wrote", sys.argv[2], f"{DUR:.0f}s peak {np.abs(mix).max():.2f} rms {np.sqrt((mix ** 2).mean()):.3f}")
