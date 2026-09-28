// motion_prep.js - lane F motion-prep test page (BIBLE 5.7 M1-M6), driven by motion_prep.mjs through window.*.
// Uses the film's own code path: src/avatar.js + src/motion/sequences.js. Everything is a pure function of its
// arguments (film time, camera, layers), like the film renderer.
//   window.frame(opts)       one render -> JPEG/PNG data URL (env 'grid' | 'studio' | 'hall' | 'sil'; shot + t or clip + t)
//   window.heelTrack(opts)   heel / ball vertex world positions of both shoes over a film-time range (posed skeleton)
//   window.atlas(opts)       S54 side-silhouette capture atlas -> PNG data URL
//   window.check(opts)       sequence continuity + FK checks
import * as THREE from 'three';
import { Avatar } from '../src/avatar.js';
import * as SEQ from '../src/motion/sequences.js';

const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, alpha: true });
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const av = await Avatar.load({ glb: '/out/avatar/subject.glb', manifest: '/out/avatar/motion/MANIFEST.json' });
window.av = av; window.SEQ = SEQ; window.THREE = THREE;
const lin = hex => new THREE.Color(hex);   // three converts hex sRGB -> linear working space

// ------------------------------------------------------------------------------------------------ environments
function gridEnv() {
  const s = new THREE.Scene();
  s.background = new THREE.Color(0x2b2b2b);
  s.add(new THREE.HemisphereLight(0xffffff, 0x5a5550, 1.5));
  const key = new THREE.DirectionalLight(0xffffff, 1.8); key.position.set(2.5, 4, 3); s.add(key);
  const rim = new THREE.DirectionalLight(0xdfe8ff, 0.7); rim.position.set(-3, 3, -3); s.add(rim);
  const g1 = new THREE.GridHelper(40, 160, 0x8a8a8a, 0x4a4a4a); g1.position.y = 0.001; s.add(g1);
  const g2 = new THREE.GridHelper(40, 40, 0xb0b0b0, 0x6a6a6a); g2.position.y = 0.002; s.add(g2);
  return { scene: s, look: 'photo' };
}

