// Runs bench.html in headless Chromium under two raster configurations and writes results.json.
//   node run_bench.mjs            (both configs)
//   node run_bench.mjs --demo=t   (render demo.html test card at time t to demo_t.png, report ms)
import puppeteer from 'puppeteer-core';
import { writeFileSync, readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const HERE = dirname(fileURLToPath(import.meta.url));
const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const BASE = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--allow-file-access-from-files', '--no-sandbox',
  '--window-size=1920,1080', '--disable-renderer-backgrounding', '--disable-background-timer-throttling', '--no-first-run', '--disable-default-apps'];
const CONFIGS = {
  gpu2d_swiftshader: BASE,
  cpu2d: [...BASE, '--disable-accelerated-2d-canvas', '--disable-gpu-compositing'],
};
const args = Object.fromEntries(process.argv.slice(2).map(a => { const [k, v] = a.replace(/^--/, '').split('='); return [k, v ?? true]; }));

async function withPage(flags, url, fn) {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, protocolTimeout: 0, args: flags });
  try { const page = await browser.newPage(); await page.setViewport({ width: 1920, height: 1080 });
    page.on('console', m => { if (['error', 'warn'].includes(m.type())) console.log('[page]', m.text()); });
    page.on('pageerror', e => console.log('[pageerror]', e.message));
    await page.goto(url, { waitUntil: 'load' }); return await fn(page, browser);
  } finally { await browser.close(); }
}

if (args.demo !== undefined) {
  const cfg = args.config || 'cpu2d';
  const times = String(args.demo === true ? '0' : args.demo).split(',').map(Number);
  await withPage(CONFIGS[cfg], pathToFileURL(join(HERE, 'demo.html')).href, async page => {
    await page.waitForFunction('window.demoReady === true', { timeout: 300000 });
    const setupMs = await page.evaluate(() => window.setupMs);
    console.log(`[${cfg}] demo setup (paper gen + sprite bake + fonts): ${setupMs} ms`);
    for (const t of times) {
      const r = await page.evaluate(async t => { const t0 = performance.now(); const parts = await window.renderAt(t); const t1 = performance.now();
        const url = document.getElementById('out').toDataURL('image/jpeg', 0.92); return { paint: Math.round(t1 - t0), encode: Math.round(performance.now() - t1), parts, url }; }, t);
      const file = join(HERE, `demo_${String(t).replace('.', '_')}.jpg`);
      writeFileSync(file, Buffer.from(r.url.split(',')[1], 'base64'));
      console.log(`[${cfg}] t=${t}: paint ${r.paint} ms, jpeg ${r.encode} ms, parts ${JSON.stringify(r.parts)} -> ${file}`);
    }
  });
  process.exit(0);
}

const results = {};
for (const [name, flags] of Object.entries(CONFIGS)) {
  if (args.config && args.config !== name) continue;
  console.log('== config', name);
  results[name] = await withPage(flags, pathToFileURL(join(HERE, 'bench.html')).href, async page => {
    await page.waitForFunction('window.benchReady === true');
    const r = await page.evaluate(() => window.runBench(3));
    console.log(JSON.stringify(r, null, 1));
    return r;
  });
}
const f = join(HERE, 'results.json');
const prev = existsSync(f) ? JSON.parse(readFileSync(f, 'utf8')) : {};
writeFileSync(f, JSON.stringify({ ...prev, ...results, _date: new Date().toISOString() }, null, 1));
console.log('wrote', f);
