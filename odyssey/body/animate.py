#!/usr/bin/env python3
"""Make the full-body subject model move: CMU mocap retargeted onto its MakeHuman skeleton, cleaned up
(level head, forearm twist spread, planted feet, no root drift, seamless loops, breathing) and written
as named animation clips into a copy of the model GLB.

    python3 odyssey/body/animate.py                                  # all clips
    python3 odyssey/body/animate.py --clips walk,idle --out X.glb    # a subset
    python3 odyssey/body/animate.py --report                         # print the per-clip QA numbers

Inputs  odyssey/out/body/subject_full.glb (+ subject_full_data.npz: rest skeleton + stand pose)
        odyssey/.cache/motion/cmu/*.bvh  (CMU mocap, cgspeed BVH; see body/curate_motion.py)
Output  odyssey/out/body/subject_animated.glb  = subject_full.glb + clips (see CLIPS below)
        odyssey/out/body/subject_animated_anim.json  (clip list, loop flags, speeds, QA numbers)

Conventions (same as build_body.py / retarget_mh.py): metres, Y up, the character faces +Z in the
stand pose, soles on y = 0.  Every clip animates the rotation of all 163 joints, the translation of
the root joint, and the "stand_corrective_L/R" morph weights of the skin and outfit meshes (the
stand-pose LBS corrective fades out as an arm leaves the hanging position).  Loop clips (idle, walk)
end on their first frame; "walk" is an in-place cycle (move the character at the speed given in
the scene extras / sidecar), "walk_forward" carries the same cycles with the root travelling along +Z.

three.js (the film renderer):
    const mixer = new THREE.AnimationMixer(gltf.scene);
    mixer.clipAction(THREE.AnimationClip.findByName(gltf.animations, 'idle')).play();   // loops seamlessly
    // in-place "walk": also move gltf.scene along +Z at scene.extras.clips.walk.speed_mps (0.797 m/s)
Blender: the importer makes one action per clip with slots for the armature and the skin / outfit
shape keys (see body/render_motion_bpy.py set_clip).

Clips: "walk" (relaxed walk, CMU 142_13, 3.04 s in-place loop, 0.80 m/s), "walk_forward" (two of
those cycles travelling 4.85 m along +Z, 6.08 s), "idle" (quiet standing with weight shifts and
glances, CMU 77_02, 5.88 s loop, breathing added), "turn_look_back" (turns to look back over the
left shoulder, then the right, and back to the front, CMU 76_10, 5.38 s).

Robustness: quaternions come from Shepperd's method (mh_rig.mat_to_quat; the old sign-from-differences
conversion flipped lip / tongue bones near 180 deg, popping the mouth open); bones mocap does not drive
(jaw, lips, tongue, eyes, face muscles, fingers) are written as their stand pose; export() records per
clip QA numbers (largest per-frame joint rotation, face-bone drift, signed knee flexion, sideways knee
deviation, per-frame shin rotation).

Retarget: world-rotation deltas.  Each source joint is paired with the rotation it has when the
model stands in its stand pose.  For the arms, neck and head that pairing comes from the source's
frame-0 T-pose with the model's limb SEGMENTS aimed along the source's (upperleg01 is a short bone
21 deg off the thigh axis: aiming the bone itself bows the legs).  For the pelvis, legs and spine it
comes from a window where the actor stands still (CMU's knee / pelvis joint centres make quiet
standing read as ~20 deg of knee bend with the pelvis tipped forward, which paired with the T-pose
crouches the model and tilts him ~9 deg forward).  Target bones sharing a source joint (shoulder01
with the clavicle, the second thigh / shin / forearm / upper-arm segments, fingers) keep their
stand-pose relation, so the shoulders keep the stand pose's deltoid share and the fingers their
relaxed curl.  Root translation is scaled by the leg-length ratio.

Calibration uses the model's symmetric neutral stance (neutral_D / neutral_H in the data npz), not the
GLB's contrapposto "stand" pose.

Clean-up per clip: heading aligned to +Z; constant neck / head pitch and roll offsets so the median
gaze is level and upright (CMU head calibration differs per session: 20 deg up, 24 deg down, 8 deg
tilted), the walk's side-to-side head wobble halved and its arm swing scaled up (x1.35 upper arm, x1.15 forearm);
the idle's glances calmed (head deviation from the clip mean halved, pitch clamped to +-10 deg, yaw to
+-35 deg); upper-arm and forearm roll spread over
upperarm01/02 and lowerarm01/02 + wrist (no candy-wrapper wrist), wrist bend clamped; foot
contacts found on the shoe soles (height + speed): while planted, the pivot (heel, then ball) is
pinned in x/z (idle: heel and ball held at their mean positions, 80 % of the feet's swivel removed),
while resting on the floor the lowest shoe point is pinned to y = 0; the pelvis height and roll are
chosen per frame so the stance knees keep their bend, then two-bone leg IK with a clean hinge (the knee
bends forward in the sagittal plane of hip, ankle and the foot / pelvis forward direction, at least 2.5
deg: a nearly straight mocap knee can no longer flip backwards or bend sideways); soles never below
y = 0; loops cut where the end matches the start, cross-faded over the seam and foot-planted on
three tiled copies so contacts wrap; slow breathing on the idle.

Mocap: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), free for any use.  "The data
used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from
NSF EIA-0196217."
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ODY = HERE.parent
sys.path.insert(0, str(ODY))
sys.path.insert(0, str(HERE))
from body.bvh import load_bvh  # noqa: E402
from body.retarget_mh import CMU_UNIT_M, MAP  # noqa: E402

OUT = ODY / "out" / "body"
CMU = ODY / ".cache" / "motion" / "cmu"
FPS = 24.0


# ============================================================================ small maths
def axis_angle(axis, ang):
    """(…,3) axes, (…) angles -> (…,3,3)."""
    axis = np.asarray(axis, float)
    ang = np.asarray(ang, float)
    axis = axis / np.maximum(np.linalg.norm(axis, axis=-1, keepdims=True), 1e-12)
    x, y, z = axis[..., 0], axis[..., 1], axis[..., 2]
    c, s = np.cos(ang), np.sin(ang)
    C = 1 - c
    return np.stack([np.stack([c + x * x * C, x * y * C - z * s, x * z * C + y * s], -1),
                     np.stack([y * x * C + z * s, c + y * y * C, y * z * C - x * s], -1),
                     np.stack([z * x * C - y * s, z * y * C + x * s, c + z * z * C], -1)], -2)


def min_rot(a, b):
    """Shortest rotation(s) taking direction(s) a onto b. (…,3) -> (…,3,3)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    a = a / np.linalg.norm(a, axis=-1, keepdims=True)
    b = b / np.linalg.norm(b, axis=-1, keepdims=True)
    v = np.cross(a, b)
    s = np.linalg.norm(v, axis=-1)
    c = np.sum(a * b, -1)
    ax = np.where(s[..., None] > 1e-9, v, np.array([1.0, 0, 0]))
    return axis_angle(ax, np.arctan2(s, c))


def rot_y(ang):
    return axis_angle(np.array([0.0, 1.0, 0.0]), ang)


from mh_rig import mat_to_quat  # noqa: E402  (robust Shepperd conversion)


def quat_to_mat(q):
    q = np.asarray(q, float)
    q = q / np.linalg.norm(q, axis=-1, keepdims=True)
    x, y, z, w = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.stack([np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
                     np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
                     np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], -2)


def quat_continuous(q):
    """Flip signs along axis 0 so consecutive quaternions stay in the same hemisphere."""
    q = q.copy()
    for i in range(1, len(q)):
        s = np.sum(q[i] * q[i - 1], -1) < 0
        q[i][s] *= -1
    return q


def rot_angle(M):
    return np.arccos(np.clip((np.trace(M, axis1=-2, axis2=-1) - 1) / 2, -1, 1))


def rot_log(M):
    """(…,3,3) -> rotation vectors (…,3)."""
    ang = rot_angle(M)
    v = np.stack([M[..., 2, 1] - M[..., 1, 2], M[..., 0, 2] - M[..., 2, 0], M[..., 1, 0] - M[..., 0, 1]], -1)
    s = np.sin(ang)
    k = np.where(s > 1e-6, ang / np.maximum(2 * s, 1e-12), 0.5)
    return v * k[..., None]


def rot_exp(v):
    ang = np.linalg.norm(v, axis=-1)
    return axis_angle(np.where(ang[..., None] > 1e-12, v, np.array([1.0, 0, 0])), ang)


def orthonormalize(M):
    U, _, Vt = np.linalg.svd(M)
    R = U @ Vt
    d = np.linalg.det(R) < 0
    if np.any(d):
        U = U.copy()
        U[d, :, -1] *= -1
        R = U @ Vt
    return R


def smooth(x, sigma, axis=0, mode="nearest"):
    from scipy.ndimage import gaussian_filter1d
    if sigma <= 0:
        return x
    return gaussian_filter1d(x, sigma, axis=axis, mode=mode)


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# ============================================================================ GLB i/o
CT = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read_glb(path):
    b = Path(path).read_bytes()
    jl = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + jl])
    off = 20 + jl
    bl = struct.unpack("<I", b[off:off + 4])[0]
    return j, bytearray(b[off + 8:off + 8 + bl])


