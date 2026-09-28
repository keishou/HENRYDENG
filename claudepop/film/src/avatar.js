// avatar.js - the protagonist (claudepop/out/avatar/subject.glb) in three.js.
//
// Deterministic mocap playback for an offline, frame-by-frame renderer: every function below is a pure function of
// its arguments (film time, clip time, layer parameters). There is no Math.random, no clock, no per-frame state
// carried from one render to the next: apply() resets every bone before writing, so frames can be rendered in any
// order, in parallel workers, or re-rendered, and always come out identical.
//
// Data: motion clips built by claudepop/avatar/tools/motion_lib.py (CMU mocap retargeted onto this exact skeleton):
//   <motion>/MANIFEST.json  + <motion>/<clip>.bin  (float32, frame-major: root xyz, then xyzw per listed bone)
// Conventions: metres, Y up, floor y = 0, every clip starts at x = z = 0 facing +Z (walks travel along +Z).
// three.js strips the dots from bone names (upperarm01.L -> upperarm01L); every name argument accepts either form.
//
// API
//   const av = await Avatar.load({ glb, manifest, clips })   glb: URL of subject.glb; manifest: URL of MANIFEST.json;
//                                                            clips: optional array of clip names to load (default all)
//   scene.add(av.root)                                       THREE.Group holding the skinned meshes and the skeleton
//   av.clipNames                                             loaded clip names
//   av.clip(name)                                            manifest entry {seconds, loop, loop_info, shows, ...}
//
//   Poses (plain data: { root: Float32Array(3), q: Float32Array(4 * bones) }, every bone present):
//   av.pose(name, t, opts)          sample a clip at clip time t (seconds). opts:
//        loop       default = the clip's own flag; loop clips chain cycles, adding cycle_root_delta per cycle
//        speed      time scale (1 = as captured); clip time = t * speed
//        rootMotion true (default) | false (x, z held at 0: walk in place, heading still turns)
//                   | 'lock' (x, z held and heading held at the clip start: a treadmill that never turns)
//        place      { x, z, yaw } rigid ground-plane placement of the clip (yaw in radians about +Y)
//   av.restPose()                   the A-pose rest
//   av.mix(pA, pB, w)               per-bone slerp / root lerp, w in [0, 1] (weight of pB)
//   av.crossfade(pA, pB, t, t0, dur) mix with a smoothstep weight rising over [t0, t0 + dur]
//   av.sequence(segments, place)    an edit of clips on the film timeline; returns { pose(T), segments, heading(T) }.
//        segments: [{ clip, at, from = 0, speed = 1, fade = 0.6, loop, rootMotion }] sorted by `at` (film seconds).
//        Segment i starts at film time `at` at clip time `from` and fades in over `fade` seconds from segment i-1
//        (at most two segments overlap). Root motion chains: each segment is placed so its root position and heading
//        at its `at` coincide with the previous segment's, so a walk -> stop -> look-up edit is one continuous body.
//   av.placePose(pose, { x, z, yaw })   rigid ground-plane move of a pose, in place (returns it)
//   av.heading(pose)                facing yaw (radians, 0 = +Z) of a pose (the pelvis: swings a few degrees in a walk)
//   av.beatSpeed(name, bpm, beatsPerStep = 1)   speed factor that lands a loop clip's steps on a tempo grid
//        e.g. beatSpeed('walk_runway_loop', 66) = one step per beat at half-time 66 BPM (a step every 2 beats of 132)
//
//   Writing the skeleton:
//   av.apply(pose, layers, t)       set every bone from the pose, then add procedural layers evaluated at time t:
//        breath { amp = 1, period = 4.4, phase = 0 }          chest rise / shoulder lift, ~1.5 deg at amp 1
//        look   { target: THREE.Vector3 (world), weight = 1, eyes = true, maxDeg = 70 }  head + neck + eyes aim
//        noise  { amp = 1, seed = 0 }                         seeded smooth micro-motion (spine, neck, head, arms)
//        hands  { curl = 0.55 }                               relaxed finger curl (mocap has no fingers)
//        Returns this. The root group's own transform (av.root.position / rotation) places the avatar in the scene.
//
//   Looks (material swaps, reversible):
//   av.setLook('photo' | 'clay' | 'silhouette' | 'ghost' | fn)   'photo' restores the GLB materials; a function
//        fn(mesh, originalMaterial) -> THREE.Material installs any custom material per part
//   av.meshes                       { partName: THREE.SkinnedMesh } (skin, hair, hair_strands, top, trousers, shoes, eyes...)
//   av.bone(name)                   THREE.Bone
//   av.worldPos(boneName, target)   bone head in world space (after apply)
//   av.headAnchor(target)           a point between the eyes, world space (for cameras and look targets)
//   av.origMat                      { partName: original GLB material } (e.g. to sample the albedo for point clouds)
//   exports: noise1(t, seed) smooth deterministic value noise in [-1, 1]; LOOKS (the built-in material factories)
//
// Verified by claudepop/film/lookdev/avatar_test.mjs: pose()/apply() purity, loop seams, sequence continuity (root
// jump < 0.1 mm, heading < 0.02 deg at cuts), root-motion modes, and pixel-identical frames rendered out of order and
// in a fresh browser.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const strip = n => n.replace(/[.:\/\[\]]/g, '');
const smoothstep = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

