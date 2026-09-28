"""Minimal MakeHuman (hm08) asset loader: base mesh, targets, macro modifiers, .mhclo proxy fitting.

Everything reads the tree written by fetch_makehuman.py (default odyssey/.cache/makehuman):

    from body.mh_assets import MH
    mh = MH()
    base = mh.base()                                   # Mesh, 19158 verts (0..13379 skin, rest helpers)
    v = mh.apply(base.v, mh.macro_targets(gender=1, age_years=25, muscle=.5, weight=.45, asian=1))
    top = mh.proxy("clothes/male_casualsuit01/male_casualsuit01.mhclo")
    top_v = top.fit(v)                                 # clothes vertices fitted to the morphed body

Units are MakeHuman decimetres (height_cm = 10 * skin bbox height).  The code follows MakeHuman 1.1
(apps/humanmodifier.py, apps/proxy.py); no MakeHuman source is imported.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

CACHE = Path(__file__).resolve().parent.parent / ".cache" / "makehuman"
GH_DATA = "gh/makehuman/makehuman/data"
DEB_DATA = "ubuntu/makehuman-data_1.1.1-1/usr/share/makehuman/data"
N_SKIN = 13380  # hm08: vertices [0, 13380) are the skin surface


@dataclass
class Mesh:
    v: np.ndarray            # (N,3) float
    vt: np.ndarray           # (M,2) float
    fv: np.ndarray           # (F,4) int, quads; triangles repeat their last index
    fuv: np.ndarray          # (F,4) int
    fgroup: np.ndarray       # (F,) int index into groups
    groups: list = field(default_factory=list)

    def triangles(self, face_mask=None):
        """(T,3) vertex and uv index triangles (quads split a-b-c, a-c-d)."""
        fv, fuv = self.fv, self.fuv
        if face_mask is not None:
            fv, fuv = fv[face_mask], fuv[face_mask]
        t1v, t1u = fv[:, [0, 1, 2]], fuv[:, [0, 1, 2]]
        quad = fv[:, 3] != fv[:, 2]
        t2v, t2u = fv[quad][:, [0, 2, 3]], fuv[quad][:, [0, 2, 3]]
        return np.vstack([t1v, t2v]), np.vstack([t1u, t2u])


def load_obj(path) -> Mesh:
    v, vt, fv, fuv, fg, groups = [], [], [], [], [], ["default"]
    gi = 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("v "):
                v.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("vt "):
                vt.append([float(x) for x in line.split()[1:3]])
            elif line.startswith("g "):
                name = line.split(None, 1)[1].strip()
                if name not in groups:
                    groups.append(name)
                gi = groups.index(name)
            elif line.startswith("f "):
                cs = line.split()[1:]
                vi = [int(c.split("/")[0]) - 1 for c in cs]
                ti = [int(c.split("/")[1]) - 1 if "/" in c and c.split("/")[1] else 0 for c in cs]
                if len(vi) == 3:
                    vi.append(vi[2]); ti.append(ti[2])
                if len(vi) != 4:
                    raise ValueError(f"{path}: only tris/quads supported")
                fv.append(vi); fuv.append(ti); fg.append(gi)
    return Mesh(np.asarray(v, np.float64), np.asarray(vt, np.float64).reshape(-1, 2),
                np.asarray(fv, np.int64), np.asarray(fuv, np.int64), np.asarray(fg, np.int64), groups)


def load_npz_mesh(path) -> Mesh:
    """MakeHuman 1.1 compiled .obj (files3d): coord, texco, fvert, fuvs, group, fgstr/fgidx."""
    d = np.load(path)
    fgstr = d["fgstr"].tobytes().decode("utf-8", "replace")
    idx = list(d["fgidx"]) + [len(fgstr)]
    groups = [fgstr[idx[i]:idx[i + 1]] for i in range(len(idx) - 1)]
    return Mesh(d["coord"].astype(np.float64), d["texco"].astype(np.float64), d["fvert"].astype(np.int64),
                d["fuvs"].astype(np.int64), d["group"].astype(np.int64), groups)


def load_target(path):
    idx, vec = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                p = s.split()
                idx.append(int(p[0])); vec.append([float(p[1]), float(p[2]), float(p[3])])
    return np.asarray(idx, np.int64), np.asarray(vec, np.float64).reshape(-1, 3)


def read_mhmat(path) -> dict:
    out = {"_path": str(path)}
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("//"):
                continue
            k, _, val = s.partition(" ")
            out[k] = val.strip()
    for k in ("diffuseTexture", "normalmapTexture", "aomapTexture", "specularmapTexture", "transparencymapTexture",
              "bumpmapTexture"):
        if k in out:
            out[k + "_abs"] = resolve_texture(Path(path), out[k])
    return out


def resolve_texture(mhmat: Path, ref: str) -> str | None:
    """MakeHuman resolves texture paths relative to the .mhmat, then to data/ (e.g. 'data/litspheres/..')."""
    ref = ref.replace("\\", "/")
    cands = [mhmat.parent / ref]
    stripped = ref[5:] if ref.startswith("data/") else ref
    for root in (CACHE / DEB_DATA, CACHE / GH_DATA):
        cands.append(root / stripped)
    for c in cands:
        if c.exists():
            return str(c.resolve())
    return None


@dataclass
class Proxy:
    path: Path
    name: str
    mesh: Mesh
    ref: np.ndarray          # (N,3) int
    w: np.ndarray            # (N,3)
    off: np.ndarray          # (N,3)
    scale: dict              # axis -> (v1, v2, den)
    delete_verts: np.ndarray
    material: dict | None
    z_depth: int = 50

    def fit(self, body_v: np.ndarray) -> np.ndarray:
        s = np.ones(3)
        for ax, i in (("x", 0), ("y", 1), ("z", 2)):
            if ax in self.scale:
                a, b, den = self.scale[ax]
                s[i] = abs(body_v[a, i] - body_v[b, i]) / den
        return (body_v[self.ref[:, 0]] * self.w[:, :1] + body_v[self.ref[:, 1]] * self.w[:, 1:2]
                + body_v[self.ref[:, 2]] * self.w[:, 2:3] + self.off * s)


def load_proxy(path) -> Proxy:
    path = Path(path)
    ref, w, off, dele = [], [], [], []
    scale, meta = {}, {}
    state = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        p = s.split()
        if state == "verts" and re.fullmatch(r"-?\d+", p[0]):
            if len(p) == 1:
                ref.append([int(p[0])] * 3); w.append([1.0, 0, 0]); off.append([0.0, 0, 0])
            else:
                ref.append([int(x) for x in p[:3]]); w.append([float(x) for x in p[3:6]])
                off.append([float(x) for x in p[6:9]])
            continue
        if state == "delete" and re.fullmatch(r"\d+", p[0]):
            toks = s.replace(" - ", "-").split()
            for t in toks:
                if "-" in t:
                    a, b = t.split("-"); dele.extend(range(int(a), int(b) + 1))
                else:
                    dele.append(int(t))
            continue
        k = p[0]
        if k == "verts":
            state = "verts"
        elif k == "delete_verts":
            state = "delete"
        elif k in ("x_scale", "y_scale", "z_scale"):
            scale[k[0]] = (int(p[1]), int(p[2]), float(p[3]))
        else:
            meta[k] = " ".join(p[1:])
    obj = path.parent / meta["obj_file"]
    npz = obj.with_suffix(".npz")
    mesh = load_obj(obj) if obj.exists() else load_npz_mesh(npz)
    ref = np.asarray(ref, np.int64)
    if len(ref) != len(mesh.v):
        raise ValueError(f"{path}: {len(ref)} reference rows for {len(mesh.v)} mesh vertices")
    mat = None
    if "material" in meta:
        mp = (path.parent / meta["material"])
        if mp.exists():
            mat = read_mhmat(mp)
    return Proxy(path, meta.get("name", path.stem), mesh, ref, np.asarray(w), np.asarray(off), scale,
                 np.asarray(sorted(set(dele)), np.int64), mat, int(meta.get("z_depth", 50)))


class MH:
    def __init__(self, cache: Path = CACHE):
        self.cache = Path(cache)
        self._tcache = {}

    def data(self, rel: str) -> Path:
        """Resolve a MakeHuman data-relative path: GitHub master copy first, else the 1.1.1 package."""
        for root in (GH_DATA, DEB_DATA):
            p = self.cache / root / rel
            if p.exists():
                return p
        raise FileNotFoundError(rel)

    def base(self) -> Mesh:
        return load_obj(self.data("3dobjs/base.obj"))

    def target(self, rel: str):
        if rel not in self._tcache:
            self._tcache[rel] = load_target(self.data(rel))
        return self._tcache[rel]

    def apply(self, v: np.ndarray, targets) -> np.ndarray:
        out = v.copy()
        for rel, wt in targets:
            if abs(wt) < 1e-9:
                continue
            i, d = self.target(rel)
            if len(i):
                out[i] += wt * d
        return out

    def proxy(self, rel: str) -> Proxy:
        return load_proxy(self.data(rel))

    @staticmethod
    def macro_targets(gender=1.0, age_years=25.0, muscle=0.5, weight=0.5, height=0.5, proportions=0.5,
                      african=0.0, asian=1.0, caucasian=0.0):
        """(target path, weight) list of MakeHuman 1.1 macro modifiers (slider values in [0,1], 0.5 = average)."""
        if age_years < 25:
            age = (age_years - 1) / (2 * (25 - 1))
        else:
            age = 0.5 + (age_years - 25) / (2 * (90 - 25))
        age = float(np.clip(age, 0, 1))
        if age < 0.5:
            old = 0.0
            baby = max(0.0, 1 - age * 5.333)
            young = max(0.0, (age - 0.1875) * 3.2)
            child = max(0.0, min(1.0, 5.333 * age) - young)
        else:
            child = baby = 0.0
            old = max(0.0, age * 2 - 1)
            young = 1 - old
        tri = lambda x: {"min": max(0.0, 1 - 2 * x), "max": max(0.0, 2 * x - 1),
                         "average": 1 - max(0.0, 1 - 2 * x) - max(0.0, 2 * x - 1)}
        G = {"female": 1 - gender, "male": gender}
        A = {"baby": baby, "child": child, "young": young, "old": old}
        M, W = tri(muscle), tri(weight)
        rs = african + asian + caucasian
        R = {"african": african / rs, "asian": asian / rs, "caucasian": caucasian / rs}
        H = {"min": max(0.0, 1 - 2 * height), "max": max(0.0, 2 * height - 1)}
        P = {"uncommon": max(0.0, 1 - 2 * proportions), "ideal": max(0.0, 2 * proportions - 1)}
        md = "targets/macrodetails"
        out = []
        for g, gw in G.items():
            for a, aw in A.items():
                if gw * aw == 0:
                    continue
                for r, rw in R.items():
                    out.append((f"{md}/{r}-{g}-{a}.target", rw * gw * aw))
                for m, mw in M.items():
                    for wn, ww in W.items():
                        base_w = gw * aw * mw * ww
                        if base_w == 0:
                            continue
                        out.append((f"{md}/universal-{g}-{a}-{m}muscle-{wn}weight.target", base_w))
                        for h, hw in H.items():
                            out.append((f"{md}/height/{g}-{a}-{m}muscle-{wn}weight-{h}height.target", base_w * hw))
                        for pn, pw in P.items():
                            out.append((f"{md}/proportions/{g}-{a}-{m}muscle-{wn}weight-{pn}proportions.target", base_w * pw))
        return [(t, w) for t, w in out if w > 1e-9]


def height_cm(v: np.ndarray) -> float:
    s = v[:N_SKIN]
    return float(10.0 * (s[:, 1].max() - s[:, 1].min()))
