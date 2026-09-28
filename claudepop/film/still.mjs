// still.mjs - render single frames (debug). Writes out/film/frames/stills/<frame>_<res>[_<layer>].jpg and prints info.
//   node film/still.mjs --t 12.3 [--res 540] [--layer final|pregrade|accent] [--previs-tags] [--q 0.95] [--out file.jpg]
//   node film/still.mjs --frame 295,296,1271 [--res 1080]
//   node film/still.mjs --shot S15 [--at mid|first|last|<sec from shot start>] [--override S15=/film/src/core/scene_template.js]
import path from 'node:path';
import { args, serve, openPage, grabFrame, writeAtomic, shotsDoc, PATHS, tc } from './tools/farm.mjs';

const o = args();
const doc = shotsDoc();
let frames = [];
if (o.frame !== undefined) frames = String(o.frame).split(',').map(Number);
else if (o.shot) {
  const s = doc.shots.find(x => x.id === o.shot); if (!s) throw new Error('no shot ' + o.shot);
  const at = o.at || 'mid';
  frames = [at === 'first' ? s.frames[0] : at === 'last' ? s.frames[1] - 1 : at === 'mid' ? Math.floor((s.frames[0] + s.frames[1] - 1) / 2) : Math.round((s.t0 + +at) * 24)];
} else frames = [Math.round((+o.t || 0) * 24)];
const res = +(o.res || 540), layer = o.layer || 'final';
const server = await serve();
const { browser, page } = await openPage(server, { query: o.override ? { override: o.override } : {} });
for (const f of frames) {
  const t0 = Date.now();
  const { jpeg, info } = await grabFrame(page, f, { res, layer, previsTags: !!o['previs-tags'] }, +(o.q || 0.95));
  const out = o.out && frames.length === 1 ? path.resolve(o.out) : path.join(PATHS.out, 'frames/stills', `${String(f).padStart(5, '0')}_${res}${layer === 'final' ? '' : '_' + layer}.jpg`);
  writeAtomic(out, jpeg);
  const i = await page.evaluate(t => window.info(t), f / 24);
  console.log(`${out}\n  F${f} ${tc(f)} ${info.shot} [${info.scene}] render ${info.ms} ms, total ${Date.now() - t0} ms${info.error ? '\n  ERROR ' + info.error : ''}`);
  if (o.info) console.log(JSON.stringify({ ...i, blocks: info.blocks, dim: info.dim }, null, 1));
}
await browser.close(); server.close();
