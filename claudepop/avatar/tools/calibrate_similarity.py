#!/usr/bin/env python3
"""Calibrate the ArcFace similarity scorer (face_similarity.py) for the protagonist.

Sets (all images stay in claudepop/out/, gitignored):
  photo_aug   the clean photo under degradations a generated plate may show (downscale, blur, JPEG, grey, colour
              shift, rotation, noise, tight crop): how far the *same image* can drift
  avatar      three.js renders of subject.glb (photo camera, head 0/35 deg, posed head, full body) - a 3D stand-in,
              i.e. what a different renderer of the same face produces
  generic     the unfitted MakeHuman head (same renderer, different face)
  lfw         Labeled Faces in the Wild (funneled), one image per identity, random 400 identities
  tpdne       StyleGAN faces from thispersondoesnotexist.com (not real people)
Output: identity/scorer_calibration.json (distributions + thresholds) and check/similarity_hist.png.
Thresholds: reject = highest impostor score seen (LFW + TPDNE + generic) rounded up;
            match  = reject + 0.10 (no impostor within 0.10 of it).
"""
from __future__ import annotations

import glob
import json
import os
import random
import tarfile

import cv2
import numpy as np

from face_similarity import CAL, IDENT, REF, Scorer

OUT = IDENT.parent
CALIB = OUT / "calib"


def augment(img):
    h, w = img.shape[:2]
    out = {"clean": img}
    out["mirror"] = img[:, ::-1].copy()
    for f in (0.5, 0.25, 0.15):
        small = cv2.resize(img, (int(w * f), int(h * f)), interpolation=cv2.INTER_AREA)
        out[f"down{f}"] = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    out["blur2"] = cv2.GaussianBlur(img, (0, 0), 2)
    out["blur4"] = cv2.GaussianBlur(img, (0, 0), 4)
    ok, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 20])
    out["jpeg20"] = cv2.imdecode(enc, 1)
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    out["gray"] = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    out["dark"] = np.clip(img.astype(np.float32) * 0.55, 0, 255).astype(np.uint8)
    cool = img.astype(np.float32) * np.array([1.15, 1.0, 0.8])
    out["cool_grade"] = np.clip(cool * 0.8, 0, 255).astype(np.uint8)
    for ang in (-12, 12):
        M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, 1.0)
        out[f"rot{ang}"] = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    rng = np.random.default_rng(0)
    out["noise"] = np.clip(img + rng.normal(0, 18, img.shape), 0, 255).astype(np.uint8)
    out["crop_tight"] = cv2.resize(img[int(h * 0.3):int(h * 0.8), int(w * 0.25):int(w * 0.75)], (w, h))
    return out


def stats(v):
    v = np.asarray([x for x in v if x is not None], float)
    if len(v) == 0:
        return {"n": 0}
    return {"n": int(len(v)), "mean": float(v.mean()), "std": float(v.std()), "min": float(v.min()),
            "p05": float(np.percentile(v, 5)), "p50": float(np.median(v)), "p95": float(np.percentile(v, 95)),
            "p99": float(np.percentile(v, 99)), "max": float(v.max())}


