"""Procedural hair cards for the fitted MakeHuman head: black, messy, medium-short, a curly fringe over the
forehead.  Everything is generated from the head geometry plus (optionally) the photo's hair silhouette.

    hair = grow_hair(v_dm, base, style, photo_sil=...)   # guide strands + clumped children (decimetres)
    mesh = ribbons(hair, style)                          # alpha-textured ribbon cards (tapered)
    tex  = strand_texture(style)                         # RGBA strand atlas

Method
  * scalp = the skin region MakeHuman's short02 hair is fitted to (its reference vertices), smoothed over
    the mesh and thresholded -> natural hairline, around the ears, nape;
  * a signed distance field of the head (1.5 mm voxels) lets strands glide over the head at a chosen
    height instead of cutting through it;
  * flow: hair radiates from a whorl at the back of the crown (forward over the top into the fringe,
    down the sides and back); gravity takes over once a strand leaves the scalp;
  * volume: each strand keeps a layer height = lambda x local thickness; the thickness around the
    silhouette is measured from the photo's hair mask (front view), elsewhere it is interpolated;
  * the fringe stops around the brows with ragged lengths, sides stop over the top of the ears, the back
    at the nape; strands carry a per-guide wave that grows towards the tip (curly ends);
  * each guide spawns children in a small disk that converge towards the tip (piecey clumps).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import scipy.ndimage as ndi
import scipy.sparse as sp


@dataclass
class HairStyle:
    seed: int = 7
    n_guides: int = 2600
    children: int = 3                 # children per guide (+ the guide itself)
    step: float = 0.022               # dm (2.2 mm)
    max_len: float = 1.45             # dm
    clump_radius: float = 0.045       # dm
    clump: tuple = (0.6, 0.9)         # tip convergence range
    thickness_top: float = 0.24       # dm, outer hair surface above the scalp on top
    thickness_side: float = 0.18
    thickness_back: float = 0.15
    thickness_nape: float = 0.05
    fringe_height: float = 0.07       # dm above the forehead skin
    fringe_stop: tuple = (-0.2, 0.3)  # dm above the brow line: where fringe strands end (random range)
    side_stop: tuple = (-0.02, 0.22)  # dm relative to the ear top
    wave_amp: tuple = (0.005, 0.016)  # dm
    wave_len: tuple = (0.32, 0.6)     # dm
    tip_curl: float = 1.2             # extra curl at the tips (fraction of wave amp)
    fringe_curl: float = 2.2          # the fringe tips curl more (the photo's curly fringe)
    width_root: float = 0.05          # dm card width at the root
    width_tip: float = 0.016
    flyaways: int = 90                # thin frizzy strands sticking out on top
    whorl: tuple = (0.12, 0.62, -0.78)  # direction from the head centre (x, y, z), normalised
    sweep: float = 0.10               # sideways sweep of the fringe (character's left = +x)
    whorl_twist: float = 0.9          # spiral around the crown whorl
    forward_comb: float = 1.6         # top/front hair combed forward into the fringe
    hug_min: float = 0.3              # side/back hair thickness at the ends (fraction of full volume)
    fringe_keep: float = 0.55         # fraction of fringe guides kept (gaps between the locks)
    fringe_wave: tuple = (0.012, 0.026)  # dm, S-curls of the fringe locks
    fringe_clump_radius: float = 0.07
    fringe_clump: tuple = (0.85, 0.97) # fringe locks converge more (separated curly locks)
    color_srgb: tuple = (0.05, 0.041, 0.036)


# ----------------------------------------------------------------------------- mesh helpers
def mesh_adjacency(fv, n):
    k = np.where(fv[:, 3] == fv[:, 2], 3, 4)
    a, b = [], []
    for j in range(4):
        m = j < k
        jn = np.where(j + 1 < k, j + 1, 0)
        a.append(fv[m, j])
        b.append(fv[np.nonzero(m)[0], jn[m]])
    a = np.concatenate(a)
    b = np.concatenate(b)
    A = sp.csr_matrix((np.ones(2 * len(a)), (np.r_[a, b], np.r_[b, a])), shape=(n, n))
    A.data[:] = 1.0
    return A


def scalp_field(mh, base, v, proxy="hair/short02/short02.mhclo", smooth_iters=6):
    """Per-vertex scalp membership in [0,1] from a MakeHuman hair proxy's reference vertices."""
    px = mh.proxy(proxy)
    s = np.zeros(len(v))
    s[np.unique(px.ref.ravel())] = 1.0
    body = base.fgroup == base.groups.index("body")
    A = mesh_adjacency(base.fv[body], len(v))
    deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
    for _ in range(smooth_iters):
        s = 0.5 * s + 0.5 * (A @ s) / deg
    return s


