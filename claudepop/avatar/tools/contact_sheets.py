#!/usr/bin/env python3
"""Compose the verification sheets from a render_glb.mjs output folder (default check/final).

    python3 contact_sheets.py [DIR]
Writes DIR/../sheet_turn.jpg (front / 3-4 / profile / back), sheet_head.jpg (head 0/35/90/180 + photo-camera view),
sheet_photo_vs_render.jpg (rectified photo | photo-camera render | 50 % blend), sheet_pose.jpg (skinning test).
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

from avlib import CHECK, WORK


def strip(files, h, out, pad=8, bg=(24, 24, 24)):
    ims = [Image.open(f).convert("RGB") for f in files if Path(f).exists()]
    ims = [im.resize((int(im.width * h / im.height), h)) for im in ims]
    W = sum(im.width for im in ims) + pad * (len(ims) - 1)
    sheet = Image.new("RGB", (W, h), bg)
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0))
        x += im.width + pad
    sheet.save(out, quality=90)


def main():
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else CHECK / "final"
    strip([d / f"turn_{a}.png" for a in (0, 35, 90, 180)], 900, CHECK / "sheet_turn.jpg")
    strip([d / f"head_{a}.png" for a in (0, 35, 90, 180)] + [d / "photo_cam.png"], 640, CHECK / "sheet_head.jpg")
    strip([d / "pose_0.png", d / "pose_35.png", d / "pose_head.png"], 800, CHECK / "sheet_pose.jpg")
    ph = Image.open(WORK / "photo_rect.png").convert("RGB")
    rc = Image.open(d / "photo_cam.png").convert("RGB").resize(ph.size)
    bl = Image.blend(ph, rc, 0.5)
    sheet = Image.new("RGB", (ph.width * 3 + 16, ph.height), (24, 24, 24))
    for i, im in enumerate((ph, rc, bl)):
        sheet.paste(im, (i * (ph.width + 8), 0))
    sheet.resize((sheet.width // 2, sheet.height // 2)).save(CHECK / "sheet_photo_vs_render.jpg", quality=90)
    print("sheets written to", CHECK)


if __name__ == "__main__":
    main()
