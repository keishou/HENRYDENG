#!/usr/bin/env python3
"""Clothes: black knit henley (custom, grown from the body surface), dark trousers and dark shoes (MakeHuman CC0).

Top    : the body-skin faces of torso + arms (hem at the MakeHuman casualsuit03 shirt length, sleeves to the wrist),
         offset outwards along the normals (6 mm, 12 mm above the trouser waistband), Taubin-smoothed so ribs/navel/
         collarbones do not print through, with a folded 3 mm edge at neckline, cuffs and hem.  It shares the body's
         vertices and is skinned with the body's MPFB2 weights (smoothed along the garment edges, like the edge
         positions, so the edges stay smooth when the neck or arms move).
         Neckline: front-facing vertices whose photo projection lies on the photo's visible neck skin are removed
         (the photo's collar line is measured), the back rises like a crew neck.  The small placket notch and the one
         gold button are placed where the photo shows them.
Trousers: MakeHuman male_casualsuit03, trouser component only, jeans texture desaturated to charcoal.
Shoes  : MakeHuman shoes03 (black).

Outputs (claudepop/out/avatar/work): clothes.npz, top_albedo.png, top_normal.png, pants_albedo.png, button.npz, check
render check/clothes_preview.jpg
"""
from __future__ import annotations

import json

import cv2
import numpy as np
from scipy.spatial import cKDTree

import swr
from avlib import CHECK, MH, WORK, Cam, interp, load_rgb, rasterize, save_rgb, vertex_normals
from bake_texture import push_pull
from mhscene import proxy_part, skin_part, texture_of, unweld

SUIT = "clothes/male_casualsuit03/male_casualsuit03.mhclo"
SHOES = "clothes/shoes03/shoes03.mhclo"
T = 2048


def mesh_adjacency(tris, n):
    import scipy.sparse as sps
    e = np.r_[tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]
    A = sps.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
    return ((A + A.T) > 0).astype(np.float64)


def taubin(v, A, fixed=None, iters=10, lam=0.5, mu=-0.53):
    deg = np.asarray(A.sum(1)).ravel()
    deg[deg == 0] = 1
    for _ in range(iters):
        for f in (lam, mu):
            d = (A @ v) / deg[:, None] - v
            if fixed is not None:
                d[fixed] = 0
            v = v + f * d
    return v


def boundary_edges(tris):
    e = np.r_[tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]
    k = np.sort(e, 1)
    u, inv, cnt = np.unique(k, axis=0, return_inverse=True, return_counts=True)
    return e[cnt[inv] == 1]  # oriented as in their face


