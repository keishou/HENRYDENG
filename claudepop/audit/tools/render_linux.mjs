// render_linux.mjs: Linux / headless-Chromium / no-GPU adaptation of pdoomvideo/render.mjs.
// Lives OUTSIDE the pdoomvideo clone (that repo is read-only for us); points at it via --root.
//
// Changes vs the original render.mjs:
//   * Chrome path defaults to the Playwright Chromium in this sandbox; ANGLE uses SwiftShader (CPU) instead of d3d11.
//   * Google Fonts (Permanent Marker, Shantell Sans 800) are served from ./fonts via request interception, because
//     headless Chromium here has no proxy/CA setup and `networkidle0` + `document.fonts.load` would otherwise hang or
//     silently fall back to Comic Sans. Every other non-file:// request is aborted (fast, deterministic).
//   * By default 2D canvases are CPU-rastered (--disable-accelerated-2d-canvas --disable-gpu-compositing): ~8x faster
//     under SwiftShader (≈16 s vs ≈125 s per 1080p frame) but low-alpha watercolour glows come out slightly weaker.
//     --faithful keeps the GPU(SwiftShader)-rastered 2D canvas path, which matches the author's GPU render more closely.
//   * EXTRA_FLAGS env var appends Chromium flags (used for the perf experiments in REPORT.md).
//   * ffmpeg defaults to the imageio_ffmpeg binary.
//   * --w=<px> downscales stills in-page (e.g. --w=960 → 960x540 PNG); the scene still paints at 1920x1080.
//   * --stills prints ms/frame split into paint vs encode, and writes a JSON timing log next to the frames.
//
//   node render_linux.mjs --root=/home/user/johnheibel/pdoomvideo --stills=3,12,24 --w=960 --out=/path/frames
//   node render_linux.mjs --root=... --sheet=23,23.5,24 --cols=3 --w=640 --out=/path/sheet.jpg
//   node render_linux.mjs --root=... --clip=0:6 --fps=24 --out=/path/clip.mp4
import { createRequire } from 'node:module';
import { spawn, execSync } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { dirname, resolve, join, basename } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const args = Object.fromEntries(process.argv.slice(2).map(a => { const [k, v] = a.replace(/^--/, '').split('='); return [k, v ?? true]; }));
const ROOT = resolve(args.root || '/home/user/johnheibel/pdoomvideo');
const HERE = dirname(fileURLToPath(import.meta.url));
const FONTS = resolve(HERE, '../fonts');
const require = createRequire(join(ROOT, 'package.json'));
const puppeteer = require('puppeteer-core');
const CHROME = args.chrome || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const FFMPEG = args.ffmpeg || execSync('python3 -c "import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())"').toString().trim();
const DUR = 156.6, fps = +(args.fps || 24);
const times = s => String(s).split(',').map(Number);

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: true, protocolTimeout: 0,
  args: ['--allow-file-access-from-files', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', ...(args.faithful ? [] : ['--disable-gpu-compositing', '--disable-accelerated-2d-canvas']),
    ...(process.env.EXTRA_FLAGS ? process.env.EXTRA_FLAGS.split(' ') : []),
    '--window-size=1920,1080', '--disable-renderer-backgrounding', '--disable-background-timer-throttling', '--no-sandbox',
    '--disable-background-networking', '--disable-component-update', '--no-first-run', '--disable-default-apps', '--disable-sync']
});

