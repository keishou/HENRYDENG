#!/usr/bin/env python3
# hall_recap.py - lane E tool (node-free, run with the project venv): caches the S54 recap stills (BIBLE 4.8 HALL
# capture system: before each of the first 12 captures, the sheet flashes an image the film already showed, in film
# order). Writes out/film/data/recap/<shot>.jpg (7:9, 398 x 512, a centred crop of the picture window) and
# out/film/data/recap/recap.json ({ shots: [{ id, frame, source, slate }] }) from the rendered frames in
# out/film/frames/<res>/ (the highest resolution that has the frame). Re-run it whenever those shots are re-rendered;
# S54 reads the files at init (a missing file is drawn as a blank flash).
#
#   out/venv/bin/python film/src/sets/hall_recap.py [--res 1080,720,540]
#
# A recap whose shot is still a slate (no src/scenes/<id>.js) is flagged "slate": true (a placeholder until built).
import json, os, sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
OUT = os.path.join(ROOT, 'out/film/data/recap')
# (shot, frame offset rule): the frame that carries the shot's image (film order, BIBLE 4.8)
RECAPS = [('S01', 'last'), ('S05', 'mid'), ('S06', 21.36), ('S08', 'mid'), ('S10', 'last'), ('S13', 'last'), ('S17b', 'mid'),
          ('S21', 63.849), ('S24', 'last'), ('S34', 'mid'), ('S38', 'last'), ('S46', 'mid')]
WIN = {'7:9': 840, '1:1': 1080, '4:3': 1440, '16:9': 1920}


def main():
    res_list = [r for r in (sys.argv[sys.argv.index('--res') + 1] if '--res' in sys.argv else '1080,720,540').split(',')]
    doc = json.load(open(os.path.join(ROOT, 'shots.json')))
    shots = {s['id']: s for s in doc['shots']}
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for sid, rule in RECAPS:
        s = shots[sid]; f0, f1 = s['frames']
        f = f1 - 1 if rule == 'last' else (f0 + f1 - 1) // 2 if rule == 'mid' else int(round(rule * 24))
        src = next((os.path.join(ROOT, 'out/film/frames', r, f'{f:05d}.jpg') for r in res_list
                    if os.path.exists(os.path.join(ROOT, 'out/film/frames', r, f'{f:05d}.jpg'))), None)
        slate = not os.path.exists(os.path.join(ROOT, 'film/src/scenes', sid + '.js'))
        if not src:
            rows.append({'id': sid, 'frame': f, 'source': None, 'slate': slate}); continue
        im = Image.open(src).convert('RGB'); W, H = im.size; k = H / 1080
        shape = (s.get('window') or '16:9').split('|')[0].strip()
        ww = WIN.get(shape, 1920) * k
        cw = min(ww, H * 7 / 9); x0 = (W - cw) / 2
        crop = im.crop((round(x0), 0, round(x0 + cw), H)).resize((398, 512), Image.LANCZOS)
        crop.save(os.path.join(OUT, sid + '.jpg'), quality=92)
        rows.append({'id': sid, 'frame': f, 'source': os.path.relpath(src, ROOT), 'slate': slate})
    json.dump({'shots': rows}, open(os.path.join(OUT, 'recap.json'), 'w'), indent=1)
    for r in rows: print(r)


if __name__ == '__main__':
    main()