# ----------------------------------------------------------------------------- SDF
class SDF:
    def __init__(self, v, tris, lo, hi, h=0.015):
        self.lo = np.asarray(lo, float)
        self.h = h
        shape = np.ceil((np.asarray(hi) - self.lo) / h).astype(int) + 1
        self.shape = shape
        surf = np.zeros(shape, bool)
        # dense surface samples (spacing < voxel) on every triangle inside the box
        P = v[tris]
        c = P.mean(1)
        keep = np.all((c > self.lo - 0.1) & (c < np.asarray(hi) + 0.1), 1)
        P = P[keep]
        e = np.maximum(np.linalg.norm(P[:, 1] - P[:, 0], axis=1), np.linalg.norm(P[:, 2] - P[:, 0], axis=1))
        nsub = np.clip(np.ceil(e / (0.5 * h)).astype(int), 1, 40)
        for ns in np.unique(nsub):
            sel = P[nsub == ns]
            i, j = np.meshgrid(np.arange(ns + 1), np.arange(ns + 1), indexing="ij")
            ok = (i + j) <= ns
            a, b = (i[ok] / ns)[None, :, None], (j[ok] / ns)[None, :, None]
            pts = sel[:, None, 0] * (1 - a - b) + sel[:, None, 1] * a + sel[:, None, 2] * b
            idx = np.round((pts.reshape(-1, 3) - self.lo) / h).astype(int)
            ok2 = np.all((idx >= 0) & (idx < shape), 1)
            surf[tuple(idx[ok2].T)] = True
        wall = surf.copy()
        wall[:, 0, :] = True        # close the neck at the bottom of the box
        inside = ndi.binary_fill_holes(wall) & ~surf
        inside[:, 0, :] = False
        d_out = ndi.distance_transform_edt(~(inside | surf)) * h
        d_in = ndi.distance_transform_edt(~(~inside)) * h
        self.d = np.where(inside, -d_in, d_out).astype(np.float32)
        g = np.gradient(self.d, h)
        self.g = [x.astype(np.float32) for x in g]

    def _coords(self, p):
        return ((np.asarray(p) - self.lo) / self.h).T

    def __call__(self, p):
        return ndi.map_coordinates(self.d, self._coords(p), order=1, mode="nearest")

    def grad(self, p):
        c = self._coords(p)
        g = np.stack([ndi.map_coordinates(gi, c, order=1, mode="nearest") for gi in self.g], 1)
        return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)


# ----------------------------------------------------------------------------- strands
@dataclass
class HeadFrame:
    c: np.ndarray        # head centre (dm)
    R: float             # skull radius
    brow_y: float
    ear_top_y: float
    nape_y: float
    face_z: float


def head_frame(base, v, scalp):
    from face_fit import vertex_groups
    g = vertex_groups(base)
    sv = v[scalp > 0.5]
    # least-squares sphere through the scalp
    A = np.c_[2 * sv, np.ones(len(sv))]
    b = (sv ** 2).sum(1)
    x = np.linalg.lstsq(A, b, rcond=None)[0]
    c = x[:3]
    c[0] = 0.0
    R = np.sqrt(x[3] + (x[:3] ** 2).sum())
    eye = 0.5 * (v[g["helper-l-eye"]].mean(0) + v[g["helper-r-eye"]].mean(0))
    return HeadFrame(c, R, brow_y=eye[1] + 0.16, ear_top_y=eye[1] + 0.12, nape_y=eye[1] - 0.36, face_z=eye[2])


def tangent(vec, n):
    t = vec - (vec * n).sum(1, keepdims=True) * n
    return t / np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)


