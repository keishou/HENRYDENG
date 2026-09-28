#!/usr/bin/env python3
"""Palette rule on rendered frames or sheets (BIBLE 4.2): every pixel with HSV saturation > 0.15 and value > 0.10 must have
a hue within +-12 deg of VOICE (#D97757, 14.8 deg); S38 also allows the cyanotype bands (pale yellow-green and blue).

    claudepop/out/venv/bin/python claudepop/film/tools/hue_check.py out/film/frames/540 [more dirs / images]
        [--every 1] [--max-frac 0.0002] [--width 480] [--json out.json] [--shots S01,S04]

Frames named <frame:05d>.jpg map to shots through shots.json (for S38's allowance and the per-shot report); other images
(contact sheets) get the strict rule. A frame fails when the fraction of off-palette pixels exceeds --max-frac (JPEG chroma
noise at colour edges stays far below the default 0.02 %). Images are box-downscaled to --width first. A pixel also needs a
chroma (max - min of RGB) above --min-chroma (0.04 = 10 levels) to count: near the value threshold, JPEG chroma noise of
2-5 levels on the dark greys reads as saturation > 0.15 but is not visible colour. Exit 1 on failure.
"""
import argparse
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CP = os.path.abspath(os.path.join(HERE, '..', '..'))
VOICE_HUE, TOL = 14.8, 12.0
CYAN_BANDS = [(55.0, 100.0), (190.0, 235.0)]          # S38: yellow-green start of the ramp, CYANOTYPE #1E3F66 (212 deg)


def hsv(a):
    a = a.astype(np.float32) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    h = np.zeros_like(mx)
    m = d > 1e-6
    rr = m & (mx == r)
    gg = m & (mx == g) & ~rr
    bb = m & ~rr & ~gg
    h[rr] = ((g - b)[rr] / d[rr]) % 6
    h[gg] = (b - r)[gg] / d[gg] + 2
    h[bb] = (r - g)[bb] / d[bb] + 4
    return h * 60.0, s, mx


def check(path, allow_cyan, width, min_chroma=0.04):
    im = Image.open(path).convert('RGB')
    if im.width > width:
        im = im.resize((width, max(1, round(im.height * width / im.width))), Image.BOX)
    h, s, v = hsv(np.asarray(im))
    live = (s > 0.15) & (v > 0.10) & (s * v > min_chroma)
    dh = np.abs((h - VOICE_HUE + 180) % 360 - 180)
    bad = live & (dh > TOL)
    if allow_cyan:
        for lo, hi in CYAN_BANDS:
            bad &= ~((h >= lo) & (h <= hi))
    n = bad.size
    hues = h[bad]
    return {'bad_frac': float(bad.sum()) / n, 'voice_frac': float((live & (dh <= TOL)).sum()) / n,
            'bad_hue_median': float(np.median(hues)) if hues.size else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('paths', nargs='+')
    ap.add_argument('--every', type=int, default=1)
    ap.add_argument('--max-frac', type=float, default=0.0002)
    ap.add_argument('--width', type=int, default=480)
    ap.add_argument('--min-chroma', type=float, default=0.04)
    ap.add_argument('--shots', default=None)
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    doc = json.load(open(os.path.join(CP, 'shots.json')))
    want = set(a.shots.split(',')) if a.shots else None
    shot_of = lambda f: next((s['id'] for s in doc['shots'] if s['frames'][0] <= f < s['frames'][1]), None)
    files = []
    for p in a.paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, '*.jpg')) + glob.glob(os.path.join(p, '*.png')))
        else:
            files.append(p)
    rows, fails = [], []
    for i, f in enumerate(files):
        m = re.fullmatch(r'(\d{5})\.(jpg|png)', os.path.basename(f))
        fr = int(m.group(1)) if m else None
        sid = shot_of(fr) if fr is not None else os.path.splitext(os.path.basename(f))[0]
        if fr is not None and a.every > 1 and fr % a.every:
            continue
        if want and sid not in want:
            continue
        r = check(f, sid == 'S38', a.width, a.min_chroma)
        r.update(file=os.path.relpath(f, CP), frame=fr, shot=sid, ok=r['bad_frac'] <= a.max_frac)
        rows.append(r)
        if not r['ok']:
            fails.append(r)
    by = {}
    for r in rows:
        b = by.setdefault(r['shot'], {'n': 0, 'fail': 0, 'worst': 0.0, 'voice_max': 0.0})
        b['n'] += 1
        b['fail'] += not r['ok']
        b['worst'] = max(b['worst'], r['bad_frac'])
        b['voice_max'] = max(b['voice_max'], r['voice_frac'])
    for sid, b in by.items():
        flag = 'FAIL' if b['fail'] else 'ok  '
        print(f"{flag} {sid:<8} {b['n']:>5} images  worst off-palette {b['worst'] * 100:.4f} %  max VOICE {b['voice_max'] * 100:.3f} %")
    for r in fails[:20]:
        print(f"  fail {r['file']}  {r['bad_frac'] * 100:.4f} % off-palette, median hue {r['bad_hue_median']:.0f} deg")
    print(f"hue check: {len(rows)} images, {len(fails)} failing (threshold {a.max_frac * 100:.3f} % of pixels)")
    if a.json:
        json.dump({'rows': rows, 'by_shot': by}, open(a.json, 'w'), indent=1)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
