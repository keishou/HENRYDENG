#!/usr/bin/env python3
"""Fringe as ribbon hair strands, traced along the photo's own strand directions.

The hair shell (build_hair.py) is carved away over the photo's fringe zone (build_hair.forehead_carve).  Here the
fringe is rebuilt as a few hundred thin, tapered ribbons:

1. Guide: a difference matte of the photo's fringe against the forehead skin (the photo is almost pure skin between
   the strands, so the clean plate is skin, not the page) and the photo's strand orientation field (structure
   tensor), blended with a fan-shaped prior (strands fall away from a point above the parting) where the photo
   has no clear direction.
2. Streamlines (evenly spaced, Jobard-Lefer style): seeds on opaque fringe pixels that the carved shell does not
   cover, or up to 120 px over the shell (there sparser and wider: the front of the hair mass gets the same strand
   texture), traced up over the shell (every strand roots in the hair mass, and the shell's cut edge is covered by
   strands flowing across it) and down to where the photo's strand ends.  Strands never turn horizontal (brows are
   not mistaken for hair) and may fall past the brows but never into the eyes.
3. Lift to 3D from the fitting camera: tips lie 3.5-6.5 mm in front of the forehead skin, roots 8 mm in front of
   the hair shell's outer surface (just over its fur shells, so they visibly cross its cut edge), blended over the
   first ~1 cm off the shell, so each strand arcs out of the hair mass and falls onto the forehead (from the side:
   bangs, not a visor).
4. Ribbons: 1.3-2.2 mm wide (2.2-3.4 mm over the hair mass), lying along the head surface, tapering to the tip,
   with a procedural fibre texture (alpha-blended, the shell's own albedo) and a per-vertex tangent along the
   strand for the anisotropic hair highlight.

Outputs (claudepop/out/avatar/work): strands.npz (ribbon mesh), strand_tex.png, strands_guide.png; check render
check/strands_preview.jpg (photo | photo camera | 35 / 90 degrees / from above).  Subject data: gitignored paths only.
"""
from __future__ import annotations

import json

import cv2
import numpy as np
from scipy.spatial import cKDTree

import swr
from avlib import CHECK, MH, WORK, Cam, load_rgb, save_rgb, vertex_normals
from bake_texture import bilinear, push_pull, smoothstep
from build_hair import forehead_carve, guide_alpha
from fit_face import mp_sets
from mhscene import proxy_part, skin_part

HAIR = "hair/short02/short02.mhclo"
RNG_SEED = 11


def orientation(photo):
    """Doubled-angle strand orientation field (cos 2t, sin 2t) and coherence from the photo's structure tensor."""
    L = cv2.GaussianBlur(photo.mean(-1).astype(np.float32), (0, 0), 0.8)
    gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)
    Jxx = cv2.GaussianBlur(gx * gx, (0, 0), 3.0)
    Jyy = cv2.GaussianBlur(gy * gy, (0, 0), 3.0)
    Jxy = cv2.GaussianBlur(gx * gy, (0, 0), 3.0)
    # strands run across the gradient: doubled strand angle = doubled gradient angle + pi
    c2, s2 = -(Jxx - Jyy), -2 * Jxy
    mag = np.sqrt(c2 ** 2 + s2 ** 2)
    coh = mag / np.maximum(Jxx + Jyy, 1e-9)
    return np.dstack([c2 / np.maximum(mag, 1e-9), s2 / np.maximum(mag, 1e-9)]), coh


