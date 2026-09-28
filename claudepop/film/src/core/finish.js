// finish.js - the per-frame finish chain (BIBLE 4.7) as the core drives it (lane A). Owns: the layer stack, the plate
// switch, the window mask, the HUD/type canvas, the card dim, the lumaProbe and the call into post.js.
//
// Two post paths:
//   post v2 (lane B, when src/post.js Post has renderFrame): the core calls
//       post.renderFrame({ layers, grade, t, seed, hud, window, accent, layer, flash, fade, dim })
//         layers  [{ scene, camera, clearDepth }] (plate layer already inserted)      grade  the merged preset (grade.js vocabulary)
//         seed    grain seed: frame index, or frozenSeed(shot) when grade.grainFrozen   hud  the Hud (type + HUD drawn, NO mask)
//         window  { x, y, w, h } output px (post masks outside -> INK after grain/halftone, before the HUD)
//         accent  [{ scene, camera }] 3D VOICE layers (2D accent draws are already on the HUD canvas)
//     and post.probeLuma?(layers, grade) -> (x, y, w, h) => { mean, std } if it provides its own probe.
//   legacy (today's post.js): layers pre-composited into a half-float stack when there are several; grade mapped onto the
//     legacy params; the window mask and 3D accents drawn onto the HUD canvas (so, until v2, grain touches the INK surround
//     and the dot screen is the legacy 0/90 deg one). Legacy 3D accents render with their own depth only (not occluded
//     by the main layers): keep VOICE objects in front (catchlights, the Omega point) or give them an occluder copy.
import * as THREE from 'three';
import { frozenSeed } from './rng.js';
import { plateLayer } from '../plates/plates.js';

const FS_VERT = 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }';
const INK = 0x0a0a09;

