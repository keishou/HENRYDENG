// develop.js - print development (BIBLE 4.5 "density by certainty", 4.8 TRAY; lane C, SHARED with lanes D and E).
//
// The model (BIBLE 4.8), per point x of the paper, in optical density D = -log10(reflectance / paper):
//   D(x, t) = cap(x) * C(tau(t) * k(x))                       C = characteristic curve 1 - exp(-s^gamma) (toe + shoulder)
//   k = k0 * (0.35 + 0.65 * darkness) * (0.25 + 0.75 * certainty)       darkness = D_target / D_max
//   cap = D_target * (0.35 + 0.65 * certainty)                 so measured features reach full density, guesses stay thin
//   (D_target = the photo's density, D_max = 2.0: a capped black still prints dark, a capped midtone goes pale)
// then the scheduled "leads" (a masked region is pulled from its chemical density to its cap on a hit frame), the
// options below, and a round-dot AM halftone at 45 deg in PAPER space (the dots are on the paper, so they ride the
// liquid's refraction, and the 16th-pulse mask develops whole dots). Dot area is gamma-correct: the average linear
// reflectance of a cell equals the photo's linear luminance. Colour output is linear (the finish chain tone-maps).
//
// USAGE
//   const pass = develop(ctx, opts)       -> DevelopPass, cached by opts.key (default: src uuid). Calling it again with
//                                            the same key updates the same pass: call it in EVERY frame() with the full
//                                            option set - options you omit return to their defaults (no state is
//                                            carried between frames, BIBLE 9.2).
//   pass.material    THREE.ShaderMaterial for a mesh whose uv spans the print (0,0 bottom-left .. 1,1 top-right): unlit,
//                    colour = print reflectance x opts.light (+ opts.tint), opaque. Use it for prints outside the tray.
//   pass.texture     the developed print as a THREE.Texture (a render target), refreshed on every update when the pass
//                    was created with opts.texture = { width, height? } (height defaults to width * size[1] / size[0]);
//                    null otherwise. For Prints / lightbox atlases.
//   pass.update(opts) same as calling develop() again with the pass's key.     pass.dispose()
//   pass.uniforms / pass.glsl   the GLSL chunk (vec4 dvPrint(vec2 uv) -> rgb reflectance, a coverage; float dvEdge is the
//                    fuse front after the call) and its uniforms, to shade a print inside another shader (tray.js does
//                    this under the liquid). Call dvPrint in uniform control flow (it uses screen-space derivatives).
//   pass.printUV(px, py) -> [u, v]   a source-image pixel (top-left origin) to print uv, through opts.crop
//   pass.state       the evaluated schedule of the last update (tau, frac, pulse, leads, outward radius), for checks
//
// OPTIONS (all optional except src)
//   key        cache key (string)
//   src        THREE.Texture - the photograph or a darkroom variant (sRGB). The print shows it cropped by `crop`.
//   certainty  THREE.Texture | null - certainty map aligned to src (out/film/data/certainty_1024.png, linear). null = 1.
//   regions    [THREE.Texture, THREE.Texture] | null - out/film/data/regions_1024.png, regions2_1024.png (for `lead`/`outward`)
//   crop       [x0, y0, w, h] in src px, top-left origin (default: the whole image). Should have the paper's aspect.
//   size       [w, h] paper size in metres (default [0.28, 0.36], 7:9). Sets the halftone pitch in paper units.
//   halftone   { pitch = 0.00151 m on the paper (4 px at 1080p through the tray lens), angle = 45 (deg) } | null
//              (null = continuous tone). The chorus trays coarsen it (BIBLE 4.5: 4.5 / 5 / 6 / 7 px).
//   t          film time (s). Evaluated at min(t, freezeAt).
//   tStart     development start (s; default 0). Before it the paper is blank.
//   pulses16   true | [t...] | false - development in discrete pulses: 16 pulses on the 16th grid from tStart (true)
//              or the given times. Pulse n (1-based) develops the 2^(n-N) share of all dots with the highest rate
//              (darkness x certainty^rankPower, dithered per dot), so each pulse doubles the developed dots; a dot's
//              development starts at the pulse that reaches it (it shows tau0 of development on arrival); between
//              pulses nothing changes; after the last pulse development is continuous. Tested by FRAME (tl.reached).
//   clock      'voice' (default: after the pulses tau grows at rate x (0.25 + 0.75 x vocal envelope) - "when she sings,
//              he develops") | 'linear' (rate x t)                                       rate  clock speed (default 1)
//   tau0       development time already given at the first pulse (s; default 0.35)
//   k0, gamma  rate constant (1/s; default 0.9) and curve toe (default 2.2)
//   dmax       full density (default 2.0)       rankPower  certainty exponent of the pulse order (default 3: the measured
//              features clearly lead; 1 = plain darkness x certainty)
//   lead       [{ region: 'pupil' | 'iris' | 'browlash' | 'noselip' | 'hair', t, frames = 3, first = 0.62 }]
//              on the frame of t the region jumps `first` of the way from its chemical density to its cap (the change
//              is on the hit frame), and completes over `frames` frames. frames 0 = a snap. Only the region's darker
//              parts move (target density above ~0.18-0.5): the pupil, not the eyelid skin around it. noselip takes
//              density: [lo, hi] (e.g. [0.4, 0.7]: the nostrils and the lip line, not the whole lips).
//   outward    { steps: [[t, r]...], soft = 0.08 } - midtones fill outward from the eyes: at each t the radius (in
//              units of 400 source px from the nearer iris) steps to r, eased like a lead.
//   stops      print exposure +n stops (0..4): each stop darkens the midtones about one zone; +4 leaves only speculars
//   fog        amount 0..1 | { amount, discs: [[u, v, r]] } - safelight fog (adds density up to 0.6); one disc (print uv,
//              r in uv of the width) stays clean (S24 coin)
//   fuse       { t0, t1, width = 0.06 } - a development front burns in from the low-certainty edges and stops before
//              the eyes (certainty level 0 -> 0.9 over t0..t1); dvEdge carries the front line (S36-S37)
//   cyan       0..1 - the cyanotype ramp (pale yellow-green paper -> CYANOTYPE blue) on the print (S38)
//   strip      { bands: [t...], axis = 'x' | 'y' } - a test strip: band i is exposed by every flash j >= i that has
//              happened (tested by frame); an unexposed band stays paper; exposure count n prints at +(n - 1) stops (S39)
//   multi      [{ src, weight = 1, offset = [0, 0], scale = 1, crop }] (up to 3) - further exposures onto the same paper:
//              their densities add to the developed one (x multiBase, default 1), toward black (S42)
//   genLoss    generation n >= 0 (float): each copy blurs, loses midtones and fades toward the paper (S51)
//   freezeAt   seconds | null - evaluate development at min(t, freezeAt) (S53)
//   soft       { lod = 2.6, sharpLod = 0, density = 1, rings: [{ t, uv: [u, v], speed = 0.7 (uv of the height per s),
//              width = 0.06 }] } a soft (out of focus, density x `density`) print; behind each ring front the print is
//              sharp and at full density (S04 grokking)
//   levels     [Yblack, Ywhite] linear luminance of the photo's black and paper white (default: auto from the crop)
//   midLift    the print's tone curve on the photo's normalized reflectance y: y + midLift * y^2 * (1 - y) (default 0 =
//              exact; 0.8 opens the midtones and highlights and keeps the blacks, as a printer would for a passport photo
//              whose background is far brighter than the face)
//   light      the standalone material's illumination (default 1)          tint  [r, g, b] multiplier (default 1)
//   paper, ink [r, g, b] linear reflectance of paper white and full density (default PAPER, D-max 2.0)
//   texture    { width, height } - keep pass.texture (a render target of the print) up to date
import * as THREE from 'three';

