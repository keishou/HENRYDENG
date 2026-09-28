// STUB - owned by lane B, replace. (Frozen on day 0 by lane A: keep the class name, constructor, init and the
// layout() signature and return shape; everything inside is lane B's.)
//
// type.js - presence levels, layout, reveal and the contrast lane (BIBLE 6). This stub draws PLAIN PLACEHOLDER TYPE
// with the right timing and roughly the right place, so the slate animatic already reads; it is not the design.
//
//   const type = new Type(ctx); await type.init()
//   type.layout(text, t, lumaProbe, frame) -> { blocks, dim, draw(hud) }
//     text      frameSpec.text: the shot's text spec array from shots.json (or a scene's override); null / [] = none
//     t         film time (s)
//     lumaProbe (x, y, w, h) -> { mean, std } luma 0..1 of the pre-type frame under a design-px box (the core renders
//               the layers on first call; tone-mapped, pre-grade). Optional to call: it costs a readback.
//     frame     { shot, s, rect (window, design px), register (the grade name), card (full-frame card shot) }
//   returns
//     blocks    [{ mode, box: [x, y, w, h] (design px), on: bool }] what is on screen (for checks and the phone sheet)
//     dim       stops the core dims the image by (the card dim: -1 stop over 4 frames while a CARD is over an image)
//     draw(hud) draws into the Hud canvas (src/hud.js; 1920x1080 design space, already scaled)
import { lineWords, wordState, zhLine, zhReveal, verticalize } from './words.js';

const TYPE = '#FAF9F5', INK_TYPE = '#111110', VOICE = '#D97757';
const F = {
  card: '"Noto Serif Display", "Instrument Serif", Georgia, serif',
  thought: '"Newsreader", "Instrument Serif", Georgia, serif',
  sub: '"Inter Tight", "Helvetica Neue", Arial, sans-serif',
  mono: '"IBM Plex Mono", "DejaVu Sans Mono", monospace',
  zh: '"Noto Sans SC", "Noto Serif SC", "WenQuanYi Zen Hei", sans-serif',
};
const mix = (a, b, k) => { const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)); const A = p(a), B = p(b); return `rgb(${A.map((x, i) => Math.round(x + (B[i] - x) * k)).join(',')})`; };
const clamp01 = x => Math.max(0, Math.min(1, x));

export class Type {
  constructor(ctx) { this.ctx = ctx; this.tl = ctx.tl; this.fps = ctx.tl.fps; }
  async init() {
    await this.ctx.assets.fonts([
      ['Inter Tight', 'InterTight.ttf', { weight: '100 900' }], ['Inter Tight', 'InterTight%5Bwght%5D.ttf', { weight: '100 900' }],
      ['IBM Plex Mono', 'IBMPlexMono-Regular.ttf', { weight: '400' }], ['IBM Plex Mono', 'IBMPlexMono-Medium.ttf', { weight: '500' }],
      ['Instrument Serif', 'InstrumentSerif-Regular.ttf', { style: 'normal' }], ['Instrument Serif', 'InstrumentSerif-Italic.ttf', { style: 'italic' }],
    ]);
  }

