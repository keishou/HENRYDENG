"""MakeHuman body assembly for the avatar: macro body, parts (eyes, brows, lashes, teeth), unwelded UV meshes."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from avlib import MH, Mesh

HEIGHT_CM = 175.0            # assumption: the subject's height is unknown
MACRO = dict(gender=1.0, age_years=25.0, muscle=0.5, weight=0.42, asian=1.0)


@dataclass
class Part:
    name: str
    src_index: np.ndarray    # (n,) index into the source vertex array (base mesh or proxy mesh)
    uv: np.ndarray           # (n,2) glTF convention (v down)
    tris: np.ndarray         # (T,3) into the unwelded arrays
    proxy: object = None     # avlib Proxy or None for the base mesh


def unweld(mesh: Mesh, face_mask=None):
    tv, tu = mesh.triangles(face_mask)
    pairs = np.stack([tv.ravel(), tu.ravel()], 1)
    uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
    uv = mesh.vt[uniq[:, 1]].copy()
    uv[:, 1] = 1.0 - uv[:, 1]
    return uniq[:, 0], uv, inv.reshape(-1, 3)


def height_slider(mh: MH, base: Mesh, target_cm=HEIGHT_CM, **macro):
    """Solve the MakeHuman height macro slider for a target skin height (piecewise linear in the slider)."""
    from avlib import height_cm
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        h = height_cm(mh.apply(base.v, mh.macro_targets(height=mid, **macro)))
        lo, hi = (mid, hi) if h < target_cm else (lo, mid)
    return 0.5 * (lo + hi)


def macro_body(mh: MH, base: Mesh, extra_targets=(), target_cm=HEIGHT_CM):
    hs = height_slider(mh, base, target_cm, **MACRO)
    tl = mh.macro_targets(height=hs, **MACRO) + list(extra_targets)
    return mh.apply(base.v, tl), tl, hs


def skin_part(base: Mesh, drop_verts=None):
    body_g = base.groups.index("body")
    mask = base.fgroup == body_g
    if drop_verts is not None and len(drop_verts):
        dele = np.zeros(len(base.v), bool)
        dele[drop_verts] = True
        mask &= ~dele[base.fv].any(1)
    idx, uv, tris = unweld(base, mask)
    return Part("skin", idx, uv, tris)


def proxy_part(mh: MH, rel: str):
    px = mh.proxy(rel)
    idx, uv, tris = unweld(px.mesh)
    return Part(px.name, idx, uv, tris, px)


def texture_of(part: Part, which="diffuseTexture_abs"):
    if part.proxy is None or part.proxy.material is None:
        return None
    p = part.proxy.material.get(which)
    return p


def load_rgba(path):
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGBA"), np.float64) / 255.0
