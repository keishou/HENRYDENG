"""Procedural hair cards for the fitted MakeHuman head: black, soft, curly / permed medium-short hair
with a split curtain fringe, full rounded sides over the ear tops and a graduated taper into the nape.

    hair = grow_hair(mh, base, v_dm, HairStyle(), guide=(hair_mask_cam, fit_cam))   # guide optional
    # -> lock guides + clumped, curled children (dm); hair_mask_cam = the photo's hair mask in the
    #    landmark-fit orthographic camera's pixels
    P, N, UV, T = ribbons(hair, style)                     # alpha-textured ribbon cards (tapered)
    rgba, normal = strand_texture(style)                   # strand atlas + per-hair cylinder normal map

Method
  * scalp = the skin region MakeHuman's short02 hair is fitted to (its reference vertices), smoothed over
    the mesh; a signed distance field of the head (1.5 mm voxels) lets strands glide over the head at a
    chosen height instead of cutting through it.
  * volume: every strand glides at a layer height lambda x T(direction); T, the outer hair envelope, is
    measured from the photo's front hair silhouette (hair mask of the frontal photo, seen by the landmark
    fit camera) above the ears, and tapers towards the back / nape.  Without a photo a parametric envelope
    is used.
  * flow: away from a whorl at the back of the crown; everything in front of the crown is combed forward
    to a part slightly off the centre, where it splits into a curtain: locks fall over the forehead and
    sweep out towards the temples as they descend.  Sides fall down over the temples to the upper third of
    the ear; the back lies down in a graduated taper (length grows with the root's height above the nape
    hairline, so tips cover the roots below -- no ledge).
  * where locks end: fringe and front-side locks stop where the photo shows no hair (so the forehead shows
    between the locks where it does in the photo, and the tips end at the photo's brow line); the locks
    are steered sideways towards the photo's hair while they descend.  Behind the ears lengths decide.
  * curl: each lock is a helix around its path (period 1.5-2.2 cm, growing from the root to the tip);
    children follow their lock inside a small clump that converges towards the tip and add a fine frizz;
    a few frizzy flyaways sit on the crown as in the photo.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.ndimage as ndi
import scipy.sparse as sp


@dataclass
class HairStyle:
    seed: int = 7
    n_guides: int = 2800              # lock guides
    children: int = 5                 # children per lock (+ the guide itself)
    step: float = 0.02                # dm (2 mm) integration step
    max_len: float = 1.7              # dm
    # envelope (used without a photo, and behind the ears)
    thickness_top: float = 0.24       # dm, outer hair surface above the scalp on top
    thickness_side: float = 0.19
    back_scale: float = 0.8           # back envelope relative to the sides
    thickness_nape: float = 0.03
    envelope_scale: float = 0.97      # the photo envelope is shrunk a touch (frizz is added on top)
    fringe_height: float = 0.045      # dm above the forehead skin
    part_x: float = -0.05             # dm, the part (subject's right = -x), slightly off centre
    curtain: float = 1.3              # sideways sweep of the fringe away from the part
    forward_comb: float = 1.7
    whorl: tuple = (0.10, 0.60, -0.80)  # direction from the head centre (x, y, z), normalised
    whorl_twist: float = 0.8
    side_end_below_ear_top: float = 0.3   # dm: side hair ends 1-3.5 cm below the ear top (covers its upper third)
    back_len: tuple = (0.12, 1.05)    # dm: lengths at the nape hairline .. at the crown (graduated)
    nape_end: tuple = (-0.06, 0.3)    # dm relative to the nape hairline: where back locks end (staggered)
    hug_min: float = 0.45             # side / back hair falls in towards the head below the ear tops
    # curl / clumps
    curl_period: tuple = (0.28, 0.42)  # dm: loose waves along each lock
    curl_amp: tuple = (0.012, 0.022)   # dm (grows towards the tip)
    fringe_curl_amp: tuple = (0.018, 0.03)
    clump_radius: float = 0.04        # dm
    clump: tuple = (0.55, 0.85)       # tip convergence range
    frizz_amp: float = 0.0015
    width_root: float = 0.036         # dm card width at the root
    width_tip: float = 0.012
    flyaways: int = 110
    color_srgb: tuple = (0.06, 0.05, 0.045)    # soft black with a warm brown undertone


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


# ----------------------------------------------------------------------------- head frame
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


def sample_roots(rng, v, tris, scalp, n, thr=0.5):
    """Area-weighted random points on the scalp (triangles with scalp > thr at all corners), with a
    blue-noise thinning so neighbouring locks do not double up."""
    s = scalp[tris].min(1)
    keep = s > thr
    T = tris[keep]
    P = v[T]
    area = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    m = int(n * 3)
    ti = rng.choice(len(T), m, p=area / area.sum())
    r1, r2 = rng.random(m), rng.random(m)
    flip = r1 + r2 > 1
    r1[flip], r2[flip] = 1 - r1[flip], 1 - r2[flip]
    p = P[ti, 0] * (1 - r1 - r2)[:, None] + P[ti, 1] * r1[:, None] + P[ti, 2] * r2[:, None]
    # Poisson-disk style thinning (greedy) to ~n points
    from scipy.spatial import cKDTree
    tot = area.sum()
    rad = 0.7 * np.sqrt(tot / n)
    tree = cKDTree(p)
    alive = np.ones(m, bool)
    out = []
    for i in rng.permutation(m):
        if not alive[i]:
            continue
        out.append(i)
        alive[tree.query_ball_point(p[i], rad)] = False
        if len(out) >= n:
            break
    return p[np.array(out)]


# ----------------------------------------------------------------------------- photo guide
class PhotoGuide:
    """The frontal photo's hair mask as seen by the landmark-fit orthographic camera (model x-y plane).

    hair(P)      -> soft hair coverage in [0,1] at the frontal projection of points P (dm)
    steer_x(P)   -> signed sideways pull (dm^-1) towards the photo's hair along x (fringe locks)
    envelope(th) -> outer hair radius (dm) about the head centre in the frontal plane, angle th from the
                    top (+ = subject's left, +x); nan where the photo gives nothing (below the ear tops)"""

    def __init__(self, mask_cam, cam, fr: HeadFrame, sdf: SDF):
        import cv2
        self.cam = cam
        m = (np.asarray(mask_cam) > 0).astype(np.uint8)
        # drop specks / the thin frizz halo for the envelope; keep a soft version for locks
        core = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        self.soft = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.0)
        blur = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 7.0)
        self.gx = np.gradient(blur, axis=1)
        self.core = core
        # envelope radii in the frontal plane (pixels -> dm)
        cpx = cam.project(fr.c[None])[0][0]
        self.c_px = cpx
        ys, xs = np.nonzero(core)
        ang = np.degrees(np.arctan2(xs + 0.5 - cpx[0], -(ys + 0.5 - cpx[1])))   # 0 = up, + = image right
        rad = np.hypot(xs + 0.5 - cpx[0], ys + 0.5 - cpx[1]) / cam.px_per_dm
        bins = np.arange(-120, 121, 2.0)
        env = np.full(len(bins), np.nan)
        for i, b in enumerate(bins):
            sel = np.abs(ang - b) < 1.5
            if sel.sum() > 20:
                env[i] = np.percentile(rad[sel], 99)
        # image right = the subject's left = model +x (the camera looks at the model's face)
        self.env_bins = bins
        self.env = env
        # skull radius along the same rays in the plane z = c_z (SDF ray march)
        sk = np.full(len(bins), np.nan)
        for i, b in enumerate(bins):
            d = np.array([np.sin(np.radians(b)), np.cos(np.radians(b)), 0.0])
            r = np.linspace(2.2, 0.3, 400)                   # march in from outside (the SDF is
            P = fr.c[None] + r[:, None] * d[None]            # unsigned inside the open head mesh)
            dist = sdf(P)
            hit = np.nonzero(dist < 0.6 * sdf.h)[0]
            if len(hit):
                sk[i] = r[hit[0]]
        self.skull = sk
        self.lowest_hair_y = cam.unproject_xy(np.array([[0, ys.max() + 0.5]]))[0, 1]

    def _px(self, P):
        return self.cam.project(P)[0]

    def hair(self, P):
        q = self._px(P)
        return ndi.map_coordinates(self.soft, [q[:, 1] - 0.5, q[:, 0] - 0.5], order=1, mode="constant")

    def steer_x(self, P):
        q = self._px(P)
        g = ndi.map_coordinates(self.gx, [q[:, 1] - 0.5, q[:, 0] - 0.5], order=1, mode="constant")
        return g * self.cam.px_per_dm

    def thickness(self, theta_deg):
        """Envelope minus skull radius (dm) at frontal angle theta (nan where unknown)."""
        return np.interp(theta_deg, self.env_bins, self.env - self.skull, left=np.nan, right=np.nan)