const cache = new Map();
const PIX = new Map();                    // texture uuid -> { w, h, data } CPU copy (for the pulse ranking)
const REGION = { pupil: [0, 0], iris: [0, 1], browlash: [0, 2], noselip: [1, 0], hair: [1, 1] };
const srgbToLin = new Float32Array(256).map((_, i) => { const c = i / 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; });
const lin = hex => { const c = new THREE.Color(hex); return [c.r, c.g, c.b]; };   // THREE.Color(hex) is linear (ColorManagement)
const DEFAULTS = {
  size: [0.28, 0.36], halftone: { pitch: 0.00151, angle: 45 }, t: 0, tStart: 0, pulses16: false, clock: 'voice', rate: 1, tau0: 0.35,
  k0: 0.9, gamma: 2.2, dmax: 2.0, rankPower: 3, lead: [], outward: null, stops: 0, fog: 0, fuse: null, cyan: 0, strip: null, multi: null, genLoss: 0,
  freezeAt: null, soft: null, levels: null, light: 1, tint: [1, 1, 1], paper: null, ink: null, certainty: null, regions: null,
  crop: null, midLift: 0, multiBase: 1,
};

export function develop(ctx, opts = {}) {
  const key = opts.key ?? (opts.src ? opts.src.uuid : 'blank');
  let p = cache.get(key);
  if (!p) { p = new DevelopPass(ctx, key, opts); cache.set(key, p); }
  p.update(opts);
  return p;
}

// the voice clock: integral of (0.25 + 0.75 env) dt, tabulated once from the timeline's envelope (pure)
const clocks = new WeakMap();
function voiceClock(tl) {
  let c = clocks.get(tl);
  if (!c) {
    const d = tl.envData;
    if (d && d.values && d.values.length) {
      const v = d.values, cum = new Float64Array(v.length + 1), dt = 1 / d.rate;
      for (let i = 0; i < v.length; i++) cum[i + 1] = cum[i] + (0.25 + 0.75 * v[i]) * dt;
      c = t => { const x = (t - (d.t0 || 0)) * d.rate; if (x <= 0) return x * 0.25 / d.rate; const i = Math.min(v.length - 1, Math.floor(x)); return cum[i] + (x - i) * (0.25 + 0.75 * v[i]) * dt; };
    } else c = t => t * 0.6;
    clocks.set(tl, c);
  }
  return c;
}

