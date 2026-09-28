"""Shared helpers for the protagonist avatar build (claudepop/avatar/tools).

Paths, MakeHuman access (reuses odyssey/body/mh_assets.py read-only), a vectorised numpy
triangle rasteriser (screen space with z-buffer, or UV space for texture baking), rig joint
evaluation from MPFB2 rig.default.json, and a minimal skinned glTF 2.0 (GLB) writer.

All subject-derived data is written under claudepop/out/avatar/ (gitignored); this file holds code only.
"""
from __future__ import annotations

import io
import json
import struct
import sys
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[2]
ODY = REPO / "odyssey"
OUT = REPO / "claudepop" / "out" / "avatar"
WORK = OUT / "work"
CHECK = OUT / "check"
IDENT = OUT / "identity"
MODELS = ODY / ".cache" / "models"
MHCACHE = ODY / ".cache" / "makehuman"
MPFB = MHCACHE / "gh" / "mpfb2" / "src" / "mpfb" / "data" / "rigs" / "standard"
DEB = MHCACHE / "ubuntu" / "makehuman-data_1.1.1-1" / "usr" / "share" / "makehuman" / "data"

sys.path.insert(0, str(ODY / "body"))
from mh_assets import MH, N_SKIN, Mesh, height_cm, load_proxy, read_mhmat  # noqa: E402,F401

# Blender (Z up, -Y forward) -> glTF/three (Y up, +Z forward); same matrix as odyssey/body/retarget_mh.py
C_B2Y = np.array([[1.0, 0, 0], [0, 0, 1], [0, -1, 0]])


