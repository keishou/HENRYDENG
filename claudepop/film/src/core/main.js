// main.js - boot, scene registry and the frame entry points of the film page (lane A).
//
// Page API (driven by render.mjs / still.mjs / sheets.mjs through Playwright):
//   window.ready                      true once booted (window.bootError holds a message if boot failed)
//   await window.renderAt(t, opts)    render film time t into the canvas; resolves when the pixels are ready.
//       opts = { res: 540 | 720 | 1080 (output height; width = 16:9), layer: 'final' | 'pregrade' | 'accent',
//                previsTags: false (tag GEN previs 'PREVIS · Pxx') }
//       returns { f, shot, scene: 'module' | 'slate' | 'error', ms, dim, plate, error? , blocks }
//       The shot is chosen by FRAME: f = round(t * 24), shot = the one whose frames [f0, f1) contain f; the scene gets
//       s = { shot, tl: t - shot.t0, u, f, fi, n, last } (tl can be slightly negative on the first frame of a shot).
//   window.grab(q = 0.92) -> base64 JPEG of the canvas (no data: prefix)
//   window.info(t) -> JSON summary of the frame (shot, section, line, word, beat, window, envelope, live, hit)
//   window.scenes() -> { id: { file, needs, error } } for every shot (file null = slate)
//   window.assetsUsed(id) -> [url] the files the shot (its scene, its sets, the core) has used so far
//
// Scenes register by existing: src/scenes/<SHOT_ID>.js with a default export { id, needs, init(ctx), frame(ctx, t, s) }
// (BIBLE 9.3). The core discovers them at boot (GET /__ls from the render server, else a HEAD probe per shot id),
// imports them, and on a shot's first frame preloads needs.sets (ctx.sets[name]), needs.avatar (ctx.avatar),
// needs.plates (ctx.plates.load) and needs.assets (URLs warmed through ctx.assets), then awaits init(ctx) once.
// A module that fails to import or throws renders the slate with the error on it and reports scene: 'error'.
import * as THREE from 'three';
import { Assets } from './assets.js';
import { Timeline } from './timeline.js';
import { WindowTrack } from './window.js';
import { createCtx } from './ctx.js';
import { Finish } from './finish.js';
import { Post } from '../post.js';
import { Hud } from '../hud.js';
import { GRADES, grade } from '../grade.js';
import { Type } from '../type/type.js';
import * as words from '../type/words.js';
import { Pencil } from '../type/pencil.js';
import { Proof } from '../hud/proof.js';
import { Plates } from '../plates/plates.js';

const INK = 0x0a0a09;
const sizeOf = res => { const h = Math.round(+res) || 540; return [Math.round(h * 16 / 9 / 2) * 2, h]; };

