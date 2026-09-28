// tray.js - THE TRAY (BIBLE 4.8; lane C). Shots S01 S04 S09 S10 S20 S22 S24 S26 S32 S36-S39 S42 S47 S52 S53.
//
// A black ABS developing tray (inner 0.34 x 0.42 x 0.06 m, 8 mm wall, 15 mm corners) on a dark bench, a print 0.28 x 0.36
// lying on its floor (top at y 0.020) under 2 mm of developer (surface at y 0.022), a soft safelight rectangle 1.2 m above
// the liquid at upper left, and the tray lens: top-down perspective, FOV 16 deg vertical, 1.45 m above the print.
// Metres, Y up; screen up is -Z (so a print's top edge lies toward -Z). The PRINT is centred on the tray group's origin
// (under the lens); the tray itself lies off centre, the print pushed 6 mm from its lower right walls, so the 7:9 window
// sees that corner of the tray: the lip of the rim and the meniscus where the developer climbs the wall are the photograph's
// scale and its highlights. The print lies a fraction of a degree off square (PRINT.rot).
//
// The liquid surface is one shader over the tray interior (the print is shaded inside it): per pixel it evaluates the
// liquid's closed-form height field (src/fx/liquid.js) plus the meniscus at the walls, looks through the surface to the
// bottom with the print's UV shifted by the (compressed) slope, shades the print through its develop pass
// (src/fx/develop.js dvPrint) or the black floor, lights it with the safelight pool, multiplies the transmission 0.96,
// adds the Fresnel reflection of the dim room and of the safelight (a large soft rectangle whose image rides the swell).
// The walls have a cheap shader of their own (black ABS: a faint diffuse, the room's sheen, the safelight on the lip).
// Everything is a pure function of t. Pixels outside the frame's window are discarded (the window masks them anyway).
//
//   const tray = ctx.sets.tray            (scene needs: { sets: ['tray'] })
//   tray.scene, tray.camera               the set and the tray lens (16:9 view; the core's window masks it)
//   tray.liquid                           the Liquid (height / grad on the CPU, for accents that ride the refraction)
//   tray.update(t, opts)                  call first in every frame(); returns the api. opts:
//       print      a DevelopPass (develop(ctx, {...})) shown on the print | null (bare floor)
//       liquid     Liquid events (see liquid.js: rock, drops, surge, tilt, ring); default: still liquid
//       light      safelight level; default base * (0.55 + 0.45 * voiceLight(t)) (BIBLE 4.3: the voice is the light;
//                  src/fx/voice.js gates the intro's bleed, leads onsets by a frame and never steps on one frame)
//       refract    apparent shift of the print per unit slope of the swell, metres (default 0.07)
//       refractLocal  the same for drops / surges / the ring (default 0.02; their slopes are compressed, so a drop is a
//                  small lens, never a radial smear)
//       caustic    light focused by the liquid, per unit of -laplacian(h) (default 0.045; soft-limited to about +-35 %)
//       falling    [{ t, x, z, h = 0.45 }] drops falling onto the liquid (a small specular glint until they strike at t;
//                  add the same drop to liquid.drops for the rings)
//       tilt       [rx, rz] radians - tilt the whole tray group (S26); pass liquid.tilt = the opposite slope to keep it level
//       safelight  { x, z, w, d, soft, radiance, base, gain, pool } overrides (tray-local metres; gain scales the
//                  surface tilt seen in the reflection; pool 0..1 how much of the cos^3 falloff reaches the paper)
//       walls      true: always draw the walls (they are drawn whenever the window can see them)
//   tray.printUVToLocal(u, v) -> THREE.Vector3 (tray-local point on the print; world when the tray is not tilted)
//   tray.localToPrintUV(x, z) -> [u, v]
//   tray.refracted(u, v, t) -> [u', v']   where the print point (u, v) APPEARS through the liquid (for 2D accents)
//   tray.project(p) -> { x, y }           a world point to design px (1920 x 1080) through tray.camera
//   tray.metresPerPx1080                  paper metres per output pixel at 1080p through the tray lens (halftone pitch)
//   tray.PRINT = { w: 0.28, h: 0.36, y: 0.020, rot }, tray.LIQUID_Y = 0.022, tray.INNER (+ cx, cz: the interior centre)
import * as THREE from 'three';
import { RectAreaLightUniformsLib } from 'three/addons/lights/RectAreaLightUniformsLib.js';
import { mergeVertices } from 'three/addons/utils/BufferGeometryUtils.js';
import { Liquid } from '../fx/liquid.js';
import { DEVELOP_GLSL, developUniforms } from '../fx/develop.js';
import { voiceLight } from '../fx/voice.js';