# ----------------------------------------------------------------------------------------------- raster
def rasterize(P, tris, W, H, Z=None, chunk=6000, cull_back=False):
    """Rasterise triangles.

    P    : (N,2) float pixel coordinates (x right, y down; pixel centres at +0.5).
    tris : (T,3) int.
    Z    : (N,) depth, smaller = closer; None -> no depth test (UV baking, first writer wins).
    Returns tri (H,W) int32 (-1 = empty), bary (H,W,3) float32, depth (H,W) float32.
    """
    P = np.asarray(P, np.float64)
    tris = np.asarray(tris, np.int64)
    tri_buf = np.full(H * W, -1, np.int64)
    dep_buf = np.full(H * W, np.inf)
    bary_buf = np.zeros((H * W, 3), np.float32)
    zz = np.zeros(len(P)) if Z is None else np.asarray(Z, np.float64)
    for s in range(0, len(tris), chunk):
        t = tris[s:s + chunk]
        a, b, c = P[t[:, 0]], P[t[:, 1]], P[t[:, 2]]
        area = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
        ok = np.abs(area) > 1e-12
        if cull_back:
            ok &= area < 0  # counter-clockwise in a y-down image == clockwise in y-up -> back face
        x0 = np.clip(np.floor(np.minimum(np.minimum(a[:, 0], b[:, 0]), c[:, 0]) - 0.5), 0, W - 1).astype(np.int64)
        x1 = np.clip(np.ceil(np.maximum(np.maximum(a[:, 0], b[:, 0]), c[:, 0]) - 0.5), 0, W - 1).astype(np.int64)
        y0 = np.clip(np.floor(np.minimum(np.minimum(a[:, 1], b[:, 1]), c[:, 1]) - 0.5), 0, H - 1).astype(np.int64)
        y1 = np.clip(np.ceil(np.maximum(np.maximum(a[:, 1], b[:, 1]), c[:, 1]) - 0.5), 0, H - 1).astype(np.int64)
        offscreen = (np.maximum(np.maximum(a[:, 0], b[:, 0]), c[:, 0]) < 0) | (np.minimum(np.minimum(a[:, 0], b[:, 0]), c[:, 0]) > W) \
            | (np.maximum(np.maximum(a[:, 1], b[:, 1]), c[:, 1]) < 0) | (np.minimum(np.minimum(a[:, 1], b[:, 1]), c[:, 1]) > H)
        ok &= ~offscreen
        idx = np.nonzero(ok)[0]
        if len(idx) == 0:
            continue
        bw = x1[idx] - x0[idx] + 1
        bh = y1[idx] - y0[idx] + 1
        n = bw * bh
        tot = int(n.sum())
        if tot == 0:
            continue
        rep = np.repeat(np.arange(len(idx)), n)
        start = np.repeat(np.cumsum(n) - n, n)
        k = np.arange(tot) - start
        ti = idx[rep]
        px = x0[ti] + k % bw[rep]
        py = y0[ti] + k // bw[rep]
        cx, cy = px + 0.5, py + 0.5
        A, B, Cc = a[ti], b[ti], c[ti]
        ar = area[ti]
        w0 = ((B[:, 0] - cx) * (Cc[:, 1] - cy) - (B[:, 1] - cy) * (Cc[:, 0] - cx)) / ar
        w1 = ((Cc[:, 0] - cx) * (A[:, 1] - cy) - (Cc[:, 1] - cy) * (A[:, 0] - cx)) / ar
        w2 = 1.0 - w0 - w1
        eps = -1e-7
        inside = (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
        if not inside.any():
            continue
        ti, px, py, w0, w1, w2 = ti[inside], px[inside], py[inside], w0[inside], w1[inside], w2[inside]
        tt = t[ti]
        d = w0 * zz[tt[:, 0]] + w1 * zz[tt[:, 1]] + w2 * zz[tt[:, 2]]
        pid = py * W + px
        order = np.lexsort((d, pid))
        pid, d = pid[order], d[order]
        first = np.r_[True, pid[1:] != pid[:-1]]
        sel = order[first]
        pid, d = pid[first], d[first]
        better = d < dep_buf[pid] if Z is not None else tri_buf[pid] < 0
        pid, d, sel = pid[better], d[better], sel[better]
        dep_buf[pid] = d
        tri_buf[pid] = s + ti[sel]
        bary_buf[pid] = np.stack([w0[sel], w1[sel], w2[sel]], 1)
    return tri_buf.reshape(H, W).astype(np.int32), bary_buf.reshape(H, W, 3), dep_buf.reshape(H, W).astype(np.float32)


def interp(attr, tris, tri_img, bary):
    """Interpolate a per-vertex attribute (N,K) through a raster result -> (H,W,K); empty pixels = 0."""
    attr = np.asarray(attr)
    m = tri_img >= 0
    out = np.zeros(tri_img.shape + attr.shape[1:], np.float64)
    t = tris[tri_img[m]]
    b = bary[m]
    out[m] = (attr[t[:, 0]] * b[:, :1] + attr[t[:, 1]] * b[:, 1:2] + attr[t[:, 2]] * b[:, 2:3])
    return out


def vertex_normals(v, tris):
    fn = np.cross(v[tris[:, 1]] - v[tris[:, 0]], v[tris[:, 2]] - v[tris[:, 0]])
    n = np.zeros_like(v)
    for k in range(3):
        np.add.at(n, tris[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


# ----------------------------------------------------------------------------------------------- camera
class Cam:
    """Pinhole camera. World: Y up. Camera looks down its -Z (OpenGL convention).

    project(X) -> (u, v, depth) with u right, v down in pixels; depth > 0 in front.
    """

    def __init__(self, R, t, f, cx, cy, W, H):
        self.R, self.t, self.f, self.cx, self.cy, self.W, self.H = np.asarray(R, float), np.asarray(t, float), float(f), float(cx), float(cy), int(W), int(H)

    @staticmethod
    def look_at(eye, target, f, W, H, up=(0, 1, 0), cx=None, cy=None):
        eye, target, up = np.asarray(eye, float), np.asarray(target, float), np.asarray(up, float)
        zc = eye - target
        zc /= np.linalg.norm(zc)
        xc = np.cross(up, zc)
        xc /= np.linalg.norm(xc)
        yc = np.cross(zc, xc)
        R = np.stack([xc, yc, zc])  # world -> camera rows
        return Cam(R, -R @ eye, f, W / 2 if cx is None else cx, H / 2 if cy is None else cy, W, H)

    def to_cam(self, X):
        return X @ self.R.T + self.t

    def project(self, X):
        Xc = self.to_cam(X)
        d = -Xc[:, 2]
        u = self.cx + self.f * Xc[:, 0] / d
        v = self.cy - self.f * Xc[:, 1] / d
        return np.stack([u, v, d], 1)

    def eye(self):
        return -self.R.T @ self.t

    def fov_y_deg(self):
        return float(np.degrees(2 * np.arctan(self.H / 2 / self.f)))

    def as_dict(self):
        return dict(R=self.R.tolist(), t=self.t.tolist(), f=self.f, cx=self.cx, cy=self.cy, W=self.W, H=self.H)

    @staticmethod
    def from_dict(d):
        return Cam(d["R"], d["t"], d["f"], d["cx"], d["cy"], d["W"], d["H"])


def render_mesh(cam, v, tris, uv=None, tex=None, color=None, vcolor=None, light=True, bg=0.0, tri_uv=None):
    """Very small software renderer (for landmark detection and checks). Returns float RGB (H,W,3) in [0,1],
    plus the raster buffers. tex: (h,w,3) float; uv per vertex (N,2) glTF convention (v down) or tri_uv (T,3,2)."""
    p = cam.project(v)
    tri_img, bary, dep = rasterize(p[:, :2], tris, cam.W, cam.H, Z=p[:, 2], cull_back=False)
    m = tri_img >= 0
    img = np.full((cam.H, cam.W, 3), bg, np.float64)
    if tex is not None:
        if tri_uv is not None:
            t = tri_img[m]
            b = bary[m]
            uvp = tri_uv[t, 0] * b[:, :1] + tri_uv[t, 1] * b[:, 1:2] + tri_uv[t, 2] * b[:, 2:3]
        else:
            uvp = interp(uv, tris, tri_img, bary)[m]
        th, tw = tex.shape[:2]
        x = np.clip(uvp[:, 0] * tw - 0.5, 0, tw - 1)
        y = np.clip(uvp[:, 1] * th - 0.5, 0, th - 1)
        x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
        x1, y1 = np.minimum(x0 + 1, tw - 1), np.minimum(y0 + 1, th - 1)
        fx, fy = (x - x0)[:, None], (y - y0)[:, None]
        col = (tex[y0, x0] * (1 - fx) * (1 - fy) + tex[y0, x1] * fx * (1 - fy) + tex[y1, x0] * (1 - fx) * fy + tex[y1, x1] * fx * fy)
    elif vcolor is not None:
        col = interp(vcolor, tris, tri_img, bary)[m]
    else:
        col = np.tile(np.asarray(color if color is not None else (0.8, 0.8, 0.8), float), (m.sum(), 1))
    if light:
        n = interp(vertex_normals(v, tris), tris, tri_img, bary)[m]
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        ldir = cam.R.T @ np.array([0.25, 0.35, 1.0])
        ldir /= np.linalg.norm(ldir)
        sh = 0.55 + 0.45 * np.clip(n @ ldir, 0, 1)
        col = col * sh[:, None]
    img[m] = col
    return np.clip(img, 0, 1), tri_img, bary, dep


# ----------------------------------------------------------------------------------------------- rig
def load_rig():
    rig = json.load(open(MPFB / "rig.default.json"))
    order, seen = [], set()

    def visit(n):
        if n in seen:
            return
        p = rig[n]["parent"]
        if p:
            visit(p)
        seen.add(n)
        order.append(n)

    for n in rig:
        visit(n)
    return rig, order


def load_weights():
    w = json.load(open(MPFB / "weights.default.json"))["weights"]
    return w


def joint_position(spec, v_obj, base: Mesh):
    """Evaluate an MPFB2 head/tail spec on MakeHuman OBJ-space vertices (decimetres) -> metres, Y up."""
    s = spec["strategy"]
    if s == "CUBE":
        g = base.groups.index(spec["cube_name"])
        vid = np.unique(base.fv[base.fgroup == g])
        p = v_obj[vid].mean(0)
    elif s == "VERTEX":
        p = v_obj[spec["vertex_index"]]
    elif s == "MEAN":
        p = v_obj[spec["vertex_indices"]].mean(0)
    else:
        raise ValueError(s)
    return p * 0.1


def blender_bone_matrix(head, tail, roll):
    """Blender vec_roll_to_mat3 (same as odyssey/body/retarget_mh.py): columns = bone X, Y(along), Z."""
    nor = tail - head
    nor = nor / np.linalg.norm(nor)
    x, y, z = nor
    theta = 1.0 + y
    theta_alt = x * x + z * z
    if theta > 1e-4 or theta_alt > 1e-12:
        if theta <= 1e-4:
            theta = theta_alt * 0.5 + theta_alt * theta_alt * 0.125
        B = np.column_stack([(1 - x * x / theta, -x, -x * z / theta), (x, y, z), (-x * z / theta, -z, 1 - z * z / theta)])
    else:
        B = np.diag([-1.0, -1.0, 1.0])
    K = np.array([[0, -nor[2], nor[1]], [nor[2], 0, -nor[0]], [-nor[1], nor[0], 0]])
    Rr = np.eye(3) + np.sin(roll) * K + (1 - np.cos(roll)) * K @ K
    return Rr @ B


def skeleton_rest(v_obj, base: Mesh, offset=np.zeros(3)):
    """Rest skeleton for (morphed) OBJ vertices: dict name -> (head_m, tail_m, R_world 3x3) in Y-up metres."""
    rig, order = load_rig()
    out = {}
    for n in order:
        h = joint_position(rig[n]["head"], v_obj, base) + offset
        t = joint_position(rig[n]["tail"], v_obj, base) + offset
        hb, tb = C_B2Y.T @ h, C_B2Y.T @ t  # back to Blender coords for the roll convention
        R = C_B2Y @ blender_bone_matrix(hb, tb, rig[n]["roll"])
        out[n] = (h, t, R)
    parents = {n: (rig[n]["parent"] or None) for n in order}
    return order, parents, out


def top4_weights(wdict, order, nverts):
    """MPFB weights dict -> (N,4) joint indices, (N,4) weights (renormalised; three.js uses 4 influences)."""
    J = np.zeros((nverts, 8), np.int64)
    Wt = np.zeros((nverts, 8))
    cnt = np.zeros(nverts, np.int64)
    bi = {n: i for i, n in enumerate(order)}
    for b, lst in wdict.items():
        for vi, w in lst:
            k = cnt[vi]
            if k < 8:
                J[vi, k], Wt[vi, k] = bi[b], w
                cnt[vi] += 1
    o = np.argsort(-Wt, axis=1)[:, :4]
    J4 = np.take_along_axis(J, o, 1)
    W4 = np.take_along_axis(Wt, o, 1)
    s = W4.sum(1, keepdims=True)
    W4 = W4 / np.maximum(s, 1e-12)
    return J4, W4


def dense_weights(wdict, order, nverts):
    Wd = np.zeros((nverts, len(order)), np.float32)
    bi = {n: i for i, n in enumerate(order)}
    for b, lst in wdict.items():
        for vi, w in lst:
            Wd[vi, bi[b]] = w
    return Wd


def reduce_dense(Wd, k=4):
    o = np.argsort(-Wd, axis=1)[:, :k]
    W = np.take_along_axis(Wd, o, 1)
    W = W / np.maximum(W.sum(1, keepdims=True), 1e-12)
    return o, W


# ----------------------------------------------------------------------------------------------- GLB
def _pad4(b: bytes, pad=b"\x00"):
    return b + pad * ((4 - len(b) % 4) % 4)


def encode_image(img, fmt="JPEG", quality=90):
    from PIL import Image
    if isinstance(img, np.ndarray):
        a = img
        if a.dtype != np.uint8:
            a = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
        img = Image.fromarray(a)
    bio = io.BytesIO()
    if fmt == "JPEG":
        img.convert("RGB").save(bio, "JPEG", quality=quality, subsampling=0)
        return bio.getvalue(), "image/jpeg"
    img.save(bio, "PNG", optimize=True)
    return bio.getvalue(), "image/png"


class GLB:
    """Minimal glTF 2.0 binary writer with skinning, PBR materials and embedded images."""

    def __init__(self):
        self.g = {"asset": {"version": "2.0", "generator": "claudepop avatar tools"}, "scenes": [{"nodes": []}], "scene": 0,
                  "nodes": [], "meshes": [], "accessors": [], "bufferViews": [], "buffers": [], "materials": [],
                  "textures": [], "images": [], "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]}
        self.bin = bytearray()
        self.ext_used = set()

    def _view(self, data: bytes, target=None):
        off = len(self.bin)
        self.bin += _pad4(data)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            bv["target"] = target
        self.g["bufferViews"].append(bv)
        return len(self.g["bufferViews"]) - 1

    def accessor(self, arr, kind, ctype=None, target=None, minmax=False, normalized=False):
        arr = np.ascontiguousarray(arr)
        ct = ctype or {np.dtype("float32"): 5126, np.dtype("uint32"): 5125, np.dtype("uint16"): 5123, np.dtype("uint8"): 5121}[arr.dtype]
        bv = self._view(arr.tobytes(), target)
        acc = {"bufferView": bv, "componentType": ct, "count": int(arr.shape[0]), "type": kind}
        if normalized:
            acc["normalized"] = True
        if minmax:
            a2 = arr.reshape(arr.shape[0], -1)
            acc["min"] = a2.min(0).astype(float).tolist()
            acc["max"] = a2.max(0).astype(float).tolist()
        self.g["accessors"].append(acc)
        return len(self.g["accessors"]) - 1

    def image(self, img, fmt="JPEG", quality=90, name=None):
        key = (id(img), fmt)
        if not hasattr(self, "_img_cache"):
            self._img_cache = {}
        if key in self._img_cache:
            return self._img_cache[key]
        data, mime = encode_image(img, fmt, quality)
        bv = self._view(data)
        self.g["images"].append({"bufferView": bv, "mimeType": mime, **({"name": name} if name else {})})
        self.g["textures"].append({"sampler": 0, "source": len(self.g["images"]) - 1})
        self._img_cache[key] = len(self.g["textures"]) - 1
        return len(self.g["textures"]) - 1

    def material(self, name, base_tex=None, base_color=(1, 1, 1, 1), metallic=0.0, roughness=0.8, normal_tex=None,
                 normal_scale=1.0, alpha="OPAQUE", cutoff=0.5, double=False, mr_tex=None, extensions=None, emissive=None):
        m = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": list(map(float, base_color)), "metallicFactor": float(metallic),
                                                    "roughnessFactor": float(roughness)}, "alphaMode": alpha, "doubleSided": bool(double)}
        if base_tex is not None:
            m["pbrMetallicRoughness"]["baseColorTexture"] = {"index": base_tex}
        if mr_tex is not None:
            m["pbrMetallicRoughness"]["metallicRoughnessTexture"] = {"index": mr_tex}
        if normal_tex is not None:
            m["normalTexture"] = {"index": normal_tex, "scale": float(normal_scale)}
        if alpha == "MASK":
            m["alphaCutoff"] = float(cutoff)
        if emissive is not None:
            m["emissiveFactor"] = list(map(float, emissive))
        if extensions:
            m["extensions"] = extensions
            self.ext_used |= set(extensions)
            if "KHR_materials_anisotropy" in extensions:
                self.ext_used.add("KHR_materials_anisotropy")
        self.g["materials"].append(m)
        return len(self.g["materials"]) - 1

    def mesh(self, name, pos, tris, material, normals=None, uv=None, joints=None, weights=None, tangents=None):
        attrs = {"POSITION": self.accessor(pos.astype(np.float32), "VEC3", target=34962, minmax=True)}
        if normals is not None:
            attrs["NORMAL"] = self.accessor(normals.astype(np.float32), "VEC3", target=34962)
        if tangents is not None:
            attrs["TANGENT"] = self.accessor(tangents.astype(np.float32), "VEC4", target=34962)
        if uv is not None:
            attrs["TEXCOORD_0"] = self.accessor(uv.astype(np.float32), "VEC2", target=34962)
        if joints is not None:
            attrs["JOINTS_0"] = self.accessor(joints.astype(np.uint16 if joints.max() > 255 else np.uint8), "VEC4", target=34962)
            attrs["WEIGHTS_0"] = self.accessor(weights.astype(np.float32), "VEC4", target=34962)
        idx = tris.astype(np.uint32 if len(pos) > 65535 else np.uint16).ravel()
        ia = self.accessor(idx, "SCALAR", target=34963)
        self.g["meshes"].append({"name": name, "primitives": [{"attributes": attrs, "indices": ia, "material": material, "mode": 4}]})
        return len(self.g["meshes"]) - 1

    def node(self, **kw):
        self.g["nodes"].append({k: v for k, v in kw.items() if v is not None})
        return len(self.g["nodes"]) - 1

    def write(self, path, extras=None):
        if extras:
            self.g["asset"]["extras"] = extras
        if self.ext_used:
            self.g["extensionsUsed"] = sorted(self.ext_used)
        for k in ("textures", "images", "samplers", "materials"):
            if not self.g[k]:
                del self.g[k]
        self.g["buffers"] = [{"byteLength": len(self.bin)}]
        js = _pad4(json.dumps(self.g, separators=(",", ":")).encode(), b" ")
        binb = _pad4(bytes(self.bin))
        total = 12 + 8 + len(js) + 8 + len(binb)
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, total))
            f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
            f.write(struct.pack("<II", len(binb), 0x004E4942) + binb)
        return total


