// post.js - HDR scene -> film finish, for the offline renderer (headless Chromium + SwiftShader, so every pass counts;
// lane B). Two entry points on one class:
//
//   const post = new Post(renderer, W, H, { samples: 4 });
//
//   post.renderFrame(o)   THE FILM (BIBLE 4.7), called by src/core/finish.js. o = { layers, grade, t, seed, hud, window,
//                         accent, layer, flash, fade, dim, stack, clear }
//     layers  [{ scene, camera, clearDepth }] rendered in order into the half-float HDR target (MSAA = samples); or
//     stack   a render target the core already filled with them (it rendered the layers for the luma probe)
//     grade   a src/grade.js preset (merged with the scene's post overrides)
//     seed    grain seed (frame index; frozen grain: the shot's seed)       hud  src/hud.js Hud (type + HUD) or null
//     window  { x, y, w, h } output px, top-left origin: outside -> INK (no grain, no dots), under the HUD
//     accent  [{ scene, camera, occlude }] VOICE objects: rendered alone (2x supersampled, scissored to their screen
//             box, no MSAA), composited AFTER the grade with a 6 px bloom, so VOICE stays pure. By default they are not
//             occluded by the main layers (keep them in front: catchlights, the Omega point, marks on sheets);
//             occlude: true first writes the main layers' depth (depth only, same scissor) so the scene hides them -
//             use it when the accent camera is the layer camera (costs one depth-only pass of the main layers)
//     layer   'final' | 'pregrade' (exposure + tone curve only: for the likeness scorer)
//     flash   0..1 to white (whole frame)   fade 0..1 to black (whole frame)   dim  stops, image only (card / freeze dim)
//     Chain per pixel: HDR (+ bloom / halation by register) -> exposure x 2^-dim -> ACES fit -> display sRGB ->
//     grade (mono mix with split tone, keepHue, saturation cap, S-curve contrast, lift / gain) -> AM halftone (round
//     dots, per-shot angle and pitch, dot area from linear luminance, mixed by amount, mean tone kept) -> grain (moving
//     or frozen) -> vignette (window-relative) -> accent composite + bloom -> window mask -> type / HUD -> flash, fade
//     -> 8-bit dither.
//     Returns { ms } (CPU time of the call).
//
//   post.render(scene, camera, params, t, hud?)     LEGACY (film/lookdev): t = film time in seconds (grain / dither
//     phase); hud composited after the grade. Passes: scene -> half-float target (optional MSAA) -> bright pass at 1/4
//     -> separable blurs at 1/4 and 1/8 -> one full-resolution composite: chromatic aberration, bloom + halation,
//     exposure, ACES fit, display sRGB, grade (mono mix with split toning, saturation, contrast, lift / gain, tint),
//     vignette, HUD overlay, grain, an ordered dot screen, scanlines, letterbox bars, 8-bit dither.
//     params (all optional): exposure, bloom, bloomThresh, halation, halationTint[3], sat, contrast, lift[3], gain[3],
//     gamma, mono (0..1), toneShadow[3], toneHigh[3], grain, grainSize, vignette, ca, screen, screenPeriod, scanlines,
//     scanPeriod, bars (fraction of height per bar), hudOpacity, fade, flash, clear (hex).
import * as THREE from 'three';

const FS_VERT = /* glsl */`varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }`;