// the interior's centre relative to the print: the print sits 5 mm from the right and the bottom (screen) walls
const INNER = { w: 0.34, d: 0.42, h: 0.06, wall: 0.008, r: 0.015, cx: -0.024, cz: -0.024 };
const FLOOR_Y = 0.0198, PRINT = { w: 0.28, h: 0.36, y: 0.020, rot: -0.006 }, LIQUID_Y = 0.022;
const LENS = { fov: 16, height: 1.45 };
// the safelight: its reflection in the liquid lies inside the print's upper left quarter (the mirror point of a light at
// (x, z) is ~0.55 (x, z) for the tray lens), large and soft; radiance tuned so it adds a veil, never a tab
const SAFE = { x: -0.142, z: -0.215, y: LIQUID_Y + 1.2, w: 0.15, d: 0.13, soft: 0.034, radiance: 11, base: 1.2, gain: 0.25, pool: 0.65 };
const ROOM = 0.42;      // the dim room the liquid and the walls reflect (radiance, x light level)

function roundedRect(w, d, r) {
  const s = new THREE.Shape(), x = w / 2, y = d / 2;
  s.moveTo(-x + r, -y); s.lineTo(x - r, -y); s.quadraticCurveTo(x, -y, x, -y + r); s.lineTo(x, y - r); s.quadraticCurveTo(x, y, x - r, y);
  s.lineTo(-x + r, y); s.quadraticCurveTo(-x, y, -x, y - r); s.lineTo(-x, -y + r); s.quadraticCurveTo(-x, -y, -x + r, -y);
  return s;
}