def sample_roots(rng, v, tris, scalp, n):
    """Area-weighted random points on the scalp (triangles with scalp > 0.5 at all corners)."""
    s = scalp[tris].min(1)
    keep = s > 0.5
    T = tris[keep]
    P = v[T]
    area = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    ti = rng.choice(len(T), n, p=area / area.sum())
    r1, r2 = rng.random(n), rng.random(n)
    flip = r1 + r2 > 1
    r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
    p = P[ti, 0] * (1 - r1 - r2)[:, None] + P[ti, 1] * r1[:, None] + P[ti, 2] * r2[:, None]
    return p


def thickness_at(dirs, style, side_profile=None):
    """Outer hair thickness (dm) for unit directions from the head centre.  side_profile: optional
    callable elevation(rad) -> thickness measured from the photo silhouette at the sides / top."""
    el = np.arcsin(np.clip(dirs[:, 1], -1, 1))
    az = np.arctan2(dirs[:, 0], dirs[:, 2])            # 0 = front, +-pi/2 sides, pi back
    top = style.thickness_top
    side = style.thickness_side if side_profile is None else side_profile(el)
    back = style.thickness_back
    # blend: top above ~55 deg elevation; sides/back by azimuth
    fb = 0.5 * (1 - np.cos(az))                         # 0 front .. 1 back
    ring = side * (1 - np.clip((fb - 0.5) * 2, 0, 1)) + back * np.clip((fb - 0.5) * 2, 0, 1)
    ring = np.where(fb < 0.5, side, ring)
    w_top = np.clip((el - np.radians(35)) / np.radians(35), 0, 1)
    t = ring * (1 - w_top) + top * w_top
    # nape: thin
    w_nape = np.clip((np.radians(-5) - el) / np.radians(35), 0, 1) * np.clip((fb - 0.35) / 0.4, 0, 1)
    return t * (1 - w_nape) + style.thickness_nape * w_nape


