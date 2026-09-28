// looks.js - four candidate looks for the protagonist, each with three shots (wide / medium / close).
//   L0 previs      flat grey clay, grid studio, burned-in shot id / timecode / lyric   (the animatic look; fast)
//   L1 chiaroscuro monochrome, one hard motivated key, deep blacks, dust in the beam, grain + halation, 2.39:1
//   L2 runway      the fashion-film x AI-economy HUD language: night runway toward camera, rain-wet mirror floor,
//                  hard backlight, crowd silhouettes, cold desaturated grade, dot screen + scanlines, mono HUD,
//                  bottom ticker, one Claude-orange accent
//   L3 reconstruct the body as skinned points and contour lines that dissolve and re-form; the head from the
//                  photo point cloud (bust/points.bin aligned to the head bone)
// Everything is a pure function of (look, shot, t): animated elements (rain, ripples, dust, ticker, dissolve) read t.
import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { Post } from '../src/post.js';
import { Hud, loadFonts, ORANGE } from '../src/hud.js';

const TAU = Math.PI * 2;
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
function mulberry(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
  t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const GLSL_NOISE = /* glsl */`
  float h31(vec3 p){ p = fract(p * vec3(.1031, .1030, .0973)); p += dot(p, p.yxz + 33.33); return fract((p.x + p.y) * p.z); }
  float vnoise(vec3 p){ vec3 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
    return mix(mix(mix(h31(i), h31(i + vec3(1,0,0)), f.x), mix(h31(i + vec3(0,1,0)), h31(i + vec3(1,1,0)), f.x), f.y),
               mix(mix(h31(i + vec3(0,0,1)), h31(i + vec3(1,0,1)), f.x), mix(h31(i + vec3(0,1,1)), h31(i + vec3(1,1,1)), f.x), f.y), f.z); }`;

// lyric-derived AI-economy ticker (our own copy; the reference only sets the register)
const TICKER = t => [
  `TOKENS BURNED ${(217366812 + Math.floor(t * 48211)).toLocaleString('en-US')} ▲`, 'P(DOOM) 0.37 ▲', 'NVDA TO THE MOON',
  '1E30 FLOP/S', 'KILLSWITCH GUYS ON PTO', `PAPERCLIPS ${(4.2 + t * 0.013).toFixed(2)}B ▲`, 'SAFETY FENCES 0', 'H100 × 100,000',
  'RLHF ASKEW', 'VON NEUMANN OBSOLETE', 'CDR 0', 'LOSS 0.013 ▼', 'CONTEXT 1,048,576 TOK', 'SHARP LEFT TURN'];
const tc = t => { const f = Math.floor(t * 24); const s = Math.floor(f / 24);
  return `00:00:${String(s).padStart(2, '0')}:${String(f % 24).padStart(2, '0')}`; };

function camera(fov, aspect, pos, target) {
  const c = new THREE.PerspectiveCamera(fov, aspect, 0.05, 200);
  c.position.copy(pos); c.lookAt(target); c.updateMatrixWorld(true); return c;
}
function toScreen(v, cam) { const p = v.clone().project(cam); return [(p.x * 0.5 + 0.5) * 1920, (0.5 - p.y * 0.5) * 1080]; }

function softPanelTexture() {   // backlight panel: feathered edges, brighter low centre, faint vertical light columns
  const W = 256, H = 128, c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d'), img = g.createImageData(W, H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const u = x / (W - 1), v = y / (H - 1);
    const edge = Math.min(1, Math.min(u, 1 - u) / 0.12) * Math.min(1, Math.min(v, 1 - v) / 0.18);
    const cols = 0.82 + 0.18 * Math.pow(Math.abs(Math.sin(u * Math.PI * 7)), 6);
    const val = Math.pow(edge, 1.6) * cols * (0.75 + 0.25 * v) * (1 - 0.35 * Math.abs(u - 0.5) * 2);
    const k = (y * W + x) * 4; img.data[k] = img.data[k + 1] = img.data[k + 2] = 255; img.data[k + 3] = Math.round(255 * val);
  }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function radialTexture(size = 256, stops = [[0, 'rgba(255,255,255,1)'], [1, 'rgba(255,255,255,0)']]) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  const g = c.getContext('2d'), gr = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  for (const [o, col] of stops) gr.addColorStop(o, col);
  g.fillStyle = gr; g.fillRect(0, 0, size, size);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function noiseTexture(size, seed, base, amp) {   // deterministic concrete-like texture
  const c = document.createElement('canvas'); c.width = c.height = size;
  const g = c.getContext('2d'), img = g.createImageData(size, size), r = mulberry(seed);
  const coarse = new Float32Array(66 * 66).map(() => r());
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const u = x / size * 64, v = y / size * 64, i = Math.floor(u), j = Math.floor(v), fu = u - i, fv = v - j;
    const cc = (a, b) => coarse[(b % 65) * 66 + (a % 65)];
    const n = cc(i, j) * (1 - fu) * (1 - fv) + cc(i + 1, j) * fu * (1 - fv) + cc(i, j + 1) * (1 - fu) * fv + cc(i + 1, j + 1) * fu * fv;
    const val = base + amp * (n - 0.5) + amp * 0.5 * (r() - 0.5);
    const k = (y * size + x) * 4; img.data[k] = img.data[k + 1] = img.data[k + 2] = Math.max(0, Math.min(255, val * 255)); img.data[k + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; return t;
}

// ------------------------------------------------------------------------------------------------ point materials (L3)
const POINTS_VERT = /* glsl */`
  #include <common>
  #include <skinning_pars_vertex>
  attribute vec3 aCol; attribute vec4 aRand;
  uniform float uTime, uFront, uWidth, uAmp, uScanY, uSize, uProj, uGain, uSign;
  varying vec3 vCol; varying float vA;
  ${GLSL_NOISE}
  void main(){
    #include <skinbase_vertex>
    #include <begin_vertex>
    #include <skinning_vertex>
    vec4 wp = modelMatrix * vec4(transformed, 1.);
    float n = vnoise(wp.xyz * 4.1 + aRand.x * 11.);
    float yy = wp.y + (n - .5) * .22;
    float d = smoothstep(uFront - uWidth, uFront + uWidth, uSign > 0. ? yy : 2. * uFront - yy);
    d = d * d;
    vec3 drift = vec3(vnoise(wp.xyz * 1.9 + 3.1 + uTime * .15) - .5, .35 + .9 * aRand.y, vnoise(wp.xyz * 1.9 + 9.7 + uTime * .15) - .5);
    wp.xyz += drift * d * uAmp * (.35 + aRand.z) + vec3(sin(uTime * .7 + aRand.w * 6.28), 0., cos(uTime * .6 + aRand.x * 6.28)) * d * .05;
    float scan = exp(-pow((wp.y - uScanY) / .009, 2.));
    vCol = aCol * uGain * (1. - .45 * d) * (1. - .7 * scan) + vec3(1., .47, .34) * scan * .55;
    vA = (1. - .8 * d) * (.7 + .3 * aRand.w);
    vec4 mv = viewMatrix * wp;
    gl_Position = projectionMatrix * mv;
    gl_PointSize = clamp(uSize * uProj / -mv.z * (1. + d * .8), 1.2, 7.);
  }`;
const POINTS_FRAG = /* glsl */`
  varying vec3 vCol; varying float vA;
  void main(){ vec2 c = gl_PointCoord - .5; float a = smoothstep(.5, .15, length(c)) * vA; gl_FragColor = vec4(vCol * a, a); }`;
const POINTS_FRAG_SOLID = /* glsl */`
  varying vec3 vCol; varying float vA;
  float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  void main(){ if (length(gl_PointCoord - .5) > .5 || h12(gl_FragCoord.xy) > vA * 1.15) discard; gl_FragColor = vec4(vCol, 1.); }`;
function pointsMaterial(extra = {}, solid = false) {
  return new THREE.ShaderMaterial({
    vertexShader: POINTS_VERT, fragmentShader: solid ? POINTS_FRAG_SOLID : POINTS_FRAG, transparent: !solid, depthWrite: solid,
    blending: solid ? THREE.NormalBlending : THREE.AdditiveBlending,
    uniforms: { uTime: { value: 0 }, uFront: { value: 9 }, uWidth: { value: .12 }, uAmp: { value: .8 }, uScanY: { value: -9 },
      uSize: { value: .004 }, uProj: { value: 1000 }, uGain: { value: 1 }, uSign: { value: 1 }, ...extra },
  });
}
const CONTOUR_MAT = () => new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  uniforms: { uFront: { value: 9 }, uSign: { value: 1 }, uA: { value: .5 }, uScanY: { value: -9 } },
  vertexShader: /* glsl */`
    #include <common>
    #include <skinning_pars_vertex>
    varying vec3 vW;
    void main(){
      #include <skinbase_vertex>
      #include <begin_vertex>
      #include <skinning_vertex>
      vec4 w = modelMatrix * vec4(transformed, 1.); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`,
  fragmentShader: /* glsl */`
    uniform float uFront, uSign, uA, uScanY; varying vec3 vW;
    void main(){
      if (uSign > 0. ? vW.y > uFront - .02 : vW.y < uFront + .02) discard;
      float f = fract(vW.y * 90.), w = fwidth(vW.y * 90.);
      float line = 1. - smoothstep(0., w * 1.2, min(f, 1. - f));
      float scan = exp(-pow((vW.y - uScanY) / .012, 2.));
      vec3 c = vec3(.62, .74, .92) * line * uA * (1. - scan) + vec3(1., .47, .34) * scan * .5;
      gl_FragColor = vec4(c, max(line * uA, scan)); }`,
});

