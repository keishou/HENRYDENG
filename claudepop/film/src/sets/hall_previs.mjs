// hall_previs.mjs - lane E node tool: exports the Route B previs segments of the hall's GEN tails for stage 2 (BIBLE
// 10.1 step 3) and their layout keyframes.
//
//   node film/src/sets/hall_previs.mjs [--res 1080] [--only S15|S54] [--layer pregrade|final] [--keep]
//
// -> out/film/previs/S15_P04_previs.mp4 (film 49.99-54.99: the plate's 5 s, whose first 12 frames are the handle
//    before the 50.49 handoff), out/film/previs/S54_P10_previs.mp4 (150.645-155.645), 1080p24, H.264 CRF 14;
//    out/film/previs/S15_first.jpg, S54_first.jpg (the segments' first frames: the keyframe layouts).
// Each frame is the shot module's own frame() at film time t - including the times past the shot's cut, which the
// timeline gives to the next shot - with the previs lighting (globalThis.__HALL_PREVIS: the plate prompt's soft low
// front fill), no text, no HUD, no plate; layer 'pregrade' by default (exposure + tone curve only: no grade, dots,
// grain or window mask - the clean input a video model needs). Frames go to out/film/previs/_frames/<shot>/ (removed
// after encoding unless --keep).
import fs from 'node:fs';
import path from 'node:path';
import { args, serve, openPage, writeAtomic, ffmpeg, run, PATHS } from '../../tools/farm.mjs';

const o = args();
const res = +(o.res || 1080), layer = o.layer || 'pregrade';
const SEGMENTS = [
  { shot: 'S15', plate: 'P04', from: 49.99, to: 54.99, inside: 50.2 },
  { shot: 'S54', plate: 'P10', from: 150.645, to: 155.645, inside: 150.0 },
].filter(s => !o.only || s.shot === o.only);
const OUT = path.join(PATHS.out, 'previs');

const server = await serve();
const { browser, page } = await openPage(server);
for (const seg of SEGMENTS) {
  const f0 = Math.round(seg.from * 24), f1 = Math.round(seg.to * 24), dir = path.join(OUT, '_frames', seg.shot);
  fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  // load and init the module through the core (a frame inside the shot), then drive its frame() directly
  await page.evaluate(async ({ t, res }) => { await window.renderAt(t, { res }); }, { t: seg.inside, res });
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    const b64 = await page.evaluate(async ({ id, f, res, layer }) => {
      const ctx = window.ctx, tl = ctx.tl, shot = tl.shot(id), t = f / 24;
      const mod = (await import(`/film/src/scenes/${id}.js`)).default;
      const H = res, W = Math.round(H * 16 / 9 / 2) * 2;
      ctx.setSize(W, H);
      const r = ctx.renderer;
      r.setRenderTarget(null); r.autoClear = true; r.setClearColor(0x0a0a09, 1); r.shadowMap.enabled = false;
      const n = shot.frames[1] - shot.frames[0];
      const s = { shot, tl: t - shot.t0, u: Math.min(1, Math.max(0, (t - shot.t0) / (shot.t1 - shot.t0))), f, fi: f - shot.frames[0], n, last: false };
      const rect = ctx.win.rect(t, shot);
      ctx.frame = { t, f, shot, s, rect, layer, previsTags: false, W, H };
      globalThis.__HALL_PREVIS = true;
      let spec;
      try { spec = await mod.frame(ctx, t, s); } finally { globalThis.__HALL_PREVIS = false; }
      spec.text = null; spec.hud = null; spec.plate = null;
      if (spec.post) delete spec.post.flash;                     // the capture flash is the film's, not the plate's
      window.finish.render(spec, ctx.frame, { res, layer, previsTags: false });
      const gl = r.getContext(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));
      return window.grab(0.95);
    }, { id: seg.shot, f, res, layer });
    writeAtomic(path.join(dir, String(f - f0).padStart(5, '0') + '.jpg'), Buffer.from(b64, 'base64'));
    if (f === f0) fs.copyFileSync(path.join(dir, '00000.jpg'), path.join(OUT, `${seg.shot}_first.jpg`));
  }
  const mp4 = path.join(OUT, `${seg.shot}_${seg.plate}_previs.mp4`);
  await run(ffmpeg(), ['-y', '-loglevel', 'error', '-framerate', '24', '-i', path.join(dir, '%05d.jpg'), '-c:v', 'libx264', '-preset', 'slow',
    '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4]);
  if (!o.keep) fs.rmSync(dir, { recursive: true, force: true });
  console.log(`${mp4}  ${f1 - f0} frames (${seg.from}-${seg.to} s, film frames ${f0}-${f1 - 1}), ${((Date.now() - t0) / (f1 - f0)).toFixed(0)} ms/frame`);
}
await browser.close(); server.close();
