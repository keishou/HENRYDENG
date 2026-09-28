// Pose a body GLB with retargeted clip frames (body/retarget_mh.py output converted to JSON:
// {bones:[names], frames:[{q:[[x,y,z,w]..], root:[x,y,z]}]}) and render them side by side in headless three.js.
//   node odyssey/body/glb_pose_test.mjs model.glb frames.json out.png
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const film = path.resolve(here, '../film');
const { chromium } = await import(path.join(film, 'node_modules/playwright-core/index.mjs'));
const [glbPath, framesPath, outPng] = process.argv.slice(2);
const N = JSON.parse(fs.readFileSync(framesPath, 'utf8')).frames.length;
const W = 420 * N, H = 820;
const HTML = `<!doctype html><html><body style="margin:0;background:#222">
<canvas id="c" width="${W}" height="${H}"></canvas>
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const r = new THREE.WebGLRenderer({ canvas: document.getElementById('c'), antialias: true, preserveDrawingBuffer: true });
r.outputColorSpace = THREE.SRGBColorSpace; r.setScissorTest(true);
const scene = new THREE.Scene();
scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.2));
const key = new THREE.DirectionalLight(0xffffff, 2.0); key.position.set(2, 4, 5); scene.add(key);
const grid = new THREE.GridHelper(4, 16, 0x666666, 0x444444); scene.add(grid);
const gltf = await new GLTFLoader().loadAsync('/model.glb');
scene.add(gltf.scene);
const clip = await (await fetch('/frames.json')).json();
const byName = {}; gltf.scene.traverse(o => { if (o.isBone) byName[o.name] = o; });
const san = n => THREE.PropertyBinding.sanitizeNodeName(n);  // GLTFLoader strips '.' etc. from node names
clip.bones = clip.bones.map(san);
const missing = clip.bones.filter(n => !byName[n]);
const rootName = clip.bones[0];
const out = { missing, frames: [] };
const cam = new THREE.PerspectiveCamera(22, 420 / ${H}, 0.05, 100);
clip.frames.forEach((f, i) => {
  clip.bones.forEach((n, b) => { const bone = byName[n]; if (bone) bone.quaternion.fromArray(f.q[b]); });
  byName[rootName].position.fromArray(f.root);
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(o => { if (o.isSkinnedMesh) { o.skeleton.update(); o.computeBoundingBox(); } });
  const box = new THREE.Box3().setFromObject(gltf.scene, true);
  const c = box.getCenter(new THREE.Vector3());
  out.frames.push({ min: box.min.toArray().map(x => +x.toFixed(3)), max: box.max.toArray().map(x => +x.toFixed(3)) });
  const a = 0.6;
  cam.position.set(c.x + Math.sin(a) * 5.2, 0.95, c.z + Math.cos(a) * 5.2); cam.lookAt(c.x, 0.9, c.z);
  grid.position.set(Math.round(c.x), 0, Math.round(c.z));
  r.setViewport(i * 420, 0, 420, ${H}); r.setScissor(i * 420, 0, 420, ${H});
  r.setClearColor(0x2a2a2a); r.render(scene, cam);
});
window.out = out; window.done = true;
</script></body></html>`;
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  let p = null, type = 'application/octet-stream';
  if (u === '/') { res.writeHead(200, { 'Content-Type': 'text/html' }); res.end(HTML); return; }
  if (u === '/model.glb') { p = path.resolve(glbPath); type = 'model/gltf-binary'; }
  else if (u === '/frames.json') { p = path.resolve(framesPath); type = 'application/json'; }
  else if (u.startsWith('/three/')) { p = path.join(film, 'node_modules', u); type = 'text/javascript'; }
  if (!p || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': type }); fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/`);
await page.waitForFunction('window.done === true', null, { timeout: 180000 });
console.log(JSON.stringify(await page.evaluate('window.out')));
await page.locator('#c').screenshot({ path: outPng });
await browser.close(); server.close();
