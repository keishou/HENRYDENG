"""Small multi-part software renderer (numpy) used for landmark detection on synthetic heads and for checks.

Layer = dict(v=(N,3) metres, tris=(T,3), uv=(N,2) glTF v-down, tex=(h,w,3|4) float, alpha='OPAQUE'|'BLEND'|'MASK',
             color=(3,) optional, light=bool)
"""
from __future__ import annotations

import numpy as np

from avlib import interp, rasterize, vertex_normals


def sample(tex, uv):
    th, tw = tex.shape[:2]
    x = np.clip(uv[:, 0] * tw - 0.5, 0, tw - 1)
    y = np.clip(uv[:, 1] * th - 0.5, 0, th - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, tw - 1), np.minimum(y0 + 1, th - 1)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    return (tex[y0, x0] * (1 - fx) * (1 - fy) + tex[y0, x1] * fx * (1 - fy) + tex[y1, x0] * (1 - fx) * fy + tex[y1, x1] * fx * fy)


def shade(cam, L, tri_img, bary, m):
    if L.get("tex") is not None:
        uvp = interp(L["uv"], L["tris"], tri_img, bary)[m]
        col = sample(L["tex"], uvp)
    else:
        col = np.tile(np.r_[np.asarray(L.get("color", (0.7, 0.7, 0.7)), float), 1.0], (m.sum(), 1))
    if col.shape[1] == 3:
        col = np.c_[col, np.ones(len(col))]
    if L.get("light", True):
        n = interp(vertex_normals(L["v"], L["tris"]), L["tris"], tri_img, bary)[m]
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        ldir = cam.R.T @ np.array([0.3, 0.45, 1.0])
        ldir /= np.linalg.norm(ldir)
        # two-sided lighting (alpha cards / inner surfaces)
        lam = np.abs(n @ ldir) if L.get("two_sided") else np.clip(n @ ldir, 0, 1)
        sh = L.get("ambient", 0.5) + (1 - L.get("ambient", 0.5)) * lam
        col[:, :3] *= sh[:, None]
    return col


def render(cam, layers, bg=(0.5, 0.5, 0.5)):
    H, W = cam.H, cam.W
    img = np.tile(np.asarray(bg, float), (H, W, 1))
    zbuf = np.full((H, W), np.inf)
    ids = np.full((H, W), -1, np.int32)
    # opaque / mask layers first (each with its own raster, merged by depth)
    for li, L in enumerate(layers):
        if L.get("alpha", "OPAQUE") == "BLEND":
            continue
        p = cam.project(L["v"])
        tri_img, bary, dep = rasterize(p[:, :2], L["tris"], W, H, Z=p[:, 2])
        m = (tri_img >= 0) & (dep < zbuf)
        if not m.any():
            continue
        col = shade(cam, L, tri_img, bary, m)
        if L.get("alpha") == "MASK":
            keep = col[:, 3] >= L.get("cutoff", 0.5)
            mm = np.zeros_like(m)
            mm[m] = keep
            col = col[keep]
            m = mm
        img[m] = col[:, :3]
        zbuf[m] = dep[m]
        ids[m] = li
    # blended layers back-to-front by mean depth
    bl = [(li, L) for li, L in enumerate(layers) if L.get("alpha") == "BLEND"]
    bl.sort(key=lambda x: -cam.project(x[1]["v"])[:, 2].mean())
    for li, L in bl:
        p = cam.project(L["v"])
        tri_img, bary, dep = rasterize(p[:, :2], L["tris"], W, H, Z=p[:, 2])
        m = (tri_img >= 0) & (dep < zbuf + L.get("zbias", 0.0))
        if not m.any():
            continue
        col = shade(cam, L, tri_img, bary, m)
        a = col[:, 3:4] * L.get("opacity", 1.0)
        img[m] = img[m] * (1 - a) + col[:, :3] * a
    return np.clip(img, 0, 1), zbuf, ids