export class Finish {
  constructor(ctx) {
    this.ctx = ctx; this.targets = new Map();
    this.quadScene = new THREE.Scene(); this.cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.copyMat = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false, uniforms: { t: { value: null } },
      fragmentShader: 'uniform sampler2D t; varying vec2 vUv; void main(){ gl_FragColor = texture2D(t, vUv); }' });
    this.probeMat = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false, uniforms: { t: { value: null }, e: { value: 1 } },
      fragmentShader: `uniform sampler2D t; uniform float e; varying vec2 vUv;
        vec3 aces(vec3 x){ return clamp((x * (2.51 * x + .03)) / (x * (2.43 * x + .59) + .14), 0., 1.); }
        void main(){ vec3 c = aces(texture2D(t, vUv).rgb * e); c = mix(c * 12.92, 1.055 * pow(c, vec3(1. / 2.4)) - .055, step(.0031308, c));
          gl_FragColor = vec4(vec3(dot(c, vec3(.2126, .7152, .0722))), 1.); }` });
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.copyMat); this.quadScene.add(this.quad);
    this.accCanvas = null;
  }
  _t(W, H, samples = 4) {
    const key = `${W}x${H}x${samples}`;
    if (!this.targets.has(key)) {
      const stack = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples, depthBuffer: true });
      const probe = new THREE.WebGLRenderTarget(W >> 2, H >> 2, { type: THREE.UnsignedByteType, depthBuffer: false });
      // accents: 2x supersampled without MSAA (an MSAA resolve costs ~160 ms at 720p under SwiftShader, even scissored)
      const accent = new THREE.WebGLRenderTarget(W * 2, H * 2, { type: THREE.UnsignedByteType, samples: 0, depthBuffer: true });
      accent.texture.colorSpace = THREE.SRGBColorSpace;
      this.targets.set(key, { stack, probe, accent, probeBuf: new Uint8Array((W >> 2) * (H >> 2) * 4), accBuf: new Uint8Array(W * H * 16) });
    }
    return this.targets.get(key);
  }
  _renderLayers(target, layers, clear, clearAlpha = 1) {
    const r = this.ctx.renderer, ac = r.autoClear;
    r.setRenderTarget(target); r.setClearColor(clear, clearAlpha); r.clear();
    r.autoClear = false;
    layers.forEach((L, i) => { if (i && L.clearDepth !== false) r.clearDepth(); r.render(L.scene, L.camera); });
    r.autoClear = ac; r.setRenderTarget(null);
  }

  // spec = the scene's frame spec; fr = ctx.frame; o = renderAt opts. Returns { dim, blocks }.
  render(spec, fr, o) {
    const ctx = this.ctx, { W, H } = ctx, r = ctx.renderer;
    const samples = spec.msaa ?? 4, T = this._t(W, H, samples), post = ctx.postFor(samples);
    const shot = fr.shot, t = fr.t;
    const v2 = typeof post.renderFrame === 'function';
    const g = ctx.grade(spec.grade || shot.look || 'DARKROOM', spec.post ? pickGrade(spec.post) : {});
    const clear = spec.clear ?? INK;

    // layers + plate (stage 2 only: stage 1 has no plates, the scene's layers are the previs)
    let layers = (spec.layers || []).filter(L => L && L.scene && L.camera);
    let plateUsed = null, plateL = null;
    if (spec.plate && ctx.plates.has(spec.plate.id) && (spec.plate.from === undefined || t >= spec.plate.from)) {
      const tex = ctx.plates.frame(spec.plate.id, t);
      if (tex) { plateL = plateLayer(tex, fr.rect, !!spec.plate.over); layers = plateL.over ? [...layers, plateL] : [plateL, ...layers]; plateUsed = spec.plate.id; }
    }
    if (o.layer === 'accent') {                                   // the VOICE layer alone, on black
      this._renderLayers(null, (spec.accent || []).filter(a => a.scene), INK);
      plateL && plateL.dispose();
      return { dim: 0, blocks: [], plate: plateUsed };
    }

    // lumaProbe: lazily renders the stack once and reads a tone-mapped luma at 1/4 res
    let stackReady = false, probeReady = false;
    const ensureStack = () => { if (!stackReady) { this._renderLayers(T.stack, layers, clear); stackReady = true; } };
    const probe = (x, y, w, h) => {
      if (!probeReady) {
        ensureStack();
        this.quad.material = this.probeMat; this.probeMat.uniforms.t.value = T.stack.texture; this.probeMat.uniforms.e.value = g.exposure ?? 1;
        r.setRenderTarget(T.probe); r.render(this.quadScene, this.cam); r.setRenderTarget(null);
        r.readRenderTargetPixels(T.probe, 0, 0, W >> 2, H >> 2, T.probeBuf); probeReady = true;
      }
      const pw = W >> 2, ph = H >> 2, s = pw / 1920;
      const x0 = Math.max(0, Math.floor(x * s)), x1 = Math.min(pw, Math.ceil((x + w) * s)), y0 = Math.max(0, Math.floor(y * s)), y1 = Math.min(ph, Math.ceil((y + h) * s));
      let n = 0, sum = 0, sq = 0;
      for (let yy = y0; yy < y1; yy++) for (let xx = x0; xx < x1; xx++) { const v = T.probeBuf[((ph - 1 - yy) * pw + xx) * 4] / 255; sum += v; sq += v * v; n++; }
      const mean = n ? sum / n : 0; return { mean, std: n ? Math.sqrt(Math.max(0, sq / n - mean * mean)) : 0 };
    };

    // HUD canvas: [legacy: window mask] -> 3D accents (legacy) + 2D accents -> overlay -> proof HUD -> type -> previs tag
    const hud = ctx.hud; hud.clear();
    const c = hud.ctx, rect = fr.rect, rp = ctx.win.px(rect, ctx.k);
    let layout = { blocks: [], dim: 0, draw() {} };
    if (o.layer !== 'pregrade') {
      if (!v2) { c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = '#0A0A09';
        c.fillRect(0, 0, rp.x, H); c.fillRect(rp.x + rp.w, 0, W - rp.x - rp.w, H); c.fillRect(rp.x, 0, rp.w, rp.y); c.fillRect(rp.x, rp.y + rp.h, rp.w, H - rp.y - rp.h); c.restore(); }
      const acc3 = (spec.accent || []).filter(a => a.scene && a.camera);
      if (acc3.length && !v2) this._accentToHud(acc3, T);
      for (const a of spec.accent || []) if (typeof a.draw === 'function') { c.save(); a.draw(c, fr); c.restore(); }
      if (typeof spec.overlay === 'function') { c.save(); spec.overlay(hud, fr); c.restore(); }
      const hudState = spec.hud === undefined ? { marks: {} } : spec.hud;
      if (hudState) ctx.proof.draw(hudState, rect, t);
      const text = spec.text === undefined ? shot.text : spec.text;
      layout = ctx.type.layout(text, t, probe, { shot, s: fr.s, rect, register: g.name, card: !!rect.card }) || layout;
      c.save(); layout.draw(hud); c.restore();
      if (o.previsTags && shot.source === 'GEN' && !plateUsed && inGenSpan(shot, t)) previsTag(c, rect, shot);
    }

    // post
    // dim (stops) darkens the IMAGE, not the type: in the legacy path it is an exposure cut before the tone curve;
    // fade (0..1) takes the whole frame toward black (type included), flash toward white
    const dim = (spec.post && spec.post.dim || 0) + (layout.dim || 0);
    const fade = spec.post && spec.post.fade || 0;
    const flash = spec.post && spec.post.flash || 0;
    const seed = g.grainFrozen ? frozenSeed(shot.id) : fr.f;
    if (v2) {
      post.renderFrame({ layers, grade: g, t, seed, hud: o.layer === 'pregrade' ? null : hud, window: rp, accent: (spec.accent || []).filter(a => a.scene),
        layer: o.layer, flash, fade, dim, stack: stackReady ? T.stack : null });
    } else {
      const p = o.layer === 'pregrade' ? pregradeParams(g) : legacyParams(g, H);
      p.flash = o.layer === 'pregrade' ? 0 : flash; p.fade = o.layer === 'pregrade' ? 0 : fade; p.clear = clear;
      if (o.layer !== 'pregrade') p.exposure *= Math.pow(2, -dim);
      let scene, camera;
      if (!stackReady && layers.length === 1) ({ scene, camera } = layers[0]);
      else if (!stackReady && layers.length === 0) { scene = this.quadScene; camera = this.cam; this.quad.material = this.copyMat; this.copyMat.uniforms.t.value = null; this.quad.visible = false; }
      else { ensureStack(); this.quad.visible = true; this.quad.material = this.copyMat; this.copyMat.uniforms.t.value = T.stack.texture; scene = this.quadScene; camera = this.cam; }
      post.render(scene, camera, p, seed / 24, o.layer === 'pregrade' ? null : hud);
      this.quad.visible = true;
    }
    plateL && plateL.dispose();
    return { dim, blocks: layout.blocks || [], plate: plateUsed };
  }

  // legacy accent composite: render the VOICE layers to RGBA8 (2x supersampled) and draw them onto the HUD canvas (after
  // the grade). Only the screen region the accent objects cover is cleared, rendered (scissor) and read back.
  _accentToHud(layers, T) {
    const { W, H } = this.ctx, r = this.ctx.renderer;
    const box = new THREE.Box3(), v = new THREE.Vector3();
    let x0 = W, y0 = H, x1 = 0, y1 = 0, all = false;
    for (const L of layers) {
      L.scene.updateMatrixWorld(); L.camera.updateMatrixWorld(); box.setFromObject(L.scene);
      if (box.isEmpty()) continue;
      for (let i = 0; i < 8; i++) {
        v.set(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z);
        v.applyMatrix4(L.camera.matrixWorldInverse);
        if (L.camera.isPerspectiveCamera && v.z > -L.camera.near) { all = true; break; }
        v.applyMatrix4(L.camera.projectionMatrix);
        x0 = Math.min(x0, (v.x + 1) / 2 * W); x1 = Math.max(x1, (v.x + 1) / 2 * W); y0 = Math.min(y0, (v.y + 1) / 2 * H); y1 = Math.max(y1, (v.y + 1) / 2 * H);
      }
    }
    if (all) { x0 = 0; y0 = 0; x1 = W; y1 = H; }
    x0 = Math.max(0, Math.floor(x0) - 8); y0 = Math.max(0, Math.floor(y0) - 8); x1 = Math.min(W, Math.ceil(x1) + 8); y1 = Math.min(H, Math.ceil(y1) + 8);
    const w = x1 - x0, h = y1 - y0;                    // (y is bottom-up here, as in GL)
    if (w <= 0 || h <= 0) return;
    r.setScissorTest(true); T.accent.scissor.set(x0 * 2, y0 * 2, w * 2, h * 2); T.accent.scissorTest = true;
    this._renderLayers(T.accent, layers, 0x000000, 0);
    r.setScissorTest(false); T.accent.scissorTest = false;
    const W2 = w * 2, buf = T.accBuf.subarray(0, W2 * h * 2 * 4);
    r.readRenderTargetPixels(T.accent, x0 * 2, y0 * 2, W2, h * 2, buf);
    // 2x2 box filter (the 2x2 samples of opaque objects over a transparent clear average to premultiplied colour),
    // flip to top-down, then un-premultiply for putImageData
    const img = new ImageData(w, h), d = img.data;
    for (let y = 0; y < h; y++) {
      const r0 = (2 * y) * W2 * 4, r1 = r0 + W2 * 4, o = (h - 1 - y) * w * 4;
      for (let x = 0; x < w; x++) {
        const i0 = r0 + x * 8, i1 = r1 + x * 8, j = o + x * 4;
        const a = buf[i0 + 3] + buf[i0 + 7] + buf[i1 + 3] + buf[i1 + 7];
        if (!a) continue;
        for (let k = 0; k < 3; k++) {
          const sum = buf[i0 + k] * buf[i0 + 3] + buf[i0 + 4 + k] * buf[i0 + 7] + buf[i1 + k] * buf[i1 + 3] + buf[i1 + 4 + k] * buf[i1 + 7];
          d[j + k] = sum / a;
        }
        d[j + 3] = a / 4;
      }
    }
    if (!this.accCanvas || this.accCanvas.width < w || this.accCanvas.height < h) {
      // a CPU-backed canvas like the HUD's: drawing a (GPU) OffscreenCanvas onto the HUD made Chromium rasterise the rest
      // of that frame's HUD differently (antialiased edges 1 premultiplied level apart) - a first-frame non-determinism
      this.accCanvas = document.createElement('canvas'); this.accCanvas.width = W; this.accCanvas.height = H;
      this.accCtx = this.accCanvas.getContext('2d', { willReadFrequently: true });
    }
    this.accCtx.clearRect(0, 0, w, h); this.accCtx.putImageData(img, 0, 0);
    const c = this.ctx.hud.ctx; c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.drawImage(this.accCanvas, 0, 0, w, h, x0, H - y0 - h, w, h); c.restore();
  }
}