def grow_guides(rng, roots, sdf: SDF, fr: HeadFrame, style: HairStyle, scalp_at, side_profile=None):
    """Integrate guide strands over the head.  Returns list of (K_i,3) polylines."""
    n = len(roots)
    W = fr.c + fr.R * np.asarray(style.whorl) / np.linalg.norm(style.whorl)
    nrm = sdf.grad(roots)
    d0 = roots - fr.c
    d0 /= np.linalg.norm(d0, axis=1, keepdims=True)
    H = thickness_at(d0, style, side_profile)
    lam = rng.random(n) ** 0.6 * 0.85 + 0.15
    h_goal = lam * H
    # region of each root decides where it ends: fringe at the brows, sides over the ear tops, back at the nape
    az = np.arctan2(d0[:, 0], d0[:, 2])
    front = np.abs(az) < np.radians(40)
    back = np.abs(az) > np.radians(115)
    stop_y = np.where(front, fr.brow_y + rng.uniform(*style.fringe_stop, n),
                      np.where(back, fr.nape_y + rng.uniform(0.02, 0.2, n), fr.ear_top_y + rng.uniform(*style.side_stop, n)))
    min_len = np.where(front, rng.uniform(0.15, 0.3, n), rng.uniform(0.16, 0.28, n))
    # roots at / below the nape hairline: short hair lying down, not a mullet
    near_nape = back & (roots[:, 1] < fr.nape_y + 0.25)
    min_len = np.where(near_nape, rng.uniform(0.04, 0.09, n), min_len)
    Lmax = style.max_len * rng.uniform(0.8, 1.0, n)
    P = roots + nrm * 0.004
    def comb(P, g):
        f = tangent(P - W, g)
        dw = np.linalg.norm(P - W, axis=1)
        f = f + style.whorl_twist * np.exp(-dw / 0.35)[:, None] * np.cross(g, f)
        # everything in front of the crown is combed forward into the fringe (no parting)
        wf = style.forward_comb * np.clip((P[:, 2] - (fr.c[2] - 0.35)) / 0.6, 0, 1) * np.clip((P[:, 1] - fr.ear_top_y) / 0.4, 0, 1)
        f = f + wf[:, None] * tangent(np.tile([0.0, -0.25, 1.0], (len(P), 1)), g)
        f[:, 0] += style.sweep * front
        return tangent(f, g)

    flow = comb(roots, nrm)
    dirp = tangent(flow + nrm * 0.9, nrm) * 0.5 + nrm * 0.5     # hair leaves the scalp at ~40-50 deg
    dirp /= np.linalg.norm(dirp, axis=1, keepdims=True)
    paths = [P.copy()]
    alive = np.ones(n, bool)
    s = np.zeros(n)
    noise_dir = rng.normal(size=(n, 3)) * 0.15
    for k in range(int(style.max_len / style.step) + 2):
        g = sdf.grad(P)
        dist = sdf(P)
        on_scalp = scalp_at(P)
        f = comb(P, g)
        grav = tangent(np.tile([0.0, -1.0, 0.0], (n, 1)), g)
        # gravity takes over as the strand leaves the scalp (fringe over the forehead, sides over the ears)
        wg = 0.25 + 1.6 * (1 - on_scalp) + 0.6 * np.clip(s / 0.8, 0, 1)
        new = 1.2 * dirp + 1.0 * f + wg[:, None] * grav + noise_dir
        # height controller: glide at the layer height (lower over bare skin: fringe lies on the forehead)
        goal = np.where(on_scalp > 0.5, h_goal, np.minimum(h_goal, style.fringe_height * (0.5 + lam)))
        # below the widest part of the skull the side / back hair falls in towards the head
        hug = np.clip((P[:, 1] - (fr.ear_top_y - 0.05)) / 0.45, style.hug_min, 1.0)
        goal = np.where(front, goal, goal * hug)
        goal = np.minimum(goal, 0.004 + s * 0.9)
        new = tangent(new, g) + np.clip((goal - dist) * 12.0, -1.5, 1.5)[:, None] * g
        new /= np.linalg.norm(new, axis=1, keepdims=True)
        Pn = P + style.step * new
        # never enter the head
        dn = sdf(Pn)
        Pn = Pn + np.maximum(0.003 - dn, 0)[:, None] * sdf.grad(Pn)
        dirp = (Pn - P) / style.step
        dirp /= np.maximum(np.linalg.norm(dirp, axis=1, keepdims=True), 1e-9)
        s = s + style.step * alive
        P = np.where(alive[:, None], Pn, P)
        paths.append(P.copy())
        stop = (P[:, 1] < stop_y) & (s > min_len)
        alive &= ~stop & (s < Lmax)
        if not alive.any():
            break
    paths = np.stack(paths, 1)                              # (n, K, 3)
    out = []
    for i in range(n):
        seg = np.linalg.norm(np.diff(paths[i], axis=0), axis=1)
        K = int(np.nonzero(seg > 1e-6)[0].max() + 2) if (seg > 1e-6).any() else 2
        out.append(paths[i, :K])
    return out, lam, front


def resample(path, step):
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    if s[-1] < step:
        return path[[0, -1]]
    t = np.linspace(0, s[-1], max(int(round(s[-1] / step)) + 1, 2))
    return np.stack([np.interp(t, s, path[:, j]) for j in range(3)], 1)


def frames(path, sdf):
    t = np.gradient(path, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    n = sdf.grad(path)
    b = np.cross(t, n)
    b /= np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-9)
    n = np.cross(b, t)
    return t, n, b


def add_wave(rng, path, sdf, style, amp=None, curl=None):
    """Per-strand wave in the (b, n) plane, growing towards the tip; tips curl."""
    L = len(path)
    if L < 3:
        return path
    t, n, b = frames(path, sdf)
    s = np.linspace(0, 1, L)
    seglen = np.linalg.norm(np.diff(path, axis=0), axis=1).sum()
    A = rng.uniform(*style.wave_amp) if amp is None else amp
    lw = rng.uniform(*style.wave_len)
    ph = rng.uniform(0, 2 * np.pi)
    arc = s * seglen
    env = np.clip(s / 0.35, 0, 1) ** 1.5 * (0.6 + 0.4 * s)
    wb = A * env * np.sin(2 * np.pi * arc / lw + ph)
    wn = 0.45 * A * env * np.cos(2 * np.pi * arc / lw + ph)
    # C-curl at the tip (towards the head and sideways)
    c = style.tip_curl * A * (curl if curl is not None else 1.0)
    tip = np.clip((s - 0.7) / 0.3, 0, 1) ** 2
    wn = wn + c * tip * 0.4
    wb = wb + c * tip * 1.3 * rng.choice([-1, 1])
    out = path + wb[:, None] * b + wn[:, None] * n
    d = sdf(out)
    return out + np.maximum(0.003 - d, 0)[:, None] * sdf.grad(out)


