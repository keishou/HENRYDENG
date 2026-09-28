"""Retarget CMU (cgspeed "MotionBuilder-friendly" BVH) motion onto the
MakeHuman *default* skeleton (163 bones, CC0) as defined by MPFB2's
rig.default.json (bone head/tail/roll in Blender coords, metres).

Method: world-space rotation deltas relative to a calibration pose.
    delta_b(t)   = Rw_src[m(b)](t) @ Rw_src[m(b)](0)^T      (frame 0 = cgspeed T-pose)
    Rw_tgt_b(t)  = delta_b(t) @ Rw_tgt_cal_b
The target calibration pose is MakeHuman's rest (A-pose) with only the limb
bones whose anatomy matches (upper arm, forearm, thigh, shin) re-aimed to the
source frame-0 directions; spine / neck / head / hands / feet keep MH rest.
Bones with no source (fingers, face, toes...) inherit their parent's delta.
Root translation = source hip trajectory * (MH hip height / CMU hip height).

Output coordinates: Y up, character faces +Z at the calibration pose
(Blender (x, y, z) -> (x, z, -y)).  Bone frames follow Blender's convention
(local +Y along the bone, roll from MPFB) so the rotations drop straight onto
a glTF/three.js export of the same MakeHuman rig.

    python3 -m body.retarget_mh RIG_DEFAULT_JSON SRC.bvh OUT.npz [--fps 24] [--start s] [--end s]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from body.bvh import load_bvh  # noqa: E402

CMU_UNIT_M = 0.0254 / 0.45

# MakeHuman default bone -> cgspeed CMU joint whose world rotation drives it
MAP = {
    "root": "Hips",
    "pelvis.L": "LHipJoint", "pelvis.R": "RHipJoint",
    "upperleg01.L": "LeftUpLeg", "upperleg02.L": "LeftUpLeg",
    "lowerleg01.L": "LeftLeg", "lowerleg02.L": "LeftLeg",
    "foot.L": "LeftFoot",
    "upperleg01.R": "RightUpLeg", "upperleg02.R": "RightUpLeg",
    "lowerleg01.R": "RightLeg", "lowerleg02.R": "RightLeg",
    "foot.R": "RightFoot",
    "spine05": "LowerBack",
    "spine04": "Spine", "spine03": "Spine",
    "spine02": "Spine1", "spine01": "Spine1",
    "neck01": "Neck", "neck02": "Neck1", "neck03": "Neck1",
    "head": "Head",
    "clavicle.L": "LeftShoulder", "shoulder01.L": "LeftShoulder",
    "upperarm01.L": "LeftArm", "upperarm02.L": "LeftArm",
    "lowerarm01.L": "LeftForeArm", "lowerarm02.L": "LeftForeArm",
    "wrist.L": "LeftHand",
    "clavicle.R": "RightShoulder", "shoulder01.R": "RightShoulder",
    "upperarm01.R": "RightArm", "upperarm02.R": "RightArm",
    "lowerarm01.R": "RightForeArm", "lowerarm02.R": "RightForeArm",
    "wrist.R": "RightHand",
}
for _s, _S in (("L", "Left"), ("R", "Right")):  # toes follow the CMU toe joint
    for _t in range(1, 6):
        for _k in range(1, 4):
            MAP[f"toe{_t}-{_k}.{_s}"] = f"{_S}ToeBase"
# limb bones re-aimed at calibration: target bone -> (src joint, src child joint)
AIM = {
    "upperarm01.L": ("LeftArm", "LeftForeArm"), "upperarm02.L": ("LeftArm", "LeftForeArm"),
    "lowerarm01.L": ("LeftForeArm", "LeftHand"), "lowerarm02.L": ("LeftForeArm", "LeftHand"),
    "upperarm01.R": ("RightArm", "RightForeArm"), "upperarm02.R": ("RightArm", "RightForeArm"),
    "lowerarm01.R": ("RightForeArm", "RightHand"), "lowerarm02.R": ("RightForeArm", "RightHand"),
    "upperleg01.L": ("LeftUpLeg", "LeftLeg"), "upperleg02.L": ("LeftUpLeg", "LeftLeg"),
    "lowerleg01.L": ("LeftLeg", "LeftFoot"), "lowerleg02.L": ("LeftLeg", "LeftFoot"),
    "upperleg01.R": ("RightUpLeg", "RightLeg"), "upperleg02.R": ("RightUpLeg", "RightLeg"),
    "lowerleg01.R": ("RightLeg", "RightFoot"), "lowerleg02.R": ("RightLeg", "RightFoot"),
}

C = np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]])  # Blender Z-up,-Y fwd -> Y-up,+Z fwd


def _axis_angle(axis, ang):
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def blender_bone_matrix(head, tail, roll):
    """Blender vec_roll_to_mat3: columns = bone X, Y(=along bone), Z axes."""
    nor = tail - head
    nor = nor / np.linalg.norm(nor)
    x, y, z = nor
    theta = 1.0 + y
    theta_alt = x * x + z * z
    if theta > 1e-4 or theta_alt > 1e-12:
        if theta <= 1e-4:
            theta = theta_alt * 0.5 + theta_alt * theta_alt * 0.125
        B = np.column_stack([(1 - x * x / theta, -x, -x * z / theta), (x, y, z), (-x * z / theta, -z, 1 - z * z / theta)])
    else:
        B = np.diag([-1.0, -1.0, 1.0])
    return _axis_angle(nor, roll) @ B


def min_rot(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    s, c = np.linalg.norm(v), float(np.dot(a, b))
    if s < 1e-9:
        return np.eye(3)
    return _axis_angle(v, np.arctan2(s, c))


def load_mh_rig(path):
    rig = json.load(open(path))
    names = list(rig.keys())
    # topological order (parents first)
    order, seen = [], set()

    def visit(n):
        if n in seen:
            return
        p = rig[n]["parent"]
        if p:
            visit(p)
        seen.add(n)
        order.append(n)

    for n in names:
        visit(n)
    head = {n: C @ np.array(rig[n]["head"]["default_position"]) for n in order}
    tail = {n: C @ np.array(rig[n]["tail"]["default_position"]) for n in order}
    R = {}
    for n in order:
        Rb = blender_bone_matrix(np.array(rig[n]["head"]["default_position"]),
                                 np.array(rig[n]["tail"]["default_position"]), rig[n]["roll"])
        R[n] = C @ Rb  # bone frame expressed in Y-up world
    parent = {n: (rig[n]["parent"] or None) for n in order}
    return order, parent, head, tail, R


def retarget(rig_json, bvh_path, fps_out=None, t0=None, t1=None):
    order, parent, head, tail, Rrest = load_mh_rig(rig_json)
    clip = load_bvh(bvh_path)
    P, Rs = clip.world()
    names = clip.names
    ix = {n: i for i, n in enumerate(names)}
    P = P * CMU_UNIT_M
    # ---- calibration pose of the target (Y-up world) -----------------------
    Rcal, Hcal = {}, {}
    for n in order:
        p = parent[n]
        if p is None:
            Rcal[n], Hcal[n] = Rrest[n].copy(), head[n].copy()
        else:
            # carry the parent's calibration change rigidly
            dP = Rcal[p] @ Rrest[p].T
            Rcal[n] = dP @ Rrest[n]
            Hcal[n] = Hcal[p] + dP @ (head[n] - head[p])
        if n in AIM:
            a, b = AIM[n]
            want = P[0, ix[b]] - P[0, ix[a]]
            cur = Rcal[n][:, 1]  # bone +Y axis
            Rcal[n] = min_rot(cur, want) @ Rcal[n]
    # ---- frames to output ---------------------------------------------------
    src_fps = clip.fps
    f_first = 1  # frame 0 is the injected T-pose
    f_last = clip.n_frames - 1
    if t0 is not None:
        f_first = max(1, int(round(t0 * src_fps)) + 1)
    if t1 is not None:
        f_last = min(clip.n_frames - 1, int(round(t1 * src_fps)) + 1)
    if fps_out:
        ts = np.arange(f_first, f_last + 1e-9, src_fps / fps_out)
    else:
        ts = np.arange(f_first, f_last + 1)
    fi = np.clip(np.round(ts).astype(int), 0, clip.n_frames - 1)  # nearest frame (120 -> 24 is exact /5)
    Rsrc = Rs[fi]
    Psrc = P[fi]
    R0 = Rs[0]
    # ---- root translation: scale by standing hip height, floor -> y=0 --------
    src_ground = float(np.percentile(P[1:, :, 1].min(axis=1), 1))
    src_hip_h = P[0, 0, 1] - P[0, :, 1].min()  # frame-0 T-pose, standing
    tgt_ground = min(Hcal[n][1] for n in order)
    tgt_hip_h = Hcal[order[0]][1] - tgt_ground
    k = tgt_hip_h / src_hip_h
    origin = np.array([Psrc[0, 0, 0], src_ground, Psrc[0, 0, 2]])
    Rw = {}
    Hw = {}
    for n in order:
        p = parent[n]
        src = MAP.get(n)
        if src is not None:
            D = Rsrc[:, ix[src]] @ R0[ix[src]].T
            Rw[n] = D @ Rcal[n]
        else:
            D = Rw[p] @ Rcal[p].T
            Rw[n] = D @ Rcal[n]
        if p is None:
            Hw[n] = (Psrc[:, 0] - origin) * k
        else:
            Hw[n] = Hw[p] + np.einsum("fij,j->fi", Rw[p] @ Rcal[p].T, Hcal[n] - Hcal[p])
    # local rotations (relative to parent bone frame), as in a glTF/three.js bone
    Rl = {}
    for n in order:
        p = parent[n]
        Rl[n] = Rw[n] if p is None else np.einsum("fji,fjk->fik", Rw[p], Rw[n])
    rest_local = {n: (Rrest[n] if parent[n] is None else Rrest[parent[n]].T @ Rrest[n]) for n in order}
    return dict(order=order, parent=parent, Rw=Rw, Hw=Hw, Rl=Rl, rest_local=rest_local,
                head_rest=head, tail_rest=tail, Rrest=Rrest, Rcal=Rcal, Hcal=Hcal,
                fps=(fps_out or src_fps), src_frames=fi, src_positions=Psrc, src_names=names,
                scale=k, clip=clip)


def mat_to_quat(M):
    """(...,3,3) -> (...,4) xyzw (robust Shepperd conversion, see mh_rig.mat_to_quat)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from mh_rig import mat_to_quat as _m2q
    return _m2q(M)


