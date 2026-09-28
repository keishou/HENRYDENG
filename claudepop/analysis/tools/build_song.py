"""Assemble claudepop/analysis/song.json, the timing backbone of the film, from the analysis intermediates.

Inputs (all under out/work/analysis unless noted)
  grid.json                 beat grid, bar phase, drum hits, per-beat levels           (grid.py)
  align_mms.json / align_w2v.json   whole-song CTC forced alignments, 4 sub-frame shifts each (align_fa.py)
  vocal_onsets.json, vocal_feats.npz   vocal-stem onsets, f0, RMS                     (vocal_feats.py)
  whisper_vocals.json       Whisper large-v3 transcript of the vocal stem, for sung material missing from lyrics.js
  analysis/tools/word_overrides.json   manually verified word starts (each with the evidence that decided it)
  analysis/tools/structure.json        sections / events / extra vocals as verified by eye and ear-proxy plots
Outputs
  analysis/song.json
  out/audio/click_words.wav   vocal stem + a click at every word start (accented on line starts), 44.1 kHz
  out/audio/click_beats.wav   full mix  + a click on every beat (accented on downbeats), 44.1 kHz
  out/work/analysis/build_stats.json

Word timing rule (per word)
  1. Each model's start = median over its 4 shifted runs, minus that model's lag (median offset to the nearest vocal
     onset over words that have one within 60 ms).
  2. If the two models agree within 80 ms, the candidate is their mean; otherwise the candidate is the model that has
     a SuperFlux vocal onset within 40 ms (wav2vec2 if both or neither), and the word is marked 'disagree'.
  3. The candidate snaps to the nearest SuperFlux onset within 50 ms, else to an energy / pitch onset within 35 ms.
  4. A manual override (verified on close-up spectrograms against the 16th-note grid and the per-character CTC
     posteriors) replaces all of that.
  Uncertainty u (ms) = the spread of the evidence around the chosen time (see REPORT.md); lines with any word start
  u > 80 ms are flagged.

usage: python3 build_song.py <claudepop_dir> <lyrics.js>
"""
import sys, os, json
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
from lyrics_lex import load_lines

ROOT, LY = sys.argv[1:3]
W = f"{ROOT}/out/work/analysis"
TOOLS = os.path.dirname(os.path.abspath(__file__))
lines_src = load_lines(LY)
G = json.load(open(f"{W}/grid.json"))
ONS = json.load(open(f"{W}/vocal_onsets.json"))
F = np.load(f"{W}/vocal_feats.npz")
OVR = json.load(open(f"{TOOLS}/word_overrides.json")) if os.path.exists(f"{TOOLS}/word_overrides.json") else {}
STRUCT = json.load(open(f"{TOOLS}/structure.json"))
WH = json.load(open(f"{W}/whisper_vocals.json")) if os.path.exists(f"{W}/whisper_vocals.json") else {"segments": []}

T0, T, BPM, DUR = G["t0"], G["beat_period"], G["bpm"], G["duration"]
beats = np.array(G["beats"])
on_flux = np.array([o[0] for o in ONS["onsets_flux"]])
on_flux_s = np.array([o[1] for o in ONS["onsets_flux"]])
on_en = np.array(ONS["onsets_energy"])
on_pitch = np.array(ONS["onsets_pitch"])
on_other = np.sort(np.concatenate([on_en, on_pitch]))


def bar_start(b):  # 1-based bar number -> time
    return T0 + (b - 1) * 4 * T


def nearest(arr, t):
    if not len(arr):
        return None, 1e9
    j = int(np.argmin(np.abs(arr - t)))
    return float(arr[j]), float(arr[j] - t)


