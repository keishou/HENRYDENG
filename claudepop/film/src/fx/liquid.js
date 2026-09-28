// liquid.js - the developer in the tray (BIBLE 4.8 TRAY; lane C). A closed-form height field over the tray interior, so
// every frame is a pure function of t (BIBLE 9.2): nothing is simulated or carried between frames.
//
//   const liq = new Liquid(ctx, { width = 0.34, depth = 0.42, res = 1, corner = 0.015 })
//   liq.update(t, events)      sets the field for film time t (call first in every frame; unset events are cleared):
//     events = {
//       rock:  { amp = 0.0015 m, lambda = 0.3 m, period = 2 bars, t0 = 0.2356, dir = [0.26, 0.97] (unit, tray x/z),
//                amp2 = 0.4 (secondary train, relative), seiche = 0.0022 rad (whole-surface tilt swing),
//                enter = true (the train enters from the upstream edge at t0 instead of being everywhere at once),
//                boosts: [{ t, gain }] (the amplitude steps up on these times, eased over ~6 frames: S04 bass) } | null,
//       drops: [{ t, x, z, amp = 1 }]   up to 8 drop impacts (rings 0.25 m/s, decay 1.2 s; a crown for 3 frames),
//       surge: { t, dir = [0, 1], amp = 0.004, speed = 0.45, width = 0.05, from = upstream edge } | [...] (up to 3)
//              solitary waves (S09 FOOM; S04 the bass); `from` = where the crest is at t, as s = dot([x, z], dir)
//              (default: just upstream of the tray, so it enters from the edge)
//       tilt:  [sx, sz] | radians       a static surface slope in tray coordinates (S26: the tray tilts, the liquid stays level),
//       ring:  { t, x, z, amp = 0.003, speed = 0.35 } | null   one pressure ring (S20),
//     }
//   liq.height(x, z, t) -> metres above the rest level (tray coordinates: x across, z along; the tray centre is 0, 0)
//   liq.grad(x, z, t) -> [dh/dx, dh/dz]     (both use the events of the last update(); t may differ from update's t)
//   liq.glsl                     GLSL chunk: uniforms + float lqH(vec2 p), vec2 lqGrad(vec2 p), vec3 lqGradLap(vec2 p)
//                                (gradient + laplacian from 5 samples; uLqT = the update t)
//   liq.uniforms                 the uniform objects the chunk reads (merge into your ShaderMaterial's uniforms)
//   liq.mesh                     a flat plane of the tray interior at local y 0 (its material is the owner's: tray.js
//                                replaces it with the refraction + Fresnel shader; the default is invisible)
//
// Shading contract (tray.js): print UV refracted by -grad(h) * refract, Fresnel reflection of the safelight rectangle,
// transmission 0.96. The same numbers drive the CPU copy (height/grad), so a VOICE catchlight drawn in 2D rides the same
// refraction as the print under it.
import * as THREE from 'three';

const TAU = Math.PI * 2;
const BAR = 4 * 0.454545;                 // song.json beat_period x 4 (132 BPM)
const MAXD = 8;
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

