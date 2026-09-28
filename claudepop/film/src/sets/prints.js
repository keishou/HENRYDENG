// prints.js - many hanging prints (lane E; SHARED with lane D). BIBLE 4.8 HALL / LINE, 9.4 (API frozen on day 0:
// constructor, layout(), set(), update(), object; everything else here is additive).
//
// One InstancedMesh of curled paper sheets (a 4 x 6 segment grid bent in the vertex shader: cylindrical curl across the
// width, a lifted bottom edge, a sag between the two clips), shaded by a small custom model (front light + backlight
// transmission through the paper, the "glow"; gloss; per-print flash), with analytic anti-aliased edges (the sheets are
// drawn back to front with blending, so no MSAA is needed for them) and a cheap defocus (texture LOD + edge softness
// from a circle of confusion). Paperclips: two per print; textured impostor quads (instanced) beyond `clipNear` metres
// from the camera, real 1 mm wire meshes (a small pool) inside it - never bulk-instanced clip meshes (BIBLE 9.6).
//
// Everything is a pure function of (t, the set() state): call reset() then set() for every print you change at the
// start of frame(), then update(t, { camera }). No state is carried between frames (BIBLE 9.2).
//
// ------------------------------------------------------------------------------------------------ API
//   const prints = new Prints(ctx, { max = 400, atlas = null, size = [0.56, 0.72], ...opts })
//       atlas  { texture, cols, rows, inset = 0.004 } | null     cells hold print images (paper-relative reflectance,
//              gamma-2 encoded 8-bit, red channel: white = paper; build it with Prints.buildAtlas); cell index =
//              row * cols + col, row 0 at the TOP
//       size   [w, h] metres of every sheet (0.56 x 0.72 hall, 0.28 x 0.36 line); a sheet hangs 10 mm below its wire
//       opts   (additive) clipNear = 2 (m: real clip meshes inside, impostors beyond), clipPool = 16 (real meshes),
//              haze = { glsl, uniforms } | null: a GLSL chunk defining  vec4 hazeAt(vec3 worldPos) -> (inscatter rgb,
//                     transmittance), applied per vertex; null = three's scene fog (FogExp2 / Fog) if the scene has one
//              border = 0: paper margin (fraction of the width) around the image, for raw atlases only (buildAtlas cells
//                     carry their border)
//   prints.layout(kind, opts) -> ids [int]           (appends; call once, in init)
//       'rows'  { z0 = -1.5, dz = -1.5, rows = 10, xs = [[-5.4, -1.4], [1.4, 5.4]], y = 1.75, perLine = 5, stagger = 0,
//               yJitter = 0 }   drying lines ACROSS the hall (BIBLE 4.8): one wire per [x0, x1] per row at height y;
//               sheets face +Z, evenly spaced; odd rows shift outward by `stagger`, even rows inward; yJitter = +- wire
//               height per line. item: { row, line, col (0 = nearest the aisle), side (-1 | 1), wireY }. A symmetric
//               rows layout also sets the occlusion hint (below).
//       'line'  { x0 = -1, x1 = 1, y = 1.9, z = 0, count = 5, yaw = 0 }   one wire; item.col = index along it
//       'grid'  { x0 = 0, y0 = 0, dx = 0.7, dy = 0.9, cols = 4, rows = 3, z = 0, yaw = 0 }   a wall; y0 = row 0's wire
//   prints.set(id, props)                            merge props into the print's state:
//       tex      atlas cell index | [cells] (a development strip: density picks between them) | -1 / null (blank paper)
//       density  0..1 (default 1 with a tex). Single cell: optical density scaled (D' = density x D); strip: position
//                along the strip (0 = first cell ... 1 = last; linear mix of the two nearest cells)
//       gloss    0..1 glossier paper: deeper blacks, a soft specular sheen of the key light over the curl
//       sway     radians of the seeded air sway about the wire (default 0.018); freq Hz (default 0.3)
//       turn     radians about the vertical through the wire point (S33: every print turned to face the aisle)
//       tilt     radians about the wire (added to the sway)       curl  (default seeded 0.25..0.55; + = edges toward +Z)
//       clip     true (default) | false: the two paperclips at the top corners
//       fall     { t0, seed = id, floor = 0, drift = 1 } | null: slips its clips at t0, flutters down (terminal velocity,
//                pendulum swing), settles flat face up on the floor (closed form, by frame)
//       capture  { t, cell, flash = 0.1, density = 1 } | null: from frame(t) the sheet shows `cell`, with a white flash
//                on the sheet for `flash` s (S54 Muybridge captures)
//       recap    { t0, t1, cell, density = 1 } | null: shows `cell` during frames [t0, t1) (S54 recap flashes)
//       flash    0..1 extra white (emissive)        light  multiplier of this sheet's light (1)        hidden  not drawn
//   prints.reset(ids = all)                          props back to their defaults: call it at the start of frame()
//   prints.update(t, { camera, sway = 1, tilt = null } = {})   writes the instance data for time t. camera = the render
//                                                    camera (back-to-front order, clip LOD); sway multiplies every
//                                                    sheet's sway; tilt(item, t) -> extra radians about the wire. -> this
//   prints.object                                    THREE.Group to add to a scene (sheets, clip impostors, clip meshes)
//   prints.items[id]                                 { id, x, y, z, yaw, row, line, col, side, seed, props }
//   prints.light = { ... }                           see LIGHT below (plain values, set per frame)
//   prints.focus = { distance, coc }                 cheap defocus: coc = blur in output px per dioptre (0 = off)
//   prints.hang = [yaw, pitch, roll] | null          static seeded settle of each sheet on its clips (default [0.07,
//                                                    0.035, 0.012] rad: no two sheets hang alike)
//   prints.setAtlas(atlas)   prints.setOcclusion({ z0, dz, rows, xIn, xOut, pitch, halfW, top, bottom, stagger } | null)
//       occlusion hint (rows seen from in front): a fragment whose ray to the camera crosses a sheet of the row in front
//       is discarded before shading (SwiftShader shades hidden fragments: this is most of the audience's saving). It
//       switches itself off for a frame in which any sheet turns, falls, tilts > 0.02 rad or sways > 0.04 rad.
//   prints.transform(id, t) -> THREE.Matrix4 (the sheet's frame: origin on the wire, z = image normal)
//   prints.corners(id, t) -> [TL, TR, BR, BL] world THREE.Vector3      prints.visibleIn(camera, id, t, margin) -> bool
//   Prints.buildAtlas(ctx, entries, { cols = 8, rows = 8, cellW = 360, cellH = 463, border = 0.045, inset })
//       -> { texture, cols, rows, inset, target, cellW, cellH }. entries[i] = null (blank paper) | { texture,
//       rect = [u0, v0, u1, v1] (source uv, v up), clip = [u0, v0, u1, v1] (outside reads empty), mode = 'photo' |
//       'silhouette' (white matte -> dark figure, tone.density) | 'reflectance' (linear reflectance, e.g. a develop()
//       pass texture) | 'paper', fit = 'cover' | 'contain', tone = { gamma, gain, lift, levels, density }, mirror, border,
//       prepare() (called just before the cell is drawn) }. Rendered once (init only).
//   Prints.clipTexture(), Prints.toothTexture()      the paperclip impostor and the paper tooth, computed in JS
//
// LIGHT (prints.light; linear RGB; the set or scene writes it each frame before update()):
//   ambient [r, g, b]; key { dir [x, y, z] (toward the light), color [r, g, b] } (front light on the image side);
//   back { pos [x, y, z] (light centre), color [r, g, b], near, far (irradiance ramps from far -> near distance),
//          shade: { zLast, kappa, over, under, band: [overW, underW], rim } | null } - light through the paper from
//          behind: exp(-kappa x rows behind zLast) + the spill over the top / under the bottom edge (falling off over
//          band metres) + an optional thin luminous top edge (rim);
//   transmission 0..1 (paper translucency, default 0.35); formation 0..1 (cloudy fibre in transmission, 0.2);
//   paper [r, g, b] (default PAPER), ink [r, g, b] (default D-max 2.0)
import * as THREE from 'three';

