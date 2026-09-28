"""Whole-song CTC forced alignment of the lyric text on the vocal-stem emissions from emissions.py.

One Viterbi pass over the entire song per model and per sub-frame shift, so the order of lines is enforced globally
and no window edges can cut a word. Between consecutive lines (and before the first / after the last) sits a
'garbage' state (like the MMS star token) that absorbs sung material that is not in the text: ad-libs, repeats,
backing vocals. Its per-frame score is  max over non-blank labels of log p  +  STAR_PEN, so a frame that matches the
expected character still prefers the character. Each line's states may only occupy frames within +-MARGIN seconds
of its subtitle interval in lyrics.js (a loose prior that prevents a line from landing on a repeat elsewhere).

Output: out/work/analysis/align_<model>.json  - per word: start/end per shift (song seconds, frame centre), plus
        per-garbage-region greedy transcriptions.

usage: python3 align_fa.py <claudepop_dir> <lyrics.js> <model: mms|w2v> [nshift=4] [star_pen=-3] [margin=1.5]
"""
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from lyrics_lex import load_lines

ROOT, LY, MODEL = sys.argv[1:4]
NSHIFT = int(sys.argv[4]) if len(sys.argv) > 4 else 4
STAR_PEN = float(sys.argv[5]) if len(sys.argv) > 5 else -3.0
MARGIN = float(sys.argv[6]) if len(sys.argv) > 6 else 1.5
W = f"{ROOT}/out/work/analysis"
labels = json.load(open(f"{W}/emis_{MODEL}_labels.json"))
BLANK = labels.index("-")
FR = 0.02

# spoken spelling of display words for character CTC models
SPELL = {
    "AGI": "ay gee eye", "ChatGPT,": "chat gee pee tee", "P(doom)": "pee doom", "P(doom),": "pee doom",
    "FOOM": "foom", "NVDA": "en vee dee ay", "E": "ee", "MLP,": "em el pee", "CDR": "see dee are",
    "PTO,": "pee tee oh", "GPU": "gee pee you", "RLHF": "are el aitch ef", "Post-Chinchilla,": "post chinchilla",
    "super-dense": "super dense", "pre-training": "pre training", "self-upgrade": "self upgrade", "'cause": "cause",
}


def spoken(w):
    if w in SPELL:
        return SPELL[w]
    s = w.replace("’", "'").replace("“", "").replace("”", "").lower()
    s = "".join(ch for ch in s if ch.isalpha() or ch == "'" or ch == " ")
    return s.strip("'")


if MODEL == "w2v":
    lab_id = {c: i for i, c in enumerate(labels)}
    to_id = lambda ch: lab_id[ch.upper()] if ch != " " else lab_id["|"]
else:
    lab_id = {c: i for i, c in enumerate(labels)}
    to_id = lambda ch: lab_id.get(ch)

lines = load_lines(LY)
STAR = -1
units = []  # (label id or STAR, line, word, sub-word letter group index)
units.append((STAR, -1, -1, -1))
for li, L in enumerate(lines):
    for wi, (dw, _) in enumerate(L["words"]):
        sp = spoken(dw)
        parts = sp.split(" ")
        for pi, part in enumerate(parts):
            if MODEL == "w2v" and (wi > 0 or pi > 0):
                units.append((lab_id["|"], li, wi, pi))
            for ch in part:
                i = to_id(ch)
                if i is not None:
                    units.append((i, li, wi, pi))
    units.append((STAR, li, -1, -1))

S = 2 * len(units) + 1
lab = np.full(S, BLANK)
own_line = np.full(S, -2)  # line index owning the state (-1: garbage)
for k, (u, li, wi, pi) in enumerate(units):
    lab[2 * k + 1] = u
    own_line[2 * k + 1] = li if u != STAR else -1
# blanks take the line of their neighbours (garbage-adjacent blanks stay free)
for s in range(0, S, 2):
    lft = own_line[s - 1] if s > 0 else -1
    rgt = own_line[s + 1] if s + 1 < S else -1
    own_line[s] = lft if lft == rgt else -1
is_star = lab == STAR
can_skip = np.zeros(S, bool)  # transition s-2 -> s
for s in range(3, S, 2):
    can_skip[s] = not (lab[s] == lab[s - 2] and lab[s] != STAR)


