// render.mjs - capture the film: window.renderAt(t) -> out/film/frames/<res>/<frame:05d>.jpg (lane A).
//
//   node film/render.mjs --res 540|720|1080 [--shots S01,S15 | --from 0 --to 156.6507 | --frames 12,40-44]
//                        [--jobs 1] [--previs-tags] [--layer final|pregrade|accent] [--q 0.92] [--force] [--dry]
//
// Resumable and cached per shot. A shot's frames are re-rendered only when its key changes: the shot JSON, the global
// shots.json fields, song / lyric / voice data, the code closure of its scene module (or the slate), its sets and the
// shared core, the render options, or the mtime/size of any /out/ file it used (recorded from the page after rendering).
// The cache manifest is out/film/frames/<res>[_<layer>]/_cache.json: { shots: { id: { hash, done: '0-141', assets,
// complete, ms, errors } } }. Frames are written atomically, so an interrupted run resumes at the next missing frame.
// Every frame's rendered shot id is checked against shots.json (the frame-accurate cut check, part 1).
// Timings: out/film/data/timing_<res>.json (median render / capture ms per shot).
import fs from 'node:fs';
import path from 'node:path';
import { args, serve, launch, openPage, grabFrame, writeAtomic, shotsDoc, targetFrames, framePath, frameDir, shotHash,
  cacheLoad, cacheSave, cacheValid, stampsOf, toRanges, fromRanges, median, PATHS, tc } from './tools/farm.mjs';

const o = args();
const res = +(o.res || 540), layer = o.layer || 'final', jobs = Math.max(1, +(o.jobs || 1));
const q = +(o.q || (res >= 1080 ? 0.95 : 0.92));
const opts = { res, layer, previsTags: !!o['previs-tags'] };
const doc = shotsDoc();
const target = targetFrames(doc, o);
const server = await serve();
const t00 = Date.now();

// worker 0 boots first: the scene registry gives each shot's needs (sets) for the cache key
const w0 = await openPage(server);
const scenes = await w0.page.evaluate(() => window.scenes());
const memo = {};
const cache = cacheLoad(res, layer);
const queue = [];
let nSkip = 0, nTodo = 0;
for (const [id, frames] of target) {
  const shot = doc.shots.find(s => s.id === id);
  const hash = shotHash(doc, shot, scenes[id].needs, { ...opts, q }, memo);
  let e = cache.shots[id];
  if (o.force || !cacheValid(e, hash)) e = cache.shots[id] = { hash, frames: shot.frames, done: '', assets: {}, complete: false };
  const done = new Set(fromRanges(e.done));
  const todo = frames.filter(f => !done.has(f) || !fs.existsSync(framePath(res, f, layer)));
  nSkip += frames.length - todo.length; nTodo += todo.length;
  if (todo.length) queue.push({ id, shot, todo, e, scene: scenes[id].file ? 'module' : 'slate' });
}
console.log(`render ${res}p ${layer}${opts.previsTags ? ' +previs-tags' : ''}: ${target.size} shots, ${nTodo} frames to render, ${nSkip} cached -> ${frameDir(res, layer)}`);
if (o.dry) { for (const j of queue) console.log(`  ${j.id} ${j.todo.length} frames (${j.scene})`); process.exit(0); }
fs.mkdirSync(frameDir(res, layer), { recursive: true });

const timingFile = path.join(PATHS.data, `timing_${res}${layer === 'final' ? '' : '_' + layer}.json`);
let timing = {}; try { timing = JSON.parse(fs.readFileSync(timingFile, 'utf8')); } catch {}
let saved = Date.now(), rendered = 0;
const mismatches = [];
const save = () => { cacheSave(res, layer, cache); writeAtomic(timingFile, JSON.stringify(timing, null, 1)); saved = Date.now(); };

async function worker(wi, page) {
  while (queue.length) {
    const job = queue.shift();
    const { id, shot, todo, e } = job;
    const done = new Set(fromRanges(e.done)), rMs = [], tMs = [], errors = new Set();
    const ts = Date.now();
    for (const f of todo) {
      const a = Date.now();
      const { jpeg, info } = await grabFrame(page, f, opts, q);
      writeAtomic(framePath(res, f, layer), jpeg);
      tMs.push(Date.now() - a); rMs.push(info.ms);
      if (info.shot !== id) mismatches.push({ f, expected: id, got: info.shot });
      if (info.error) errors.add(info.error.split('\n')[0]); else done.add(f);
      rendered++;
      if (Date.now() - saved > 20000) { e.done = toRanges([...done]); save(); }
    }
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
for (let i = 1; i < jobs; i++) { const w = await openPage(server); pages.push(w.page); browsers.push(w.browser); }
await Promise.all(pages.map((p, i) => worker(i, p)));
for (const b of browsers) await b.close();
server.close();
save();
const wall = (Date.now() - t00) / 1000;
console.log(`done: ${rendered} frames in ${wall.toFixed(1)} s (${rendered ? (wall * 1000 / rendered).toFixed(0) : 0} ms/frame wall, ${jobs} job${jobs > 1 ? 's' : ''})`);
if (mismatches.length) { console.log(`CUT CHECK FAILED: ${mismatches.length} frames rendered the wrong shot, e.g. ${JSON.stringify(mismatches.slice(0, 5))}`); process.exitCode = 2; }
else if (rendered) console.log('cut check: every rendered frame belongs to the shot shots.json assigns it');
