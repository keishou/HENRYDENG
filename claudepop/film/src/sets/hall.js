// hall.js - THE HALL (BIBLE 4.1 HALL, 4.8 HALL, 7 THE AUDIENCE; lane E). The machine's show: a long dark hall, a wet
// black floor, haze, a large cold backlight at the far end, and rows of prints hanging across both sides of a central
// aisle like a seated audience.
//
// Construction (metres, Y up; the camera end at z ~ 0, the hall runs down -Z):
//   floor      12 x 60 (x +-6, z +2 .. -58), wet black: a planar mirror (our own reflection pass at half the output
//              size, rendered in update(), NOT three's Reflector), a streak-blurred quarter-size copy for the damp
//              concrete, a puddle / damp mask, Fresnel; no rain; heel rings only when asked.
//   rows       every 1.5 m in z (38 rows, z -1.5 .. -57), on each side of the 2.4 m aisle a wire from |x| 1.4 to 5.4
//              carrying 5 prints (0.56 x 0.72, facing +Z) on two paperclips each (src/sets/prints.js: 380 prints), at
//              y 1.2 - BIBLE 4.8 says 1.75; lowered to seated-head height, below the 1.55 eye, so the long lens looks
//              over the rows and each row's top edge steps up behind the one in front: a seated audience, where 1.75
//              compressed the 38 rows into two walls of slabs (lane E note; proposed BIBLE diff). Thin stands at the wire
//              ends; wires and stands as anti-aliased hairlines.
//   backlight  an emissive panel 10 x 5 at z -58 (bottom edge 0.25 m; BACKLIGHT; level = levelAt(t), the film's
//              brightness arc), seen through the haze; the haze glows around it (forward scatter) and down the aisle.
//   haze       analytic single scattering, per vertex in every hall material (hazeAt: transmittance exp(-(rho d)^p) +
//              in-scatter = ambient haze + a backlight term with a forward lobe around the panel, weighted by the share
//              of the ray's lit haze in front of the point (closed-form integral of a Lorentzian falloff), the aisle
//              corridor brighter than the haze the rows shade). No FogExp2 banding, no ray march.
//   audience   the sheets glow by the panel's light through the paper: shaded by the rows behind (kappa), a spill of
//              light over each top edge (the rows read as heads rimmed by stage light), formation, curl, per-sheet
//              variation; cheap defocus (circle of confusion -> texture LOD + edge softness) for the long lens.
//   stand-in   hallAvatarMaterial: MeshBasic + a small backlight model (two cold rims from the panel side, a low soft
//              footlight within 30 deg of the lens, ambient, skin sheen), hazed like the set; hair cards with an
//              anti-aliased alpha test (no MSAA: 2x or 4x costs 200-470 ms here). The shared avatar's own materials are
//              never modified. A shot that does not pass opts.avatar gets him hidden (he is shared across shots).
//
// DETERMINISM (BIBLE 9.2; the look-dev L2 floor differed between browser launches): every texture here is computed in
// JS (no canvas 2D rasterisation), the reflection and blur are explicit passes in update() into non-MSAA targets with
// fixed state (no onBeforeRender re-entry), nothing is carried between frames, and the stand-in cannot leak from one
// shot into another. Verified with film/tools/determinism.mjs across fresh browsers.
//
// API (ctx.sets.hall)
//   scene, camera (the chorus master: (0, 1.55, 0) looking down -Z, FOV 14)
//   prints                      the standard rows (Prints: call hall.resetPrints() then prints.set() in your frame)
//   rows                        { n, z(r), xs, y, perLine, ids[r][line][col] }  (line 0 = the -X side, 1 = +X; col 0 at
//                               the aisle)
//   update(t, opts)             per frame, in frame() after posing the stand-in and setting the prints, before
//                               returning the layers (it renders the floor reflection now):
//       opts.camera     the render camera (required: reflection, sorting, defocus, occlusion)
//       opts.level      backlight level (default levelAt(t))        opts.haze   multiplier of the haze density (1)
//       opts.glow       haze glow multiplier (1)                     opts.focus  { distance, coc } defocus
//       opts.avatar     true: the stand-in is in the scene (its lights aim at opts.head)   opts.head  THREE.Vector3
//       opts.reflectAvatar  render him into the floor reflection (default false: never in frame in the long lens)
//       opts.veil       0..1 the stand-in dissolves into the hall behind him (S15 "steps out of the backlight")
//       opts.fill       footlight multiplier (1)   opts.even  footlight near the axis (the previs' even face light)
//       opts.rim        rim multiplier (1)          opts.sway  sheets' sway multiplier (1)
//       opts.tremble    { t, amp, speed } a decaying shiver through the sheets from time t, travelling at speed m/s
//       opts.sheets     { kappa, over, overW, under, key } the audience's light: kappa = how much each row behind shades a
//                       sheet's back (0.2: dark bodies, glowing tops - the blank chorus master; 0.08: images read on the
//                       near rows), over / overW = the spill over the tops (amount, fall-off m), key = front light on them
//       opts.rings      [{ t, x, z, amp }] heel-strike rings in the wet floor (up to 4)
//   levelAt(t)                  the backlight level of the brightness arc (BIBLE 4.1): chorus 1 ... climax -> white
//   avatarLook(av)              installs the hall materials on the stand-in (every frame, after re-parenting him)
//   resetPrints()               every sheet blank, default sway, clips on -> prints
//   photoAtlas()                (async, once) the photograph developing: 4 darkroom variants x [blank, 8 develop()
//                               stages] -> { atlas, strips, taus }; stripDensity(tau) -> strip position for a
//                               chemistry time
//   hazeGLSL, hazeUniforms      the haze chunk (vec4 hazeAt(vec3 worldPos)) for scene-owned materials
//   CFG                         the look constants (see below)
import * as THREE from 'three';
import { Prints } from './prints.js';
import { develop } from '../fx/develop.js';
import { loadPrint, faceCrop } from '../fx/print.js';

const C = hex => new THREE.Color(hex);                      // linear (ColorManagement)
const BACKLIGHT = C('#DCE3E8'), NIGHT = C('#10151A');
// Look constants. Review overrides (development only; render.mjs never passes them, and a given URL renders
// deterministically): ?hallcfg=key:value,... overrides these numbers; ?halldbg=prof logs per-component GPU times,
// ?halldbg=noprints,norefl,nolines,noav,noocc switch parts off.
const CFG = { wire: 1.2, dz: 1.5, rows: 38, perLine: 5, stagger: 0, yJitter: 0.01, kappa: 0.2, over: 2.2, overW: 0.04, under: 0.15, back: 0.8, rim: 0,
  key: 0.008, trans: 0.42, panel: 0.62, glow: 0.03, form: 0.2, dof: 1, msaa: -1,
  bloomT: 0.93, bloomA: 0.22, hal: 0.1 };