def grow_hair(mh, base, v, style: HairStyle = HairStyle(), side_profile=None, log=print):
    rng = np.random.default_rng(style.seed)
    body = base.fgroup == base.groups.index("body")
    tv, _ = base.triangles(body)
    scalp = scalp_field(mh, base, v)
    fr = head_frame(base, v, scalp)
    lo = fr.c - np.array([fr.R + 0.6, fr.R + 1.4, fr.R + 0.7])
    hi = fr.c + np.array([fr.R + 0.6, fr.R + 0.6, fr.R + 0.9])
    sdf = SDF(v, tv, lo, hi)
    log(f"  head centre {np.round(fr.c, 3).tolist()} R {fr.R:.3f} dm; sdf grid {sdf.shape.tolist()}")
    from scipy.spatial import cKDTree
    sv_idx = np.nonzero(scalp > 0.05)[0]
    near_tree = cKDTree(v[np.unique(tv)])
    near_ids = np.unique(tv)

    def scalp_at(p):
        _, i = near_tree.query(p, k=1)
        return scalp[near_ids[i]]

    roots = sample_roots(rng, v, tv, scalp, int(style.n_guides * 1.25))
    d = (roots - fr.c) / np.linalg.norm(roots - fr.c, axis=1, keepdims=True)
    az = np.abs(np.arctan2(d[:, 0], d[:, 2]))
    sideburn = (roots[:, 1] < fr.ear_top_y + 0.08) & (az > np.radians(40)) & (az < np.radians(115))
    nape = (roots[:, 1] < fr.nape_y + 0.18) & (az >= np.radians(115))
    front_root = (az < np.radians(40)) & (rng.random(len(roots)) > style.fringe_keep) & \
        ((roots - fr.c)[:, 1] < 0.8 * fr.R)
    roots = roots[~(sideburn | nape | front_root)][: style.n_guides]
    guides, lam, is_front = grow_guides(rng, roots, sdf, fr, style, scalp_at, side_profile)
    guides = [resample(g, style.step) for g in guides]
    strands = []
    for gi, g in enumerate(guides):
        if len(g) < 3:
            continue
        gw = add_wave(rng, g, sdf, style, curl=style.fringe_curl if is_front[gi] else 1.0,
                      amp=rng.uniform(*style.fringe_wave) if is_front[gi] else None)
        t, n, b = frames(gw, sdf)
        L = len(gw)
        s = np.linspace(0, 1, L)
        kappa = rng.uniform(*(style.fringe_clump if is_front[gi] else style.clump))
        strands.append(gw)
        for c in range(style.children):
            r = (style.fringe_clump_radius if is_front[gi] else style.clump_radius) * np.sqrt(rng.random())
            a = rng.uniform(0, 2 * np.pi)
            ob, on = r * np.cos(a), 0.35 * r * np.sin(a)
            conv = 1 - kappa * s ** 0.8
            jit = rng.normal(size=3) * 0.004
            cp = gw + (ob * conv)[:, None] * b + (on * conv + 0.002)[:, None] * n + jit * s[:, None]
            cut = int(max(3, round(L * rng.uniform(0.75, 1.0))))
            cp = cp[:cut]
            # keep outside the head
            d = sdf(cp)
            cp = cp + np.maximum(0.002 - d, 0)[:, None] * sdf.grad(cp)
            strands.append(cp)
    # frizzy flyaways on the top (the photo shows fine curls sticking out of the crown)
    fly = []
    top_roots = roots[(roots - fr.c)[:, 1] > 0.75 * fr.R]
    for i in range(min(style.flyaways, len(top_roots))):
        p0 = top_roots[rng.integers(len(top_roots))]
        nrm = sdf.grad(p0[None])[0]
        dist0 = sdf(p0[None])[0]
        L = rng.uniform(0.25, 0.55)
        K = int(L / 0.012)
        dirn = nrm + rng.normal(size=3) * 0.5 + np.array([0, 0.3, 0])
        dirn /= np.linalg.norm(dirn)
        pts = [p0 + nrm * (thickness_at(((p0 - fr.c) / np.linalg.norm(p0 - fr.c))[None], style)[0] * 0.7 - dist0)]
        ax = np.cross(dirn, rng.normal(size=3))
        ax /= np.linalg.norm(ax)
        rad = rng.uniform(0.03, 0.07)
        for k in range(K):
            ang = k * 0.012 / rad
            d = dirn * np.cos(ang * 0.35) + np.cross(ax, dirn) * np.sin(ang)
            d = d / np.linalg.norm(d) + np.array([0, -0.15, 0]) * (k / K)
            pts.append(pts[-1] + 0.012 * d / np.linalg.norm(d))
        fly.append(np.array(pts))
    info = {"guides": len(guides), "strands": len(strands), "flyaways": len(fly),
            "points": int(sum(len(s) for s in strands) + sum(len(f) for f in fly)),
            "head_centre_dm": fr.c.tolist(), "head_radius_dm": float(fr.R)}
    return {"strands": strands, "fly": fly, "sdf": sdf, "frame": fr, "scalp": scalp, "info": info}


