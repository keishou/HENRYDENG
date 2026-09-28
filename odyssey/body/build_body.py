#!/usr/bin/env python3
"""Full-body base human: MakeHuman hm08 (CC0) morphed to a slim ~175 cm young East Asian man, dressed in a
black knit henley, dark trousers and black shoes, with eyes / brows / lashes / teeth / tongue, the
MakeHuman default skeleton (163 bones) and skin weights, exported as a skinned GLB (metres, Y up, +Z
forward, shoe soles on y = 0).  Hair and the face texture are left for the next stage.

    python3 odyssey/body/build_body.py                       # -> odyssey/out/body/body_base.glb (+ .json, _rig.json, _data.npz)
    python3 odyssey/body/build_body.py --out X.glb --height-cm 178 --weight 0.38

Library use (next stages add face offsets / textures / hair and re-export):

    from build_body import BodyConfig, build, export_glb
    cfg = BodyConfig(vertex_delta=my_face_offsets_dm, skin_texture="face_skin.png", hair="hair/short02/short02.mhclo")
    model = build(cfg); export_glb(model, "out.glb")

The GLB's bind pose (inverse bind matrices) is MakeHuman's A-pose rest, with bone frames in the
body/retarget_mh.py convention (Blender head/tail/roll, MPFB2 rolls, Y-up world), so its local_quat
output drives the joints directly.  The joint nodes' default TRS hold a relaxed standing pose, so a
viewer that just loads the file shows him standing; one-key clips "stand" and "rest_apose" carry the
same two poses.  Two morph targets per deforming mesh, "stand_corrective_L/R" (default weight 1),
remove linear-blend-skinning crumples at the shoulders/armpits in the stand pose (see corrective.py);
set them towards 0 for arms-up poses.
Notes for consumers: three.js' GLTFLoader strips '.' from node names (clavicle.L -> clavicleL, use
THREE.PropertyBinding.sanitizeNodeName); Blender keeps them.  Sidecars: <stem>.json (measurements,
config, parts), <stem>_rig.json (this body's rest skeleton in MPFB2 rig JSON layout, usable as the
`rig` argument of body/retarget_mh.py), <stem>_data.npz (morphed base vertices, skeleton, pose, and
skin_src = base-mesh vertex index of every GL vertex of the "skin" mesh, for face work).
No face data, texture or mesh from the subject is used here: macro sliders, modifiers and colours are
constants (the 3-number skin_tint hue was only sanity-checked against the photo's median skin colour).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cloth_textures import lin_to_srgb, make_suit_textures, srgb_to_lin  # noqa: E402
from corrective import stand_corrective  # noqa: E402
from gltf_skinned import GLB  # noqa: E402
from mh_assets import MH, Mesh, height_cm, read_mhmat  # noqa: E402
from mh_rig import Rig, top_k  # noqa: E402
from subdiv import catmull_clark  # noqa: E402

OUT_DIR = HERE.parent / "out" / "body"


@dataclass
class BodyConfig:
    # macro sliders (MakeHuman 1.1 semantics; 0.5 = average)
    height_cm: float = 175.0          # barefoot stature (skin bbox); solved with the height slider
    gender: float = 1.0
    age_years: float = 25.5
    muscle: float = 0.5
    weight: float = 0.40              # slim
    proportions: float = 0.5          # MakeHuman "ideal" (1.0) broadens the shoulders too much for a slim build
    asian: float = 0.9
    caucasian: float = 0.1
    african: float = 0.0
    # modelling modifiers: "group/name" -> value in [-1, 1]; files targets/<group>/<name>-<decr|incr>.target
    modifiers: dict = field(default_factory=lambda: {
        "neck/neck-scale-vert": 0.2,          # slim, longish neck
        "neck/neck-scale-horiz": -0.20,
        "neck/neck-scale-depth": -0.15,
        "torso/torso-scale-depth": -0.10,
        "measure/measure-shoulder-dist": -0.3,
        "stomach/stomach-pregnant": -0.25,    # flat stomach
        "hip/hip-scale-horiz": -0.10,
    })
    extra_targets: list = field(default_factory=list)       # [(data-relative .target, weight)]
    vertex_delta: np.ndarray | None = None                   # (19158,3) decimetres, added after the morphs
    # assets (data-relative paths)
    top: str = "clothes/male_casualsuit02/male_casualsuit02.mhclo"   # crew-neck long sleeve + jeans; retextured
    shoes: str = "clothes/shoes03/shoes03.mhclo"
    eyes: str = "eyes/high-poly/high-poly.mhclo"
    eyebrows: str | None = "eyebrows/eyebrow004/eyebrow004.mhclo"
    eyelashes: str | None = "eyelashes/eyelashes01/eyelashes01.mhclo"
    teeth: str | None = "teeth/teeth_base/teeth_base.mhclo"
    tongue: str | None = "tongue/tongue01/tongue01.mhclo"
    hair: str | None = None
    hair_tint: tuple = (0.12, 0.115, 0.11)    # linear multiplier: MakeHuman's brown hair textures -> near black
    skin_material: str = "skins/young_asian_male/young_asian_male.mhmat"
    skin_texture: str | None = None   # override the skin diffuse (e.g. a face-projected texture)
    skin_tint: tuple = (0.90, 0.965, 0.985)  # linear RGB multiplier: MakeHuman's skin is pinker than a fair East Asian tone
    eye_tint: tuple = (0.30, 0.30, 0.30)      # iris only: MakeHuman's red-brown -> dark brown
    brow_tint: tuple | None = None            # optional linear multiplier for the eyebrow texture
    # geometry
    shirt_fit: float = 0.6            # multiplier on the shirt's offsets from the body (1 = MakeHuman fit)
    subdiv_clothes: int = 1
    subdiv_skin: int = 0
    tex_size: int = 4096
    stand_pose: dict = field(default_factory=lambda: {  # kwargs for Rig.pose_stand
        "shoulder_drop_deg": 3.0, "arm_out_deg": 4.0, "shoulder_share": 0.75})
    stand_corrective: bool = True     # Laplacian LBS corrective for the stand pose, as morph targets


@dataclass
class Part:
    name: str
    v: np.ndarray            # (N,3) decimetres, rest pose, before the global shift
    fv: np.ndarray           # (F,4)
    vt: np.ndarray
    fuv: np.ndarray
    W: np.ndarray            # (N,B) dense weights
    face_mask: np.ndarray | None = None
    material: dict = field(default_factory=dict)
    src: np.ndarray | None = None     # source vertex id per vertex (base-mesh index for the skin)
    adj_fv: np.ndarray | None = None  # faces used for connectivity (skin: the whole body group)
    morph: np.ndarray | None = None   # (N,3) bind-space stand-pose corrective, metres


# ============================================================================= morph
def _modifier_targets(mh: MH, mods: dict):
    out = []
    for key, val in mods.items():
        if abs(val) < 1e-6:
            continue
        group, name = key.split("/")
        tdir = f"targets/{group}"
        for lo, hi in (("decr", "incr"), ("in", "out"), ("down", "up"), ("backward", "forward")):
            p_hi = f"{tdir}/{name}-{hi}.target"
            try:
                mh.data(p_hi)
            except FileNotFoundError:
                continue
            out.append((p_hi, val) if val > 0 else (f"{tdir}/{name}-{lo}.target", -val))
            break
        else:
            raise FileNotFoundError(f"modifier {key}: no target pair found")
    return out


def morph(mh: MH, base: Mesh, cfg: BodyConfig, log=print):
    mods = _modifier_targets(mh, cfg.modifiers) + list(cfg.extra_targets)

    def body(hs):
        tl = mh.macro_targets(gender=cfg.gender, age_years=cfg.age_years, muscle=cfg.muscle, weight=cfg.weight,
                              height=hs, proportions=cfg.proportions, african=cfg.african, asian=cfg.asian,
                              caucasian=cfg.caucasian)
        v = mh.apply(base.v, tl + mods)
        if cfg.vertex_delta is not None:
            v = v + cfg.vertex_delta
        return v, tl

    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if height_cm(body(mid)[0]) < cfg.height_cm:
            lo = mid
        else:
            hi = mid
    hs = 0.5 * (lo + hi)
    v, tl = body(hs)
    log(f"  height slider {hs:.4f} -> {height_cm(v):.1f} cm")
    return v, {"height_slider": hs, "targets": tl + mods}


# ============================================================================= geometry helpers
def uv_islands(mesh: Mesh):
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    F = len(mesh.fuv)
    A = sp.csr_matrix((np.ones(F * 4), (np.repeat(np.arange(F), 4), mesh.fuv.ravel())), shape=(F, len(mesh.vt)))
    return connected_components(A @ A.T)[1]


def _upper_island_verts(mesh: Mesh, pv):
    """Vertices of the UV islands that sit well above the lowest island (the shirt of a shirt+trousers mesh)."""
    lab = uv_islands(mesh)
    cent = np.array([pv[mesh.fv[lab == i].ravel()].mean(0) for i in range(lab.max() + 1)])
    up = np.nonzero(cent[:, 1] > cent[:, 1].min() + 4.0)[0]
    return np.unique(mesh.fv[np.isin(lab, up)])


def vertex_normals(v, fv):
    tri = fv[:, 3] != fv[:, 2]
    t = np.vstack([fv[:, [0, 1, 2]], fv[tri][:, [0, 2, 3]]])
    fn = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    acc = np.zeros_like(v)
    for k in range(3):
        np.add.at(acc, t[:, k], fn)
    return acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-12)


def gl_arrays(p: Part):
    """Split (vertex, uv) pairs into GL vertices. Returns uniq (vid, uvid), tris (T,3)."""
    fv, fuv = p.fv, p.fuv
    if p.face_mask is not None:
        fv, fuv = fv[p.face_mask], fuv[p.face_mask]
    quad = fv[:, 3] != fv[:, 2]
    tv = np.vstack([fv[:, [0, 1, 2]], fv[quad][:, [0, 2, 3]]])
    tu = np.vstack([fuv[:, [0, 1, 2]], fuv[quad][:, [0, 2, 3]]])
    pairs = np.stack([tv.ravel(), tu.ravel()], 1)
    uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
    return uniq, inv.reshape(-1, 3)


def subdivide(p: Part, levels=1):
    for _ in range(levels):
        S, fv2, U, fuv2 = catmull_clark(p.fv, p.fuv, len(p.v), len(p.vt))
        mask = None
        if p.face_mask is not None:  # a sub-quad keeps its parent's mask
            k = np.where(p.fv[:, 3] == p.fv[:, 2], 3, 4)
            mask = np.concatenate([p.face_mask[j < k] for j in range(4)])
        W = S @ p.W
        p = Part(p.name, S @ p.v, fv2, U @ p.vt, fuv2, W / np.maximum(W.sum(1, keepdims=True), 1e-12),
                 mask, p.material, None)
    return p


# ============================================================================= build
def build(cfg: BodyConfig | None = None, log=print):
    cfg = cfg or BodyConfig()
    t0 = time.time()
    mh = MH()
    base = mh.base()
    v, minfo = morph(mh, base, cfg, log)
    rig = Rig.from_mesh(v)
    Wb = rig.body_weights(len(v))
    parts, deleted = [], set()

    def add_proxy(rel, name, mat_kind):
        px = mh.proxy(rel)
        pv = px.fit(v)
        if name == "outfit" and cfg.shirt_fit != 1.0:
            # knit tops are fitted: pull the shirt's offsets from the body towards it (trousers untouched)
            off0 = px.off
            px.off = np.zeros_like(off0)
            pv0 = px.fit(v)
            px.off = off0
            shirt_v = _upper_island_verts(px.mesh, pv)
            is_shirt = np.zeros(len(pv), bool)
            is_shirt[shirt_v] = True
            hem_y = pv[is_shirt, 1].min()                      # decimetres
            k = np.ones(len(pv))
            # shirt: fitted, easing back to the original fit over the last 12 cm above the hem so it
            # still clears the trouser waistband (belt loops)
            ramp = np.clip((pv[:, 1] - hem_y) / 1.2, 0, 1)
            k[is_shirt] = (1.0 + (cfg.shirt_fit - 1.0) * ramp)[is_shirt]
            # trousers: the waistband hidden under the shirt is tucked in (invisible, avoids poke-through)
            tr = ~is_shirt
            tuck = np.clip((pv[:, 1] - (hem_y + 0.15)) / 0.4, 0, 1)
            k[tr] = (1.0 - 0.6 * tuck)[tr]
            pv = pv0 + (pv - pv0) * k[:, None]
        own = px.path.with_suffix(".mhw")
        W = rig.proxy_weights(px, Wb, own if own.exists() else None)
        deleted.update(px.delete_verts.tolist())
        p = Part(name, pv, px.mesh.fv, px.mesh.vt, px.mesh.fuv, W,
                 material={"kind": mat_kind, "mhmat": px.material or {}, "proxy": px, "rel": rel})
        parts.append(p)
        return p

    eyes = add_proxy(cfg.eyes, "eyes", "eyes")
    # MakeHuman's high-poly eyes carry a cornea shell mapped onto a transparent texture patch; glTF
    # viewers without proper transparency show it as a milky film, so keep only the eyeballs (which get
    # a glossy finish instead)
    ea = np.asarray(Image.open(eyes.material["mhmat"]["diffuseTexture_abs"]).convert("RGBA"))[..., 3]
    uvc = np.stack([eyes.vt[eyes.fuv[:, j]] for j in range(4)], 1).mean(1)
    px_ = np.clip((uvc[:, 0] * ea.shape[1]).astype(int), 0, ea.shape[1] - 1)
    py_ = np.clip(((1 - uvc[:, 1]) * ea.shape[0]).astype(int), 0, ea.shape[0] - 1)
    eyes.face_mask = ea[py_, px_] > 127
    if cfg.eyebrows:
        add_proxy(cfg.eyebrows, "eyebrows", "alpha")
    if cfg.eyelashes:
        add_proxy(cfg.eyelashes, "eyelashes", "alpha")
    if cfg.teeth:
        add_proxy(cfg.teeth, "teeth", "teeth")
    if cfg.tongue:
        add_proxy(cfg.tongue, "tongue", "tongue")
    suit = add_proxy(cfg.top, "outfit", "suit")
    if cfg.shoes:
        add_proxy(cfg.shoes, "shoes", "shoes")
    if cfg.hair:
        add_proxy(cfg.hair, "hair", "hair")
    # skin: 'body' group minus faces hidden under clothes / shoes
    dele = np.zeros(len(v), bool)
    dele[list(deleted)] = True
    fmask = (base.fgroup == base.groups.index("body")) & ~dele[base.fv].any(1)
    skin = Part("skin", v, base.fv, base.vt, base.fuv, Wb, fmask,
                material={"kind": "skin", "mhmat": read_mhmat(mh.data(cfg.skin_material))}, src=np.arange(len(v)),
                adj_fv=base.fv[base.fgroup == base.groups.index("body")])
    parts.insert(0, skin)
    # retextured suit: textures are designed on the rest-pose fitted garment (before subdivision)
    log(f"  morph + fit {time.time() - t0:.1f}s; generating suit textures ...")
    suit.material["tex"] = make_suit_textures(suit.material["proxy"], suit.v, size=cfg.tex_size, log=log)
    if cfg.subdiv_clothes:
        for i, p in enumerate(parts):
            if p.name in ("outfit",):
                parts[i] = subdivide(p, cfg.subdiv_clothes)
    if cfg.subdiv_skin:
        parts[0] = subdivide(parts[0], cfg.subdiv_skin)
    # global placement: metres, soles on y = 0, pelvis above the origin
    allv = np.vstack([p.v[np.unique((p.fv if p.face_mask is None else p.fv[p.face_mask]).ravel())]
                      for p in parts if p.name in ("skin", "shoes", "outfit")]) * 0.1
    root = rig.head[rig.parent < 0][0]
    shift = np.array([-root[0], -allv[:, 1].min(), -root[2]])
    rig = rig.translated(shift)
    E = rig.pose_stand(**cfg.stand_pose)
    D, H = rig.fk(E)
    if cfg.stand_corrective:
        for p in parts:
            if p.name in ("skin", "outfit"):
                idx, w, _ = top_k(p.W, 4)
                fv = p.adj_fv if p.adj_fv is not None else p.fv
                p.morph, _, _ = stand_corrective(p.v * 0.1 + shift, fv, idx, w, D, H, rig.head)
                log(f"  stand corrective {p.name}: max {np.abs(p.morph).max() * 100:.1f} cm")
    # re-seat the stand pose so its lowest sole point is on y = 0 (the bind pose already is)
    low = []
    for p in parts:
        if p.name in ("shoes", "skin", "outfit"):
            used = np.unique((p.fv if p.face_mask is None else p.fv[p.face_mask]).ravel())
            idx, w, _ = top_k(p.W[used], 4)
            mo = 0 if p.morph is None else p.morph[used]
            low.append(Rig.skin(p.v[used] * 0.1 + shift + mo, idx, w, D, H, rig.head)[:, 1].min())
    H = H + np.array([0.0, -min(low), 0.0])
    log(f"  stand pose re-seated by {-min(low) * 1000:.1f} mm; build done {time.time() - t0:.1f}s")
    return {"cfg": cfg, "mh": mh, "base": base, "v_dm": v, "rig": rig, "parts": parts, "shift": shift,
            "pose": (E, D, H), "morph": minfo, "deleted_verts": np.array(sorted(deleted))}


# ============================================================================= materials
def _img(path, mode=None):
    im = Image.open(path)
    return im.convert(mode) if mode else im


def _tint(img, mul):
    a = srgb_to_lin(np.asarray(img.convert("RGB"), np.float32) / 255.0) * np.asarray(mul, np.float32)
    return Image.fromarray((lin_to_srgb(a) * 255 + 0.5).astype(np.uint8))


def _iris_tint(img, mul):
    """Darken/desaturate only the iris (saturated, darker texels), leave the sclera alone."""
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lin = srgb_to_lin(a)
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    m = np.clip((sat - 0.25) / 0.25, 0, 1)[..., None]
    out = lin * (1 - m) + lin * np.asarray(mul, np.float32) * m
    return Image.fromarray((lin_to_srgb(out) * 255 + 0.5).astype(np.uint8))


def make_material(g: GLB, p: Part, cfg: BodyConfig):
    kind, mm = p.material["kind"], p.material.get("mhmat", {})
    if kind == "skin":
        src = cfg.skin_texture or mm["diffuseTexture_abs"]
        t = g.texture(_tint(_img(src), cfg.skin_tint), "image/jpeg", 93, "skin_base")
        return g.material("skin", base_tex=t, roughness=0.52, extras={"subsurface": 0.2})
    if kind == "eyes":
        t = g.texture(_iris_tint(_img(mm["diffuseTexture_abs"]), cfg.eye_tint), "image/jpeg", 93, "eye_base")
        return g.material("eyes", base_tex=t, roughness=0.08)
    if kind == "alpha":
        src = _img(mm["diffuseTexture_abs"], "RGBA")
        if p.name == "eyebrows" and cfg.brow_tint is not None:
            rgb = _tint(src, cfg.brow_tint).convert("RGB")
            src = Image.merge("RGBA", (*rgb.split(), src.split()[3]))
        t = g.texture(src, "image/png", name=f"{p.name}_base")
        return g.material(p.name, base_tex=t, roughness=0.7, alpha_mode="BLEND", double_sided=True)
    if kind in ("teeth", "tongue"):
        t = g.texture(_img(mm["diffuseTexture_abs"], "RGB"), "image/jpeg", 90, f"{kind}_base")
        return g.material(kind, base_tex=t, roughness=0.3 if kind == "teeth" else 0.45)
    if kind == "suit":
        tex = p.material["tex"]
        tb = g.texture(tex["base"], "image/jpeg", 92, "outfit_base")
        tn = g.texture(tex["normal"], "image/jpeg", 95, "outfit_normal")
        to = g.texture(tex["orm"], "image/jpeg", 92, "outfit_orm")
        return g.material("outfit_knit_henley_trousers", base_tex=tb, normal_tex=tn, normal_scale=1.0, orm_tex=to,
                          roughness=1.0, metallic=1.0, double_sided=True, sheen=((0.10, 0.10, 0.115), 0.45))
    if kind == "shoes":
        t = g.texture(_img(mm["diffuseTexture_abs"], "RGB"), "image/jpeg", 92, "shoes_base")
        nt = None
        if mm.get("normalmapTexture_abs"):
            nt = g.texture(_img(mm["normalmapTexture_abs"], "RGB"), "image/jpeg", 95, "shoes_normal")
        return g.material("shoes_leather", base_tex=t, normal_tex=nt, roughness=0.38)
    if kind == "hair":
        src = _img(mm["diffuseTexture_abs"], "RGBA")
        rgb = _tint(src, cfg.hair_tint).convert("RGB")
        t = g.texture(Image.merge("RGBA", (*rgb.split(), src.split()[3])), "image/png", name="hair_base")
        return g.material("hair", base_tex=t, roughness=0.55, alpha_mode="MASK", alpha_cutoff=0.4,
                          double_sided=True)
    raise ValueError(kind)


# ============================================================================= export
def export_glb(model, path: Path, log=print, extra=None):
    """extra: optional callback extra(g, model) that adds more meshes (e.g. hair cards) to the GLB
    before the animations are written; it may return a dict merged into the summary."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rig, cfg, shift = model["rig"], model["cfg"], model["shift"]
    E, D, H = model["pose"]
    g = GLB()
    t_rest, q_rest = rig.local_trs()
    t_pose, q_pose = rig.local_trs(D, H)
    joints = g.skeleton(rig.names, rig.parent, t_pose, q_pose, rig.inverse_bind())
    summary = {}
    for p in model["parts"]:
        uniq, tris = gl_arrays(p)
        vid, uvid = uniq[:, 0], uniq[:, 1]
        pos = p.v * 0.1 + shift
        nrm = vertex_normals(pos, p.fv if p.face_mask is None else p.fv[p.face_mask])
        idx, w, bad = top_k(p.W[vid], 4)
        if bad.any():  # unweighted vertices (should not happen): pin to the nearest joint
            near = np.argmin(np.linalg.norm(pos[vid][bad][:, None] - rig.head[None], axis=2), 1)
            idx[bad, 0] = near
            w[bad] = [1, 0, 0, 0]
        mat = make_material(g, p, cfg)
        extras = {"mh_part": p.name}
        if p.name == "skin":
            extras["base_vertex_of_gl_vertex"] = "see body_base_data.npz: skin_src"
        targets = None
        if p.morph is not None:
            fvn = p.fv if p.face_mask is None else p.fv[p.face_mask]
            dn = vertex_normals(pos + p.morph, fvn) - nrm
            side = np.clip(0.5 + pos[:, 0] / 0.04, 0, 1)[:, None]  # character's left = +x
            targets = [("stand_corrective_L", (p.morph * side)[vid], (dn * side)[vid]),
                       ("stand_corrective_R", (p.morph * (1 - side))[vid], (dn * (1 - side))[vid])]
        has_nmap = "normalTexture" in g.j["materials"][mat]
        g.skinned_mesh(p.name, pos[vid], nrm[vid], p.vt[uvid], tris, idx, w, mat, extras, targets,
                       with_tangents=has_nmap)
        summary[p.name] = {"gl_vertices": int(len(vid)), "triangles": int(len(tris)),
                           "unweighted_fixed": int(bad.sum())}
        if p.name == "skin":
            model["skin_src"] = vid
    if extra is not None:
        summary.update(extra(g, model) or {})
    # animations: the standing pose and the bind (A-pose) rest, one key each
    root = int(np.nonzero(rig.parent < 0)[0][0])
    g.animation("stand", {i: q_pose[i][None] for i in range(len(joints))}, [0.0], {root: t_pose[root][None]})
    g.animation("rest_apose", {i: q_rest[i][None] for i in range(len(joints))}, [0.0], {root: t_rest[root][None]})
    size = g.save(path, extras={"units": "metres", "up": "+Y", "forward": "+Z",
                                "bind_pose": "MakeHuman A-pose rest", "default_pose": "stand"})
    log(f"  wrote {path} ({size / 1e6:.1f} MB)")
    return summary