def _head_sdf(v, tv, fr):
    lo = fr.c - np.array([fr.R + 0.6, fr.R + 1.4, fr.R + 0.7])
    hi = fr.c + np.array([fr.R + 0.6, fr.R + 0.6, fr.R + 0.9])
    return SDF(v, tv, lo, hi)


# ----------------------------------------------------------------------------- growth
def envelope_thickness(P, fr: HeadFrame, style: HairStyle, guide: PhotoGuide | None):
    """Outer hair thickness (dm) above the scalp for points P (direction from the head centre)."""
    d = P - fr.c
    d = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    el = np.degrees(np.arcsin(np.clip(d[:, 1], -1, 1)))
    az = np.degrees(np.arctan2(d[:, 0], d[:, 2]))                 # 0 front, +-90 sides, 180 back
    theta = np.degrees(np.arctan2(d[:, 0], d[:, 1]))              # frontal-plane angle from the top
    fb = 0.5 * (1 - np.cos(np.radians(az)))                       # 0 front .. 1 back
    # parametric default: top / sides
    w_top = np.clip((el - 35) / 35, 0, 1)
    T = style.thickness_side * (1 - w_top) + style.thickness_top * w_top
    if guide is not None:
        tg = guide.thickness(np.clip(theta, -84, 84)) * style.envelope_scale
        T = np.where(np.isfinite(tg), np.clip(tg, 0.04, 0.45), T)
    # back of the head: a little flatter than the sides; the nape tapers to a thin layer
    back = np.clip((fb - 0.6) / 0.35, 0, 1)
    T = T * (1 - back * (1 - style.back_scale))
    w_nape = np.clip((-5 - el) / 35, 0, 1) * np.clip((fb - 0.35) / 0.4, 0, 1)
    return T * (1 - w_nape) + style.thickness_nape * w_nape


