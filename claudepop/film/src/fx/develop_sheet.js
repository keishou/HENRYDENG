// develop_sheet.js - a test scene for the shared develop() API (lane C): one print per option through the standalone
// material (and one through pass.texture), laid out flat under an orthographic camera. Not a shot; run it through the
// core's override hook:
//   node film/still.mjs --shot S40 --override S40=/film/src/fx/develop_sheet.js --res 1080
// It shows the photograph's print, so its output is face media: it lands under out/film/frames/stills/ (gitignored).
import * as THREE from 'three';
import { develop } from './develop.js';
import { loadPrint, PRINT_ASSETS } from './print.js';

const CASES = [
  ['developed', {}],
  ['+2 stops', { stops: 2 }],
  ['+4 stops', { stops: 4 }],
  ['fog + coin', { fog: { amount: 0.8, discs: [[0.5, 0.35, 0.18]] } }],
  ['fuse (mid)', { fuse: { t0: 0, t1: 2 } }],
  ['cyanotype', { cyan: 1 }],
  ['test strip', { strip: { bands: [0, 0, 0, 0], axis: 'x' } }],
  ['multi x3', { multi: [{ weight: 0.8, offset: [0.06, 0] }, { weight: 0.8, offset: [-0.05, 0.03] }, { weight: 0.8, offset: [0, -0.05] }] }],
  ['genLoss 3', { genLoss: 3 }],
  ['genLoss 6', { genLoss: 6 }],
  ['soft', { soft: { lod: 3.3, density: 0.8 } }],
  ['texture 512', { texture: { width: 512 } }],
];

export default {
  id: 'DEVELOP_SHEET',
  needs: { assets: PRINT_ASSETS },
  async init(ctx) {
    this.print = await loadPrint(ctx);
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0a0a09);
    const cols = 6, w = 0.28, h = 0.36, gap = 0.03;
    const aspect = 16 / 9, W = cols * (w + gap) + 0.06, H = W / aspect;
    this.cam = new THREE.OrthographicCamera(-W / 2, W / 2, H / 2, -H / 2, -1, 1);
    this.meshes = CASES.map((c, i) => {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h));
      m.position.set((i % cols - (cols - 1) / 2) * (w + gap), ((i < cols ? 0.5 : -0.5)) * (h + gap), 0);
      this.scene.add(m); return m;
    });
  },
  frame(ctx, t) {
    const P = this.print;
    CASES.forEach(([name, o], i) => {
      const multi = o.multi ? o.multi.map(m => ({ ...m, src: P.src, crop: P.crop })) : null;
      const pass = develop(ctx, { key: 'sheet' + i, src: P.src, certainty: P.cert, crop: P.crop, t: 1, tStart: -60, clock: 'linear',
        midLift: 1.2, halftone: { pitch: 0.0028, angle: 45 }, light: 0.9, ...o, ...(multi ? { multi } : {}) });
      if (o.texture) {
        this.meshes[i].material = this._texMat ??= new THREE.MeshBasicMaterial({ map: pass.texture });
      } else this.meshes[i].material = pass.material;
    });
    return {
      layers: [{ scene: this.scene, camera: this.cam }], grade: 'CYANOTYPE', post: { halftone: null, grainFrozen: false }, msaa: 0, text: null, hud: null,
      overlay: (hud) => {
        const c = hud.ctx; c.font = '500 16px "IBM Plex Mono", monospace'; c.fillStyle = '#FAF9F5';
        CASES.forEach(([name], i) => {
          const m = this.meshes[i], v = m.position.clone(); v.y += 0.18 + 0.012; v.project(this.cam);
          c.fillText(name.toUpperCase(), (v.x + 1) / 2 * 1920 - 70, (1 - v.y) / 2 * 1080);
        });
      },
    };
  },
};