def grid_pos(t):
    q = (t - T0) / (T / 4)
    qi = int(np.round(q))
    return {"bar": qi // 16 + 1, "beat": (qi // 4) % 4 + 1, "six": qi % 4 + 1, "off_ms": round((q - qi) * T / 4 * 1000)}


# ------------------------------------------------------------------ per-model word starts
def load_model(m):
    A = json.load(open(f"{W}/align_{m}.json"))
    out = {}
    for li, L in enumerate(lines_src):
        for wi in range(len(L["words"])):
            k = f"{li}:{wi}"
            ts = [s["words"][k]["t"] for s in A["shifts"] if k in s["words"]]
            es = [s["words"][k]["e"] for s in A["shifts"] if k in s["words"]]
            subs = {}
            for s in A["shifts"]:
                for gk, gv in s["letter_groups"].items():
                    if gk.startswith(k + ":"):
                        subs.setdefault(int(gk.split(":")[2]), []).append(gv["t"])
            out[(li, wi)] = {"t": float(np.median(ts)), "e": float(np.median(es)), "spread": float(max(ts) - min(ts)),
                             "subs": {p: float(np.median(v)) for p, v in sorted(subs.items())}}
    return out


M = {m: load_model(m) for m in ("mms", "w2v")}


def lag_of(m):
    d = []
    for v in M[m].values():
        _, dd = nearest(on_flux, v["t"])
        if abs(dd) < 0.06:
            d.append(-dd)  # model time minus onset time
    return float(np.median(d)), len(d)


LAG = {m: lag_of(m) for m in M}
for m in M:
    for v in M[m].values():
        v["tc"] = v["t"] - LAG[m][0]
        v["subs_c"] = {p: t - LAG[m][0] for p, t in v["subs"].items()}

# ------------------------------------------------------------------ choose word starts
SPELL_FIRST = {"AGI": "a", "NVDA": "e", "E": "e", "MLP,": "e", "RLHF": "a", "ChatGPT,": "c", "P(doom)": "p",
               "P(doom),": "p", "CDR": "s", "PTO,": "p", "GPU": "g", "One": "w", "'cause": "c", "“Just": "j"}


PART_NAMES = {"AGI": ["ay", "gee", "eye"], "ChatGPT,": ["chat", "gee", "pee", "tee"], "P(doom)": ["pee", "doom"],
              "P(doom),": ["pee", "doom"], "NVDA": ["en", "vee", "dee", "ay"], "MLP,": ["em", "el", "pee"],
              "CDR": ["see", "dee", "are"], "PTO,": ["pee", "tee", "oh"], "GPU": ["gee", "pee", "you"],
              "RLHF": ["are", "el", "aitch", "ef"], "Post-Chinchilla,": ["post", "chinchilla"],
              "super-dense": ["super", "dense"], "pre-training": ["pre", "training"], "self-upgrade": ["self", "upgrade"]}


def spoken_first(dw):
    if dw in SPELL_FIRST:
        return SPELL_FIRST[dw]
    c = [ch for ch in dw.lower() if ch.isalpha()]
    return c[0] if c else ""


words_out = {}
stats_rows = []
for li, L in enumerate(lines_src):
    for wi, (dw, _) in enumerate(L["words"]):
        a, b = M["mms"][(li, wi)], M["w2v"][(li, wi)]
        dis = abs(a["tc"] - b["tc"])
        if dis <= 0.08:
            cand, src = 0.5 * (a["tc"] + b["tc"]), "both"
        else:
            _, da = nearest(on_flux, a["tc"])
            _, db = nearest(on_flux, b["tc"])
            if abs(da) <= 0.04 and abs(db) > 0.04:
                cand, src = a["tc"], "mms"
            else:
                cand, src = b["tc"], "w2v"
        t = cand
        o, d = nearest(on_flux, cand)
        snapped = None
        first = spoken_first(dw)
        pk = (li, wi - 1) if wi > 0 else ((li - 1, len(lines_src[li - 1]["words"]) - 1) if li > 0 else None)
        prev_t = words_out[pk]["t"] if pk else 0.0
        prev_e = (M["w2v"][pk]["e"] - LAG["w2v"][0]) if pk else 0.0  # end of the previous word's last CTC character
        lo = max(prev_t + 0.12, prev_e, cand - 0.25)
        look = [(tt, ss) for tt, ss in zip(on_flux, on_flux_s) if lo <= tt <= cand + 0.03 and ss >= 0.2]
        if first and first in "aeiouymnlrw" and look:
            # vowel- or sonorant-initial word: CTC fires mid-vowel, up to ~200 ms after the voicing onset -> take the
            # latest vocal onset between the end of the previous word's CTC characters and this word's CTC start
            t, snapped = max(look)[0], "vowel-lookback"
        elif abs(d) <= 0.05:
            t, snapped = o, "flux"
        else:
            o2, d2 = nearest(on_other, cand)
            if abs(d2) <= 0.035:
                t, snapped = o2, "energy/pitch"
        spread = (a["spread"] + b["spread"]) / 2 if src == "both" else (a if src == "mms" else b)["spread"]
        if snapped == "vowel-lookback":
            # both models fire after the onset that was chosen, so their disagreement matters less than usual
            u = max(0.03, spread / 2, min(dis / 2, 0.06))
        elif dis <= 0.08:
            u = max(0.015, dis / 2, abs(t - cand), spread / 2)
        else:
            u = max(dis, 0.015)
        key = f"{li}:{wi}"
        how = src + (">" + snapped if snapped else "")
        t_auto, u_auto = t, u
        if key in OVR:
            ov = OVR[key]
            t, u, how = ov["t"], ov.get("u", 0.03), "manual"
        words_out[(li, wi)] = {"w": dw, "t": t, "u": u, "how": how, "t_auto": t_auto, "u_auto": u_auto, "mms": a["tc"], "w2v": b["tc"], "dis": dis,
                               "subs_w2v": b["subs_c"], "subs_mms": a["subs_c"]}
        stats_rows.append((li, wi, a["tc"], b["tc"], t, how))

# monotonic order inside and across lines (>= 40 ms apart)
flat = [(k, words_out[k]) for k in sorted(words_out)]
for i in range(1, len(flat)):
    if flat[i][1]["t"] < flat[i - 1][1]["t"] + 0.04:
        flat[i][1]["t"] = flat[i - 1][1]["t"] + 0.04
        flat[i][1]["how"] += ",monotonic"
        flat[i][1]["u"] = max(flat[i][1]["u"], 0.08)

# ------------------------------------------------------------------ word ends from vocal energy
r5, t5 = F["r5"], F["t5"]
REF = float(np.percentile(r5, 95))


DT5 = float(t5[1] - t5[0])
r5s = np.convolve(r5, np.ones(3) / 3, mode="same")


def dip_between(t_word, a, b, min_depth=10.0, min_w=0.09):
    """deepest level dip of the vocal stem in (a, b) relative to the word's own level (75th percentile of the 250 ms
    after its start). Returns (gap_start, gap_end, depth_db) when the dip is >= min_depth dB deep and >= min_w wide at
    half depth (plosive closures inside words are shorter), else None."""
    i, j = int(np.searchsorted(t5, a)), int(np.searchsorted(t5, b))
    if j - i < 4:
        return None
    seg = r5s[i:j]
    k = int(np.argmin(seg))
    mn = seg[k]
    w0 = int(np.searchsorted(t5, t_word))
    lvl = float(np.percentile(r5s[w0:w0 + int(0.25 / DT5)], 75))
    if lvl - mn < min_depth:
        return None
    thr = mn + 0.5 * (lvl - mn)
    s0, s1 = k, k
    while s0 > 0 and seg[s0 - 1] < thr:
        s0 -= 1
    while s1 < len(seg) - 1 and seg[s1 + 1] < thr:
        s1 += 1
    if (s1 - s0 + 1) * DT5 < min_w:
        return None
    return float(t5[i + s0]), float(t5[i + s1]), float(lvl - mn)


def sustain_end(t_from, t_limit):
    """end of a held note: first 100 ms run >= 14 dB under the note's own peak, searched until t_limit."""
    i = int(np.searchsorted(t5, t_from))
    j = int(np.searchsorted(t5, t_limit))
    if j <= i + 2:
        return t_limit
    pk = r5[i:min(j, i + int(0.3 / (t5[1] - t5[0])))].max()
    n = int(0.1 / (t5[1] - t5[0]))
    run = 0
    for k in range(i, j):
        run = run + 1 if r5[k] < pk - 14 else 0
        if run >= n:
            return float(t5[k - n + 1])
    return float(t_limit)


flat = [(k, words_out[k]) for k in sorted(words_out)]
for i, (k, w) in enumerate(flat):
    nxt = flat[i + 1][1]["t"] if i + 1 < len(flat) else min(DUR, w["t"] + 3)
    last_in_line = i + 1 >= len(flat) or flat[i + 1][0][0] != k[0]
    key_end = f"{k[0]}:end"
    w["gap_db"] = 0.0
    if not last_in_line:
        g = dip_between(w["t"], w["t"] + 0.1, nxt)
        w["e"] = g[0] if g else nxt
        if g:
            w["gap_db"] = g[2]
    else:
        g = dip_between(w["t"], w["t"] + 0.1, nxt)
        if g:
            w["gap_db"] = g[2]
        w["e"] = sustain_end(w["t"] + 0.12, min(nxt - 0.02, w["t"] + 4.0))
        if key_end in OVR:
            w["e"] = OVR[key_end]["t"]

# ------------------------------------------------------------------ lines
lines = []
for li, L in enumerate(lines_src):
    ws = [words_out[(li, wi)] for wi in range(len(L["words"]))]
    wl = []
    for wi, w in enumerate(ws):
        row = {"w": w["w"], "t": round(w["t"], 3), "e": round(w["e"], 3), "u": int(round(w["u"] * 1000)),
               "_gap": w.get("gap_db", 0.0)}
        # sub-parts of spelled words (acronyms, P(doom), hyphenated words): wav2vec2 letter-group times
        subs = w["subs_w2v"] if len(w["subs_w2v"]) > 1 else {}
        key = f"{li}:{wi}"
        if key in OVR and "parts" in OVR[key]:
            row["parts"] = OVR[key]["parts"]
        elif subs:
            names = PART_NAMES.get(w["w"], [])
            parts = [round(w["t"], 3)]
            for j, (p, v) in enumerate(sorted(subs.items())):
                if j == 0:
                    continue
                v2 = v
                nm = names[j] if j < len(names) else "x"
                lk = [tt for tt, ss in zip(on_flux, on_flux_s) if parts[-1] + 0.1 <= tt <= v + 0.03 and v - tt <= 0.12 and ss >= 0.2]
                o, d = nearest(on_flux, v)
                if nm[0] in "aeiou" and lk:
                    v2 = max(lk)  # vowel-initial letter name (ay, ee, el, em, en, are, aitch, ef, eye, oh)
                elif abs(d) <= 0.05 and o > parts[-1] + 0.08:
                    v2 = o
                parts.append(round(max(v2, parts[-1] + 0.06), 3))
            row["parts"] = parts
        if "parts" in row and row["parts"][-1] > row["e"] - 0.1:
            # the end was cut at a gap between letter names / word parts: search again after the last part
            if wi + 1 < len(ws):
                nxt_t = ws[wi + 1]["t"]
            elif li + 1 < len(lines_src):
                nxt_t = words_out[(li + 1, 0)]["t"]
            else:
                nxt_t = DUR
            g = dip_between(row["parts"][-1], row["parts"][-1] + 0.1, nxt_t)
            if wi + 1 < len(ws):
                row["e"] = round(g[0] if g else nxt_t, 3)
            else:
                row["e"] = round(min(nxt_t - 0.02, sustain_end(row["parts"][-1] + 0.12, nxt_t - 0.02)), 3)
        row["how"] = w["how"]
        if w["how"] == "manual":
            row["auto"] = round(w["t_auto"], 3)
        wl.append(row)
    start, end = wl[0]["t"], wl[-1]["e"]
    u_max = max(r["u"] for r in wl)
    ln = {"i": li, "text": L["text"], "start": start, "end": end, "words": wl,
          "sub_start": L["start"], "sub_end": L["end"], "d_start": round(start - L["start"], 3),
          "d_end": round(end - L["end"], 3), "u_max_ms": u_max, "flag": u_max > 80,
          "flag_words": [r["w"] for r in wl if r["u"] > 80],
          "auto_u_max_ms": int(round(max(words_out[(li, wi)]["u_auto"] for wi in range(len(ws))) * 1000)),
          **grid_pos(start)}
    sx = STRUCT.get("sung_as", {}).get(str(li))
    if sx:
        ln["sung_as"] = sx
    lines.append(ln)

# ------------------------------------------------------------------ phrases
# level "line": each sung line, split at internal punctuation where the voice pauses or holds (>= 0.1 s gap or a
# word held >= 1 s), plus the extra (non-lyric) vocals. level "couplet": the musical phrases the lines pair into
# (structure.json), usually 2 bars ending on a downbeat. breath_before = silence before the phrase in the vocal stem.
downbeats = beats[::4]


def landing(ws):
    """downbeat that the phrase resolves onto: nearest downbeat to any word/part start in its last 40 %, within 120 ms"""
    ts = sorted([w["t"] for w in ws] + [p for w in ws for p in w.get("parts", [])])
    a0, a1 = ts[0], max(ts)
    land = None
    for t in ts:
        if t >= a0 + 0.6 * (a1 - a0) - 1e-6:
            d = downbeats[np.argmin(np.abs(downbeats - t))]
            if abs(d - t) < 0.12:
                land = round(float(d), 4)
    return land


phrases = []
for L in lines:
    cur = []
    ws = L["words"]
    for j, w in enumerate(ws):
        cur.append(w)
        last = j == len(ws) - 1
        end_ch = w["w"].rstrip("”\"")[-1:]
        split = (not last) and (end_ch in "?!." or (end_ch == "," and (ws[j + 1]["t"] - w["e"] >= 0.1 or ws[j + 1]["t"] - w["t"] >= 1.0)))
        if last or split:
            phrases.append({"level": "line", "kind": "lyric", "start": cur[0]["t"], "end": cur[-1]["e"],
                            "text": " ".join(x["w"] for x in cur), "lines": [L["i"]], "lands_on_downbeat": landing(cur)})
            cur = []
for x in STRUCT["extra_vocals"]:
    if x.get("phrase", True):
        phrases.append({"level": "line", "kind": x["kind"], "start": x["t"], "end": x["e"], "text": x["text"],
                        "lines": [], "lands_on_downbeat": None})
phrases.sort(key=lambda p: p["start"])
prev_end = 0.0
for p in phrases:
    g = dip_between(p["start"], max(prev_end - 0.05, 0.0), p["start"] + 0.01, min_depth=12.0, min_w=0.08) if p["start"] > prev_end - 0.05 else None
    p["breath_before"] = round(max(0.0, p["start"] - prev_end), 3) if g else 0.0
    prev_end = max(prev_end, p["end"])
for grp in STRUCT["couplets"]:
    ws = [w for L in lines if L["i"] in grp for w in L["words"]]
    phrases.append({"level": "couplet", "kind": "lyric", "start": ws[0]["t"], "end": ws[-1]["e"],
                    "text": " / ".join(L["text"] for L in lines if L["i"] in grp), "lines": grp,
                    "lands_on_downbeat": landing([w for L in lines if L["i"] == grp[-1] for w in L["words"]])})
phrases.sort(key=lambda p: (p["level"] != "couplet", p["start"]))
phrases.sort(key=lambda p: (0 if p["level"] == "line" else 1, p["start"]))
for i, p in enumerate(phrases):
    p["i"] = i
    p["start"], p["end"] = round(p["start"], 3), round(p["end"], 3)
    p.update({k: v for k, v in grid_pos(p["start"]).items() if k != "off_ms"})

for L in lines:
    for w in L["words"]:
        w.pop("_gap", None)

# ------------------------------------------------------------------ sections
PB = G["per_beat"]
sections = []
for s in STRUCT["sections"]:
    t_a = 0.0 if s["bar0"] == 0 else bar_start(s["bar0"])
    t_b = DUR if s["bar1"] is None else bar_start(s["bar1"])
    rows = [r for r in PB if t_a - 1e-6 <= r["t"] < t_b - 1e-6]
    en = float(np.mean([r["energy"] for r in rows])) if rows else 0.0
    onsets_in = lambda L: [w["t"] for w in L["words"]] + [p for w in L["words"] for p in w.get("parts", [])]
    last_bar = max(r["bar"] for r in rows if r["t"] < t_b - 0.1) if rows else 1
    sections.append({"name": s["name"], "t0": round(t_a, 4), "t1": round(t_b, 4),
                     "bars": [s["bar0"] if s["bar0"] else 1, last_bar],
                     "n_bars": round((t_b - max(t_a, T0)) / (4 * T), 2), "energy": round(en, 3),
                     "mix_db": round(float(np.mean([r["mix_db"] for r in rows])), 1) if rows else None,
                     "lines": [L["i"] for L in lines if any(t_a - 0.06 <= t < t_b - 0.06 for t in onsets_in(L))],
                     "description": s["description"]})

# ------------------------------------------------------------------ events
events = []
for e in STRUCT["events"]:
    ev = dict(e)
    if "bar" in e:
        ev["t"] = round(bar_start(e["bar"]) + (e.get("beat", 1) - 1) * T, 4)
    if "bar_end" in e:
        ev["t_end"] = round(bar_start(e["bar_end"]) + (e.get("beat_end", 1) - 1) * T, 4)
    for k in ("bar", "beat", "bar_end", "beat_end"):
        ev.pop(k, None)
    events.append(ev)
events.sort(key=lambda e: e["t"])

# ------------------------------------------------------------------ hits (kick/snare with strengths; hats compact)
hits = {"kick": [], "snare": [], "hat": []}
for h in G["hits"]:
    hits[h["type"]].append([h["t"], h["s"]])

per_beat = [{"t": r["t"], "bar": r["bar"], "beat": r["beat"], "energy": r["energy"], "mix_db": r["mix_db"],
             "drums_db": r["drums_db"], "bass_db": r["bass_db"], "other_db": r["other_db"], "vocal_db": r["vocal_db"],
             "kick": r["kick"], "snare": r["snare"]} for r in PB]

# ------------------------------------------------------------------ verification statistics
def coinc(ts, arr, win):
    ts = np.asarray(ts)
    return float(np.mean([abs(nearest(arr, t)[1]) <= win for t in ts]))


raw_m = [M["mms"][k]["tc"] for k in sorted(M["mms"])]
raw_w = [M["w2v"][k]["tc"] for k in sorted(M["w2v"])]
fin = [words_out[k]["t"] for k in sorted(words_out)]
dis = np.abs(np.array(raw_m) - np.array(raw_w)) * 1000
allu = np.array([words_out[k]["u"] for k in words_out]) * 1000
on_all = np.sort(np.concatenate([on_flux, on_en]))
eighth = T / 2
q8 = [abs(((t - T0) / eighth) - np.round((t - T0) / eighth)) * eighth * 1000 for t in fin]
stats = {
    "lags_ms": {m: {"lag": round(LAG[m][0] * 1000, 1), "n": LAG[m][1]} for m in LAG},
    "method_disagreement_ms": {"median": round(float(np.median(dis)), 1), "p75": round(float(np.percentile(dis, 75)), 1),
                               "p90": round(float(np.percentile(dis, 90)), 1),
                               "frac_le_50": round(float(np.mean(dis <= 50)), 3), "frac_le_80": round(float(np.mean(dis <= 80)), 3),
                               "frac_gt_200": round(float(np.mean(dis > 200)), 3)},
    "onset_coincidence": {name: {"flux_30ms": round(coinc(ts, on_flux, 0.03), 3), "flux_50ms": round(coinc(ts, on_flux, 0.05), 3),
                                 "any_50ms": round(coinc(ts, on_all, 0.05), 3)}
                          for name, ts in (("mms", raw_m), ("w2v", raw_w), ("final", fin))},
    "chance_onset_coincidence_50ms": round(float(min(1.0, len(on_flux) / (DUR - 2) * 0.1)), 3),
    "final_offset_from_8th_grid_ms": {"median": round(float(np.median(q8)), 1), "frac_le_40": round(float(np.mean(np.array(q8) <= 40)), 3),
                                      "chance_median": round(eighth * 1000 / 4, 1)},
    "word_u_ms": {"median": round(float(np.median(allu)), 1), "p90": round(float(np.percentile(allu, 90)), 1),
                  "n_gt_80": int(np.sum(allu > 80))},
    "how": {h: sum(1 for k in words_out if words_out[k]["how"].split(",")[0] == h) for h in sorted({w["how"].split(",")[0] for w in words_out.values()})},
    "n_words": len(words_out), "n_manual": sum(1 for w in words_out.values() if w["how"] == "manual"),
    "flagged_lines": [L["i"] for L in lines if L["flag"]],
    "auto_flagged_lines": [L["i"] for L in lines if L["auto_u_max_ms"] > 80],
    "manual_changed_ms": {"n_moved_gt_30ms": int(sum(1 for w in words_out.values() if w["how"] == "manual" and abs(w["t"] - w["t_auto"]) > 0.03)),
                          "max": int(round(max(abs(w["t"] - w["t_auto"]) for w in words_out.values()) * 1000))},
}

# third method: Whisper large-v3 word times (coarse, cross-attention DTW) matched by spelling within +-1.5 s
import re as _re
wh_words = [(w["w"], w["t"]) for sg in WH["segments"] for w in sg["words"]]
norm = lambda x: _re.sub(r"[^a-z]", "", x.lower())
offs = []
for k in sorted(words_out):
    fw = norm(words_out[k]["w"])
    cands = [t for ww, t in wh_words if norm(ww) == fw and abs(t - words_out[k]["t"]) <= 1.5]
    if fw and cands:
        offs.append(min(cands, key=lambda t: abs(t - words_out[k]["t"])) - words_out[k]["t"])
offs = np.array(offs)
med = float(np.median(offs))
stats["whisper_check"] = {"n_matched": int(len(offs)), "median_offset_ms": round(med * 1000),
                          "mad_ms": round(float(np.median(np.abs(offs - med))) * 1000),
                          "frac_within_150ms_of_median": round(float(np.mean(np.abs(offs - med) <= 0.15)), 3),
                          "note": "Whisper word starts are systematically early and coarse; a small spread around a constant offset is the check"}

# section starts vs the grid: the nearest drum attack / vocal onset / crash to each section downbeat
kick_t = np.array([h[0] for h in hits["kick"]])
sn_t = np.array([h[0] for h in hits["snare"]])
cr_t = np.array([c["t"] for c in G["crashes"]])
dbc = []
for sct in sections[1:]:
    row = {"section": sct["name"], "t0": sct["t0"]}
    for nm, arr, win in (("kick", kick_t, 0.05), ("snare", sn_t, 0.05), ("crash", cr_t, 0.05), ("vocal_onset", on_flux, 0.06)):
        o, d = nearest(arr, sct["t0"])
        row[nm + "_ms"] = round(d * 1000, 1) if abs(d) <= win else None
    bi = int(round((sct["t0"] - T0) / T))
    if 1 <= bi < len(PB):
        row["level_step_db"] = round(PB[bi]["mix_db"] - PB[bi - 1]["mix_db"], 1)
        row["drums_step_db"] = round(PB[bi]["drums_db"] - PB[bi - 1]["drums_db"], 1)
    dbc.append(row)
stats["section_downbeat_check"] = dbc

song = {
    "_about": "Timing backbone for the Claude Pop film. All times are seconds from the first sample of the gapless "
              "decode of pdoom.mp3 (ffmpeg honours the LAME header: 1105 priming samples at 48 kHz = 23.0 ms are "
              "skipped). Generated by claudepop/analysis/tools/build_song.py; method and verification in REPORT.md.",
    "song": "I'm Upping My P(doom)", "audio": "pdoomvideo/assets/pdoom.mp3 (48 kHz stereo MP3, untouched)",
    "duration": round(DUR, 4), "first_sound": STRUCT["first_sound"], "bpm": BPM, "beat_period": round(T, 6),
    "meter": "4/4", "t0": T0,
    "t0_note": "t0 = the attack start (10 % of rise, unfiltered drum stem) of the kick on clap-free beats. Beat n is at "
               "t0 + n*60/132; bar b (1-based) starts at t0 + (b-1)*4*60/132. Claps on beats 2/4 are flammed and start "
               "up to 19 ms before the beat; the kick's low-frequency peak is ~23 ms after it.",
    "half_time": {"bpm": 66.0, "period": round(2 * T, 6),
                  "grid": "t0 + n*2*60/132 = beats 1 and 3 of every bar (the kick-only beats; the claps sit on 2 and 4 "
                          "between them). Cutting on this grid gives a half-time edit (one cut per 0.909 s), which suits "
                          "verse 1, the breakdown and the bridge; the choruses and the outro carry a full 132 four-on-the-floor.",
                  "units_s": {"beat": round(T, 6), "half_time_beat": round(2 * T, 6), "bar": round(4 * T, 6),
                              "two_bars": round(8 * T, 6), "eight_bars": round(32 * T, 6), "sixteenth": round(T / 4, 6)}},
    "beats": [round(float(b), 4) for b in beats],
    "downbeats": [round(float(b), 4) for b in beats[::4]],
    "phase_estimates": G["phase_estimates"], "tempo_check": G["tempo_check"],
    "bar_phase_votes": G["bar_phase_votes"], "onset_offsets_ms_from_grid": G["onset_offsets_ms_from_grid"],
    "sections": sections,
    "events": events,
    "lines": lines,
    "extra_vocals": STRUCT["extra_vocals"],
    "phrases": phrases,
    "hits": {"_format": "[t, strength 0..1]; t = attack start", **hits},
    "per_beat": per_beat,
    "verification": stats,
}


def dump(o, f):
    """compact JSON with one array element per line for big lists (diff-friendly, still valid JSON)."""
    s = json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    f.write(s)


with open(f"{ROOT}/analysis/song.json", "w") as f:
    txt = json.dumps(song, ensure_ascii=False, indent=1)
    # collapse short inner arrays / word objects onto one line
    import re
    txt = re.sub(r"\[\s+([-\d.,\s]+?)\s+\]", lambda m: "[" + ",".join(x.strip() for x in m.group(1).split(",")) + "]", txt)
    txt = re.sub(r"\{\s+(\"w\"[^{}\[\]]*?(\[[^\[\]]*\])?[^{}\[\]]*?)\s+\}",
                 lambda m: "{" + " ".join(l.strip() for l in m.group(1).splitlines()) + "}", txt)
    f.write(txt)
json.dump(stats, open(f"{W}/build_stats.json", "w"), indent=1)

# ------------------------------------------------------------------ click-track auditions
voc, sr = sf.read(f"{ROOT}/out/audio/stems/htdemucs/pdoom_44k/vocals.wav", always_2d=True)


def click(freq, dur=0.03, amp=0.5):
    n = int(dur * sr)
    tt = np.arange(n) / sr
    return amp * np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 120)


