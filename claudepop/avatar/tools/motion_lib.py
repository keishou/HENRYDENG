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
    dict(name="walk_runway_sym_loop", cmu="142_04", seg=[2.0, 7.5], cat="walk", align="travel", footlock=True,
         loop=dict(search=[2.8, 7.2], min=0.9, max=3.2), symmetric="L",
         shows="walk_runway_loop made symmetric: the left-stance half-cycle (heel planted) and its mirror, so both steps "
               "last exactly half a cycle; the film's half-time gait (heel strikes land on beats 1 and 3 at one speed)"),
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
    dict(name="stand_breathe_loop", cmu="111_28", seg=[0.0, 4.0], cat="idle", footlock=True, plant=True,
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
    # ---- authored static keys for the film (BIBLE 5.7 M1, M6); built from sit_stool_head_bowed, so after it
    dict(name="pose_sit_stool_upright", cat="pose",
         pose=dict(kind="sit_stool_upright", src="sit_stool_head_bowed", t=5.8, pelvis_tilt=0.45, lean_deg=4.0,
                   seat_y=0.60, ankle_x=0.165, knee_x=0.15, shin_deg=4.0, toe_out_deg=7.0, hand_u=0.62,
                   hand_yaw_in_deg=14.0, hand_roll_deg=8.0, curl=[0.42, 0.46, 0.52, 0.58], thumb=0.25),
         shows="the sitter (S05): upright on the 0.60 m stool facing +Z, hands on the knees, feet flat on the floor"),
    dict(name="pose_sit_stool_face_in_hands", cat="pose",
         pose=dict(kind="sit_stool_face_in_hands", src="sit_stool_head_bowed", t=3.0, pelvis_tilt=0.8,
                   seat_y=0.60, ankle_x=0.17, knee_x=0.16, shin_deg=2.0, toe_out_deg=9.0, neck_deg=34.0),
         shows="S35: on the 0.60 m stool, elbows on the thighs, face buried in both hands (face hidden)"),
]


# ------------------------------------------------------------------------------------------------ io
def raw_url(cid):
    s = int(cid.split("_")[0])
    return f"https://raw.githubusercontent.com/una-dinosauria/cmu-mocap/master/data/{s:03d}/{cid}.bvh"


def fetch(ids=None):
    CMU.mkdir(parents=True, exist_ok=True)
    ids = sorted({c["cmu"] for c in CLIPS if c.get("cmu")}) if ids is None else ids
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
        faces = {}
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
            if "indices" in pr:
                faces[m["name"]] = accessor(g, bin_, pr["indices"]).reshape(-1, 3).astype(int)
        self.parts = parts
        self.faces = faces
        self.children = [[] for _ in joints]
        for k, p in enumerate(par):
            if p >= 0:
                self.children[p].append(k)

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


def heel_strikes(sk, Rw, Hw, fps, rise=0.03, contact=0.012):
    """Heel-strike times (clip seconds, sub-frame) from the skinned heel vertex of each shoe: the heel falls through
    (planted height + `contact`) after having risen above (planted height + `rise`) in the swing. The same definition
    is used by the film-side check (claudepop/film/lookdev/motion_prep.js), which samples the posed skeleton."""
    fp = foot_points(sk)
    T = track_points(sk, Rw, Hw, [fp["L"][0], fp["R"][0]])
    out = []
    for j, s in enumerate("LR"):
        y = T[:, j, 1]
        g = float(np.percentile(y, 5))
        armed = False
        for f in range(1, len(y)):
            if y[f] > g + rise:
                armed = True
            if armed and y[f - 1] >= g + contact > y[f]:
                a = (y[f - 1] - (g + contact)) / (y[f - 1] - y[f])
                out.append(dict(foot=s, t=round((f - 1 + a) / fps, 4)))
                armed = False
    return sorted(out, key=lambda e: e["t"])


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


# ------------------------------------------------------------------------------------------------ authored poses
# Static keys authored from retargeted frames with FK + IK on the subject's own skeleton (film BIBLE 5.7 M1, M6):
#   pose_sit_stool_upright        the sitter (S05): on the 0.60 m stool, pelvis near neutral, spine / neck / head from
#                                 a real standing posture, hands resting on the knees (arm IK + palm orientation +
#                                 forearm twist split + a baked finger curl), feet flat on the floor (leg IK)
#   pose_sit_stool_face_in_hands  S35: the same seat, trunk flexed, head bowed into both hands (palms on the face),
#                                 elbows resting on the thighs; the trunk flexion is solved so the elbows land there
# Each is written as a 1-frame clip (all bones that differ from rest, fingers included: apply it WITHOUT the avatar.js
# hands layer) with its stool placement (props.stool, clip space) and its checks (hand / seat penetration, feet).
M_X = np.diag([-1.0, 1.0, 1.0])     # mirror across the sagittal plane (x -> -x)


def load_built(sk, name):
    """Local rotations (F,B,3,3) and root (F,3) of an already built clip (MOTION/<name>.bin)."""
    man = json.loads((MOTION / "MANIFEST.json").read_text())
    c = next(c for c in man["clips"] if c["name"] == name)
    d = np.fromfile(MOTION / c["file"], dtype=np.float32).reshape(c["frames"], -1).astype(float)
    idx = {n.replace(".", ""): k for k, n in enumerate(sk.names)}
    Rl = np.tile(sk.rest_L[None], (len(d), 1, 1, 1))
    for j, bn in enumerate(c["bones"]):
        Rl[:, idx[bn]] = q2m(d[:, 3 + 4 * j:7 + 4 * j])
    return Rl, d[:, :3].copy()


def rot_avg(A, B, w=0.5):
    return A @ rot_exp(w * rot_log(A.T @ B))


def rot_pow(D, w):
    return rot_exp(w * rot_log(D))


