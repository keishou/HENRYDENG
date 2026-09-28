#!/usr/bin/env python3
"""Full-body base human: MakeHuman hm08 (CC0) morphed to a slim ~175 cm young East Asian man, dressed in a
black knit henley, slim charcoal trousers and black low-top sneakers, with eyes / brows / lashes / teeth /
tongue, the MakeHuman default skeleton (163 bones) and skin weights, exported as a skinned GLB (metres,
Y up, +Z forward, shoe soles on y = 0).  Hair and the face texture are added by graft_face.py.

    python3 odyssey/body/build_body.py                       # -> odyssey/out/body/body_base.glb (+ .json, _rig.json, _data.npz)
    python3 odyssey/body/build_body.py --out X.glb --height-cm 178 --weight 0.38

Library use (next stages add face offsets / textures / hair and re-export):

    from build_body import BodyConfig, build, export_glb
    cfg = BodyConfig(vertex_delta=my_face_offsets_dm, skin_texture="face_skin.png", hair="hair/short02/short02.mhclo")
    model = build(cfg); export_glb(model, "out.glb")

The GLB's bind pose (inverse bind matrices) is MakeHuman's A-pose rest, with bone frames in the
body/retarget_mh.py convention (Blender head/tail/roll, MPFB2 rolls, Y-up world), so its local_quat
output drives the joints directly.  The joint nodes' default TRS hold a relaxed standing pose
(Rig.pose_stand: level shoulders -- only a quarter of the arm drop at shoulder01 --, arms close to the
body, palms to the thighs, fingers closed with a graded curl, a light contrapposto with the weight on the
right leg, legs solved by IK), so a viewer that just loads the file shows him standing; one-key clips
"stand" and "rest_apose" carry the same two poses.  The symmetric version of the stand pose (no weight
shift) is stored in the data npz (neutral_D / neutral_H): motion retargeting is calibrated on it.  Two
morph targets per deforming mesh, "stand_corrective_L/R" (default weight 1), remove linear-blend-skinning
crumples at the shoulders / armpits in the stand pose (see corrective.py); set them towards 0 for arms-up
poses.
Outfit: MakeHuman's male_casualsuit02 (tee + jeans) refitted as a fitted knit (offsets scaled per region,
Taubin-smoothed so the fabric bridges the chest, tighter over the shoulder caps) and slim trousers (legs
tapered to their centre line), retextured procedurally with knit / rib / placket / fold normals
(cloth_textures.py); shoes: the shoes02 sneaker mesh retextured as black leather with an off-white sole.
Notes for consumers: three.js' GLTFLoader strips '.' from node names (clavicle.L -> clavicleL, use
THREE.PropertyBinding.sanitizeNodeName); Blender keeps them.  Sidecars: <stem>.json (measurements,
config, parts), <stem>_rig.json (this body's rest skeleton in MPFB2 rig JSON layout, usable as the
`rig` argument of body/retarget_mh.py), <stem>_data.npz (morphed base vertices, skeleton, stand and
neutral poses, and skin_src = base-mesh vertex index of every GL vertex of the "skin" mesh, for face work).
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
from cloth_textures import lin_to_srgb, make_shoe_textures, make_suit_textures, srgb_to_lin  # noqa: E402
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
        "neck/neck-scale-horiz": 0.05,        # neck close to jaw width (a thin, long neck read as eerie)
        "torso/torso-scale-depth": -0.10,
        "stomach/stomach-pregnant": -0.25,    # flat stomach
        "hip/hip-scale-horiz": -0.10,
    })
    extra_targets: list = field(default_factory=list)       # [(data-relative .target, weight)]
    vertex_delta: np.ndarray | None = None                   # (19158,3) decimetres, added after the morphs
    # assets (data-relative paths)
    top: str = "clothes/male_casualsuit02/male_casualsuit02.mhclo"   # crew-neck long sleeve + jeans; retextured
    shoes: str = "clothes/shoes02/shoes02.mhclo"    # low-top sneaker shape; retextured (cloth_textures.make_shoe_textures)
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
    brow_offset: tuple | None = None          # optional ((dx, dy) subject-left, (dx, dy) right) dm shift of the brow proxy
    iris_srgb: tuple | None = None            # optional iris colour (sRGB 0..1): recolours the iris, keeps its detail
    eye_occlusion: float = 0.55               # baked lid shadow on the eyeballs (0 = off)
    # geometry
    shirt_fit: float = 0.9            # multiplier on the shirt body's offsets from the body (1 = MakeHuman fit)
    sleeve_fit: float = 0.65          # the same for the sleeves
    shoulder_fit: float = 0.4         # the same over the shoulder caps (deltoids)
    shirt_smooth: int = 12            # Taubin smoothing passes on the shirt body (fabric bridges the pecs)
    trouser_taper: tuple = (1.0, 0.93, 0.84)   # radial scale of the trouser legs at upper thigh / knee / hem
    subdiv_clothes: int = 1
    subdiv_skin: int = 0
    tex_size: int = 4096
    stand_pose: dict = field(default_factory=dict)   # kwargs for Rig.pose_stand (defaults: relaxed contrapposto)
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



def _slide_on_skin(pv, v, base, offset, iters=3):
    """Shift a face proxy (brows) in the front view by per-side (dx, dy) and slide it over the skin: each
    vertex keeps its original height above the nearest skin surface point."""
    from scipy.spatial import cKDTree
    body = base.fgroup == base.groups.index("body")
    ids = np.unique(base.fv[body].ravel())
    ids = ids[v[ids, 1] > pv[:, 1].min() - 1.0]
    nrm = vertex_normals(v, base.fv[body])
    tree = cKDTree(v[ids])

    def height(p):
        _, k = tree.query(p)
        s = ids[k]
        return np.einsum("ij,ij->i", p - v[s], nrm[s]), nrm[s]

    h0, _ = height(pv)
    left = (pv[:, 0] > 0)[:, None]
    o = np.where(left, np.array([offset[0][0], offset[0][1], 0.0]), np.array([offset[1][0], offset[1][1], 0.0]))
    out = pv + o
    for _ in range(iters):
        h, n = height(out)
        out = out + (h0 - h)[:, None] * n
    return out


# ============================================================================= outfit fit
def _mesh_adj(fv, n):
    import scipy.sparse as sp
    k = np.where(fv[:, 3] == fv[:, 2], 3, 4)
    a, b = [], []
    for j in range(4):
        m = j < k
        jn = np.where(j + 1 < k, j + 1, 0)
        a.append(fv[m, j])
        b.append(fv[np.nonzero(m)[0], jn[m]])
    a, b = np.concatenate(a), np.concatenate(b)
    A = sp.csr_matrix((np.ones(2 * len(a)), (np.r_[a, b], np.r_[b, a])), shape=(n, n))
    A.data[:] = 1.0
    return A


def _fit_outfit(px, v, pv, rig, cfg):
    """Refit MakeHuman's shirt+jeans proxy as a fitted knit and slim trousers (decimetres, rest pose).
    Shirt: the offsets from the body are scaled (body / sleeves), eased back to the original fit over the
    last 12 cm above the hem (clears the trouser waistband), then the shirt body is Taubin-smoothed so
    the knit bridges the hollows (between the pecs, spine) instead of shrink-wrapping them, with a
    minimum clearance from the body.  Trousers: the waistband hidden under the shirt is tucked in; the
    legs are tapered towards their own centre line (slim chino: knee ~0.93, hem ~0.84 of the jeans)."""
    off0 = px.off
    px.off = np.zeros_like(off0)
    pv0 = px.fit(v)                                    # the body surface point each vertex hangs off
    px.off = off0
    shirt_v = _upper_island_verts(px.mesh, pv)
    is_shirt = np.zeros(len(pv), bool)
    is_shirt[shirt_v] = True
    hem_y = pv[is_shirt, 1].min()
    J = rig.head * 10.0                                # joints in decimetres (rest)
    ix = rig.index
    # sleeves: shirt vertices closer to an arm bone segment than to the spine
    def seg_dist(P, a, b):
        ab = b - a
        t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
        return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
    d_arm = np.minimum.reduce([seg_dist(pv, J[ix[f"upperarm01.{s}"]], J[ix[f"wrist.{s}"]]) for s in "LR"])
    d_sp = seg_dist(pv, J[ix["root"]], J[ix["neck01"]])
    arm_w = np.clip((d_sp - d_arm - 0.2) / 0.5, 0, 1)       # 0 torso .. 1 sleeve
    fit = cfg.shirt_fit * (1 - arm_w) + cfg.sleeve_fit * arm_w
    # shoulder caps: the A-pose garment is cut loose over the deltoid; lowered arms make that a pad
    d_sh = np.minimum.reduce([np.linalg.norm(pv - J[ix[f"upperarm01.{s}"]], axis=1) for s in "LR"])
    w_sh = np.exp(-(d_sh / 1.1) ** 2)
    fit = fit * (1 - w_sh) + cfg.shoulder_fit * w_sh
    k = np.ones(len(pv))
    ramp = np.clip((pv[:, 1] - hem_y) / 1.2, 0, 1)
    # at the hem the knit eases out to clear the trouser waistband, less at the back (the MakeHuman tee's
    # back hem flares out over the seat)
    w_back = np.clip((J[ix["root"]][2] - pv[:, 2]) / 0.5, 0, 1)
    k_hem = 0.9 - 0.3 * w_back
    k[is_shirt] = (k_hem + (fit - k_hem) * ramp)[is_shirt]
    tr = ~is_shirt
    tuck = np.clip((pv[:, 1] - (hem_y - 0.25)) / 0.6, 0, 1)
    k[tr] = (1.0 - 0.6 * tuck)[tr]
    pv = pv0 + (pv - pv0) * k[:, None]
    # ---- shirt body: Taubin smoothing (no shrinkage) weighted away from the sleeves / bands
    if cfg.shirt_smooth:
        A = _mesh_adj(px.mesh.fv, len(pv))
        deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
        wgt = (is_shirt * (1 - arm_w) * np.clip((pv[:, 1] - hem_y - 0.4) / 0.6, 0, 1))[:, None]
        n0 = pv - pv0
        n0 /= np.maximum(np.linalg.norm(n0, axis=1, keepdims=True), 1e-9)
        clear0 = np.einsum("ij,ij->i", pv - pv0, n0)
        for _ in range(cfg.shirt_smooth):
            for lam in (0.5, -0.53):
                pv = pv + lam * wgt * ((A @ pv) / deg[:, None] - pv)
            # keep at least 1.5 mm (or 60 % of the fitted offset) off the body
            c = np.einsum("ij,ij->i", pv - pv0, n0)
            need = np.maximum(np.minimum(0.015, 0.6 * clear0) - c, 0) * is_shirt
            pv = pv + need[:, None] * n0
    # ---- trouser legs: taper towards each leg's centre line
    t0, t1, t2 = cfg.trouser_taper
    if (t0, t1, t2) != (1.0, 1.0, 1.0):
        crotch = pv[tr & (np.abs(pv[:, 0]) < 0.15), 1].min() if (tr & (np.abs(pv[:, 0]) < 0.15)).any() else J[ix["root"]][1] - 1.0
        for s, sx in (("L", 1.0), ("R", -1.0)):
            hip, knee, ank = J[ix[f"upperleg01.{s}"]], J[ix[f"lowerleg01.{s}"]], J[ix[f"foot.{s}"]]
            leg = tr & (pv[:, 0] * sx > 0) & (pv[:, 1] < crotch + 0.3)
            if not leg.any():
                continue
            # centre line: centroids of trouser vertices in 1 cm height bins, smoothed
            y = pv[leg, 1]
            bins = np.arange(y.min() - 0.05, y.max() + 0.15, 0.1)
            cen = np.full((len(bins), 3), np.nan)
            for i, b0 in enumerate(bins):
                m_ = leg & (np.abs(pv[:, 1] - b0) < 0.15)
                if m_.sum() >= 6:
                    lo_, hi_ = pv[m_].min(0), pv[m_].max(0)
                    cen[i] = 0.5 * (lo_ + hi_)
            ok = ~np.isnan(cen[:, 0])
            for j in (0, 2):
                cen[:, j] = np.interp(bins, bins[ok], cen[ok, j])
                from scipy.ndimage import gaussian_filter1d
                cen[:, j] = gaussian_filter1d(cen[:, j], 2.0, mode="nearest")
            cy = np.c_[np.interp(pv[leg, 1], bins, cen[:, 0]), pv[leg, 1], np.interp(pv[leg, 1], bins, cen[:, 2])]
            yy = pv[leg, 1]
            f = np.interp(yy, [ank[1] - 0.5, knee[1], knee[1] + 1.8, crotch - 0.4, crotch + 0.3],
                          [t2, t1, t0 * 0.5 + t1 * 0.5, t0, 1.0])
            r = pv[leg] - cy
            r[:, 1] = 0.0
            pv[leg] = cy + r * f[:, None] + (pv[leg] - cy) * np.array([0, 1.0, 0])
    return pv


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
        if name == "outfit":
            pv = _fit_outfit(px, v, pv, rig, cfg)
        if name == "eyebrows" and cfg.brow_offset is not None:
            pv = _slide_on_skin(pv, v, base, cfg.brow_offset)
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
    suit = add_proxy(cfg.top, "outfit", "suit") if cfg.top else None
    if cfg.shoes:
        sh = add_proxy(cfg.shoes, "shoes", "shoes")
        if any(k in cfg.shoes for k in ("shoes02", "shoes05", "shoes06")):
            sh.material["tex"] = make_shoe_textures(sh.material["proxy"], sh.v, size=min(cfg.tex_size, 2048), log=log)
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
    if suit is not None:
        ixr = rig.index
        jc = {f"{k}.{s}": rig.head[ixr[f"{b}.{s}"]] * 100 for s in "LR"
              for k, b in (("shoulder", "upperarm01"), ("elbow", "lowerarm01"), ("wrist", "wrist"))}
        jc["chest"] = rig.head[ixr["spine01"]] * 100
        suit.material["tex"] = make_suit_textures(suit.material["proxy"], suit.v, size=cfg.tex_size,
                                                  joints_cm=jc, log=log)
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
    # symmetric neutral stance (no weight shift): what motion retargeting is calibrated on
    Dn, Hn = rig.fk(rig.pose_stand(**{**cfg.stand_pose, "weight_shift": 0.0}))
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
    Hn = Hn + np.array([0.0, _neutral_seat(parts, shift, Dn, Hn, rig), 0.0])
    log(f"  stand pose re-seated by {-min(low) * 1000:.1f} mm; build done {time.time() - t0:.1f}s")
    return {"cfg": cfg, "mh": mh, "base": base, "v_dm": v, "rig": rig, "parts": parts, "shift": shift,
            "pose": (E, D, H), "neutral": (Dn, Hn), "morph": minfo, "deleted_verts": np.array(sorted(deleted))}


def _neutral_seat(parts, shift, D, H, rig):
    """Vertical shift that puts the lowest sole point of a pose on y = 0."""
    low = []
    for p in parts:
        if p.name in ("shoes", "skin", "outfit"):
            used = np.unique((p.fv if p.face_mask is None else p.fv[p.face_mask]).ravel())
            idx, w, _ = top_k(p.W[used], 4)
            mo = 0 if p.morph is None else p.morph[used]
            low.append(Rig.skin(p.v[used] * 0.1 + shift + mo, idx, w, D, H, rig.head)[:, 1].min())
    return -min(low)


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


def _iris_recolor(img, srgb):
    """Recolour the iris (saturated texels) to srgb, keeping its luminance pattern (fibres, limbal ring)."""
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    lin = srgb_to_lin(a)
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    m = np.clip((sat - 0.25) / 0.25, 0, 1)
    lum = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    ref = np.median(lum[m > 0.9]) if (m > 0.9).any() else lum.mean()
    tgt = srgb_to_lin(np.asarray(srgb, np.float32))
    col = np.clip((lum / max(ref, 1e-4))[..., None] * tgt, 0, 1)
    out = lin * (1 - m[..., None]) + col * m[..., None]
    return Image.fromarray((lin_to_srgb(out) * 255 + 0.5).astype(np.uint8))


def _eye_lid_shadow(img, p: Part, strength=0.55):
    """Bake the lids' occlusion into the eyeball texture: MakeHuman's eyeballs are lit evenly right up to
    the lids, which reads as a doll's eye.  Texels on the upper part of each eyeball (under the upper lid)
    and towards the corners are darkened (a soft wedge), the lower rim a little."""
    from cloth_textures import rasterize as uv_raster
    a = np.asarray(img.convert("RGB"), np.float32) / 255.0
    H, W = a.shape[:2]
    fv, fuv = p.fv, p.fuv
    if p.face_mask is not None:
        fv, fuv = fv[p.face_mask], fuv[p.face_mask]
    q = fv[:, 3] != fv[:, 2]
    tv = np.vstack([fv[:, [0, 1, 2]], fv[q][:, [0, 2, 3]]])
    tu = np.vstack([fuv[:, [0, 1, 2]], fuv[q][:, [0, 2, 3]]])
    lab, P = uv_raster(p.vt[tu], p.v[tv], np.zeros(len(tv), np.int32), W)
    ok = lab >= 0
    mult = np.ones((H, W), np.float32)
    for sx in (1, -1):
        sel = p.v[:, 0] * sx > 0
        c = p.v[sel].mean(0)
        r = np.linalg.norm(p.v[sel] - c, axis=1).max()
        side = ok & (P[..., 0] * sx > 0)
        hy = (P[..., 1] - c[1]) / r
        hx = np.abs(P[..., 0] - c[0]) / r
        up = np.clip((hy - 0.08) / 0.5, 0, 1)
        up = up * up * (3 - 2 * up)
        low = np.clip((-hy - 0.45) / 0.35, 0, 1)
        corner = np.clip((hx - 0.45) / 0.4, 0, 1)
        m = 1 - strength * up - 0.25 * strength * low - 0.3 * strength * corner
        mult = np.where(side, np.clip(m, 0.3, 1), mult)
    from scipy import ndimage as _nd
    mult = _nd.gaussian_filter(mult, 2.0)
    lin = srgb_to_lin(a) * mult[..., None]
    return Image.fromarray((lin_to_srgb(lin) * 255 + 0.5).astype(np.uint8))


def make_material(g: GLB, p: Part, cfg: BodyConfig):
    kind, mm = p.material["kind"], p.material.get("mhmat", {})
    if kind == "skin":
        src = cfg.skin_texture or mm["diffuseTexture_abs"]
        t = g.texture(_tint(_img(src), cfg.skin_tint), "image/jpeg", 93, "skin_base")
        return g.material("skin", base_tex=t, roughness=0.52, extras={"subsurface": 0.2})
    if kind == "eyes":
        src = _img(mm["diffuseTexture_abs"])
        src = _iris_recolor(src, cfg.iris_srgb) if cfg.iris_srgb is not None else _iris_tint(src, cfg.eye_tint)
        if cfg.eye_occlusion:
            src = _eye_lid_shadow(src, p, cfg.eye_occlusion)
        t = g.texture(src, "image/jpeg", 93, "eye_base")
        return g.material("eyes", base_tex=t, roughness=0.12)
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
    if kind == "shoes" and "tex" in p.material:
        tex = p.material["tex"]
        tb = g.texture(tex["base"], "image/jpeg", 92, "shoes_base")
        tn = g.texture(tex["normal"], "image/jpeg", 95, "shoes_normal")
        to = g.texture(tex["orm"], "image/jpeg", 92, "shoes_orm")
        return g.material("shoes_leather", base_tex=tb, normal_tex=tn, normal_scale=1.0, orm_tex=to,
                          roughness=1.0, occlusion_strength=0.0)
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
                        neutral_D=model["neutral"][0], neutral_H=model["neutral"][1],
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