def accessor(j, bin_, i):
    a = j["accessors"][i]
    bv = j["bufferViews"][a["bufferView"]]
    dt = CT[a["componentType"]]
    n = NC[a["type"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    arr = np.frombuffer(bytes(bin_[start:start + a["count"] * n * np.dtype(dt).itemsize]), dt).reshape(a["count"], n)
    if a.get("normalized"):
        arr = arr.astype(np.float32) / np.iinfo(dt).max
    return arr


class GLBEdit:
    """Append accessors / animations to an existing GLB and save it."""

    def __init__(self, path):
        self.j, self.bin = read_glb(path)

    def _view(self, data):
        while len(self.bin) % 4:
            self.bin += b"\0"
        self.j["bufferViews"].append({"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)})
        self.bin += data
        return len(self.j["bufferViews"]) - 1

    def acc(self, arr, atype, minmax=False):
        arr = np.ascontiguousarray(arr, np.float32)
        a = {"bufferView": self._view(arr.tobytes()), "componentType": 5126, "count": int(arr.shape[0]),
             "type": atype}
        if minmax:
            a2 = arr.reshape(arr.shape[0], -1)
            a["min"] = [float(x) for x in a2.min(0)]
            a["max"] = [float(x) for x in a2.max(0)]
        self.j["accessors"].append(a)
        return len(self.j["accessors"]) - 1

    def save(self, path):
        while len(self.bin) % 4:
            self.bin += b"\0"
        self.j["buffers"][0]["byteLength"] = len(self.bin)
        js = json.dumps(self.j, separators=(",", ":")).encode()
        js += b" " * ((4 - len(js) % 4) % 4)
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        with open(path, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, total))
            f.write(struct.pack("<I4s", len(js), b"JSON"))
            f.write(js)
            f.write(struct.pack("<I4s", len(self.bin), b"BIN\0"))
            f.write(self.bin)
        return total


# ============================================================================ the body
class Body:
    """Rest skeleton + stand pose of the exported model, and its skinned meshes (for QA / contacts)."""

    def __init__(self, glb=OUT / "subject_full.glb", data=None):
        glb = Path(glb)
        data = Path(data) if data else glb.with_name(glb.stem + "_data.npz")
        d = np.load(data)
        self.glb = glb
        self.names = [str(n) for n in d["bone_names"]]
        self.parent = d["bone_parent"].astype(int)
        self.head = d["bone_head"]
        self.Rr = d["bone_R"]
        # retargeting is calibrated on the symmetric neutral stance (the GLB's "stand" clip may carry a
        # relaxed contrapposto, which would make every clip lean on one leg)
        self.Dst = d["neutral_D"] if "neutral_D" in d else d["pose_D"]
        self.Hst = d["neutral_H"] if "neutral_H" in d else d["pose_H"]
        self.Tst = self.Dst @ self.Rr               # stand-pose bone frames (world)
        self.ix = {n: i for i, n in enumerate(self.names)}
        self.B = len(self.names)
        # parent-frame offsets (constant)
        self.off = np.zeros((self.B, 3))
        for b in range(self.B):
            p = self.parent[b]
            if p >= 0:
                self.off[b] = self.Rr[p].T @ (self.head[b] - self.head[p])
        self.j, self.bin = read_glb(glb)
        skin = self.j["skins"][0]
        jn = [self.j["nodes"][k]["name"] for k in skin["joints"]]
        assert jn == self.names, "GLB joint order differs from the data npz"
        self.joint_nodes = skin["joints"]
        self.mesh_nodes = {}
        for k, n in enumerate(self.j["nodes"]):
            if "mesh" in n:
                self.mesh_nodes[n["name"]] = k
        self._mesh_cache = {}
        self.legs = {s: dict(hip=self.ix[f"upperleg01.{s}"], thigh2=self.ix[f"upperleg02.{s}"],
                             knee=self.ix[f"lowerleg01.{s}"], shin2=self.ix[f"lowerleg02.{s}"],
                             foot=self.ix[f"foot.{s}"]) for s in "LR"}

    def i(self, n):
        return self.ix[n]

    def mesh(self, name):
        """Bind-space positions, joints, weights (+ morph targets) of a skinned mesh."""
        if name not in self._mesh_cache:
            node = self.j["nodes"][self.mesh_nodes[name]]
            prim = self.j["meshes"][node["mesh"]]["primitives"][0]
            at = prim["attributes"]
            pos = accessor(self.j, self.bin, at["POSITION"]).astype(float)
            jo = accessor(self.j, self.bin, at["JOINTS_0"]).astype(int)
            w = accessor(self.j, self.bin, at["WEIGHTS_0"]).astype(float)
            w = w / w.sum(1, keepdims=True)
            morph = None
            if "targets" in prim:
                morph = sum(accessor(self.j, self.bin, t["POSITION"]).astype(float) for t in prim["targets"])
            self._mesh_cache[name] = (pos, jo, w, morph)
        return self._mesh_cache[name]

    # ---------------------------------------------------------------- kinematics
    def fk(self, Rw, root):
        """Bone heads (F,B,3) from world bone frames (F,B,3,3) and the root head (F,3)."""
        F = Rw.shape[0]
        H = np.zeros((F, self.B, 3))
        for b in range(self.B):
            p = self.parent[b]
            H[:, b] = root if p < 0 else H[:, p] + np.einsum("fij,j->fi", Rw[:, p], self.off[b])
        return H

    def to_local(self, Rw):
        L = np.empty_like(Rw)
        for b in range(self.B):
            p = self.parent[b]
            L[:, b] = Rw[:, b] if p < 0 else np.einsum("fji,fjk->fik", Rw[:, p], Rw[:, b])
        return L

    def to_world(self, L):
        Rw = np.empty_like(L)
        for b in range(self.B):
            p = self.parent[b]
            Rw[:, b] = L[:, b] if p < 0 else Rw[:, p] @ L[:, b]
        return Rw

    def skin(self, name, Rw, H, vids=None, morph_w=1.0):
        """World positions (F,N,3) of mesh vertices under the pose (LBS, as glTF does)."""
        pos, jo, w, morph = self.mesh(name)
        if vids is not None:
            pos, jo, w = pos[vids], jo[vids], w[vids]
            morph = None if morph is None else morph[vids]
        if morph is not None:
            pos = pos + morph * morph_w
        M = Rw @ np.transpose(self.Rr, (0, 2, 1))[None]            # (F,B,3,3)
        T = H - np.einsum("fbij,bj->fbi", M, self.head)           # (F,B,3)
        out = np.zeros((Rw.shape[0], len(pos), 3))
        for k in range(4):
            b = jo[:, k]
            out += w[None, :, k, None] * (np.einsum("fnij,nj->fni", M[:, b], pos) + T[:, b])
        return out

    def stand_world(self, F=1):
        Rw = np.repeat(self.Tst[None], F, 0)
        root = np.repeat(self.Hst[None, 0], F, 0)
        return Rw, root

    def facing(self, Rw):
        """Horizontal facing direction of the pelvis (stand pose faces +Z)."""
        r = self.ix["root"]
        f = np.einsum("fij,j->fi", Rw[:, r] @ self.Tst[r].T, np.array([0.0, 0, 1]))
        f[:, 1] = 0
        return f / np.linalg.norm(f, axis=1, keepdims=True)

    # ------------------------------------------------------------------ soles
    def sole_points(self):
        """Per side: shoe vertex ids of the heel and of the ball/toe part of the sole (stand pose)."""
        if hasattr(self, "_soles"):
            return self._soles
        Rw, root = self.stand_world()
        H = self.fk(Rw, root)
        P = self.skin("shoes", Rw, H)[0]
        out = {}
        for s, sx in (("L", 1), ("R", -1)):
            side = np.nonzero(P[:, 0] * sx > 0)[0]
            q = P[side]
            y0 = q[:, 1].min()
            sole = side[q[:, 1] < y0 + 0.012]
            z = P[sole, 2]
            zmin, zmax = z.min(), z.max()
            L = zmax - zmin
            heel = sole[z < zmin + 0.22 * L]
            ball = sole[(z > zmin + 0.62 * L) & (z < zmin + 0.86 * L)]
            tip = sole[z > zmin + 0.86 * L]
            out[s] = dict(heel=heel, ball=ball, tip=tip, all=side, sole_y=y0, length=L)
        self._soles = out
        return out


# ============================================================================ motion container
@dataclass
class Motion:
    name: str
    Rw: np.ndarray                  # (F,B,3,3) world bone frames
    root: np.ndarray                # (F,3) root head
    fps: float = FPS
    loop: bool = False
    info: dict = field(default_factory=dict)
    morph: np.ndarray | None = None   # (F,2) stand_corrective_L/R weights
    D: np.ndarray = field(default_factory=lambda: np.zeros(3))   # loop displacement (travelling loops)
    src_leg: dict | None = None       # scaled source hip -> ankle vectors per side (F,3)

    @property
    def F(self):
        return self.Rw.shape[0]

    def copy(self):
        return Motion(self.name, self.Rw.copy(), self.root.copy(), self.fps, self.loop, dict(self.info),
                      None if self.morph is None else self.morph.copy(), self.D.copy(),
                      None if self.src_leg is None else {k: v.copy() for k, v in self.src_leg.items()})


# ============================================================================ retarget
PRIMARY = {}   # source joint -> the target bone whose calibration defines it
SEG_AIM = {}   # target limb bone -> (segment end bone, source joint, source child joint)
for _s, _S in (("L", "Left"), ("R", "Right")):
    SEG_AIM[f"upperleg01.{_s}"] = (f"lowerleg01.{_s}", f"{_S}UpLeg", f"{_S}Leg")
    SEG_AIM[f"lowerleg01.{_s}"] = (f"foot.{_s}", f"{_S}Leg", f"{_S}Foot")
    SEG_AIM[f"upperarm01.{_s}"] = (f"lowerarm01.{_s}", f"{_S}Arm", f"{_S}ForeArm")
    SEG_AIM[f"lowerarm01.{_s}"] = (f"wrist.{_s}", f"{_S}ForeArm", f"{_S}Hand")
for _b, _m in MAP.items():
    PRIMARY.setdefault(_m, _b)


REF_LOWER = ("Hips", "LHipJoint", "RHipJoint", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
             "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase", "LowerBack", "Spine", "Spine1")


def retarget(body: Body, bvh_path, t0=None, t1=None, fps=FPS, name="clip", ref=None, ref_w=None):
    """ref=(ta, tb): source seconds where the actor stands still; ref_w={source joint: w}.  For those
    joints the calibration pairs the actor's mean standing pose in that window (w=1), rather than the
    synthetic frame-0 T-pose (w=0), with the model's stand pose.  CMU's knee / pelvis joint centres
    make quiet standing read as ~20 deg of knee bend and a pelvis tipped forward; paired with the
    frame-0 T-pose the model would stand crouched and leaning forward."""
    clip = load_bvh(bvh_path)
    P, Rs = clip.world()
    P = P * CMU_UNIT_M
    ix = {n: i for i, n in enumerate(clip.names)}
    B = body.B
    # target calibration = the pose of the target that matches the source's frame-0 T-pose: MakeHuman
    # rest, with each limb SEGMENT (upperleg01 head -> knee, knee -> ankle, shoulder -> elbow,
    # elbow -> wrist) re-aimed along the source segment (note: upperleg01 is a short bone 21 deg off the
    # thigh axis, so aiming the bone itself would bow the legs), and the feet flat as in the rest pose,
    # turned about the vertical to the source feet's heading.
    Rcal = np.zeros((B, 3, 3))
    for b in range(B):
        p = body.parent[b]
        Rcal[b] = body.Rr[b] if p < 0 else (Rcal[p] @ body.Rr[p].T) @ body.Rr[b]
        n = body.names[b]
        if n in SEG_AIM:
            end, sa, sb = SEG_AIM[n]
            seg = Rcal[b] @ body.Rr[b].T @ (body.head[body.ix[end]] - body.head[b])
            Rcal[b] = min_rot(seg, P[0, ix[sb]] - P[0, ix[sa]]) @ Rcal[b]
        elif n.startswith("foot."):
            S = "Left" if n.endswith("L") else "Right"
            want = P[0, ix[f"{S}ToeBase"]] - P[0, ix[f"{S}Foot"]]
            have = body.head[body.ix[f"toe3-1.{n[-1]}"]] - body.head[b]
            ang = heading_angle(want) - heading_angle(have)
            Rcal[b] = rot_y(ang) @ body.Rr[b]
    # frames
    src_fps = clip.fps
    f_first = 1 if t0 is None else max(1, int(round(t0 * src_fps)) + 1)
    f_last = clip.n_frames - 1 if t1 is None else min(clip.n_frames - 1, int(round(t1 * src_fps)) + 1)
    ts = np.arange(f_first, f_last + 1e-9, src_fps / fps)
    fi = np.clip(np.round(ts).astype(int), 1, clip.n_frames - 1)
    Rsrc = Rs[fi]
    R0 = Rs[0]
    F = len(fi)
    # the source rotation that each source joint has when the model is in its stand pose
    Scal = {}
    for mj, bn in PRIMARY.items():
        bs = body.ix[bn]
        Scal[mj] = body.Tst[bs] @ Rcal[bs].T @ R0[ix[mj]]
    if ref is not None and ref_w:
        wa, wb = (max(1, int(round(t * src_fps)) + 1) for t in ref)
        f = Rs[wa:wb, ix["Hips"]][:, :, 2]
        psi = np.arctan2(f[:, 0].mean(), f[:, 2].mean())
        for mj, w in ref_w.items():
            Sref = rot_y(-psi) @ orthonormalize(Rs[wa:wb, ix[mj]].sum(0)[None])[0]
            Scal[mj] = slerp_mats(Scal[mj][None], Sref[None], np.array([w]))[0]
    Rw = np.zeros((F, B, 3, 3))
    for b in range(B):
        n = body.names[b]
        m = MAP.get(n)
        if m is not None:
            K = Scal[m].T @ body.Tst[b]
            Rw[:, b] = Rsrc[:, ix[m]] @ K
        else:
            p = body.parent[b]
            Rw[:, b] = Rw[:, p] @ (body.Tst[p].T @ body.Tst[b])
    # root translation, scaled by the leg-length ratio
    def leglen_src(s):
        S = "Left" if s == "L" else "Right"
        return (np.linalg.norm(P[0, ix[f"{S}Leg"]] - P[0, ix[f"{S}UpLeg"]]) +
                np.linalg.norm(P[0, ix[f"{S}Foot"]] - P[0, ix[f"{S}Leg"]]))

    def leglen_tgt(s):
        g = body.legs[s]
        return (np.linalg.norm(body.head[g["knee"]] - body.head[g["hip"]]) +
                np.linalg.norm(body.head[g["foot"]] - body.head[g["knee"]]))

    k = (leglen_tgt("L") + leglen_tgt("R")) / (leglen_src("L") + leglen_src("R"))
    hips = P[fi, ix["Hips"]]
    ground = np.percentile(P[1:, :, 1].min(axis=1), 2)
    root = np.zeros((F, 3))
    root[:, [0, 2]] = (hips[:, [0, 2]] - hips[0, [0, 2]]) * k
    root[:, 1] = (hips[:, 1] - ground) * k
    m = Motion(name, Rw, root, fps, info=dict(source=Path(bvh_path).name, t0=t0, t1=t1, scale=float(k)))
    # the source's hip -> ankle vectors, scaled: the legs are re-solved to them (match_leg_vectors)
    m.src_leg = {s: (leglen_tgt(s) / leglen_src(s)) * (P[fi, ix[f"{S}Foot"]] - P[fi, ix[f"{S}UpLeg"]])
                 for s, S in (("L", "Left"), ("R", "Right"))}
    return m


def match_leg_vectors(body, m: Motion):
    """Copying the thigh and shin directions puts the target's feet at different heights than the
    source's when the segment proportions differ and a knee is bent (e.g. a weight-shifted stance:
    one foot 2-3 cm in the air, the other through the floor).  Re-solve each leg with two-bone IK so
    that hip -> ankle equals the source's scaled hip -> ankle vector; the knee keeps its bend plane
    and the foot its orientation.  For clips calibrated on the frame-0 T-pose only; the built-in clips
    use a standing reference (retarget(ref=...)) instead, which makes this unnecessary."""
    H = body.fk(m.Rw, m.root)
    targets = {s: H[:, body.legs[s]["hip"]] + m.src_leg[s] for s in "LR"}
    before = {s: np.linalg.norm(H[:, body.legs[s]["foot"]] - targets[s], axis=1) for s in "LR"}
    m.Rw, m.root, drop = leg_ik(body, m.Rw, m.root, targets)
    m.info["leg_vector_fix_cm"] = {s: round(100 * float(before[s].max()), 1) for s in "LR"}
    return m


# ============================================================================ clean-up steps
def turn(m: Motion, ang, pivot=None):
    """Rotate the whole motion about the vertical axis through `pivot` (default: first root xz)."""
    R = rot_y(ang)
    piv = np.array(m.root[0] if pivot is None else pivot, float)
    piv[1] = 0
    m.Rw = np.einsum("ij,fbjk->fbik", R, m.Rw)
    m.root = (m.root - piv) @ R.T + piv
    if m.src_leg is not None:
        m.src_leg = {s: v @ R.T for s, v in m.src_leg.items()}
    return m


def heading_angle(v):
    """Yaw angle (about +Y) that takes +Z onto the horizontal direction v."""
    return np.arctan2(v[0], v[2])


def align_heading(body, m: Motion, mode="facing", frames=None, target=0.0):
    """Turn the clip so that its mean facing (or travel direction) is at yaw `target` (0 = +Z)."""
    if mode == "travel":
        d = m.root[-1] - m.root[0]
        a = heading_angle(d)
    else:
        f = body.facing(m.Rw)
        sel = slice(None) if frames is None else frames
        v = f[sel].mean(0)
        a = heading_angle(v)
    turn(m, target - a)
    m.root[:, [0, 2]] -= m.root[0, [0, 2]]
    return m




def gaze_pitch(body, Rw):
    """Pitch of the head's forward axis above the horizon, degrees (F,)."""
    h = body.ix["head"]
    fw = np.einsum("fij,j->fi", Rw[:, h], body.Tst[h].T @ np.array([0.0, 0, 1]))
    return np.degrees(np.arcsin(np.clip(fw[:, 1], -1, 1)))


def bone_pitch(body, Rw, name):
    """Pitch (deg) of a bone's stand-pose forward axis above the horizon, (F,)."""
    b = body.ix[name]
    fw = np.einsum("fij,j->fi", Rw[:, b], body.Tst[b].T @ np.array([0.0, 0, 1]))
    return np.degrees(np.arcsin(np.clip(fw[:, 1], -1, 1)))


def _nod(body, Rw, bones, weights, delta, axis=(1.0, 0, 0)):
    """Add a constant rotation spread over `bones` about one of the head's own axes (stand-pose
    frame): axis x (lateral) = nod, delta > 0 raises the face; axis z (forward) = roll, delta > 0
    lifts the head's left side."""
    h = body.ix["head"]
    ax_w = np.einsum("fij,j->fi", Rw[:, h], body.Tst[h].T @ np.array(axis, float))
    sign = -1.0 if axis[0] else 1.0     # rotating +z about +x tips it down; +x about +z lifts it
    L = body.to_local(Rw)
    for n, w in zip(bones, weights):
        b = body.ix[n]
        ax = np.einsum("fji,fj->fi", Rw[:, b], ax_w)            # the same axis in the bone's own frame
        L[:, b] = L[:, b] @ axis_angle(ax, np.full(len(Rw), sign * w * delta))
    return body.to_world(L)


def head_roll(body, Rw):
    """Sideways tilt (deg) of the head: elevation of its lateral axis, (F,)."""
    h = body.ix["head"]
    x = np.einsum("fij,j->fi", Rw[:, h], body.Tst[h].T @ np.array([1.0, 0, 0]))
    return np.degrees(np.arcsin(np.clip(x[:, 1], -1, 1)))


def head_level(body, m: Motion, gaze_deg=-3.0, neck_deg=-4.0, frames=None, roll_damp=0.0):
    """Constant neck / head pitch offsets so that the median neck-base pitch is neck_deg and the median
    gaze is gaze_deg (relative to the model's stand pose).  CMU neck/head marker calibration differs
    per session: some sessions tilt the head 20 deg back on a forward neck, some stare at the floor."""
    sel = slice(None) if frames is None else frames
    before = (float(np.median(bone_pitch(body, m.Rw, "neck01")[sel])), float(np.median(gaze_pitch(body, m.Rw)[sel])))
    d1 = np.radians(neck_deg - before[0])
    m.Rw = _nod(body, m.Rw, ("spine01", "neck01"), (0.3, 0.7), d1)
    cur = float(np.median(gaze_pitch(body, m.Rw)[sel]))
    m.Rw = _nod(body, m.Rw, ("neck02", "neck03", "head"), (0.3, 0.3, 0.4), np.radians(gaze_deg - cur))
    # the same calibration spread shows up as a constant sideways head tilt in some sessions
    roll0 = float(np.median(head_roll(body, m.Rw)[sel]))
    m.Rw = _nod(body, m.Rw, ("neck01", "neck02", "neck03", "head"), (0.2, 0.25, 0.25, 0.3), np.radians(-roll0),
                axis=(0, 0, 1.0))
    if roll_damp > 0:   # calm the side-to-side head wobble (walks): per-frame, same bone split
        dev = head_roll(body, m.Rw)
        dev = smooth(dev - np.median(dev[sel]), 1.0)
        h = body.ix["head"]
        ax_w = np.einsum("fij,j->fi", m.Rw[:, h], body.Tst[h].T @ np.array([0, 0, 1.0]))
        L = body.to_local(m.Rw)
        for n, w in zip(("neck01", "neck02", "neck03", "head"), (0.2, 0.25, 0.25, 0.3)):
            bi = body.ix[n]
            ax = np.einsum("fji,fj->fi", m.Rw[:, bi], ax_w)
            L[:, bi] = L[:, bi] @ axis_angle(ax, -roll_damp * w * np.radians(dev))
        m.Rw = body.to_world(L)
    r = head_roll(body, m.Rw)[sel]
    m.info["head_roll_median_deg"] = [round(roll0, 1), round(float(np.median(r)), 1)]
    m.info["head_roll_range_deg"] = [round(float(r.min()), 1), round(float(r.max()), 1)]
    after = (float(np.median(bone_pitch(body, m.Rw, "neck01")[sel])), float(np.median(gaze_pitch(body, m.Rw)[sel])))
    m.info["neck_gaze_pitch_median_deg"] = dict(before=[round(x, 1) for x in before], after=[round(x, 1) for x in after])
    return m


def scale_swing(body, m: Motion, gains):
    """Scale the swing of limb joints about their clip-mean local rotation: gains {bone: k}.  CMU's
    relaxed walk has a small arm swing that reads stiff on a slim character."""
    L = body.to_local(m.Rw)
    for n, k in gains.items():
        b = body.ix[n]
        Lm = orthonormalize(L[:, b].sum(0)[None])[0]
        dev = rot_log(np.einsum("ji,fjk->fik", Lm, L[:, b]))
        L[:, b] = Lm[None] @ rot_exp(dev * k)
    m.Rw = body.to_world(L)
    m.info["swing_gain"] = gains
    return m


def widen_stance(body, m: Motion, deg=2.5):
    """Abduct both legs by `deg` at the hips (about the pelvis' forward axis), feet keeping their world
    orientation.  CMU 142_13 walks on a line (the swing foot crosses in front of the stance foot seen from
    the front), which reads as a catwalk / scissoring gait; the foot planting afterwards re-pins the
    stances on the wider track."""
    z = np.array([0.0, 0, 1])
    rb = body.ix["root"]
    fwd = np.einsum("fij,j->fi", m.Rw[:, rb] @ body.Tst[rb].T, z)
    L = body.to_local(m.Rw)
    Wf = {s: m.Rw[:, body.legs[s]["foot"]].copy() for s in "LR"}
    for s, sx in (("L", 1.0), ("R", -1.0)):
        b = body.legs[s]["hip"]
        ax = np.einsum("fji,fj->fi", m.Rw[:, b], fwd)            # forward axis in the thigh's frame
        # a positive rotation about +z (forward) swings a downward leg towards +x (the character's left)
        L[:, b] = L[:, b] @ axis_angle(ax, np.full(m.F, sx * np.radians(deg)))
    Rw = body.to_world(L)
    for s in "LR":
        f = body.legs[s]["foot"]
        L[:, f] = np.einsum("fji,fjk->fik", Rw[:, body.parent[f]], Wf[s])
    m.Rw = body.to_world(L)
    m.info["stance_widen_deg"] = deg
    return m


def calm_head(body, m: Motion, scale=0.5, pitch_lim_deg=10.0, yaw_lim_deg=35.0, roll_lim_deg=6.0, iters=2):
    """Quieter glances: the head's orientation relative to the chest, as a deviation from the clip's
    mean, is scaled by `scale` and clamped (pitch = nod, yaw = turn, roll = tilt, in the head's stand
    frame); the correction is spread over the neck and head bones.  Mocap idles often have the actor
    look up at the ceiling or down at the floor, which reads as unsettling on a character."""
    ch, hd = body.ix["spine01"], body.ix["head"]
    chain = (("neck01", 0.25), ("neck02", 0.25), ("neck03", 0.2), ("head", 0.3))
    Tst_rel = body.Tst[ch].T @ body.Tst[hd]
    before = None
    for it in range(iters):
        Q = np.einsum("fji,fjk->fik", m.Rw[:, ch], m.Rw[:, hd]) @ Tst_rel.T      # head rel. chest, stand = I
        Qm = orthonormalize(Q.sum(0)[None])[0]
        r = rot_log(np.einsum("ji,fjk->fik", Qm, Q))                            # deviation (chest frame)
        # r is in the chest bone frame, which is close to the world axes in the stand pose
        # (x lateral = pitch / nod, y up = yaw / turn, z forward = roll / tilt)
        rr = r * scale if it == 0 else r
        lim = np.radians([pitch_lim_deg, yaw_lim_deg, roll_lim_deg])
        rr = np.clip(rr, -lim, lim)
        if before is None:
            before = np.degrees(np.abs(r).max(0))
        Qn = Qm[None] @ rot_exp(rr)
        K = Qn @ np.transpose(Q, (0, 2, 1))                                     # correction, chest frame
        kw = np.einsum("fij,fj->fi", m.Rw[:, ch], rot_log(K))                   # world axis-angle
        L = body.to_local(m.Rw)
        Rw = m.Rw
        for n, w in chain:
            b = body.ix[n]
            L[:, b] = L[:, b] @ rot_exp(np.einsum("fji,fj->fi", Rw[:, b], kw) * w)
        m.Rw = body.to_world(L)
    Q = np.einsum("fji,fjk->fik", m.Rw[:, ch], m.Rw[:, hd]) @ Tst_rel.T
    Qm = orthonormalize(Q.sum(0)[None])[0]
    after = np.degrees(np.abs(rot_log(np.einsum("ji,fjk->fik", Qm, Q))).max(0))
    m.info["head_calm"] = dict(scale=scale, dev_max_deg_before=[round(float(x), 1) for x in before],
                               dev_max_deg_after=[round(float(x), 1) for x in after])
    return m


def _twist_about_y(M):
    """Swing-twist split of rotations M (F,3,3) about the local y axis: M = S @ T(y, ang). Returns (S, ang)."""
    q = mat_to_quat(M)
    tw = np.zeros_like(q)
    tw[:, 1] = q[:, 1]
    tw[:, 3] = q[:, 3]
    n = np.linalg.norm(tw, axis=1)
    ang = np.where(n > 1e-9, 2 * np.arctan2(tw[:, 1], tw[:, 3]), 0.0)
    ang = (ang + np.pi) % (2 * np.pi) - np.pi
    T = axis_angle(np.tile([0.0, 1.0, 0.0], (len(M), 1)), ang)
    return M @ np.transpose(T, (0, 2, 1)), ang


def spread_twist(body, m: Motion, split=(0.3, 0.4), wrist_bend_max_deg=40.0, upper_split=0.5):
    """Linear blend skinning collapses a limb that twists at a single joint (candy-wrapper wrist).
    The roll of the hand about the forearm axis (relative to the stand pose) is spread over
    lowerarm01 (split[0]), lowerarm02 (split[1]) and the wrist (rest); the hand keeps its world
    orientation except that the wrist bend is clamped to wrist_bend_max_deg.  The upper-arm roll is
    shared between upperarm01 and upperarm02 (upper_split)."""
    Rw = m.Rw
    L = body.to_local(Rw)
    Lst = body.to_local(body.Tst[None])[0]
    Y = np.tile([0.0, 1.0, 0.0], (m.F, 1))
    for s in "LR":
        sh, ua1, ua2 = body.ix[f"shoulder01.{s}"], body.ix[f"upperarm01.{s}"], body.ix[f"upperarm02.{s}"]
        la1, la2, wr = body.ix[f"lowerarm01.{s}"], body.ix[f"lowerarm02.{s}"], body.ix[f"wrist.{s}"]
        # ---- upper arm: roll of upperarm01 (relative to its stand relation) shared with upperarm02
        E = np.einsum("ji,fjk->fik", Lst[ua1], L[:, ua1])               # L_ua1 = Lst_ua1 @ E
        S, a_u = _twist_about_y(E)
        W_sh = Rw[:, sh]
        W_ua1 = W_sh @ Lst[ua1] @ S @ axis_angle(Y, (1 - upper_split) * a_u)
        W_ua2 = Rw[:, ua2]                                               # keeps the full roll
        # ---- forearm: remove lowerarm01's own roll, then measure the hand's roll about the forearm
        W_la1_orig = Rw[:, la1]
        E1 = np.einsum("fji,fjk->fik", W_ua2 @ Lst[la1], W_la1_orig)    # la1 relative to its stand relation
        S1, _ = _twist_about_y(E1)
        W_la1_0 = W_ua2 @ Lst[la1] @ S1
        W_la2_0 = W_la1_0 @ Lst[la2]
        W_wr = Rw[:, wr]
        Dh = np.einsum("fji,fjk->fik", W_la2_0, W_wr) @ Lst[wr].T       # W_wr = W_la2_0 @ Dh @ Lst_wr
        Sh, tau = _twist_about_y(Dh)
        # clamp the wrist bend (swing)
        ang = rot_angle(Sh)
        lim = np.radians(wrist_bend_max_deg)
        k = np.where(ang > lim, lim / np.maximum(ang, 1e-9), 1.0)
        Sh = rot_exp(rot_log(Sh) * k[:, None])
        W_wr_new = W_la2_0 @ Sh @ axis_angle(Y, tau) @ Lst[wr]
        W_la1 = W_la1_0 @ axis_angle(Y, split[0] * tau)
        W_la2 = W_la2_0 @ axis_angle(Y, (split[0] + split[1]) * tau)
        L[:, ua1] = np.einsum("fji,fjk->fik", W_sh, W_ua1)
        L[:, ua2] = np.einsum("fji,fjk->fik", W_ua1, W_ua2)
        L[:, la1] = np.einsum("fji,fjk->fik", W_ua2, W_la1)
        L[:, la2] = np.einsum("fji,fjk->fik", W_la1, W_la2)
        L[:, wr] = np.einsum("fji,fjk->fik", W_la2, W_wr_new)
        m.info.setdefault("roll_deg", {})[s] = dict(
            upperarm_max=round(float(np.degrees(np.abs(a_u)).max()), 1),
            hand_about_forearm_max=round(float(np.degrees(np.abs(tau)).max()), 1),
            wrist_bend_clamped_frames=int((k < 1).sum()))
    m.Rw = body.to_world(L)
    return m


# ---------------------------------------------------------------------------- feet
def _runs(mask):
    """[(start, end_exclusive)] of True runs."""
    d = np.diff(np.r_[0, mask.astype(int), 0])
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def _clean_mask(mask, min_on=3, min_gap=3):
    m = mask.copy()
    for s, e in _runs(~m):                      # fill short gaps
        if e - s < min_gap and s > 0 and e < len(m):
            m[s:e] = True
    for s, e in _runs(m):                       # drop short blips
        if e - s < min_on:
            m[s:e] = False
    return m


def sole_tracks(body, m: Motion, Rw=None, root=None):
    """Per side: heel / ball points (F,3), lowest shoe point y (F,), for the given pose."""
    Rw = m.Rw if Rw is None else Rw
    root = m.root if root is None else root
    H = body.fk(Rw, root)
    so = body.sole_points()
    out = {}
    for s in "LR":
        g = so[s]
        P = body.skin("shoes", Rw, H, g["all"])
        loc = {k: np.searchsorted(g["all"], g[k]) for k in ("heel", "ball", "tip")}
        heel = P[:, loc["heel"]]
        ball = P[:, loc["ball"]]
        out[s] = dict(heel=np.c_[heel[..., 0].mean(1), heel[..., 1].min(1), heel[..., 2].mean(1)],
                      ball=np.c_[ball[..., 0].mean(1), ball[..., 1].min(1), ball[..., 2].mean(1)],
                      tip_y=P[:, loc["tip"], 1].min(1), low=P[..., 1].min(1), H=H)
    return out


def detect_contacts(tr, fps, h_thr=0.035, v_thr=0.35, gh_thr=None, gv_thr=None):
    """Per foot: stance mask (foot planted: pinned in xz), ground mask (sole resting on the floor,
    possibly pivoting / shuffling: pinned in y only; thresholds gh_thr / gv_thr, default = stance) and
    the pivot choice (0 heel, 1 ball) per frame, from sole heights and speeds."""
    out = {}
    for s in "LR":
        t = tr[s]
        sp = {}
        for k in ("heel", "ball"):
            v = np.gradient(t[k][:, [0, 2]], axis=0) * fps
            sp[k] = np.linalg.norm(v, axis=1)
        heel_c = (t["heel"][:, 1] < h_thr) & (sp["heel"] < v_thr)
        ball_c = (t["ball"][:, 1] < h_thr) & (sp["ball"] < v_thr)
        stance = _clean_mask(heel_c | ball_c)
        pivot = np.where(heel_c & ((t["heel"][:, 1] <= t["ball"][:, 1] + 0.01) | ~ball_c), 0, 1)
        # a pivot, once it moved to the ball, stays there until the stance ends (heel -> ball roll)
        for s0, e0 in _runs(stance):
            seen_ball = False
            for f in range(s0, e0):
                if pivot[f] == 1 and not heel_c[f]:
                    seen_ball = True
                if seen_ball:
                    pivot[f] = 1
        gh = h_thr if gh_thr is None else gh_thr
        gv = v_thr if gv_thr is None else gv_thr
        ground = _clean_mask(((t["heel"][:, 1] < gh) & (sp["heel"] < gv)) |
                             ((t["ball"][:, 1] < gh) & (sp["ball"] < gv))) | stance
        out[s] = dict(stance=stance, pivot=pivot, speed=sp, ground=ground)
    return out


def _unit(x):
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)


def _frame(a, k):
    """(F,3,3) frames with columns a, k (made perpendicular to a), a x k."""
    a = _unit(a)
    k = _unit(k - a * np.sum(a * k, -1, keepdims=True))
    return np.stack([a, k, np.cross(a, k)], -1)


def knee_forward(body, Rw, g, pelvis_w=0.3):
    """Direction the knee should point: the foot's forward (stand-relative) blended with the pelvis'
    forward, flattened to the horizontal plane."""
    z = np.array([0.0, 0, 1])
    ff = np.einsum("fij,j->fi", Rw[:, g["foot"]] @ body.Tst[g["foot"]].T, z)
    rb = body.ix["root"]
    pf = np.einsum("fij,j->fi", Rw[:, rb] @ body.Tst[rb].T, z)
    kf = (1 - pelvis_w) * ff + pelvis_w * pf
    kf[:, 1] = 0.0
    return _unit(kf)


def _two_bone(hip, knee, ankle, target, kf, L1=None, L2=None, min_flex_deg=2.5):
    """Knee position for a hip->knee->ankle chain reaching `target` (all (F,3)).  The knee always bends
    forward in the sagittal plane spanned by hip->target and the knee-forward direction kf (so a nearly
    straight mocap knee can never flip backwards or bend sideways), with at least min_flex_deg of flex."""
    L1 = np.linalg.norm(knee - hip, axis=1) if L1 is None else L1
    L2 = np.linalg.norm(ankle - knee, axis=1) if L2 is None else L2
    r = target - hip
    d = np.linalg.norm(r, axis=1)
    dmax = np.sqrt(L1 ** 2 + L2 ** 2 + 2 * L1 * L2 * np.cos(np.radians(min_flex_deg)))
    short = np.maximum(d - dmax, 0)
    d = np.clip(d, np.abs(L1 - L2) + 1e-4, dmax)
    u = _unit(r)
    tgt = hip + u * d[:, None]
    v = _unit(kf - u * np.sum(kf * u, 1, keepdims=True))
    ca = np.clip((L1 ** 2 + d ** 2 - L2 ** 2) / (2 * L1 * d), -1, 1)
    sa = np.sqrt(1 - ca ** 2)
    knee_new = hip + L1[:, None] * (ca[:, None] * u + sa[:, None] * v)
    return knee_new, tgt, short


def leg_ik(body, Rw, root, targets, max_iter=2):
    """Move each ankle (foot bone head) to targets[s] (F,3) with two-bone IK, feet keep their world
    orientation.  The pelvis is lowered where a target is out of reach.  The thigh and shin are rebuilt
    as a clean hinge: their frames relate to (segment direction, knee-forward) exactly as in the stand
    pose, so the knee bends only forwards, over the toes.  Returns new Rw, root, drop."""
    Rw = Rw.copy()
    root = root.copy()
    drop_total = np.zeros(len(root))
    for _ in range(max_iter):
        H = body.fk(Rw, root)
        need = np.zeros(len(root))
        for s, g in body.legs.items():
            hip, ankle = H[:, g["hip"]], targets[s]
            L1 = np.linalg.norm(H[:, g["knee"]] - hip, axis=1)
            L2 = np.linalg.norm(H[:, g["foot"]] - H[:, g["knee"]], axis=1)
            Lm = 0.998 * (L1 + L2)
            r = ankle - hip
            rxz2 = r[:, 0] ** 2 + r[:, 2] ** 2
            dy = -np.sqrt(np.maximum(Lm ** 2 - rxz2, 0)) - r[:, 1]     # >0: hip must come down by dy
            need = np.maximum(need, dy)
        need = np.maximum(need, 0)
        if need.max() < 1e-4:
            break
        from scipy.ndimage import maximum_filter1d
        dd = smooth(maximum_filter1d(need, 7), 2.0)
        dd = np.maximum(dd, need)
        root[:, 1] -= dd
        drop_total += dd
    H = body.fk(Rw, root)
    Hs = body.fk(body.Tst[None], body.Hst[None, 0])[0]
    z = np.tile([0.0, 0, 1], (len(root), 1))
    L = body.to_local(Rw)
    for s, g in body.legs.items():
        hip, knee, ankle = H[:, g["hip"]], H[:, g["knee"]], H[:, g["foot"]]
        kf = knee_forward(body, Rw, g)
        knee_new, tgt, _ = _two_bone(hip, knee, ankle, targets[s], kf)
        # stand relations: bone frame = F(segment, knee-forward) @ C
        a0 = Hs[g["knee"]] - Hs[g["hip"]]
        b0 = Hs[g["foot"]] - Hs[g["knee"]]
        C_th = _frame(a0[None], z[:1])[0].T @ body.Tst[g["hip"]]
        C_sh = _frame(b0[None], z[:1])[0].T @ body.Tst[g["knee"]]
        W = {k: Rw[:, g[k]] for k in ("hip", "thigh2", "knee", "shin2", "foot")}
        W_hip = _frame(knee_new - hip, kf) @ C_th
        W_knee = _frame(tgt - knee_new, kf) @ C_sh
        d_th = W_hip @ np.transpose(W["hip"], (0, 2, 1))
        d_sh = W_knee @ np.transpose(W["knee"], (0, 2, 1))
        Wn = {"hip": W_hip, "thigh2": d_th @ W["thigh2"], "knee": W_knee, "shin2": d_sh @ W["shin2"],
              "foot": W["foot"]}
        par = {"hip": Rw[:, body.parent[g["hip"]]], "thigh2": Wn["hip"],
               "knee": Wn["thigh2"], "shin2": Wn["knee"], "foot": Wn["shin2"]}
        for k in Wn:
            L[:, g[k]] = np.einsum("fji,fjk->fik", par[k], Wn[k])
    Rw = body.to_world(L)
    return Rw, root, drop_total


def signed_knee_flex(body, Rw, root):
    """Per leg: signed knee flexion (deg, > 0 = knee in front of the hip-ankle line, bending forward)
    and the knee's sideways (varus / valgus) deviation angle from the sagittal plane (deg)."""
    H = body.fk(Rw, root)
    out = {}
    for s, g in body.legs.items():
        hip, knee, ankle = H[:, g["hip"]], H[:, g["knee"]], H[:, g["foot"]]
        th, sh = knee - hip, ankle - knee
        flex = np.degrees(np.arccos(np.clip(np.sum(_unit(th) * _unit(sh), 1), -1, 1)))
        u = _unit(ankle - hip)
        off = (knee - hip) - u * np.sum((knee - hip) * u, 1, keepdims=True)
        kf = knee_forward(body, Rw, g)
        sgn = np.sign(np.sum(off * kf, 1))
        side = np.degrees(np.arctan2(np.abs(np.sum(off * _unit(np.cross(u, kf)), 1)),
                                     np.abs(np.sum(off * kf, 1)) + 1e-9)) * (np.linalg.norm(off, axis=1) > 0.004)
        out[s] = (flex * np.where(sgn == 0, 1, sgn), side)
    return out


def level_feet(body, m: Motion, h_thr=0.03, v_thr=0.25, max_deg=15.0):
    """Per-clip constant foot calibration: CMU sessions define the flat foot differently, so a
    retargeted stance foot can be pitched / rolled a few degrees (heel or edge through the floor).
    The mean rotation that makes the sole level over the foot-flat frames (heel and ball both down,
    foot still) is added to the foot bone for the whole clip."""
    tr = sole_tracks(body, m)
    L = body.to_local(m.Rw)
    up = np.array([0.0, 1.0, 0.0])
    out = {}
    for s in "LR":
        t = tr[s]
        f = body.legs[s]["foot"]
        low = np.minimum(t["heel"][:, 1], t["ball"][:, 1])
        flat = ((t["heel"][:, 1] - low < h_thr) & (t["ball"][:, 1] - low < h_thr) &
                (np.linalg.norm(np.gradient(t["ball"][:, [0, 2]], axis=0), axis=1) * m.fps < v_thr))
        if flat.sum() < 3:
            out[s] = 0.0
            continue
        n_w = np.einsum("fij,j->fi", m.Rw[:, f], body.Tst[f].T @ up)          # sole normal
        C = np.einsum("fji,fjk,fkl->fil", m.Rw[:, f], min_rot(n_w, np.tile(up, (m.F, 1))), m.Rw[:, f])
        v = rot_log(C[flat]).mean(0)                                           # foot-local correction
        ang = np.linalg.norm(v)
        if ang > np.radians(max_deg):
            v *= np.radians(max_deg) / ang
        L[:, f] = L[:, f] @ rot_exp(v)
        out[s] = round(float(np.degrees(np.linalg.norm(v))), 1)
    m.Rw = body.to_world(L)
    m.info["foot_level_deg"] = out
    return m


def knee_flexion(body, H):
    out = {}
    for s, g in body.legs.items():
        th = H[:, g["knee"]] - H[:, g["hip"]]
        sh = H[:, g["foot"]] - H[:, g["knee"]]
        c = np.sum(th * sh, 1) / (np.linalg.norm(th, axis=1) * np.linalg.norm(sh, axis=1))
        out[s] = np.arccos(np.clip(c, -1, 1))
    return out


def pelvis_for_targets(body, m: Motion, targets, w, p_range=(-0.05, 0.03), r_max_deg=6.0,
                       lam_p=60.0, lam_r=40.0, sigma=2.0):
    """Per frame, pick a pelvis height shift p and roll r (about the pelvis' forward axis) so that the
    stance legs (weights w[s]) reach their ankle targets with knee bends as close as possible to the
    current ones; smooth over time and apply to the root (the spine counter-rotates, so the chest
    keeps its orientation).  A straight leg is very stiff under IK: lifting its foot 1 cm costs
    ~15 deg of knee bend, so without this the pins would crouch the character."""
    H = body.fk(m.Rw, m.root)
    th0 = knee_flexion(body, H)
    ps = np.linspace(p_range[0], p_range[1], 41)
    rs = np.radians(np.linspace(-r_max_deg, r_max_deg, 25))
    P, Rr = np.meshgrid(ps, rs, indexing="ij")                  # (41,25)
    rootb = body.ix["root"]
    Rroot = m.Rw[:, rootb] @ body.Tst[rootb].T
    fwd = np.einsum("fij,j->fi", Rroot, [0, 0, 1.0])
    cost = lam_p * P[None] ** 2 + lam_r * Rr[None] ** 2
    cost = np.broadcast_to(cost, (m.F,) + P.shape).copy()
    for s, g in body.legs.items():
        hip = H[:, g["hip"]]
        L1 = np.linalg.norm(H[:, g["knee"]] - hip, axis=1)
        L2 = np.linalg.norm(H[:, g["foot"]] - H[:, g["knee"]], axis=1)
        rel = hip - m.root                                      # hip about the pelvis centre
        # vertical displacement of this hip under roll r about fwd: (fwd x rel).y * sin r (+ small cos term)
        lat = np.cross(fwd, rel)[:, 1]
        dy = P[None] + lat[:, None, None] * np.sin(Rr)[None] + rel[:, 1, None, None] * (np.cos(Rr)[None] - 1)
        r = targets[s] - hip
        d = np.sqrt(r[:, 0, None, None] ** 2 + (r[:, 1, None, None] - dy) ** 2 + r[:, 2, None, None] ** 2)
        cth = np.clip((L1[:, None, None] ** 2 + L2[:, None, None] ** 2 - d ** 2) / (2 * L1 * L2)[:, None, None], -1, 1)
        flex = np.pi - np.arccos(cth)
        over = np.maximum(d - 0.998 * (L1 + L2)[:, None, None], 0)
        cost += w[s][:, None, None] * (((flex - th0[s][:, None, None]) / np.radians(10)) ** 2 + (over / 0.005) ** 2)
    k = cost.reshape(m.F, -1).argmin(1)
    p = smooth(P.ravel()[k], sigma)
    r = smooth(Rr.ravel()[k], sigma)
    # apply: root height, root roll with the spine counter-rotated
    L = body.to_local(m.Rw)
    Q = axis_angle(fwd, r)
    sp = body.ix["spine05"]
    W_sp = m.Rw[:, sp].copy()
    m.Rw[:, rootb] = Q @ m.Rw[:, rootb]
    L[:, rootb] = m.Rw[:, rootb]
    L[:, sp] = np.einsum("fji,fjk->fik", m.Rw[:, rootb], W_sp)
    m.Rw = body.to_world(L)
    m.root[:, 1] += p
    return dict(height_mm=[round(1000 * float(p.min()), 1), round(1000 * float(p.max()), 1)],
                roll_deg=[round(float(np.degrees(r.min())), 1), round(float(np.degrees(r.max())), 1)])


def plant_feet(body, m: Motion, h_thr=0.035, v_thr=0.35, ramp=3, clearance=0.002, report=True, level=True,
               gh_thr=None, gv_thr=None, anchor="pivot", lock_yaw=0.0):
    """Pin the stance-foot pivot (heel, then ball) to the floor where it touched down, spread the
    correction over the swing, solve the legs with IK and keep the soles above y = 0.
    anchor="fixed": each stance holds one mean anchor (standing clips: no creep, loops close);
    lock_yaw in [0, 1] removes that share of the feet's swivel about the vertical (standing clips)."""
    fps = m.fps
    if level:
        level_feet(body, m)
    if lock_yaw > 0:
        L = body.to_local(m.Rw)
        for s in "LR":
            f = body.legs[s]["foot"]
            fw = np.einsum("fij,j->fi", m.Rw[:, f], body.Tst[f].T @ np.array([0, 0, 1.0]))
            yaw = np.unwrap(np.arctan2(fw[:, 0], fw[:, 2]))
            d = -lock_yaw * (yaw - yaw.mean())
            ax = np.einsum("fji,j->fi", m.Rw[:, f], np.array([0, 1.0, 0]))    # world up, foot frame
            L[:, f] = L[:, f] @ axis_angle(ax, d)
        m.Rw = body.to_world(L)
    tr = sole_tracks(body, m)
    # 1) floor: the median contact height -> 0
    lows = []
    for s in "LR":
        t = tr[s]
        v = np.linalg.norm(np.gradient(t["heel"][:, [0, 2]], axis=0), axis=1) * fps
        lows.append(np.minimum(t["heel"][:, 1], t["ball"][:, 1])[v < 0.2])
    lows = np.concatenate(lows)
    floor = float(np.median(lows)) if len(lows) else float(min(tr[s]["low"].min() for s in "LR"))
    m.root[:, 1] -= floor
    tr = sole_tracks(body, m)
    ct = detect_contacts(tr, fps, h_thr, v_thr, gh_thr, gv_thr)
    F = m.F
    targets = {}
    stats = {}
    for s in "LR":
        t, c = tr[s], ct[s]
        H = t["H"]
        ankle = H[:, body.legs[s]["foot"]]
        pts = np.stack([t["heel"], t["ball"]], 1)          # (F,2,3)
        o = np.full((F, 3), np.nan)
        runs = _runs(c["stance"])
        slide = []
        for s0, e0 in runs:
            if anchor == "fixed":
                # one anchor per stance: a blend of heel and ball (towards whichever is lower) held at
                # its mean position -- no creep from pivot hand-overs, periodic on a tiled loop
                wb = np.clip((t["heel"][s0:e0, 1] - t["ball"][s0:e0, 1] - 0.002) / 0.012, 0, 1)
                wb = smoothstep(smooth(wb, 1.5))[:, None]
                hs, bs = t["heel"][s0:e0], t["ball"][s0:e0]
                o[s0:e0] = (1 - wb) * (hs.mean(0) - hs) + wb * (bs.mean(0) - bs)
                o[s0:e0, 1] = 0.0
                slide.append(float(np.abs(o[s0:e0, [0, 2]]).max()))
                continue
            A = None
            cur = None
            for f in range(s0, e0):
                pv = c["pivot"][f]
                p = pts[f, pv]
                if cur is None:
                    A = p.copy()
                    A[1] = 0.0
                elif pv != cur:
                    A = p + o[f - 1]
                    A[1] = 0.0
                cur = pv
                o[f] = A - p
            slide.append(float(np.linalg.norm(o[e0 - 1, [0, 2]])))
        # swing: blend the offset between stances (xz: from the last stance's end to 0; y: to 0)
        idx = np.arange(F)
        known = ~np.isnan(o[:, 0])
        if known.any():
            for k in range(3):
                o[:, k] = np.interp(idx, idx[known], o[known, k])
            # smooth the swing interpolation (C1 at stance boundaries) with smoothstep in each gap
            for s0, e0 in _runs(~known):
                if s0 == 0 or e0 == F:
                    continue
                a, b = o[s0 - 1], o[e0]
                w = smoothstep((np.arange(s0, e0) - (s0 - 1)) / (e0 - s0 + 1))[:, None]
                o[s0:e0] = a + (b - a) * w
        else:
            o[:] = 0
        # vertical: while the sole is on the ground its lowest point rests on y = 0; in the air the
        # correction is interpolated between ground phases and eased in / out
        g = c["ground"]
        oy = np.where(g, -t["low"], np.nan)
        if g.any():
            oy = np.interp(idx, idx[g], oy[g])
            for s0, e0 in _runs(~g):
                if s0 == 0 or e0 == F:
                    continue
                w = smoothstep((np.arange(s0, e0) - (s0 - 1)) / (e0 - s0 + 1))
                oy[s0:e0] = oy[s0 - 1] + (oy[e0] - oy[s0 - 1]) * w
            wy = np.clip(smooth(g.astype(float), ramp / 2.0), 0, 1)
            oy = np.where(g, oy, oy * wy)
        else:
            oy = np.zeros(F)
        o[:, 1] = smooth(oy, 1.5)               # no vertical pop when the pivot moves heel -> ball
        targets[s] = ankle + o
        stats[s] = dict(stances=len(runs), stance_frac=round(float(c["stance"].mean()), 2),
                        slide_cm_max=round(100 * max(slide), 1) if slide else 0.0,
                        slide_cm_mean=round(100 * float(np.mean(slide)), 1) if slide else 0.0)
    # let the pelvis (height, roll) absorb the pins so that the knees keep the source's bend
    wst = {s: np.clip(smooth(ct[s]["ground"].astype(float), ramp / 2.0), 0, 1) for s in "LR"}
    pel = pelvis_for_targets(body, m, targets, wst)
    m.info["pelvis_fit"] = pel
    Rw, root, drop = leg_ik(body, m.Rw, m.root, targets)
    # keep every shoe point above the floor: lift the ankle target where needed, re-solve
    for _ in range(2):
        tr2 = sole_tracks(body, m, Rw, root)
        lift = {s: np.maximum(-tr2[s]["low"], 0) for s in "LR"}
        if max(v.max() for v in lift.values()) < 5e-4:
            break
        for s in "LR":
            l = np.maximum(smooth(lift[s] + clearance * (lift[s] > 0), 1.0), lift[s])
            targets[s] = targets[s] + np.c_[np.zeros(F), l, np.zeros(F)]
        Rw, root, drop = leg_ik(body, m.Rw, m.root, targets)
    m.Rw, m.root = Rw, root
    m.contacts = ct
    if report:
        tr3 = sole_tracks(body, m)
        ct3 = ct
        res = {}
        for s in "LR":
            st = ct3[s]["stance"]
            piv = np.where(ct3[s]["pivot"][:, None] == 0, tr3[s]["heel"], tr3[s]["ball"])
            v = np.linalg.norm(np.diff(piv[:, [0, 2]], axis=0), axis=1) * fps
            same = st[1:] & st[:-1] & (ct3[s]["pivot"][1:] == ct3[s]["pivot"][:-1])
            core = st.copy()                                  # stance without its first/last 2 frames
            for s0, e0 in _runs(st):
                core[s0:s0 + 2] = False
                core[max(s0, e0 - 2):e0] = False
            res[s] = dict(pivot_speed_in_stance_cm_s_max=round(100 * float(v[same].max()), 2) if same.any() else 0.0,
                          sole_gap_in_stance_mm_max=round(1000 * float(np.abs(tr3[s]["low"][core]).max()), 1) if core.any() else 0.0,
                          lowest_point_mm=round(1000 * float(tr3[s]["low"].min()), 1))
        m.info["feet"] = dict(floor_shift_mm=round(1000 * floor, 1), before=stats, after=res,
                              pelvis_drop_mm_max=round(1000 * float(drop.max()), 1))
    return m


# ---------------------------------------------------------------------------- loops
LOOP_JOINTS = ("foot.L", "foot.R", "lowerleg01.L", "lowerleg01.R", "wrist.L", "wrist.R", "lowerarm01.L",
               "lowerarm01.R", "head", "spine01")


def heading(body, Rw):
    f = body.facing(Rw)
    return np.arctan2(f[:, 0], f[:, 2])


def pose_features(body, m: Motion, joints=LOOP_JOINTS):
    """Heading-invariant pose + velocity features (F, D) for loop matching."""
    H = body.fk(m.Rw, m.root)
    J = [body.ix[n] for n in joints]
    psi = heading(body, m.Rw)
    R = rot_y(-psi)                                        # (F,3,3) undo the heading
    rel = np.einsum("fij,fnj->fni", R, H[:, J] - m.root[:, None])
    rel[..., 1] += m.root[:, None, 1]
    vel = np.gradient(rel, axis=0) * m.fps
    rv = np.einsum("fij,fj->fi", R, np.gradient(m.root, axis=0) * m.fps)
    return np.concatenate([rel.reshape(m.F, -1), 0.15 * vel.reshape(m.F, -1), 0.3 * rv], 1)


def find_loop(body, m: Motion, n_range, lo=0, hi=None, win=2):
    """Best (a, N): frames a..a+N such that frame a+N matches frame a (poses and velocities)."""
    X = pose_features(body, m)
    psi = np.unwrap(heading(body, m.Rw))
    hi = m.F if hi is None else hi
    best = (np.inf, None, None)
    for N in range(n_range[0], n_range[1] + 1):
        for a in range(max(lo, win), hi - N - win):
            d = np.sum((X[a - win:a + win + 1] - X[a + N - win:a + N + win + 1]) ** 2)
            d += 4.0 * (psi[a + N] - psi[a]) ** 2
            if d < best[0]:
                best = (d, a, N)
    return best[1], best[2], float(best[0])


def slerp_mats(A, B, w):
    """Per-frame rotation interpolation (…,3,3) with weights w (…)."""
    D = np.einsum("...ji,...jk->...ik", A, B)
    return A @ rot_exp(rot_log(D) * w[..., None])


def make_loop(body, m: Motion, a, N, W, name, travel=True):
    """Loop of N frames starting at frame a (needs a >= W): the last W frames cross-fade (local
    rotations, smoothstep) into the W frames that precede frame a, shifted by the loop's displacement,
    so that playing frame N-1 -> frame 0 is seamless.  With travel=True the net displacement D is
    kept (for walks) and turned onto +Z; otherwise the root's net drift is removed."""
    assert a >= W and a + N <= m.F
    L = body.to_local(m.Rw)
    D = m.root[a + N] - m.root[a]
    D[1] = 0
    dpsi = float(np.unwrap(heading(body, m.Rw))[a + N] - np.unwrap(heading(body, m.Rw))[a])
    Lo = L[a:a + N].copy()
    ro = m.root[a:a + N].copy()
    i = np.arange(N)
    if not travel:          # remove the drift linearly (the seam then only needs the pose blend)
        ro[:, [0, 2]] -= (i[:, None] / N) * D[[0, 2]]
        D = np.zeros(3)
    k = i >= N - W
    w = smoothstep((i[k] - (N - W) + 1) / (W + 1))
    src = i[k] + a - N                                   # the frames just before a
    Lb = L[src]                                          # (their heading: the cycle's heading drift
    rb = m.root[src] + D                                 #  is blended out over the seam)
    Lo[k] = slerp_mats(Lo[k], Lb, np.repeat(w[:, None], body.B, 1))
    ro[k] = ro[k] * (1 - w[:, None]) + rb * w[:, None]
    out = Motion(name, body.to_world(Lo), ro, m.fps, loop=True, info=dict(m.info))
    out.info.update(loop_src_frames=[int(a), int(a + N)], loop_blend_frames=int(W),
                    loop_heading_change_deg=round(float(np.degrees(dpsi)), 2))
    if travel:
        # the per-cycle heading change is blended out over the seam; turn the loop so D points to +Z
        turn(out, -heading_angle(D), pivot=out.root[0])
        out.info["loop_displacement_m"] = round(float(np.linalg.norm(D[[0, 2]])), 3)
    out.D = np.array([0.0, 0.0, np.linalg.norm(D[[0, 2]])]) if travel else np.zeros(3)
    return out


def tile(m: Motion, n=3):
    """n copies of a loop, each shifted by the loop displacement."""
    Rw = np.concatenate([m.Rw] * n)
    root = np.concatenate([m.root + k * m.D for k in range(n)])
    return Motion(m.name, Rw, root, m.fps, m.loop, dict(m.info), None, m.D.copy())


def plant_loop(body, m: Motion, **kw):
    """Foot planting on a loop: solved on three tiled copies, the middle copy is kept (cyclic contacts)."""
    t3 = tile(m, 3)
    plant_feet(body, t3, **kw)
    N = m.F
    m.Rw = t3.Rw[N:2 * N]
    m.root = t3.root[N:2 * N] - m.D
    m.info.update(t3.info)
    m.contacts = {s: {k: v[N:2 * N] for k, v in c.items() if k != "speed"} for s, c in t3.contacts.items()}
    return m


def close_loop(m: Motion):
    """Append frame 0 (shifted by the displacement) so a looping player wraps without a hitch."""
    m.Rw = np.concatenate([m.Rw, m.Rw[:1]])
    m.root = np.concatenate([m.root, m.root[:1] + m.D])
    if m.morph is not None:
        m.morph = np.concatenate([m.morph, m.morph[:1]])
    return m


def in_place(m: Motion):
    """Remove the constant forward progression of a travelling loop (root oscillation stays)."""
    out = m.copy()
    out.D = np.zeros(3)
    N = m.F - 1 if m.loop else m.F
    i = np.arange(out.F)
    out.root = out.root - (i[:, None] / N) * m.D
    out.info["speed_mps"] = round(float(np.linalg.norm(m.D) / (N / m.fps)), 3)
    return out


# ---------------------------------------------------------------------------- layers
def add_rotation_layer(body, m: Motion, layer):
    """layer: {bone: (axis_world (F,3) or (3,), angle (F,))} applied as local rotations about world axes."""
    L = body.to_local(m.Rw)
    for n, (ax, ang) in layer.items():
        b = body.ix[n]
        ax = np.broadcast_to(np.asarray(ax, float), (m.F, 3))
        axl = np.einsum("fji,fj->fi", m.Rw[:, b], ax)
        L[:, b] = L[:, b] @ axis_angle(axl, ang)
    m.Rw = body.to_world(L)
    return m


def breathe(body, m: Motion, period_s=4.2, chest_deg=0.9, shoulder_deg=1.1):
    """Slow breathing on a loop: chest opens (spine pitch back), shoulders rise a little, the neck
    compensates so the gaze stays put.  The number of breaths is rounded so the loop stays seamless."""
    N = m.F - 1 if m.loop else m.F
    T = N / m.fps
    nb = max(1, int(round(T / period_s)))
    t = np.arange(m.F) / m.fps
    b = 0.5 - 0.5 * np.cos(2 * np.pi * nb * t / T)      # 0 exhaled .. 1 inhaled
    b = b ** 1.3                                          # quicker inhale, longer exhale tail
    Rroot = m.Rw[:, body.ix["root"]] @ body.Tst[body.ix["root"]].T
    left = np.einsum("fij,j->fi", Rroot, [1.0, 0, 0])
    fwd = np.einsum("fij,j->fi", Rroot, [0, 0, 1.0])
    c = np.radians(chest_deg) * b
    layer = {"spine03": (left, -0.35 * c), "spine02": (left, -0.4 * c), "spine01": (left, -0.25 * c),
             "neck01": (left, 0.6 * c), "neck02": (left, 0.4 * c),
             "clavicle.L": (fwd, -np.radians(shoulder_deg) * b), "clavicle.R": (fwd, np.radians(shoulder_deg) * b)}
    add_rotation_layer(body, m, layer)
    m.info["breathing"] = dict(breaths=nb, period_s=round(T / nb, 2), chest_deg=chest_deg, shoulder_deg=shoulder_deg)
    return m


def corrective_weights(body, m: Motion, full_deg=25.0, zero_deg=80.0):
    """stand_corrective_L/R morph weights: 1 while the upper arm hangs roughly as in the stand pose
    (relative to the chest), fading to 0 as it leaves (the corrective was solved for the stand pose)."""
    ch = body.ix["spine01"]
    w = []
    for s in "LR":
        ua = body.ix[f"upperarm01.{s}"]
        d_st = body.Tst[ch].T @ body.Tst[ua][:, 1]                      # stand arm direction, chest frame
        d = np.einsum("fji,fj->fi", m.Rw[:, ch], m.Rw[:, ua][:, :, 1])
        ang = np.degrees(np.arccos(np.clip(d @ d_st, -1, 1)))
        w.append(1 - smoothstep((ang - full_deg) / (zero_deg - full_deg)))
    m.morph = np.stack(w, 1)
    m.info["corrective_weight_min"] = [round(float(x), 2) for x in m.morph.min(0)]
    return m


# ============================================================================ export
STATIC_PREFIX = ("jaw", "oris", "tongue", "levator", "eye", "oculi", "special", "temporalis", "risorius",
                 "finger", "metacarpal", "orbicularis", "mandible", "cheek", "nose", "lip")


def motion_qa(body, m, L=None):
    """Numbers that catch the classic retarget failures: per-frame rotation jumps of any joint (sign flips,
    snapping knees), face bones drifting from the stand pose, knees bending backwards or sideways."""
    L = body.to_local(m.Rw) if L is None else L
    Lst = body.to_local(body.Tst[None])[0]
    d = rot_angle(np.einsum("fbji,fbjk->fbik", L[:-1], L[1:]))            # (F-1, B) rad
    jump = np.degrees(d.max(0))
    worst = np.argsort(-jump)[:5]
    face = [b for b, n in enumerate(body.names) if n.startswith(STATIC_PREFIX) and not n.startswith(("finger", "metacarpal"))]
    dev = np.degrees(rot_angle(np.einsum("bji,fbjk->fbik", Lst[face], L[:, face]))).max() if face else 0.0
    kf = signed_knee_flex(body, m.Rw, m.root)
    H = body.fk(m.Rw, m.root)
    shin = {}
    for s, g in body.legs.items():
        v = _unit(H[:, g["foot"]] - H[:, g["knee"]])
        shin[s] = float(np.degrees(np.arccos(np.clip(np.sum(v[1:] * v[:-1], 1), -1, 1))).max())
    qa = {"max_joint_step_deg": round(float(jump.max()), 2),
          "worst_joints": {body.names[b]: round(float(jump[b]), 1) for b in worst},
          "face_bone_dev_from_stand_deg": round(float(dev), 3),
          "knee_flex_min_deg": {s: round(float(kf[s][0].min()), 1) for s in "LR"},
          "knee_side_dev_max_deg": {s: round(float(kf[s][1].max()), 1) for s in "LR"},
          "shin_step_max_deg": {s: round(v, 1) for s, v in shin.items()}}
    qa["ok"] = bool(qa["face_bone_dev_from_stand_deg"] < 0.5 and min(qa["knee_flex_min_deg"].values()) >= 0 and
                    max(shin.values()) <= 18.0)
    return qa


def export(body: Body, motions, out_path, extras=None, log=print):
    """Copy of the model GLB with the clips appended (the existing "stand" / "rest_apose" stay)."""
    g = GLBEdit(body.glb)
    names_before = [a["name"] for a in g.j.get("animations", [])]
    g.j["animations"] = [a for a in g.j.get("animations", []) if a["name"] not in {m.name for m in motions}]
    morph_nodes = [k for n, k in body.mesh_nodes.items()
                   if g.j["meshes"][g.j["nodes"][k]["mesh"]].get("extras", {}).get("targetNames")]
    root_b = int(np.nonzero(body.parent < 0)[0][0])
    summary = {}
    Lst = body.to_local(body.Tst[None])[0]
    static = [b for b, n in enumerate(body.names) if n.startswith(STATIC_PREFIX)]
    for m in motions:
        L = body.to_local(m.Rw)
        # bones mocap does not drive (face, eyes, jaw, tongue, fingers) are written as their stand pose
        L[:, static] = Lst[static][None]
        q = quat_continuous(mat_to_quat(L))                 # (F,B,4)
        m.info["qa"] = motion_qa(body, m, L)
        times = np.arange(m.F) / m.fps
        t_all = g.acc(times, "SCALAR", minmax=True)
        t_two = g.acc(np.array([0.0, times[-1]]), "SCALAR", minmax=True)
        samplers, channels = [], []

        def add(node, path, t_acc, data, atype):
            samplers.append({"input": t_acc, "output": g.acc(data, atype), "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1, "target": {"node": node, "path": path}})

        add(body.joint_nodes[root_b], "translation", t_all, m.root, "VEC3")
        const = 0
        for b in range(body.B):
            qb = q[:, b]
            if np.abs(qb - qb[:1]).max() < 1e-6:
                add(body.joint_nodes[b], "rotation", t_two, np.repeat(qb[:1], 2, 0), "VEC4")
                const += 1
            else:
                add(body.joint_nodes[b], "rotation", t_all, qb, "VEC4")
        if m.morph is not None:
            for k in morph_nodes:
                add(k, "weights", t_all, m.morph.reshape(-1), "SCALAR")
        g.j["animations"].append({"name": m.name, "samplers": samplers, "channels": channels})
        summary[m.name] = dict(frames=int(m.F), fps=m.fps, duration_s=round(times[-1], 3), loop=bool(m.loop),
                               constant_tracks=const, **{k: v for k, v in m.info.items()})
    ex = g.j["scenes"][0].setdefault("extras", {})
    ex["clips"] = {k: {kk: summary[k][kk] for kk in ("duration_s", "loop") if kk in summary[k]} |
                   ({"speed_mps": summary[k]["speed_mps"]} if "speed_mps" in summary[k] else {})
                   for k in summary}
    ex["mocap_credit"] = ("CMU Graphics Lab Motion Capture Database, mocap.cs.cmu.edu (created with funding "
                          "from NSF EIA-0196217)")
    if extras:
        ex.update(extras)
    size = g.save(out_path)
    log(f"wrote {out_path} ({size / 1e6:.1f} MB): clips {[a['name'] for a in g.j['animations']]}"
        f" (had {names_before})")
    return summary


# ============================================================================ the clips
def clip_walk(body, log=print):
    """Relaxed walk (CMU 142_13, 'Relaxed', first straight pass): two gait cycles cut where the end
    matches the start, cross-faded, feet planted cyclically.  Returns (walk in place, walk_forward)."""
    m = retarget(body, CMU / "142_13.bvh", 1.5, 9.0, name="walk", ref=(0.2, 1.2), ref_w=dict.fromkeys(REF_LOWER, 1.0))
    align_heading(body, m, "travel")
    head_level(body, m, gaze_deg=-4.0, neck_deg=-4.0, roll_damp=0.5)
    scale_swing(body, m, {"upperarm01.L": 1.35, "upperarm01.R": 1.35, "lowerarm01.L": 1.15, "lowerarm01.R": 1.15})
    widen_stance(body, m, 1.6)
    spread_twist(body, m)
    a, N, err = find_loop(body, m, (66, 78), lo=40, hi=m.F - 4)
    log(f"  walk loop: frames {a}..{a + N} ({N / m.fps:.2f} s), match error {err:.3f}")
    lp = make_loop(body, m, a, N, W=10, name="walk_forward", travel=True)
    plant_loop(body, lp)                       # (level: the stance feet land ~8 deg toe-down otherwise)
    lp.root[:, [0, 2]] -= lp.root[0, [0, 2]]
    corrective_weights(body, lp)
    walk = in_place(close_loop(lp.copy()))
    walk.name = "walk"
    fwd = tile(lp, 2)
    fwd.loop = False
    fwd.morph = np.concatenate([lp.morph] * 2)
    close_loop(fwd)                                   # end on the next cycle's first pose
    fwd.root[-1] = lp.root[0] + 2 * lp.D
    fwd.loop = False
    fwd.name = "walk_forward"
    fwd.info["speed_mps"] = walk.info["speed_mps"]
    return [walk, fwd]


def clip_idle(body, log=print):
    """Quiet standing (CMU 77_02, 'standing'): small weight shifts, the head looks around.  Cut into
    a loop whose end matches its start, cross-faded, root drift removed, feet pinned, breathing added."""
    m = retarget(body, CMU / "77_02.bvh", 0.0, 7.8, name="idle", ref=(0.0, 7.8), ref_w=dict.fromkeys(REF_LOWER, 1.0))
    align_heading(body, m, "facing")
    head_level(body, m, gaze_deg=-2.0, neck_deg=-4.0)
    calm_head(body, m)
    head_level(body, m, gaze_deg=-2.0, neck_deg=-4.0)
    spread_twist(body, m)
    W = 16
    a, N, err = find_loop(body, m, (132, m.F - W - 4), lo=W, hi=m.F - 2, win=3)
    log(f"  idle loop: frames {a}..{a + N} ({N / m.fps:.2f} s), match error {err:.3f}")
    lp = make_loop(body, m, a, N, W=W, name="idle", travel=False)
    align_heading(body, lp, "facing")
    lp.root[:, [0, 2]] -= lp.root[:, [0, 2]].mean(0)
    plant_loop(body, lp, level=False, anchor="fixed", lock_yaw=0.8)
    close_loop(lp)
    breathe(body, lp)
    corrective_weights(body, lp)
    return [lp]


def clip_turn_look_back(body, log=print):
    """Standing, turns the torso and head to look back over the left shoulder (head ~115 deg from
    the front), then over the right shoulder (~90 deg), and comes back to the front (CMU 76_10,
    'turning', 0-5.4 s).  Feet planted; the left foot steps once to pivot, as in the capture."""
    m = retarget(body, CMU / "76_10.bvh", 0.0, 5.4, name="turn_look_back", ref=(0.0, 0.4),
                 ref_w=dict.fromkeys(REF_LOWER, 1.0))
    align_heading(body, m, "facing", frames=slice(0, 12))
    head_level(body, m, gaze_deg=-2.0, neck_deg=-4.0)
    spread_twist(body, m)
    m.root[:, [0, 2]] -= m.root[0, [0, 2]]
    # the turn is made of small shuffle steps (feet lifted 2-4 cm, moving at 0.2-0.5 m/s): a tight
    # speed test keeps them as steps in the air instead of pinning (or sliding) them
    plant_feet(body, m, h_thr=0.045, v_thr=0.15, level=False)
    corrective_weights(body, m)
    return [m]


CLIPS = {"walk": clip_walk, "idle": clip_idle, "turn_look_back": clip_turn_look_back}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glb", type=Path, default=OUT / "subject_full.glb")
    ap.add_argument("--out", type=Path, default=OUT / "subject_animated.glb")
    ap.add_argument("--clips", default=",".join(CLIPS))
    ap.add_argument("--report", action="store_true", help="print the per-clip QA numbers")
    a = ap.parse_args()
    body = Body(a.glb)
    motions = []
    for k in a.clips.split(","):
        print(f"clip {k}")
        motions += CLIPS[k](body)
    summary = export(body, motions, a.out)
    side = a.out.with_name(a.out.stem + "_anim.json")
    side.write_text(json.dumps({"glb": str(a.out), "source_glb": str(a.glb), "clips": summary,
                                "credit": "CMU Graphics Lab Motion Capture Database, mocap.cs.cmu.edu; "
                                          "created with funding from NSF EIA-0196217"}, indent=1, default=float))
    print(f"wrote {side}")
    if a.report:
        for k, v in summary.items():
            print(k, json.dumps(v, default=float))


if __name__ == "__main__":
    main()