function pixelsOf(tex) {
  if (!tex || !tex.image) return null;
  let p = PIX.get(tex.uuid);
  if (!p) {
    const img = tex.image, w = img.width, h = img.height;
    const cv = new OffscreenCanvas(w, h), g = cv.getContext('2d', { willReadFrequently: true });
    g.drawImage(img, 0, 0);
    const flip = !(typeof ImageBitmap !== 'undefined' && img instanceof ImageBitmap) && tex.flipY;   // rows -> texture v
    p = { w, h, data: g.getImageData(0, 0, w, h).data, flip };
    PIX.set(tex.uuid, p);
  }
  return p;
}
// bilinear sample of channel ch at texture uv (v up), 0..1 (sRGB decoded to linear when lin)
function sampleUV(P, u, v, ch, linear) {
  const x = u * P.w - 0.5, yv = (P.flip ? 1 - v : v) * P.h - 0.5;
  const x0 = Math.max(0, Math.min(P.w - 1, Math.floor(x))), y0 = Math.max(0, Math.min(P.h - 1, Math.floor(yv)));
  const x1 = Math.min(P.w - 1, x0 + 1), y1 = Math.min(P.h - 1, y0 + 1), fx = Math.min(1, Math.max(0, x - x0)), fy = Math.min(1, Math.max(0, yv - y0));
  const g = (xx, yy) => { const b = P.data[(yy * P.w + xx) * 4 + ch]; return linear ? srgbToLin[b] : b / 255; };
  return (g(x0, y0) * (1 - fx) + g(x1, y0) * fx) * (1 - fy) + (g(x0, y1) * (1 - fx) + g(x1, y1) * fx) * fy;
}
const lumUV = (P, u, v) => 0.2126 * sampleUV(P, u, v, 0, true) + 0.7152 * sampleUV(P, u, v, 1, true) + 0.0722 * sampleUV(P, u, v, 2, true);
// per-dot dither for the pulse ranking (deterministic integer hash of the cell index)
function cellHash(i, j) {
  let h = (Math.imul(i | 0, 0x27d4eb2d) ^ Math.imul(j | 0, 0x165667b1)) >>> 0;
  h ^= h >>> 15; h = Math.imul(h, 0x85ebca6b) >>> 0; h ^= h >>> 13; h = Math.imul(h, 0xc2b2ae35) >>> 0; h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}