class PoseEdit:
    """One frame of the skeleton held as world rotations Rw (B,3,3) plus the root position; positions follow by FK."""

    def __init__(self, sk, Rl, root):
        self.sk = sk
        self.root = np.asarray(root, float).copy()
        self.set_locals(Rl)

    def k(self, n):
        return self.sk.ix[n]

    def subtree(self, k):
        out, st = [], [k]
        while st:
            i = st.pop()
            out.append(i)
            st.extend(self.sk.children[i])
        return out

    def Rl(self):
        """Local rotations, re-orthonormalised (through unit quaternions) so repeated edits never drift."""
        return q2m(m2q(self.sk.locals_(self.Rw[None])[0]))

    def set_locals(self, Rl):
        self.Rw = self.sk.fk(q2m(m2q(Rl))[None], self.root[None])[0][0]

    def H(self):
        _, H = self.sk.fk(self.Rl()[None], self.root[None])
        return H[0]

    def head(self, n):
        return self.H()[self.k(n)]

    def rotate(self, n, D, pivot=None, subtree=True):
        """World rotation D applied to bone n (and its subtree): children follow; the root pivots about `pivot`."""
        k = self.k(n) if isinstance(n, str) else n
        D = q2m(m2q(D))
        for i in (self.subtree(k) if subtree else [k]):
            self.Rw[i] = D @ self.Rw[i]
        if k == 0:
            p = self.root if pivot is None else np.asarray(pivot, float)
            self.root = p + D @ (self.root - p)

    def delta(self, n):
        k = self.k(n)
        return self.Rw[k] @ self.sk.R[k].T

    def set_delta(self, n, D, follow=True):
        """Bone n gets the world rotation D @ rest; its subtree follows rigidly (face bones stay on the head, fingers
        on the hand) unless follow=False (then the children keep their world rotations)."""
        k = self.k(n)
        new = q2m(m2q(D @ self.sk.R[k]))
        if follow:
            self.rotate(k, new @ self.Rw[k].T)
        else:
            self.Rw[k] = new

    def skin(self, part):
        P, J, W = self.sk.parts[part]
        Rl = self.Rl()
        Rw, Hw = self.sk.fk(Rl[None], self.root[None])
        return self.sk.skin(Rw, Hw, P, J, W)[0]


def mirror_bone(n):
    return n[:-2] + (".R" if n.endswith(".L") else ".L")


def symmetrize(pe, names_L, keep=0.0):
    """Make left / right world deltas mirror images (their average); `keep` re-adds that fraction of the asymmetry."""
    for n in names_L:
        if n not in pe.sk.ix:
            continue
        DL, DR = pe.delta(n), pe.delta(mirror_bone(n))
        Dm = rot_avg(DL, M_X @ DR @ M_X)
        if keep:
            Dm = rot_avg(Dm, DL, keep)
        pe.set_delta(n, Dm)
        pe.set_delta(mirror_bone(n), M_X @ Dm @ M_X)


def pitch_only(D, keep=0.0):
    """The sagittal (x-axis) part of a world rotation; `keep` of the rest of it."""
    rv = rot_log(D[None])[0]
    return rot_exp(np.array([rv[0], keep * rv[1], keep * rv[2]]))


LEG = ["upperleg01", "upperleg02", "lowerleg01", "lowerleg02", "foot"] + [f"toe{t}-{k}" for t in range(1, 6) for k in range(1, 4)]
ARM = ["clavicle", "shoulder01", "upperarm01", "upperarm02", "lowerarm01", "lowerarm02", "wrist"]
SPINE = ["spine05", "spine04", "spine03", "spine02", "spine01", "neck01", "neck02", "neck03", "head"]


def hand_rest_frame(sk, s):
    """Rest hand frame of side s: wrist head, direction wrist -> knuckles, palm normal (same handedness rule as
    avatar.js: left along x across, right across x along), and the palm surface point under the metacarpals."""
    ix = sk.ix
    wp = sk.H[ix[f"wrist.{s}"]]
    idx, pky = sk.H[ix[f"finger2-1.{s}"]], sk.H[ix[f"finger5-1.{s}"]]
    across = (idx - pky) / np.linalg.norm(idx - pky)
    along = (idx + pky) / 2 - wp
    along /= np.linalg.norm(along)
    palm = np.cross(along, across) if s == "L" else np.cross(across, along)
    palm /= np.linalg.norm(palm)
    along = along - palm * float(along @ palm)
    along /= np.linalg.norm(along)
    knuckles = (sk.H[ix[f"finger3-1.{s}"]] + sk.H[ix[f"finger4-1.{s}"]]) / 2
    centre = wp + 0.62 * (knuckles - wp) + palm * 0.012
    return wp, along, palm, centre


def frame_rot(a0, b0, a1, b1):
    """Rotation taking the orthonormal pair (a0, b0) onto (a1, b1)."""
    def basis(a, b):
        a = a / np.linalg.norm(a)
        b = b - a * float(a @ b)
        b /= np.linalg.norm(b)
        return np.stack([a, b, np.cross(a, b)], 1)
    return basis(a1, b1) @ basis(a0, b0).T


def finger_curl(sk, Rl, s, curl, thumb=None):
    """Bake the avatar.js relaxed finger curl into local rotations (same axes and per-phalanx angles)."""
    ix = sk.ix
    wp = sk.H[ix[f"wrist.{s}"]]
    idx, pky = sk.H[ix[f"finger2-1.{s}"]], sk.H[ix[f"finger5-1.{s}"]]
    across = (idx - pky) / np.linalg.norm(idx - pky)
    along = (idx + pky) / 2 - wp
    along /= np.linalg.norm(along)
    palm = np.cross(along, across) if s == "L" else np.cross(across, along)
    palm /= np.linalg.norm(palm)
    for f in range(1, 6):
        for kk in range(1, 4):
            n = f"finger{f}-{kk}.{s}"
            if n not in ix:
                continue
            i = ix[n]
            ch = [c for c in sk.children[i]]
            tail = sk.H[ch[0]] if ch else sk.H[i] + sk.R[i][:, 1] * 0.02
            d = (tail - sk.H[i]) / np.linalg.norm(tail - sk.H[i])
            axw = np.cross(d, palm)
            axw /= np.linalg.norm(axw)
            axl = sk.R[i].T @ axw
            deg = [10, 12, 10][kk - 1] if f == 1 else [18, 26, 14][kk - 1] * (1 + 0.12 * (f - 2))
            c = (thumb if thumb is not None else curl) if f == 1 else (curl[f - 2] if isinstance(curl, (list, tuple)) else curl)
            Rl[i] = sk.rest_L[i] @ axis_angle(axl, np.radians(deg * c))
    return Rl