// ------------------------------------------------------------------------------------------------ quaternion math
// (plain arrays, xyzw, so pose math never touches three.js objects and stays allocation-light)
function qslerp(out, o, a, b, t) {   // out[o..o+3] = slerp(a, b, t) where a, b are 4-arrays
  let ax = a[0], ay = a[1], az = a[2], aw = a[3], bx = b[0], by = b[1], bz = b[2], bw = b[3];
  let c = ax * bx + ay * by + az * bz + aw * bw;
  if (c < 0) { c = -c; bx = -bx; by = -by; bz = -bz; bw = -bw; }
  let k0, k1;
  if (c > 0.9995) { k0 = 1 - t; k1 = t; } else {
    const th = Math.acos(c), s = Math.sin(th);
    k0 = Math.sin((1 - t) * th) / s; k1 = Math.sin(t * th) / s;
  }
  let x = ax * k0 + bx * k1, y = ay * k0 + by * k1, z = az * k0 + bz * k1, w = aw * k0 + bw * k1;
  const n = Math.hypot(x, y, z, w) || 1;
  out[o] = x / n; out[o + 1] = y / n; out[o + 2] = z / n; out[o + 3] = w / n;
}
function qmul(a, b) {   // a * b
  return [a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
          a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
          a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
          a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2]];
}
const qconj = a => [-a[0], -a[1], -a[2], a[3]];
const qyaw = y => [0, Math.sin(y / 2), 0, Math.cos(y / 2)];
function qrot(q, v) {   // rotate vector v by unit quaternion q
  const [x, y, z, w] = q, [vx, vy, vz] = v;
  const tx = 2 * (y * vz - z * vy), ty = 2 * (z * vx - x * vz), tz = 2 * (x * vy - y * vx);
  return [vx + w * tx + (y * tz - z * ty), vy + w * ty + (z * tx - x * tz), vz + w * tz + (x * ty - y * tx)];
}
const get4 = (arr, i) => [arr[4 * i], arr[4 * i + 1], arr[4 * i + 2], arr[4 * i + 3]];

// ------------------------------------------------------------------------------------------------ deterministic noise
function hash1(n) {   // integer hash -> [0, 1)
  n = (n ^ 61) ^ (n >>> 16); n = Math.imul(n, 9); n ^= n >>> 4; n = Math.imul(n, 0x27d4eb2d); n ^= n >>> 15;
  return (n >>> 0) / 4294967296;
}
export function noise1(t, seed = 0) {   // smooth value noise in [-1, 1], period-free, C2 (quintic fade)
  const i = Math.floor(t), f = t - i, u = f * f * f * (f * (f * 6 - 15) + 10);
  const a = hash1(i * 374761393 + seed * 668265263), b = hash1((i + 1) * 374761393 + seed * 668265263);
  return (a + (b - a) * u) * 2 - 1;
}
const fbm = (t, seed) => noise1(t, seed) * 0.7 + noise1(t * 2.13 + 17.1, seed + 1) * 0.3;

