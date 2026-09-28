#!/usr/bin/env python3
"""Assemble and export the protagonist as one skinned GLB: claudepop/out/avatar/subject.glb.

Conventions (same as odyssey/body/retarget_mh.py output): metres, Y up, the character faces +Z, MakeHuman default
skeleton (163 bones, MPFB2 rig.default.json, CC0) with Blender bone frames (+Y along the bone, MPFB roll) converted
(x, y, z) -> (x, z, -y).  Rest pose = MakeHuman A-pose.  The whole model is shifted so the shoe soles touch y = 0
(the shift is stored in asset.extras.floor_offset_m; bone heads of retarget_mh.py motion files are in the unshifted
MakeHuman frame, root_pos in a floor-at-0 frame, so root_pos can be applied to the root bone directly).
Skin weights: MPFB2 weights.default.json (up to 8 influences) reduced to the 4 largest (three.js uses 4) and
renormalised; proxies (eyes, brows, teeth, tongue, hair, trousers, shoes) get weights interpolated from
their MakeHuman reference vertices exactly as MakeHuman/MPFB do; the knit top shares the body's vertices and
weights (smoothed along its edges, build_clothes.py).

Also writes subject_camera.json (the photo camera in the GLB frame, three.js-ready) and subject_report.json.
"""
from __future__ import annotations

import json

import cv2
import numpy as np
from PIL import Image

from avlib import (GLB, MH, OUT, WORK, Cam, dense_weights, load_rgb, load_rig, load_weights, mat_to_quat,
                   reduce_dense, skeleton_rest)
from bake_texture import push_pull
from mhscene import load_rgba, proxy_part, skin_part, texture_of

BROW = "eyebrows/eyebrow012/eyebrow012.mhclo"


def pad_texture(img, uv, tris, T=None):
    """Bleed texels into the UV gutters (no seams from bilinear/mipmap sampling across island borders)."""
    from avlib import rasterize
    H, W = img.shape[:2]
    ti, _, _ = rasterize(uv * np.array([W, H]), tris, W, H)
    m = (ti >= 0).astype(np.float32)
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))  # keep the anti-aliased border texels
    if img.shape[2] == 4:
        rgb = push_pull(img[..., :3].astype(np.float32), m)
        a = img[..., 3]
        return np.dstack([np.where(m[..., None] > 0, img[..., :3], rgb), a])
    fill = push_pull(img.astype(np.float32), m)
    return np.where(m[..., None] > 0, img, fill)


def proxy_weights(px, Wd):
    """Dense bone weights of a proxy's vertices from its MakeHuman reference vertices."""
    return (Wd[px.ref[:, 0]] * px.w[:, :1] + Wd[px.ref[:, 1]] * px.w[:, 1:2] + Wd[px.ref[:, 2]] * px.w[:, 2:3])


def smooth_normals(pos, tris, src):
    """Normals averaged per source vertex (continuous across UV seams)."""
    fn = np.cross(pos[tris[:, 1]] - pos[tris[:, 0]], pos[tris[:, 2]] - pos[tris[:, 0]])
    acc = np.zeros((src.max() + 1, 3))
    for k in range(3):
        np.add.at(acc, src[tris[:, k]], fn)
    n = acc[src]
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def photo_camera(cam: Cam, s, R2, t2):
    """The camera of the photo itself: render camera composed with the inverse 2D similarity (scale -> focal,
    shift -> principal point, rotation -> roll about the optical axis)."""
    f2 = cam.f / s
    c2 = R2.T @ (np.array([cam.cx, cam.cy]) - t2) / s
    phi = np.arctan2(R2[1, 0], R2[0, 0])
    best = None
    for sgn in (1, -1):
        a = sgn * phi
        Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
        c = Cam(Rz @ cam.R, Rz @ cam.t, f2, c2[0], c2[1], 1024, 1024)
        X = cam.eye() + np.random.default_rng(0).normal(0, 0.1, (50, 3)) + (-cam.R[2]) * 1.2
        pr = cam.project(X)[:, :2]
        want = ((pr - t2) @ R2) / s
        err = np.abs(c.project(X)[:, :2] - want).max()
        if best is None or err < best[0]:
            best = (err, c)
    return best[1], best[0]