  layout(text, t, lumaProbe = null, frame = {}) {
    const tl = this.tl, fps = this.fps, rect = frame.rect || { x: 0, y: 0, w: 1920, h: 1080 };
    const shot = frame.shot || tl.shotAt(t);
    const bright = /STUDIO|WHITE/.test(frame.register || '');
    const ops = [], blocks = [];
    let dim = 0;
    const specs = text || [];
    const none = specs.find(s => s.mode === 'NONE' && (s.from === undefined || t >= s.from) && (s.to === undefined || t < s.to));
    if (none) return { blocks: [{ mode: 'NONE', box: [0, 0, 0, 0], on: true }], dim: 0, draw() {} };
    const left = { x0: 0, x1: rect.x }, right = { x0: rect.x + rect.w, x1: 1920 };
    const margins = rect.x >= 200;
    const f = Math.round(t * fps), shotEnd = shot.t1;
    const lineSpan = i => { const l = tl.line(i); return [l.start - 2 / fps, l.end + 6 / fps]; };

    for (const spec of specs) {
      const ink = spec.ink || bright, col = ink ? INK_TYPE : TYPE;
      const wcol = (w) => { const st = wordState(w, t, fps); return mix(VOICE, col, st.settle); };
      switch (spec.mode) {
        case 'PREMISE': {
          const out = t >= spec.off ? clamp01(1 - (f - Math.round(spec.off * fps) + 1) / 4) : 1;
          if (out <= 0) break;
          spec.lines_en.forEach((s, i) => {
            const on = spec.on[i]; if (t < on) return;
            const n = Math.min(s.length, Math.floor((f - Math.round(on * fps)) + 1));
            ops.push({ kind: 'text', font: `500 56px ${F.mono}`, str: s.slice(0, n), x: 72, y: 180 + i * 78, color: col, alpha: out, cursor: n < s.length });
            blocks.push({ mode: 'PREMISE', box: [72, 130 + i * 78, 420, 60], on: true });
            const zh = (spec.lines_zh || [])[i];
            if (zh && margins) ops.push({ kind: 'vert', str: [...zh].slice(0, Math.ceil(n / s.length * [...zh].length)).join(''), x: right.x0 + (right.x1 - right.x0) * (i ? 0.38 : 0.62), y: 150, size: 56, color: col, alpha: out });
          });
          break;
        }
        case 'CARD': {
          let toks;
          if (spec.text_en) toks = [{ w: spec.text_en, t: spec.on ?? shot.t0 }];
          else if (spec.build) toks = Object.entries(spec.build).map(([w, bt]) => ({ w: w.replace(/\d+$/, ''), t: bt }));
          else toks = lineWords(tl, spec.line, { from: spec.words_from, to: spec.words_to, only: spec.words });
          if (!toks.length || t < toks[0].t - 1e-6) break;
          if (spec.until !== undefined && t >= spec.until + (spec.fade_frames || 0) / fps) break;
          const fade = spec.until !== undefined && t > spec.until ? clamp01(1 - (t - spec.until) * fps / (spec.fade_frames || 4)) : 1;
          if (!frame.card) dim = Math.max(dim, clamp01((f - Math.round(toks[0].t * fps) + 1) / 4));
          const vis = toks.filter(w => t >= w.t - 1e-6);
          if (spec.layout === 'margin-stack-left' && spec.rows && margins) {
            const size = 124, pitch = 138; let wi = 0;
            spec.rows.forEach((row, r) => {
              const n = row.split(' ').length, ws = toks.slice(wi, wi + n); wi += n;
              const shown = ws.filter(w => t >= w.t - 1e-6);
              if (!shown.length) return;
              ops.push({ kind: 'runs', font: `400 ${size}px ${F.card}`, x: 72, y: 190 + r * pitch, alpha: fade, fit: left.x1 - 110,
                runs: shown.map((w, k) => [(k ? ' ' : '') + w.w, wcol(w)]) });
            });
            blocks.push({ mode: 'CARD', box: [72, 90, left.x1 - 110, spec.rows.length * pitch], on: true });
          } else {
            const full = /full-bleed/.test(spec.layout || ''), upper = /upper-third/.test(spec.layout || ''), small = /small/.test(spec.layout || '');
            const size = small ? 110 : full ? 420 : frame.card ? 300 : 230;
            const y = upper ? 360 : small ? 520 : 600 + size * 0.25;
            const cx = small ? rect.x + rect.w * 0.66 : rect.x + rect.w / 2;
            ops.push({ kind: 'runs', font: `400 ${size}px ${F.card}`, x: cx, y, align: 'center', alpha: fade, fit: rect.w * 0.86,
              runs: vis.map((w, k) => [(k ? ' ' : '') + w.w, wcol(w)]) });
            blocks.push({ mode: 'CARD', box: [rect.x + rect.w * 0.07, y - size * 0.75, rect.w * 0.86, size], on: true });
          }
          break;
        }
        case 'THOUGHT': {
          const [a, b] = lineSpan(spec.line); if (t < a || t >= b + 6 / fps) break;
          const alpha = t > b ? clamp01(1 - (t - b) * fps / 6) : 1, lead = spec.lead || 0;
          const ws = lineWords(tl, spec.line).map(w => ({ ...w, t: w.t - lead * (w.k / Math.max(1, tl.wordsOf(spec.line).length - 1)) }));
          const vis = ws.filter(w => t >= w.t - 1e-6);
          if (!vis.length) break;
          const size = spec.size === 'small' ? 64 : 78;
          if (spec.layout === 'margin-stack-left' && margins) {
            vis.forEach((w, k) => { const e = clamp01((t - w.t) * fps / 3 + 0.34); ops.push({ kind: 'runs', font: `italic 400 ${size}px ${F.thought}`, x: 72, y: 200 + k * size * 1.1 + (1 - e) * 4, alpha: alpha * e, fit: left.x1 - 110, runs: [[w.w, wcol(w)]] }); });
            blocks.push({ mode: 'THOUGHT', box: [72, 140, left.x1 - 110, ws.length * size * 1.1], on: true });
          } else {
            const x = rect.x + (spec.layout === 'left-third' ? 72 : 96), y = spec.layout === 'left-third' ? 470 : 250;
            ops.push({ kind: 'runs', font: `italic 400 ${size}px ${F.thought}`, x, y, alpha, fit: rect.w * 0.6, wrap: rect.w * 0.5, lh: size * 1.1,
              runs: vis.map((w, k) => [(k ? ' ' : '') + w.w, wcol(w)]) });
            blocks.push({ mode: 'THOUGHT', box: [x, y - size, rect.w * 0.5, size * 2.2], on: true });
          }
          break;
        }
        case 'SUBTITLE': {
          const [a, b0] = lineSpan(spec.line);
          const next = tl.line(spec.line + 1), b = next ? Math.min(b0, next.start - 2 / fps) : b0;
          if (t < a || t >= b) break;
          const ws = lineWords(tl, spec.line);
          const runs = ws.map((w, k) => { const st = wordState(w, t, fps); return [(k ? ' ' : '') + w.w, st.active ? VOICE : col]; });
          if (margins && rect.x >= 420) {           // 7:9 / 1:1: the left margin, bottom, wrapped
            ops.push({ kind: 'runs', font: `500 44px ${F.sub}`, x: 72, y: 860, runs, wrap: left.x1 - 120, lh: 54, anchor: 'bottom', alpha: 1 });
            blocks.push({ mode: 'SUBTITLE', box: [72, 700, left.x1 - 120, 200], on: true });
          } else {
            const x = rect.x + (margins ? 48 : 72);
            ops.push({ kind: 'runs', font: `500 50px ${F.sub}`, x, y: 880, runs, alpha: 1, fit: 1920 - x - 72 });
            if (!margins) ops.push({ kind: 'text', font: `500 46px ${F.zh}`, str: zhLine(tl, spec.line), x, y: 936, color: col, alpha: 0.92 });
            blocks.push({ mode: 'SUBTITLE', box: [x, 830, 1200, 120], on: true });
          }
          break;
        }
        case 'ZH': {
          if (!margins) break;
          const l = tl.line(spec.line), [a, b] = lineSpan(spec.line);
          if (t < a || t >= b + 6 / fps) break;
          const n = zhReveal(tl, spec.line, t); if (!n) break;
          const chars = [...zhLine(tl, spec.line)], two = /2col/.test(spec.layout || '') || chars.length > 11;
          const size = right.x1 - right.x0 < 300 ? 44 : 56, per = two ? Math.ceil(chars.length / 2) : chars.length;
          const alpha = t > b ? clamp01(1 - (t - b) * fps / 6) : 1;
          for (let c = 0; c * per < n; c++) {
            const x = two ? right.x0 + (right.x1 - right.x0) * (c ? 0.36 : 0.64) : (right.x0 + right.x1) / 2;
            ops.push({ kind: 'vert', str: chars.slice(c * per, Math.min(n, (c + 1) * per)).join(''), x, y: 150, size, color: col, alpha });
          }
          blocks.push({ mode: 'ZH', box: [right.x0, 100, right.x1 - right.x0, 880], on: true, line: l.i });
          break;
        }
        case 'QUESTION': {
          if (t < spec.on) break;
          const n = Math.min(spec.text_en.length, Math.floor((t - spec.on) * 24) + 1);
          const alpha = clamp01((Math.round(shotEnd * fps) - f) / 8);
          ops.push({ kind: 'text', font: `400 84px ${F.thought}`, str: spec.text_en.slice(0, n), x: 960, y: 800, align: 'center', color: col, alpha, cursor: n < spec.text_en.length });
          if (n >= spec.text_en.length) ops.push({ kind: 'text', font: `400 58px ${F.zh}`, str: spec.text_zh, x: 960, y: 880, align: 'center', color: col, alpha: alpha * 0.9 });
          blocks.push({ mode: 'QUESTION', box: [360, 720, 1200, 180], on: true });
          break;
        }
        case 'MONO': {
          spec.lines_en.forEach((s, i) => {
            const on = (spec.on || [])[i] ?? shot.t0; if (t < on) return;
            const n = Math.min(s.length, Math.floor((t - on) * 24) + 1);
            const cardy = frame.card ? 430 : 470 + i * 56;
            ops.push({ kind: 'text', font: `500 40px ${F.mono}`, str: s.slice(0, n), x: frame.card ? 960 : rect.x + 120, y: cardy, align: frame.card ? 'center' : 'left', color: col, alpha: 1, cursor: n < s.length });
          });
          blocks.push({ mode: 'MONO', box: [rect.x + 120, 420, 800, 140], on: true });
          break;
        }
        case 'APPROVAL': {
          if (t < spec.on - 0.4) break;
          const ws = spec.boxes.map(s => '☐ ' + s), y = 600;
          ops.push({ kind: 'text', font: `400 26px ${F.mono}`, str: ws.join('     '), x: 960, y, align: 'center', color: col, alpha: 0.9 });
          if (t >= spec.on) ops.push({ kind: 'text', font: `500 30px ${F.mono}`, str: '✓', x: 960 - ops[ops.length - 1].str.length * 7.8, y: y - 2, color: VOICE, alpha: 1 });
          blocks.push({ mode: 'APPROVAL', box: [480, 570, 960, 40], on: true });
          break;
        }
        case 'TITLE': {
          if (t < spec.on) break;
          ops.push({ kind: 'text', font: `400 64px ${F.card}`, str: spec.text, x: 960, y: 760, align: 'center', color: col, alpha: clamp01((t - spec.on) * fps / 6) });
          blocks.push({ mode: 'TITLE', box: [560, 700, 800, 80], on: true });
          break;
        }
      }
    }
    return { blocks, dim, draw: hud => drawOps(hud, ops) };
  }
}