// the stool of BIBLE 4.8 (seat D 0.33 at 0.60 m, four legs, footring at 0.25 m, pale wood) and the tape X
export function buildStool() {
  const g = new THREE.Group(), wood = new THREE.MeshLambertMaterial({ color: lin(0xcdbb9e) });
  const seat = new THREE.Mesh(new THREE.CylinderGeometry(0.165, 0.163, 0.035, 72), wood); seat.position.y = 0.6 - 0.0175; g.add(seat);
  const rTop = 0.115, rBot = 0.205, yTop = 0.565;
  for (let k = 0; k < 4; k++) {
    const a = Math.PI / 4 + k * Math.PI / 2, c = Math.cos(a), s = Math.sin(a);
    const top = new THREE.Vector3(rTop * c, yTop, rTop * s), bot = new THREE.Vector3(rBot * c, 0, rBot * s);
    const len = top.distanceTo(bot), leg = new THREE.Mesh(new THREE.CylinderGeometry(0.0135, 0.0115, len, 20), wood);
    leg.position.copy(top).add(bot).multiplyScalar(0.5);
    leg.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), top.clone().sub(bot).normalize()); g.add(leg);
  }
  const yr = 0.25, rr = rBot + (rTop - rBot) * yr / yTop;
  const ring = new THREE.Mesh(new THREE.TorusGeometry(rr, 0.0085, 12, 96), wood); ring.rotation.x = Math.PI / 2; ring.position.y = yr; g.add(ring);
  const tape = new THREE.MeshLambertMaterial({ color: lin(0xdad7cf) });
  for (const a of [Math.PI / 4, -Math.PI / 4]) {
    const t = new THREE.Mesh(new THREE.PlaneGeometry(0.30, 0.048).rotateX(-Math.PI / 2), tape); t.rotation.y = a; t.position.y = 0.0008; g.add(t);
  }
  return g;
}
function shadowTex() {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const x = c.getContext('2d'), gr = x.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(0.45, 'rgba(0,0,0,0.55)'); gr.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = gr; x.fillRect(0, 0, 256, 256);
  return new THREE.CanvasTexture(c);
}
function studioEnv() {
  const s = new THREE.Scene();
  const PAPER = lin(0xf2efe8);
  s.background = PAPER.clone();
  const mat = new THREE.MeshLambertMaterial({ color: PAPER });
  // cyclorama: floor, 1 m cove, back wall (8 x 6 x 4), the stool on the tape X at the origin
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(8, 5).rotateX(-Math.PI / 2), mat); floor.position.set(0, 0, 0.5); s.add(floor);
  const cove = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 8, 48, 1, true, Math.PI, Math.PI / 2).rotateZ(Math.PI / 2), mat);
  cove.material = mat.clone(); cove.material.side = THREE.BackSide; cove.position.set(0, 1, -2); s.add(cove);
  const wall = new THREE.Mesh(new THREE.PlaneGeometry(8, 3), mat); wall.position.set(0, 2.5, -3); s.add(wall);
  const stool = buildStool(); s.add(stool);
  const sh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ map: shadowTex(), transparent: true, opacity: 0.14, depthWrite: false, color: 0x000000 }));
  sh.scale.set(0.75, 1, 0.6); sh.position.set(0, 0.0012, 0.12); s.add(sh);
  // flat, shadowless frontal light: a big soft source behind the camera + hemisphere fill
  const hemi = new THREE.HemisphereLight(0xffffff, 0xf3efe7, 1.9); s.add(hemi);
  const front = new THREE.DirectionalLight(0xffffff, 1.25); s.add(front); s.add(front.target);
  return { scene: s, look: 'photo', front, stool, shadow: sh };
}
function silEnv() {
  const s = new THREE.Scene();
  s.background = new THREE.Color(0x000000);
  return { scene: s, look: (n, o) => silMat(n, o) };
}
const _sil = {};
function silMat(n, o) {   // white silhouette (alpha-cut hair keeps its fibre edge)
  return (_sil[n] ??= new THREE.MeshBasicMaterial({ color: 0xffffff, map: /^hair|brow|lash/.test(n) ? o.map : null,
    alphaTest: /^hair|brow|lash/.test(n) ? (o.alphaTest || 0.35) : 0, side: o.side }));
}
const ENVS = {};
const env = k => (ENVS[k] ??= { grid: gridEnv, studio: studioEnv, sil: silEnv }[k]());

// ------------------------------------------------------------------------------------------------ one frame
const cams = { p: new THREE.PerspectiveCamera(30, 1, 0.02, 200), o: new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 100) };
function camera({ pos, target, fov = 30, ortho = null, w, h }) {
  const c = ortho ? cams.o : cams.p;
  if (ortho) { const hh = ortho / 2, ww = hh * w / h; Object.assign(c, { left: -ww, right: ww, top: hh, bottom: -hh }); }
  else { c.fov = fov; c.aspect = w / h; }
  c.position.set(...pos); c.up.set(0, 1, 0); c.lookAt(...target); c.updateProjectionMatrix(); c.updateMatrixWorld(true);
  return c;
}

// pose for opts: a shot's sequence at film time t, or a clip at clip time t (optionally placed)
function poseFor({ shot, clip, t = 0, place, speed, loop }) {
  if (shot) return SEQ.poseAt(av, shot, t);
  return av.pose(clip, t, { place, speed, loop });
}

