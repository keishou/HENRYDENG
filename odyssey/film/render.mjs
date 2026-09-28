// Frame-accurate capture to a JPEG sequence (resumable; encode separately with encode.sh).
//   node render.mjs --out <dir> [--w 1920 --h 1080] [--jobs 2] [--from 0 --to 180] [--grain .6] [--force]
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
import { serve } from './serve.mjs';

const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i < 0 ? d : process.argv[i + 1]; };
const OUT = path.resolve(arg('out', 'out/frames'));
const W = +arg('w', 1920), H = +arg('h', 1080), JOBS = +arg('jobs', 2);
const TL = JSON.parse(fs.readFileSync('timeline.json', 'utf8'));
const FPS = TL.fps;
const F0 = Math.round(+arg('from', 0) * FPS), F1 = Math.round(+arg('to', TL.duration) * FPS);
const FORCE = process.argv.includes('--force');
fs.mkdirSync(OUT, { recursive: true });
const file = f => path.join(OUT, `${String(f).padStart(5, '0')}.jpg`);

// work queue of 24-frame chunks, skipping frames already on disk
const queue = [];
for (let f = F0; f < F1; f += 24) {
  const frames = [];
  for (let g = f; g < Math.min(f + 24, F1); g++) if (FORCE || !fs.existsSync(file(g))) frames.push(g);
  if (frames.length) queue.push(frames);
}
const total = queue.reduce((a, c) => a + c.length, 0);
console.log(`${total} frames to render`);

const server = await serve(process.cwd());
const url = `http://127.0.0.1:${server.address().port}/index.html?capture&w=${W}&h=${H}&grain=${arg('grain', .6)}`;
let done = 0; const t0 = Date.now();

async function worker(n) {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', e => console.log(`[w${n} err]`, e.message));
  await page.goto(url);
  await page.waitForFunction('window.ready === true', null, { timeout: 600000 });
  while (queue.length) {
    const frames = queue.shift();
    for (const f of frames) {
      const b64 = await page.evaluate(T => { window.renderAt(T); return document.getElementById('c').toDataURL('image/jpeg', .95).slice(23); }, f / FPS);
      fs.writeFileSync(file(f) + '.tmp', Buffer.from(b64, 'base64'));
      fs.renameSync(file(f) + '.tmp', file(f));
      done++;
    }
    const el = (Date.now() - t0) / 1000;
    console.log(`[w${n}] ${done}/${total}  ${(el / done).toFixed(2)} s/frame  eta ${((total - done) * el / done / 60).toFixed(1)} min`);
  }
  await browser.close();
}
await Promise.all(Array.from({ length: JOBS }, (_, n) => worker(n)));
server.close();
console.log('all frames rendered');
