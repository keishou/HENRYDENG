"""Fit the MakeHuman head of build_body's base human to a face seen in ONE frontal photo.

The face is not warped freely: it is expressed with MakeHuman's own sculpted face / head / neck / ear
modifiers (bounded weights, ridge-regularised), so the result stays anatomically clean (no bumps from
landmark noise) and the eye / teeth helper geometry and all proxies follow automatically.

    ff, v, img = fit_face(mh, cfg, lm_photo, cls_photo, "face_landmarker.task")
    BodyConfig(extra_targets=ff.extra_targets)       # the fitted head

Pipeline (all software, CPU):
  1. the model head is rendered frontally (orthographic, own skin texture, eyes, brows) with the numpy
     rasteriser and MediaPipe FaceLandmarker runs on the render; each model landmark is ray-cast onto
     the skin mesh -> a mesh anchor (triangle, barycentrics).
  2. the photo landmarks are similarity-aligned to the model's in the frontal plane (-> the "photo
     camera" used later for texture projection); depth differences come from MediaPipe's own z of both
     faces (detector-consistent), heavily damped.  Forehead / face-oval landmarks (hidden by the fringe,
     or placed inconsistently between a photo and a CG render) get low weight.
  3. extra linear terms: the front-view skin silhouette (ear outer edges, ear-lobe height, lower face and
     neck) and the eye openings (lid heights, corners) are matched to the photo's segmentation / eye
     contours.
  4. bounded least squares over the modifier weights (one side of each decr/incr pair), then a closed
     loop: render, re-detect, feed the 2D landmark residuals back into the targets (a few iterations).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from PIL import Image

from build_body import BodyConfig, vertex_normals
from mh_assets import MH
from raster import rasterize, sample_bilinear

# MediaPipe face mesh index sets
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152,
             148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
LIPS_INNER = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
LIPS_OUTER = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]
LEFT_EYE = [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466]   # subject's left
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
LEFT_BROW = [276, 283, 282, 295, 285, 300, 293, 334, 296, 336]
RIGHT_BROW = [46, 53, 52, 65, 55, 70, 63, 105, 66, 107]
UPPER_FOREHEAD = [10, 338, 297, 332, 284, 109, 67, 103, 54, 151, 9, 108, 69, 104, 68, 337, 299, 333, 298]


def mp_detect(rgb: np.ndarray, model_path: str):
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    fl = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path=str(model_path)), num_faces=1))
    H, W = rgb.shape[:2]
    res = fl.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb)))
    fl.close()
    if not res.face_landmarks:
        return None
    return np.array([[p.x * W, p.y * H, p.z * W] for p in res.face_landmarks[0]])


# ============================================================================ head scene
@dataclass
class Obj:
    name: str
    V: np.ndarray
    T: np.ndarray       # (t,3) vertex tris
    TU: np.ndarray      # (t,3) uv tris
    VT: np.ndarray
    tex: np.ndarray     # (h,w,3|4) float 0..1
    N: np.ndarray
    alpha_test: float | None = None   # RGBA textures: cutoff (z-buffered, drawn in random batches)


def _tex(path, mode="RGB"):
    return np.asarray(Image.open(path).convert(mode), np.float32) / 255.0


class HeadScene:
    """Skin + eyes + brows + lashes of a morphed hm08 body, for software landmark renders."""

    def __init__(self, mh: MH, cfg: BodyConfig, skin_tex_path: str | None = None):
        self.mh, self.cfg = mh, cfg
        self.base = mh.base()
        self.body = self.base.fgroup == self.base.groups.index("body")
        self.tv, self.tu = self.base.triangles(self.body)
        self.skin_tex = _tex(skin_tex_path or mh.data("skins/textures/young_lightskinned_male_diffuse3.png"))
        self.eyes = mh.proxy(cfg.eyes)
        ea = np.asarray(Image.open(self.eyes.material["diffuseTexture_abs"]).convert("RGBA"))
        uvc = np.stack([self.eyes.mesh.vt[self.eyes.mesh.fuv[:, j]] for j in range(4)], 1).mean(1)
        px_ = np.clip((uvc[:, 0] * ea.shape[1]).astype(int), 0, ea.shape[1] - 1)
        py_ = np.clip(((1 - uvc[:, 1]) * ea.shape[0]).astype(int), 0, ea.shape[0] - 1)
        self.eye_mask = ea[py_, px_, 3] > 127
        self.eye_tex = ea[..., :3].astype(np.float32) / 255.0
        self.alpha_proxies = []
        for rel in (cfg.eyebrows, cfg.eyelashes):
            if rel:
                px = mh.proxy(rel)
                self.alpha_proxies.append((rel, px, _tex(px.material["diffuseTexture_abs"], "RGBA")))

    def objects(self, v, skin_tex=None, with_brows=True):
        objs = [Obj("skin", v, self.tv, self.tu, self.base.vt, self.skin_tex if skin_tex is None else skin_tex,
                    vertex_normals(v, self.base.fv[self.body]))]
        ev = self.eyes.fit(v)
        etv, etu = self.eyes.mesh.triangles(self.eye_mask)
        objs.append(Obj("eyes", ev, etv, etu, self.eyes.mesh.vt, self.eye_tex,
                        vertex_normals(ev, self.eyes.mesh.fv[self.eye_mask])))
        for rel, px, t in self.alpha_proxies:
            if not with_brows and "eyebrow" in rel:
                continue
            pv = px.fit(v)
            a, b = px.mesh.triangles()
            objs.append(Obj(rel, pv, a, b, px.mesh.vt, t, vertex_normals(pv, px.mesh.fv)))
        return objs


@dataclass
class OrthoCam:
    """Frontal orthographic camera: model (x, y) -> pixel; looks along -Z (model faces +Z)."""
    center: np.ndarray   # (3,) decimetres
    half: float          # half extent (dm) of the square view
    res: int = 1024
    yaw: float = 0.0     # radians, rotates the MODEL about +y before projecting

    @property
    def R(self):
        c, s = np.cos(self.yaw), np.sin(self.yaw)
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

    def project(self, V):
        X = (np.asarray(V) - self.center) @ self.R.T
        return np.stack([(X[:, 0] / self.half + 1) * self.res / 2, (1 - X[:, 1] / self.half) * self.res / 2], 1), X[:, 2]

    def unproject_xy(self, P2):
        """pixel -> model-space x, y (for yaw 0)."""
        P2 = np.asarray(P2, float)
        return np.stack([(P2[:, 0] * 2 / self.res - 1) * self.half + self.center[0],
                         (1 - P2[:, 1] * 2 / self.res) * self.half + self.center[1]], 1)

    @property
    def px_per_dm(self):
        return self.res / (2 * self.half)


def render(objs, cam: OrthoCam, light=(0.3, 0.4, 1.0), ambient=0.35, bg=(0.93, 0.93, 0.92)):
    res = cam.res
    L = np.asarray(light, float)
    L /= np.linalg.norm(L)
    img = np.ones((res, res, 3)) * np.asarray(bg)
    zbest = np.full((res, res), -np.inf)
    R = cam.R
    for o in objs:
        P2, Z = cam.project(o.V)
        if o.alpha_test is not None:
            order = np.random.default_rng(0).permutation(len(o.T))
            for part in np.array_split(order, 8):
                tid, bary, depth = rasterize(P2, Z, o.T[part], res, res)
                m = (tid >= 0) & (depth > zbest)
                tt, bb = part[tid[m]], bary[m]
                uv = sum(o.VT[o.TU[tt, k]] * bb[:, k:k + 1] for k in range(3))
                col = sample_bilinear(o.tex, uv[:, 0] * o.tex.shape[1], (1 - uv[:, 1]) * o.tex.shape[0])
                n = sum(o.N[o.T[tt, k]] * bb[:, k:k + 1] for k in range(3)) @ R.T
                n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
                sh = ambient + (1 - ambient) * (0.8 * np.abs(n @ L) + 0.2 * np.abs(n[:, 2]))
                keep = col[:, 3] >= o.alpha_test
                idx = np.argwhere(m)[keep]
                img[idx[:, 0], idx[:, 1]] = col[keep, :3] * sh[keep, None]
                zbest[idx[:, 0], idx[:, 1]] = depth[m][keep]
            continue
        tid, bary, depth = rasterize(P2, Z, o.T, res, res)
        m = (tid >= 0) & (depth > zbest - 1e-3)
        tt, bb = tid[m], bary[m]
        uv = sum(o.VT[o.TU[tt, k]] * bb[:, k:k + 1] for k in range(3))
        col = sample_bilinear(o.tex, uv[:, 0] * o.tex.shape[1], (1 - uv[:, 1]) * o.tex.shape[0])
        n = sum(o.N[o.T[tt, k]] * bb[:, k:k + 1] for k in range(3)) @ R.T
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        sh = ambient + (1 - ambient) * (0.8 * np.clip(n @ L, 0, 1) + 0.2 * np.clip(n[:, 2], 0, 1))
        rgb = col[:, :3] * sh[:, None]
        idx = np.argwhere(m)
        if o.tex.shape[2] == 4:
            a = col[:, 3:4]
            k = a[:, 0] > 0.02
            idx, a, rgb = idx[k], a[k], rgb[k]
            img[idx[:, 0], idx[:, 1]] = img[idx[:, 0], idx[:, 1]] * (1 - a) + rgb * a
        else:
            img[idx[:, 0], idx[:, 1]] = rgb
            zbest[idx[:, 0], idx[:, 1]] = depth[m]
    return np.clip(img, 0, 1)


def raycast_anchors(v, scene: HeadScene, cam: OrthoCam, P2_lm, z_min=None):
    """Front-most skin triangle under each 2D point -> (tri vertex ids (n,3), barycentrics (n,3), ok (n,))."""
    P2, Z = cam.project(v)
    tris = scene.tv
    tid, bary, depth = rasterize(P2, Z, tris, cam.res, cam.res, cull_backfaces=True)
    valid = tid >= 0
    if z_min is not None:
        valid &= depth > z_min
    from scipy.ndimage import distance_transform_edt
    _, (iy, ix) = distance_transform_edt(~valid, return_indices=True)
    out_t = np.zeros((len(P2_lm), 3), np.int64)
    out_b = np.zeros((len(P2_lm), 3))
    dist = np.zeros(len(P2_lm))
    for i, (x, y) in enumerate(P2_lm[:, :2]):
        r, c = int(np.clip(y, 0, cam.res - 1)), int(np.clip(x, 0, cam.res - 1))
        r2, c2 = iy[r, c], ix[r, c]
        dist[i] = np.hypot(r2 - r, c2 - c)
        t = tris[tid[r2, c2]]
        a, b, cc = P2[t[0]], P2[t[1]], P2[t[2]]
        # barycentrics of the exact landmark point in this triangle (may be slightly outside: fine)
        M = np.array([[a[0] - cc[0], b[0] - cc[0]], [a[1] - cc[1], b[1] - cc[1]]])
        w01 = np.linalg.solve(M, np.array([x - cc[0], y - cc[1]]))
        w = np.array([w01[0], w01[1], 1 - w01.sum()])
        if dist[i] > 0.5:  # landmark in a hole (eye opening / mouth gap): snap to the nearest skin point
            w = bary[r2, c2]
        out_t[i], out_b[i] = t, w
    return out_t, out_b, dist


def anchor_pos(v, at, ab):
    return np.einsum("nk,nkj->nj", ab, v[at])


# ============================================================================ helpers / groups
def vertex_groups(base):
    """group name -> vertex ids (from the faces of each group)."""
    out = {}
    for gi, g in enumerate(base.groups):
        f = base.fv[base.fgroup == gi]
        if len(f):
            out[g] = np.unique(f.ravel())
    return out


# ============================================================================ MakeHuman-target face fit
PAIR_SUFFIX = [("decr", "incr"), ("in", "out"), ("down", "up"), ("backward", "forward"), ("concave", "convex"),
               ("compress", "uncompress")]
FIT_GROUPS = ("head", "eyes", "nose", "mouth", "chin", "cheek", "forehead", "eyebrows", "ears", "neck")
EXCLUDE = ("head-trans-", "neck-trans-", "head-age-", "neck-double", "neck-scale-vert", "neck-back",
           "head-back-scale", "head-angle",
           # skull / forehead shape is hidden under the hair in the photo: never let landmarks drive it
           "head-diamond", "head-oval", "head-round", "head-square", "head-triangular", "head-invertedtriangular",
           "head-rectangular", "head-scale-", "forehead-",
           # profile-only or ageing details a frontal photo cannot see
           "eye-bag", "eye-eyefold-angle", "eye-push", "mouth-laugh-lines", "mouth-dimples", "nose-hump",
           "nose-greek", "nose-curve", "nose-septumangle", "nose-compression", "nose-nostrils-angle",
           "chin-cleft", "chin-prognathism", "ear-shape-", "ear-flap", "ear-lobe", "ear-scale-depth", "cheek-trans",
           "mouth-lowerlip-ext", "mouth-upperlip-ext", "mouth-cupidsbow-width")


def face_modifiers(mh: MH, groups=FIT_GROUPS, symmetric=True, allow=()):
    """[(label, [neg target rels], [pos target rels])]; one-sided shape targets get an empty neg list.
    l-/r- targets are tied into one symmetric variable when symmetric=True."""
    import os
    mods = {}
    for g in groups:
        d = mh.data(f"targets/{g}")
        names = sorted(f[:-7] for f in os.listdir(d) if f.endswith(".target"))
        for n in names:
            bare = n[2:] if n[:2] in ("l-", "r-") else n
            if any(bare.startswith(e) for e in EXCLUDE) and not any(bare.startswith(x) for x in allow):
                continue
            if g in ("nose", "mouth") and (n.endswith("-trans-in") or n.endswith("-trans-out")):
                continue  # lateral shifts of midline features
            stem, side, pair = n, None, ""
            for lo, hi in PAIR_SUFFIX:
                if n.endswith("-" + lo):
                    stem, side, pair = n[: -len(lo) - 1], 0, f":{lo}-{hi}"
                    break
                if n.endswith("-" + hi):
                    stem, side, pair = n[: -len(hi) - 1], 1, f":{lo}-{hi}"
                    break
            key = stem + pair
            if symmetric and (stem.startswith("l-") or stem.startswith("r-")):
                key = stem[2:] + pair
            ent = mods.setdefault(f"{g}/{key}", ([], []))
            rel = f"targets/{g}/{n}.target"
            (ent[1] if side in (1, None) else ent[0]).append(rel)
    return [(k, neg, pos) for k, (neg, pos) in sorted(mods.items())]


def target_dense(mh: MH, rels, n):
    D = np.zeros((n, 3))
    for r in rels:
        i, d = mh.target(r)
        D[i] += d
    return D


def fit_modifiers(mh, v0, at, ab, T, w_xy, w_z, extra=None, ridge=0.02, mods=None, bound=1.0):
    """Bounded linear least squares for MakeHuman modifier weights so the anchors hit the targets.
    T (m,3) target anchor positions (dm); w_xy / w_z (m,) weights.  extra: optional list of
    (rows (k,n) sparse selector producing positions, targets (k,3), weights (k,3)) silhouette terms.
    Returns (extra_targets [(rel, weight)], info)."""
    from scipy.optimize import lsq_linear
    mods = mods or face_modifiers(mh)
    n = len(v0)
    A0 = anchor_pos(v0, at, ab)
    cols = []
    Ds = []
    for label, neg, pos in mods:
        for sgn, rels in ((-1, neg), (1, pos)):
            if not rels:
                continue
            D = target_dense(mh, rels, n)
            Ds.append((label, sgn, rels))
            J = anchor_pos(D, at, ab)                      # (m,3)
            col = [(J[:, :2] * w_xy[:, None]).ravel(), J[:, 2] * w_z]
            if extra:
                for S, Tt, We in extra:
                    col.append(((S @ D) * We).ravel())
            cols.append(np.concatenate(col))
    Jm = np.stack(cols, 1)
    r = [((T - A0)[:, :2] * w_xy[:, None]).ravel(), (T - A0)[:, 2] * w_z]
    if extra:
        for S, Tt, We in extra:
            r.append(((Tt - S @ v0) * We).ravel())
    rhs = np.concatenate(r)
    k = Jm.shape[1]
    Jr = np.vstack([Jm, ridge * np.eye(k)])
    rr = np.concatenate([rhs, np.zeros(k)])
    sol = lsq_linear(Jr, rr, bounds=(0, bound), lsmr_tol="auto", max_iter=5000)
    wts = sol.x
    # a modifier is one slider: keep only the stronger side of each decr/incr pair and refit
    best = {}
    for j, (label, sgn, rels) in enumerate(Ds):
        if label not in best or wts[j] > wts[best[label]]:
            best[label] = j
    keep = np.zeros(k, bool)
    keep[list(best.values())] = True
    ub = np.where(keep, bound, 1e-12)
    sol = lsq_linear(Jr, rr, bounds=(np.zeros(k), ub), lsmr_tol="auto", max_iter=5000)
    wts = np.where(keep, sol.x, 0.0)
    out, info = [], []
    for (label, sgn, rels), wv in zip(Ds, wts):
        if wv > 1e-3:
            for rel in rels:
                out.append((rel, float(wv)))
            info.append((label, sgn, round(float(wv), 3)))
    info.sort(key=lambda t: -t[2])
    res0 = np.linalg.norm(rhs)
    res1 = np.linalg.norm(Jm @ wts - rhs)
    return out, {"weights": info, "residual_before": float(res0), "residual_after": float(res1)}


def similarity_2d(src, dst, w=None):
    """Weighted 2D similarity dst ~ s R (src - ms) + md."""
    w = np.ones(len(src)) if w is None else np.asarray(w, float)
    ms = (src * w[:, None]).sum(0) / w.sum()
    md = (dst * w[:, None]).sum(0) / w.sum()
    a, b = src - ms, dst - md
    Hm = (a * w[:, None]).T @ b
    U, _, Vt = np.linalg.svd(Hm)
    R = (U @ Vt).T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = (U @ Vt).T
    s = np.trace(R @ Hm) / ((a ** 2).sum(1) * w).sum()
    A = np.zeros((2, 3))
    A[:, :2] = s * R
    A[:, 2] = md - s * R @ ms
    return A


def silhouette_selectors(v, scene, cam, rows_px, n):
    """Front-view skin silhouette at pixel rows: sparse selectors (2k, n) giving the left / right
    silhouette surface points (as barycentric blends of vertices) and their pixel x."""
    P2, Z = cam.project(v)
    tid, bary, _ = rasterize(P2, Z, scene.tv, cam.res, cam.res)
    I, J, W, xs = [], [], [], []
    r = 0
    for y in rows_px:
        cols = np.nonzero(tid[y] >= 0)[0]
        if not len(cols):
            continue
        for c in (cols.min(), cols.max()):
            t = scene.tv[tid[y, c]]
            I += [r] * 3
            J += list(t)
            W += list(bary[y, c])
            xs.append(c + 0.5)
            r += 1
    return sp.csr_matrix((W, (I, J)), shape=(r, n)), np.array(xs)


def row_profile(mask):
    """Leftmost / rightmost set pixel per row (nan where the row is empty)."""
    H = mask.shape[0]
    L = np.full(H, np.nan)
    R = np.full(H, np.nan)
    for y in range(H):
        c = np.nonzero(mask[y])[0]
        if len(c):
            L[y], R[y] = c.min() + 0.5, c.max() + 0.5
    return L, R


def ear_bottom_row(prof, start, side, jump=9.0, span=160):
    """First row below `start` where the silhouette steps inwards (the ear lobe ends)."""
    for y in range(start, start + span):
        a, b = prof[y], prof[y + 4]
        if np.isfinite(a) and np.isfinite(b) and (b - a) * (-side) > jump:
            return y + 2
    return start + span // 2


def silhouette_terms(v, sc, cam, ph_L, ph_R, ph_ear, ear_mid, jaw_end, weight, n):
    """Linear silhouette constraints between the model's front-view skin silhouette and the photo's:
    x of the ear outer edges (ear band) and of the lower face / neck (jaw band), plus the y of the
    ear-lobe bottoms.  Returns (S (k,n) selector, targets (k,3), weights (k,3))."""
    res = cam.res
    P2, Z = cam.project(v)
    tid, bary, _ = rasterize(P2, Z, sc.tv, res, res)
    mL, mR = row_profile(tid >= 0)
    md_ear = [ear_bottom_row(mL, ear_mid, -1), ear_bottom_row(mR, ear_mid, +1)]
    I, J, W, T, Wt = [], [], [], [], []

    def add(y, x_px, tx=None, ty=None, w=(1.0, 0.0, 0.0)):
        c = int(np.clip(np.floor(x_px), 0, res - 1))
        if tid[y, c] < 0:
            return
        r = len(T)
        t = sc.tv[tid[y, c]]
        I.extend([r] * 3)
        J.extend(list(t))
        W.extend(list(bary[y, c]))
        tgt = np.zeros(3)
        if tx is not None:
            tgt[0] = (tx * 2 / res - 1) * cam.half + cam.center[0]
        if ty is not None:
            tgt[1] = (1 - ty * 2 / res) * cam.half + cam.center[1]
        T.append(tgt)
        Wt.append(np.asarray(w) * weight)

    for side, (mprof, pprof) in enumerate(((mL, ph_L), (mR, ph_R))):
        top = ear_mid - 60
        lo_band = max(ph_ear[side], md_ear[side]) + 14
        hi_band = min(ph_ear[side], md_ear[side]) - 14
        for y in list(range(top, hi_band, 8)) + list(range(lo_band, jaw_end, 8)):
            if np.isfinite(mprof[y]) and np.isfinite(pprof[y]):
                add(y, mprof[y] - 0.5 if side == 0 else mprof[y] - 0.5, tx=pprof[y])
        # ear-lobe bottom height
        y = md_ear[side] - 3
        if np.isfinite(mprof[y]):
            add(y, mprof[y] - 0.5, ty=ph_ear[side] - 3, w=(0.0, 2.0, 0.0))
    S = sp.csr_matrix((W, (I, J)), shape=(len(T), n))
    T = np.array(T)
    Wt = np.array(Wt)
    # rows with a zero weight keep their current value as target
    cur = S @ v
    T = np.where(Wt > 0, T, cur)
    return S, T, Wt


def eye_opening_terms(v, sc, cam, S2, weight, n, inset=(6.5, 2.0), corner_ext=1.0):
    """Linear constraints that make the model's eye openings (where the eyeball is the front-most
    surface, front view) match the photo's eye contours (MediaPipe, render px): lid heights across the
    middle of each eye and the corner positions."""
    import cv2
    res = cam.res
    P2, Z = cam.project(v)
    tid, bary, dsk = rasterize(P2, Z, sc.tv, res, res)
    ev = sc.eyes.fit(v)
    etv, _ = sc.eyes.mesh.triangles(sc.eye_mask)
    P2e, Ze = cam.project(ev)
    te, _, de = rasterize(P2e, Ze, etv, res, res)
    opening = (te >= 0) & (de > dsk)
    I, J, W, T, Wt = [], [], [], [], []

    def add(y, x, tx=None, ty=None):
        if not (0 <= y < res and 0 <= x < res) or tid[y, x] < 0:
            return
        r = len(T)
        t = sc.tv[tid[y, x]]
        I.extend([r] * 3)
        J.extend(list(t))
        W.extend(list(bary[y, x]))
        tgt = np.zeros(3)
        w = np.zeros(3)
        if tx is not None:
            tgt[0] = (tx * 2 / res - 1) * cam.half + cam.center[0]
            w[0] = weight
        if ty is not None:
            tgt[1] = (1 - ty * 2 / res) * cam.half + cam.center[1]
            w[1] = weight
        T.append(tgt)
        Wt.append(w)

    from face_texture import EYE_L, EYE_R
    for ring in (EYE_R, EYE_L):
        poly = np.zeros((res, res), np.uint8)
        cv2.fillPoly(poly, [np.round(S2[ring] * 8).astype(np.int32)], 1, shift=3)
        x0, x1 = S2[ring, 0].min(), S2[ring, 0].max()
        cx = 0.5 * (x0 + x1)
        box = np.zeros_like(opening)
        box[:, int(x0) - 15:int(x1) + 15] = True
        mo = opening & box & (np.abs(np.arange(res)[:, None] - S2[ring, 1].mean()) < 40)
        if not mo.any():
            continue
        for x in range(int(x0 + 0.2 * (x1 - x0)), int(x1 - 0.2 * (x1 - x0)), 3):
            pc = np.nonzero(poly[:, x])[0]
            mc = np.nonzero(mo[:, x])[0]
            if len(pc) < 2 or len(mc) < 2:
                continue
            add(mc.min() - 1, x, ty=pc.min() + inset[0])      # the photo contour sits on the lash line
            add(mc.max() + 1, x, ty=pc.max() + 1 - inset[1])
        ys, xs = np.nonzero(mo)
        # corners: leftmost / rightmost opening pixels
        # corners: the photo's almond eyes run out to thin inner / outer corners
        for sel, tx in ((xs.argmin(), x0 + inset[1] + 1 - corner_ext), (xs.argmax(), x1 - inset[1] - 1 + corner_ext)):
            y, x = ys[sel], xs[sel]
            add(y, x - 1 if tx < cx else x + 1, tx=tx)
    S = sp.csr_matrix((W, (I, J)), shape=(len(T), n))
    T = np.array(T).reshape(-1, 3)
    Wt = np.array(Wt).reshape(-1, 3)
    cur = S @ v
    return S, np.where(Wt > 0, T, cur), Wt


@dataclass
class FaceFit:
    extra_targets: list          # [(target rel, weight)] for BodyConfig.extra_targets
    photo_to_px: np.ndarray      # (2,3) affine: photo pixel -> fit-camera pixel
    cam: OrthoCam
    anchors: tuple               # (tri (468,3), bary (468,3)) on the base mesh
    info: dict


def fit_face(mh: MH, cfg: BodyConfig, lm_photo, cls_photo, mp_model, iters=3, ridge=0.05, wz=0.2, oval_weight=0.1,
             sil_weight=1.5, allow=("head-invertedtriangular", "head-oval"), eye_weight=3.0, log=print):
    """Fit MakeHuman face / head / neck modifiers so the model's frontal landmarks and lower-face
    silhouette match the photo.  lm_photo (478,3) MediaPipe landmarks in photo pixels; cls_photo (H,W)
    selfie-multiclass map of the photo (2 body skin, 3 face skin)."""
    import cv2
    from build_body import morph
    base = mh.base()
    v0, _ = morph(mh, base, cfg, log=lambda *a: None)
    n = len(v0)
    sc = HeadScene(mh, cfg)
    eyec = sc.eyes.fit(v0).mean(0)
    cam = OrthoCam(np.array([0.0, eyec[1] - 0.15, 0.0]), 1.6)
    img = render(sc.objects(v0), cam)
    lmA = mp_detect((img * 255).astype(np.uint8), mp_model)
    if lmA is None:
        raise RuntimeError("no face found on the model render")
    at, ab, _ = raycast_anchors(v0, sc, cam, lmA[:468])
    A0 = anchor_pos(v0, at, ab)
    S = np.asarray(lm_photo, float)[:468]
    w = np.ones(468)
    w[UPPER_FOREHEAD] = 0.1
    w[LEFT_BROW + RIGHT_BROW] = 0.5
    w[LEFT_EYE + RIGHT_EYE] = 1.0
    w[LIPS_INNER + LIPS_OUTER] = 1.5
    oval = [i for i in FACE_OVAL if i not in UPPER_FOREHEAD]
    w[oval] = oval_weight
    Aff = similarity_2d(S[:, :2], lmA[:468, :2], w)
    s = np.sqrt(abs(np.linalg.det(Aff[:, :2])))
    S2 = S[:, :2] @ Aff[:, :2].T + Aff[:, 2]
    zS, zA = S[:, 2] * s, lmA[:468, 2]
    mean_w = lambda x: (x * w).sum() / w.sum()
    dz = -((zS - mean_w(zS)) - (zA - mean_w(zA))) / cam.px_per_dm
    T = A0.copy()
    T[:, :2] = cam.unproject_xy(S2)
    T[:, 2] = A0[:, 2] + dz
    wzv = w * wz
    wzv[oval] = 0.0
    feedback = np.ones(468)
    feedback[oval] = 0.0
    feedback[UPPER_FOREHEAD] = 0.0
    # photo silhouette: ear outer edges, ear-lobe height, lower face and neck (above the collar)
    cls_r = cv2.warpAffine(np.asarray(cls_photo, np.uint8), Aff, (cam.res, cam.res), flags=cv2.INTER_NEAREST)
    skin = (cls_r == 2) | (cls_r == 3)
    chin = S2[152, 1]
    ear_mid = int(S2[[234, 454], 1].mean())
    ph_L, ph_R = row_profile(skin)
    ph_ear = [ear_bottom_row(ph_L, ear_mid, -1), ear_bottom_row(ph_R, ear_mid, +1)]
    jaw_end = int(chin + 0.45 * (chin - S2[1, 1]))
    log(f"  photo ear bottoms at rows {ph_ear}")
    hist = []
    et = []
    v = v0
    for it in range(iters + 1):
        Ssel, Tt, We = silhouette_terms(v, sc, cam, ph_L, ph_R, ph_ear, ear_mid, jaw_end, sil_weight, n)
        Se, Te, We_e = eye_opening_terms(v, sc, cam, S2, eye_weight, n)
        Ssel, Tt, We = sp.vstack([Ssel, Se]).tocsr(), np.vstack([Tt, Te]), np.vstack([We, We_e])
        Tt0 = Tt
        et, info = fit_modifiers(mh, v0, at, ab, T, w, wzv, extra=[(Ssel, Tt0, We)], ridge=ridge,
                                 mods=face_modifiers(mh, allow=allow))
        v, _ = morph(mh, base, BodyConfig(**{**cfg.__dict__, "extra_targets": list(cfg.extra_targets) + et}),
                     log=lambda *a: None)
        sil_err = np.abs((Ssel @ v)[:, 0] - Tt[:, 0]).mean() * cam.px_per_dm
        sil_err0 = np.abs((Ssel @ v0)[:, 0] - Tt0[:, 0]).mean() * cam.px_per_dm
        img = render(sc.objects(v), cam)
        lm1 = mp_detect((img * 255).astype(np.uint8), mp_model)
        res2 = S2 - lm1[:468, :2]
        err = float(np.linalg.norm(res2, axis=1)[w >= 1].mean())
        hist.append(err)
        log(f"  face fit iter {it}: landmark residual {err:.2f} px ({err / cam.px_per_dm * 100:.2f} mm), "
            f"silhouette err {sil_err0:.1f} -> {sil_err:.1f} px")
        if it < iters:
            T[:, :2] += 0.7 * feedback[:, None] * res2 * np.array([1.0, -1.0]) / cam.px_per_dm
    info.update({"landmark_residual_px": hist, "px_per_dm": cam.px_per_dm,
                 "residual_before_px": float(np.linalg.norm(S2 - lmA[:468, :2], axis=1)[w >= 1].mean())})
    return FaceFit(et, Aff, cam, (at, ab), info), v, img