def write_sidecars(model, glb_path: Path, summary, log=print):
    glb_path = Path(glb_path)
    rig, cfg = model["rig"], model["cfg"]
    E, D, H = model["pose"]
    stem = glb_path.with_suffix("")
    posed, rest = {}, {}
    for p in model["parts"]:
        if p.name in ("skin", "outfit", "shoes"):
            used = np.unique((p.fv if p.face_mask is None else p.fv[p.face_mask]).ravel())
            idx, w, _ = top_k(p.W[used], 4)
            rest[p.name] = p.v[used] * 0.1 + model["shift"]
            mo = 0 if p.morph is None else p.morph[used]
            posed[p.name] = Rig.skin(rest[p.name] + mo, idx, w, D, H, rig.head)
    allp = np.vstack(list(posed.values()))
    allr = np.vstack(list(rest.values()))
    info = {
        "glb": str(glb_path),
        "height_barefoot_cm": round(height_cm(model["v_dm"]), 2),
        "height_with_shoes_cm": round(100 * (allp[:, 1].max() - allp[:, 1].min()), 2),
        "bbox_rest_m": None,
        "bbox_stand_m": [np.round(allp.min(0), 3).tolist(), np.round(allp.max(0), 3).tolist()],
        "height_slider": model["morph"]["height_slider"],
        "config": {k: (v if not isinstance(v, np.ndarray) else "array") for k, v in asdict(cfg).items()},
        "targets": [[t, round(float(w), 5)] for t, w in model["morph"]["targets"]],
        "parts": summary,
        "skeleton": {"bones": len(rig.names), "root": rig.names[int(np.nonzero(rig.parent < 0)[0][0])],
                     "bind_pose": "MakeHuman A-pose rest (inverse bind matrices)",
                     "default_node_pose": "stand (Rig.pose_stand)",
                     "bone_frames": "Blender vec_roll_to_mat3 with MPFB2 rolls, in Y-up world (see mh_rig.py)"},
        "suit_texture_info": next((p.material["tex"]["info"] for p in model["parts"]
                                   if p.material.get("kind") == "suit" and "tex" in p.material), None),
        "global_shift_m": model["shift"].tolist(),
        "licence": "MakeHuman assets CC0 (see odyssey/.cache/makehuman/manifest.json); textures of the outfit "
                   "are procedurally generated here on top of male_casualsuit02's normal/AO maps.",
    }
    info["bbox_rest_m"] = [np.round(allr.min(0), 3).tolist(), np.round(allr.max(0), 3).tolist()]
    Path(f"{stem}.json").write_text(json.dumps(info, indent=1))
    Path(f"{stem}_rig.json").write_text(json.dumps(rig.to_mpfb_json(), indent=1))
    np.savez_compressed(f"{stem}_data.npz", base_v_dm=model["v_dm"], shift_m=model["shift"],
                        bone_names=np.array(rig.names), bone_parent=rig.parent, bone_head=rig.head,
                        bone_tail=rig.tail, bone_R=rig.R, pose_D=D, pose_H=H,
                        skin_src=model.get("skin_src", np.zeros(0, int)),
                        deleted_verts=model["deleted_verts"])
    log(f"  wrote {stem}.json, {stem}_rig.json, {stem}_data.npz")
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT_DIR / "body_base.glb")
    ap.add_argument("--height-cm", type=float, default=175.0)
    ap.add_argument("--weight", type=float, default=None)
    ap.add_argument("--tex-size", type=int, default=4096)
    ap.add_argument("--subdiv-skin", type=int, default=0)
    ap.add_argument("--subdiv-clothes", type=int, default=1)
    ap.add_argument("--hair", default=None, help="optional hair proxy, e.g. hair/short02/short02.mhclo")
    a = ap.parse_args()
    cfg = BodyConfig(height_cm=a.height_cm, tex_size=a.tex_size, subdiv_skin=a.subdiv_skin,
                     subdiv_clothes=a.subdiv_clothes, hair=a.hair)
    if a.weight is not None:
        cfg.weight = a.weight
    model = build(cfg)
    summary = export_glb(model, a.out)
    info = write_sidecars(model, a.out, summary)
    print(json.dumps({k: info[k] for k in ("height_barefoot_cm", "height_with_shoes_cm", "bbox_stand_m", "parts")},
                     indent=1))


if __name__ == "__main__":
    main()
