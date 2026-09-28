"""Render analysis/song_map.png from song.json + the decoded mix.

usage: python3 plot_map.py song.json mix.wav out.png
"""
import sys, json
import numpy as np
import soundfile as sf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

SJ, WAV, OUT = sys.argv[1:4]
S = json.load(open(SJ))
x, sr = sf.read(WAV)
x = x.mean(1)

INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"
# section colour by role (reference categorical palette, fixed order; every band is also text-labelled)
ROLE = {"verse": "#2a78d6", "chorus": "#eb6834", "prechorus": "#1baf7a", "breakdown": "#4a3aa7", "stop": "#52514e",
        "outro": "#e87ba4", "intro": "#b9b8b3", "ending": "#b9b8b3"}


def role(name):
    for k in ("prechorus", "chorus", "verse", "breakdown", "stop", "outro", "intro", "ending"):
        if name.startswith(k):
            return k
    return "intro"


plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": SURF})

STRIPS = [(0, 53), (52.5, 105.5), (105, 157)]
fig = plt.figure(figsize=(30, 36))
gs = fig.add_gridspec(1 + 4 * len(STRIPS), 1, height_ratios=[2.2] + [2.0, 1.4, 0.9, 2.3] * len(STRIPS), hspace=0.35)

# envelope of the mix at 10 ms
h = int(sr * 0.01)
n = len(x) // h
env_max = x[:n * h].reshape(n, h).max(1)
env_min = x[:n * h].reshape(n, h).min(1)
te = np.arange(n) * 0.01
en = np.array(S["energy"])
t10 = np.arange(len(en)) * 0.1
C = S["curves10hz"]
T0, T, BAR = S["grid"]["t0"], S["beat_period"], S["grid"]["bar_period"]


def bands(ax, a, b, label=True, y=0.97, fs=12):
    for s in S["sections"]:
        if s["end"] < a or s["start"] > b:
            continue
        col = ROLE[role(s["name"])]
        ax.axvspan(max(a, s["start"]), min(b, s["end"]), color=col, alpha=0.10, lw=0)
        ax.axvline(s["start"], color=col, lw=1.5, alpha=0.8)
        if label and s["start"] >= a - 0.1:
            ax.text(s["start"] + 0.15, y, s["name"].replace("_", " "), transform=ax.get_xaxis_transform(), va="top",
                    ha="left", fontsize=fs, color=INK, fontweight="bold")


def bar_ticks(ax, a, b, every=1, labels=True):
    k = int(np.ceil((a - T0) / BAR))
    while T0 + k * BAR <= b:
        t = T0 + k * BAR
        ax.axvline(t, color=GRID, lw=0.8, zorder=0)
        if labels and k % every == 0:
            ax.text(t + 0.05, 0.02, f"{k + 1}", transform=ax.get_xaxis_transform(), fontsize=8.5, color=MUTED)
        k += 1


# ---------------- overview
ax = fig.add_subplot(gs[0])
ax.fill_between(t10, 0, en, color="#2a78d6", alpha=0.35, lw=0)
ax.plot(t10, en, color="#2a78d6", lw=1.5)
bands(ax, 0, S["duration"], fs=11)
for e in S["events"]:
    if e["type"] in ("drop",):
        ax.annotate("", xy=(e["t"], 1.02), xytext=(e["t"], 1.16), xycoords=("data", "axes fraction"),
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5))
    if e["type"] == "stop":
        ax.add_patch(Rectangle((e["t"], 0), e["end"] - e["t"], 1, color=INK, alpha=0.25, lw=0))
ax.set_xlim(0, S["duration"])
ax.set_ylim(0, 1.05)
ax.set_ylabel("energy (0-1)")
ax.set_title(f"I'm Upping My P(doom) - song map   |   {S['bpm']:.0f} BPM, 4/4, beat {S['beat_period']*1000:.1f} ms, "
             f"grid t0 {S['grid']['t0']:.3f} s, {len(S['downbeats'])} bars, integrated {S['energy_info']['integrated_lufs']:.1f} LUFS"
             "   (arrows = drops, dark bands = instrumental stops)", loc="left", fontsize=15, color=INK, pad=28)
ax.set_xticks(np.arange(0, 157, 10))
ax.grid(axis="y", color=GRID, lw=0.6)

