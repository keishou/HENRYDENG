// render.mjs - capture the film: window.renderAt(t) -> out/film/frames/<res>/<frame:05d>.jpg (lane A).
//
//   node film/render.mjs --res 540|720|1080 [--shots S01,S15 | --from 0 --to 156.6507 | --frames 12,40-44]
//                        [--jobs 1] [--previs-tags] [--layer final|pregrade|accent] [--safe] [--q 0.92] [--force] [--dry]
//                        [--no-cut-check]
//
// Resumable and cached per shot. A shot's frames are re-rendered only when its key changes: the shot JSON, the global
// shots.json fields, song / lyric / voice data, the code closure of its scene module (or the slate), its sets and the
// shared core, the render options, the shot's dependencies outside its own entry (window.shotDeps: the next shot's text,
// the proof-sheet HUD track over its frames), or the mtime/size of any /out/ file it used (recorded after rendering).
// The cache manifest is out/film/frames/<res>[_safe][_<layer>]/_cache.json: { shots: { id: { hash, done: '0-141',
// assets, complete, ms, errors } } }. Frames are written atomically, so an interrupted run resumes at the next missing
// frame. The type blocks renderAt reports (mode, box, contrast, safe, luma, ...) are kept per frame in _blocks.json next
// to the cache (tools/contrast_report.mjs reads them).
//
// --safe renders the faceSafe variant (ctx.flags.faceSafe, BIBLE 12.1 fallbacks of S12 S37 S50 S51) into
// out/film/frames/<res>_safe/. Only those shots are rendered; every other shot whose main render is valid for the same
// key is hard-linked from out/film/frames/<res>/ (identical by construction), else rendered.
//
// Cut check: after rendering, tools/cut_check.py runs on the cuts into and out of the rendered shots whose neighbouring
// frames exist (the picture must change exactly on shots.json frames[0]); --no-cut-check skips it.
// Timings: out/film/data/timing_<res>[_safe][_<layer>].json (median render / capture ms per shot).
import fs from 'node:fs';
import path from 'node:path';
import { args, serve, openPage, grabFrame, writeAtomic, shotsDoc, targetFrames, framePath, frameDir, shotHash, pageDeps,
  cacheLoad, cacheSave, cacheValid, blocksLoad, blocksSave, stampsOf, toRanges, fromRanges, median, PATHS, tc, faceSafeShots,
  pageQuery, linkFrames, run } from './tools/farm.mjs';

const o = args();
const res = +(o.res || 540), layer = o.layer || 'final', jobs = Math.max(1, +(o.jobs || 1));
const q = +(o.q || (res >= 1080 ? 0.95 : 0.92));
const safe = !!o.safe, variant = safe ? 'safe' : '';
const opts = { res, layer, previsTags: !!o['previs-tags'], ...(safe ? { safe: true } : {}) };
const pageOpts = { res, layer, previsTags: opts.previsTags };
const doc = shotsDoc();
const target = targetFrames(doc, o);
const server = await serve();
const t00 = Date.now();