try { for (const kv of (new URLSearchParams(location.search).get('hallcfg') || '').split(',').filter(Boolean)) { const [k, v] = kv.split(':'); if (k in CFG) CFG[k] = +v; } } catch {}
const PANEL = { x: 0, y: 2.75, z: -58, w: 10, h: 5 };        // panel centre, size (bottom edge at y 0.25)
const ROWS = { n: CFG.rows, z0: -CFG.dz, dz: -CFG.dz, xs: [[-5.4, -1.4], [1.4, 5.4]], y: CFG.wire, perLine: CFG.perLine };   // wire below the eye (1.55): see note
const DEV_TAUS = [0.35, 0.8, 1.5, 2.6, 4.2, 7, 12, 30];     // develop() chemistry times of the atlas stages (s)
const smooth = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
const lerp = (a, b, u) => a + (b - a) * u;

// ------------------------------------------------------------------------------------------------ haze
export const HAZE_GLSL = /* glsl */`
  uniform vec3 uHzBase, uHzGlow; uniform vec4 uHzPanel; uniform vec4 uHzP; uniform float uHzT, uHzLf; uniform vec2 uHzRows;
  float hzH(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
  float hzN(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
    return mix(mix(hzH(i), hzH(i + vec2(1, 0)), f.x), mix(hzH(i + vec2(0, 1)), hzH(i + vec2(1, 1)), f.x), f.y); }
  // in-scattered light and transmittance along the camera ray to wp. uHzPanel = (half w, half h, centre y, z plane);
  // uHzP = (rho, power, aisle half width, glow falloff scale)
  vec4 hazeRay(vec3 ro, vec3 rd, float d){
    float T = exp(-pow(uHzP.x * d, uHzP.y));
    vec3 ins = uHzBase * (1. - T);
    if (rd.z < -1e-4) {
      float sP = (uHzPanel.w - ro.z) / rd.z;                        // distance to the panel plane
      vec2 hit = ro.xy + rd.xy * sP;
      vec2 dq = max(abs(hit - vec2(0., uHzPanel.z)) - uHzPanel.xy, 0.);
      float ang = length(dq) / max(sP, 1.);                        // angle off the panel rectangle
      float lobe = .7 * exp(-ang / (.012 * uHzP.w)) + .3 * exp(-ang / (.045 * uHzP.w));
      // share of the ray's lit haze (a Lorentzian around the panel plane, width uHzLf) in front of this point
      float Lf = uHzLf, a0 = atan(sP / Lf), full = a0 + 1.5707963;
      float part = (a0 - atan((sP - d) / Lf)) / full;
      // the corridor: the panel's light travels down the aisle; over the audience the rows shade the haze at print
      // height (uHzRows: the sheets' span); above and below the rows it passes. Evaluated at the far part of the ray.
      float se = min(d, max(sP - Lf, .62 * d));
      vec2 pe = ro.xy + rd.xy * se;
      float aisle = 1. - smoothstep(uHzP.z - .2, uHzP.z + 1.6, abs(pe.x));
      float band = smoothstep(uHzRows.x - .15, uHzRows.x + .05, pe.y) * (1. - smoothstep(uHzRows.y - .05, uHzRows.y + .2, pe.y));
      float lit = mix(1., .38, band * (1. - aisle)) * (.72 + .28 * aisle);
      // slow drift of the haze density (seeded, a pure function of time)
      float drift = .9 + .2 * hzN(hit * .35 + vec2(uHzT * .05, -uHzT * .02));
      ins += uHzGlow * lobe * part * lit * drift * (1. - T * .35);
    }
    return vec4(ins, T);
  }
  vec4 hazeAt(vec3 wp){ vec3 v = wp - cameraPosition; float d = length(v); return hazeRay(cameraPosition, v / max(d, 1e-4), d); }
`;
function hazeUniforms() {
  return {
    uHzBase: { value: new THREE.Vector3() }, uHzGlow: { value: new THREE.Vector3() },
    uHzPanel: { value: new THREE.Vector4(PANEL.w / 2, PANEL.h / 2, PANEL.y, PANEL.z) },
    uHzP: { value: new THREE.Vector4(0.022, 1.4, 1.2, 1) }, uHzT: { value: 0 }, uHzLf: { value: 14 },
    uHzRows: { value: new THREE.Vector2(ROWS.y - 0.73, ROWS.y) },
  };
}

