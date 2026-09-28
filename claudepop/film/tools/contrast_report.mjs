// contrast_report.mjs - the contrast-lane report (BIBLE 6.4, 6.6, 9.8.4; lane A): every type block on every frame,
// checked against its legibility target, the phone-safe area and the exit-with-the-cut rule.
//
//   node film/tools/contrast_report.mjs --res 540 [--shots S01,S04 | --from 0 --to 20] [--safe] [--no-render] [--json f]
//
// Source: the blocks renderAt reported when render.mjs made the frames (out/film/frames/<res>[_safe]/_blocks.json), for
// shots whose cache is valid for the current code; any other frame is rendered in the page (no capture) unless
// --no-render. Per block (type.js layout): mode, box, contrast (WCAG ratio of the type colour against the MEAN luma of
// the pre-type frame under the box), luma { mean, std }, ink, band, safe, critical, alpha.
//
// Checks
//   FAIL contrast   a critical block below its target (CARD 3:1; SUBTITLE, THOUGHT, QUESTION, PREMISE, MONO, TITLE,
//                   APPROVAL 4.5:1)
//   WARN bright     the same ratio taken against the bright side of the box (mean + std for light type, mean - std for
//                   INK TYPE; a banded block counts as measured against its band) is below target: the words over the
//                   brightest part of the picture may not hold
//   WARN unmeasured a critical block over the image whose luma was not probed (contrast null)
//   FAIL unsafe     a critical block outside x 72-1848 / y 60-1020 or in a player-overlay zone (BIBLE 6.6)
//   FAIL fade cut   a block still fading (0.25 < alpha < 1) on a shot's last frame and gone on the next: a fade the cut
//                   interrupts (BIBLE 6.2: a card exits with the cut or completes its 4-frame fade)
//   NOTE blocks     frames with more than one critical type block (BIBLE 6.7: one type block per frame; ZH partners and
//                   the non-critical columns do not count)
// Also lists every CARD / THOUGHT whose last frame lies within 4 frames of a cut (the exit-with-the-cut audit).
// Writes out/film/data/contrast_<res>[_safe].json; exit 1 on any FAIL.
import fs from 'node:fs';
import path from 'node:path';
import { args, serve, openPage, shotsDoc, targetFrames, shotHash, pageDeps, cacheLoad, cacheValid, blocksLoad, fromRanges,
  PATHS, pageQuery, writeAtomic, toRanges } from './farm.mjs';

