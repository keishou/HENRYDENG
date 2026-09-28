// STUB - owned by lane D, replace. (Frozen on day 0 by lane A: keep the default export { name, init(ctx) }; the api
// object init returns is the owner's to define, but keep `scene`, `camera` and `update(t, opts)` on it.)
//
// LINE / WALL (BIBLE 4.8): back wall 4 x 2.5 matte #0e0f10, stainless wire at 1.9 m, 33 mm paperclips, prints 0.28 x 0.36
// with curl, sway, tremble, fall (S17b), slip (S31); drips; wall objects (S34); the Draper moon print (S21); mirror prints (S45).
// Macro camera: FOV 6-8 deg at 0.25 m.
// Shots: S02(previs) S03 S11 S14 S17a-c S21 S27 S30 S31 S34 S45.
//
// Set module contract (all sets): a scene module lists the set in needs.sets; the core imports this file once, awaits
// init(ctx) once per page, and exposes the returned api as ctx.sets.line. Scenes call api.update(t, opts) at the start
// of their frame() (pure function of t: reset anything mutated) and return { layers: [{ scene: api.scene, camera }] }.
import * as THREE from 'three';

export default {
  name: 'line',
  async init(ctx) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d0e0f);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, 0.6));
    const camera = new THREE.PerspectiveCamera(7, 16 / 9, 0.02, 20); camera.position.set(0, 1.75, 0.25); camera.lookAt(0, 1.75, 0);
    return { scene, camera, update(t, opts = {}) {} };
  },
};
