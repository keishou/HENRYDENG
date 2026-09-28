#!/usr/bin/env python3
"""Project the rectified photo onto the fitted head and blend it into a colour-matched MakeHuman skin texture.

  photo side : hair strands lying on the forehead are inpainted (the 3D fringe re-creates them); the eyebrow
               band (MediaPipe brow landmarks) keeps the photo's own pixels; background/hair-mass/clothes are
               excluded and the valid region is eroded at the silhouette so no white background bleeds in.
  texture    : the skin mesh is rasterised in UV space; every texel is lifted to 3D, projected through the photo
               camera (render camera + the 2D similarity found by fit_face.py), tested for visibility with a
               z-buffer and weighted by how frontal it is.
  blend      : MakeHuman's young_asian_male skin (CC0) is colour-transferred (Lab mean/std) to the photo's skin,
               then photo and body texture are merged with a Laplacian-pyramid (multi-band) blend -> no seam.

Outputs (claudepop/out/avatar/work): skin_albedo.png (2048), photo_weight.png, photo_clean.png, eye_albedo.png
"""
from __future__ import annotations

import json

import cv2
import numpy as np

from avlib import MH, WORK, Cam, interp, load_rgb, rasterize, read_mhmat, save_rgb, vertex_normals
from fit_face import mp_sets
from mhscene import load_rgba, proxy_part, skin_part

T = 2048


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def bilinear(img, x, y):
    h, w = img.shape[:2]
    x = np.clip(x, 0, w - 1.001)
    y = np.clip(y, 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    if img.ndim == 3:
        fx, fy = fx[:, None], fy[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy
            + img[y0 + 1, x0 + 1] * fx * fy)


def push_pull(img, w, levels=10):
    """Fill where w==0 from the weighted surroundings (w in [0,1]); pull-push pyramid as in odyssey build_mesh."""
    pyr = [(img * w[..., None], w.copy())]
    for _ in range(levels):
        i, ww = pyr[-1]
        if min(ww.shape) < 4:
            break
        pyr.append((cv2.pyrDown(i), cv2.pyrDown(ww)))
    i, ww = pyr[-1]
    acc = i / np.maximum(ww[..., None], 1e-8)
    for i, ww in reversed(pyr[:-1]):
        up = cv2.resize(acc, (i.shape[1], i.shape[0]), interpolation=cv2.INTER_LINEAR)
        acc = i + (1 - np.clip(ww, 0, 1))[..., None] * up
    return acc


def multiband(a, b, m, levels=6):
    """Blend a (where m=1) and b (m=0) with Laplacian pyramids."""
    ga, gb, gm = [a], [b], [m]
    for _ in range(levels):
        ga.append(cv2.pyrDown(ga[-1]))
        gb.append(cv2.pyrDown(gb[-1]))
        gm.append(cv2.pyrDown(gm[-1]))
    out = ga[-1] * gm[-1][..., None] + gb[-1] * (1 - gm[-1][..., None])
    for k in range(levels - 1, -1, -1):
        sz = (ga[k].shape[1], ga[k].shape[0])
        la = ga[k] - cv2.pyrUp(ga[k + 1], dstsize=sz)
        lb = gb[k] - cv2.pyrUp(gb[k + 1], dstsize=sz)
        out = cv2.pyrUp(out, dstsize=sz) + la * gm[k][..., None] + lb * (1 - gm[k][..., None])
    return out


def lab(x):
    return cv2.cvtColor(x.astype(np.float32), cv2.COLOR_RGB2LAB)


def rgb(x):
    return cv2.cvtColor(x.astype(np.float32), cv2.COLOR_LAB2RGB)


def prepare_photo(photo, cls, conf, lm):
    """-> photo (unchanged), valid (float weight of usable face/ears/neck pixels), forehead cut mask, skin mask.

    * forehead: everything above a soft line just under the lower eyebrow contour is left to the colour-matched
      body skin (the photo's forehead is a patchwork of fringe strands; the 3D fringe re-creates them and the
      brows come from a tinted MakeHuman eyebrow proxy);
    * silhouette: the weight ramps up over 6-16 px from any non-skin pixel (background, hair, clothes), so no
      white background, hair or collar colour bleeds into the texture.
    """
    H, W = cls.shape
    sets = mp_sets()
    skin = ((cls == 3) | (cls == 2)).astype(np.uint8)
    n, labm, st, _ = cv2.connectedComponentsWithStats(skin, 8)
    if n > 1:
        skin = (labm == labm[int(lm[1, 1]), int(lm[1, 0])]).astype(np.uint8)
    d = cv2.distanceTransform(skin, cv2.DIST_L2, 5)
    ramp = smoothstep(6.0, 16.0, d)
    # lower eyebrow edge: quadratic through the lower half of each brow's landmarks
    pts = []
    for k in ("lbrow", "rbrow"):
        q = lm[sets[k], :2]
        med = np.median(q[:, 1])
        pts.append(q[q[:, 1] >= med])
    pts = np.concatenate(pts)
    cy = np.polyfit(pts[:, 0], pts[:, 1], 2)
    yy, xx = np.mgrid[0:H, 0:W]
    ycut = np.polyval(cy, xx)
    cut = smoothstep(ycut + 2.0, ycut + 12.0, yy)
    # thin hair strands that the segmenter misses between the brows and the upper eyelids: darker than the local
    # skin, outside the (dilated) eye contours
    eyes = np.zeros((H, W), np.uint8)
    for k in ("leye", "reye"):
        cv2.fillConvexPoly(eyes, cv2.convexHull(lm[sets[k], :2].astype(np.float32)).astype(np.int32), 1)
    eyes = cv2.dilate(eyes, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))).astype(bool)
    eye_top = min(lm[sets["leye"], 1].min(), lm[sets["reye"], 1].min())
    L = cv2.cvtColor((photo * 255).astype(np.uint8), cv2.COLOR_RGB2LAB)[..., 0].astype(np.float32)
    local = cv2.medianBlur(L.astype(np.uint8), 31).astype(np.float32)
    zone = (yy < eye_top + 0.3 * (lm[152, 1] - eye_top) * 0.2) & (yy > ycut - 5) & ~eyes & skin.astype(bool)
    dark = zone & (L < local - 18)
    dark = cv2.dilate(dark.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))).astype(bool)
    dark_w = 1.0 - cv2.GaussianBlur(dark.astype(np.float32), (0, 0), 2.0)
    valid = (ramp * cut * np.clip(dark_w * 1.5 - 0.5, 0, 1)).astype(np.float32)
    return photo, valid, cut, skin.astype(bool)