// ------------------------------------------------------------------------------------------------ the avatar
export class Avatar {
  static async load({ glb, manifest, clips } = {}) {
    const av = new Avatar();
    const gltf = await new GLTFLoader().loadAsync(glb);
    av._init(gltf);
    if (manifest) await av._loadMotion(manifest, clips);
    return av;
  }

  _init(gltf) {
    this.root = new THREE.Group();
    this.root.name = 'avatar';
    this.root.add(gltf.scene);
    this.meshes = {};
    let skel = null;
    gltf.scene.traverse(o => {
      if (o.isSkinnedMesh) { this.meshes[o.name] = o; o.frustumCulled = false; skel = o.skeleton; }
      // the alpha-tested hair shell: alpha to coverage in MSAA targets softens its hard card edges (not on the sparse
      // fur shells hair_shell1/2, where it dithers their cut edge over the fringe into a dotted light line)
      if (o.isMesh && o.name === 'hair' && o.material.alphaTest > 0) o.material.alphaToCoverage = true;
    });
    this.skeleton = skel;
    this.bones = skel.bones;
    this.B = this.bones.length;
    this.index = {};
    this.bones.forEach((b, i) => { this.index[b.name] = i; });
    this.rootBone = this.bones[this.index.root];
    this.restQ = new Float32Array(4 * this.B);
    this.bones.forEach((b, i) => b.quaternion.toArray(this.restQ, 4 * i));
    this.restRoot = this.rootBone.position.toArray();
    // rest world frames (for bone-local axes of the procedural layers and the facing direction)
    gltf.scene.updateMatrixWorld(true);
    this.restWorldQ = this.bones.map(b => b.getWorldQuaternion(new THREE.Quaternion()).toArray());
    this.origMat = {};
    for (const [n, m] of Object.entries(this.meshes)) this.origMat[n] = m.material;
    this.clips = {};
    this.clipNames = [];
    this.fps = 30;
    // bone-local axis that corresponds to a world axis in the rest pose
    this._restAxis = (i, v) => qrot(qconj(this.restWorldQ[i]), v);
    const need = n => { const i = this.index[strip(n)]; if (i === undefined) throw new Error('bone ' + n); return i; };
    this._i = need;
    const L = (n, w) => [need(n), this._restAxis(need(n), w)];
    // procedural rig tables (indices + bone-local axes, computed once from the rest pose)
    this._breath = [
      [...L('spine03', [1, 0, 0]), -0.35], [...L('spine02', [1, 0, 0]), -0.6], [...L('spine01', [1, 0, 0]), -0.5],
      [...L('neck01', [1, 0, 0]), 0.9], [...L('clavicle.L', [0, 0, 1]), 1.0], [...L('clavicle.R', [0, 0, 1]), -1.0],
    ];
    this._noise = [
      [...L('spine04', [0, 1, 0]), 0.9, 11], [...L('spine03', [1, 0, 0]), 0.6, 12], [...L('spine03', [0, 0, 1]), 0.5, 13],
      [...L('neck02', [0, 1, 0]), 1.4, 21], [...L('neck02', [1, 0, 0]), 1.0, 22], [...L('head', [0, 0, 1]), 0.8, 23],
      [...L('upperarm01.L', [1, 0, 0]), 1.2, 31], [...L('upperarm01.R', [1, 0, 0]), 1.2, 32],
      [...L('lowerarm01.L', [1, 0, 0]), 1.0, 33], [...L('lowerarm01.R', [1, 0, 0]), 1.0, 34],
    ];
    // fingers: flexion about the axis perpendicular to the finger and the palm normal (from rest geometry)
    this._fingers = [];
    for (const s of ['L', 'R']) {
      const wp = this._restHead(need('wrist.' + s));
      const idx = this._restHead(need('finger2-1.' + s)), pky = this._restHead(need('finger5-1.' + s));
      const across = norm(sub(idx, pky));                     // pinky -> index
      const along = norm(sub(mid(idx, pky), wp));              // wrist -> knuckles
      // palm normal from handedness: left hand along x across, right hand across x along (see LOOKDEV.md)
      const palm = s === 'L' ? norm(cross(along, across)) : norm(cross(across, along));
      for (let f = 1; f <= 5; f++) {
        for (let k = 1; k <= 3; k++) {
          const i = this.index[strip(`finger${f}-${k}.${s}`)];
          if (i === undefined) continue;
          const dir = norm(sub(this._restTail(i), this._restHead(i)));
          const axisW = norm(cross(dir, palm));                // rotating +angle about this curls toward the palm
          const deg = f === 1 ? [10, 12, 10][k - 1] : [18, 26, 14][k - 1] * (1 + 0.12 * (f - 2));
          this._fingers.push([i, this._restAxis(i, axisW), deg]);
        }
      }
    }
    // head / eye data for look-at
    this._neckChain = [['neck01', 0.12], ['neck02', 0.18], ['neck03', 0.2], ['head', 0.5]].map(([n, w]) => [need(n), w]);
    this._head = need('head');
    this._eyes = [need('eye.L'), need('eye.R')];
    this._fwdLocal = i => qrot(qconj(this.restWorldQ[i]), [0, 0, 1]);
  }