def mat_to_quat(M):
    """3x3 -> xyzw."""
    M = np.asarray(M, float)
    tr = np.trace(M)
    if tr > 0:
        s = np.sqrt(tr + 1.0) * 2
        w, x, y, z = 0.25 * s, (M[2, 1] - M[1, 2]) / s, (M[0, 2] - M[2, 0]) / s, (M[1, 0] - M[0, 1]) / s
    elif M[0, 0] > M[1, 1] and M[0, 0] > M[2, 2]:
        s = np.sqrt(1.0 + M[0, 0] - M[1, 1] - M[2, 2]) * 2
        w, x, y, z = (M[2, 1] - M[1, 2]) / s, 0.25 * s, (M[0, 1] + M[1, 0]) / s, (M[0, 2] + M[2, 0]) / s
    elif M[1, 1] > M[2, 2]:
        s = np.sqrt(1.0 + M[1, 1] - M[0, 0] - M[2, 2]) * 2
        w, x, y, z = (M[0, 2] - M[2, 0]) / s, (M[0, 1] + M[1, 0]) / s, 0.25 * s, (M[1, 2] + M[2, 1]) / s
    else:
        s = np.sqrt(1.0 + M[2, 2] - M[0, 0] - M[1, 1]) * 2
        w, x, y, z = (M[1, 0] - M[0, 1]) / s, (M[0, 2] + M[2, 0]) / s, (M[1, 2] + M[2, 1]) / s, 0.25 * s
    q = np.array([x, y, z, w])
    return q / np.linalg.norm(q)


def load_rgb(path):
    from PIL import Image
    return np.asarray(Image.open(path).convert("RGB"), np.float64) / 255.0


def save_rgb(path, img, quality=92):
    from PIL import Image
    a = img if img.dtype == np.uint8 else (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if str(path).lower().endswith((".jpg", ".jpeg")):
        Image.fromarray(a).save(path, quality=quality)
    else:
        Image.fromarray(a).save(path)
