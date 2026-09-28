// Render a contact sheet of stills: node still.mjs out.png 960 540 t1 t2 ...
import { chromium } from 'playwright-core';
import { serve } from './serve.mjs';
import fs from 'node:fs';

const [out, w, h, ...times] = process.argv.slice(2);
const server = await serve(process.cwd());
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: +w, height: +h } });
page.on('console', m => { if (m.type() !== 'log' || /error|warn/i.test(m.text())) console.log('[page]', m.text()); });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/index.html?capture&w=${w}&h=${h}`);
await page.waitForFunction('window.ready === true', null, { timeout: 300000 });
const shots = [];
for (const t of times) {
  const t0 = Date.now();
  const id = await page.evaluate(T => window.renderAt(T), +t);
  const data = await page.evaluate(() => document.getElementById('c').toDataURL('image/jpeg', .9));
  shots.push({ t, id, data, ms: Date.now() - t0 });
  console.log(`t=${t} ${id} ${Date.now() - t0}ms`);
}
const html = `<body style="margin:0;background:#222;display:flex;flex-wrap:wrap;width:${2 * w}px">` +
  shots.map(s => `<div style="position:relative"><img src="${s.data}" width="${w}" height="${h}" style="display:block">
  <span style="position:absolute;left:6px;top:4px;color:#ff0;font:14px monospace">${s.t}s ${s.id}</span></div>`).join('') + '</body>';
const sheet = await browser.newPage({ viewport: { width: 2 * w, height: Math.ceil(shots.length / 2) * h } });
await sheet.setContent(html);
await sheet.screenshot({ path: out, fullPage: true });
await browser.close(); server.close();
