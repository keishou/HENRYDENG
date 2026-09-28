// Look-dev capture: stills of every look x shot, and render-time measurement.
//   node capture.mjs stills [--looks L0,L1,L2,L3] [--shots wide,medium,close] [--t 0]
//   node capture.mjs timing --workers 1|2 [--frames 12] [--looks ...]
// Stills -> claudepop/out/lookdev/<look>_<shot>.jpg (1920x1080; L0 at 1280x720). Timing -> claudepop/out/lookdev/timing_w<N>.json
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { serve, CHROME, CHROME_ARGS, CLAUDEPOP } from './serve.mjs';

const mode = process.argv[2] || 'stills';
const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i < 0 ? d : process.argv[i + 1]; };
const LOOKS = arg('looks', 'L0,L1,L2,L3').split(','), SHOTS = arg('shots', 'wide,medium,close').split(',');
const OUT = path.join(CLAUDEPOP, 'out/lookdev'); fs.mkdirSync(OUT, { recursive: true });
const size = look => look === 'L0' ? [1280, 720] : [1920, 1080];
const server = await serve();
const url = `http://127.0.0.1:${server.address().port}/film/lookdev/index.html`;

async function openPage() {
  const browser = await chromium.launch({ executablePath: CHROME, args: CHROME_ARGS });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.log('[err]', e.message));
  page.on('console', m => { if (/error|warn/i.test(m.type()) && !/404/.test(m.text())) console.log('[page]', m.text()); });
  await page.goto(url);
  await page.waitForFunction('window.ready === true', null, { timeout: 600000 });
  return { browser, page };
}

if (mode === 'stills') {
  const { browser, page } = await openPage();
  const t = +arg('t', 0);
  for (const look of LOOKS) for (const shot of SHOTS) {
    const [w, h] = size(look);
    const ms = await page.evaluate(p => window.shot(p), { look, shot, t, w, h });
    const b64 = await page.evaluate(() => window.grab(0.93).slice(23));
    fs.writeFileSync(path.join(OUT, `${look}_${shot}.jpg`), Buffer.from(b64, 'base64'));
    console.log(`${look} ${shot} ${w}x${h} ${ms.toFixed(0)} ms (first render includes shader compile)`);
  }
  await browser.close();
} else {
  // timing: each worker renders the same consecutive 24 fps frames of every look x shot, capturing JPEG like the film
  const workers = +arg('workers', 1), frames = +arg('frames', 12);
  const load0 = os.loadavg();
  const results = await Promise.all(Array.from({ length: workers }, async (_, wi) => {
    const { browser, page } = await openPage();
    const res = {};
    for (const look of LOOKS) {
      const [w, h] = size(look);
      for (const shot of SHOTS) await page.evaluate(p => window.shot(p), { look, shot, t: 0, w, h });   // warm-up / compile
      const per = [];
      const tw0 = Date.now();
      for (const shot of SHOTS) for (let f = 0; f < frames; f++) {
        const t0 = Date.now();
        await page.evaluate(p => { window.shot(p); return window.grab(0.92).length; }, { look, shot, t: f / 24, w, h });
        per.push(Date.now() - t0);
      }
      per.sort((a, b) => a - b);
      res[look] = { w, h, frames: per.length, median_ms: per[per.length >> 1], p90_ms: per[Math.floor(per.length * 0.9)], wall_ms: Date.now() - tw0 };
      console.log(`[w${wi}] ${look} ${w}x${h}: median ${res[look].median_ms} ms/frame, p90 ${res[look].p90_ms}`);
    }
    await browser.close();
    return res;
  }));
  const load1 = os.loadavg();
  const out = { date: new Date().toISOString(), workers, frames_per_shot: frames, cpus: os.cpus().length, loadavg_before: load0, loadavg_after: load1, per_worker: results };
  for (const look of LOOKS) {
    const med = results.map(r => r[look].median_ms).sort((a, b) => a - b);
    const wall = Math.max(...results.map(r => r[look].wall_ms)), total = results.reduce((a, r) => a + r[look].frames, 0);
    out[look] = { median_ms_per_frame_per_worker: med[med.length >> 1], effective_ms_per_frame: Math.round(wall / total) };
  }
  fs.writeFileSync(path.join(OUT, `timing_w${workers}.json`), JSON.stringify(out, null, 1));
  console.log(JSON.stringify(Object.fromEntries(LOOKS.map(l => [l, out[l]]))), 'load', load0.map(x => x.toFixed(2)), '->', load1.map(x => x.toFixed(2)));
}
server.close();
