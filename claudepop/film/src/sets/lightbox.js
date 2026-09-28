// STUB - owned by lane D, replace. (Frozen on day 0 by lane A: keep the default export { name, init(ctx) }; the api
// object init returns is the owner's to define, but keep `scene`, `camera` and `update(t, opts)` on it.)
//
// LIGHTBOX / INSERTS (BIBLE 4.8): emissive PAPER light box; contact sheet (S13), negative sleeve (S29), Loom tree (S49),
// copy stand (S51), enlargement wall (S23).
// Shots: S13 S23 S29 S49 S51 S55.
//
// Set module contract (all sets): a scene module lists the set in needs.sets; the core imports this file once, awaits
// init(ctx) once per page, and exposes the returned api as ctx.sets.lightbox. Scenes call api.update(t, opts) at the start
// of their frame() (pure function of t: reset anything mutated) and return { layers: [{ scene: api.scene, camera }] }.
import * as THREE from 'three';

export default {
  name: 'lightbox',
  async init(ctx) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d0e0f);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, 0.6));
    const camera = new THREE.PerspectiveCamera(20, 16 / 9, 0.05, 20); camera.position.set(0, 1.2, 0); camera.up.set(0, 0, -1); camera.lookAt(0, 0, 0);
    return { scene, camera, update(t, opts = {}) {} };
  },
};