// frameSpec.post keys that override the grade preset (the rest are per-frame effects handled above)
function pickGrade(p) {
  const o = { ...p };
  if (p.pitch !== undefined || p.halftoneAngle !== undefined) o.halftone = { pitch: p.pitch ?? 4, angle: p.halftoneAngle ?? 45 };
  delete o.flash; delete o.dim; delete o.fade; delete o.pitch; delete o.halftoneAngle;
  return o;
}
// grade.js vocabulary -> today's post.js params
function legacyParams(g, H) {
  const lift = g.lift || 0, bloom = g.bloom && typeof g.bloom === 'object' ? g.bloom : null;
  if (g.ink || g.paper) return { exposure: g.exposure ?? 1, bloom: 0, halation: 0, mono: 1, sat: 1, contrast: 1, lift: [0, 0, 0], grain: 0, vignette: 0, screen: 0 };
  return {
    exposure: g.exposure ?? 1, bloom: bloom ? bloom.amount : 0, bloomThresh: bloom ? bloom.thresh : 0.9,
    halation: g.halation || 0, halationTint: [0.92, 0.96, 1.0], mono: g.mono ?? 1, sat: 1,
    toneShadow: g.toneShadow || [1, 1, 1], toneHigh: g.toneHigh || [1, 1, 1], contrast: g.contrast ?? 1, gamma: 1,
    lift: [lift, lift, lift], gain: g.gain ? [g.gain, g.gain, g.gain] : [1, 1, 1],
    grain: (g.grain || 0) * 2, grainSize: 1, vignette: g.vignette ?? 0,
    screen: g.halftone ? 0.3 : 0, screenPeriod: g.halftone ? Math.max(2, g.halftone.pitch * H / 1080) : 3,
    ca: 0, scanlines: 0, bars: 0, hudOpacity: 1,
  };
}
function pregradeParams(g) {
  return { exposure: g.exposure ?? 1, bloom: 0, halation: 0, mono: 0, sat: 1, contrast: 1, lift: [0, 0, 0], gain: [1, 1, 1], grain: 0, vignette: 0, screen: 0, scanlines: 0, ca: 0, bars: 0 };
}
// the part of a GEN shot the plate will cover (all of it, or the tail: S15 from 50.49, S54 from 151.145), by frame
function inGenSpan(shot, t) {
  const use = shot.gen && shot.gen.use; if (!use) return true;
  return Math.round(t * 24) >= Math.round((shot.t1 - (use[1] - use[0])) * 24);
}
function previsTag(c, r, shot) {
  const s = `PREVIS · ${shot.gen && shot.gen.plate || 'GEN'}`;
  c.save(); c.font = '500 16px "IBM Plex Mono", monospace'; c.letterSpacing = '2.5px'; c.textAlign = 'right'; c.textBaseline = 'alphabetic';
  const w = c.measureText(s).width, x = r.x + r.w - 40, y = r.y + r.h - 96;
  c.globalAlpha = 0.9; c.strokeStyle = '#FAF9F5'; c.lineWidth = 1; c.strokeRect(x - w - 14, y - 19, w + 24, 28);
  c.fillStyle = '#FAF9F5'; c.fillText(s, x + 1, y); c.restore();
}
