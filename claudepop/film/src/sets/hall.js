// STUB - owned by lane E, replace. (Frozen on day 0 by lane A: keep the default export { name, init(ctx) }; the api
// object init returns is the owner's to define, but keep `scene`, `camera` and `update(t, opts)` on it.)
//
// HALL (BIBLE 4.8): builds on film/lookdev/looks.js buildL2 minus rain and crowd; floor 12 x 60 (z +2 .. -58), aisle
// x +-1.2, wet floor (Reflector 960x540), 38 rows x 2 x 5 prints via src/sets/prints.js, backlight panel 10 x 5 at z -58,
// FogExp2 0.025-0.035. Chorus master camera (0, 1.55, 0) looking down -Z, FOV 14 deg.
// Shots: S08 S15 S16 S19 S25 S28a S28b S33 S40 S43a-d S44 S48 S54 S56.
//
// Set module contract (all sets): a scene module lists the set in needs.sets; the core imports this file once, awaits
// init(ctx) once per page, and exposes the returned api as ctx.sets.hall. Scenes call api.update(t, opts) at the start
// of their frame() (pure function of t: reset anything mutated) and return { layers: [{ scene: api.scene, camera }] }.
import * as THREE from 'three';

export default {
  name: 'hall',
  async init(ctx) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d0e0f);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, 0.6));
    const camera = new THREE.PerspectiveCamera(14, 16 / 9, 0.1, 200); camera.position.set(0, 1.55, 0); camera.lookAt(0, 1.55, -10);
    return { scene, camera, update(t, opts = {}) {} };
  },
};