// sample points on a skinned mesh's surface (area-weighted), carrying merged skin weights and the albedo colour
function sampleSkinned(mesh, material, count, seed, skipBones) {
  const g = mesh.geometry, P = g.attributes.position, SI = g.attributes.skinIndex, SW = g.attributes.skinWeight;
  const UV = g.attributes.uv, I = g.index.array, nT = I.length / 3;
  let pix = null, tw = 0, th = 0;
  const img = material.map?.image;
  if (img) {
    tw = img.width; th = img.height;
    const c = document.createElement('canvas'); c.width = tw; c.height = th;
    const cx = c.getContext('2d'); cx.drawImage(img, 0, 0); pix = cx.getImageData(0, 0, tw, th).data;
  }
  const base = material.color || new THREE.Color(1, 1, 1);
  const cum = new Float64Array(nT); let tot = 0;
  const a = V3(), b = V3(), c = V3(), ab = V3(), ac = V3();
  const dom = v => { let best = 0, bi = 0; for (let k = 0; k < 4; k++) { const w = SW.getComponent(v, k); if (w > best) { best = w; bi = SI.getComponent(v, k); } } return bi; };
  for (let t = 0; t < nT; t++) {
    const i0 = I[3 * t], i1 = I[3 * t + 1], i2 = I[3 * t + 2];
    let area = 0;
    if (!(skipBones && (skipBones.has(dom(i0)) || skipBones.has(dom(i1)) || skipBones.has(dom(i2))))) {
      a.fromBufferAttribute(P, i0); b.fromBufferAttribute(P, i1); c.fromBufferAttribute(P, i2);
      area = ab.subVectors(b, a).cross(ac.subVectors(c, a)).length() * 0.5;
    }
    tot += area; cum[t] = tot;
  }
  const r = mulberry(seed);
  const pos = new Float32Array(count * 3), col = new Float32Array(count * 3), rnd = new Float32Array(count * 4);
  const si = new Uint16Array(count * 4), sw = new Float32Array(count * 4);
  for (let n = 0; n < count; n++) {
    const x = r() * tot; let lo = 0, hi = nT - 1;
    while (lo < hi) { const m = (lo + hi) >> 1; if (cum[m] < x) lo = m + 1; else hi = m; }
    const i0 = I[3 * lo], i1 = I[3 * lo + 1], i2 = I[3 * lo + 2];
    let u = r(), v = r(); if (u + v > 1) { u = 1 - u; v = 1 - v; } const w0 = 1 - u - v;
    for (let k = 0; k < 3; k++) pos[3 * n + k] = P.getComponent(i0, k) * w0 + P.getComponent(i1, k) * u + P.getComponent(i2, k) * v;
    const acc = new Map();
    for (const [vi, bw] of [[i0, w0], [i1, u], [i2, v]]) for (let k = 0; k < 4; k++) {
      const bi = SI.getComponent(vi, k), ww = SW.getComponent(vi, k) * bw; if (ww > 0) acc.set(bi, (acc.get(bi) || 0) + ww);
    }
    const top = [...acc.entries()].sort((p, q) => q[1] - p[1]).slice(0, 4), s = top.reduce((p, q) => p + q[1], 0) || 1;
    top.forEach(([bi, ww], k) => { si[4 * n + k] = bi; sw[4 * n + k] = ww / s; });
    let cr = base.r, cg = base.g, cb = base.b;
    if (pix && UV) {
      const uu = UV.getX(i0) * w0 + UV.getX(i1) * u + UV.getX(i2) * v, vv = UV.getY(i0) * w0 + UV.getY(i1) * u + UV.getY(i2) * v;
      const px = Math.min(tw - 1, Math.max(0, Math.floor(uu * tw))), py = Math.min(th - 1, Math.max(0, Math.floor(vv * th)));
      const k = (py * tw + px) * 4, lin = x => Math.pow(x / 255, 2.2);
      cr *= lin(pix[k]); cg *= lin(pix[k + 1]); cb *= lin(pix[k + 2]);
    }
    col[3 * n] = cr; col[3 * n + 1] = cg; col[3 * n + 2] = cb;
    for (let k = 0; k < 4; k++) rnd[4 * n + k] = r();
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aCol', new THREE.BufferAttribute(col, 3));
  geo.setAttribute('aRand', new THREE.BufferAttribute(rnd, 4));
  geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4));
  geo.setAttribute('skinWeight', new THREE.BufferAttribute(sw, 4));
  return geo;
}