# ----------------------------------------------------------------------------- geometry
def ribbons(hair, style: HairStyle, n_variants=4, seed=3, geo_step=0.034):
    """Tapered ribbon cards lying on the hair surface.  Returns pos (N,3) dm, nrm (N,3), uv (N,2), tris."""
    rng = np.random.default_rng(seed)
    sdf = hair["sdf"]
    P, N, UV, T = [], [], [], []
    off = 0
    items = [(s, 1.0) for s in hair["strands"]] + [(f, 0.35) for f in hair["fly"]]
    for path, wscale in items:
        if wscale == 1.0 and geo_step:
            path = resample(path, geo_step)
        L = len(path)
        if L < 2:
            continue
        t, n, b = frames(path, sdf)
        s = np.linspace(0, 1, L)
        w = (style.width_root * (1 - s) + style.width_tip * s) * wscale * rng.uniform(0.7, 1.2)
        # slight twist so cards do not all lie perfectly flat (reads as volume from the side)
        tw = rng.normal() * 0.35 * s
        bb = b * np.cos(tw)[:, None] + n * np.sin(tw)[:, None]
        nn = n * np.cos(tw)[:, None] - b * np.sin(tw)[:, None]
        left = path - bb * (w / 2)[:, None]
        right = path + bb * (w / 2)[:, None]
        P.append(np.stack([left, right], 1).reshape(-1, 3))
        N.append(np.repeat(nn, 2, 0))
        k = rng.integers(n_variants)
        u0, u1 = k / n_variants, (k + 1) / n_variants
        vv = s * rng.uniform(0.85, 1.0)
        UV.append(np.stack([np.stack([np.full(L, u0), vv], 1), np.stack([np.full(L, u1), vv], 1)], 1).reshape(-1, 2))
        i = off + 2 * np.arange(L - 1)
        T.append(np.stack([i, i + 1, i + 3], 1))
        T.append(np.stack([i, i + 3, i + 2], 1))
        off += 2 * L
    return np.vstack(P), np.vstack(N), np.vstack(UV), np.vstack(T)