  _restHead(i) { const v = new THREE.Vector3(); this.bones[i].getWorldPosition(v); return v.toArray(); }
  _restTail(i) {   // first child's head, or along +Y
    const c = this.bones[i].children.find(o => o.isBone);
    if (c) { const v = new THREE.Vector3(); c.getWorldPosition(v); return v.toArray(); }
    const h = this._restHead(i), y = qrot(this.restWorldQ[i], [0, 0.02, 0]);
    return [h[0] + y[0], h[1] + y[1], h[2] + y[2]];
  }

  async _loadMotion(manifestUrl, only) {
    const man = await (await fetch(manifestUrl)).json();
    this.manifest = man;
    this.fps = man.fps;
    const base = new URL('.', new URL(manifestUrl, location.href)).href;
    const want = only ? new Set(only) : null;
    await Promise.all(man.clips.filter(c => !want || want.has(c.name)).map(async c => {
      const buf = await (await fetch(base + c.file)).arrayBuffer();
      const data = new Float32Array(buf);
      const map = c.bones.map(n => { const i = this.index[strip(n)]; if (i === undefined) throw new Error('clip bone ' + n); return i; });
      const stride = 3 + 4 * map.length;
      if (data.length !== stride * c.frames) throw new Error(`clip ${c.name}: size mismatch`);
      const delta = c.loop_info ? c.loop_info.cycle_root_delta : [0, 0, 0];
      this.clips[c.name] = { ...c, data, map, stride, N: c.frames, delta };
    }));
    this.clipNames = Object.keys(this.clips).sort();
  }

  clip(name) { const c = this.clips[name]; if (!c) throw new Error('no clip ' + name); return c; }

  restPose() { return { root: Float32Array.from(this.restRoot), q: Float32Array.from(this.restQ) }; }

