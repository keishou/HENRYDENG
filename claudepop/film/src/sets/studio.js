// STUB - owned by lane F, replace. (Frozen on day 0 by lane A: keep the default export { name, init(ctx) }; the api
// object init returns is the owner's to define, but keep `scene`, `camera` and `update(t, opts)` on it.)
//
// STUDIO (BIBLE 4.8): cyclorama 8 x 6 x 4 PAPER matte, stool (seat 0.33 at 0.60 m, footring 0.25 m), tape X; one large
// soft frontal area light + hemisphere fill.
// Shots: S05 S35 S46 (+ S30 print renders).
//
// Set module contract (all sets): a scene module lists the set in needs.sets; the core imports this file once, awaits
// init(ctx) once per page, and exposes the returned api as ctx.sets.studio. Scenes call api.update(t, opts) at the start
// of their frame() (pure function of t: reset anything mutated) and return { layers: [{ scene: api.scene, camera }] }.
import * as THREE from 'three';

export default {
  name: 'studio',
  async init(ctx) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d0e0f);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, 0.6));
    const camera = new THREE.PerspectiveCamera(27, 16 / 9, 0.1, 50); camera.position.set(0, 1.0, 4.2); camera.lookAt(0, 0.8, 0);
    return { scene, camera, update(t, opts = {}) {} };
  },
};
