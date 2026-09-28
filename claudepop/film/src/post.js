// post.js - HDR scene -> film finish, for the offline renderer (headless Chromium + SwiftShader, so every pass counts).
//
//   const post = new Post(renderer, W, H, { samples: 4 });
//   post.render(scene, camera, params, t, hud?)     t = film time in seconds (drives grain / dither phase only);
//                                                   hud = a Hud (src/hud.js), composited after the grade
//
// Passes: scene -> half-float target (optional MSAA) -> bright pass at 1/4 -> separable blurs at 1/4 and 1/8
// -> one full-resolution composite. The composite does, in order: chromatic aberration, bloom + halation (a wide,
// red-shifted glow around highlights, as film emulsion scatters light back through the red layer), exposure, filmic
// tone curve (ACES fit), conversion to display sRGB, grade in display space (monochrome mix with split toning, saturation, contrast, lift / gain, tint), vignette,
// HUD overlay (a 2D canvas, drawn after the grade so type stays clean), luminance-dependent grain, an ordered
// halftone / dither screen, scanlines, letterbox bars, and a final 8-bit dither against banding.
// params (all optional): exposure, bloom, bloomThresh, halation, halationTint[3], sat, contrast, lift[3], gain[3],
//   gamma, mono (0..1), toneShadow[3], toneHigh[3], grain, grainSize, vignette, ca, screen, screenPeriod, scanlines,
//   scanPeriod, bars (fraction of height per bar), hudOpacity, fade, flash, clear (hex).
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
}