def strand_texture(style: HairStyle, n_variants=4, w=1024, h=2048, seed=11):
    """RGBA atlas + tangent-space normal map.  n_variants columns, each a card-full of fine hairs running
    along v (root v=0 at the image bottom, tip v=1 at the top).  Hair density falls off towards the card
    edges and hairs end at staggered lengths, so cards read as soft locks rather than strips; the normal
    map makes every hair a little cylinder (x across the card), which breaks the specular highlight into
    strand-like lines instead of one plastic sheet per card."""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 4), np.float32)
    nrm = np.zeros((h, w, 3), np.float32)
    nrm[..., 2] = 1.0
    cw = w // n_variants
    vfrac = (1 - (np.arange(h)[:, None] + 0.5) / h).astype(np.float32)   # 0 root .. 1 tip
    xx = np.arange(cw)[None, :].astype(np.float32)
    base = np.asarray(style.color_srgb, np.float32)
    for k in range(n_variants):
        x0 = k * cw
        nh = int(rng.integers(60, 85))
        xs = np.clip(rng.normal(0.5, 0.22, nh), 0.03, 0.97) * cw
        col_acc = np.zeros((h, cw, 3), np.float32)
        a_acc = np.zeros((h, cw), np.float32)
        nx_acc = np.zeros((h, cw), np.float32)
        for x in xs:
            width = rng.uniform(1.6, 3.0)
            edge = abs(x / cw - 0.5) * 2                      # 0 centre .. 1 edge
            v_end = rng.uniform(0.6, 1.0) * (1 - 0.35 * edge ** 2)
            v_start = rng.uniform(0.0, 0.12) * edge
            amp = rng.uniform(0.5, 5.0)
            freq = rng.uniform(2.5, 7.0)
            ph = rng.uniform(0, 6.28)
            cx = x + amp * np.sin(vfrac * freq + ph) + rng.uniform(-4, 4) * vfrac
            dx = xx - cx
            taper = np.clip((v_end - vfrac) / 0.15, 0, 1)
            wid = width * (0.3 + 0.7 * taper)
            a = np.clip(wid / 2 + 0.5 - np.abs(dx), 0, 1) * (vfrac < v_end) * (vfrac > v_start)
            shade = rng.uniform(0.7, 1.5) * (0.85 + 0.3 * vfrac)          # roots a touch darker
            c = base[None, None, :] * (shade * (0.92 + 0.12 * np.sin(vfrac * 55 + ph)))[..., None]
            col_acc = col_acc * (1 - a[..., None]) + c * a[..., None]
            nx = np.clip(dx / np.maximum(wid / 2, 0.5), -0.85, 0.85)
            nx_acc = nx_acc * (1 - a) + nx * a
            a_acc = np.maximum(a_acc, a)
        img[:, x0:x0 + cw, :3] = np.where(a_acc[..., None] > 0, col_acc / np.maximum(a_acc[..., None], 1e-3), base)
        img[:, x0:x0 + cw, 3] = a_acc
        nrm[:, x0:x0 + cw, 0] = nx_acc
        nrm[:, x0:x0 + cw, 2] = np.sqrt(np.clip(1 - nx_acc ** 2, 0, 1))
    return np.clip(img, 0, 1), (nrm * 0.5 + 0.5).clip(0, 1)


def scalp_paint_weights(hair, v, brow_clear=0.42):
    """Per-vertex weight for painting the scalp in the hair colour: the hair-bearing scalp, minus the
    sideburn / temple band in front of and around the ears (no cards grow there; painted it reads as dirt)."""
    fr = hair["frame"]
    d = (v - fr.c) / np.maximum(np.linalg.norm(v - fr.c, axis=1, keepdims=True), 1e-9)
    az = np.abs(np.arctan2(d[:, 0], d[:, 2]))
    side = np.clip((az - np.radians(35)) / np.radians(10), 0, 1) * np.clip((np.radians(125) - az) / np.radians(10), 0, 1)
    low = np.clip((fr.ear_top_y + 0.14 - v[:, 1]) / 0.1, 0, 1)
    # forehead: keep skin up to ~4 cm above the brows (the fringe separates into locks there)
    front = np.clip((np.radians(45) - az) / np.radians(15), 0, 1)
    fh = np.clip((v[:, 1] - (fr.brow_y + brow_clear)) / 0.15, 0, 1)
    # nape: fade out just above the nape hairline so no painted blotches show below the hair
    backw = np.clip((az - np.radians(110)) / np.radians(15), 0, 1)
    nape = np.clip((v[:, 1] - (fr.nape_y + 0.05)) / 0.12, 0, 1)
    w = hair["scalp"] * (1 - side * low)
    w = w * (1 - front * (1 - fh))
    return w * (1 - backw * (1 - nape))
