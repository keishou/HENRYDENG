"""Small vectorised numpy triangle rasteriser (z-buffer, barycentrics), used for landmark renders of the
model head and for baking textures in UV space.  No GPU / OpenGL needed.

    tid, bary, depth = rasterize(P2, Z, tris, W, H)     # P2 (N,2) pixel coords (x right, y down), Z bigger = nearer
    img = shade_uv(tid, bary, uv, tuv, texture)         # sample a texture at the rasterised fragments

Pixel (i, j) has its centre at (j + 0.5, i + 0.5).  tid = -1 where nothing is drawn.
"""
from __future__ import annotations

import numpy as np


def rasterize(P2, Z, tris, W, H, chunk=400_000, cull_backfaces=False):
    P2 = np.asarray(P2, np.float64)
    Z = np.asarray(Z, np.float64)
    tris = np.asarray(tris, np.int64)
    a, b, c = P2[tris[:, 0]], P2[tris[:, 1]], P2[tris[:, 2]]
    area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    keep = np.abs(area) > 1e-12
    if cull_backfaces:
        keep &= area < 0  # y down: counter-clockwise in world (front facing) is clockwise on screen
    x0 = np.clip(np.floor(np.minimum(np.minimum(a[:, 0], b[:, 0]), c[:, 0]) - 0.5), 0, W - 1).astype(np.int64)
    x1 = np.clip(np.ceil(np.maximum(np.maximum(a[:, 0], b[:, 0]), c[:, 0]) - 0.5), 0, W - 1).astype(np.int64)
    y0 = np.clip(np.floor(np.minimum(np.minimum(a[:, 1], b[:, 1]), c[:, 1]) - 0.5), 0, H - 1).astype(np.int64)
    y1 = np.clip(np.ceil(np.maximum(np.maximum(a[:, 1], b[:, 1]), c[:, 1]) - 0.5), 0, H - 1).astype(np.int64)
    inside_img = (np.maximum(np.maximum(a[:, 0], b[:, 0]), c[:, 0]) >= 0) & \
                 (np.minimum(np.minimum(a[:, 0], b[:, 0]), c[:, 0]) <= W) & \
                 (np.maximum(np.maximum(a[:, 1], b[:, 1]), c[:, 1]) >= 0) & \
                 (np.minimum(np.minimum(a[:, 1], b[:, 1]), c[:, 1]) <= H)
    keep &= inside_img
    ids = np.nonzero(keep)[0]
    bw = x1[ids] - x0[ids] + 1
    bh = y1[ids] - y0[ids] + 1
    n = bw * bh
    depth = np.full(W * H, -np.inf)
    tid = np.full(W * H, -1, np.int64)
    bary = np.zeros((W * H, 3))
    # process in chunks of triangles so the candidate list stays bounded
    csum = np.cumsum(n)
    start = 0
    while start < len(ids):
        base = csum[start - 1] if start else 0
        stop = int(np.searchsorted(csum, base + chunk, side="right"))
        stop = max(stop, start + 1)
        sel = ids[start:stop]
        nn = n[start:stop]
        t = np.repeat(np.arange(len(sel)), nn)
        off = np.arange(nn.sum()) - np.repeat(np.cumsum(nn) - nn, nn)
        bws = bw[start:stop][t]
        px = x0[sel][t] + off % bws
        py = y0[sel][t] + off // bws
        tri = tris[sel][t]
        A, B, Cc = P2[tri[:, 0]], P2[tri[:, 1]], P2[tri[:, 2]]
        fx, fy = px + 0.5, py + 0.5
        ar = area[sel][t]
        w0 = ((B[:, 0] - fx) * (Cc[:, 1] - fy) - (B[:, 1] - fy) * (Cc[:, 0] - fx)) / ar
        w1 = ((Cc[:, 0] - fx) * (A[:, 1] - fy) - (Cc[:, 1] - fy) * (A[:, 0] - fx)) / ar
        w2 = 1.0 - w0 - w1
        eps = -1e-9
        ins = (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
        if ins.any():
            w0, w1, w2 = w0[ins], w1[ins], w2[ins]
            tri = tri[ins]
            z = w0 * Z[tri[:, 0]] + w1 * Z[tri[:, 1]] + w2 * Z[tri[:, 2]]
            pix = py[ins] * W + px[ins]
            o = np.lexsort((-z, pix))
            pix_o = pix[o]
            first = np.ones(len(o), bool)
            first[1:] = pix_o[1:] != pix_o[:-1]
            o = o[first]
            pix_o = pix_o[first]
            better = z[o] > depth[pix_o]
            o, pix_o = o[better], pix_o[better]
            depth[pix_o] = z[o]
            tid[pix_o] = sel[t[ins][o]]
            bary[pix_o] = np.stack([w0[o], w1[o], w2[o]], 1)
        start = stop
    return tid.reshape(H, W), bary.reshape(H, W, 3), depth.reshape(H, W)


def interp(tid, bary, tris, attr):
    """Interpolate a per-vertex attribute (N,C) at the rasterised fragments -> (H,W,C) (0 where empty)."""
    attr = np.asarray(attr)
    H, W = tid.shape
    out = np.zeros((H, W, attr.shape[1]), attr.dtype if attr.dtype.kind == "f" else np.float64)
    m = tid >= 0
    t = tris[tid[m]]
    bb = bary[m]
    out[m] = attr[t[:, 0]] * bb[:, :1] + attr[t[:, 1]] * bb[:, 1:2] + attr[t[:, 2]] * bb[:, 2:3]
    return out


def sample_bilinear(img, x, y):
    """img (H,W,C) float, x/y float pixel coords (pixel centres at +0.5) -> (...,C)."""
    H, W = img.shape[:2]
    x = np.clip(np.asarray(x, np.float64) - 0.5, 0, W - 1.000001)
    y = np.clip(np.asarray(y, np.float64) - 0.5, 0, H - 1.000001)
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    x1 = np.minimum(x0 + 1, W - 1)
    y1 = np.minimum(y0 + 1, H - 1)
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy)
            + img[y1, x0] * (1 - fx) * fy + img[y1, x1] * fx * fy)
