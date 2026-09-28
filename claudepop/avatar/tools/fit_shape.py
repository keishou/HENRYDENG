#!/usr/bin/env python3
"""Second fitting stage: silhouette features that the 478 face landmarks do not cover.

Measured on the photo (MediaPipe multiclass segmentation) and on a render of the MakeHuman skin from the same
camera, both normalised by the outer-eye-corner distance:
  * each ear: outer extent, top and bottom (face-skin pixels outside the landmark hull)
  * neck width just below the chin
Solved with MakeHuman's own modifiers (ear scale / vertical shift / protrusion per side, neck width) by a
damped Gauss-Newton on finite differences.  Input face_fit.npz, output face_fit.npz updated (v_fit) + shape_log.json.
"""
from __future__ import annotations

import json

import cv2
import numpy as np

from avlib import CHECK, MH, WORK, Cam, rasterize, save_rgb
from mhscene import skin_part

PARAMS = [  # (name, decr target, incr target)
    ("r-ear-scale", "targets/ears/r-ear-scale-decr.target", "targets/ears/r-ear-scale-incr.target"),
    ("r-ear-trans", "targets/ears/r-ear-trans-down.target", "targets/ears/r-ear-trans-up.target"),
    ("r-ear-wing", "targets/ears/r-ear-wing-decr.target", "targets/ears/r-ear-wing-incr.target"),
    ("l-ear-scale", "targets/ears/l-ear-scale-decr.target", "targets/ears/l-ear-scale-incr.target"),
    ("l-ear-trans", "targets/ears/l-ear-trans-down.target", "targets/ears/l-ear-trans-up.target"),
    ("l-ear-wing", "targets/ears/l-ear-wing-decr.target", "targets/ears/l-ear-wing-incr.target"),
    ("neck-width", "targets/neck/neck-scale-horiz-decr.target", "targets/neck/neck-scale-horiz-incr.target"),
    ("torso-width", "targets/torso/torso-scale-horiz-decr.target", "targets/torso/torso-scale-horiz-incr.target"),
    ("neck-length", "targets/neck/neck-scale-vert-decr.target", "targets/neck/neck-scale-vert-incr.target"),
]
CLOTH_ALLOWANCE = 0.08  # photo shoulder silhouette includes the knit top: ~4 mm per side, in outer-eye-distance units


def measure(skin, lm, ear_mask=None, sil=None):
    """skin: bool (H,W) skin mask (face+ears+neck), lm: (478,3) landmarks, ear_mask: optional explicit ear pixels
    (renders: the bald MakeHuman scalp would otherwise merge with the ears). Returns the feature vector."""
    H, W = skin.shape
    iod = np.linalg.norm(lm[33, :2] - lm[263, :2])
    cx = 0.5 * (lm[33, 0] + lm[263, 0])
    ey = 0.5 * (lm[33, 1] + lm[263, 1])
    hull = cv2.convexHull(lm[:468, :2].astype(np.float32)).astype(np.int32)
    hm = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(hm, hull, 1)
    hm = cv2.dilate(hm, np.ones((7, 7), np.uint8)).astype(bool)
    yy, xx = np.mgrid[0:H, 0:W]
    band = (yy > ey - 0.6 * iod) & (yy < lm[152, 1] - 0.1 * iod)
    ear = (skin if ear_mask is None else ear_mask) & ~hm & band
    feats = []
    for side in (-1, 1):  # image left (subject's right, MakeHuman r-), image right (l-)
        m = ear & ((xx - cx) * side > 0.5 * iod)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
        if n <= 1:
            feats += [np.nan] * 3
            continue
        k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
        ys, xs = np.nonzero(lab == k)
        feats += [np.abs(xs - cx).max() / iod, (ys.min() - ey) / iod, (ys.max() - ey) / iod]
    sil = skin if sil is None else sil
    for k in (0.10, 0.20):  # neck silhouette width below the chin (photo: skin + clothes, i.e. not hair/background)
        yn = int(lm[152, 1] + k * iod)
        row = sil[min(yn, H - 1)]
        c = int(cx)
        if not row[c]:
            feats.append(np.nan)
            continue
        l = c
        while l > 0 and row[l - 1]:
            l -= 1
        r = c
        while r < W - 1 and row[r + 1]:
            r += 1
        feats.append((r - l + 1) / iod)
    for k in (0.5, 0.65, 0.8):  # shoulder line (trapezius) width
        yn = int(lm[152, 1] + k * iod)
        if yn >= H:
            feats.append(np.nan)
            continue
        row = sil[yn]
        c = int(cx)
        l = c
        while l > 0 and row[l - 1]:
            l -= 1
        r = c
        while r < W - 1 and row[r + 1]:
            r += 1
        feats.append((r - l + 1) / iod if l > 0 and r < W - 1 else np.nan)
    for k in (-1.8, -1.4, 1.4, 1.8):  # shoulder line height (trapezius) beside the neck, below the chin
        x = int(cx + k * iod)
        col = sil[:, min(max(x, 0), W - 1)]
        ys = np.nonzero(col[int(lm[152, 1] - 0.5 * iod):])[0]
        feats.append((ys[0] + int(lm[152, 1] - 0.5 * iod) - lm[152, 1]) / iod if len(ys) else np.nan)
    return np.array(feats)


