"""Forced alignment of the lyrics against the separated vocal stem with PocketSphinx (bundled en-us model).

Lines are grouped into phrases separated by subtitle gaps; each group is aligned as one utterance
with a padded window. Output: JSON with per-token and per-phone times (seconds, song time).

usage: python3 align_ps.py vocals.wav lyrics.js out.json [pad]
"""
import sys, json
import numpy as np
import soundfile as sf
import librosa
from pocketsphinx import Decoder
from lyrics_lex import LEX, load_lines

voc_path, ly_path, out_path = sys.argv[1:4]
PAD = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
GAP = 0.9

v, sr = sf.read(voc_path, always_2d=True)
v = librosa.resample(v.mean(1), orig_sr=sr, target_sr=16000)
v = v / (np.abs(v).max() + 1e-9) * 0.9
pcm = (v * 32767).astype(np.int16)

lines = load_lines(ly_path)
groups, cur = [], [0]
for i in range(1, len(lines)):
    if lines[i]["start"] - lines[i - 1]["end"] >= GAP:
        groups.append(cur)
        cur = []
    cur.append(i)
groups.append(cur)

dec = Decoder(samprate=16000, loglevel="ERROR", bestpath=False)
for w, p in LEX.items():
    if dec.lookup_word(w) is None:
        dec.add_word(w, p, False)

res = []
for gi, g in enumerate(groups):
    a = lines[g[0]]["start"] - PAD
    b = lines[g[-1]]["end"] + PAD
    if gi > 0:
        a = max(a, lines[groups[gi - 1][-1]]["end"] + 0.05)
    if gi + 1 < len(groups):
        b = min(b, lines[groups[gi + 1][0]]["start"] - 0.05)
    a = max(0.0, a)
    toks, owners = [], []
    for li in g:
        for wi, (dw, sp) in enumerate(lines[li]["words"]):
            for s in sp:
                toks.append(s)
                owners.append((li, wi))
    buf = pcm[int(a * 16000):int(b * 16000)].tobytes()
    dec.set_align_text(" ".join(toks))
    dec.start_utt()
    dec.process_raw(buf, full_utt=True)
    dec.end_utt()
    segs = [(s.word, s.start_frame, s.end_frame, s.ascore) for s in dec.seg()]
    # phone level second pass
    dec.set_alignment()
    dec.start_utt()
    dec.process_raw(buf, full_utt=True)
    dec.end_utt()
    al = dec.get_alignment()
    words = []
    if al is not None:
        for w in al:
            phones = [(p.name, a + p.start / 100.0, a + (p.start + p.duration) / 100.0) for p in w]
            words.append({"w": w.name, "t": a + w.start / 100.0, "e": a + (w.start + w.duration) / 100.0, "phones": phones})
    # attach owners to non-silence words in order
    k = 0
    out_words = []
    for w in words:
        if w["w"] in ("<sil>", "<s>", "</s>", "[NOISE]", "<sil>"):
            continue
        base = w["w"].split("(")[0]
        if k < len(toks) and base == toks[k]:
            w["line"], w["word"] = owners[k]
            k += 1
        out_words.append(w)
    ok = k == len(toks)
    hyp = dec.hyp()
    res.append({"group": gi, "lines": g, "win": [a, b], "ok": ok, "score": hyp.score if hyp else None, "tokens": out_words,
                "segs": [(w, a + s / 100.0, a + (e + 1) / 100.0, sc) for w, s, e, sc in segs]})
    print(f"group {gi:2d} lines {g[0]:2d}-{g[-1]:2d} win {a:6.2f}-{b:6.2f} ok={ok} n={len(out_words)}/{len(toks)}", flush=True)

json.dump(res, open(out_path, "w"), indent=0)