hits = S["hits"]
for si, (a, b) in enumerate(STRIPS):
    base = 1 + 4 * si
    # waveform
    axw = fig.add_subplot(gs[base])
    m = (te >= a) & (te <= b)
    bands(axw, a, b)
    bar_ticks(axw, a, b)
    axw.fill_between(te[m], env_min[m], env_max[m], color=INK2, lw=0)
    for e in S["events"]:
        if not (a <= e["t"] <= b):
            continue
        if "end" in e and e["type"] in ("stop", "riser", "fill", "build", "fade"):
            col = {"stop": INK, "riser": "#eda100", "fill": "#1baf7a", "build": "#eda100", "fade": MUTED}[e["type"]]
            axw.add_patch(Rectangle((e["t"], -1.0), e["end"] - e["t"], 0.16, color=col, alpha=0.9, lw=0))
            axw.text(e["t"], -0.80, e["type"], fontsize=9, color=col, va="bottom")
        elif e["type"] in ("drop", "impact", "accent", "final_hit", "drop_out", "vocal_entry"):
            axw.axvline(e["t"], color="#e34948" if e["type"] == "drop" else INK2, lw=2 if e["type"] == "drop" else 1, ls="-" if e["type"] == "drop" else "--")
            axw.text(e["t"] + 0.08, 0.55 if e["type"] == "drop" else -0.55, e["type"].upper() if e["type"] == "drop" else e["type"].replace("_", " "), fontsize=10,
                     color="#e34948" if e["type"] == "drop" else INK2, fontweight="bold" if e["type"] == "drop" else None)
    axw.set_xlim(a, b)
    axw.set_ylim(-1.0, 1.0)
    axw.set_ylabel("mix waveform")
    axw.set_xticks(np.arange(np.ceil(a), b, 1), minor=True)
    axw.set_xticks(np.arange(np.ceil(a / 5) * 5, b, 5))
    axw.tick_params(labelbottom=False)
    axw.text(0.0, 1.02, f"{a:.0f}-{b:.0f} s   (grey numbers at the bottom = bar numbers)", transform=axw.transAxes, fontsize=11, color=INK2)

    # loudness
    axl = fig.add_subplot(gs[base + 1], sharex=axw)
    bands(axl, a, b, label=False)
    m10 = (t10 >= a) & (t10 <= b)
    for key, col, lab in [("lufs", INK, "mix"), ("lufs_inst", "#2a78d6", "instrumental stem"), ("lufs_vocal", "#eb6834", "vocal stem")]:
        axl.plot(t10[m10], np.array(C[key])[m10], color=col, lw=2 if key == "lufs" else 1.4, label=lab)
    axl.set_ylim(-50, -5)
    axl.set_ylabel("momentary LUFS")
    axl.grid(axis="y", color=GRID, lw=0.6)
    axl.legend(loc="lower left", fontsize=9, frameon=False, ncol=3)
    axl.tick_params(labelbottom=False)

    # hits raster
    axh = fig.add_subplot(gs[base + 2], sharex=axw)
    bar_ticks(axh, a, b, labels=False)
    rows = {"kick": 3, "clap": 2, "hat": 1, "perc": 0}
    for ty, yv in rows.items():
        ts = [hh["t"] for hh in hits if hh["type"] == ty and a <= hh["t"] <= b]
        axh.vlines(ts, yv - 0.35, yv + 0.35, color={"kick": INK, "clap": "#eb6834", "hat": "#2a78d6", "perc": MUTED}[ty], lw=1.3)
    axh.set_yticks(list(rows.values()))
    axh.set_yticklabels(list(rows.keys()))
    axh.set_ylim(-0.6, 3.6)
    axh.tick_params(labelbottom=False)

    # lyrics
    axy = fig.add_subplot(gs[base + 3], sharex=axw)
    bar_ticks(axy, a, b, labels=False)
    bands(axy, a, b, label=False)
    k = 0
    for L in S["lines"]:
        if L["end"] < a or L["start"] > b:
            continue
        yv = 3.0 - (L["i"] % 4) * 0.8
        hook = "P(doom)" in L["text"]
        # subtitle span (thin, muted) vs refined span (thick)
        axy.plot([L["sub_start"], L["sub_end"]], [yv + 0.32, yv + 0.32], color="#e34948" if L["sub_off_gt150ms"] else MUTED, lw=2, alpha=0.8)
        axy.plot([L["start"], L["end"]], [yv, yv], color="#eb6834" if hook else "#2a78d6", lw=7, solid_capstyle="butt")
        tx = max(a, L["start"])
        axy.text(tx, yv - 0.16, f"{L['i']}: {L['text']}", fontsize=10, color=INK, va="top", clip_on=True,
                 fontweight="bold" if hook else None)
        for w in L["words"]:
            if a <= w["t"] <= b:
                axy.plot([w["t"], w["t"]], [yv - 0.12, yv + 0.12], color=INK, lw=1)
    for hk in S["hooks"]:
        for j_, (s_, t_) in enumerate(hk["syl"]):
            if a <= t_ <= b:
                axy.text(t_, 3.62 + 0.22 * (j_ % 2), s_, fontsize=9, color="#b8420f", ha="center", fontweight="bold", clip_on=True)
                axy.plot([t_, t_], [3.45, 3.6 + 0.22 * (j_ % 2)], color="#eb6834", lw=1.2)
    for v in S["vocal_extra"]:
        if v["end"] < a or v["start"] > b:
            continue
        axy.plot([max(a, v["start"]), min(b, v["end"])], [-0.25, -0.25], color="#1baf7a", lw=5)
        axy.text(max(a, v["start"]), -0.45, v["what"][:60], fontsize=8.5, color="#0e7a55", va="top", clip_on=True)
    axy.set_ylim(-1.0, 4.1)
    axy.set_yticks([])
    axy.set_xlim(a, b)
    axy.set_xlabel("time (s)")
    axy.set_xticks(np.arange(np.ceil(a / 5) * 5, b, 5))
    if si == 0:
        axy.text(0.0, 1.02, "lyrics: thick = refined line span (orange = P(doom) hook), ticks = word starts; thin line above = burned-in "
                 "subtitle span (red = off by >150 ms); orange labels on top = hook syllables; green = wordless vocal",
                 transform=axy.transAxes, fontsize=10, color=INK2)

plt.savefig(OUT, dpi=62, bbox_inches="tight")
print("saved", OUT)
