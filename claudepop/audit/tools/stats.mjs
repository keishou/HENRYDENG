// stats.mjs: instrumented single-worker pass (fast mode) over audit times: ms/frame, draw-call census, on-screen character sizes, shot list → tools/stats.json
// For each time: wall-clock paint cost and a census of drawing calls (watercolour fills, flat washes, ink outlines,
// inkLine strokes, letters), plus the whole shot list (CH) for pacing analysis. Writes tools/stats.json.
//   node stats.mjs [--faithful] [--times=3,12,...]
import { createRequire } from 'node:module';
import { writeFileSync, readFileSync, existsSync } from 'node:fs';
import { dirname, resolve, join, basename } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const args = Object.fromEntries(process.argv.slice(2).map(a => { const [k, v] = a.replace(/^--/, '').split('='); return [k, v ?? true]; }));
const ROOT = '/home/user/johnheibel/pdoomvideo', HERE = dirname(fileURLToPath(import.meta.url)), FONTS = resolve(HERE, '../fonts');
const puppeteer = createRequire(join(ROOT, 'package.json'))('puppeteer-core');
const TIMES = String(args.times || '3,12,24,31,34,44,50,55,61,67,80,88,98,110,126,138').split(',').map(Number);

const browser = await puppeteer.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true, protocolTimeout: 0,
  args: ['--allow-file-access-from-files', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist',
    ...(args.faithful ? [] : ['--disable-gpu-compositing', '--disable-accelerated-2d-canvas']),
    '--window-size=1920,1080', '--no-sandbox', '--disable-background-networking', '--disable-component-update', '--no-first-run']
});
const page = await browser.newPage();
await page.setRequestInterception(true);
page.on('request', req => {
  const u = req.url();
  if (u.startsWith('file:') || u.startsWith('data:')) return req.continue();
  if (u.startsWith('https://fonts.googleapis.com/')) return req.respond({ status: 200, contentType: 'text/css', body: readFileSync(join(FONTS, 'fonts.css'), 'utf8') });
  const f = join(FONTS, basename(new URL(u).pathname));
  if (u.startsWith('https://fonts.gstatic.com/') && existsSync(f)) return req.respond({ status: 200, contentType: 'font/woff2', headers: { 'access-control-allow-origin': '*' }, body: readFileSync(f) });
  req.abort();
});
page.on('pageerror', e => console.log('[page error]', e.message));
await page.goto(pathToFileURL(join(ROOT, 'studio.html')).href + '?render', { waitUntil: 'networkidle0', timeout: 120000 });
await page.waitForFunction('window.ready === true', { timeout: 120000 });

// Wrap the drawing entry points (top-level function declarations live on window, so wrapping rebinds every caller).
await page.evaluate(() => {
  window.__C = {};
  const bump = k => { window.__C[k] = (window.__C[k] || 0) + 1; };
  const P = window.paint;
  window.paint = function (pts, o = {}) {
    bump('paint'); if (o.fill) bump('fill_watercolour'); if (o.wash) bump('wash_flat'); if (o.hatch) bump('hatch');
    if (o.ink !== null) bump('ink_outline'); window.__C.vertices = (window.__C.vertices || 0) + pts.length;
    return P.apply(this, arguments);
  };
  const L = window.inkLine; window.inkLine = function () { bump('inkLine'); return L.apply(this, arguments); };
  const Le = window.letter; window.letter = function () { bump('letter'); return Le.apply(this, arguments); };
  const sc = () => { try { const r = (window.p5 && p5.instance && p5.instance._renderer) || window._renderer; const m = r.states.uModelMatrix.mat4; return Math.hypot(m[0], m[1]); } catch (e) { return NaN; } };
  window.__S = [];
  const C = window.clawd; window.clawd = function (x, y, u, o = {}) { bump('clawd'); window.__S.push(['clawd', 8 * u * sc() / 1080, 10 * u * sc() / 1920]); return C.apply(this, arguments); };
  const R = window.researcher; window.researcher = function (x, y, s) { bump('researcher'); window.__S.push(['researcher', 13.2 * s * sc() / 1080, 0]); return R.apply(this, arguments); };
});
// warm-up
await page.evaluate(async () => { T = 0.5; await redraw(); composite(0.5); document.getElementById('out').toDataURL('image/png'); });
const rows = [];
for (const t of TIMES) {
  const r = await page.evaluate(async t => {
    window.__C = {}; window.__S = []; const t0 = performance.now();
    T = t; await redraw(); composite(t);
    const px = document.getElementById('out').getContext('2d').getImageData(0, 0, 1, 1).data[0]; // force flush
    return { t, ms: Math.round(performance.now() - t0), counts: window.__C, px, sizes: window.__S.map(a => [a[0], Math.round(a[1] * 1000) / 1000, Math.round(a[2] * 1000) / 1000]) };
  }, t);
  delete r.px; rows.push(r); console.log(JSON.stringify(r));
}
const shots = await page.evaluate(() => CH.map(c => ({ name: c.name, start: c.start, end: c.end, shots: c.shots.map(s => [Math.round(s[0] * 1000) / 1000, s[1].name]) })));
writeFileSync(join(HERE, args.out || (args.faithful ? 'stats_faithful.json' : 'stats.json')), JSON.stringify({ mode: args.faithful ? 'faithful (SwiftShader-GPU 2D canvas)' : 'fast (CPU 2D canvas)', rows, shots }, null, 1));
await browser.close();