  // ---------------------------------------------------------------------------------------------- sampling
  pose(name, t, opts = {}) {
    const c = this.clip(name);
    const loop = opts.loop ?? c.loop;
    const speed = opts.speed ?? 1;
    const rootMotion = opts.rootMotion ?? true;
    const N = c.N, fps = this.fps;
    let u = t * speed * fps, cycle = 0, f0, f1, a;
    if (loop) {
      cycle = Math.floor(u / N);
      u -= cycle * N;
      f0 = Math.floor(u); a = u - f0; f1 = f0 + 1;
    } else {
      u = Math.min(Math.max(u, 0), N - 1);
      f0 = Math.min(Math.floor(u), N - 2); a = u - f0; f1 = f0 + 1;
      if (N === 1) { f0 = f1 = 0; a = 0; }
    }
    const wrap = loop && f1 >= N;           // interpolating into the next cycle's first frame
    const g1 = wrap ? 0 : f1;
    const d = c.data, s = c.stride, o0 = f0 * s, o1 = g1 * s;
    const out = this.restPose();
    const dx = wrap ? c.delta[0] : 0, dz = wrap ? c.delta[2] : 0;
    out.root[0] = d[o0] + (d[o1] + dx - d[o0]) * a + cycle * c.delta[0];
    out.root[1] = d[o0 + 1] + (d[o1 + 1] - d[o0 + 1]) * a;
    out.root[2] = d[o0 + 2] + (d[o1 + 2] + dz - d[o0 + 2]) * a + cycle * c.delta[2];
    const qa = [0, 0, 0, 1], qb = [0, 0, 0, 1];
    for (let k = 0; k < c.map.length; k++) {
      const p0 = o0 + 3 + 4 * k, p1 = o1 + 3 + 4 * k;
      qa[0] = d[p0]; qa[1] = d[p0 + 1]; qa[2] = d[p0 + 2]; qa[3] = d[p0 + 3];
      qb[0] = d[p1]; qb[1] = d[p1 + 1]; qb[2] = d[p1 + 2]; qb[3] = d[p1 + 3];
      qslerp(out.q, 4 * c.map[k], qa, qb, a);
    }
    if (rootMotion === false || rootMotion === 'lock') { out.root[0] = 0; out.root[2] = 0; }
    if (rootMotion === 'lock') {
      const y0 = this.heading(this._frame0(c)), y = this.heading(out);
      this._rotateRoot(out, -(y - y0));
    }
    if (opts.place) this.placePose(out, opts.place);
    return out;
  }

  _frame0(c) {
    if (!c._f0) {
      const p = this.restPose(), d = c.data;
      p.root.set(d.subarray(0, 3));
      for (let k = 0; k < c.map.length; k++) p.q.set(d.subarray(3 + 4 * k, 7 + 4 * k), 4 * c.map[k]);
      c._f0 = p;   // cached constant derived from the data (not render state)
    }
    return c._f0;
  }

  _rotateRoot(p, yaw) {
    const r = this.index.root, q = qmul(qyaw(yaw), get4(p.q, r));
    p.q.set(q, 4 * r);
    const [x, , z] = qrot(qyaw(yaw), [p.root[0], 0, p.root[2]]);
    p.root[0] = x; p.root[2] = z;
  }

  placePose(p, { x = 0, z = 0, yaw = 0 } = {}) {
    if (yaw) this._rotateRoot(p, yaw);
    p.root[0] += x; p.root[2] += z;
    return p;
  }

  heading(p) {   // facing yaw of a pose: root rotation relative to rest, applied to +Z, projected on the ground
    const r = this.index.root;
    const rel = qmul(get4(p.q, r), qconj(get4(this.restQ, r)));
    const f = qrot(rel, [0, 0, 1]);
    return Math.atan2(f[0], f[2]);
  }

  mix(pA, pB, w) {
    if (w <= 0) return pA;
    if (w >= 1) return pB;
    const out = { root: new Float32Array(3), q: new Float32Array(4 * this.B) };
    for (let i = 0; i < 3; i++) out.root[i] = pA.root[i] + (pB.root[i] - pA.root[i]) * w;
    for (let i = 0; i < this.B; i++) qslerp(out.q, 4 * i, get4(pA.q, i), get4(pB.q, i), w);
    return out;
  }

  crossfade(pA, pB, t, t0, dur) { return this.mix(pA, pB, smoothstep(t0, t0 + dur, t)); }

  beatSpeed(name, bpm, beatsPerStep = 1) {
    const sp = this.clip(name).loop_info?.step_period_s;
    if (!sp) throw new Error(name + ' has no step period');
    return sp / (beatsPerStep * 60 / bpm);
  }

