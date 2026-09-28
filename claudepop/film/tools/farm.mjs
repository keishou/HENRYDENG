// farm.mjs - node-side plumbing shared by render.mjs, still.mjs, sheets.mjs, watch.mjs and the check tools (lane A).
//
//   import { serve, openPage, args, PATHS, shotsDoc, framePath, ffmpeg, cacheLoad, cacheSave, shotHash, ... } from './tools/farm.mjs'
//
// - serve(root): static server rooted at claudepop/ (so /film/, /out/, /fonts/, /shots.json resolve), with HEAD, a
//   directory listing endpoint (GET /__ls?dir=film/src/scenes -> ["S01.js", ...]) and CORS (fonts for the compose page).
// - openPage({ res, previsTags }): headless Chromium (SwiftShader) on film/index.html, resolved when window.ready.
// - shotHash(): the shot-level cache key = shot JSON + global shots.json fields + song/lyric/voice data + the code closure
//   (static import graph) of the shot's scene module, its sets and the shared core, + render options + the shot's
//   dependencies outside its own entry as the page reports them (window.shotDeps: the next shot's text / window, the
//   proof-sheet HUD track over the shot's frames, whose run starts and sibling captions come from other shots). Asset
//   stamps (mtime + size of every /out/ file the shot used, recorded by the page) are checked separately (cacheValid).
// - variants: --safe renders into out/film/frames/<res>_safe/ (page URL ?safe=1: ctx.flags.faceSafe, the BIBLE 12.1
//   fallbacks). The flag enters the key only of the shots it changes (shots.json flags.faceSafe.shots), so every other
//   shot's safe frames are hard links to the main render's (renderOpts / linkFrames).
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync, spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export const FILM = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const CLAUDEPOP = path.resolve(FILM, '..');
export const PATHS = {
  film: FILM, claudepop: CLAUDEPOP,
  out: path.join(CLAUDEPOP, 'out/film'),
  frames: res => path.join(CLAUDEPOP, 'out/film/frames', String(res)),
  sheets: path.join(CLAUDEPOP, 'out/film/sheets'),
  watch: path.join(CLAUDEPOP, 'out/film/watch'),
  data: path.join(CLAUDEPOP, 'out/film/data'),
  shots: path.join(CLAUDEPOP, 'shots.json'),
  song: path.join(CLAUDEPOP, 'analysis/song.json'),
  mp3: '/home/user/johnheibel/pdoomvideo/assets/pdoom.mp3',
  python: fs.existsSync(path.join(CLAUDEPOP, 'out/venv/bin/python')) ? path.join(CLAUDEPOP, 'out/venv/bin/python') : 'python3',
};
export const CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
export const CHROME_ARGS = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
process.env.PLAYWRIGHT_DISABLE_FORCED_CHROMIUM_PROXIED_LOOPBACK = '1';

// ------------------------------------------------------------------------------------------------ args
export function args(argv = process.argv.slice(2)) {
  const o = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const k = a.slice(2), v = argv[i + 1];
      if (v === undefined || v.startsWith('--')) o[k] = true; else { o[k] = v; i++; }
    } else o._.push(a);
  }
  return o;
}
export const resSize = res => { const h = +res; return [Math.round(h * 16 / 9 / 2) * 2, h]; };