async function boot() {
  const canvas = document.getElementById('c');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const assets = new Assets();
  const tl = await Timeline.load(assets);
  const win = new WindowTrack(tl.doc);
  const ctx = createCtx({ renderer, assets, tl, win, Post, Hud });
  await assets.fonts([['IBM Plex Mono', 'IBMPlexMono-Regular.ttf', { weight: '400' }], ['IBM Plex Mono', 'IBMPlexMono-Medium.ttf', { weight: '500' }]]);
  ctx.grades = GRADES; ctx.grade = grade; ctx.words = words;
  ctx.type = new Type(ctx); await ctx.type.init();
  ctx.pencil = new Pencil(ctx); ctx.proof = new Proof(ctx); ctx.plates = new Plates(ctx);
  const finish = new Finish(ctx);
  const slate = (await import('./slate.js')).default;
  await slate.init(ctx);

  // scene registry
  let files = await assets.list('film/src/scenes');
  const ids = tl.shots.map(s => s.id);
  if (!files.length) files = (await Promise.all(ids.map(async id => (await assets.exists(`/film/src/scenes/${id}.js`)) ? `${id}.js` : null))).filter(Boolean);
  // ?override=S40=/film/src/core/scene_template.js : render a shot with another module (debug / A-B; still.mjs and
  // sheets.mjs --override; render.mjs never uses it, so the frame cache always reflects src/scenes/)
  const overrides = Object.fromEntries(new URLSearchParams(location.search).getAll('override').map(x => x.split('=')));
  const registry = {};
  await Promise.all(ids.filter(id => files.includes(`${id}.js`) || overrides[id]).map(async id => {
    const file = overrides[id] || `/film/src/scenes/${id}.js`;
    try {
      const mod = (await import(file)).default;
      if (!mod || typeof mod.frame !== 'function') throw new Error('default export has no frame()');
      if (mod.id && mod.id !== id && !overrides[id]) console.warn(`scene ${file} declares id ${mod.id}`);
      registry[id] = { id, file, mod, needs: mod.needs || {}, ready: null, error: null };
    } catch (e) { registry[id] = { id, file, mod: null, needs: {}, ready: null, error: 'import: ' + (e.message || e) }; }
  }));

  let avatarP = null;
  const loadAvatar = () => (avatarP ??= (async () => {
    const { Avatar } = await import('../avatar.js');
    ctx.avatar = await assets.scope('core', () => Avatar.load({ glb: '/out/avatar/subject.glb', manifest: '/out/avatar/motion/MANIFEST.json' }));
    return ctx.avatar;
  })());
  const ensure = e => (e.ready ??= assets.scope('shot:' + e.id, async () => {
    const n = e.needs;
    for (const name of n.sets || []) await ctx.sets.get(name);
    if (n.avatar) await loadAvatar();
    for (const p of n.plates || []) await ctx.plates.load(p);
    for (const url of n.assets || []) await (/\.(jpe?g|png)$/i.test(url) ? assets.texture(url) : /\.glb$/i.test(url) ? assets.glb(url) : /\.json$/i.test(url) ? assets.json(url) : assets.bin(url));
    if (typeof e.mod.init === 'function') await e.mod.init(ctx);
  }));

  function resetRenderer() {
    renderer.setRenderTarget(null);
    renderer.autoClear = true; renderer.setClearColor(INK, 1);
    renderer.shadowMap.enabled = false; renderer.shadowMap.type = THREE.PCFShadowMap; renderer.shadowMap.autoUpdate = true;
    renderer.toneMapping = THREE.NoToneMapping; renderer.toneMappingExposure = 1;
    renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.localClippingEnabled = false; renderer.clippingPlanes = [];
  }

  window.renderAt = async (t, opts = {}) => {
    const t0 = performance.now();
    const o = { res: 540, layer: 'final', previsTags: false, ...opts };
    const [W, H] = sizeOf(o.res);
    ctx.setSize(W, H);
    const s = tl.frameCtx(t), shot = s.shot;
    let e = registry[shot.id], kind = e ? 'module' : 'slate', error = e && e.error;
    if (e && !error) { try { await ensure(e); } catch (err) { error = e.error = 'init: ' + (err.stack || err.message || err); e.ready = null; } }
    resetRenderer();
    const rect = win.rect(t, shot);
    ctx.frame = { t, f: s.f, shot, s, rect, layer: o.layer, previsTags: !!o.previsTags, W, H };
    let spec;
    if (e && !error) {
      try {
        for (const p of e.needs.plates || []) await ctx.plates.prepare(p, t);
        spec = await assets.scope('shot:' + shot.id, () => e.mod.frame(ctx, t, s));
        if (!spec || typeof spec !== 'object') throw new Error('frame() returned no spec');
      } catch (err) { error = 'frame: ' + (err.stack || err.message || err); }
    }
    if (error) { kind = 'error'; console.error(`[${shot.id}] ${error}`); }
    if (!spec || error) {
      spec = slate.frame(ctx, t, s);
      if (error) { const ov = spec.overlay; spec.overlay = (hud, fr) => { ov(hud, fr); errorLabel(hud.ctx, fr.rect, error); }; }
    }
    const res = finish.render(spec, ctx.frame, o);
    const gl = renderer.getContext(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));   // sync
    return { f: s.f, shot: shot.id, scene: kind, ms: +(performance.now() - t0).toFixed(1), dim: res.dim, plate: res.plate,
      blocks: res.blocks.map(b => ({ mode: b.mode, box: b.box.map(v => Math.round(v)) })), ...(error ? { error: String(error).slice(0, 600) } : {}) };
  };
  window.grab = (q = 0.92) => canvas.toDataURL('image/jpeg', q).slice(23);
  window.info = t => {
    const s = tl.frameCtx(t), shot = s.shot, l = tl.lineAt(t), w = tl.wordAt(t), b = tl.beatAt(t), r = win.rect(t, shot);
    return { t, f: s.f, shot: shot.id, title: shot.title, source: shot.source, module: shot.module, look: shot.look,
      t0: shot.t0, t1: shot.t1, frames: shot.frames, tl: +s.tl.toFixed(4), u: +s.u.toFixed(4), fi: s.fi, n: s.n,
      section: tl.sectionAt(t).name, line: l ? { i: l.i, text: l.text } : null, word: w ? w.w : null,
      bar: b.bar, beat: b.beat, phase: +b.phase.toFixed(3), env: +tl.env(t).toFixed(4), live: tl.live(t),
      hit: tl.hitAt(shot, s.f), window: { x: r.x, w: r.w, shape: r.shape, k: +r.k.toFixed(3) },
      scene: registry[shot.id] ? (registry[shot.id].error ? 'error' : 'module') : 'slate' };
  };
  window.scenes = () => Object.fromEntries(ids.map(id => { const e = registry[id]; return [id, e ? { file: e.file, needs: e.needs, error: e.error } : { file: null, needs: {}, error: null }]; }));
  window.assetsUsed = id => {
    const e = registry[id], urls = new Set([...assets.used('core'), ...assets.used('shot:' + id)]);
    for (const n of (e && e.needs.sets) || []) for (const u of assets.used('set:' + n)) urls.add(u);
    return [...urls].filter(u => u.startsWith('/out/') || u.startsWith('/fonts/')).sort();
  };
  window.ctx = ctx;   // for debugging from still.mjs --eval
  window.ready = true;
}

function errorLabel(c, r, msg) {
  c.save(); c.globalAlpha = 1; c.fillStyle = '#FAF9F5'; c.font = '500 18px "IBM Plex Mono", monospace'; c.textAlign = 'left';
  const lines = String(msg).split('\n').slice(0, 4);
  lines.forEach((l, i) => c.fillText((i ? '  ' : 'SCENE ERROR  ') + l.slice(0, 110), r.x + 40, r.y + r.h / 2 + i * 26));
  c.restore();
}

boot().catch(e => { console.error(e); window.bootError = String(e && (e.stack || e.message) || e); });
