"""Combine three lyric aligners + vocal onsets into per-word and per-line timings.

Evidence:
  PS  PocketSphinx HMM forced alignment (fine boundaries, occasionally derails)
  PK  Parakeet TDT-CTC 110M (CTC branch) forced alignment, 8 sub-frame shifts (robust, ~80 ms lag)
  FC  NeMo FastConformer hybrid large (CTC branch) forced alignment, 8 sub-frame shifts
  ON  vocal onsets: madmom CNN onsets on the MDX vocal stem + pYIN pitch-change onsets
  VA  vocal activity (vocal stem RMS + pYIN voicing) for line ends

usage: python3 vocal_timing.py <scratch> <lyrics.js> <out.json> [overrides.json]
"""
import sys, json
import numpy as np
from lyrics_lex import load_lines

SP, LY, OUT = sys.argv[1:4]
OVR = {k: v for k, v in json.load(open(sys.argv[4])).items() if not k.startswith("_")} if len(sys.argv) > 4 else {}
lines = load_lines(LY)

LAG = {"PK": 0.08, "FC": 0.05, "PS": -0.02}  # calibrated by onset coincidence (see REPORT.md)


def w_ctc(fn):
    R = json.load(open(fn))
    W = {}
    for g in R:
        for t in g["tokens"]:
            k = (t["line"], t["word"])
            if t["t"] is None:
                continue
            if k not in W:
                W[k] = [t["t"], t["e"]]
            else:
                W[k][1] = t["e"]
    return W


def w_ps(fn):
    R = json.load(open(fn))
    W = {}
    for g in R:
        for t in g["tokens"]:
            if "line" not in t:
                continue
            k = (t["line"], t["word"])
            if k not in W:
                W[k] = [t["t"], t["e"]]
            else:
                W[k][1] = t["e"]
    return W


PK = w_ctc(f"{SP}/work/align_ctc_pk8.json")
FC = w_ctc(f"{SP}/work/align_ctc_fc8.json")
PS = w_ps(f"{SP}/work/align_ps.json")

# ---------------- onsets
on_mm = np.load(f"{SP}/mm_onsets_vocals.npy")
P = np.load(f"{SP}/vocal_pitch.npz")
f0, vprob, rms = P["f0"], P["vprob"], P["rms"]
hop_t = 256 / 22050
tp = np.arange(len(f0)) * hop_t
midi = 69 + 12 * np.log2(np.where(np.isfinite(f0), f0, np.nan) / 440)
# pitch-change onsets: median-smoothed pitch jumps >= 0.8 st that hold for >= 60 ms
pc = []
m = np.copy(midi)
k = 5
for i in range(k, len(m) - k):
    a, b = m[i - k:i], m[i:i + k]
    if np.sum(np.isfinite(a)) >= 3 and np.sum(np.isfinite(b)) >= 4:
        if abs(np.nanmedian(b) - np.nanmedian(a)) >= 0.8:
            pc.append(tp[i])
pc = np.array(pc)
if len(pc):
    keep = [pc[0]]
    for t in pc[1:]:
        if t - keep[-1] > 0.08:
            keep.append(t)
    pc = np.array(keep)
# voicing onsets: unvoiced->voiced transitions
vo = tp[1:][(vprob[1:] > 0.5) & (vprob[:-1] <= 0.5)]
ON = np.sort(np.concatenate([on_mm, pc, vo]))
merged = [ON[0]]
for t in ON[1:]:
    if t - merged[-1] > 0.035:
        merged.append(t)
ON = np.array(merged)
# priority: madmom onsets are the most reliable, pitch/voicing ones are fallbacks
def nearest(t, arr, win):
    if len(arr) == 0:
        return None
    j = np.argmin(np.abs(arr - t))
    return float(arr[j]) if abs(arr[j] - t) <= win else None


# ---------------- vocal activity (10 ms)
rms_db = 20 * np.log10(rms + 1e-6)
ref = np.percentile(rms_db[np.isfinite(rms_db)], 95)
active = (rms_db > ref - 24) & (vprob > 0.25)