// ------------------------------------------------------------------------------------------------ shots
export function shotsDoc() { return JSON.parse(fs.readFileSync(PATHS.shots, 'utf8')); }
export function selectShots(doc, spec) {
  if (!spec || spec === true || spec === 'all') return doc.shots;
  const want = String(spec).split(',').map(s => s.trim()).filter(Boolean);
  const bad = want.filter(id => !doc.shots.some(s => s.id === id));
  if (bad.length) throw new Error('unknown shot ids: ' + bad.join(','));
  return doc.shots.filter(s => want.includes(s.id));
}
// frames to render: the union of the selected shots' spans, intersected with [from, to) in seconds
export function targetFrames(doc, o) {
  const shots = selectShots(doc, o.shots);
  const f0 = o.from !== undefined ? Math.round(+o.from * doc.fps) : 0;
  const f1 = o.to !== undefined ? Math.round(+o.to * doc.fps) : doc.frames;
  const byShot = new Map();
  for (const s of shots) {
    const a = Math.max(s.frames[0], f0), b = Math.min(s.frames[1], f1);
    if (b > a) byShot.set(s.id, Array.from({ length: b - a }, (_, i) => a + i));
  }
  if (o.frames) {   // explicit list "12,40-44"
    const want = new Set(String(o.frames).split(',').flatMap(r => { const [a, b] = r.split('-').map(Number); return b === undefined ? [a] : Array.from({ length: b - a + 1 }, (_, i) => a + i); }));
    for (const [id, fr] of byShot) { const k = fr.filter(f => want.has(f)); if (k.length) byShot.set(id, k); else byShot.delete(id); }
  }
  return byShot;
}
export const shotOfFrame = (doc, f) => doc.shots.find(s => f >= s.frames[0] && f < s.frames[1]);
// variant: '' (the film) | 'safe' (faceSafe fallbacks); dirs out/film/frames/<res>[_<variant>][_<layer>]
export const frameDir = (res, layer = 'final', variant = '') => PATHS.frames(`${res}${variant ? '_' + variant : ''}${layer === 'final' ? '' : '_' + layer}`);
export const framePath = (res, f, layer = 'final', variant = '') => path.join(frameDir(res, layer, variant), String(f).padStart(5, '0') + '.jpg');
// faceSafe: the shots whose frames change with the flag (shots.json flags.faceSafe.shots)
export const faceSafeShots = doc => ((doc.flags && doc.flags.faceSafe && doc.flags.faceSafe.shots) || []);
// the render options that enter a shot's key: `safe` only for the shots it changes
export function renderOpts(doc, shot, opts) {
  const o = { ...opts }; delete o.safe;
  if (opts.safe && faceSafeShots(doc).includes(shot.id)) o.safe = true;
  return o;
}
// the page's query string for the options (safe=1)
export const pageQuery = (o, extra = {}) => ({ ...(o.safe ? { safe: '1' } : {}), ...extra });
export const tc = (f, fps = 24) => { const s = Math.floor(f / fps); return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}:${String(f % fps).padStart(2, '0')}`; };

// ------------------------------------------------------------------------------------------------ server
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.glb': 'model/gltf-binary', '.bin': 'application/octet-stream', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
  '.ttf': 'font/ttf', '.otf': 'font/otf', '.woff2': 'font/woff2', '.ttc': 'font/collection', '.css': 'text/css', '.mp3': 'audio/mpeg',
  '.wav': 'audio/wav', '.svg': 'image/svg+xml', '.txt': 'text/plain' };
export function serve(root = CLAUDEPOP, port = 0) {
  const server = http.createServer((req, res) => {
    const u = new URL(req.url, 'http://x');
    const cors = { 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'no-store' };
    if (u.pathname === '/__ls') {           // directory listing for scene discovery / plate takes
      const d = path.join(root, u.searchParams.get('dir') || '');
      if (!d.startsWith(root) || !fs.existsSync(d) || !fs.statSync(d).isDirectory()) { res.writeHead(404, cors); res.end('[]'); return; }
      res.writeHead(200, { ...cors, 'Content-Type': 'application/json' });
      res.end(JSON.stringify(fs.readdirSync(d).sort())); return;
    }
    const p = path.join(root, decodeURIComponent(u.pathname));
    if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404, cors); res.end(); return; }
    const st = fs.statSync(p);
    res.writeHead(200, { ...cors, 'Content-Type': TYPES[path.extname(p).toLowerCase()] || 'application/octet-stream', 'Content-Length': st.size });
    if (req.method === 'HEAD') { res.end(); return; }
    fs.createReadStream(p).pipe(res);
  });
  return new Promise(r => server.listen(port, '127.0.0.1', () => r(server)));
}

// ------------------------------------------------------------------------------------------------ browser
let _chromium = null;
async function chromium() { return (_chromium ??= (await import('playwright-core')).chromium); }
export async function launch() { return (await chromium()).launch({ executablePath: CHROME, args: CHROME_ARGS }); }
// open film/index.html; resolves once window.ready (boot done: timeline, fonts, scene registry)
export async function openPage(server, { browser = null, query = {}, log = true } = {}) {
  const b = browser || await launch();
  const page = await b.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('pageerror', e => log && console.log('[pageerror]', e.message));
  page.on('console', m => { const t = m.text(); if (log && /error|warn/i.test(m.type()) && !/404|Failed to load resource/.test(t)) console.log('[page]', t); });
  const q = new URLSearchParams(query).toString();
  await page.goto(`http://127.0.0.1:${server.address().port}/film/index.html${q ? '?' + q : ''}`);
  await page.waitForFunction('window.ready === true || window.bootError', null, { timeout: 600000 });
  const err = await page.evaluate(() => window.bootError || null);
  if (err) throw new Error('boot failed: ' + err);
  return { browser: b, page, own: !browser };
}
// render one frame in the page and return { jpeg: Buffer, info }
export async function grabFrame(page, f, opts = {}, q = 0.92) {
  const r = await page.evaluate(async ({ t, opts, q }) => {
    const info = await window.renderAt(t, opts);
    return { info, b64: window.grab(q) };
  }, { t: f / 24, opts, q });
  return { jpeg: Buffer.from(r.b64, 'base64'), info: r.info };
}
export function writeAtomic(file, buf) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = file + '.tmp' + process.pid;
  fs.writeFileSync(tmp, buf); fs.renameSync(tmp, file);
}

