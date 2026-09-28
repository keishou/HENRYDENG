"""Procedural textures that turn MakeHuman's male_casualsuit02 (crew-neck long-sleeve tee + jeans, CC0)
into a black fine-knit henley (rib neck band, cuffs and hem, short button placket with light horn buttons)
and dark charcoal trousers.

Nothing here comes from the subject's photo: colours and sizes are art-directed constants.
Only the garment's own maps are reused (jeans normal / AO / luminance detail).

    tex = make_suit_textures(proxy, fitted_v_dm, size=4096)
    tex["base"], tex["normal"], tex["orm"]   # PIL images (sRGB base, OpenGL/glTF normal, AO-rough-metal)

UV conventions: MakeHuman v points up (OpenGL); image row 0 is v = 1, as in glTF after v -> 1 - v.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage


def srgb_to_lin(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.clip(np.asarray(c, np.float32), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


# ----------------------------------------------------------------------------- rasterisation
def rasterize(tri_uv, tri_attr, tri_label, size):
    """Rasterise UV triangles (T,3,2) into a size^2 grid.  Returns label map (-1 = empty) and the
    barycentrically interpolated per-corner attribute (T,3,C) -> (size,size,C)."""
    C = tri_attr.shape[2]
    lab = -np.ones((size, size), np.int32)
    out = np.zeros((size, size, C), np.float32)
    P = np.stack([tri_uv[..., 0] * size, (1 - tri_uv[..., 1]) * size], -1)  # pixel coords (x, row)
    for t in range(len(P)):
        a, b, c = P[t]
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not m.any():
            continue
        yy, xx = np.nonzero(m)
        yy += y0
        xx += x0
        lab[yy, xx] = tri_label[t]
        out[yy, xx] = (l1[m, None] * tri_attr[t, 0] + l2[m, None] * tri_attr[t, 1] + l3[m, None] * tri_attr[t, 2])
    return lab, out


def dilate(img, valid, iterations=None):
    """Fill invalid texels with the nearest valid texel (texture padding against mip bleeding)."""
    idx = ndimage.distance_transform_edt(~valid, return_distances=False, return_indices=True)
    return img[idx[0], idx[1]]


def _seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    t = np.clip(((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy), 0, 1)
    return np.hypot(px - (ax + t * vx), py - (ay + t * vy))


# ----------------------------------------------------------------------------- knit height fields
def jersey_height(u_cm, v_cm, wale=0.30, course=0.26, rng=None):
    """Plain (jersey) knit face: columns of V-shaped loops.  u across wales, v along the wale (up)."""
    a = u_cm / wale
    b = v_cm / course
    col = np.floor(a)
    xa = a - col - 0.5                      # [-0.5, 0.5) across the wale
    # alternate the course phase a little per column so it does not look like a grid
    fb = (b + 0.07 * np.sin(col * 1.7)) % 1.0
    h = np.zeros_like(u_cm, dtype=np.float32)
    for s in (-1.0, 1.0):                   # two legs of the V, top-outside to bottom-centre
        for off in (-1.0, 0.0, 1.0):        # neighbouring courses overlap
            d = _seg_dist(xa, (fb + off) * (course / wale), s * 0.40, 1.05 * (course / wale),
                          s * 0.06, -0.05 * (course / wale))
            h = np.maximum(h, np.clip(1 - (d / 0.21) ** 2, 0, 1) ** 0.5)
    if rng is not None:
        h *= 0.85 + 0.15 * rng.random(h.shape, dtype=np.float32)
    return h


def rib_height(u_cm, period=0.36):
    """1x1 rib: alternating raised knit columns and sunken purl columns."""
    x = (u_cm / period) % 1.0
    return (0.5 + 0.5 * np.cos(2 * np.pi * x)).astype(np.float32) ** 0.7


def height_to_normal(h, strength):
    gy, gx = np.gradient(h.astype(np.float32))   # d/drow, d/dcol
    n = np.stack([-strength * gx, strength * gy, np.ones_like(h)], -1)   # +Y = up in the image
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n


def blend_normals(base, detail):
    """Reoriented normal mapping (unpacked [-1,1] tangent-space normals)."""
    t = base + np.array([0, 0, 1.0], np.float32)
    u = detail * np.array([-1, -1, 1.0], np.float32)
    r = t * np.sum(t * u, -1, keepdims=True) / t[..., 2:3] - u
    return r / np.linalg.norm(r, axis=-1, keepdims=True)


# ----------------------------------------------------------------------------- main
def make_suit_textures(proxy, fitted_v_dm, size=4096, base_size=2048, seed=7,
                       knit_srgb=(24, 25, 30), trouser_srgb=(42, 43, 48), button_srgb=(202, 178, 142),
                       placket_len_cm=9.5, placket_w_cm=2.3, n_buttons=3, log=print):
    rng = np.random.default_rng(seed)
    m = proxy.mesh
    pos_cm = fitted_v_dm * 10.0
    tv, tu = m.triangles()
    # islands (UV connectivity)
    import scipy.sparse as sp
    from scipy.sparse.csgraph import connected_components
    F = len(m.fuv)
    A = sp.csr_matrix((np.ones(F * 4), (np.repeat(np.arange(F), 4), m.fuv.ravel())), shape=(F, len(m.vt)))
    _, flab = connected_components(A @ A.T)
    # shirt vs trousers: shirt islands sit above the shirt hem in 3D
    cent = np.array([pos_cm[m.fv[flab == i].ravel()].mean(0) for i in range(flab.max() + 1)])
    shirt_isl = set(np.nonzero(cent[:, 1] > cent[:, 1].min() + 40)[0].tolist())
    # triangle -> face label (triangles(): first all a-b-c, then quads' a-c-d)
    quad = m.fv[:, 3] != m.fv[:, 2]
    tri_face = np.concatenate([np.arange(F), np.nonzero(quad)[0]])
    tri_lab = flab[tri_face]
    lab, P = rasterize(m.vt[tu], pos_cm[tv], tri_lab, size)
    valid = lab >= 0
    shirt = np.isin(lab, list(shirt_isl))
    trous = valid & ~shirt
    log(f"  suit texture {size}: islands {flab.max() + 1}, shirt islands {sorted(shirt_isl)}, "
        f"coverage {valid.mean():.2f}")
    # uv density -> cm coordinates in texture space
    e3 = np.linalg.norm(pos_cm[tv[:, 1]] - pos_cm[tv[:, 0]], axis=1)
    eu = np.linalg.norm(m.vt[tu[:, 1]] - m.vt[tu[:, 0]], axis=1)
    px_per_cm = float(np.median(eu / np.maximum(e3, 1e-9))) * size
    rows, cols = np.mgrid[0:size, 0:size].astype(np.float32)
    u_cm = cols / px_per_cm
    v_cm = (size - rows) / px_per_cm
    # ---- garment landmarks from the boundary loops (rest pose)
    k = np.where(m.fv[:, 3] == m.fv[:, 2], 3, 4)
    from collections import Counter
    ec = Counter()
    for f, kk in zip(m.fv, k):
        for j in range(kk):
            a, b = f[j], f[(j + 1) % kk]
            ec[(min(a, b), max(a, b))] += 1
    be = np.array([e for e, c in ec.items() if c == 1])
    G = sp.csr_matrix((np.ones(len(be)), (be[:, 0], be[:, 1])), shape=(len(pos_cm),) * 2)
    _, blab = connected_components(G + G.T)
    loops = {}
    for L in np.unique(blab[np.unique(be)]):
        ids = np.unique(be)[blab[np.unique(be)] == L]
        loops[L] = ids
    shirt_verts = np.unique(m.fv[np.isin(flab, list(shirt_isl))])
    sloops = {L: ids for L, ids in loops.items() if np.isin(ids, shirt_verts).all()}
    neck = max(sloops, key=lambda L: pos_cm[sloops[L], 1].mean())
    hem = min(sloops, key=lambda L: pos_cm[sloops[L], 1].mean())
    cuffs = [L for L in sloops if L not in (neck, hem)]

    def loop_dist(L):
        # densify loop polyline by sampling edges
        es = [e for e in be if blab[e[0]] == L]
        pts = np.concatenate([pos_cm[a][None] * (1 - t) + pos_cm[b][None] * t
                              for a, b in es for t in np.linspace(0, 1, 12)[:, None]])
        from scipy.spatial import cKDTree
        d = np.full((size, size), 1e9, np.float32)
        d[shirt] = cKDTree(pts).query(P[shirt], k=1)[0]
        return d

    d_neck, d_hem = loop_dist(neck), loop_dist(hem)
    d_cuff = np.minimum(*[loop_dist(L) for L in cuffs]) if len(cuffs) >= 2 else np.full((size, size), 1e9)
    neck_front = pos_cm[sloops[neck]][np.argmax(pos_cm[sloops[neck], 2])]
    log(f"  px/cm {px_per_cm:.1f}; neck front at {np.round(neck_front, 1)} cm; loops neck/hem/cuffs "
        f"{len(sloops[neck])}/{len(sloops[hem])}/{[len(sloops[c]) for c in cuffs]}")
    # ---- height field
    h = np.zeros((size, size), np.float32)
    rough = np.full((size, size), 0.9, np.float32)
    jer = jersey_height(u_cm, v_cm, rng=rng)
    rib = rib_height(u_cm)
    NECK_BAND, CUFF_BAND, HEM_BAND = 1.7, 6.0, 4.5
    band = shirt & ((d_neck < NECK_BAND) | (d_cuff < CUFF_BAND) | (d_hem < HEM_BAND))
    body_knit = shirt & ~band
    h[body_knit] = jer[body_knit]
    h[band] = rib[band] * 1.2
    # seam where each band joins the body (a small tuck)
    for d, w in ((d_neck, NECK_BAND), (d_cuff, CUFF_BAND), (d_hem, HEM_BAND)):
        s = shirt & (np.abs(d - w) < 0.12)
        h[s] -= 0.6
    # side/shoulder/sleeve seams: island borders inside the shirt
    edge_d = ndimage.distance_transform_edt(shirt) / px_per_cm
    s = shirt & (edge_d < 0.18)
    h[s] -= 0.5 * (1 - edge_d[s] / 0.18)
    # ---- henley placket on the front: centred at x = 0, hanging from the neck band
    front = shirt & (P[..., 2] > 0) & (np.abs(P[..., 0]) < 6) & (P[..., 1] > neck_front[1] - 20)
    top_y = neck_front[1]
    px_x = P[..., 0]
    px_y = P[..., 1]
    placket = front & (np.abs(px_x) < placket_w_cm / 2) & (px_y > top_y - placket_len_cm) & (px_y < top_y + 0.5)
    h[placket] = 0.35 + 0.35 * jer[placket]
    # placket edge stitching (two rows of stitches, 3 mm in) and outline groove
    ex = np.abs(np.abs(px_x) - placket_w_cm / 2)
    groove = front & (ex < 0.07) & (px_y > top_y - placket_len_cm) & (px_y < top_y + 0.3)
    h[groove] -= 0.9
    bottom = front & (np.abs(px_y - (top_y - placket_len_cm)) < 0.07) & (np.abs(px_x) < placket_w_cm / 2 + 0.05)
    h[bottom] -= 0.9
    stitch = front & placket & (np.abs(np.abs(px_x) - (placket_w_cm / 2 - 0.3)) < 0.035) & \
        (((px_y * 4.0) % 1.0) < 0.6)
    h[stitch] -= 0.35
    # opening: centre slit from the neck band down to the first button (the photo's small notch)
    slit = front & (np.abs(px_x) < 0.05) & (px_y > top_y - 2.6) & (px_y < top_y + 0.5)
    h[slit] -= 1.2
    # buttons
    but = np.zeros((size, size), bool)
    by = [top_y - 2.6 - i * 2.9 for i in range(n_buttons)]
    R = 0.55
    for y0 in by:
        r = np.hypot(px_x, px_y - y0)
        m_ = front & (r < R)
        but |= m_
        dome = np.sqrt(np.clip(1 - (r[m_] / R) ** 2, 0, 1))
        rim = np.clip(1 - np.abs(r[m_] - 0.78 * R) / (0.1 * R), 0, 1)
        holes = np.zeros_like(dome)
        for hx in (-0.13, 0.13):
            rh = np.hypot(px_x[m_] - hx, px_y[m_] - y0)
            holes = np.maximum(holes, np.clip(1 - rh / 0.07, 0, 1))
        h[m_] = 1.6 + 1.1 * dome - 0.25 * rim - 1.2 * holes
        rough[m_] = 0.32
        # thread cross in the holes, shadow ring around the button
        ring = front & (r >= R) & (r < R + 0.12)
        h[ring] -= 0.4 * (1 - (r[ring] - R) / 0.12)
    rough[band] = 0.93
    rough[trous] = 0.82
    # ---- normals
    strength_knit = 0.16 * (px_per_cm / 23.5)   # tuned by eye at 4096 px (~23.5 px/cm)
    hs = ndimage.gaussian_filter(h, 0.6)
    n_shirt = height_to_normal(hs, strength_knit * 6)
    # button/placket read stronger: use a smoothed, higher-gain copy there
    hb = ndimage.gaussian_filter(h, 1.2)
    n_btn = height_to_normal(hb, strength_knit * 9)
    n_shirt[but | placket] = n_btn[but | placket]
    normal = np.zeros((size, size, 3), np.float32)
    normal[..., 2] = 1
    normal[shirt] = n_shirt[shirt]
    # trousers: keep the garment's own fold normal map
    mat = proxy.material or {}
    if mat.get("normalmapTexture_abs"):
        on = np.asarray(Image.open(mat["normalmapTexture_abs"]).convert("RGB").resize((size, size), Image.BICUBIC),
                        np.float32) / 127.5 - 1
        on /= np.linalg.norm(on, axis=-1, keepdims=True)
        normal[trous] = on[trous]
    # ---- base colour (linear), then sRGB
    knit_lin = srgb_to_lin(np.array(knit_srgb) / 255.0)
    tr_lin = srgb_to_lin(np.array(trouser_srgb) / 255.0)
    bt_lin = srgb_to_lin(np.array(button_srgb) / 255.0)
    base = np.zeros((size, size, 3), np.float32)
    # knit: yarn cavities darker, very low-frequency heather so large areas do not look flat
    heather = ndimage.gaussian_filter(rng.standard_normal((size // 16, size // 16)).astype(np.float32), 2)
    heather = np.kron(heather / (heather.std() + 1e-6), np.ones((16, 16), np.float32))
    shade = 0.78 + 0.34 * np.clip(hs, 0, 1.2) + 0.04 * heather
    base[shirt] = knit_lin * shade[shirt, None]
    # buttons: horn/wood with a darker rim and grain
    if but.any():
        grain = 0.9 + 0.1 * np.sin(px_y[but] * 40 + 3 * np.sin(px_x[but] * 9))
        rr = np.clip(np.hypot(px_x[but], (px_y[but] - np.array(by)[np.argmin(np.abs(px_y[but, None] - np.array(by)[None]), 1)])) / R, 0, 1)
        base[but] = bt_lin * (grain * (1.0 - 0.35 * rr ** 4))[:, None]
        holes_m = h[but] < 1.0
        base[np.nonzero(but)[0][holes_m], np.nonzero(but)[1][holes_m]] *= 0.3
    # trousers: luminance detail of the original jeans, contrast squeezed into charcoal
    if mat.get("diffuseTexture_abs"):
        od = np.asarray(Image.open(mat["diffuseTexture_abs"]).convert("RGB").resize((size, size), Image.BICUBIC),
                        np.float32) / 255.0
        lum = srgb_to_lin(od) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        mu = float(np.median(lum[trous]))
        rel = np.clip(lum / max(mu, 1e-4), 0.3, 3.0)
        base[trous] = tr_lin * (rel[trous] ** 0.3)[:, None]
    # ---- AO (garment's own map) -> ORM
    ao = np.ones((size, size), np.float32)
    if mat.get("aomapTexture_abs"):
        ao = np.asarray(Image.open(mat["aomapTexture_abs"]).convert("L").resize((size, size), Image.BICUBIC),
                        np.float32) / 255.0
        ao = 0.35 + 0.65 * ao
    ao[shirt] *= (0.85 + 0.15 * np.clip(hs[shirt], 0, 1))
    # ---- pad + pack
    base = dilate(base, valid)
    normal = dilate(normal, valid)
    rough = dilate(rough, valid)
    ao = dilate(ao, valid)
    base8 = (lin_to_srgb(base) * 255 + 0.5).astype(np.uint8)
    nrm8 = ((normal * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)
    orm8 = (np.stack([ao, rough, np.zeros_like(ao)], -1) * 255 + 0.5).astype(np.uint8)
    base_img = Image.fromarray(base8)
    orm_img = Image.fromarray(orm8)
    if base_size and base_size != size:
        base_img = base_img.resize((base_size, base_size), Image.LANCZOS)
        orm_img = orm_img.resize((base_size, base_size), Image.LANCZOS)
    info = {"px_per_cm": px_per_cm, "shirt_islands": sorted(int(i) for i in shirt_isl),
            "neck_front_cm": neck_front.tolist(), "buttons_y_cm": by}
    return {"base": base_img, "normal": Image.fromarray(nrm8), "orm": orm_img, "info": info,
            "masks": {"shirt": shirt, "trousers": trous, "placket": placket, "buttons": but}}