// worker 0 boots first: the scene registry gives each shot's needs (sets) and the page its outside dependencies
const w0 = await openPage(server, { query: pageQuery(opts) });
const scenes = await w0.page.evaluate(() => window.scenes());
const deps = await pageDeps(w0.page);
const memo = {};
const cache = cacheLoad(res, layer, variant);
const blocks = blocksLoad(res, layer, variant);
const main = safe ? cacheLoad(res, layer, '') : null;        // the film's own render (hard links for unchanged shots)
const queue = [];
let nSkip = 0, nTodo = 0, nLinked = 0;
for (const [id, frames] of target) {
  const shot = doc.shots.find(s => s.id === id);
  const hash = shotHash(doc, shot, scenes[id].needs, { ...opts, q }, memo, deps[id] || '');
  let e = cache.shots[id];
  if (o.force || !cacheValid(e, hash)) e = cache.shots[id] = { hash, frames: shot.frames, done: '', assets: {}, complete: false };
  if (!blocks.shots[id] || blocks.shots[id].hash !== hash) blocks.shots[id] = { hash, done: '', frames: {} };
  const done = new Set(fromRanges(e.done));
  let todo = frames.filter(f => !done.has(f) || !fs.existsSync(framePath(res, f, layer, variant)));
  // --safe: an unchanged shot whose main render is valid for the same key -> hard links
  if (safe && todo.length && !faceSafeShots(doc).includes(id) && !o.force) {
    const m = main.shots[id], mdone = new Set(fromRanges(m && m.done));
    const ok = cacheValid(m, hash) ? todo.filter(f => mdone.has(f) && fs.existsSync(framePath(res, f, layer))) : [];
    if (ok.length && !o.dry) {
      linkFrames(ok, f => framePath(res, f, layer), f => framePath(res, f, layer, variant));
      for (const f of ok) done.add(f);
      e.done = toRanges([...done]); e.assets = m.assets; e.complete = m.complete; e.errors = m.errors || [];
      const mb = blocksLoad(res, layer, '').shots[id];
      if (mb && mb.hash === hash) blocks.shots[id] = mb;
      nLinked += ok.length; todo = todo.filter(f => !done.has(f));
    }
  }
  nSkip += frames.length - todo.length; nTodo += todo.length;
  if (todo.length) queue.push({ id, shot, todo, e, scene: scenes[id].file ? 'module' : 'slate' });
}
const outDir = frameDir(res, layer, variant);
console.log(`render ${res}p ${layer}${opts.previsTags ? ' +previs-tags' : ''}${safe ? ' +safe' : ''}: ${target.size} shots, ${nTodo} frames to render, ` +
  `${nSkip} cached${nLinked ? ` (${nLinked} linked from the film's render)` : ''} -> ${outDir}`);
if (o.dry) { for (const j of queue) console.log(`  ${j.id} ${j.todo.length} frames (${j.scene})`); await w0.browser.close(); server.close(); process.exit(0); }
fs.mkdirSync(outDir, { recursive: true });

const timingFile = path.join(PATHS.data, `timing_${res}${safe ? '_safe' : ''}${layer === 'final' ? '' : '_' + layer}.json`);
let timing = {}; try { timing = JSON.parse(fs.readFileSync(timingFile, 'utf8')); } catch {}
let saved = Date.now(), rendered = 0;
const renderedShots = new Set();
const save = () => { cacheSave(res, layer, cache, variant); blocksSave(res, layer, blocks, variant); writeAtomic(timingFile, JSON.stringify(timing, null, 1)); saved = Date.now(); };

async function worker(wi, page) {
  while (queue.length) {
    const job = queue.shift();
    const { id, shot, todo, e } = job;
    const done = new Set(fromRanges(e.done)), rMs = [], tMs = [], errors = new Set();
    const bs = blocks.shots[id], bl = bs.frames, recorded = new Set(fromRanges(bs.done));
    const ts = Date.now();
    for (const f of todo) {
      const a = Date.now();
      const { jpeg, info } = await grabFrame(page, f, pageOpts, q);
      writeAtomic(framePath(res, f, layer, variant), jpeg);
      tMs.push(Date.now() - a); rMs.push(info.ms);
      if (info.blocks && info.blocks.length) bl[f] = info.blocks; else delete bl[f];
      recorded.add(f); bs.done = toRanges([...recorded]);
      if (info.error) errors.add(info.error.split('\n')[0]); else done.add(f);
      rendered++;
      if (Date.now() - saved > 20000) { e.done = toRanges([...done]); save(); }
    }
    renderedShots.add(id);
    e.done = toRanges([...done]);
    e.assets = stampsOf(await page.evaluate(i => window.assetsUsed(i), id));
    e.complete = Array.from({ length: shot.frames[1] - shot.frames[0] }, (_, i) => shot.frames[0] + i).every(f => done.has(f));
    e.errors = [...errors];
    timing[id] = { frames: rMs.length, scene: job.scene, render_ms: median(rMs), total_ms: median(tMs), res, at: new Date().toISOString() };
    save();
    const secs = (Date.now() - ts) / 1000;
    console.log(`[w${wi}] ${id.padEnd(5)} ${String(todo.length).padStart(4)} f  ${tc(todo[0])}-${tc(todo[todo.length - 1])}  ${secs.toFixed(1)} s  ` +
      `render ${median(rMs).toFixed(0)} ms, total ${median(tMs)} ms/f  [${job.scene}]${errors.size ? '  ERRORS: ' + [...errors].join(' | ').slice(0, 300) : ''}`);
  }
}

const pages = [w0.page];
const browsers = [w0.browser];
for (let i = 1; i < jobs; i++) { const w = await openPage(server, { query: pageQuery(opts) }); pages.push(w.page); browsers.push(w.browser); }
await Promise.all(pages.map((p, i) => worker(i, p)));
for (const b of browsers) await b.close();
server.close();
save();
const wall = (Date.now() - t00) / 1000;
console.log(`done: ${rendered} frames in ${wall.toFixed(1)} s (${rendered ? (wall * 1000 / rendered).toFixed(0) : 0} ms/frame wall, ${jobs} job${jobs > 1 ? 's' : ''})`);

// the frame-accurate cut check on the pixels (tools/cut_check.py) for the cuts touching what was rendered. (The old
// check compared each frame's shot id with shots.json, the same lookup the page renders with: it could not fail.)
if (rendered && layer === 'final' && !o['no-cut-check']) {
  try {
    await run(PATHS.python, [path.join(PATHS.film, 'tools/cut_check.py'), outDir, '--shots', [...renderedShots].join(','), '--skip-missing']);
  } catch (e) { console.log('CUT CHECK FAILED (see above)'); process.exitCode = 2; }
}