function drawOps(hud, ops) {
  const c = hud.ctx;
  for (const o of ops) {
    c.save(); c.globalAlpha = o.alpha ?? 1; c.textBaseline = 'alphabetic'; c.shadowBlur = 0;
    if (o.kind === 'text') {
      c.font = o.font; c.textAlign = o.align || 'left'; c.fillStyle = o.color; c.fillText(o.str, o.x, o.y);
      if (o.cursor) { const w = c.measureText(o.str).width, m = c.measureText('M'); const x = o.align === 'center' ? o.x + w / 2 : o.x + w; c.fillRect(x + 4, o.y - m.actualBoundingBoxAscent, m.width * 0.6, m.actualBoundingBoxAscent); }
    } else if (o.kind === 'runs') {
      c.font = o.font; c.textAlign = 'left';
      let lines = [o.runs];
      if (o.wrap) {                        // greedy wrap on run boundaries
        lines = []; let cur = [], w = 0;
        for (const r of o.runs) { const rw = c.measureText(r[0]).width; if (cur.length && w + rw > o.wrap) { lines.push(cur); cur = [[r[0].replace(/^ /, ''), r[1]]]; w = c.measureText(cur[0][0]).width; } else { cur.push(r); w += rw; } }
        if (cur.length) lines.push(cur);
      }
      const lh = o.lh || 0, y0 = o.anchor === 'bottom' ? o.y - (lines.length - 1) * lh : o.y;
      lines.forEach((runs, li) => {
        const widths = runs.map(r => c.measureText(r[0]).width), total = widths.reduce((a, b) => a + b, 0);
        const sc = o.fit && total > o.fit ? o.fit / total : 1;
        c.save(); c.translate(o.align === 'center' ? o.x - total * sc / 2 : o.x, y0 + li * lh); c.scale(sc, sc);
        let x = 0; runs.forEach((r, i) => { c.fillStyle = r[1]; c.fillText(r[0], x, 0); x += widths[i]; });
        c.restore();
      });
    } else if (o.kind === 'vert') {
      c.font = `500 ${o.size}px ${F.zh}`; c.textAlign = 'center'; c.fillStyle = o.color;
      let y = o.y + o.size;
      for (const g of verticalize(o.str)) {
        if (g.rotate) { const w = c.measureText(g.ch).width; c.save(); c.translate(o.x - o.size * 0.35, y - o.size * 0.8); c.rotate(Math.PI / 2); c.textAlign = 'left'; c.fillText(g.ch, 0, 0); c.restore(); y += w + o.size * 0.3; }
        else { c.fillText(g.ch, o.x, y); y += o.size * 1.18; }
      }
    }
    c.restore();
  }
}
