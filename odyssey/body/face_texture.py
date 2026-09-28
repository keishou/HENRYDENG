"""Head texture from one frontal photo: project the photo onto the fitted head in the MakeHuman UV layout
and blend it (multi-band) into the MakeHuman skin texture, colour-matched to the photo.

    tex, wmap, info = bake_skin_texture(v, base, tv, tu, base_tex, photo, cls, lm, fit_cam, photo_to_px,
                                        size=4096, eye_geo=(eye_verts, eye_tris))
    tex = paint_scalp(tex, base, tv, tu, scalp_weights, hair_colour, clean=..., skin_ref=...)

* the photo is cleaned first: light edge-preserving smoothing (noise / blemishes), eye openings in-painted
  with lid skin (the eyeballs are real geometry), pixels the segmenter calls hair -- plus thin fringe
  strands on the forehead / upper lids found with a black-hat filter -- filled with a smooth skin
  estimate, flash highlights compressed; the brows are kept from the photo; the confidence falls off
  towards hair / background (wide ramp, so the photo's jaw-edge shading does not land on the cheeks) and
  is zero above the brows (the forehead is streaked with fringe in the photo: base skin there);
* de-lighting: the photo's low-frequency shading is fitted as SH2(normal) on the projected skin (robust
  IRLS) and divided out, so the render's own lights shade the face;
* every texel of the head is ray-cast into the photo's orthographic camera (the landmark fit camera);
  its weight = photo confidence x visibility (front z-buffer) x a facing term, so the grazing sides of
  the face, the ears and the back of the head come from the base texture, not from stretched pixels;
* the base texture's forehead / glabella creases are smoothed away (they aged him in 3/4 views);
* the base texture is colour-matched to the photo (per-channel gain in linear RGB measured on the
  confidently projected texels) for the whole body, so neck and hands match the face;
* Laplacian-pyramid blending hides the seam: low frequencies blend over a wide band, fine detail over a
  narrow one;
* a lash line is painted right at the mesh's eye openings (so it always sits where lids meet eyeballs),
  and paint_scalp() paints the hair-bearing scalp in the hair colour (gaps between hair cards read as
  hair) while cleaning MakeHuman's scalp stubble off the nape / sideburns.
"""
from __future__ import annotations

import cv2
import numpy as np

from raster import rasterize, sample_bilinear

EYE_R = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]
EYE_L = [263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249]
LIPS_OUT = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 375, 321, 405, 314, 17, 84, 181, 91, 146]
BROW_R = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
BROW_L = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]


