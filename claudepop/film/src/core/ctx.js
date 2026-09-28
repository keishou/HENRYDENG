// ctx.js - the shared context every scene and set receives (lane A). One per page; its size-dependent parts (post, hud)
// follow the current output resolution.
//
//   ctx.THREE                 the three module (0.180)
//   ctx.renderer              the WebGLRenderer (canvas; preserveDrawingBuffer; outputColorSpace sRGB; no tone mapping:
//                             post.js tone-maps). The core resets its state before every frame (shadowMap off, autoClear,
//                             no clipping); a scene that needs shadows turns them on in its own frame().
//   ctx.W, ctx.H, ctx.res     output size in px (res = H: 540 | 720 | 1080)      ctx.k = W / 1920 (design px -> output px)
//   ctx.design = { W: 1920, H: 1080 }        ctx.fps = 24
//   ctx.post                  src/post.js Post for the current size, 4x MSAA (lane B); ctx.postFor(samples) another count
//   ctx.hud                   src/hud.js Hud for the current size (CPU canvas, 1920x1080 design space)
//   ctx.type                  src/type/type.js Type         ctx.words  src/type/words.js module     ctx.pencil  Pencil
//   ctx.proof                 src/hud/proof.js Proof        ctx.grades src/grade.js GRADES          ctx.grade(name, over)
//   ctx.tl                    Timeline (src/core/timeline.js)      ctx.win   WindowTrack (src/core/window.js)
//   ctx.assets                Assets (src/core/assets.js)          ctx.plates Plates (src/plates/plates.js)
//   ctx.rng                   src/core/rng.js module (hash, hash01, rand, noise1, noise2, fbm1, frozenSeed ...)
//   ctx.palette               BIBLE 4.2 tokens as display-sRGB hex; ctx.color(name) -> THREE.Color (linear, for materials)
//   ctx.sets                  { get(name) -> Promise<api> } plus ctx.sets[name] = api once loaded (scene needs.sets)
//   ctx.avatar                the stand-in (src/avatar.js Avatar) once any scene has needs.avatar, else null. Shared:
//                             re-parent ctx.avatar.root into your scene and set its look in every frame().
//   ctx.frame                 the frame being rendered: { t, f, shot, s, rect (window, design px), layer, previsTags, W, H }
import * as THREE from 'three';
import * as rng from './rng.js';

export const PALETTE = {
  INK: '#0A0A09', DARKROOM: '#0D0E0F', SAFELIGHT: '#3B3A37', NIGHT: '#10151A', STEEL: '#5E6A73', BACKLIGHT: '#DCE3E8',
  PAPER: '#F2EFE8', PAPER_SHADE: '#CFCBC2', FOG: '#9A9690', TYPE: '#FAF9F5', INK_TYPE: '#111110', VOICE: '#D97757', CYANOTYPE: '#1E3F66',
};

export function createCtx({ renderer, assets, tl, win, Post, Hud }) {
  const posts = new Map(), huds = new Map();
  const ctx = {
    THREE, renderer, assets, tl, win, rng, palette: PALETTE,
    design: { W: 1920, H: 1080 }, fps: tl.fps,
    W: 0, H: 0, res: 0, k: 1, hud: null,
    get post() { return ctx.postFor(4); },
    type: null, words: null, pencil: null, proof: null, grades: null, grade: null, plates: null,
    avatar: null, frame: null,
    color: name => new THREE.Color(PALETTE[name] || name),
    setSize(W, H) {
      if (W === ctx.W && H === ctx.H) return;
      ctx.W = W; ctx.H = H; ctx.res = H; ctx.k = W / 1920;
      renderer.setSize(W, H, false);
      const key = `${W}x${H}`;
      if (!huds.has(key)) { const h = new Hud(W, H); h.shadows = false; huds.set(key, h); }
      ctx.hud = huds.get(key);
    },
    // Post for the current size with a given MSAA sample count (frameSpec.msaa; 4 by default, the slate uses 0:
    // a 4x half-float MSAA target alone costs ~56 ms at 540p and ~230 ms at 1080p under SwiftShader)
    postFor(samples = 4) {
      const key = `${ctx.W}x${ctx.H}x${samples}`;
      if (!posts.has(key)) posts.set(key, new Post(renderer, ctx.W, ctx.H, { samples }));
      return posts.get(key);
    },
  };
  const loaded = new Map();
  ctx.sets = {
    get(name) {
      if (!loaded.has(name)) loaded.set(name, (async () => {
        const mod = (await import(`/film/src/sets/${name}.js`)).default;
        const api = await assets.scope('set:' + name, () => mod.init(ctx));
        ctx.sets[name] = api;
        return api;
      })());
      return loaded.get(name);
    },
  };
  return ctx;
}