def signed_depth(points, verts, faces):
    """Signed distance of points to a skinned surface (negative = inside, by the closest face's normal)."""
    import trimesh
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    cp, dist, tri = trimesh.proximity.closest_point(m, points)
    sgn = np.sign(np.einsum("ij,ij->i", points - cp, m.face_normals[tri]))
    return dist * np.where(sgn == 0, 1, sgn)


def part_verts_of_bones(sk, part, bone_names, wmin=0.5):
    P, J, W = sk.parts[part]
    ks = [sk.ix[n] for n in bone_names if n in sk.ix]
    w = sum((W * (J == k)).sum(1) for k in ks)
    return np.nonzero(w >= wmin)[0]


def hand_bones(sk, s):
    return [n for n in sk.names if n.endswith("." + s) and (n.startswith("finger") or n.startswith("metacarpal") or n.startswith("wrist"))]


def arm_ik(pe, s, target, pole):
    """Two-bone IK of the arm of side s (shoulder joint -> elbow -> wrist head onto `target`)."""
    A, B, C = pe.head(f"upperarm01.{s}"), pe.head(f"lowerarm01.{s}"), pe.head(f"wrist.{s}")
    R1, R2 = two_bone_ik(A[None], B[None], C[None], np.asarray(target, float)[None], np.asarray(pole, float)[None])
    pe.rotate(f"upperarm01.{s}", R1[0])
    pe.rotate(f"lowerarm01.{s}", R2[0])


def leg_ik(pe, s, target, pole):
    A, B, C = pe.head(f"upperleg01.{s}"), pe.head(f"lowerleg01.{s}"), pe.head(f"foot.{s}")
    R1, R2 = two_bone_ik(A[None], B[None], C[None], np.asarray(target, float)[None], np.asarray(pole, float)[None])
    pe.rotate(f"upperleg01.{s}", R1[0])
    pe.rotate(f"lowerleg01.{s}", R2[0])


def orient_hand(pe, s, along_t, palm_t):
    """Turn the hand (and fingers) so its rest direction / palm normal map onto along_t / palm_t, then split the
    forearm twist 1/3 : 2/3 over lowerarm01 / 02 like the retarget (no candy-wrapper at the wrist)."""
    sk = pe.sk
    wp, along, palm, _ = hand_rest_frame(sk, s)
    Rt = frame_rot(along, palm, along_t, palm_t)
    kw = pe.k(f"wrist.{s}")
    D = (Rt @ sk.R[kw]) @ pe.Rw[kw].T
    pe.rotate(f"wrist.{s}", D)
    a, b = pe.k(f"lowerarm01.{s}"), pe.k(f"lowerarm02.{s}")
    rig = pe.Rw[b] @ sk.rest_L[kw]
    Dw = pe.Rw[kw] @ rig.T
    tau = swing_twist_angle(Dw[None], pe.Rw[b][:, 1][None])[0]
    pe.Rw[a] = axis_angle(pe.Rw[a][:, 1], tau / 3) @ pe.Rw[a]
    pe.Rw[b] = axis_angle(pe.Rw[b][:, 1], 2 * tau / 3) @ pe.Rw[b]
    return float(np.degrees(tau))


def seat_profile(pe, seat_y, centre_xz, radius):
    """Trouser (and top hem) vertices over the seat disk: lowest point and penetration below the seat plane."""
    X = pe.skin("trousers")
    d = np.hypot(X[:, 0] - centre_xz[0], X[:, 2] - centre_xz[1])
    m = d < radius
    return X, m


def feet_report(pe):
    fp = foot_points(pe.sk)
    Rl = pe.Rl()
    Rw, Hw = pe.sk.fk(Rl[None], pe.root[None])
    T = track_points(pe.sk, Rw, Hw, [fp["L"][0], fp["L"][1], fp["R"][0], fp["R"][1]])[0]
    S = pe.skin("shoes")
    return dict(heel_L_cm=round(T[0, 1] * 100, 2), ball_L_cm=round(T[1, 1] * 100, 2), heel_R_cm=round(T[2, 1] * 100, 2),
                ball_R_cm=round(T[3, 1] * 100, 2), shoe_lowest_cm=round(float(S[:, 1].min()) * 100, 2))


def stand_upper(sk):
    """Upper-body world deltas of a real standing posture (stand_breathe_loop frame 0, facing +Z), symmetrised."""
    Rl, root = load_built(sk, "stand_breathe_loop")
    ps = PoseEdit(sk, Rl[0], root[0])
    fwd = forward_of(sk, ps.H()[None])[0]
    ps.rotate(0, rot_y(-np.arctan2(fwd[0], fwd[2])), pivot=ps.root)
    ps.set_delta("root", pitch_only(ps.delta("root")))
    for n in SPINE:
        ps.set_delta(n, pitch_only(ps.delta(n)))
    symmetrize(ps, [f"{b}.L" for b in ARM])
    return ps


def seated_base(sk, spec):
    """Seated frame of sit_stool_head_bowed, facing +Z, hips centred at x = z = 0, root and legs symmetric, the
    pelvis tilt set to `pelvis_tilt` of the capture's posterior tilt relative to standing."""
    Rl, root = load_built(sk, spec.get("src", "sit_stool_head_bowed"))
    f = int(round(spec["t"] * FPS))
    pe = PoseEdit(sk, Rl[f], root[f])
    fwd = forward_of(sk, pe.H()[None])[0]
    pe.rotate(0, rot_y(-np.arctan2(fwd[0], fwd[2])), pivot=pe.root)
    hc = (pe.head("upperleg01.L") + pe.head("upperleg01.R")) / 2
    pe.root -= np.array([hc[0], 0, hc[2]])
    ps = stand_upper(sk)
    # root: sagittal part only; pelvis tilt as a fraction of the capture's posterior tilt (pivot: the hip axis)
    hc = (pe.head("upperleg01.L") + pe.head("upperleg01.R")) / 2
    D_seat = pitch_only(pe.delta("root"))
    D_stand = ps.delta("root")
    D_target = rot_pow(D_seat @ D_stand.T, spec.get("pelvis_tilt", 0.5)) @ D_stand
    Dfix = D_target @ pe.delta("root").T
    for n in ("root", "pelvis.L", "pelvis.R"):
        pe.rotate(n, Dfix, pivot=hc, subtree=False)
    symmetrize(pe, [f"{b}.L" for b in LEG], keep=spec.get("leg_asym", 0.0))
    return pe, ps, D_target @ D_stand.T


