#!/usr/bin/env python3
"""Certainty map for the tray (BIBLE 4.5 "density by certainty", 4.8 TRAY; lane C).

The photograph measured the front of his face and nothing else. This tool turns that into a map aligned pixel for pixel
with out/avatar/identity/face_clean_1024.png: high where the landmarks measured a feature (eyes, brows, nose, mouth),
lower on the rest of the face, and low where the picture is really a guess at an edge (ear rims, the outer hairline, the
jaw outline, the neck edge). src/fx/develop.js caps the final print density with it and orders development by
darkness x certainty.

    claudepop/out/venv/bin/python claudepop/film/tools/certainty.py [--preview]

Inputs (gitignored):  out/avatar/bust/facemesh.json   478 MediaPipe landmarks (image px = origin + p * px_per_unit, y up)
                      out/avatar/identity/face_clean_1024.png, face_hair_matte.png, matte.png
Outputs (gitignored, face data: never commit, never copy numbers from them into tracked files):
    out/film/data/certainty_1024.png   L8   certainty 0..1
    out/film/data/regions_1024.png     RGB8 feature masks for the development schedule: R pupils, G irises (incl. pupils),
                                            B brows + lash line
    out/film/data/regions2_1024.png    RGB8 R nostrils + lip line, G hair mass, B distance from the nearer eye
                                            (0 at the iris centre -> 1 at EYEDIST interocular distances), for "midtones
                                            fill outward from the eyes"
    out/film/data/certainty_1024.json  iris centres / radii, the photo's own catchlights, the eye line, the chin and the
                                       top of the hair in image px (top-left origin), for the framing rule in
                                       src/fx/print.js
    out/film/data/certainty_preview.jpg (--preview) the maps beside the photo, for review
The region masks are generous on purpose: develop.js only moves a masked pixel from its chemical density to its capped
final density, so light skin inside a mask barely changes and the dark feature inside it snaps.

Every length below is a proportion of the interocular distance D (iris centre to iris centre, measured at run time from
the landmarks), never a pixel count tuned to this photograph: the tracked file holds rules, the JSON holds the numbers.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
from scipy.spatial import ConvexHull

HERE = os.path.dirname(os.path.abspath(__file__))
CP = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(CP, 'out/film/data')
N = 1024
EYEDIST = 2.4      # regions2 B channel: distance from the nearer iris in interocular distances (0 .. 1 over 0 .. 2.4 D)

# MediaPipe face-mesh topology (index sets from mediapipe's face_mesh_connections; generic, not measured from the face)
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176,
             149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
EYE_R = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
EYE_L = [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466]
LID_R = [33, 246, 161, 160, 159, 158, 157, 173, 133]
LID_L = [263, 466, 388, 387, 386, 385, 384, 398, 362]
LOWLID_R = [33, 7, 163, 144, 145, 153, 154, 155, 133]
LOWLID_L = [263, 249, 390, 373, 374, 380, 381, 382, 362]
BROW_R = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
BROW_L = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
LIPS_OUT = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
LIPS_IN = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
NOSE = [168, 6, 197, 195, 5, 4, 1, 2, 98, 327, 64, 294, 129, 358, 49, 279, 48, 278, 219, 439, 94, 19, 122, 351, 196,
        419, 174, 399]
NOSE_LOW = [4, 1, 2, 98, 327, 64, 294, 129, 358, 49, 279, 48, 278, 219, 439, 94, 19, 97, 326, 45, 275]
IRIS_R, IRIS_L = (468, [469, 470, 471, 472]), (473, [474, 475, 476, 477])


def landmarks():
    d = json.load(open(os.path.join(CP, 'out/avatar/bust/facemesh.json')))
    p = np.array(d['points'], float)
    o, s = d['origin_px'], d['px_per_unit']
    assert d.get('image_px', N) == N
    return np.stack([o[0] + p[:, 0] * s, o[1] - p[:, 1] * s], 1)


def poly_mask(pts, dilate=0.0, blur=0.0):
    im = Image.new('L', (N, N), 0)
    ImageDraw.Draw(im).polygon([tuple(map(float, q)) for q in pts], fill=255)
    m = np.asarray(im, np.float32) / 255
    if dilate > 0:
        m = (ndimage.distance_transform_edt(m < 0.5) <= dilate).astype(np.float32)
    if blur > 0:
        m = ndimage.gaussian_filter(m, blur)
    return m


def line_mask(pts, width, blur=1.0):
    im = Image.new('L', (N, N), 0)
    ImageDraw.Draw(im).line([tuple(map(float, q)) for q in pts], fill=255, width=int(round(width)), joint='curve')
    return ndimage.gaussian_filter(np.asarray(im, np.float32) / 255, blur)


def hull(pts):
    h = ConvexHull(pts)
    return pts[h.vertices]


def disc(cx, cy, r, soft=1.5):
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    d = np.hypot(x - cx, y - cy)
    return np.clip((r - d) / soft + 0.5, 0, 1)


def smooth01(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def iris_of(L, spec):
    c, ring = spec
    cx, cy = L[c]
    r = float(np.mean([np.hypot(*(L[i] - L[c])) for i in ring]))
    return float(cx), float(cy), r


def catchlight(lum, cx, cy, r):
    """The photo's own catchlight: the strongest small bright blob (luminance above its surround) in the inner part of
    the iris, away from the sclera edge."""
    y, x = np.mgrid[0:N, 0:N]
    inside = (np.hypot(x - cx, y - cy) < r * 0.6) & (y < cy - 0.1 * r)       # catchlights sit above the centre (a light from above)
    sm = ndimage.gaussian_filter(lum, 1.0)
    top = sm - ndimage.gaussian_filter(lum, 0.28 * r)
    v = np.where(inside, top, -1)
    iy, ix = np.unravel_index(np.argmax(v), v.shape)
    return float(ix), float(iy), float(v[iy, ix])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true')
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    L = landmarks()
    rgb = np.asarray(Image.open(os.path.join(CP, 'out/avatar/identity/face_clean_1024.png')).convert('RGB'), np.float32) / 255
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    lum = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    lum_d = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)          # display luma, for dark/light tests
    head = np.asarray(Image.open(os.path.join(CP, 'out/avatar/identity/face_hair_matte.png')).convert('L'), np.float32) / 255
    person = np.asarray(Image.open(os.path.join(CP, 'out/avatar/identity/matte.png')).convert('L'), np.float32) / 255

    D = float(np.hypot(L[IRIS_L[0]][0] - L[IRIS_R[0]][0], L[IRIS_L[0]][1] - L[IRIS_R[0]][1]))   # interocular distance
    u = lambda k: k * D
    oval = poly_mask(L[FACE_OVAL])
    oval_s = ndimage.gaussian_filter(oval, u(.018))
    d_oval_in = ndimage.distance_transform_edt(oval > 0.5)               # px inside the face oval to its outline
    d_head_in = ndimage.distance_transform_edt(head > 0.5)                # px inside the head silhouette to its edge
    d_person_in = ndimage.distance_transform_edt(person > 0.5)
    eye_y = float((L[IRIS_R[0]][1] + L[IRIS_L[0]][1]) / 2)
    chin_y = float(L[152][1])
    yy = np.mgrid[0:N, 0:N][0].astype(np.float32)

    # regions
    ir, il = iris_of(L, IRIS_R), iris_of(L, IRIS_L)
    pupil = np.maximum(disc(ir[0], ir[1], ir[2] * 0.46), disc(il[0], il[1], il[2] * 0.46))
    iris = np.maximum(disc(ir[0], ir[1], ir[2] * 1.1), disc(il[0], il[1], il[2] * 1.1))
    eye_open = np.maximum(poly_mask(L[EYE_R]), poly_mask(L[EYE_L]))
    lidcut = np.clip(ndimage.gaussian_filter((ndimage.distance_transform_edt(eye_open < 0.5) <= u(.009)).astype(np.float32), u(.006)), 0, 1)
    iris *= lidcut
    pupil *= lidcut
    brows = np.maximum(poly_mask(L[BROW_R], dilate=u(.055), blur=u(.018)), poly_mask(L[BROW_L], dilate=u(.055), blur=u(.018)))
    lash = np.maximum.reduce([line_mask(L[LID_R], u(.055), u(.009)), line_mask(L[LID_L], u(.055), u(.009)),
                              line_mask(L[LOWLID_R], u(.024), u(.007)), line_mask(L[LOWLID_L], u(.024), u(.007))])
    brow_lash = np.clip(np.maximum(brows, lash), 0, 1)
    nose_low = poly_mask(hull(L[NOSE_LOW]), dilate=u(.03), blur=u(.015))
    lips = poly_mask(L[LIPS_OUT], dilate=u(.03), blur=u(.015))
    lipline = line_mask(L[LIPS_IN + LIPS_IN[:1]], u(.037), u(.009))
    nose_lip = np.clip(np.maximum.reduce([nose_low, lips, lipline]), 0, 1)
    # ears: the head silhouette outside the face oval, at ear height, skin-light
    band = smooth01(eye_y - u(.55), eye_y - u(.30), yy) * (1 - smooth01(eye_y + u(.91), eye_y + u(1.16), yy))
    outside = np.clip(head - oval_s, 0, 1)
    light = smooth01(0.30, 0.45, ndimage.gaussian_filter(lum_d, u(.012)))
    ears = np.clip(outside * band * light, 0, 1)
    # hair: the rest of the head outside the oval, plus the dark fringe strands inside it above the eyes
    dark = 1 - smooth01(0.22, 0.36, ndimage.gaussian_filter(lum_d, u(.009)))
    fringe = oval * dark * (1 - smooth01(eye_y - u(.24), eye_y - u(.11), yy))
    hair = np.clip(np.maximum(outside * (1 - ears) * (1 - smooth01(0.30, 0.5, ndimage.gaussian_filter(lum_d, u(.018)))), fringe), 0, 1)
    hair = ndimage.gaussian_filter(hair, u(.015))
    # distance from the nearer eye
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    deye = np.minimum(np.hypot(x - ir[0], y - ir[1]), np.hypot(x - il[0], y - il[1]))
    eyedist = np.clip(deye / u(EYEDIST), 0, 1)

    # certainty
    neck_clothes = np.clip(person - head, 0, 1)
    skin = smooth01(0.33, 0.45, ndimage.gaussian_filter(lum_d, u(.012)))
    neck = neck_clothes * skin
    shirt = neck_clothes * (1 - skin)
    feats = np.clip(np.maximum.reduce([
        np.maximum(poly_mask(L[EYE_R], dilate=u(.073), blur=u(.024)), poly_mask(L[EYE_L], dilate=u(.073), blur=u(.024))),
        np.maximum(poly_mask(L[BROW_R], dilate=u(.061), blur=u(.024)), poly_mask(L[BROW_L], dilate=u(.061), blur=u(.024))),
        poly_mask(hull(L[NOSE]), dilate=u(.049), blur=u(.024)),
        poly_mask(L[LIPS_OUT], dilate=u(.061), blur=u(.024))]), 0, 1)
    # the face: 0.9 inside, down to 0.22 on the jaw outline (below the eyes; the outline above is under the fringe)
    lower = smooth01(eye_y + u(.06), eye_y + u(.55), yy)
    jaw = 0.22 + (0.9 - 0.22) * smooth01(u(.012), u(.23), d_oval_in)
    face_c = np.maximum(0.9 * (1 - lower) + jaw * lower, feats)
    # hair: dense inside, thin toward the outer silhouette
    hair_c = 0.08 + 0.77 * smooth01(u(.018), u(.58), d_head_in)
    ear_c = 0.07 + 0.33 * smooth01(u(.012), u(.16), d_head_in)
    neck_c = 0.1 + 0.42 * smooth01(u(.012), u(.21), d_person_in) * (1 - smooth01(chin_y + u(.91), chin_y + u(1.58), yy) * 0.3)
    shirt_c = 0.1 + 0.25 * smooth01(u(.012), u(.24), d_person_in)
    # outside the face: every head pixel is hair or ear, every body pixel neck or shirt (no gaps at the oval seam)
    c_head = ears * ear_c + (1 - ears) * hair_c
    c_body = skin * neck_c + (1 - skin) * shirt_c
    c_out = head * c_head + np.clip(person - head, 0, 1) * c_body
    c = c_out * (1 - oval_s) + face_c * oval_s
    c = np.maximum(c, feats * np.clip(oval_s * 2, 0, 1))
    c = np.where(ears > 0.5, np.minimum(c, ear_c + 0.02), c)                # the ear rims stay a guess
    c = ndimage.gaussian_filter(c, u(.018)) * np.clip(person * 1.2, 0, 1)
    c = np.clip(c, 0, 1)

    save_l = lambda arr, name: Image.fromarray(np.round(np.clip(arr, 0, 1) * 255).astype(np.uint8), 'L').save(os.path.join(OUT, name))
    save_rgb = lambda r, g, b, name: Image.fromarray(np.round(np.clip(np.stack([r, g, b], -1), 0, 1) * 255).astype(np.uint8), 'RGB').save(os.path.join(OUT, name))
    save_l(c, 'certainty_1024.png')
    save_rgb(pupil, iris, brow_lash, 'regions_1024.png')
    save_rgb(nose_lip, hair, eyedist, 'regions2_1024.png')
    # the top of the hair and the head's width (the framing rule in src/fx/print.js: the hair top inside the print)
    rows = np.where((head > 0.5).sum(1) > 3)[0]
    cols = np.where((head > 0.5).sum(0) > 3)[0]
    hair_top = float(rows.min()) if len(rows) else 0.0
    head_x = [float(cols.min()), float(cols.max())] if len(cols) else [0.0, float(N)]
    cr, cl = catchlight(lum, *ir), catchlight(lum, *il)
    # one light made both: use the clearer catchlight's offset (in iris radii) for both eyes
    ref, ri = (cr, ir) if cr[2] >= cl[2] else (cl, il)
    off = ((ref[0] - ri[0]) / ri[2], (ref[1] - ri[1]) / ri[2])
    cr = (ir[0] + off[0] * ir[2], ir[1] + off[1] * ir[2], cr[2]); cl = (il[0] + off[0] * il[2], il[1] + off[1] * il[2], cl[2])
    meta = {'_about': 'face-derived (gitignored): iris centres / radii and the photo catchlights, image px, top-left origin, '
                      'aligned to out/avatar/identity/face_clean_1024.png. Built by film/tools/certainty.py.',
            'size': N, 'iris': [list(ir), list(il)], 'catch': [list(cr[:2]), list(cl[:2])],
            'eye_y': eye_y, 'chin_y': chin_y, 'hair_top': hair_top, 'head_x': head_x, 'iod': D, 'eyedist_iod': EYEDIST}
    json.dump(meta, open(os.path.join(OUT, 'certainty_1024.json'), 'w'), indent=1)
    print('wrote', os.path.join(OUT, 'certainty_1024.png'), '+ regions_1024.png, regions2_1024.png, certainty_1024.json')

    if a.preview:
        k = 512
        ph = Image.open(os.path.join(CP, 'out/avatar/identity/face_clean_1024.png')).convert('RGB').resize((k, k), Image.LANCZOS)
        cm = Image.fromarray(np.round(c * 255).astype(np.uint8)).resize((k, k), Image.LANCZOS).convert('RGB')
        reg = np.zeros((N, N, 3), np.float32)
        for m, col in [(hair, (0.35, 0.35, 0.9)), (ears, (0.2, 0.8, 0.8)), (nose_lip, (0.9, 0.3, 0.3)),
                       (brow_lash, (0.9, 0.9, 0.2)), (iris, (0.3, 0.9, 0.3)), (pupil, (1, 1, 1))]:
            reg = reg * (1 - m[..., None]) + np.array(col, np.float32) * m[..., None]
        rg = Image.fromarray(np.round(np.clip(reg * 0.75 + rgb * 0.25, 0, 1) * 255).astype(np.uint8)).resize((k, k), Image.LANCZOS)
        ed = Image.fromarray(np.round(eyedist * 255).astype(np.uint8)).resize((k, k)).convert('RGB')
        sheet = Image.new('RGB', (k * 4, k))
        for i, im in enumerate([ph, cm, rg, ed]):
            sheet.paste(im, (i * k, 0))
        sheet.save(os.path.join(OUT, 'certainty_preview.jpg'), quality=90)
        print('preview', os.path.join(OUT, 'certainty_preview.jpg'))


if __name__ == '__main__':
    main()