// ------------------------------------------------------------------------------------------------ materials
const BASIC_VERT = /* glsl */`varying vec3 vW; varying vec2 vUv; void main(){ vUv = uv; vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
// the big planes take the haze per vertex (subdivided geometry; the haze varies slowly across them)
const HAZE_VERT = /* glsl */`varying vec3 vW; varying vec2 vUv; varying vec4 vHz;
  ${HAZE_GLSL}
  void main(){ vUv = uv; vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz; vHz = hazeAt(w.xyz); gl_Position = projectionMatrix * viewMatrix * w; }`;

// the panel: a frosted light wall of five modules, a slightly hotter lower centre, soft edges
const PANEL_FRAG = /* glsl */`
  uniform vec3 uCol; uniform float uLevel, uCoc; varying vec3 vW; varying vec2 vUv; varying vec4 vHz;
  void main(){
    vec2 q = vUv;
    vec2 fw = fwidth(q) * (1. + uCoc);                       // defocus: the edge widens with the circle of confusion
    vec2 ew = vec2(.018, .03) + fw;
    float edge = smoothstep(0., ew.x, q.x) * smoothstep(0., ew.x, 1. - q.x) * smoothstep(0., ew.y, q.y) * smoothstep(0., ew.y, 1. - q.y);
    float m = abs(fract(q.x * 5.) - .5);                     // five modules: faint darker seams
    float seams = 1. - .06 * smoothstep(.47, .5, m);
    float hot = .55 + .45 * exp(-pow((q.x - .5) / .42, 2.) - pow((q.y - .42) / .55, 2.)) + .25 * exp(-pow((q.x - .5) / .18, 2.) - pow((q.y - .35) / .3, 2.));
    vec3 col = uCol * uLevel * edge * seams * hot;
    gl_FragColor = vec4(col * vHz.a + vHz.rgb, 1.);
  }`;

// the shell (end wall around the panel, side walls, ceiling): near black, a little of the panel's light grazing it
const SHELL_FRAG = /* glsl */`
  uniform vec3 uCol, uBack; uniform vec4 uHzPanel; varying vec3 vW; varying vec2 vUv; varying vec4 vHz;
  void main(){
    float nearP = 1. / (1. + pow(max(0., vW.z - uHzPanel.w) / 9., 2.));
    vec3 col = uCol + uBack * nearP * .08;
    gl_FragColor = vec4(col * vHz.a + vHz.rgb, 1.);
  }`;

// the wet floor: our mirror texture, projected; puddles (mirror) vs damp (rough, dimmer), vertical streaks, Fresnel
const FLOOR_VERT = /* glsl */`varying vec3 vW; varying vec4 vHz; varying float vF;
  ${HAZE_GLSL}
  void main(){ vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz; vHz = hazeAt(w.xyz);
    float cosT = clamp(normalize(cameraPosition - w.xyz).y, 0., 1.); vF = .02 + .98 * pow(1. - cosT, 5.);
    gl_Position = projectionMatrix * viewMatrix * w; }`;
const FLOOR_FRAG = /* glsl */`
  uniform sampler2D uRefl, uReflSoft, uFloorTex; uniform mat4 uReflMat; uniform vec2 uReflPx;
  uniform vec3 uBase, uBack; uniform float uLevel, uT; uniform vec4 uHzPanel;
  uniform vec4 uRings[4]; uniform float uRingN;
  varying vec3 vW; varying vec4 vHz; varying float vF;
  void main(){
    vec2 p = vW.xz;
    // puddles (R: a warped low-frequency mask, 19 x 72 m tile) and concrete grain (GB: micro normal, A: tone)
    float pud = smoothstep(.3, .72, texture2D(uFloorTex, p * vec2(.42, .11) / 8.).r);
    vec4 g = texture2D(uFloorTex, p * .9);
    vec2 nrm = (g.gb - .5) * .010 * (1. - pud * .7);
    if (uRingN > 0.) for (int i = 0; i < 4; i++) {
      if (float(i) >= uRingN) break;
      vec4 R = uRings[i];                                    // x, z, age (s), amp
      if (R.z < 0.) continue;
      vec2 d = p - R.xy; float r = length(d), rad = .06 + .32 * R.z;
      float ring = sin((r - rad) * 70.) * exp(-pow((r - rad) * 22., 2.)) * exp(-R.z * 1.6) * R.w;
      nrm += d / (r + 1e-4) * ring * .02;
    }
    vec4 pc = uReflMat * vec4(vW, 1.);
    vec2 uv = pc.xy / pc.w + nrm;
    // blur: vertical streaks (wet floor): mip LOD for the width, taps along v for the streak; rougher on damp concrete
    float rough = 1. - pud;
    // two bilinear taps: the sharp mirror (puddles) and the streak-blurred copy (damp concrete)
    vec3 r = mix(texture2D(uRefl, uv).rgb, texture2D(uReflSoft, uv + vec2(0., nrm.y * 2.)).rgb, smoothstep(.15, .85, rough));
    float refl = vF * mix(.24, .62, pud);
    // the floor's own (dark, wet concrete) light: a pool of the panel's light near the far end, darker under the rows
    float pool = 1. / (1. + pow(max(0., vW.z - uHzPanel.w) / 7., 2.));
    float under = mix(1., .55, smoothstep(1.2, 1.8, abs(vW.x)));
    vec3 base = uBase * (.85 + .3 * g.a) + uBack * uLevel * pool * .012 * under;
    vec3 col = base * (1. - refl) + r * refl;
    gl_FragColor = vec4(col * vHz.a + vHz.rgb, 1.);
  }`;

// floor noise texture (pure JS): R = warped fbm puddle mask over an 8 x 8 cell tile, GB = fine grain (micro normal),
// A = tone. Tileable.
function floorTexture() {
  const N = 256, data = new Uint8Array(N * N * 4);
  const h = (i, j, s) => { let n = (i * 374761393 + j * 668265263 + s * 2147483647) | 0; n = Math.imul(n ^ (n >>> 13), 1274126177); n ^= n >>> 16; return (n >>> 0) / 4294967296; };
  const vn = (x, y, per, s) => { const i = Math.floor(x), j = Math.floor(y), u = x - i, v = y - j, su = u * u * (3 - 2 * u), sv = v * v * (3 - 2 * v);
    const q = (a, b) => h(((a % per) + per) % per, ((b % per) + per) % per, s);
    return (q(i, j) * (1 - su) + q(i + 1, j) * su) * (1 - sv) + (q(i, j + 1) * (1 - su) + q(i + 1, j + 1) * su) * sv; };
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const X = x / N * 8, Y = y / N * 8;
    const wx = vn(X * 0.8, Y * 0.8, 6.4 | 0 || 6, 3) - 0.5, wy = vn(X * 0.8 + 11, Y * 0.8, 6, 8) - 0.5;
    const qx = X + wx * 0.35, qy = Y + wy * 0.35;
    const pm = vn(qx, qy, 8, 1) * 0.55 + vn(qx * 2, qy * 2, 16, 2) * 0.3 + vn(qx * 4, qy * 4, 32, 4) * 0.15;
    const G = vn(x / N * 64, y / N * 64, 64, 5), B = vn(x / N * 64, y / N * 64, 64, 6), A = vn(x / N * 16, y / N * 16, 16, 7);
    const k = (y * N + x) * 4;
    data[k] = Math.round(255 * pm); data[k + 1] = Math.round(255 * G); data[k + 2] = Math.round(255 * B); data[k + 3] = Math.round(255 * A);
  }
  const t = new THREE.DataTexture(data, N, N, THREE.RGBAFormat);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true;
  t.colorSpace = THREE.NoColorSpace; t.needsUpdate = true;
  return t;
}

// hairlines (wires, stands): a ribbon expanded to at least ~1.1 px, alpha = real width / drawn width (coverage)
const LINE_VERT = /* glsl */`
  attribute vec3 aDir; attribute float aSide; attribute float aWidth;
  uniform vec2 uRes; uniform vec2 uFocus; varying float vCov; varying vec3 vW; varying float vAlong;
  void main(){
    vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz;
    vec4 c0 = projectionMatrix * viewMatrix * w, c1 = projectionMatrix * viewMatrix * (w + vec4(aDir * .05, 0.));
    vec2 s0 = c0.xy / c0.w * uRes * .5, s1 = c1.xy / c1.w * uRes * .5;
    vec2 t = normalize(s1 - s0 + 1e-6), n = vec2(-t.y, t.x);
    float pxPerM = uRes.y * .5 * projectionMatrix[1][1] / c0.w;   // output px per metre at this depth
    float coc = uFocus.y * abs(1. / max(c0.w, .05) - 1. / uFocus.x);
    float wpx = aWidth * pxPerM, draw = max(wpx, 1.15) + coc;
    vCov = clamp(wpx / draw, 0., 1.);
    vAlong = aSide;
    gl_Position = c0 + vec4(n * aSide * draw * .5 / (uRes * .5) * c0.w, 0., 0.);
  }`;
const LINE_FRAG = /* glsl */`
  uniform vec3 uCol, uGlint; varying float vCov; varying vec3 vW; varying float vAlong;
  ${HAZE_GLSL}
  void main(){
    float edge = 1. - smoothstep(.55, 1., abs(vAlong));
    vec3 col = uCol + uGlint;
    vec4 hz = hazeAt(vW);
    gl_FragColor = vec4(col * hz.a + hz.rgb, vCov * (.55 + .45 * edge));
  }`;

// The stand-in in the hall: a MeshBasic base (texture, alpha cut-out, skinning) with a small backlight model instead of
// PBR - a wrap-diffuse soft fill from the camera side (the footlight), two cold rims from the panel behind him on the
// silhouette edges (a Fresnel-shaped lobe, strongest on hair and knit fuzz), an ambient, a faint skin sheen - then the
// hall haze (per vertex). The veil (S15, "he steps out of the backlight") mixes each fragment toward the hall behind him
// (a quarter-size render of the set without him, sampled in screen space), edges first: he condenses out of the light.
// Under SwiftShader this costs about a third of the GLB's PBR / anisotropic-hair materials.
const AV_VERT_DECL = `\nvarying vec3 vNrmV, vViewP; varying vec4 vHz;\n`;
function hallAvatarMaterial(orig, key, U) {
  // alpha-tested hair cards: an anti-aliased alpha test (the cut-off smoothstepped over one pixel of the alpha gradient,
  // blended) instead of MSAA, which costs 200-470 ms here; brows and fringe strands blend as in the GLB
  const soft = (orig.alphaTest || 0) > 0;
  const m = new THREE.MeshBasicMaterial({ color: orig.color, map: orig.map, alphaTest: orig.alphaTest || 0, side: orig.side,
    transparent: !!orig.transparent || soft, depthWrite: orig.depthWrite !== false, fog: true });
  const sheen = /hair|brow|lash/.test(key) ? 1.0 : /top|trousers/.test(key) ? 0.55 : /skin/.test(key) ? 0.3 : 0.15;
  m.onBeforeCompile = sh => {
    Object.assign(sh.uniforms, U);
    sh.defines = { ...(sh.defines || {}), AV_SHEEN: sheen.toFixed(2), ...(/skin/.test(key) ? { AV_SKIN: 1 } : {}) };
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>' + AV_VERT_DECL + HAZE_GLSL)
      .replace('#include <fog_vertex>', `#include <fog_vertex>
        #ifdef USE_SKINNING
          vNrmV = normalize(transformedNormal);
        #else
          vNrmV = normalize(normalMatrix * normal);
        #endif
        vViewP = mvPosition.xyz;
        vHz = hazeAt((modelMatrix * vec4(transformed, 1.)).xyz);`);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
        varying vec3 vNrmV, vViewP; varying vec4 vHz;
        uniform vec3 uAvFill, uAvFillDir, uAvRimCol, uAvRimL, uAvRimR, uAvAmb; uniform float uVeil; uniform sampler2D uAvBg; uniform vec2 uAvRes;`)
      .replace('#include <opaque_fragment>', `{
        vec3 N_ = normalize(vNrmV); if (!gl_FrontFacing) N_ = -N_;
        vec3 V_ = normalize(-vViewP);
        float nv = max(dot(N_, V_), 0.);
        vec3 a_ = diffuseColor.rgb;
        float fl = max(dot(N_, uAvFillDir) * .88 + .12, 0.);
        vec3 lit = a_ * (uAvAmb + uAvFill * fl);
        float fr = pow(1. - nv, 2.2);
        float rim = fr * (max(dot(N_, uAvRimL) + .25, 0.) + max(dot(N_, uAvRimR) + .25, 0.));
        lit += uAvRimCol * rim * (.2 * a_ + AV_SHEEN * .22);
        #ifdef AV_SKIN
          lit += uAvFill * .035 * pow(max(dot(N_, normalize(uAvFillDir + V_)), 0.), 24.);
        #endif
        outgoingLight = lit * vHz.a + vHz.rgb;
        if (uVeil > .001) {
          vec3 bg = texture2D(uAvBg, gl_FragCoord.xy / uAvRes).rgb;
          float v = clamp(uVeil * (1. + .6 * (1. - nv)), 0., 1.);        // the edges dissolve last
          outgoingLight = mix(outgoingLight, bg, v);
        }
      }
      #include <opaque_fragment>`)
      .replace('#include <fog_fragment>', '');
    if (soft) sh.fragmentShader = sh.fragmentShader.replace('#include <alphatest_fragment>', `
        { float fw_ = max(fwidth(diffuseColor.a) * .7, 1e-3);
          diffuseColor.a = smoothstep(alphaTest - fw_, alphaTest + fw_, diffuseColor.a);
          if (diffuseColor.a < .02) discard; }`);
  };
  m.customProgramCacheKey = () => 'hall-av-v2-' + key;
  return m;
}

