"""Visual check: CMU source skeleton vs retargeted MakeHuman default skeleton.

    python3 -m body.check_retarget RIG_DEFAULT_JSON SRC.bvh OUT.png [--start s --end s --n 8]
Top row(s): source (grey, scaled to target size) overlaid with retargeted MH
bones (colour).  First column = calibration pose (source frame 0 T-pose vs
MH calibration pose).
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from body.retarget_mh import retarget  # noqa: E402

SKIP = ("finger", "toe", "levator", "oculi", "orbicularis", "oris", "risorius", "temporalis",
        "tongue", "special", "jaw", "eye", "metacarpal", "breast")


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ap = argparse.ArgumentParser()
    ap.add_argument("rig")
    ap.add_argument("bvh")
    ap.add_argument("out")
    ap.add_argument("--start", type=float)
    ap.add_argument("--end", type=float)
    ap.add_argument("--n", type=int, default=8)
    a = ap.parse_args()
    r = retarget(a.rig, a.bvh, None, a.start, a.end)
    order = r["order"]
    bones = [n for n in order if not n.startswith(SKIP)]
    length = {n: np.linalg.norm(r["tail_rest"][n] - r["head_rest"][n]) for n in order}
    clip = r["clip"]
    k = r["scale"]
    Ps = r["src_positions"]
    par = clip.parents
    F = len(r["src_frames"])
    idx = np.linspace(0, F - 1, a.n).round().astype(int)
    # align source drawing with target root each frame (source scaled by k)
    views = [(0, "front (from +Z)"), (90, "side (from +X)")]
    fig, axs = plt.subplots(len(views), a.n + 1, figsize=(2.1 * (a.n + 1), 5.2))

    def col(n):
        return "#d9622b" if n.endswith(".L") else "#2b6fd9" if n.endswith(".R") else "#222"

    for row, (az, lab) in enumerate(views):
        th = np.radians(az)
        ex = np.array([np.cos(th), 0, -np.sin(th)])  # screen-x axis
        for c in range(a.n + 1):
            ax = axs[row, c]
            if c == 0:  # calibration
                src = r["clip"].world_positions([0])[0] * 0.0254 / 0.45
                src = (src - src[0]) * k
                H = {n: r["Hcal"][n] - r["Hcal"][order[0]] for n in order}
                T = {n: H[n] + r["Rcal"][n][:, 1] * length[n] for n in order}
                title = "calibration"
            else:
                f = idx[c - 1]
                src = (Ps[f] - Ps[f, 0]) * k
                root = r["Hw"][order[0]][f]
                H = {n: r["Hw"][n][f] - root for n in order}
                T = {n: H[n] + r["Rw"][n][f][:, 1] * length[n] for n in order}
                title = f"t={f / r['fps']:.1f}s"
            for j, p in enumerate(par):
                if p >= 0 and not any(x in clip.names[j] for x in ("Thumb", "Index", "Finger")):
                    ax.plot([src[p] @ ex, src[j] @ ex], [src[p][1], src[j][1]], "-", color="#bbb", lw=5,
                            solid_capstyle="round", zorder=1)
            for n in bones:
                ax.plot([H[n] @ ex, T[n] @ ex], [H[n][1], T[n][1]], "-", color=col(n), lw=1.6, zorder=2)
            # nose marker: head bone's -Z?  use head frame +Z (faces forward) for a short tick
            hn = "head"
            Rh = r["Rcal"][hn] if c == 0 else r["Rw"][hn][idx[c - 1]]
            mid = (H[hn] + T[hn]) / 2
            fwd = mid + Rh @ np.array([0, 0, 1.0]) * 0.12
            ax.plot([mid @ ex, fwd @ ex], [mid[1], fwd[1]], "-", color="g", lw=2, zorder=3)
            ax.set_xlim(-1.0, 1.0)
            ax.set_ylim(-1.05, 0.95)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(title, fontsize=8)
            if c == 0:
                ax.set_ylabel(lab, fontsize=8)
    fig.suptitle(f"{os.path.basename(a.bvh)} -> MakeHuman default (grey = CMU source scaled x{k:.3f}; "
                 f"orange=L, blue=R; green tick = head bone +Z)", fontsize=9)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(a.out, dpi=80)


if __name__ == "__main__":
    main()