def save_npz(res, out):
    order = res["order"]
    np.savez_compressed(
        out,
        bones=np.array(order),
        parents=np.array([order.index(res["parent"][n]) if res["parent"][n] else -1 for n in order]),
        fps=res["fps"],
        root_pos=res["Hw"][order[0]],  # (F,3) metres, Y up
        head_pos=np.stack([res["Hw"][n] for n in order], 1),  # (F,B,3) bone head positions (for checks)
        local_quat=np.stack([mat_to_quat(res["Rl"][n]) for n in order], 1),  # (F,B,4) xyzw
        world_quat=np.stack([mat_to_quat(res["Rw"][n]) for n in order], 1),
        rest_local_quat=np.stack([mat_to_quat(res["rest_local"][n]) for n in order], 0),
        rest_head=np.stack([res["head_rest"][n] for n in order]),
        rest_tail=np.stack([res["tail_rest"][n] for n in order]),
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("rig")
    ap.add_argument("bvh")
    ap.add_argument("out")
    ap.add_argument("--fps", type=float, default=None)
    ap.add_argument("--start", type=float, default=None)
    ap.add_argument("--end", type=float, default=None)
    a = ap.parse_args()
    r = retarget(a.rig, a.bvh, a.fps, a.start, a.end)
    save_npz(r, a.out)
    print(f"{a.out}: {len(r['src_frames'])} frames @ {r['fps']} fps, root scale {r['scale']:.3f}")