def main():
    F = np.load(WORK / "face_fit.npz")
    v_fit = F["v_fit_landmarks"] if "v_fit_landmarks" in F.files else F["v_fit"]
    cam = Cam.from_dict(json.loads(str(F["cam_face"] if "cam_face" in F.files else F["cam"])))
    s, R, t = float(F["sim_s"]), F["sim_R"], F["sim_t"]
    Tl, Bl = F["T"], F["B"]
    A = np.load(WORK / "analysis.npz")
    lm_p = A["lm"].astype(np.float64)
    cls = A["cls"]
    # photo landmarks mapped into the render frame
    tgt = np.c_[(lm_p[:, :2] @ R.T) * s + t, lm_p[:, 2] * s]
    # photo skin mask mapped into the render frame (warp by the similarity)
    M = np.c_[s * R, t]
    skin_p = cv2.warpAffine(((cls == 2) | (cls == 3)).astype(np.uint8), M, (cam.W, cam.H), flags=cv2.INTER_NEAREST).astype(bool)
    sil_p = cv2.warpAffine(((cls > 0) & (cls != 1)).astype(np.uint8), M, (cam.W, cam.H), flags=cv2.INTER_NEAREST).astype(bool)
    f_photo = measure(skin_p, tgt, sil=sil_p)
    f_photo[-7:-4] -= CLOTH_ALLOWANCE
    f_photo[-4:] += 0.5 * CLOTH_ALLOWANCE   # the knit adds ~4 mm on top of the shoulders
    print("photo features", np.round(f_photo, 3))

    mh = MH()
    base = mh.base()
    skin = skin_part(base)
    tris = skin.src_index[skin.tris]
    tg = {}
    for n, dn, up in PARAMS:
        tg[n] = (mh.target(dn), mh.target(up))

    def apply(x):
        v = v_fit.copy()
        for (n, _, _), w in zip(PARAMS, x):
            (i, d) = tg[n][1] if w > 0 else tg[n][0]
            v[i] += abs(w) * d
        return v

    # ear vertices = the part the ear-translation modifier moves rigidly (its blend ring is excluded)
    ear_v = np.zeros(len(base.v), bool)
    for n in ("r-ear-trans", "l-ear-trans"):
        i, d = tg[n][1]
        ear_v[i[np.linalg.norm(d, axis=1) > 0.1]] = True
    ear_tri = ear_v[tris].all(1)

    def head_cam(v):
        """The neck modifiers move the whole head: follow it with the camera so the face keeps its photo alignment."""
        d = ((v[Tl[:468]] * Bl[:468, :, None]).sum(1) - (v_fit[Tl[:468]] * Bl[:468, :, None]).sum(1)).mean(0) * 0.1
        return Cam(cam.R, cam.t - cam.R @ d, cam.f, cam.cx, cam.cy, cam.W, cam.H)

    def skin_mask(v, with_ears=False):
        p = head_cam(v).project(v * 0.1)
        ti, _, _ = rasterize(p[:, :2], tris, cam.W, cam.H, Z=p[:, 2])
        if with_ears:
            return ti >= 0, (ti >= 0) & ear_tri[np.maximum(ti, 0)]
        return ti >= 0

    # landmarks of the fitted render (ear/neck targets barely move the face)
    lm_r = F["lm_render"]

    def feats(x):
        sk, em = skin_mask(apply(x), True)
        return measure(sk, lm_r, em)

    x = np.zeros(len(PARAMS))
    f0 = feats(x)
    print("render features (before)", np.round(f0, 3))
    ok = ~np.isnan(f_photo) & ~np.isnan(f0)
    ok[[1, 4]] = False  # ear tops: hidden under the side hair in the photo
    log = {"photo": f_photo.tolist(), "before": f0.tolist(), "steps": []}
    for it in range(10):
        fx = feats(x)
        r = (fx - f_photo)[ok]
        J = np.zeros((ok.sum(), len(x)))
        h = 0.15
        for j in range(len(x)):
            xp = x.copy()
            xp[j] += h
            J[:, j] = ((feats(xp) - fx)[ok]) / h
        lam = 0.02
        dx = -np.linalg.solve(J.T @ J + lam * np.eye(len(x)), J.T @ r)
        x = np.clip(x + np.clip(dx, -0.5, 0.5), -1, 1)
        log["steps"].append({"x": x.tolist(), "rms_before_step": float(np.sqrt((r ** 2).mean()))})
        print(f"step {it}: rms {np.sqrt((r ** 2).mean()):.4f} x={np.round(x, 2)}")
    f1 = feats(x)
    print("render features (after)", np.round(f1, 3))
    log["after"] = f1.tolist()
    log["params"] = {n: float(w) for (n, _, _), w in zip(PARAMS, x)}
    v2 = apply(x)
    d = dict(F)
    d["cam_face"] = json.dumps(cam.as_dict())
    d["cam"] = json.dumps(head_cam(v2).as_dict())
    d["v_fit_landmarks"] = v_fit
    d["v_fit"] = v2
    d["shape_params"] = json.dumps(log["params"])
    np.savez_compressed(WORK / "face_fit.npz", **d)
    (WORK / "shape_log.json").write_text(json.dumps(log, indent=1))
    # overlay: photo skin (red) vs render skin (green)
    sm = skin_mask(v2)
    ov = np.zeros((cam.H, cam.W, 3))
    ov[..., 0] = skin_p
    ov[..., 1] = sm
    ov[..., 2] = skin_mask(v2, True)[1]
    save_rgb(CHECK / "fit_silhouette.png", ov)


if __name__ == "__main__":
    main()