def main():
    F = np.load(WORK / "face_fit.npz")
    v = F["v_fit"]
    vm = v * 0.1
    cam = Cam.from_dict(json.loads(str(F["cam"])))
    s, R, t = float(F["sim_s"]), F["sim_R"], F["sim_t"]
    A_ = np.load(WORK / "analysis.npz")
    cls, lm = A_["cls"], A_["lm"].astype(np.float64)
    photo = load_rgb(WORK / "photo_rect.png")
    mh = MH()
    base = mh.base()
    from avlib import dense_weights, load_rig, load_weights
    rig, order = load_rig()
    Wd = dense_weights(load_weights(), order, len(base.v))

    def W(prefixes):
        return Wd[:, [i for i, n in enumerate(order) if any(n.startswith(p) for p in prefixes)]].sum(1)

    body_g = base.groups.index("body")
    bf = base.fv[base.fgroup == body_g]
    btris = np.r_[bf[:, [0, 1, 2]], bf[bf[:, 3] != bf[:, 2]][:, [0, 2, 3]]]
    bn = vertex_normals(vm, btris)

    # ---------------- top region (per base vertex)
    w_hand = W(["wrist", "finger", "metacarpal"])
    w_leg = W(["upperleg", "lowerleg", "foot", "toe"])
    w_head = W(["head", "jaw", "levator", "oculi", "orbicularis", "oris", "risorius", "special", "temporalis", "tongue", "eye"])
    w_neck = W(["neck"])
    HEM_Y = 0.092 - 0.005               # MakeHuman casualsuit03 shirt length
    in_top = (vm[:, 1] > HEM_Y) & (w_hand < 0.12) & (w_head < 0.5) & (w_leg < 0.6)
    # neckline, front: vertices seen by the photo camera on the photo's visible neck skin
    neck_skin = (cls == 2).astype(np.uint8)
    neck_skin = cv2.erode(neck_skin, np.ones((3, 3), np.uint8))
    p = cam.project(vm)
    q = ((p[:, :2] - t) @ R) / s
    eye = cam.eye()
    vd = eye[None] - vm
    vd /= np.linalg.norm(vd, axis=1, keepdims=True)
    facing = (bn * vd).sum(1) > 0.15
    qi = np.clip(q.astype(int), 0, 1023)
    on_neck_photo = facing & (q[:, 0] >= 0) & (q[:, 0] < 1024) & (q[:, 1] >= 0) & (q[:, 1] < 1024) & (neck_skin[qi[:, 1], qi[:, 0]] > 0)
    # crew neckline as a closed curve around the neck: height y_n(theta) around the neck axis, measured on the photo
    # in front (centre and where the collar meets the neck silhouette), rising ~1.5 cm towards the back
    neck_col = (w_neck > 0.25) & (vm[:, 1] > 0.55)
    zc = np.median(vm[neck_col, 2])
    ctr = on_neck_photo & (np.abs(vm[:, 0]) < 0.012) & (vm[:, 2] > zc)
    y_front = vm[ctr, 1].min() if ctr.any() else 0.64
    # side: where the photo's collar meets the neck silhouette -> the MakeHuman neck silhouette vertex at that image row
    ns = (cls == 2).astype(np.uint8)
    ys_, xs_ = np.nonzero(ns)
    ymax = []
    for side in (-1, 1):
        sel = (xs_ - lm[1, 0]) * side > 0
        # outermost neck-skin column per row; the junction is the lowest row where the neck edge is still vertical
        rows = {}
        for y_, x_ in zip(ys_[sel], xs_[sel]):
            rows[y_] = max(rows.get(y_, -1), abs(x_ - lm[1, 0]))
        yy_ = np.array(sorted(rows))
        ww_ = np.convolve(np.array([rows[y_] for y_ in yy_], float), np.ones(5) / 5, mode="same")
        # the neck widens down to the collar, then the collar cuts in: junction = widest row
        ymax.append(yy_[np.argmax(ww_[2:-2]) + 2])
    jr = np.array([[lm[1, 0] - 1, np.mean(ymax)]]) @ R.T * s + t       # junction row in the render frame
    ring_v = neck_col & (np.abs((bn * vd).sum(1)) < 0.35) & (np.abs(p[:, 1] - jr[0, 1]) < 4)
    y_side = float(np.median(vm[ring_v, 1])) if ring_v.any() else y_front + 0.03
    theta = np.arctan2(vm[:, 0], vm[:, 2] - zc)          # 0 = front, +-pi = back
    at = np.abs(theta)
    y_n = np.where(at <= np.pi / 2, y_front + (y_side - y_front) * np.sin(at) ** 2,
                   y_side + 0.015 * (at - np.pi / 2) / (np.pi / 2))
    col = np.hypot(vm[:, 0], vm[:, 2] - zc) < 0.085
    above = col & (vm[:, 1] > y_n) & (vm[:, 1] > y_front - 0.005)
    in_top &= ~above & ~(on_neck_photo & (vm[:, 1] > y_front - 0.005))
    print(f"neckline: front {y_front:.3f} side {y_side:.3f} (MakeHuman metres, body frame)")
    # faces fully in the region; clean up small islands / holes
    fmask = in_top[btris].sum(1) >= 2  # majority: the MakeHuman chest faces are coarse near the neck
    from scipy.sparse.csgraph import connected_components
    ft = btris[fmask]
    A = mesh_adjacency(ft, len(base.v))
    ncomp, lab = connected_components(A, directed=False)
    used = np.unique(ft)
    sizes = np.bincount(lab[used], minlength=ncomp)
    main_c = np.argmax(sizes)
    ft = ft[lab[ft[:, 0]] == main_c]
    print(f"top: {len(ft)} triangles from the body surface")

    # ---------------- offset + smoothing
    pants = proxy_part(mh, SUIT)
    pm = pants.proxy.mesh
    pv_all = pants.proxy.fit(v) * 0.1
    import scipy.sparse as sp2
    f4 = pm.fv
    e = np.r_[f4[:, [0, 1]], f4[:, [1, 2]], f4[:, [2, 3]], f4[:, [3, 0]]]
    Ap = sp2.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(len(pm.v),) * 2)
    nc, plab = connected_components(Ap, directed=False)
    comp_minY = [pv_all[plab == c, 1].min() for c in range(nc)]
    trouser_c = int(np.argmin(comp_minY))
    pvert = plab == trouser_c
    ptree = cKDTree(pv_all[pvert])
    off = np.full(len(base.v), 0.006)
    fore = W(["lowerarm"]) > 0.5
    off[fore] = 0.005
    # above the trouser waistband: clear the trousers by 5 mm
    dpt, _ = ptree.query(vm)
    near_p = (dpt < 0.03) & (vm[:, 1] < 0.20)
    off[near_p] = np.maximum(off[near_p], dpt[near_p] + 0.006)
    # smooth the offset field itself so the hem flares evenly
    Au = mesh_adjacency(ft, len(base.v))
    offs = off.copy()
    deg = np.maximum(np.asarray(Au.sum(1)).ravel(), 1)
    for _ in range(30):
        offs = np.where(np.isin(np.arange(len(offs)), used), 0.5 * offs + 0.5 * (Au @ offs) / deg, offs)
    offs = np.maximum(offs, off * 0.8)
    top_v = vm + bn * offs[:, None]
    bnd = boundary_edges(ft)
    bverts = np.unique(bnd)
    top_v = taubin(top_v, Au, fixed=None, iters=12)
    # never closer than 4 mm to the skin (along the skin normal)
    h = ((top_v - vm) * bn).sum(1)
    top_v = np.where((h < 0.004)[:, None], top_v + bn * (0.004 - h)[:, None], top_v)

    # smooth each boundary loop (neckline, cuffs, hem) as a 1D curve so the face stair-steps disappear
    nxt = {int(a): int(b_) for a, b_ in bnd}
    seen = set()
    loops = []
    for a0 in nxt:
        if a0 in seen:
            continue
        loop, a = [], a0
        while a not in seen and a in nxt:
            seen.add(a)
            loop.append(a)
            a = nxt[a]
        if len(loop) > 8:
            loops.append(np.array(loop))
    loop_n = bn.copy()
    for lp in loops:
        P0 = top_v[lp].copy()
        P = P0.copy()
        for _ in range(12):
            P = 0.5 * P + 0.25 * (np.roll(P, 1, 0) + np.roll(P, -1, 0))
        if P0[:, 1].mean() > 0.5:  # neckline: cut the henley placket notch at the centre front
            front = P[:, 2] > np.median(P[:, 2])
            wn = np.clip(1 - np.abs(P[:, 0]) / 0.010, 0, 1) * front
            P[:, 1] -= 0.009 * wn
        # keep the loop on the garment surface: restore the offset from the skin, as a correction that is itself
        # smoothed along the loop and applied along loop-smoothed normals (per-vertex skin normals differ between
        # neighbouring boundary vertices on the coarse MakeHuman mesh and put a "pie-crust" wave back into the edge)
        nl = bn[lp].copy()
        for _ in range(8):
            nl = 0.5 * nl + 0.25 * (np.roll(nl, 1, 0) + np.roll(nl, -1, 0))
        nl /= np.maximum(np.linalg.norm(nl, axis=1, keepdims=True), 1e-9)
        corr = offs[lp] - ((P - vm[lp]) * bn[lp]).sum(1)
        for _ in range(8):
            corr = 0.5 * corr + 0.25 * (np.roll(corr, 1) + np.roll(corr, -1))
        P += nl * corr[:, None]
        top_v[lp] = P
        loop_n[lp] = nl
    print("boundary loops:", [len(lp) for lp in loops])
    # relax the rings just inside each loop towards the moved boundary (Laplacian, boundary fixed): otherwise the
    # first interior triangles are sheared / folded and catch the light as a serrated edge
    ring_d = np.full(len(base.v), 99)
    ring_d[bverts] = 0
    for k in range(1, 4):
        nb = (Au @ (ring_d == k - 1).astype(float)) > 0
        ring_d[nb & (ring_d > k)] = k
    relax = np.isin(np.arange(len(base.v)), used) & (ring_d >= 1) & (ring_d <= 3)
    h_before = ((top_v - vm) * bn).sum(1)
    for _ in range(10):
        lap = (Au @ top_v) / deg[:, None] - top_v
        top_v[relax] += 0.5 * lap[relax]
    # tangential relaxation only: never closer to the body than before (the hem rings clear the trouser waistband)
    h = ((top_v - vm) * bn).sum(1)
    top_v = np.where(((h < h_before) & relax)[:, None], top_v + bn * (h_before - h)[:, None], top_v)
    # skin weights smoothed the same way: the boundary loops follow the zigzag of the MakeHuman faces, so
    # neighbouring edge vertices alternate between neck- and chest-weighted (wrist- and forearm-, ...) base
    # vertices.  With their positions smoothed but their weights not, any neck or arm motion pulled the neckline,
    # cuffs and hem back into saw teeth.  1D smoothing along each loop, then Laplacian over the relaxed rings.
    Wtop = Wd.astype(np.float64).copy()
    for lp in loops:
        Wl = Wtop[lp]
        for _ in range(12):
            Wl = 0.5 * Wl + 0.25 * (np.roll(Wl, 1, 0) + np.roll(Wl, -1, 0))
        Wtop[lp] = Wl
    for _ in range(10):
        Wtop[relax] = 0.5 * Wtop[relax] + 0.5 * ((Au @ Wtop) / deg[:, None])[relax]
    Wtop /= np.maximum(Wtop.sum(1, keepdims=True), 1e-9)
    # folded edge: inner copy of the boundary 3 mm towards the skin (along the loop-smoothed normal)
    tb = np.unique(bnd)
    inner_id = {int(i): k for k, i in enumerate(tb)}
    inner_v = top_v[tb] - loop_n[tb] * 0.003
    # ---------------- top texture (MakeHuman skin UV layout): dark navy knit
    # unweld only the top faces (UV per corner from the base mesh)
    # map each top triangle to its UV triangle via the skin part (same face order is not kept, so match per face)
    key = {tuple(sorted(tri)): k for k, tri in enumerate(btris)}
    btu = np.r_[base.fuv[base.fgroup == body_g][:, [0, 1, 2]],
                base.fuv[base.fgroup == body_g][bf[:, 3] != bf[:, 2]][:, [0, 2, 3]]]
    ft_uv = btu[[key[tuple(sorted(tr))] for tr in ft]]
    pairs = np.stack([ft.ravel(), ft_uv.ravel()], 1)
    uniq, inv = np.unique(pairs, axis=0, return_inverse=True)
    top_src = uniq[:, 0]
    top_uv = base.vt[uniq[:, 1]].copy()
    top_uv[:, 1] = 1 - top_uv[:, 1]
    top_tris = inv.reshape(-1, 3)
    # edge band: quads between boundary vertex (outer) and its inner copy
    # boundary edges in unwelded indices: use the first unwelded copy of each base vertex
    first = {}
    for k, b_ in enumerate(top_src):
        first.setdefault(int(b_), k)
    n_u = len(top_src)
    band_tris = []
    for a, b_ in bnd:
        ia, ib = first[int(a)], first[int(b_)]
        ja, jb = n_u + inner_id[int(a)], n_u + inner_id[int(b_)]
        band_tris += [[ib, ia, ja], [ib, ja, jb]]
    band_src = tb
    band_uv = np.tile(np.array([[0.995, 0.005]]), (len(tb), 1))   # a corner texel painted with the knit colour
    all_src = np.r_[top_src, band_src]
    all_pos = np.r_[top_v[top_src], inner_v]
    all_uv = np.r_[top_uv, band_uv]
    all_tris = np.r_[top_tris, np.array(band_tris, np.int64).reshape(-1, 3)]

    # knit albedo + normal map in UV space
    rng = np.random.default_rng(7)
    cloth = np.median(photo[(cls == 4) & (photo.mean(-1) < 0.3)], 0)
    n1 = cv2.GaussianBlur(rng.normal(0, 1, (T, T)).astype(np.float32), (0, 0), 0.6)
    n2 = cv2.GaussianBlur(rng.normal(0, 1, (T, T)).astype(np.float32), (0, 0), 2.0)
    n1 /= n1.std()
    n2 /= n2.std()
    alb = cloth[None, None] * (1 + 0.10 * n1[..., None] + 0.06 * n2[..., None])
    # placket: a short darker seam line below the neckline centre (front), drawn in UV
    ti, ba, _ = rasterize(top_uv * T, top_tris, T, T)
    mk = ti >= 0
    P3 = np.zeros((T, T, 3))
    P3[mk] = interp(top_v[top_src], top_tris, ti, ba)[mk]
    front_neck = top_v[top_src][(np.abs(top_v[top_src][:, 0]) < 0.01)]
    neck_front_y = front_neck[front_neck[:, 2] > 0.05, 1].max() if len(front_neck) else 0.64
    # photo: button and notch positions -> find the top surface points under them (render camera raster)
    pz = cam.project(top_v[top_src])
    tri_r, bar_r, _ = rasterize(pz[:, :2], top_tris, cam.W, cam.H, Z=pz[:, 2])

    def surf_at_photo(x, y):
        rx, ry = np.array([x, y]) @ R.T * s + t
        k = tri_r[int(ry), int(rx)]
        if k < 0:
            return None
        return (top_v[top_src][top_tris[k]] * bar_r[int(ry), int(rx)][:, None]).sum(0)

    # button: brightest compact blob in the photo's clothes region below the collar
    br = (cls == 4) & (photo.mean(-1) > 0.45)
    br = cv2.morphologyEx(br.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n_, lab_, st_, cen_ = cv2.connectedComponentsWithStats(br, 8)
    cands = [(st_[i, cv2.CC_STAT_AREA], cen_[i]) for i in range(1, n_) if 60 < st_[i, cv2.CC_STAT_AREA] < 4000
             and abs(cen_[i][0] - lm[1, 0]) < 80]
    button_px = max(cands, key=lambda c: c[0])[1] if cands else np.array([lm[1, 0], 985.0])
    bpos = surf_at_photo(*button_px)
    btn_r_px = np.sqrt(max(cands, key=lambda c: c[0])[0] / np.pi) if cands else 22
    print("button at photo px", np.round(button_px, 1), "->", None if bpos is None else np.round(bpos, 3))
    # placket seam from the neckline centre down to just below the button
    top_vs = top_v[top_src]
    if bpos is None:
        bpos = np.array([0.0, neck_front_y - 0.06, top_vs[np.abs(top_vs[:, 0]) < 0.01, 2].max()])
    seam = mk & (np.abs(P3[..., 0] - bpos[0]) < 0.0012) & (P3[..., 1] > bpos[1] - 0.012) & (P3[..., 1] < neck_front_y + 0.01) & (P3[..., 2] > bpos[2] - 0.05)
    seam_w = cv2.GaussianBlur(seam.astype(np.float32), (0, 0), 1.2)
    alb = alb * (1 - 0.45 * seam_w[..., None])
    alb[int(0.005 * T):int(0.005 * T) + 8, T - 12:] = cloth  # band corner texel
    alb = np.clip(alb, 0, 1)
    alb_f = push_pull(alb.astype(np.float32), mk.astype(np.float32))
    alb = np.where(mk[..., None], alb, alb_f)
    save_rgb(WORK / "top_albedo.png", alb)
    hgt = 0.6 * n1 + 0.4 * n2
    gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3)
    nm = np.dstack([-gx * 0.25, gy * 0.25, np.ones_like(gx)])
    nm /= np.linalg.norm(nm, axis=-1, keepdims=True)
    save_rgb(WORK / "top_normal.png", nm * 0.5 + 0.5)

    # button geometry: a small disc (radius from the photo blob), axis along the local top normal
    tn = vertex_normals(top_v[top_src], top_tris)
    kd = cKDTree(top_vs)
    _, jn = kd.query(bpos)
    nrm = tn[jn]
    rad = btn_r_px * s * cam.project(bpos[None])[0, 2] / cam.f  # photo px -> render px -> metres
    rad = float(np.clip(rad, 0.004, 0.007))
    seg = 20
    ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    up = np.array([0, 1.0, 0])
    ax1 = np.cross(up, nrm)
    ax1 /= np.linalg.norm(ax1)
    ax2 = np.cross(nrm, ax1)
    ring = np.cos(ang)[:, None] * ax1 + np.sin(ang)[:, None] * ax2
    c0 = bpos + nrm * 0.0008
    c1 = bpos + nrm * 0.0030
    bv = np.r_[c0 + ring * rad, c1 + ring * rad * 0.92, [c1 + nrm * 0.0004]]
    btris_ = []
    for i in range(seg):
        j = (i + 1) % seg
        btris_ += [[i, j, seg + j], [i, seg + j, seg + i], [seg + i, seg + j, 2 * seg]]
    btris_ = np.array(btris_)
    b_src = kd.query(bv)[1]
    button_src = top_src[b_src]  # nearest top vertex's base vertex (kept for reference; the button is skinned
    #                              rigidly with the weights at its centre, button_W, so it never shears)

    # ---------------- trousers texture: jeans -> charcoal
    ptex = load_rgb(texture_of(pants))
    lum = ptex @ np.array([0.3, 0.59, 0.11])
    char = np.array([0.05, 0.05, 0.055])
    pal = np.clip(char[None, None] * (0.6 + 0.8 * (lum / max(np.median(lum), 1e-3)))[..., None], 0, 1)
    save_rgb(WORK / "pants_albedo.png", pal)
    # trouser component faces only
    pf_keep = pvert[pm.fv].all(1)
    pidx, puv, ptris = unweld(pm, pf_keep)

    shoes = proxy_part(mh, SHOES)

    # ---------------- skin faces to delete (under top, trousers, shoes)
    dele = np.zeros(len(base.v), bool)
    dele[np.unique(ft)] = True
    dp = np.zeros(len(base.v), bool)
    dp[pants.proxy.delete_verts] = True
    dele |= dp & (vm[:, 1] < HEM_Y + 0.02)
    dele[shoes.proxy.delete_verts] = True
    # keep a ring of skin under the top's boundary (neckline / cuffs) so no gap opens when posed
    keep = np.zeros(len(base.v), bool)
    keep[bverts] = True
    Ab = mesh_adjacency(btris, len(base.v))
    ring = (Ab @ keep.astype(float)) > 0
    dele &= ~(keep | ring)

    np.savez_compressed(WORK / "clothes.npz", top_pos=all_pos, top_src=all_src, top_uv=all_uv, top_tris=all_tris,
                        top_W=Wtop[all_src].astype(np.float32), button_W=np.tile(Wtop[top_src[jn]], (len(bv), 1)).astype(np.float32),
                        pants_idx=pidx, pants_uv=puv, pants_tris=ptris, skin_delete=np.nonzero(dele)[0],
                        button_v=bv, button_tris=btris_, button_src=button_src, hem_y=HEM_Y, cloth_rgb=cloth,
                        button_px=np.asarray(button_px), button_radius_m=rad)
    print(f"top verts {len(all_pos)} tris {len(all_tris)}; trousers tris {len(ptris)}; button r={rad*1000:.1f} mm; skin deleted verts {dele.sum()}")

    # ---------------- preview (front / 3-4 / back, upper body) + photo camera
    skin = skin_part(base, np.nonzero(dele)[0])
    stex = load_rgb(WORK / "skin_albedo_hair.png")
    L = [dict(v=vm[skin.src_index], tris=skin.tris, uv=skin.uv, tex=stex),
         dict(v=all_pos, tris=all_tris, uv=all_uv, tex=alb, two_sided=True),
         dict(v=pv_all[pidx], tris=ptris, uv=puv, tex=pal),
         dict(v=shoes.proxy.fit(v)[shoes.src_index] * 0.1, tris=shoes.tris, uv=shoes.uv, tex=load_rgb(texture_of(shoes))),
         dict(v=bv, tris=btris_, color=(0.74, 0.64, 0.50))]
    imgs = []
    img, _, _ = swr.render(cam, L, bg=(0.2, 0.2, 0.2))
    Mw = np.c_[s * R, t]
    imgs.append(np.hstack([cv2.warpAffine(photo, Mw, (cam.W, cam.H))[500:1024, 150:874], img[500:1024, 150:874]]))
    row = []
    for angd in (0, 40, 90, 180):
        ar = np.radians(angd)
        tgt = np.array([0, 0.05, 0])
        c2 = Cam.look_at(tgt + 4.2 * np.array([np.sin(ar), 0, np.cos(ar)]), tgt, 1500, 480, 1000)
        im2, _, _ = swr.render(c2, L, bg=(0.2, 0.2, 0.2))
        row.append(im2)
    save_rgb(CHECK / "clothes_preview.jpg", np.hstack(row))
    save_rgb(CHECK / "clothes_collar.jpg", imgs[0])


if __name__ == "__main__":
    main()
