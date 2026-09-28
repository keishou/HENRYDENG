#!/usr/bin/env python3
"""Give the full-body base human (build_body.py) the subject's face and hair, from ONE frontal photo.

    python3 odyssey/body/graft_face.py --work <dir with photo_rect.png + analysis.npz> \
        --mp-model <face_landmarker.task> [--reuse-fit] [--reuse-texture] [--out odyssey/out/body/subject_full.glb]
    # previews (Blender Cycles): full body + face close-ups + a render framed exactly like the photo
    python3 odyssey/body/render_body_bpy.py odyssey/out/body/subject_full.glb odyssey/out/body/previews \
        --prefix subject_ --portrait odyssey/out/body/face/graft_info.json --photo <photo_rect.png>

About 3.5 min on 4 CPU cores (fit 15 s, texture 2 min, hair 15 s, body build 80 s).

Stages (details in the module docstrings):
  1. face_fit.fit_face  - MakeHuman face / head / neck / ear modifiers fitted so the model's MediaPipe
                          landmarks (detected on a software render of the model), its front silhouette
                          (ears, jaw, neck) and its eye openings match the photo; closed loop over a few
                          iterations.  Output: BodyConfig.extra_targets.
  2. face_texture       - the photo projected onto the fitted head in the MakeHuman UV layout, cleaned
                          (eye openings, fringe), multi-band blended into the colour-matched body skin; the
                          hair-bearing scalp is painted in the hair colour.
  3. hair_gen           - procedural hair cards (black, soft, curly medium-short hair with a split curtain
                          fringe) grown over the head's signed distance field; the photo's hair mask (seen
                          by the fit camera) sets the envelope, the fringe locks and where locks end;
                          clumped, curled, alpha-textured, rigidly skinned to 'head'.  The brow proxy is
                          slid over the skin onto the photo's brow position.
  4. build_body.build / export_glb - the skinned GLB with everything above.

Everything written here is derived from the subject's face and stays out of git: outputs go to
odyssey/out/body/ (gitignored).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_body import BodyConfig, build, export_glb, morph, write_sidecars  # noqa: E402
from face_fit import HeadScene, OrthoCam, fit_face  # noqa: E402
from face_texture import bake_skin_texture, paint_scalp  # noqa: E402
from hair_gen import HairStyle, grow_hair, ribbons, scalp_paint_weights, strand_texture  # noqa: E402
from mh_assets import MH  # noqa: E402

OUT_DIR = HERE.parent / "out" / "body"
FACE_DIR = OUT_DIR / "face"
DEFAULT_WORK = os.environ.get("ODYSSEY_FACE_WORK", "")
DEFAULT_MP = os.environ.get("ODYSSEY_FACE_LANDMARKER", "")


def iris_colour(photo, lm):
    """Median sRGB colour of the photo's irises (a ring inside each iris, avoiding pupil and glints)."""
    H, W = photo.shape[:2]
    yy, xx = np.mgrid[:H, :W]
    vals = []
    for c, ring in ((468, (469, 470, 471, 472)), (473, (474, 475, 476, 477))):
        r = np.mean(np.linalg.norm(lm[list(ring), :2] - lm[c, :2], axis=1))
        d = np.hypot(xx - lm[c, 0], yy - lm[c, 1])
        m = (d > 0.5 * r) & (d < 0.85 * r)
        px = photo[m]
        lum = px.mean(1)
        vals.append(px[(lum > np.percentile(lum, 20)) & (lum < np.percentile(lum, 80))])
    # the photo's irises sit in the lids' shadow; MakeHuman's iris texture is lit openly -> darken a bit
    return tuple(float(x) * 0.6 for x in np.median(np.vstack(vals), 0))