const PAPER_HEX = '#F2EFE8';
const SEG_X = 4, SEG_Y = 6, PAD = 0.03;   // geometry grid, AA margin (fraction of the sheet) outside the paper
const DEF = { tex: -1, density: null, gloss: 0, sway: 0.018, freq: 0.3, turn: 0, tilt: 0, curl: null, clip: true, fall: null,
  capture: null, recap: null, flash: 0, light: 1, hidden: false };

// ------------------------------------------------------------------------------------------------ shaders
// Cost notes (SwiftShader, no early-z): the fragment work is what counts, times the overdraw of 38 compressed rows.
// Slowly varying terms (light, transmission through the rows behind, haze, gloss sheen) are per vertex; the fragment
// does the edge coverage, the image (one or two gamma-2 texels, scalar), the spill bands and the paper texture. With
// an occlusion hint (rows layouts), a fragment whose ray to the camera crosses a sheet of the row in front is
// discarded before any of that.
const VERT = /* glsl */`
  attribute vec4 aCell;   // cell A, cell B, mix, density (cell < 0 = blank)
  attribute vec4 aLook;   // gloss, curl, flash, light
  attribute float aSeed;
  uniform vec2 uSize;
  uniform vec3 uAmbient, uKeyDir, uKeyCol, uBackPos, uBackCol;
  uniform vec2 uBackRange; uniform float uTrans; uniform vec4 uBackShape;
  varying vec2 vUv; varying vec3 vW; varying vec4 vCell, vLook; varying float vSeed, vDepth;
  varying vec3 vFront, vBackK, vBackFace; varying float vThru, vSpec;
  #HAZE_VDECL
  void main(){
    vec2 p = position.xy;                       // unit sheet: x -0.5..0.5, y -1..0 (top edge at y = 0), + pad
    vUv = vec2(p.x + .5, 1. + p.y);
    float cx = clamp(p.x * 2., -1., 1.), dn = clamp(-p.y, 0., 1.);
    float c = aLook.y, k = uSize.x / .56;
    // cylindrical curl across the width (edges forward), stronger toward the free bottom edge; the bottom edge lifts;
    // a sag of the top edge between the two clips
    float z = c * (.030 * cx * cx * (.45 + .55 * dn) + .018 * dn * dn * dn);
    float dzdx = c * (.030 * 2. * cx * 2. * (.45 + .55 * dn));
    float dzdy = -c * (.030 * cx * cx * .55 + .018 * 3. * dn * dn);
    float sag = .006 * (1. - cx * cx) * (1. - smoothstep(0., .25, dn));
    vec3 lp = vec3(p.x * uSize.x, p.y * uSize.y - sag - .010, z * k);
    vec3 ln = normalize(vec3(-dzdx * k / uSize.x, -dzdy * k / uSize.y, 1.));
    vec4 wp = modelMatrix * instanceMatrix * vec4(lp, 1.);
    vW = wp.xyz;
    vec3 N = normalize(mat3(modelMatrix) * mat3(instanceMatrix) * ln);
    vCell = aCell; vLook = aLook; vSeed = aSeed;
    vec4 mv = viewMatrix * wp; vDepth = -mv.z;
    // light terms (per vertex)
    vec3 toB = uBackPos - wp.xyz; float dB = length(toB); toB /= dB;
    float irr = 1. - smoothstep(uBackRange.x, uBackRange.y, dB);
    float nb = dot(N, toB);
    vFront = uAmbient + uKeyCol * max(dot(N, normalize(uKeyDir)), 0.);
    vBackK = uBackCol * irr * uTrans * max(-nb, 0.);
    vBackFace = uAmbient * .6 + uBackCol * irr * max(nb, 0.) * (1. - uTrans * .6) + uKeyCol * max(dot(-N, normalize(uKeyDir)), 0.) * .6;
    float behind = uBackShape.y > 0. ? max(0., (wp.z - uBackShape.x)) / 1.5 : 0.;
    vThru = exp(-uBackShape.y * behind);
    vec3 V = normalize(cameraPosition - wp.xyz), Hk = normalize(normalize(uKeyDir) + V);
    vSpec = pow(max(dot(N, Hk), 0.), 24.) * aLook.x;
    #HAZE_VAPPLY
    gl_Position = projectionMatrix * mv;
  }`;

