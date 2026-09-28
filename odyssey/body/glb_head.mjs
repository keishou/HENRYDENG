// Head close-ups of a body GLB in three.js (headless Chromium, software WebGL): front and 3/4, with the
// hair drawn as the GLB says (alpha MASK) and with alpha-to-coverage + MSAA (recommended for the film).
//   node odyssey/body/glb_head.mjs model.glb out.png
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const film = path.resolve(here, '../film');
const { chromium } = await import(path.join(film, 'node_modules/playwright-core/index.mjs'));
const [glbPath, outPng] = process.argv.slice(2);
const HTML = `<!doctype html><html><body style="margin:0;background:#1b1b1b">
<canvas id="c" width="1600" height="800"></canvas>
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const r = new THREE.WebGLRenderer({ canvas: document.getElementById('c'), antialias: true, preserveDrawingBuffer: true });
r.outputColorSpace = THREE.SRGBColorSpace; r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = 1.0;
r.setScissorTest(true);
const scene = new THREE.Scene();
scene.add(new THREE.HemisphereLight(0xf4f1ec, 0x5a5550, 1.5));
const key = new THREE.DirectionalLight(0xfff4e8, 2.2); key.position.set(-2, 3, 4); scene.add(key);
const fill = new THREE.DirectionalLight(0xe8f0ff, 0.8); fill.position.set(3, 1, 3); scene.add(fill);
const gltf = await new GLTFLoader().loadAsync('/model.glb');
scene.add(gltf.scene);
scene.updateMatrixWorld(true);
let eye = new THREE.Vector3();
gltf.scene.traverse(o => { if (o.isBone && o.name.startsWith('head')) { if (o.name === 'head') o.getWorldPosition(eye); } });
const tgt = eye.clone().add(new THREE.Vector3(0, 0.05, 0.05));
const hair = []; gltf.scene.traverse(o => { if (o.isMesh && /hair/i.test(o.material.name)) hair.push(o.material); });
const cam = new THREE.PerspectiveCamera(20, 1, 0.05, 50);
const shots = [[0, false], [35, false], [0, true], [35, true]];
shots.forEach(([deg, a2c], i) => {
  hair.forEach(m => { m.alphaToCoverage = a2c; m.needsUpdate = true; });
  const a = THREE.MathUtils.degToRad(deg), d = 0.95;
  cam.position.set(tgt.x + Math.sin(a) * d, tgt.y + 0.02, tgt.z + Math.cos(a) * d); cam.lookAt(tgt);
  r.setViewport(i * 400, 0, 400, 800); r.setScissor(i * 400, 0, 400, 800);
  cam.aspect = 0.5; cam.updateProjectionMatrix();
  r.setClearColor(0xcfccc7); r.render(scene, cam);
});
window.done = true;
</script></body></html>`;
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  let p = null, type = 'application/octet-stream';
  if (u === '/') { res.writeHead(200, { 'Content-Type': 'text/html' }); res.end(HTML); return; }
  if (u === '/model.glb') { p = path.resolve(glbPath); type = 'model/gltf-binary'; }
  else if (u.startsWith('/three/')) { p = path.join(film, 'node_modules', u); type = 'text/javascript'; }
  if (!p || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': type }); fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 800 } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/`);
await page.waitForFunction('window.done === true', null, { timeout: 180000 });
await page.locator('#c').screenshot({ path: outPng });
await browser.close(); server.close();