def main():
    sc = Scorer()
    if sc.ref is None:
        raise SystemExit("run face_similarity.py --build-ref first")
    sc.cal = None
    res = {}
    # photo augmentations (the clean photo and the raw rectified page crop)
    clean = cv2.imread(str(IDENT / "face_clean_1024.png"))
    raw = cv2.imread(str(OUT / "work" / "photo_rect.png"))
    pa = {}
    for tag, im in (("clean", clean), ("raw", raw)):
        for k, a in augment(im).items():
            pa[f"{tag}/{k}"] = sc.score(a)["best"]
    res["photo_aug"] = {"scores": pa}
    # avatar renders
    av = {}
    for p in sorted(glob.glob(str(OUT / "check" / "final" / "*.png"))):
        name = os.path.basename(p)
        if name.startswith(("photo_cam", "head_", "headflat_", "pose_head", "turn_0", "turn_35", "turn_90")):
            av[name] = sc.score(cv2.imread(p))["best"]
    res["avatar"] = {"scores": av}
    # generic MakeHuman head (unfitted) rendered by the fitting stage
    gen = {}
    for p in (OUT / "work" / "fit_iter0.png", OUT / "work" / "mh_generic_head.png"):
        if p.exists():
            gen[p.name] = sc.score(cv2.imread(str(p)))["best"]
    res["generic"] = {"scores": gen}
    # LFW: one image per identity
    lfw_dir = CALIB / "lfw"
    tgz = CALIB / "lfw-funneled.tgz"
    if tgz.exists() and not any(lfw_dir.glob("*/*.jpg")):
        with tarfile.open(tgz) as tf:
            members = [m for m in tf.getmembers() if m.name.endswith("_0001.jpg")]
            random.Random(0).shuffle(members)
            for m in members[:400]:
                m.name = os.path.join(os.path.basename(os.path.dirname(m.name)), os.path.basename(m.name))
                tf.extract(m, lfw_dir)
    lf = {}
    for p in sorted(lfw_dir.glob("*/*.jpg")):
        lf[p.parent.name] = sc.score(cv2.imread(str(p)))["best"]
    res["lfw"] = {"scores": lf}
    tp = {}
    for p in sorted((CALIB / "tpdne").glob("*.jpg")):
        im = cv2.imread(str(p))
        if im is not None:
            tp[p.name] = sc.score(im)["best"]
    res["tpdne"] = {"scores": tp}
    # hardest impostors: young men (InsightFace gender/age estimate: male, 18-35) among LFW + TPDNE
    from face_similarity import GenderAge
    ga = GenderAge()
    ym = {}
    for p in list(sorted(lfw_dir.glob("*/*.jpg"))) + list(sorted((CALIB / "tpdne").glob("*.jpg"))):
        im = cv2.imread(str(p))
        if im is None:
            continue
        fs = sc.faces(im)
        if not fs:
            continue
        f = max(fs, key=lambda d: d["score"])
        g, age = ga(im, f["box"])
        if g == "male" and 18 <= age <= 35:
            ym[p.name] = float(f["emb"] @ sc.ref)
    res["young_male_impostors"] = {"scores": ym}
    for k in res:
        res[k]["stats"] = stats(res[k]["scores"].values())
    imp = [x for k in ("lfw", "tpdne", "generic") for x in res[k]["scores"].values() if x is not None]
    reject = float(np.ceil(max(imp) * 20) / 20)
    thresholds = {"reject": reject, "match": round(reject + 0.10, 2),
                  "rule": "reject = max impostor score (LFW+TPDNE+generic MakeHuman) rounded up to 0.05; match = reject + 0.10"}
    cal = {"model": "InsightFace buffalo_l: SCRFD-10G + ArcFace R50 (WebFace600K)", "reference": str(REF.name),
           "thresholds": thresholds, "sets": {k: res[k]["stats"] for k in res}, "scores": {k: res[k]["scores"] for k in res}}
    CAL.write_text(json.dumps(cal, indent=1))
    print(json.dumps({"thresholds": thresholds, "sets": cal["sets"]}, indent=1))
    # histogram
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 3.2))
    bins = np.linspace(-0.3, 1.0, 66)
    for k, c in (("lfw", "#888"), ("tpdne", "#b9a"), ("photo_aug", "#2a7"), ("avatar", "#d73")):
        v = [x for x in res[k]["scores"].values() if x is not None]
        if v:
            ax.hist(v, bins=bins, alpha=0.6, color=c, label=f"{k} (n={len(v)})", density=True)
    for x, c in ((thresholds["reject"], "k"), (thresholds["match"], "r")):
        ax.axvline(x, color=c, lw=1, ls="--")
    ax.set_xlabel("cosine similarity to the protagonist reference")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "check" / "similarity_hist.png", dpi=110)


if __name__ == "__main__":
    main()
