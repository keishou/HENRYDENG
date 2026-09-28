#!/usr/bin/env python3
"""Smoke test for the fetched MakeHuman assets: build a GENERIC dressed male (no subject data) and export GLB.

    python3 odyssey/body/mh_smoke.py [--out DIR] [--name generic_male] [--top clothes/x/x.mhclo] [--shoes ..] [--hair ..]
    node odyssey/body/glb_views.mjs DIR/generic_male.glb DIR/views.png [closeup_distance_m]

Checks that the base mesh, macro targets, .mhclo fitting (1.1.1 compiled meshes on the master base
mesh), materials and textures all line up.  Prints the resulting body height.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mh_assets import MH, N_SKIN, Mesh, height_cm, read_mhmat  # noqa: E402

FIXED_PARTS = [  # (data-relative .mhclo, alpha mode)
    ("eyes/high-poly/high-poly.mhclo", "BLEND"),
    ("eyebrows/eyebrow001/eyebrow001.mhclo", "BLEND"),
    ("eyelashes/eyelashes01/eyelashes01.mhclo", "BLEND"),
    ("teeth/teeth_base/teeth_base.mhclo", "OPAQUE"),
    ("tongue/tongue01/tongue01.mhclo", "OPAQUE"),
]


def to_trimesh(mesh: Mesh, v: np.ndarray, face_mask, tex_path, alpha_mode, name):
    tv, tu = mesh.triangles(face_mask)
    pairs = np.stack([tv.ravel(), tu.ravel()], 1)
    uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
    verts = v[uniq[:, 0]] * 0.1                              # decimetres -> metres
    uv = mesh.vt[uniq[:, 1]]
    faces = inv.reshape(-1, 3)
    img = Image.open(tex_path) if tex_path else None
    if img is not None and alpha_mode == "OPAQUE":
        img = img.convert("RGB")
    mat = trimesh.visual.material.PBRMaterial(name=name, baseColorTexture=img, metallicFactor=0.0,
                                              roughnessFactor=0.8, alphaMode=alpha_mode,
                                              alphaCutoff=0.5 if alpha_mode == "MASK" else None,
                                              doubleSided=alpha_mode != "OPAQUE")
    tm = trimesh.Trimesh(verts, faces, visual=trimesh.visual.TextureVisuals(uv=uv, material=mat), process=False)
    # smooth normals shared across uv seams: average face normals per original vertex id
    fn = np.cross(verts[faces[:, 1]] - verts[faces[:, 0]], verts[faces[:, 2]] - verts[faces[:, 0]])
    acc = np.zeros((len(v), 3))
    for k in range(3):
        np.add.at(acc, uniq[faces[:, k], 0], fn)
    n = acc[uniq[:, 0]]
    tm.vertex_normals = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    return tm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / ".cache/makehuman/smoke")
    ap.add_argument("--name", default="generic_male")
    ap.add_argument("--top", default="clothes/male_casualsuit01/male_casualsuit01.mhclo")
    ap.add_argument("--shoes", default="clothes/shoes03/shoes03.mhclo")
    ap.add_argument("--hair", default="hair/short02/short02.mhclo")
    ap.add_argument("--height", type=float, default=0.5, help="MakeHuman height slider (0.5 = average)")
    a = ap.parse_args()
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    PARTS = FIXED_PARTS + [(a.hair, "MASK"), (a.top, "OPAQUE"), (a.shoes, "OPAQUE")]
    mh = MH()
    base = mh.base()
    tl = mh.macro_targets(gender=1.0, age_years=25, muscle=0.5, weight=0.42, height=a.height, asian=1.0)
    v = mh.apply(base.v, tl)
    report = {"targets": tl, "height_cm_default_macro": round(height_cm(v), 1)}

    scene = trimesh.Scene()
    deleted = set()
    for rel, alpha in PARTS:
        px = mh.proxy(rel)
        pv = px.fit(v)
        deleted |= set(px.delete_verts.tolist())
        tex = px.material.get("diffuseTexture_abs") if px.material else None
        scene.add_geometry(to_trimesh(px.mesh, pv, None, tex, alpha, px.name), geom_name=px.name)
        report[px.name] = {"verts": int(len(pv)), "texture": tex, "delete_verts": int(len(px.delete_verts)),
                           "bbox_m": np.round(np.r_[pv.min(0), pv.max(0)] * 0.1, 3).tolist()}

    # skin: body group only, minus faces hidden under the clothes
    body_g = base.groups.index("body")
    dele = np.zeros(len(base.v), bool)
    dele[list(deleted)] = True
    mask = (base.fgroup == body_g) & ~dele[base.fv].any(1)
    skin = read_mhmat(mh.data("skins/young_asian_male/young_asian_male.mhmat"))
    scene.add_geometry(to_trimesh(base, v, mask, skin["diffuseTexture_abs"], "OPAQUE", "skin"), geom_name="skin")
    report["skin_texture"] = skin["diffuseTexture_abs"]
    report["skin_faces_kept"] = int(mask.sum())

    glb = out / f"{a.name}.glb"
    glb.write_bytes(scene.export(file_type="glb", include_normals=True))
    report["glb"] = str(glb)
    report["glb_bytes"] = glb.stat().st_size
    (out / f"{a.name}_report.json").write_text(json.dumps(report, indent=1))
    man_p = mh.cache / "manifest.json"
    if man_p.exists():  # record the smoke test next to the download proof
        man = json.loads(man_p.read_text())
        man.setdefault("smoke_tests", {})[a.name] = {
            "what": "generic male (no subject data) assembled from the fetched assets, exported as GLB",
            "parts": [r for r, _ in PARTS] + ["skins/young_asian_male/young_asian_male.mhmat"],
            "macro": {"gender": 1.0, "age_years": 25, "muscle": 0.5, "weight": 0.42, "height": a.height, "asian": 1.0},
            "height_cm": report["height_cm_default_macro"], "glb": str(glb), "report": str(out / f"{a.name}_report.json"),
            "render": str(out / f"{a.name}_views.png") + " (node odyssey/body/glb_views.mjs)"}
        man_p.write_text(json.dumps(man, indent=1))
    print(json.dumps({k: report[k] for k in ("height_cm_default_macro", "skin_faces_kept", "glb", "glb_bytes")}, indent=1))


if __name__ == "__main__":
    main()
