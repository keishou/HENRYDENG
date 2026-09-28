// contrast_scene.js - lane B test fixture for the contrast lane (BIBLE 6.4). Not a shot: try it on any shot with
//   node film/still.mjs --shot S19 --override S19=/film/src/type/fixtures/contrast_scene.js
// The frame: the left half paper white, the right half dark, and across the subtitle zone a band of hard stripes (a
// "mixed" box), so every type block meets bright, dark and mixed backgrounds. Deterministic; no assets.
import * as THREE from 'three';

export default {
  id: 'CONTRAST_FIXTURE',
  needs: {},
  async init(ctx) {
    const c = document.createElement('canvas'); c.width = 1920; c.height = 1080;
    const g = c.getContext('2d');
    g.fillStyle = '#e9e6df'; g.fillRect(0, 0, 960, 1080);
    g.fillStyle = '#141516'; g.fillRect(960, 0, 960, 1080);
    for (let x = 0; x < 1920; x += 48) { g.fillStyle = (x / 48) % 2 ? '#f0ede6' : '#0e0f10'; g.fillRect(x, 820, 24, 150); }
    const grad = g.createLinearGradient(0, 0, 0, 1080); grad.addColorStop(0, 'rgba(0,0,0,0)'); grad.addColorStop(1, 'rgba(0,0,0,0.25)');
    g.fillStyle = grad; g.fillRect(0, 0, 1920, 1080);
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace;
    this.scene = new THREE.Scene();
    this.scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false })));
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -1, 1);
  },
  frame(ctx, t, s) {
    return { layers: [{ scene: this.scene, camera: this.camera }], grade: 'SLATE', msaa: 0, text: s.shot.text };
  },
};
