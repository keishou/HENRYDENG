#!/usr/bin/env python3
"""Hair for the avatar: MakeHuman short02 (CC0) re-volumised to the photo's silhouette, carved over the fringe.

1. Base volume: MakeHuman hair proxy short02 (short back and sides, volume on top) fitted to the fitted body.
   Its thickness is increased per image angle so that, seen from the photo camera, the head+hair silhouette
   matches the photo's (MediaPipe segmentation, smoothed so single flyaway curls do not count).  Roots stay on
   the scalp (vertices move along the scalp normal in proportion to their height above it).
2. The photo's hair is baked onto the shell's frontal texels, and the shell is carved away over the photo's
   fringe zone (forehead_carve: below a smooth hairline arc between the outer eye corners, the cut edge ending in
   pointed clump tips).  The fringe itself is rebuilt as ribbon strands by build_strands.py.  (The photo matte and
   a 2.5D relief of it are still computed here: the matte gives the hair colours, the relief's depth the
   visibility for the bake; the relief mesh is no longer exported - from the side it read as a visor.)
3. Scalp: skin texels under the hair get the hair's root colour (no skin through gaps), except in the carved
   fringe zone (bare forehead); behind the dense root band of the fringe and right under the cut edge the root
   colour is kept, and further down the forehead gets a soft shadow of the photo's fringe.
   The fur shells (export_glb.py) get their own texture, carved a little further back.

Outputs (claudepop/out/avatar/work): hair_fit.npz (short02 vertex positions, fringe carve curve, colours; relief
mesh for diagnostics), short02_black.png, short02_fur.png, skin_albedo_hair.png, check renders.
"""
from __future__ import annotations

import json

import cv2
import numpy as np
from scipy.spatial import cKDTree

import swr
from avlib import CHECK, MH, WORK, Cam, interp, load_rgb, rasterize, save_rgb, vertex_normals
from bake_texture import push_pull, smoothstep
from fit_face import mp_sets
from mhscene import load_rgba, proxy_part, skin_part, texture_of

HAIR = "hair/short02/short02.mhclo"


def photo_matte(photo, cls, lm):
    """Difference matting of the hair against a clean plate. Returns alpha (H,W), hair colour F (H,W,3)."""
    H, W = cls.shape
    L = photo.mean(-1)
    sets = mp_sets()
    hair = (cls == 1).astype(np.uint8)
    # the head's hair region only (drops the stamps, which are separate dark marks on the page)
    n, lab, st, _ = cv2.connectedComponentsWithStats(hair, 8)
    keep = np.zeros_like(hair)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a > 2000 and y < lm[1, 1]:
            keep[lab == i] = 1
    hair = keep
    near = cv2.dilate(hair, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))).astype(bool)
    core = cv2.erode(hair, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))).astype(bool)
    nonhair = (~hair.astype(bool)) & (L > 0.45) & (cls != 4)
    B = push_pull(photo.astype(np.float32), nonhair.astype(np.float32))
    confident = hair.astype(bool) & (L < 0.28)
    F = push_pull(photo.astype(np.float32), confident.astype(np.float32))
    BL, FL = B.mean(-1), F.mean(-1)
    a = np.clip((BL - L) / np.maximum(BL - FL, 0.15), 0, 1)
    a[core & (L < 0.45)] = 1.0   # not on light pixels: the segmenter labels the skin between fringe strands as hair
    # limits: near the hair mass, above the lower eyebrow edge, never on clothes / eyes
    pts = []
    for k in ("lbrow", "rbrow"):
        q = lm[sets[k], :2]
        pts.append(q[q[:, 1] >= np.median(q[:, 1])])
    pts = np.concatenate(pts)
    cy = np.polyfit(pts[:, 0], pts[:, 1], 2)
    yy, xx = np.mgrid[0:H, 0:W]
    face_hull = np.zeros((H, W), np.uint8)
    cv2.fillConvexPoly(face_hull, cv2.convexHull(lm[:468, :2].astype(np.float32)).astype(np.int32), 1)
    below_brow = (yy > np.polyval(cy, xx) + 4) & face_hull.astype(bool)
    a[~near | below_brow | (cls == 4)] = 0
    # sides of the face below eye level belong to ears/cheeks
    a[(yy > lm[33, 1]) & ~hair.astype(bool)] = 0
    a = cv2.GaussianBlur(a.astype(np.float32), (0, 0), 0.6)
    a[a < 0.04] = 0
    return a, np.clip(F, 0, 1), hair.astype(bool)


