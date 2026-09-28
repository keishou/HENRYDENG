// debug helper: node dbg.mjs OUT.jpg 'js expression run before the shot' look shot [t]
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import { serve, CHROME, CHROME_ARGS } from './serve.mjs';
const [out, pre, look, shot, t = '0', w = '1920', h = '1080'] = process.argv.slice(2);
const server = await serve();
const browser = await chromium.launch({ executablePath: CHROME, args: CHROME_ARGS });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.on('pageerror', e => console.log('[err]', e.message));
page.on('console', m => console.log('[page]', m.text()));
await page.goto(`http://127.0.0.1:${server.address().port}/film/lookdev/index.html`);
await page.waitForFunction('window.ready === true', null, { timeout: 600000 });
const res = await page.evaluate(async ([pre, look, shot, t, w, h]) => {
  window.shot({ look, shot, t: +t, w: +w, h: +h });   // build
  const r = await (new Function('return (async () => {' + pre + '})()'))();
  const ms = window.shot({ look, shot, t: +t, w: +w, h: +h });
  return { r, ms, img: window.grab(0.92).slice(23) };
}, [pre, look, shot, t, w, h]);
fs.writeFileSync(out, Buffer.from(res.img, 'base64'));
console.log(JSON.stringify(res.r), res.ms);
await browser.close(); server.close();