export class Liquid {
  constructor(ctx, { width = 0.34, depth = 0.42, res = 1, corner = 0.015 } = {}) {
    this.ctx = ctx; this.width = width; this.depth = depth; this.corner = corner;
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, depth, res, res).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.0, depthWrite: false }));
    this.uniforms = {
      uLqT: { value: 0 },
      uLqRock: { value: new THREE.Vector4() },        // amp, lambda, period, t0
      uLqRock2: { value: new THREE.Vector4() },       // amp2 (abs), seiche (rad), enter (0/1), upstream s0
      uLqDir: { value: new THREE.Vector2(0, 1) },
      uLqDrops: { value: Array.from({ length: MAXD }, () => new THREE.Vector4(-1e3, 0, 0, 0)) },   // t, x, z, amp
      uLqNDrops: { value: 0 },
      uLqSurge: { value: Array.from({ length: 3 }, () => new THREE.Vector4(-1e3, 0, 0.45, 0.05)) },   // t, amp, speed, width
      uLqSurgeDir: { value: Array.from({ length: 3 }, () => new THREE.Vector3(0, 1, 0)) },           // dir x, z, start s0
      uLqTilt: { value: new THREE.Vector2() },
      uLqRing: { value: new THREE.Vector4(-1e3, 0, 0, 0) },          // t, x, z, amp
      uLqRingSpeed: { value: 0.35 },
      uLqLocal: { value: 0 },                          // any drop / surge / ring active at uLqT (else skip their samples)
    };
    this.ev = this._norm({});
    this.glsl = GLSL;
  }

  _norm(e) {
    const r = e.rock ? { amp: 0.0015, lambda: 0.3, period: 2 * BAR, t0: 0.2356, dir: [0.26, 0.97], amp2: 0.4, seiche: 0.0022, enter: true, boosts: [], ...e.rock } : null;
    if (r) { const l = Math.hypot(r.dir[0], r.dir[1]) || 1; r.dir = [r.dir[0] / l, r.dir[1] / l]; }
    const drops = (e.drops || []).slice(0, MAXD).map(d => ({ amp: 1, ...d }));
    const surges = (Array.isArray(e.surge) ? e.surge : e.surge ? [e.surge] : []).slice(0, 3).map(x => {
      const S = { dir: [0, 1], amp: 0.004, speed: 0.45, width: 0.05, ...x }, l = Math.hypot(S.dir[0], S.dir[1]) || 1;
      S.dir = [S.dir[0] / l, S.dir[1] / l]; S.s0 = S.from ?? (this._upstream(S.dir) - S.width * 2); return S;
    });
    const tilt = Array.isArray(e.tilt) ? e.tilt : typeof e.tilt === 'number' ? [0, Math.tan(e.tilt)] : [0, 0];
    const ring = e.ring ? { amp: 0.003, speed: 0.35, ...e.ring } : null;
    return { rock: r, drops, surges, tilt, ring };
  }

  // the rocking amplitude at t (boosts step it up, eased over ~6 frames, the step visible on its own frame)
  _rockAmp(r, t) {
    let a = r.amp;
    for (const b of r.boosts || []) {
      const df = Math.round(t * 24) - Math.round(b.t * 24);
      if (df >= 0) a *= 1 + (b.gain - 1) * (1 - 0.55 * Math.exp(-df / 2.2));
    }
    return a;
  }

  update(t, events = {}) {
    const u = this.uniforms, e = this.ev = this._norm(events);
    this.t = t;
    u.uLqT.value = t;
    if (e.rock) {
      const r = e.rock, s0 = this._upstream(r.dir);
      u.uLqRock.value.set(this._rockAmp(r, t), r.lambda, r.period, r.t0);
      u.uLqRock2.value.set(r.amp2, r.seiche * u.uLqRock.value.x / r.amp, r.enter ? 1 : 0, s0);
      u.uLqDir.value.set(r.dir[0], r.dir[1]);
    } else { u.uLqRock.value.set(0, 0.3, 1, 0); u.uLqRock2.value.set(0, 0, 0, 0); }
    u.uLqNDrops.value = e.drops.length;
    for (let i = 0; i < MAXD; i++) { const d = e.drops[i]; u.uLqDrops.value[i].set(d ? d.t : -1e3, d ? d.x : 0, d ? d.z : 0, d ? d.amp : 0); }
    for (let i = 0; i < 3; i++) {
      const S = e.surges[i];
      if (S) { u.uLqSurge.value[i].set(S.t, S.amp, S.speed, S.width); u.uLqSurgeDir.value[i].set(S.dir[0], S.dir[1], S.s0); }
      else u.uLqSurge.value[i].set(-1e3, 0, 0.45, 0.05);
    }
    u.uLqTilt.value.set(e.tilt[0], e.tilt[1]);
    if (e.ring) { u.uLqRing.value.set(e.ring.t, e.ring.x, e.ring.z, e.ring.amp); u.uLqRingSpeed.value = e.ring.speed; }
    else u.uLqRing.value.set(-1e3, 0, 0, 0);
    this.rockAmpNow = e.rock ? u.uLqRock.value.x : 0;
    u.uLqLocal.value = (e.drops.some(d => t >= d.t && t - d.t <= 4) || e.surges.some(S => t >= S.t && t - S.t < 4) ||
      (e.ring && t >= e.ring.t && t - e.ring.t < 3)) ? 1 : 0;
    return this;
  }

  _upstream(dir) {   // the most upstream s = dot(p, dir) over the tray interior (the rocking train enters there)
    return -(Math.abs(dir[0]) * this.width / 2 + Math.abs(dir[1]) * this.depth / 2);
  }

  // closed form; mirrors lqH() in the GLSL below term for term
  height(x, z, t = this.t) {
    const e = this.ev; let h = 0;
    if (e.rock) {
      const r = e.rock, A = this._rockAmp(r, this.t ?? t), tt = t - r.t0;
      if (tt > 0) {
        const s = x * r.dir[0] + z * r.dir[1];
        const s0 = this._upstream(r.dir), c = r.lambda / r.period;
        const front = r.enter ? smooth(-0.06, 0.02, s0 + c * tt * 1.6 + 0.02 - s) : 1;
        const on = smooth(0, 0.5, tt);
        h += A * on * front * Math.sin(TAU * (s / r.lambda - tt / r.period));
        const s2 = x * (-r.dir[1] * 0.55 + r.dir[0] * 0.45) + z * (r.dir[0] * 0.55 + r.dir[1] * 0.45);
        h += A * r.amp2 * on * front * Math.sin(TAU * (s2 / (r.lambda * 0.73) - tt / (r.period * 0.81)) + 1.3);
        const sw = r.seiche * (A / r.amp) * on * Math.sin(TAU * tt / r.period + 0.4);
        h += sw * (x * 0.6 + z * 0.8);
      }
    }
    for (const d of e.drops) {
      const tt = t - d.t; if (tt < 0 || tt > 4) continue;
      const rr = Math.hypot(x - d.x, z - d.z);
      h += d.amp * dropH(rr, tt);
    }
    for (const S of e.surges) {
      const tt = t - S.t;
      if (tt >= 0 && tt < 4) {
        const s = x * S.dir[0] + z * S.dir[1];
        const u = (s - (S.s0 + S.speed * tt)) / S.width, ch = Math.cosh(Math.min(20, Math.abs(u)));
        h += S.amp / (ch * ch) * Math.exp(-tt / 2.5);
      }
    }
    h += e.tilt[0] * x + e.tilt[1] * z;
    if (e.ring) {
      const R = e.ring, tt = t - R.t;
      if (tt >= 0 && tt < 3) { const rr = Math.hypot(x - R.x, z - R.z), u = (rr - R.speed * tt) / 0.018; h += R.amp * Math.exp(-tt / 0.8) * Math.exp(-u * u) * (1 - 0.6 * u); }
    }
    return h;
  }
  grad(x, z, t = this.t) {
    const e = 0.0007;
    return [(this.height(x + e, z, t) - this.height(x - e, z, t)) / (2 * e), (this.height(x, z + e, t) - this.height(x, z - e, t)) / (2 * e)];
  }
}