class DevelopPass {
  constructor(ctx, key, opts) {
    this.ctx = ctx; this.key = key; this.state = {};
    this.uniforms = developUniforms();
    this._blank = this.uniforms.dvSrc.value; this._zero = this.uniforms.dvReg1.value;
    this.glsl = DEVELOP_GLSL;
    this.material = new THREE.ShaderMaterial({
      uniforms: this.uniforms, vertexShader: VERT, fragmentShader: DEVELOP_GLSL + FRAG_STANDALONE,
      side: THREE.DoubleSide,
    });
    this.material.name = 'develop:' + key;
    this.texture = null;
    if (opts.texture) {
      const size = opts.size || DEFAULTS.size, w = opts.texture.width || 512, h = opts.texture.height || Math.round(w * size[1] / size[0]);
      this._rt = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, depthBuffer: false });
      this.texture = this._rt.texture;
      this._rtScene = new THREE.Scene(); this._rtCam = new THREE.OrthographicCamera(0, 1, 1, 0, -1, 1);
      this._rtScene.add(new THREE.Mesh(new THREE.PlaneGeometry(1, 1).translate(0.5, 0.5, 0), this.material));
    }
  }

  printUV(px, py) {
    const o = this.opts || {}, src = o.src, W = src && src.image ? src.image.width : 1024, H = src && src.image ? src.image.height : 1024;
    const c = o.crop || [0, 0, W, H];
    return [(px - c[0]) / c[2], 1 - (py - c[1]) / c[3]];
  }

  update(opts = {}) {
    const o = this.opts = { ...DEFAULTS, ...opts };
    const u = this.uniforms, tl = this.ctx.tl, fps = tl ? tl.fps : 24;
    const F = T => Math.round(T * fps);
    const tEval = o.freezeAt != null ? Math.min(o.t, o.freezeAt) : o.t, f = F(tEval);
    const reached = T => f >= F(T);
    // textures and crop
    const src = o.src || null;
    u.dvSrc.value = src || this._blank;
    const W = src && src.image ? src.image.width : 1, H = src && src.image ? src.image.height : 1;
    const crop = o.crop || [0, 0, W, H];
    u.dvCrop.value.set(crop[0] / W, 1 - (crop[1] + crop[3]) / H, crop[2] / W, crop[3] / H);
    u.dvCert.value = o.certainty || this._blank;
    const reg = o.regions || null;
    u.dvReg1.value = reg ? reg[0] : this._zero; u.dvReg2.value = reg ? reg[1] || this._zero : this._zero;
    u.dvSize.value.set(o.size[0], o.size[1]);
    const ht = o.halftone ? { pitch: 0.00151, angle: 45, ...o.halftone } : null;
    u.dvScreen.value.set(ht ? ht.pitch : 0, (ht ? ht.angle : 45) * Math.PI / 180);
    // levels (auto from the crop, once per source)
    const levels = o.levels || this._autoLevels(src, crop);
    u.dvLevels.value.set(levels[0], levels[1], o.midLift || 0);
    // development clock + pulses
    let tau = 0, frac = 1, pulse = null, times = null;
    const vc = o.clock === 'linear' ? (t => t) : voiceClock(tl), clock = t => o.rate * vc(t);
    if (o.pulses16) {
      const bp = tl ? tl.beatPeriod : 0.454545;
      times = Array.isArray(o.pulses16) ? o.pulses16 : Array.from({ length: 16 }, (_, k) => +(o.tStart + k * bp / 4).toFixed(4));
      const N = times.length;
      let n = 0; for (let k = 0; k < N; k++) if (reached(times[k])) n = k + 1;
      pulse = n;
      if (n === 0) { frac = 0; tau = 0; }
      else if (n < N) { frac = Math.pow(2, n - N); tau = times[n - 1] - o.tStart + o.tau0; }
      else { frac = 1; const tN = times[N - 1], tq = F(tN) / fps, te = f / fps; tau = tN - o.tStart + o.tau0 + (clock(te) - clock(tq)); }
    } else if (f >= F(o.tStart)) { tau = clock(f / fps) - clock(F(o.tStart) / fps); frac = 1; }
    else { tau = 0; frac = 1; }
    u.dvFrac.value = frac;
    u.dvChem.value.set(Math.max(0, tau), o.k0, o.gamma, 1.2); u.dvDmax.value = o.dmax;
    const needRank = !!(o.pulses16 && src);
    u.dvFlags.value.set(o.certainty ? 1 : 0, reg ? 1 : 0, needRank ? 1 : 0, 0);
    if (times) { u.dvPulses.value.set(times.length, 0); for (let k = 0; k < 16; k++) u.dvPulseTau.value[k] = (times[Math.min(k, times.length - 1)] - o.tStart); }
    const lat = ht ? this._lattice(o.size, ht) : null;
    if (lat) { u.dvRankOff.value.set(lat.i0, lat.j0); u.dvRankMax.value.set(lat.ni - 1, lat.nj - 1); }
    if (needRank) this._rank(src, o.certainty, crop, o.size, ht, levels, o.dmax, o.rankPower);
    // leads
    const ramp = (T, frames = 3, first = 0.62) => { const df = f - F(T); if (df < 0) return 0; if (frames <= 0 || df >= frames) return 1; return 1 - (1 - first) * Math.exp(-1.1 * df); };
    const L1 = [0, 0, 0], L2 = [0, 0];
    const leads = {};
    for (const l of o.lead || []) {
      const rc = REGION[l.region]; if (!rc) continue;
      const w = ramp(l.t, l.frames ?? 3, l.first ?? 0.62); leads[l.region] = Math.max(leads[l.region] || 0, w);
      if (rc[0] === 0) L1[rc[1]] = Math.max(L1[rc[1]], w); else L2[rc[1]] = Math.max(L2[rc[1]], w);
    }
    u.dvLead1.value.set(...L1); u.dvLead2.value.set(...L2);
    const nl = (o.lead || []).find(l => l.region === 'noselip');
    u.dvLeadNL.value.set(...(nl && nl.density ? nl.density : [0.18, 0.5]));
    let R = 0;
    if (o.outward) {
      let prev = 0;
      for (const [T, r] of o.outward.steps || []) { const w = ramp(T, 3, 0.62); if (w > 0) { R = prev + (r - prev) * w; prev = r; } }
    }
    const soft = o.outward ? o.outward.soft ?? 0.08 : 0.08;
    u.dvOut.value.set(R > 0 ? R + (R >= 1 ? soft : 0) : 0, soft);
    // exposure options
    u.dvStops.value = o.stops || 0;
    const fog = typeof o.fog === 'number' ? { amount: o.fog, discs: [] } : { amount: 0, discs: [], ...(o.fog || {}) };
    const d0 = (fog.discs || [])[0];
    u.dvFog.value.set(fog.amount || 0, d0 ? d0[0] : 0, d0 ? d0[1] : 0, d0 ? d0[2] : -1);
    if (o.fuse) { const w = o.fuse.width ?? 0.06, k = Math.min(1, Math.max(0, (tEval - o.fuse.t0) / Math.max(1e-3, o.fuse.t1 - o.fuse.t0))); u.dvFuse.value.set(f >= F(o.fuse.t0) ? 0.9 * k * k * (3 - 2 * k) : -1, w, 1, 0); }
    else u.dvFuse.value.set(-1, 0.06, 0, 0);
    u.dvCyan.value = o.cyan || 0;
    if (o.strip && o.strip.bands) {
      const b = o.strip.bands, n = b.length, st = [-1, -1, -1, -1];
      for (let i = 0; i < Math.min(4, n); i++) { let c = 0; for (let j = i; j < n; j++) if (reached(b[j])) c++; st[i] = c > 0 ? c - 1 + (o.stops || 0) : -1; }
      u.dvStrip.value.set(...st); u.dvStripAx.value.set(o.strip.axis === 'y' ? 1 : 0, Math.min(4, n));
    } else u.dvStripAx.value.set(0, 0);
    const M = (o.multi || []).slice(0, 3);
    u.dvFlags.value.w = M.length;
    const mW = [0, 0, 0];
    M.forEach((m, i) => {
      u[`dvM${i}`].value = m.src; mW[i] = m.weight ?? 1;
      u.dvMultiXf.value[i].set((m.offset || [0, 0])[0], (m.offset || [0, 0])[1], m.scale ?? 1, 0);
      const mw = m.src && m.src.image ? m.src.image.width : 1, mh = m.src && m.src.image ? m.src.image.height : 1, c = m.crop || [0, 0, mw, mh];
      u.dvMultiCrop.value[i].set(c[0] / mw, 1 - (c[1] + c[3]) / mh, c[2] / mw, c[3] / mh);
    });
    u.dvMultiW.value.set(mW[0], mW[1], mW[2], o.multiBase ?? 1);
    u.dvGen.value = o.genLoss || 0;
    if (o.soft) {
      const rings = (o.soft.rings || []).slice(0, 4);
      u.dvSoft.value.set(o.soft.lod ?? 2.6, o.soft.sharpLod ?? 0, rings.length, 0);
      rings.forEach((r, i) => u.dvRings.value[i].set(f >= F(r.t) ? (f - F(r.t)) / fps : -1, r.uv[0], r.uv[1], r.speed ?? 0.7));
      u.dvSoft.value.w = (o.soft.rings && o.soft.rings[0] && o.soft.rings[0].width) || 0.06;
      u.dvSoftD.value = o.soft.density ?? 1;
    } else { u.dvSoft.value.set(0, 0, 0, 0.06); u.dvSoftD.value = 1; }
    if (o.paper) u.dvPaper.value.set(...o.paper); else u.dvPaper.value.set(...lin('#F2EFE8'));
    if (o.ink) u.dvInk.value.set(...o.ink); else u.dvInk.value.set(0.011, 0.011, 0.012);
    u.dvLight.value = o.light ?? 1; u.dvTint.value.set(...(o.tint || [1, 1, 1]));
    this.state = { t: tEval, f, tau, frac, pulse, leads, outward: R, levels };
    // the cell pass: develop every halftone dot once (one texel per cell) instead of once per pixel
    u.dvCellsOn.value = 0;
    if (lat && src && this.ctx.renderer) this._cellPass(lat);
    if (this._rt) {
      const r = this.ctx.renderer, prev = r.getRenderTarget();
      r.setRenderTarget(this._rt); r.render(this._rtScene, this._rtCam); r.setRenderTarget(prev);
    }
    return this;
  }

  // the halftone lattice: cell (i, j) of the 45-degree screen covers q in [i, i+1) x [j, j+1), q = R(-angle) p / pitch
  _lattice(size, ht) {
    const pitch = ht.pitch, ang = ht.angle * Math.PI / 180, key = [size.join(','), pitch, ang].join('|');
    if (this._lat && this._lat.key === key) return this._lat;
    const ca = Math.cos(ang), sa = Math.sin(ang);
    const qs = [[0, 0], [size[0], 0], [0, size[1]], [size[0], size[1]]].map(([x, y]) => [(ca * x + sa * y) / pitch, (-sa * x + ca * y) / pitch]);
    const i0 = Math.floor(Math.min(...qs.map(c => c[0]))) - 1, i1 = Math.ceil(Math.max(...qs.map(c => c[0]))) + 1;
    const j0 = Math.floor(Math.min(...qs.map(c => c[1]))) - 1, j1 = Math.ceil(Math.max(...qs.map(c => c[1]))) + 1;
    return (this._lat = { key, i0, j0, ni: i1 - i0 + 1, nj: j1 - j0 + 1, pitch, ca, sa });
  }

  _cellPass(lat) {
    const u = this.uniforms, r = this.ctx.renderer;
    if (!this._cellRT || this._cellRT.width !== lat.ni || this._cellRT.height !== lat.nj) {
      if (this._cellRT) this._cellRT.dispose();
      this._cellRT = new THREE.WebGLRenderTarget(lat.ni, lat.nj, { type: THREE.HalfFloatType, depthBuffer: false,
        minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, generateMipmaps: false });
    }
    if (!this._cellScene) {
      this._cellScene = new THREE.Scene(); this._cellCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
      this._cellMat = new THREE.ShaderMaterial({ uniforms: u, vertexShader: 'void main(){ gl_Position = vec4(position.xy, 0., 1.); }',
        fragmentShader: DEVELOP_GLSL + CELL_FRAG, depthTest: false, depthWrite: false });
      this._cellScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this._cellMat));
    }
    const prev = r.getRenderTarget();
    r.setRenderTarget(this._cellRT); r.render(this._cellScene, this._cellCam); r.setRenderTarget(prev);
    u.dvCells.value = this._cellRT.texture; u.dvCellsOn.value = 1;
  }

  _autoLevels(src, crop) {
    if (!src) return [0.006, 0.85];
    const key = src.uuid + crop.join(',');
    if (this._lvKey === key) return this._lv;
    const P = pixelsOf(src); if (!P) return [0.006, 0.85];
    const ys = [];
    for (let j = 0; j < 96; j++) for (let i = 0; i < 96; i++) {
      const px = crop[0] + (i + 0.5) / 96 * crop[2], py = crop[1] + (j + 0.5) / 96 * crop[3];
      ys.push(lumUV(P, px / P.w, 1 - py / P.h));
    }
    ys.sort((a, b) => a - b);
    this._lvKey = key; this._lv = [ys[Math.floor(ys.length * 0.003)], ys[Math.floor(ys.length * 0.85)]];
    return this._lv;
  }

  // the pulse ranking: every halftone cell of the print sorted by rate = darkness x certainty (x a per-dot dither), so
  // "the 2^(n-16) share with the highest rate" is exact; stored as a float texture indexed by cell
  _rank(src, cert, crop, size, ht, levels, dmax = 2, pw = 3) {
    const pitch = ht ? ht.pitch : 0.00151, ang = (ht ? ht.angle : 45) * Math.PI / 180;
    const key = [src.uuid, cert ? cert.uuid : '-', crop.join(','), size.join(','), pitch, ang, levels.join(','), dmax, pw].join('|');
    if (this._rankKey === key) return;
    const P = pixelsOf(src), C = cert ? pixelsOf(cert) : null;
    const { i0, j0, ni, nj, ca, sa } = this._lattice(size, { pitch, angle: ang * 180 / Math.PI });
    const i1 = i0 + ni - 1, j1 = j0 + nj - 1;
    const W = P.w, H = P.h, cu = crop[0] / W, cv = 1 - (crop[1] + crop[3]) / H, cw = crop[2] / W, ch = crop[3] / H;
    const cells = [];
    const data = new Float32Array(ni * nj).fill(2);
    for (let j = j0; j <= j1; j++) for (let i = i0; i <= i1; i++) {
      const qx = (i + 0.5) * pitch, qy = (j + 0.5) * pitch;
      const px = ca * qx - sa * qy, py = sa * qx + ca * qy, uu = px / size[0], vv = py / size[1];
      if (uu < 0 || uu > 1 || vv < 0 || vv > 1) continue;
      const tu = cu + uu * cw, tv = cv + vv * ch;
      const du = 0.35 * pitch / size[0] * cw, dv = 0.35 * pitch / size[1] * ch;
      const Y = (lumUV(P, tu - du, tv - dv) + lumUV(P, tu + du, tv - dv) + lumUV(P, tu - du, tv + dv) + lumUV(P, tu + du, tv + dv)) / 4;
      const y = Math.min(1, Math.max(Math.pow(10, -dmax), (Y - levels[0]) / (levels[1] - levels[0])));
      const dark = -Math.log10(y) / dmax;
      const c = C ? sampleUV(C, tu, tv, 0, false) : 1;
      cells.push([dark * Math.pow(c, pw) * (0.9 + 0.2 * cellHash(i, j)), (j - j0) * ni + (i - i0)]);
    }
    cells.sort((a, b) => b[0] - a[0] || a[1] - b[1]);
    const n = cells.length;
    cells.forEach(([, idx], r) => { data[idx] = (r + 0.5) / n; });
    const tex = new THREE.DataTexture(data, ni, nj, THREE.RedFormat, THREE.FloatType);
    tex.minFilter = tex.magFilter = THREE.NearestFilter; tex.generateMipmaps = false; tex.needsUpdate = true;
    if (this.uniforms.dvRank.value && this.uniforms.dvRank.value.isDataTexture && this._rankTex) this._rankTex.dispose();
    this._rankTex = tex; this.uniforms.dvRank.value = tex;
    this.uniforms.dvRankOff.value.set(i0, j0); this.uniforms.dvRankMax.value.set(ni - 1, nj - 1);
    this._rankKey = key; this.rankCells = n;
  }

  dispose() {
    this.material.dispose(); if (this._rt) this._rt.dispose(); if (this._rankTex) this._rankTex.dispose();
    if (this._cellRT) this._cellRT.dispose(); if (this._cellMat) this._cellMat.dispose();
    cache.delete(this.key);
  }
}

