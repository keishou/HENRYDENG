#!/usr/bin/env python3
"""Fit the MakeHuman head to the subject's face (478 MediaPipe landmarks from the rectified photo).

Method (analysis-by-synthesis, no hand-placed correspondences):
  1. Build the macro body (male, 25 y, East Asian, lean, 175 cm assumed) and render its head with a
     pinhole camera (distance CAM_D) using the small numpy renderer (skin texture, eyes, brows, lashes).
  2. Run the same MediaPipe Face Landmarker on that render.  Each detected landmark is traced back to the
     MakeHuman skin surface (triangle + barycentric), which gives 478 MH-surface <-> MediaPipe correspondences.
  3. Map the photo landmarks into the render's image plane with a 2D similarity (scale/rotation/shift):
     the head keeps MakeHuman's size ("scaled to MH head size").
  4. Displacement at every correspondence: image-plane offset lifted to world units at the landmark depth,
     plus a damped depth offset from the difference of MediaPipe's own z estimates (photo vs render).
     Solve  d(x) = affine(x) + TPS residual(x)  with zero-residual anchors on the back of the skull and neck,
     masked by the MPFB2 head-bone weights (1 on the head, fading through the neck).  Eyeballs move rigidly.
  5. Re-render, re-detect, repeat.  The loop converges to the geometry on which MediaPipe sees the photo's face.
  6. Irises: translate each eyeball in the image plane so the rendered iris centre lands on the photo's.

Outputs (claudepop/out/avatar/work, gitignored): face_fit.npz (fitted base vertices, correspondences, camera,
similarity), fit_log.json (errors per iteration, as % of outer-eye-corner distance), debug renders.

    python3 fit_face.py [--iters 6]
"""
from __future__ import annotations

import argparse
import json
import time

import cv2
import numpy as np
from scipy.interpolate import RBFInterpolator

import swr
from avlib import CHECK, MODELS, MH, WORK, Cam, dense_weights, load_rgb, load_rig, load_weights, read_mhmat, save_rgb
from mhscene import load_rgba, macro_body, proxy_part, skin_part, texture_of

CAM_D = 1.3          # assumed photo camera distance (m); a passport camera is typically 1-1.5 m away
IMG = 1024
Z_GAIN = 0.6         # trust in MediaPipe's depth differences (0 = keep MakeHuman depth)
OUTER = (33, 263)    # outer eye corners (normalisation of landmark errors)


def mp_sets():
    from mediapipe.python.solutions import face_mesh_connections as fmc
    s = lambda c: sorted({i for e in c for i in e})
    return dict(leye=s(fmc.FACEMESH_LEFT_EYE), reye=s(fmc.FACEMESH_RIGHT_EYE), lips=s(fmc.FACEMESH_LIPS),
                oval=s(fmc.FACEMESH_FACE_OVAL), lbrow=s(fmc.FACEMESH_LEFT_EYEBROW), rbrow=s(fmc.FACEMESH_RIGHT_EYEBROW),
                liris=s(fmc.FACEMESH_LEFT_IRIS), riris=s(fmc.FACEMESH_RIGHT_IRIS))


class Detector:
    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision
        self.mp = mp
        self.fl = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
            base_options=mpt.BaseOptions(model_asset_path=str(MODELS / "face_landmarker.task")), num_faces=1,
            output_facial_transformation_matrixes=True))

    def __call__(self, img):
        a = img if img.dtype == np.uint8 else (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
        H, W = a.shape[:2]
        r = self.fl.detect(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(a[..., :3])))
        if not r.face_landmarks:
            return None
        return np.array([[p.x * W, p.y * H, p.z * W] for p in r.face_landmarks[0]])


