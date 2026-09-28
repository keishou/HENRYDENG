#!/usr/bin/env python3
"""Face-identity similarity to the protagonist (ArcFace, CPU) - auto-verification of generated plates.

    # score images, folders of frames or videos against the protagonist reference
    python3 face_similarity.py plate_001.png shots/042/ render.mp4 [--every 12] [--json scores.json]
    # (re)build the reference embedding from the identity pack
    python3 face_similarity.py --build-ref
    # (re)run the calibration (genuine = photo variants + avatar renders, impostors = other faces)
    python3 face_similarity.py --calibrate

Pipeline (the standard InsightFace recipe, reimplemented on onnxruntime, no insightface package needed):
  SCRFD-10G face detector (det_10g.onnx) -> 5 keypoints -> similarity warp to the ArcFace 112x112 template ->
  ArcFace ResNet-50 trained on WebFace600K (w600k_r50.onnx) -> 512-d L2-normalised embedding -> cosine similarity
  with the reference embedding (mean of the rectified photo and its mirror image).
Models: InsightFace "buffalo_l" pack (github.com/deepinsight/insightface releases v0.7), cached in
odyssey/.cache/models/insightface/.  Licence note: InsightFace's pretrained models are released for non-commercial
research use; check before any commercial use.
The verdict thresholds come from identity/scorer_calibration.json (written by --calibrate, gitignored).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[2]
MODEL_DIR = REPO / "odyssey" / ".cache" / "models" / "insightface" / "buffalo_l"
IDENT = REPO / "claudepop" / "out" / "avatar" / "identity"
REF = IDENT / "ref_embedding.npy"
CAL = IDENT / "scorer_calibration.json"
ARC_TEMPLATE = np.array([[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
                         [41.5493, 92.3655], [70.7299, 92.2041]], np.float32)


def _sess(name):
    so = ort.SessionOptions()
    so.intra_op_num_threads = 2
    so.log_severity_level = 3
    return ort.InferenceSession(str(MODEL_DIR / name), so, providers=["CPUExecutionProvider"])


class SCRFD:
    """SCRFD face detector (InsightFace det_10g.onnx: 3 strides, 2 anchors, boxes + 5 keypoints)."""

    def __init__(self, size=640, thresh=0.5, nms=0.4):
        self.s = _sess("det_10g.onnx")
        self.inp = self.s.get_inputs()[0].name
        self.size, self.thresh, self.nms = size, thresh, nms
        self.strides = (8, 16, 32)

    def __call__(self, bgr):
        """Two scales (image fitted to the input, and at half that size) so faces that fill the frame - common in
        generated close-ups - are found too (SCRFD's largest anchors top out around half the input size)."""
        dets = self._detect(bgr, 1.0) + self._detect(bgr, 0.5)
        return self._nms(dets)

    def _nms(self, dets):
        dets = sorted(dets, key=lambda d: -d["score"])
        keep = []
        for d in dets:
            ok = True
            for k in keep:
                a, b = d["box"], k["box"]
                iw = max(0, min(a[2], b[2]) - max(a[0], b[0]))
                ih = max(0, min(a[3], b[3]) - max(a[1], b[1]))
                inter = iw * ih
                u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
                if inter / max(u, 1e-9) > self.nms:
                    ok = False
                    break
            if ok:
                keep.append(d)
        return keep

    def _detect(self, bgr, scale):
        h, w = bgr.shape[:2]
        sc = self.size / max(h, w) * scale
        nh, nw = int(round(h * sc)), int(round(w * sc))
        img = np.zeros((self.size, self.size, 3), np.uint8)
        img[:nh, :nw] = cv2.resize(bgr, (nw, nh))
        blob = cv2.dnn.blobFromImage(img, 1.0 / 128, (self.size, self.size), (127.5, 127.5, 127.5), swapRB=True)
        outs = self.s.run(None, {self.inp: blob})
        boxes, scores, kpss = [], [], []
        for i, st in enumerate(self.strides):
            sco = outs[i].reshape(-1)
            bb = outs[i + 3].reshape(-1, 4) * st
            kp = outs[i + 6].reshape(-1, 10) * st
            g = self.size // st
            cy, cx = np.mgrid[0:g, 0:g]
            cen = np.stack([cx, cy], -1).reshape(-1, 2).astype(np.float32) * st
            cen = np.repeat(cen, 2, 0)
            keep = sco >= self.thresh
            if not keep.any():
                continue
            c = cen[keep]
            b = np.c_[c - bb[keep, :2], c + bb[keep, 2:]]
            k = kp[keep].reshape(-1, 5, 2) + c[:, None]
            boxes.append(b)
            scores.append(sco[keep])
            kpss.append(k)
        if not boxes:
            return []
        boxes, scores, kpss = np.concatenate(boxes) / sc, np.concatenate(scores), np.concatenate(kpss) / sc
        order = np.argsort(-scores)
        keep = []
        while len(order):
            i = order[0]
            keep.append(i)
            xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
            yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
            xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
            yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])
            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            area = lambda j: (boxes[j, 2] - boxes[j, 0]) * (boxes[j, 3] - boxes[j, 1])
            iou = inter / (area(i) + area(order[1:]) - inter + 1e-9)
            order = order[1:][iou < self.nms]
        return [dict(box=boxes[i], score=float(scores[i]), kps=kpss[i]) for i in keep]


