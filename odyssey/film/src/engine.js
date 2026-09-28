// Renderer, post-processing (grade, bloom, grain, aspect bars) and the text layer.
import * as THREE from 'three';

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const ease = t => (t = clamp(t), t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const easeOut = t => 1 - Math.pow(1 - clamp(t), 3);
export const easeIn = t => Math.pow(clamp(t), 3);
export function rng(seed) {           // mulberry32
  return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
// smooth deterministic "hand-held / helicopter" drift
export function drift(t, seed = 0) {
  const s = (f, p) => Math.sin(t * f + p + seed * 12.9898);
  return new THREE.Vector3(
    s(.31, 0) * .6 + s(.73, 1.3) * .3 + s(1.9, 2.1) * .1,
    s(.27, 4) * .6 + s(.61, .7) * .3 + s(2.3, 5.2) * .1,
    s(.19, 2) * .6 + s(.53, 3.3) * .4);
}

const FS_VERT = /* glsl */`varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }`;

export class Engine {
  constructor(canvas, W, H) {
    this.W = W; this.H = H;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, alpha: false });
    this.renderer.setPixelRatio(1);
    this.renderer.setSize(W, H, false);
    const rt = (w, h, depth) => new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, depthBuffer: depth,
      minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
    this.rtScene = rt(W, H, true);
    this.rtA = rt(W >> 2, H >> 2, false);
    this.rtB = rt(W >> 2, H >> 2, false);
    this.rtC = rt(W >> 3, H >> 3, false);
    this.rtD = rt(W >> 3, H >> 3, false);
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2));
    this.fsScene = new THREE.Scene(); this.fsScene.add(this.quad);
    this.fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    this.brightMat = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false,
      uniforms: { tSrc: { value: null }, uThresh: { value: 1 } },
      fragmentShader: /* glsl */`uniform sampler2D tSrc; uniform float uThresh; varying vec2 vUv;
        void main(){ vec3 c = texture2D(tSrc, vUv).rgb; float l = max(c.r, max(c.g, c.b));
          gl_FragColor = vec4(c * smoothstep(uThresh, uThresh * 1.8 + .2, l), 1.); }` });
    this.blurMat = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false,
      uniforms: { tSrc: { value: null }, uDir: { value: new THREE.Vector2() } },
      fragmentShader: /* glsl */`uniform sampler2D tSrc; uniform vec2 uDir; varying vec2 vUv;
        void main(){ vec3 s = texture2D(tSrc, vUv).rgb * .227;
          s += (texture2D(tSrc, vUv + uDir * 1.385).rgb + texture2D(tSrc, vUv - uDir * 1.385).rgb) * .316;
          s += (texture2D(tSrc, vUv + uDir * 3.231).rgb + texture2D(tSrc, vUv - uDir * 3.231).rgb) * .070;
          gl_FragColor = vec4(s, 1.); }` });

    this.textCanvas = document.createElement('canvas');
    this.textCanvas.width = W; this.textCanvas.height = H;
    this.textCtx = this.textCanvas.getContext('2d');
    this.textTex = new THREE.CanvasTexture(this.textCanvas);
    this.textTex.colorSpace = THREE.NoColorSpace;

    this.postMat = new THREE.ShaderMaterial({ vertexShader: FS_VERT, depthTest: false, depthWrite: false,
      uniforms: {
        tScene: { value: this.rtScene.texture }, tBloom: { value: this.rtA.texture }, tBloom2: { value: this.rtD.texture },
        tText: { value: this.textTex }, uRes: { value: new THREE.Vector2(W, H) }, uTime: { value: 0 },
        uExposure: { value: 1 }, uBloom: { value: .6 }, uSat: { value: 1 }, uContrast: { value: 1 },
        uLift: { value: new THREE.Vector3() }, uGain: { value: new THREE.Vector3(1, 1, 1) }, uBW: { value: 0 },
        uGrain: { value: .06 }, uVig: { value: .35 }, uBars: { value: 0 }, uFlash: { value: 0 }, uFade: { value: 0 },
        uCA: { value: .002 }, uWarp: { value: new THREE.Vector3(.5, .5, 0) }, uTextA: { value: 1 },
        uSplit: { value: new THREE.Vector3(0, 0, 0) } },
      fragmentShader: /* glsl */`
        uniform sampler2D tScene, tBloom, tBloom2, tText; uniform vec2 uRes; uniform float uTime;
        uniform float uExposure, uBloom, uSat, uContrast, uBW, uGrain, uVig, uBars, uFlash, uFade, uCA, uTextA;
        uniform vec3 uLift, uGain, uWarp, uSplit; varying vec2 vUv;
        float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
        vec3 aces(vec3 x){ return clamp((x * (2.51 * x + .03)) / (x * (2.43 * x + .59) + .14), 0., 1.); }
        void main(){
          vec2 uv = vUv;
          // gravitational lensing around a point (the ensō / the void)
          vec2 d = uv - uWarp.xy; d.x *= uRes.x / uRes.y; float r = length(d) + 1e-4;
          vec2 off = d / r * uWarp.z * .012 / (r + .02); off.x *= uRes.y / uRes.x;
          uv -= off;
          vec2 c = uv - .5;
          vec3 col;
          col.r = texture2D(tScene, uv - c * uCA).r;
          col.g = texture2D(tScene, uv).g;
          col.b = texture2D(tScene, uv + c * uCA).b;
          col += (texture2D(tBloom, uv).rgb * .6 + texture2D(tBloom2, uv).rgb * .8) * uBloom;
          col = aces(col * uExposure);
          float l = dot(col, vec3(.2126, .7152, .0722));
          col = mix(vec3(l), col, uSat);
          // split-tone: cool shadows / warm highlights (uSplit = amount, balance)
          col += uSplit.x * (vec3(-.02, .01, .045) * (1. - l) + vec3(.04, .015, -.03) * l);
          col = (col - .5) * uContrast + .5;
          col = col * uGain + uLift * (1. - col);
          col = mix(col, vec3(dot(col, vec3(.299, .587, .114))), uBW);
          col = clamp(col, 0., 1.);
          col = pow(col, vec3(1. / 2.2));
          vec2 q = vUv - .5; q.x *= 1.2;
          col *= 1. - uVig * smoothstep(.12, .75, dot(q, q) * 2.2);
          vec4 tx = texture2D(tText, vUv);
          col = mix(col, tx.rgb, tx.a * uTextA);
          col = mix(col, vec3(1.), uFlash);
          col *= 1. - uFade;
          float g = h12(floor(vUv * uRes * .75) + fract(uTime * 7.31) * 911.) + h12(vUv * uRes + fract(uTime * 3.77) * 517.) - 1.;
          float lum = dot(col, vec3(.333));
          col += g * uGrain * (.55 + .8 * lum * (1. - lum) * 4.) * .5;
          if (vUv.y < uBars || vUv.y > 1. - uBars) col = vec3(0.);
          gl_FragColor = vec4(clamp(col, 0., 1.), 1.);
        }` });
  }

  pass(mat, target) {
    this.quad.material = mat;
    this.renderer.setRenderTarget(target);
    this.renderer.render(this.fsScene, this.fsCam);
  }

  // shot = { scene, camera }, post = partial uniform values
  render(shot, post, T) {
    const r = this.renderer;
    r.setRenderTarget(this.rtScene);
    r.setClearColor(shot.clear ?? 0x000000, 1);
    r.clear();
    if (shot.scene) r.render(shot.scene, shot.camera);
    // bloom: threshold -> 1/4 blur -> 1/8 blur
    this.brightMat.uniforms.tSrc.value = this.rtScene.texture;
    this.brightMat.uniforms.uThresh.value = post.bloomThresh ?? .9;
    this.pass(this.brightMat, this.rtA);
    const b = this.blurMat.uniforms;
    const blur = (src, dst, dx, dy) => { b.tSrc.value = src.texture; b.uDir.value.set(dx / src.width, dy / src.height); this.pass(this.blurMat, dst); };
    blur(this.rtA, this.rtB, 1.2, 0); blur(this.rtB, this.rtA, 0, 1.2);     // 1/4 res result in rtA
    blur(this.rtA, this.rtC, 1.5, 0); blur(this.rtC, this.rtD, 0, 1.5);     // 1/8 res
    blur(this.rtD, this.rtC, 3.0, 0); blur(this.rtC, this.rtD, 0, 3.0);     // 1/8 res result in rtD

    const u = this.postMat.uniforms;
    const def = { exposure: 1, bloom: .6, sat: 1, contrast: 1, lift: [0, 0, 0], gain: [1, 1, 1], bw: 0, grain: .07,
      vig: .35, bars: 0, flash: 0, fade: 0, ca: .0015, warp: [.5, .5, 0], textA: 1, split: 0 };
    const p = Object.assign({}, def, post);
    u.uTime.value = T; u.uExposure.value = p.exposure; u.uBloom.value = p.bloom; u.uSat.value = p.sat;
    u.uContrast.value = p.contrast; u.uLift.value.fromArray(p.lift); u.uGain.value.fromArray(p.gain);
    u.uBW.value = p.bw; u.uGrain.value = p.grain; u.uVig.value = p.vig; u.uBars.value = p.bars;
    u.uFlash.value = p.flash; u.uFade.value = p.fade; u.uCA.value = p.ca; u.uWarp.value.fromArray(p.warp);
    u.uTextA.value = p.textA; u.uSplit.value.set(p.split, 0, 0);
    this.textTex.needsUpdate = true;
    this.pass(this.postMat, null);
  }
}