def ray_profile(mask, c, angles, rmax=700):
    """Distance from c to the outer boundary of mask along each image angle (0 = +x, 90 = up)."""
    out = np.zeros(len(angles))
    rs = np.arange(0, rmax, 0.5)
    for k, a in enumerate(np.radians(angles)):
        x = c[0] + rs * np.cos(a)
        y = c[1] - rs * np.sin(a)
        ok = (x >= 0) & (x < mask.shape[1]) & (y >= 0) & (y < mask.shape[0])
        inside = np.zeros(len(rs), bool)
        inside[ok] = mask[y[ok].astype(int), x[ok].astype(int)]
        idx = np.nonzero(inside)[0]
        out[k] = rs[idx.max()] if len(idx) else 0
    return out


def forehead_carve(photo, cls, lm):
    """The fringe zone of the photo, where the hair shell is carved away and ribbon strands (build_strands.py)
    carry the fringe: every row below a smooth hairline curve, between the outer eye corners (+ margin), down to just below
    the brows.  The curve is the lower of (a) the top of the forehead skin visible between the strands (per
    column, robustly smoothed) and (b) a smooth arc from that top at the face centre down to just above the brows
    at the outer eye corners, so dense parts of the fringe (no skin visible) are carved too and nothing leaves a slot.
    Returns ycarve (W,) photo rows (inf = column not carved), (xl, xr), brow top row."""
    from scipy.ndimage import median_filter, minimum_filter1d
    H, W = cls.shape
    sets = mp_sets()
    L = photo.mean(-1)
    oval = lm[sets["oval"], :2]
    ybrow = float(min(lm[sets["lbrow"], 1].min(), lm[sets["rbrow"], 1].min()))
    fs = (cls == 3) & (L > 0.45)
    fs = cv2.morphologyEx(fs.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(bool)
    # x-range: the forehead between the outer eye corners (+ a margin); the hair over the temples stays shell
    # (carving there cut the side hair into a jagged edge in front of the ears)
    xl = int(max(oval[:, 0].min(), min(lm[33, 0], lm[263, 0]) - 18))
    xr = int(min(oval[:, 0].max(), max(lm[33, 0], lm[263, 0]) + 18))
    xs = np.arange(W)
    yt = np.full(W, np.nan)
    for x in range(xl, xr + 1):
        r = np.nonzero(fs[:int(ybrow), x])[0]
        if len(r):
            yt[x] = r.min()
    ok = ~np.isnan(yt)
    yt = np.interp(xs, xs[ok], yt[ok])
    yt = cv2.GaussianBlur(minimum_filter1d(median_filter(yt, 21), 31)[None].astype(np.float32), (0, 0), 12)[0]
    xc = float(lm[10, 0])
    y_top = float(np.percentile(yt[xl:xr + 1], 5))
    a = (ybrow - 20 - y_top) / max((xr - xc) ** 2, (xc - xl) ** 2)
    yc = np.minimum(np.minimum(y_top + a * (xs - xc) ** 2, yt), ybrow - 12)
    yc = cv2.GaussianBlur(yc[None].astype(np.float32), (0, 0), 6)[0].astype(np.float64)
    # the shell's cut edge ends in pointed clump tips (seeded noise, 6-12 px features, up to ~18 px long), so it
    # reads as the ends of hair clumps among the strands, not as one smooth cap line
    nz = cv2.GaussianBlur(np.random.default_rng(5).normal(0, 1, W)[None].astype(np.float32), (0, 0), 3.0)[0]
    nz = np.clip(nz / max(float(nz.std()), 1e-6), 0, None) ** 1.5
    yc = yc + 11.0 * np.minimum(nz, 1.7)
    yc[(xs < xl) | (xs > xr)] = np.inf
    return yc, (xl, xr), ybrow


def guide_alpha(photo, cls, lm):
    """Matte of the fringe strands against the forehead skin, (H, W) in [0, 1]."""
    L = photo.mean(-1)
    skin_ok = ((cls == 3) | (cls == 2)) & (L > 0.45)
    B = push_pull(photo.astype(np.float32), skin_ok.astype(np.float32))
    hair_ok = (cls == 1) & (L < 0.28)
    Fh = push_pull(photo.astype(np.float32), hair_ok.astype(np.float32))
    BL, FL = B.mean(-1), Fh.mean(-1)
    a = np.clip((BL - L) / np.maximum(BL - FL, 0.15), 0, 1)
    a[L < 0.25] = 1.0
    eyes = np.zeros(L.shape, np.uint8)
    sets = mp_sets()
    for k in ("leye", "reye"):
        cv2.fillConvexPoly(eyes, cv2.convexHull(lm[sets[k], :2].astype(np.float32)).astype(np.int32), 1)
    eyes = cv2.dilate(eyes, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))).astype(bool)
    a[eyes] = 0
    return cv2.GaussianBlur(a.astype(np.float32), (0, 0), 0.7)