def srgb_to_lin(x):
    x = np.clip(np.asarray(x, np.float32), 0, 1)
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(x):
    x = np.clip(np.asarray(x, np.float32), 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def normalized_fill(img, mask, sigma):
    """Fill img where mask==0 with a Gaussian normalised-convolution average of the masked pixels."""
    m = mask.astype(np.float32)
    num = cv2.GaussianBlur(img * m[..., None], (0, 0), sigma)
    den = cv2.GaussianBlur(m, (0, 0), sigma)[..., None]
    return num / np.maximum(den, 1e-4), den[..., 0]


def clean_photo(rgb, cls, lm, hair_margin=(6.0, 36.0)):
    """rgb float sRGB (H,W,3).  Returns (clean rgb, confidence (H,W), masks dict)."""
    H, W = cls.shape
    skin = ((cls == 2) | (cls == 3)).astype(np.uint8)
    # eye openings (the eyeball is geometry) -> lid skin
    eyes = np.zeros((H, W), np.uint8)
    for ring in (EYE_R, EYE_L):
        cv2.fillPoly(eyes, [np.round(lm[ring, :2]).astype(np.int32)], 1)
    eyes_d = cv2.dilate(eyes, np.ones((5, 5), np.uint8), iterations=1)
    # brows (landmark outline)
    brows = np.zeros((H, W), np.uint8)
    for ring in (BROW_R, BROW_L):
        cv2.fillPoly(brows, [np.round(lm[ring, :2]).astype(np.int32)], 1)
    brows = cv2.dilate(brows, np.ones((3, 3), np.uint8), iterations=1).astype(bool)
    img8 = (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    # a light edge-preserving smoothing: the photo's sensor / JPEG noise and blemishes read as dirt at
    # texture scale; eyes, lips and brows keep their edges
    img8 = cv2.bilateralFilter(img8, 7, 14, 4)
    img8 = cv2.inpaint(img8, eyes_d, 6, cv2.INPAINT_TELEA)
    out = img8.astype(np.float32) / 255.0
    # thin fringe strands lying on the forehead that the segmenter does not call hair (they would paint
    # frown lines): black-hat (thin dark lines) above the brows -> treated as hair
    lum = cv2.cvtColor(img8, cv2.COLOR_RGB2GRAY).astype(np.float32)
    bh = cv2.morphologyEx(lum, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    brow_top = lm[BROW_R + BROW_L, 1].min() - 3
    fz = np.zeros((H, W), bool)
    fz[: int(brow_top)] = True
    # ... and between the brows and the upper lids (fringe tips hang over the lids), stricter threshold
    lidz = np.zeros((H, W), np.uint8)
    for br, ey in ((BROW_R, EYE_R), (BROW_L, EYE_L)):
        pts = np.vstack([lm[br, :2], lm[ey, :2][lm[ey, 1] < lm[ey, 1].mean()] - [0, 6]])
        cv2.fillPoly(lidz, [cv2.convexHull(np.round(pts).astype(np.int32))], 1)
    lidz = lidz.astype(bool) & ~cv2.dilate(eyes.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)
    thin = ((bh > 12) & fz) | ((bh > 18) & lidz)
    strands = cv2.dilate((thin & ~brows & ~eyes_d.astype(bool)).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    strands &= ~brows
    hair = ((cls == 1) & ~brows) | (strands & skin.astype(bool))
    # hair over the forehead / temples -> smooth skin estimate from the surrounding skin
    good = (skin.astype(bool) & ~eyes_d.astype(bool) & ~hair) | brows
    good_e = cv2.erode(good.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    fill, den = normalized_fill(out, good_e, 18)
    fill2, _ = normalized_fill(out, good_e, 60)
    fill = np.where((den > 0.15)[..., None], fill, fill2)
    region = hair | ((~good) & ~eyes_d.astype(bool))
    out = np.where(region[..., None], fill, out)
    # flash highlights (forehead, nose bridge, cheeks) are not albedo: compress them
    lum2 = out @ np.array([0.299, 0.587, 0.114], np.float32)
    hi = np.clip(lum2 - cv2.GaussianBlur(lum2, (0, 0), 12), 0, None)
    out = np.clip(out - 0.65 * hi[..., None], 0, 1)
    # confidence: 1 on skin (incl. the in-painted eyes), ramps to 0 over ~10 px at hair / background
    conf_src = (good | eyes_d.astype(bool)).astype(np.uint8)
    dist = cv2.distanceTransform(conf_src, cv2.DIST_L2, 5)
    conf = smoothstep(dist, 3.0, 24.0)       # wide: the photo's jaw-edge shading must not land on the cheeks
    # skin seen between fringe strands is lit differently and would paint streaks: fade the photo out
    # well before the hair (the 3D fringe covers that part of the forehead anyway)
    d_hair = cv2.distanceTransform((~hair).astype(np.uint8), cv2.DIST_L2, 5)
    fade = smoothstep(d_hair, hair_margin[0], hair_margin[1])
    # ... but not over the brows themselves (kept from the photo)
    bz = cv2.GaussianBlur(brows.astype(np.float32), (0, 0), 1.5)
    conf = np.maximum(conf * fade, np.clip(bz * 1.5, 0, 1))
    # the forehead above the brows is mostly hidden by (and streaked with) fringe in the photo: the
    # colour-matched base skin is used there instead
    yy = np.arange(H, dtype=np.float32)[:, None]
    conf = conf * smoothstep(yy, brow_top - 30, brow_top + 2)
    return out, conf.astype(np.float32), {"eyes": eyes_d, "hair": hair, "skin": good, "brows": brows}


def sh9(n):
    """Real spherical harmonics basis up to order 2 for unit normals (N,3) -> (N,9)."""
    x, y, z = n[:, 0], n[:, 1], n[:, 2]
    return np.stack([np.ones_like(x), y, z, x, x * y, y * z, 3 * z * z - 1, x * z, x * x - y * y], 1)


def delight(col_lin, n_cam, w, clip=(0.72, 1.45), log=print):
    """Remove the photo's low-frequency shading: fit luminance ~ SH2(normal) on confidently projected skin
    texels (robust IRLS, so lips / brows / stubble do not bias it) and divide the fitted shading out,
    normalised to its median.  Returns (corrected colours, per-texel factor)."""
    lum = col_lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    Y = sh9(n_cam)
    sel = (w > 0.8) & (lum > 0.01)
    if sel.sum() < 500:
        return col_lin, np.ones(len(col_lin), np.float32)
    ww = np.ones(sel.sum())
    for _ in range(6):
        c = np.linalg.lstsq(Y[sel] * ww[:, None], lum[sel] * ww, rcond=None)[0]
        r = lum[sel] - Y[sel] @ c
        sig = 1.4826 * np.median(np.abs(r)) + 1e-6
        ww = 1.0 / (1.0 + (r / (2 * sig)) ** 2)
    S = Y @ c
    f = np.clip(np.median(S[sel]) / np.maximum(S, 1e-4), *clip).astype(np.float32)
    log(f"  de-light: SH2 shading range {np.percentile(S[sel], 5):.3f}..{np.percentile(S[sel], 95):.3f}, "
        f"factor {np.percentile(f[sel], 5):.2f}..{np.percentile(f[sel], 95):.2f}")
    return col_lin * f[:, None], f


def laplacian_blend(a, b, w, levels=7):
    """Multi-band blend: w=1 -> a, w=0 -> b.  a, b (H,W,3) float, w (H,W) float."""
    ga, gb, gw = [a], [b], [w]
    for _ in range(levels):
        ga.append(cv2.pyrDown(ga[-1]))
        gb.append(cv2.pyrDown(gb[-1]))
        gw.append(cv2.pyrDown(gw[-1]))
    out = ga[-1] * gw[-1][..., None] + gb[-1] * (1 - gw[-1][..., None])
    for i in range(levels - 1, -1, -1):
        size = (ga[i].shape[1], ga[i].shape[0])
        la = ga[i] - cv2.pyrUp(ga[i + 1], dstsize=size)
        lb = gb[i] - cv2.pyrUp(gb[i + 1], dstsize=size)
        out = cv2.pyrUp(out, dstsize=size) + la * gw[i][..., None] + lb * (1 - gw[i][..., None])
    return out


def uv_raster(base, tv, tu, v, size, face_sel=None):
    """Rasterise the skin in UV space -> per-texel triangle id (into tv), barycentrics, 3D pos, normal."""
    from build_body import vertex_normals
    sel = np.arange(len(tv)) if face_sel is None else np.nonzero(face_sel)[0]
    uv = base.vt
    P2 = np.stack([uv[:, 0] * size, (1 - uv[:, 1]) * size], 1)
    tid, bary, _ = rasterize(P2, np.zeros(len(uv)), tu[sel], size, size)
    m = tid >= 0
    tri_v = tv[sel][tid[m]]
    bb = bary[m]
    pos = np.einsum("nk,nkj->nj", bb, v[tri_v])
    body = base.fgroup == base.groups.index("body")
    nrm_v = vertex_normals(v, base.fv[body])
    nrm = np.einsum("nk,nkj->nj", bb, nrm_v[tri_v])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    return m, pos, nrm


def dilate_texture(img, mask, iters=24):
    """Push colours outwards from mask (UV gutter fill) so mip-mapping never sees garbage."""
    img = img.copy()
    m = mask.astype(np.float32)
    for _ in range(iters):
        num = cv2.blur(img * m[..., None], (3, 3))
        den = cv2.blur(m, (3, 3))
        grow = (den > 0) & (m == 0)
        img[grow] = num[grow] / den[grow][:, None]
        m = np.where(grow, 1.0, m)
    return img


def bake_skin_texture(v, base, tv, tu, base_tex_srgb, photo_srgb, cls, lm, cam, photo_to_px, size=4096,
                      head_y_min=None, facing=(0.3, 0.7), lash=(0.8, 0.012), eye_geo=None, log=print, debug_dir=None,
                      delight_photo=True, smooth_forehead=True):
    """Returns (texture sRGB float (size,size,3), weight map (size,size), info)."""
    H, W = cls.shape
    clean, conf, masks = clean_photo(photo_srgb, cls, lm)
    clean_lin = srgb_to_lin(clean)
    # --- visibility from the photo camera: skin z-buffer at the fit camera
    P2c, Zc = cam.project(v)
    zres = cam.res
    tid, _, depth = rasterize(P2c, Zc, tv, zres, zres)
    # --- texels
    tri_y = v[tv].mean(1)[:, 1]
    sel = tri_y > (head_y_min if head_y_min is not None else -1e9)
    m, pos, nrm = uv_raster(base, tv, tu, v, size, sel)
    q, z = cam.project(pos)
    zb = sample_bilinear(np.where(np.isfinite(depth), depth, -1e9)[..., None], q[:, 0], q[:, 1])[:, 0]
    vis = smoothstep(z - zb, -0.03, -0.01)             # dm: fully visible within 1 mm of the front surface
    Ainv = cv2.invertAffineTransform(photo_to_px)
    ph = q @ Ainv[:, :2].T + Ainv[:, 2]
    inside = (ph[:, 0] > 1) & (ph[:, 0] < W - 2) & (ph[:, 1] > 1) & (ph[:, 1] < H - 2)
    col = sample_bilinear(clean_lin, ph[:, 0], ph[:, 1])
    cf = sample_bilinear(conf[..., None], ph[:, 0], ph[:, 1])[:, 0]
    face_n = nrm @ cam.R.T
    wv = cf * vis * smoothstep(face_n[:, 2], *facing) * inside
    if delight_photo:
        col, _ = delight(col, face_n, wv, log=log)
    Wmap = np.zeros((size, size), np.float32)
    Wmap[m] = wv
    proj = np.zeros((size, size, 3), np.float32)
    proj[m] = col
    # --- colour-match the base texture (linear gain per channel on confident texels)
    base_lin = srgb_to_lin(cv2.resize(base_tex_srgb, (size, size), interpolation=cv2.INTER_CUBIC))
    good = Wmap > 0.9
    # compare low frequencies only (the photo has no pores, the base has no identity)
    pb = cv2.GaussianBlur(proj, (0, 0), 6)
    bb = cv2.GaussianBlur(base_lin, (0, 0), 6)
    gain = np.median(pb[good], 0) / np.maximum(np.median(bb[good], 0), 1e-4)
    log(f"  skin colour gain (linear RGB) {np.round(gain, 3).tolist()} from {int(good.sum())} texels")
    base_m = np.clip(base_lin * gain, 0, 1)
    if smooth_forehead:
        # MakeHuman's base skin has frown lines between / above the brows and forehead creases that age
        # him in the 3/4 views (where the base shows): keep only a fraction of the mid / high frequencies
        eye_y = cam.center[1] + 0.15                           # the fit camera is centred 1.5 cm below the eyes
        fz = np.zeros((size, size), np.float32)
        fz[m] = (smoothstep(pos[:, 1], eye_y + 0.08, eye_y + 0.25) * smoothstep(nrm[:, 2], 0.0, 0.5) *
                 (1 - smoothstep(np.abs(pos[:, 0]), 0.45, 0.7))).astype(np.float32)
        fz = cv2.GaussianBlur(fz, (0, 0), size / 400)
        lo = cv2.GaussianBlur(base_m, (0, 0), size / 180)
        base_m = base_m * (1 - fz[..., None]) + (lo + 0.25 * (base_m - lo)) * fz[..., None]
    # the projected layer must be defined everywhere for the pyramid: fill outside with the base
    proj_f = np.where((Wmap > 0.02)[..., None], proj, base_m)
    # feather the weight a touch so single-texel rims never pop
    Wb = cv2.GaussianBlur(Wmap, (0, 0), 2.0)
    Wb = np.minimum(Wb, Wmap + 0.05) * (Wmap > 0)
    out = laplacian_blend(proj_f, base_m, np.clip(Wb, 0, 1), levels=7)
    out = np.clip(out, 0, 1)
    # lash line: darken the lid margins right at the mesh's eye openings (geometry-driven, so it always
    # sits where the lids meet the eyeballs); upper lid darker and wider than the lower one
    if eye_geo is not None:
        ev, etv = eye_geo
        zr = 2048
        cz = type(cam)(cam.center, cam.half, zr)
        P2s, Zs = cz.project(v)
        _, _, dsk = rasterize(P2s, Zs, tv, zr, zr)
        P2e, Ze = cz.project(ev)
        te, _, de = rasterize(P2e, Ze, etv, zr, zr)
        opening = (te >= 0) & (de > dsk)
        dist_px = cv2.distanceTransform((~opening).astype(np.uint8), cv2.DIST_L2, 5)
        qs, zs = cz.project(pos)
        dist = sample_bilinear(dist_px[..., None], qs[:, 0], qs[:, 1])[:, 0] / cz.px_per_dm
        zb2 = sample_bilinear(np.where(np.isfinite(dsk), dsk, -1e9)[..., None], qs[:, 0], qs[:, 1])[:, 0]
        near_front = smoothstep(zs - zb2, -0.04, -0.015)
        eye_y = cz.project(ev)[0][:, 1].mean()
        up = qs[:, 1] < eye_y
        sig = np.where(up, lash[1], lash[1] * 0.55)
        amt = np.where(up, lash[0], lash[0] * 0.3) * np.exp(-(dist / sig) ** 2) * near_front
    else:
        amt = np.zeros(len(pos))
    lash_col = np.array([0.018, 0.012, 0.010], np.float32)
    o = out[m]
    out[m] = o * (1 - amt[:, None]) + lash_col * amt[:, None]
    # gutter fill outside the skin UV islands
    m_all, _, _ = uv_raster(base, tv, tu, v, size)
    out = np.where(m_all[..., None], out, base_m)
    info = {"gain_linear_rgb": gain.tolist(), "projected_texels": int((Wmap > 0.5).sum())}
    if debug_dir is not None:
        cv2.imwrite(str(debug_dir / "photo_clean.png"), cv2.cvtColor((clean * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(debug_dir / "photo_conf.png"), (conf * 255).astype(np.uint8))
        cv2.imwrite(str(debug_dir / "uv_weight.png"), cv2.resize((Wmap * 255).astype(np.uint8), (1024, 1024)))
    return lin_to_srgb(out), Wmap, info


def paint_scalp(tex_srgb, base, tv, tu, scalp, color_srgb, strength=0.97, seed=0, clean=None, skin_ref=None):
    """Paint the hair-bearing scalp (per-vertex weights in [0,1]) in the hair colour so gaps between hair
    cards read as dense hair, with a soft, slightly noisy hairline.  clean (per-vertex, optional): where
    the base texture has MakeHuman's scalp stubble but no hair is painted (nape, sideburns, forehead),
    its low frequencies are pulled to skin_ref (linear RGB) so those areas read as clean skin."""
    size = tex_srgb.shape[0]
    uv = base.vt
    P2 = np.stack([uv[:, 0] * size, (1 - uv[:, 1]) * size], 1)
    tid, bary, _ = rasterize(P2, np.zeros(len(uv)), tu, size, size)
    m = tid >= 0
    val = np.zeros((size, size), np.float32)
    val[m] = np.einsum("nk,nk->n", bary[m], scalp[tv[tid[m]]])
    rng = np.random.default_rng(seed)
    noise = cv2.GaussianBlur(rng.random((size // 16, size // 16)).astype(np.float32), (0, 0), 2.0)
    noise = cv2.resize(noise, (size, size), interpolation=cv2.INTER_LINEAR)
    noise = (noise - noise.mean()) / (noise.std() + 1e-6)
    w = smoothstep(val + 0.04 * noise, 0.35, 0.85)
    # soften the per-vertex steps of the hairline (coarse triangles) in texture space; normalised inside
    # the UV islands so the paint does not fade out along island borders (the crown / top of the head)
    mf = m.astype(np.float32)
    sig = size / 400
    w = cv2.GaussianBlur(w.astype(np.float32) * mf, (0, 0), sig) / np.maximum(cv2.GaussianBlur(mf, (0, 0), sig), 1e-3)
    w = w * strength
    lin = srgb_to_lin(tex_srgb)
    if clean is not None and skin_ref is not None:
        cv_ = np.zeros((size, size), np.float32)
        cv_[m] = np.einsum("nk,nk->n", bary[m], clean[tv[tid[m]]])
        wc = smoothstep(cv_, 0.05, 0.4) * (1 - w)
        low = cv2.GaussianBlur(lin, (0, 0), 12)
        fixed = np.clip(lin * np.asarray(skin_ref, np.float32) / np.maximum(low, 1e-3), 0, 1)
        lin = lin * (1 - wc[..., None]) + fixed * wc[..., None]
    col = srgb_to_lin(np.asarray(color_srgb, np.float32))
    out = lin * (1 - w[..., None]) + col * w[..., None]
    # gutter: push island colours outwards so filtering never pulls skin colour across UV seams
    dil = dilate_texture(np.where(m[..., None], out, 0).astype(np.float32), m, iters=12)
    grown = cv2.dilate(m.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
    out = np.where(m[..., None], out, np.where(grown[..., None], dil, lin))
    return lin_to_srgb(out)