def upright_upper(pe, ps, D_pel, lean_deg=0.0, lumbar=(0.55, 0.3, 0.1)):
    """Spine / neck / head from the standing posture; the remaining pelvis tilt is taken out over the lumbar bones so
    the chest is as upright as standing; then an optional forward lean of the whole upper body."""
    for n in SPINE:
        pe.set_delta(n, ps.delta(n))
    for n, w in zip(("spine05", "spine04", "spine03"), lumbar):
        pe.set_delta(n, rot_pow(D_pel, w) @ ps.delta(n))
    for s in "LR":
        for b in ARM:
            pe.set_delta(f"{b}.{s}", ps.delta(f"{b}.{s}"))
    # hands and fingers follow the wrist (rest locals)
    Rl = pe.Rl()
    for s in "LR":
        for n in hand_bones(pe.sk, s):
            if not n.startswith("wrist"):
                Rl[pe.k(n)] = pe.sk.rest_L[pe.k(n)]
    pe.set_locals(Rl)
    if lean_deg:
        pe.rotate("spine05", axis_angle(np.array([1.0, 0, 0]), np.radians(lean_deg)))


def settle_seat_and_feet(pe, spec, iters=3):
    """Root height so the buttocks rest on the seat; leg IK so the feet stand flat on the floor under the knees."""
    sk = pe.sk
    seat_y, R = spec.get("seat_y", 0.60), 0.165
    for _ in range(iters):
        hc = (pe.head("upperleg01.L") + pe.head("upperleg01.R")) / 2
        X = pe.skin("trousers")
        m = (np.abs(X[:, 0]) < 0.17) & (X[:, 2] > hc[2] - 0.16) & (X[:, 2] < hc[2] + 0.05)
        low = float(X[m, 1].min())
        pe.root[1] += seat_y - spec.get("sink", 0.004) - low
        for s, sg in (("L", 1), ("R", -1)):
            hip = pe.head(f"upperleg01.{s}")
            L1 = np.linalg.norm(pe.head(f"lowerleg01.{s}") - hip)
            L2 = np.linalg.norm(pe.head(f"foot.{s}") - pe.head(f"lowerleg01.{s}"))
            ya = sk.H[sk.ix[f"foot.{s}"]][1] + spec.get("ankle_lift", 0.0) + pe.__dict__.setdefault("_sole", {"L": 0.0, "R": 0.0})[s]
            xa = sg * spec.get("ankle_x", 0.16)
            # shin leaning forward by shin_deg: knee above/behind the ankle
            sh = np.radians(spec.get("shin_deg", 4.0))
            ky = ya + L2 * np.cos(sh)
            kx = sg * spec.get("knee_x", 0.15)
            dz = np.sqrt(max(L1 ** 2 - (ky - hip[1]) ** 2 - (kx - hip[0]) ** 2, 1e-6))
            kz = hip[2] + dz
            za = kz + L2 * np.sin(sh)
            leg_ik(pe, s, [xa, ya, za], [kx - (hip[0] + xa) / 2, 0.0, 1.0])
            toe_out = np.radians(spec.get("toe_out_deg", 7.0)) * sg
            for n in ["foot"] + [f"toe{t}-{k}" for t in range(1, 6) for k in range(1, 4)]:
                if f"{n}.{s}" in sk.ix:
                    pe.set_delta(f"{n}.{s}", rot_y(toe_out))
        S = pe.skin("shoes")
        P0 = sk.parts["shoes"][0]
        for s, sg in (("L", 1), ("R", -1)):     # the lowest sole vertex of each shoe onto the floor
            pe._sole[s] -= float(S[P0[:, 0] * sg > 0, 1].min())
    return low


def author_sit_stool_upright(sk, spec):
    pe, ps, D_pel = seated_base(sk, spec)
    upright_upper(pe, ps, D_pel, lean_deg=spec.get("lean_deg", 2.0))
    settle_seat_and_feet(pe, spec)
    # hands on the thighs: the palm on the top of the thigh at hand_u of hip -> knee, fingers along the thigh (turned a
    # little inward), the pinky side a little lower; solved on the left and mirrored (the coarse trouser mesh is not
    # symmetric); the height is iterated until the palms rest on the cloth (max penetration 0.5-5 mm, both hands)
    Ft = sk.faces["trousers"]
    Xt = pe.skin("trousers")
    hip, knee = pe.head("upperleg01.L"), pe.head("lowerleg01.L")
    p = hip + spec.get("hand_u", 0.6) * (knee - hip)
    top = surface_below(Xt, Ft, p)
    dth = (knee - hip) / np.linalg.norm(knee - hip)
    up = np.array([0.0, 1, 0])
    n_surf = up - dth * float(up @ dth)
    n_surf /= np.linalg.norm(n_surf)
    frames = {}
    for s, sg in (("L", 1), ("R", -1)):
        M = np.diag([sg, 1.0, 1.0])
        along_t = rot_y(np.radians(spec.get("hand_yaw_in_deg", 14.0)) * (-sg)) @ (M @ dth)
        palm_t = axis_angle(along_t, np.radians(spec.get("hand_roll_deg", 8.0)) * sg) @ (-(M @ n_surf))
        frames[s] = (M @ top, M @ n_surf, along_t, palm_t)
    off, rep = {"L": 0.0, "R": 0.0}, {}
    hb = {s: part_verts_of_bones(sk, "skin", hand_bones(sk, s), 0.5) for s in "LR"}
    for it in range(8):
        taus, targets = {}, {}
        for s, sg in (("L", 1), ("R", -1)):
            tp, ns, along_t, palm_t = frames[s]
            wp, along, palm, centre = hand_rest_frame(sk, s)
            Rt = frame_rot(along, palm, along_t, palm_t)
            targets[s] = tp + ns * off[s] - Rt @ (centre - wp)
            arm_ik(pe, s, targets[s], [sg * spec.get("elbow_out", 0.55), -0.3, -1.0])
            taus[s] = orient_hand(pe, s, along_t, palm_t)
            Rl = pe.Rl()
            finger_curl(sk, Rl, s, spec.get("curl", [0.42, 0.46, 0.52, 0.58]), thumb=spec.get("thumb", 0.25))
            pe.set_locals(Rl)
        Xs, Xt = pe.skin("skin"), pe.skin("trousers")
        dd = {s: signed_depth(Xs[hb[s]], Xt, Ft) for s in "LR"}
        done = True
        for s in "LR":          # per-hand height (the cloth differs by a few mm left / right)
            dmin = float(dd[s].min())
            pen = max(0.0, -dmin)
            if not 0.0005 <= pen <= 0.005:
                done = False
                off[s] += (pen - 0.0025) if dmin < 0 else -(dmin + 0.0025)
        if done:
            break
    for s in "LR":
        el = pe.head(f"lowerarm01.{s}")
        u_, v_ = pe.head(f"upperarm01.{s}") - el, pe.head(f"wrist.{s}") - el
        rep[s] = dict(max_penetration_mm=round(max(0.0, -float(dd[s].min())) * 1000, 1), verts_inside=int((dd[s] < 0).sum()),
                      min_gap_mm=round(max(0.0, float(dd[s].min())) * 1000, 1), height_offset_mm=round(off[s] * 1000, 1),
                      forearm_twist_deg=round(taus[s], 1), iters=it + 1,
                      wrist_reach_error_mm=round(float(np.linalg.norm(pe.head(f"wrist.{s}") - targets[s])) * 1000, 1),
                      elbow_deg=round(float(np.degrees(np.arccos(np.clip(u_ @ v_ / np.linalg.norm(u_) / np.linalg.norm(v_), -1, 1)))), 1))
    return pe, dict(hands=rep)


