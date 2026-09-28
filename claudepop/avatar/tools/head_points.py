#!/usr/bin/env python3
"""Head point cloud for the 'reconstruction' look: the odyssey single-view bust point cloud (bust/points.bin, photo
coloured) aligned onto the subject.glb head and expressed in the head bone's local frame, so a three.js Points object
parented to the head bone follows every motion clip.

    python head_points.py          # -> claudepop/out/avatar/lookdev/head_points.bin (+ .json header)

Alignment: least-squares similarity (Umeyama 1991) from the bust's 478 MediaPipe landmarks (bust/facemesh.json) onto the
same 478 landmarks on the fitted subject skin (face_fit.npz: triangle + barycentric per landmark), which fit_face.py
established. Points kept: hair, face and neck skin classes plus the inferred back-of-head shell, inside a sphere around
the head and above the collar. Output binary: uint32 count, float32 xyz (head-bone local, metres), uint8 rgb, uint8 class.
Everything written here is subject-derived and stays under claudepop/out/ (gitignored); this file holds code only.
"""
from __future__ import annotations

import json

import numpy as np

from motion_lib import OUT, Skeleton

LOOKDEV = OUT / "lookdev"


def umeyama(src, dst):
    """Similarity (s, R, t) minimising |dst - (s R src + t)|^2."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    xs, xd = src - mu_s, dst - mu_d
    cov = xd.T @ xs / len(src)
    U, S, Vt = np.linalg.svd(cov)
    D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    var = (xs ** 2).sum() / len(src)
    s = np.trace(np.diag(S) @ D) / var
    return s, R, mu_d - s * R @ mu_s


def main():
    sk = Skeleton()
    off = sk.g["asset"]["extras"]["floor_offset_m"]
    F = np.load(OUT / "work" / "face_fit.npz", allow_pickle=True)
    dst = (F["B"][:, :, None] * F["v_fit"][F["T"]]).sum(1) * 0.1 + np.array([0.0, off, 0.0])
    fm = json.load(open(OUT / "bust" / "facemesh.json"))
    src = np.array(fm["points"], float)
    n = min(len(src), len(dst), 468)            # the 468 surface landmarks (iris points excluded)
    s, R, t = umeyama(src[:n], dst[:n])
    res = np.linalg.norm((s * src[:n] @ R.T + t) - dst[:n], axis=1)
    buf = (OUT / "bust" / "points.bin").read_bytes()
    cnt = int(np.frombuffer(buf[:4], np.uint32)[0])
    pos = np.frombuffer(buf, np.float32, cnt * 3, 8).reshape(cnt, 3).astype(float)
    col = np.frombuffer(buf, np.uint8, cnt * 3, 8 + cnt * 12).reshape(cnt, 3)
    cls = np.frombuffer(buf, np.uint8, cnt, 8 + cnt * 15)
    X = s * pos @ R.T + t                        # subject rest frame (floor at 0)
    ih, inck = sk.ix["head"], sk.ix["neck02"]
    head_c = dst[:n].mean(0) + np.array([0.0, 0.03, -0.04])
    keep = np.isin(cls, [1, 2, 3, 9]) & (np.linalg.norm(X - head_c, axis=1) < 0.16) & (X[:, 1] > sk.H[inck][1] - 0.02)
    Xk, Ck, Kk = X[keep], col[keep], cls[keep]
    # head-bone local coordinates (rest pose): p_local = R_head^T (p - head_pos)
    L = (Xk - sk.H[ih]) @ sk.R[ih]
    LOOKDEV.mkdir(parents=True, exist_ok=True)
    with open(LOOKDEV / "head_points.bin", "wb") as f:
        f.write(np.array([len(L)], np.uint32).tobytes())
        f.write(L.astype(np.float32).tobytes())
        f.write(Ck.astype(np.uint8).tobytes())
        f.write(Kk.astype(np.uint8).tobytes())
    info = dict(count=int(len(L)), bone="head", frame="head bone local (rest), metres",
                fit_rms_mm=round(float(np.sqrt((res ** 2).mean()) * 1000), 2), scale=round(float(s), 5),
                classes={"1": "hair", "2": "neck skin", "3": "face skin", "9": "inferred back of head"})
    (LOOKDEV / "head_points.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info))


if __name__ == "__main__":
    main()