async function openPage(tag = '') {
  const page = await browser.newPage();
  await page.setRequestInterception(true);
  page.on('request', req => {
    const u = req.url();
    if (u.startsWith('file:') || u.startsWith('data:')) return req.continue();
    if (u.startsWith('https://fonts.googleapis.com/')) {
      const css = readFileSync(join(FONTS, 'fonts.css'), 'utf8');
      return req.respond({ status: 200, contentType: 'text/css', headers: { 'access-control-allow-origin': '*' }, body: css });
    }
    if (u.startsWith('https://fonts.gstatic.com/')) {
      const f = join(FONTS, basename(new URL(u).pathname));
      if (existsSync(f)) return req.respond({ status: 200, contentType: 'font/woff2', headers: { 'access-control-allow-origin': '*' }, body: readFileSync(f) });
    }
    console.log('[blocked]', u); req.abort();
  });
  page.on('console', m => { if (['error', 'warn'].includes(m.type())) console.log(`[page${tag}]`, m.text()); });
  page.on('pageerror', e => console.log(`[page error${tag}]`, e.message));
  await page.goto(pathToFileURL(join(ROOT, 'studio.html')).href + '?render', { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForFunction('window.ready === true', { timeout: 120000 });
  const fontsOk = await page.evaluate(() => document.fonts.check('100px "Permanent Marker"') && document.fonts.check('800 50px "Shantell Sans"'));
  console.log(`page${tag} ready; fonts loaded: ${fontsOk}`);
  return page;
}

// Paint at 1920x1080, optionally downscale in-page to width w, return bytes + timings.
async function frameOf(page, t, type, q, w) {
  const r = await page.evaluate(async (t, type, q, w) => {
    const t0 = performance.now();
    T = t; await redraw(); composite(t);
    const t1 = performance.now();
    let src = document.getElementById('out');
    if (w && w !== src.width) {
      const c = document.createElement('canvas'); c.width = w; c.height = Math.round(w * 9 / 16);
      const x = c.getContext('2d'); x.imageSmoothingEnabled = true; x.imageSmoothingQuality = 'high';
      x.drawImage(src, 0, 0, c.width, c.height); src = c;
    }
    const url = src.toDataURL(type, q);
    return { url, paint: t1 - t0, encode: performance.now() - t1 };
  }, t, type, q, w || 0);
  return { buf: Buffer.from(r.url.slice(r.url.indexOf(',') + 1), 'base64'), paint: r.paint, encode: r.encode };
}

if (args.sheet) {
  const page = await openPage(), out = args.out || 'sheet.jpg'; mkdirSync(dirname(out), { recursive: true });
  const { url, ms } = await page.evaluate((ts, c, w) => window.renderSheet(ts, c, w), times(args.sheet), +(args.cols || 3), +(args.w || 640));
  writeFileSync(out, Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
  console.log(`${out}  ms/frame: ${ms.join(' ')}`);
} else if (args.stills) {
  const out = args.out || 'stills', workers = +(args.workers || 1); mkdirSync(out, { recursive: true });
  const list = times(args.stills), log = [];
  let next = 0;
  await Promise.all(Array.from({ length: workers }, async (_, wk) => {
    const page = await openPage('#' + wk);
    if (wk === 0) console.log('GL renderer:', await page.evaluate(() => window.gpuInfo()));
    // warm-up frame so shader compilation is not billed to the first real still
    await frameOf(page, 0.5, 'image/png', 1, +(args.w || 0));
    while (next < list.length) {
      const s = list[next++], t0 = Date.now();
      const { buf, paint, encode } = await frameOf(page, s, 'image/png', 1, +(args.w || 0));
      const f = `${out}/t${s.toFixed(2).replace('.', '_').padStart(6, '0')}.png`; writeFileSync(f, buf);
      const rec = { t: s, file: f, paint_ms: Math.round(paint), encode_ms: Math.round(encode), wall_ms: Date.now() - t0 };
      log.push(rec); console.log(JSON.stringify(rec));
    }
  }));
  log.sort((a, b) => a.t - b.t);
  writeFileSync(`${out}/timings.json`, JSON.stringify(log, null, 1));
} else if (args.clip) {
  const page = await openPage();
  const [a, b] = String(args.clip).split(':').map(Number);
  const out = args.out || 'clip.mp4'; mkdirSync(dirname(out), { recursive: true });
  const ff = spawn(FFMPEG, ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-ss', String(a), '-t', String(b - a), '-i', join(ROOT, 'assets/pdoom.mp3'),
    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round((b - a) * fps), start = Date.now();
  for (let i = 0; i < n; i++) {
    const { buf } = await frameOf(page, a + i / fps, 'image/jpeg', .92, +(args.w || 0));
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 24 === 0 || i === n - 1) console.log(`frame ${i + 1}/${n}  ${((Date.now() - start) / (i + 1)).toFixed(0)} ms/frame`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log(`wrote ${out}`);
}
await browser.close();
