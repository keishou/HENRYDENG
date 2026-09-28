#!/usr/bin/env node
// Render the autopilot run of ETHER to an mp4 (deterministic, frame-stepped), with the
// generative soundtrack rendered offline from the same event log.
//
//   node tools/render.js out.mp4 [--fps 30] [--max 200] [--chrome /path/to/chrome] [--ffmpeg /path/to/ffmpeg]
//   node tools/render.js --shots dir [--scene 1 --at 6,12,20]   (QA stills)
//
// Needs: playwright (npm i playwright) and an ffmpeg with libx264+aac.
const fs = require('fs'), path = require('path'), http = require('http'), { spawn } = require('child_process');
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--'+k); return i>=0 ? args[i+1] : d; };
const has = k => args.includes('--'+k);
const ROOT = path.resolve(__dirname, '..');
const FPS = +opt('fps', 30), MAX = +opt('max', 300), OUT = args.find(a => !a.startsWith('--') && a.endsWith('.mp4')) || 'ether.mp4';
const CHROME = opt('chrome', process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome');
const FFMPEG = opt('ffmpeg', process.env.FFMPEG_PATH || 'ffmpeg');
const MIME = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.png':'image/png', '.css':'text/css', '.json':'application/json' };

function serve(){ return new Promise(res => { const srv = http.createServer((q, r) => {
  const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
  if(!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()){ r.writeHead(404); r.end(); return; }
  r.writeHead(200, {'Content-Type': MIME[path.extname(p)] || 'application/octet-stream'}); fs.createReadStream(p).pipe(r); });
  srv.listen(0, '127.0.0.1', () => res({ srv, url: `http://127.0.0.1:${srv.address().port}/index.html` })); }); }

function wavHeader(dataLen, sr, ch){ const b = Buffer.alloc(44); b.write('RIFF',0); b.writeUInt32LE(36+dataLen,4); b.write('WAVE',8); b.write('fmt ',12); b.writeUInt32LE(16,16); b.writeUInt16LE(1,20); b.writeUInt16LE(ch,22);
  b.writeUInt32LE(sr,24); b.writeUInt32LE(sr*ch*2,28); b.writeUInt16LE(ch*2,32); b.writeUInt16LE(16,34); b.write('data',36); b.writeUInt32LE(dataLen,40); return b; }

(async () => {
  const { chromium } = require('playwright');
  const { srv, url } = await serve();
  const browser = await chromium.launch({ executablePath: fs.existsSync(CHROME) ? CHROME : undefined, headless: true, ignoreHTTPSErrors: true,
    args: ['--ignore-certificate-errors', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-dev-shm-usage', '--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1, ignoreHTTPSErrors: true });
  page.on('console', m => { if(m.type()==='error') console.error('[page]', m.text()); });
  page.on('pageerror', e => console.error('[pageerror]', e.message));
  await page.goto(url + '?render=1&seed=' + (opt('seed','7')), { waitUntil: 'load' });
  await page.evaluate(() => window.ETHER.ready);
  console.error('page ready');

  if (has('shots')) {
    // QA stills. --plan "1:4,10;3:8,20"  (scene:seconds,...)  --dt 0.1
    const dir = opt('shots', 'shots'); fs.mkdirSync(dir, { recursive: true });
    const plan = (opt('plan', null) || `${opt('scene','1')}:${opt('at','6')}`).split(';').map(x => { const [sc, ats] = x.split(':'); return { sc: +sc, ats: ats.split(',').map(Number) }; });
    const DT = +opt('dt', 1/FPS);
    for (const { sc, ats } of plan) {
      await page.evaluate(n => window.ETHER.jump(n), sc); let t = 0;
      for (const at of ats) { while (t < at - 1e-6) { await page.evaluate(dt => window.ETHER.step(dt), DT); t += DT; }
        const data = await page.evaluate(() => window.ETHER.frame(0.92)); fs.writeFileSync(path.join(dir, `s${sc}_${at}.jpg`), Buffer.from(data.split(',')[1], 'base64'));
        console.error('shot', sc, at, await page.evaluate(() => window.ETHER.scene())); } }
    await browser.close(); srv.close(); return;
  }
  if (has('bench')) {
    for (const sc of [0,1,2,3,4,5,6,7,8]) { await page.evaluate(n => { window.ETHER.jump(n); for (let i=0;i<10;i++) window.ETHER.step(1/30); window.ETHER.bench(1); }, sc);
      console.error('scene', sc, await page.evaluate(() => window.ETHER.bench(4))); }
    await browser.close(); srv.close(); return;
  }

  if (has('audio-only')) {
    // Re-run the deterministic logic without drawing, render the soundtrack, and mux it onto an existing video.
    const video = opt('audio-only'); let n = 0, done = false;
    while (!done && n < MAX*FPS) { done = await page.evaluate(dt => { for (let i=0;i<30;i++) window.ETHER.stepLogic(dt); return window.ETHER.done(); }, 1/FPS); n += 30; }
    const nf = await page.evaluate(() => Math.round(window.ETHER.time()*30)/30);
    const duration = +opt('duration', String(nf)); console.error(`logic steps=${n} t=${nf}s; rendering audio for ${duration}s…`);
    const au = await page.evaluate(d => window.ETHER.renderAudio(d), duration + 0.5);
    const pcm = Buffer.concat(au.chunks.map(c => Buffer.from(c, 'base64')));
    const wav = OUT.replace(/\.mp4$/, '.wav'); fs.writeFileSync(wav, Buffer.concat([wavHeader(pcm.length, au.sampleRate, au.channels), pcm]));
    await browser.close(); srv.close();
    const mux = spawn(FFMPEG, ['-y', '-hide_banner', '-loglevel', 'error', '-i', video, '-i', wav, '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], { stdio: 'inherit' });
    await new Promise(res => mux.on('close', res)); fs.unlinkSync(wav); console.error('done ->', OUT); return;
  }

  // ---- full render ----
  const tmpWav = OUT.replace(/\.mp4$/, '.wav');
  const ff = spawn(FFMPEG, ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', 'pipe:0',
    '-c:v', 'libx264', '-preset', opt('preset','medium'), '-crf', opt('crf','20'), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT + '.video.mp4'], { stdio: ['pipe', 'inherit', 'inherit'] });
  const write = buf => new Promise(res => { if (!ff.stdin.write(buf)) ff.stdin.once('drain', res); else res(); });
  let n = 0; const t0 = Date.now(); let done = false;
  while (!done && n < MAX*FPS) {
    const data = await page.evaluate(dt => { window.ETHER.step(dt); return window.ETHER.frame(0.93); }, 1/FPS);
    await write(Buffer.from(data.split(',')[1], 'base64')); n++;
    done = await page.evaluate(() => window.ETHER.done());
    if (n % (FPS*5) === 0) console.error(`t=${(n/FPS).toFixed(0)}s scene=${await page.evaluate(() => window.ETHER.scene())} (${((Date.now()-t0)/1000).toFixed(0)}s wall)`);
  }
  ff.stdin.end(); await new Promise(res => ff.on('close', res));
  const duration = n / FPS; console.error(`frames=${n} duration=${duration.toFixed(2)}s; rendering audio…`);
  const au = await page.evaluate(d => window.ETHER.renderAudio(d), duration + 0.5);
  const pcm = Buffer.concat(au.chunks.map(c => Buffer.from(c, 'base64')));
  fs.writeFileSync(tmpWav, Buffer.concat([wavHeader(pcm.length, au.sampleRate, au.channels), pcm]));
  await browser.close(); srv.close();
  const mux = spawn(FFMPEG, ['-y', '-hide_banner', '-loglevel', 'error', '-i', OUT + '.video.mp4', '-i', tmpWav, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], { stdio: 'inherit' });
  await new Promise(res => mux.on('close', res));
  fs.unlinkSync(OUT + '.video.mp4'); fs.unlinkSync(tmpWav);
  console.error('done ->', OUT);
})().catch(e => { console.error(e); process.exit(1); });