  sequence(segments, place = {}) {
    const segs = segments.map(s => ({ from: 0, speed: 1, fade: 0.6, rootMotion: true, ...s }));
    segs.sort((a, b) => a.at - b.at);
    const local = (s, T) => this.pose(s.clip, s.from + (T - s.at) * s.speed, { loop: s.loop, rootMotion: s.rootMotion });
    // placements: segment 0 from `place`, each next one continues the previous at its start time
    segs.forEach((s, i) => {
      if (i === 0) { s.place = { x: 0, z: 0, yaw: 0, ...place }; return; }
      const prev = this.placePose(local(segs[i - 1], s.at), segs[i - 1].place);
      const cur = local(s, s.at);
      const yaw = this.heading(prev) - this.heading(cur);
      const [rx, , rz] = qrot(qyaw(yaw), [cur.root[0], 0, cur.root[2]]);
      s.place = { x: prev.root[0] - rx, z: prev.root[2] - rz, yaw };
    });
    const at = T => {
      let i = 0;
      while (i + 1 < segs.length && segs[i + 1].at <= T) i++;
      const s = segs[i];
      const p = this.placePose(local(s, T), s.place);
      if (i > 0 && T < s.at + s.fade) {
        const q = segs[i - 1];
        return this.mix(this.placePose(local(q, T), q.place), p, smoothstep(s.at, s.at + s.fade, T));
      }
      return p;
    };
    return { segments: segs, pose: at, heading: T => this.heading(at(T)) };
  }

  // ---------------------------------------------------------------------------------------------- skeleton write
  apply(pose, layers = {}, t = 0) {
    const B = this.B, q = pose.q;
    for (let i = 0; i < B; i++) this.bones[i].quaternion.set(q[4 * i], q[4 * i + 1], q[4 * i + 2], q[4 * i + 3]);
    this.rootBone.position.set(pose.root[0], pose.root[1], pose.root[2]);
    const rotLocal = (i, axis, deg) => {   // post-multiply a bone-local axis rotation
      if (!deg) return;
      _q.setFromAxisAngle(_v.set(axis[0], axis[1], axis[2]), deg * Math.PI / 180);
      this.bones[i].quaternion.multiply(_q);
    };
    if (layers.hands !== undefined && layers.hands !== false) {
      const curl = layers.hands.curl ?? 0.55;
      for (const [i, ax, deg] of this._fingers) rotLocal(i, ax, deg * curl);
    }
    if (layers.breath) {
      const { amp = 1, period = 4.4, phase = 0 } = layers.breath;
      const x = ((t / period + phase) % 1 + 1) % 1;
      // inhale 40 % of the cycle, exhale 60 %, both eased
      const b = x < 0.4 ? 0.5 - 0.5 * Math.cos(Math.PI * x / 0.4) : 0.5 + 0.5 * Math.cos(Math.PI * (x - 0.4) / 0.6);
      for (const [i, ax, deg] of this._breath) rotLocal(i, ax, deg * 1.5 * amp * b);
    }
    if (layers.noise) {
      const { amp = 1, seed = 0 } = layers.noise;
      for (const [i, ax, deg, ch] of this._noise) rotLocal(i, ax, deg * amp * fbm(t * 0.23 + ch * 7.3, seed * 97 + ch));
    }
    this.root.updateMatrixWorld(true);
    if (layers.look && layers.look.target) this._lookAt(layers.look);
    return this;
  }

  _lookAt({ target, weight = 1, eyes = true, maxDeg = 70 }) {
    const tgt = target.isVector3 ? target : _v2.fromArray(target);
    const head = this.bones[this._head];
    const hq = head.getWorldQuaternion(new THREE.Quaternion());
    const eye = this.headAnchor(new THREE.Vector3());
    const fwd = new THREE.Vector3(...this._fwdLocal(this._head)).applyQuaternion(hq).normalize();
    const want = tgt.clone().sub(eye).normalize();
    const full = new THREE.Quaternion().setFromUnitVectors(fwd, want);
    let ang = 2 * Math.acos(Math.min(1, Math.abs(full.w)));
    const lim = maxDeg * Math.PI / 180;
    const scale = weight * (ang > lim ? lim / ang : 1);
    const I = new THREE.Quaternion();
    for (const [i, w] of this._neckChain) {
      const part = I.clone().slerp(full, w * scale);
      const b = this.bones[i];
      const pq = b.parent.getWorldQuaternion(new THREE.Quaternion());
      // world rotation `part` applied to bone i: local' = parent^-1 * part * parent * local
      b.quaternion.premultiply(pq.clone().invert().multiply(part).multiply(pq));
      b.updateMatrixWorld(true);
    }
    if (eyes) {
      for (const i of this._eyes) {
        const b = this.bones[i];
        const bq = b.getWorldQuaternion(new THREE.Quaternion());
        const p = b.getWorldPosition(new THREE.Vector3());
        const f = new THREE.Vector3(...this._fwdLocal(i)).applyQuaternion(bq).normalize();
        const d = tgt.clone().sub(p).normalize();
        const r = new THREE.Quaternion().setFromUnitVectors(f, d);
        const a = 2 * Math.acos(Math.min(1, Math.abs(r.w))), lim2 = 22 * Math.PI / 180;
        const part = I.clone().slerp(r, weight * (a > lim2 ? lim2 / a : 1));
        const pq = b.parent.getWorldQuaternion(new THREE.Quaternion());
        b.quaternion.premultiply(pq.clone().invert().multiply(part).multiply(pq));
        b.updateMatrixWorld(true);
      }
    }
  }