def forehead_zone(photo, cls, lm, below_brow=12):
    """Soft (H, W) mask of the carved fringe zone in the photo (see forehead_carve)."""
    yc, _, ybrow = forehead_carve(photo, cls, lm)
    yy = np.arange(cls.shape[0])[:, None]
    z = (yy >= yc[None, :]) & (yy <= ybrow + below_brow)
    return cv2.GaussianBlur(z.astype(np.float32), (0, 0), 1.2), yc, ybrow


def main():
    F = np.load(WORK / "face_fit.npz")
    v = F["v_fit"]
    cam = Cam.from_dict(json.loads(str(F["cam"])))
    s, R, t = float(F["sim_s"]), F["sim_R"], F["sim_t"]
    A = np.load(WORK / "analysis.npz")
    lm, cls = A["lm"].astype(np.float64), A["cls"]
    photo = load_rgb(WORK / "photo_rect.png")
    M = np.c_[s * R, t]

    mh = MH()
    base = mh.base()
    skin = skin_part(base)
    vm = v * 0.1
    vs = vm[skin.src_index]
    skin_albedo = load_rgb(WORK / "skin_albedo.png")
    head_mask = F["mask"]

    # ---------------- 1. short02, re-volumised
    P = proxy_part(mh, HAIR)
    hv0 = P.proxy.fit(v) * 0.1               # proxy vertex positions (metres)
    htex = load_rgba(texture_of(P))
    # scalp reference: skin vertices of the head
    head_ids = np.nonzero(head_mask[: len(base.v)] > 0.5)[0]
    head_ids = head_ids[np.isin(head_ids, skin.src_index)]
    sn = vertex_normals(vs, skin.tris)
    acc = np.zeros((len(base.v), 3))
    np.add.at(acc, skin.src_index, sn)
    bn = acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-9)
    tree = cKDTree(vm[head_ids])
    d, j = tree.query(hv0)
    near_ids = head_ids[j]
    nrm = bn[near_ids]
    h = np.maximum(((hv0 - vm[near_ids]) * nrm).sum(1), 0)

    # photo head silhouette (hair + face + ears + neck), smoothed, in the render frame
    sil_p = ((cls == 1) | (cls == 2) | (cls == 3)).astype(np.uint8)
    sil_p = cv2.morphologyEx(sil_p, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    sil_p = cv2.warpAffine(sil_p, M, (cam.W, cam.H), flags=cv2.INTER_NEAREST).astype(bool)
    head_c3 = vm[head_ids].mean(0)
    c_img = cam.project(head_c3[None])[0]
    depth_c = c_img[2]
    angles = np.arange(-20, 201, 2.0)
    skinL = dict(v=vs, tris=skin.tris, uv=skin.uv, tex=skin_albedo)

    def hair_layer(hv):
        return dict(v=hv[P.src_index], tris=P.tris, uv=P.uv, tex=htex, alpha="MASK", cutoff=0.45, two_sided=True)

    # displacement smoothing over the hair mesh (keeps short02's own shape, removes the lumps that lifting its
    # layers by different amounts would create); spatially close vertices (separate layers) are coupled too
    import scipy.sparse as sps
    pm_ = P.proxy.mesh
    e_ = np.r_[pm_.fv[:, [0, 1]], pm_.fv[:, [1, 2]], pm_.fv[:, [2, 3]], pm_.fv[:, [3, 0]]]
    Ah = sps.coo_matrix((np.ones(len(e_)), (e_[:, 0], e_[:, 1])), shape=(len(hv0),) * 2).tocsr()
    close = cKDTree(hv0).query_pairs(0.008, output_type="ndarray")
    Ah = Ah + sps.coo_matrix((np.ones(len(close)), (close[:, 0], close[:, 1])), shape=Ah.shape).tocsr()
    Ah = ((Ah + Ah.T) > 0).astype(np.float64)
    degh = np.maximum(np.asarray(Ah.sum(1)).ravel(), 1)

    def smooth_disp(d, n=25):
        for _ in range(n):
            d = 0.5 * d + 0.5 * (Ah @ d) / degh[:, None]
        return d

    r_p = ray_profile(sil_p, c_img[:2], angles)
    hv = hv0.copy()
    log = {"iters": []}
    for it in range(6):
        _, z, ids = swr.render(cam, [skinL, hair_layer(hv)])
        sil_r = np.isfinite(z)
        r_r = ray_profile(sil_r, c_img[:2], angles)
        delta_px = r_p - r_r
        delta_px = np.convolve(np.pad(delta_px, 3, mode="edge"), np.ones(7) / 7, mode="valid")
        delta_m = delta_px * depth_c / cam.f
        log["iters"].append({"iter": it, "mean_abs_px": float(np.abs(r_p - r_r).mean()), "max_px": float(np.abs(r_p - r_r).max())})
        print(f"hair silhouette iter {it}: mean |d| {np.abs(r_p - r_r).mean():.1f}px max {np.abs(r_p - r_r).max():.1f}px")
        if it == 5:
            break
        # per-vertex: image angle of the vertex around c_img
        pv = cam.project(hv)
        ang = np.degrees(np.arctan2(-(pv[:, 1] - c_img[1]), pv[:, 0] - c_img[0]))
        ang = np.where(ang < -90, ang + 360, ang)
        dm = np.interp(ang, angles, delta_m, left=0, right=0)
        # height above the scalp relative to the outer layer at that angle
        hcur = np.maximum(((hv - vm[near_ids]) * nrm).sum(1), 0)
        bins = np.clip(((ang - angles[0]) / 10).astype(int), 0, 1 + int((angles[-1] - angles[0]) / 10))
        href = np.ones_like(hcur) * 0.015
        for b in np.unique(bins):
            sel = bins == b
            if sel.sum() > 5:
                href[sel] = max(np.percentile(hcur[sel], 90), 0.006)
        gain = np.clip(hcur / href, 0, 1.3)
        hv = hv0 + smooth_disp(hv + nrm * (dm * gain)[:, None] - hv0)
    hair_fit = hv

    # ---------------- 2. photo relief layer
    alpha, Fcol, hairmask = photo_matte(photo, cls, lm)
    hmed = np.median(Fcol[hairmask & (photo.mean(-1) < 0.25)], 0)
    # albedo scale like the short02 hair (the photo's hair is lit and exposed); keep the photo's relative strand
    # detail, desaturate a little (thin strands pick up the skin's warmth in the photo)
    gray = Fcol.mean(-1, keepdims=True)
    Fcol = 0.7 * Fcol + 0.3 * gray
    Fcol = Fcol * (0.13 / max(float(hmed.mean()), 1e-3))
    rgba = np.dstack([Fcol, alpha])
    save_rgb(WORK / "hair_front_alpha.png", np.repeat(alpha[..., None], 3, -1))
    from PIL import Image
    Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(WORK / "hair_front_rgba.png")
    # alpha in the render frame
    a_r = cv2.warpAffine(alpha, M, (cam.W, cam.H), flags=cv2.INTER_LINEAR)
    # depth of the front-most surface (skin + re-volumised hair) and what it is
    _, z, ids = swr.render(cam, [skinL, hair_layer(hair_fit)])
    region = cv2.dilate((a_r > 0.02).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    geo = np.isfinite(z)
    off = np.where(ids == 1, 0.003, 0.006).astype(np.float32)      # 3 mm over hair, 6 mm over skin
    off = cv2.GaussianBlur(off, (0, 0), 6)
    zf = np.where(geo, z - off, 0).astype(np.float32)
    rim = geo & ~cv2.erode(geo.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    zfill = push_pull(zf[..., None].repeat(3, -1), rim.astype(np.float32))[..., 0]
    # outside the geometry (flyaways beyond the silhouette): continue the rim depth, slightly behind
    zc = np.where(geo, zf, zfill)
    # smooth strongly (no ledge where the fringe leaves the hair mass), but never closer than 4 mm to the skin
    zc = cv2.GaussianBlur(zc, (0, 0), 9.0)
    # in front of the skin by >= 4 mm and in front of the re-volumised hair by >= 2 mm (so the photo hair is what
    # the photo camera sees)
    zskin = np.where(geo & (ids == 0), z - 0.004, np.where(geo, z - 0.009, np.inf)).astype(np.float32)  # hair: clear the 7 mm fur shells
    zc = np.minimum(zc, zskin)
    zc = cv2.GaussianBlur(zc, (0, 0), 1.0)
    zc = np.minimum(zc, zskin)
    step = 4
    ys, xs = np.mgrid[0:cam.H:step, 0:cam.W:step]
    gh, gw = ys.shape
    use = region[ys, xs]
    # quads whose 4 corners are in the region
    q = use[:-1, :-1] & use[1:, :-1] & use[:-1, 1:] & use[1:, 1:]
    vid = -np.ones((gh, gw), np.int64)
    corner = np.zeros((gh, gw), bool)
    corner[:-1, :-1] |= q
    corner[1:, :-1] |= q
    corner[:-1, 1:] |= q
    corner[1:, 1:] |= q
    vid[corner] = np.arange(corner.sum())
    gx, gy = xs[corner].astype(float) + 0.5, ys[corner].astype(float) + 0.5
    gd = zc[ys[corner], xs[corner]]
    Xc = np.stack([(gx - cam.cx) / cam.f * gd, -(gy - cam.cy) / cam.f * gd, -gd], 1)
    Xw = (Xc - cam.t) @ cam.R  # R^T (Xc - t)
    qi, qj = np.nonzero(q)
    a_, b_, c_, d_ = vid[qi, qj], vid[qi, qj + 1], vid[qi + 1, qj + 1], vid[qi + 1, qj]
    ftris = np.r_[np.c_[a_, d_, c_], np.c_[a_, c_, b_]]
    # uv = photo pixel / 1024 (the texture is the photo-space RGBA)
    pp = ((np.c_[gx, gy] - t) @ R) / s
    fuv = pp / np.array([photo.shape[1], photo.shape[0]])
    print(f"relief layer: {len(Xw)} verts, {len(ftris)} tris")
    # fade the layer where its surface is seen edge-on by the photo camera (the photo would be smeared there;
    # the re-volumised short02 underneath carries those parts)
    rn = vertex_normals(Xw, ftris)
    # smooth the normals over the layer: the fold where the fringe leaves the hair mass is steep but narrow and
    # must not fade (it would open a thin light line); only broad edge-on regions fade
    import scipy.sparse as _sp
    e_r = np.r_[ftris[:, [0, 1]], ftris[:, [1, 2]], ftris[:, [2, 0]]]
    Ar = _sp.coo_matrix((np.ones(len(e_r)), (e_r[:, 0], e_r[:, 1])), shape=(len(Xw),) * 2).tocsr()
    Ar = ((Ar + Ar.T) > 0).astype(np.float64)
    dr = np.maximum(np.asarray(Ar.sum(1)).ravel(), 1)
    for _ in range(12):
        rn = 0.5 * rn + 0.5 * (Ar @ rn) / dr[:, None]
    rn /= np.maximum(np.linalg.norm(rn, axis=1, keepdims=True), 1e-9)
    dcam = cam.eye()[None] - Xw
    dcam /= np.linalg.norm(dcam, axis=1, keepdims=True)
    fade_v = smoothstep(0.12, 0.40, np.abs((rn * dcam).sum(1)))
    ti_f, ba_f, _ = rasterize(fuv * np.array([photo.shape[1], photo.shape[0]]), ftris, photo.shape[1], photo.shape[0])
    fade_img = np.ones(alpha.shape)
    mf = ti_f >= 0
    fade_img[mf] = interp(fade_v[:, None], ftris, ti_f, ba_f)[mf][:, 0]
    fade_img = cv2.GaussianBlur(fade_img.astype(np.float32), (0, 0), 2)
    # over the hair mass the photo is baked into short02 itself (below); the relief layer keeps the fringe over the
    # forehead, a 14 px band where the fringe roots into the hair mass, and flyaways beyond the silhouette
    keep = (ids != 1).astype(np.uint8)
    keep = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (71, 71)))   # covers short02's front rim
    keep_w = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 8)
    Minv = cv2.invertAffineTransform(M)
    keep_p = cv2.warpAffine(keep_w, Minv, (photo.shape[1], photo.shape[0]), flags=cv2.INTER_LINEAR, borderValue=1)
    a_fin = alpha * fade_img * keep_p
    # drop isolated specks (small alpha islands not connected to the hair mass)
    n_, lab_, st_, _ = cv2.connectedComponentsWithStats((a_fin > 0.15).astype(np.uint8), 8)
    small = np.isin(lab_, [i for i in range(1, n_) if st_[i, cv2.CC_STAT_AREA] < 60])
    a_fin[cv2.dilate(small.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)] = 0
    rgba[..., 3] = a_fin
    Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(WORK / "hair_front_rgba.png")
    z_front = z

    # ---------------- 3. scalp darkening under the hair: a skin vertex is "under hair" when a ray along its normal
    # hits the re-volumised short02 where its texture is opaque (alpha > 0.5)
    import trimesh
    from swr import sample
    hm_tri = trimesh.Trimesh(hair_fit[P.src_index], P.tris, process=False)
    ray = trimesh.ray.ray_triangle.RayMeshIntersector(hm_tri)
    sn_u = bn[skin.src_index]
    cand = np.nonzero(head_mask[skin.src_index] > 0.3)[0]
    origins = vs[cand] + sn_u[cand] * 0.0005
    locs, ridx, tidx = ray.intersects_location(origins, sn_u[cand], multiple_hits=True)
    cover = np.zeros(len(vs))
    if len(locs):
        tri = P.tris[tidx]
        a_, b_, c_ = hm_tri.vertices[tri[:, 0]], hm_tri.vertices[tri[:, 1]], hm_tri.vertices[tri[:, 2]]
        bc = trimesh.triangles.points_to_barycentric(np.stack([a_, b_, c_], 1), locs)
        uvh = (P.uv[tri] * bc[:, :, None]).sum(1)
        al = sample(htex, uvh)[:, 3]
        dist = np.linalg.norm(locs - origins[ridx], axis=1)
        hit = (al > 0.5) & (dist < 0.08)
        np.maximum.at(cover, cand[ridx[hit]], 1.0)
    # smooth over the mesh a little (per base vertex average over one ring, twice)
    cb = np.zeros(len(base.v))
    np.maximum.at(cb, skin.src_index, cover)
    tb = skin.src_index[skin.tris]
    for _ in range(3):
        acc2 = np.zeros(len(base.v))
        cnt = np.zeros(len(base.v))
        for k in range(3):
            np.add.at(acc2, tb[:, k], cb[tb[:, (k + 1) % 3]] + cb[tb[:, (k + 2) % 3]])
            np.add.at(cnt, tb[:, k], 2)
        cb = 0.5 * cb + 0.5 * acc2 / np.maximum(cnt, 1)
    cover = cb[skin.src_index]
    # never darken skin that the photo camera sees as bare forehead / temple skin (between the fringe strands)
    pvs = cam.project(vs)
    _, _, z_sk = rasterize(pvs[:, :2], skin.tris, cam.W, cam.H, Z=pvs[:, 2])   # skin only: hair does not occlude
    vis_s = pvs[:, 2] <= z_sk[np.clip(pvs[:, 1].astype(int), 0, cam.H - 1), np.clip(pvs[:, 0].astype(int), 0, cam.W - 1)] + 0.003
    qs = ((pvs[:, :2] - t) @ R) / s
    from bake_texture import bilinear as _bil
    # the carved fringe zone (forehead_carve) stays bare forehead skin; everywhere else under the hair is scalp
    zone_ph, ycarve, ybrow = forehead_zone(photo, cls, lm)
    # (slightly inside the carved edge, so the skin under the shell's cut edge is root-coloured, not a light line)
    skin_ph2 = cv2.erode(zone_ph, np.ones((7, 7), np.uint8)) * ((cls == 3) | (cls == 1) | (cls == 2))
    skin_ph2 = cv2.GaussianBlur(skin_ph2.astype(np.float32), (0, 0), 2.0)
    # behind the dense root band of the fringe (the first ~1 cm under the carved edge, where the photo shows opaque
    # hair) the skin gets the root colour too, fading out downwards: gaps between the strand roots then read as
    # more hair behind, not as bright forehead slivers; the photo's real skin gaps (low matte) stay skin
    yy_ = np.arange(cls.shape[0])[:, None]
    dy_c = yy_ - np.where(np.isfinite(ycarve), ycarve, 1e9)[None, :]
    ga_ph = cv2.GaussianBlur(guide_alpha(photo, cls, lm), (0, 0), 3.0)
    root_band = np.maximum(ga_ph * (1 - smoothstep(6.0, 26.0, dy_c)), 1 - smoothstep(2.0, 9.0, dy_c)) * (dy_c > -20)
    skin_ph2 = skin_ph2 * (1 - np.clip(root_band, 0, 1))
    # further down, the forehead under the photo's dense fringe gets a soft shadow of it (not scalp colour): seen
    # through the gaps between the ribbon strands it keeps the photo's fringe density; from other angles it reads
    # as the fringe's own shadow on the forehead
    fr_shadow = np.clip(0.5 * cv2.GaussianBlur(ga_ph, (0, 0), 3.0) * ((dy_c > 0) & (yy_ < ybrow + 30))
                        * (1 - np.clip(root_band, 0, 1)), 0, 0.5)
    facing_s = (sn_u * ((cam.eye()[None] - vs) / np.linalg.norm(cam.eye()[None] - vs, axis=1, keepdims=True))).sum(1) > 0.3
    bare = vis_s * facing_s * _bil(skin_ph2, qs[:, 0], qs[:, 1])
    cover = cover * np.clip(1 - 1.5 * bare, 0, 1)
    print(f"scalp cover: {int((cb[skin.src_index] > 0.5).sum())} verts; bare-forehead exclusions: {int((bare > 0.3).sum())} (vis {int(vis_s.sum())}, facing {int(facing_s.sum())}, photo-skin {int((_bil(skin_ph2, qs[:, 0], qs[:, 1]) > 0.3).sum())})")
    tri_img, bary, _ = rasterize(skin.uv * skin_albedo.shape[0], skin.tris, skin_albedo.shape[1], skin_albedo.shape[0])
    cv_img = interp(cover[:, None], skin.tris, tri_img, bary)[..., 0]
    cv_img = cv2.GaussianBlur(cv_img.astype(np.float32), (0, 0), 3)
    root = np.median(Fcol[hairmask & (photo.mean(-1) < 0.25)], 0)
    root_col = np.clip(root * 0.9 + 0.02, 0, 1)
    rng = np.random.default_rng(3)
    grain = cv2.GaussianBlur(rng.normal(0, 1, skin_albedo.shape[:2]).astype(np.float32), (0, 0), 1.2)
    scalp = np.clip(root_col[None, None] * (1 + 0.25 * grain[..., None]), 0, 1)
    k = np.clip(cv_img * 1.1, 0, 1)[..., None]
    skin_h = skin_albedo * (1 - k) + scalp * k
    # fringe shadow on the forehead skin (photo-visible, frontal texels only)
    sh_v = vis_s * facing_s * _bil(fr_shadow.astype(np.float32), qs[:, 0], qs[:, 1])
    sh_img = cv2.GaussianBlur(interp(sh_v[:, None], skin.tris, tri_img, bary)[..., 0].astype(np.float32), (0, 0), 2)
    skin_h = skin_h * (1 - sh_img[..., None])
    save_rgb(WORK / "skin_albedo_hair.png", skin_h)

    # recolour short02 to the photo's hair colour (keep its strand contrast and alpha)
    lum = htex[..., :3] @ np.array([0.3, 0.59, 0.11])
    lum_n = lum / max(np.percentile(lum[htex[..., 3] > 0.5], 90), 1e-3)
    hi = np.median(Fcol[hairmask & (photo.mean(-1) < 0.35)], 0)
    # albedo, not the photo's exposed appearance: black hair reflects little; the sheen comes from the specular
    dark = hi / max(hi.mean(), 1e-3) * 0.075
    black = np.clip(dark[None, None] * (0.4 + 1.25 * lum_n[..., None]), 0, 1)
    # strand direction from the texture's structure tensor -> glTF KHR_materials_anisotropy texture
    # (RG = direction in tangent space, u right / v down, B = strength = coherence)
    gx = cv2.Sobel(lum.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(lum.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
    Jxx = cv2.GaussianBlur(gx * gx, (0, 0), 6)
    Jyy = cv2.GaussianBlur(gy * gy, (0, 0), 6)
    Jxy = cv2.GaussianBlur(gx * gy, (0, 0), 6)
    th = 0.5 * np.arctan2(2 * Jxy, Jxx - Jyy) + np.pi / 2   # strands run across the gradient
    lam_d = np.sqrt((Jxx - Jyy) ** 2 + 4 * Jxy ** 2)
    coh = lam_d / np.maximum(Jxx + Jyy, 1e-9)
    aniso = np.dstack([np.cos(th) * 0.5 + 0.5, np.sin(th) * 0.5 + 0.5, np.clip(coh * 1.5, 0, 1)])
    save_rgb(WORK / "short02_aniso.png", aniso)
    # the photo's hair baked onto the re-volumised short02 wherever the photo camera sees it (frontal texels)
    HT = htex.shape[0]
    ti_h, ba_h, _ = rasterize(P.uv * HT, P.tris, HT, HT)
    mh_ = ti_h >= 0
    hvu = hair_fit[P.src_index]
    Xh = interp(hvu, P.tris, ti_h, ba_h)[mh_]
    Nh = interp(vertex_normals(hvu, P.tris), P.tris, ti_h, ba_h)[mh_]
    Nh /= np.maximum(np.linalg.norm(Nh, axis=1, keepdims=True), 1e-9)
    ph = cam.project(Xh)
    pxi = np.clip(ph[:, 0].astype(int), 0, cam.W - 1)
    pyi = np.clip(ph[:, 1].astype(int), 0, cam.H - 1)
    vis_h = ph[:, 2] <= z_front[pyi, pxi] + 0.004
    dh = cam.eye()[None] - Xh
    dh /= np.linalg.norm(dh, axis=1, keepdims=True)
    cos_h = np.abs((Nh * dh).sum(1))
    qh = ((ph[:, :2] - t) @ R) / s
    from bake_texture import bilinear
    w_h = smoothstep(0.30, 0.65, cos_h) * vis_h * bilinear(alpha, qh[:, 0], qh[:, 1])
    col_h = bilinear(Fcol, qh[:, 0], qh[:, 1])
    Wimg = np.zeros((HT, HT))
    Wimg[mh_] = w_h
    Cimg = np.zeros((HT, HT, 3))
    Cimg[mh_] = col_h
    Wimg = cv2.GaussianBlur(Wimg.astype(np.float32), (0, 0), 2)
    Cimg = push_pull(Cimg.astype(np.float32), (Wimg > 0.02).astype(np.float32))
    black = black * (1 - Wimg[..., None]) + Cimg * Wimg[..., None]
    # carve short02 over the fringe zone (forehead_carve): every hair texel that projects into the zone and lies in
    # front of the forehead skin (all card layers, not only the visible one, so no inner layer is left hanging over
    # the forehead; texels on the back of the head project there too but lie behind the skin).  The fringe itself
    # is rebuilt from ribbon strands (build_strands.py), which root under the carved edge.
    pz_s = cam.project(vs)
    _, _, z_sk = rasterize(pz_s[:, :2], skin.tris, cam.W, cam.H, Z=pz_s[:, 2])
    in_front = ph[:, 2] < z_sk[pyi, pxi]
    carve_v = in_front * bilinear(zone_ph, qh[:, 0], qh[:, 1])
    Cv = np.zeros((HT, HT), np.float32)
    Cv[mh_] = carve_v
    Cv = cv2.GaussianBlur(Cv, (0, 0), 2.5)
    a_short = htex[..., 3] * np.clip(1 - 1.4 * Cv, 0, 1)
    short_rgba = np.dstack([black, a_short])
    Image.fromarray((short_rgba * 255 + 0.5).astype(np.uint8), "RGBA").save(WORK / "short02_black.png")
    # the fur shells (export_glb.py: the same cards pushed 3 / 7 mm out) are carved a little further back: their
    # cut edge would otherwise overhang the forehead as a sparse grey rim in front of the shell's own edge
    Cv_f = cv2.GaussianBlur(cv2.dilate((Cv > 0.15).astype(np.uint8), np.ones((25, 25), np.uint8)).astype(np.float32), (0, 0), 4)
    a_fur = htex[..., 3] * np.clip(1 - 1.4 * np.maximum(Cv, Cv_f), 0, 1)
    Image.fromarray((np.dstack([black, a_fur]) * 255 + 0.5).astype(np.uint8), "RGBA").save(WORK / "short02_fur.png")

    np.savez_compressed(WORK / "hair_fit.npz", short02_v=hair_fit, short02_v0=hv0, relief_v=Xw, relief_tris=ftris,
                        relief_uv=fuv, root_col=root_col, hair_col=hi, ycarve=ycarve,
                        ybrow=ybrow)
    (WORK / "hair_log.json").write_text(json.dumps(log, indent=1))

    # ---------------- check render: photo camera, 3/4, profile, back
    L = [dict(v=vs, tris=skin.tris, uv=skin.uv, tex=skin_h, ambient=0.7),
         dict(v=hair_fit[P.src_index], tris=P.tris, uv=P.uv, tex=short_rgba, alpha="MASK", cutoff=0.45, two_sided=True, ambient=0.6),
         dict(v=Xw, tris=ftris, uv=fuv, tex=rgba, alpha="BLEND", two_sided=True, light=False)]
    E = proxy_part(mh, "eyes/high-poly/high-poly.mhclo")
    cc = E.uv[E.tris].mean(1)
    L.insert(1, dict(v=E.proxy.fit(v)[E.src_index] * 0.1, tris=E.tris[~((cc[:, 0] > 0.8) & (cc[:, 1] > 0.8))], uv=E.uv,
                     tex=load_rgb(WORK / "eye_albedo.png"), ambient=0.75))
    imgs = [cv2.warpAffine(photo, M, (cam.W, cam.H))]
    img, _, _ = swr.render(cam, L, bg=(0.2, 0.2, 0.2))
    imgs.append(img)
    tgt = head_c3 + np.array([0, -0.02, 0])
    for angd in (35, 90, 180):
        ar = np.radians(angd)
        c2 = Cam.look_at(tgt + 1.3 * np.array([np.sin(ar), 0, np.cos(ar)]), tgt, cam.f * 0.9, 1024, 1024)
        img, _, _ = swr.render(c2, L, bg=(0.2, 0.2, 0.2))
        imgs.append(img)
    row = np.hstack(imgs)[120:900]
    save_rgb(CHECK / "hair_preview.jpg", cv2.resize(row, (row.shape[1] // 2, row.shape[0] // 2)))


if __name__ == "__main__":
    main()
