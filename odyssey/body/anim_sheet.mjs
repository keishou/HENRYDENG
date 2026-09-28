// Contact sheet of animation clips of a skinned GLB, played through three.js' AnimationMixer in headless
// Chromium (software WebGL) -- i.e. exactly what the film renderer will see.
//   node odyssey/body/anim_sheet.mjs model.glb spec.json out.png
// spec = {"tile":[w,h], "rows":[{"clip":"walk", "times":[0,0.5,...], "view":{"az":30,"dist":4.2,"h":1.0,
//          "look":"root"|"<bone name>", "lookY":0.95, "fov":28}, "move":[0,0,0.8]}], "bg":"#d9d6d0"}
// "move" (m/s) translates the whole model with time (to preview in-place loops travelling).
// The floor carries a 25 cm grid fixed in the world, so sliding feet show against it.
// Prints JSON: per tile the root position, the lowest skinned vertex y and the missing tracks, if any.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const film = path.resolve(here, '../film');
const { chromium } = await import(path.join(film, 'node_modules/playwright-core/index.mjs'));
const [glbPath, specPath, outPng] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const [TW, TH] = spec.tile || [300, 480];
const ncol = Math.max(...spec.rows.map(r => r.times.length));
const W = TW * ncol, H = TH * spec.rows.length;
const HTML = `<!doctype html><html><body style="margin:0;background:#000">
<canvas id="c" width="${W}" height="${H}"></canvas>
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const spec = await (await fetch('/spec.json')).json();
const r = new THREE.WebGLRenderer({ canvas: document.getElementById('c'), antialias: true, preserveDrawingBuffer: true });
r.outputColorSpace = THREE.SRGBColorSpace; r.setScissorTest(true);
r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = 1.0;
r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
const bg = new THREE.Color(spec.bg || '#d9d6d0');
scene.add(new THREE.HemisphereLight(0xf4f1ec, 0x5a5550, 1.4));
const key = new THREE.DirectionalLight(0xfff4e8, 2.4); key.position.set(-2.5, 5, 4);
key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
Object.assign(key.shadow.camera, { left: -2, right: 2, top: 2, bottom: -2, near: 0.5, far: 20 });
scene.add(key); scene.add(key.target);
const rim = new THREE.DirectionalLight(0xe8f0ff, 1.2); rim.position.set(3, 3, -4); scene.add(rim);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color: 0xbdb8b0, roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
const grid = new THREE.GridHelper(60, 240, 0x8a857d, 0xa29d95); grid.position.y = 0.001; scene.add(grid);
const gltf = await new GLTFLoader().loadAsync('/model.glb');
const model = gltf.scene; scene.add(model);
model.traverse(o => { if (o.isMesh) { o.castShadow = true; o.frustumCulled = false; } });
const bones = {}; model.traverse(o => { if (o.isBone) bones[o.name] = o; });
const skinned = []; model.traverse(o => { if (o.isSkinnedMesh) skinned.push(o); });
const mixer = new THREE.AnimationMixer(model);
const clips = Object.fromEntries(gltf.animations.map(c => [c.name, c]));
const out = { clips: gltf.animations.map(c => ({ name: c.name, duration: +c.duration.toFixed(3), tracks: c.tracks.length })), tiles: [] };
const cam = new THREE.PerspectiveCamera(28, ${TW} / ${TH}, 0.05, 200);
const san = n => THREE.PropertyBinding.sanitizeNodeName(n);
const v = new THREE.Vector3(), tmp = new THREE.Vector3();
function lowestY(mesh) {   // lowest skinned vertex (sampled)
  const pos = mesh.geometry.attributes.position; let lo = 1e9;
  const step = Math.max(1, Math.floor(pos.count / 4000));
  for (let i = 0; i < pos.count; i += step) { v.fromBufferAttribute(pos, i); mesh.applyBoneTransform(i, v); v.applyMatrix4(mesh.matrixWorld); lo = Math.min(lo, v.y); }
  return lo;
}
spec.rows.forEach((row, ri) => {
  const clip = clips[row.clip];
  mixer.stopAllAction();
  const act = mixer.clipAction(clip); act.reset(); act.play();
  row.times.forEach((t, ci) => {
    act.time = Math.min(t, clip.duration); mixer.update(0);
    const mv = row.move || [0, 0, 0];
    model.position.set(mv[0] * t, mv[1] * t, mv[2] * t);
    model.updateMatrixWorld(true);
    const vw = row.view || {};
    const lookBone = bones[san(vw.look || 'root')] || bones['root'];
    lookBone.getWorldPosition(tmp);
    const tgt = new THREE.Vector3(tmp.x, vw.lookY !== undefined ? vw.lookY : tmp.y, tmp.z);
    if (vw.fixed) tgt.set(...vw.fixed);
    const az = (vw.az || 0) * Math.PI / 180, dist = vw.dist || 4.2;
    cam.fov = vw.fov || 28; cam.aspect = ${TW} / ${TH}; cam.updateProjectionMatrix();
    cam.position.set(tgt.x + Math.sin(az) * dist, (vw.h !== undefined ? vw.h : 1.0) + (vw.relH ? tgt.y : 0), tgt.z + Math.cos(az) * dist);
    cam.lookAt(tgt);
    key.position.set(tgt.x - 2.5, 5, tgt.z + 4); key.target.position.set(tgt.x, 0, tgt.z); key.target.updateMatrixWorld();
    const lo = row.measure === false ? null : Math.min(...skinned.filter(m => m.name.startsWith('shoes') || m.name.startsWith('skin') || m.name.startsWith('outfit')).map(lowestY));
    const rp = bones['root'].getWorldPosition(new THREE.Vector3());
    out.tiles.push({ clip: row.clip, t, root: rp.toArray().map(x => +x.toFixed(3)), lowest: lo === null ? null : +lo.toFixed(4) });
    r.setViewport(ci * ${TW}, ${H} - (ri + 1) * ${TH}, ${TW}, ${TH}); r.setScissor(ci * ${TW}, ${H} - (ri + 1) * ${TH}, ${TW}, ${TH});
    r.setClearColor(bg); r.render(scene, cam);
  });
});
window.out = out; window.done = true;
</script></body></html>`;
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  let p = null, type = 'application/octet-stream';
  if (u === '/') { res.writeHead(200, { 'Content-Type': 'text/html' }); res.end(HTML); return; }
  if (u === '/model.glb') { p = path.resolve(glbPath); type = 'model/gltf-binary'; }
  else if (u === '/spec.json') { p = path.resolve(specPath); type = 'application/json'; }
  else if (u.startsWith('/three/')) { p = path.join(film, 'node_modules', u); type = 'text/javascript'; }
  if (!p || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': type }); fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on('pageerror', e => console.log('[err]', e.message));
page.on('console', m => { if (m.type() === 'error') console.log('[console]', m.text()); });
await page.goto(`http://127.0.0.1:${server.address().port}/`);
await page.waitForFunction('window.done === true', null, { timeout: 900000 });
console.log(JSON.stringify(await page.evaluate('window.out')));
const dataUrl = await page.evaluate(() => document.getElementById('c').toDataURL('image/png'));
fs.writeFileSync(outPng, Buffer.from(dataUrl.split(',')[1], 'base64'));
await browser.close(); server.close();