def subject_config(extra_targets, skin_texture=None, iris=None) -> BodyConfig:
    return BodyConfig(
        extra_targets=list(extra_targets),
        eyebrows="eyebrows/eyebrow012/eyebrow012.mhclo",   # natural straight male brows (mostly under the fringe)
        eyelashes=None,                                   # MakeHuman's lashes read as doll lashes; the lash
                                                          # line is painted into the skin texture instead
        skin_texture=skin_texture,
        skin_tint=(1.0, 0.9, 0.82),                       # the baked texture is colour-matched to the photo; this
                                                          # linear warm-up compensates the studio render's
                                                          # desaturation (cheeks / lips read grey otherwise)
        brow_tint=(0.25, 0.24, 0.23),                     # dark brows (the photo's brows are also in the skin texture)
        eye_tint=(0.34, 0.3, 0.28),                       # dark brown iris (when no photo colour is given)
        iris_srgb=iris,                                   # the photo's iris colour (measured at run time)
    )


def load_fit(path: Path):
    d = json.loads(path.read_text())
    return [(r, float(w)) for r, w in d["extra_targets"]], np.array(d["photo_to_px"]), d["cam"], d["info"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", default=DEFAULT_WORK, help="dir with photo_rect.png and analysis.npz")
    ap.add_argument("--mp-model", default=DEFAULT_MP, help="MediaPipe face_landmarker.task")
    ap.add_argument("--out", type=Path, default=OUT_DIR / "subject_full.glb")
    ap.add_argument("--reuse-fit", action="store_true", help="reuse out/body/face/face_fit.json")
    ap.add_argument("--reuse-texture", action="store_true", help="reuse out/body/face/subject_skin.png")
    ap.add_argument("--tex-size", type=int, default=4096)
    ap.add_argument("--hair-seed", type=int, default=7)
    a = ap.parse_args()
    if not a.work or not (Path(a.work) / "photo_rect.png").exists():
        ap.error("--work must point at a dir with photo_rect.png and analysis.npz (or set ODYSSEY_FACE_WORK)")
    if not a.reuse_fit and not Path(a.mp_model or "").is_file():
        ap.error("--mp-model must point at MediaPipe's face_landmarker.task (or set ODYSSEY_FACE_LANDMARKER)")
    work = Path(a.work)
    FACE_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    photo = cv2.cvtColor(cv2.imread(str(work / "photo_rect.png")), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    an = np.load(work / "analysis.npz")
    lm, cls = an["lm"].astype(np.float64), an["cls"]
    mh = MH()
    base = mh.base()

    # ------------------------------------------------------------------ 1. face shape
    fit_path = FACE_DIR / "face_fit.json"
    if a.reuse_fit and fit_path.exists():
        extra_targets, aff, camd, info = load_fit(fit_path)
        cam = OrthoCam(np.array(camd["center"]), camd["half"], camd["res"])
        print(f"reusing {fit_path}")
    else:
        print("fitting face modifiers ...")
        ff, v_fit, img = fit_face(mh, subject_config([]), lm, cls, a.mp_model)
        extra_targets, aff, cam, info = ff.extra_targets, ff.photo_to_px, ff.cam, ff.info
        fit_path.write_text(json.dumps({
            "extra_targets": extra_targets, "photo_to_px": aff.tolist(),
            "chin_anchor": [ff.anchors[0][152].tolist(), ff.anchors[1][152].tolist()],
            "cam": {"center": cam.center.tolist(), "half": cam.half, "res": cam.res}, "info": info}, indent=1))
        Image.fromarray((img * 255).astype(np.uint8)).save(FACE_DIR / "fit_render.png")
        print(f"  {len(extra_targets)} targets; landmark residual {info['residual_before_px']:.2f} -> "
              f"{info['landmark_residual_px'][-1]:.2f} px  ({time.time() - t0:.0f}s)")
    iris = iris_colour(photo, lm)
    # brow proxy placement: MakeHuman's brow ridge sits lower than the photo's brows even after the fit;
    # shift each brow proxy so its centre lands on the photo's brow centre (front view)
    from face_texture import BROW_L, BROW_R
    cfg0 = subject_config(extra_targets)
    v0, _ = morph(mh, base, cfg0, log=lambda *x: None)
    pvb = mh.proxy(cfg0.eyebrows).fit(v0)
    Ainv = cv2.invertAffineTransform(aff)
    offs = []
    for ring, sx in ((BROW_L, 1), (BROW_R, -1)):       # subject's left brow = model +x
        q = lm[ring, :2] @ aff[:, :2].T + aff[:, 2]
        tgt = cam.unproject_xy(q).mean(0)
        half = pvb[pvb[:, 0] * sx > 0]
        # the proxy card is taller than the drawn brow: use its middle 60 % in height
        yl, yh = np.percentile(half[:, 1], [20, 80])
        cur = np.array([half[:, 0].mean(), 0.5 * (yl + yh)])
        d = tgt - cur
        offs.append((float(np.clip(d[0], -0.04, 0.04)), float(np.clip(d[1], -0.12, 0.12))))
    brow_offset = (offs[0], offs[1])
    print(f"brow proxy offset (dm) L {np.round(offs[0], 3).tolist()} R {np.round(offs[1], 3).tolist()}")
    print(f"iris colour (sRGB) {np.round(iris, 3).tolist()}")
    cfg = subject_config(extra_targets, iris=iris)
    cfg.brow_offset = brow_offset
    v, _ = morph(mh, base, cfg, log=lambda *x: None)

    # ------------------------------------------------------------------ 2. hair (needs the scalp for the texture)
    style = HairStyle(seed=a.hair_seed)
    print("growing hair ...")
    # the photo's hair mask seen by the fit camera guides the hair envelope, the fringe locks and the ends
    hair_mask_cam = cv2.warpAffine((cls == 1).astype(np.uint8), aff, (cam.res, cam.res), flags=cv2.INTER_NEAREST)
    hair = grow_hair(mh, base, v, style, guide=(hair_mask_cam, cam))
    print(f"  {hair['info']}  ({time.time() - t0:.0f}s)")

    # ------------------------------------------------------------------ 3. skin texture
    tex_path = FACE_DIR / "subject_skin.png"
    bake_path = FACE_DIR / "subject_skin_bake.npz"          # photo bake before the scalp paint
    if a.reuse_texture and bake_path.exists():
        print(f"reusing {bake_path}")
        bk = np.load(bake_path)
        tex, wmap = bk["tex"].astype(np.float32) / 65535.0, bk["wmap"].astype(np.float32) / 255.0
    else:
        print("baking the head texture ...")
        sc = HeadScene(mh, cfg)
        base_tex = np.asarray(Image.open(mh.data("skins/textures/young_lightskinned_male_diffuse3.png"))
                              .convert("RGB"), np.float32) / 255.0
        eye_geo = (sc.eyes.fit(v), sc.eyes.mesh.triangles(sc.eye_mask)[0])
        tex, wmap, tinfo = bake_skin_texture(v, base, sc.tv, sc.tu, base_tex, photo, cls, lm, cam, aff,
                                             size=a.tex_size, head_y_min=6.2, eye_geo=eye_geo, lash=(0.92, 0.016),
                                             debug_dir=FACE_DIR)
        np.savez_compressed(bake_path, tex=(np.clip(tex, 0, 1) * 65535).astype(np.uint16),
                            wmap=(np.clip(wmap, 0, 1) * 255).astype(np.uint8))
        print(f"  {tinfo}  ({time.time() - t0:.0f}s)")
    from face_texture import srgb_to_lin
    sc_ = HeadScene(mh, cfg)
    skin_ref = np.median(srgb_to_lin(tex[wmap > 0.9]), 0) * 0.97
    tex = paint_scalp(tex, base, sc_.tv, sc_.tu, scalp_paint_weights(hair, v), style.color_srgb,
                      clean=np.clip(hair["scalp"] * 3, 0, 1), skin_ref=skin_ref)
    Image.fromarray((np.clip(tex, 0, 1) * 255 + 0.5).astype(np.uint8)).save(tex_path)
    cfg.skin_texture = str(tex_path)

    # ------------------------------------------------------------------ 4. build + export
    P, N, UV, T = ribbons(hair, style)
    htex, hnrm = strand_texture(style)
    hair_png = Image.fromarray((htex * 255 + 0.5).astype(np.uint8), "RGBA")
    hair_png.save(FACE_DIR / "hair_cards.png")
    hair_nrm = Image.fromarray((hnrm * 255 + 0.5).astype(np.uint8), "RGB")
    print(f"hair cards: {len(P)} vertices, {len(T)} triangles")
    print("building the body ...")
    model = build(cfg)
    assert np.allclose(model["v_dm"], v), "build() morph differs from the fitted morph"

    def add_hair(g, model):
        rig = model["rig"]
        head = rig.names.index("head")
        pos = P * 0.1 + model["shift"]
        t = g.texture(hair_png, "image/png", name="hair_cards")
        tn = g.texture(hair_nrm, "image/jpeg", 95, name="hair_cards_normal")
        mat = g.material("hair_cards", base_tex=t, normal_tex=tn, normal_scale=0.5, roughness=0.74,
                         alpha_mode="MASK", alpha_cutoff=0.3, double_sided=True, specular=0.3,
                         extras={"note": "procedural hair cards (odyssey/body/hair_gen.py); in three.js "
                                         "render with alphaToCoverage + MSAA (or alpha-hash) for soft tips"})
        J = np.zeros((len(pos), 4), np.int64)
        J[:, 0] = head
        Wt = np.zeros((len(pos), 4))
        Wt[:, 0] = 1.0
        g.skinned_mesh("hair", pos, N, UV, T, J, Wt, mat, {"mh_part": "hair", "skinned_to": "head"},
                       with_tangents=True, compact_skin=True)
        return {"hair": {"gl_vertices": int(len(pos)), "triangles": int(len(T)), "cards": hair["info"]["strands"]
                         + hair["info"]["flyaways"]}}

    summary = export_glb(model, a.out, extra=add_hair)
    # portrait framing for the previews: posed (stand) eye centre and eye-chin distance, glTF metres
    from mh_rig import Rig, top_k
    E, D, Hh = model["pose"]
    skin = model["parts"][0]
    eyes = next(p for p in model["parts"] if p.name == "eyes")

    def posed(part, ids):
        idx, w, _ = top_k(part.W[ids], 4)
        mo = 0 if part.morph is None else part.morph[ids]
        return Rig.skin(part.v[ids] * 0.1 + model["shift"] + mo, idx, w, D, Hh, model["rig"].head)

    eye_c = posed(eyes, np.arange(len(eyes.v))).mean(0)
    ct, cb = (np.array(x) for x in json.loads(fit_path.read_text())["chin_anchor"])
    chin = (posed(skin, ct) * cb[:, None]).sum(0)
    portrait = {"eye_center_m": eye_c.tolist(), "chin_m": chin.tolist(),
                "photo_eye_center_px": ((lm[468, :2] + lm[473, :2]) / 2).tolist(), "photo_chin_px": lm[152, :2].tolist(),
                "photo_size_px": [photo.shape[1], photo.shape[0]]}
    info_s = write_sidecars(model, a.out, summary)
    meta = {"face_fit": {"targets": extra_targets, "info": {k: v for k, v in info.items() if k != "weights"}},
            "hair": hair["info"], "hair_style": style.__dict__, "height_barefoot_cm": info_s["height_barefoot_cm"],
            "portrait": portrait}
    (FACE_DIR / "graft_info.json").write_text(json.dumps(meta, indent=1, default=str))
    print(f"done in {time.time() - t0:.0f}s -> {a.out}")


if __name__ == "__main__":
    main()