def similarity_2d(src, dst, w=None):
    """Least-squares s,R,t with dst ~ s R src + t (Umeyama, 2D)."""
    w = np.ones(len(src)) if w is None else w
    w = w / w.sum()
    ms, md = (w[:, None] * src).sum(0), (w[:, None] * dst).sum(0)
    a, b = src - ms, dst - md
    Cm = (w[:, None, None] * (b[:, :, None] * a[:, None, :])).sum(0)
    U, S, Vt = np.linalg.svd(Cm)
    D = np.diag([1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    var = (w * (a ** 2).sum(1)).sum()
    s = np.trace(np.diag(S) @ D) / var
    t = md - s * R @ ms
    return s, R, t


def nme(a, b):
    """Mean landmark distance (first 468) as % of the outer-eye-corner distance of b."""
    iod = np.linalg.norm(b[OUTER[0], :2] - b[OUTER[1], :2])
    return float(100 * np.linalg.norm(a[:468, :2] - b[:468, :2], axis=1).mean() / iod)


class HeadScene:
    def __init__(self, mh: MH, base, v0):
        self.mh, self.base = mh, base
        self.skin = skin_part(base)
        self.skintex = load_rgb(read_mhmat(mh.data("skins/young_asian_male/young_asian_male.mhmat"))["diffuseTexture_abs"])
        self.parts = []
        for rel, alpha in (("eyes/high-poly/high-poly.mhclo", "OPAQUE"), ("eyebrows/eyebrow001/eyebrow001.mhclo", "BLEND"),
                           ("eyelashes/eyelashes01/eyelashes01.mhclo", "BLEND")):
            P = proxy_part(mh, rel)
            tp = texture_of(P)
            tex = load_rgba(tp) if tp else None
            tris = P.tris
            if "eyes" in rel:  # drop the cornea shell (it maps to the white disc of the eye texture)
                c = P.uv[tris].mean(1)
                tris = tris[~((c[:, 0] > 0.8) & (c[:, 1] > 0.8))]
            self.parts.append((P, tris, tex, alpha))
        # skin triangles in base-vertex indices (for correspondences)
        self.skin_tris_base = self.skin.src_index[self.skin.tris]

    def layers(self, v):
        vm = v * 0.1
        L = [dict(v=vm[self.skin.src_index], tris=self.skin.tris, uv=self.skin.uv, tex=self.skintex, name="skin")]
        for P, tris, tex, alpha in self.parts:
            pv = P.proxy.fit(v) * 0.1
            L.append(dict(v=pv[P.src_index], tris=tris, uv=P.uv, tex=tex, alpha=alpha, zbias=0.002, name=P.name))
        return L


def trace_landmarks(cam, lm_r, v, scene: HeadScene):
    """Map render landmarks to MH skin surface points -> (tri base-vertex ids (478,3), bary (478,3))."""
    vm = v * 0.1
    layers = scene.layers(v)
    skinL = layers[0]
    p = cam.project(skinL["v"])
    from avlib import rasterize
    tri_img, bary, dep = rasterize(p[:, :2], skinL["tris"], cam.W, cam.H, Z=p[:, 2])
    # full-scene depth, to detect landmarks that fall on the eyeballs (eyelid margins) or inside the mouth slit
    _, zfull, ids = swr.render(cam, [L for L in layers if L.get("alpha", "OPAQUE") != "BLEND"])
    T = np.zeros((len(lm_r), 3), np.int64)
    B = np.zeros((len(lm_r), 3))
    # visible skin vertices (for snapping)
    pv = cam.project(vm)
    skin_v = np.unique(scene.skin_tris_base)
    vis = np.zeros(len(vm), bool)
    xi, yi = np.clip(pv[skin_v, 0].astype(int), 0, cam.W - 1), np.clip(pv[skin_v, 1].astype(int), 0, cam.H - 1)
    vis[skin_v] = pv[skin_v, 2] <= zfull[yi, xi] + 0.003
    vis_ids = np.nonzero(vis)[0]
    snapped = 0
    for i, (x, y, _) in enumerate(lm_r):
        xi_, yi_ = int(np.clip(x, 0, cam.W - 1)), int(np.clip(y, 0, cam.H - 1))
        t = tri_img[yi_, xi_]
        ok = t >= 0 and ids[yi_, xi_] == 0 and abs(dep[yi_, xi_] - zfull[yi_, xi_]) < 0.002
        if ok:
            T[i] = scene.skin_tris_base[t]
            B[i] = bary[yi_, xi_]
        else:
            d = np.hypot(pv[vis_ids, 0] - x, pv[vis_ids, 1] - y)
            j = vis_ids[np.argmin(d)]
            T[i] = [j, j, j]
            B[i] = [1, 0, 0]
            snapped += 1
    return T, B, snapped


def surf(v, T, B):
    return (v[T] * B[:, :, None]).sum(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=6)
    a = ap.parse_args()
    t_start = time.time()
    CHECK.mkdir(parents=True, exist_ok=True)
    sets = mp_sets()
    det = Detector()
    A = np.load(WORK / "analysis.npz")
    lm_p = A["lm"].astype(np.float64)

    mh = MH()
    base = mh.base()
    v0, tl, hs = macro_body(mh, base)
    scene = HeadScene(mh, base, v0)

    # head mask from MPFB2 weights: head bone and all its descendants
    rig, order = load_rig()
    Wd = dense_weights(load_weights(), order, len(base.v))
    kids = {n: [m for m in order if rig[m]["parent"] == n] for n in order}
    sub, st = [], ["head"]
    while st:
        n = st.pop()
        sub.append(n)
        st += kids[n]
    wh = Wd[:, [order.index(n) for n in sub]].sum(1)
    wh = np.clip(wh, 0, 1)
    wn3 = Wd[:, order.index("neck03")]
    mask = np.clip(wh + 0.5 * wn3, 0, 1)  # head fully, upper neck half-way
    eye_groups = {}
    for g in ("helper-l-eye", "helper-r-eye"):
        gi = base.groups.index(g)
        eye_groups[g] = np.unique(base.fv[base.fgroup == gi])

    # camera: CAM_D in front of the eye midpoint
    eyec = 0.5 * (v0[eye_groups["helper-l-eye"]].mean(0) + v0[eye_groups["helper-r-eye"]].mean(0)) * 0.1
    # focal length so that the face occupies the same image fraction as in the photo
    iod_photo = np.linalg.norm(lm_p[OUTER[0], :2] - lm_p[OUTER[1], :2])
    f = 1.0 * IMG * CAM_D / 0.30  # provisional, refined after first detection
    target = eyec + np.array([0, -0.035, 0])
    cam = Cam.look_at(target + np.array([0, 0, CAM_D]), target, f, IMG, IMG)
    img, _, _ = swr.render(cam, scene.layers(v0), bg=(0.93, 0.93, 0.92))
    lm_r = det(img)
    iod_r = np.linalg.norm(lm_r[OUTER[0], :2] - lm_r[OUTER[1], :2])
    f *= iod_photo / iod_r
    # centre the render on the photo's framing (principal point offset)
    cam = Cam.look_at(target + np.array([0, 0, CAM_D]), target, f, IMG, IMG)
    img, _, _ = swr.render(cam, scene.layers(v0), bg=(0.93, 0.93, 0.92))
    lm_r = det(img)
    cam = Cam(cam.R, cam.t, cam.f, cam.cx - (np.mean(lm_r[:468, 0]) - np.mean(lm_p[:468, 0])),
              cam.cy - (np.mean(lm_r[:468, 1]) - np.mean(lm_p[:468, 1])), IMG, IMG)
    img, _, _ = swr.render(cam, scene.layers(v0), bg=(0.93, 0.93, 0.92))
    lm_r = det(img)
    save_rgb(WORK / "fit_iter0.png", img)
    T, B, snapped = trace_landmarks(cam, lm_r, v0, scene)
    print(f"correspondences: 478 ({snapped} snapped to nearest visible skin vertex)")

    # landmark weights: forehead / upper oval lie under the fringe in the photo -> lower weight
    wl = np.ones(478)
    for i in (10, 338, 297, 332, 284, 251, 21, 54, 103, 67, 109, 151, 9, 8, 107, 336, 66, 296, 69, 299, 104, 333, 108, 337):
        wl[i] = 0.4
    wl[468:] = 0.0  # irises handled separately (rigid eyeballs)

    # anchors: back of the skull + lower neck keep the affine-only motion
    vm0 = v0 * 0.1
    skin_ids = np.unique(scene.skin_tris_base)
    head_ids = skin_ids[mask[skin_ids] > 0.9]
    zc = np.median(vm0[head_ids, 2])
    back = head_ids[vm0[head_ids, 2] < zc - 0.02]
    neck = skin_ids[(mask[skin_ids] > 0.02) & (mask[skin_ids] < 0.5)]
    rng = np.random.default_rng(0)
    anchors = np.r_[rng.choice(back, min(160, len(back)), replace=False), rng.choice(neck, min(80, len(neck)), replace=False)]

    v = v0.copy()
    log = {"cam_d_m": CAM_D, "z_gain": Z_GAIN, "iters": []}
    base_err = None
    for it in range(a.iters + 1):
        img, _, _ = swr.render(cam, scene.layers(v), bg=(0.93, 0.93, 0.92))
        lm_r = det(img)
        if lm_r is None:
            raise SystemExit(f"iteration {it}: no face detected on the render")
        s, R, t = similarity_2d(lm_p[:468, :2], lm_r[:468, :2], wl[:468] + 1e-3)
        tgt2 = (lm_p[:, :2] @ R.T) * s + t
        err = nme(lm_r, np.c_[tgt2, lm_p[:, 2]])
        if base_err is None:
            base_err = err
        # per-region errors
        reg = {k: float(100 * np.linalg.norm(lm_r[idx, :2] - tgt2[idx], axis=1).mean() /
                        np.linalg.norm(tgt2[OUTER[0]] - tgt2[OUTER[1]])) for k, idx in sets.items() if max(idx) < 468}
        log["iters"].append({"iter": it, "nme_pct": err, "regions": reg})
        print(f"iter {it}: NME {err:.2f}% of outer-eye distance  " + " ".join(f"{k}={x:.2f}" for k, x in reg.items()))
        save_rgb(WORK / f"fit_iter{it}.png", img)
        if it == a.iters:
            break
        # displacement at the correspondences
        P = surf(v, T, B) * 0.1                    # metres
        pc = cam.project(P)
        depth = pc[:, 2]
        dpx = tgt2 - lm_r[:, :2]                   # image-plane offset (px)
        dz_px = (lm_p[:, 2] * s) - lm_r[:, 2]      # MediaPipe z difference (px units, smaller = closer)
        # to world: camera axes
        xc, yc, zcax = cam.R[0], cam.R[1], cam.R[2]
        dW = (dpx[:, :1] * xc - dpx[:, 1:2] * yc) * (depth / cam.f)[:, None] - (Z_GAIN * dz_px * depth / cam.f)[:, None] * zcax
        step = 1.0 if it < 3 else 0.8
        dW *= step
        use = wl > 0
        # affine part (damped towards identity) from weighted least squares
        X = np.c_[P[use], np.ones(use.sum())]
        Wt = wl[use]
        lam = 1e-4
        Aff = np.linalg.solve(X.T @ (X * Wt[:, None]) + lam * np.eye(4), X.T @ (dW[use] * Wt[:, None]))
        res = dW[use] - X @ Aff
        Pa = v[anchors] * 0.1
        ctrl = np.r_[P[use], Pa]
        vals = np.r_[res, np.zeros((len(anchors), 3))]
        rbf = RBFInterpolator(ctrl, vals, kernel="thin_plate_spline", smoothing=np.r_[1e-5 / np.maximum(Wt, 0.1), np.full(len(anchors), 1e-4)], degree=1)
        vm = v * 0.1
        sel = np.nonzero(mask > 1e-3)[0]
        disp = np.zeros_like(vm)
        disp[sel] = (np.c_[vm[sel], np.ones(len(sel))] @ Aff) + rbf(vm[sel])
        disp *= mask[:, None]
        # eyeballs: rigid translation (mean of the field over the eyeball)
        for g, ids in eye_groups.items():
            disp[ids] = disp[ids].mean(0)
        v = v + disp * 10.0
    # ---- irises: move the eyeballs so the rendered iris centres match the photo
    for k in range(3):
        img, _, _ = swr.render(cam, scene.layers(v), bg=(0.93, 0.93, 0.92))
        lm_r = det(img)
        s, R, t = similarity_2d(lm_p[:468, :2], lm_r[:468, :2], wl[:468] + 1e-3)
        tgt2 = (lm_p[:, :2] @ R.T) * s + t
        msgs = []
        for g, ids in eye_groups.items():
            c = v[ids].mean(0) * 0.1
            pc = cam.project(c[None])[0]
            # which iris is nearer to this eyeball in the image
            i_a, i_b = 468, 473
            ii = i_a if np.hypot(*(lm_r[i_a, :2] - pc[:2])) < np.hypot(*(lm_r[i_b, :2] - pc[:2])) else i_b
            d = tgt2[ii] - lm_r[ii, :2]
            dw = (d[0] * cam.R[0] - d[1] * cam.R[1]) * pc[2] / cam.f
            dw = np.clip(dw, -0.003, 0.003)
            v[ids] += dw * 10.0
            msgs.append(f"{g} iris offset {np.hypot(*d):.1f}px")
        print("iris pass", k, *msgs)
    img, _, _ = swr.render(cam, scene.layers(v), bg=(0.93, 0.93, 0.92))
    lm_r = det(img)
    s, R, t = similarity_2d(lm_p[:468, :2], lm_r[:468, :2], wl[:468] + 1e-3)
    tgt2 = (lm_p[:, :2] @ R.T) * s + t
    final = nme(lm_r, np.c_[tgt2, lm_p[:, 2]])
    log["final_nme_pct"] = final
    log["baseline_generic_nme_pct"] = base_err
    print(f"generic MH head: {base_err:.2f}%  ->  fitted: {final:.2f}%")
    # photo camera = render camera composed with the inverse 2D similarity (photo px = S^-1(render px))
    np.savez_compressed(WORK / "face_fit.npz", v_fit=v, v0=v0, T=T, B=B, cam=json.dumps(cam.as_dict()),
                        sim_s=s, sim_R=R, sim_t=t, mask=mask, lm_render=lm_r, height_slider=hs,
                        targets=json.dumps(tl))
    (WORK / "fit_log.json").write_text(json.dumps(log, indent=1))
    # debug: overlay of render landmarks vs target
    dbg = (img * 255).astype(np.uint8)[..., ::-1].copy()
    for (x, y), (xt, yt) in zip(lm_r[:468, :2], tgt2[:468]):
        cv2.line(dbg, (int(x), int(y)), (int(xt), int(yt)), (0, 0, 255), 1)
        cv2.circle(dbg, (int(xt), int(yt)), 1, (0, 255, 0), -1)
    cv2.imwrite(str(CHECK / "fit_landmarks.png"), dbg)
    print(f"done in {time.time() - t_start:.0f}s")


if __name__ == "__main__":
    main()
