// STUB - owned by lane C, replace. (Frozen on day 0 by lane A: keep develop(ctx, opts) and the DevelopPass shape;
// lanes D and E develop prints through it.)
//
// develop.js - print development (BIBLE 4.8 TRAY): density D(x, t) = cap(x) * C((t - tStart) * k(x)),
//   C = characteristic curve (toe, shoulder), k = k0 * (0.35 + 0.65 * darkness) * (0.25 + 0.75 * certainty),
//   cap = D_target * (0.35 + 0.65 * certainty).
//
//   const pass = develop(ctx, opts) -> DevelopPass (cached by opts.key; calling again with the same key returns the same
//                                     pass, updated to the new opts, so it is safe to call every frame)
//     opts = { key, src: THREE.Texture (the photograph or a variant), certainty: THREE.Texture | null,
//              t, tStart, pulses16: bool | [t...], stops: 0..4, fog: 0..1, fuse: { t0, t1 } | null, cyan: 0..1,
//              strip: { bands: [t...] } | null, multi: [{ src, weight }] | null, genLoss: 0..n, freezeAt: seconds | null }
//   DevelopPass = { material: THREE.Material (the developed print, for a mesh), texture: THREE.Texture (the developed
//                   print as a 2D image, for Prints / lightbox atlases), update(opts), dispose() }
// This stub shows the source image as a finished print (no development).
import * as THREE from 'three';

const cache = new Map();
export function develop(ctx, opts = {}) {
  const key = opts.key ?? (opts.src ? opts.src.uuid : 'blank');
  let p = cache.get(key);
  if (!p) {
    const material = new THREE.MeshBasicMaterial({ map: opts.src || null, color: opts.src ? 0xffffff : 0xf2efe8 });
    p = { material, texture: opts.src || null, opts: {}, update(o) { Object.assign(this.opts, o); }, dispose() { material.dispose(); cache.delete(key); } };
    cache.set(key, p);
  }
  p.update(opts);
  return p;
}
