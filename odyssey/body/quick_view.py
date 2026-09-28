"""Fast software preview (matplotlib, flat shaded) of a build_body model: rest and stand pose, 3 views.
    python3 odyssey/body/quick_view.py OUT.png [--tex 512]
Debug aid only; the real previews come from render_body_bpy.py (Blender Cycles on the exported GLB)."""
import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_body import BodyConfig, build  # noqa: E402
from mh_rig import Rig, top_k  # noqa: E402

COL = {"skin": (0.85, 0.72, 0.62), "outfit": (0.25, 0.26, 0.3), "shoes": (0.15, 0.15, 0.15),
       "eyes": (0.9, 0.9, 0.9), "eyebrows": (0.1, 0.1, 0.1), "eyelashes": (0.1, 0.1, 0.1),
       "teeth": (0.9, 0.9, 0.85), "tongue": (0.8, 0.4, 0.4), "hair": (0.1, 0.1, 0.1)}


def tris_of(p):
    fv = p.fv if p.face_mask is None else p.fv[p.face_mask]
    q = fv[:, 3] != fv[:, 2]
    return np.vstack([fv[:, [0, 1, 2]], fv[q][:, [0, 2, 3]]])


def draw(ax, X, T, cols, az):
    from matplotlib.collections import PolyCollection
    a = np.radians(az)
    d = np.array([np.sin(a), 0.0, np.cos(a)])
    ex = np.cross([0, 1, 0], d); ex /= np.linalg.norm(ex)
    ey = np.array([0, 1.0, 0])
    P = np.stack([X @ ex, X @ ey, X @ d], -1)
    tri = P[T]
    n = np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    L = d * 0.5 + np.array([0.3, 0.8, 0.2]); L /= np.linalg.norm(L)
    sh = np.clip(n @ L, 0, 1) * 0.7 + 0.3
    vis = (n @ d) > -0.05
    o = np.argsort(tri[:, :, 2].mean(1))
    o = o[vis[o]]
    ax.add_collection(PolyCollection(tri[o][:, :, :2], facecolors=np.clip(cols[o] * sh[o, None], 0, 1),
                                     edgecolors="none", antialiased=False))


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--tex", type=int, default=512)
    a = ap.parse_args()
    m = build(BodyConfig(tex_size=a.tex), log=lambda *x: None)
    rig, sh = m["rig"], m["shift"]
    E, D, H = m["pose"]
    Xr, Xp, T, C = [], [], [], []
    off = 0
    for p in m["parts"]:
        used = np.unique(tris_of(p))
        remap = -np.ones(len(p.v), int); remap[used] = np.arange(len(used))
        v = p.v[used] * 0.1 + sh
        idx, w, _ = top_k(p.W[used], 4)
        Xr.append(v); Xp.append(Rig.skin(v, idx, w, D, H, rig.head))
        T.append(remap[tris_of(p)] + off); C.append(np.tile(COL.get(p.name, (0.5, 0.5, 0.5)), (len(T[-1]), 1)))
        off += len(v)
    Xr, Xp, T, C = np.vstack(Xr), np.vstack(Xp), np.vstack(T), np.vstack(C)
    fig, axs = plt.subplots(1, 6, figsize=(18, 6.4))
    for i, (X, az, t) in enumerate([(Xr, 0, "rest front"), (Xr, 90, "rest side"), (Xp, 0, "stand front"),
                                     (Xp, 90, "stand side"), (Xp, 35, "stand 3/4"), (Xp, 180, "stand back")]):
        ax = axs[i]
        draw(ax, X, T, C, az)
        ax.set_xlim(-0.65, 0.65); ax.set_ylim(-0.02, 1.85); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(t)
    fig.tight_layout()
    fig.savefig(a.out, dpi=80)


if __name__ == "__main__":
    main()
