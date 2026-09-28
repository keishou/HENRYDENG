// Close-up joint checks: node detail.mjs OUT.jpg clip:t:bone:az[:span] ...   (panels 480x480, 3 per row)
import { chromium } from 'playwright-core';
import path from 'node:path';
import { serve, CHROME, CHROME_ARGS } from './serve.mjs';
const [out, ...specs] = process.argv.slice(2);
const server = await serve();
const browser = await chromium.launch({ executablePath: CHROME, args: CHROME_ARGS });
const page = await browser.newPage({ viewport: { width: 600, height: 600 } });
page.on('pageerror', e => console.log('[err]', e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/film/lookdev/index.html`);
await page.waitForFunction('window.ready === true', null, { timeout: 300000 });
const P = 480, imgs = [];
for (const s of specs) {
  const [clip, t, bone, az, span, look] = s.split(':');
  imgs.push([s, await page.evaluate(p => window.sheetPanel(p), { clip, t: +t, center: bone, az: +az, el: 8, span: +(span || 0.9), w: P, h: P, look: look || 'photo' })]);
}
const sheet = await browser.newPage({ viewport: { width: 3 * P, height: 400 } });
await sheet.setContent(`<body style="margin:0;background:#111;display:flex;flex-wrap:wrap;width:${3 * P}px">` + imgs.map(([s, d]) =>
  `<div style="position:relative"><img src="${d}" width="${P}" height="${P}" style="display:block"><span style="position:absolute;left:5px;top:3px;color:#ffd24a;font:13px monospace">${s}</span></div>`).join('') + '</body>');
await sheet.screenshot({ path: path.resolve(out), type: 'jpeg', quality: 90, fullPage: true });
await browser.close(); server.close();