def frame_ranges(n_frames, t_first):
    lo = np.zeros(S, int)
    hi = np.full(S, n_frames - 1)
    for s in range(S):
        li = own_line[s]
        if li >= 0:
            a = lines[li]["start"] - MARGIN
            b = lines[li]["end"] + MARGIN
            lo[s] = max(0, int((a - t_first) / FR))
            hi[s] = min(n_frames - 1, int((b - t_first) / FR))
    # garbage states between line i and i+1 may sit anywhere between the two lines' margins
    for k, (u, li, wi, pi) in enumerate(units):
        if u == STAR:
            s = 2 * k + 1
            a = lines[li]["end"] - MARGIN if li >= 0 else 0.0
            b = lines[li + 1]["start"] + MARGIN if li + 1 < len(lines) else 1e9
            lo[s] = max(0, int((a - t_first) / FR))
            hi[s] = min(n_frames - 1, int((b - t_first) / FR))
    return lo, hi


def viterbi(lp, t_first):
    Tn = lp.shape[0]
    star = np.max(np.delete(lp, BLANK, axis=1), axis=1) + STAR_PEN
    em = np.where(is_star[None, :], star[:, None], lp[:, np.where(is_star, BLANK, lab)])
    lo, hi = frame_ranges(Tn, t_first)
    NEG = -1e18
    allowed = (np.arange(Tn)[:, None] >= lo[None, :]) & (np.arange(Tn)[:, None] <= hi[None, :])
    em = np.where(allowed, em, NEG)
    bp = np.zeros((Tn, S), np.int8)
    prev = np.full(S, NEG)
    prev[0] = em[0, 0]
    prev[1] = em[0, 1]
    for t in range(1, Tn):
        c1 = np.concatenate([[NEG], prev[:-1]])
        c2 = np.where(can_skip, np.concatenate([[NEG, NEG], prev[:-2]]), NEG)
        st = np.stack([prev, c1, c2])
        k = st.argmax(0)
        prev = st[k, np.arange(S)] + em[t]
        bp[t] = k
    s = S - 1 if prev[S - 1] >= prev[S - 2] else S - 2
    score = float(prev[s])
    path = np.zeros(Tn, np.int32)
    for t in range(Tn - 1, -1, -1):
        path[t] = s
        s -= bp[t, s]
    return path, score


res = {"model": MODEL, "star_pen": STAR_PEN, "margin": MARGIN, "nshift": NSHIFT, "labels": labels, "shifts": []}
for k in range(NSHIFT):
    lp = np.load(f"{W}/emis_{MODEL}_s{k}.npy").astype(np.float32)
    meta = json.load(open(f"{W}/emis_{MODEL}_s{k}.json"))
    t_first = meta["first_frame_start_s"] + 0.0125  # frame centre (400-sample receptive field, 320 hop)
    path, score = viterbi(lp, t_first)
    words = {}
    groups = {}
    garbage = []
    cur = None
    for t, s in enumerate(path):
        tt = t_first + t * FR
        if s % 2 == 1:
            u, li, wi, pi = units[s // 2]
            if u == STAR:
                if cur is None or cur["unit"] != s // 2:
                    cur = {"unit": s // 2, "after_line": li, "t": tt, "e": tt + FR, "greedy": []}
                    garbage.append(cur)
                cur["e"] = tt + FR
                g = int(np.argmax(lp[t]))
                cur["greedy"].append(g)
                continue
            if labels[u] == "|":
                continue
            key = f"{li}:{wi}"
            w = words.setdefault(key, {"t": tt, "e": tt + FR})
            w["e"] = tt + FR
            gk = f"{li}:{wi}:{pi}"
            gg = groups.setdefault(gk, {"t": tt, "e": tt + FR})
            gg["e"] = tt + FR
    for g in garbage:
        seq, last = [], None
        for i in g.pop("greedy"):
            if i != last and i != BLANK:
                seq.append(labels[i])
            last = i
        g["heard"] = "".join(seq).replace("|", " ").lower()
        g["t"], g["e"] = round(g["t"], 3), round(g["e"], 3)
    res["shifts"].append({"t_first": t_first, "score": score, "words": words, "letter_groups": groups,
                          "garbage": [g for g in garbage if g["e"] - g["t"] > 0.1]})
    print(f"{MODEL} shift {k} score {score:.1f} words {len(words)} garbage>{0.1}s {len(res['shifts'][-1]['garbage'])}", flush=True)

json.dump(res, open(f"{W}/align_{MODEL}.json", "w"))