out = voc.copy() * 0.8
for L in lines:
    for j, w in enumerate(L["words"]):
        c = click(2400 if j == 0 else 1500, amp=0.45 if j == 0 else 0.3)
        i = int(w["t"] * sr)
        n = min(len(c), len(out) - i)
        out[i:i + n] += c[:n, None]
sf.write(f"{ROOT}/out/audio/click_words.wav", np.clip(out, -1, 1), sr, subtype="PCM_16")
mix, _ = sf.read(f"{ROOT}/out/audio/pdoom_44k.wav", always_2d=True)
out = mix.copy() * 0.7
for n, b in enumerate(beats):
    c = click(2000 if n % 4 == 0 else 1200, amp=0.4 if n % 4 == 0 else 0.22)
    i = int(b * sr)
    k = min(len(c), len(out) - i)
    out[i:i + k] += c[:k, None]
sf.write(f"{ROOT}/out/audio/click_beats.wav", np.clip(out, -1, 1), sr, subtype="PCM_16")

print(json.dumps(stats, indent=1))
for L in lines:
    fl = " FLAG " + ",".join(L["flag_words"]) if L["flag"] else ""
    print(f"{L['i']:2d} {L['start']:7.3f}-{L['end']:7.3f} u{L['u_max_ms']:4d}{fl} | " +
          " ".join(f"{w['w']}@{w['t']:.2f}" for w in L["words"]))
