// Render the avatar GLB with three.js in headless Chromium (SwiftShader) - the renderer the film uses.
//   node render_glb.mjs MODEL.glb OUT_DIR [--camera subject_camera.json] [--modes turn,photo,head,pose] [--size 1024]
// turn : front / 3-4 / profile / back full-body views (one PNG each) + a contact strip
// photo: the photo's own camera (subject_camera.json photo_camera), soft frontal light -> compare with the photo
// head : head close-ups from 0/35/90/180 degrees
// pose : a test pose (arms down, head turned, knee bent) to check skinning, front + 3-4
// views: review close-ups from a JSON list (--views FILE)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const nm = path.join(here, 'node_modules');
const { chromium } = await import(path.join(nm, 'playwright-core/index.mjs'));
const args = process.argv.slice(2);
const glbPath = path.resolve(args[0]);
const outDir = path.resolve(args[1]);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const camPath = opt('--camera', path.join(path.dirname(glbPath), 'subject_camera.json'));
const modes = opt('--modes', 'turn,photo,head,pose').split(',');
const SIZE = Number(opt('--size', '1024'));
const BG = opt('--bg', '0x2a2a2a');
const HIDE = opt('--hide', '');
fs.mkdirSync(outDir, { recursive: true });
const camJson = fs.existsSync(camPath) ? fs.readFileSync(camPath, 'utf8') : 'null';

