// previs.mjs - stage-2 handover exports of the GEN shots' previs (BIBLE 10.1 step 3; lane A).
//
//   node film/tools/previs.mjs [--shots S02,S05 (default: every GEN shot)] [--res 1080] [--segments] [--safe]
//                              [--layer final|pregrade] [--tags]
//
// first     out/film/previs/<shot>_first.jpg: the first frame of the part the plate will cover (the whole shot, or the
//           tail of S15 from 50.49 / S54 from 151.145), the picture only (renderAt { clean: true }: no type, no HUD,
//           no previs tag) in the film's look, at 1080p: the layout keyframe for the plate's keyframe prompt.
//           Stills plates (S30, S35: gen.duration 0) export their frame the same way.
// segments  (--segments) out/film/previs/<shot>_<plate>_previs.mp4 for the Route B plates (previs-to-plate video):
//           the plate's whole duration, head and tail handles included (plate time 0 = film time tGen - use[0]; S15
//           49.99-54.99, S54 150.645-155.645), rendered with the shot's own scene past its cut (renderAt { shot }),
//           clean, 1080p24, x264 CRF 16 -tune grain, no audio; plus the frames in out/film/previs/<shot>_<plate>/.
// --tags draws the PREVIS tag and the type (a review copy: *_tagged.jpg); --layer pregrade exports the ungraded
// picture (exposure + tone curve only).
import fs from 'node:fs';
import path from 'node:path';
import { args, serve, openPage, grabFrame, writeAtomic, shotsDoc, selectShots, PATHS, pageQuery, ffmpeg, run, tc } from './farm.mjs';

const o = args();
const res = +(o.res || 1080), layer = o.layer || 'final', q = 0.95;
const doc = shotsDoc(), fps = doc.fps;
const shots = (o.shots ? selectShots(doc, o.shots) : doc.shots).filter(s => s.source === 'GEN' || s.gen);
const out = path.join(PATHS.out, 'previs');
fs.mkdirSync(out, { recursive: true });
const server = await serve();
const { browser, page } = await openPage(server, { query: pageQuery({ safe: !!o.safe }) });
const sfx = (o.safe ? '_safe' : '') + (layer === 'final' ? '' : '_' + layer);
// the film time the plate starts covering, and plate time 0 in film time
const span = s => {
  const g = s.gen || {}, use = g.use || [0, s.t1 - s.t0];
  const tGen = s.t1 - (use[1] - use[0]);
  return { tGen, t0: tGen - use[0], t1: tGen - use[0] + (g.duration || 0), use };
};
for (const s of shots) {
  const sp = span(s), f = Math.round(sp.tGen * fps);
  const opts = { res, layer, clean: !o.tags, previsTags: !!o.tags };
  const { jpeg, info } = await grabFrame(page, f, opts, q);
  const file = path.join(out, `${s.id}_first${o.tags ? '_tagged' : ''}${sfx}.jpg`);
  writeAtomic(file, jpeg);
  console.log(`${file}  F${f} ${tc(f)} ${info.shot} [${info.scene}]${info.error ? '  ERROR ' + info.error.split('\n')[0] : ''}`);
  const route = String((s.gen && s.gen.route) || '');
  if (!o.segments || !/^B\b/.test(route) || !(s.gen && s.gen.duration)) continue;
  const plate = s.gen.plate, dir = path.join(out, `${s.id}_${plate}${sfx}`);
  fs.mkdirSync(dir, { recursive: true });
  const fa = Math.round(sp.t0 * fps), fb = Math.round(sp.t1 * fps);
  const t0 = Date.now();
  for (let k = fa; k < fb; k++) {
    const r = await grabFrame(page, k, { ...opts, shot: s.id }, q);
    writeAtomic(path.join(dir, String(k - fa).padStart(5, '0') + '.jpg'), r.jpeg);
  }
  const mp4 = path.join(out, `${s.id}_${plate}_previs${sfx}.mp4`);
  await run(ffmpeg(), ['-y', '-v', 'error', '-framerate', String(fps), '-i', path.join(dir, '%05d.jpg'), '-frames:v', String(fb - fa),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-tune', 'grain', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', mp4]);
  console.log(`${mp4}  film ${sp.t0.toFixed(3)}-${sp.t1.toFixed(3)} s (F${fa}-F${fb - 1}, ${fb - fa} frames; plate use ${sp.use.join('-')} s) ` +
    `${((Date.now() - t0) / 1000).toFixed(0)} s`);
}
await browser.close(); server.close();