def grow_guides(rng, roots, sdf: SDF, fr: HeadFrame, style: HairStyle, scalp_at, guide: PhotoGuide | None):
    """Integrate lock guides over the head.  Returns (list of (K_i,3) polylines, per-lock info)."""
    n = len(roots)
    W = fr.c + fr.R * np.asarray(style.whorl) / np.linalg.norm(style.whorl)
    nrm = sdf.grad(roots)
    d0 = roots - fr.c
    d0 /= np.linalg.norm(d0, axis=1, keepdims=True)
    az0 = np.degrees(np.arctan2(d0[:, 0], d0[:, 2]))
    front = np.abs(az0) < 55
    back = np.abs(az0) > 115
    side = ~front & ~back
    lam = rng.random(n) ** 0.55 * 0.8 + 0.2          # layer height fraction (outer layers more common)
    # lengths: the back is a graduated taper from the nape hairline to the crown
    nape_line = fr.nape_y
    hgt = np.clip((roots[:, 1] - nape_line) / max(W[1] - nape_line, 1e-3), 0, 1)
    L_back = style.back_len[0] + (style.back_len[1] - style.back_len[0]) * hgt ** 1.2
    Lmax = np.where(back, L_back * rng.uniform(0.85, 1.1, n), style.max_len * rng.uniform(0.85, 1.0, n))
    # temples / sideburns (low side roots, in front of and above the ear): short, lying down
    low_side = side & (roots[:, 1] < fr.ear_top_y + 0.12)
    temple = np.abs(az0) < 85
    Lmax = np.where(low_side, np.where(temple, rng.uniform(0.3, 0.55, n), rng.uniform(0.25, 0.45, n)), Lmax)
    min_len = np.where(front, rng.uniform(0.06, 0.12, n), 0.1)
    side_end = fr.ear_top_y - style.side_end_below_ear_top * rng.uniform(0.35, 1.15, n)
    # the back ends in a soft, staggered line around the nape hairline (short hair there lies flat)
    back_end = nape_line + rng.uniform(*style.nape_end, n) - 0.12 * np.clip(1 - np.abs(roots[:, 0]) / 0.45, 0, 1)
    P = roots + nrm * 0.004
    sgn_part = np.sign(roots[:, 0] - style.part_x + 1e-6)
    top_y = fr.c[1] + 0.75 * fr.R

    def comb(P, g, s, off_scalp=None):
        f = tangent(P - W, g)
        dw = np.linalg.norm(P - W, axis=1)
        f = f + style.whorl_twist * np.exp(-dw / 0.3)[:, None] * np.cross(g, f)
        # in front of the crown: combed forward (and down), towards the fringe
        azp = np.abs(np.degrees(np.arctan2(P[:, 0] - fr.c[0], P[:, 2] - fr.c[2])))
        wf = style.forward_comb * np.clip((P[:, 2] - (fr.c[2] - 0.3)) / 0.6, 0, 1) * \
            np.clip((P[:, 1] - fr.ear_top_y) / 0.4, 0, 1)
        # ... except on the sides of the head, where the hair falls down over the ears
        side_w = np.clip((azp - 55) / 30, 0, 1) * np.clip((P[:, 1] - fr.c[1] - 0.5 * fr.R) / (-0.4), 0, 1)
        wf = wf * (1 - np.clip((azp - 50) / 35, 0, 1) * 0.85)
        f = f + wf[:, None] * tangent(np.tile([0.0, -0.3, 1.0], (len(P), 1)), g)
        f = f + (1.2 * side_w)[:, None] * tangent(np.tile([0.0, -1.0, 0.1], (len(P), 1)), g)
        # curtain: away from the part, more as the lock descends over the forehead
        desc = np.clip((top_y - P[:, 1]) / 0.55, 0, 1.2)
        if off_scalp is not None:      # the curtain opens over the forehead, not on top of the head
            desc = desc * np.clip(0.25 + off_scalp, 0, 1)
        wc = style.curtain * desc * np.clip((P[:, 2] - fr.c[2]) / 0.5, 0, 1)
        f[:, 0] += wc * sgn_part
        return tangent(f, g)

    flow = comb(roots, nrm, np.zeros(n))
    dirp = tangent(flow + nrm * 0.9, nrm) * 0.5 + nrm * 0.5      # hair leaves the scalp at ~40-50 deg
    dirp /= np.linalg.norm(dirp, axis=1, keepdims=True)
    paths = [P.copy()]
    alive = np.ones(n, bool)
    s = np.zeros(n)
    noise_dir = rng.normal(size=(n, 3)) * 0.12
    out_of_hair = np.zeros(n, int)
    for k in range(int(style.max_len / style.step) + 2):
        g = sdf.grad(P)
        dist = sdf(P)
        on_scalp = scalp_at(P)
        f = comb(P, g, s, 1 - on_scalp)
        grav = tangent(np.tile([0.0, -1.0, 0.0], (n, 1)), g)
        wg = 0.2 + 1.5 * (1 - on_scalp) + 0.6 * np.clip(s / 0.8, 0, 1)
        new = 1.2 * dirp + 1.0 * f + wg[:, None] * grav + noise_dir
        if guide is not None:
            # fringe / front locks drift sideways towards the photo's hair as they descend
            fr_w = (1 - on_scalp) * (P[:, 2] > fr.c[2] + 0.4)
            new[:, 0] += 0.035 * np.clip(guide.steer_x(P), -12, 12) * fr_w
        # layer height: glide at lambda x envelope; low over bare skin (fringe lies on the forehead)
        T = envelope_thickness(P, fr, style, guide)
        goal = np.where(on_scalp > 0.5, lam * T, np.minimum(lam * T, style.fringe_height * (0.5 + lam)))
        hug = np.clip((P[:, 1] - (fr.ear_top_y - 0.3)) / 0.4, style.hug_min, 1.0)
        backw = np.clip((np.abs(np.degrees(np.arctan2(P[:, 0] - fr.c[0], P[:, 2] - fr.c[2]))) - 95) / 30, 0, 1)
        hug = hug * backw + np.maximum(hug, 0.8) * (1 - backw)       # the sides stay full to the ear tops
        goal = np.where(front, goal, goal * hug)
        goal = np.minimum(goal, 0.004 + s * 0.9)
        new = tangent(new, g) + np.clip((goal - dist) * 12.0, -1.5, 1.5)[:, None] * g
        new /= np.linalg.norm(new, axis=1, keepdims=True)
        Pn = P + style.step * new
        dn = sdf(Pn)
        Pn = Pn + np.maximum(0.003 - dn, 0)[:, None] * sdf.grad(Pn)
        dirp = (Pn - P) / style.step
        dirp /= np.maximum(np.linalg.norm(dirp, axis=1, keepdims=True), 1e-9)
        s = s + style.step * alive
        P = np.where(alive[:, None], Pn, P)
        paths.append(P.copy())
        # ---- stop rules
        stop = s >= Lmax
        dd = P - fr.c
        az = np.degrees(np.arctan2(dd[:, 0], dd[:, 2]))
        frontal = np.abs(az) < 72
        if guide is not None:
            # front / side locks visible from the front end where the photo shows no hair
            inh = guide.hair(P)
            out_of_hair = np.where(inh < 0.3, out_of_hair + 1, 0)
            stop |= frontal & (out_of_hair >= 2) & (s > min_len) & (P[:, 1] < top_y)
        else:
            stop |= front & (P[:, 1] < fr.brow_y + rng.uniform(-0.05, 0.25, n)) & (s > min_len)
        # side locks end ~2 cm below the ear tops; at the temples (seen from the front) the photo decides
        stop |= side & ((np.abs(az) > 72) | (guide is None)) & (P[:, 1] < side_end) & (s > 0.1)
        stop |= side & (P[:, 1] < side_end - 0.2)
        stop |= back & (P[:, 1] < back_end) & (s > 0.05)
        over_face = (P[:, 2] > fr.c[2] + 0.5 * fr.R) & (np.abs(P[:, 0]) < 0.55 * fr.R)
        stop |= over_face & (P[:, 1] < fr.brow_y - 0.1)              # never over the eyes
        alive &= ~stop
        if not alive.any():
            break
    paths = np.stack(paths, 1)
    out = []
    for i in range(n):
        seg = np.linalg.norm(np.diff(paths[i], axis=0), axis=1)
        K = int(np.nonzero(seg > 1e-6)[0].max() + 2) if (seg > 1e-6).any() else 2
        out.append(paths[i, :K])
    return out, dict(lam=lam, front=front, side=side, back=back, Lmax=Lmax, side_end=side_end, roots=roots)