const HTML = `<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;background:#111">
<canvas id="c"></canvas>
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const CAM = ${camJson};
const canvas = document.getElementById('c');
const r = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
r.outputColorSpace = THREE.SRGBColorSpace;
r.setPixelRatio(1);
const scene = new THREE.Scene();
const hemi = new THREE.HemisphereLight(0xffffff, 0x3a3a3a, 1.1); scene.add(hemi);
const key = new THREE.DirectionalLight(0xffffff, 1.9); scene.add(key); scene.add(key.target);
const fill = new THREE.DirectionalLight(0xdde6ff, 0.6); scene.add(fill); scene.add(fill.target);
const rim = new THREE.DirectionalLight(0xffffff, 0.9); scene.add(rim); scene.add(rim.target);
const gltf = await new GLTFLoader().loadAsync('/model.glb');
scene.add(gltf.scene);
// the alpha-tested hair shell: alpha to coverage on the MSAA canvas softens its hard card edges (as avatar.js does in
// the film's MSAA targets); not on the sparse fur shells, where it dithers their cut edge into a dotted light line
gltf.scene.traverse(o => { if (o.isMesh && o.name === 'hair' && o.material.alphaTest > 0) o.material.alphaToCoverage = true; });
const HIDE = '${HIDE}'.split(',').filter(Boolean);
const hid = (n) => HIDE.some(h => h.startsWith('=') ? n === h.slice(1) : n.startsWith(h));
gltf.scene.traverse(o => { if (o.isMesh && (hid(o.name) || (o.parent && hid(o.parent.name)))) o.visible = false; });
let skinned = null; gltf.scene.traverse(o => { if (o.isSkinnedMesh) { skinned = o; o.frustumCulled = false; } });
const bones = {}; if (skinned) skinned.skeleton.bones.forEach(b => bones[b.name] = b);
const rest = {}; for (const [k, b] of Object.entries(bones)) rest[k] = b.quaternion.clone();
const box = new THREE.Box3().setFromObject(gltf.scene);
window.info = { bbox: [box.min.toArray(), box.max.toArray()], bones: skinned ? skinned.skeleton.bones.length : 0,
  tris: (() => { let t = 0; gltf.scene.traverse(o => { if (o.isMesh) t += o.geometry.index.count / 3; }); return t; })() };
function setLights(az) {
  key.position.set(Math.sin(az + 0.6) * 5, 4, Math.cos(az + 0.6) * 5);
  fill.position.set(Math.sin(az - 1.0) * 5, 1.5, Math.cos(az - 1.0) * 5);
  rim.position.set(-Math.sin(az) * 5, 3, -Math.cos(az) * 5);
}
function resetPose() { for (const [k, b] of Object.entries(bones)) b.quaternion.copy(rest[k]); }
function rotBone(name, axis, deg) {   // rotate a bone about a WORLD axis (applied in its parent frame)
  const b = bones[name] || bones[name.replace(/[.]/g, '')]; if (!b) return;
  b.updateMatrixWorld(true);
  const pq = new THREE.Quaternion(); b.parent.getWorldQuaternion(pq);
  const wq = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(...axis).normalize(), THREE.MathUtils.degToRad(deg));
  const lq = pq.clone().invert().multiply(wq).multiply(pq);
  b.quaternion.premultiply(lq);
  b.updateMatrixWorld(true);
}
window.testPose = () => {
  resetPose();
  rotBone('upperarm01.L', [0, 0, 1], -38); rotBone('upperarm01.R', [0, 0, 1], 38);
  rotBone('lowerarm01.L', [1, 0, 0], -25); rotBone('lowerarm01.R', [1, 0, 0], -25);
  rotBone('neck02', [0, 1, 0], 18); rotBone('head', [0, 1, 0], 14); rotBone('head', [1, 0, 0], 8);
  rotBone('upperleg01.R', [1, 0, 0], -22); rotBone('lowerleg01.R', [1, 0, 0], 40);
  rotBone('spine03', [0, 1, 0], -8);
};
window.renderView = (kind, p) => {
  const W = p.w, H = p.h; r.setSize(W, H, false);
  r.setClearColor(new THREE.Color(Number(p.bg)), 1);
  let cam;
  if (kind === 'photo') {
    const c = CAM.photo_camera;
    cam = new THREE.PerspectiveCamera(30, W / H, 0.05, 50);
    const s = W / c.W;
    const f = c.f * s, cx = c.cx * s, cy = c.cy * s, n = 0.05, fa = 50;
    cam.projectionMatrix.set(2 * f / W, 0, 1 - 2 * cx / W, 0,  0, 2 * f / H, 2 * cy / H - 1, 0,
                             0, 0, -(fa + n) / (fa - n), -2 * fa * n / (fa - n),  0, 0, -1, 0);
    cam.projectionMatrixInverse.copy(cam.projectionMatrix).invert();
    const R = c.R, t = c.t;
    const eye = [-(R[0][0]*t[0] + R[1][0]*t[1] + R[2][0]*t[2]), -(R[0][1]*t[0] + R[1][1]*t[1] + R[2][1]*t[2]), -(R[0][2]*t[0] + R[1][2]*t[1] + R[2][2]*t[2])];
    const M = new THREE.Matrix4().set(R[0][0], R[1][0], R[2][0], eye[0],  R[0][1], R[1][1], R[2][1], eye[1],  R[0][2], R[1][2], R[2][2], eye[2],  0, 0, 0, 1);
    cam.matrixAutoUpdate = false; cam.matrix.copy(M); cam.matrixWorld.copy(M); cam.matrixWorldInverse.copy(M).invert();
    // flat, frontal light like a passport photo booth (the photo's own shading is already in the albedo)
    hemi.color.set(0xffffff); hemi.groundColor.set(0xd8d4d0);
    hemi.intensity = Number(p.hemi ?? 2.4); key.intensity = Number(p.key ?? 0.9); fill.intensity = 0.3; rim.intensity = 0.0;
    key.position.set(eye[0] + 0.3, eye[1] + 0.6, eye[2] + 2); fill.position.set(eye[0] - 1.5, eye[1], eye[2] + 2);
  } else {
    hemi.color.set(0xffffff); hemi.groundColor.set(p.flat ? 0xd8d4d0 : 0x807a74);
    hemi.intensity = p.flat ? 2.4 : 1.35; key.intensity = p.flat ? 0.9 : 1.7; fill.intensity = p.flat ? 0.3 : 0.6; rim.intensity = p.flat ? 0 : 0.8;
    const az = THREE.MathUtils.degToRad(p.az);
    cam = new THREE.PerspectiveCamera(p.fov, W / H, 0.05, 50);
    const tgt = new THREE.Vector3(...p.target);
    cam.position.set(tgt.x + Math.sin(az) * p.dist, tgt.y + (p.dy || 0), tgt.z + Math.cos(az) * p.dist);
    cam.lookAt(tgt); cam.updateMatrixWorld(true);
    setLights(az);
  }
  scene.updateMatrixWorld(true);
  r.render(scene, cam);
  return canvas.toDataURL('image/png');
};
window.ready = true;
</script></body></html>`;