const FRAG = /* glsl */`
  uniform sampler2D uAtlas; uniform vec4 uAtlasInfo;      // cols, rows, inset, on
  uniform vec2 uSize; uniform float uBorder;
  uniform vec3 uKeyCol, uPaper, uInk;
  uniform vec4 uBackShape, uBackBand; uniform float uEdgeGlow, uForm;
  uniform vec3 uFocus;                                    // distance, coc px per dioptre
  uniform vec4 uOcc, uOccL; uniform vec3 uOccY;           // occlusion hint (rows): on, z0, dz, rows | x in, x out, pitch, half w | top, bottom, stagger
  uniform sampler2D uTooth;
  varying vec2 vUv; varying vec3 vW; varying vec4 vCell, vLook; varying float vSeed, vDepth;
  varying vec3 vFront, vBackK, vBackFace; varying float vThru, vSpec;
  #HAZE_FDECL
  // paper-relative reflectance of cell c at paper uv (v up): gamma-2 texels (decode = square), scalar
  float cellRefl(float c, vec2 uv, vec2 gx, vec2 gy){
    float cols = uAtlasInfo.x, rows = uAtlasInfo.y, ins = uAtlasInfo.z;
    float col = mod(c, cols), row = floor(c / cols);
    vec2 cuv = mix(vec2(ins), vec2(1. - ins), uv);
    vec2 auv = vec2((col + cuv.x) / cols, 1. - (row + 1. - cuv.y) / rows);
    float g = textureGrad(uAtlas, auv, gx, gy).r;
    return g * g;
  }
  void main(){
    // occlusion hint: hidden behind a sheet of the row in front (regular rows, the camera in front of them)
    if (uOcc.x > .5) {
      float r = floor((vW.z - uOcc.y) / uOcc.z + .5);
      float zf = uOcc.y + (r - 1.) * uOcc.z;
      if (r >= 1. && r < uOcc.w && cameraPosition.z > zf + .05) {
        float s = (zf - cameraPosition.z) / (vW.z - cameraPosition.z);
        vec3 q = cameraPosition + (vW - cameraPosition) * s;
        float ax = abs(q.x) - uOccL.x - (mod(r - 1., 2.) > .5 ? uOccY.z : -uOccY.z);
        float u = ax / uOccL.z;
        if (q.y < uOccY.x - .03 && q.y > uOccY.y + .03 && ax > 0. && abs(q.x) < uOccL.y
            && abs(fract(u) - .5) * uOccL.z < uOccL.w - .03) discard;
      }
    }
    // circle of confusion (px) -> edge softness and texture blur
    float coc = uFocus.y > 0. ? uFocus.y * abs(1. / max(vDepth, .05) - 1. / uFocus.x) : 0.;
    // paper edge (metres from the nearest edge), anti-aliased over one pixel (+ the defocus)
    vec2 em = min(vUv, 1. - vUv) * uSize;
    float e = min(em.x, em.y);
    vec2 dux = dFdx(vUv), duy = dFdy(vUv);
    float fw = max((abs(dux.x) + abs(duy.x)) * uSize.x, (abs(dux.y) + abs(duy.y)) * uSize.y);
    float soft = fw * (1. + coc);
    float cov = smoothstep(-.5 * soft, .5 * soft, e);
    if (cov < .003) discard;
    vec2 uv = clamp(vUv, 0., 1.);
    // the image (scalar reflectance, paper = 1)
    float refl = 1.;
    if (vCell.x >= 0. && uAtlasInfo.w > .5) {
      vec2 bb = vec2(uBorder, uBorder * uSize.x / uSize.y);
      vec2 iuv = (uv - bb) / (1. - 2. * bb);
      float gs = exp2(log2(1. + coc * .5));
      vec2 gx = dux / (1. - 2. * bb) * vec2(1. / uAtlasInfo.x, 1. / uAtlasInfo.y) * gs, gy = duy / (1. - 2. * bb) * vec2(1. / uAtlasInfo.x, 1. / uAtlasInfo.y) * gs;
      vec2 ci = clamp(iuv, 0., 1.);
      float a = cellRefl(vCell.x, ci, gx, gy);
      if (vCell.y >= 0. && vCell.z > 0.) a = mix(a, cellRefl(vCell.y, ci, gx, gy), vCell.z);
      if (uBorder > 0. && (iuv.x < 0. || iuv.x > 1. || iuv.y < 0. || iuv.y > 1.)) a = 1.;
      // optical density scaling (single cells: density x D); gloss deepens the blacks
      float kd = vCell.w * (1. + .28 * vLook.x);
      refl = exp2(log2(max(a, 1e-3)) * kd);
    }
    vec4 tx = texture2D(uTooth, uv * uSize * 7. + vSeed * 3.1);
    float tooth = tx.r, form = texture2D(uTooth, uv * uSize * .9 + vSeed * 5.7).r;
    refl *= .97 + .03 * tooth;
    vec3 base = mix(uInk, uPaper, refl);
    vec3 col;
    if (gl_FrontFacing) {
      // transmitted backlight: through the rows behind (per vertex) + spill over the top / under the bottom edge
      float dTop = (1. - uv.y) * uSize.y, dBot = uv.y * uSize.y;
      float over = uBackShape.z * (exp2(-1.4427 * dTop / uBackBand.x) + .25 * exp2(-1.4427 * dTop / (uBackBand.x * 5.)));
      float under = uBackShape.w * exp2(-1.4427 * dBot / uBackBand.y);
      float cxs = abs(uv.x * 2. - 1.);
      float curlT = 1. - .55 * vLook.y * smoothstep(.35, 1., cxs) * (.5 + .5 * (1. - uv.y));   // curled edges transmit less
      float rim = uEdgeGlow * exp2(-1.4427 * dTop / max(fw * 1.4, 1e-5));
      float vary = .78 + .32 * fract(vSeed * 7.31);
      vec3 trans = vBackK * (.8 + .2 * tooth) * (1. + uForm * (form - .5)) * ((vThru + over + under) * curlT + rim) * vary;
      col = base * (vFront + trans) + uKeyCol * vSpec * .35;
    } else col = uPaper * vBackFace * (.65 + .35 * sqrt(refl));      // the back: paper, the image faint through
    col *= vLook.w;
    col += vec3(6.) * vLook.z;                // flash (HDR white)
    #HAZE_FAPPLY
    gl_FragColor = vec4(col, cov);
  }`;

const HAZE_FOG = { decl: '#include <fog_pars_fragment>', apply: 'gl_FragColor = vec4(col, 1.); \n #include <fog_fragment>\n col = gl_FragColor.rgb;' };

// ------------------------------------------------------------------------------------------------ clip impostors
const CLIP_VERT = /* glsl */`
  attribute vec4 aClip;   // alpha, seed, -, -
  varying vec2 vUv; varying float vA; varying vec3 vW;
  #include <fog_pars_vertex>
  void main(){ vUv = uv; vA = aClip.x;
    vec4 wp = modelMatrix * instanceMatrix * vec4(position, 1.); vW = wp.xyz;
    vec4 mvPosition = viewMatrix * wp;
    #include <fog_vertex>
    gl_Position = projectionMatrix * mvPosition; }`;
const CLIP_FRAG = /* glsl */`
  uniform sampler2D uClip; uniform vec3 uAmbient, uKeyCol, uBackCol; uniform float uClipSheen;
  varying vec2 vUv; varying float vA; varying vec3 vW;
  #HAZE_DECL
  void main(){
    vec4 c = texture2D(uClip, vUv);
    float a = c.a * vA; if (a < .01) discard;
    // steel: dark with a bright upper edge (the backlight catching the wire); c.r carries the edge highlight
    vec3 col = vec3(.035) + (uAmbient * .5 + uKeyCol * .25) * .5 + uBackCol * uClipSheen * c.r;
    #HAZE_APPLY
    gl_FragColor = vec4(col, a);
  }`;