window.frame = (o) => {
  const { envName = 'grid', w = 600, h = 600, look, layers, lens, fmt = 'jpeg', q = 0.9, hideAvatar = false, stool = null, transparent = false } = o;
  const E = env(envName);
  renderer.setSize(w, h, false);
  if (av.root.parent !== E.scene) E.scene.add(av.root);
  av.root.visible = !hideAvatar;
  av.setLook(look || E.look);
  const pose = poseFor(o);
  const L = layers !== undefined ? layers : o.shot ? SEQ.layersAt(o.shot, o.t, { lens: lens || o.cam.pos, av }) : { hands: { curl: 0.5 } };
  if (L && L.look && L.look.target && !L.look.target.isVector3) L.look.target = new THREE.Vector3(...L.look.target);
  av.apply(pose, L || {}, o.t || 0);
  // camera may follow the root (sheets)
  let cam = o.cam;
  if (o.follow) {
    const r = av.worldPos('root'), f = o.follow;
    cam = { ...cam, pos: [r.x + f.off[0], f.off[1], r.z + f.off[2]], target: [r.x + (f.aim?.[0] || 0), f.aim?.[1] ?? 0.9, r.z + (f.aim?.[2] || 0)] };
  }
  const c = camera({ ...cam, w, h });
  if (E.stool) {
    E.stool.visible = !!stool || envName === 'studio' && stool !== false;
    if (stool) E.stool.position.set(stool.x, 0, stool.z);
    E.shadow.position.set(E.stool.position.x, 0.0012, E.stool.position.z + 0.12);
    E.front.position.copy(c.position).add(new THREE.Vector3(0, 0.6, 0)); E.front.target.position.set(...cam.target); E.front.target.updateMatrixWorld();
  }
  if (transparent) { renderer.setClearColor(0x000000, 0); E.scene.background = null; }
  renderer.render(E.scene, c);
  if (transparent) E.scene.background = envName === 'studio' ? lin(0xf2efe8) : new THREE.Color(0x000000);
  av.root.visible = true;
  return canvas.toDataURL(fmt === 'png' ? 'image/png' : 'image/jpeg', q);
};

// ------------------------------------------------------------------------------------------------ feet on the posed skeleton
const shoes = av.meshes.shoes;
function footPoints() {   // heel and ball vertex of each shoe from the rest mesh (as motion_lib.py foot_points)
  const P = shoes.geometry.attributes.position, out = {};
  for (const [s, sign] of [['L', 1], ['R', -1]]) {
    const idx = []; for (let i = 0; i < P.count; i++) if (P.getX(i) * sign > 0) idx.push(i);
    const ymin = Math.min(...idx.map(i => P.getY(i)));
    const cand = idx.filter(i => P.getY(i) < ymin + 0.012);
    const zs = cand.map(i => P.getZ(i)), zmin = Math.min(...zs), zmax = Math.max(...zs);
    const heel = cand[zs.indexOf(zmin)];
    const xm = cand.reduce((a, i) => a + P.getX(i), 0) / cand.length, zt = zmin + 0.72 * (zmax - zmin);
    let ball = cand[0], bd = 1e9;
    for (const i of cand) { const d = Math.abs(P.getZ(i) - zt) + 0.2 * Math.abs(P.getX(i) - xm); if (d < bd) { bd = d; ball = i; } }
    out[s] = { heel, ball };
  }
  return out;
}
const FP = footPoints();
const _v = new THREE.Vector3();
const vpos = (mesh, i) => { mesh.getVertexPosition(i, _v); _v.applyMatrix4(mesh.matrixWorld); return [_v.x, _v.y, _v.z]; };

window.heelTrack = ({ shot, t0, t1, dt = 1 / 240 }) => {
  const out = { t: [], LH: [], LB: [], RH: [], RB: [], root: [] };
  const n = Math.round((t1 - t0) / dt);
  for (let k = 0; k <= n; k++) {
    const t = t0 + k * dt;
    av.apply(SEQ.poseAt(av, shot, t), {}, t);
    out.t.push(+t.toFixed(5));
    out.LH.push(vpos(shoes, FP.L.heel)); out.LB.push(vpos(shoes, FP.L.ball));
    out.RH.push(vpos(shoes, FP.R.heel)); out.RB.push(vpos(shoes, FP.R.ball));
    const r = av.worldPos('root'); out.root.push([r.x, r.y, r.z]);
  }
  return out;
};

