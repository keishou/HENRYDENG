// print.js - the photograph as a print (lane C; shared): the assets every print of the photograph uses, and the framing
// rule that crops it to the face. Face numbers (iris centres, the photo's catchlights) are read at run time from
// out/film/data/certainty_1024.json (film/tools/certainty.py); nothing measured from the face is in this file.
//
//   PRINT_ASSETS                          put in a scene's needs.assets
//   await loadPrint(ctx) -> { src, cert, regions: [r1, r2], meta, crop }   textures for develop() + the face crop
//   faceCrop(meta, W, H, { widthIOD = 3.8, eyeLine = 0.44 }) -> [x0, y0, w, h]   a 7:9 crop: width = widthIOD interocular
//                                          distances, centred between the irises, the eye line eyeLine down from the top
const DATA = '/out/film/data/';
export const PRINT_ASSETS = ['/out/avatar/identity/face_clean_1024.png', DATA + 'certainty_1024.png', DATA + 'regions_1024.png',
  DATA + 'regions2_1024.png', DATA + 'certainty_1024.json'];

// framing rules (proportions, not measurements): the print is 7:9, its width 3.8 interocular distances, centred between
// the irises, the eye line 44 % down from the top edge
export function faceCrop(meta, W = 1024, H = 1024, { widthIOD = 3.8, eyeLine = 0.44 } = {}) {
  const [a, b] = meta.iris, iod = Math.hypot(b[0] - a[0], b[1] - a[1]);
  let w = widthIOD * iod, h = w * 9 / 7;
  if (h > H) { h = H; w = h * 7 / 9; }
  const cx = (a[0] + b[0]) / 2, ey = (a[1] + b[1]) / 2;
  const x0 = Math.min(W - w, Math.max(0, cx - w / 2)), y0 = Math.min(H - h, Math.max(0, ey - eyeLine * h));
  return [x0, y0, w, h];
}

export async function loadPrint(ctx) {
  const A = ctx.assets;
  const [src, cert, r1, r2, meta] = await Promise.all([
    A.texture(PRINT_ASSETS[0]), A.texture(PRINT_ASSETS[1], { srgb: false }), A.texture(PRINT_ASSETS[2], { srgb: false }),
    A.texture(PRINT_ASSETS[3], { srgb: false }), A.json(PRINT_ASSETS[4])]);
  return { src, cert, regions: [r1, r2], meta, crop: faceCrop(meta, src.image.width, src.image.height) };
}