def umeyama(src, dst):
    ms, md = src.mean(0), dst.mean(0)
    a, b = src - ms, dst - md
    U, S, Vt = np.linalg.svd(b.T @ a / len(src))
    D = np.diag([1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / (a ** 2).sum(1).mean()
    t = md - s * R @ ms
    return np.c_[s * R, t]


class ArcFace:
    def __init__(self):
        self.s = _sess("w600k_r50.onnx")
        self.inp = self.s.get_inputs()[0].name

    def align(self, bgr, kps):
        M = umeyama(kps.astype(np.float32), ARC_TEMPLATE)
        return cv2.warpAffine(bgr, M, (112, 112), borderValue=0)

    def embed(self, crops):
        blob = cv2.dnn.blobFromImages(crops, 1.0 / 127.5, (112, 112), (127.5, 127.5, 127.5), swapRB=True)
        e = self.s.run(None, {self.inp: blob})[0]
        return e / np.linalg.norm(e, axis=1, keepdims=True)


class GenderAge:
    """InsightFace genderage.onnx (96x96 crop around the detection box): used to pick the hardest impostors
    (young men) during calibration."""

    def __init__(self):
        self.s = _sess("genderage.onnx")
        self.inp = self.s.get_inputs()[0].name

    def __call__(self, bgr, box):
        w, h = box[2] - box[0], box[3] - box[1]
        c = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        sc = 96 / (max(w, h) * 1.5)
        M = np.array([[sc, 0, 48 - c[0] * sc], [0, sc, 48 - c[1] * sc]], np.float32)
        crop = cv2.warpAffine(bgr, M, (96, 96), borderValue=0)
        blob = cv2.dnn.blobFromImage(crop, 1.0, (96, 96), (0, 0, 0), swapRB=True)
        p = self.s.run(None, {self.inp: blob})[0][0]
        return ("male" if p[1] > p[0] else "female"), float(p[2] * 100)


class Scorer:
    def __init__(self):
        self.det = SCRFD()
        self.arc = ArcFace()
        self.ref = np.load(REF) if REF.exists() else None
        self.cal = json.loads(CAL.read_text()) if CAL.exists() else None

    def faces(self, bgr, min_size=24):
        out = []
        for f in self.det(bgr):
            bw = f["box"][2] - f["box"][0]
            if bw < min_size:
                continue
            crop = self.arc.align(bgr, f["kps"])
            f["emb"] = self.arc.embed([crop])[0]
            f["crop"] = crop
            out.append(f)
        return out

    def verdict(self, sim):
        if self.cal is None:
            return None
        t = self.cal["thresholds"]
        return "match" if sim >= t["match"] else ("uncertain" if sim >= t["reject"] else "no-match")

    @staticmethod
    def yaw_proxy(kps):
        """Horizontal nose offset from the eye midpoint in eye-distance units: 0 for a frontal face, growing with head
        yaw; |r| > 0.6 corresponds to roughly 40 deg and more (checked on renders at known yaw)."""
        em = 0.5 * (kps[0] + kps[1])
        return float((kps[2, 0] - em[0]) / max(np.linalg.norm(kps[1] - kps[0]), 1e-6))

    def score(self, bgr):
        fs = self.faces(bgr)
        if not fs:
            return {"faces": 0, "best": None}
        sims = [float(f["emb"] @ self.ref) for f in fs]
        i = int(np.argmax(sims))
        yp = self.yaw_proxy(fs[i]["kps"])
        v = self.verdict(sims[i])
        # a frontal reference cannot vouch for near-profile faces: ArcFace scores drop there for the same person
        if v is not None and v != "match" and abs(yp) > 0.6:
            v = "pose-unreliable"
        return {"faces": len(fs), "best": sims[i], "verdict": v, "all": sims, "yaw_proxy": yp,
                "box": [float(x) for x in fs[i]["box"]], "det_score": fs[i]["score"]}


def iter_inputs(paths, every):
    exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
    for p in paths:
        if os.path.isdir(p):
            for q in sorted(glob.glob(os.path.join(p, "*"))):
                if q.lower().endswith(exts):
                    yield q, cv2.imread(q)
        elif p.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
            import imageio_ffmpeg
            rd = imageio_ffmpeg.read_frames(p)
            meta = next(rd)
            W, H = meta["size"]
            for k, fr in enumerate(rd):
                if k % every == 0:
                    rgb = np.frombuffer(fr, np.uint8).reshape(H, W, 3)
                    yield f"{p}#frame{k}", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        else:
            yield p, cv2.imread(p)


def build_ref():
    sc = Scorer()
    src = IDENT / "face_clean_1024.png"
    img = cv2.imread(str(src))
    embs = []
    for im in (img, img[:, ::-1].copy()):
        fs = sc.faces(im)
        if not fs:
            raise SystemExit(f"no face in {src}")
        embs.append(max(fs, key=lambda f: f["score"])["emb"])
    ref = np.mean(embs, 0)
    ref /= np.linalg.norm(ref)
    np.save(REF, ref)
    cv2.imwrite(str(IDENT / "arcface_aligned_112.png"), sc.faces(img)[0]["crop"])
    print(f"reference embedding -> {REF} (from {src.name} + mirror, self-similarity {float(embs[0] @ embs[1]):.3f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="*")
    ap.add_argument("--every", type=int, default=12, help="video: score every Nth frame")
    ap.add_argument("--json")
    ap.add_argument("--build-ref", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    a = ap.parse_args()
    if a.build_ref:
        build_ref()
        return
    if a.calibrate:
        import calibrate_similarity
        calibrate_similarity.main()
        return
    sc = Scorer()
    if sc.ref is None:
        raise SystemExit("no reference embedding: run --build-ref first")
    res = {}
    for name, img in iter_inputs(a.inputs, a.every):
        if img is None:
            res[name] = {"error": "unreadable"}
            continue
        r = sc.score(img)
        res[name] = r
        b = "-" if r["best"] is None else f"{r['best']:.3f}"
        print(f"{b:>7}  {r.get('verdict') or '':<15} faces={r['faces']}  {name}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    sys.exit(main())
