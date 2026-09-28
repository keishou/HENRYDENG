// tray.js - THE TRAY (BIBLE 4.8; lane C). Shots S01 S04 S09 S10 S20 S22 S24 S26 S32 S36-S39 S42 S47 S52 S53.
//
// A black ABS developing tray (inner 0.34 x 0.42 x 0.06 m, 8 mm wall, 15 mm corners) on a dark bench, a print 0.28 x 0.36
// lying on its floor (top at y 0.020) under 2 mm of developer (surface at y 0.022), a soft safelight rectangle 1.2 m above
// the liquid at upper left, and the tray lens: top-down perspective, FOV 16 deg vertical, 1.45 m above the print.
// Metres, Y up; screen up is -Z (so a print's top edge lies toward -Z). The tray group sits at the world origin.
//
// The liquid surface is one shader over the tray interior (the print is shaded inside it): per pixel it evaluates the
// liquid's closed-form height field (src/fx/liquid.js), looks through the surface to the bottom with the print's UV
// shifted by -grad(h) * refract, shades the print through its develop pass (src/fx/develop.js dvPrint) or the black
// floor, lights it with the safelight pool, multiplies the transmission 0.96, and adds the Fresnel reflection of the
// safelight rectangle. Everything is a pure function of t.
//
//   const tray = ctx.sets.tray            (scene needs: { sets: ['tray'] })
//   tray.scene, tray.camera               the set and the tray lens (16:9 view; the core's window masks it)
//   tray.liquid                           the Liquid (height / grad on the CPU, for accents that ride the refraction)
//   tray.update(t, opts)                  call first in every frame(); returns the api. opts:
//       print      a DevelopPass (develop(ctx, {...})) shown on the print | null (bare floor)
//       liquid     Liquid events (see liquid.js: rock, drops, surge, tilt, ring); default: still liquid
//       light      safelight level; default ctx.tl.env(t) -> base * (0.55 + 0.45 * env) (BIBLE 4.3: the voice is the light)
//       refract    apparent shift of the print per unit slope, metres (default 0.07)
//       caustic    light focused by the liquid, per unit of -laplacian(h) (default 0.045; clamped to -25 %..+30 %)
//       falling    [{ t, x, z, h = 0.45 }] drops falling onto the liquid (visible until they strike at t; add the same
//                  drop to liquid.drops for the rings)
//       tilt       [rx, rz] radians - tilt the whole tray group (S26); pass liquid.tilt = the opposite slope to keep it level
//       safelight  { x, z, w, d, soft, radiance, base, gain } overrides (tray-local metres; gain scales the surface tilt
//                  seen in the reflection)
//   tray.printUVToLocal(u, v) -> THREE.Vector3 (tray-local point on the print; world when the tray is not tilted)
//   tray.refracted(u, v, t) -> [u', v']   where the print point (u, v) APPEARS through the liquid (for 2D accents)
//   tray.project(p) -> { x, y }           a world point to design px (1920 x 1080) through tray.camera
//   tray.metresPerPx1080                  paper metres per output pixel at 1080p through the tray lens (halftone pitch)
//   tray.PRINT = { w: 0.28, h: 0.36, y: 0.020 }, tray.LIQUID_Y = 0.022
import * as THREE from 'three';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import { Liquid } from '../fx/liquid.js';
import { DEVELOP_GLSL, developUniforms } from '../fx/develop.js';

const INNER = { w: 0.34, d: 0.42, h: 0.06, wall: 0.008, r: 0.015 };
const FLOOR_Y = 0.0198, PRINT = { w: 0.28, h: 0.36, y: 0.020 }, LIQUID_Y = 0.022;
const LENS = { fov: 16, height: 1.45 };
const SAFE = { x: -0.215, z: -0.29, y: LIQUID_Y + 1.2, w: 0.15, d: 0.10, soft: 0.014, radiance: 9, base: 1.35, gain: 0.3 };

function roundedRect(w, d, r) {
  const s = new THREE.Shape(), x = w / 2, y = d / 2;
  s.moveTo(-x + r, -y); s.lineTo(x - r, -y); s.quadraticCurveTo(x, -y, x, -y + r); s.lineTo(x, y - r); s.quadraticCurveTo(x, y, x - r, y);
  s.lineTo(-x + r, y); s.quadraticCurveTo(-x, y, -x, y - r); s.lineTo(-x, -y + r); s.quadraticCurveTo(-x, -y, -x + r, -y);
  return s;
}