// a fresh set of the chunk's uniforms at neutral values (a pass owns one; tray.js uses one for a bare floor)
export function developUniforms() {
  const V2 = (x = 0, y = 0) => new THREE.Vector2(x, y), V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z), V4 = (a = 0, b = 0, c = 0, d = 0) => new THREE.Vector4(a, b, c, d);
  const blank = new THREE.DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1); blank.needsUpdate = true;
  const zero = new THREE.DataTexture(new Uint8Array([0, 0, 0, 255]), 1, 1); zero.needsUpdate = true;
  const r0 = new THREE.DataTexture(new Float32Array([0]), 1, 1, THREE.RedFormat, THREE.FloatType); r0.needsUpdate = true;
  return {
    dvSrc: { value: blank }, dvCert: { value: blank }, dvReg1: { value: zero }, dvReg2: { value: zero }, dvRank: { value: r0 },
    dvM0: { value: blank }, dvM1: { value: blank }, dvM2: { value: blank },
    dvFlags: { value: V4() },                     // hasCert, hasReg, hasRank, nMulti
    dvRankOff: { value: new THREE.Vector2() }, dvRankMax: { value: new THREE.Vector2() },
    dvCrop: { value: V4(0, 0, 1, 1) }, dvSize: { value: V2(0.28, 0.36) }, dvScreen: { value: V2(0.00151, Math.PI / 4) },
    dvLevels: { value: V3(0.006, 0.85, 1) }, dvChem: { value: V4(0, 0.9, 2.2, 1.2) }, dvFrac: { value: 1 }, dvDmax: { value: 2 },
    dvPulses: { value: V2(16, 0) }, dvPulseTau: { value: new Array(16).fill(0) },
    dvLead1: { value: V3() }, dvLead2: { value: V2() }, dvOut: { value: V2(0, 0.08) }, dvLeadNL: { value: V2(0.18, 0.5) },
    dvStops: { value: 0 }, dvFog: { value: V4(0, 0, 0, -1) }, dvFuse: { value: V4(-1, 0.06, 0, 0) }, dvCyan: { value: 0 },
    dvStrip: { value: V4() }, dvStripAx: { value: V2() },
    dvMultiW: { value: V4(0, 0, 0, 1) }, dvMultiXf: { value: [V4(0, 0, 1, 0), V4(0, 0, 1, 0), V4(0, 0, 1, 0)] },
    dvMultiCrop: { value: [V4(0, 0, 1, 1), V4(0, 0, 1, 1), V4(0, 0, 1, 1)] },
    dvGen: { value: 0 }, dvSoft: { value: V4() }, dvSoftD: { value: 1 }, dvRings: { value: [V4(), V4(), V4(), V4()] },
    dvPaper: { value: V3(...lin('#F2EFE8')) }, dvInk: { value: V3(0.011, 0.011, 0.012) },
    dvCyanLo: { value: V3(...lin('#E6E9C9')) }, dvCyanHi: { value: V3(...lin('#1E3F66')) },
    dvLight: { value: 1 }, dvTint: { value: V3(1, 1, 1) },
    dvCells: { value: blank }, dvCellsOn: { value: 0 },
  };
}