// ------------------------------------------------------------------------------------------------ helpers
const smooth = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
function h1(n) { n = (n ^ 61) ^ (n >>> 16); n = Math.imul(n, 9); n ^= n >>> 4; n = Math.imul(n, 0x27d4eb2d); n ^= n >>> 15; return (n >>> 0) / 4294967296; }
function noise1(t, seed) {   // smooth value noise [-1, 1] (same construction as avatar.js noise1)
  const i = Math.floor(t), f = t - i, u = f * f * f * (f * (f * 6 - 15) + 10);
  const a = h1(i * 374761393 + seed * 668265263), b = h1((i + 1) * 374761393 + seed * 668265263);
  return (a + (b - a) * u) * 2 - 1;
}
const linOf = hex => { const c = new THREE.Color(hex); return [c.r, c.g, c.b]; };

// the classic 33 mm paperclip as a 2D path (metres; x across, y up, top at y = 0): three nested U-turns, the wire
// starting at the inner tongue and ending on the outer leg two thirds down
function clipPath() {
  const pts = [], mm = 0.001;
  const arc = (cx, cy, r, a0, a1, n = 10) => { for (let i = 0; i <= n; i++) { const a = a0 + (a1 - a0) * i / n; pts.push([(cx + r * Math.cos(a)) * mm, (cy + r * Math.sin(a)) * mm]); } };
  const P = (x, y) => pts.push([x * mm, y * mm]);
  P(-1.5, -13); P(-1.5, -3.5); arc(0, -3.5, 1.5, Math.PI, 0);          // inner tongue, small top turn
  P(1.5, -29.5); arc(-1.25, -29.5, 2.75, 0, -Math.PI);                    // down, bottom turn
  P(-4.0, -4.0); arc(0, -4.0, 4.0, Math.PI, 0);                            // up the outside, big top turn
  P(4.0, -22);                                                              // the outer leg
  return { pts, W: 0.0105, L: 0.0345 };
}

export class Prints {
  constructor(ctx, { max = 400, atlas = null, size = [0.56, 0.72], clipNear = 2, clipPool = 16, haze = null, border = 0 } = {}) {
    this.ctx = ctx; this.max = max; this.atlas = atlas; this.size = size; this.clipNear = clipNear; this.border = border;
    this.items = [];
    this.focus = { distance: 10, coc: 0 };
    this.hang = [0.07, 0.035, 0.012];                 // yaw, pitch, roll jitter (rad): no two sheets hang alike
    this.light = { ambient: [0.02, 0.022, 0.025], key: { dir: [0, 0.3, 1], color: [0.2, 0.2, 0.2] },
      back: { pos: [0, 2.5, -58], color: [0, 0, 0], near: 5, far: 80 }, transmission: 0.35, paper: linOf(PAPER_HEX), ink: [0.011, 0.011, 0.012] };
    const hz = haze ? { decl: haze.glsl, apply: 'vec4 hz_ = hazeAt(vW); col = col * hz_.a + hz_.rgb;' } : HAZE_FOG;
    // the sheets take the haze per vertex (it varies slowly across a sheet; per-pixel it was most of their cost)
    const hzv = haze ? { vdecl: haze.glsl + '\nvarying vec4 vHz;', vapply: 'vHz = hazeAt(vW);', fdecl: 'varying vec4 vHz;', fapply: 'col = col * vHz.a + vHz.rgb;' }
      : { vdecl: '#include <fog_pars_vertex>', vapply: 'vec4 mvPosition = mv;\n#include <fog_vertex>', fdecl: HAZE_FOG.decl, fapply: HAZE_FOG.apply };
    const useFog = !haze;
    // sheets
    const g = new THREE.PlaneGeometry(1 + 2 * PAD, 1 + 2 * PAD * size[0] / size[1], SEG_X, SEG_Y).translate(0, -0.5, 0);
    this.aCell = new THREE.InstancedBufferAttribute(new Float32Array(max * 4), 4);
    this.aLook = new THREE.InstancedBufferAttribute(new Float32Array(max * 4), 4);
    this.aSeed = new THREE.InstancedBufferAttribute(new Float32Array(max), 1);
    for (const a of [this.aCell, this.aLook, this.aSeed]) a.setUsage(THREE.DynamicDrawUsage);
    g.setAttribute('aCell', this.aCell); g.setAttribute('aLook', this.aLook); g.setAttribute('aSeed', this.aSeed);
    this.uniforms = {
      uAtlas: { value: null }, uAtlasInfo: { value: new THREE.Vector4(1, 1, 0.004, 0) },
      uSize: { value: new THREE.Vector2(size[0], size[1]) }, uRes: { value: new THREE.Vector2(1920, 1080) }, uPad: { value: PAD },
      uBorder: { value: border },
      uAmbient: { value: new THREE.Vector3() }, uKeyDir: { value: new THREE.Vector3(0, 0.3, 1) }, uKeyCol: { value: new THREE.Vector3() },
      uBackPos: { value: new THREE.Vector3() }, uBackCol: { value: new THREE.Vector3() }, uBackRange: { value: new THREE.Vector2(5, 80) },
      uTrans: { value: 0.35 }, uPaper: { value: new THREE.Vector3() }, uInk: { value: new THREE.Vector3() },
      uBackShape: { value: new THREE.Vector4(0, 0, 0, 0) }, uBackBand: { value: new THREE.Vector4(1, 2, 0, 0) }, uEdgeGlow: { value: 0 }, uForm: { value: 0.2 },
      uOcc: { value: new THREE.Vector4(0, 0, 1, 0) }, uOccL: { value: new THREE.Vector4(0, 0, 1, 0) }, uOccY: { value: new THREE.Vector3(0, 0, 0) },
      uFocus: { value: new THREE.Vector3(10, 0, 1) }, uClip: { value: Prints.clipTexture() }, uClipSheen: { value: 0.6 },
      uTooth: { value: Prints.toothTexture() },
      ...(haze ? haze.uniforms : {}),
      ...(useFog ? THREE.UniformsUtils.clone(THREE.UniformsLib.fog) : {}),
    };
    const mat = new THREE.ShaderMaterial({
      uniforms: this.uniforms, vertexShader: VERT.replace('#HAZE_VDECL', hzv.vdecl).replace('#HAZE_VAPPLY', hzv.vapply),
      fragmentShader: FRAG.replace('#HAZE_FDECL', hzv.fdecl).replace('#HAZE_FAPPLY', hzv.fapply),
      transparent: true, depthWrite: true, side: THREE.DoubleSide, fog: useFog,
    });
    mat.extensions = { derivatives: true };
    this.mesh = new THREE.InstancedMesh(g, mat, max);
    this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.mesh.count = 0; this.mesh.frustumCulled = false; this.mesh.renderOrder = 10;
    // clip impostors (two per print)
    const cp = clipPath(), cg = new THREE.PlaneGeometry(cp.W, cp.L).translate(0, -cp.L / 2 + 0.003, 0);
    this.aClip = new THREE.InstancedBufferAttribute(new Float32Array(max * 2 * 4), 4); this.aClip.setUsage(THREE.DynamicDrawUsage);
    cg.setAttribute('aClip', this.aClip);
    const cmat = new THREE.ShaderMaterial({ uniforms: this.uniforms, vertexShader: CLIP_VERT,
      fragmentShader: CLIP_FRAG.replace('#HAZE_DECL', hz.decl).replace('#HAZE_APPLY', hz.apply.replace(/vW/g, 'vW')),
      transparent: true, depthWrite: false, side: THREE.DoubleSide, fog: useFog });
    this.clips = new THREE.InstancedMesh(cg, cmat, max * 2);
    this.clips.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.clips.count = 0; this.clips.frustumCulled = false; this.clips.renderOrder = 11;
    // real clip meshes (near the camera only)
    const path = new THREE.CatmullRomCurve3(cp.pts.map(([x, y]) => new THREE.Vector3(x, y + 0.0027, 0)), false, 'catmullrom', 0.2);
    const tube = new THREE.TubeGeometry(path, 140, 0.0005, 6, false);
    const steel = new THREE.MeshStandardMaterial({ color: 0x9aa0a6, metalness: 1, roughness: 0.32 });
    this.clipMeshes = [];
    this.object = new THREE.Group(); this.object.add(this.mesh, this.clips);
    for (let i = 0; i < clipPool; i++) { const m = new THREE.Mesh(tube, steel); m.visible = false; m.matrixAutoUpdate = false; this.clipMeshes.push(m); this.object.add(m); }
    this.clipMaterial = steel;
    if (atlas) this.setAtlas(atlas);
    this._m = new THREE.Matrix4(); this._q = new THREE.Quaternion(); this._e = new THREE.Euler(0, 0, 0, 'YXZ');
    this._v = new THREE.Vector3(); this._s = new THREE.Vector3(1, 1, 1); this._order = [];
  }

