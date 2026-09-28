// STUB - owned by lane C, replace. (Frozen on day 0 by lane A: keep the default export { name, init(ctx) }; the api
// object init returns is the owner's to define, but keep `scene`, `camera` and `update(t, opts)` on it.)
//
// TRAY (BIBLE 4.8): tray 0.34 x 0.42 x 0.06 black ABS, print 0.28 x 0.36 at y 0.020, liquid at y 0.022 (src/fx/liquid.js),
// development through src/fx/develop.js; easel + enlarger (S22, S39, S42); safelight = soft rectangle 1.2 m above, driven by
// ctx.tl.env(t). Camera "the tray lens": top-down, FOV 16 deg vertical, 1.45 m above the print.
// Shots: S01 S04 S09 S10 S20 S22 S24 S26 S32 S36-S39 S42 S47 S52 S53.
//
// Set module contract (all sets): a scene module lists the set in needs.sets; the core imports this file once, awaits
// init(ctx) once per page, and exposes the returned api as ctx.sets.tray. Scenes call api.update(t, opts) at the start
// of their frame() (pure function of t: reset anything mutated) and return { layers: [{ scene: api.scene, camera }] }.
import * as THREE from 'three';

export default {
  name: 'tray',
  async init(ctx) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d0e0f);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, 0.6));
    const camera = new THREE.PerspectiveCamera(16, 16 / 9, 0.05, 20); camera.position.set(0, 1.45 + 0.02, 0); camera.up.set(0, 0, -1); camera.lookAt(0, 0.02, 0);
    return { scene, camera, update(t, opts = {}) {} };
  },
};
