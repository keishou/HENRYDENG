// node run_brushbench.mjs : times p5.brush primitives at 1080p in both raster configs; appends to results.json
import puppeteer from 'puppeteer-core';
import { writeFileSync, readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const HERE = dirname(fileURLToPath(import.meta.url));
const BASE = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--allow-file-access-from-files', '--no-sandbox', '--window-size=1920,1080'];
const CONFIGS = { gpu2d_swiftshader: BASE, cpu2d: [...BASE, '--disable-accelerated-2d-canvas', '--disable-gpu-compositing'] };
const res = {};
for (const [name, flags] of Object.entries(CONFIGS)) {
  const b = await puppeteer.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true, protocolTimeout: 0, args: flags });
  const p = await b.newPage(); p.on('pageerror', e => console.log('[pageerror]', e.message)); p.on('console', m => { if (m.type() === 'error') console.log('[page]', m.text()); });
  await p.goto(pathToFileURL(join(HERE, 'brushbench.html')).href); await p.waitForFunction('window.bready === true', { timeout: 120000 });
  res[name] = await p.evaluate(() => window.runBrushBench(2)); console.log(name, JSON.stringify(res[name])); await b.close();
}
const f = join(HERE, 'results.json'); const prev = existsSync(f) ? JSON.parse(readFileSync(f, 'utf8')) : {};
writeFileSync(f, JSON.stringify({ ...prev, p5brush: res }, null, 1));
