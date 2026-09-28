// STUB - owned by lane F, replace. (Frozen on day 0 by lane A: keep the default export { name, init(ctx) }; the api
// object init returns is the owner's to define, but keep `scene`, `camera` and `update(t, opts)` on it.)
//
// BEAM (BIBLE 4.8): black room, matte wall 1.2 m behind the head, SpotLight with .map = the photograph at photo_camera
// (out/avatar/subject_camera.json), PCF soft shadows 2048^2; subject.glb heads (clay / photo looks); turntable (S50).
// Shots: S06 S12 S41 S50.
//
// Set module contract (all sets): a scene module lists the set in needs.sets; the core imports this file once, awaits
// init(ctx) once per page, and exposes the returned api as ctx.sets.beam. Scenes call api.update(t, opts) at the start
// of their frame() (pure function of t: reset anything mutated) and return { layers: [{ scene: api.scene, camera }] }.
import * as THREE from 'three';

export default {
  name: 'beam',
  async init(ctx) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d0e0f);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, 0.6));
    const camera = new THREE.PerspectiveCamera(16, 16 / 9, 0.1, 50); camera.position.set(0, 1.62, 1.6); camera.lookAt(0, 1.62, 0);
    return { scene, camera, update(t, opts = {}) {} };
  },
};
