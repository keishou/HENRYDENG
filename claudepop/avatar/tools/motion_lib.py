#!/usr/bin/env python3
"""Motion library for the protagonist: CMU mocap retargeted onto the skeleton of subject.glb.

    python motion_lib.py fetch                 # download the BVH sources into odyssey/.cache/motion/cmu/
    python motion_lib.py build [--only a,b]    # retarget -> claudepop/out/avatar/motion/<clip>.bin + MANIFEST.json
    python motion_lib.py list                  # print the catalogue

Sources: CMU Graphics Lab Motion Capture Database (mocap.cs.cmu.edu), 2010 "MotionBuilder-friendly" BVH conversion
by Bruce Hahne (cgspeed), mirrored at github.com/una-dinosauria/cmu-mocap (raw URLs below). Licence: free for any
use (CMU + B. Hahne, READMEFIRST.txt). Requested acknowledgement: "The data used in this project was obtained from
mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217."

Retargeting (the method of odyssey/body/retarget_mh.py, copied and extended here; odyssey is not modified):
  * world-space rotation deltas relative to the cgspeed T-pose frame, onto the calibration pose of the *subject's own*
    rest skeleton read from subject.glb (not the MakeHuman default rig), so the rotations drop straight onto the GLB.
    The cgspeed T-pose bends the neck and head (Neck.X -16, Neck1.X +21, Head.X +11 deg: head pitched ~16 deg down)
    while the MakeHuman rest head is upright, so neck/head deltas are taken from the zero pose instead (else every
    clip carries a permanent chin-up of ~16 deg);
  * unmapped bones (fingers, face, breast, tongue) are left at their rest local rotation (rigid w.r.t. the parent);
  * twist distribution (no candy-wrapper): forearm pronation is spread over lowerarm01/02 (1/3, 2/3), shin twist over
    lowerleg01/02, and upperarm01 / upperleg01 keep only half of the humerus / femur twist (upperarm02 / upperleg02
    carry all of it), so the shoulder and hip skin never takes the full twist;
  * bend distribution: the CMU spine has 3 segments and the neck 2, the MakeHuman rig 5 + 3; each CMU segment that
    drives two MakeHuman bones is split half/half instead of kinking at the first one;
  * heading normalisation: every clip starts at x = z = 0 facing +Z ('travel' clips: start->end displacement along
    +Z; 'facing_end': facing +Z at the end, for clips that end standing);
  * foot lock (clips flagged footlock): heel and ball contacts of each shoe are detected (low + slow, per-clip
    thresholds for runs), each contact span is held at its median ground position with two-bone leg IK (thigh +
    shin; the foot keeps its world orientation), eased in/out over 4 frames; 3 passes, contacts re-detected each pass;
  * floor contact: the skinned subject mesh (shoes, trousers, skin, top, hair; subsampled) is evaluated per frame and
    the root is lowered/raised so the lowest point touches y = 0 in every frame (lightly smoothed; runs use one
    median shift instead, since they leave the ground);
  * loops: a cycle [a, b) is chosen where pose and velocity match best, the seam residual is removed linearly over
    the cycle, foot lock and floor contact run on 3 chained copies (so spans cross the seam) and the middle copy is
    kept; the per-cycle root displacement is stored so a player can chain cycles deterministically;
  * checks written to the manifest: lowest point per frame (floor float / penetration), foot skate per contact span
    (max drift from the span's median, cm), source twist and residual per-segment twist (deg).

Output (gitignored, under claudepop/out/avatar/motion/):
  <clip>.bin   float32, frame-major: [root_pos xyz, then (x,y,z,w) local quaternion per animated bone] per frame
  MANIFEST.json  fps, skeleton bone names (three.js names, dots removed), per clip: animated bone list, frames,
                 seconds, loop info, root-motion distance, source clip + segment, what it shows, checks.
Bones not listed for a clip stay at the GLB rest rotation (the retarget leaves them rigid w.r.t. their parent).
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[2]
ODY = REPO / "odyssey"
CMU = ODY / ".cache" / "motion" / "cmu"
OUT = REPO / "claudepop" / "out" / "avatar"
MOTION = OUT / "motion"
GLB_PATH = OUT / "subject.glb"
FPS = 30.0

sys.path.insert(0, str(ODY / "body"))
from bvh import load_bvh  # noqa: E402  (odyssey/body/bvh.py, used read-only)

CMU_UNIT_M = 0.0254 / 0.45
C_B2Y = np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]])

# ------------------------------------------------------------------------------------------------ catalogue
# name, cmu id, [start, end] s (source time after the T-pose frame), category, what it shows, options
#   loop: {"search": [s0, s1], "min": s, "max": s}  -> seamless cycle searched inside [s0, s1] (source seconds)
#   align: "facing" (default) | "travel"  (rotate so the start->end displacement points along +Z)
#   footlock: True for clips whose feet should be pinned while planted
CLIPS = [
    # ---- from odyssey/body/curate_motion.py (curated contemplative set)
    dict(name="walk_slow", cmu="132_45", seg=[1.5, 11.5], cat="walk", align="travel", footlock=True,
         shows="very slow, even, straight walk (~0.45 m/s), head level; the cleanest walk: toward / away from camera"),
    dict(name="walk_slow_loop", cmu="132_45", seg=[1.5, 11.5], cat="walk", align="travel", footlock=True,
         loop=dict(search=[2.0, 11.0], min=2.0, max=5.5),
         shows="seamless cycle of walk_slow; chain cycles for a walk of any length toward / away from camera"),
    dict(name="walk_sad_headdown", cmu="142_15", seg=[2.1, 11.8], cat="walk", align="travel", footlock=True,
         shows="'sad' stylised walk, head lowered, shoulders dropped; one straight pass"),
    dict(name="walk_relaxed", cmu="142_13", seg=[1.5, 9.0], cat="walk", align="travel", footlock=True,
         shows="relaxed walk, neutral head, easy arm swing; one straight pass"),
    dict(name="walk_runway_loop", cmu="142_04", seg=[2.0, 7.5], cat="walk", align="travel", footlock=True,
         loop=dict(search=[2.8, 7.2], min=0.9, max=3.2),
         shows="seamless cycle of a confident 'cool' walk (~1 m/s), arms swinging: the runway walk toward camera"),
    dict(name="walk_attitude", cmu="104_44", seg=[0.0, 9.0], cat="walk", align="travel", footlock=True,
         shows="'attitude' walk, one straight 4.3 m pass at ~0.5 m/s, chin up"),
    dict(name="walk_stop_lookright", cmu="104_35", seg=[0.0, 8.9], cat="walk", align="travel", footlock=True,
         shows="stands, slow walk ~4 m, stops, head turns ~45 deg to the right"),
    dict(name="walk_stop_lookup", cmu="82_14", seg=[0.0, 7.5], cat="walk", align="travel", footlock=True,
         shows="walks in, decelerates, stops and tilts the head up (~25-30 deg) from ~4.5 s: 'stop and look up'"),
    dict(name="walk_depressed", cmu="91_14", seg=[2.6, 9.7], cat="walk", align="facing", footlock=True,
         shows="'depressed' walk, head low; back-and-forth with an in-place 180 turn"),
    dict(name="idle_stand", cmu="77_02", seg=[0.0, 7.8], cat="idle", footlock=True,
         shows="quiet standing, small weight shifts and head moves"),
    dict(name="idle_wait", cmu="137_28", seg=[0.0, 31.0], cat="idle", footlock=True,
         shows="'normal wait': long idle with weight shifts, a few steps and glances around"),
    dict(name="idle_lookaround_lookback", cmu="40_10", seg=[0.0, 51.8], cat="idle", footlock=True,
         shows="52 s waiting at a bus stop: shifts, steps, turns body and head to look around and behind"),
    dict(name="look_back_over_shoulder", cmu="76_10", seg=[0.0, 11.4], cat="turn", footlock=True,
         shows="stands and twists torso + head to look back over each shoulder (hips +-70, head +-50 deg)"),
    dict(name="sit_floor", cmu="82_05", seg=[0.0, 18.7], cat="floor",
         shows="seated on the floor the whole clip, knees up, hands on knees / behind, looks around"),
    dict(name="kneel_one_knee", cmu="23_03", seg=[0.0, 6.8], cat="floor", footlock=True,
         shows="steps in, goes down on one knee (low 1.5-4.1 s) reaching one hand out and forward, rises again"),
    dict(name="sit_stool_head_bowed", cmu="22_03", seg=[0.0, 6.0], cat="prop", footlock=True,
         shows="seated on a stool (needs a ~0.6 m seat prop), elbows on knees, head bowed low"),
    dict(name="turn_in_place_ccw", cmu="69_16", seg=[0.0, 9.4], cat="turn", footlock=True,
         shows="slow 360 deg turn in place to the left in ~4 x 90 deg step-turns"),
    dict(name="turn_in_place_cw", cmu="69_18", seg=[0.0, 8.8], cat="turn", footlock=True,
         shows="slow 360 deg turn in place to the right"),
    # ---- added for the stream-of-consciousness film
    dict(name="stand_breathe_loop", cmu="111_28", seg=[0.0, 4.0], cat="idle", footlock=True,
         loop=dict(search=[0.3, 4.0], min=2.4, max=3.7),
         shows="near-motionless standing, arms down: base for procedural breathing (layer on top in avatar.js)"),
    dict(name="stand_head_roll", cmu="113_21", seg=[0.0, 11.4], cat="idle", footlock=True,
         shows="standing still while the head rolls slowly (tilts back, around): neck stretch / looking up and around"),
    dict(name="lie_down_and_rise", cmu="113_08", seg=[0.0, 15.3], cat="floor",
         shows="standing -> lowers to the floor -> lies on the back (~4-10 s) -> gets up again"),
    dict(name="lie_down", cmu="113_08", seg=[0.0, 9.5], cat="floor",
         shows="standing -> lowers to the floor and lies on the back, still at the end"),
    dict(name="rise_from_lying", cmu="113_08", seg=[9.0, 15.3], cat="floor", align="facing_end",
         shows="lying on the back -> rolls to the side, gets up to standing"),
    dict(name="fall_backwards", cmu="90_18", seg=[0.0, 3.2], cat="fall",
         shows="stands, legs go from under him, falls straight back and lands flat on the back (~1.1 s), lies still"),
    dict(name="reach_forward", cmu="15_06", seg=[1.5, 12.5], cat="gesture", footlock=True,
         shows="standing, leans and reaches one hand forward (repeated), returns to neutral"),
    dict(name="face_in_hands_standing", cmu="79_72", seg=[0.0, 7.9], cat="gesture", footlock=True,
         shows="standing, bends forward and buries the face in both hands (crying, 1.8-6.2 s), straightens"),
    dict(name="grief_standing", cmu="80_45", seg=[0.0, 13.3], cat="gesture", footlock=True,
         shows="standing, a hand to the face and head bowed (crying), long and quiet"),
    dict(name="start_run", cmu="127_03", seg=[0.0, 2.75], cat="run", align="travel", footlock=True, floor="median",
         contact=dict(h_thr=0.05, v_thr=1.0),
         shows="standing still, then breaks into a run, accelerating to ~4 m/s by the end (~4.4 m)"),
    dict(name="run_loop", cmu="16_36", seg=[0.0, 1.55], cat="run", align="travel", footlock=True, floor="median",
         contact=dict(h_thr=0.05, v_thr=1.0),
         loop=dict(search=[0.0, 1.55], min=0.55, max=1.5),
         shows="seamless jog cycle (~2.6 m/s); chain cycles for a run of any length"),
    dict(name="tai_chi_sway", cmu="12_04", seg=[20.0, 80.0], cat="dance",
         shows="60 s of slow tai chi: weight shifts, arm arcs; understated, sits under half-time 66 BPM"),
    dict(name="dance_expressive_arms", cmu="05_02", seg=[0.0, 9.4], cat="dance",
         shows="modern dance: expressive arm sweeps, a pirouette"),
    dict(name="dance_twist", cmu="141_12", seg=[0.0, 4.7], cat="dance",
         shows="casual 'twist' dance on the spot; can be warped onto the 132 BPM grid"),
    dict(name="arms_open_stretch", cmu="143_30", seg=[0.0, 3.1], cat="gesture", footlock=True,
         shows="stretch: both arms open wide and up (peak ~1.4-2.0 s), relax"),
    dict(name="arms_out_balance", cmu="49_18", seg=[2.0, 9.2], cat="gesture",
         footlock=True,
         shows="arms held out to the sides, balancing on one leg (dancer)"),
    dict(name="sit_down_get_up", cmu="143_18", seg=[0.0, 6.3], cat="prop",
         footlock=True,
         shows="sits down onto a low seat and gets up (needs a ~0.45 m seat prop)"),
]


# ------------------------------------------------------------------------------------------------ io
def raw_url(cid):
    s = int(cid.split("_")[0])
    return f"https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/{s:03d}/{cid}.bvh"


def fetch(ids=None):
    CMU.mkdir(parents=True, exist_ok=True)
    ids = sorted({c["cmu"] for c in CLIPS}) if ids is None else ids
    for cid in ids:
        p = CMU / f"{cid}.bvh"
        if p.exists() and p.stat().st_size > 1000:
            continue
        print("fetch", raw_url(cid))
        urllib.request.urlretrieve(raw_url(cid), p)
        assert p.read_bytes()[:9] == b"HIERARCHY", p
    idx = CMU / "cmu-mocap-index-text.txt"
    if not idx.exists():
        urllib.request.urlretrieve("https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/cmu-mocap-index-text.txt", idx)


def cmu_titles():
    T = {}
    p = CMU / "cmu-mocap-index-text.txt"
    if p.exists():
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and "_" in parts[0]:
                T[parts[0].strip()] = parts[1].strip()
    return T


def read_glb(path):
    b = Path(path).read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    g = json.loads(b[20:20 + n])
    o = 20 + n
    bl = struct.unpack("<I", b[o:o + 4])[0]
    return g, b[o + 8:o + 8 + bl]


def accessor(g, bin_, i):
    a = g["accessors"][i]
    bv = g["bufferViews"][a["bufferView"]]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a["componentType"]]
    nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
    start = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride")
    isz = np.dtype(dt).itemsize
    if stride and stride != nc * isz:
        raw = np.frombuffer(bin_, np.uint8, count=stride * a["count"], offset=start).reshape(a["count"], stride)
        arr = raw[:, :nc * isz].copy().view(dt).reshape(a["count"], nc)
    else:
        arr = np.frombuffer(bin_, dt, count=a["count"] * nc, offset=start).reshape(a["count"], nc)
    if a.get("normalized"):
        arr = arr.astype(np.float32) / np.iinfo(dt).max
    return arr


def q2m(q):
    q = np.asarray(q, float)
    x, y, z, w = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.stack([
        np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], -1),
        np.stack([2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], -1),
        np.stack([2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)], -1)], -2)


def m2q(M):
    """(...,3,3) -> (...,4) xyzw, robust (Shepperd), vectorised."""
    M = np.asarray(M, float)
    sh = M.shape[:-2]
    M = M.reshape(-1, 3, 3)
    m00, m11, m22 = M[:, 0, 0], M[:, 1, 1], M[:, 2, 2]
    tr = m00 + m11 + m22
    q = np.zeros((len(M), 4))
    c0 = tr > 0
    c1 = ~c0 & (m00 > m11) & (m00 > m22)
    c2 = ~c0 & ~c1 & (m11 > m22)
    c3 = ~c0 & ~c1 & ~c2
    s = np.sqrt(np.maximum(tr[c0] + 1.0, 1e-12)) * 2
    m = M[c0]
    q[c0] = np.stack([(m[:, 2, 1] - m[:, 1, 2]) / s, (m[:, 0, 2] - m[:, 2, 0]) / s, (m[:, 1, 0] - m[:, 0, 1]) / s, 0.25 * s], 1)
    m = M[c1]
    s = np.sqrt(np.maximum(1.0 + m[:, 0, 0] - m[:, 1, 1] - m[:, 2, 2], 1e-12)) * 2
    q[c1] = np.stack([0.25 * s, (m[:, 0, 1] + m[:, 1, 0]) / s, (m[:, 0, 2] + m[:, 2, 0]) / s, (m[:, 2, 1] - m[:, 1, 2]) / s], 1)
    m = M[c2]
    s = np.sqrt(np.maximum(1.0 + m[:, 1, 1] - m[:, 0, 0] - m[:, 2, 2], 1e-12)) * 2
    q[c2] = np.stack([(m[:, 0, 1] + m[:, 1, 0]) / s, 0.25 * s, (m[:, 1, 2] + m[:, 2, 1]) / s, (m[:, 0, 2] - m[:, 2, 0]) / s], 1)
    m = M[c3]
    s = np.sqrt(np.maximum(1.0 + m[:, 2, 2] - m[:, 0, 0] - m[:, 1, 1], 1e-12)) * 2
    q[c3] = np.stack([(m[:, 0, 2] + m[:, 2, 0]) / s, (m[:, 1, 2] + m[:, 2, 1]) / s, 0.25 * s, (m[:, 1, 0] - m[:, 0, 1]) / s], 1)
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    return q.reshape(sh + (4,))


def axis_angle(axis, ang):
    """Rodrigues, vectorised: axis (...,3) unit, ang (...) -> (...,3,3)."""
    axis = np.asarray(axis, float)
    ang = np.asarray(ang, float)
    x, y, z = axis[..., 0], axis[..., 1], axis[..., 2]
    c, s = np.cos(ang), np.sin(ang)
    C = 1 - c
    return np.stack([
        np.stack([c + x * x * C, x * y * C - z * s, x * z * C + y * s], -1),
        np.stack([y * x * C + z * s, c + y * y * C, y * z * C - x * s], -1),
        np.stack([z * x * C - y * s, z * y * C + x * s, c + z * z * C], -1)], -2)


def rot_log(R):
    """(...,3,3) -> rotation vectors (...,3)."""
    q = m2q(R)
    q = np.where(q[..., 3:4] < 0, -q, q)
    v = q[..., :3]
    s = np.linalg.norm(v, axis=-1)
    ang = 2 * np.arctan2(s, q[..., 3])
    return v / np.maximum(s, 1e-12)[..., None] * ang[..., None]


def rot_exp(rv):
    ang = np.linalg.norm(rv, axis=-1)
    ax = rv / np.maximum(ang, 1e-12)[..., None]
    return axis_angle(ax, ang)


# ------------------------------------------------------------------------------------------------ subject skeleton
class Skeleton:
    """Rest skeleton + skin of subject.glb (Y up, metres, floor at 0, faces +Z)."""

    def __init__(self, path=GLB_PATH):
        g, bin_ = read_glb(path)
        self.g = g
        nodes = g["nodes"]
        sk = g["skins"][0]
        joints = sk["joints"]
        self.names = [nodes[j]["name"] for j in joints]
        ji = {j: k for k, j in enumerate(joints)}
        par = np.full(len(joints), -1)
        for j in joints:
            for c in nodes[j].get("children", []):
                if c in ji:
                    par[ji[c]] = ji[j]
        self.parents = par
        assert all(par[k] < k for k in range(len(par))), "joints not topologically ordered"
        self.rest_q = np.array([nodes[j].get("rotation", [0, 0, 0, 1]) for j in joints], float)
        self.rest_t = np.array([nodes[j].get("translation", [0, 0, 0]) for j in joints], float)
        self.rest_L = q2m(self.rest_q)
        B = len(joints)
        self.R = np.zeros((B, 3, 3))
        self.H = np.zeros((B, 3))
        for k in range(B):
            p = par[k]
            if p < 0:
                self.R[k], self.H[k] = self.rest_L[k], self.rest_t[k]
            else:
                self.R[k] = self.R[p] @ self.rest_L[k]
                self.H[k] = self.H[p] + self.R[p] @ self.rest_t[k]
        self.ix = {n: k for k, n in enumerate(self.names)}
        self.ibm = accessor(g, bin_, sk["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
        # skinned vertices of every part (for floor / sliding checks); subsample the big parts
        parts = {}
        for node in nodes:
            if "mesh" not in node:
                continue
            m = g["meshes"][node["mesh"]]
            pr = m["primitives"][0]
            at = pr["attributes"]
            P = accessor(g, bin_, at["POSITION"]).astype(float)
            J = accessor(g, bin_, at["JOINTS_0"]).astype(int)
            W = accessor(g, bin_, at["WEIGHTS_0"]).astype(float)
            parts[m["name"]] = (P, J, W)
        self.parts = parts

    def fk(self, Rl, root_pos):
        """Rl (F,B,3,3) local rotations, root_pos (F,3) -> world rotations (F,B,3,3), heads (F,B,3)."""
        F, B = Rl.shape[:2]
        Rw = np.empty_like(Rl)
        Hw = np.empty((F, B, 3))
        for k in range(B):
            p = self.parents[k]
            if p < 0:
                Rw[:, k] = Rl[:, k]
                Hw[:, k] = root_pos
            else:
                Rw[:, k] = Rw[:, p] @ Rl[:, k]
                Hw[:, k] = Hw[:, p] + Rw[:, p] @ self.rest_t[k]
        return Rw, Hw

    def locals_(self, Rw):
        Rl = np.empty_like(Rw)
        for k in range(Rw.shape[1]):
            p = self.parents[k]
            Rl[:, k] = Rw[:, k] if p < 0 else np.swapaxes(Rw[:, p], -1, -2) @ Rw[:, k]
        return Rl

    def skin(self, Rw, Hw, P, J, Wt):
        """Linear blend skinning of vertices P (N,3) for frames -> (F,N,3)."""
        F = Rw.shape[0]
        M = np.zeros((F, len(self.names), 4, 4))
        M[:, :, :3, :3] = Rw
        M[:, :, :3, 3] = Hw
        M[:, :, 3, 3] = 1
        S = M @ self.ibm[None]  # (F,B,4,4)
        Ph = np.concatenate([P, np.ones((len(P), 1))], 1)
        out = np.zeros((F, len(P), 3))
        for c in range(4):
            Sc = S[:, J[:, c]]  # (F,N,4,4)
            out += Wt[None, :, c, None] * np.einsum("fnij,nj->fni", Sc[..., :3, :], Ph)
        return out


# ------------------------------------------------------------------------------------------------ retarget
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
for _s, _S in (("L", "Left"), ("R", "Right")):
    for _t in range(1, 6):
        for _k in range(1, 4):
            MAP[f"toe{_t}-{_k}.{_s}"] = f"{_S}ToeBase"
AIM = {}
for _s, _S in (("L", "Left"), ("R", "Right")):
    AIM.update({f"upperarm01.{_s}": (f"{_S}Arm", f"{_S}ForeArm"), f"upperarm02.{_s}": (f"{_S}Arm", f"{_S}ForeArm"),
                f"lowerarm01.{_s}": (f"{_S}ForeArm", f"{_S}Hand"), f"lowerarm02.{_s}": (f"{_S}ForeArm", f"{_S}Hand"),
                f"upperleg01.{_s}": (f"{_S}UpLeg", f"{_S}Leg"), f"upperleg02.{_s}": (f"{_S}UpLeg", f"{_S}Leg"),
                f"lowerleg01.{_s}": (f"{_S}Leg", f"{_S}Foot"), f"lowerleg02.{_s}": (f"{_S}Leg", f"{_S}Foot")})


def min_rot(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    s, c = np.linalg.norm(v), float(np.dot(a, b))
    if s < 1e-9:
        return np.eye(3)
    return axis_angle(v / s, np.arctan2(s, c))


def retarget(sk: Skeleton, bvh_path, t0, t1, fps_out=FPS):
    clip = load_bvh(bvh_path)
    P, Rs = clip.world()
    ix = {n: i for i, n in enumerate(clip.names)}
    P = P * CMU_UNIT_M
    names, par = sk.names, sk.parents
    B = len(names)
    Rcal = np.zeros((B, 3, 3))
    Hcal = np.zeros((B, 3))
    for k, n in enumerate(names):
        p = par[k]
        if p < 0:
            Rcal[k], Hcal[k] = sk.R[k], sk.H[k]
        else:
            dP = Rcal[p] @ sk.R[p].T
            Rcal[k] = dP @ sk.R[k]
            Hcal[k] = Hcal[p] + dP @ (sk.H[k] - sk.H[p])
        if n in AIM:
            a, b = AIM[n]
            Rcal[k] = min_rot(Rcal[k][:, 1], P[0, ix[b]] - P[0, ix[a]]) @ Rcal[k]
    src_fps = clip.fps
    f_first = max(1, int(round(t0 * src_fps)) + 1)
    f_last = min(clip.n_frames - 1, int(round(t1 * src_fps)) + 1)
    ts = np.arange(f_first, f_last + 1e-9, src_fps / fps_out)
    fi = np.clip(np.round(ts).astype(int), 0, clip.n_frames - 1)
    Rsrc, Psrc = Rs[fi], P[fi]
    # calibration frame: the cgspeed T-pose (frame 0) bends the neck and head (Neck.X -16, Neck1.X +21, Head.X +11:
    # the head pitched ~16 deg down). The MakeHuman rest head is upright, so neck/head deltas are taken from the
    # zero pose instead (all their channels 0, parents are 0 in frame 0 -> identity world rotation), which is upright.
    R0 = Rs[0].copy()
    for j in ("Neck", "Neck1", "Head"):
        R0[ix[j]] = np.eye(3)
    src_ground = float(np.percentile(P[1:, :, 1].min(axis=1), 1))
    src_hip_h = P[0, 0, 1] - P[0, :, 1].min()
    tgt_ground = Hcal[:, 1].min()
    k_scale = (Hcal[0, 1] - tgt_ground) / src_hip_h
    F = len(fi)
    Rw = np.zeros((F, B, 3, 3))
    for k, n in enumerate(names):
        src = MAP.get(n)
        if src is not None:
            D = Rsrc[:, ix[src]] @ R0[ix[src]].T
        else:
            D = Rw[:, par[k]] @ Rcal[par[k]].T
        Rw[:, k] = D @ Rcal[k]
    root = Psrc[:, 0] - np.array([0.0, src_ground, 0.0])
    root = root * k_scale
    root[:, [0, 2]] -= root[0, [0, 2]]
    return dict(Rw=Rw, root=root, scale=float(k_scale), src_fps=src_fps, frames=fi, clip=clip)


# ------------------------------------------------------------------------------------------------ post-processing
def swing_twist_angle(D, axis):
    """Twist angle of rotations D (F,3,3) about unit axes (F,3)."""
    q = m2q(D)
    q = np.where(q[:, 3:4] < 0, -q, q)
    return 2 * np.arctan2(np.einsum("fi,fi->f", q[:, :3], axis), q[:, 3])


def distribute_twist(sk: Skeleton, Rw):
    """Spread limb twist over the twist segments (see module docstring). Rw edited in place, world space."""
    ix = sk.ix
    Rl0 = sk.rest_L
    out = {}
    for s in ("L", "R"):
        for (parent, seg1, seg2, child, k1, k2, mode) in (
                (f"shoulder01.{s}", f"upperarm01.{s}", f"upperarm02.{s}", None, 0.5, None, "self"),
                (f"lowerarm01.{s}", f"lowerarm01.{s}", f"lowerarm02.{s}", f"wrist.{s}", 1 / 3, 2 / 3, "child"),
                (f"pelvis.{s}", f"upperleg01.{s}", f"upperleg02.{s}", None, 0.5, None, "self"),
                (f"lowerleg01.{s}", f"lowerleg01.{s}", f"lowerleg02.{s}", f"foot.{s}", 1 / 3, 2 / 3, "child")):
            a, b = ix[seg1], ix[seg2]
            if mode == "self":
                # twist of seg1 relative to its parent carried rigidly: keep k1 of it on seg1, seg2 keeps all
                p = ix[parent]
                rig = Rw[:, p] @ Rl0[a]
                D = Rw[:, a] @ np.swapaxes(rig, -1, -2)
                tau = swing_twist_angle(D, rig[:, :, 1])
                Rw[:, a] = axis_angle(Rw[:, a][:, :, 1], -(1 - k1) * tau) @ Rw[:, a]
                out[seg1] = tau
            else:
                c = ix[child]
                rig = Rw[:, b] @ Rl0[c]
                D = Rw[:, c] @ np.swapaxes(rig, -1, -2)
                tau = swing_twist_angle(D, Rw[:, b][:, :, 1])
                Rw[:, a] = axis_angle(Rw[:, a][:, :, 1], k1 * tau) @ Rw[:, a]
                Rw[:, b] = axis_angle(Rw[:, b][:, :, 1], k2 * tau) @ Rw[:, b]
                out[child] = tau
    return out


def distribute_bend(sk: Skeleton, Rw):
    """Half/half split of the bend of CMU segments that drive two MakeHuman bones (spine04/03, spine02/01, neck02/03)."""
    ix = sk.ix
    for parent, a in (("spine05", "spine04"), ("spine03", "spine02"), ("neck01", "neck02")):
        p, k = ix[parent], ix[a]
        rig = Rw[:, p] @ sk.rest_L[k]
        D = Rw[:, k] @ np.swapaxes(rig, -1, -2)
        Rw[:, k] = rot_exp(0.5 * rot_log(D)) @ rig


def forward_of(sk: Skeleton, Hw):
    """Facing direction in the ground plane from the hip joints (F,3)."""
    lat = Hw[:, sk.ix["upperleg01.L"]] - Hw[:, sk.ix["upperleg01.R"]]
    f = np.cross(lat, [0.0, 1.0, 0.0])
    f[:, 1] = 0
    return f / np.linalg.norm(f, axis=1, keepdims=True)


def yaw_of(v):
    return np.arctan2(v[..., 0], v[..., 2])


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def apply_yaw(Rw_root, root, ang, pivot=np.zeros(3)):
    Ry = rot_y(ang)
    return Ry @ Rw_root, (root - pivot) @ Ry.T + pivot


# ------------------------------------------------------------------------------------------------ feet
FOOT_PTS = {}


def foot_points(sk: Skeleton):
    """Heel and ball point of each shoe (vertex index into the shoes part) from the rest mesh."""
    if FOOT_PTS:
        return FOOT_PTS
    P, J, W = sk.parts["shoes"]
    for s, sign in (("L", 1), ("R", -1)):
        m = (P[:, 0] * sign) > 0
        idx = np.nonzero(m)[0]
        Q = P[idx]
        low = Q[:, 1] < Q[:, 1].min() + 0.012
        cand = idx[low]
        z = P[cand, 2]
        heel = cand[np.argmin(z)]
        zs = z.min() + 0.72 * (z.max() - z.min())      # ball of the foot ~72 % of shoe length from the heel
        ball = cand[np.argmin(np.abs(z - zs) + 0.2 * np.abs(P[cand, 0] - P[cand, 0].mean()))]
        FOOT_PTS[s] = (heel, ball)
    return FOOT_PTS


def track_points(sk, Rw, Hw, ids):
    P, J, W = sk.parts["shoes"]
    return sk.skin(Rw, Hw, P[ids], J[ids], W[ids])


def contacts(pts, fps, h_thr=0.035, v_thr=0.30):
    """pts (F,3) -> boolean contact mask (low + slow), cleaned of 1-2 frame blips."""
    v = np.zeros(len(pts))
    v[1:] = np.linalg.norm(np.diff(pts[:, [0, 2]], axis=0), axis=1) * fps
    v[0] = v[1] if len(v) > 1 else 0
    ground = np.percentile(pts[:, 1], 5)
    c = (pts[:, 1] < ground + h_thr) & (v < v_thr)
    # morphological clean-up
    c2 = c.copy()
    for i in range(1, len(c) - 1):
        if c[i - 1] == c[i + 1] != c[i]:
            c2[i] = c[i - 1]
    return c2


def spans(mask):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j + 1 < len(mask) and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def sliding_stats(sk, Rw, Hw, fps, cth=None):
    """Foot skate: for each heel/ball contact span, the max horizontal drift from its mean position (cm)."""
    fp = foot_points(sk)
    ids = [fp["L"][0], fp["L"][1], fp["R"][0], fp["R"][1]]
    T = track_points(sk, Rw, Hw, ids)
    drift = []
    for j in range(4):
        c = contacts(T[:, j], fps, **(cth or {}))
        for a, b in spans(c):
            if b - a < 3:
                continue
            xz = T[a:b + 1, j][:, [0, 2]]
            drift.append(float(np.linalg.norm(xz - np.median(xz, 0), axis=1).max()))
    drift = np.array(drift) * 100
    return dict(contacts=int(len(drift)), max_cm=round(float(drift.max()), 2) if len(drift) else 0.0,
                p90_cm=round(float(np.percentile(drift, 90)), 2) if len(drift) else 0.0,
                median_cm=round(float(np.median(drift)), 2) if len(drift) else 0.0)


def two_bone_ik(A, B, C, T, pole):
    """Positions of hip A, knee B, ankle C (F,3), target ankle T. Returns rotations (F,3,3) for the upper and lower
    segment (world, to pre-multiply) that bring C to T keeping the bend plane close to the current (pole) one."""
    F = len(A)
    l1 = np.linalg.norm(B - A, axis=1)
    l2 = np.linalg.norm(C - B, axis=1)
    d = T - A
    dl = np.clip(np.linalg.norm(d, axis=1), np.abs(l1 - l2) + 1e-4, l1 + l2 - 1e-4)
    dn = d / np.linalg.norm(d, axis=1, keepdims=True)
    # bend plane from the current knee direction
    kd = pole - np.einsum("fi,fi->f", pole, dn)[:, None] * dn
    kd /= np.maximum(np.linalg.norm(kd, axis=1, keepdims=True), 1e-9)
    cosA = np.clip((l1 ** 2 + dl ** 2 - l2 ** 2) / (2 * l1 * dl), -1, 1)
    sinA = np.sqrt(1 - cosA ** 2)
    Bn = A + (dn * cosA[:, None] + kd * sinA[:, None]) * l1[:, None]
    Cn = A + dn * dl[:, None]
    R1 = np.stack([min_rot(B[f] - A[f], Bn[f] - A[f]) for f in range(F)])
    # after R1 the lower segment direction is R1 (C-B); rotate it onto Cn-Bn
    R2 = np.stack([min_rot(R1[f] @ (C[f] - B[f]), Cn[f] - Bn[f]) for f in range(F)])
    return R1, R2


def foot_lock(sk: Skeleton, Rl, root, fps, blend=4, cth=None):
    """Pin planted feet: per leg, contact spans of the ankle-projected sole are held at their median ground position
    with two-bone IK (thigh + shin), eased in/out over `blend` frames. Returns new Rl and a report."""
    ix = sk.ix
    Rw, Hw = sk.fk(Rl, root)
    fp = foot_points(sk)
    rep = {}
    for s in ("L", "R"):
        ids = list(fp[s])
        T = track_points(sk, Rw, Hw, ids)           # (F,2,3) heel, ball
        heel, ball = T[:, 0], T[:, 1]
        ch, cb = contacts(heel, fps, **(cth or {})), contacts(ball, fps, **(cth or {}))
        planted = ch | cb
        ua, ub, la, lb, ft = (ix[f"upperleg01.{s}"], ix[f"upperleg02.{s}"], ix[f"lowerleg01.{s}"],
                              ix[f"lowerleg02.{s}"], ix[f"foot.{s}"])
        A, K, C = Hw[:, ua], Hw[:, la], Hw[:, ft]
        target = C.copy()
        weight = np.zeros(len(C))
        wh = np.convolve(ch.astype(float), np.ones(5) / 5, "same") * ch
        wb = np.convolve(cb.astype(float), np.ones(5) / 5, "same") * cb
        for a, b in spans(planted):
            if b - a < 2:
                continue
            sl = slice(a, b + 1)
            off = np.zeros((b - a + 1, 3))
            acc = np.zeros(b - a + 1)
            for pts, cm, wv in ((heel, ch, wh), (ball, cb, wb)):
                m = cm[sl]
                if not m.any():
                    continue
                ref = np.median(pts[sl][m][:, [0, 2]], 0)       # where this sole point rests during the span
                o = np.zeros((b - a + 1, 3))
                o[:, [0, 2]] = ref - pts[sl][:, [0, 2]]
                off += o * wv[sl, None]
                acc += wv[sl]
            ok = acc > 1e-6
            off[ok] /= acc[ok, None]
            # frames of the span where neither weight is set: hold the nearest defined offset
            if (~ok).any() and ok.any():
                idx = np.nonzero(ok)[0]
                for i in np.nonzero(~ok)[0]:
                    off[i] = off[idx[np.argmin(np.abs(idx - i))]]
            target[sl] = C[sl] + off
            w = np.ones(b - a + 1)
            n = min(blend, (b - a + 1) // 2)
            if n > 0:
                ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n + 2)[1:-1])
                w[:n] = ramp
                w[-n:] = ramp[::-1]
            weight[sl] = np.maximum(weight[sl], w)
        target = C + (target - C) * weight[:, None]
        R1, R2 = two_bone_ik(A, K, C, target, K - (A + C) / 2)
        Rw2 = Rw.copy()
        foot_world = Rw[:, ft].copy()
        for b_ in (ua, ub):
            Rw2[:, b_] = R1 @ Rw[:, b_]
        for b_ in (la, lb):
            Rw2[:, b_] = R2 @ R1 @ Rw[:, b_]
        Rw2[:, ft] = foot_world                     # keep the foot's world orientation (flat on the floor)
        # write back into locals only for this leg chain (+ the foot and its descendants keep their locals)
        Rl_new = sk.locals_(Rw2)
        for b_ in (ua, ub, la, lb, ft):
            Rl[:, b_] = Rl_new[:, b_]
        Rw, Hw = sk.fk(Rl, root)
        rep[s] = dict(planted_frac=round(float(planted.mean()), 3), max_fix_cm=round(float(np.linalg.norm((target - C)[:, [0, 2]], axis=1).max() * 100), 2))
    return Rl, rep


def lowest_points(sk, Rw, Hw):
    """Per-frame lowest point of the skinned subject (shoes, trousers, skin, top, hair; subsampled)."""
    sub = []
    for nm, every in (("shoes", 3), ("trousers", 2), ("skin", 4), ("top", 4), ("hair", 4)):
        P, J, W = sk.parts[nm]
        sub.append((P[::every], J[::every], W[::every]))
    lows = []
    for f0 in range(0, len(Rw), 64):
        f1 = min(len(Rw), f0 + 64)
        m = np.inf * np.ones(f1 - f0)
        for P, J, W in sub:
            X = sk.skin(Rw[f0:f1], Hw[f0:f1], P, J, W)
            m = np.minimum(m, X[:, :, 1].min(1))
        lows.append(m)
    return np.concatenate(lows)


def floor_contact(sk, Rl, root, sigma=1.5):
    """Per-frame floor contact: shift the root so the lowest point of the skinned subject touches y = 0 in every frame
    (lightly smoothed). Valid for clips with continuous ground contact (all but runs / jumps)."""
    Rw, Hw = sk.fk(Rl, root)
    low = lowest_points(sk, Rw, Hw)
    k = np.arange(-4, 5)
    g = np.exp(-0.5 * (k / sigma) ** 2)
    g /= g.sum()
    pad = np.concatenate([np.full(4, low[0]), low, np.full(4, low[-1])])
    sm = np.convolve(pad, g, "valid")
    root = root.copy()
    root[:, 1] -= sm
    return root


def foot_lock_iter(sk, Rl, root, fps, iters=3, cth=None):
    """foot_lock repeated: each pass re-detects contacts on the corrected legs (heel/ball references converge)."""
    reps = []
    for _ in range(iters):
        Rl, rep = foot_lock(sk, Rl, root, fps, cth=cth)
        reps.append(rep)
    return Rl, dict(passes=iters, first=reps[0], last=reps[-1])


# ------------------------------------------------------------------------------------------------ loops
def pose_features(sk, Rl, root, Hw):
    main = [sk.ix[n] for n in ("upperleg01.L", "lowerleg01.L", "foot.L", "upperleg01.R", "lowerleg01.R", "foot.R",
                               "upperarm01.L", "lowerarm01.L", "upperarm01.R", "lowerarm01.R", "spine04", "neck01", "head")]
    f = [Rl[:, main].reshape(len(Rl), -1)]
    fwd = forward_of(sk, Hw)
    yaw = yaw_of(fwd)
    # root velocity in the heading frame
    v = np.gradient(root, axis=0)
    c, s = np.cos(-yaw), np.sin(-yaw)
    vl = np.stack([c * v[:, 0] + s * v[:, 2], v[:, 1], -s * v[:, 0] + c * v[:, 2]], 1)
    f.append(root[:, 1:2] * 4)
    return np.concatenate(f, 1), vl * 30


def find_loop(sk, Rl, root, fps, s0, s1, tmin, tmax):
    Rw, Hw = sk.fk(Rl, root)
    feat, vel = pose_features(sk, Rl, root, Hw)
    a0, a1 = int(s0 * fps), int(s1 * fps)
    best = None
    for a in range(a0, a1):
        for b in range(a + int(tmin * fps), min(a + int(tmax * fps), a1) + 1):
            if b >= len(Rl):
                break
            d = np.linalg.norm(feat[a] - feat[b]) + 0.5 * np.linalg.norm(vel[a] - vel[b]) \
                + 0.3 * np.linalg.norm(feat[a + 1] - feat[b + 1] if b + 1 < len(Rl) else 0)
            if best is None or d < best[0]:
                best = (d, a, b)
    return best


def close_loop(sk, Rl, root, a, b):
    """Frames a..b-1 become the cycle; residual at the seam (frame b vs a) is removed linearly. Returns Rl, root,
    per-cycle delta (dx, dz in the start heading frame, dyaw)."""
    N = b - a
    Rl_c = Rl[a:b + 1].copy()
    rt = root[a:b + 1].copy()
    wts = np.arange(N + 1) / N
    for k in range(Rl.shape[1]):
        D = Rl_c[N, k] @ Rl_c[0, k].T   # seam residual (left-multiplied)
        rv = rot_log(D[None])[0]
        if np.linalg.norm(rv) < 1e-7:
            continue
        corr = rot_exp(-wts[:, None] * rv[None])
        Rl_c[:, k] = corr @ Rl_c[:, k]
    rt[:, 1] -= wts * (rt[N, 1] - rt[0, 1])
    return Rl_c[:N], rt[:N], rt[N] - rt[0]


# ------------------------------------------------------------------------------------------------ build
def build_clip(sk, c, titles):
    t_start = time.time()
    bvh = CMU / f"{c['cmu']}.bvh"
    r = retarget(sk, bvh, c["seg"][0], c["seg"][1])
    Rw = r["Rw"]
    root = r["root"]
    twist = distribute_twist(sk, Rw)
    distribute_bend(sk, Rw)
    Rl = sk.locals_(Rw)
    for k, n in enumerate(sk.names):     # unmapped bones (fingers, face, breast...) stay rigid w.r.t. their parent
        if n not in MAP:
            Rl[:, k] = sk.rest_L[k]
    Rw, Hw = sk.fk(Rl, root)
    # ---- heading normalisation (start at origin facing +Z; walks: travelling along +Z)
    fwd = forward_of(sk, Hw)
    n0 = max(1, min(len(fwd), int(0.25 * FPS)))
    if c.get("align") == "travel":
        d = root[-1] - root[0]
        ang = -np.arctan2(d[0], d[2])
    elif c.get("align") == "facing_end":
        f1 = fwd[-n0:].mean(0)
        ang = -np.arctan2(f1[0], f1[2])
    else:
        f0 = fwd[:n0].mean(0)
        ang = -np.arctan2(f0[0], f0[2])
    Ry = rot_y(ang)
    Rl[:, 0] = Ry @ Rl[:, 0]
    root = (root - root[0] * np.array([1, 0, 1])) @ Ry.T
    # ---- floor from the skinned mesh
    Rw, Hw = sk.fk(Rl, root)
    low = lowest_points(sk, Rw, Hw)
    shift = -float(np.median(low))
    root[:, 1] += shift
    cth = c.get("contact")      # contact thresholds, e.g. runs: the stance foot is only 'slow', not still
    # ---- loop (cycle search + seam closure), then foot lock (tiled x3 for loops so spans can cross the seam)
    loop = None
    fl_rep = None
    if c.get("loop"):
        L = c["loop"]
        s0 = L["search"][0] - c["seg"][0]
        s1 = L["search"][1] - c["seg"][0]
        d, a, b = find_loop(sk, Rl, root, FPS, s0, s1, L["min"], L["max"])
        Rl, root, delta = close_loop(sk, Rl, root, a, b)
        ang2 = -np.arctan2(delta[0], delta[2]) if np.hypot(delta[0], delta[2]) > 0.05 else 0.0
        Ry = rot_y(ang2)
        Rl[:, 0] = Ry @ Rl[:, 0]
        root = (root - root[0] * np.array([1, 0, 1])) @ Ry.T
        delta = Ry @ delta
        loop = dict(seam_distance=round(float(d), 4), src_frames=[int(a), int(b)], cycle_s=round((b - a) / FPS, 4),
                    cycle_root_delta=[round(float(delta[0]), 4), 0.0, round(float(delta[2]), 4)], cycle_yaw_delta=0.0)
        N = len(Rl)
        Rl3 = np.concatenate([Rl, Rl, Rl], 0)
        root3 = np.concatenate([root, root + delta, root + 2 * delta], 0)
        if c.get("footlock"):
            Rl3, fl_rep = foot_lock_iter(sk, Rl3, root3, FPS, cth=cth)
        if c.get("floor", "contact") == "contact":
            root3 = floor_contact(sk, Rl3, root3)
        Rl = Rl3[N:2 * N].copy()
        root = root3[N:2 * N] - delta
        Rw, Hw = sk.fk(Rl, root)
        R3 = np.concatenate([Rl, Rl, Rl], 0)
        P3 = np.concatenate([root, root + delta, root + 2 * delta], 0)
        Rw3, Hw3 = sk.fk(R3, P3)
        slide = sliding_stats(sk, Rw3, Hw3, FPS, cth)
    else:
        if c.get("footlock"):
            Rl, fl_rep = foot_lock_iter(sk, Rl, root, FPS, cth=cth)
        if c.get("floor", "contact") == "contact":
            root = floor_contact(sk, Rl, root)
        Rw, Hw = sk.fk(Rl, root)
        slide = sliding_stats(sk, Rw, Hw, FPS, cth)
    F = len(Rl)
    low = lowest_points(sk, Rw, Hw)
    # ---- animated bones (local differs from rest anywhere)
    ang_dev = np.zeros(len(sk.names))
    for k in range(len(sk.names)):
        D = np.swapaxes(sk.rest_L[k][None], -1, -2) @ Rl[:, k]
        ang_dev[k] = np.degrees(np.arccos(np.clip((np.trace(D, axis1=1, axis2=2) - 1) / 2, -1, 1))).max()
    anim = [k for k in range(len(sk.names)) if ang_dev[k] > 0.01 or k == 0]
    Q = m2q(Rl[:, anim])
    # hemisphere continuity per bone (for slerp without flips)
    for k in range(Q.shape[1]):
        for f in range(1, F):
            if np.dot(Q[f, k], Q[f - 1, k]) < 0:
                Q[f, k] = -Q[f, k]
    data = np.concatenate([root, Q.reshape(F, -1)], 1).astype(np.float32)
    MOTION.mkdir(parents=True, exist_ok=True)
    (MOTION / f"{c['name']}.bin").write_bytes(data.tobytes())
    # ---- report
    xz = root[:, [0, 2]]
    path = float(np.linalg.norm(np.diff(xz, axis=0), axis=1).sum())
    net = float(np.linalg.norm(xz[-1] - xz[0]))
    Rw, Hw = sk.fk(Rl, root)
    yaw = np.unwrap(yaw_of(forward_of(sk, Hw)))
    tw = {k: round(float(np.degrees(np.abs(v)).max()), 1) for k, v in twist.items()}
    # residual twist per deforming segment after distribution (local twist about the bone axis)
    seg_tw = {}
    for n in ("upperarm01.L", "upperarm02.L", "lowerarm01.L", "lowerarm02.L", "wrist.L",
              "upperarm01.R", "upperarm02.R", "lowerarm01.R", "lowerarm02.R", "wrist.R",
              "upperleg01.L", "upperleg02.L", "lowerleg02.L", "foot.L", "upperleg01.R", "upperleg02.R", "lowerleg02.R", "foot.R"):
        k = sk.ix[n]
        D = Rl[:, k] @ sk.rest_L[k].T
        # express the pose delta in the bone frame (rest local of k relative to parent)
        Dl = sk.rest_L[k].T @ D @ sk.rest_L[k]
        tau = swing_twist_angle(Dl, np.tile([0.0, 1.0, 0.0], (F, 1)))
        seg_tw[n] = round(float(np.degrees(np.abs(tau)).max()), 1)
    info = dict(
        name=c["name"], file=f"{c['name']}.bin", category=c["cat"], shows=c["shows"],
        frames=F, fps=FPS, seconds=round(F / FPS, 3), loop=bool(loop), loop_info=loop,
        bones=[sk.names[k].replace(".", "") for k in anim],
        root_motion=dict(path_m=round(path, 3), net_m=round(net, 3), turn_deg=round(float(np.degrees(yaw[-1] - yaw[0])), 1),
                         mean_speed_mps=round(path / max(F / FPS, 1e-6), 3)),
        source=dict(cmu_id=c["cmu"], cmu_title=titles.get(c["cmu"]), segment_s=c["seg"], url=raw_url(c["cmu"]),
                    source_bvh=str((CMU / f"{c['cmu']}.bvh").relative_to(REPO)), root_scale=round(r["scale"], 4)),
        checks=dict(floor_shift_m=round(shift, 4),
                    lowest_point_m=dict(min=round(float(low.min()), 4), p5=round(float(np.percentile(low, 5)), 4),
                                        p95=round(float(np.percentile(low, 95)), 4), max=round(float(low.max()), 4)),
                    foot_slide=slide, foot_lock=fl_rep, source_twist_deg=tw, residual_local_twist_deg=seg_tw),
        build_s=round(time.time() - t_start, 1),
    )
    if loop:
        info["loop_info"]["note"] = "chain cycles: cycle k starts at k * cycle_root_delta (heading unchanged)"
        # gait period: count ball contacts of one foot per cycle
        fp = foot_points(sk)
        T = track_points(sk, Rw, Hw, [fp["L"][1]])[:, 0]
        n_steps = len([s for s in spans(contacts(T, FPS)) if s[1] - s[0] >= 2])
        info["loop_info"]["left_foot_contacts_per_cycle"] = n_steps
        if n_steps:
            info["loop_info"]["step_period_s"] = round(F / FPS / (2 * n_steps), 4)
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "build", "list"])
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    if a.cmd == "list":
        for c in CLIPS:
            print(f"{c['name']:28s} {c['cmu']:7s} {c['seg']}  {c['shows']}")
        return
    fetch()
    if a.cmd == "fetch":
        return
    sk = Skeleton()
    titles = cmu_titles()
    only = set(filter(None, a.only.split(",")))
    man_path = MOTION / "MANIFEST.json"
    old = {}
    if man_path.exists() and only:
        old = {c["name"]: c for c in json.loads(man_path.read_text())["clips"]}
    clips = []
    for c in CLIPS:
        if only and c["name"] not in only:
            if c["name"] in old:
                clips.append(old[c["name"]])
            continue
        info = build_clip(sk, c, titles)
        ch = info["checks"]
        print(f"{c['name']:28s} {info['seconds']:6.2f}s bones={len(info['bones']):3d} path={info['root_motion']['path_m']:5.2f}m "
              f"low[{ch['lowest_point_m']['min']:+.3f},{ch['lowest_point_m']['max']:+.3f}] slide p90={ch['foot_slide']['p90_cm']}cm "
              f"max={ch['foot_slide']['max_cm']}cm loop={info['loop_info']['cycle_s'] if info['loop'] else '-'}  ({info['build_s']}s)",
              flush=True)
        clips.append(info)
    man = dict(
        version=1, fps=FPS, generated="claudepop/avatar/tools/motion_lib.py",
        skeleton=dict(glb="claudepop/out/avatar/subject.glb", bones=[n.replace(".", "") for n in sk.names],
                      note="three.js GLTFLoader strips dots from node names; names here are already stripped"),
        coordinate_system="Y up, metres, floor y=0, clip starts at x=z=0 facing +Z (walks travel along +Z)",
        layout="<clip>.bin float32 frame-major: root_pos(3) then xyzw local quaternion per listed bone; unlisted bones = GLB rest",
        source_license="CMU Graphics Lab Motion Capture Database: free for any use; cgspeed BVH conversion by B. Hahne",
        acknowledgement="The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217.",
        clips=clips,
    )
    man_path.write_text(json.dumps(man, indent=1, ensure_ascii=False))
    print("wrote", man_path)


if __name__ == "__main__":
    main()
