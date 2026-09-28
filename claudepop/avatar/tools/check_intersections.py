#!/usr/bin/env python3
"""Penetration check of subject.glb in the rest pose.

For every vertex of hair, fringe strands, top, trousers, shoes and eyes: signed distance to the body skin along the
nearest skin vertex's normal (negative = inside the body).  Hair and fringe vertices only count where their texture
is opaque (alpha >= the material cutoff).  Writes check/intersections.json.
"""
from __future__ import annotations

import io
import json
import struct

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree

from avlib import CHECK, OUT


def read_glb(path):
    b = open(path, "rb").read()
    L = struct.unpack("<I", b[12:16])[0]
    g = json.loads(b[20:20 + L])
    binoff = 20 + L + 8
    blob = b[binoff:]

    def acc(i):
        a = g["accessors"][i]
        bv = g["bufferViews"][a["bufferView"]]
        dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]]
        n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        arr = np.frombuffer(blob, dt, a["count"] * n, bv.get("byteOffset", 0))
        return arr.reshape(a["count"], n) if n > 1 else arr

    def image(tex_index):
        img = g["images"][g["textures"][tex_index]["source"]]
        bv = g["bufferViews"][img["bufferView"]]
        data = blob[bv["byteOffset"]:bv["byteOffset"] + bv["byteLength"]]
        return np.asarray(Image.open(io.BytesIO(data)).convert("RGBA"), np.float32) / 255

    meshes = {}
    for m in g["meshes"]:
        p = m["primitives"][0]
        mat = g["materials"][p["material"]]
        at = p["attributes"]
        d = dict(pos=acc(at["POSITION"]).astype(np.float64), idx=acc(p["indices"]).reshape(-1, 3),
                 uv=acc(at["TEXCOORD_0"]) if "TEXCOORD_0" in at else None, mat=mat)
        t = mat["pbrMetallicRoughness"].get("baseColorTexture")
        d["tex"] = image(t["index"]) if t is not None and mat.get("alphaMode") in ("MASK", "BLEND") else None
        meshes[m["name"]] = d
    return meshes


def vnormals(v, f):
    n = np.zeros_like(v)
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def main():
    M = read_glb(OUT / "subject.glb")
    skin = M["skin"]
    # weld the skin's UV-seam duplicates so normals are continuous
    key = np.round(skin["pos"] * 1e5).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    wn = np.zeros((inv.max() + 1, 3))
    fn = np.cross(skin["pos"][skin["idx"][:, 1]] - skin["pos"][skin["idx"][:, 0]],
                  skin["pos"][skin["idx"][:, 2]] - skin["pos"][skin["idx"][:, 0]])
    for k in range(3):
        np.add.at(wn, inv[skin["idx"][:, k]], fn)
    sn = wn[inv] / np.maximum(np.linalg.norm(wn[inv], axis=1, keepdims=True), 1e-12)
    tree = cKDTree(skin["pos"])
    res = {}
    for name, d in M.items():
        if name in ("skin", "teeth", "tongue", "cornea"):
            continue
        v = d["pos"]
        ok = np.ones(len(v), bool)
        # ribbon strands: their vertices sit on the ribbon edges, where the fibre texture is transparent; check them all
        if d["tex"] is not None and d["uv"] is not None and name != "hair_strands":
            tx = d["tex"]
            h, w = tx.shape[:2]
            a = tx[np.clip((d["uv"][:, 1] * h).astype(int), 0, h - 1), np.clip((d["uv"][:, 0] * w).astype(int), 0, w - 1), 3]
            ok = a >= d["mat"].get("alphaCutoff", 0.5 if d["mat"].get("alphaMode") == "MASK" else 0.1)
        dist, j = tree.query(v)
        sd = ((v - skin["pos"][j]) * sn[j]).sum(1)
        near = dist < 0.03
        inside = ok & near & (sd < -0.001)
        res[name] = {"vertices": int(len(v)), "checked": int((ok & near).sum()), "inside_skin_gt_1mm": int(inside.sum()),
                     "worst_mm": float(-sd[ok & near].min() * 1000) if (ok & near).any() else 0.0}
    (CHECK / "intersections.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
