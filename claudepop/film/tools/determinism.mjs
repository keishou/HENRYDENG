// determinism.mjs - BIBLE 9.2 / 9.8.4: frames rendered out of order, in parallel or in a fresh browser are identical.
//
//   node film/tools/determinism.mjs --res 540 [--frames 12,1500,3001 | --n 3] [--previs-tags]
//
// For each frame: (a) the stored frame out/film/frames/<res>/<f>.jpg (from render.mjs, rendered in film order),
// (b) a fresh browser rendering the frames in reverse order, (c) the same page re-rendering them after other shots.
// Compares the JPEG bytes (same encoder -> identical bytes iff identical pixels); on a mismatch decodes both in the page
// and reports the max channel difference. The render options must match the stored frames' (e.g. --previs-tags).
import fs from 'node:fs';
import crypto from 'node:crypto';
import { args, serve, openPage, grabFrame, framePath, shotsDoc } from './farm.mjs';

const o = args();
const res = +(o.res || 540), doc = shotsDoc(), q = res >= 1080 ? 0.95 : 0.92;
const opts = { res, layer: 'final', previsTags: !!o['previs-tags'] };
let frames = o.frames ? String(o.frames).split(',').map(Number) : [];
if (!frames.length) { const n = +(o.n || 3); while (frames.length < n) { const f = crypto.randomInt(doc.frames); if (!frames.includes(f)) frames.push(f); } }
const md5 = b => crypto.createHash('md5').update(b).digest('hex');
const server = await serve();
const A = await openPage(server);
const fresh = {};
for (const f of [...frames].reverse()) fresh[f] = (await grabFrame(A.page, f, opts, q)).jpeg;       // fresh browser, reverse order
for (const f of [0, 1800, 3700]) await grabFrame(A.page, f, opts, q);                               // other shots in between
const again = {};
for (const f of frames) again[f] = (await grabFrame(A.page, f, opts, q)).jpeg;
const report = [];
for (const f of frames) {
  const stored = fs.existsSync(framePath(res, f)) ? fs.readFileSync(framePath(res, f)) : null;
  const r = { frame: f, shot: doc.shots.find(s => f >= s.frames[0] && f < s.frames[1]).id, fresh: md5(fresh[f]), same_page_later: md5(again[f]),
    stored: stored ? md5(stored) : null };
  r.identical = r.fresh === r.same_page_later && (!stored || r.fresh === r.stored);
  if (!r.identical) {
    const diff = async (a, b) => A.page.evaluate(async ([a, b]) => {
      const dec = async s => { const i = await createImageBitmap(await (await fetch('data:image/jpeg;base64,' + s)).blob()); const c = new OffscreenCanvas(i.width, i.height).getContext('2d'); c.drawImage(i, 0, 0); return c.getImageData(0, 0, i.width, i.height).data; };
      const x = await dec(a), y = await dec(b); let m = 0, n = 0; for (let i = 0; i < x.length; i++) { const d = Math.abs(x[i] - y[i]); if (d) n++; m = Math.max(m, d); } return { max: m, px: n };
    }, [a.toString('base64'), b.toString('base64')]);
    r.diff_vs_stored = stored ? await diff(fresh[f], stored) : null;
    r.diff_same_page = await diff(fresh[f], again[f]);
  }
  report.push(r);
}
await A.browser.close(); server.close();
console.log(JSON.stringify(report, null, 1));
const ok = report.every(r => r.identical);
console.log(ok ? `determinism: ${frames.length} frames identical (stored in-order render = fresh browser reverse order = same page after other shots)` : 'DETERMINISM FAILED');
process.exitCode = ok ? 0 : 1;