def resample(path, step):
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.r_[0, np.cumsum(seg)]
    if s[-1] < step:
        return path[[0, -1]]
    t = np.linspace(0, s[-1], max(int(round(s[-1] / step)) + 1, 2))
    return np.stack([np.interp(t, s, path[:, j]) for j in range(3)], 1)


def frames(path, sdf, smooth_n=2.0):
    """Tangent, normal (away from the head, smoothed along the strand so ribbons do not flip where the
    distance field's gradient is noisy) and binormal of a polyline."""
    t = np.gradient(path, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    n = sdf.grad(path)
    if smooth_n and len(path) > 3:
        n = ndi.gaussian_filter1d(n, smooth_n, axis=0, mode="nearest")
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    b = np.cross(t, n)
    b /= np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-9)
    n = np.cross(b, t)
    return t, n, b


def _keep_out(p, sdf, gap=0.003):
    d = sdf(p)
    return p + np.maximum(gap - d, 0)[:, None] * sdf.grad(p)


def curl(rng, path, sdf, amp, period, start=0.2, flat=0.55):
    """Helical curl around the path, amplitude growing from `start` (fraction of length) to the tip;
    `flat` squashes the helix towards the head (hair lies on the head more than it lifts off)."""
    L = len(path)
    if L < 4:
        return path
    t, n, b = frames(path, sdf)
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    s = arc / max(arc[-1], 1e-9)
    env = np.clip((s - start) / 0.45, 0, 1) ** 1.3
    ph = rng.uniform(0, 2 * np.pi)
    w = 2 * np.pi * arc / period + ph
    out = path + (amp * env)[:, None] * (np.cos(w)[:, None] * b + flat * np.sin(w)[:, None] * n)
    return _keep_out(out, sdf)