const VERT = /* glsl */`
varying vec3 vW; varying vec2 vL;
void main(){ vL = position.xz; vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;

const FRAG = /* glsl */`
uniform vec3 uCam;
uniform vec4 uPrint;          // print centre x, z (tray local), half w, half h
uniform float uHasPrint, uRefract, uLight, uTrans, uF0, uSafeL, uSafeSoft, uReflGain, uCaustic;
uniform vec3 uSafePos; uniform vec2 uSafeHalf;
uniform vec3 uFloor;
uniform vec3 uInner;          // inner half w, half d, corner radius
uniform mat3 uRot;            // tray group rotation (local -> world)
varying vec3 vW; varying vec2 vL;
float sdRound(vec2 p, vec2 b, float r){ vec2 q = abs(p) - b + r; return length(max(q, 0.)) + min(max(q.x, q.y), 0.) - r; }
void main(){
  if (sdRound(vL, uInner.xy, uInner.z) > 0.) discard;
  vec3 gl = lqGradLap(vL);
  vec2 g = gl.xy;
  vec3 nL = normalize(vec3(-g.x, 1., -g.y));
  vec3 n = normalize(uRot * nL);
  vec2 pb = vL - uRefract * g;                                   // the bottom point seen through the surface
  vec2 puv = vec2((pb.x - uPrint.x) / (2. * uPrint.z) + .5, .5 - (pb.y - uPrint.y) / (2. * uPrint.w));
  vec4 pr = dvPrint(clamp(puv, 0., 1.));
  vec2 e = min(puv, 1. - puv) * 2. * uPrint.zw;                 // metres inside the paper edge
  float aa = max(fwidth(puv.x) * 2. * uPrint.z, 1e-5);
  float inside = uHasPrint * smoothstep(-aa * .7, aa * .7, min(e.x, e.y));
  vec3 albedo = mix(uFloor, pr.rgb, inside);
  // the safelight pool: cos^3 falloff from its nadir (a soft overhead source)
  vec2 dl = vW.xz - uSafePos.xz; float hh = uSafePos.y - vW.y;
  float c3 = pow(hh / sqrt(hh * hh + dot(dl, dl)), 3.);
  // caustics: the liquid layer focuses the overhead light where the surface is convex (-laplacian h); faint for the
  // rocking swell, a ring of light and shade under a drop's ripples
  float caus = clamp(1. - uCaustic * gl.z, .75, 1.3);
  vec3 col = albedo * uLight * c3 * uTrans * caus;
  // Fresnel reflection of the safelight rectangle (the surface normal's tilt scaled by uReflGain: the real 1.5 mm swell
  // would swing the reflection ~4 cm; the rectangle has to stay a rectangle)
  vec3 nr = normalize(uRot * normalize(vec3(-g.x * uReflGain, 1., -g.y * uReflGain)));
  vec3 V = normalize(vW - uCam), R = reflect(V, nr);
  float m = 0.;
  if (R.y > 1e-3) {
    vec3 hit = vW + R * ((uSafePos.y - vW.y) / R.y);
    float sd = sdRound(hit.xz - uSafePos.xz, uSafeHalf, .012);
    m = 1. - smoothstep(-uSafeSoft, uSafeSoft, sd);
  }
  float ci = clamp(dot(-V, nr), 0., 1.);
  float F = uF0 + (1. - uF0) * pow(1. - ci, 5.);
  col += F * uSafeL * m;
  gl_FragColor = vec4(col, 1.);
}`;

const DROP_FRAG = /* glsl */`
uniform vec3 uCam, uSafePos; uniform vec2 uSafeHalf; uniform float uSafeL, uLight;
varying vec3 vN, vP;
void main(){
  vec3 n = normalize(vN), V = normalize(vP - uCam), R = reflect(V, n);
  float m = 0.;
  if (R.y > 1e-3) { vec3 hit = vP + R * ((uSafePos.y - vP.y) / R.y); vec2 d = abs(hit.xz - uSafePos.xz) - uSafeHalf; m = 1. - smoothstep(-.05, .05, max(d.x, d.y)); }
  float ci = clamp(dot(-V, n), 0., 1.);
  float F = .02 + .98 * pow(1. - ci, 5.);
  vec3 col = vec3(.55) * uLight * (1. - F) * (.6 + .4 * ci) + F * uSafeL * m * 1.6;
  gl_FragColor = vec4(col, 1.);
}`;

export default {
  name: 'tray',
  async init(ctx) {
    RectAreaLightUniformsLib.init();
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d0e0f).convertSRGBToLinear();
    const group = new THREE.Group(); scene.add(group);

    // bench + tray body (black ABS)
    const abs = new THREE.MeshStandardMaterial({ color: new THREE.Color('#0b0b0b'), roughness: 0.35, metalness: 0 });
    const bench = new THREE.Mesh(new THREE.PlaneGeometry(4, 3).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: new THREE.Color('#2a2b2d'), roughness: 0.9 }));
    bench.position.y = -0.0005; scene.add(bench);
    const outer = roundedRect(INNER.w + 2 * INNER.wall, INNER.d + 2 * INNER.wall, INNER.r + INNER.wall);
    const ring = outer.clone(); ring.holes = [roundedRect(INNER.w, INNER.d, INNER.r)];
    const walls = new THREE.Mesh(new THREE.ExtrudeGeometry(ring, { depth: INNER.h, bevelEnabled: true, bevelThickness: 0.002, bevelSize: 0.002, bevelSegments: 2, curveSegments: 10 }).rotateX(-Math.PI / 2).translate(0, FLOOR_Y, 0), abs);
    const base = new THREE.Mesh(new THREE.ExtrudeGeometry(outer, { depth: FLOOR_Y, bevelEnabled: false, curveSegments: 10 }).rotateX(-Math.PI / 2), abs);
    group.add(walls, base);

    // light: the safelight (a soft rectangle 1.2 m above the liquid) + a whisper of room light
    const safe = new THREE.RectAreaLight(0xffffff, 1, SAFE.w, SAFE.d);
    safe.position.set(SAFE.x, SAFE.y, SAFE.z); safe.lookAt(SAFE.x, 0, SAFE.z); scene.add(safe);
    const room = new THREE.HemisphereLight(0xffffff, 0x000000, 0.05); scene.add(room);

    // the liquid + print shader over the tray interior
    const liquid = new Liquid(ctx, { width: INNER.w, depth: INNER.d, corner: INNER.r });
    const trayU = {
      uCam: { value: new THREE.Vector3() }, uPrint: { value: new THREE.Vector4(0, 0, PRINT.w / 2, PRINT.h / 2) },
      uHasPrint: { value: 0 }, uRefract: { value: 0.07 }, uLight: { value: 1 }, uTrans: { value: 0.96 }, uF0: { value: 0.025 },
      uSafeL: { value: SAFE.radiance }, uSafeSoft: { value: SAFE.soft }, uReflGain: { value: SAFE.gain }, uCaustic: { value: 0.045 }, uSafePos: { value: new THREE.Vector3(SAFE.x, SAFE.y, SAFE.z) },
      uSafeHalf: { value: new THREE.Vector2(SAFE.w / 2, SAFE.d / 2) },
      uFloor: { value: new THREE.Vector3().setScalar(new THREE.Color('#0b0b0b').r * 0.9) },
      uInner: { value: new THREE.Vector3(INNER.w / 2, INNER.d / 2, INNER.r) },
      uRot: { value: new THREE.Matrix3() },
    };
    const mats = new Map();         // one liquid material per develop pass (its uniforms are the pass's own objects)
    const bare = { uniforms: {} };  // no print: the develop uniforms still have to exist
    const matFor = pass => {
      const k = pass ? pass.key : '-';
      if (!mats.has(k)) {
        const dvU = pass ? pass.uniforms : (bare.uniforms = bare.uniforms.dvSrc ? bare.uniforms : developUniforms());
        mats.set(k, new THREE.ShaderMaterial({ uniforms: { ...liquid.uniforms, ...dvU, ...trayU }, vertexShader: VERT,
          fragmentShader: liquid.glsl + DEVELOP_GLSL + FRAG, depthWrite: true }));
      }
      return mats.get(k);
    };
    const surf = new THREE.Mesh(new THREE.PlaneGeometry(INNER.w, INNER.d, 1, 1).rotateX(-Math.PI / 2), matFor(null));
    surf.position.y = LIQUID_Y; group.add(surf);

    // falling drops (S04): small lenses that catch the safelight
    const dropMat = new THREE.ShaderMaterial({ uniforms: { uCam: trayU.uCam, uSafePos: trayU.uSafePos, uSafeHalf: trayU.uSafeHalf, uSafeL: trayU.uSafeL, uLight: trayU.uLight },
      vertexShader: 'varying vec3 vN, vP; void main(){ vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix * vec4(position, 1.); vP = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
      fragmentShader: DROP_FRAG });
    const dropGeo = new THREE.SphereGeometry(0.0022, 16, 12); dropGeo.scale(1, 1.25, 1);
    const drops = Array.from({ length: 4 }, () => { const m = new THREE.Mesh(dropGeo, dropMat); m.visible = false; group.add(m); return m; });

    // the tray lens
    const camera = new THREE.PerspectiveCamera(LENS.fov, 16 / 9, 0.05, 20);
    camera.position.set(0, PRINT.y + LENS.height, 0); camera.up.set(0, 0, -1); camera.lookAt(0, PRINT.y, 0);
    camera.updateMatrixWorld();
    const metresPerPx1080 = 2 * LENS.height * Math.tan(LENS.fov / 2 * Math.PI / 180) / 1080;

    const api = {
      scene, camera, group, liquid, surf, safe, PRINT, LIQUID_Y, INNER, metresPerPx1080,
      printUVToLocal(u, v) { return new THREE.Vector3((u - 0.5) * PRINT.w, PRINT.y, -(v - 0.5) * PRINT.h); },
      // where the print point (u, v) appears through the liquid: solve p - refract * grad(p) = bottom (2 fixed-point steps)
      refracted(u, v, t) {
        const b = api.printUVToLocal(u, v); let x = b.x, z = b.z;
        for (let i = 0; i < 3; i++) { const g = liquid.grad(x, z, t); x = b.x + trayU.uRefract.value * g[0]; z = b.z + trayU.uRefract.value * g[1]; }
        return [x / PRINT.w + 0.5, 0.5 - z / PRINT.h];
      },
      project(p) {
        const v = p.clone().project(camera);
        return { x: (v.x + 1) / 2 * 1920, y: (1 - v.y) / 2 * 1080 };
      },
      update(t, o = {}) {
        const tl = ctx.tl;
        liquid.update(t, o.liquid || {});
        const sl = { ...SAFE, ...(o.safelight || {}) };
        const level = o.light ?? (sl.base * (0.55 + 0.45 * (tl ? tl.env(t) : 0)));
        trayU.uLight.value = level;
        trayU.uSafeL.value = sl.radiance * level;
        trayU.uSafePos.value.set(sl.x, sl.y, sl.z); trayU.uSafeHalf.value.set(sl.w / 2, sl.d / 2); trayU.uSafeSoft.value = sl.soft; trayU.uReflGain.value = sl.gain;
        safe.position.set(sl.x, sl.y, sl.z); safe.width = sl.w; safe.height = sl.d; safe.lookAt(sl.x, 0, sl.z);
        safe.intensity = 6 * level;
        trayU.uRefract.value = o.refract ?? 0.07; trayU.uCaustic.value = o.caustic ?? 0.045;
        const pass = o.print || null;
        surf.material = matFor(pass);
        trayU.uHasPrint.value = pass ? 1 : 0;
        // the walls, base and bench are outside a 7:9 window (the tray lens sees 0.317 m across it, the walls start at
        // 0.34): skip them there (they are the costly lit materials); any wider window or a tilt shows them
        const rect = ctx.frame && ctx.frame.rect, tilted = !!(o.tilt && (o.tilt[0] || o.tilt[1]));
        const seen = tilted || o.walls === true || !rect || rect.w / 1080 * metresPerPx1080 * 1080 / 2 > INNER.w / 2 - 0.004;
        walls.visible = base.visible = bench.visible = seen;
        group.rotation.set((o.tilt || [0, 0])[0], 0, (o.tilt || [0, 0])[1]);
        group.updateMatrixWorld(true);
        trayU.uRot.value.setFromMatrix4(group.matrixWorld);
        camera.updateMatrixWorld();
        trayU.uCam.value.copy(camera.position);
        // falling drops: y(t) = liquid + h - g/2 (t - (tStrike - T))^2, visible until the strike frame
        const fr = Math.round(t * 24);
        drops.forEach((m, i) => {
          const d = (o.falling || [])[i]; m.visible = false; if (!d) return;
          const h = d.h ?? 0.45, T = Math.sqrt(2 * h / 9.81), ts = Math.round(d.t * 24) / 24, t0 = ts - T;
          if (t < t0 || fr >= Math.round(d.t * 24)) return;
          const k = t - t0; m.position.set(d.x, LIQUID_Y + h - 0.5 * 9.81 * k * k, d.z); m.visible = true;
        });
        return api;
      },
    };
    return api;
  },
};
