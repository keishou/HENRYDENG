// Render a full-body GLB (metres, y-up) from 4 directions + a head close-up in headless Chromium.
//   node odyssey/body/glb_views.mjs model.glb out.png
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const film = path.resolve(here, '../film');
const { chromium } = await import(path.join(film, 'node_modules/playwright-core/index.mjs'));
const [glbPath, outPng, headDist = '1.3'] = process.argv.slice(2);  // optional close-up distance (m)

const HTML = `<!doctype html><html><head><script>window.HD=${Number(headDist)}</script></head><body style="margin:0;background:#1b1b1b">
<canvas id="c" width="2000" height="800"></canvas>
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const r = new THREE.WebGLRenderer({ canvas: document.getElementById('c'), antialias: true, preserveDrawingBuffer: true });
r.outputColorSpace = THREE.SRGBColorSpace;
r.setScissorTest(true);
const scene = new THREE.Scene();
scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.2));
const key = new THREE.DirectionalLight(0xffffff, 2.0); scene.add(key);
const gltf = await new GLTFLoader().loadAsync('/model.glb');
scene.add(gltf.scene);
const box = new THREE.Box3().setFromObject(gltf.scene);
const size = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
window.bbox = { min: box.min.toArray(), max: box.max.toArray() };
const cam = new THREE.PerspectiveCamera(20, 400 / 800, 0.05, 100); const HD = window.HD;
[0, 90, 180, 270].forEach((deg, i) => {
  const a = THREE.MathUtils.degToRad(deg), d = size.y * 3.1;
  cam.aspect = 400 / 800; cam.updateProjectionMatrix();
  cam.position.set(c.x + Math.sin(a) * d, c.y, c.z + Math.cos(a) * d); cam.lookAt(c);
  key.position.set(Math.sin(a + 0.5) * 5, 4, Math.cos(a + 0.5) * 5);
  r.setViewport(i * 400, 0, 400, 800); r.setScissor(i * 400, 0, 400, 800);
  r.setClearColor(0x2a2a2a); r.render(scene, cam);
});
// head close-up (front, slightly right)
const head = new THREE.Vector3(c.x, box.max.y - size.y * 0.075, c.z);
cam.aspect = 400 / 800; cam.fov = 20; cam.updateProjectionMatrix();
cam.position.set(head.x + 0.25 * HD / 1.3, head.y + 0.02, head.z + HD); cam.lookAt(head);
key.position.set(2, 3, 4);
r.setViewport(1600, 0, 400, 800); r.setScissor(1600, 0, 400, 800);
r.setClearColor(0x2a2a2a); r.render(scene, cam);
window.done = true;
</script></body></html>`;

const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  let p = null, type = 'application/octet-stream';
  if (u === '/' ) { res.writeHead(200, { 'Content-Type': 'text/html' }); res.end(HTML); return; }
  if (u === '/model.glb') { p = path.resolve(glbPath); type = 'model/gltf-binary'; }
  else if (u.startsWith('/three/')) { p = path.join(film, 'node_modules', u); type = 'text/javascript'; }
  if (!p || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': type }); fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 2000, height: 800 } });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/`);
await page.waitForFunction('window.done === true', null, { timeout: 180000 });
console.log('bbox', JSON.stringify(await page.evaluate('window.bbox')));
await page.locator('#c').screenshot({ path: outPng });
await browser.close(); server.close();