def main():
    rng = np.random.default_rng(RNG_SEED)
    F = np.load(WORK / "face_fit.npz")
    v = F["v_fit"]
    vm = v * 0.1
    cam = Cam.from_dict(json.loads(str(F["cam"])))
    s, R, t = float(F["sim_s"]), F["sim_R"], F["sim_t"]
    A = np.load(WORK / "analysis.npz")
    lm, cls = A["lm"].astype(np.float64), A["cls"]
    photo = load_rgb(WORK / "photo_rect.png")
    H, W = cls.shape
    Hf = np.load(WORK / "hair_fit.npz")
    ycarve, (xl, xr), ybrow = forehead_carve(photo, cls, lm)
    sets = mp_sets()

    # ---------------- depth maps from the fitting camera: forehead skin, hair shell outer envelope (uncarved), and
    # where the carved shell covers the photo (strands root under it)
    from PIL import Image
    mh = MH()
    base = mh.base()
    skin = skin_part(base)
    vs = vm[skin.src_index]
    skinL = dict(v=vs, tris=skin.tris, light=False)
    _, z_sk, _ = swr.render(cam, [skinL])
    P = proxy_part(mh, HAIR)
    hv = Hf["short02_v"][P.src_index]
    _, z_sh, _ = swr.render(cam, [dict(v=hv, tris=P.tris, light=False)])
    short = np.asarray(Image.open(WORK / "short02_black.png"), np.float64) / 255
    _, _, ids = swr.render(cam, [skinL, dict(v=hv, tris=P.tris, uv=P.uv, tex=short, alpha="MASK", cutoff=0.45, light=False)])
    Minv = cv2.invertAffineTransform(np.c_[s * R, t])
    cov = cv2.warpAffine((ids == 1).astype(np.uint8), Minv, (W, H), flags=cv2.INTER_NEAREST)
    cov = cv2.morphologyEx(cov, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # the head's silhouette (skin or shell), shrunk a little: a strand never leaves it (its depth would be a guess)
    sil = cv2.erode(cv2.warpAffine((ids >= 0).astype(np.uint8), Minv, (W, H), flags=cv2.INTER_NEAREST), np.ones((9, 9), np.uint8))
    # signed distance to the shell's coverage in photo pixels: > 0 outside (bare forehead), < 0 under the shell
    sd = cv2.distanceTransform(1 - cov, cv2.DIST_L2, 5) - cv2.distanceTransform(cov, cv2.DIST_L2, 5)

    ga = guide_alpha(photo, cls, lm)
    ori, coh = orientation(photo)
    # lower limit: just below the lower eyebrow edge (quadratic through the lower half of the brow landmarks)
    pts = []
    for k in ("lbrow", "rbrow"):
        q = lm[sets[k], :2]
        pts.append(q[q[:, 1] >= np.median(q[:, 1])])
    pts = np.concatenate(pts)
    cy = np.polyfit(pts[:, 0], pts[:, 1], 2)
    ylow = lambda x: np.polyval(cy, x) + 24.0         # fringe tips may fall past the brows (not into the eyes)
    ytop_c = float(np.nanmin(np.where(np.isfinite(ycarve), ycarve, np.nan)))
    fan = np.array([float(lm[10, 0]), ytop_c - 160.0])       # strands fall away from a point above the parting

    FLD = np.dstack([ori, np.clip(2.0 * coh, 0, 1) * 0.8, ga, sd, sil]).astype(np.float64)   # cos2t, sin2t, w, alpha, sd, sil

    def samp(p):
        x = min(max(p[0], 0.0), W - 1.001)
        y = min(max(p[1], 0.0), H - 1.001)
        x0, y0 = int(x), int(y)
        fx, fy = x - x0, y - y0
        q = FLD[y0:y0 + 2, x0:x0 + 2]
        return (q[0, 0] * (1 - fx) + q[0, 1] * fx) * (1 - fy) + (q[1, 0] * (1 - fx) + q[1, 1] * fx) * fy

    def direction(p, prev):
        c2, s2, w = samp(p)[:3]
        th = 0.5 * np.arctan2(s2, c2)
        d = np.array([np.cos(th), np.sin(th)])
        if prev is not None and d @ prev < 0:
            d = -d
        pr = p - fan
        pr /= max(np.linalg.norm(pr), 1e-9)
        if prev is not None and pr @ prev < 0:
            pr = -pr
        d = w * d + (1 - w) * pr
        return d / max(np.linalg.norm(d), 1e-9)

    ROOT_IN = 14.0          # min. photo px a strand runs on over the shell before it ends (its root fades in there)
    OVER = 120.0            # strands also start up to this far over the shell (sparser, wider: the front of the
                            # hair mass gets the same strand texture as the fringe) and flow down across its cut
                            # edge, so the edge is covered by hair instead of reading as a cap line

    def trace(p0, down, maxlen=260, h=0.8):
        p = np.array(p0, float)
        prev = np.array([0.0, 1.0 if down else -1.0])
        out, miss = [], 0
        for _ in range(int(maxlen / h)):
            d = direction(p, prev)
            if (d[1] if down else -d[1]) < 0.2:         # never horizontal (brows, the hair mass)
                break
            q = p + h * d
            dq = direction(q, d)
            p = p + h * 0.5 * (d + dq)
            prev = d
            if not (0 <= p[0] < W - 1 and 0 <= p[1] < H - 1):
                break
            a, sdp, inside = samp(p)[3:6]
            if inside < 0.5:
                break
            if down:
                if p[1] > ylow(p[0]):
                    break
                miss = miss + 1 if a < 0.35 else 0
                if miss * h > 3.0:
                    break
            else:
                if sdp < -OVER - ROOT_IN:
                    out.append(p.copy())
                    break
                miss = miss + 1 if (a < 0.3 and sdp > 0) else 0
                if miss * h > 25.0:                      # a root through too much bare skin: not a strand
                    return None
            out.append(p.copy())
        return out

    # ---------------- streamlines: seeds on opaque fringe pixels the shell does not cover, above the brows
    yy, xx = np.mgrid[0:H, 0:W]
    oval = lm[sets["oval"], :2]
    zone = (sd > -OVER) & (yy < ylow(xx) - 4) & (yy > oval[:, 1].min() - 110) & (xx >= xl - 25) & (xx <= xr + 25)
    cand = np.argwhere(zone & (ga > 0.5))
    rng.shuffle(cand)
    occ_f = np.zeros((H, W), np.uint8)     # fringe (over bare forehead): dense
    occ_c = np.zeros((H, W), np.uint8)     # over the shell: sparse, wide strands (the mass is dark behind them)
    DSEP_F, DSEP_C = 1.1, 2.6
    strands, mass = [], []
    for (y0, x0) in cand:
        if (occ_f if sd[y0, x0] > 0 else occ_c)[y0, x0]:
            continue
        p0 = np.array([x0 + 0.5, y0 + 0.5])
        up = trace(p0, down=False)
        if up is None:
            continue
        dn = trace(p0, down=True)
        poly = np.array(up[::-1] + [p0] + (dn or []))
        sdp_ = np.array([samp(q)[4] for q in poly])
        if sdp_.min() > -ROOT_IN:                        # every strand roots over / in the hair mass
            continue
        if len(poly) * 0.8 < 18:
            continue
        strands.append(poly)
        mass.append(sdp_.max() < 2)
        pi = [np.round(poly).astype(np.int32)]
        cv2.polylines(occ_f, pi, False, 1, thickness=int(round(2 * DSEP_F)))
        cv2.polylines(occ_c, pi, False, 1, thickness=int(round(2 * DSEP_C)))
    print(f"strands: {len(strands)} ({sum(mass)} over the hair mass only; {len(cand)} seed candidates)")

    def fill(z):
        ok = np.isfinite(z)
        zf = push_pull(np.where(ok, z, 0)[..., None].repeat(3, -1).astype(np.float32), ok.astype(np.float32))[..., 0]
        return zf, ok

    z_skf, _ = fill(z_sk)
    z_shf, sh_ok = fill(z_sh)
    sh_okf = cv2.GaussianBlur(sh_ok.astype(np.float32), (0, 0), 2)

    # ---------------- ribbons
    head_ids = np.nonzero(F["mask"] > 0.9)[0]
    head_ids = head_ids[np.isin(head_ids, skin.src_index)]
    sn = vertex_normals(vs, skin.tris)
    acc = np.zeros((len(base.v), 3))
    np.add.at(acc, skin.src_index, sn)
    bn = acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-9)
    kd = cKDTree(vm[head_ids])
    Vs, Ts, UVs, TGs, SRC = [], [], [], [], []
    nv = 0
    SEG_PX = 6.0
    for poly, is_mass in zip(strands, mass):
        # resample at SEG_PX photo pixels
        seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
        sl = np.r_[0, np.cumsum(seg)]
        n = max(int(sl[-1] / SEG_PX), 3)
        ss = np.linspace(0, sl[-1], n + 1)
        pp = np.stack([np.interp(ss, sl, poly[:, 0]), np.interp(ss, sl, poly[:, 1])], 1)
        pr = pp @ R.T * s + t                                      # render-camera pixels
        zs = bilinear(z_skf[..., None], pr[:, 0], pr[:, 1])[:, 0]
        zh = bilinear(z_shf[..., None], pr[:, 0], pr[:, 1])[:, 0]
        okh = bilinear(sh_okf[..., None], pr[:, 0], pr[:, 1])[:, 0] > 0.5
        off_tip = rng.uniform(0.0035, 0.0065)
        d_tip = zs - off_tip
        d_root = np.where(okh, np.minimum(zh - 0.008, zs - 0.002), d_tip)
        sdl = bilinear(sd[..., None], pp[:, 0], pp[:, 1])[:, 0]
        w = smoothstep(-4.0, 30.0, sdl)
        d = (1 - w) * d_root + w * d_tip
        for _ in range(4):                                         # smooth along the strand (z-buffer steps)
            d[1:-1] = 0.5 * d[1:-1] + 0.25 * (d[:-2] + d[2:])
        d = np.minimum(d, zs - 0.003)
        Xc = np.stack([(pr[:, 0] - cam.cx) / cam.f * d, -(pr[:, 1] - cam.cy) / cam.f * d, -d], 1)
        X = (Xc - cam.t) @ cam.R
        tg = np.gradient(X, axis=0)
        tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-9)
        _, j = kd.query(X)
        nrm = bn[head_ids[j]]
        side = np.cross(tg, nrm)
        side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-9)
        u = ss / ss[-1]
        width = rng.uniform(*((0.0022, 0.0034) if is_mass else (0.0013, 0.0022))) * np.where(u < 0.6, 1.0, 1.0 - 0.7 * (u - 0.6) / 0.4)
        L_ = X - side * width[:, None] / 2
        R_ = X + side * width[:, None] / 2
        m = len(X)
        Vs.append(np.r_[L_, R_])
        UVs.append(np.r_[np.c_[np.zeros(m), u], np.c_[np.ones(m), u]])
        TGs.append(np.r_[tg, tg])
        SRC.append(np.r_[head_ids[j], head_ids[j]])
        i = np.arange(m - 1)
        Ts.append(nv + np.r_[np.c_[i, i + m, i + 1], np.c_[i + 1, i + m, i + 1 + m]])
        nv += 2 * m
    Vs, Ts, UVs, TGs, SRC = np.concatenate(Vs), np.concatenate(Ts), np.concatenate(UVs), np.concatenate(TGs), np.concatenate(SRC)
    print(f"ribbons: {len(Vs)} verts, {len(Ts)} tris")

    # ---------------- fibre texture (u across the ribbon, v root -> tip), colour = the shell's hair albedo
    TW, TH = 32, 256
    uu, vv = np.meshgrid((np.arange(TW) + 0.5) / TW, (np.arange(TH) + 0.5) / TH)
    alpha = np.zeros((TH, TW))
    lum = np.zeros((TH, TW))
    for k, (c, end, g) in enumerate(((0.28, 0.86, 0.9), (0.5, 1.0, 1.1), (0.72, 0.93, 1.0), (0.4, 0.97, 0.95), (0.6, 0.9, 1.05))):
        wave = 0.03 * np.sin(vv * 9.0 + k * 1.7)
        f = np.exp(-((uu - c - wave) / 0.13) ** 2) * (1 - smoothstep(end - 0.12, end, vv))
        alpha = np.maximum(alpha, f)
        lum = np.maximum(lum, f * g)
    alpha = np.clip(alpha * 1.15, 0, 1) * (1 - smoothstep(0.35, 0.5, np.abs(uu - 0.5))) * smoothstep(0.0, 0.03, vv)
    # the shell's own albedo (median over its opaque texels, photo bake included), so strands and hair mass match
    # in tone and the carved edge between them does not read as a line
    sh_px = short[..., :3][short[..., 3] > 0.5]
    dark = np.median(sh_px, 0)
    col = np.clip(dark[None, None] * (0.8 + 0.3 * lum[..., None]), 0, 1)
    tex = np.dstack([col, alpha])
    Image.fromarray((tex * 255 + 0.5).astype(np.uint8), "RGBA").save(WORK / "strand_tex.png")
    gimg = np.dstack([photo * 0.6, photo * 0.6, photo * 0.6])[..., :3].copy()
    for poly in strands:
        cv2.polylines(gimg, [np.round(poly * 4).astype(np.int32)], False, (1.0, 0.2, 0.1), 1, cv2.LINE_AA, shift=2)
    save_rgb(WORK / "strands_guide.png", np.clip(gimg[200:520, 260:780], 0, 1))
    np.savez_compressed(WORK / "strands.npz", pos=Vs, tris=Ts, uv=UVs, tangent=TGs, src=SRC, n_strands=len(strands))

    # ---------------- check render (software): skin + carved shell + strands, photo camera and three more views
    stex = load_rgb(WORK / "skin_albedo_hair.png")
    Ls = [dict(v=vs, tris=skin.tris, uv=skin.uv, tex=stex, ambient=0.7),
          dict(v=hv, tris=P.tris, uv=P.uv, tex=short, alpha="MASK", cutoff=0.45, two_sided=True, ambient=0.6),
          dict(v=Vs, tris=Ts, uv=UVs, tex=tex, alpha="BLEND", two_sided=True, ambient=0.6)]
    E = proxy_part(mh, "eyes/high-poly/high-poly.mhclo")
    cc = E.uv[E.tris].mean(1)
    Ls.insert(1, dict(v=E.proxy.fit(v)[E.src_index] * 0.1, tris=E.tris[~((cc[:, 0] > 0.8) & (cc[:, 1] > 0.8))], uv=E.uv,
                      tex=load_rgb(WORK / "eye_albedo.png"), ambient=0.75))
    Mw = np.c_[s * R, t]
    imgs = [cv2.warpAffine(photo, Mw, (cam.W, cam.H))]
    img, _, _ = swr.render(cam, Ls, bg=(0.2, 0.2, 0.2))
    imgs.append(img)
    head_c = vm[head_ids].mean(0) + np.array([0, 0.02, 0])
    for angd, el in ((35, 0), (90, 0), (15, 40)):
        ar, er = np.radians(angd), np.radians(el)
        eye = head_c + 1.3 * np.array([np.sin(ar) * np.cos(er), np.sin(er), np.cos(ar) * np.cos(er)])
        c2 = Cam.look_at(eye, head_c, cam.f * 0.9, 1024, 1024)
        im2, _, _ = swr.render(c2, Ls, bg=(0.2, 0.2, 0.2))
        imgs.append(im2)
    row = np.hstack(imgs)[150:800]
    save_rgb(CHECK / "strands_preview.jpg", cv2.resize(row, (row.shape[1] * 2 // 3, row.shape[0] * 2 // 3)))


if __name__ == "__main__":
    main()