export default {
  name: 'hall',
  async init(ctx) {
    const scene = new THREE.Scene();
    scene.background = null;
    const U = hazeUniforms();
    const camera = new THREE.PerspectiveCamera(14, 16 / 9, 0.1, 200); camera.position.set(0, 1.55, 0); camera.lookAt(0, 1.55, -10);

    // ---- backlight panel
    const panelMat = new THREE.ShaderMaterial({ uniforms: { ...U, uCol: { value: BACKLIGHT.clone() }, uLevel: { value: 6 }, uCoc: { value: 0 } },
      vertexShader: HAZE_VERT, fragmentShader: PANEL_FRAG });
    const panel = new THREE.Mesh(new THREE.PlaneGeometry(PANEL.w, PANEL.h, 20, 10), panelMat);
    panel.position.set(PANEL.x, PANEL.y, PANEL.z); scene.add(panel);

    // ---- shell: end wall (with the panel opening), side walls, ceiling
    const shellMat = new THREE.ShaderMaterial({ uniforms: { ...U, uCol: { value: NIGHT.clone().multiplyScalar(0.25) }, uBack: { value: BACKLIGHT.clone() } },
      vertexShader: HAZE_VERT, fragmentShader: SHELL_FRAG, side: THREE.DoubleSide });
    const shell = new THREE.Group();
    const endW = 12, endH = 8;
    const wallPiece = (w, h, x, y, z, ry = 0) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h, Math.max(1, Math.round(w / 2)), Math.max(1, Math.round(h / 2))), shellMat); m.position.set(x, y, z); m.rotation.y = ry; shell.add(m); };
    const zEnd = PANEL.z - 0.02;
    wallPiece((endW - PANEL.w) / 2, endH, -(PANEL.w / 2 + (endW - PANEL.w) / 4), endH / 2, zEnd);
    wallPiece((endW - PANEL.w) / 2, endH, (PANEL.w / 2 + (endW - PANEL.w) / 4), endH / 2, zEnd);
    wallPiece(PANEL.w, endH - (PANEL.y + PANEL.h / 2), 0, (endH + PANEL.y + PANEL.h / 2) / 2, zEnd);
    wallPiece(PANEL.w, PANEL.y - PANEL.h / 2, 0, (PANEL.y - PANEL.h / 2) / 2, zEnd);
    wallPiece(62, endH, -6, endH / 2, -28, Math.PI / 2); wallPiece(62, endH, 6, endH / 2, -28, -Math.PI / 2);
    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(12, 62, 6, 31), shellMat); ceil.rotation.x = Math.PI / 2; ceil.position.set(0, endH, -28); shell.add(ceil);
    const behind = new THREE.Mesh(new THREE.PlaneGeometry(12, endH), shellMat); behind.position.set(0, endH / 2, 3); shell.add(behind);
    scene.add(shell);

    // ---- floor (wet mirror)
    const floorU = { ...U, uRefl: { value: null }, uReflMat: { value: new THREE.Matrix4() }, uReflPx: { value: new THREE.Vector2(1 / 960, 1 / 540) },
      uBase: { value: NIGHT.clone().multiplyScalar(0.35) }, uBack: { value: BACKLIGHT.clone() }, uLevel: { value: 6 }, uT: { value: 0 },
      uRings: { value: [0, 1, 2, 3].map(() => new THREE.Vector4(0, 0, -1, 0)) }, uRingN: { value: 0 }, uFloorTex: { value: floorTexture() }, uReflSoft: { value: null } };
    const floorMat = new THREE.ShaderMaterial({ uniforms: floorU, vertexShader: FLOOR_VERT, fragmentShader: FLOOR_FRAG});
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(12, 60.5, 12, 121).rotateX(-Math.PI / 2).translate(0, 0, -27.75), floorMat);
    scene.add(floor);

    // ---- the rows: prints, wires, stands
    const prints = new Prints(ctx, { max: ROWS.n * 2 * ROWS.perLine, size: [0.56, 0.72], haze: { glsl: HAZE_GLSL, uniforms: U } });
    const allIds = prints.layout('rows', { z0: ROWS.z0, dz: ROWS.dz, rows: ROWS.n, xs: ROWS.xs, y: ROWS.y, perLine: ROWS.perLine, stagger: CFG.stagger, yJitter: CFG.yJitter });
    const ids = [];
    for (const id of allIds) { const it = prints.items[id]; ((ids[it.row] ??= [[], []])[it.line])[it.col] = id; }
    scene.add(prints.object);
    // wires with a sag between the clips (a catenary-ish droop of 6 mm per span), stands at both ends
    const lp = [], ld = [], ls = [], lw = [], li = [];
    const seg = (a, b, width) => {
      const d = new THREE.Vector3().subVectors(b, a).normalize(), base = lp.length / 3;
      for (const [p, s] of [[a, -1], [a, 1], [b, -1], [b, 1]]) { lp.push(p.x, p.y, p.z); ld.push(d.x, d.y, d.z); ls.push(s); lw.push(width); }
      li.push(base, base + 1, base + 2, base + 2, base + 1, base + 3);
    };
    for (let r = 0; r < ROWS.n; r++) {
      const z = ROWS.z0 + r * ROWS.dz;
      for (const [li, [x0, x1]] of ROWS.xs.entries()) {
        const wy = prints.items[ids[r][li][0]].wireY;
        const N = 40, pts = [];
        for (let i = 0; i <= N; i++) {
          const u = i / N, x = x0 + (x1 - x0) * u;
          const k = u * ROWS.perLine, fr = k - Math.floor(k);           // sag between the clip points of each print
          pts.push(new THREE.Vector3(x, wy + 0.0027 - 0.006 * Math.sin(Math.PI * u) - 0.0015 * Math.sin(Math.PI * fr), z));
        }
        for (let i = 0; i < N; i++) seg(pts[i], pts[i + 1], 0.0012);
        for (const x of [x0, x1]) seg(new THREE.Vector3(x, 0, z), new THREE.Vector3(x, wy + 0.06, z), 0.014);
      }
    }
    const lg = new THREE.BufferGeometry();
    lg.setAttribute('position', new THREE.Float32BufferAttribute(lp, 3)); lg.setAttribute('aDir', new THREE.Float32BufferAttribute(ld, 3));
    lg.setAttribute('aSide', new THREE.Float32BufferAttribute(ls, 1)); lg.setAttribute('aWidth', new THREE.Float32BufferAttribute(lw, 1));
    lg.setIndex(li);
    const lineMat = new THREE.ShaderMaterial({ uniforms: { ...U, uRes: { value: new THREE.Vector2(1920, 1080) }, uFocus: { value: new THREE.Vector2(20, 0) }, uCol: { value: new THREE.Vector3(0.012, 0.013, 0.015) },
      uGlint: { value: new THREE.Vector3() } }, vertexShader: LINE_VERT, fragmentShader: LINE_FRAG, transparent: true, depthWrite: false });
    const lines = new THREE.Mesh(lg, lineMat); lines.frustumCulled = false; lines.renderOrder = 5;
    scene.add(lines);

    // ---- the stand-in's light (hallAvatarMaterial uniforms; view-space directions, set per frame in update())
    const AVU = { ...U, uAvFill: { value: new THREE.Vector3() }, uAvFillDir: { value: new THREE.Vector3(0, 0, 1) }, uAvRimCol: { value: new THREE.Vector3() },
      uAvRimL: { value: new THREE.Vector3() }, uAvRimR: { value: new THREE.Vector3() }, uAvAmb: { value: new THREE.Vector3() },
      uVeil: { value: 0 }, uAvBg: { value: null }, uAvRes: { value: new THREE.Vector2(1920, 1080) } };
    let bgRT = null;
    // ---- lights for the stand-in (standard materials only; the set's own materials are self-lit shaders)
    const rimL = new THREE.DirectionalLight(BACKLIGHT, 3), rimR = new THREE.DirectionalLight(BACKLIGHT, 3);
    const fill = new THREE.DirectionalLight(0xf2efe8, 0.4), hemi = new THREE.HemisphereLight(0x8a96a3, 0x05070a, 0.25);
    for (const l of [rimL, rimR, fill]) { scene.add(l); scene.add(l.target); }
    scene.add(hemi);

    // ---- reflection pass
    const mirrorCam = new THREE.PerspectiveCamera();
    let reflRT = null, blurA = null, blurB = null;
    // the wet-floor streak: a vertical blur (7 taps, then 7 wider) with a touch of horizontal spread, at quarter size
    const blurMat = new THREE.ShaderMaterial({ depthTest: false, depthWrite: false,
      uniforms: { tSrc: { value: null }, uStep: { value: new THREE.Vector2() } },
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }',
      fragmentShader: `uniform sampler2D tSrc; uniform vec2 uStep; varying vec2 vUv;
        void main(){ vec3 c = texture2D(tSrc, vUv).rgb * .2;
          c += (texture2D(tSrc, vUv + uStep).rgb + texture2D(tSrc, vUv - uStep).rgb) * .18;
          c += (texture2D(tSrc, vUv + uStep * 2.).rgb + texture2D(tSrc, vUv - uStep * 2.).rgb) * .13;
          c += (texture2D(tSrc, vUv + uStep * 3.).rgb + texture2D(tSrc, vUv - uStep * 3.).rgb) * .09;
          gl_FragColor = vec4(c, 1.); }` });
    const blurScene = new THREE.Scene(), blurCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    blurScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), blurMat));
    const reflTarget = (w, h) => {
      if (!reflRT || reflRT.width !== w || reflRT.height !== h) {
        if (reflRT) reflRT.dispose();
        reflRT = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, samples: 0, depthBuffer: true, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, generateMipmaps: false });
        const o = { type: THREE.HalfFloatType, samples: 0, depthBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, generateMipmaps: false };
        blurA?.dispose(); blurB?.dispose();
        blurA = new THREE.WebGLRenderTarget(Math.max(16, w >> 1), Math.max(9, h >> 1), o); blurB = new THREE.WebGLRenderTarget(Math.max(16, w >> 1), Math.max(9, h >> 1), o);
      }
      return reflRT;
    };
    const bias = new THREE.Matrix4().set(0.5, 0, 0, 0.5, 0, 0.5, 0, 0.5, 0, 0, 0.5, 0.5, 0, 0, 0, 1);
    const _v = new THREE.Vector3(), _t = new THREE.Vector3(), _u = new THREE.Vector3();

    // ---- the brightness arc (BIBLE 4.1): chorus 1 cold night ... the climax climbing toward white
    const ARC = [[0, 5.0], [23.87, 5.5], [38.4, 4.6], [60.2, 6.0], [72.3, 6.2], [81.4, 6.4], [96.6, 6.6], [111.1, 7.0], [125.7, 7.6],
      [140.24, 3.2], [143, 4.6], [146.5, 8], [152.5, 17], [153, 14], [156.7, 14]];
    const levelAt = t => {
      for (let i = 1; i < ARC.length; i++) if (t < ARC[i][0]) { const [a, x] = ARC[i - 1], [b, y] = ARC[i]; return lerp(x, y, (t - a) / (b - a)); }
      return ARC[ARC.length - 1][1];
    };

    const DBG = new URLSearchParams(location.search).get('halldbg') || '';
    const api = {
      CFG, scene, camera, prints, panel, floor, lines, shell, PANEL, ROWS,
      rows: { ...ROWS, z: r => ROWS.z0 + r * ROWS.dz, ids },
      lights: { rimL, rimR, fill, hemi },
      hazeGLSL: HAZE_GLSL, hazeUniforms: U,
      levelAt,
      resetPrints() { prints.reset(); return prints; },
      // the hall's finish overrides for frameSpec.post (BIBLE 4.3: bloom and halation only on the backlight): the
      // threshold sits above the paper's glow so the sheets stay crisp and only the panel and its haze bloom (the
      // HALL preset's 0.85 / 0.35 / 0.2 laid a grey veil over the audience). o.scale scales both (S54 thins them).
      post(t, o = {}) {
        const k = o.scale ?? 1;
        return { bloom: { thresh: o.thresh ?? CFG.bloomT, amount: CFG.bloomA * k }, halation: CFG.hal * k };
      },
      // the photograph developing, as print images for the audience: VARIANTS darkroom variants of the one photograph
      // (BIBLE 4.5 crop: the face, chin just above the bottom edge, no shoulders), each a strip [blank, stage 1..8] of
      // develop() at the chemistry times DEV_TAUS (halftone null: the post screen is on). Built once (call from a
      // scene's init so the asset use is recorded under the shot). -> { atlas, strips: [[cell...] per variant], taus }
      async photoAtlas() {
        if (this._photoAtlas) return this._photoAtlas;
        const P = await loadPrint(ctx), W = P.src.image.width, H = P.src.image.height;
        const A = faceCrop(P.meta, W, H, { widthIOD: 3.1, eyeLine: 0.4 });
        const B = faceCrop(P.meta, W, H, { widthIOD: 2.7, eyeLine: 0.43 });
        const iod = Math.hypot(P.meta.iris[1][0] - P.meta.iris[0][0], P.meta.iris[1][1] - P.meta.iris[0][1]);
        const Bx = [Math.min(W - B[2], B[0] + 0.12 * iod), B[1], B[2], B[3]];                       // a crop offset variant
        const VARIANTS = [{ crop: A }, { crop: Bx }, { crop: A, stops: 1 }, { crop: A, midLift: 0.55 }];
        const PAPER_Y = 0.864, entries = [], strips = [];
        VARIANTS.forEach((v, vi) => {
          const strip = [entries.length]; entries.push(null);                                           // stage 0: blank
          for (const tau of DEV_TAUS) {
            strip.push(entries.length);
            const e = { mode: 'reflectance', tone: { gain: 1 / PAPER_Y }, texture: null };
            e.prepare = () => {
              const pass = develop(ctx, { key: 'hall-photo-' + vi, src: P.src, certainty: P.cert, crop: v.crop, t: tau, tStart: 0, clock: 'linear',
                halftone: null, stops: v.stops || 0, midLift: v.midLift || 0, texture: { width: 360 } });
              e.texture = pass.texture;
            };
            entries.push(e);
          }
          strips.push(strip);
        });
        const atlas = Prints.buildAtlas(ctx, entries, { cols: 8, rows: Math.ceil(entries.length / 8), cellW: 360, cellH: 463, border: 0.045 });
        return (this._photoAtlas = { atlas, strips, taus: [0, ...DEV_TAUS] });
      },
      // position along a development strip for chemistry time tau (the strip's stages at [0, ...DEV_TAUS])
      stripDensity(tau) {
        const T = [0, ...DEV_TAUS];
        if (tau <= 0) return 0;
        for (let i = 1; i < T.length; i++) if (tau < T[i]) return (i - 1 + (tau - T[i - 1]) / (T[i] - T[i - 1])) / (T.length - 1);
        return 1;
      },
      _avatarMats: new Map(),
      avatarLook(av) {
        const mats = this._avatarMats;
        av.setLook((mesh, orig) => {
          const key = mesh.name;
          if (!mats.has(key)) mats.set(key, hallAvatarMaterial(orig, key, AVU));
          return mats.get(key);
        });
        // the blended hair draws after the sheets (their transparent pass), so its soft edge blends over them
        // DETERMINISM: every avatar mesh gets its own fixed renderOrder (by sorted name). Three orders opaque objects
        // of equal renderOrder by material.id - a global counter, so it depended on which shots had been initialised
        // first in the page - and the hair cap and scalp coincide at the hairline, where the draw order decides the
        // depth-equal pixels (verified: a one-pixel line along the hairline differed between histories).
        Object.keys(av.meshes).sort().forEach((n, i) => { av.meshes[n].renderOrder = (/^hair|brow|lash/.test(n) ? 20 : 1) + i * 0.001; });
        // DETERMINISM: three sorts transparent objects by the view depth of SkinnedMesh.boundingSphere, which it
        // computes once, lazily, from whatever pose the mesh has on its first render - so the order of the blended
        // fringe strands, hair and brows depended on the page's render history (verified: F1000 / F1200 differed in
        // the fringe between a fresh page and an in-order render). A fixed sphere at the root makes every avatar mesh
        // tie on depth, and three then orders them by id (load order): the same in every browser launch. Culling is
        // off for the avatar already (avatar.js). Requested of lane F: set this in avatar.js at load for every shot.
        if (!av._hallSphere) {
          av._hallSphere = new THREE.Sphere(new THREE.Vector3(0, 0, 0), 100);
          for (const mesh of Object.values(av.meshes)) if (mesh.isSkinnedMesh) mesh.boundingSphere = av._hallSphere;
        }
        for (const n of ['teeth', 'tongue']) if (av.meshes[n]) av.meshes[n].visible = false;
        return av;
      },
      // review: per-component GPU cost (gl.finish around each render into a scratch target), logged as a warning
      _profile(cam, W, H) {
        const r = ctx.renderer, gl = r.getContext();
        this._profRT ??= new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 0, depthBuffer: true });
        if (this._profRT.width !== W) this._profRT.setSize(W, H);
        const av = ctx.avatar, parts = { panel, shell, floor, lines, prints: prints.object, avatar: av && av.root.parent === scene ? av.root : null };
        const vis = Object.fromEntries(Object.entries(parts).filter(([, o]) => o).map(([k, o]) => [k, o.visible]));
        const time = (label, only) => {
          for (const [k, o] of Object.entries(parts)) if (o) o.visible = only.includes(k) && vis[k];
          const px = new Uint16Array(4), sync = () => r.readRenderTargetPixels(this._profRT, 0, 0, 1, 1, px);
          r.setRenderTarget(this._profRT); r.setClearColor(0, 1); r.clear(); sync();
          const t0 = performance.now(); r.render(scene, cam); sync();
          return label + ' ' + (performance.now() - t0).toFixed(1);
        };
        const out = [time('none', []), time('panel', ['panel']), time('shell', ['shell']), time('floor', ['floor']), time('lines', ['lines']),
          time('prints', ['prints']), time('avatar', ['avatar']), time('all', Object.keys(parts))];
        for (const [k, o] of Object.entries(parts)) if (o) o.visible = vis[k];
        r.setRenderTarget(null);
        console.warn('HALLPROF ' + W + 'x' + H + ' ' + out.join(' | '));
      },
      update(t, o = {}) {
        const cam = o.camera || camera, r = ctx.renderer, W = ctx.W || 1920, H = ctx.H || 1080;
        // the stand-in is shared across shots: a hall shot that does not ask for him must not inherit him (determinism)
        if (!o.avatar && ctx.avatar && ctx.avatar.root.parent === scene) ctx.avatar.root.visible = false;
        const level = o.level ?? levelAt(t);
        // haze
        const hz = o.haze ?? 1, glow = o.glow ?? 1;
        U.uHzBase.value.set(NIGHT.r, NIGHT.g, NIGHT.b).multiplyScalar(0.6).addScaledVector(new THREE.Vector3(BACKLIGHT.r, BACKLIGHT.g, BACKLIGHT.b), 0.0012 * level);
        U.uHzGlow.value.set(BACKLIGHT.r, BACKLIGHT.g, BACKLIGHT.b).multiplyScalar(CFG.glow * level * glow);
        U.uHzP.value.set(0.022 * hz, 1.4, 1.2, 1); U.uHzT.value = t;
        panelMat.uniforms.uLevel.value = level * CFG.panel;
        floorU.uLevel.value = level; floorU.uT.value = t;
        // rings
        const rings = (o.rings || []).slice(-4);
        floorU.uRingN.value = rings.length;
        rings.forEach((g, i) => floorU.uRings.value[i].set(g.x, g.z, (ctx.tl.frameOf(t) - ctx.tl.frameOf(g.t)) / 24, g.amp ?? 1));
        lineMat.uniforms.uRes.value.set(W, H);
        lineMat.uniforms.uGlint.value.set(BACKLIGHT.r, BACKLIGHT.g, BACKLIGHT.b).multiplyScalar(0.012 * level);
        // prints: light, sway, focus
        const L = prints.light, bl = [BACKLIGHT.r, BACKLIGHT.g, BACKLIGHT.b];
        L.ambient = [0.004, 0.0045, 0.0055].map(v => v * (0.6 + 0.08 * level));
        const sh = { kappa: CFG.kappa, over: CFG.over, overW: CFG.overW, under: CFG.under, key: CFG.key, ...(o.sheets || {}) };
        L.key = { dir: [0, 0.18, 1], color: [0.9, 0.9, 0.88].map(v => v * sh.key) };
        L.back = { pos: [0, PANEL.y, PANEL.z], color: bl.map(v => v * CFG.back * level), near: 2, far: 70,
          shade: { zLast: ROWS.z0 + (ROWS.n - 1) * ROWS.dz, kappa: sh.kappa, over: sh.over, under: sh.under, band: [sh.overW, 0.05], rim: CFG.rim } };
        L.transmission = CFG.trans; L.formation = CFG.form;
        const focus = o.focus ? { ...o.focus, coc: (o.focus.coc || 0) * CFG.dof } : { distance: 20, coc: 0 };
        prints.focus = focus;
        lineMat.uniforms.uFocus.value.set(focus.distance, (focus.coc || 0) * H / 1080);
        panelMat.uniforms.uCoc.value = (focus.coc || 0) * H / 1080 * Math.abs(1 / Math.max(0.1, cam.position.z - PANEL.z) - 1 / focus.distance);
        // sway multiplier and the crash shiver are passed to update() (pure: the props are the scene's)
        const tr = o.tremble;
        const tilt = tr ? (it => {
          const age = (ctx.tl.frameOf(t) - ctx.tl.frameOf(tr.t)) / 24 - Math.max(0, -it.z) / (tr.speed || 1e9);
          return age >= 0 ? (tr.amp ?? 0.02) * Math.sin(age * 17 + it.seed * 6) * Math.exp(-age * 4.5) : 0;
        }) : null;
        const pOpts = { camera: cam, sway: o.sway ?? 1, tilt };
        prints.update(t, pOpts);
        prints.object.visible = !DBG.includes('noprints'); lines.visible = !DBG.includes('nolines');
        if (DBG.includes('noocc')) prints.uniforms.uOcc.value.x = 0;
        if (DBG.includes('noav') && ctx.avatar) ctx.avatar.root.visible = false;
        // stand-in lights: rims from the panel side, a low soft fill from the camera side
        const head = o.head || _v.set(0, 1.6, -8);
        rimL.position.set(head.x - 3.2, head.y + 3.4, head.z - 9); rimL.target.position.copy(head);
        rimR.position.set(head.x + 3.2, head.y + 3.0, head.z - 9); rimR.target.position.copy(head);
        rimL.intensity = rimR.intensity = 0.55 * level * (o.rim ?? 1);
        // the footlight: low, within 30 deg of the lens; the fallback keys from camera left (face half in shadow), the
        // previs for the plate (o.even) lights the face evenly from near the axis
        if (o.even) fill.position.set(head.x - 0.5, 0.55, head.z + 3.4); else fill.position.set(head.x - 1.75, 0.45, head.z + 3.0);
        fill.target.position.copy(head);
        fill.intensity = 0.55 * (o.fill ?? 1);
        hemi.intensity = 0.22;
        for (const l of [rimL, rimR, fill]) l.target.updateMatrixWorld();
        cam.updateMatrixWorld();
        const toView = (from, to, out) => out.subVectors(from, to).normalize().transformDirection(cam.matrixWorldInverse);
        toView(fill.position, fill.target.position, AVU.uAvFillDir.value);
        toView(rimL.position, rimL.target.position, AVU.uAvRimL.value);
        toView(rimR.position, rimR.target.position, AVU.uAvRimR.value);
        AVU.uAvFill.value.set(0.95, 0.94, 0.92).multiplyScalar(0.55 * (o.fill ?? 1));
        AVU.uAvRimCol.value.set(BACKLIGHT.r, BACKLIGHT.g, BACKLIGHT.b).multiplyScalar(0.55 * level * (o.rim ?? 1));
        AVU.uAvAmb.value.set(0.010, 0.011, 0.013).multiplyScalar(0.6 + 0.1 * level);
        AVU.uVeil.value = o.veil || 0;
        // ---- the reflection pass (explicit, before the core renders the layers)
        cam.updateMatrixWorld();
        mirrorCam.copy(cam);
        mirrorCam.position.set(cam.position.x, -cam.position.y, cam.position.z);
        cam.getWorldDirection(_t); _t.y = -_t.y; _t.add(mirrorCam.position);
        _u.set(0, 1, 0).applyQuaternion(cam.quaternion); _u.y = -_u.y;
        mirrorCam.up.copy(_u); mirrorCam.lookAt(_t);
        mirrorCam.updateMatrixWorld(); mirrorCam.projectionMatrix.copy(cam.projectionMatrix); mirrorCam.projectionMatrixInverse.copy(cam.projectionMatrixInverse);
        const rw = Math.max(64, Math.round(W / 2)), rh = Math.max(36, Math.round(H / 2)), rt = reflTarget(rw, rh);
        floorU.uReflMat.value.copy(bias).multiply(mirrorCam.projectionMatrix).multiply(mirrorCam.matrixWorldInverse);
        floorU.uReflPx.value.set(1 / rw, 1 / rh);
        floorU.uRefl.value = rt.texture;
        const av = ctx.avatar, avVis = av && av.root.parent === scene ? av.root.visible : null;
        floor.visible = false;
        if (avVis !== null && !o.reflectAvatar) av.root.visible = false;
        const prevT = r.getRenderTarget(), ac = r.autoClear;
        r.setRenderTarget(rt); r.setClearColor(0x000000, 1); r.autoClear = true; r.clear(); if (!DBG.includes('norefl')) r.render(scene, mirrorCam);
        // streak blur: reflection -> blurA (vertical, fine) -> blurB (vertical, wide, slight horizontal)
        blurMat.uniforms.tSrc.value = rt.texture; blurMat.uniforms.uStep.value.set(0, 2 / rt.height);
        r.setRenderTarget(blurA); r.render(blurScene, blurCam);
        blurMat.uniforms.tSrc.value = blurA.texture; blurMat.uniforms.uStep.value.set(0.6 / blurA.width, 6 / blurA.height);
        r.setRenderTarget(blurB); r.render(blurScene, blurCam);
        floorU.uReflSoft.value = blurB.texture;
        r.setRenderTarget(prevT); r.autoClear = ac;
        floor.visible = true;
        if (avVis !== null) av.root.visible = avVis;
        // the veil: the hall without him, from this camera, at quarter size (only while he condenses out of the light)
        if ((o.veil || 0) > 0.001 && avVis) {
          const bw = Math.max(64, W >> 2), bh = Math.max(36, H >> 2);
          if (!bgRT || bgRT.width !== bw || bgRT.height !== bh) { bgRT?.dispose(); bgRT = new THREE.WebGLRenderTarget(bw, bh, { type: THREE.HalfFloatType, samples: 0, depthBuffer: true, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter }); }
          av.root.visible = false;
          const pt = r.getRenderTarget(), pa = r.autoClear;
          r.setRenderTarget(bgRT); r.setClearColor(0x000000, 1); r.autoClear = true; r.clear(); r.render(scene, cam);
          r.setRenderTarget(pt); r.autoClear = pa;
          av.root.visible = true;
          AVU.uAvBg.value = bgRT.texture; AVU.uAvRes.value.set(W, H);
        }
        if (DBG.includes('prof')) this._profile(cam, W, H);
        return this;
      },
    };
    return api;
  },
};