def vocal_offset(t_from, t_limit):
    """first time after t_from where vocal activity stops for >= 150 ms (<= t_limit)."""
    i = int(t_from / hop_t)
    n_off = int(0.15 / hop_t)
    run = 0
    while i < len(active) and tp[i] < t_limit:
        run = run + 1 if not active[i] else 0
        if run >= n_off:
            return float(tp[i - n_off + 1]) + 0.05  # + consonant release allowance
        i += 1
    return float(t_limit)


def vocal_onset_before(t, lookback):
    """earliest start of the continuous active region that contains / precedes t (within lookback)."""
    i = int(t / hop_t)
    j = i
    gap = 0
    while j > 0 and tp[j] > t - lookback:
        if active[j]:
            gap = 0
        else:
            gap += 1
            if gap > int(0.08 / hop_t):
                break
        j -= 1
    return float(tp[j + gap]) if j + gap < i else float(t)


out_lines = []
flags = []
for li, L in enumerate(lines):
    words = []
    for wi, (dw, sp) in enumerate(L["words"]):
        k = (li, wi)
        est = {}
        if k in PK:
            est["PK"] = PK[k][0] - LAG["PK"]
        if k in FC:
            est["FC"] = FC[k][0] - LAG["FC"]
        if k in PS:
            est["PS"] = PS[k][0] - LAG["PS"]
        ctc = np.mean([est[m] for m in ("PK", "FC") if m in est])
        src = "ctc"
        t = ctc
        if "PS" in est and abs(est["PS"] - ctc) <= 0.2:
            t = 0.5 * est["PS"] + 0.5 * ctc if abs(est["PS"] - ctc) > 0.1 else est["PS"]
            src = "ps+ctc"
        s = nearest(t, on_mm, 0.07)
        if s is not None:
            t, src = s, src + ">onset"
        else:
            s = nearest(t, ON, 0.05)
            if s is not None:
                t, src = s, src + ">pitch/voicing"
        key = f"{li}:{wi}"
        if key in OVR:
            t, src = OVR[key], "manual"
        words.append({"w": dw, "t": round(float(t), 3), "src": src,
                      "est": {m: round(float(v), 3) for m, v in est.items()}})
    # enforce monotonic word order
    for j in range(1, len(words)):
        if words[j]["t"] <= words[j - 1]["t"] + 0.05:
            if words[j]["src"] == "manual" and words[j - 1]["src"] != "manual":
                words[j - 1]["t"] = round(words[j]["t"] - 0.12, 3)
                words[j - 1]["src"] += ",forced-monotonic"
            else:
                words[j]["t"] = round(words[j - 1]["t"] + 0.06, 3)
                words[j]["src"] += ",forced-monotonic"
    out_lines.append({"i": li, "text": L["text"], "sub_start": L["start"], "sub_end": L["end"], "words": words})

# word ends and line boundaries
for li, L in enumerate(out_lines):
    ws = L["words"]
    nxt = out_lines[li + 1]["words"][0]["t"] if li + 1 < len(out_lines) else ws[-1]["t"] + 4
    for j, w in enumerate(ws):
        lim = ws[j + 1]["t"] if j + 1 < len(ws) else nxt - 0.02
        if j + 1 < len(ws):
            w["e"] = round(lim, 3)
        else:
            w["e"] = round(min(vocal_offset(w["t"] + 0.12, lim), lim), 3)
    L["start"] = ws[0]["t"]
    L["end"] = ws[-1]["e"]
    ko = f"{li}:end"
    if ko in OVR:
        L["end"] = ws[-1]["e"] = OVR[ko]
    L["d_start"] = round(L["start"] - L["sub_start"], 3)
    L["d_end"] = round(L["end"] - L["sub_end"], 3)
    L["flag_150ms"] = bool(abs(L["d_start"]) > 0.15 or abs(L["d_end"]) > 0.15)

json.dump({"lags": LAG, "lines": out_lines, "onsets": [round(float(x), 3) for x in on_mm],
           "pitch_onsets": [round(float(x), 3) for x in pc]}, open(OUT, "w"), indent=1)
for L in out_lines:
    print(f"{L['i']:2d} {L['start']:7.2f}-{L['end']:7.2f} (sub {L['sub_start']:6.2f}-{L['sub_end']:6.2f}, d {L['d_start']:+.2f}/{L['d_end']:+.2f}) "
          + " ".join(f"{w['w']}@{w['t']:.2f}" for w in L["words"]))
