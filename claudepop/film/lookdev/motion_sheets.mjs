// Skinned contact sheets of every motion clip with the real subject.glb through avatar.js (the film's own code path):
// 6 times per clip x 2 views (3/4 front, side), a 25 cm floor grid, camera following the pelvis horizontally.
//   node motion_sheets.mjs [--only a,b] [--out ../../out/avatar/motion/sheets]
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
import { serve, CHROME, CHROME_ARGS, CLAUDEPOP } from './serve.mjs';

const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i < 0 ? d : process.argv[i + 1]; };
const OUT = path.resolve(arg('out', path.join(CLAUDEPOP, 'out/avatar/motion/sheets')));
const only = new Set((arg('only', '') || '').split(',').filter(Boolean));
const PW = 330, PH = 330;
fs.mkdirSync(OUT, { recursive: true });
const server = await serve();
const browser = await chromium.launch({ executablePath: CHROME, args: CHROME_ARGS });
const page = await browser.newPage({ viewport: { width: 800, height: 800 } });
page.on('pageerror', e => console.log('[err]', e.message));
page.on('console', m => { if (/error|warn/i.test(m.type())) console.log('[page]', m.text()); });
await page.goto(`http://127.0.0.1:${server.address().port}/film/lookdev/index.html`);
await page.waitForFunction('window.ready === true', null, { timeout: 300000 });
const man = JSON.parse(fs.readFileSync(path.join(CLAUDEPOP, 'out/avatar/motion/MANIFEST.json'), 'utf8'));
const sheetPage = await browser.newPage({ viewport: { width: 6 * PW, height: 2 * PH + 40 } });
for (const c of man.clips) {
  if (only.size && !only.has(c.name)) continue;
  const T = c.loop ? 2 * c.seconds : c.seconds;
  const times = Array.from({ length: 6 }, (_, i) => +(i * (T - 1 / 30) / 5).toFixed(3));
  const imgs = [];
  const t0 = Date.now();
  for (const az of [30, 90]) for (const t of times) {
    imgs.push(await page.evaluate(p => window.sheetPanel(p), { clip: c.name, t, az, w: PW, h: PH }));
  }
  const ms = (Date.now() - t0) / imgs.length;
  const cells = imgs.map((d, k) => `<div style="position:relative;width:${PW}px;height:${PH}px"><img src="${d}" width="${PW}" height="${PH}">
    <span style="position:absolute;left:5px;top:3px;color:#ffd24a;font:12px monospace">t=${times[k % 6].toFixed(2)}s ${k < 6 ? 'az30' : 'az90'}</span></div>`).join('');
  const lm = c.checks.lowest_point_m, fs_ = c.checks.foot_slide;
  const title = `${c.name}  |  CMU ${c.source.cmu_id} "${c.source.cmu_title}" ${c.source.segment_s.join('-')}s  |  ${c.seconds}s${c.loop ? ' LOOP (2 cycles shown)' : ''}  |  root path ${c.root_motion.path_m} m  |  floor ${lm.min}..${lm.max} m  |  skate p90 ${fs_.p90_cm} cm`;
  await sheetPage.setContent(`<body style="margin:0;background:#111;width:${6 * PW}px"><div style="color:#eee;font:14px monospace;padding:10px 8px;height:20px">${title}</div><div style="display:flex;flex-wrap:wrap;width:${6 * PW}px">${cells}</div></body>`);
  await sheetPage.screenshot({ path: path.join(OUT, `${c.name}.jpg`), type: 'jpeg', quality: 88, fullPage: true });
  console.log(`${c.name}: ${ms.toFixed(0)} ms/panel`);
}
await browser.close(); server.close();
