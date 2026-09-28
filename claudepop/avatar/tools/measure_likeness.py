#!/usr/bin/env python3
"""Likeness check: MediaPipe Face Landmarker on the three.js render from the photo's camera vs on the photo.

    python3 measure_likeness.py RENDER.png [--out check/likeness.json]

Reports the mean distance over the 468 face landmarks as a percentage of the photo's outer-eye-corner distance
(33-263), both raw (the render uses the photo camera, so no alignment) and after a 2D similarity alignment, plus
per-region values.  Writes an overlay (photo | render | 50 % blend with both landmark sets).
Numbers go to claudepop/out (gitignored) only.
"""
from __future__ import annotations

import argparse
import json

import cv2
import numpy as np

from avlib import CHECK, WORK, load_rgb
from fit_face import Detector, mp_sets, similarity_2d

OUTER = (33, 263)


def nme(a, b):
    iod = np.linalg.norm(b[OUTER[0], :2] - b[OUTER[1], :2])
    return float(100 * np.linalg.norm(a[:468, :2] - b[:468, :2], axis=1).mean() / iod)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("--out", default=str(CHECK / "likeness.json"))
    a = ap.parse_args()
    det = Detector()
    photo = load_rgb(WORK / "photo_rect.png")
    ren = load_rgb(a.render)
    if ren.shape[:2] != photo.shape[:2]:
        ren = cv2.resize(ren, (photo.shape[1], photo.shape[0]), interpolation=cv2.INTER_AREA)
    lp = det(photo)
    lr = det(ren)
    if lr is None:
        raise SystemExit("no face detected on the render")
    raw = nme(lr, lp)
    s, R, t = similarity_2d(lr[:468, :2], lp[:468, :2])
    lr_al = np.c_[(lr[:, :2] @ R.T) * s + t, lr[:, 2]]
    aligned = nme(lr_al, lp)
    sets = mp_sets()
    iod = np.linalg.norm(lp[OUTER[0], :2] - lp[OUTER[1], :2])
    reg = {k: float(100 * np.linalg.norm(lr_al[idx, :2] - lp[idx, :2], axis=1).mean() / iod) for k, idx in sets.items() if max(idx) < 468}
    res = {"nme_raw_pct_outer_eye": raw, "nme_aligned_pct_outer_eye": aligned, "regions_aligned_pct": reg,
           "similarity_scale": float(s), "similarity_rot_deg": float(np.degrees(np.arctan2(R[1, 0], R[0, 0])))}
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    # overlay
    P8 = (photo * 255).astype(np.uint8)[..., ::-1].copy()
    R8 = (ren * 255).astype(np.uint8)[..., ::-1].copy()
    B8 = cv2.addWeighted(P8, 0.5, R8, 0.5, 0)
    for (x, y), (xr, yr) in zip(lp[:468, :2], lr[:468, :2]):
        cv2.circle(B8, (int(x), int(y)), 1, (0, 255, 0), -1)
        cv2.circle(B8, (int(xr), int(yr)), 1, (0, 0, 255), -1)
    row = np.hstack([P8, R8, B8])
    cv2.imwrite(str(CHECK / "likeness_side_by_side.jpg"), cv2.resize(row, (row.shape[1] * 2 // 3, row.shape[0] * 2 // 3)))


if __name__ == "__main__":
    main()
