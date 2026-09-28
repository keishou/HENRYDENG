// Throughput test: N independent headless Chromium processes each render F frames of demo.html (JPEG q92 to disk).
//   node run_parallel.mjs --workers=4 --frames=24
import puppeteer from 'puppeteer-core'; import { pathToFileURL } from 'node:url'; import { writeFileSync, mkdirSync } from 'node:fs'; import { join } from 'node:path';
const args = Object.fromEntries(process.argv.slice(2).map(a => { const [k, v] = a.replace(/^--/, '').split('='); return [k, v ?? true]; }));
const N = +(args.workers || 1), F = +(args.frames || 24), OUT = args.out || '/tmp/claude-0/-home-user-HENRYDENG/7f8d1921-66d2-537c-b24c-b53f151ed290/scratchpad/par';
mkdirSync(OUT, { recursive: true });
const FLAGS = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--allow-file-access-from-files', '--no-sandbox', '--disable-accelerated-2d-canvas', '--disable-gpu-compositing', '--window-size=1920,1080'];
const T0 = Date.now();
await Promise.all([...Array(N)].map(async (_, w) => {
  const b = await puppeteer.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true, protocolTimeout: 0, args: FLAGS });
  const p = await b.newPage(); await p.goto(pathToFileURL(process.cwd() + '/demo.html').href); await p.waitForFunction('window.demoReady === true', { timeout: 300000 });
  for (let k = 0; k < F; k++) { const t = 20 + (w * F + k) / 24;
    const u = await p.evaluate(async t => { await window.renderAt(t); return document.getElementById('out').toDataURL('image/jpeg', 0.92); }, t);
    writeFileSync(join(OUT, `f${String(w * F + k).padStart(5, '0')}.jpg`), Buffer.from(u.split(',')[1], 'base64')); }
  await b.close();
}));
const s = (Date.now() - T0) / 1000; console.log(JSON.stringify({ workers: N, frames: N * F, wall_s: s, s_per_frame_effective: +(s / (N * F)).toFixed(3) }));
