"""MakeHuman default skeleton (163 bones, CC0) fitted to a morphed hm08 mesh, plus skin weights and FK posing.

Conventions (shared with body/retarget_mh.py so retargeted clips drop straight onto the exported GLB):
  * world = MakeHuman mesh space scaled to metres: Y up, character faces +Z, x = character's left.
  * joint positions = mean of the .mhskel joint vertices on the *morphed* mesh (MakeHuman 1.1 behaviour).
  * bone frame = Blender's vec_roll_to_mat3(head, tail, roll) with the MPFB2 rig.default.json roll,
    expressed in the Y-up world:  R = C @ R_blender  (columns = bone X, Y (along the bone), Z).
  * weights = MPFB2 weights.default.json (CC0), normalised per vertex; proxies get MakeHuman's
    reference-vertex blend (negative barycentric contributions dropped, as in apps/proxy.py).

    rig = Rig.from_mesh(v_dm)                     # v_dm: (19158,3) morphed base verts, decimetres
    W   = rig.body_weights()                      # (19158, 163) dense, rows sum to 1 (0 for unweighted)
    Wp  = rig.proxy_weights(proxy, W)             # (Np, 163)
    D, H = rig.fk(rig.pose_stand())               # posed world rotations / heads
    Vp  = rig.skin(V, W4idx, W4, D, H)            # linear blend skinning
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from mh_assets import CACHE, GH_DATA

MHSKEL = CACHE / GH_DATA / "rigs/default.mhskel"
MPFB_RIG = CACHE / "gh/mpfb2/src/mpfb/data/rigs/standard/rig.default.json"
MPFB_WEIGHTS = CACHE / "gh/mpfb2/src/mpfb/data/rigs/standard/weights.default.json"

C = np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]])  # Blender (Z up, -Y forward) -> Y up, +Z forward


def axis_angle(axis, ang):
    axis = np.asarray(axis, float)
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def min_rot(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    s, c = np.linalg.norm(v), float(np.dot(a, b))
    if s < 1e-9:
        return np.eye(3)
    return axis_angle(v, np.arctan2(s, c))


def blender_bone_matrix(head, tail, roll):
    """Blender vec_roll_to_mat3 (Blender coordinates): columns = bone X, Y (along bone), Z."""
    nor = np.asarray(tail, float) - np.asarray(head, float)
    nor = nor / np.linalg.norm(nor)
    x, y, z = nor
    theta = 1.0 + y
    theta_alt = x * x + z * z
    if theta > 1e-4 or theta_alt > 1e-12:
        if theta <= 1e-4:
            theta = theta_alt * 0.5 + theta_alt * theta_alt * 0.125
        B = np.column_stack([(1 - x * x / theta, -x, -x * z / theta), (x, y, z),
                             (-x * z / theta, -z, 1 - z * z / theta)])
    else:
        B = np.diag([-1.0, -1.0, 1.0])
    return axis_angle(nor, roll) @ B


def mat_to_quat(M):
    """(...,3,3) rotation -> (...,4) quaternion xyzw (glTF order)."""
    M = np.asarray(M, float)
    w = np.sqrt(np.maximum(0, 1 + M[..., 0, 0] + M[..., 1, 1] + M[..., 2, 2])) / 2
    x = np.sqrt(np.maximum(0, 1 + M[..., 0, 0] - M[..., 1, 1] - M[..., 2, 2])) / 2
    y = np.sqrt(np.maximum(0, 1 - M[..., 0, 0] + M[..., 1, 1] - M[..., 2, 2])) / 2
    z = np.sqrt(np.maximum(0, 1 - M[..., 0, 0] - M[..., 1, 1] + M[..., 2, 2])) / 2
    x = np.copysign(x, M[..., 2, 1] - M[..., 1, 2])
    y = np.copysign(y, M[..., 0, 2] - M[..., 2, 0])
    z = np.copysign(z, M[..., 1, 0] - M[..., 0, 1])
    q = np.stack([x, y, z, w], -1)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


@dataclass
class Rig:
    names: list            # bone names, parents first
    parent: np.ndarray     # (B,) int, -1 for root
    head: np.ndarray       # (B,3) metres, world (Y up)
    tail: np.ndarray       # (B,3)
    R: np.ndarray          # (B,3,3) rest bone frames in world
    roll: np.ndarray       # (B,) MPFB roll (radians, Blender convention)

    @property
    def index(self):
        return {n: i for i, n in enumerate(self.names)}

    # ------------------------------------------------------------------ build
    @classmethod
    def from_mesh(cls, v_dm: np.ndarray, mhskel=MHSKEL, mpfb_rig=MPFB_RIG):
        sk = json.loads(Path(mhskel).read_text())
        mp = json.loads(Path(mpfb_rig).read_text())
        J = {k: v_dm[np.asarray(idx)].mean(0) * 0.1 for k, idx in sk["joints"].items()}
        bones = sk["bones"]
        order, seen = [], set()

        def visit(n):
            if n in seen:
                return
            p = bones[n]["parent"]
            if p:
                visit(p)
            seen.add(n)
            order.append(n)

        for n in sorted(bones):
            visit(n)
        ix = {n: i for i, n in enumerate(order)}
        head = np.array([J[bones[n]["head"]] for n in order])
        tail = np.array([J[bones[n]["tail"]] for n in order])
        roll = np.array([float(mp[n]["roll"]) for n in order])
        R = np.stack([C @ blender_bone_matrix(C.T @ h, C.T @ t, r) for h, t, r in zip(head, tail, roll)])
        parent = np.array([ix[bones[n]["parent"]] if bones[n]["parent"] else -1 for n in order])
        return cls(order, parent, head, tail, R, roll)

    def translated(self, d):
        return Rig(self.names, self.parent, self.head + d, self.tail + d, self.R, self.roll)

    # ---------------------------------------------------------------- weights
    def body_weights(self, n_verts=19158, path=MPFB_WEIGHTS):
        wj = json.loads(Path(path).read_text())["weights"]
        W = np.zeros((n_verts, len(self.names)))
        ix = self.index
        for b, lst in wj.items():
            if not lst:
                continue
            a = np.asarray(lst, float)
            np.add.at(W[:, ix[b]], a[:, 0].astype(int), a[:, 1])
        s = W.sum(1, keepdims=True)
        return np.where(s > 0, W / np.maximum(s, 1e-12), 0.0)

    def proxy_weights(self, proxy, W_body, own_weights: Path | None = None):
        """MakeHuman apps/proxy.py getVertexWeights: blend of the reference vertices' weights
        (negative barycentric parts dropped); a proxy's own .mhw file wins when present."""
        if own_weights is not None and Path(own_weights).exists():
            wj = json.loads(Path(own_weights).read_text())["weights"]
            W = np.zeros((len(proxy.ref), len(self.names)))
            ix = self.index
            for b, lst in wj.items():
                if lst:
                    a = np.asarray(lst, float)
                    np.add.at(W[:, ix[b]], a[:, 0].astype(int), a[:, 1])
        else:
            w = np.clip(proxy.w, 0, None)
            W = sum(W_body[proxy.ref[:, k]] * w[:, k:k + 1] for k in range(3))
        s = W.sum(1, keepdims=True)
        return np.where(s > 0, W / np.maximum(s, 1e-12), 0.0)

    # ------------------------------------------------------------------- pose
    def fk(self, E: dict | None = None):
        """World rotation deltas D (B,3,3) and posed heads H (B,3).
        E maps bone name -> extra rotation expressed in the REST world frame, applied about the bone head
        after its parent's motion:  D[b] = D[parent] @ E[b]."""
        E = E or {}
        ix = self.index
        B = len(self.names)
        D = np.zeros((B, 3, 3))
        H = np.zeros((B, 3))
        Ei = {ix[k]: v for k, v in E.items()}
        for b in range(B):
            p = self.parent[b]
            e = Ei.get(b, np.eye(3))
            if p < 0:
                D[b] = e
                H[b] = self.head[b]
            else:
                D[b] = D[p] @ e
                H[b] = H[p] + D[p] @ (self.head[b] - self.head[p])
        return D, H

    def local_trs(self, D=None, H=None):
        """glTF node TRS for every joint: translation in parent frame (rest), rotation (posed if D given)."""
        B = len(self.names)
        if D is None:
            D = np.repeat(np.eye(3)[None], B, 0)
        Rw = D @ self.R
        t = np.zeros((B, 3))
        q = np.zeros((B, 4))
        for b in range(B):
            p = self.parent[b]
            if p < 0:
                t[b] = self.head[b] if H is None else H[b]
                q[b] = mat_to_quat(Rw[b])
            else:
                t[b] = self.R[p].T @ (self.head[b] - self.head[p])
                q[b] = mat_to_quat(Rw[p].T @ Rw[b])
        return t, q

    def inverse_bind(self):
        M = np.tile(np.eye(4), (len(self.names), 1, 1))
        M[:, :3, :3] = np.transpose(self.R, (0, 2, 1))
        M[:, :3, 3] = -np.einsum("bji,bj->bi", self.R, self.head)
        return M

    @staticmethod
    def skin(V, idx, w, D, H, head_rest):
        """Linear blend skinning with top-k weights. V (N,3), idx/w (N,k)."""
        T = H - np.einsum("bij,bj->bi", D, head_rest)          # (B,3)
        out = np.zeros_like(V)
        for k in range(idx.shape[1]):
            b = idx[:, k]
            out += w[:, k:k + 1] * (np.einsum("nij,nj->ni", D[b], V) + T[b])
        return out

    # ------------------------------------------------------------- stand pose
    def pose_stand(self, arm_out_deg=6.0, arm_fwd_deg=3.0, elbow_deg=12.0, wrist_deg=0.0,
                   palm_back_deg=10.0, twist_split=0.5, finger_curl_deg=(6.0, 12.0, 7.0), thumb_deg=6.0,
                   finger_close=0.7, thumb_close=0.6, shoulder_drop_deg=2.0, shoulder_share=0.5,
                   leg_in_deg=2.5, toe_out_deg=6.0):
        """Relaxed standing pose built from MakeHuman's A-pose rest (upper arms ~49 deg below horizontal,
        elbows already bent ~45 deg forward).  Each arm segment is AIMED at a world target (not rotated additively): upper arm
        hangs slightly out/forward, soft elbow, palm faces the thigh (turned a little back), fingers
        loosely curled; legs come in a little with the feet kept flat and turned out.
        Returns {bone: rest-frame rotation} for fk()."""
        ix = self.index
        E = {}
        fwd = np.array([0.0, 0.0, 1.0])
        up = np.array([0.0, 1.0, 0.0])

        def D_of(name):
            return self.fk(E)[0][ix[name]]

        def unit(x):
            return x / np.linalg.norm(x)

        for s, sx in (("L", 1.0), ("R", -1.0)):
            hd = lambda n: self.head[ix[f"{n}.{s}"]]  # noqa: E731
            if shoulder_drop_deg:
                E[f"clavicle.{s}"] = axis_angle(fwd, -sx * np.radians(shoulder_drop_deg))
            # upper arm
            a = hd("lowerarm01") - hd("upperarm01")
            out, fw = np.radians(arm_out_deg), np.radians(arm_fwd_deg)
            t_ua = np.array([sx * np.sin(out), -np.cos(out) * np.cos(fw), np.cos(out) * np.sin(fw)])
            # share part of the arm drop with shoulder01 (the deltoid/acromion bone): with linear blend
            # skinning a single 40 deg rotation at the gleno-humeral joint balloons the shoulder cap
            full = min_rot(a, D_of(f"shoulder01.{s}").T @ t_ua)
            ang_full = np.arccos(np.clip((np.trace(full) - 1) / 2, -1, 1))
            if shoulder_share > 0 and ang_full > 1e-6:
                axf = np.array([full[2, 1] - full[1, 2], full[0, 2] - full[2, 0], full[1, 0] - full[0, 1]])
                E[f"shoulder01.{s}"] = axis_angle(axf, shoulder_share * ang_full)
            E[f"upperarm01.{s}"] = min_rot(a, D_of(f"shoulder01.{s}").T @ t_ua)
            # forearm: bend forward from the upper arm by elbow_deg
            f = hd("wrist") - hd("lowerarm01")
            t_fa = axis_angle(np.cross(t_ua, fwd), np.radians(elbow_deg)) @ t_ua
            E[f"lowerarm01.{s}"] = min_rot(f, D_of(f"upperarm02.{s}").T @ t_fa)
            # palm normal in rest from the thumb side: with the palm on the thigh the thumb points forward,
            # which gives n = sx * (hand_dir x thumb_dir) for both hands
            h_rest = hd("finger3-1") - hd("wrist")
            th = hd("finger1-2") - hd("wrist")
            th = th - h_rest * (th @ h_rest) / (h_rest @ h_rest)
            n_rest = unit(sx * np.cross(h_rest, th))
            # forearm twist so the palm faces the thigh, turned palm_back_deg towards the back
            want = unit(np.array([-sx * np.cos(np.radians(palm_back_deg)), 0.0, -np.sin(np.radians(palm_back_deg))]))
            n_now = D_of(f"wrist.{s}") @ n_rest
            ax = unit(t_fa)
            pn = unit(n_now - ax * (n_now @ ax))
            pw = unit(want - ax * (want @ ax))
            ang = np.arctan2(np.cross(pn, pw) @ ax, pn @ pw)
            Dl_prev = E[f"lowerarm01.{s}"]
            # split the twist between the two forearm bones (less candy-wrapping)
            Dp = D_of(f"upperarm02.{s}")
            E[f"lowerarm01.{s}"] = Dp.T @ axis_angle(ax, ang * twist_split) @ Dp @ Dl_prev
            Dl = D_of(f"lowerarm01.{s}")
            E[f"lowerarm02.{s}"] = Dl.T @ axis_angle(ax, ang * (1 - twist_split)) @ Dl
            # hand: continue the forearm, flexed slightly towards the palm
            n_w = D_of(f"wrist.{s}") @ n_rest
            t_h = axis_angle(np.cross(t_fa, n_w), np.radians(wrist_deg)) @ unit(t_fa)
            Dw = D_of(f"lowerarm02.{s}")
            E[f"wrist.{s}"] = min_rot(h_rest, Dw.T @ t_h)
            # fingers: close the MakeHuman splay towards the middle finger (about the palm normal), then flex
            # towards the palm (rest-frame axes; the hand moves rigidly with the wrist)
            d3 = self.tail[ix[f"finger3-1.{s}"]] - self.head[ix[f"finger3-1.{s}"]]

            def adduct(d, target, frac):
                a_ = d - n_rest * (d @ n_rest)
                b_ = target - n_rest * (target @ n_rest)
                ang_ = np.arctan2(np.cross(a_, b_) @ n_rest, a_ @ b_)
                return axis_angle(n_rest, frac * ang_)

            for fi in range(2, 6):
                for k in range(1, 4):
                    b = f"finger{fi}-{k}.{s}"
                    d = self.tail[ix[b]] - self.head[ix[b]]
                    curl = np.radians(finger_curl_deg[k - 1] * (1 + 0.12 * (fi - 2)))
                    if k == 1 and fi != 3:
                        A = adduct(d, d3, finger_close)
                        E[b] = axis_angle(np.cross(A @ d, n_rest), curl) @ A
                    else:
                        E[b] = axis_angle(np.cross(d, n_rest), curl)
            d2 = self.tail[ix[f"finger2-1.{s}"]] - self.head[ix[f"finger2-1.{s}"]]
            for k in range(1, 4):
                b = f"finger1-{k}.{s}"
                d = self.tail[ix[b]] - self.head[ix[b]]
                if k == 1:  # thumb: swing towards the index finger in 3D (MakeHuman's rest thumb sticks out)
                    full = min_rot(d, d2 + 0.15 * np.linalg.norm(d2) * n_rest)
                    ang_ = np.arccos(np.clip((np.trace(full) - 1) / 2, -1, 1))
                    axf = np.array([full[2, 1] - full[1, 2], full[0, 2] - full[2, 0], full[1, 0] - full[0, 1]])
                    A = axis_angle(axf, thumb_close * ang_) if ang_ > 1e-6 else np.eye(3)
                    E[b] = axis_angle(np.cross(A @ d, n_rest), np.radians(thumb_deg)) @ A
                else:
                    E[b] = axis_angle(np.cross(d, n_rest), np.radians(thumb_deg))
            # legs: bring the feet in, turn them out a little, keep the soles flat
            R_in = axis_angle(fwd, -sx * np.radians(leg_in_deg))
            R_out = axis_angle(up, sx * np.radians(toe_out_deg))
            E[f"upperleg01.{s}"] = R_out @ R_in
            # D[foot] = D[lowerleg02] @ E_foot = (R_out R_in) E_foot  ->  want R_out (flat sole, toes out)
            E[f"foot.{s}"] = (R_out @ R_in).T @ R_out
        return E

    # -------------------------------------------------------------- export
    def to_mpfb_json(self):
        """Rig in MPFB2 rig.*.json layout (Blender coordinates, metres) so body/retarget_mh.py can use
        this exact body's rest skeleton instead of the MPFB default proportions."""
        out = {}
        for i, n in enumerate(self.names):
            p = self.parent[i]
            out[n] = {"head": {"default_position": (C.T @ self.head[i]).tolist()},
                      "tail": {"default_position": (C.T @ self.tail[i]).tolist()},
                      "roll": float(self.roll[i]), "parent": self.names[p] if p >= 0 else ""}
        return out


def top_k(W, k=4, eps=1e-4):
    """Dense (N,B) weights -> (N,k) indices and renormalised weights (glTF JOINTS_0/WEIGHTS_0)."""
    idx = np.argsort(-W, axis=1)[:, :k]
    w = np.take_along_axis(W, idx, 1)
    w = np.where(w > eps, w, 0.0)
    idx = np.where(w > 0, idx, 0)          # glTF: unused influence slots point at joint 0
    s = w.sum(1, keepdims=True)
    bad = s[:, 0] <= 0
    w = w / np.maximum(s, 1e-12)
    return idx.astype(np.int64), w, bad