// ------------------------------------------------------------------------------------------------ checks
window.check = () => {
  const out = { fk: {}, joins: {} };
  // pure FK against the skeleton
  const p = SEQ.poseAt(av, 'S54', 145.0); av.apply(p, {}, 145.0);
  for (const n of ['root', 'footL', 'wristR', 'head', 'toe3-1L']) {
    const a = av.fkHead(p, n), b = av.worldPos(n);
    out.fk[n] = +(Math.hypot(a[0] - b.x, a[1] - b.y, a[2] - b.z) * 1000).toFixed(4);
  }
  // root continuity at every segment join, and the largest per-240th root step in +-0.5 s around each join
  for (const id of Object.keys(SEQ.SHOTS)) {
    const spec = SEQ.SHOTS[id];
    if (!spec.segments || spec.still) continue;
    const seq = SEQ.sequenceFor(av, id);
    out.joins[id] = seq.segments.slice(1).map(s => {
      const a = seq.pose(s.at - 1e-5), b = seq.pose(s.at + 1e-5);
      let worst = 0;
      for (let t = s.at - 0.5; t < s.at + Math.max(0.5, s.fade + 0.1); t += 1 / 240) {
        const u = seq.pose(t), v = seq.pose(t + 1 / 240);
        worst = Math.max(worst, Math.hypot(u.root[0] - v.root[0], u.root[1] - v.root[1], u.root[2] - v.root[2]));
      }
      const hd = ((av.heading(b) - av.heading(a)) * 180 / Math.PI + 540) % 360 - 180;
      return { clip: s.clip, at: +s.at.toFixed(4), from: +(s.from || 0).toFixed(4), fade: s.fade,
        root_jump_mm: +(Math.hypot(a.root[0] - b.root[0], a.root[1] - b.root[1], a.root[2] - b.root[2]) * 1000).toFixed(4),
        heading_jump_deg: +hd.toFixed(4), max_root_speed_mps_near_join: +(worst * 240).toFixed(3) };
    });
    if (seq.segments.some(s => s.turn)) {   // pivot continuity at the turn start
      const s = seq.segments.find(s => s.turn), a = seq.pose(s.turn.at - 1e-5), b = seq.pose(s.turn.at + 1e-5);
      out.joins[id].push({ turn_at: s.turn.at, root_jump_mm: +(Math.hypot(a.root[0] - b.root[0], a.root[2] - b.root[2]) * 1000).toFixed(4), pivot: s.turn.P.map(v => +v.toFixed(3)) });
    }
  }
  // determinism: the same pose twice, and out of order
  const q1 = SEQ.poseAt(av, 'S15', 44.4), junk = SEQ.poseAt(av, 'S54', 150), q2 = SEQ.poseAt(av, 'S15', 44.4);
  out.pure = q1.q.every((v, i) => v === q2.q[i]) && q1.root.every((v, i) => v === q2.root[i]);
  out.marks = Object.fromEntries(Object.keys(SEQ.SHOTS).filter(id => SEQ.SHOTS[id].segments && !SEQ.SHOTS[id].still).map(id => [id, SEQ.sequenceFor(av, id).marks]));
  return out;
};

// ------------------------------------------------------------------------------------------------ S54 capture atlas
window.atlas = ({ shot = 'S54', times, cellW = 280, cellH = 360, cols = 13, span = 2.1, side = -1, ground = 0.07 }) => {
  const rows = Math.ceil(times.length / cols);
  const A = document.createElement('canvas'); A.width = cols * cellW; A.height = rows * cellH;
  const g = A.getContext('2d'); g.fillStyle = '#000'; g.fillRect(0, 0, A.width, A.height);
  const E = env('sil');
  renderer.setSize(cellW, cellH, false);
  if (av.root.parent !== E.scene) E.scene.add(av.root);
  av.setLook(E.look);
  const meta = [];
  times.forEach((t, k) => {
    av.apply(SEQ.poseAt(av, shot, t), {}, t);
    const r = av.worldPos('root');
    // orthographic side view from the figure's right (-X): he walks left -> right, feet on a common ground line
    const hh = span, yc = hh / 2 - ground * hh;
    const c = camera({ pos: [r.x + side * 6, yc, r.z], target: [r.x, yc, r.z], ortho: hh, w: cellW, h: cellH });
    renderer.setClearColor(0x000000, 1);
    renderer.render(E.scene, c);
    const x = (k % cols) * cellW, y = Math.floor(k / cols) * cellH;
    g.drawImage(canvas, x, y);
    meta.push({ i: k, t, x, y, w: cellW, h: cellH, root: [r.x, r.y, r.z].map(v => +v.toFixed(4)) });
  });
  return { png: A.toDataURL('image/png'), meta, cols, rows, cellW, cellH, span, ground };
};

window.ready = true;