def surface_below(X, F, p, h=0.3):
    """The highest point of a skinned surface straight below p + (0, h, 0) (ray cast)."""
    import trimesh
    m = trimesh.Trimesh(vertices=X, faces=F, process=False)
    loc, _, _ = m.ray.intersects_location([p + np.array([0.0, h, 0.0])], [[0.0, -1.0, 0.0]])
    if not len(loc):
        raise RuntimeError("no surface below %s" % p)
    return loc[np.argmax(loc[:, 1])]


def author_sit_stool_face_in_hands(sk, spec):
    pe0, ps, D_pel = seated_base(sk, spec)

    def flexed(trunk, neck):
        pe = PoseEdit(sk, pe0.Rl(), pe0.root)
        upright_upper(pe, ps, D_pel, lean_deg=0.0)
        for n, w in zip(("spine05", "spine04", "spine03", "spine02", "spine01"), spec.get("trunk_w", (0.26, 0.24, 0.2, 0.15, 0.15))):
            pe.rotate(n, axis_angle(np.array([1.0, 0, 0]), np.radians(trunk * w)))
        for n, w in zip(("neck01", "neck02", "neck03", "head"), (0.3, 0.25, 0.2, 0.25)):
            pe.rotate(n, axis_angle(np.array([1.0, 0, 0]), np.radians(neck * w)))
        return pe

    # 2D search: trunk flexion x neck flexion so the elbows rest on the thighs with the least neck bend
    best = None
    for trunk in spec.get("trunk_search", np.arange(40.0, 92.0, 4.0)):
        for neck in spec.get("neck_search", np.arange(6.0, 34.0, 6.0)):
            pe = flexed(trunk, neck)
            settle_seat_and_feet(pe, spec, iters=1)
            res = place_face_hands(pe, spec, check=False)
            c = res["cost"] + spec.get("neck_cost", 0.003) * neck
            if best is None or c < best[0]:
                best = (c, trunk, neck)
    _, trunk, neck = best
    pe = flexed(trunk, neck)
    settle_seat_and_feet(pe, spec)
    res = place_face_hands(pe, spec, check=True)
    res.update(trunk_flexion_deg=float(trunk), neck_flexion_deg=float(neck))
    return pe, res


