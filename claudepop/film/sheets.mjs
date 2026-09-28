// sheets.mjs - contact sheets for review (lane A). Look at every one with the Read tool (BIBLE 9.8).
//
//   node film/sheets.mjs --res 540 [--shots all | S01,S15]        per shot: t0+1f, every beat_hit, mid, t1-1f
//        -> out/film/sheets/<shot>.jpg   (hit frames outlined; a hit must show its change on its own frame)
//   node film/sheets.mjs --res 540 --cuts                         every cut as a pair (last frame of A | first of B)
//        -> out/film/sheets/cuts_<res>_<n>.jpg                     (the frame-accurate cut check, part 2: by eye)
//   options: --render (always render in the page; default reuses out/film/frames/<res>/ when that shot's cache is
//            valid), --previs-tags, --cols 4, --cell 480, --override S40=/film/src/core/scene_template.js (implies --render)
import fs from 'node:fs';
import path from 'node:path';
import { args, serve, openPage, launch, grabFrame, writeAtomic, shotsDoc, selectShots, framePath, shotHash, cacheLoad,
  cacheValid, fromRanges, PATHS, tc } from './tools/farm.mjs';

const o = args();
const res = +(o.res || 540), cols = +(o.cols || 4), cellW = +(o.cell || 480), cellH = Math.round(cellW * 9 / 16);
const opts = { res, layer: 'final', previsTags: !!o['previs-tags'] };
const q = res >= 1080 ? 0.95 : 0.92;
const doc = shotsDoc();
const SONG = JSON.parse(fs.readFileSync(PATHS.song, 'utf8'));
const server = await serve();
const film = await openPage(server, { query: o.override ? { override: o.override } : {} });
if (o.override) o.render = true;   // never reuse cached frames for an override
const browser = film.browser;
const comp = await browser.newPage({ viewport: { width: 800, height: 600 } });
await comp.goto(`http://127.0.0.1:${server.address().port}/film/tools/compose.html`);
await comp.waitForFunction('window.composeReady === true');
const scenes = await film.page.evaluate(() => window.scenes());
const cache = cacheLoad(res, 'final'), memo = {};
const validShot = {};
const frameOk = f => {
  const s = doc.shots.find(x => f >= x.frames[0] && f < x.frames[1]);
  if (o.render || !s) return false;
  if (!(s.id in validShot)) validShot[s.id] = cacheValid(cache.shots[s.id], shotHash(doc, s, scenes[s.id].needs, { ...opts, q }, memo));
  return validShot[s.id] && fromRanges(cache.shots[s.id].done).includes(f) && fs.existsSync(framePath(res, f));
};
let rendered = 0, reused = 0;
async function frameJpeg(f) {
  if (frameOk(f)) { reused++; return fs.readFileSync(framePath(res, f)); }
  rendered++;
  return (await grabFrame(film.page, f, opts, q)).jpeg;
}
const dataUrl = b => 'data:image/jpeg;base64,' + b.toString('base64');
async function compose(file, spec) {
  const b64 = await comp.evaluate(s => window.compose(s), { cols, cellW, cellH, ...spec });
  writeAtomic(file, Buffer.from(b64, 'base64'));
  console.log(file);
}

fs.mkdirSync(PATHS.sheets, { recursive: true });
if (o.cuts) {
  const pairs = [[null, 0]].concat(doc.shots.slice(1).map(s => [s.frames[0] - 1, s.frames[0]]));
  const per = 16;
  for (let p = 0; p * per < pairs.length; p++) {
    const panels = [];
    for (const [a, b] of pairs.slice(p * per, (p + 1) * per)) {
      const sb = doc.shots.find(s => s.frames[0] === b);
      const sa = a === null ? null : doc.shots.find(s => a >= s.frames[0] && a < s.frames[1]);
      panels.push(a === null ? { src: dataUrl(await frameJpeg(0)), label: 'START', sub: '' } :
        { src: dataUrl(await frameJpeg(a)), label: `${sa.id} last  F${a}`, sub: `${tc(a)}  (${sa.t1.toFixed(3)} s)` });
      panels.push({ src: dataUrl(await frameJpeg(b)), label: `${sb.id} first F${b}`, sub: `${tc(b)}  t0 ${sb.t0.toFixed(3)} · cut on ${sb.anchor || ''}`.slice(0, 44), hot: true });
    }
    await compose(path.join(PATHS.sheets, `cuts_${res}_${p + 1}.jpg`), { title: `CUTS ${p + 1}/${Math.ceil(pairs.length / per)} · ${res}p`,
      sub: 'each pair: last frame of the outgoing shot | first frame of the incoming shot (outlined) = shots.json frames[0]', panels, cellW: 360, cellH: 203, cols: 8 });
  }
} else {
  for (const s of selectShots(doc, o.shots)) {
    const [f0, f1] = s.frames, n = f1 - f0;
    const items = new Map();
    const add = (f, label, hot = false, sub = '') => {
      f = Math.max(f0, Math.min(f1 - 1, f));
      const it = items.get(f) || { f, labels: [], hot: false, subs: [] };
      it.labels.push(label); it.hot ||= hot; if (sub) it.subs.push(sub); items.set(f, it);
    };
    add(n > 1 ? f0 + 1 : f0, 'first+1');
    (s.beat_hits || []).forEach((h, i) => {
      const w = SONG.lines.flatMap(l => l.words).find(w => Math.abs(w.t - h) < 0.03 || (w.parts || []).some(p => Math.abs(p - h) < 0.03));
      add(Math.round(h * doc.fps), `HIT ${i + 1}`, true, `${h.toFixed(3)}${w ? ` “${w.w}”` : ''}`);
    });
    add(Math.floor((f0 + f1 - 1) / 2), 'mid');
    add(f1 - 1, 'last');
    const list = [...items.values()].sort((a, b) => a.f - b.f);
    const panels = [];
    for (const it of list) panels.push({ src: dataUrl(await frameJpeg(it.f)), hot: it.hot,
      label: `F${it.f}  ${tc(it.f)}  ${((it.f / doc.fps) - s.t0 >= 0 ? "+" : "")}${((it.f / doc.fps) - s.t0).toFixed(3)}  ${it.labels.join(' · ')}`, sub: it.subs.join('  ') });
    const src = s.source === 'GEN' ? `GEN ${s.gen && s.gen.plate}` : s.source;
    await compose(path.join(PATHS.sheets, `${s.id}.jpg`), { title: `${s.id} · ${s.title}`,
      sub: `${s.t0.toFixed(3)}-${s.t1.toFixed(3)} s · frames ${f0}-${f1 - 1} (${n}) · ${src} · ${s.look} · window ${s.window} · ${scenes[s.id].file ? 'scene module' : 'slate'} · ${res}p`, panels });
  }
}
console.log(`frames reused ${reused}, rendered ${rendered}`);
await browser.close(); server.close();
