"""Stage 2 — fuse the analysis into a closed, textured 3D bust.

Front surface : Depth-Anything-V2 disparity, calibrated to MediaPipe's metric-ish
                landmark depth (affine fit + thin-plate residual over the face).
Back surface  : silhouette inflation. sqrt of the Poisson solution (lap h = -1,
                h = 0 on the outline) is exactly a sphere for a circular outline and
                an ellipsoid for an elliptic one, so it gives a plausible skull /
                torso volume behind the harmonic "rim" surface of the outline.

Outputs (odyssey/film/assets):
  bust.glb        textured mesh (front = photo, back = synthesized hair / cloth)
  points.bin      dense coloured point cloud of the front surface (+ back)
  facemesh.json   478 landmarks lifted onto the surface + canonical triangulation
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import trimesh
from PIL import Image
from scipy.interpolate import RBFInterpolator

WORK = Path(sys.argv[1])
MODELS = Path(sys.argv[2])
OUT = Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)

PX_PER_UNIT = 200.0          # full-res photo pixels per world unit (~7.5 cm)
DEPTH_GAIN = 1.0             # global relief gain on top of the landmark calibration
K_HEAD, K_BODY = 2.35, 1.05  # back-inflation gains (2.0 = sphere)
FRONT_SHELL = 0.55           # minimum front roundness relative to back inflation

A = np.load(WORK / "analysis.npz")
lm, cls, disp = A["lm"], A["cls"], A["disp"].astype(np.float64)
photo = cv2.cvtColor(cv2.imread(str(WORK / "photo_rect.png")), cv2.COLOR_BGR2RGB)
N = cls.shape[0]  # 1024

# ------------------------------------------------------------------ masks
def clean(m, r=3):
    m = m.astype(np.uint8)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    m = cv2.morphologyEx(cv2.morphologyEx(m, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 4)
    if n > 1:
        m = (lab == 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    # fill holes
    inv = 1 - m
    n, lab = cv2.connectedComponents(inv, connectivity=4)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    for i in range(1, n):
        if i not in border:
            m[lab == i] = 1
    return m.astype(bool)

subject = clean(cls > 0, 4)
yy, xx = np.mgrid[0:N, 0:N].astype(np.float64)
cx = lm[1, 0]
# classical bust cut: a U-shaped lower edge that clears the photo border
cut = 985 - 170 * ((xx - cx) / 470.0) ** 2
bust = subject & (yy < cut) & (np.abs(xx - cx) < 470)
bust = clean(bust, 2)
head = bust & ((cls == 1) | (cls == 3) | (cls == 2))       # hair, face, neck
body = bust & ((cls == 2) | (cls == 4) | (cls == 5))       # neck, clothes
head = clean(head, 3) & bust
body = clean(body, 3) & bust

# ------------------------------------------------------------------ calibrated depth
u = np.clip(lm[:, 0].round().astype(int), 0, N - 1)
v = np.clip(lm[:, 1].round().astype(int), 0, N - 1)
zmp = -lm[:, 2]                                   # toward camera = positive
a, b = np.linalg.lstsq(np.c_[disp[v, u], np.ones(len(u))], zmp, rcond=None)[0]
Zda = a * disp + b
res = zmp - Zda[v, u]
rbf = RBFInterpolator(lm[:, :2], res - res.mean(), kernel="thin_plate_spline", smoothing=40.0)
hull = cv2.convexHull(lm[:468, :2].astype(np.float32)).astype(np.int32)
face_w = np.zeros((N, N), np.float32)
cv2.fillConvexPoly(face_w, hull, 1.0)
face_w = cv2.GaussianBlur(cv2.dilate(face_w, np.ones((25, 25))), (0, 0), 18)
ys, xs = np.nonzero(face_w > 1e-3)
corr = np.zeros((N, N))
corr[ys, xs] = rbf(np.c_[xs, ys].astype(np.float64))
Zf_full = (Zda + res.mean() + face_w * corr) * DEPTH_GAIN
print(f"affine fit a={a:.2f} b={b:.2f}; residual rms {np.sqrt((res**2).mean()):.1f}px")

# ------------------------------------------------------------------ half-res solve
def push_pull(img, m, levels=9):
    """Bleed foreground values into the background (kills halos at the outline)."""
    if img.ndim == 2:
        return push_pull(np.repeat(img[..., None], 3, -1), m, levels)[..., 0]
    pyr = [(img * m[..., None], m)]
    for _ in range(levels):
        i, w = pyr[-1]
        pyr.append((cv2.pyrDown(i), cv2.pyrDown(w)))
    i, w = pyr[-1]
    acc = i / np.maximum(w[..., None], 1e-6)
    for i, w in reversed(pyr[:-1]):
        up = cv2.resize(acc, (i.shape[1], i.shape[0]), interpolation=cv2.INTER_LINEAR)
        acc = i + (1 - np.clip(w, 0, 1)[..., None]) * up   # i is premultiplied by w
    return acc
G = 2
M = N // G
def down(img, interp=cv2.INTER_AREA):
    return cv2.resize(img.astype(np.float32), (M, M), interpolation=interp)

bust_h = down(bust) > 0.5
head_h = down(head) > 0.5
body_h = down(body) > 0.5
Zf = down(Zf_full).astype(np.float64) / G  # in half-res pixel units

def interior_boundary(m):
    er = cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8), borderValue=0).astype(bool)
    return er, m & ~er

def solve(mask, rhs=None, bvals=None):
    """Solve lap(f) = rhs on the interior of mask with f = bvals on its rim."""
    inner, rim = interior_boundary(mask)
    idx = -np.ones(mask.shape, np.int64)
    ys, xs = np.nonzero(inner)
    idx[ys, xs] = np.arange(len(ys))
    n = len(ys)
    rows, cols, vals = [np.arange(n)], [np.arange(n)], [np.full(n, -4.0)]
    b = np.zeros(n) if rhs is None else np.full(n, float(rhs))
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        ny, nx = ys + dy, xs + dx
        j = idx[ny, nx]
        ok = j >= 0
        rows.append(np.arange(n)[ok]); cols.append(j[ok]); vals.append(np.ones(ok.sum()))
        if bvals is not None:
            b[~ok] -= bvals[ny[~ok], nx[~ok]]
    L = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), (n, n))
    sol = spla.spsolve(L.tocsc(), b)
    out = np.zeros(mask.shape) if bvals is None else bvals.copy()
    out[ys, xs] = sol
    out[~mask] = 0
    return out

# Depth-Anything blurs across the outline, so the last few pixels are unreliable:
# re-extrapolate the depth from well inside the silhouette before using it on the rim.
inner8 = cv2.erode(bust_h.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
Zin = push_pull(Zf.astype(np.float32), inner8).astype(np.float64)
Zf = np.where(inner8 > 0.5, Zf, Zin)
# Rim plane E: a frontal silhouette is traced by the head's widest section, i.e. the
# coronal plane through the ears. Anchor it on the face-oval landmarks beside the ears.
EAR_LMS = [234, 454, 93, 323, 127, 356]
ear_z = np.mean([Zf_full[int(lm[i, 1]), int(lm[i, 0])] for i in EAR_LMS]) - 25.0
E = np.full((M, M), ear_z / G)
# inflation thickness behind the rim
Th = K_HEAD * np.sqrt(np.maximum(solve(head_h, -1.0), 0))
Tb = K_BODY * np.sqrt(np.maximum(solve(body_h, -1.0), 0))
T = np.maximum(Th, Tb)
T = np.where(bust_h, cv2.GaussianBlur(T.astype(np.float32), (0, 0), 2.0), 0)
_, rim = interior_boundary(bust_h)
T[rim] = 0

# front = measured relief, rolled smoothly onto the rim, never thinner than a
# fraction of the inflated shell (keeps the sides of the skull round)
def smax(x, y, k):
    return np.maximum(x, y) + k * np.log1p(np.exp(-np.abs(x - y) / k))
dist = cv2.distanceTransform(bust_h.astype(np.uint8), cv2.DIST_L2, 3)
ramp = np.clip(dist / 16.0, 0, 1); ramp = ramp * ramp * (3 - 2 * ramp)
front = E + smax(np.maximum(Zf - E, 0) * ramp, FRONT_SHELL * T, 3.0)
front[rim] = E[rim]
back = E - T

# ------------------------------------------------------------------ world coords
X0, Y0 = lm[1, 0], 0.5 * (lm[33, 1] + lm[263, 1])
hy, hx = np.nonzero(head_h)
Z0 = 0.5 * (front[hy, hx].max() + back[hy, hx].min()) * G

def world(px, py, z_half):
    return np.c_[(px - X0) / PX_PER_UNIT, (Y0 - py) / PX_PER_UNIT, (z_half * G - Z0) / PX_PER_UNIT]

gy, gx = np.nonzero(bust_h)
vid = -np.ones((M, M), np.int64)
vid[gy, gx] = np.arange(len(gy))
nv = len(gy)
px, py = (gx + 0.5).astype(np.float64), (gy + 0.5).astype(np.float64)
Bm = cv2.GaussianBlur(bust_h.astype(np.float32), (0, 0), 1.6)
gBy, gBx = np.gradient(Bm)
on_rim = rim[gy, gx] | (dist[gy, gx] < 2.5)
g2 = gBx[gy, gx] ** 2 + gBy[gy, gx] ** 2 + 1e-6
step = np.clip((Bm[gy, gx] - 0.5) / g2, -1.5 / np.sqrt(g2), 1.5 / np.sqrt(g2)) * on_rim
px = px - step * gBx[gy, gx]; py = py - step * gBy[gy, gx]
px, py = px * G, py * G
Vf = world(px, py, front[gy, gx])
Vb = world(px, py, back[gy, gx])
V = np.vstack([Vf, Vb])
UV = np.vstack([np.c_[px / N * 0.5, 1 - py / N], np.c_[0.5 + px / N * 0.5, 1 - py / N]])

a_ = vid[:-1, :-1]; b_ = vid[:-1, 1:]; c_ = vid[1:, :-1]; d_ = vid[1:, 1:]
tris = []
for t in ((a_, c_, b_), (b_, c_, d_)):   # counter-clockwise seen from +Z (y flipped)
    ok = (t[0] >= 0) & (t[1] >= 0) & (t[2] >= 0)
    tris.append(np.c_[t[0][ok], t[1][ok], t[2][ok]])
# cells with exactly three corners soften the staircase outline
full = (a_ >= 0) & (b_ >= 0) & (c_ >= 0) & (d_ >= 0)
for t, cond in (((a_, c_, d_), (b_ < 0)), ((a_, d_, b_), (c_ < 0))):
    ok = cond & (t[0] >= 0) & (t[1] >= 0) & (t[2] >= 0) & ~full
    tris.append(np.c_[t[0][ok], t[1][ok], t[2][ok]])
Ff = np.vstack(tris)
Fb = Ff[:, ::-1] + nv
F = np.vstack([Ff, Fb])
# normals from a copy whose rim is welded (front/back share rim vertices) so the
# silhouette seam shades continuously; the exported mesh keeps split UVs
on_rim_v = rim[gy, gx]
weld = np.where(np.r_[np.zeros(nv, bool), on_rim_v], np.r_[np.arange(nv), np.arange(nv)], np.arange(2 * nv))
FW = weld[F]
# Taubin-smooth the band near the outline: the single view says least about it, and
# the grid staircase there otherwise reads as streaks when seen from the side
e = np.r_[FW[:, [0, 1]], FW[:, [1, 2]], FW[:, [2, 0]]]
adj = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), (2 * nv, 2 * nv)).tocsr()
adj = ((adj + adj.T) > 0).astype(np.float64)
deg = np.asarray(adj.sum(1)).ravel()
Lw = sp.diags(1.0 / np.maximum(deg, 1)) @ adj
w_near = np.clip(1.0 - np.r_[dist[gy, gx], dist[gy, gx]] / 14.0, 0, 1)[:, None] * (deg > 0)[:, None]
for _ in range(25):
    for f in (0.5, -0.53):
        V = V + f * w_near * (Lw @ V - V)
V = V[weld]
welded = trimesh.Trimesh(V, FW, process=False)
NRM = np.asarray(welded.vertex_normals).copy()
w_n = np.clip(1.0 - np.r_[dist[gy, gx], dist[gy, gx]] / 20.0, 0, 1)[:, None] * (deg > 0)[:, None]
for _ in range(12):                      # relax shading normals along the outline band
    NRM = NRM + w_n * (Lw @ NRM - NRM)
    NRM /= np.linalg.norm(NRM, axis=1, keepdims=True) + 1e-9
NRM = NRM[weld]
print(f"mesh: {len(V)} vertices, {len(F)} triangles")

# ------------------------------------------------------------------ textures
fg = bust.astype(np.float32)
col = photo.astype(np.float32)
inner_fg = cv2.erode(fg, np.ones((3, 3)))
front_tex = push_pull(col, inner_fg)
front_tex = np.where(inner_fg[..., None] > 0.5, col, front_tex)

# back of head: procedural strands in the photo's own hair colours; back of torso:
# the shirt's median colour with a faint weave
rng = np.random.default_rng(7)
hair_px = photo[(cls == 1) & bust].astype(np.float32)
lum = hair_px.mean(1)
hair_dark, hair_lite = np.median(hair_px[lum < np.percentile(lum, 40)], 0), np.median(hair_px[lum > np.percentile(lum, 85)], 0)
noise = rng.normal(0, 1, (N, N)).astype(np.float32)
kern = np.zeros((41, 41), np.float32); kern[:, 20] = 1; kern /= kern.sum()
yy_, xx_ = np.mgrid[0:N, 0:N].astype(np.float32)
warp_x = (xx_ + 14 * np.sin(yy_ / 57.0) + 9 * np.sin(yy_ / 23.0 + xx_ / 91.0)).astype(np.float32)
strands = cv2.remap(cv2.filter2D(noise, -1, kern), warp_x, yy_, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
strands = (strands - strands.mean()) / (strands.std() + 1e-6)
t_ = np.clip(0.25 + 0.22 * strands + 0.1 * cv2.GaussianBlur(noise, (0, 0), 30) * 8, 0, 1)[..., None]
hair_tile = hair_dark * (1 - t_) + hair_lite * t_
shirt = np.median(photo[cls == 4], 0).astype(np.float32)
weave = cv2.GaussianBlur(noise, (0, 0), 1.0)[..., None] * 6
back_tex = np.where((cls == 1)[..., None] | (cls == 3)[..., None], hair_tile, shirt + weave)
back_tex = np.where((cls == 2)[..., None], col * 0.85, back_tex)
atlas = np.clip(np.concatenate([front_tex, back_tex], 1), 0, 255).astype(np.uint8)
Image.fromarray(atlas).save(OUT / "bust_atlas.jpg", quality=92)
Image.fromarray(np.clip(front_tex, 0, 255).astype(np.uint8)).save(OUT / "photo_front.jpg", quality=92)
Image.fromarray(photo).save(OUT / "photo_full.jpg", quality=93)

mesh = trimesh.Trimesh(V, F, vertex_normals=NRM, process=False)
mat = trimesh.visual.material.PBRMaterial(baseColorTexture=Image.fromarray(atlas),
                                          metallicFactor=0.0, roughnessFactor=0.75)
mesh.visual = trimesh.visual.TextureVisuals(uv=UV, material=mat)
mesh.export(OUT / "bust.glb", include_normals=True)
trimesh.Trimesh(V, F, process=False).export(WORK / "bust_geometry.obj")

# ------------------------------------------------------------------ point cloud
# full-res front surface: reuse the half-res rim/inflation fields, full-res depth detail
def up(f):
    return cv2.resize(f.astype(np.float32), (N, N), interpolation=cv2.INTER_LINEAR).astype(np.float64) * G
E_full, T_full, Zin_full = up(E), up(T), up(Zin)
inner_full = cv2.resize(inner8, (N, N), interpolation=cv2.INTER_LINEAR) > 0.5
Zf_full = np.where(inner_full, Zf_full, Zin_full)
dist_full = cv2.distanceTransform(bust.astype(np.uint8), cv2.DIST_L2, 3) / G
ramp_full = np.clip(dist_full / 16.0, 0, 1); ramp_full = ramp_full * ramp_full * (3 - 2 * ramp_full)
front_full = E_full + smax(np.maximum(Zf_full - E_full, 0) * ramp_full, FRONT_SHELL * T_full, 6.0)
py1, px1 = np.nonzero(bust)
P_front = world(px1 + 0.5, py1 + 0.5, front_full[py1, px1] / G)
C_front = photo[py1, px1]
K_front = cls[py1, px1]
P_back, C_back = Vb, (back_tex[gy * G, gx * G]).clip(0, 255).astype(np.uint8)
K_back = np.full(len(P_back), 9, np.uint8)
P = np.vstack([P_front, P_back]).astype(np.float32)
C = np.vstack([C_front, C_back]).astype(np.uint8)
K = np.concatenate([K_front, K_back]).astype(np.uint8)
with open(OUT / "points.bin", "wb") as f:
    f.write(np.array([len(P), len(P_front)], np.uint32).tobytes())
    f.write(P.tobytes()); f.write(C.tobytes()); f.write(K.tobytes())
print(f"points: {len(P_front)} front + {len(P_back)} back")

# ------------------------------------------------------------------ face mesh
tri = []
for line in open(MODELS / "canonical_face_model.obj"):
    if line.startswith("f "):
        tri.append([int(t.split("/")[0]) - 1 for t in line.split()[1:4]])
lu, lv = lm[:, 0], lm[:, 1]
lz = cv2.remap(front_full.astype(np.float32), lu.astype(np.float32)[None], lv.astype(np.float32)[None],
               cv2.INTER_LINEAR)[0]
LP = world(lu, lv, lz / G + 1.5 / G)
json.dump({"points": np.round(LP, 5).tolist(), "triangles": tri,
           "px_per_unit": PX_PER_UNIT, "image_px": N,
           "origin_px": [float(X0), float(Y0), float(Z0)],
           "rim_z": float((ear_z - Z0) / PX_PER_UNIT)},
          open(OUT / "facemesh.json", "w"))

# ------------------------------------------------------------------ sanity numbers (cm @ ~27 px/cm)
nose = LP[1]; earL = LP[234]
print(f"nose-to-ear depth {(nose[2]-earL[2]) * PX_PER_UNIT / 27:.1f} cm, "
      f"head depth {(front[hy,hx].max()-back[hy,hx].min()) * G / 27:.1f} cm, "
      f"head width {(hx.max()-hx.min()) * G / 27:.1f} cm")
print("bounds", V.min(0).round(2), V.max(0).round(2))