def grow_hair(mh, base, v, style: HairStyle | None = None, guide: PhotoGuide | None = None, log=print,
              side_profile=None):
    style = style or HairStyle()
    rng = np.random.default_rng(style.seed)
    body = base.fgroup == base.groups.index("body")
    tv, _ = base.triangles(body)
    scalp = scalp_field(mh, base, v)
    fr = head_frame(base, v, scalp)
    # strands glide over a head whose ears are folded flat (so the side hair flows down over the ear tops
    # instead of piling up on the helix); the finished strands are then pushed out of the real head
    v_glide = v.copy()
    for side in "lr":
        try:
            ii, dd_ = mh.target(f"targets/ears/{side}-ear-scale-decr.target")
            v_glide[ii] += 1.6 * dd_
            ii, dd_ = mh.target(f"targets/ears/{side}-ear-flap-decr.target")
            v_glide[ii] += 1.0 * dd_
        except FileNotFoundError:
            pass
    sdf_full = _head_sdf(v, tv, fr)
    sdf = _head_sdf(v_glide, tv, fr)
    if guide is not None and not isinstance(guide, PhotoGuide):
        mask_cam, cam = guide                       # (photo hair mask in fit-camera pixels, OrthoCam)
        guide = PhotoGuide(mask_cam, cam, fr, sdf)
    log(f"  head centre {np.round(fr.c, 3).tolist()} R {fr.R:.3f} dm; sdf grid {sdf.shape.tolist()}")
    from scipy.spatial import cKDTree
    near_ids = np.unique(tv)
    near_tree = cKDTree(v[near_ids])

    def scalp_at(p):
        _, i = near_tree.query(p, k=1)
        return scalp[near_ids[i]]

    roots = sample_roots(rng, v, tv, scalp, style.n_guides, thr=0.45)
    # hairline: MakeHuman's hair scalp region runs far down the neck and the jaw; the nape hairline sits
    # at about ear-lobe level and the sideburns end at mid-ear
    dd = roots - fr.c
    az_r = np.abs(np.degrees(np.arctan2(dd[:, 0], dd[:, 2])))
    keep = roots[:, 1] > fr.nape_y + np.where(az_r > 120, 0.0, 0.25)
    keep &= ~((az_r > 50) & (az_r < 120) & (roots[:, 1] < fr.ear_top_y - 0.25))
    roots = roots[keep]
    if guide is not None:
        # front roots where the photo shows forehead skin (between the fringe locks, near the hairline)
        dd = roots - fr.c
        front_half = (dd[:, 2] > 0.35 * fr.R) & (roots[:, 1] < fr.c[1] + 0.75 * fr.R)
        roots = roots[~(front_half & (guide.hair(roots) < 0.3))]
    guides, gi = grow_guides(rng, roots, sdf, fr, style, scalp_at, guide)
    strands, lock_of = [], []
    for k, g in enumerate(guides):
        g = resample(g, style.step)
        if len(g) < 3:
            continue
        is_front = gi["front"][k]
        amp = rng.uniform(*(style.fringe_curl_amp if is_front else style.curl_amp))
        per = rng.uniform(*style.curl_period)
        gw = curl(rng, g, sdf, amp, per, start=0.15 if is_front else 0.25)
        t, n, b = frames(gw, sdf)
        L = len(gw)
        s = np.linspace(0, 1, L)
        kappa = rng.uniform(*style.clump)
        strands.append(gw)
        lock_of.append(k)
        for c in range(style.children):
            r = style.clump_radius * np.sqrt(rng.random())
            a = rng.uniform(0, 2 * np.pi)
            ob, on = r * np.cos(a), 0.4 * r * np.sin(a)
            conv = 1 - kappa * s ** 0.9
            cp = gw + (ob * conv)[:, None] * b + (on * conv + 0.002)[:, None] * n
            # fine frizz of the child around its lock
            cp = curl(rng, cp, sdf, style.frizz_amp * rng.uniform(0.5, 1.5), rng.uniform(0.1, 0.16), start=0.1, flat=1.0)
            cut = int(max(3, round(L * rng.uniform(0.7, 1.0))))
            cp = _keep_out(cp[:cut], sdf, 0.002)
            strands.append(cp)
            lock_of.append(k)
    # curls and clumps spread the locks: trim every strand where it leaves the photo's hair in the front
    # view (keeps the forehead clear between the fringe locks, as in the photo)
    if guide is not None:
        top_y = fr.c[1] + 0.75 * fr.R
        trimmed = []
        for p in strands:
            dd = p - fr.c
            az = np.degrees(np.arctan2(dd[:, 0], dd[:, 2]))
            chk = (np.abs(az) < 72) & (p[:, 1] < top_y)
            bad = chk & (guide.hair(p) < 0.25)
            bad[:3] = False
            k = np.nonzero(bad)[0]
            if len(k):
                q = p[:max(k[0], 3)]
                Lq = np.linalg.norm(np.diff(q, axis=0), axis=1).sum()
                Lp = np.linalg.norm(np.diff(p, axis=0), axis=1).sum()
                if Lq < 0.25 and Lq < 0.5 * Lp:      # a cut-off stub reads as a dark chip on the forehead
                    continue
                p = q
            trimmed.append(p)
        strands = trimmed
    # stubs (a few mm left after trimming, or tiny sideburn hairs) render as dark specks: drop them
    def _long_enough(p):
        L = np.linalg.norm(np.diff(p, axis=0), axis=1).sum()
        dz = p[0, 2] - fr.c[2]
        return L > (0.16 if dz > 0.4 * fr.R else 0.22)      # back / sides: no tiny tufts at the hairline
    keep_s = [_long_enough(p) for p in strands]
    strands = [_keep_out(p, sdf_full, 0.0025) for p, k in zip(strands, keep_s) if k]
    # frizzy flyaways on the top (the photo shows fine curls sticking out of the crown)
    fly = []
    top_roots = roots[(roots - fr.c)[:, 1] > 0.6 * fr.R]
    for i in range(min(style.flyaways, len(top_roots))):
        p0 = top_roots[rng.integers(len(top_roots))]
        nrm = sdf.grad(p0[None])[0]
        T0 = envelope_thickness(p0[None], fr, style, guide)[0]
        dist0 = sdf(p0[None])[0]
        L = rng.uniform(0.2, 0.5)
        K = int(L / 0.012)
        dirn = nrm + rng.normal(size=3) * 0.6 + np.array([0, 0.2, 0.3])
        dirn /= np.linalg.norm(dirn)
        pts = [p0 + nrm * (T0 * rng.uniform(0.75, 0.95) - dist0)]
        ax = np.cross(dirn, rng.normal(size=3))
        ax /= np.linalg.norm(ax)
        rad = rng.uniform(0.025, 0.06)
        for k in range(K):
            ang = k * 0.012 / rad
            d = dirn * np.cos(ang * 0.35) + np.cross(ax, dirn) * np.sin(ang)
            d = d / np.linalg.norm(d) + np.array([0, -0.2, 0]) * (k / K)
            pts.append(pts[-1] + 0.012 * d / np.linalg.norm(d))
        fly.append(np.array(pts))
    lens = np.array([np.linalg.norm(np.diff(g, axis=0), axis=1).sum() for g in guides])
    info = {"guides": len(guides), "strands": len(strands), "flyaways": len(fly),
            "points": int(sum(len(s) for s in strands) + sum(len(f) for f in fly)),
            "head_centre_dm": fr.c.tolist(), "head_radius_dm": float(fr.R),
            "lock_len_dm": {"front": float(np.median(lens[gi["front"]])), "side": float(np.median(lens[gi["side"]])),
                            "back": float(np.median(lens[gi["back"]]))},
            "photo_guided": guide is not None}
    return {"strands": strands, "fly": fly, "sdf": sdf, "frame": fr, "scalp": scalp, "info": info,
            "guides": guides, "guide_info": gi, "photo_guide": guide}