// a drop: a crown for ~3 frames, then a packet of capillary rings leaving at 0.25 m/s, decaying over 1.2 s
function dropH(r, tt) {
  const c = 0.25, rf = c * tt;
  const sig = 0.009 + 0.024 * tt, lam = 0.015 + 0.016 * tt;
  const u = r - rf;
  const spread = 1 / Math.sqrt(1 + r / 0.012);
  let h = 0.0022 * Math.exp(-tt / 1.2) * spread * Math.exp(-(u * u) / (2 * sig * sig)) * Math.cos(TAU * u / lam) * (u < 0 ? 1 : Math.exp(-u / 0.01));
  const crown = Math.exp(-tt / 0.06);
  h += 0.0018 * crown * Math.exp(-(r * r) / (0.0045 * 0.0045)) * Math.cos(TAU * tt / 0.14);
  return h;
}

const GLSL = /* glsl */`
#define LQ_TAU 6.28318530718
uniform float uLqT;
uniform vec4 uLqRock, uLqRock2;
uniform vec2 uLqDir;
uniform vec4 uLqDrops[8];
uniform int uLqNDrops;
uniform vec4 uLqSurge[3];
uniform vec3 uLqSurgeDir[3];
uniform vec2 uLqTilt;
uniform vec4 uLqRing;
uniform float uLqRingSpeed;
uniform float uLqLocal;
float lqSmooth(float a, float b, float x){ float t = clamp((x - a) / (b - a), 0., 1.); return t * t * (3. - 2. * t); }
float lqDrop(float r, float tt){
  float rf = .25 * tt, sig = .009 + .024 * tt, lam = .015 + .016 * tt, u = r - rf;
  float spread = inversesqrt(1. + r / .012);
  float h = .0022 * exp(-tt / 1.2) * spread * exp(-(u * u) / (2. * sig * sig)) * cos(LQ_TAU * u / lam) * (u < 0. ? 1. : exp(-u / .01));
  h += .0018 * exp(-tt / .06) * exp(-(r * r) / (.0045 * .0045)) * cos(LQ_TAU * tt / .14);
  return h;
}
float lqHLocal(vec2 p);
float lqH(vec2 p){
  float h = 0.;
  float A = uLqRock.x, tt = uLqT - uLqRock.w;
  if (A > 0. && tt > 0.) {
    float lam = uLqRock.y, per = uLqRock.z;
    float s = dot(p, uLqDir), c = lam / per;
    float front = uLqRock2.z > .5 ? lqSmooth(-.06, .02, uLqRock2.w + c * tt * 1.6 + .02 - s) : 1.;
    float on = lqSmooth(0., .5, tt);
    h += A * on * front * sin(LQ_TAU * (s / lam - tt / per));
    float s2 = p.x * (-uLqDir.y * .55 + uLqDir.x * .45) + p.y * (uLqDir.x * .55 + uLqDir.y * .45);
    h += A * uLqRock2.x * on * front * sin(LQ_TAU * (s2 / (lam * .73) - tt / (per * .81)) + 1.3);
    h += uLqRock2.y * on * sin(LQ_TAU * tt / per + .4) * dot(p, vec2(.6, .8));
  }
  return h + dot(uLqTilt, p) + lqHLocal(p);
}
// drops, surges and the pressure ring (the local, short-lived part of the field)
float lqHLocal(vec2 p){
  float h = 0.;
  for (int i = 0; i < 8; i++) {
    if (i >= uLqNDrops) break;
    vec4 d = uLqDrops[i]; float dt = uLqT - d.x;
    if (dt < 0. || dt > 4.) continue;
    h += d.w * lqDrop(length(p - d.yz), dt);
  }
  for (int i = 0; i < 3; i++) {
    vec4 S = uLqSurge[i]; float st = uLqT - S.x;
    if (S.y <= 0. || st < 0. || st >= 4.) continue;
    float u = (dot(p, uLqSurgeDir[i].xy) - (uLqSurgeDir[i].z + S.z * st)) / S.w;
    float ch = cosh(min(20., abs(u)));
    h += S.y / (ch * ch) * exp(-st / 2.5);
  }
  float rt = uLqT - uLqRing.x;
  if (uLqRing.w > 0. && rt >= 0. && rt < 3.) {
    float u = (length(p - uLqRing.yz) - uLqRingSpeed * rt) / .018;
    h += uLqRing.w * exp(-rt / .8) * exp(-u * u) * (1. - .6 * u);
  }
  return h;
}
vec2 lqGrad(vec2 p){
  const float e = .0007;
  return vec2(lqH(p + vec2(e, 0.)) - lqH(p - vec2(e, 0.)), lqH(p + vec2(0., e)) - lqH(p - vec2(0., e))) / (2. * e);
}
// gradient and laplacian: closed form for the rocking swell, seiche and tilt; five samples of the local part only
// while a drop, surge or ring is live
vec3 lqGradLap(vec2 p){
  vec3 r = vec3(uLqTilt, 0.);
  float A = uLqRock.x, tt = uLqT - uLqRock.w;
  if (A > 0. && tt > 0.) {
    float lam = uLqRock.y, per = uLqRock.z, s = dot(p, uLqDir), c = lam / per;
    float fx = clamp((uLqRock2.w + c * tt * 1.6 + .02 - s + .06) / .08, 0., 1.);
    float front = uLqRock2.z > .5 ? fx * fx * (3. - 2. * fx) : 1.;
    float dfront = uLqRock2.z > .5 ? -6. * fx * (1. - fx) / .08 : 0.;
    float on = lqSmooth(0., .5, tt), k1 = LQ_TAU / lam, k2 = LQ_TAU / (lam * .73);
    vec2 d2 = vec2(-uLqDir.y * .55 + uLqDir.x * .45, uLqDir.x * .55 + uLqDir.y * .45);
    float p1 = LQ_TAU * (s / lam - tt / per), p2 = LQ_TAU * (dot(p, d2) / (lam * .73) - tt / (per * .81)) + 1.3;
    float s1 = sin(p1), c1 = cos(p1), s2 = sin(p2), c2 = cos(p2), A2 = A * uLqRock2.x;
    r.xy += on * (A * (dfront * s1 * uLqDir + front * c1 * k1 * uLqDir) + A2 * (dfront * s2 * uLqDir + front * c2 * k2 * d2));
    r.z -= on * front * (A * s1 * k1 * k1 + A2 * s2 * k2 * k2 * dot(d2, d2));
    r.xy += uLqRock2.y * on * sin(LQ_TAU * tt / per + .4) * vec2(.6, .8);
  }
  if (uLqLocal > .5) {
    const float e = .0007;
    float a = lqHLocal(p + vec2(e, 0.)), b = lqHLocal(p - vec2(e, 0.)), c = lqHLocal(p + vec2(0., e)), d = lqHLocal(p - vec2(0., e)), h = lqHLocal(p);
    r += vec3((a - b) / (2. * e), (c - d) / (2. * e), (a + b + c + d - 4. * h) / (e * e));
  }
  return r;
}
`;
