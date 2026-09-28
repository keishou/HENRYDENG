"""Minimal BVH reader + vectorised forward kinematics (numpy only).

    from body.bvh import load_bvh
    clip = load_bvh("82_05.bvh")
    P = clip.world_positions()        # (F, J, 3) joint positions, BVH units
    R = clip.world_rotations()        # (F, J, 3, 3)

Conventions follow the BVH spec: a joint's CHANNELS list is applied in the
order written (e.g. "Zrotation Yrotation Xrotation" -> R = Rz @ Ry @ Rx),
local transform = translate(OFFSET [+ position channels]) * R, and a child's
world transform is parent_world * local.  End Sites are kept as extra
leaf joints named "<parent>_End" (no channels) so bones can be drawn.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Joint:
    name: str
    parent: int
    offset: np.ndarray
    channels: list = field(default_factory=list)
    chan_start: int = 0
    is_end: bool = False


@dataclass
class BVHClip:
    joints: list
    frames: np.ndarray  # (F, C) raw channel values
    frame_time: float
    path: str = ""

    # ---- metadata -------------------------------------------------------
    @property
    def names(self):
        return [j.name for j in self.joints]

    @property
    def parents(self):
        return np.array([j.parent for j in self.joints])

    @property
    def fps(self):
        return 1.0 / self.frame_time

    @property
    def n_frames(self):
        return self.frames.shape[0]

    def index(self, name):
        return self.names.index(name)

    def hierarchy_text(self, show_end=False):
        lines = []

        def rec(i, depth):
            j = self.joints[i]
            if j.is_end and not show_end:
                return
            ch = "".join(c[0] for c in j.channels if c.endswith("rotation"))
            pos = "+pos" if any(c.endswith("position") for c in j.channels) else ""
            lines.append("  " * depth + f"{j.name}" + (f"  [{ch}{pos}]" if ch else ""))
            for k, jj in enumerate(self.joints):
                if jj.parent == i:
                    rec(k, depth + 1)

        rec(0, 0)
        return "\n".join(lines)

    # ---- kinematics ------------------------------------------------------
    def local_rotations(self, frames=None):
        F = self.frames if frames is None else self.frames[frames]
        n = F.shape[0]
        out = np.tile(np.eye(3), (n, len(self.joints), 1, 1))
        for ji, j in enumerate(self.joints):
            R = np.tile(np.eye(3), (n, 1, 1))
            for k, ch in enumerate(j.channels):
                if not ch.endswith("rotation"):
                    continue
                a = np.deg2rad(F[:, j.chan_start + k])
                R = R @ _axis_rot(ch[0], a)
            out[:, ji] = R
        return out

    def local_translations(self, frames=None):
        F = self.frames if frames is None else self.frames[frames]
        n = F.shape[0]
        out = np.tile(np.stack([j.offset for j in self.joints])[None], (n, 1, 1)).astype(float)
        for ji, j in enumerate(self.joints):
            for k, ch in enumerate(j.channels):
                if ch.endswith("position"):
                    axis = "XYZ".index(ch[0])
                    out[:, ji, axis] = out[:, ji, axis] + F[:, j.chan_start + k]
        return out

    def world(self, frames=None):
        """Returns (positions (F,J,3), rotations (F,J,3,3))."""
        Rl = self.local_rotations(frames)
        Tl = self.local_translations(frames)
        n, J = Rl.shape[:2]
        Rw = np.empty_like(Rl)
        Pw = np.empty((n, J, 3))
        for ji, j in enumerate(self.joints):
            p = j.parent
            if p < 0:
                Rw[:, ji] = Rl[:, ji]
                Pw[:, ji] = Tl[:, ji]
            else:
                Rw[:, ji] = Rw[:, p] @ Rl[:, ji]
                Pw[:, ji] = Pw[:, p] + np.einsum("fij,fj->fi", Rw[:, p], Tl[:, ji])
        return Pw, Rw

    def world_positions(self, frames=None):
        return self.world(frames)[0]

    def world_rotations(self, frames=None):
        return self.world(frames)[1]


def _axis_rot(axis, a):
    c, s = np.cos(a), np.sin(a)
    o, z = np.ones_like(a), np.zeros_like(a)
    if axis == "X":
        m = [[o, z, z], [z, c, -s], [z, s, c]]
    elif axis == "Y":
        m = [[c, z, s], [z, o, z], [-s, z, c]]
    else:
        m = [[c, -s, z], [s, c, z], [z, z, o]]
    return np.moveaxis(np.array(m), (0, 1), (-2, -1))


def load_bvh(path) -> BVHClip:
    with open(path, "r", errors="replace") as fh:
        text = fh.read()
    head, _, motion = text.partition("MOTION")
    toks = re.findall(r"[^\s{}]+|[{}]", head)
    joints: list[Joint] = []
    stack: list[int] = []
    pending = None
    nchan = 0
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in ("ROOT", "JOINT"):
            name = toks[i + 1]
            pending = Joint(name, stack[-1] if stack else -1, np.zeros(3))
            i += 2
        elif t == "End":  # End Site
            par = stack[-1]
            pending = Joint(joints[par].name + "_End", par, np.zeros(3), is_end=True)
            i += 2
        elif t == "{":
            joints.append(pending)
            stack.append(len(joints) - 1)
            i += 1
        elif t == "}":
            stack.pop()
            i += 1
        elif t == "OFFSET":
            joints[stack[-1]].offset = np.array([float(x) for x in toks[i + 1:i + 4]])
            i += 4
        elif t == "CHANNELS":
            n = int(toks[i + 1])
            j = joints[stack[-1]]
            j.channels = toks[i + 2:i + 2 + n]
            j.chan_start = nchan
            nchan += n
            i += 2 + n
        else:
            i += 1
    m = re.search(r"Frames:\s*(\d+)", motion)
    ft = re.search(r"Frame Time:\s*([0-9.eE+-]+)", motion)
    nf = int(m.group(1))
    body = motion[ft.end():]
    vals = np.array(body.split(), dtype=float)
    if vals.size != nf * nchan:  # tolerate trailing junk / truncated last line
        nf_ok = vals.size // nchan
        vals = vals[: nf_ok * nchan]
        nf = nf_ok
    frames = vals.reshape(nf, nchan)
    return BVHClip(joints, frames, float(ft.group(1)), str(path))


def write_bvh(clip: BVHClip, path, frames=None, frame_time=None):
    """Write a clip back out (optionally a frame subset / new frame time)."""
    F = clip.frames if frames is None else clip.frames[frames]
    out = ["HIERARCHY"]

    def rec(i, depth):
        j = clip.joints[i]
        ind = "\t" * depth
        if j.is_end:
            out.append(f"{ind}End Site")
        else:
            out.append(f"{ind}{'ROOT' if j.parent < 0 else 'JOINT'} {j.name}")
        out.append(ind + "{")
        out.append(f"{ind}\tOFFSET " + " ".join(f"{v:.6f}" for v in j.offset))
        if j.channels:
            out.append(f"{ind}\tCHANNELS {len(j.channels)} " + " ".join(j.channels))
        for k, jj in enumerate(clip.joints):
            if jj.parent == i:
                rec(k, depth + 1)
        out.append(ind + "}")

    rec(0, 0)
    out.append("MOTION")
    out.append(f"Frames: {F.shape[0]}")
    out.append(f"Frame Time: {frame_time or clip.frame_time:.7f}")
    for row in F:
        out.append(" ".join(f"{v:.5f}" for v in row))
    with open(path, "w") as fh:
        fh.write("\n".join(out) + "\n")