# ----------------------------------------------------------------------------- geometry
def ribbons(hair, style: HairStyle, n_variants=4, seed=3, geo_step=0.04):
    """Tapered ribbon cards lying on the hair surface.  Returns pos (N,3) dm, nrm (N,3), uv (N,2), tris."""
    rng = np.random.default_rng(seed)
    sdf = hair["sdf"]
    P, N, UV, T = [], [], [], []
    off = 0
    items = [(s, 1.0) for s in hair["strands"]] + [(f, 0.3) for f in hair["fly"]]
    for path, wscale in items:
        if wscale == 1.0 and geo_step:
            path = resample(path, geo_step)
        L = len(path)
        if L < 2:
            continue
        t, n, b = frames(path, sdf)
        s = np.linspace(0, 1, L)
        w = (style.width_root * (1 - s) + style.width_tip * s) * wscale * rng.uniform(0.75, 1.2)
        tw = rng.normal() * 0.4 * s
        bb = b * np.cos(tw)[:, None] + n * np.sin(tw)[:, None]
        nn = n * np.cos(tw)[:, None] - b * np.sin(tw)[:, None]
        left = path - bb * (w / 2)[:, None]
        right = path + bb * (w / 2)[:, None]
        P.append(np.stack([left, right], 1).reshape(-1, 3))
        N.append(np.repeat(nn, 2, 0))
        k = rng.integers(n_variants)
        u0, u1 = k / n_variants, (k + 1) / n_variants
        vv = s * rng.uniform(0.9, 1.0)
        UV.append(np.stack([np.stack([np.full(L, u0), vv], 1), np.stack([np.full(L, u1), vv], 1)], 1).reshape(-1, 2))
        i = off + 2 * np.arange(L - 1)
        T.append(np.stack([i, i + 1, i + 3], 1))
        T.append(np.stack([i, i + 3, i + 2], 1))
        off += 2 * L
    return np.vstack(P), np.vstack(N), np.vstack(UV), np.vstack(T)


