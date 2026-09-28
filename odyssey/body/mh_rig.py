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
    """(...,3,3) rotation -> (...,4) unit quaternion xyzw (glTF order), w >= 0.
    Shepperd's method: branch on the largest of w, x, y, z so the result is exact also near 180 deg
    (w ~ 0), where taking signs from near-zero matrix differences flips components at random."""
    M = np.asarray(M, float)
    shp = M.shape[:-2]
    M = M.reshape(-1, 3, 3)
    tr = M[:, 0, 0] + M[:, 1, 1] + M[:, 2, 2]
    cand = np.stack([tr, M[:, 0, 0], M[:, 1, 1], M[:, 2, 2]], 1)
    k = cand.argmax(1)
    q = np.zeros((len(M), 4))
    # w largest
    i = k == 0
    s = np.sqrt(np.maximum(1 + tr[i], 1e-12)) * 2
    q[i] = np.stack([(M[i, 2, 1] - M[i, 1, 2]) / s, (M[i, 0, 2] - M[i, 2, 0]) / s,
                     (M[i, 1, 0] - M[i, 0, 1]) / s, 0.25 * s], 1)
    # x largest
    i = k == 1
    s = np.sqrt(np.maximum(1 + M[i, 0, 0] - M[i, 1, 1] - M[i, 2, 2], 1e-12)) * 2
    q[i] = np.stack([0.25 * s, (M[i, 0, 1] + M[i, 1, 0]) / s, (M[i, 0, 2] + M[i, 2, 0]) / s,
                     (M[i, 2, 1] - M[i, 1, 2]) / s], 1)
    # y largest
    i = k == 2
    s = np.sqrt(np.maximum(1 - M[i, 0, 0] + M[i, 1, 1] - M[i, 2, 2], 1e-12)) * 2
    q[i] = np.stack([(M[i, 0, 1] + M[i, 1, 0]) / s, 0.25 * s, (M[i, 1, 2] + M[i, 2, 1]) / s,
                     (M[i, 0, 2] - M[i, 2, 0]) / s], 1)
    # z largest
    i = k == 3
    s = np.sqrt(np.maximum(1 - M[i, 0, 0] - M[i, 1, 1] + M[i, 2, 2], 1e-12)) * 2
    q[i] = np.stack([(M[i, 0, 2] + M[i, 2, 0]) / s, (M[i, 1, 2] + M[i, 2, 1]) / s, 0.25 * s,
                     (M[i, 1, 0] - M[i, 0, 1]) / s], 1)
    q = np.where(q[:, 3:4] < 0, -q, q)
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    return q.reshape(shp + (4,))


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
    def pose_stand(self, arm_out_deg=3.0, arm_fwd_deg=3.0, elbow_deg=14.0, forearm_in_deg=3.0, wrist_deg=0.0,
                   palm_back_deg=18.0, twist_split=0.5,
                   finger_curl_deg=((8.0, 14.0, 8.0), (10.0, 18.0, 10.0), (12.0, 22.0, 12.0), (15.0, 26.0, 14.0)),
                   thumb_curl_deg=(10.0, 12.0, 10.0), finger_close=1.0, finger_squeeze_deg=2.5, thumb_close=0.85,
                   shoulder_drop_deg=0.0, shoulder_share=0.25,
                   stance_half_width=0.095, toe_out_deg=7.0, straight_flex_deg=4.0,
                   weight_shift=1.0, weight_side="R", pelvis_roll_deg=2.6, pelvis_yaw_deg=3.0,
                   free_foot_fwd=0.045, free_foot_out=0.035, free_toe_out_deg=14.0, stand_foot_in=0.022,
                   spine_counter=1.5, head_tilt_deg=1.5, head_turn_deg=2.5):
        """Relaxed standing pose built from MakeHuman's A-pose rest (upper arms ~49 deg below horizontal,
        elbows already bent ~45 deg forward).  Each limb segment is AIMED at a world target (not rotated
        additively).

        Arms: hang close to the body with soft elbows, the palm faces the thigh (thumb forward), fingers
        closed together with a graded curl (index least, little finger most), thumb along the index.
        Legs: solved with two-bone IK to foot targets on the floor, knees bending over the toes.
        weight_shift in [0, 1] blends in a relaxed contrapposto: weight on `weight_side` (that leg nearly
        straight, its foot under the body), the pelvis rolls so the free hip drops and the free knee softens,
        the free foot sits a little forward and turned out; the spine counter-rolls (shoulders tilt the
        other way) and the head tilts / turns slightly.  weight_shift=0 gives the symmetric neutral stance
        that motion retargeting is calibrated on.  Returns {bone: rest-frame rotation} for fk()."""
        ix = self.index
        E = {}
        fwd = np.array([0.0, 0.0, 1.0])
        up = np.array([0.0, 1.0, 0.0])
        ws = float(weight_shift)

        def D_of(name):
            return self.fk(E)[0][ix[name]]

        def H_of(name):
            return self.fk(E)[1][ix[name]]

        def unit(x):
            return x / np.linalg.norm(x)

        def frame(a, b):
            """Orthonormal frame with first axis along a, second as close as possible to b."""
            e1 = unit(a)
            e2 = unit(b - e1 * (b @ e1))
            return np.column_stack([e1, e2, np.cross(e1, e2)])

        # ---- pelvis / spine / head (contrapposto): weight side sw = +1 (L) / -1 (R)
        sw = 1.0 if weight_side == "L" else -1.0
        roll = np.radians(pelvis_roll_deg) * ws
        # free hip (side -sw) drops: rotation about +z by angle sw*roll lifts +x when sw > 0
        E["root"] = axis_angle(up, -sw * np.radians(pelvis_yaw_deg) * ws) @ axis_angle(fwd, sw * roll)
        # counter-roll spread over the lumbar / thoracic spine: net chest roll = (1 - spine_counter) * roll
        for b, w in (("spine04", 0.3), ("spine03", 0.35), ("spine02", 0.35)):
            E[b] = axis_angle(fwd, -sw * roll * spine_counter * w) @ axis_angle(up, sw * np.radians(pelvis_yaw_deg) * ws * w)
        # neck brings the head back near level, with a slight tilt and turn
        chest_roll = sw * roll * (1 - spine_counter)
        head_roll = -chest_roll + np.radians(head_tilt_deg) * ws * sw
        for b, w in (("neck01", 0.35), ("neck02", 0.35), ("head", 0.3)):
            E[b] = axis_angle(up, -sw * np.radians(head_turn_deg) * ws * w) @ axis_angle(fwd, head_roll * w)

        for s, sx in (("L", 1.0), ("R", -1.0)):
            hd = lambda n: self.head[ix[f"{n}.{s}"]]  # noqa: E731
            if shoulder_drop_deg:
                E[f"clavicle.{s}"] = axis_angle(fwd, -sx * np.radians(shoulder_drop_deg))
            # upper arm
            a = hd("lowerarm01") - hd("upperarm01")
            out, fw = np.radians(arm_out_deg), np.radians(arm_fwd_deg)
            t_ua = np.array([sx * np.sin(out), -np.cos(out) * np.cos(fw), np.cos(out) * np.sin(fw)])
            # share part of the arm drop with shoulder01 (the deltoid/acromion bone): with linear blend
            # skinning a single 40 deg rotation at the gleno-humeral joint balloons the shoulder cap, but
            # a large share drops and narrows the shoulder line (wine-bottle slope); ~0.25 keeps it level
            full = min_rot(a, D_of(f"shoulder01.{s}").T @ t_ua)
            ang_full = np.arccos(np.clip((np.trace(full) - 1) / 2, -1, 1))
            if shoulder_share > 0 and ang_full > 1e-6:
                axf = np.array([full[2, 1] - full[1, 2], full[0, 2] - full[2, 0], full[1, 0] - full[0, 1]])
                E[f"shoulder01.{s}"] = axis_angle(axf, shoulder_share * ang_full)
            E[f"upperarm01.{s}"] = min_rot(a, D_of(f"shoulder01.{s}").T @ t_ua)
            # forearm: bend forward from the upper arm by elbow_deg, and a little in towards the thigh
            f = hd("wrist") - hd("lowerarm01")
            t_fa = axis_angle(np.cross(t_ua, fwd), np.radians(elbow_deg)) @ t_ua
            t_fa = axis_angle(fwd, sx * np.radians(forearm_in_deg)) @ t_fa
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
            # fingers: close the MakeHuman splay onto the middle finger (about the palm normal) and squeeze
            # them together a little more (they touch), then a graded flex towards the palm (index least,
            # little finger most) -- rest-frame axes; the hand moves rigidly with the wrist
            d3 = self.tail[ix[f"finger3-1.{s}"]] - self.head[ix[f"finger3-1.{s}"]]

            def adduct(d, target, frac, extra=0.0):
                a_ = d - n_rest * (d @ n_rest)
                b_ = target - n_rest * (target @ n_rest)
                ang_ = np.arctan2(np.cross(a_, b_) @ n_rest, a_ @ b_)
                return axis_angle(n_rest, frac * ang_ + np.sign(ang_) * extra)

            for fi in range(2, 6):
                for k in range(1, 4):
                    b = f"finger{fi}-{k}.{s}"
                    d = self.tail[ix[b]] - self.head[ix[b]]
                    curl = np.radians(finger_curl_deg[fi - 2][k - 1])
                    if k == 1 and fi != 3:
                        A = adduct(d, d3, finger_close, np.radians(finger_squeeze_deg) * (0.5 if fi == 4 else 1.0))
                        E[b] = axis_angle(np.cross(A @ d, n_rest), curl) @ A
                    else:
                        E[b] = axis_angle(np.cross(d, n_rest), curl)
            d2 = self.tail[ix[f"finger2-1.{s}"]] - self.head[ix[f"finger2-1.{s}"]]
            for k in range(1, 4):
                b = f"finger1-{k}.{s}"
                d = self.tail[ix[b]] - self.head[ix[b]]
                if k == 1:  # thumb: swing towards the index finger in 3D (MakeHuman's rest thumb sticks out)
                    full = min_rot(d, d2 + 0.2 * np.linalg.norm(d2) * n_rest)
                    ang_ = np.arccos(np.clip((np.trace(full) - 1) / 2, -1, 1))
                    axf = np.array([full[2, 1] - full[1, 2], full[0, 2] - full[2, 0], full[1, 0] - full[0, 1]])
                    A = axis_angle(axf, thumb_close * ang_) if ang_ > 1e-6 else np.eye(3)
                    E[b] = axis_angle(np.cross(A @ d, n_rest), np.radians(thumb_curl_deg[0])) @ A
                else:
                    E[b] = axis_angle(np.cross(d, n_rest), np.radians(thumb_curl_deg[k - 1]))

        # ---- legs: two-bone IK to foot targets on a common floor, knees over the toes, soles flat
        Dfk, Hfk = self.fk(E)
        L = {}
        for s in "LR":
            hip, kn, an = (self.head[ix[f"{n}.{s}"]] for n in ("upperleg01", "lowerleg01", "foot"))
            L[s] = (np.linalg.norm(kn - hip), np.linalg.norm(an - kn))
        ank_rest_z = self.head[ix["foot.L"]][2]

        def reach(s):   # hip -> ankle distance for a leg bent by straight_flex_deg
            l1, l2 = L[s]
            return np.sqrt(l1 ** 2 + l2 ** 2 + 2 * l1 * l2 * np.cos(np.radians(straight_flex_deg)))

        targets, yaws = {}, {}
        for s, sx in (("L", 1.0), ("R", -1.0)):
            hip = Hfk[ix[f"upperleg01.{s}"]]
            stand = (sx == sw)
            x = sx * stance_half_width
            z = ank_rest_z
            yaw = toe_out_deg
            if ws > 0:
                if stand:
                    x -= sx * stand_foot_in * ws
                else:
                    x += sx * free_foot_out * ws
                    z += free_foot_fwd * ws
                    yaw += (free_toe_out_deg - toe_out_deg) * ws
            targets[s] = np.array([x, np.nan, z])
            yaws[s] = yaw
        # floor height: the standing leg (both legs when neutral) reaches it with straight_flex_deg of bend
        ys = []
        for s in ("LR" if ws == 0 else ("L" if sw > 0 else "R")):
            hip = Hfk[ix[f"upperleg01.{s}"]]
            t = targets[s]
            ys.append(hip[1] - np.sqrt(max(reach(s) ** 2 - (t[0] - hip[0]) ** 2 - (t[2] - hip[2]) ** 2, 1e-6)))
        ank_y = min(ys)
        for s, sx in (("L", 1.0), ("R", -1.0)):
            targets[s][1] = ank_y
            hip = Hfk[ix[f"upperleg01.{s}"]]
            l1, l2 = L[s]
            T = targets[s]
            r = T - hip
            d = np.clip(np.linalg.norm(r), abs(l1 - l2) + 1e-4, 0.9995 * (l1 + l2))
            u = unit(r)
            R_out = axis_angle(up, sx * np.radians(yaws[s]))
            kf = R_out @ fwd                              # the knee bends over the toes
            v = unit(kf - u * (kf @ u))
            ca = np.clip((l1 ** 2 + d ** 2 - l2 ** 2) / (2 * l1 * d), -1, 1)
            knee = hip + l1 * (ca * u + np.sqrt(1 - ca ** 2) * v)
            ankle = hip + u * d
            hip0, kn0, an0 = (self.head[ix[f"{n}.{s}"]] for n in ("upperleg01", "lowerleg01", "foot"))
            W_th = frame(knee - hip, kf) @ frame(kn0 - hip0, fwd).T
            W_sh = frame(ankle - knee, kf) @ frame(an0 - kn0, fwd).T
            Dp = D_of(f"pelvis.{s}")
            E[f"upperleg01.{s}"] = Dp.T @ W_th
            E[f"lowerleg01.{s}"] = D_of(f"upperleg02.{s}").T @ W_sh
            E[f"foot.{s}"] = D_of(f"lowerleg02.{s}").T @ R_out
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