def place_face_hands(pe, spec, check=True):
    """Hands over the face: palms on the cheeks (fingers up over the brows toward the forehead), elbows toward the
    thighs. Returns the elbow-to-thigh residual as `cost` (the trunk search minimises it)."""
    sk = pe.sk
    ixh = pe.k("head")
    Rh = pe.Rw[ixh] @ sk.R[ixh].T          # head world delta
    fwd, upv = Rh @ np.array([0.0, 0, 1]), Rh @ np.array([0.0, 1, 0])
    eyes = {s: pe.head(f"eye.{s}") for s in "LR"}
    Xs_all = pe.skin("skin")
    face = part_verts_of_bones(sk, "skin", ["head", "jaw"] + [n for n in sk.names if n.startswith(("orbicularis", "oris", "levator", "risorius", "oculi", "special0", "temporalis"))], 0.5)
    Xf = Xs_all[face]
    Xt = pe.skin("trousers")
    cost, rep = 0.0, {}
    for s, sg in (("L", 1), ("R", -1)):
        e = eyes[s]
        lat = Rh @ np.array([sg * 1.0, 0, 0])
        # cheek point: below and outside the eye; the face surface there (the most forward face vertex near the ray)
        c0 = e + lat * spec.get("cheek_out", 0.012) - upv * spec.get("cheek_down", 0.035)
        rel = Xf - c0
        perp = rel - np.outer(rel @ fwd, fwd)
        near = np.linalg.norm(perp, axis=1) < 0.012
        surf = Xf[near][np.argmax((Xf[near] - c0) @ fwd)] if near.any() else c0
        along_t = rot_y(0) @ (upv * np.cos(np.radians(spec.get("finger_in_deg", 12.0))) - lat * np.sin(np.radians(spec.get("finger_in_deg", 12.0))))
        palm_t = -(fwd * np.cos(np.radians(spec.get("palm_out_deg", 25.0))) - lat * np.sin(np.radians(spec.get("palm_out_deg", 25.0))))
        palm_t = palm_t - along_t * float(palm_t @ along_t)
        palm_t /= np.linalg.norm(palm_t)
        # elbow pole: down toward the knee of the same side
        knee = pe.head(f"lowerleg01.{s}")
        off = 0.004
        hb = part_verts_of_bones(sk, "skin", hand_bones(sk, s), 0.5)
        for it in range(6 if check else 1):
            wp, along, palm, centre = hand_rest_frame(sk, s)
            Rt = frame_rot(along, palm, along_t, palm_t)
            target = surf - palm_t * off - Rt @ (centre - wp)
            sh = pe.head(f"upperarm01.{s}")
            pole = knee + np.array([sg * spec.get("elbow_x", 0.0), 0, -0.06]) - (sh + target) / 2
            arm_ik(pe, s, target, pole)
            tau = orient_hand(pe, s, along_t, palm_t)
            Rl = pe.Rl()
            finger_curl(sk, Rl, s, spec.get("curl", [0.18, 0.2, 0.24, 0.28]), thumb=spec.get("thumb", 0.1))
            pe.set_locals(Rl)
            if not check:
                break
            Xs = pe.skin("skin")
            # hand vs face: nearest face vertex, signed along the face's forward direction (negative = inside)
            H_ = Xs[hb]
            from scipy.spatial import cKDTree
            Xf = Xs[face]
            tr = cKDTree(Xf)
            dist, j = tr.query(H_)
            sgn = np.einsum("ij,j->i", H_ - Xf[j], fwd)
            pen = float(max(0.0, -(sgn[dist < 0.02]).min())) if (dist < 0.02).any() else 0.0
            gap = float(dist.min())
            if pen <= 0.006 and gap <= 0.004:
                break
            off += (pen - 0.003) if pen > 0.006 else -(gap - 0.002)
        el = pe.head(f"lowerarm01.{s}")
        # the thigh as a tapered cylinder along hip -> knee: its top under the elbow, and the elbow's lateral offset
        hip = pe.head(f"upperleg01.{s}")
        ax = knee - hip
        u = float(np.clip((el - hip) @ ax / (ax @ ax), 0.0, 1.0))
        a = hip + u * ax
        top = a[1] + (0.082 - 0.022 * u)
        r_el = spec.get("elbow_radius", 0.042)
        reach = float(np.linalg.norm(pe.head(f"wrist.{s}") - target))
        cost += abs(el[1] - (top + r_el)) + max(0.0, abs(el[0] - a[0]) - 0.035) \
            + 0.5 * max(0.0, el[2] - (knee[2] + 0.02)) + 0.5 * max(0.0, (knee[2] - 0.16) - el[2]) + 5 * reach
        rep[s] = dict(elbow=el.round(3).tolist(), thigh_top=round(float(top), 3), elbow_above_thigh_cm=round((el[1] - top) * 100, 1),
                      wrist_reach_error_mm=round(reach * 1000, 1), forearm_twist_deg=round(tau, 1))
        if check:
            rep[s].update(hand_face_penetration_mm=round(pen * 1000, 1), hand_face_gap_mm=round(gap * 1000, 1))
    return dict(cost=float(cost), hands=rep)


POSES = {
    "sit_stool_upright": author_sit_stool_upright,
    "sit_stool_face_in_hands": author_sit_stool_face_in_hands,
}


def build_pose(sk, c, titles):
    t_start = time.time()
    spec = c["pose"]
    pe, rep = POSES[spec["kind"]](sk, spec)
    Rl = pe.Rl()
    root = pe.root
    hc = (pe.head("upperleg01.L") + pe.head("upperleg01.R")) / 2
    # stool: under the buttocks, pushed back until the seat's front edge cuts the thighs by <= seat_cut (soft tissue)
    seat_y, R = spec.get("seat_y", 0.60), 0.165
    X = pe.skin("trousers")
    best = None
    for zc in np.arange(hc[2] + 0.04, hc[2] - 0.12, -0.005):
        m = np.hypot(X[:, 0], X[:, 2] - zc) < R
        cut = float(max(0.0, seat_y - X[m, 1].min())) if m.any() else 0.0
        low_inside = float(np.hypot(0, X[m, 2][np.argmin(X[m, 1])] - zc)) if m.any() else 1.0
        if best is None or (cut <= spec.get("seat_cut", 0.012) and best[1] > spec.get("seat_cut", 0.012)):
            best = (zc, cut, low_inside)
        if cut <= spec.get("seat_cut", 0.012):
            best = (zc, cut, low_inside)
            break
    zc, cut, _ = best
    m = np.hypot(X[:, 0], X[:, 2] - zc) < R
    buttock_gap = float(X[m, 1].min() - seat_y)
    feet = feet_report(pe)
    Rw, Hw = sk.fk(Rl[None], root[None])
    low = float(lowest_points(sk, Rw, Hw)[0])
    anim = [k for k in range(len(sk.names)) if k == 0 or
            np.degrees(np.arccos(np.clip((np.trace(sk.rest_L[k].T @ Rl[k]) - 1) / 2, -1, 1))) > 0.01]
    Q = m2q(Rl[anim])
    data = np.concatenate([root, Q.reshape(-1)])[None].astype(np.float32)
    MOTION.mkdir(parents=True, exist_ok=True)
    (MOTION / f"{c['name']}.bin").write_bytes(data.tobytes())
    src = c["pose"].get("src", "sit_stool_head_bowed")
    info = dict(
        name=c["name"], file=f"{c['name']}.bin", category=c["cat"], shows=c["shows"], frames=1, fps=FPS,
        seconds=round(1 / FPS, 4), loop=False, loop_info=None, bones=[sk.names[k].replace(".", "") for k in anim],
        root_motion=dict(path_m=0.0, net_m=0.0, turn_deg=0.0, mean_speed_mps=0.0),
        source=dict(authored_from=src, frame_s=spec["t"], method="motion_lib.py POSES['%s']" % spec["kind"]),
        props=dict(stool=dict(x=0.0, z=round(float(zc), 4), seat_y=seat_y, seat_d=0.33,
                              note="clip space (before any place / yaw): seat centre under the buttocks")),
        apply_note="fingers are baked into the pose: apply without the avatar.js hands layer",
        checks=dict(lowest_point_m=round(low, 4), feet=feet, seat=dict(front_edge_cut_cm=round(cut * 100, 2),
                    buttock_gap_cm=round(buttock_gap * 100, 2)), **rep),
        build_s=round(time.time() - t_start, 1),
    )
    return info


