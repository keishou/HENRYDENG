"""Summarise and contact-sheet BVH clips so they can be checked by eye.

    python3 -m body.inspect_motion OUT_DIR clip1.bvh clip2.bvh ...

For every clip writes OUT_DIR/<name>.png (stick-figure strip + top-down path
+ time series) and prints/accumulates a JSON summary (OUT_DIR/summary.json).
Assumes Y-up BVH (CMU / cgspeed, three.js, MakeHuman all are).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from body.bvh import load_bvh  # noqa: E402

CMU_UNIT_M = 0.0254 / 0.45  # CMU ASF length unit: inches * 0.45  -> 0.05644 m

def side(name):
    n = name[:-4] if name.endswith("_End") else name
    low = n.lower()
    if low.startswith("left") or n.startswith(("LHip", "LThumb")) or (len(n) > 1 and n[0] == "l" and n[1].isupper()) \
            or low.endswith((".l", "_l")):
        return "L"
    if low.startswith("right") or n.startswith(("RHip", "RThumb")) or (len(n) > 1 and n[0] == "r" and n[1].isupper()) \
            or low.endswith((".r", "_r")):
        return "R"
    return "C"


def find(names, *cands):
    low = [n.lower() for n in names]
    for c in cands:
        if c.lower() in low:
            return low.index(c.lower())
    return None


def yaw_of(v):
    return np.degrees(np.arctan2(v[..., 0], v[..., 2]))


def unwrap_deg(a):
    return np.degrees(np.unwrap(np.radians(a)))


def analyse(path, unit_m=None, skip_first=None):
    clip = load_bvh(path)
    names = clip.names
    P, R = clip.world()
    root = 0
    head = find(names, "Head", "head")
    headend = find(names, "Head_End", "head_End")
    neck = find(names, "Neck1", "Neck", "neck", "neck01")
    # detect an injected T-pose first frame (cgspeed CMU release, three.js pirouette):
    # frame 0 -> 1 jumps far more than any later frame -> frame step.
    if skip_first is None:
        rot = [k for j in clip.joints for k, c in enumerate(j.channels, j.chan_start) if c.endswith("rotation")]
        d = np.abs(np.diff(clip.frames[:6, rot], axis=0))
        d = np.minimum(d, 360 - d).max(axis=1)
        skip_first = bool(d[0] > 15 and d[0] > 5 * d[1:].max())
    s = 1 if skip_first else 0
    Pm, Rm = P[s:], R[s:]
    top = headend if headend is not None else head
    if unit_m is None:
        low = [n.lower() for n in names]
        if "lhipjoint" in low:  # CMU skeleton (ASF units: inches*0.45)
            unit_m = CMU_UNIT_M
        else:
            rest_h = _rest_height(clip)
            unit_m = 1.75 / rest_h if rest_h > 0 else 1.0
            if 140 < rest_h < 210:
                unit_m = 0.01
            elif 55 < rest_h < 85:
                unit_m = 0.0254
            elif 1.4 < rest_h < 2.1:
                unit_m = 1.0
    fps = clip.fps
    hip = Pm[:, root] * unit_m
    ground = float(np.percentile(Pm[:, :, 1].min(axis=1), 1)) * unit_m
    fwd = np.einsum("fij,j->fi", Rm[:, root], [0, 0, 1.0])
    hip_yaw = unwrap_deg(yaw_of(fwd))
    hfwd = np.einsum("fij,j->fi", Rm[:, head], [0, 0, 1.0]) if head is not None else fwd
    head_yaw_rel = (yaw_of(hfwd) - yaw_of(fwd) + 180) % 360 - 180
    head_pitch = np.degrees(np.arcsin(np.clip(hfwd[:, 1], -1, 1)))
    # up-vector of head (neck->head end) elevation: robust alternative
    if neck is not None and top is not None:
        up = Pm[:, top] - Pm[:, neck]
        up /= np.linalg.norm(up, axis=1, keepdims=True) + 1e-9
    step = np.linalg.norm(np.diff(hip[:, [0, 2]], axis=0), axis=1)
    win = max(1, int(round(fps * 0.5)))
    xz = hip[:, [0, 2]]
    sp = np.linalg.norm(xz[win:] - xz[:-win], axis=1) / (win / fps) if len(xz) > win else np.zeros(1)
    summ = dict(
        file=os.path.basename(path),
        joints=[n for n in names if not n.endswith("_End")],
        n_joints=sum(1 for j in clip.joints if not j.is_end),
        root=names[0],
        frames_total=int(clip.n_frames),
        tpose_first_frame=bool(skip_first),
        fps=round(fps, 3),
        duration_s=round((clip.n_frames - s) / fps, 2),
        unit_m=unit_m,
        rest_height_m=round(_rest_height(clip) * unit_m, 3),
        path_len_m=round(float(step.sum()), 2),
        net_disp_m=round(float(np.linalg.norm(xz[-1] - xz[0])), 2),
        speed_mean_mps=round(float(sp.mean()), 3),
        speed_max_mps=round(float(sp.max()), 3),
        hip_yaw_total_deg=round(float(hip_yaw[-1] - hip_yaw[0]), 1),
        hip_yaw_range_deg=round(float(hip_yaw.max() - hip_yaw.min()), 1),
        hip_h_min_m=round(float(hip[:, 1].min() - ground), 2),
        hip_h_max_m=round(float(hip[:, 1].max() - ground), 2),
        head_yaw_rel_minmax_deg=[round(float(head_yaw_rel.min()), 1), round(float(head_yaw_rel.max()), 1)],
        head_pitch_minmax_deg=[round(float(head_pitch.min()), 1), round(float(head_pitch.max()), 1)],
    )
    series = dict(t=np.arange(len(hip)) / fps, hip=hip, hip_yaw=hip_yaw, head_yaw_rel=head_yaw_rel,
                  head_pitch=head_pitch, speed=sp, ground=ground)
    return clip, P, s, unit_m, summ, series


def _rest_height(clip):
    # FK with all channels zero
    J = len(clip.joints)
    pos = np.zeros((J, 3))
    for i, j in enumerate(clip.joints):
        pos[i] = j.offset + (pos[j.parent] if j.parent >= 0 else 0)
    return float(pos[:, 1].max() - pos[:, 1].min())


def contact_sheet(path, out_png, title="", n=10):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    clip, P, s, unit_m, summ, ser = analyse(path)
    Pm = P[s:] * unit_m
    Pm[..., 1] -= ser["ground"]
    par = clip.parents
    sides = [side(n) for n in clip.names]
    col = {"L": "#d9622b", "R": "#2b6fd9", "C": "#333333"}
    F = len(Pm)
    idx = np.linspace(0, F - 1, n).round().astype(int)
    fig = plt.figure(figsize=(2.0 * n, 8.2))
    gs = fig.add_gridspec(3, n, height_ratios=[3.2, 3.2, 2.2])
    for row, (az, lab) in enumerate([(35, "3/4 view (world az 35)"), (-90, "side view (world +X)")]):
        a = np.radians(az)
        # orthographic camera looking horizontally; screen x = rotated horizontal, y = up
        ex = np.array([np.cos(a), 0, -np.sin(a)])
        for k, f in enumerate(idx):
            ax = fig.add_subplot(gs[row, k])
            X = Pm[f]
            c = X[0] * np.array([1, 0, 1])
            sx = (X - c) @ ex
            sy = X[:, 1]
            for ji, p in enumerate(par):
                if p < 0:
                    continue
                ax.plot([sx[p], sx[ji]], [sy[p], sy[ji]], "-", color=col[sides[ji]], lw=2)
            hi = find(clip.names, "Head", "head")
            if hi is not None:
                ax.plot(sx[hi], sy[hi], "o", color="k", ms=4)
            ax.axhline(0, color="#999", lw=0.8)
            ax.set_xlim(-1.0, 1.0)
            ax.set_ylim(-0.05, 2.0)
            ax.set_aspect("equal")
            ax.set_xticks([])
            ax.set_yticks([] if k else [0, 0.5, 1, 1.5])
            if row == 0:
                ax.set_title(f"t={f / clip.fps:.1f}s", fontsize=8)
            if k == 0:
                ax.set_ylabel(lab, fontsize=7)
    # bottom: trajectory + time series
    ax = fig.add_subplot(gs[2, 0:3])
    hip = ser["hip"]
    ax.plot(hip[:, 0], hip[:, 2], "-", color="#555")
    fwd = np.stack([np.sin(np.radians(ser["hip_yaw"])), np.cos(np.radians(ser["hip_yaw"]))], 1)
    for f in idx:
        ax.arrow(hip[f, 0], hip[f, 2], 0.25 * fwd[f, 0], 0.25 * fwd[f, 1], head_width=0.06, color="C3")
    ax.plot(hip[0, 0], hip[0, 2], "go")
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title("top-down hip path (x,z m), arrows=facing", fontsize=8)
    ax.tick_params(labelsize=6)
    t = ser["t"]
    ax = fig.add_subplot(gs[2, 3:6])
    ax.plot(t, hip[:, 1] - ser["ground"], label="hip height m")
    ax.plot(t[: len(ser["speed"])], ser["speed"], label="speed m/s")
    ax.legend(fontsize=6)
    ax.tick_params(labelsize=6)
    ax = fig.add_subplot(gs[2, 6:])
    ax.plot(t, ser["hip_yaw"] - ser["hip_yaw"][0], label="hip yaw (deg, from start)")
    ax.plot(t, ser["head_yaw_rel"], label="head yaw rel. hips")
    ax.plot(t, ser["head_pitch"], label="head pitch (+=up)")
    ax.legend(fontsize=6)
    ax.tick_params(labelsize=6)
    fig.suptitle(f"{summ['file']}  {title}  | {summ['duration_s']}s @ {summ['fps']:.0f}fps, "
                 f"{summ['n_joints']} joints, path {summ['path_len_m']}m, mean speed {summ['speed_mean_mps']}m/s, "
                 f"turn {summ['hip_yaw_total_deg']}deg, hip h {summ['hip_h_min_m']}-{summ['hip_h_max_m']}m",
                 fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_png, dpi=70)
    plt.close(fig)
    return summ


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    titles = {}
    tfile = os.environ.get("CLIP_TITLES")
    if tfile and os.path.exists(tfile):
        titles = json.load(open(tfile))
    allsum = {}
    sp = os.path.join(out, "summary.json")
    if os.path.exists(sp):
        allsum = json.load(open(sp))
    for p in sys.argv[2:]:
        b = os.path.splitext(os.path.basename(p))[0]
        try:
            s = contact_sheet(p, os.path.join(out, b + ".png"), titles.get(b, ""))
        except Exception as e:  # keep going
            print("FAIL", p, e)
            continue
        s.pop("joints")
        allsum[b] = s
        print(json.dumps(s))
    json.dump(allsum, open(sp, "w"), indent=1)
