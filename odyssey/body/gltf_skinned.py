"""Tiny glTF 2.0 binary (GLB) writer for skinned, textured meshes.  numpy + json only.

    g = GLB()
    tex = g.texture(pil_image, "image/jpeg")
    mat = g.material("skin", base_tex=tex, roughness=0.5)
    joints = g.skeleton(names, parents, translations, rotations_xyzw, inverse_bind (B,4,4))
    g.skinned_mesh("skin", positions, normals, uvs, tris, joints4, weights4, mat)
    g.animation("stand", {bone_index: quats_xyzw (K,4)}, times)
    g.save("out.glb")

UVs are given MakeHuman/OpenGL style (v up) and flipped to glTF (v down) here.
"""
from __future__ import annotations

import io
import json
import struct

import numpy as np

FLOAT, UINT, USHORT, UBYTE = 5126, 5125, 5123, 5121
ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER = 34962, 34963


def tangents(pos, nrm, uv_gltf, tris):
    """Per-vertex tangents (Lengyel) for glTF: xyz along +u, w = handedness so that
    bitangent = cross(normal, tangent) * w points along -v_gltf (= +v in OpenGL / 'up' in the image)."""
    pos = np.asarray(pos, np.float64)
    nrm = np.asarray(nrm, np.float64)
    uv = np.asarray(uv_gltf, np.float64).copy()
    uv[:, 1] = 1.0 - uv[:, 1]                    # back to OpenGL v (up) for the usual derivation
    p0, p1, p2 = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
    w0, w1, w2 = uv[tris[:, 0]], uv[tris[:, 1]], uv[tris[:, 2]]
    e1, e2 = p1 - p0, p2 - p0
    d1, d2 = w1 - w0, w2 - w0
    r = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    r = np.where(np.abs(r) < 1e-12, 1e-12, r)
    sdir = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / r[:, None]
    tdir = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / r[:, None]
    T = np.zeros_like(pos)
    B = np.zeros_like(pos)
    for k in range(3):
        np.add.at(T, tris[:, k], sdir)
        np.add.at(B, tris[:, k], tdir)
    T = T - nrm * np.sum(nrm * T, 1, keepdims=True)
    ln = np.linalg.norm(T, axis=1, keepdims=True)
    fallback = np.cross(nrm, np.array([0.0, 1.0, 0.0]))
    T = np.where(ln > 1e-12, T / np.maximum(ln, 1e-12), fallback)
    w = np.where(np.sum(np.cross(nrm, T) * B, 1) < 0, -1.0, 1.0)
    return np.concatenate([T, w[:, None]], 1).astype(np.float32)