# ------------------------------------------------------------------------------------------------ planted feet
def plant_feet(sk, Rl, root, iters=3):
    """Standing clips: both soles flat on the floor. The floor pass only grounds the lowest point and the foot lock
    pins each foot where it rests, so a foot that hovers in the capture (stand_breathe_loop: the right foot 4 cm up)
    stays in the air. Each foot is turned flat (yaw kept); the body comes down until the lower sole touches y = 0 and
    the other ankle is lowered by leg IK onto the floor; one correction per pass for the whole clip (medians), so a
    loop stays seamless. Returns Rl, root, report."""
    ix = sk.ix
    P, J, W = sk.parts["shoes"]
    root = root.copy()
    sides = {s: P[:, 0] * sg > 0 for s, sg in (("L", 1), ("R", -1))}
    toes = {s: [c for c in range(len(sk.names)) if sk.names[c].startswith("toe") and sk.names[c].endswith("." + s)] for s in "LR"}

    def lows():
        Rw, Hw = sk.fk(Rl, root)
        return {s: float(np.median(sk.skin(Rw, Hw, P[m], J[m], W[m])[:, :, 1].min(1))) for s, m in sides.items()}

    before = lows()
    for s in "LR":                       # flatten (keep the yaw of the foot's world delta; toes flat with it)
        Rw, _ = sk.fk(Rl, root)
        kf = ix[f"foot.{s}"]
        f = (Rw[:, kf] @ sk.R[kf].T)[:, :, 2]
        Ry = np.stack([rot_y(a) for a in np.arctan2(f[:, 0], f[:, 2])])
        Rw2 = Rw.copy()
        for k in [kf] + toes[s]:
            Rw2[:, k] = Ry @ sk.R[k]
        Rl2 = sk.locals_(Rw2)
        for k in [kf] + toes[s]:
            Rl[:, k] = Rl2[:, k]
    for _ in range(iters):
        lo = lows()
        root[:, 1] -= min(lo.values())
        lo = lows()
        for s in "LR":
            if lo[s] < 0.0005:
                continue
            Rw, Hw = sk.fk(Rl, root)
            ua, ub, la, lb, ft = (ix[f"upperleg01.{s}"], ix[f"upperleg02.{s}"], ix[f"lowerleg01.{s}"], ix[f"lowerleg02.{s}"], ix[f"foot.{s}"])
            A, K, C = Hw[:, ua], Hw[:, la], Hw[:, ft]
            R1, R2 = two_bone_ik(A, K, C, C - np.array([0.0, lo[s], 0.0]), K - (A + C) / 2)
            Rw2 = Rw.copy()
            for b_ in (ua, ub):
                Rw2[:, b_] = R1 @ Rw[:, b_]
            for b_ in (la, lb):
                Rw2[:, b_] = R2 @ R1 @ Rw[:, b_]
            Rw2[:, ft] = Rw[:, ft]
            Rl_new = sk.locals_(Rw2)
            for b_ in (ua, ub, la, lb, ft):
                Rl[:, b_] = Rl_new[:, b_]
    after = lows()
    return Rl, root, {s: dict(hover_before_cm=round(before[s] * 100, 2), hover_after_cm=round(after[s] * 100, 2)) for s in "LR"}


# ------------------------------------------------------------------------------------------------ symmetric gait
def mirror_partner(sk):
    """Index of each bone's mirror (L <-> R), or itself for bones on the midline."""
    out = []
    for n in sk.names:
        m = n[:-2] + (".R" if n.endswith(".L") else ".L") if n.endswith((".L", ".R")) else n
        out.append(sk.ix.get(m, sk.ix[n]))
    return np.array(out)


def sample_frames(Rl, root, fr):
    """Local rotations / root at fractional frame positions fr (slerp / lerp between neighbours)."""
    f0 = np.floor(fr).astype(int)
    a = fr - f0
    f1 = np.minimum(f0 + 1, len(Rl) - 1)
    D = np.swapaxes(Rl[f0], -1, -2) @ Rl[f1]
    Rs = Rl[f0] @ rot_exp(a[:, None, None] * rot_log(D))
    Ps = root[f0] + (root[f1] - root[f0]) * a[:, None]
    return Rs, Ps


def symmetric_cycle(sk, Rl, root, delta, keep="L"):
    """A perfectly symmetric gait cycle: the half-cycle from a `keep` heel strike to the next opposite strike, then its
    mirror image (left <-> right) for the second half. Both steps then last exactly half a cycle, so a uniform time
    scale lands every heel strike on a beat grid, and both feet get the kept side's stance (heel planted). The seam
    at the half junction is closed by a linear correction over the first half. Returns Rl, root, delta, info."""
    N = len(Rl)
    R3 = np.concatenate([Rl, Rl, Rl], 0)
    P3 = np.concatenate([root, root + delta, root + 2 * delta], 0)
    Rw3, Hw3 = sk.fk(R3, P3)
    st = heel_strikes(sk, Rw3, Hw3, FPS)
    other = "R" if keep == "L" else "L"
    a = next(e["t"] for e in st if e["foot"] == keep and e["t"] >= N / FPS)
    b = next(e["t"] for e in st if e["foot"] == other and e["t"] > a)
    H = int(round((b - a) * FPS))
    fr = a * FPS + (b - a) * FPS * np.arange(H + 1) / H          # H + 1 samples: a .. b inclusive
    Rh, Ph = sample_frames(R3, P3, fr)
    mp = mirror_partner(sk)

    def mirror(Rloc, P):
        Rw, _ = sk.fk(Rloc, P)
        Dw = Rw @ np.swapaxes(sk.R, -1, -2)[None]
        Dm = M_X[None, None] @ Dw[:, mp] @ M_X[None, None]
        return sk.locals_(Dm @ sk.R[None])

    xc = (Ph[0, 0] + Ph[H, 0]) / 2
    # seam: the pose at b must equal the mirror of the pose at a -> correct the first half linearly
    tgt = mirror(Rh[:1], Ph[:1])[0]
    res = tgt @ np.swapaxes(Rh[H], -1, -2)
    rv = rot_log(res)
    w = np.arange(H + 1) / H
    Rh = rot_exp(w[:, None, None] * rv[None]) @ Rh
    Ph = Ph.copy()
    Ph[:, 1] += w * (Ph[0, 1] - Ph[H, 1])
    first_R, first_P = Rh[:H], Ph[:H]
    sec_R = mirror(first_R, first_P)
    sec_P = first_P.copy()
    sec_P[:, 0] = 2 * xc - first_P[:, 0]
    sec_P[:, 2] = first_P[:, 2] + (Ph[H, 2] - Ph[0, 2])
    Rl2 = np.concatenate([first_R, sec_R], 0)
    P2 = np.concatenate([first_P, sec_P], 0)
    d_half = Ph[H] - Ph[0]
    delta2 = np.array([0.0, 0.0, 2 * d_half[2]])
    P2[:, [0, 2]] -= P2[0, [0, 2]]
    return Rl2, P2, delta2, dict(kept=keep, half_frames=H, source_half_s=round(b - a, 4),
                                 seam_residual_deg=round(float(np.degrees(np.linalg.norm(rv, axis=-1).max())), 2))