def strand_texture(style: HairStyle, n_variants=4, w=1024, h=2048, seed=11):
    """RGBA atlas + tangent-space normal map.  n_variants columns, each a card-full of fine hairs running
    along v (root v=0 at the image bottom, tip v=1 at the top).  Hair density falls off towards the card
    edges and hairs end at staggered lengths with thinning tips (soft lock ends, no blunt cut); roots are
    a touch darker; the normal map makes every hair a little cylinder (x across the card), which breaks
    the specular highlight into strands instead of one plastic sheet per card."""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 4), np.float32)
    nrm = np.zeros((h, w, 3), np.float32)
    nrm[..., 2] = 1.0
    cw = w // n_variants
    vfrac = (1 - (np.arange(h)[:, None] + 0.5) / h).astype(np.float32)   # 0 root .. 1 tip
    xx = np.arange(cw)[None, :].astype(np.float32)
    base = np.asarray(style.color_srgb, np.float32)
    warm = np.array([1.35, 1.1, 0.95], np.float32)
    for k in range(n_variants):
        x0 = k * cw
        nh = int(rng.integers(120, 150))
        xs = np.clip(rng.normal(0.5, 0.24, nh), 0.03, 0.97) * cw
        col_acc = np.zeros((h, cw, 3), np.float32)
        a_acc = np.zeros((h, cw), np.float32)
        nx_acc = np.zeros((h, cw), np.float32)
        for x in xs:
            width = rng.uniform(2.6, 4.4)
            edge = abs(x / cw - 0.5) * 2                      # 0 centre .. 1 edge
            v_end = rng.uniform(0.6, 1.0) * (1 - 0.3 * edge ** 2)
            v_start = rng.uniform(0.0, 0.1) * edge
            amp = rng.uniform(1.0, 6.0)
            freq = rng.uniform(4.0, 11.0)                     # fine waviness of single hairs
            ph = rng.uniform(0, 6.28)
            cx = x + amp * np.sin(vfrac * freq + ph) + rng.uniform(-5, 5) * vfrac
            dx = xx - cx
            taper = np.clip((v_end - vfrac) / 0.25, 0, 1)   # hairs thin out over their last quarter
            wid = width * (0.25 + 0.75 * taper)
            a = np.clip(wid / 2 + 0.5 - np.abs(dx), 0, 1) * (vfrac < v_end) * (vfrac > v_start)
            a *= 0.6 + 0.4 * taper                            # and fade (soft tips)
            shade = rng.uniform(0.75, 1.35) * (0.7 + 0.45 * np.clip(vfrac / 0.4, 0, 1))   # darker roots
            tint = 1 + (warm - 1) * rng.uniform(0, 0.5)
            c = base[None, None, :] * tint * (shade * (0.94 + 0.08 * np.sin(vfrac * 61 + ph)))[..., None]
            col_acc = col_acc * (1 - a[..., None]) + c * a[..., None]
            nx = np.clip(dx / np.maximum(wid / 2, 0.5), -0.85, 0.85)
            nx_acc = nx_acc * (1 - a) + nx * a
            a_acc = np.maximum(a_acc, a)
        img[:, x0:x0 + cw, :3] = np.where(a_acc[..., None] > 0, col_acc / np.maximum(a_acc[..., None], 1e-3), base)
        img[:, x0:x0 + cw, 3] = a_acc
        nrm[:, x0:x0 + cw, 0] = nx_acc
        nrm[:, x0:x0 + cw, 2] = np.sqrt(np.clip(1 - nx_acc ** 2, 0, 1))
    return np.clip(img, 0, 1), (nrm * 0.5 + 0.5).clip(0, 1)


