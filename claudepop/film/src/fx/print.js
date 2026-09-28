// print.js - the photograph as a print (lane C; shared): the assets every print of the photograph uses, and the framing
// rule that crops it to the face. Face numbers (iris centres, the photo's catchlights, the chin, the top of the hair) are
// read at run time from out/film/data/certainty_1024.json (film/tools/certainty.py); nothing measured from the face is
// in this file: the rule is written in interocular distances (D).
//
//   PRINT_ASSETS                          put in a scene's needs.assets
//   await loadPrint(ctx) -> { src, cert, regions: [r1, r2], meta, crop, iod }   textures for develop() + the face crop
//   faceCrop(meta, W, H, opts) -> [x0, y0, w, h]   a 7:9 crop in source px (top-left origin)
//   eyesUV(meta, crop) -> [[u, v, r]...]   the iris centres (and radii, in uv of the print height) in print uv (v up)
//   blinkEyes(meta, crop) -> develop()'s blink.eyes for the two eyes (the lid geometry as proportions of D)
//
// THE FRAMING RULE (BIBLE 4.5, revised after the foundation review): the print is the face, not an ID photo. The chin sits
// just above the bottom edge (chinMargin D below the chin), the top of the hair just inside the top edge (hairMargin D
// above it), no shoulders, no shirt; the width follows from the 7:9 paper; centred between the irises. opts.widthIOD
// (+ eyeLine) selects the old width-based rule, for a deliberate variant.
const DATA = '/out/film/data/';
export const PRINT_ASSETS = ['/out/avatar/identity/face_clean_1024.png', DATA + 'certainty_1024.png', DATA + 'regions_1024.png',
  DATA + 'regions2_1024.png', DATA + 'certainty_1024.json'];

export const FRAMING = { chinMargin: 0.10, hairMargin: 0.10, aspect: 7 / 9 };

const iodOf = meta => { const [a, b] = meta.iris; return Math.hypot(b[0] - a[0], b[1] - a[1]); };

export function faceCrop(meta, W = 1024, H = 1024, opts = {}) {
  const [a, b] = meta.iris, iod = iodOf(meta), cx = (a[0] + b[0]) / 2, ey = (a[1] + b[1]) / 2;
  const aspect = opts.aspect ?? FRAMING.aspect;
  let w, h, y0;
  if (opts.widthIOD !== undefined || meta.chin_y == null || meta.hair_top == null) {
    const widthIOD = opts.widthIOD ?? 3.8, eyeLine = opts.eyeLine ?? 0.44;
    w = widthIOD * iod; h = w / aspect; y0 = ey - eyeLine * h;
  } else {
    const bottom = meta.chin_y + (opts.chinMargin ?? FRAMING.chinMargin) * iod;
    const top = meta.hair_top - (opts.hairMargin ?? FRAMING.hairMargin) * iod;
    h = bottom - top; w = h * aspect; y0 = top;
  }
  if (h > H) { h = H; w = h * aspect; }
  if (w > W) { w = W; h = w / aspect; }
  const x0 = Math.min(W - w, Math.max(0, cx - w / 2));
  y0 = Math.min(H - h, Math.max(0, y0));
  return [x0, y0, w, h];
}

// source px (top-left origin) -> print uv (v up) through a crop
export const cropUV = (crop, px, py) => [(px - crop[0]) / crop[2], 1 - (py - crop[1]) / crop[3]];

export function eyesUV(meta, crop) {
  return meta.iris.map(([x, y, r]) => [...cropUV(crop, x, y), r / crop[3]]);
}

// the lids for develop({ blink }): per eye [u, v, half width, lash, lower lid, brow band] in print uv (v up). Generic
// proportions of an eye (D = interocular distance, r = iris radius), not measurements: the opening is an almond about
// 0.3 D to each side of the iris centre; at the centre the upper lash line lies 0.9 r above it, the lower lid 1.0 r below;
// the stretched lid band reaches 0.42 D above the centre (under the brow)
export function blinkEyes(meta, crop) {
  const iod = iodOf(meta), U = crop[2], V = crop[3];
  return meta.iris.map(([x, y, r]) => { const [u, v] = cropUV(crop, x, y); return [u, v, 0.3 * iod / U, 0.9 * r / V, 1.0 * r / V, 0.42 * iod / V]; });
}

export async function loadPrint(ctx) {
  const A = ctx.assets;
  const [src, cert, r1, r2, meta] = await Promise.all([
    A.texture(PRINT_ASSETS[0]), A.texture(PRINT_ASSETS[1], { srgb: false }), A.texture(PRINT_ASSETS[2], { srgb: false }),
    A.texture(PRINT_ASSETS[3], { srgb: false }), A.json(PRINT_ASSETS[4])]);
  return { src, cert, regions: [r1, r2], meta, iod: iodOf(meta), crop: faceCrop(meta, src.image.width, src.image.height) };
}