# ------------------------------------------------------------------------------------------------ build
def build_clip(sk, c, titles):
    if c.get("pose"):
        return build_pose(sk, c, titles)
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
        if c.get("symmetric"):
            Rl, root, delta, sym = symmetric_cycle(sk, Rl, root, delta, keep=c["symmetric"])
            loop.update(cycle_s=round(len(Rl) / FPS, 4), symmetric=sym,
                        cycle_root_delta=[round(float(delta[0]), 4), 0.0, round(float(delta[2]), 4)])
        N = len(Rl)
        Rl3 = np.concatenate([Rl, Rl, Rl], 0)
        root3 = np.concatenate([root, root + delta, root + 2 * delta], 0)
        if c.get("footlock"):
            Rl3, fl_rep = foot_lock_iter(sk, Rl3, root3, FPS, cth=cth)
        if c.get("floor", "contact") == "contact":
            root3 = floor_contact(sk, Rl3, root3)
        Rl = Rl3[N:2 * N].copy()
        root = root3[N:2 * N] - delta
        if c.get("plant"):
            Rl, root, plant_rep = plant_feet(sk, Rl, root)
            loop["plant_feet"] = plant_rep
        Rw, Hw = sk.fk(Rl, root)
        R3 = np.concatenate([Rl, Rl, Rl], 0)
        P3 = np.concatenate([root, root + delta, root + 2 * delta], 0)
        Rw3, Hw3 = sk.fk(R3, P3)
        slide = sliding_stats(sk, Rw3, Hw3, FPS, cth)
        # heel strikes of the middle copy, folded into one cycle
        strikes = [dict(foot=e["foot"], t=round(e["t"] - N / FPS, 4)) for e in heel_strikes(sk, Rw3, Hw3, FPS)
                   if N / FPS <= e["t"] < 2 * N / FPS] if c["cat"] in ("walk", "run") else None
    else:
        if c.get("footlock"):
            Rl, fl_rep = foot_lock_iter(sk, Rl, root, FPS, cth=cth)
        if c.get("floor", "contact") == "contact":
            root = floor_contact(sk, Rl, root)
        Rw, Hw = sk.fk(Rl, root)
        slide = sliding_stats(sk, Rw, Hw, FPS, cth)
        strikes = heel_strikes(sk, Rw, Hw, FPS) if c["cat"] in ("walk", "run") else None
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
    if strikes is not None:
        info["gait"] = dict(heel_strikes=strikes,
                            note="clip seconds at speed 1 (loops: within one cycle); heel below planted height + 1.2 cm "
                                 "after a swing above + 3 cm, from the skinned shoe heel vertex")
    if loop:
        info["loop_info"]["note"] = "chain cycles: cycle k starts at k * cycle_root_delta (heading unchanged)"
        # gait period: count ball contacts of one foot per cycle
        fp = foot_points(sk)
        T = track_points(sk, Rw, Hw, [fp["L"][1]])[:, 0]
        n_steps = len([s for s in spans(contacts(T, FPS)) if s[1] - s[0] >= 2])
        info["loop_info"]["left_foot_contacts_per_cycle"] = n_steps
        if strikes:     # step period = cycle / heel strikes per cycle (both feet)
            info["loop_info"]["step_period_s"] = round(F / FPS / len(strikes), 4)
            info["loop_info"]["step_intervals_s"] = [round(b["t"] - a["t"], 4) for a, b in zip(strikes, strikes[1:] + [
                dict(t=strikes[0]["t"] + F / FPS)])]
        elif n_steps:
            info["loop_info"]["step_period_s"] = round(F / FPS / (2 * n_steps), 4)
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "build", "list"])
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    if a.cmd == "list":
        for c in CLIPS:
            print(f"{c['name']:28s} {c.get('cmu', 'pose'):7s} {c.get('seg', c.get('pose', {}).get('src', ''))}  {c['shows']}")
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
        if c.get("pose"):
            print(f"{c['name']:28s} pose bones={len(info['bones']):3d} {json.dumps({k: v for k, v in ch.items()})}  ({info['build_s']}s)",
                  flush=True)
        else:
            print(f"{c['name']:28s} {info['seconds']:6.2f}s bones={len(info['bones']):3d} path={info['root_motion']['path_m']:5.2f}m "
                  f"low[{ch['lowest_point_m']['min']:+.3f},{ch['lowest_point_m']['max']:+.3f}] slide p90={ch['foot_slide']['p90_cm']}cm "
                  f"max={ch['foot_slide']['max_cm']}cm loop={info['loop_info']['cycle_s'] if info['loop'] else '-'}"
                  f"{'  strikes=' + str([(e['foot'], e['t']) for e in info['gait']['heel_strikes']]) if info.get('gait') and info['loop'] else ''}"
                  f"  ({info['build_s']}s)", flush=True)
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
