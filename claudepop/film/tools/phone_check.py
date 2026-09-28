#!/usr/bin/env python3
"""Phone review sheets (BIBLE 3 phone gate, 6.6): frames downscaled to 390 x 219 (the X feed's 16:9 width in points) and
laid out for reading at phone size: the hook (0-10 s), the three QUESTIONs, the cards and the empty clip.

    claudepop/out/venv/bin/python claudepop/film/tools/phone_check.py out/film/frames/540 [--zones] [--cols 4]
        -> out/film/sheets/phone_<res>.jpg (+ phone_<res>_zones.jpg with --zones: the 6.6 safe area and player-overlay
           zones as hairlines, to check that no critical type sits in them)
Missing frames are skipped (render them first: node film/render.mjs --res 540).
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CP = os.path.abspath(os.path.join(HERE, '..', '..'))
PW, PH = 390, 219
FPS = 24


def picks(doc):
    S = {s['id']: s for s in doc['shots']}
    at = lambda sid, sec: (round((S[sid]['t0'] + sec) * FPS), sid)
    last = lambda sid: (S[sid]['frames'][1] - 1, sid)
    hook = [(f, 'hook') for f in (0, 6, 18, 27, 40, 49, 60, 68, 90, 114, 126, 130, 141, 150, 170, 192, 203, 215, 235)]
    q = [(round((37.05 + 0.9) * FPS), 'Q1 S14'), (last('S14')[0] - 8, 'Q1 hold'), (round((72.27 + 1.3) * FPS), 'Q2 S25'),
         (last('S25')[0] - 8, 'Q2 hold'), (round((122.73 + 1.1) * FPS), 'Q3 S46'), (last('S46')[0] - 8, 'Q3 hold')]
    cards = [(round(23.7 * FPS), 'S07 stop'), (round(24.2 * FPS), 'S08 card'), (last('S17c')[0], 'S17c card'),
             (round(60.1 * FPS), 'S18 stop'), (round(60.4 * FPS), 'S19 card'), (round(96.3 * FPS), 'S32 card'),
             (round(97.2 * FPS), 'S33 card'), (round(110.9 * FPS), 'S39 strip'), (round(112.6 * FPS), 'S40 card'),
             (round(125.5 * FPS), 'S47 card'), (round(125.9 * FPS), 'S48 card'), (round(133.2 * FPS), 'S52 card'),
             (round(137.9 * FPS), 'S52 card 2'), (round(139.5 * FPS), 'S53 freeze'), (round(140.8 * FPS), 'S54 show?'),
             (round(155.0 * FPS), 'S57 proof'), (last('S57')[0], 'S57 end')]
    clip = [(round(153.0 * FPS), 'S56 clip'), (round(153.65 * FPS), 'S56 closing'), (last('S56')[0], 'S56 7:9')]
    return [('THE HOOK 0-10 s', hook), ('QUESTIONS', q), ('CARDS', cards), ('THE EMPTY CLIP', clip)]


def font(size):
    for p in [os.path.join(CP, 'out/fonts/IBMPlexMono-Medium.ttf'), os.path.join(CP, 'fonts/IBMPlexMono-Medium.ttf'),
              '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf']:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def zones(im):
    """BIBLE 6.6 in phone px (1 design px = 390/1920): safe x 72-1848, y 60-1020; overlays bottom-left 480x120,
    bottom-right 360x120."""
    d = ImageDraw.Draw(im)
    k = PW / 1920
    d.rectangle([72 * k, 60 * k, 1848 * k, 1020 * k], outline=(200, 200, 200))
    d.rectangle([0, (1080 - 120) * k, 480 * k, PH - 1], outline=(120, 120, 120))
    d.rectangle([(1920 - 360) * k, (1080 - 120) * k, PW - 1, PH - 1], outline=(120, 120, 120))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('frames')
    ap.add_argument('--cols', type=int, default=4)
    ap.add_argument('--zones', action='store_true')
    a = ap.parse_args()
    doc = json.load(open(os.path.join(CP, 'shots.json')))
    res = os.path.basename(os.path.normpath(a.frames))
    groups = picks(doc)
    gap, lab, head = 12, 30, 34
    rows = sum((len(g) + a.cols - 1) // a.cols for _, g in groups)
    W = a.cols * PW + (a.cols + 1) * gap
    H = 60 + len(groups) * head + rows * (PH + lab + gap)
    for with_zones in ([False, True] if a.zones else [False]):
        sheet = Image.new('RGB', (W, H), (18, 18, 18))
        d = ImageDraw.Draw(sheet)
        d.text((gap, 14), f'PHONE CHECK · 390 x 219 · frames {res}' + (' · safe zones' if with_zones else ''), fill=(240, 238, 232), font=font(20))
        y = 60
        missing = 0
        for title, items in groups:
            d.text((gap, y + 6), title, fill=(160, 158, 152), font=font(16))
            y += head
            for i, (f, why) in enumerate(items):
                x = gap + (i % a.cols) * (PW + gap)
                if i and i % a.cols == 0:
                    y += PH + lab + gap
                p = os.path.join(a.frames, f'{f:05d}.jpg')
                if not os.path.exists(p):
                    missing += 1
                    d.rectangle([x, y, x + PW, y + PH], outline=(80, 80, 80))
                    d.text((x + 8, y + 8), 'missing', fill=(120, 120, 120), font=font(14))
                else:
                    im = Image.open(p).convert('RGB').resize((PW, PH), Image.LANCZOS)
                    sheet.paste(zones(im) if with_zones else im, (x, y))
                sid = next(s['id'] for s in doc['shots'] if s['frames'][0] <= f < s['frames'][1])
                d.text((x, y + PH + 7), f'F{f} {f / FPS:6.2f}s {sid}  {why}', fill=(200, 198, 192), font=font(13))
            y += PH + lab + gap
        out = os.path.join(CP, 'out', 'film', 'sheets', f'phone_{res}{"_zones" if with_zones else ""}.jpg')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sheet.save(out, quality=92)
        print(out, f'({missing} missing)' if missing else '')
    return 0


if __name__ == '__main__':
    sys.exit(main())
