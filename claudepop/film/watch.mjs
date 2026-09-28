// watch.mjs - frames -> a watch-through mp4 with the song (lane A).
//
//   node film/watch.mjs --res 540 [--burn] [--from 38.4 --to 53] [--crf 20] [--preset medium] [--out file.mp4] [--check]
//
// Full film: every frame 0..3759 of out/film/frames/<res>/ + the ORIGINAL pdoom.mp3 stream copied (-c:a copy, never
// re-encoded, no -shortest) -> out/film/watch/watch_<res>_<stamp>.mp4. A segment (--from/--to) re-encodes the audio
// cut to AAC (exact trim; stream-copied MP3 can only cut on 26 ms frames).
// --burn adds a small burn-in (shot id, timecode, frame) via an ASS track (libass). --check runs tools/av_offset.py.
// Warns about shots whose frames are missing or were not completed with the current cache key.
import fs from 'node:fs';
import path from 'node:path';
import { args, shotsDoc, framePath, frameDir, cacheLoad, fromRanges, ffmpeg, run, stamp, PATHS, tc } from './tools/farm.mjs';

const o = args();
const res = +(o.res || 540), doc = shotsDoc(), fps = doc.fps;
const f0 = o.from !== undefined ? Math.round(+o.from * fps) : 0;
const f1 = o.to !== undefined ? Math.min(doc.frames, Math.round(+o.to * fps)) : doc.frames;
const full = f0 === 0 && f1 === doc.frames;
const missing = [];
for (let f = f0; f < f1; f++) if (!fs.existsSync(framePath(res, f))) missing.push(f);
if (missing.length) { console.error(`${missing.length} frames missing in ${frameDir(res)} (first ${missing.slice(0, 10).join(',')}); render them first`); process.exit(1); }
const cache = cacheLoad(res, 'final');
for (const s of doc.shots) {
  if (s.frames[1] <= f0 || s.frames[0] >= f1) continue;
  const e = cache.shots[s.id];
  if (!e || !e.complete) console.warn(`warning: ${s.id} not complete in the cache (${e ? 'partial / errors ' + (e.errors || []).join(' | ') : 'never rendered'})`);
}
fs.mkdirSync(PATHS.watch, { recursive: true });
const out = o.out ? path.resolve(o.out) : path.join(PATHS.watch, `watch_${res}${full ? '' : `_${(f0 / fps).toFixed(1)}-${(f1 / fps).toFixed(1)}`}_${stamp()}.mp4`);
const FF = ffmpeg();
const vf = [];
if (o.burn) {
  const ass = out.replace(/\.mp4$/, '.ass');
  const [W, H] = [Math.round(res * 16 / 9), res], size = Math.max(11, Math.round(res / 48));
  const t = f => { const s = f / fps; const h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60, ss = (s % 60).toFixed(2).padStart(5, '0'); return `${h}:${String(m).padStart(2, '0')}:${ss}`; };
  const lines = [];
  for (let f = f0; f < f1; f++) {
    const s = doc.shots.find(x => f >= x.frames[0] && f < x.frames[1]);
    lines.push(`Dialogue: 0,${t(f - f0)},${t(f - f0 + 1)},B,,0,0,0,,${s.id}  ${tc(f, fps)}  F${String(f).padStart(4, '0')}`);
  }
  fs.writeFileSync(ass, `[Script Info]\nScriptType: v4.00+\nPlayResX: ${W}\nPlayResY: ${H}\nWrapStyle: 2\n\n[V4+ Styles]\n` +
    'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n' +
    `Style: B,DejaVu Sans Mono,${size},&H00F5F9FA,&H00F5F9FA,&H00000000,&H80000000,0,0,0,0,100,100,0,0,3,${Math.max(1, Math.round(size / 5))},0,3,${Math.round(size * 0.8)},${Math.round(size * 0.8)},${Math.round(size * 0.6)},1\n\n` +
    '[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n' + lines.join('\n') + '\n');
  vf.push(`subtitles=${ass.replace(/:/g, '\\:')}`);
}
const argv = ['-y', '-v', 'error', '-framerate', String(fps), '-start_number', String(f0), '-i', path.join(frameDir(res), '%05d.jpg')];
if (full) argv.push('-i', PATHS.mp3);
else argv.push('-ss', (f0 / fps).toFixed(4), '-t', ((f1 - f0) / fps).toFixed(4), '-i', PATHS.mp3);
argv.push('-map', '0:v:0', '-map', '1:a:0', '-frames:v', String(f1 - f0));
if (vf.length) argv.push('-vf', vf.join(','));
argv.push('-c:v', 'libx264', '-preset', o.preset || 'medium', '-crf', String(o.crf || 20), '-pix_fmt', 'yuv420p', '-g', '48');
argv.push(...(full ? ['-c:a', 'copy'] : ['-c:a', 'aac', '-b:a', '192k']), '-movflags', '+faststart', out);
const t0 = Date.now();
await run(FF, argv);
console.log(`${out}  (${(fs.statSync(out).size / 1048576).toFixed(1)} MiB, ${((Date.now() - t0) / 1000).toFixed(1)} s)`);
if (o.check) await run(PATHS.python, [path.join(PATHS.film, 'tools/av_offset.py'), out, ...(full ? [] : ['--start', (f0 / fps).toFixed(4)])]);
