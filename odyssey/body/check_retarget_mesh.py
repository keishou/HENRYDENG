"""Skinned-mesh check of a retarget: MakeHuman base mesh (MPFB2 base.obj, CC0)
+ MPFB2 weights.default.json, linear-blend-skinned with body.retarget_mh output,
flat-shaded software render with matplotlib (no GPU).  Verifies twist/roll,
head yaw and hands, which a stick figure cannot show.

    python3 -m body.check_retarget_mesh MH_DIR SRC.bvh OUT.png --times 1 3 5 [--start s --end s] [--az 30]
MH_DIR must contain mpfb2_rig.default.json, mpfb2_weights.default.json, mpfb2_base.obj
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from body.retarget_mh import retarget  # noqa: E402


def load_body(obj_path):
    V, F, g = [], [], None
    for line in open(obj_path):
        if line.startswith("v "):
            V.append([float(x) for x in line.split()[1:4]])
        elif line.startswith("g "):
            g = line.split()[1]
        elif line.startswith("f ") and g == "body":
            F.append([int(t.split("/")[0]) - 1 for t in line.split()[1:]])
    V = np.array(V) * 0.1  # MakeHuman OBJ: decimetres, Y up, faces +Z  == our Y-up world
    tris = []
    for f in F:
        for i in range(1, len(f) - 1):
            tris.append([f[0], f[i], f[i + 1]])
    return V, np.array(tris)


def skin(V, W, r, frame):
    out = np.zeros_like(V)
    for b, (idx, w) in W.items():
        R = r["Rw"][b][frame] @ r["Rrest"][b].T
        t = r["Hw"][b][frame] - R @ r["head_rest"][b]
        out[idx] += w[:, None] * (V[idx] @ R.T + t)
    return out


def render(ax, X, T, az_deg, el_deg=8, color=(0.80, 0.78, 0.74)):
    from matplotlib.collections import PolyCollection
    az, el = np.radians(az_deg), np.radians(el_deg)
    # camera looks toward -dir; build orthonormal screen basis
    d = np.array([np.sin(az) * np.cos(el), np.sin(el), np.cos(az) * np.cos(el)])  # from target to camera
    ex = np.cross([0, 1, 0], d)
    ex /= np.linalg.norm(ex)
    ey = np.cross(d, ex)
    P = np.stack([X @ ex, X @ ey, X @ d], -1)
    tri = P[T]
    n = np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    light = d * 0.6 + np.array([0.3, 0.7, 0.2])
    light /= np.linalg.norm(light)
    shade = np.clip(np.abs(n @ light), 0, 1) * 0.75 + 0.25
    order = np.argsort(tri[:, :, 2].mean(1))  # far first
    cols = np.clip(np.array(color)[None] * shade[order, None], 0, 1)
    pc = PolyCollection(tri[order][:, :, :2], facecolors=cols, edgecolors="none", antialiased=False)
    ax.add_collection(pc)
    g = np.array([[-1.5, 0, -1.5], [1.5, 0, -1.5], [1.5, 0, 1.5], [-1.5, 0, 1.5], [-1.5, 0, -1.5]])
    ax.plot(g @ ex, g @ ey, color="#aaa", lw=0.6, zorder=0)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ap = argparse.ArgumentParser()
    ap.add_argument("mhdir")
    ap.add_argument("bvh")
    ap.add_argument("out")
    ap.add_argument("--times", type=float, nargs="+", required=True)
    ap.add_argument("--start", type=float)
    ap.add_argument("--end", type=float)
    ap.add_argument("--az", type=float, nargs="+", default=[30.0])
    a = ap.parse_args()
    r = retarget(os.path.join(a.mhdir, "mpfb2_rig.default.json"), a.bvh, None, a.start, a.end)
    V, T = load_body(os.path.join(a.mhdir, "mpfb2_base.obj"))
    wj = json.load(open(os.path.join(a.mhdir, "mpfb2_weights.default.json")))["weights"]
    acc = np.zeros(len(V))
    W = {}
    for b, lst in wj.items():
        arr = np.array(lst)
        if arr.ndim != 2 or not len(arr):
            continue
        W[b] = (arr[:, 0].astype(int), arr[:, 1])
        np.add.at(acc, W[b][0], W[b][1])
    for b in W:
        idx, w = W[b]
        W[b] = (idx, w / np.maximum(acc[idx], 1e-9))
    fps = r["fps"]
    frames = [min(len(r["src_frames"]) - 1, int(round(t * fps))) for t in a.times]
    cols = len(frames) + 1
    fig, axs = plt.subplots(len(a.az), cols, figsize=(2.6 * cols, 4.6 * len(a.az)), squeeze=False)
    for row, az in enumerate(a.az):
        for c in range(cols):
            ax = axs[row, c]
            if c == 0:
                X = V.copy()
                X[:, 1] -= X[:, 1].min()
                title = "MH rest (A-pose)"
                cx = X[:, [0, 2]].mean(0)
            else:
                f = frames[c - 1]
                X = skin(V, W, r, f)
                title = f"t={f / fps:.2f}s"
                cx = r["Hw"]["root"][f][[0, 2]]
            X = X - np.array([cx[0], 0, cx[1]])
            render(ax, X, T, az)
            ax.set_xlim(-1.0, 1.0)
            ax.set_ylim(-0.1, 1.9)
            ax.set_aspect("equal")
            ax.axis("off")
            ax.set_title(f"{title}  az{az:.0f}", fontsize=8)
    fig.suptitle(os.path.basename(a.bvh) + " retargeted onto MakeHuman base mesh (LBS, MPFB2 default weights)", fontsize=9)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(a.out, dpi=90)


if __name__ == "__main__":
    main()