const VERT = /* glsl */`varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }`;
const CELL_FRAG = /* glsl */`
void main(){ dvEdge = 0.; float a = dvCellCov(floor(gl_FragCoord.xy) + dvRankOff); gl_FragColor = vec4(a, dvEdge, 0., 1.); }`;
const FRAG_STANDALONE = /* glsl */`
uniform float dvLight; uniform vec3 dvTint; varying vec2 vUv;
void main(){ vec4 pr = dvPrint(vUv); gl_FragColor = vec4(pr.rgb * dvLight * dvTint, 1.); }`;

export const DEVELOP_GLSL = /* glsl */`
uniform sampler2D dvSrc, dvCert, dvReg1, dvReg2, dvRank, dvM0, dvM1, dvM2;
uniform vec4 dvFlags;
uniform vec2 dvRankOff, dvRankMax;
uniform vec4 dvCrop;
uniform vec2 dvSize, dvScreen;
uniform vec3 dvLevels;
uniform vec4 dvChem;
uniform float dvFrac, dvDmax;
uniform vec2 dvPulses;
uniform float dvPulseTau[16];
uniform vec3 dvLead1;
uniform vec2 dvLead2, dvOut, dvLeadNL;
uniform float dvStops;
uniform vec4 dvFog, dvFuse;
uniform float dvCyan;
uniform vec4 dvStrip;
uniform vec2 dvStripAx;
uniform vec4 dvMultiW;
uniform vec4 dvMultiXf[3];
uniform vec4 dvMultiCrop[3];
uniform float dvGen;
uniform vec4 dvSoft;
uniform float dvSoftD;
uniform vec4 dvRings[4];
uniform vec3 dvPaper, dvInk, dvCyanLo, dvCyanHi;
uniform sampler2D dvCells;
uniform float dvCellsOn;
float dvEdge;
float dvLumA(vec3 c){ return dot(c, vec3(.2126, .7152, .0722)); }
float dvCurve(float s){ return 1. - exp(-pow(max(s, 0.), dvChem.z)); }
// the cosine spot 0.5 + 0.25 (cos 2 pi x + cos 2 pi y): round dots below 50 %, round holes above; this maps the wanted
// dot area to the spot threshold so the inked area is exact (fitted to 0.2 %)
float dvAreaFix(float a){ float b = min(a, 1. - a); float g = b * (1.54599 + b * (-1.04928 - .07654 * b)); return a <= .5 ? g : 1. - g; }
// the photo's density at a point (0 = paper white .. dvDmax), after +st stops of print exposure (speculars survive)
float dvTarget(vec3 c, float st){
  float y = (dvLumA(c) - dvLevels.x) / (dvLevels.y - dvLevels.x);
  float spec = smoothstep(1.02, 1.15, y);
  float yc = clamp(y, 0., 1.), yp = (yc + dvLevels.z * yc * yc * (1. - yc)) * exp2(-st);
  if (st > 0.) yp = max(yp, spec);
  return -log(max(yp, exp2(-dvDmax * 3.3219281))) * .4342945;
}
// coverage (dot area 0..1) of the print at a cell centre uv
float dvCov(vec2 uv, float lodAuto, float age){
  vec2 puv = dvCrop.xy + uv * dvCrop.zw;
  float lod = max(lodAuto, dvChem.w) + dvGen * .55, sharp = 1.;
  if (dvSoft.x > 0. || dvSoft.z > 0.) {
    sharp = 0.;
    for (int i = 0; i < 4; i++) {
      if (float(i) >= dvSoft.z) break;
      vec4 r = dvRings[i]; if (r.x < 0.) continue;
      float d = length((uv - r.yz) * vec2(dvSize.x / dvSize.y, 1.));
      float front = r.w * r.x + dvSoft.w;                       // the sharp disc already has a radius on the hit frame
      sharp = max(sharp, 1. - smoothstep(front - dvSoft.w, front, d));
    }
    lod = max(lod, mix(dvSoft.x, dvSoft.y, sharp));
  }
  float st = dvStops;
  if (dvStripAx.y > 0.) {
    float band = clamp(floor((dvStripAx.x > .5 ? uv.y : uv.x) * dvStripAx.y), 0., dvStripAx.y - 1.);
    st = band < .5 ? dvStrip.x : band < 1.5 ? dvStrip.y : band < 2.5 ? dvStrip.z : dvStrip.w;
    if (st < 0.) return 0.;
  }
  float Dt = dvTarget(textureLod(dvSrc, puv, lod).rgb, st), at = Dt / dvDmax;
  float cert = dvFlags.x > .5 ? texture(dvCert, puv).r : 1.;
  float cap = Dt * (.35 + .65 * cert);
  float k = dvChem.y * (.35 + .65 * at) * (.25 + .75 * cert);
  float D = cap * dvCurve(k * age) * mix(dvSoftD, 1., sharp);
  if (dvFlags.y > .5) {
    vec3 r1 = texture(dvReg1, puv).rgb, r2 = texture(dvReg2, puv).rgb;
    float lead = max(max(r1.r * dvLead1.x, r1.g * dvLead1.y), max(r1.b * dvLead1.z, r2.g * dvLead2.y));
    lead = max(lead * smoothstep(.18, .5, Dt), r2.r * dvLead2.x * smoothstep(dvLeadNL.x, dvLeadNL.y, Dt));   // a lead moves the feature, not the skin
    if (dvOut.x > 0.) lead = max(lead, 1. - smoothstep(dvOut.x - dvOut.y, dvOut.x, r2.b));
    D = mix(D, cap, lead);
  }
  if (dvFlags.w > 0.) {                                        // multiple exposure: densities add, toward black
    D *= dvMultiW.w;
    for (int i = 0; i < 3; i++) {
      if (float(i) >= dvFlags.w) break;
      vec4 xf = dvMultiXf[i], cr = dvMultiCrop[i];
      vec2 muv = cr.xy + ((uv - .5) / xf.z + .5 + xf.xy) * cr.zw;
      vec3 mc = i == 0 ? textureLod(dvM0, muv, lod).rgb : i == 1 ? textureLod(dvM1, muv, lod).rgb : textureLod(dvM2, muv, lod).rgb;
      float w = i == 0 ? dvMultiW.x : i == 1 ? dvMultiW.y : dvMultiW.z;
      D += w * dvTarget(mc, st);
    }
  }
  if (dvGen > 0.) D = dvDmax * pow(clamp(D / dvDmax, 0., 1.), 1. + .25 * dvGen) * pow(.82, dvGen);
  if (dvFog.x > 0.) {
    float m = dvFog.w > 0. ? smoothstep(dvFog.w * .92, dvFog.w, length((uv - dvFog.yz) * vec2(1., dvSize.y / dvSize.x))) : 1.;
    D += dvFog.x * .6 * m;
  }
  if (dvFuse.z > .5 && dvFuse.x >= 0.) {
    float burned = 1. - smoothstep(dvFuse.x - dvFuse.y, dvFuse.x, cert);
    D = max(D, .97 * dvDmax * burned);
    dvEdge = max(dvEdge, exp(-pow((cert - dvFuse.x) / (dvFuse.y * .5), 2.)) * step(.01, at + .05));
  }
  // density -> dot area: the cell's mean reflectance (paper x (1 - a) + ink x a) equals paper x 10^-D
  float Rk = dot(dvInk, vec3(.2126, .7152, .0722)) / dot(dvPaper, vec3(.2126, .7152, .0722));
  return clamp((1. - exp2(-3.3219281 * max(D, 0.))) / (1. - Rk), 0., 1.);
}
// the dot area of halftone cell ci (lattice index; its centre is the cell's sample point): pulse mask, age, density
float dvCellCov(vec2 ci){
  float pitch = dvScreen.x, ca = cos(dvScreen.y), sa = sin(dvScreen.y);
  vec2 qc = (ci + .5) * pitch;
  vec2 uvc = vec2(ca * qc.x - sa * qc.y, sa * qc.x + ca * qc.y) / dvSize;
  float lod = log2(max(1., pitch / dvSize.y * dvCrop.w * float(textureSize(dvSrc, 0).y) * .8));
  float mask = 1., age = dvChem.x;
  if (dvFlags.z > .5) {                                        // pulses: the dot's rank decides when it started
    ivec2 ti = clamp(ivec2(ci - dvRankOff), ivec2(0), ivec2(dvRankMax));
    float r = texelFetch(dvRank, ti, 0).r;
    mask = r < dvFrac ? 1. : 0.;
    int nj = int(clamp(floor(dvPulses.x + log2(max(r, 1e-7))) + 1., 1., dvPulses.x)) - 1;
    age = dvChem.x - dvPulseTau[nj];
  }
  return dvCov(clamp(uvc, 0., 1.), lod, age) * mask;
}
vec4 dvPrint(vec2 uv){
  dvEdge = 0.;
  vec2 p = uv * dvSize;
  float pitch = dvScreen.x, ca = cos(dvScreen.y), sa = sin(dvScreen.y);
  vec2 q = vec2(ca * p.x + sa * p.y, -sa * p.x + ca * p.y) / max(pitch, 1e-5);
  float w = max(fwidth(q.x), fwidth(q.y));                     // cells per pixel
  vec2 tsz = vec2(textureSize(dvSrc, 0));
  vec2 puv = dvCrop.xy + uv * dvCrop.zw;
  float lodAuto = log2(max(1e-4, max(fwidth(puv.x) * tsz.x, fwidth(puv.y) * tsz.y)));
  vec2 ci = floor(q);
  float a;
  if (pitch > 0. && dvCellsOn > .5) {                          // the cell pass already developed every dot
    vec2 ce = texelFetch(dvCells, clamp(ivec2(ci - dvRankOff), ivec2(0), ivec2(dvRankMax)), 0).rg;
    a = ce.r; dvEdge = ce.g;
  } else if (pitch > 0.) a = dvCellCov(ci);
  else a = dvCov(uv, lodAuto, dvChem.x);
  float ink = a;
  if (pitch > 0.) {
    vec2 f = q - ci - .5;
    float T = .5 + .25 * (cos(6.2831853 * f.x) + cos(6.2831853 * f.y));
    float th = 1. - dvAreaFix(a), aa = clamp(w * .8, .004, .5);
    float dotv = smoothstep(th - aa, th + aa, T);
    if (a <= .002) dotv = 0.; else if (a >= .998) dotv = 1.;
    ink = mix(dotv, a, smoothstep(.3, .62, w));                // a screen finer than the pixels averages to tone
  }
  vec3 refl = mix(dvPaper, dvInk, ink);
  if (dvCyan > 0.) refl = mix(refl, mix(dvCyanLo, dvCyanHi, ink), dvCyan);
  return vec4(refl, a);
}
`;