const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (u === '/') { res.writeHead(200, { 'Content-Type': 'text/html' }); res.end(HTML); return; }
  let p = null, type = 'application/octet-stream';
  if (u === '/model.glb') { p = glbPath; type = 'model/gltf-binary'; }
  else if (u.startsWith('/three/')) { p = path.join(nm, u); type = 'text/javascript'; }
  if (!p || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': type }); fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1200, height: 1200 } });
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/`);
await page.waitForFunction('window.ready === true', null, { timeout: 300000 });
const info = await page.evaluate('window.info');
console.log('info', JSON.stringify(info));
const save = async (name, kind, p) => {
  const url = await page.evaluate(([k, pp]) => window.renderView(k, pp), [kind, { bg: BG, ...p }]);
  fs.writeFileSync(path.join(outDir, name), Buffer.from(url.split(',')[1], 'base64'));
  console.log('wrote', name);
};
const ymax = info.bbox[1][1];
const THREE_DEG = d => d * Math.PI / 180;
if (modes.includes('turn')) {
  for (const az of [0, 35, 90, 180]) await save(`turn_${az}.png`, 'view', { w: 600, h: 1100, az, fov: 22, dist: 5.2, target: [0, ymax / 2, 0] });
}
if (modes.includes('fit')) {   // frame the bounding box (any GLB, e.g. the photo bust)
  const [mn, mx] = info.bbox; const cy = (mn[1] + mx[1]) / 2, hgt = mx[1] - mn[1];
  for (const az of [0, 35, 90, 180]) await save(`fit_${az}.png`, 'view', { w: 800, h: 800, az, fov: 22, dist: hgt * 2.9, target: [(mn[0] + mx[0]) / 2, cy, (mn[2] + mx[2]) / 2] });
}
if (modes.includes('head')) {
  for (const az of [0, 35, 90, 180]) await save(`head_${az}.png`, 'view', { w: 800, h: 800, az, fov: 18, dist: 1.25, target: [0, ymax - 0.14, 0.01] });
}
if (modes.includes('photo') && camJson !== 'null') await save('photo_cam.png', 'photo', { w: SIZE, h: SIZE });
if (modes.includes('photolit') && camJson !== 'null') {   // same camera, the default (directional) look lighting
  await save('photo_cam_lit.png', 'photo', { w: SIZE, h: SIZE, hemi: 1.1, key: 1.9 });
}
if (modes.includes('headflat')) {   // head views under the flat photo-booth light (for the identity scorer)
  for (const az of [0, 20, 35, 50, 90]) await save(`headflat_${az}.png`, 'view', { w: 800, h: 800, az, fov: 18, dist: 1.25, target: [0, ymax - 0.14, 0.01], flat: true });
}
if (modes.includes('views')) {   // arbitrary close-ups for review: --views FILE.json, [{name, az, el, fov, dist, target, flat, w, h}]
  // target: [x, y, z] in metres, or [dx, dy, dz] relative to the head centre when rel: true
  const views = JSON.parse(fs.readFileSync(opt('--views'), 'utf8'));
  const head = [0, ymax - 0.14, 0.01];
  for (const v of views) {
    const tg = v.rel ? v.target.map((x, i) => x + head[i]) : v.target;
    const el = THREE_DEG(v.el || 0);
    await save(`${v.name}.png`, 'view', { w: v.w || 800, h: v.h || 800, az: v.az, fov: v.fov || 18, dist: (v.dist || 1.25) * Math.cos(el),
      dy: (v.dist || 1.25) * Math.sin(el), target: tg, flat: !!v.flat });
  }
}
if (modes.includes('pose')) {
  await page.evaluate('window.testPose()');
  for (const az of [0, 35]) await save(`pose_${az}.png`, 'view', { w: 600, h: 1100, az, fov: 22, dist: 5.2, target: [0, ymax / 2, 0] });
  await save('pose_head.png', 'view', { w: 800, h: 800, az: 20, fov: 18, dist: 1.3, target: [0, ymax - 0.15, 0.02] });
}
await browser.close(); server.close();