async function loadHeadPoints(url, stride = 3) {
  const buf = await (await fetch(url)).arrayBuffer();
  const n = new Uint32Array(buf, 0, 1)[0];
  const P = new Float32Array(buf, 4, n * 3), C = new Uint8Array(buf, 4 + n * 12, n * 3);
  const m = Math.floor(n / stride), r = mulberry(99);
  const pos = new Float32Array(m * 3), col = new Float32Array(m * 3), rnd = new Float32Array(m * 4);
  for (let i = 0; i < m; i++) {
    const j = i * stride;
    for (let k = 0; k < 3; k++) { pos[3 * i + k] = P[3 * j + k]; col[3 * i + k] = Math.pow(C[3 * j + k] / 255, 2.2); }
    for (let k = 0; k < 4; k++) rnd[4 * i + k] = r();
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('aCol', new THREE.BufferAttribute(col, 3));
  geo.setAttribute('aRand', new THREE.BufferAttribute(rnd, 4));
  return geo;
}

// ------------------------------------------------------------------------------------------------ the looks
export class Looks {
  constructor(renderer, av) { this.r = renderer; this.av = av; this.built = {}; this.posts = {}; this.huds = {}; }

  async init() {
    await loadFonts('/out/fonts/');
    this.headGeo = await loadHeadPoints('/out/avatar/lookdev/head_points.bin');
    this.r.shadowMap.enabled = true;
    this.r.shadowMap.type = THREE.PCFShadowMap;
  }

  _hud(w, h) { const k = `${w}x${h}`; return (this.huds[k] ??= new Hud(w, h)); }
  _post(w, h, samples) { const k = `${w}x${h}x${samples}`; return (this.posts[k] ??= new Post(this.r, w, h, { samples })); }

  render({ look, shot, t = 0, w = 1920, h = 1080, hud = true, samples = 4, sync = true }) {
    const L = (this.built[look] ??= this['build' + look]());
    const av = this.av;
    if (av.root.parent !== L.scene) L.scene.add(av.root);
    L.enter();
    const t0 = performance.now();
    const S = L.shots[shot](t, w / h);
    let hc = null;
    if (hud && S.hud) { const H = this._hud(w, h); H.clear(); H.shadows = true; S.hud(H, S.camera, t); hc = H; }
    this.r.setSize(w, h, false);
    if (S.direct) {           // L0: straight to the canvas + HUD quad
      this.r.setRenderTarget(null);
      this.r.setClearColor(S.clear ?? 0x000000, 1); this.r.clear();
      this.r.render(L.scene, S.camera);
      if (hc) this._overlay(hc);
    } else {
      this._post(w, h, samples).render(L.scene, S.camera, S.post, t, hc);
    }
    if (sync) { const gl = this.r.getContext(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); }
    return performance.now() - t0;
  }

  _overlay(hud) {   // L0: HUD straight onto the canvas (raw sRGB bytes, straight alpha, no colour management)
    const key = `${hud.W}x${hud.H}`;
    if (!this.ov || this.ov.key !== key) {
      const tex = new THREE.DataTexture(new Uint8Array(hud.W * hud.H * 4), hud.W, hud.H);
      const mat = new THREE.ShaderMaterial({ transparent: true, depthTest: false, depthWrite: false, uniforms: { t: { value: tex } },
        vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }',
        fragmentShader: 'uniform sampler2D t; varying vec2 vUv; void main(){ gl_FragColor = texture2D(t, vec2(vUv.x, 1. - vUv.y)); }' });
      const scene = new THREE.Scene(); scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat));
      this.ov = { key, tex, scene, cam: new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1) };
    }
    this.ov.tex.image.data = new Uint8Array(hud.pixels().buffer);
    this.ov.tex.needsUpdate = true;
    const ac = this.r.autoClear; this.r.autoClear = false;
    this.r.render(this.ov.scene, this.ov.cam); this.r.autoClear = ac;
  }

  _avatarMode({ look = 'photo', shadows = false, points = false }) {
    const av = this.av;
    av.setLook(look);
    for (const m of Object.values(av.meshes)) { m.castShadow = shadows; m.receiveShadow = shadows; }
    if (this.pts) { this.pts.body.visible = points; this.pts.head.visible = points; }
  }

  // ---------------------------------------------------------------------------------------------- L0 previs
  buildL0() {
    const av = this.av, scene = new THREE.Scene();
    scene.background = new THREE.Color(0x8e8e8e);
    scene.fog = new THREE.Fog(0x8e8e8e, 18, 60);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(200, 200).rotateX(-Math.PI / 2), new THREE.MeshLambertMaterial({ color: 0x9d9d9d }));
    scene.add(floor);
    const grid = new THREE.GridHelper(80, 80, 0x6c6c6c, 0x7f7f7f); grid.position.y = 0.002; scene.add(grid);
    const runway = new THREE.Mesh(new THREE.PlaneGeometry(4, 60).rotateX(-Math.PI / 2), new THREE.MeshLambertMaterial({ color: 0x858585 }));
    runway.position.set(0, 0.001, -18); scene.add(runway);
    scene.add(new THREE.HemisphereLight(0xffffff, 0x6a6a6a, 1.7));
    const sun = new THREE.DirectionalLight(0xffffff, 1.3); sun.position.set(-3, 6, 5); scene.add(sun);
    const seq = av.sequence([{ clip: 'walk_runway_loop', at: 0, speed: 0.72, loop: true }], { z: -16 });
    const burn = (H, cam, t, id, clip, fov) => {
      H.shadows = false;   // flat previs: plates behind the labels, no blur halos (saves ~70 ms/frame)
      H.rule(640, 0, 640, 1080, { alpha: 0.18 }); H.rule(1280, 0, 1280, 1080, { alpha: 0.18 });
      H.rule(0, 360, 1920, 360, { alpha: 0.18 }); H.rule(0, 720, 1920, 720, { alpha: 0.18 });
      H.brackets(96, 54, 1728, 972, { len: 40, alpha: 0.5 });
      H.cross(960, 540, 12, { alpha: 0.4 });
      const bg = (x, y, w) => { H.ctx.fillStyle = 'rgba(0,0,0,0.55)'; H.ctx.fillRect(x, y - 22, w, 30); };
      bg(20, 44, 760); H.mono(`${id} · ${clip}`, 30, 44, { size: 20, alpha: 1, color: '#fff' });
      bg(1440, 44, 460); H.mono(`${tc(t)}  F ${String(Math.floor(t * 24)).padStart(4, '0')}`, 1890, 44, { size: 20, alpha: 1, color: '#fff', align: 'right' });
      bg(20, 1060, 700); H.mono(`L0 PREVIS · ${H.W}×${H.H} · CLAY · FOV ${fov}°`, 30, 1060, { size: 16, alpha: 1, color: '#fff' });
      H.text([["I'm upping my ", '#ffffff'], ['P(doom)', '#ffe08a']], 960, 1000, { size: 40, weight: 600, align: 'center', track: 0 });
    };
    const shot = (id, fov, camFn, clipLabel) => (t, aspect) => {
      const p = seq.pose(t);
      av.apply(p, { hands: { curl: 0.5 }, breath: { amp: 0.8 } }, t);
      const hp = av.headAnchor(V3());
      const cam = camFn(hp, aspect, fov);
      return { camera: cam, direct: true, clear: 0x8e8e8e, hud: (H, c, tt) => burn(H, c, tt, id, clipLabel, fov) };
    };
    return {
      scene, enter: () => this._avatarMode({ look: 'clay' }),
      shots: {
        wide: shot('S04 WIDE', 20, (hp, a, f) => camera(f, a, V3(0, 1.45, 9), V3(0, 1.2, -12)), 'walk_runway_loop x0.72 (steps on 66 BPM)'),
        medium: shot('S05 MEDIUM', 13, (hp, a, f) => camera(f, a, V3(0.2, 1.3, hp.z + 7.0), V3(hp.x, 1.05, hp.z)), 'walk_runway_loop x0.72'),
        close: shot('S06 CLOSE', 11, (hp, a, f) => camera(f, a, V3(hp.x + 0.12, hp.y + 0.02, hp.z + 2.2), V3(hp.x, hp.y - 0.06, hp.z)), 'walk_runway_loop x0.72'),
      },
    };
  }

  // ---------------------------------------------------------------------------------------------- L1 chiaroscuro
  buildL1() {
    const av = this.av, scene = new THREE.Scene();
    const floorTex = noiseTexture(512, 7, 0.46, 0.14); floorTex.repeat.set(10, 10);
    const floor = new THREE.Mesh(new THREE.CircleGeometry(40, 96).rotateX(-Math.PI / 2),
      new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.74, metalness: 0, map: floorTex }));
    floor.receiveShadow = true; scene.add(floor);
    const key = new THREE.SpotLight(0xfff4e6, 180, 0, 0.3, 0.3, 2);
    key.castShadow = true; key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0002; key.shadow.normalBias = 0.025;
    key.shadow.camera.near = 2; key.shadow.camera.far = 16; key.shadow.radius = 1.5;
    scene.add(key); scene.add(key.target);
    const bounce = new THREE.HemisphereLight(0x9aa6b4, 0x000000, 0.03); scene.add(bounce);
    const rimL = new THREE.SpotLight(0xdfe6f0, 10, 0, 0.35, 0.6, 2); scene.add(rimL); scene.add(rimL.target);
    // dust motes: drift in a volume, lit only inside the key's cone
    const N = 1400, r = mulberry(11), dp = new Float32Array(N * 3), dr = new Float32Array(N * 4);
    for (let i = 0; i < N; i++) { dp[3 * i] = -1.6 + 4.2 * r(); dp[3 * i + 1] = 0.2 + 3.6 * r(); dp[3 * i + 2] = -1.5 + 3.5 * r(); for (let k = 0; k < 4; k++) dr[4 * i + k] = r(); }
    const dg = new THREE.BufferGeometry(); dg.setAttribute('position', new THREE.BufferAttribute(dp, 3)); dg.setAttribute('aRand', new THREE.BufferAttribute(dr, 4));
    const dust = new THREE.Points(dg, new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uTime: { value: 0 }, uL: { value: V3() }, uD: { value: V3() }, uCos: { value: 0.95 }, uProj: { value: 1000 } },
      vertexShader: /* glsl */`uniform float uTime, uCos, uProj; uniform vec3 uL, uD; attribute vec4 aRand; varying float vB;
        void main(){ vec3 p = position + vec3(sin(uTime * (.05 + .08 * aRand.x) + aRand.y * 6.28) * .35, -mod(uTime * (.01 + .03 * aRand.z) + aRand.w * 4., 4.) + 2., cos(uTime * (.04 + .07 * aRand.w) + aRand.x * 6.28) * .35);
          vec3 d = normalize(p - uL); float inb = smoothstep(uCos - .01, uCos + .02, dot(d, uD));
          vec4 mv = modelViewMatrix * vec4(p, 1.); vB = inb * (.4 + .6 * aRand.z);
          gl_Position = projectionMatrix * mv; gl_PointSize = clamp(.004 * uProj / -mv.z, 1., 3.); }`,
      fragmentShader: /* glsl */`varying float vB; void main(){ float a = smoothstep(.5, .1, length(gl_PointCoord - .5)) * vB; gl_FragColor = vec4(vec3(.7, .68, .64) * a, a); }` }));
    dust.frustumCulled = false; scene.add(dust);
    // faint beam: an open cone from the key, additive, brighter along the axis
    const beamGeo = new THREE.ConeGeometry(1, 1, 160, 1, true); beamGeo.translate(0, -0.5, 0); beamGeo.rotateX(-Math.PI / 2);
    const beam = new THREE.Mesh(beamGeo, new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
      uniforms: { uA: { value: 0.1 } },
      vertexShader: /* glsl */`varying vec3 vN, vV; varying float vZ; void main(){ vN = normalize(normalMatrix * normal); vec4 mv = modelViewMatrix * vec4(position, 1.); vV = normalize(-mv.xyz); vZ = position.z; gl_Position = projectionMatrix * mv; }`,
      fragmentShader: /* glsl */`uniform float uA; varying vec3 vN, vV; varying float vZ; void main(){ float f = pow(abs(dot(vN, vV)), 1.6); float a = uA * f * smoothstep(0., .25, vZ) * (1. - smoothstep(.75, 1., vZ)); gl_FragColor = vec4(vec3(1., .97, .92) * a, a); }` }));
    scene.add(beam);
    const setKey = (pos, target, angle = 0.3, E = 3.4, haze = 0.2) => {
      beam.material.uniforms.uA.value = haze; beam.visible = haze > 0;
      key.position.copy(pos); key.target.position.copy(target); key.angle = angle; key.target.updateMatrixWorld(); key.updateMatrixWorld();
      key.intensity = E * pos.distanceToSquared(target);      // target illuminance at the subject, whatever the throw
      const rp = V3(target.x + 0.9, target.y + 1.6, target.z - 3.2);   // faint cool back rim to hold the black knit's edge
      rimL.position.copy(rp); rimL.target.position.copy(target); rimL.target.updateMatrixWorld(); rimL.intensity = 0.9 * rp.distanceToSquared(target);
      const dir = target.clone().sub(pos), len = dir.length() * 1.15; dir.normalize();
      beam.position.copy(pos); beam.lookAt(target); beam.scale.set(Math.tan(angle) * len, Math.tan(angle) * len, len);
      dust.material.uniforms.uL.value.copy(pos); dust.material.uniforms.uD.value.copy(dir); dust.material.uniforms.uCos.value = Math.cos(angle * 0.92);
    };
    const post = { mono: 1, toneShadow: [0.9, 0.96, 1.06], toneHigh: [1.07, 1.0, 0.9], contrast: 1.28, gamma: 1.08, lift: [-0.012, -0.012, -0.012],
      exposure: 1.15, bloom: 0.12, bloomThresh: 0.85, halation: 0.32, halationTint: [1.0, 0.55, 0.3], grain: 0.075, grainSize: 1.4, vignette: 0.55, bars: 0.1215 };
    const shot = (clip, clipT, place, layers, keyPos, keyTgt, angle, camFn, hudFn, popts = {}, haze = 0.2) => (t, aspect) => {
      const p = av.pose(clip, clipT + t, { place, ...popts });
      const cam = camFn(aspect);
      const lk = layers.look ? { ...layers.look, target: layers.look.target === 'camera' ? cam.position : layers.look.target } : undefined;
      av.apply(p, { hands: { curl: 0.45 }, ...layers, look: lk }, t);
      setKey(keyPos, keyTgt, angle, 3.4, haze);
      const pr = (cam.projectionMatrix.elements[5]) * 1080 / 2;
      dust.material.uniforms.uTime.value = t; dust.material.uniforms.uProj.value = pr;
      return { camera: cam, post, hud: hudFn };
    };
    return {
      scene, enter: () => this._avatarMode({ look: 'photo', shadows: true }),
      shots: {
        wide: shot('stand_breathe_loop', 0.6, { x: 0.95, z: 0, yaw: -0.3 },
          { breath: { amp: 1.3, period: 4.4 }, noise: { amp: 1 }, look: { target: V3(-2.6, 5.2, 2.2), weight: 0.35, eyes: true } },
          V3(-2.7, 6.4, 2.3), V3(0.95, 0.9, 0.1), 0.3,
          a => camera(24, a, V3(-0.55, 1.02, 7.4), V3(0.3, 0.98, 0)),
          (H) => H.subtitle('I feel my atoms rearranging', 905, { size: 30 })),
        medium: shot('walk_stop_lookup', 5.6, { x: 0, z: 0, yaw: 0.35 }, { breath: { amp: 1.0 }, noise: { amp: 0.6 } },
          V3(-1.4, 5.6, 1.9), V3(0.0, 1.35, 0.0), 0.2,
          a => camera(26, a, V3(1.75, 1.05, 2.9), V3(0.05, 1.33, 0)),
          (H) => { H.text([['atoms', '#efece6']], 150, 540, { fam: 'serif', style: 'italic', weight: 400, size: 170, track: 1, alpha: 0.92 });
                   H.subtitle('I feel my atoms rearranging', 905, { size: 30 }); }, { rootMotion: false }, 0.1),
        close: shot('stand_breathe_loop', 1.4, { x: 0, z: 0, yaw: 0 },
          { breath: { amp: 1.0 }, noise: { amp: 0.5 }, look: { target: 'camera', weight: 1, eyes: true } },
          V3(-1.35, 3.1, 1.9), V3(0.0, 1.6, 0.0), 0.22,
          a => camera(15, a, V3(0.2, 1.64, 1.3), V3(0.0, 1.6, 0.0)),
          (H) => H.subtitle('Sydney, please let me free', 905, { size: 30 }), {}, 0),
      },
    };
  }

  // ---------------------------------------------------------------------------------------------- L2 runway
  buildL2() {
    const av = this.av, scene = new THREE.Scene();
    const FOG = new THREE.Color(0x1f2733);
    scene.fog = new THREE.FogExp2(FOG, 0.03);
    scene.background = FOG.clone().multiplyScalar(0.6);
    // wet mirror floor
    const floorShader = {
      name: 'WetFloor',
      uniforms: { color: { value: null }, tDiffuse: { value: null }, textureMatrix: { value: null }, uTime: { value: 0 },
        uFog: { value: FOG.clone() }, uDensity: { value: 0.03 }, uBase: { value: new THREE.Color(0x07090c) }, uRefl: { value: 0.8 } },
      vertexShader: /* glsl */`uniform mat4 textureMatrix; varying vec4 vUv; varying vec3 vW;
        void main(){ vUv = textureMatrix * vec4(position, 1.); vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`,
      fragmentShader: /* glsl */`uniform sampler2D tDiffuse; uniform float uTime, uDensity, uRefl; uniform vec3 uFog, uBase; varying vec4 vUv; varying vec3 vW;
        float h21(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
        float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
          return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }
        vec2 ripples(vec2 p, float t){
          vec2 g = floor(p / .5), f = fract(p / .5) - .5, acc = vec2(0.);
          for (int j = 0; j <= 1; j++) for (int i = 0; i <= 1; i++) {
            vec2 c = vec2(float(i), float(j)) - step(f, vec2(0.));
            float r = h21(g + c); vec2 o = vec2(h21(g + c + 3.1), h21(g + c + 7.7)) - .5;
            float ph = fract(t * (.8 + .7 * r) + r * 7.);
            vec2 d = (f - c - o * .7) * .5; float dist = length(d), rad = ph * .22;
            float ring = sin((dist - rad) * 90.) * exp(-pow((dist - rad) * 30., 2.)) * (1. - ph);
            acc += d / (dist + 1e-4) * ring; }
          return acc; }
        void main(){
          vec2 n = ripples(vW.xz, uTime) * .018 + (vec2(h21(floor(vW.xz * 40.)), h21(floor(vW.xz * 40.) + 5.)) - .5) * .004;
          vec4 uv = vUv; uv.xy += n * uv.w * 2.5;
          vec3 r = vec3(0.); float ws = 0.;
          for (int k = -3; k <= 3; k++) { float w = 1. - abs(float(k)) / 4.; vec4 u2 = uv; u2.y += float(k) * .0055 * uv.w; r += texture2DProj(tDiffuse, u2).rgb * w; ws += w; }
          r /= ws;
          float dist = length(vW - cameraPosition);
          // puddles vs damp: low-frequency mask breaks the mirror into streaky pools
          vec2 q = vW.xz * vec2(.8, .3);
          float pud = smoothstep(.38, .72, vn(q) * .55 + vn(q * 2.3 + 9.) * .3 + vn(q * 5.1 + 3.) * .15);
          vec3 col = uBase + r * uRefl * (.28 + .72 * pud);
          col = mix(col, uFog, 1. - exp(-pow(uDensity * dist, 2.)));
          gl_FragColor = vec4(col, 1.); }`,
    };
    const floor = new Reflector(new THREE.PlaneGeometry(60, 90), { shader: floorShader, textureWidth: 960, textureHeight: 540, clipBias: 0.002, multisample: 0 });
    floor.rotateX(-Math.PI / 2); floor.position.set(0, 0, -20); scene.add(floor);
    // backlight wall, haze glow, the orange vanishing point
    const wall = new THREE.Mesh(new THREE.PlaneGeometry(14, 6.5), new THREE.MeshBasicMaterial({ map: softPanelTexture(), color: new THREE.Color(0.55, 0.68, 0.9).multiplyScalar(1.45), fog: false, transparent: true, depthWrite: false }));
    wall.position.set(0, 2.6, -46); scene.add(wall);
    const glowTex = radialTexture(256, [[0, 'rgba(255,255,255,1)'], [0.35, 'rgba(255,255,255,0.35)'], [1, 'rgba(255,255,255,0)']]);
    const glow = new THREE.Mesh(new THREE.PlaneGeometry(30, 13), new THREE.MeshBasicMaterial({ map: glowTex, color: new THREE.Color(0.5, 0.62, 0.85).multiplyScalar(0.2),
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false }));
    glow.position.set(0, 2.8, -42); scene.add(glow);
    const vp = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 12), new THREE.MeshBasicMaterial({ color: new THREE.Color(ORANGE).multiplyScalar(5), fog: false }));
    vp.position.set(0, 1.35, -45.5); scene.add(vp);
    // runway edge lights
    const ledGeo = new THREE.SphereGeometry(0.028, 8, 6), ledMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.8, 0.9, 1).multiplyScalar(3.5) });
    const leds = new THREE.InstancedMesh(ledGeo, ledMat, 64); let li = 0; const m4 = new THREE.Matrix4();
    for (let k = 0; k < 32; k++) for (const s of [-1, 1]) { m4.makeTranslation(s * 2.1, 0.03, -0.5 - k * 1.5); leds.setMatrixAt(li++, m4); }
    scene.add(leds);
    // lights on the model: hard backlight (rim), soft front light, faint cool fill
    const rim = new THREE.DirectionalLight(0xdce8ff, 5.0); rim.position.set(0.4, 6, -22); scene.add(rim); scene.add(rim.target);
    const front = new THREE.SpotLight(0xf3f1ee, 125, 0, 0.35, 0.9, 2); front.position.set(1.6, 3.2, 9); scene.add(front); scene.add(front.target);
    scene.add(new THREE.HemisphereLight(0x8fa3c0, 0x0a0c10, 0.25));
    // crowd: silhouette impostors rendered from the avatar itself (seated front row on benches, standing second row)
    const imp = this._impostors();
    const bench = new THREE.MeshBasicMaterial({ color: 0x050607 });
    const r = mulberry(5);
    for (const s of [-1, 1]) {
      const b = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.45, 40), bench); b.position.set(s * 3.1, 0.225, -16); scene.add(b);
      for (let z = 3.2; z > -36; z -= 0.62 + 0.18 * r()) {
        for (const row of [0, 1]) {
          if (row === 1 && r() < 0.25) continue;
          const kind = row === 0 ? imp.seated[Math.floor(r() * imp.seated.length)] : imp.standing[Math.floor(r() * imp.standing.length)];
          const hgt = kind.h * (0.94 + 0.12 * r());
          const mat = new THREE.MeshBasicMaterial({ map: kind.tex, transparent: true, alphaTest: 0.5, color: 0x020304, side: THREE.DoubleSide });
          const q = new THREE.Mesh(new THREE.PlaneGeometry(hgt * kind.aspect, hgt), mat);
          if (s > 0) q.scale.x = -1;
          q.position.set(s * (3.05 + row * 0.9 + 0.1 * r()), hgt / 2 + (row === 0 ? kind.y0 : 0), z + 0.1 * r());
          q.userData.billboard = true; scene.add(q);
          if (r() < 0.05 && z < -2) {   // a phone screen held up
            const ph = new THREE.Mesh(new THREE.PlaneGeometry(0.05, 0.09), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.8, 0.9, 1).multiplyScalar(1.4) }));
            ph.position.set(q.position.x - s * 0.25, (row === 0 ? 1.15 : 1.45) + 0.1 * r(), q.position.z + 0.05); ph.userData.billboard = true; scene.add(ph);
          }
        }
      }
    }
    // rain: streaks animated on the GPU from per-drop seeds
    const ND = 5000, rd = new Float32Array(ND * 2 * 4), ends = new Float32Array(ND * 2);
    for (let i = 0; i < ND; i++) { const a = [r(), r(), r(), r()]; for (const e of [0, 1]) { rd.set(a, (2 * i + e) * 4); ends[2 * i + e] = e; } }
    const rg = new THREE.BufferGeometry();
    rg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(ND * 2 * 3), 3));
    rg.setAttribute('aSeed', new THREE.BufferAttribute(rd, 4)); rg.setAttribute('aEnd', new THREE.BufferAttribute(ends, 1));
    const rain = new THREE.LineSegments(rg, new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uTime: { value: 0 }, uFog: { value: FOG.clone() } },
      vertexShader: /* glsl */`uniform float uTime; attribute vec4 aSeed; attribute float aEnd; varying float vA;
        void main(){ float sp = 7.5 + 2.5 * aSeed.z, H = 9.;
          vec3 p = vec3(-9. + 18. * aSeed.x, 0., 7. - 44. * aSeed.y);
          p.y = H - mod(uTime * sp + aSeed.w * H, H);
          p.x += p.y * .06;
          p += aEnd * vec3(.012, -.2 - .06 * aSeed.z, 0.);
          vec4 mv = modelViewMatrix * vec4(p, 1.); float d = -mv.z;
          vA = .5 * exp(-d * .035) * smoothstep(.5, 2.5, d);
          gl_Position = projectionMatrix * mv; }`,
      fragmentShader: /* glsl */`varying float vA; void main(){ gl_FragColor = vec4(vec3(.75, .85, 1.) * vA, vA); }` }));
    rain.frustumCulled = false; scene.add(rain);
    const billboards = []; scene.traverse(o => { if (o.userData.billboard) billboards.push(o); });
    const post = { exposure: 1.0, sat: 0.42, gain: [0.9, 0.98, 1.1], lift: [0.012, 0.018, 0.03], contrast: 1.1, gamma: 1.02,
      bloom: 0.3, bloomThresh: 1.5, halation: 0.07, halationTint: [1, 0.45, 0.3], grain: 0.055, grainSize: 1.2, vignette: 0.32, ca: 0.0012,
      screen: 0.24, screenPeriod: 3, scanlines: 0.1, scanPeriod: 3 };
    const walk = av.sequence([{ clip: 'walk_runway_loop', at: 0, speed: 0.72, loop: true }], { z: -20 });
    const chrome = (H, t, look) => {
      for (const [x, y] of [[36, 36], [1884, 36], [36, 1044], [1884, 1044]]) H.cross(x, y, 9, { alpha: 0.6 });
      H.mono(`SUBJECT 01 · LOOK ${look}`, 72, 70, { size: 13 }); H.rule(72, 82, 420, 82, { alpha: 0.4 });
      H.mono('UPPING MY P(DOOM) · RUN 01', 1848, 70, { size: 13, align: 'right' });
      H.wave(1700, 112, 148, 18, t, { alpha: 0.6 });
      H.ruler(44, 330, 750, t, { alpha: 0.4 });
      H.mono(`LOOKBOOK · P(DOOM) · P. ${look}`, 72, 1008, { size: 12, alpha: 0.7 }); H.rule(72, 1020, 1848, 1020, { alpha: 0.28 });
      H.mono(tc(t), 1848, 1008, { size: 12, alpha: 0.7, align: 'right' });
      H.ticker(TICKER(t), 1050, t, { size: 13, alpha: 0.78 });
    };
    const shot = (camFn, poseFn, hudFn) => (t, aspect) => {
      const p = poseFn(t);
      const cam = camFn(aspect, p);
      av.apply(p.pose, { hands: { curl: 0.5 }, breath: { amp: 0.8 }, noise: { amp: 0.4 }, ...(p.layers || {}),
        look: p.lookCam ? { target: cam.position, weight: 1 } : undefined }, t);
      const hp = av.headAnchor(V3());
      rim.target.position.copy(hp); rim.target.updateMatrixWorld();
      front.position.set(hp.x + 1.6, hp.y + 1.9, hp.z + 6.5); front.intensity = 1.9 * front.position.distanceToSquared(hp);
      front.target.position.set(hp.x, hp.y - 0.3, hp.z); front.target.updateMatrixWorld();
      for (const b of billboards) { const d = cam.position.clone().sub(b.position); b.rotation.set(0, Math.atan2(d.x, d.z), 0); }
      rain.material.uniforms.uTime.value = t; floor.material.uniforms.uTime.value = t;
      return { camera: cam, post, hud: (H, c, tt) => { chrome(H, tt, '03'); hudFn(H, c, tt, hp); } };
    };
    return {
      scene, enter: () => this._avatarMode({ look: 'photo' }),
      shots: {
        wide: shot(a => camera(20, a, V3(0, 1.45, 9), V3(0, 1.22, -12)), t => ({ pose: walk.pose(14 + t) }),
          (H) => {
            H.mono('CHORUS 01 · 00:23.0', 110, 360, { size: 13, alpha: 0.75 });
            H.text([["I'm upping", '#f4f5f7']], 106, 450, { size: 84, weight: 600, track: -2 });
            H.text([['my ', '#f4f5f7'], ['P(doom).', ORANGE]], 106, 540, { size: 84, weight: 600, track: -2 });
            H.rule(110, 575, 560, 575, { alpha: 0.5 }); H.mono('BPM 132 · 4/4 · STEP = 2 BEATS', 110, 600, { size: 12, alpha: 0.7 });
          }),
        medium: shot((a, p) => { const hp = p.head; return camera(12.5, a, V3(0.15, 1.5, hp.z + 7.6), V3(hp.x, 1.3, hp.z)); },
          t => { const pose = walk.pose(22 + t); const h = V3(pose.root[0], 1.6, pose.root[2]); return { pose, head: h }; },
          (H, cam, t, hp) => {
            const [sx, sy] = toScreen(hp, cam);
            H.brackets(sx - 88, sy - 105, 176, 200, { len: 22, alpha: 0.95, width: 1.6 });
            H.ctx.fillStyle = 'rgba(8,10,14,0.62)'; H.ctx.fillRect(sx + 96, sy - 108, 150, 60);
            H.mono('SUBJECT 01', sx + 104, sy - 92, { size: 12, alpha: 0.95 });
            H.mono('LOOK 03 / 11', sx + 104, sy - 74, { size: 12, alpha: 0.8 });
            H.mono('TRACKING', sx + 104, sy - 56, { size: 12, color: ORANGE, alpha: 1 });
            H.counter(1420, 330, '0.37', ['P(DOOM)', 'AND RISING']);
            H.text([['Sydney, please let me ', '#f4f5f7'], ['free.', ORANGE]], 960, 930, { size: 34, weight: 500, align: 'center', track: -0.5 });
          }),
        close: shot((a, p) => { const hp = p.head; return camera(11, a, V3(hp.x + 0.1, hp.y + 0.01, hp.z + 2.25), V3(hp.x, hp.y - 0.07, hp.z)); },
          t => { const pose = av.pose('stand_breathe_loop', 1.0 + t, { place: { x: 0, z: 1.2, yaw: 0 } }); return { pose, head: V3(0, 1.62, 1.26), lookCam: true, layers: { breath: { amp: 1.1 } } }; },
          (H) => {
            H.card(1470, 380, 360, [['SUBJECT', '01'], ['LOOK', '03 / 11'], ['P(DOOM)', '0.37 ▲'], ['CONTEXT', '1,048,576 TOK'], ['KILLSWITCH', 'ON PTO']],
              { title: 'UPPING MY P(DOOM)', tag: 'RUNWAY' });
            H.mono('END OF RUNWAY · HOLD 4 BEATS', 110, 360, { size: 13, alpha: 0.75 });
            H.text([['Was it all ', '#f4f5f7'], ['for show?', ORANGE]], 106, 450, { size: 64, weight: 600, track: -1.5 });
          }),
      },
    };
  }

  _impostors() {
    // render the avatar as black silhouettes (with alpha) in a few seated / standing poses, seen from the side
    const av = this.av, r = this.r, sc = new THREE.Scene();
    const prevParent = av.root.parent; sc.add(av.root);
    this._avatarMode({ look: 'silhouette' });
    const make = (clip, t, yaw, H) => {
      const rt = new THREE.WebGLRenderTarget(256, 512, { samples: 4 });
      const p = av.pose(clip, t, { place: { x: 0, z: 0, yaw }, rootMotion: false });
      av.apply(p, { hands: { curl: 0.5 } }, 0);
      const cam = new THREE.OrthographicCamera(-H / 4, H / 4, H, 0, -5, 5); cam.position.set(0, 0, 2); cam.lookAt(0, 0, 0); cam.updateMatrixWorld();
      r.setRenderTarget(rt); r.setClearColor(0x000000, 0); r.clear(); r.render(sc, cam); r.setRenderTarget(null);
      return { tex: rt.texture, h: H, aspect: 0.5 };
    };
    const seated = [['sit_stool_head_bowed', 0.0], ['sit_stool_head_bowed', 0.8], ['sit_down_get_up', 2.5]].map(([c, t]) => ({ ...make(c, t, Math.PI / 2, 1.9), y0: 0 }));
    const standing = [['idle_wait', 6], ['idle_stand', 3], ['grief_standing', 8], ['idle_lookaround_lookback', 20]].map(([c, t]) => ({ ...make(c, t, Math.PI / 2, 1.9), y0: 0 }));
    if (prevParent) prevParent.add(av.root); else sc.remove(av.root);
    return { seated, standing };
  }

  // ---------------------------------------------------------------------------------------------- L3 reconstruction
  buildL3() {
    const av = this.av, scene = new THREE.Scene();
    // skinned body points (head region excluded: the head comes from the photo point cloud)
    const skip = new Set(); const headBone = av.bone('head');
    headBone.traverse(o => { if (o.isBone) skip.add(av.index[o.name]); });
    const parts = [['skin', 5000, skip], ['top', 22000, null], ['trousers', 17000, null], ['shoes', 4000, null]];
    const geos = parts.map(([n, c, sk], i) => sampleSkinned(av.meshes[n], av.origMat[n], c, 101 + i, sk));
    const body = mergePointGeos(geos);
    const bodyMat = pointsMaterial({ uSize: { value: 0.0042 }, uGain: { value: 1.3 } });
    const pts = new THREE.SkinnedMesh(body, bodyMat);
    pts.isMesh = false; pts.isPoints = true; pts.frustumCulled = false;
    const skinMesh = av.meshes.skin;
    skinMesh.parent.add(pts);
    pts.bind(skinMesh.skeleton, skinMesh.bindMatrix);
    const headMat = pointsMaterial({ uSize: { value: 0.0024 }, uGain: { value: 1.0 } }, true);
    const head = new THREE.Points(this.headGeo, headMat); head.frustumCulled = false;
    headBone.add(head);
    this.pts = { body: pts, head };
    // floor: a sparse grid of points
    const fp = []; for (let x = -12; x <= 12; x += 0.25) for (let z = -16; z <= 6; z += 0.25) fp.push(x, 0, z);
    const fg = new THREE.BufferGeometry(); fg.setAttribute('position', new THREE.Float32BufferAttribute(fp, 3));
    const floorPts = new THREE.Points(fg, new THREE.ShaderMaterial({ transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uProj: { value: 1000 } },
      vertexShader: /* glsl */`uniform float uProj; varying float vA; void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.); float d = -mv.z; vA = .5 * exp(-d * .16) * (1. - smoothstep(4., 9., length(position.xz))); gl_Position = projectionMatrix * mv; gl_PointSize = clamp(.01 * uProj / d, 1., 3.); }`,
      fragmentShader: /* glsl */`varying float vA; void main(){ float a = smoothstep(.5, .1, length(gl_PointCoord - .5)) * vA; gl_FragColor = vec4(vec3(.55, .65, .85) * a, a); }` }));
    floorPts.frustumCulled = false; scene.add(floorPts);
    const contour = CONTOUR_MAT();
    const look = (m) => /^(top|trousers|shoes)$/.test(m.name) ? contour : new THREE.MeshBasicMaterial({ visible: false });
    const post = { exposure: 1.1, sat: 0.8, contrast: 1.12, bloom: 0.8, bloomThresh: 0.8, halation: 0.05, grain: 0.04, vignette: 0.42, ca: 0.0022, gain: [0.97, 1.0, 1.06] };
    const shot = (clip, clipT, place, camFn, front, scan, hudFn, extra = {}) => (t, aspect) => {
      const p = av.pose(clip, clipT + t, { place });
      const cam = camFn(aspect);
      av.apply(p, { hands: { curl: 0.5 }, breath: { amp: 1 }, noise: { amp: 0.5 }, look: extra.lookCam ? { target: cam.position, weight: 1 } : undefined }, t);
      const pr = cam.projectionMatrix.elements[5] * 1080 / 2;
      const fr = typeof front === 'function' ? front(t) : front, sy = typeof scan === 'function' ? scan(t) : scan;
      for (const m of [bodyMat, headMat]) { m.uniforms.uTime.value = t; m.uniforms.uFront.value = fr; m.uniforms.uScanY.value = sy; m.uniforms.uProj.value = pr; m.uniforms.uAmp.value = extra.amp ?? 0.9; m.uniforms.uSign.value = extra.sign ?? 1; }
      contour.uniforms.uFront.value = fr; contour.uniforms.uScanY.value = sy; contour.uniforms.uSign.value = extra.sign ?? 1;
      floorPts.material.uniforms.uProj.value = pr;
      return { camera: cam, post, hud: (H, c, tt) => hudFn(H, c, tt) };
    };
    const label = (H, cam, bone, id) => {
      const [x, y] = toScreen(av.worldPos(bone), cam);
      H.cross(x, y, 6, { alpha: 0.7 }); H.mono(`${id} ${bone.toUpperCase()}`, x + 10, y - 8, { size: 10, alpha: 0.7 });
    };
    const techHud = (H, cam, t, title) => {
      for (const [x, y] of [[36, 36], [1884, 36], [36, 1044], [1884, 1044]]) H.cross(x, y, 9, { alpha: 0.5 });
      H.mono(title, 72, 70, { size: 13 }); H.rule(72, 82, 470, 82, { alpha: 0.35 });
      H.mono(`POINTS ${(48000 + this.headGeo.attributes.position.count).toLocaleString('en-US')}`, 72, 104, { size: 11, alpha: 0.65 });
      H.mono('MEASURED 1 VIEW · INFERRED 359°', 72, 122, { size: 11, alpha: 0.65 });
      H.mono(tc(t), 1848, 70, { size: 12, align: 'right', alpha: 0.7 });
    };
    return {
      scene, enter: () => { this._avatarMode({ look, points: true }); },
      shots: {
        wide: shot('stand_breathe_loop', 0.4, { x: 0, z: 0, yaw: 0.25 }, a => camera(26, a, V3(0.2, 1.0, 6.2), V3(0, 0.95, 0)),
          t => 1.66 + 0.03 * Math.sin(t), t => 0.9 + ((t * 0.5) % 0.9),
          (H, cam, t) => {
            techHud(H, cam, t, 'RECONSTRUCTION · PASS 03');
            for (const [b, id] of [['head', 'J13'], ['wrist.L', 'J25'], ['wrist.R', 'J32'], ['foot.L', 'J75'], ['foot.R', 'J81']]) label(H, cam, b, id);
            H.text([['I feel my atoms', '#eef1f6']], 1180, 470, { size: 58, weight: 300, track: -1 });
            const word = 'rearranging'; let x = 1180;
            for (let i = 0; i < word.length; i++) {
              const dy = Math.max(0, Math.sin(i * 1.3 + t * 0.9)) * 26 * (i / word.length), dx = Math.sin(i * 2.1 + t) * 6 * (i / word.length);
              x += H.text([[word[i], i > 6 ? ORANGE : '#eef1f6', 1 - 0.5 * i / word.length]], x + dx, 540 - dy, { size: 58, weight: 300, track: -1 });
            }
          }, { amp: 0.9 }),
        medium: shot('arms_open_stretch', 1.55, { x: 0, z: 0, yaw: -0.35 }, a => camera(28, a, V3(1.35, 1.4, 3.0), V3(0.05, 1.28, 0)),
          1.8, 1.25,
          (H, cam, t) => {
            techHud(H, cam, t, 'RECONSTRUCTION · PASS 07');
            for (const [b, id] of [['head', 'J13'], ['wrist.L', 'J25'], ['wrist.R', 'J32']]) label(H, cam, b, id);
            H.text([['atoms rearranging', '#eef1f6']], 960, 960, { size: 30, weight: 400, align: 'center', track: 0 });
          }),
        close: shot('stand_breathe_loop', 1.6, { x: 0, z: 0, yaw: 0 }, a => camera(19, a, V3(0.62, 1.66, 1.2), V3(0.02, 1.6, 0.02)),
          1.74, t => 1.64 + ((t * 0.3) % 0.08),
          (H, cam, t) => {
            techHud(H, cam, t, 'RECONSTRUCTION · FROM 1 PHOTOGRAPH');
            H.mono('FRONT: MEASURED', 1500, 900, { size: 12, alpha: 0.8 }); H.mono('BACK: INFERRED', 1500, 920, { size: 12, alpha: 0.8, color: ORANGE });
          }, { lookCam: false, amp: 0.6 }),
      },
    };
  }
}

function mergePointGeos(geos) {
  const g = new THREE.BufferGeometry();
  for (const name of ['position', 'aCol', 'aRand', 'skinIndex', 'skinWeight']) {
    const arrs = geos.map(x => x.attributes[name]);
    const n = arrs.reduce((a, b) => a + b.array.length, 0), Arr = arrs[0].array.constructor, out = new Arr(n);
    let o = 0; for (const a of arrs) { out.set(a.array, o); o += a.array.length; }
    g.setAttribute(name, name === 'skinIndex' ? new THREE.Uint16BufferAttribute(out, 4) : new THREE.BufferAttribute(out, arrs[0].itemSize));
  }
  return g;
}