def main():
    F = np.load(WORK / "face_fit.npz")
    v = F["v_fit"]
    vm = v * 0.1
    cam = Cam.from_dict(json.loads(str(F["cam"])))
    Hf = np.load(WORK / "hair_fit.npz")
    Cf = np.load(WORK / "clothes.npz")
    mh = MH()
    base = mh.base()
    rig, order = load_rig()
    Wd = dense_weights(load_weights(), order, len(base.v))

    # ---------------- parts (positions in metres, MakeHuman frame)
    parts = []  # (name, pos, tris, uv, dense_weights, material dict)
    skin = skin_part(base, Cf["skin_delete"])
    stex = load_rgb(WORK / "skin_albedo_hair.png")
    stex = pad_texture(stex, skin.uv, skin.tris)
    parts.append(dict(name="skin", pos=vm[skin.src_index], tris=skin.tris, uv=skin.uv, W=Wd[skin.src_index],
                      src=skin.src_index, mat=dict(tex=stex, fmt="JPEG", roughness=0.58, name="skin")))

    E = proxy_part(mh, "eyes/high-poly/high-poly.mhclo")
    ev = E.proxy.fit(v)[E.src_index] * 0.1
    cc = E.uv[E.tris].mean(1)
    corn = (cc[:, 0] > 0.8) & (cc[:, 1] > 0.8)
    ew = proxy_weights(E.proxy, Wd)[E.src_index]
    etex = load_rgb(WORK / "eye_albedo.png")
    parts.append(dict(name="eyes", pos=ev, tris=E.tris[~corn], uv=E.uv, W=ew, src=E.src_index,
                      mat=dict(tex=cv2.resize(etex, (512, 512), interpolation=cv2.INTER_AREA), fmt="JPEG", roughness=0.75, name="eyes")))
    # (the cornea shell is left out: as a blended layer it greys the iris in three.js)

    hair_col = Hf["hair_col"]
    # brows: tinted MakeHuman proxy (the photo's brows are mostly under the fringe).  No eyelash cards: the photo
    # texture carries the subject's dense lash line, and MakeHuman's lash cards (even shortened, upper lid only)
    # read as a grey mascara comb above it from the front.
    P = proxy_part(mh, BROW)
    tx = load_rgba(texture_of(P))
    tint = np.dstack([np.broadcast_to(hair_col * 0.35, tx.shape[:2] + (3,)), tx[..., 3] * 0.55])
    tint = cv2.resize(tint, (256, 256), interpolation=cv2.INTER_AREA)
    parts.append(dict(name="eyebrows", pos=P.proxy.fit(v)[P.src_index] * 0.1, tris=P.tris, uv=P.uv,
                      W=proxy_weights(P.proxy, Wd)[P.src_index], src=P.src_index,
                      mat=dict(tex=tint, fmt="PNG", alpha="BLEND", roughness=0.8, double=True, name="eyebrows")))
    for rel, nm in (("teeth/teeth_base/teeth_base.mhclo", "teeth"), ("tongue/tongue01/tongue01.mhclo", "tongue")):
        P = proxy_part(mh, rel)
        tp = texture_of(P)
        tx = load_rgb(tp) if tp else np.full((4, 4, 3), 0.8)
        ppos = P.proxy.fit(v)[P.src_index] * 0.1
        parts.append(dict(name=nm, pos=ppos, tris=P.tris, uv=P.uv,
                          W=proxy_weights(P.proxy, Wd)[P.src_index], src=P.src_index,
                          mat=dict(tex=cv2.resize(tx, (256, 256), interpolation=cv2.INTER_AREA), fmt="JPEG", roughness=0.4, name=nm)))

    # hair: re-volumised short02 (weights from its MakeHuman refs), carved over the fringe zone
    P = proxy_part(mh, "hair/short02/short02.mhclo")
    hs = np.asarray(Image.open(WORK / "short02_black.png"), np.float64) / 255
    hs = cv2.resize(hs, (1024, 1024), interpolation=cv2.INTER_AREA)
    hn = load_rgb(mh.data("hair/short02/short02_normal.png"))
    hn = cv2.resize(hn, (1024, 1024), interpolation=cv2.INTER_AREA)
    hw = proxy_weights(P.proxy, Wd)
    hpos = Hf["short02_v"][P.src_index]
    # anisotropic highlights along the combing direction: away from the crown, along the surface (TANGENT attribute,
    # anisotropy direction = tangent); a uniform anisotropy texture keeps the bands coherent
    head_top = vm[F["mask"] > 0.9]
    crown = np.array([0.0, head_top[:, 1].max(), np.median(head_top[:, 2]) - 0.03])
    han = np.ones((4, 4, 3)) * np.array([1.0, 0.5, 1.0])
    parts.append(dict(name="hair", pos=hpos, tris=P.tris, uv=P.uv, W=hw[P.src_index], src=P.src_index,
                      mat=dict(tex=hs, fmt="PNG", alpha="MASK", cutoff=0.45, double=True, roughness=0.58, aniso=han, name="hair")))
    # two fur shells (same cards pushed out 2.5 / 5 mm, sparser alpha) break up the silhouette and the flat look
    hnrm = smooth_normals(hpos, P.tris, P.src_index)
    flow = hpos - crown
    flow -= hnrm * (flow * hnrm).sum(1, keepdims=True)
    flow /= np.maximum(np.linalg.norm(flow, axis=1, keepdims=True), 1e-9)
    htan = np.c_[flow, np.ones(len(flow))]
    parts[-1]["tangents"] = htan
    hsf = cv2.resize(np.asarray(Image.open(WORK / "short02_fur.png"), np.float64) / 255, (1024, 1024), interpolation=cv2.INTER_AREA)
    for k, (d, cut) in enumerate(((0.003, 0.6), (0.007, 0.8))):
        parts.append(dict(name=f"hair_shell{k + 1}", pos=hpos + hnrm * d, tris=P.tris, uv=P.uv, W=hw[P.src_index], src=P.src_index,
                          tangents=htan, mat=dict(tex=hsf, fmt="PNG", alpha="MASK", cutoff=cut, double=True, roughness=0.6, aniso=han, name=f"hair_shell{k + 1}")))
    # fringe: ribbon strands traced along the photo's strand directions (build_strands.py); the shell is carved
    # over the fringe zone.  Weights: the nearest head skin vertex (head bone), like the shell roots.
    S = np.load(WORK / "strands.npz")
    stx = np.asarray(Image.open(WORK / "strand_tex.png"), np.float64) / 255
    parts.append(dict(name="hair_strands", pos=S["pos"], tris=S["tris"], uv=S["uv"], W=Wd[S["src"]],
                      src=np.arange(len(S["pos"])), tangents=np.c_[S["tangent"], np.ones(len(S["pos"]))],
                      mat=dict(tex=stx, fmt="PNG", alpha="BLEND", double=True, roughness=0.62, aniso=han,
                               name="hair_strands")))

    # clothes
    top_alb = load_rgb(WORK / "top_albedo.png")
    top_alb = cv2.resize(top_alb, (1024, 1024), interpolation=cv2.INTER_AREA)
    top_nrm = cv2.resize(load_rgb(WORK / "top_normal.png"), (1024, 1024), interpolation=cv2.INTER_AREA)
    parts.append(dict(name="top", pos=Cf["top_pos"], tris=Cf["top_tris"], uv=Cf["top_uv"], W=Cf["top_W"],
                      src=Cf["top_src"], mat=dict(tex=top_alb, fmt="JPEG", roughness=0.92, normal=top_nrm, normal_scale=0.3,
                                                   double=True, name="knit_top")))
    parts.append(dict(name="button", pos=Cf["button_v"], tris=Cf["button_tris"], uv=None, W=Cf["button_W"],
                      src=np.arange(len(Cf["button_v"])), mat=dict(color=(0.74, 0.62, 0.44, 1), metallic=0.75, roughness=0.38, name="gold_button")))
    SUIT = proxy_part(mh, "clothes/male_casualsuit03/male_casualsuit03.mhclo")
    pv = SUIT.proxy.fit(v) * 0.1
    pw = proxy_weights(SUIT.proxy, Wd)
    pal = cv2.resize(load_rgb(WORK / "pants_albedo.png"), (1024, 1024), interpolation=cv2.INTER_AREA)
    pn_path = SUIT.proxy.material.get("normalmapTexture_abs")
    pn = cv2.resize(load_rgb(pn_path), (1024, 1024), interpolation=cv2.INTER_AREA) if pn_path else None
    parts.append(dict(name="trousers", pos=pv[Cf["pants_idx"]], tris=Cf["pants_tris"], uv=Cf["pants_uv"], W=pw[Cf["pants_idx"]],
                      src=Cf["pants_idx"], mat=dict(tex=pal, fmt="JPEG", roughness=0.85, normal=pn, name="trousers")))
    SH = proxy_part(mh, "clothes/shoes03/shoes03.mhclo")
    sh_tex = load_rgb(texture_of(SH))
    parts.append(dict(name="shoes", pos=SH.proxy.fit(v)[SH.src_index] * 0.1, tris=SH.tris, uv=SH.uv,
                      W=proxy_weights(SH.proxy, Wd)[SH.src_index], src=SH.src_index,
                      mat=dict(tex=cv2.resize(sh_tex, (512, 512), interpolation=cv2.INTER_AREA), fmt="JPEG", roughness=0.45, name="shoes")))

    # ---------------- floor offset, skeleton
    floor = min(p["pos"][:, 1].min() for p in parts if p["name"] in ("shoes",))
    off = np.array([0.0, -floor, 0.0])
    order_s, parents, rest = skeleton_rest(v, base, offset=off)
    g = GLB()
    bone_node = {}
    Rw = {n: rest[n][2] for n in order_s}
    Hw = {n: rest[n][0] for n in order_s}
    for n in order_s:
        p = parents[n]
        if p is None:
            Rl, tl = Rw[n], Hw[n]
        else:
            Rl = Rw[p].T @ Rw[n]
            tl = Rw[p].T @ (Hw[n] - Hw[p])
        bone_node[n] = g.node(name=n, rotation=mat_to_quat(Rl).tolist(), translation=tl.tolist())
    for n in order_s:
        ch = [bone_node[m] for m in order_s if parents[m] == n]
        if ch:
            g.g["nodes"][bone_node[n]]["children"] = ch
    ibm = []
    for n in order_s:
        M = np.eye(4)
        M[:3, :3] = Rw[n]
        M[:3, 3] = Hw[n]
        ibm.append(np.linalg.inv(M).T.ravel())  # column-major
    ibm_acc = g.accessor(np.asarray(ibm, np.float32), "MAT4")
    g.g["skins"] = [{"inverseBindMatrices": ibm_acc, "joints": [bone_node[n] for n in order_s], "skeleton": bone_node["root"],
                     "name": "MakeHuman_default_MPFB2"}]
    root_nodes = [bone_node["root"]]
    report = {"parts": {}, "total_triangles": 0}
    for p in parts:
        m = p["mat"]
        tex = None
        if m.get("tex") is not None:
            tex = g.image(m["tex"], fmt=m.get("fmt", "JPEG"), quality=90, name=p["name"])
        nt = g.image(m["normal"], fmt="JPEG", quality=92, name=p["name"] + "_normal") if m.get("normal") is not None else None
        ext = None
        if m.get("aniso") is not None:
            at = g.image(m["aniso"], fmt="PNG", name=p["name"] + "_aniso")
            ext = {"KHR_materials_anisotropy": {"anisotropyStrength": 0.55, "anisotropyRotation": 0.0,
                                                "anisotropyTexture": {"index": at}}}
        mat = g.material(m["name"], base_tex=tex, extensions=ext, base_color=m.get("color", (1, 1, 1, 1)), metallic=m.get("metallic", 0.0),
                         roughness=m.get("roughness", 0.8), normal_tex=nt, normal_scale=m.get("normal_scale", 1.0),
                         alpha=m.get("alpha", "OPAQUE"), cutoff=m.get("cutoff", 0.5), double=m.get("double", False))
        pos = p["pos"] + off
        nrm = smooth_normals(pos, p["tris"], p["src"])
        J, Wt = reduce_dense(p["W"].astype(np.float64), 4)
        mi = g.mesh(p["name"], pos, p["tris"], mat, normals=nrm, uv=p["uv"], joints=J, weights=Wt, tangents=p.get("tangents"))
        root_nodes.append(g.node(name=p["name"], mesh=mi, skin=0))
        report["parts"][p["name"]] = {"vertices": int(len(pos)), "triangles": int(len(p["tris"]))}
        report["total_triangles"] += int(len(p["tris"]))
    g.g["scenes"][0]["nodes"] = root_nodes
    extras = {"units": "m", "up": "+Y", "forward": "+Z", "rig": "MakeHuman default (163 bones), MPFB2 rig/weights, CC0",
              "rest_pose": "MakeHuman A-pose", "floor_offset_m": float(off[1]), "height_assumed_cm": 175.0,
              "root_head_m": Hw["root"].tolist(), "note": "subject-derived model: keep out of public repositories"}
    size = g.write(OUT / "subject.glb", extras=extras)
    report["glb_bytes"] = size
    report["bones"] = len(order_s)
    report["floor_offset_m"] = float(off[1])
    report["height_m_skin_top"] = float(max(p["pos"][:, 1].max() for p in parts if p["name"] == "skin") + off[1])
    report["height_m_with_hair"] = float(max(p["pos"][:, 1].max() for p in parts if p["name"] in ("hair", "hair_strands")) + off[1])
    # cameras in the GLB frame
    s, R2, t2 = float(F["sim_s"]), F["sim_R"], F["sim_t"]
    cam_g = Cam(cam.R, cam.t - cam.R @ off, cam.f, cam.cx, cam.cy, cam.W, cam.H)
    pc, err = photo_camera(cam_g, s, R2, t2)
    camj = {"render_camera": cam_g.as_dict(), "photo_camera": pc.as_dict(), "photo_camera_fit_err_px": float(err),
            "convention": "world->camera rows R, t; camera looks down -Z; pixels: u right, v down; f in px",
            "photo_distance_assumed_m": 1.3}
    (OUT / "subject_camera.json").write_text(json.dumps(camj, indent=1))
    (OUT / "subject_report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({k: report[k] for k in ("total_triangles", "glb_bytes", "bones", "height_m_skin_top", "height_m_with_hair")}))
    print({k: vv["triangles"] for k, vv in report["parts"].items()})


if __name__ == "__main__":
    main()