def scalp_paint_weights(hair, v, brow_clear=0.3, guide=None):
    """Per-vertex weight for painting the scalp in the hair colour so gaps between cards read as dense
    hair: the whole hair-bearing scalp (temples and the nape included: hair grows there now), minus the
    forehead up to ~brow_clear dm above the brows (the fringe separates into locks there and the photo
    shows forehead between them) and a soft fade at the nape hairline."""
    fr = hair["frame"]
    d = (v - fr.c) / np.maximum(np.linalg.norm(v - fr.c, axis=1, keepdims=True), 1e-9)
    az = np.abs(np.degrees(np.arctan2(d[:, 0], d[:, 2])))
    front = np.clip((55 - az) / 15, 0, 1)
    fh = np.clip((v[:, 1] - (fr.brow_y + brow_clear)) / 0.15, 0, 1)
    w = hair["scalp"] * (1 - front * (1 - fh))
    g = hair.get("photo_guide")
    if g is not None:   # no paint where the photo shows forehead skin between the fringe locks
        fh2 = (d[:, 2] > 0.3) & (v[:, 1] < fr.c[1] + 0.75 * fr.R)
        w = w * np.where(fh2, np.clip((g.hair(v) - 0.15) / 0.35, 0, 1), 1.0)
    az_s = np.degrees(np.arctan2(d[:, 0], d[:, 2]))
    hl = fr.nape_y + np.where(np.abs(az_s) > 120, 0.0, np.where(np.abs(az_s) > 50, 0.45, 0.25))
    w = w * np.clip((v[:, 1] - hl) / 0.12, 0, 1)
    # thin the paint over the low temples / sideburns a little (short hair lies there, skin shows through)
    side = np.clip((az - 55) / 15, 0, 1) * np.clip((135 - az) / 15, 0, 1)
    low = np.clip((fr.ear_top_y + 0.05 - v[:, 1]) / 0.2, 0, 1)
    return w * (1 - 0.35 * side * low)
