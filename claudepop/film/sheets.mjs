// sheets.mjs - contact sheets for review (lane A). Look at every one with the Read tool (BIBLE 9.8).
//
//   node film/sheets.mjs --res 540 [--shots all | S01,S15]        per shot: t0+1f, every beat_hit AND the frame before
//        -> out/film/sheets/<shot>.jpg                             it, mid, t1-1f (hit frames outlined; a hit must show
//                                                                  its change on its own frame, not +-1)
//   node film/sheets.mjs --res 540 --shots S01 --every 4          every 4th frame of the shot from its first, plus its
//        -> out/film/sheets/<shot>_every4[_2 ...].jpg              last; hit frames outlined (48 panels per page)
//   node film/sheets.mjs --res 540 --cuts                         every cut as a pair (last frame of A | first of B)
//        -> out/film/sheets/cuts_<res>_<n>.jpg                     (the frame-accurate cut check by eye)
//   options: --render (always render in the page; default reuses out/film/frames/<res>/ when that shot's cache is
//            valid), --previs-tags, --safe (the faceSafe variant: frames/<res>_safe/, sheets named *_safe), --cols 4,
//            --cell 480, --out-prefix NAME (sheets named NAME_<shot>...), --override S40=/film/src/core/scene_template.js
//            (implies --render)
import fs from 'node:fs';
import path from 'node:path';
import { args, serve, openPage, grabFrame, writeAtomic, shotsDoc, selectShots, framePath, shotHash, cacheLoad, pageDeps,
  cacheValid, fromRanges, PATHS, tc, pageQuery } from './tools/farm.mjs';