const VERT = /* glsl */`
varying vec3 vW; varying vec2 vL;
void main(){ vL = position.xz; vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;

// shared: the soft safelight rectangle as seen along a reflected ray (1 inside, soft falloff over `soft` at its plane)
const SAFE_GLSL = /* glsl */`
uniform vec3 uSafePos; uniform vec2 uSafeHalf; uniform float uSafeL, uSafeSoft, uLight, uRoom;
uniform vec4 uWinPx;
float sdRound(vec2 p, vec2 b, float r){ vec2 q = abs(p) - b + r; return length(max(q, 0.)) + min(max(q.x, q.y), 0.) - r; }
float safeSeen(vec3 P, vec3 R, float extraSoft){
  if (R.y <= 1e-3) return 0.;
  vec3 hit = P + R * ((uSafePos.y - P.y) / R.y);
  vec2 d = hit.xz - uSafePos.xz;
  float sd = sdRound(d, uSafeHalf, .05), s = uSafeSoft + extraSoft;
  float m = 1. - smoothstep(-s, s, sd);
  return m * (.8 + .2 * (1. - dot(d / uSafeHalf, d / uSafeHalf) * .5));     // a softbox: a touch brighter at its centre
}
void winClip(){ vec2 fc = gl_FragCoord.xy; if (fc.x < uWinPx.x || fc.y < uWinPx.y || fc.x > uWinPx.z || fc.y > uWinPx.w) discard; }`;

const FRAG = /* glsl */`
uniform vec3 uCam;
uniform vec4 uPrint;          // print centre x, z (tray local), half w, half h
uniform vec2 uPrintRot;       // cos, sin of the print's rotation
uniform float uHasPrint, uRefract, uRefractL, uTrans, uF0, uReflGain, uCaustic, uPool;
uniform vec3 uFloor;
uniform vec4 uInner;          // inner half w, half d, corner radius, meniscus height
uniform vec2 uInnerC;         // the interior's centre (tray local)
uniform mat3 uRot;            // tray group rotation (local -> world)
varying vec3 vW; varying vec2 vL;
void main(){
  winClip();
  vec2 pi = vL - uInnerC;
  float sd = sdRound(pi, uInner.xy, uInner.z);
  if (sd > 0.) discard;
  // the meniscus: the developer climbs the wall over ~2 mm (its slope points away from the wall)
  const float e = .0004;
  vec2 nOut = normalize(vec2(sdRound(pi + vec2(e, 0.), uInner.xy, uInner.z) - sdRound(pi - vec2(e, 0.), uInner.xy, uInner.z),
                             sdRound(pi + vec2(0., e), uInner.xy, uInner.z) - sdRound(pi - vec2(0., e), uInner.xy, uInner.z)) + 1e-9);
  float dW = -sd, men = exp(-dW / .0011);
  vec2 gMen = nOut * uInner.w / .0011 * men;
  vec3 gloc = lqBakedL(vL), gl = lqBakedS(vL) + gloc;          // the liquid's field, baked per frame at 1 mm
  vec2 gs = gl.xy - gloc.xy;                                     // the swell (+ tilt)
  vec2 gd = gloc.xy / (1. + length(gloc.xy) / .12);              // drops / surges, slopes compressed (a lens, not a smear)
  vec2 g = gs + gd;
  vec2 pb = vL - uRefract * gs - uRefractL * gd;                  // the bottom point seen through the surface
  vec2 pr = pb - uPrint.xy;
  pr = vec2(uPrintRot.x * pr.x + uPrintRot.y * pr.y, -uPrintRot.y * pr.x + uPrintRot.x * pr.y);   // into the print's frame
  vec2 puv = vec2(pr.x / (2. * uPrint.z) + .5, .5 - pr.y / (2. * uPrint.w));
  vec4 prc = dvPrint(clamp(puv, 0., 1.));
  vec2 ein = min(puv, 1. - puv) * 2. * uPrint.zw;                // metres inside the paper edge
  float aa = max(fwidth(puv.x) * 2. * uPrint.z, 1e-5);
  float inside = uHasPrint * smoothstep(-aa * .7, aa * .7, min(ein.x, ein.y));
  // the sheet is not perfectly flat: its last few mm lift a little, catching less light on the sides away from the lamp
  vec2 edgeK = vec2(puv.x > .5 ? 1. : -.4, puv.y < .5 ? 1. : -.4);
  float lift = 1. - .035 * (edgeK.x * (1. - smoothstep(0., .005, ein.x)) + edgeK.y * (1. - smoothstep(0., .005, ein.y)));
  vec3 albedo = mix(uFloor, prc.rgb * lift, inside);
  // the safelight pool: a soft overhead source (cos^3 from its nadir, only part of the falloff reaches the paper)
  vec2 dl = vW.xz - uSafePos.xz; float hh = uSafePos.y - vW.y;
  float c1 = hh * inversesqrt(hh * hh + dot(dl, dl)), pool = mix(1., c1 * c1 * c1, uPool);
  // caustics: the liquid focuses the overhead light where the surface is convex (-laplacian h), soft-limited
  float ck = -uCaustic * (gl.z - gloc.z), cl = -uCaustic * .6 * gloc.z;
  float caus = (1. + .35 * ck / (1. + abs(ck))) * (1. + .5 * cl / (1. + abs(cl)));   // the drop's rings: a bright refraction ring
  vec3 col = albedo * uLight * pool * uTrans * caus;
  // reflections: the dim room everywhere (a sheen that keeps the tray black above INK) and the safelight rectangle
  vec2 gr = g * uReflGain + gMen;
  vec3 nr = normalize(uRot * normalize(vec3(-gr.x, 1., -gr.y)));
  vec3 V = normalize(vW - uCam), R = reflect(V, nr);
  float ci = clamp(dot(-V, nr), 0., 1.), c5 = 1. - ci, c2 = c5 * c5;
  float F = uF0 + (1. - uF0) * c2 * c2 * c5;
  float m = safeSeen(vW, R, 0.);
  col += F * (uSafeL * m + uRoom * uLight * (.55 + .45 * clamp(R.y, 0., 1.)));
  // the meniscus is a curved mirror a couple of mm wide: across its profile it catches the lamp somewhere - a thin line
  float mp = men * (1. - men) * 4.;
  col += mp * mp * (.03 * uSafeL * safeSeen(vW, R, .5) + .07 * uLight);
  gl_FragColor = vec4(col, 1.);
}`;

// the walls: black ABS (roughness ~0.35): a faint diffuse from the lamp, the room's sheen, the lamp's soft reflection
// on the lip (the fillet of the rim faces the lamp and the lens at once)
const WALL_FRAG = /* glsl */`
uniform vec3 uCam; uniform float uAlb;
varying vec3 vN, vP;
void main(){
  winClip();
  vec3 n = normalize(vN), V = normalize(vP - uCam), R = reflect(V, n);
  vec3 Ld = normalize(uSafePos - vP);
  float dif = max(dot(n, Ld), 0.) * uAlb * uLight;
  float ci = clamp(dot(-V, n), 0., 1.), c5 = 1. - ci, c2 = c5 * c5;
  float F = .04 + .96 * c2 * c2 * c5 * .3;                         // rough: the grazing Fresnel rise is damped
  float m = safeSeen(vP, R, .1);                                   // the lamp's soft image, only where the lip faces it
  float env = R.y > 0. ? .35 + .65 * R.y : .25;                    // the dark room above; the tray's own dark below
  vec3 col = vec3(dif + F * (uSafeL * 1.3 * m + uRoom * uLight * env * .6));
  gl_FragColor = vec4(col, 1.);
}`;

// a falling drop: a clear lens, all but invisible, a darker rim and a tiny sharp glint of the lamp
const DROP_FRAG = /* glsl */`
uniform vec3 uCam;
varying vec3 vN, vP;
void main(){
  vec3 n = normalize(vN), V = normalize(vP - uCam);
  float ci = clamp(dot(-V, n), 0., 1.);
  float rim = pow(1. - ci, 3.);
  vec3 Ld = normalize(uSafePos - vP), H = normalize(Ld - V);
  float spec = pow(max(dot(n, H), 0.), 140.) * 14.;               // the glint: the lamp in a 4 mm lens, a point of light
  float a = .06 + .3 * rim;                                        // premultiplied: a faint lens edge, add the glint
  gl_FragColor = vec4(vec3(spec * uLight), clamp(a, 0., 1.));
}`;

export default {
  name: 'tray',
  async init(ctx) {
    RectAreaLightUniformsLib.init();
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0d0e0f).convertSRGBToLinear();
    const group = new THREE.Group(); scene.add(group);

    const trayU = {
      uCam: { value: new THREE.Vector3() }, uPrint: { value: new THREE.Vector4(0, 0, PRINT.w / 2, PRINT.h / 2) },
      uPrintRot: { value: new THREE.Vector2(Math.cos(PRINT.rot), Math.sin(PRINT.rot)) },
      uHasPrint: { value: 0 }, uRefract: { value: 0.07 }, uRefractL: { value: 0.02 }, uLight: { value: 1 }, uTrans: { value: 0.96 }, uF0: { value: 0.02 },
      uSafeL: { value: SAFE.radiance }, uSafeSoft: { value: SAFE.soft }, uReflGain: { value: SAFE.gain }, uCaustic: { value: 0.045 },
      uPool: { value: SAFE.pool }, uRoom: { value: ROOM },
      uSafePos: { value: new THREE.Vector3(SAFE.x, SAFE.y, SAFE.z) }, uSafeHalf: { value: new THREE.Vector2(SAFE.w / 2, SAFE.d / 2) },
      uFloor: { value: new THREE.Vector3().setScalar(0.012) },       // the wet black floor (a little above the dry ABS)
      uInner: { value: new THREE.Vector4(INNER.w / 2, INNER.d / 2, INNER.r, 0.0012) },
      uInnerC: { value: new THREE.Vector2(INNER.cx, INNER.cz) },
      uRot: { value: new THREE.Matrix3() },
      uWinPx: { value: new THREE.Vector4(-1e5, -1e5, 1e5, 1e5) },
      uAlb: { value: new THREE.Color('#0b0b0b').r * 1.6 },
    };

    // bench + tray body (black ABS): the walls in a cheap shader; the base and the bench (seen only in wide windows) lit
    const abs = new THREE.MeshStandardMaterial({ color: new THREE.Color('#0b0b0b'), roughness: 0.35, metalness: 0 });
    const bench = new THREE.Mesh(new THREE.PlaneGeometry(4, 3).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: new THREE.Color('#2a2b2d'), roughness: 0.9 }));
    bench.position.y = -0.0005; scene.add(bench);
    // the extrusion's bevel grows the shape by `bev` (the hole shrinks): draw the hole that much larger so the inner face
    // stands exactly on the liquid's edge (else it would hang over the meniscus and the print's corner)
    const bev = 0.0025, outer = roundedRect(INNER.w + 2 * INNER.wall - 2 * bev, INNER.d + 2 * INNER.wall - 2 * bev, INNER.r + INNER.wall - bev);
    const ring = outer.clone(); ring.holes = [roundedRect(INNER.w + 2 * bev, INNER.d + 2 * bev, INNER.r + bev)];
    const wallMat = new THREE.ShaderMaterial({ uniforms: trayU,
      vertexShader: 'varying vec3 vN, vP; void main(){ vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix * vec4(position, 1.); vP = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
      fragmentShader: SAFE_GLSL + WALL_FRAG });
    // smooth normals (merged vertices): the lip's highlight runs as one soft line, not a row of facets
    const wallGeo = mergeVertices(new THREE.ExtrudeGeometry(ring, { depth: INNER.h, bevelEnabled: true, bevelThickness: bev, bevelSize: bev, bevelSegments: 5, curveSegments: 28 }).deleteAttribute('uv').deleteAttribute('normal'), 1e-5);
    wallGeo.computeVertexNormals();
    const walls = new THREE.Mesh(wallGeo.rotateX(-Math.PI / 2).translate(INNER.cx, FLOOR_Y, INNER.cz), wallMat);
    const baseShape = roundedRect(INNER.w + 2 * INNER.wall, INNER.d + 2 * INNER.wall, INNER.r + INNER.wall);
    const base = new THREE.Mesh(new THREE.ExtrudeGeometry(baseShape, { depth: FLOOR_Y, bevelEnabled: false, curveSegments: 10 }).rotateX(-Math.PI / 2).translate(INNER.cx, 0, INNER.cz), abs);
    group.add(walls, base);

    // light for the lit materials (base, bench): the safelight + a whisper of room light
    const safe = new THREE.RectAreaLight(0xffffff, 1, SAFE.w, SAFE.d);
    safe.position.set(SAFE.x, SAFE.y, SAFE.z); safe.lookAt(SAFE.x, 0, SAFE.z); scene.add(safe);
    const room = new THREE.HemisphereLight(0xffffff, 0x000000, 0.05); scene.add(room);

    // the liquid + print shader over the tray interior (vL = tray-local x, z: the plane is built at the interior centre)
    const liquid = new Liquid(ctx, { width: INNER.w, depth: INNER.d, corner: INNER.r, center: [INNER.cx, INNER.cz] });
    const mats = new Map();         // one liquid material per develop pass (its uniforms are the pass's own objects)
    const bare = { uniforms: {} };  // no print: the develop uniforms still have to exist
    const matFor = pass => {
      const cells = !!(pass && pass.cellsOnly), k = (pass ? pass.key : '-') + (cells ? ':cells' : '');
      if (!mats.has(k)) {
        const dvU = pass ? pass.uniforms : (bare.uniforms = bare.uniforms.dvSrc ? bare.uniforms : developUniforms());
        mats.set(k, new THREE.ShaderMaterial({ uniforms: { ...liquid.uniforms, ...liquid.bakedUniforms, ...dvU, ...trayU }, vertexShader: VERT,
          defines: cells ? { DV_CELLS_ONLY: 1 } : {}, fragmentShader: liquid.bakedGlsl + DEVELOP_GLSL + SAFE_GLSL + FRAG, depthWrite: true }));
      }
      return mats.get(k);
    };
    const surf = new THREE.Mesh(new THREE.PlaneGeometry(INNER.w, INNER.d, 1, 1).rotateX(-Math.PI / 2).translate(INNER.cx, 0, INNER.cz), matFor(null));
    surf.position.y = LIQUID_Y; group.add(surf);

    // falling drops (S04): small clear lenses with a glint of the lamp
    const dropMat = new THREE.ShaderMaterial({ uniforms: trayU, transparent: true, depthWrite: false,
      blending: THREE.CustomBlending, blendSrc: THREE.OneFactor, blendDst: THREE.OneMinusSrcAlphaFactor,
      vertexShader: 'varying vec3 vN, vP; void main(){ vN = normalize(mat3(modelMatrix) * normal); vec4 w = modelMatrix * vec4(position, 1.); vP = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }',
      fragmentShader: SAFE_GLSL + DROP_FRAG });
    const dropGeo = new THREE.SphereGeometry(0.0018, 20, 14); dropGeo.scale(1, 1.2, 1);
    const drops = Array.from({ length: 4 }, () => { const m = new THREE.Mesh(dropGeo, dropMat); m.visible = false; m.renderOrder = 2; group.add(m); return m; });

    // the tray lens
    const camera = new THREE.PerspectiveCamera(LENS.fov, 16 / 9, 0.05, 20);
    camera.position.set(0, PRINT.y + LENS.height, 0); camera.up.set(0, 0, -1); camera.lookAt(0, PRINT.y, 0);
    camera.updateMatrixWorld();
    const metresPerPx1080 = 2 * LENS.height * Math.tan(LENS.fov / 2 * Math.PI / 180) / 1080;
    const cr = Math.cos(PRINT.rot), sr = Math.sin(PRINT.rot);

    const api = {
      scene, camera, group, liquid, surf, walls, safe, PRINT, LIQUID_Y, INNER, metresPerPx1080,
      printUVToLocal(u, v) { const px = (u - 0.5) * PRINT.w, pz = -(v - 0.5) * PRINT.h; return new THREE.Vector3(cr * px - sr * pz, PRINT.y, sr * px + cr * pz); },
      localToPrintUV(x, z) { const px = cr * x + sr * z, pz = -sr * x + cr * z; return [px / PRINT.w + 0.5, 0.5 - pz / PRINT.h]; },
      // where the print point (u, v) appears through the liquid: solve p - refract * grad(p) = bottom (fixed-point steps;
      // the swell only: the drops' local slopes refract little and are compressed)
      refracted(u, v, t) {
        const b = api.printUVToLocal(u, v); let x = b.x, z = b.z;
        for (let i = 0; i < 3; i++) { const g = liquid.grad(x, z, t); x = b.x + trayU.uRefract.value * g[0]; z = b.z + trayU.uRefract.value * g[1]; }
        return api.localToPrintUV(x, z);
      },
      project(p) {
        const v = p.clone().project(camera);
        return { x: (v.x + 1) / 2 * 1920, y: (1 - v.y) / 2 * 1080 };
      },
      update(t, o = {}) {
        const tl = ctx.tl;
        liquid.update(t, o.liquid || {});
        liquid.bake(ctx.renderer);
        const sl = { ...SAFE, ...(o.safelight || {}) };
        const level = o.light ?? (sl.base * (0.55 + 0.45 * (tl ? voiceLight(tl)(t) : 0)));
        trayU.uLight.value = level;
        trayU.uSafeL.value = sl.radiance * level;
        trayU.uSafePos.value.set(sl.x, sl.y, sl.z); trayU.uSafeHalf.value.set(sl.w / 2, sl.d / 2); trayU.uSafeSoft.value = sl.soft; trayU.uReflGain.value = sl.gain;
        trayU.uPool.value = sl.pool;
        safe.position.set(sl.x, sl.y, sl.z); safe.width = sl.w; safe.height = sl.d; safe.lookAt(sl.x, 0, sl.z);
        safe.intensity = 6 * level;
        trayU.uRefract.value = o.refract ?? 0.07; trayU.uRefractL.value = o.refractLocal ?? 0.02; trayU.uCaustic.value = o.caustic ?? 0.045;
        const pass = o.print || null;
        surf.material = matFor(pass);
        trayU.uHasPrint.value = pass ? 1 : 0;
        // the window in output px (gl_FragCoord: y up): pixels outside it are discarded (the core masks them to INK);
        // the base and the bench only show in windows wider than the tray (or tilted)
        const rect = ctx.frame && ctx.frame.rect, tilted = !!(o.tilt && (o.tilt[0] || o.tilt[1]));
        if (rect && ctx.win && ctx.frame.layer !== 'pregrade') {
          const rp = ctx.win.px(rect, ctx.k), H = ctx.H;
          trayU.uWinPx.value.set(rp.x - 2, H - rp.y - rp.h - 2, rp.x + rp.w + 2, H - rp.y + 2);
        } else trayU.uWinPx.value.set(-1e5, -1e5, 1e5, 1e5);
        const halfW = rect ? rect.w / 2 * metresPerPx1080 : 1;
        const wide = tilted || o.walls === true || !rect || halfW > PRINT.w / 2 + 0.06;
        base.visible = bench.visible = wide;
        walls.visible = true;
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
