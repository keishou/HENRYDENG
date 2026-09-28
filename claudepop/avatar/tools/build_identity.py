#!/usr/bin/env python3
"""Identity reference pack for the generative models of the next session: claudepop/out/avatar/identity/.

  face_clean_1024.png     the rectified passport photo with the page (texture, AAA stamps) replaced by a clean
                          neutral background through a soft person matte (hair strands kept by difference matting)
  head_shoulders_4x5.png  head-and-shoulders crop, 4:5, from the clean photo (native resolution, no upscaling)
  face_crop_square.png    square face + hair crop, native resolution
  face_aligned_512.png    FFHQ-style aligned square crop (eyes level, face centred), 512 px
  arcface_aligned_112.png ArcFace-template crop used by the similarity scorer (written by face_similarity.py)
  matte.png               soft person matte (face, hair, neck, clothes), 8-bit
  face_hair_matte.png     soft face + hair matte (no neck / clothes)
  cutout_rgba.png         clean photo with the person matte as alpha
All of it is subject data: it stays in the gitignored claudepop/out/.
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from avlib import IDENT, WORK, load_rgb, save_rgb
from bake_texture import push_pull

BG = np.array([0.93, 0.93, 0.925])   # neutral light-grey passport background


def guided(I, p, r=8, eps=1e-3):
    return cv2.ximgproc.guidedFilter(I.astype(np.float32), p.astype(np.float32), r, eps)


def main():
    IDENT.mkdir(parents=True, exist_ok=True)
    photo = load_rgb(WORK / "photo_rect.png")
    A = np.load(WORK / "analysis.npz")
    cls, conf, lm = A["cls"], A["conf"].astype(np.float32), A["lm"].astype(np.float64)
    H, W = cls.shape
    L = photo.mean(-1)
    # ---- person matte: soft segmentation for skin/clothes, difference matte for hair
    body = conf[..., 2] + conf[..., 3] + conf[..., 4]
    hair_c = conf[..., 1]
    person_seg = np.clip(body + hair_c, 0, 1)
    # keep the component that contains the face (drops the stamps)
    core = (person_seg > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(core, 8)
    core = (lab == lab[int(lm[1, 1]), int(lm[1, 0])]).astype(np.uint8)
    near = cv2.dilate(core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))).astype(bool)
    # clean plate of the page (background) and hair colour
    bgm = (person_seg < 0.05) & ~near
    B = push_pull(photo.astype(np.float32), bgm.astype(np.float32))
    hair = (cls == 1) & core.astype(bool)
    Fh = push_pull(photo.astype(np.float32), (hair & (L < 0.3)).astype(np.float32))
    a_hair = np.clip((B.mean(-1) - L) / np.maximum(B.mean(-1) - Fh.mean(-1), 0.15), 0, 1)
    hair_zone = cv2.dilate(hair.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))).astype(bool)
    # the matte of the person: guided-filtered segmentation, plus hair strands in the hair zone
    a_seg = np.clip(guided(photo, np.where(near, person_seg, 0), 6, 1e-3), 0, 1)
    # crisp but anti-aliased edge for skin / clothes (a wide soft edge would drag the page colour in as a halo)
    a_seg = np.clip((a_seg - 0.35) / 0.35, 0, 1)
    a_seg = cv2.GaussianBlur(a_seg.astype(np.float32), (0, 0), 0.8)
    a = np.where(hair_zone & ~(cls == 3) & ~(cls == 2) & ~(cls == 4), np.maximum(a_hair, a_seg * (cls != 0)), a_seg)
    a[~near] = 0
    a = np.clip(a, 0, 1)
    # stamp lines that cross the matte (thin dark lines on light background near the shoulders): the difference
    # matte only runs in the hair zone, so the stamps never enter; the shoulder edge comes from the segmentation
    # ---- foreground colour (unmix the old background at soft edges) and composite on a clean background
    Fg = photo.copy()
    edge = (a > 0.02) & (a < 0.98)
    Fg[edge] = np.clip((photo[edge] - (1 - a[edge, None]) * B[edge]) / np.maximum(a[edge, None], 0.15), 0, 1)
    solid = (a > 0.9).astype(np.float32)
    Ffill = push_pull(Fg.astype(np.float32), solid)
    Fg = np.where((a < 0.5)[..., None], Ffill, Fg)
    clean = a[..., None] * Fg + (1 - a[..., None]) * BG[None, None]
    save_rgb(IDENT / "face_clean_1024.png", clean)
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(IDENT / "matte.png")
    Image.fromarray((np.dstack([clean, a]) * 255 + 0.5).astype(np.uint8), "RGBA").save(IDENT / "cutout_rgba.png")
    fh_seg = np.clip((conf[..., 1] + conf[..., 3] - 0.35) / 0.35, 0, 1)
    fh = a * np.clip(np.maximum(fh_seg, a_hair * hair_zone * (cls != 2) * (cls != 4)), 0, 1)
    fh = np.clip(guided(photo, fh, 4, 1e-3), 0, 1)
    fh[fh > 0.9] = 1.0
    Image.fromarray((fh * 255 + 0.5).astype(np.uint8)).save(IDENT / "face_hair_matte.png")

    # ---- crops (native resolution; the clean photo is 1024 px)
    eye_l, eye_r = lm[[33, 133, 160, 158, 144, 153]].mean(0)[:2], lm[[263, 362, 387, 385, 373, 380]].mean(0)[:2]
    mouth_l, mouth_r = lm[61, :2], lm[291, :2]
    eye_c = 0.5 * (eye_l + eye_r)
    mouth_c = 0.5 * (mouth_l + mouth_r)
    # head-and-shoulders 4:5 inside the photo (nothing below the photo's lower edge is known, so no padding there)
    hs_h = H
    hs_w = int(round(hs_h * 4 / 5))
    x0 = int(np.clip(round(eye_c[0] - hs_w / 2), 0, W - hs_w))
    save_rgb(IDENT / "head_shoulders_4x5.png", clean[:, x0:x0 + hs_w])
    # square face + hair crop centred between the eyes and mouth
    cy = 0.5 * (eye_c[1] + mouth_c[1]) - 0.25 * (lm[152, 1] - lm[10, 1])
    side = int(round(1.9 * (lm[152, 1] - lm[10, 1])))
    x0, y0 = int(round(eye_c[0] - side / 2)), int(round(cy - side / 2))
    canvas = np.tile(BG[None, None], (side, side, 1))
    sx0, sy0 = max(x0, 0), max(y0, 0)
    sx1, sy1 = min(x0 + side, W), min(y0 + side, H)
    canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = clean[sy0:sy1, sx0:sx1]
    save_rgb(IDENT / "face_crop_square.png", canvas)
    # FFHQ alignment (Karras et al. 2019, ffhq-dataset/align_face): eyes + mouth corners -> oriented square
    e2e = eye_r - eye_l
    e2m = mouth_c - eye_c
    x = e2e - np.array([-e2m[1], e2m[0]])
    x /= np.hypot(*x)
    x *= max(np.hypot(*e2e) * 2.0, np.hypot(*e2m) * 1.8)
    y = np.array([-x[1], x[0]])
    c = eye_c + e2m * 0.1
    quad = np.array([c - x - y, c - x + y, c + x + y, c + x - y], np.float32)
    dst = np.array([[0, 0], [0, 512], [512, 512], [512, 0]], np.float32)
    Mq = cv2.getPerspectiveTransform(quad, dst)
    big = cv2.copyMakeBorder((clean * 255).astype(np.uint8), 0, 0, 0, 0, cv2.BORDER_CONSTANT)
    ffhq = cv2.warpPerspective(big, Mq, (512, 512), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT,
                               borderValue=tuple(int(v * 255) for v in BG))
    Image.fromarray(ffhq).save(IDENT / "face_aligned_512.png")
    # the native photo region covered by the aligned crop is ~2*|x| px: note whether 512 is an upscale
    print(f"ffhq crop side in photo px: {2 * np.hypot(*x):.0f} -> 512")
    print("identity pack written to", IDENT)


if __name__ == "__main__":
    main()