  // occlusion hint for a regular 'rows' layout seen from in front (the hall): { z0, dz, rows, xIn, xOut, pitch, halfW,
  // top, bottom, stagger } (world metres; top / bottom = the sheets' span) | null. Set automatically by layout('rows').
  setOcclusion(o) {
    const U = this.uniforms;
    if (!o) { U.uOcc.value.set(0, 0, 1, 0); return this; }
    U.uOcc.value.set(1, o.z0, o.dz, o.rows); U.uOccL.value.set(o.xIn, o.xOut, o.pitch, o.halfW); U.uOccY.value.set(o.top, o.bottom, o.stagger || 0);
    return this;
  }

  setAtlas(atlas) {
    this.atlas = atlas;
    this.uniforms.uAtlas.value = atlas ? atlas.texture : null;
    this.uniforms.uAtlasInfo.value.set(atlas ? atlas.cols : 1, atlas ? atlas.rows : 1, atlas ? (atlas.inset ?? 0.004) : 0, atlas ? 1 : 0);
    return this;
  }

  // ---------------------------------------------------------------------------------------------- layout
  layout(kind, o = {}) {
    const ids = [], [w, h] = this.size;
    const add = (x, y, z, meta) => {
      if (this.items.length >= this.max) return;
      const id = this.items.length;
      ids.push(id);
      this.items.push({ id, x, y, z, yaw: meta.yaw || 0, row: 0, line: 0, col: 0, side: Math.sign(x) || 1, ...meta, props: { ...DEF },
        seed: h1(id * 7919 + 17) });
    };
    if (kind === 'rows') {
      const { z0 = -1.5, dz = -1.5, rows = 10, xs = [[-5.4, -1.4], [1.4, 5.4]], y = 1.75, perLine = 5, stagger = 0, yJitter = 0 } = o;
      for (let r = 0; r < rows; r++) xs.forEach(([x0, x1], li) => {
        const st = (r % 2 ? 1 : -1) * stagger, yr = y + yJitter * (h1(r * 977 + li * 31 + 5) * 2 - 1);
        for (let i = 0; i < perLine; i++) {
          // col counts outward from the aisle (0 = the sheet nearest the aisle); odd rows shift outward by `stagger`
          const k = Math.abs(x0) < Math.abs(x1) ? i : perLine - 1 - i, out = Math.sign(x0 + x1) || 1;
          add(x0 + (x1 - x0) * (i + 0.5) / perLine + out * st, yr, z0 + r * dz, { row: r, line: li, col: k, side: out, wireY: yr });
        }
      });
      // symmetric lines about the aisle -> an analytic occlusion hint (see setOcclusion); jitter is covered by a margin
      const [ax0, ax1] = [Math.min(Math.abs(xs[0][0]), Math.abs(xs[0][1])), Math.max(Math.abs(xs[0][0]), Math.abs(xs[0][1]))];
      const sym = xs.every(([a, b]) => Math.abs(Math.min(Math.abs(a), Math.abs(b)) - ax0) < 1e-6 && Math.abs(Math.max(Math.abs(a), Math.abs(b)) - ax1) < 1e-6);
      if (sym && this.items.length === rows * xs.length * perLine) {
        const pitch = (ax1 - ax0) / perLine;
        this.setOcclusion({ z0, dz, rows, xIn: ax0, xOut: ax1, pitch, halfW: w / 2, top: y - 0.010 - yJitter, bottom: y - 0.010 - h + yJitter, stagger });
        this._occ = true;
      }
    } else if (kind === 'line') {
      const { x0 = -1, x1 = 1, y = 1.9, z = 0, count = 5, yaw = 0 } = o;
      for (let i = 0; i < count; i++) add(x0 + (x1 - x0) * (i + 0.5) / count, y, z, { col: i, yaw });
    } else if (kind === 'grid') {
      const { x0 = 0, y0 = 0, dx = 0.7, dy = 0.9, cols = 4, rows = 3, z = 0, yaw = 0 } = o;
      for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) add(x0 + c * dx, y0 - r * dy, z, { row: r, col: c, yaw });
    }
    return ids;
  }

  set(id, props) { const it = this.items[id]; if (it) Object.assign(it.props, props); return this; }
  reset(ids = null) {
    if (ids) for (const id of ids) { if (this.items[id]) this.items[id].props = { ...DEF }; }
    else for (const it of this.items) it.props = { ...DEF };
    return this;
  }

  // ---------------------------------------------------------------------------------------------- motion
  // the sheet's frame at time t: origin on the wire above the top centre (the paper hangs 10 mm below it), x across,
  // y up, z = the image normal. Sway = rotation about the wire (x), a smaller twist about the vertical, both seeded
  // value noise of t; fall = a closed-form flutter (terminal-velocity descent, pendulum swing) that lies flat on landing.
  transform(id, t, out = new THREE.Matrix4(), ex = null) {
    const it = this.items[id], p = it.props, s = it.seed, [, h] = this.size, k = Math.floor(s * 1e6);
    const amp = (p.sway ?? 0.018) * (ex && ex.sway !== undefined ? ex.sway : 1), fq = p.freq ?? 0.3;
    const sway = amp * (0.8 * noise1(t * fq + s * 91.7, k) + 0.2 * noise1(t * fq * 2.3 + 4.1, k + 3));
    const twist = amp * 0.35 * noise1(t * fq * 0.7 + 17.3, k + 5);
    const hang = this.hang;   // static seeded settle of each sheet on its clips (yaw, pitch, roll amplitudes, radians)
    const jy = hang ? hang[0] * (h1(k + 101) * 2 - 1) : 0, jp = hang ? hang[1] * (h1(k + 202) * 2 - 1) : 0, jr = hang ? hang[2] * (h1(k + 303) * 2 - 1) : 0;
    let x = it.x, y = it.y, z = it.z, yaw = it.yaw + (p.turn || 0) + twist + jy, pitch = sway + jp + (p.tilt || 0) + (ex && ex.tilt ? ex.tilt(it, t) : 0), roll = jr;
    const F = this.ctx.tl ? (T => this.ctx.tl.frameOf(T)) : (T => Math.round(T * 24));
    if (p.fall && F(t) >= F(p.fall.t0)) {
      const fs = p.fall.seed ?? id, dr = p.fall.drift ?? 1, floor = p.fall.floor ?? 0;
      const tau = (F(t) - F(p.fall.t0)) / 24, vT = 0.9, T0 = 0.35;
      const drop = τ => vT * (τ - T0 * (1 - Math.exp(-τ / T0)));
      const ph = h1(fs * 131 + 7) * 6.283, om = 3.2 + 1.4 * h1(fs * 17 + 3);
      // landing: the bottom edge reaches the floor
      const reach = y - 0.010 - h - floor;
      let tl = 0; while (tl < 20 && drop(tl) < reach) tl += 1 / 96;
      const tt = Math.min(tau, tl);
      const A = 0.16 * dr * (1 - Math.exp(-tt / 0.4));
      x += A * Math.sin(om * tt + ph) + 0.25 * tt * (h1(fs * 5 + 1) - 0.5) * dr;
      z += 0.3 * tt * (h1(fs * 3 + 9) - 0.2) * dr;
      roll = 0.45 * Math.cos(om * tt + ph) * (1 - Math.exp(-tt / 0.3));
      pitch += 0.6 * (1 - Math.exp(-tt / 0.6)) + 0.2 * Math.sin(om * 0.5 * tt);
      y -= drop(tt);
      if (tau > tl) {                                 // settle flat, face up, over 0.3 s
        const u = smooth((tau - tl) / 0.3);
        pitch = pitch + (-Math.PI / 2 - pitch) * u; roll *= 1 - u;
        y = y + (floor + 0.0015 - y) * u;
      }
    }
    this._e.set(pitch, yaw, roll, 'YXZ');
    this._q.setFromEuler(this._e);
    this._v.set(x, y, z);
    return out.compose(this._v, this._q, this._s);
  }

  corners(id, t) {
    const m = this.transform(id, t, new THREE.Matrix4()), [w, h] = this.size;
    return [[-w / 2, 0], [w / 2, 0], [w / 2, -h], [-w / 2, -h]].map(([x, y]) => new THREE.Vector3(x, y, 0).applyMatrix4(m));
  }
  // is the sheet (with a margin, fraction of the frame) inside the camera frustum at time t?
  visibleIn(camera, id, t, margin = 0) {
    camera.updateMatrixWorld();
    for (const c of this.corners(id, t)) {
      const p = c.clone().project(camera);
      if (p.z > 1 || Math.abs(p.x) > 1 - margin || Math.abs(p.y) > 1 - margin) return false;
    }
    return true;
  }

  // ---------------------------------------------------------------------------------------------- per frame
  update(t, { camera = null, sway = 1, tilt = null } = {}) {
    const ex = { sway, tilt };
    const ctx = this.ctx, F = ctx.tl ? (T => ctx.tl.frameOf(T)) : (T => Math.round(T * 24)), fr = F(t);
    const L = this.light, U = this.uniforms;
    U.uAmbient.value.fromArray(L.ambient); U.uKeyDir.value.fromArray(L.key.dir); U.uKeyCol.value.fromArray(L.key.color);
    U.uBackPos.value.fromArray(L.back.pos); U.uBackCol.value.fromArray(L.back.color); U.uBackRange.value.set(L.back.near ?? 5, L.back.far ?? 80);
    U.uTrans.value = L.transmission ?? 0.35; U.uPaper.value.fromArray(L.paper || linOf(PAPER_HEX)); U.uInk.value.fromArray(L.ink || [0.011, 0.011, 0.012]);
    U.uBorder.value = this.border;
    const sh = L.back.shade || null;          // { zLast, kappa, over, under, band: [topLo, topHi, botLo, botHi], rim }
    U.uBackShape.value.set(sh ? sh.zLast : 0, sh ? sh.kappa : 0, sh ? sh.over : 0, sh ? sh.under : 0);
    const bb = sh && sh.band ? sh.band : [0.05, 0.05];
    U.uBackBand.value.set(bb[0], bb[1], 0, 0);
    U.uEdgeGlow.value = sh ? sh.rim || 0 : 0;
    U.uForm.value = L.formation ?? 0.2;
    // defocus: coc (output px per dioptre) and the projection scale
    const H = ctx.H || 1080;
    U.uFocus.value.set(this.focus.distance || 10, (this.focus.coc || 0) * H / 1080, 1);
    // order: back to front from the camera (the sheets blend their anti-aliased edges)
    const n = this.items.length, order = this._order; order.length = 0;
    const depth = new Float32Array(n);
    if (camera) {
      camera.updateMatrixWorld();
      const cp = camera.position, fw = new THREE.Vector3(); camera.getWorldDirection(fw);
      for (let i = 0; i < n; i++) { const it = this.items[i]; depth[i] = (it.x - cp.x) * fw.x + (it.y - 0.3 - cp.y) * fw.y + (it.z - cp.z) * fw.z; }
    }
    for (let i = 0; i < n; i++) if (!this.items[i].props.hidden) order.push(i);
    if (camera) order.sort((a, b) => (depth[b] - depth[a]) || a - b);
    if (this._occ) {
      let ok = !(tilt && camera);
      if (ok) for (const it of this.items) { const p = it.props; if (p.turn || p.fall || Math.abs(p.tilt || 0) > 0.02 || (p.sway ?? 0.018) * sway > 0.04) { ok = false; break; } }
      this.uniforms.uOcc.value.x = ok ? 1 : 0;
    }
    const m = this._m, cell = this.aCell.array, look = this.aLook.array, seed = this.aSeed.array, ca = this.aClip.array;
    let ci = 0, near = 0;
    const [w] = this.size, cm = new THREE.Matrix4(), off = new THREE.Matrix4(), camPos = camera ? camera.position : null;
    for (const cmesh of this.clipMeshes) cmesh.visible = false;
    order.forEach((id, k) => {
      const it = this.items[id], p = it.props;
      this.transform(id, t, m, ex);
      this.mesh.setMatrixAt(k, m);
      // image state
      let A = -1, B = -1, mix = 0, dens = 0, flash = p.flash || 0;
      const tex = p.tex;
      if (Array.isArray(tex) && tex.length) {
        const d = Math.min(1, Math.max(0, p.density ?? 1)) * (tex.length - 1), i0 = Math.floor(d), i1 = Math.min(tex.length - 1, i0 + 1);
        A = tex[i0]; B = tex[i1]; mix = d - i0; dens = 1;
      } else if (tex !== null && tex !== undefined && tex >= 0) { A = tex; dens = p.density ?? 1; }
      if (p.recap && fr >= F(p.recap.t0) && fr < F(p.recap.t1)) { A = p.recap.cell; B = -1; mix = 0; dens = p.recap.density ?? 1; }
      if (p.capture && fr >= F(p.capture.t)) {
        A = p.capture.cell; B = -1; mix = 0; dens = p.capture.density ?? 1;
        const df = fr - F(p.capture.t), nf = Math.max(1, Math.round((p.capture.flash ?? 0.1) * 24));
        if (df < nf + 1) flash = Math.max(flash, df < nf ? 1 - df / (nf + 0.5) * 0.6 : 0.15);
      }
      cell[k * 4] = A; cell[k * 4 + 1] = B; cell[k * 4 + 2] = mix; cell[k * 4 + 3] = dens;
      const curl = p.curl ?? (0.25 + 0.3 * it.seed);
      look[k * 4] = p.gloss || 0; look[k * 4 + 1] = curl; look[k * 4 + 2] = flash; look[k * 4 + 3] = p.light ?? 1;
      seed[k] = it.seed;
      // clips at the top corners (6 % in from each side), unless it fell
      const falling = p.fall && fr >= F(p.fall.t0);
      if (p.clip !== false) for (const sx of [-1, 1]) {
        off.makeTranslation(sx * w * 0.44, 0.004, 0.0015);
        cm.multiplyMatrices(m, off);
        if (falling) continue;
        const dist = camPos ? this._v.setFromMatrixPosition(cm).distanceTo(camPos) : 99;
        if (dist < this.clipNear && near < this.clipMeshes.length) {
          const cmesh = this.clipMeshes[near++]; cmesh.matrix.copy(cm); cmesh.matrixWorldNeedsUpdate = true; cmesh.visible = true;
        } else if (ci < this.max * 2) {
          this.clips.setMatrixAt(ci, cm);
          ca[ci * 4] = 1; ca[ci * 4 + 1] = it.seed; ci++;
        }
      }
    });
    this.mesh.count = order.length; this.clips.count = ci;
    this.mesh.instanceMatrix.needsUpdate = true; this.clips.instanceMatrix.needsUpdate = true;
    this.aCell.needsUpdate = true; this.aLook.needsUpdate = true; this.aSeed.needsUpdate = true; this.aClip.needsUpdate = true;
    return this;
  }

  // ---------------------------------------------------------------------------------------------- statics
  // the paperclip impostor: alpha = the wire (1 mm) along the clip path, r = a highlight on the upper-left edges.
  // Pure JS (a distance field): identical bytes in every browser launch.
  static clipTexture() {
    if (Prints._clipTex) return Prints._clipTex;
    const cp = clipPath(), Wt = 48, Ht = 160, data = new Uint8Array(Wt * Ht * 4);
    const segs = []; for (let i = 1; i < cp.pts.length; i++) segs.push([cp.pts[i - 1], cp.pts[i]]);
    const sx = cp.W / Wt, sy = cp.L / Ht, r = 0.0006;
    for (let j = 0; j < Ht; j++) for (let i = 0; i < Wt; i++) {
      const x = (i + 0.5) * sx - cp.W / 2, y = 0.0003 - ((j + 0.5) * sy);   // path coords (frame y - 2.7 mm)
      let dmin = 1, nx = 0, ny = 0;
      for (const [[ax, ay], [bx, by]] of segs) {
        const vx = bx - ax, vy = by - ay, l2 = vx * vx + vy * vy || 1e-12;
        const u = Math.max(0, Math.min(1, ((x - ax) * vx + (y - ay) * vy) / l2));
        const dx = x - (ax + u * vx), dy = y - (ay + u * vy), d = Math.hypot(dx, dy);
        if (d < dmin) { dmin = d; nx = dx / (d || 1); ny = dy / (d || 1); }
      }
      const a = Math.max(0, Math.min(1, (r - dmin) / (sx * 0.9) + 0.5));
      const hl = Math.max(0, -nx * 0.5 + ny * 0.85);    // upper edge catches the light
      const k = ((Ht - 1 - j) * Wt + i) * 4;
      data[k] = Math.round(255 * Math.min(1, hl * 1.2)); data[k + 1] = data[k]; data[k + 2] = data[k]; data[k + 3] = Math.round(255 * a);
    }
    const tex = new THREE.DataTexture(data, Wt, Ht, THREE.RGBAFormat);
    tex.colorSpace = THREE.NoColorSpace; tex.magFilter = THREE.LinearFilter; tex.minFilter = THREE.LinearMipmapLinearFilter; tex.generateMipmaps = true;
    tex.needsUpdate = true;
    return (Prints._clipTex = tex);
  }

  // paper tooth: tiling fibre noise (luminance), pure JS
  static toothTexture() {
    if (Prints._toothTex) return Prints._toothTex;
    const N = 128, data = new Uint8Array(N * N * 4), g = new Float32Array(N * N);
    const lat = (sz, seed) => { const L = new Float32Array(sz * sz); for (let i = 0; i < L.length; i++) L[i] = h1(i * 2654435761 + seed); return L; };
    const oct = [[16, 0.55, 11], [32, 0.3, 23], [64, 0.15, 37]];
    for (const [sz, w, seed] of oct) {
      const L = lat(sz, seed), k = N / sz;
      for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
        const fx = x / k, fy = y / k, i = Math.floor(fx), j = Math.floor(fy), u = fx - i, v = fy - j;
        const su = u * u * (3 - 2 * u), sv = v * v * (3 - 2 * v), q = (a, b) => L[((b % sz) * sz) + (a % sz)];
        g[y * N + x] += w * ((q(i, j) * (1 - su) + q(i + 1, j) * su) * (1 - sv) + (q(i, j + 1) * (1 - su) + q(i + 1, j + 1) * su) * sv);
      }
    }
    for (let i = 0; i < N * N; i++) { const v = Math.round(255 * Math.min(1, Math.max(0, g[i]))); data[4 * i] = data[4 * i + 1] = data[4 * i + 2] = v; data[4 * i + 3] = 255; }
    const tex = new THREE.DataTexture(data, N, N, THREE.RGBAFormat);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.magFilter = THREE.LinearFilter; tex.minFilter = THREE.LinearMipmapLinearFilter; tex.generateMipmaps = true;
    tex.colorSpace = THREE.NoColorSpace; tex.needsUpdate = true;
    return (Prints._toothTex = tex);
  }

  // Compose an atlas of print images once (init): each entry is drawn into its cell of a mipmapped RGBA8 target that
  // holds paper-relative reflectance, gamma-2 encoded (sqrt; the sheet shader squares), with a paper border baked in.
  // Monochrome (the red channel is read). modes:
  //   'photo'       the texture's luminance -> reflectance (tone: { gamma, gain, lift, levels: [black, white] })
  //   'silhouette'  a white-on-black matte -> a dark figure on the paper (density `tone.density`, default 1.6)
  //   'reflectance' the texture already holds linear reflectance (e.g. a develop() pass texture)
  //   'paper'       blank
  static buildAtlas(ctx, entries, { cols = 8, rows = 8, cellW = 360, cellH = 463, border = 0.045, inset = 0.004 } = {}) {
    const r = ctx.renderer, W = cols * cellW, H = rows * cellH;
    const target = new THREE.WebGLRenderTarget(W, H, { type: THREE.UnsignedByteType, depthBuffer: false, samples: 0,
      minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter, generateMipmaps: true });
    target.texture.colorSpace = THREE.NoColorSpace;    // the shader encodes / decodes sRGB itself
    const scene = new THREE.Scene(), cam = new THREE.OrthographicCamera(0, W, H, 0, -1, 1);
    const mat = new THREE.ShaderMaterial({
      depthTest: false, depthWrite: false,
      uniforms: { tSrc: { value: null }, uRect: { value: new THREE.Vector4(0, 0, 1, 1) }, uClip: { value: new THREE.Vector4(0, 0, 1, 1) }, uMode: { value: 0 }, uTone: { value: new THREE.Vector4(1, 1, 0, 1.6) },
        uLevels: { value: new THREE.Vector2(0, 1) }, uBorder: { value: new THREE.Vector2(border, border) }, uMirror: { value: 0 }, uSrgb: { value: 1 } },
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }',
      fragmentShader: /* glsl */`
        uniform sampler2D tSrc; uniform vec4 uRect, uClip, uTone; uniform float uMode, uMirror, uSrgb; uniform vec2 uLevels, uBorder; varying vec2 vUv;
        vec3 toLin(vec3 c){ return mix(c / 12.92, pow((c + .055) / 1.055, vec3(2.4)), step(.04045, c)); }
        vec3 toG2(vec3 c){ return sqrt(clamp(c, 0., 1.)); }                // gamma-2 encoding (the sheet shader squares)
        void main(){
          vec2 q = (vUv - uBorder) / (1. - 2. * uBorder);
          float refl = 1.;
          if (q.x >= 0. && q.x <= 1. && q.y >= 0. && q.y <= 1. && uMode > .5) {
            if (uMirror > .5) q.x = 1. - q.x;
            vec2 s = uRect.xy + q * (uRect.zw - uRect.xy);
            vec3 c = (s.x < uClip.x || s.x > uClip.z || s.y < uClip.y || s.y > uClip.w) ? vec3(0.) : texture2D(tSrc, s).rgb;
            if (uSrgb > .5) c = toLin(c);
            float Y = dot(c, vec3(.2126, .7152, .0722));
            if (uMode < 1.5) {           // photo
              float y = clamp((Y - uLevels.x) / max(1e-4, uLevels.y - uLevels.x), 0., 1.);
              refl = clamp(uTone.z + uTone.y * pow(y, uTone.x), 0., 1.);
            } else if (uMode < 2.5) {    // silhouette matte: white figure -> density
              refl = pow(10., -uTone.w * clamp(Y, 0., 1.));
            } else refl = clamp(Y, 0., 1.);   // reflectance
          }
          gl_FragColor = vec4(toG2(vec3(refl)), 1.);
        }` });
    const quad = new THREE.Mesh(new THREE.PlaneGeometry(1, 1).translate(0.5, 0.5, 0), mat); scene.add(quad);
    const prevT = r.getRenderTarget(), prevAC = r.autoClear;
    r.setRenderTarget(target); r.setClearColor(0xffffff, 1); r.clear(); r.autoClear = false;
    const MODES = { paper: 0, photo: 1, silhouette: 2, reflectance: 3 };
    entries.forEach((e, i) => {
      if (!e || i >= cols * rows) return;
      if (typeof e.prepare === 'function') { e.prepare(); r.setRenderTarget(target); r.autoClear = false; }
      const c = i % cols, row = Math.floor(i / cols);
      quad.position.set(c * cellW, H - (row + 1) * cellH, 0); quad.scale.set(cellW, cellH, 1);
      const u = mat.uniforms, tex = e.texture || null;
      u.tSrc.value = tex; u.uMode.value = tex ? MODES[e.mode || 'photo'] : 0;
      let rect = e.rect || [0, 0, 1, 1];
      if (tex && tex.image && e.fit === 'contain') {
        // widen the source rect so the whole source fits in the cell's image area (paper around it)
        const ia = (cellW * (1 - 2 * border)) / (cellH * (1 - 2 * border)), sw = (rect[2] - rect[0]) * tex.image.width, sh = (rect[3] - rect[1]) * tex.image.height;
        const sa = sw / sh;
        if (sa > ia) { const nh = (rect[3] - rect[1]) * sa / ia, cy = (rect[1] + rect[3]) / 2; rect = [rect[0], cy - nh / 2, rect[2], cy + nh / 2]; }
        else { const nw = (rect[2] - rect[0]) * ia / sa, cx = (rect[0] + rect[2]) / 2; rect = [cx - nw / 2, rect[1], cx + nw / 2, rect[3]]; }
      }
      u.uRect.value.set(...rect);
      u.uClip.value.set(...(e.clip || [-1, -1, 2, 2]));
      const tone = e.tone || {};
      u.uTone.value.set(tone.gamma ?? 1, tone.gain ?? 1, tone.lift ?? 0, tone.density ?? 1.6);
      u.uLevels.value.set(...(tone.levels || [0, 1]));
      const b = e.border ?? border; u.uBorder.value.set(b, b * cellW / cellH);
      u.uMirror.value = e.mirror ? 1 : 0;
      u.uSrgb.value = tex && tex.colorSpace === THREE.SRGBColorSpace && e.mode !== 'reflectance' ? 1 : 0;
      r.render(scene, cam);
    });
    r.autoClear = prevAC; r.setRenderTarget(prevT);
    mat.dispose(); quad.geometry.dispose();
    return { texture: target.texture, cols, rows, inset, target, cellW, cellH };
  }
}

export default Prints;
