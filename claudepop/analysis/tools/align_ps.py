"""Forced alignment of the lyrics against the separated vocal stem with PocketSphinx (bundled en-us model).

Lines are grouped into phrases separated by subtitle gaps; each group is aligned as one utterance
with a padded window. If a group fails, it is retried with wider beams, then line by line.
Output: JSON list of groups with per-token and per-phone times (seconds, song time).

usage: python3 align_ps.py vocals.wav lyrics.js out.json [pad] [gap]
"""
import sys, json
import numpy as np
import soundfile as sf
import librosa
from pocketsphinx import Decoder
from lyrics_lex import LEX, load_lines

voc_path, ly_path, out_path = sys.argv[1:4]
PAD = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
GAP = float(sys.argv[5]) if len(sys.argv) > 5 else 0.9

v, sr = sf.read(voc_path, always_2d=True)
v = librosa.resample(v.mean(1), orig_sr=sr, target_sr=16000)
v = v / (np.abs(v).max() + 1e-9) * 0.9
pcm = (v * 32767).astype(np.int16)

lines = load_lines(ly_path)


def make_dec(wide):
    kw = dict(samprate=16000, loglevel="FATAL", bestpath=False)
    if wide:
        kw.update(beam=1e-120, wbeam=1e-100, pbeam=1e-120)
    d = Decoder(**kw)
    for w, p in LEX.items():
        if d.lookup_word(w) is None:
            d.add_word(w, p, False)
    return d


DEC = [make_dec(False), make_dec(True)]


def run(a, b, li_list):
    toks, owners = [], []
    for li in li_list:
        for wi, (dw, sp) in enumerate(lines[li]["words"]):
            for s in sp:
                toks.append(s)
                owners.append((li, wi))
    buf = pcm[int(a * 16000):int(b * 16000)].tobytes()
    for dec in DEC:
      try:
        dec.set_align_text(" ".join(toks))
        dec.start_utt()
        dec.process_raw(buf, full_utt=True)
        dec.end_utt()
        sg = dec.seg()
        if sg is None:
            continue
        segs = [(s.word, s.start_frame, s.end_frame, s.ascore) for s in sg]
        dec.set_alignment()
        dec.start_utt()
        dec.process_raw(buf, full_utt=True)
        dec.end_utt()
        al = dec.get_alignment()
        if al is None:
            continue
        words = []
        for w in al:
            phones = [(p.name, a + p.start / 100.0, a + (p.start + p.duration) / 100.0) for p in w]
            words.append({"w": w.name, "t": a + w.start / 100.0, "e": a + (w.start + w.duration) / 100.0, "phones": phones})
        k, out = 0, []
        for w in words:
            if w["w"].startswith("<") or w["w"].startswith("["):
                continue
            base = w["w"].split("(")[0]
            if k < len(toks) and base == toks[k]:
                w["line"], w["word"] = owners[k]
                k += 1
            out.append(w)
        if k == len(toks):
            return {"win": [a, b], "lines": li_list, "wide": dec is DEC[1], "score": float(sum(x[3] for x in segs)), "tokens": out}
      except RuntimeError as e:
        print("   runtime error", e, flush=True)
    return None


groups, cur = [], [0]
for i in range(1, len(lines)):
    if lines[i]["start"] - lines[i - 1]["end"] >= GAP:
        groups.append(cur)
        cur = []
    cur.append(i)
groups.append(cur)

res = []
for gi, g in enumerate(groups):
    a = lines[g[0]]["start"] - PAD
    b = lines[g[-1]]["end"] + PAD
    if gi > 0:
        a = max(a, lines[groups[gi - 1][-1]]["end"] + 0.05)
    if gi + 1 < len(groups):
        b = min(b, lines[groups[gi + 1][0]]["start"] - 0.05)
    a = max(0.0, a)
    r = run(a, b, g)
    if r is not None:
        res.append(r)
        print(f"group {gi:2d} lines {g[0]:2d}-{g[-1]:2d} win {a:6.2f}-{b:6.2f} OK wide={r['wide']}", flush=True)
        continue
    print(f"group {gi:2d} lines {g[0]:2d}-{g[-1]:2d} FAILED as a group -> per line", flush=True)
    for li in g:
        la = max(a, lines[li]["start"] - 0.45)
        lb = min(b, lines[li]["end"] + 0.45)
        r = run(la, lb, [li])
        if r is None:
            print(f"   line {li} FAILED", flush=True)
            res.append({"win": [la, lb], "lines": [li], "failed": True, "tokens": []})
        else:
            print(f"   line {li:2d} win {la:6.2f}-{lb:6.2f} OK wide={r['wide']}", flush=True)
            res.append(r)

json.dump(res, open(out_path, "w"))