class GLB:
    def __init__(self, generator="odyssey/body/gltf_skinned.py"):
        self.j = {"asset": {"version": "2.0", "generator": generator}, "scene": 0,
                  "scenes": [{"name": "Scene", "nodes": []}], "nodes": [], "meshes": [], "materials": [],
                  "textures": [], "images": [], "samplers": [{"magFilter": 9729, "minFilter": 9987,
                                                              "wrapS": 10497, "wrapT": 10497}],
                  "accessors": [], "bufferViews": [], "buffers": [{"byteLength": 0}], "skins": [],
                  "animations": []}
        self.bin = bytearray()
        self.skin_index = None
        self.root = None
        self.ext_used = set()

    # ------------------------------------------------------------------ raw data
    def _view(self, data: bytes, target=None):
        while len(self.bin) % 4:
            self.bin += b"\0"
        bv = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            bv["target"] = target
        self.bin += data
        self.j["bufferViews"].append(bv)
        return len(self.j["bufferViews"]) - 1

    def accessor(self, arr, ctype, atype, target=None, minmax=False, normalized=False):
        arr = np.ascontiguousarray(arr)
        view = self._view(arr.tobytes(), target)
        count = arr.shape[0]
        acc = {"bufferView": view, "componentType": ctype, "count": int(count), "type": atype}
        if normalized:
            acc["normalized"] = True
        if minmax:
            a2 = arr.reshape(count, -1)
            acc["min"] = [float(x) for x in a2.min(0)]
            acc["max"] = [float(x) for x in a2.max(0)]
        self.j["accessors"].append(acc)
        return len(self.j["accessors"]) - 1

    # ------------------------------------------------------------------ materials
    def texture(self, img, mime="image/png", quality=92, name=None):
        buf = io.BytesIO()
        if mime == "image/jpeg":
            img.convert("RGB").save(buf, "JPEG", quality=quality, subsampling=0, optimize=True)
        else:
            img.save(buf, "PNG", optimize=False, compress_level=6)
        view = self._view(buf.getvalue())
        im = {"bufferView": view, "mimeType": mime}
        if name:
            im["name"] = name
        self.j["images"].append(im)
        self.j["textures"].append({"sampler": 0, "source": len(self.j["images"]) - 1})
        return len(self.j["textures"]) - 1

    def material(self, name, base_tex=None, base_color=(1, 1, 1, 1), roughness=0.8, metallic=0.0,
                 normal_tex=None, normal_scale=1.0, orm_tex=None, occlusion_strength=1.0,
                 alpha_mode="OPAQUE", alpha_cutoff=None, double_sided=False, sheen=None, extras=None,
                 specular=None):
        pbr = {"baseColorFactor": [float(x) for x in base_color], "metallicFactor": float(metallic),
               "roughnessFactor": float(roughness)}
        if base_tex is not None:
            pbr["baseColorTexture"] = {"index": base_tex}
        if orm_tex is not None:
            pbr["metallicRoughnessTexture"] = {"index": orm_tex}
        m = {"name": name, "pbrMetallicRoughness": pbr, "alphaMode": alpha_mode, "doubleSided": bool(double_sided)}
        if orm_tex is not None:
            m["occlusionTexture"] = {"index": orm_tex, "strength": float(occlusion_strength)}
        if normal_tex is not None:
            m["normalTexture"] = {"index": normal_tex, "scale": float(normal_scale)}
        if alpha_mode == "MASK":
            m["alphaCutoff"] = float(alpha_cutoff if alpha_cutoff is not None else 0.5)
        if sheen:
            m.setdefault("extensions", {})["KHR_materials_sheen"] = {
                "sheenColorFactor": [float(x) for x in sheen[0]], "sheenRoughnessFactor": float(sheen[1])}
            self.ext_used.add("KHR_materials_sheen")
        if specular is not None:   # KHR_materials_specular: scales the dielectric F0 (1 = default 4%)
            m.setdefault("extensions", {})["KHR_materials_specular"] = {"specularFactor": float(specular)}
            self.ext_used.add("KHR_materials_specular")
        if extras:
            m["extras"] = extras
        self.j["materials"].append(m)
        return len(self.j["materials"]) - 1

    # ------------------------------------------------------------------ nodes
    def node(self, **kw):
        self.j["nodes"].append({k: v for k, v in kw.items() if v is not None})
        return len(self.j["nodes"]) - 1

    def skeleton(self, names, parents, t, q, inverse_bind, root_name="body_base"):
        """Joint nodes (parents first) under a scene root node; returns joint node indices."""
        self.root = self.node(name=root_name, children=[])
        self.j["scenes"][0]["nodes"].append(self.root)
        idx = []
        for i, n in enumerate(names):
            idx.append(self.node(name=n, translation=[float(x) for x in t[i]],
                                 rotation=[float(x) for x in q[i]]))
        for i, p in enumerate(parents):
            if p < 0:
                self.j["nodes"][self.root]["children"].append(idx[i])
            else:
                self.j["nodes"][idx[p]].setdefault("children", []).append(idx[i])
        ibm = self.accessor(np.asarray(inverse_bind, np.float32).transpose(0, 2, 1).reshape(-1, 16), FLOAT, "MAT4")
        root_j = [idx[i] for i, p in enumerate(parents) if p < 0][0]
        self.j["skins"].append({"name": "mh_default", "joints": idx, "inverseBindMatrices": ibm,
                                "skeleton": root_j})
        self.skin_index = len(self.j["skins"]) - 1
        self.joint_nodes = idx
        return idx

    def skinned_mesh(self, name, pos, nrm, uv, tris, joints, weights, material, extras=None, targets=None,
                     with_tangents=False, compact_skin=False):
        """targets: optional [(name, dpos (N,3), dnrm (N,3))] morph targets, default weight 1 each."""
        pos = np.asarray(pos, np.float32)
        attrs = {"POSITION": self.accessor(pos, FLOAT, "VEC3", ARRAY_BUFFER, minmax=True),
                 "NORMAL": self.accessor(np.asarray(nrm, np.float32), FLOAT, "VEC3", ARRAY_BUFFER)}
        if uv is not None:
            uvg = np.asarray(uv, np.float32).copy()
            uvg[:, 1] = 1.0 - uvg[:, 1]
            attrs["TEXCOORD_0"] = self.accessor(uvg, FLOAT, "VEC2", ARRAY_BUFFER)
            if with_tangents:
                attrs["TANGENT"] = self.accessor(tangents(pos, nrm, uvg, np.asarray(tris)), FLOAT, "VEC4",
                                                 ARRAY_BUFFER)
        if joints is not None:
            w = np.asarray(weights, np.float32)
            w = w / w.sum(1, keepdims=True)
            if compact_skin:  # u8 joints + u8-normalised weights (exact for rigid 1-bone skinning)
                assert np.asarray(joints).max() < 256
                w8 = np.round(w * 255).astype(np.int64)
                w8[:, 0] += 255 - w8.sum(1)
                attrs["JOINTS_0"] = self.accessor(np.asarray(joints, np.uint8), UBYTE, "VEC4", ARRAY_BUFFER)
                attrs["WEIGHTS_0"] = self.accessor(w8.astype(np.uint8), UBYTE, "VEC4", ARRAY_BUFFER, normalized=True)
            else:
                attrs["JOINTS_0"] = self.accessor(np.asarray(joints, np.uint16), USHORT, "VEC4", ARRAY_BUFFER)
                attrs["WEIGHTS_0"] = self.accessor(w, FLOAT, "VEC4", ARRAY_BUFFER)
        tris = np.asarray(tris)
        ind = self.accessor(tris.astype(np.uint32).ravel(), UINT, "SCALAR", ELEMENT_ARRAY_BUFFER)
        prim = {"attributes": attrs, "indices": ind, "material": material, "mode": 4}
        mesh = {"name": name, "primitives": [prim]}
        extras = dict(extras or {})
        if targets:
            prim["targets"] = [{"POSITION": self.accessor(np.asarray(dp, np.float32), FLOAT, "VEC3", ARRAY_BUFFER,
                                                          minmax=True),
                                "NORMAL": self.accessor(np.asarray(dn, np.float32), FLOAT, "VEC3", ARRAY_BUFFER)}
                               for _, dp, dn in targets]
            mesh["weights"] = [1.0] * len(targets)
            extras["targetNames"] = [t[0] for t in targets]
        if extras:
            mesh["extras"] = extras
        self.j["meshes"].append(mesh)
        n = self.node(name=name, mesh=len(self.j["meshes"]) - 1,
                      skin=self.skin_index if joints is not None else None)
        # skinned meshes live at the scene root (parent transforms never apply to them)
        self.j["scenes"][0]["nodes"].append(n)
        return n

    def animation(self, name, rotations: dict, times, translations: dict | None = None):
        """rotations: joint list index -> (K,4) xyzw quats at `times` (K,); translations likewise (K,3)."""
        t_acc = self.accessor(np.asarray(times, np.float32).reshape(-1), FLOAT, "SCALAR", minmax=True)
        samplers, channels = [], []
        for bi, tr in (translations or {}).items():
            o = self.accessor(np.asarray(tr, np.float32).reshape(-1, 3), FLOAT, "VEC3")
            samplers.append({"input": t_acc, "output": o, "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1,
                             "target": {"node": self.joint_nodes[bi], "path": "translation"}})
        for bi, q in rotations.items():
            o = self.accessor(np.asarray(q, np.float32).reshape(-1, 4), FLOAT, "VEC4")
            samplers.append({"input": t_acc, "output": o, "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1,
                             "target": {"node": self.joint_nodes[bi], "path": "rotation"}})
        self.j["animations"].append({"name": name, "samplers": samplers, "channels": channels})

    # ------------------------------------------------------------------ output
    def save(self, path, extras=None):
        for k in ("skins", "animations", "textures", "images", "materials"):
            if not self.j[k]:
                del self.j[k]
        if self.ext_used:
            self.j["extensionsUsed"] = sorted(self.ext_used)
        if extras:
            self.j["scenes"][0]["extras"] = extras
        while len(self.bin) % 4:
            self.bin += b"\0"
        self.j["buffers"][0]["byteLength"] = len(self.bin)
        js = json.dumps(self.j, separators=(",", ":")).encode("utf-8")
        js += b" " * ((4 - len(js) % 4) % 4)
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        with open(path, "wb") as f:
            f.write(struct.pack("<4sII", b"glTF", 2, total))
            f.write(struct.pack("<I4s", len(js), b"JSON"))
            f.write(js)
            f.write(struct.pack("<I4s", len(self.bin), b"BIN\0"))
            f.write(self.bin)
        return total
