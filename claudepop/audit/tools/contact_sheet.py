# Contact sheet: grid of frames with time + lyric/shot labels. Usage: contact_sheet.py <frames_dir> <out.png> [cols] [thumb_w] [title]
import sys, glob, os, re, json
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
tw = int(sys.argv[4]) if len(sys.argv) > 4 else 480
title = sys.argv[5] if len(sys.argv) > 5 else 'pdoomvideo (previous attempt): audit frames'
th = tw * 9 // 16
# lyric lookup from the previous video's lyrics.js
LY = []
js = open('/home/user/johnheibel/pdoomvideo/src/lyrics.js', encoding='utf-8').read()
for m in re.finditer(r'\[([\d.]+),\s*([\d.]+),\s*"((?:[^"\\]|\\.)*)"\]', js): LY.append((float(m[1]), float(m[2]), m[3]))
CH = [(0, 1.5, 'curtain'), (1.5, 23, 'lab'), (23, 38.5, 'chorus 1'), (38.5, 59, 'takeoff'), (59, 73, 'chorus 2'), (73, 95.4, 'obsolete'),
      (95.4, 109.4, 'chorus 3'), (109.4, 123.5, 'scale'), (123.5, 140.5, 'chorus 4'), (140.5, 157, 'finale')]
files = sorted(glob.glob(os.path.join(src, 't*.png')), key=lambda f: float(os.path.basename(f)[1:-4].replace('_', '.')))
rows = (len(files) + cols - 1) // cols
pad, lab, head = 8, 44, 56
W = cols * (tw + pad) + pad; H = head + rows * (th + lab + pad) + pad
sheet = Image.new('RGB', (W, H), (27, 24, 32)); d = ImageDraw.Draw(sheet)
def font(sz, bold=False):
    for p in ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
d.text((pad + 4, 14), title, fill=(243, 235, 220), font=font(24, True))
for i, f in enumerate(files):
    t = float(os.path.basename(f)[1:-4].replace('_', '.'))
    im = Image.open(f).convert('RGB').resize((tw, th), Image.LANCZOS)
    x = pad + (i % cols) * (tw + pad); y = head + (i // cols) * (th + lab + pad)
    sheet.paste(im, (x, y))
    ly = next((l[2] for l in LY if l[0] <= t < l[1]), '(no lyric)')
    ch = next((c[2] for c in CH if c[0] <= t < c[1]), '')
    d.text((x + 2, y + th + 4), f'{t:6.2f}s  [{ch}]', fill=(232, 170, 56), font=font(15, True))
    d.text((x + 2, y + th + 23), ly[:62], fill=(220, 214, 200), font=font(14))
sheet.save(out); print(out, sheet.size)
