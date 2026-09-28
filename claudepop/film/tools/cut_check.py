#!/usr/bin/env python3
"""Frame-accurate cut check on rendered frames (BIBLE 9.8.4), part 3 (part 1: render.mjs checks every rendered frame's
shot id against shots.json; part 2: the cut-pair sheets of sheets.mjs --cuts, looked at by eye).

    claudepop/out/venv/bin/python claudepop/film/tools/cut_check.py out/film/frames/540 [--json out.json]

For every cut (shots.json frames[0] of each shot after the first) it measures the frame-to-frame change (mean absolute
difference of 240-px-wide greyscale thumbnails) for the five pairs (f0-3, f0-2) .. (f0+1, f0+2) and requires a clear
change exactly at (f0-1, f0): at least 2x the median of the four neighbouring pairs and above 0.3 grey levels. A cut
rendered a frame early or late leaves (f0-1, f0) inside one shot, so it fails. Neighbouring changes are allowed (a
2-frame beat_hit tick, a flash or a word landing next to the cut are legitimate); the position of the largest change is
reported. Exit 1 on any cut without its change on frames[0].
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CP = os.path.abspath(os.path.join(HERE, '..', '..'))


def thumb(d, f):
    p = os.path.join(d, f'{f:05d}.jpg')
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert('L')
    return np.asarray(im.resize((240, round(240 * im.height / im.width)), Image.BOX), np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('frames')
    ap.add_argument('--json')
    a = ap.parse_args()
    doc = json.load(open(os.path.join(CP, 'shots.json')))
    rows, bad = [], 0
    for s in doc['shots'][1:]:
        f0 = s['frames'][0]
        ts = [thumb(a.frames, f) for f in range(f0 - 3, f0 + 3)]
        if any(t is None for t in ts):
            rows.append({'shot': s['id'], 'f0': f0, 'status': 'missing'})
            bad += 1
            continue
        d = [float(np.abs(ts[i + 1] - ts[i]).mean()) for i in range(5)]   # pairs (f0-3,f0-2) .. (f0+1,f0+2)
        others = float(np.median(d[:2] + d[3:]))
        ratio = d[2] / max(others, 1e-3)
        st = 'ok' if (d[2] >= 2 * others and d[2] > 0.3) else 'NO CHANGE AT f0'
        bad += st != 'ok'
        rows.append({'shot': s['id'], 'f0': f0, 'status': st, 'ratio': round(ratio, 1),
                     'largest_at': int(np.argmax(d)) - 2, 'diffs': [round(x, 3) for x in d]})
    for r in rows:
        if r['status'] != 'ok':
            print(f"  {r['shot']:<5} F{r['f0']:<5} {r['status']}  {r.get('ratio', '-')}x  {r.get('diffs', '')}")
    ok = sum(r['status'] == 'ok' for r in rows)
    rated = [r for r in rows if 'ratio' in r]
    lo = min(rated, key=lambda r: r['ratio']) if rated else None
    near = sum(1 for r in rated if r['largest_at'] != 0)
    print(f'cut check: {ok}/{len(rows)} cuts change the picture exactly on shots.json frames[0]'
          + (f' (weakest {lo["shot"]}: {lo["ratio"]}x its neighbours; {near} cuts have a larger change nearby, e.g. a hit tick)' if lo else '')
          + f'; {bad} failing')
    if a.json:
        json.dump(rows, open(a.json, 'w'), indent=1)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