const o = args();
const res = +(o.res || 540), safe = !!o.safe, variant = safe ? 'safe' : '';
const doc = shotsDoc(), fps = doc.fps;
const opts = { res, layer: 'final', previsTags: !!o['previs-tags'], ...(safe ? { safe: true } : {}) };
const q = res >= 1080 ? 0.95 : 0.92;
const target = targetFrames(doc, o);
const TARGET = { CARD: 3, SUBTITLE: 4.5, THOUGHT: 4.5, QUESTION: 4.5, PREMISE: 4.5, MONO: 4.5, TITLE: 4.5, APPROVAL: 4.5, ZH: 4.5 };
const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const lin = v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
const relLum = h => { const [r, g, b] = hex(h).map(v => lin(v / 255)); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const LT = relLum('#FAF9F5'), LI = relLum('#111110');
const ratio = (a, b) => (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);

const server = await serve();
const { browser, page } = await openPage(server, { query: pageQuery(opts) });
const scenes = await page.evaluate(() => window.scenes());
const deps = await pageDeps(page);
const cache = cacheLoad(res, 'final', variant), side = blocksLoad(res, 'final', variant), memo = {};
const frames = new Map();             // f -> blocks
let fromSide = 0, renderedN = 0, missing = 0;
for (const [id, fl] of target) {
  const shot = doc.shots.find(s => s.id === id);
  const hash = shotHash(doc, shot, scenes[id].needs, { ...opts, q }, memo, deps[id] || '');
  const e = cache.shots[id], b = side.shots[id];
  const ok = cacheValid(e, hash) && b && b.hash === hash;
  const rec = new Set(ok ? fromRanges(b.done) : []);
  for (const f of fl) {
    if (rec.has(f)) { frames.set(f, b.frames[f] || []); fromSide++; continue; }
    if (o['no-render']) { missing++; continue; }
    const info = await page.evaluate(async ({ t, opts }) => window.renderAt(t, opts), { t: f / fps, opts: { res, layer: 'final', previsTags: opts.previsTags } });
    frames.set(f, info.blocks || []); renderedN++;
  }
}
await browser.close(); server.close();

const shotOf = f => doc.shots.find(s => f >= s.frames[0] && f < s.frames[1]);
const issues = { contrast: [], bright: [], unmeasured: [], unsafe: [], fadeCut: [], multi: [] };
const perMode = {};
const push = (k, f, b, extra = {}) => issues[k].push({ f, shot: shotOf(f).id, mode: b ? b.mode : null, line: b ? b.line : null, ...extra });
for (const [f, bl] of [...frames].sort((a, b) => a[0] - b[0])) {
  const crit = bl.filter(b => b.critical !== false && b.mode !== 'ZH' && b.mode !== 'NONE' && b.mode !== 'ERROR');
  if (crit.length > 1) push('multi', f, null, { modes: crit.map(b => b.mode + (b.line != null ? ':' + b.line : '')).join(' + ') });
  for (const b of bl) {
    if (b.mode === 'NONE' || b.mode === 'ERROR') continue;
    const tgt = TARGET[b.mode] ?? 4.5, pm = (perMode[b.mode] ??= { n: 0, min: Infinity, minF: null, brightMin: Infinity, brightF: null, banded: 0, ink: 0 });
    pm.n++; if (b.band) pm.banded++; if (b.ink) pm.ink++;
    if (b.contrast != null && b.contrast < pm.min) { pm.min = b.contrast; pm.minF = f; }
    const critical = b.critical !== false;
    if (critical && b.contrast != null && b.contrast < tgt - 1e-6) push('contrast', f, b, { contrast: b.contrast, target: tgt });
    if (critical && b.contrast == null) push('unmeasured', f, b);
    if (b.luma && !b.band) {
      const bg = b.ink ? Math.max(0, b.luma.mean - b.luma.std) : Math.min(1, b.luma.mean + b.luma.std);
      const c = ratio(b.ink ? LI : LT, lin(bg));
      if (c < pm.brightMin) { pm.brightMin = c; pm.brightF = f; }
      if (critical && c < tgt) push('bright', f, b, { bright: +c.toFixed(2), target: tgt, luma: b.luma });
    }
    if (critical && b.safe === false) push('unsafe', f, b, { box: b.box });
  }
  const s = shotOf(f);
  if (f === s.frames[1] - 1) {
    const next = frames.get(f + 1);
    for (const b of bl) {
      if (!(b.alpha > 0.25 && b.alpha < 1)) continue;
      const cont = next && next.some(x => x.mode === b.mode && x.line === b.line);
      if (!cont) push('fadeCut', f, b, { alpha: +b.alpha.toFixed(3) });
    }
  }
}
// the exit-with-the-cut audit: CARD / THOUGHT blocks whose last visible frame is within 4 frames of a cut
const audit = [];
for (const s of doc.shots) {
  const [f0, f1] = s.frames;
  if (!frames.has(f1 - 1)) continue;
  const lastOf = new Map();
  for (let f = Math.max(f0, f1 - 12); f < f1; f++) for (const b of frames.get(f) || []) if (b.mode === 'CARD' || b.mode === 'THOUGHT') {
    const k = b.mode + ':' + b.line; const r = lastOf.get(k) || { mode: b.mode, line: b.line, alphas: [] };
    r.last = f; r.alphas.push([f, +(b.alpha ?? 1).toFixed(2)]); lastOf.set(k, r);
  }
  for (const r of lastOf.values()) {
    const gap = f1 - 1 - r.last;
    if (gap <= 4) {
      const next = frames.get(f1) || [], spans = next.some(x => x.mode === r.mode && x.line === r.line);
      audit.push({ shot: s.id, cut: f1, mode: r.mode, line: r.line, lastFrame: r.last, framesBeforeCut: gap, spansCut: spans,
        exit: spans ? 'spans the cut' : gap === 0 && r.alphas[r.alphas.length - 1][1] >= 0.99 ? 'with the cut' : gap === 0 ? 'fade ends on the last frame' : 'fade completed before the cut',
        alphas: r.alphas.slice(-6) });
    }
  }
}
// compact ranges for the long lists
const group = list => {
  const m = new Map();
  for (const x of list) { const k = `${x.shot}|${x.mode}|${x.line}`; const g = m.get(k) || { shot: x.shot, mode: x.mode, line: x.line, frames: [], worst: x }; g.frames.push(x.f);
    const val = x.contrast ?? x.bright ?? x.alpha ?? 0; if (val < (g.worst.contrast ?? g.worst.bright ?? g.worst.alpha ?? Infinity)) g.worst = x; m.set(k, g); }
  return [...m.values()].map(g => ({ ...g, frames: toRanges(g.frames), n: g.frames.length }));
};
const report = { res, safe, frames: frames.size, fromSidecar: fromSide, rendered: renderedN, missing,
  perMode: Object.fromEntries(Object.entries(perMode).map(([k, v]) => [k, { ...v, min: v.min === Infinity ? null : v.min, brightMin: v.brightMin === Infinity ? null : +v.brightMin.toFixed(2) }])),
  fail: { contrast: group(issues.contrast), unsafe: group(issues.unsafe), fadeCut: issues.fadeCut },
  warn: { bright: group(issues.bright), unmeasured: group(issues.unmeasured) },
  note: { multiBlock: group(issues.multi.map(x => ({ ...x, mode: x.modes }))) },
  exitAudit: audit };
const out = o.json ? path.resolve(o.json) : path.join(PATHS.data, `contrast_${res}${safe ? '_safe' : ''}.json`);
writeAtomic(out, JSON.stringify(report, null, 1));

const nf = Object.values(report.fail).reduce((a, l) => a + l.length, 0);
console.log(`contrast lane ${res}p${safe ? ' safe' : ''}: ${frames.size} frames (${fromSide} from render.mjs, ${renderedN} rendered now${missing ? `, ${missing} missing` : ''})`);
for (const [k, v] of Object.entries(report.perMode)) console.log(`  ${k.padEnd(9)} ${String(v.n).padStart(5)} block-frames  min ${v.min ?? '-'} (F${v.minF ?? '-'})  bright-side min ${v.brightMin ?? '-'} (F${v.brightF ?? '-'})  ink ${v.ink}  banded ${v.banded}`);
const show = (tag, list, fmt) => { if (list.length) { console.log(`${tag} (${list.length})`); for (const x of list.slice(0, 30)) console.log('  ' + fmt(x)); } };
show('FAIL contrast', report.fail.contrast, g => `${g.shot} ${g.mode} L${g.line} frames ${g.frames}: worst ${g.worst.contrast} < ${g.worst.target}`);
show('FAIL unsafe', report.fail.unsafe, g => `${g.shot} ${g.mode} L${g.line} frames ${g.frames} box ${JSON.stringify(g.worst.box)}`);
show('FAIL fade cut', report.fail.fadeCut, x => `${x.shot} F${x.f} ${x.mode} L${x.line} alpha ${x.alpha}`);
show('WARN bright side', report.warn.bright, g => `${g.shot} ${g.mode} L${g.line} frames ${g.frames}: ${g.worst.bright} < ${g.worst.target} (mean ${g.worst.luma.mean}, std ${g.worst.luma.std})`);
show('WARN unmeasured', report.warn.unmeasured, g => `${g.shot} ${g.mode} L${g.line} frames ${g.frames}`);
show('NOTE more than one type block', report.note.multiBlock, g => `${g.shot} ${g.mode} frames ${g.frames}`);
console.log(`exit audit: ${audit.length} CARD/THOUGHT blocks end within 4 frames of a cut`);
for (const a of audit) console.log(`  ${a.shot} -> cut F${a.cut}: ${a.mode} L${a.line} last F${a.lastFrame} (${a.framesBeforeCut} before) ${a.exit}  ${a.alphas.map(x => x[1]).join(' ')}`);
console.log(nf ? `CONTRAST LANE: ${nf} failures -> ${out}` : `contrast lane: no failures -> ${out}`);
process.exitCode = nf ? 1 : 0;