export class Post {
  constructor(renderer, W, H, { samples = 4 } = {}) {
    this.r = renderer;
    this.W = W; this.H = H;
    const rt = (w, h, depth, s = 0) => new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, depthBuffer: depth,
      samples: s, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
    this.rtScene = rt(W, H, true, samples);
    this.rtA = rt(W >> 2, H >> 2, false); this.rtB = rt(W >> 2, H >> 2, false);
    this.rtC = rt(W >> 3, H >> 3, false); this.rtD = rt(W >> 3, H >> 3, false);
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2));
    this.fs = new THREE.Scene(); this.fs.add(this.quad);
    this.cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.hudTex = null;
    this.bright = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false,
      uniforms: { tSrc: { value: null }, uThresh: { value: 1 } },
      fragmentShader: /* glsl */`uniform sampler2D tSrc; uniform float uThresh; varying vec2 vUv;
        void main(){
          vec2 px = vec2(dFdx(vUv.x), dFdy(vUv.y));
          vec3 c = (texture2D(tSrc, vUv).rgb + texture2D(tSrc, vUv + px * .5).rgb + texture2D(tSrc, vUv - px * .5).rgb) / 3.;
          float l = max(c.r, max(c.g, c.b));
          gl_FragColor = vec4(c * smoothstep(uThresh, uThresh * 1.6 + .15, l), 1.); }` });
    this.blur = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false,
      uniforms: { tSrc: { value: null }, uDir: { value: new THREE.Vector2() } },
      fragmentShader: /* glsl */`uniform sampler2D tSrc; uniform vec2 uDir; varying vec2 vUv;
        void main(){ vec3 s = texture2D(tSrc, vUv).rgb * .227;
          s += (texture2D(tSrc, vUv + uDir * 1.385).rgb + texture2D(tSrc, vUv - uDir * 1.385).rgb) * .316;
          s += (texture2D(tSrc, vUv + uDir * 3.231).rgb + texture2D(tSrc, vUv - uDir * 3.231).rgb) * .070;
          gl_FragColor = vec4(s, 1.); }` });
    this.comp = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false,
      uniforms: {
        tScene: { value: this.rtScene.texture }, tNear: { value: this.rtA.texture }, tFar: { value: this.rtD.texture },
        tHud: { value: null }, uHud: { value: 0 }, uRes: { value: new THREE.Vector2(W, H) }, uFrame: { value: 0 },
        uExposure: { value: 1 }, uBloom: { value: .5 }, uHal: { value: 0 }, uHalTint: { value: new THREE.Vector3(1, .35, .12) },
        uSat: { value: 1 }, uContrast: { value: 1 }, uGamma: { value: 1 }, uLift: { value: new THREE.Vector3() },
        uGain: { value: new THREE.Vector3(1, 1, 1) }, uMono: { value: 0 },
        uToneS: { value: new THREE.Vector3(1, 1, 1) }, uToneH: { value: new THREE.Vector3(1, 1, 1) },
        uGrain: { value: .05 }, uGrainSize: { value: 1 }, uVig: { value: .3 }, uCA: { value: .0 },
        uScreen: { value: 0 }, uScreenP: { value: 3 }, uScan: { value: 0 }, uScanP: { value: 3 },
        uBars: { value: 0 }, uFade: { value: 0 }, uFlash: { value: 0 } },
      fragmentShader: /* glsl */`
        uniform sampler2D tScene, tNear, tFar, tHud; uniform float uHud; uniform vec2 uRes; uniform float uFrame;
        uniform float uExposure, uBloom, uHal, uSat, uContrast, uGamma, uMono, uGrain, uGrainSize, uVig, uCA;
        uniform float uScreen, uScreenP, uScan, uScanP, uBars, uFade, uFlash;
        uniform vec3 uHalTint, uLift, uGain, uToneS, uToneH; varying vec2 vUv;
        float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
        vec3 aces(vec3 x){ return clamp((x * (2.51 * x + .03)) / (x * (2.43 * x + .59) + .14), 0., 1.); }
        vec3 toSRGB(vec3 c){ return mix(c * 12.92, 1.055 * pow(c, vec3(1. / 2.4)) - .055, step(.0031308, c)); }
        void main(){
          vec2 uv = vUv, c = uv - .5;
          vec3 col;
          if (uCA > 0.) {
            col.r = texture2D(tScene, uv - c * uCA).r; col.g = texture2D(tScene, uv).g; col.b = texture2D(tScene, uv + c * uCA).b;
          } else col = texture2D(tScene, uv).rgb;
          vec3 near = texture2D(tNear, uv).rgb, far = texture2D(tFar, uv).rgb;
          col += (near * .55 + far * .75) * uBloom;
          col += (far * 1.2 + near * .2) * uHal * uHalTint;          // halation: wide, red-shifted
          col = aces(col * uExposure);
          col = toSRGB(col);                                          // grade in display space (perceptual pivots)
          float l = dot(col, vec3(.2126, .7152, .0722));
          vec3 mono = l * mix(uToneS, uToneH, smoothstep(.1, .85, l));
          col = mix(col, mono, uMono);
          col = mix(vec3(dot(col, vec3(.2126, .7152, .0722))), col, uSat);
          col = pow(max(col, 0.), vec3(uGamma));
          col = (col - .5) * uContrast + .5;
          col = col * uGain + uLift * (1. - col);
          col = clamp(col, 0., 1.);
          vec2 q = vUv - .5; q.x *= uRes.x / uRes.y * .75;
          col *= 1. - uVig * smoothstep(.15, .85, dot(q, q) * 2.4);
          if (uHud > 0.) { vec4 hd = texture2D(tHud, vec2(vUv.x, 1. - vUv.y)); col = mix(col, hd.rgb, hd.a * uHud); }
          vec2 px = floor(vUv * uRes);
          float g = h12(floor(px / uGrainSize) + fract(uFrame * .6180339) * 1013.) + h12(px.yx * 1.37 + fract(uFrame * .4142) * 719.) - 1.;
          float lum = dot(col, vec3(.333));
          col += g * uGrain * (.35 + 2.6 * lum * (1. - lum));
          if (uScreen > 0.) {                                           // halftone / LCD dot screen
            vec2 s = (px + .5) / uScreenP * 6.2831853;
            float d = .5 + .5 * cos(s.x) * cos(s.y);
            col *= 1. - uScreen * (1. - d) * (.55 + .45 * (1. - lum));
          }
          if (uScan > 0.) col *= 1. - uScan * step(uScanP - 1., mod(px.y, uScanP));
          col = mix(col, vec3(1.), uFlash);
          col *= 1. - uFade;
          if (vUv.y < uBars || vUv.y > 1. - uBars) col = vec3(0.);
          col += (h12(px + 17.17) - .5) / 255.;
          gl_FragColor = vec4(clamp(col, 0., 1.), 1.);
        }` });
  }

  _pass(mat, target) { this.quad.material = mat; this.r.setRenderTarget(target); this.r.render(this.fs, this.cam); }

  render(scene, camera, p = {}, t = 0, hud = null) {
    const r = this.r;
    r.setRenderTarget(this.rtScene);
    r.setClearColor(p.clear ?? 0x000000, 1);
    r.clear();
    r.render(scene, camera);
    const bloomOn = (p.bloom ?? .5) > 0 || (p.halation ?? 0) > 0;
    if (bloomOn) {
      this.bright.uniforms.tSrc.value = this.rtScene.texture;
      this.bright.uniforms.uThresh.value = p.bloomThresh ?? .9;
      this._pass(this.bright, this.rtA);
      const b = this.blur.uniforms;
      const bl = (src, dst, dx, dy) => { b.tSrc.value = src.texture; b.uDir.value.set(dx / src.width, dy / src.height); this._pass(this.blur, dst); };
      bl(this.rtA, this.rtB, 1.2, 0); bl(this.rtB, this.rtA, 0, 1.2);
      bl(this.rtA, this.rtC, 1.5, 0); bl(this.rtC, this.rtD, 0, 1.5);
      bl(this.rtD, this.rtC, 3.2, 0); bl(this.rtC, this.rtD, 0, 3.2);
    }
    const u = this.comp.uniforms;
    u.uFrame.value = Math.round(t * 24);
    u.uExposure.value = p.exposure ?? 1; u.uBloom.value = bloomOn ? (p.bloom ?? .5) : 0; u.uHal.value = bloomOn ? (p.halation ?? 0) : 0;
    u.uHalTint.value.fromArray(p.halationTint ?? [1, .35, .12]);
    u.uSat.value = p.sat ?? 1; u.uContrast.value = p.contrast ?? 1; u.uGamma.value = p.gamma ?? 1;
    u.uLift.value.fromArray(p.lift ?? [0, 0, 0]); u.uGain.value.fromArray(p.gain ?? [1, 1, 1]);
    u.uMono.value = p.mono ?? 0; u.uToneS.value.fromArray(p.toneShadow ?? [1, 1, 1]); u.uToneH.value.fromArray(p.toneHigh ?? [1, 1, 1]);
    u.uGrain.value = p.grain ?? .05; u.uGrainSize.value = p.grainSize ?? 1; u.uVig.value = p.vignette ?? .3; u.uCA.value = p.ca ?? 0;
    u.uScreen.value = p.screen ?? 0; u.uScreenP.value = p.screenPeriod ?? 3; u.uScan.value = p.scanlines ?? 0; u.uScanP.value = p.scanPeriod ?? 3;
    u.uBars.value = p.bars ?? 0; u.uFade.value = p.fade ?? 0; u.uFlash.value = p.flash ?? 0;
    if (hud) {
      if (!this.hudTex) { this.hudTex = new THREE.DataTexture(new Uint8Array(this.W * this.H * 4), this.W, this.H); this.hudTex.colorSpace = THREE.NoColorSpace; }
      this.hudTex.image.data = new Uint8Array(hud.pixels().buffer);
      this.hudTex.needsUpdate = true;
      u.tHud.value = this.hudTex; u.uHud.value = p.hudOpacity ?? 1;
    } else u.uHud.value = 0;
    this._pass(this.comp, null);
  }

  // ================================================================================================ v2: the film
  _v2init() {
    if (this.v2) return this.v2;
    const W = this.W, H = this.H;
    const u8 = (w, h, depth = false) => new THREE.WebGLRenderTarget(w, h, { type: THREE.UnsignedByteType, depthBuffer: depth, samples: 0,
      minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
    const v2 = this.v2 = { acc: null, accA: null, accB: null, accBuf: null };
    v2.alloc = () => {
      if (v2.acc) return;
      v2.acc = u8(W * 2, H * 2, true); v2.acc.texture.colorSpace = THREE.NoColorSpace;
      v2.accA = u8(W >> 1, H >> 1); v2.accB = u8(W >> 1, H >> 1);
    };
    v2.bright = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false,
      uniforms: { tSrc: { value: null }, uThresh: { value: 0.85 }, uExposure: { value: 1 } },
      fragmentShader: /* glsl */`uniform sampler2D tSrc; uniform float uThresh, uExposure; varying vec2 vUv;
        vec3 aces(vec3 x){ return clamp((x * (2.51 * x + .03)) / (x * (2.43 * x + .59) + .14), 0., 1.); }
        void main(){
          vec2 px = vec2(dFdx(vUv.x), dFdy(vUv.y));
          vec3 c = (texture2D(tSrc, vUv).rgb + texture2D(tSrc, vUv + px * .5).rgb + texture2D(tSrc, vUv - px * .5).rgb) / 3.;
          float l = pow(dot(aces(c * uExposure), vec3(.2126, .7152, .0722)), 1. / 2.2);
          gl_FragColor = vec4(c * smoothstep(uThresh, uThresh + .12, l), 1.); }` });
    v2.copy = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false, uniforms: { tSrc: { value: null } },
      fragmentShader: 'uniform sampler2D tSrc; varying vec2 vUv; void main(){ gl_FragColor = texture2D(tSrc, vUv); }' });
    v2.blurA = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false,
      uniforms: { tSrc: { value: null }, uDir: { value: new THREE.Vector2() } },
      fragmentShader: /* glsl */`uniform sampler2D tSrc; uniform vec2 uDir; varying vec2 vUv;
        void main(){ vec4 s = texture2D(tSrc, vUv) * .227;
          s += (texture2D(tSrc, vUv + uDir * 1.385) + texture2D(tSrc, vUv - uDir * 1.385)) * .316;
          s += (texture2D(tSrc, vUv + uDir * 3.231) + texture2D(tSrc, vUv - uDir * 3.231)) * .070;
          gl_FragColor = s; }` });
    v2.comp = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false,
      uniforms: {
        tScene: { value: null }, tNear: { value: this.rtA.texture }, tFar: { value: this.rtD.texture }, tAcc: { value: null }, tAccB: { value: null },
        tHud: { value: null }, uRes: { value: new THREE.Vector2(W, H) }, uWin: { value: new THREE.Vector4(0, 0, W, H) },
        uExposure: { value: 1 }, uBloom: { value: 0 }, uHal: { value: 0 }, uHalTint: { value: new THREE.Vector3(0.92, 0.96, 1.0) },
        uMono: { value: 1 }, uSatCap: { value: 1 }, uContrast: { value: 1 }, uLift: { value: 0 }, uGain: { value: 1 },
        uToneS: { value: new THREE.Vector3(1, 1, 1) }, uToneH: { value: new THREE.Vector3(1, 1, 1) }, uKeepHue: { value: 0 }, uKeepW: { value: 0 },
        uHTAmount: { value: 0 }, uHTPitch: { value: 4 }, uHTRot: { value: new THREE.Vector2(1, 0) },
        uGrain: { value: 0 }, uSeed: { value: 0 }, uVig: { value: 0 }, uAcc: { value: 0 }, uAccBloom: { value: 0 },
        uHud: { value: 0 }, uFlash: { value: 0 }, uFade: { value: 0 }, uPregrade: { value: 0 }, uInk: { value: new THREE.Vector3(10 / 255, 10 / 255, 9 / 255) } },
      fragmentShader: /* glsl */`
        uniform sampler2D tScene, tNear, tFar, tAcc, tAccB, tHud; uniform vec2 uRes; uniform vec4 uWin;
        uniform float uExposure, uBloom, uHal, uMono, uSatCap, uContrast, uLift, uGain, uKeepHue, uKeepW;
        uniform float uHTAmount, uHTPitch, uGrain, uSeed, uVig, uAcc, uAccBloom, uHud, uFlash, uFade, uPregrade;
        uniform vec3 uHalTint, uToneS, uToneH, uInk; uniform vec2 uHTRot; varying vec2 vUv;
        float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
        vec3 aces(vec3 x){ return clamp((x * (2.51 * x + .03)) / (x * (2.43 * x + .59) + .14), 0., 1.); }
        vec3 toSRGB(vec3 c){ c = max(c, 0.); return mix(c * 12.92, 1.055 * pow(c, vec3(1. / 2.4)) - .055, step(.0031308, c)); }
        vec3 toLin(vec3 c){ return mix(c / 12.92, pow((c + .055) / 1.055, vec3(2.4)), step(.04045, c)); }
        float luma(vec3 c){ return dot(c, vec3(.2126, .7152, .0722)); }
        // S-curve with slope k at the pivot that keeps 0 and 1
        float sc1(float x, float k){ const float p = .45; x = clamp(x, 0., 1.);
          return x < p ? p * pow(x / p, k) : 1. - (1. - p) * pow((1. - x) / (1. - p), k); }
        float hueOf(vec3 c){ float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b)), d = mx - mn; if (d < 1e-5) return 0.;
          float h = mx == c.r ? mod((c.g - c.b) / d, 6.) : mx == c.g ? (c.b - c.r) / d + 2. : (c.r - c.g) / d + 4.; return h * 60.; }
        void main(){
          vec2 fc = gl_FragCoord.xy, uv = vUv;
          bool inWin = fc.x >= uWin.x && fc.x < uWin.x + uWin.z && fc.y >= uWin.y && fc.y < uWin.y + uWin.w;
          vec3 col;
          if (!inWin && uPregrade < .5) col = uInk;
          else {
            vec3 hdr = texture2D(tScene, uv).rgb;
            if (uBloom > 0.) hdr += (texture2D(tNear, uv).rgb * .55 + texture2D(tFar, uv).rgb * .75) * uBloom;
            if (uHal > 0.) hdr += (texture2D(tFar, uv).rgb * 1.2 + texture2D(tNear, uv).rgb * .2) * uHal * uHalTint;
            col = toSRGB(aces(hdr * uExposure));
            if (uPregrade < .5) {
              // grade (display space)
              float l = luma(col);
              vec3 toned = l * mix(uToneS, uToneH, smoothstep(.1, .85, l));
              float keep = 0.;
              if (uKeepW > 0.) { float mx = max(col.r, max(col.g, col.b)), s = mx > 1e-4 ? (mx - min(col.r, min(col.g, col.b))) / mx : 0.;
                float d = abs(mod(hueOf(col) - uKeepHue + 540., 360.) - 180.); keep = (1. - smoothstep(uKeepW * .6, uKeepW, d)) * smoothstep(.42, .6, s); }
              col = mix(col, toned, uMono * (1. - keep));
              if (uSatCap < 1.) { float mx = max(col.r, max(col.g, col.b)), mn = min(col.r, min(col.g, col.b)), s = mx > 1e-4 ? (mx - mn) / mx : 0.;
                if (s > uSatCap) col = mx - (mx - col) * (uSatCap / s); }
              col = vec3(sc1(col.r, uContrast), sc1(col.g, uContrast), sc1(col.b, uContrast));
              col = clamp((col + uLift * (1. - col)) * uGain, 0., 1.);
              // AM halftone: round dots at uHTRot, dot area = ink coverage from linear luminance (Euclidean dot:
              // ink circles below 50 %, paper holes above); mixed in linear light so the mean tone is kept
              if (uHTAmount > 0.) {
                vec3 lc = toLin(col); float Y = luma(lc), a = clamp(1. - Y, 0., 1.);
                vec2 q = mat2(uHTRot.x, uHTRot.y, -uHTRot.y, uHTRot.x) * (fc / uHTPitch);
                float aa = .75 / uHTPitch, ink;
                if (a <= .5) { float r = sqrt(a / 3.14159265); ink = 1. - smoothstep(r - aa, r + aa, length(fract(q) - .5)); }
                else { float r = sqrt((1. - a) / 3.14159265); ink = smoothstep(r - aa, r + aa, length(fract(q + .5) - .5)); }
                float Ys = 1. - ink;
                vec3 scr = Y > 1e-5 ? lc * (Ys / Y) : vec3(Ys);
                col = toSRGB(clamp(mix(lc, scr, uHTAmount), 0., 1.));
              }
              // silver grain: monochrome, strongest in the midtones
              if (uGrain > 0.) { float n = h12(fc + uSeed * vec2(17.31, 91.73)) + h12(fc.yx * 1.37 + uSeed * vec2(7.13, 3.37)) - 1.;
                float lu = luma(col); col += n * uGrain * 1.7 * (.35 + 2.6 * lu * (1. - lu)); }
              if (uVig > 0.) { vec2 wq = (fc - (uWin.xy + uWin.zw * .5)) / (uWin.zw * .5); col *= 1. - uVig * smoothstep(.45, 2.0, dot(wq, wq)); }
              // VOICE accents after the grade (premultiplied, 2x supersampled: one bilinear tap = the 2x2 box) + bloom
              if (uAcc > 0.) {
                vec4 A = texture2D(tAcc, uv);
                if (A.a > .002) col = mix(col, toSRGB(A.rgb / A.a), clamp(A.a, 0., 1.));
                vec3 g = toSRGB(texture2D(tAccB, uv).rgb) * uAccBloom;
                col = 1. - (1. - clamp(col, 0., 1.)) * (1. - g);
              }
            }
          }
          if (uHud > 0.) { vec4 hd = texture2D(tHud, vec2(uv.x, 1. - uv.y)); col = mix(col, hd.rgb, hd.a); }
          col = mix(col, vec3(1.), uFlash);
          col *= 1. - uFade;
          col += (h12(fc + 17.17 + fract(uSeed * .618) * 311.) - .5) / 255.;
          gl_FragColor = vec4(clamp(col, 0., 1.), 1.);
        }` });
    return v2;
  }

  renderFrame(o = {}) {
    const t0 = performance.now();
    const r = this.r, W = this.W, H = this.H, v2 = this._v2init(), g = o.grade || {};
    const pre = o.layer === 'pregrade';
    const INK = 0x0a0a09;
    // 1. the HDR stack
    let src = o.stack;
    if (!src) {
      const layers = (o.layers || []).filter(L => L && L.scene && L.camera);
      const ac = r.autoClear;
      r.setRenderTarget(this.rtScene); r.setClearColor(o.clear ?? INK, 1); r.clear();
      r.autoClear = false;
      layers.forEach((L, i) => { if (i && L.clearDepth !== false) r.clearDepth(); r.render(L.scene, L.camera); });
      r.autoClear = ac;
      src = this.rtScene;
    }
    const u = v2.comp.uniforms;
    const exposure = (g.exposure ?? 1) * Math.pow(2, -(pre ? 0 : (o.dim || 0)));
    // 4. bloom / halation by register (on display luminance above the threshold)
    const bl = !pre && g.bloom && typeof g.bloom === 'object' ? g.bloom : null;
    const hal = !pre && bl ? (g.halation || 0) : 0;
    if (bl && (bl.amount > 0 || hal > 0)) {
      v2.bright.uniforms.tSrc.value = src.texture; v2.bright.uniforms.uThresh.value = bl.thresh ?? 0.85; v2.bright.uniforms.uExposure.value = exposure;
      this._pass(v2.bright, this.rtA);
      const b = this.blur.uniforms;
      const blr = (s, d, dx, dy) => { b.tSrc.value = s.texture; b.uDir.value.set(dx / s.width, dy / s.height); this._pass(this.blur, d); };
      blr(this.rtA, this.rtB, 1.2, 0); blr(this.rtB, this.rtA, 0, 1.2);
      blr(this.rtA, this.rtC, 1.5, 0); blr(this.rtC, this.rtD, 0, 1.5);
      blr(this.rtD, this.rtC, 3.2, 0); blr(this.rtC, this.rtD, 0, 3.2);
    }
    // 2 / 9. VOICE accents
    const acc = pre ? [] : (o.accent || []).filter(a => a && a.scene && a.camera);
    let accOn = 0;
    if (acc.length && this._renderAccent(acc, (o.layers || []).filter(L => L && L.scene && L.camera))) accOn = 1;
    // uniforms
    u.tScene.value = src.texture; u.tNear.value = this.rtA.texture; u.tFar.value = this.rtD.texture;
    u.uExposure.value = exposure;
    u.uBloom.value = bl ? (bl.amount || 0) : 0; u.uHal.value = hal;
    u.uMono.value = g.mono ?? 1; u.uSatCap.value = g.satCap ?? 1; u.uContrast.value = g.contrast ?? 1;
    u.uLift.value = g.lift || 0; u.uGain.value = g.gain ?? 1;
    u.uToneS.value.fromArray(g.toneShadow || [1, 1, 1]); u.uToneH.value.fromArray(g.toneHigh || [1, 1, 1]);
    u.uKeepHue.value = g.keepHue ? g.keepHue.h : 0; u.uKeepW.value = g.keepHue ? g.keepHue.w : 0;
    const ht = !g.paper && !g.ink && g.halftone ? g.halftone : null;
    const pitchPx = ht ? Math.max(1, (ht.pitch ?? 4) * H / 1080) : 4;
    // below ~3 output px a round dot cannot form: the screen fades out at preview sizes (the mean tone is unchanged)
    u.uHTAmount.value = ht ? (ht.amount ?? 0.38) * smooth01((pitchPx - 1.6) / 1.6) : 0;
    u.uHTPitch.value = pitchPx;
    const ang = (ht ? ht.angle ?? 45 : 45) * Math.PI / 180; u.uHTRot.value.set(Math.cos(ang), Math.sin(ang));
    u.uGrain.value = g.paper || g.ink ? 0 : (g.grain || 0); u.uSeed.value = (o.seed ?? 0) % 9973;
    u.uVig.value = g.paper || g.ink ? 0 : (g.vignette || 0);
    const w = o.window || { x: 0, y: 0, w: W, h: H };
    u.uWin.value.set(w.x, H - w.y - w.h, w.w, w.h);
    u.uAcc.value = accOn; u.tAcc.value = accOn ? v2.acc.texture : null; u.tAccB.value = accOn ? v2.accB.texture : null; u.uAccBloom.value = 0.85;
    u.uFlash.value = pre ? 0 : (o.flash || 0); u.uFade.value = pre ? 0 : (o.fade || 0); u.uPregrade.value = pre ? 1 : 0;
    const hud = pre ? null : o.hud;
    if (hud) {
      if (!this.hudTex) { this.hudTex = new THREE.DataTexture(new Uint8Array(W * H * 4), W, H); this.hudTex.colorSpace = THREE.NoColorSpace; }
      this.hudTex.image.data = new Uint8Array(hud.pixels().buffer);
      this.hudTex.needsUpdate = true;
      u.tHud.value = this.hudTex; u.uHud.value = 1;
    } else u.uHud.value = 0;
    this._pass(v2.comp, null);
    return { ms: performance.now() - t0 };
  }

  // the accent layers alone: 2x supersampled RGBA8 (no MSAA; an MSAA resolve costs ~160 ms at 720p under SwiftShader),
  // scissored to the screen box their objects cover; then a half-res blurred copy for the 6 px bloom
  _renderAccent(layers, main = []) {
    const v2 = this.v2, r = this.r, W = this.W, H = this.H;
    v2.alloc();
    const box = new THREE.Box3(), v = new THREE.Vector3();
    let x0 = W, y0 = H, x1 = 0, y1 = 0, all = false, any = false;
    for (const L of layers) {
      L.scene.updateMatrixWorld(); L.camera.updateMatrixWorld(); box.setFromObject(L.scene);
      if (box.isEmpty()) continue;
      any = true;
      for (let i = 0; i < 8; i++) {
        v.set(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z);
        v.applyMatrix4(L.camera.matrixWorldInverse);
        if (L.camera.isPerspectiveCamera && v.z > -L.camera.near) { all = true; break; }
        v.applyMatrix4(L.camera.projectionMatrix);
        x0 = Math.min(x0, (v.x + 1) / 2 * W); x1 = Math.max(x1, (v.x + 1) / 2 * W); y0 = Math.min(y0, (v.y + 1) / 2 * H); y1 = Math.max(y1, (v.y + 1) / 2 * H);
      }
    }
    if (!any) return false;
    if (all) { x0 = 0; y0 = 0; x1 = W; y1 = H; }
    const pad = Math.ceil(14 * H / 1080);
    x0 = Math.max(0, Math.floor(x0) - pad); y0 = Math.max(0, Math.floor(y0) - pad); x1 = Math.min(W, Math.ceil(x1) + pad); y1 = Math.min(H, Math.ceil(y1) + pad);
    // clear the whole target once per frame (cheap without MSAA), draw inside the scissor
    const ac = r.autoClear;
    r.setRenderTarget(v2.acc); r.setClearColor(0x000000, 0); r.clear();
    if (x1 > x0 && y1 > y0) {
      v2.acc.scissor.set(x0 * 2, y0 * 2, (x1 - x0) * 2, (y1 - y0) * 2); v2.acc.scissorTest = true;
      r.setRenderTarget(v2.acc);
      r.autoClear = false;
      const occ = layers.some(L => L.occlude) && main.length;
      if (occ) {                                   // the main layers' depth only (no colour) as the occluder
        v2.depthMat ??= new THREE.MeshDepthMaterial({ colorWrite: false });
        for (const M of main) { const prev = M.scene.overrideMaterial, bg = M.scene.background; M.scene.overrideMaterial = v2.depthMat; M.scene.background = null;
          r.render(M.scene, M.camera); M.scene.overrideMaterial = prev; M.scene.background = bg; }
      }
      layers.forEach((L, i) => { if (i && !(occ && L.occlude)) r.clearDepth(); r.render(L.scene, L.camera); });
      r.autoClear = ac; v2.acc.scissorTest = false;
    }
    r.setRenderTarget(null);
    // bloom: half res, two separable passes (~6 px at 1080p)
    v2.copy.uniforms.tSrc.value = v2.acc.texture; this._pass(v2.copy, v2.accA);
    const b = v2.blurA.uniforms, k = 1.7 * H / 1080;
    b.tSrc.value = v2.accA.texture; b.uDir.value.set(k / v2.accA.width, 0); this._pass(v2.blurA, v2.accB);
    b.tSrc.value = v2.accB.texture; b.uDir.value.set(0, k / v2.accB.height); this._pass(v2.blurA, v2.accA);
    [v2.accA, v2.accB] = [v2.accB, v2.accA];        // accB holds the result
    r.setRenderTarget(null);
    return true;
  }
}

function smooth01(x) { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); }