def main():
    F = np.load(WORK / "face_fit.npz")
    v = F["v_fit"]
    cam = Cam.from_dict(json.loads(str(F["cam"])))
    s, R, t = float(F["sim_s"]), F["sim_R"], F["sim_t"]
    A = np.load(WORK / "analysis.npz")
    lm, cls, conf = A["lm"].astype(np.float64), A["cls"], A["conf"].astype(np.float32)
    photo = load_rgb(WORK / "photo_rect.png")
    clean, valid, cut, skinm = prepare_photo(photo, cls, conf, lm)
    save_rgb(WORK / "photo_valid.png", np.repeat(valid[..., None], 3, -1))

    mh = MH()
    base = mh.base()
    skin = skin_part(base)
    vm = v * 0.1
    vs = vm[skin.src_index]
    ns = vertex_normals(vs, skin.tris)
    # normals must be continuous across UV seams: average per base vertex
    acc = np.zeros((len(base.v), 3))
    np.add.at(acc, skin.src_index, ns)
    ns = acc[skin.src_index]
    ns /= np.maximum(np.linalg.norm(ns, axis=1, keepdims=True), 1e-9)

    # visibility z-buffer in the render camera (skin + eyeballs)
    eyes = proxy_part(mh, "eyes/high-poly/high-poly.mhclo")
    ev = eyes.proxy.fit(v)[eyes.src_index] * 0.1
    allv = np.r_[vs, ev]
    _cc = eyes.uv[eyes.tris].mean(1)
    allt = np.r_[skin.tris, eyes.tris[~((_cc[:, 0] > 0.8) & (_cc[:, 1] > 0.8))] + len(vs)]  # no cornea shell
    pz = cam.project(allv)
    _, _, zbuf = rasterize(pz[:, :2], allt, cam.W, cam.H, Z=pz[:, 2])

    # UV-space raster
    tri_img, bary, _ = rasterize(skin.uv * T, skin.tris, T, T)
    m = tri_img >= 0
    X = interp(vs, skin.tris, tri_img, bary)[m]
    N = interp(ns, skin.tris, tri_img, bary)[m]
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    p = cam.project(X)
    inside = (p[:, 0] >= 0) & (p[:, 0] < cam.W - 1) & (p[:, 1] >= 0) & (p[:, 1] < cam.H - 1) & (p[:, 2] > 0)
    zb = zbuf[np.clip(p[:, 1].astype(int), 0, cam.H - 1), np.clip(p[:, 0].astype(int), 0, cam.W - 1)]
    vis = inside & (p[:, 2] <= zb + 0.0025)
    eye = cam.eye()
    vdir = eye[None] - X
    vdir /= np.linalg.norm(vdir, axis=1, keepdims=True)
    cosv = (N * vdir).sum(1)
    wf = smoothstep(0.40, 0.78, cosv)
    q = ((p[:, :2] - t) @ R) / s  # photo pixel coordinates: R^T (p - t) / s
    wv = bilinear(valid, q[:, 0], q[:, 1])
    w = wf * vis * wv
    # the photo booth's side lights leave bright bands along the face sides (the cheeks near the ears); they are
    # lighting, not albedo, and at 35-50 degrees of yaw they face the camera as a light streak on the cheek.
    # Remove the local highlight excess (over a masked 8 px blur of the skin) where the surface turns away.
    vf_ = valid.astype(np.float32)
    Lc = clean.mean(-1).astype(np.float32)
    Lb = cv2.GaussianBlur(Lc * vf_, (0, 0), 8.0) / np.maximum(cv2.GaussianBlur(vf_, (0, 0), 8.0), 1e-3)
    hl_excess = np.clip(Lc - Lb - 0.015, 0, None) * vf_
    col = bilinear(clean, q[:, 0], q[:, 1]) - (bilinear(hl_excess, q[:, 0], q[:, 1]) * (1 - smoothstep(0.6, 0.92, cosv)))[:, None]

    W_img = np.zeros((T, T))
    W_img[m] = w
    P_img = np.zeros((T, T, 3))
    P_img[m] = col
    save_rgb(WORK / "photo_weight.png", np.repeat(W_img[..., None], 3, -1))

    # MakeHuman skin, colour-transferred to the photo's skin
    ktex = load_rgb(read_mhmat(mh.data("skins/young_asian_male/young_asian_male.mhmat"))["diffuseTexture_abs"])
    if ktex.shape[0] != T:
        ktex = cv2.resize(ktex, (T, T), interpolation=cv2.INTER_AREA)
    sel = W_img > 0.8
    # exclude eyes/brows/lips from the statistics: use cheek-like texels (photo luminance close to median)
    Lk, Lp = lab(ktex), lab(P_img)
    lum = Lp[..., 0]
    med = np.median(lum[sel])
    sel &= np.abs(lum - med) < 12
    mk, sk = Lk[sel].mean(0), Lk[sel].std(0)
    mp_, sp = Lp[sel].mean(0), Lp[sel].std(0)
    ratio = np.clip(sp / np.maximum(sk, 1e-6), 0.6, 1.4)
    K2 = rgb((Lk - mk) * ratio + mp_)
    K2 = np.clip(K2, 0, 1)
    # ---- seam-free low-frequency colour field on the mesh: per base vertex, photo colour where the photo sees
    # the skin, MakeHuman body colour far from the head, harmonic interpolation in between (continuous across
    # UV seams because it lives on the vertices), then MakeHuman's own high frequencies (clamped) on top
    import scipy.sparse as sps
    import scipy.sparse.linalg as spla
    nb = len(base.v)
    tb = skin.src_index[skin.tris]
    used = np.unique(tb)
    bnorm = acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-9)
    pvv = cam.project(vm[used])
    inb = (pvv[:, 0] >= 0) & (pvv[:, 0] < cam.W - 1) & (pvv[:, 1] >= 0) & (pvv[:, 1] < cam.H - 1)
    zbv = zbuf[np.clip(pvv[:, 1].astype(int), 0, cam.H - 1), np.clip(pvv[:, 0].astype(int), 0, cam.W - 1)]
    visv = inb & (pvv[:, 2] <= zbv + 0.0025)
    vd = eye[None] - vm[used]
    vd /= np.linalg.norm(vd, axis=1, keepdims=True)
    cos_b = (bnorm[used] * vd).sum(1)
    qv = ((pvv[:, :2] - t) @ R) / s
    # masked (normalised) blur: near the face silhouette a plain blur mixes the page / ear / hair into the skin's
    # low-frequency colour, which showed as a light streak on the cheek at 35-50 degrees of yaw
    vf = valid.astype(np.float32)
    photo_dh = photo.astype(np.float32) - hl_excess[..., None]      # base colour without the side-light highlights
    photo_lp = cv2.GaussianBlur(photo_dh * vf[..., None], (0, 0), 3.0) / \
        np.maximum(cv2.GaussianBlur(vf, (0, 0), 3.0), 1e-3)[..., None]
    wv_b = smoothstep(0.40, 0.78, cos_b) * visv * bilinear(valid, qv[:, 0], qv[:, 1])
    col_b = bilinear(photo_lp, qv[:, 0], qv[:, 1])
    K2lp = cv2.GaussianBlur(K2.astype(np.float32), (0, 0), 10.0)
    uv_b = np.zeros((nb, 2))
    uv_b[skin.src_index] = skin.uv
    k_b = bilinear(K2lp, uv_b[used, 0] * T - 0.5, uv_b[used, 1] * T - 0.5)
    hm = F["mask"][used]
    fix_p = wv_b > 0.5
    fix_k = (hm < 0.02) & ~fix_p
    ci = np.zeros((len(used), 3))
    ci[fix_p] = col_b[fix_p]
    ci[fix_k] = k_b[fix_k]
    loc = -np.ones(nb, np.int64)
    loc[used] = np.arange(len(used))
    e = np.r_[tb[:, [0, 1]], tb[:, [1, 2]], tb[:, [2, 0]]]
    e = loc[e]
    Adj = sps.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(used),) * 2).tocsr()
    Adj = ((Adj + Adj.T) > 0).astype(np.float64)
    Lap = sps.diags(np.asarray(Adj.sum(1)).ravel()) - Adj
    fixed = fix_p | fix_k
    free = ~fixed
    Lff = Lap[free][:, free].tocsc()
    rhs = -Lap[free][:, fixed] @ ci[fixed]
    solve = spla.factorized(Lff)
    for ch in range(3):
        ci[free, ch] = solve(rhs[:, ch])
    cfield = np.zeros((nb, 3))
    cfield[used] = ci
    lf_img = np.zeros((T, T, 3))
    lf_img[m] = interp(cfield[skin.src_index], skin.tris, tri_img, bary)[m]
    lf_img = push_pull(lf_img.astype(np.float32), m.astype(np.float32))
    hf = K2 - cv2.GaussianBlur(K2.astype(np.float32), (0, 0), 4.0)
    head_uv = np.zeros((T, T))
    head_uv[m] = interp(F["mask"][skin.src_index][:, None], skin.tris, tri_img, bary)[m][:, 0]
    head_uv = cv2.GaussianBlur(head_uv.astype(np.float32), (0, 0), 4)
    clampv = (0.06 - 0.035 * head_uv)[..., None]
    base_tex = np.clip(lf_img + np.clip(hf, -clampv, clampv), 0, 1)
    # fill the photo layer outside its support, then multi-band blend
    wb = cv2.GaussianBlur(W_img.astype(np.float32), (0, 0), 1.5)
    P_fill = push_pull(P_img.astype(np.float32), (W_img > 0.02).astype(np.float32) * np.clip(W_img * 4, 0, 1).astype(np.float32))
    out = multiband(P_fill.astype(np.float32), base_tex.astype(np.float32), wb.astype(np.float32), levels=6)
    out = np.clip(out, 0, 1)
    save_rgb(WORK / "skin_albedo.png", out)
    save_rgb(WORK / "skin_body_transfer.png", K2)
    save_rgb(WORK / "skin_lowfreq.png", lf_img)
    stats = {"photo_texels": int((W_img > 0.5).sum()), "lab_mean_mh": mk.tolist(), "lab_mean_photo": mp_.tolist()}
    (WORK / "bake_log.json").write_text(json.dumps(stats, indent=1))

    # eyes: recolour MakeHuman's brown eye texture towards the photo's iris / sclera
    ep = eyes.proxy.material["diffuseTexture_abs"]
    et = load_rgba(ep)
    sets = mp_sets()
    iris_px = []
    for c in (468, 473):
        r = np.linalg.norm(lm[c, :2] - lm[c + 1, :2])
        yy, xx = np.mgrid[0:photo.shape[0], 0:photo.shape[1]]
        mm = (xx - lm[c, 0]) ** 2 + (yy - lm[c, 1]) ** 2 < (0.6 * r) ** 2
        iris_px.append(photo[mm])
    iris = np.concatenate(iris_px)
    iris_col = np.median(iris, 0)
    L = lab(et[..., :3])
    # iris pixels of the MH texture: saturated / dark region
    # the two iris discs: pupil = darkest blobs; iris radius = where the radial lightness profile reaches the sclera
    Lc = L[..., 0]
    n_, lab_, st_, cen_ = cv2.connectedComponentsWithStats((Lc < 18).astype(np.uint8), 8)
    order_ = np.argsort(-st_[1:, cv2.CC_STAT_AREA])[:2] + 1
    yy_, xx_ = np.mgrid[0:Lc.shape[0], 0:Lc.shape[1]]
    irism = np.zeros(Lc.shape, bool)
    for i in order_:
        cx_, cy_ = cen_[i]
        rr = np.hypot(xx_ - cx_, yy_ - cy_)
        prof = [np.median(Lc[(rr >= r) & (rr < r + 2)]) for r in range(0, int(0.25 * Lc.shape[0]), 2)]
        r_iris = 2 * next((k for k, val in enumerate(prof) if k > 3 and val > 62), len(prof))
        irism |= rr < r_iris
    li = lab(iris_col[None, None])[0, 0]
    L2 = L.copy()
    # the photo's irises read almost black at portrait distance: match their mean lightness (a bit darker)
    L2[irism, 0] = L[irism, 0] * min(0.6, 0.85 * li[0] / max(L[irism, 0].mean(), 1))
    L2[irism, 1:] = (L[irism, 1:] - L[irism, 1:].mean(0)) * 0.8 + li[1:] * 1.2
    # sclera: slightly warm, not paper white
    scl = ~irism
    L2[scl, 0] = np.minimum(L[scl, 0] * 1.25, 93)
    eo = np.clip(rgb(L2), 0, 1)
    # project the photo's own eyes (iris, sclera, catch-light) onto the front of the fitted eyeballs: from the photo
    # camera the eyes are then the real ones; when the eye bones rotate, the iris moves with the ball
    ET = eo.shape[0]
    corn = (lambda c: (c[:, 0] > 0.8) & (c[:, 1] > 0.8))(eyes.uv[eyes.tris].mean(1))
    etris = eyes.tris[~corn]
    ti_e, ba_e, _ = rasterize(eyes.uv * ET, etris, ET, ET)
    me = ti_e >= 0
    Xe = interp(ev, etris, ti_e, ba_e)[me]
    ne_ = vertex_normals(ev, etris)
    Ne = interp(ne_, etris, ti_e, ba_e)[me]
    Ne /= np.maximum(np.linalg.norm(Ne, axis=1, keepdims=True), 1e-9)
    pe = cam.project(Xe)
    zbe = zbuf[np.clip(pe[:, 1].astype(int), 0, cam.H - 1), np.clip(pe[:, 0].astype(int), 0, cam.W - 1)]
    vis_e = pe[:, 2] <= zbe + 0.0015
    de = eye[None] - Xe
    de /= np.linalg.norm(de, axis=1, keepdims=True)
    cos_e = (Ne * de).sum(1)
    qe = ((pe[:, :2] - t) @ R) / s
    # photo eye apertures (MediaPipe eye contours), slightly shrunk so no eyelid/lash pixels are taken
    # the eye contour as an ordered polygon (not its convex hull, which would take lid and lash pixels)
    from mediapipe.python.solutions import face_mesh_connections as fmc
    ap = np.zeros(photo.shape[:2], np.uint8)
    for conns in (fmc.FACEMESH_LEFT_EYE, fmc.FACEMESH_RIGHT_EYE):
        nxt = {}
        for a_, b_ in conns:
            nxt.setdefault(a_, []).append(b_)
            nxt.setdefault(b_, []).append(a_)
        start = next(iter(nxt))
        ring, prev, cur = [start], None, start
        while True:
            cand = [n for n in nxt[cur] if n != prev]
            if not cand or cand[0] == start:
                break
            prev, cur = cur, cand[0]
            ring.append(cur)
        cv2.fillPoly(ap, [lm[ring, :2].astype(np.int32)], 1)
    ap = cv2.erode(ap, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    apf = cv2.GaussianBlur(ap.astype(np.float32), (0, 0), 1.2)
    # complete each photo iris as a full disc (MediaPipe iris centre + radius): the part hidden by the upper lid
    # is filled by mirroring the visible lower half through the iris centre
    iris_img = photo.astype(np.float32).copy()
    disc = np.zeros(photo.shape[:2], np.float32)
    yy, xx = np.mgrid[0:photo.shape[0], 0:photo.shape[1]]
    for c in (468, 473):
        cx_, cy_ = lm[c, :2]
        r_ = np.mean(np.linalg.norm(lm[c + 1:c + 5, :2] - lm[c, :2], axis=1)) * 1.05
        d_ = np.hypot(xx - cx_, yy - cy_)
        inside = d_ < r_
        hidden = inside & (ap == 0)
        # radial colour profile of the visible iris (limbus ring, stroma, pupil) -> rotationally symmetric fill
        vis_px = inside & (ap > 0)
        nb = 12
        rb = np.clip((d_ / r_ * nb).astype(int), 0, nb - 1)
        prof = np.array([np.median(photo[vis_px & (rb == k)], 0) if (vis_px & (rb == k)).sum() > 3 else np.full(3, np.nan)
                         for k in range(nb)])
        for k in range(nb):  # fill empty bins from their neighbours
            if np.isnan(prof[k]).any():
                good = [j for j in range(nb) if not np.isnan(prof[j]).any()]
                prof[k] = prof[min(good, key=lambda j: abs(j - k))]
        iris_img[hidden] = prof[rb[hidden]]
        disc = np.maximum(disc, np.clip(r_ + 0.5 - d_, 0, 1))
    front = smoothstep(0.45, 0.75, cos_e)
    w_ap = front * vis_e * bilinear(apf, qe[:, 0], qe[:, 1])
    w_ir = front * bilinear(disc, qe[:, 0], qe[:, 1])
    col_ap = bilinear(photo.astype(np.float32), qe[:, 0], qe[:, 1])
    col_ir = bilinear(iris_img, qe[:, 0], qe[:, 1])
    # base: recoloured MakeHuman eyeball with its own iris painted over by sclera (the iris now comes from the photo)
    scl_col = np.median(eo[~irism], 0)
    base_e = eo.copy()
    irm = cv2.GaussianBlur(cv2.dilate(irism.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32), (0, 0), 3)
    base_e = base_e * (1 - irm[..., None]) + scl_col * irm[..., None]
    # match the MakeHuman sclera around the photo aperture to the photo's own sclera colour: the photo's eye white
    # is a dim warm grey (lid shadow, the real eye is not paper white); a bright MH sclera shows as white wedges at
    # the eye corners wherever the 3D lid aperture is a little wider than the photo's
    scl_ph = []
    for c in (468, 473):
        r_ = np.mean(np.linalg.norm(lm[c + 1:c + 5, :2] - lm[c, :2], axis=1))
        d_ = np.hypot(xx - lm[c, 0], yy - lm[c, 1])
        sel = (ap > 0) & (d_ > 1.2 * r_) & (d_ < 3.5 * r_)
        if sel.sum() > 10:
            scl_ph.append(photo[sel])
    if scl_ph:
        # the median of the whole visible white (lid-shadowed corners included), a little darker still: the MH
        # sclera only shows in the thin band between the photo aperture and the 3D lids, which is in lid shadow
        tgt = 0.92 * np.median(np.concatenate(scl_ph), 0)
        cur = np.median(base_e[~irism], 0)
        base_e = np.clip(base_e * (tgt / np.maximum(cur, 1e-3))[None, None], 0, 1)
        print("sclera matched to the photo")
    def to_img(vals, fill_w=None):
        img = np.zeros((ET, ET) + vals.shape[1:], np.float32)
        img[me] = vals
        return img
    Wa = cv2.GaussianBlur(to_img(w_ap), (0, 0), 1.5)
    Wi = cv2.GaussianBlur(to_img(w_ir), (0, 0), 1.5)
    Ca = push_pull(to_img(col_ap), (Wa > 0.05).astype(np.float32))
    Ci = push_pull(to_img(col_ir), (Wi > 0.05).astype(np.float32))
    eo = base_e * (1 - Wi[..., None]) + Ci * Wi[..., None]
    eo = eo * (1 - Wa[..., None]) + Ca * Wa[..., None]
    We = np.maximum(Wa, Wi)
    save_rgb(WORK / "eye_albedo.png", eo)
    save_rgb(WORK / "eye_photo_weight.png", np.repeat(We[..., None], 3, -1))
    print(json.dumps({"photo_texels": stats["photo_texels"], "iris_rgb": iris_col.round(3).tolist()}))


if __name__ == "__main__":
    main()