// ------------------------------------------------------------------------------------------------ cache
// The code closure: every module reachable by static imports (and literal dynamic imports) from a root file.
const IMPORT_RES = [/(?:^|[\s;])(?:import|export)\s[^'"`;]*?from\s*['"]([^'"]+)['"]/g, /(?:^|[\s;])import\s*['"]([^'"]+)['"]/g, /import\(\s*['"]([^'"]+)['"]\s*\)/g];
const THREE_VER = (() => { try { return JSON.parse(fs.readFileSync(path.join(FILM, 'node_modules/three/package.json'), 'utf8')).version; } catch { return '?'; } })();
function resolveSpec(spec, fromFile) {
  if (spec === 'three' || spec.startsWith('three/')) return null;          // versioned below
  if (spec.startsWith('/')) return path.join(CLAUDEPOP, spec);
  if (spec.startsWith('.')) return path.resolve(path.dirname(fromFile), spec);
  return null;
}
export function closure(roots, exclude = new Set()) {
  const seen = new Set(), stack = [...roots].filter(f => fs.existsSync(f));
  while (stack.length) {
    const f = stack.pop();
    if (seen.has(f) || exclude.has(f) || !fs.existsSync(f)) continue;
    seen.add(f);
    if (!/\.m?js$/.test(f)) continue;
    const src = fs.readFileSync(f, 'utf8');
    for (const re of IMPORT_RES) for (const m of src.matchAll(re)) { const r = resolveSpec(m[1], f); if (r && !seen.has(r)) stack.push(r); }
  }
  return [...seen].sort();
}
const fileHash = f => crypto.createHash('sha1').update(fs.readFileSync(f)).digest('hex');
const SRC = p => path.join(FILM, 'src', p);
const SLATE = SRC('core/slate.js');
export function coreFiles() {   // shared by every shot (the slate is added only for shots without a scene module)
  return closure([path.join(FILM, 'index.html'), SRC('core/main.js')], new Set([SLATE])).concat(path.join(FILM, 'index.html'));
}
export function sceneFiles(id, needs) {
  const roots = [];
  const mod = SRC(`scenes/${id}.js`);
  if (fs.existsSync(mod)) roots.push(mod); else roots.push(SLATE);
  for (const s of (needs && needs.sets) || []) roots.push(SRC(`sets/${s}.js`));
  return closure(roots);
}
const stable = v => JSON.stringify(v, (k, x) => (x && typeof x === 'object' && !Array.isArray(x)) ? Object.fromEntries(Object.entries(x).sort(([a], [b]) => a < b ? -1 : 1)) : x);
export function globalDataHash(doc) {
  const g = { ...doc }; delete g.shots; delete g.sections;
  const h = crypto.createHash('sha1').update(stable(g));
  for (const f of [PATHS.song, path.join(CLAUDEPOP, 'research/lyric_concepts.json'), path.join(PATHS.data, 'voice_env.json')])
    h.update(fs.existsSync(f) ? fileHash(f) : 'none:' + f);
  return h.digest('hex');
}
// deps: window.shotDeps()[shot.id] from the page (a string; '' when unknown - tools that have no page)
export function shotHash(doc, shot, needs, opts, memo = {}, deps = '') {
  const core = (memo.core ??= coreFiles().map(f => path.relative(CLAUDEPOP, f) + ':' + fileHash(f)).join('\n'));
  const glob = (memo.glob ??= globalDataHash(doc));
  const scene = sceneFiles(shot.id, needs).map(f => path.relative(CLAUDEPOP, f) + ':' + fileHash(f)).join('\n');
  const parts = [stable(shot), glob, core, scene, 'three@' + THREE_VER, stable(renderOpts(doc, shot, opts))];
  if (deps) parts.push('deps:' + crypto.createHash('sha1').update(deps).digest('hex'));
  return crypto.createHash('sha1').update(parts.join('\n#\n')).digest('hex').slice(0, 16);
}
// the page's view of every shot's outside dependencies (see main.js window.shotDeps)
export async function pageDeps(page) { return page.evaluate(() => window.shotDeps ? window.shotDeps() : {}); }
// hard-link (or copy) frames from one frame dir to another (the safe variant reuses the film's unchanged shots)
export function linkFrames(frames, from, to) {
  fs.mkdirSync(path.dirname(to(frames[0] ?? 0)), { recursive: true });
  for (const f of frames) {
    const a = from(f), b = to(f);
    try { fs.unlinkSync(b); } catch {}
    try { fs.linkSync(a, b); } catch { fs.copyFileSync(a, b); }
  }
}
export function assetStamp(url) {
  const f = path.join(CLAUDEPOP, decodeURIComponent(url.replace(/^\//, '').split('?')[0]));
  try { const st = fs.statSync(f); return st.isDirectory() ? `d:${Math.round(st.mtimeMs)}` : `${st.size}:${Math.round(st.mtimeMs)}`; } catch { return 'missing'; }
}
export const stampsOf = urls => Object.fromEntries([...new Set(urls)].sort().map(u => [u, assetStamp(u)]));
export function cacheValid(entry, hash) {
  if (!entry || entry.hash !== hash) return false;
  for (const [u, st] of Object.entries(entry.assets || {})) if (assetStamp(u) !== st) return false;
  return true;
}
export function cachePath(res, layer = 'final', variant = '') { return path.join(frameDir(res, layer, variant), '_cache.json'); }
export function cacheLoad(res, layer, variant = '') { try { return JSON.parse(fs.readFileSync(cachePath(res, layer, variant), 'utf8')); } catch { return { version: 1, shots: {} }; } }
export function cacheSave(res, layer, c, variant = '') { writeAtomic(cachePath(res, layer, variant), JSON.stringify(c, null, 1)); }
// the type blocks renderAt reported per frame (render.mjs; tools/contrast_report.mjs): { shots: { id: { hash, frames: { f: [...] } } } }
export function blocksPath(res, layer = 'final', variant = '') { return path.join(frameDir(res, layer, variant), '_blocks.json'); }
export function blocksLoad(res, layer = 'final', variant = '') { try { return JSON.parse(fs.readFileSync(blocksPath(res, layer, variant), 'utf8')); } catch { return { version: 1, shots: {} }; } }
export function blocksSave(res, layer, b, variant = '') { writeAtomic(blocksPath(res, layer, variant), JSON.stringify(b)); }
// frame lists <-> compact ranges "0-141,150"
export const toRanges = fr => { const s = [...new Set(fr)].sort((a, b) => a - b), out = []; for (let i = 0; i < s.length;) { let j = i; while (j + 1 < s.length && s[j + 1] === s[j] + 1) j++; out.push(i === j ? `${s[i]}` : `${s[i]}-${s[j]}`); i = j + 1; } return out.join(','); };
export const fromRanges = r => !r ? [] : r.split(',').flatMap(x => { const [a, b] = x.split('-').map(Number); return b === undefined ? [a] : Array.from({ length: b - a + 1 }, (_, i) => a + i); });

// ------------------------------------------------------------------------------------------------ ffmpeg
export function ffmpeg() {
  if (process.env.FFMPEG) return process.env.FFMPEG;
  for (const py of [PATHS.python, path.join(CLAUDEPOP, 'out/venv-avatar/bin/python')]) {
    try { return execFileSync(py, ['-c', 'import imageio_ffmpeg as f; print(f.get_ffmpeg_exe())']).toString().trim(); } catch {}
  }
  return 'ffmpeg';
}
export function run(cmd, argv, { quiet = false } = {}) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, argv, { stdio: quiet ? ['ignore', 'pipe', 'pipe'] : 'inherit' });
    let err = '';
    if (quiet) { p.stderr.on('data', d => { err += d; }); p.stdout.on('data', () => {}); }
    p.on('close', code => code === 0 ? resolve() : reject(new Error(`${path.basename(cmd)} exited ${code}\n${err.slice(-2000)}`)));
  });
}
export const stamp = () => new Date().toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15);
export const median = a => { const s = [...a].sort((x, y) => x - y); return s.length ? s[s.length >> 1] : 0; };