  bone(name) { return this.bones[this._i(name)]; }
  worldPos(name, target = new THREE.Vector3()) { return this.bone(name).getWorldPosition(target); }
  headAnchor(target = new THREE.Vector3()) {
    const a = this.bones[this._eyes[0]].getWorldPosition(new THREE.Vector3());
    const b = this.bones[this._eyes[1]].getWorldPosition(new THREE.Vector3());
    return target.copy(a).add(b).multiplyScalar(0.5);
  }

  // ---------------------------------------------------------------------------------------------- looks
  setLook(look) {
    for (const [n, m] of Object.entries(this.meshes)) {
      const orig = this.origMat[n];
      if (look === 'photo' || !look) { m.material = orig; m.visible = true; continue; }
      if (typeof look === 'function') { m.material = look(m, orig) || orig; continue; }
      m.material = LOOKS[look](n, orig);
    }
    // teeth / tongue never show with a closed mouth; hide them in the derived looks (saves 7.6k triangles)
    for (const n of ['teeth', 'tongue']) if (this.meshes[n]) this.meshes[n].visible = look === 'photo' || !look;
    return this;
  }
}

const _q = new THREE.Quaternion(), _v = new THREE.Vector3(), _v2 = new THREE.Vector3();
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = a => { const n = Math.hypot(...a) || 1; return a.map(x => x / n); };

const _cache = {};
const cached = (k, f) => (_cache[k] ??= f());
export const LOOKS = {
  // flat grey previs: readable silhouette, hair and shoes a step darker so the head and feet read. Alpha-carrying
  // parts (fringe strands, fur shells, brows, lashes) keep the original texture for its alpha channel.
  clay: (n, o) => cached('clay:' + n, () => {
    const m = new THREE.MeshLambertMaterial({
      color: /hair|brow|lash/.test(n) ? 0x6a6a6a : /eyes/.test(n) ? 0xb4b4b4 : /shoes/.test(n) ? 0x2a2a2a : /trousers/.test(n) ? 0x6a6a6a : /top|button/.test(n) ? 0x7c7c7c : 0xa8a8a8,
      map: ALPHA.test(n) || /eyes/.test(n) ? o.map : null, alphaTest: ALPHA.test(n) ? (o.alphaTest || 0.35) : 0, side: o.side,
    });
    // alpha parts: the map only cuts the shape (its alpha); the colour stays the flat clay grey, not the dark albedo
    if (ALPHA.test(n)) m.onBeforeCompile = sh => {
      sh.fragmentShader = sh.fragmentShader.replace('#include <map_fragment>',
        '#ifdef USE_MAP\n  diffuseColor.a *= texture2D( map, vMapUv ).a;\n#endif');
    };
    return m;
  }),
  silhouette: (n, o) => cached('sil:' + n, () => new THREE.MeshBasicMaterial({ color: 0x000000, map: ALPHA.test(n) ? o.map : null,
    alphaTest: ALPHA.test(n) ? (o.alphaTest || 0.35) : 0, side: o.side })),
  ghost: n => cached('ghost:' + n, () => new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true, transparent: true, opacity: 0.25 })),
};
const ALPHA = /^hair|brow|lash/;   // every hair part (shell cards are alpha-carved over the fringe), brows, lashes
