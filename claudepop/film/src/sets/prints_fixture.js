// prints_fixture.js - lane E test scene for the SHARED src/sets/prints.js outside the hall (no hall haze: three's scene
// fog path), and a worked example for lane D. Not a shot; run it on any shot through the core's override hook:
//   node film/still.mjs --shot S03 --at mid --res 720 --override S03=/film/src/sets/prints_fixture.js
// A dark wall, one wire of five 0.28 x 0.36 prints (line layout) with the hall's photo atlas (development strips at
// five densities, one glossy), a grid of three blank sheets, one print falling from its clips, one capture flash and
// one recap, all as pure functions of the shot time; the camera is 1.2 m from the wire so the real clip meshes show.
import * as THREE from 'three';
import { Prints } from './prints.js';
import { PRINT_ASSETS } from '../fx/print.js';

export default {
  id: 'FIXTURE',
  needs: { sets: ['hall'], assets: PRINT_ASSETS },
  async init(ctx) {
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x0d0e0f, 0.08);
    const wall = new THREE.Mesh(new THREE.PlaneGeometry(4, 2.5), new THREE.MeshBasicMaterial({ color: 0x0e0f10 }));
    wall.position.set(0, 1.25, -0.25); this.scene.add(wall);
    this.photo = await ctx.sets.hall.photoAtlas();
    this.prints = new Prints(ctx, { max: 16, size: [0.28, 0.36] });
    this.line = this.prints.layout('line', { x0: -1.1, x1: 1.1, y: 1.9, z: 0, count: 5 });
    this.grid = this.prints.layout('grid', { x0: -0.5, y0: 1.35, dx: 0.5, dy: 0.45, cols: 3, rows: 1, z: 0.05 });
    this.prints.setAtlas(this.photo.atlas);
    this.scene.add(this.prints.object);
    this.cam = new THREE.PerspectiveCamera(40, 16 / 9, 0.05, 50);
    this.cam.position.set(0, 1.6, 1.2); this.cam.lookAt(0, 1.6, 0);
  },
  frame(ctx, t, s) {
    const pr = this.prints, P = this.photo, T0 = s.shot.t0;
    pr.reset();
    pr.light = { ...pr.light, ambient: [0.05, 0.05, 0.05], key: { dir: [0.2, 0.8, 0.6], color: [0.7, 0.68, 0.64] },
      back: { pos: [0, 2, -3], color: [0, 0, 0], near: 1, far: 5, shade: null }, transmission: 0.2 };
    this.line.forEach((id, i) => pr.set(id, { tex: P.strips[i % P.strips.length], density: [0.15, 0.35, 0.6, 0.85, 1][i], gloss: i === 4 ? 1 : 0 }));
    pr.set(this.line[1], { fall: { t0: T0 + 0.4, seed: 3 } });
    pr.set(this.grid[0], { capture: { t: T0 + 0.5, cell: P.strips[0][8], flash: 0.1 } });
    pr.set(this.grid[2], { recap: { t0: T0 + 0.3, t1: T0 + 0.9, cell: P.strips[2][6] } });
    pr.update(t, { camera: this.cam });
    return { layers: [{ scene: this.scene, camera: this.cam }], grade: 'DARKROOM', msaa: 0, text: null, hud: null };
  },
};