const o = args();
const res = +(o.res || 540), cols = +(o.cols || 4), cellW = +(o.cell || 480), cellH = Math.round(cellW * 9 / 16);
const safe = !!o.safe, variant = safe ? 'safe' : '';
const opts = { res, layer: 'final', previsTags: !!o['previs-tags'], ...(safe ? { safe: true } : {}) };
const pageOpts = { res, layer: 'final', previsTags: opts.previsTags };
const q = res >= 1080 ? 0.95 : 0.92;
const doc = shotsDoc();
const SONG = JSON.parse(fs.readFileSync(PATHS.song, 'utf8'));
const server = await serve();
const film = await openPage(server, { query: pageQuery(opts, o.override ? { override: o.override } : {}) });
if (o.override) o.render = true;   // never reuse cached frames for an override
const browser = film.browser;
const comp = await browser.newPage({ viewport: { width: 800, height: 600 } });
await comp.goto(`http://127.0.0.1:${server.address().port}/film/tools/compose.html`);
await comp.waitForFunction('window.composeReady === true');
const scenes = await film.page.evaluate(() => window.scenes());
const deps = o.render ? {} : await pageDeps(film.page);
const cache = cacheLoad(res, 'final', variant), memo = {};
const validShot = {};
const frameOk = f => {
  const s = doc.shots.find(x => f >= x.frames[0] && f < x.frames[1]);
  if (o.render || !s) return false;
  if (!(s.id in validShot)) validShot[s.id] = cacheValid(cache.shots[s.id], shotHash(doc, s, scenes[s.id].needs, { ...opts, q }, memo, deps[s.id] || ''));
  return validShot[s.id] && fromRanges(cache.shots[s.id].done).includes(f) && fs.existsSync(framePath(res, f, 'final', variant));
};
let rendered = 0, reused = 0;
async function frameJpeg(f) {
  if (frameOk(f)) { reused++; return fs.readFileSync(framePath(res, f, 'final', variant)); }
  rendered++;
  return (await grabFrame(film.page, f, pageOpts, q)).jpeg;
}
const dataUrl = b => 'data:image/jpeg;base64,' + b.toString('base64');
async function compose(file, spec) {
  const b64 = await comp.evaluate(s => window.compose(s), { cols, cellW, cellH, ...spec });
  writeAtomic(file, Buffer.from(b64, 'base64'));
  console.log(file);
}
const pre = o['out-prefix'] ? o['out-prefix'] + '_' : '';
const suf = safe ? '_safe' : '';
const hitWord = h => {
  const w = SONG.lines.flatMap(l => l.words).find(w => Math.abs(w.t - h) < 0.03 || (w.parts || []).some(p => Math.abs(p - h) < 0.03));
  return `${h.toFixed(3)}${w ? ` “${w.w}”` : ''}`;
};
const srcTag = s => s.source === 'GEN' ? `GEN ${s.gen && s.gen.plate}` : s.source;
const labelOf = (s, it) => `F${it.f}  ${tc(it.f)}  ${((it.f / doc.fps) - s.t0 >= 0 ? '+' : '')}${((it.f / doc.fps) - s.t0).toFixed(3)}  ${it.labels.join(' · ')}`;

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
    await compose(path.join(PATHS.sheets, `${pre}cuts_${res}${suf}_${p + 1}.jpg`), { title: `CUTS ${p + 1}/${Math.ceil(pairs.length / per)} · ${res}p${safe ? ' · faceSafe' : ''}`,
      sub: 'each pair: last frame of the outgoing shot | first frame of the incoming shot (outlined) = shots.json frames[0]', panels, cellW: 360, cellH: 203, cols: 8 });
  }
} else if (o.every) {
  const N = Math.max(1, +o.every), per = 48, ecols = +(o.cols || 6), ew = +(o.cell || 320), eh = Math.round(ew * 9 / 16);
  for (const s of selectShots(doc, o.shots)) {
    const [f0, f1] = s.frames, hits = new Map((s.beat_hits || []).map((h, i) => [Math.round(h * doc.fps), i]));
    const fs_ = []; for (let f = f0; f < f1; f += N) fs_.push(f);
    if (fs_[fs_.length - 1] !== f1 - 1) fs_.push(f1 - 1);
    const pages = Math.ceil(fs_.length / per);
    for (let p = 0; p < pages; p++) {
      const panels = [];
      for (const f of fs_.slice(p * per, (p + 1) * per)) {
        const hi = hits.get(f), labels = [];
        if (f === f0) labels.push('first'); if (f === f1 - 1) labels.push('last'); if (hi !== undefined) labels.push(`HIT ${hi + 1}`);
        panels.push({ src: dataUrl(await frameJpeg(f)), hot: hi !== undefined, label: labelOf(s, { f, labels }).slice(0, 40), sub: hi !== undefined ? hitWord(s.beat_hits[hi]) : '' });
      }
      await compose(path.join(PATHS.sheets, `${pre}${s.id}_every${N}${suf}${pages > 1 ? '_' + (p + 1) : ''}.jpg`), {
        title: `${s.id} · every ${N} frames${pages > 1 ? ` · ${p + 1}/${pages}` : ''} · ${s.title}`.slice(0, 96),
        sub: `${s.t0.toFixed(3)}-${s.t1.toFixed(3)} s · frames ${f0}-${f1 - 1} (${f1 - f0}) · ${srcTag(s)} · ${s.look} · ${scenes[s.id].file ? 'scene module' : 'slate'} · ${res}p${safe ? ' · faceSafe' : ''} · hits outlined`,
        panels, cols: ecols, cellW: ew, cellH: eh });
    }
  }
} else {
  for (const s of selectShots(doc, o.shots)) {
    const [f0, f1] = s.frames, n = f1 - f0;
    const items = new Map();
    const add = (f, label, hot = false, sub = '') => {
      if (f < f0 || f >= f1) return;
      const it = items.get(f) || { f, labels: [], hot: false, subs: [] };
      it.labels.push(label); it.hot ||= hot; if (sub) it.subs.push(sub); items.set(f, it);
    };
    add(n > 1 ? f0 + 1 : f0, 'first+1');
    (s.beat_hits || []).forEach((h, i) => {
      const hf = Math.round(h * doc.fps);
      add(hf - 1, `before HIT ${i + 1}`);                  // the frame before: the change must not be there yet
      add(hf, `HIT ${i + 1}`, true, hitWord(h));
    });
    add(Math.floor((f0 + f1 - 1) / 2), 'mid');
    add(f1 - 1, 'last');
    const list = [...items.values()].sort((a, b) => a.f - b.f);
    const panels = [];
    for (const it of list) panels.push({ src: dataUrl(await frameJpeg(it.f)), hot: it.hot, label: labelOf(s, it).slice(0, 52), sub: it.subs.join('  ') });
    await compose(path.join(PATHS.sheets, `${pre}${s.id}${suf}.jpg`), { title: `${s.id} · ${s.title}`.slice(0, 80),
      sub: `${s.t0.toFixed(3)}-${s.t1.toFixed(3)} s · frames ${f0}-${f1 - 1} (${n}) · ${srcTag(s)} · ${s.look} · window ${s.window} · ${scenes[s.id].file ? 'scene module' : 'slate'} · ${res}p${safe ? ' · faceSafe' : ''}`,
      panels });
  }
}
console.log(`frames reused ${reused}, rendered ${rendered}`);
await browser.close(); server.close();
