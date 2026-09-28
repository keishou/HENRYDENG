// type.js - the film's type engine (BIBLE 6; lane B): presence levels, layout, reveal, the bilingual policy, vertical
// Chinese, the contrast lane and the phone safe areas. Every frame is a pure function of (text spec, t, the luma under
// the text): no state between frames, every event tested by FRAME (round(T * 24)).
//
//   const type = new Type(ctx); await type.init()
//   type.layout(text, t, lumaProbe, frame) -> { blocks, dim, draw(hud) }
//     text      frameSpec.text: the shot's text spec array from shots.json (or a scene's override); null / [] = none
//     t         film time (s)
//     lumaProbe (x, y, w, h) -> { mean, std }: luma 0..1 of the pre-type frame under a design-px box (optional)
//     frame     { shot, s, rect (window, design px), register (the grade name), card (full-frame card shot) }
//   returns
//     blocks    [{ mode, box: [x, y, w, h] (design px), on: true, line, ink, band, contrast, safe }]  what is on screen
//               (contrast = WCAG ratio of the type colour against the mean luma under the box; safe = inside the BIBLE
//               6.6 phone area and out of the player-overlay zones)
//     dim       stops the core dims the image by: the card dim, -1 stop over 4 frames while a CARD is over an image
//     draw(hud) draws into the Hud canvas (1920x1080 design space, already scaled)
//
// Presence levels (BIBLE 6.2) and where they sit:
//   PREMISE   IBM Plex Mono 500 cap 40, left margin, typed 1 char / frame with a block cursor; ZH (Noto Sans SC) vertical
//             right; 4-frame fade from `off`
//   CARD      Noto Serif Display wdth 62.5 wght 900, tracking -1 %; each word hard on its onset (2-frame 102 -> 100 %
//             scale), VOICE while sung then -> TYPE over 8 frames; >= 1.2 s per appearance; exits with the cut or a
//             4-frame fade; layouts: margin-stack-left (S01), stop-card (S06-S07, S17c-S18), center-large (chorus cards
//             set as a small italic line over the huge word; other lines centred), upper-third, full-bleed, outline
//             (style), small (the Omega), stack (S39-S40 build)
//   THOUGHT   Newsreader Italic, cap 56-60, lowercase as sung, leading 1.12; word by word (3-frame fade, 4 px rise);
//             `lead` shifts onsets so the line completes early (S03); dissolves over the 6 frames after the line end
//   QUESTION  Newsreader Roman cap 64, centred low (baseline 800), 1 char / frame with a block cursor, ZH beneath in
//             Noto Serif SC 400 at 0.7x, 8-frame fade at the shot end
//   SUBTITLE  Inter Tight 500 50 px over Noto Sans SC 500 46 px; x 72, baselines 880 / 936 (16:9); on at line start -
//             2 frames (snapped to the cut when the line starts on it), off at line end + 6 frames or the next line;
//             the active word VOICE
//   ZH        the vertical column(s) of the window spans (right margin; reading order right to left)
//   MONO / APPROVAL / TITLE   S29 and S57 (the approval tick is drawn with the grease pencil)
//   NONE      withheld: nothing (the HUD follows its own track in hud/proof.js)
// Bilingual policy (BIBLE 6.5): 7:9 and 1:1 spans -> triptych (EN left margin, ZH vertical right margin); 4:3 -> one ZH
// column in the right margin for every sung line (added automatically); 16:9 -> SUBTITLE EN over ZH, THOUGHT and CARD
// with a small ZH line beneath (0.55x, cap 4 % of the frame height). A spec may carry zh: false.
// Scene overrides a text spec may carry (beyond shots.json): at: [x, y] (MONO lines, the small Omega card), side:
// 'left' | 'right' (THOUGHT), zh: false, until (s), fade_frames.
import { lineWords, wordState, zhLine, zhReveal, verticalize, segments, displayWord, zhSubtitle, zhCut, F } from './words.js';

export const COLORS = { TYPE: '#FAF9F5', INK_TYPE: '#111110', VOICE: '#D97757', INK: '#0A0A09' };
const { TYPE, INK_TYPE, VOICE } = COLORS;
export const SAFE = { x0: 72, x1: 1848, y0: 60, y1: 1020, overlays: [[0, 960, 480, 120], [1560, 960, 360, 120]] };
const TOP = 104;          // the cap-top line of the triptych (premise, stack, thought, ZH columns)
const GAP = 48;           // margin type <-> window edge
const L = 72, R = 1848;

export const ROLES = {
  card:     { family: '"Noto Serif Display", "Noto Serif SC", Georgia, serif', weight: 900, stretch: 'extra-condensed', track: -0.01 },
  cardI:    { family: 'Newsreader, Georgia, serif', weight: 400, style: 'italic' },
  thought:  { family: 'Newsreader, Georgia, serif', weight: 400, style: 'italic' },
  question: { family: 'Newsreader, Georgia, serif', weight: 400 },
  sub:      { family: '"Inter Tight", "Noto Sans SC", Arial, sans-serif', weight: 500 },
  mono:     { family: '"IBM Plex Mono", "Noto Sans SC", monospace', weight: 500 },
  monoR:    { family: '"IBM Plex Mono", "Noto Sans SC", monospace', weight: 400 },
  zhSerif:  { family: '"Noto Serif SC", "Noto Sans SC", serif', weight: 500 },
  zhSerifQ: { family: '"Noto Serif SC", "Noto Sans SC", serif', weight: 400 },
  zhSans:   { family: '"Noto Sans SC", sans-serif', weight: 500 },
  title:    { family: '"Noto Serif SC", serif', weight: 600 },
};
const FONT_FILES = [
  ['Noto Serif Display', ['NotoSerifDisplay-VF.ttf'], { weight: '100 900', stretch: '62.5% 100%' }],
  ['Newsreader', ['Newsreader-Italic-VF.ttf'], { weight: '200 800', style: 'italic' }],
  ['Newsreader', ['Newsreader-VF.ttf'], { weight: '200 800', style: 'normal' }],
  ['Inter Tight', ['InterTight-VF.ttf', 'InterTight.ttf'], { weight: '100 900' }],
  ['IBM Plex Mono', ['IBMPlexMono-Regular.ttf'], { weight: '400' }],
  ['IBM Plex Mono', ['IBMPlexMono-Medium.ttf'], { weight: '500' }],
  ['Noto Serif SC', ['NotoSerifSC-sub.ttf', 'NotoSerifSC-VF.ttf'], { weight: '200 900' }],
  ['Noto Sans SC', ['NotoSansSC-sub.ttf', 'NotoSansSC-VF.ttf'], { weight: '100 900' }],
];

const clamp01 = x => Math.max(0, Math.min(1, x));
const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const mix = (a, b, k) => { if (k <= 0) return a; if (k >= 1) return b; const A = hex(a), B = hex(b); return `rgb(${A.map((x, i) => Math.round(x + (B[i] - x) * k)).join(',')})`; };
const lin = v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
const relLum = h => { const [r, g, b] = hex(h).map(v => lin(v / 255)); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const LUM = { [TYPE]: relLum(TYPE), [INK_TYPE]: relLum(INK_TYPE) };
const contrastOn = (col, lumaMean) => { const a = LUM[col], b = lin(lumaMean); return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); };
const pop = df => df <= 0 ? 1.02 : df === 1 ? 1.01 : 1;       // CARD: 2-frame 102 -> 100 % scale
const isChorusCard = line => line && /P\(doom\)/.test(line.text);

export class Type {
  constructor(ctx) { this.ctx = ctx; this.tl = ctx.tl; this.fps = ctx.tl.fps; this._w = new Map(); }

  async init() {
    const a = this.ctx.assets;
    // each family: the first file found under /fonts/ (fetch_fonts.sh) or /out/fonts/
    const ok = await Promise.all(FONT_FILES.map(async ([fam, files, desc]) => {
      for (const file of files) {
        for (const base of ['/fonts/', '/out/fonts/']) {
          if (!(await a.exists(base + file))) continue;
          try { const f = new FontFace(fam, `url(${base}${file})`, desc); await f.load(); document.fonts.add(f); return fam; } catch (e) { console.warn('font', file, e.message); }
        }
      }
      console.warn(`type.js: no font file for ${fam} (run film/fetch_fonts.sh)`); return null;
    }));
    await document.fonts.ready;
    this.fontsLoaded = ok.filter(Boolean);
    const cv = document.createElement('canvas'); cv.width = cv.height = 8;
    this.mc = cv.getContext('2d', { willReadFrequently: true });
    this.cap = {};
    for (const r of Object.keys(ROLES)) { this.font(this.mc, r, 100); this.cap[r] = this.mc.measureText('H').actualBoundingBoxAscent / 100 || 0.7; }
    this.xh = {}; for (const r of ['thought', 'sub']) { this.font(this.mc, r, 100); this.xh[r] = this.mc.measureText('x').actualBoundingBoxAscent / 100 || 0.48; }
  }

  // ------------------------------------------------------------------------------------------------ font helpers
  font(c, role, size) {
    const r = ROLES[role];
    c.font = `${r.style || 'normal'} ${r.weight} ${size.toFixed(2)}px ${r.family}`;
    c.fontStretch = r.stretch || 'normal';
    c.letterSpacing = `${((r.track || 0) * size).toFixed(2)}px`;
    c.fontKerning = 'normal'; c.textAlign = 'left'; c.textBaseline = 'alphabetic';
  }
  sizeForCap(role, cap) { return cap / this.cap[role]; }
  w(role, size, str) {
    const key = role + '|' + size.toFixed(2) + '|' + str;
    let v = this._w.get(key);
    if (v === undefined) { this.font(this.mc, role, size); v = this.mc.measureText(str).width; if (this._w.size > 20000) this._w.clear(); this._w.set(key, v); }
    return v;
  }
  // x offset of each word in a line of words joined by spaces (prefix measurement keeps the kerning)
  line(role, size, words) {
    const xs = [], ws = [];
    for (let k = 0; k < words.length; k++) { const end = this.w(role, size, words.slice(0, k + 1).join(' ')), wk = this.w(role, size, words[k]); xs.push(end - wk); ws.push(wk); }
    return { xs, ws, width: words.length ? this.w(role, size, words.join(' ')) : 0 };
  }
  // x offset of each segment inside a word (letter parts)
  segX(role, size, word, segs) { return segs.map(sg => this.w(role, size, word.slice(0, sg.i1)) - this.w(role, size, sg.s)); }
  // balanced wrap (minimum raggedness; no widows when avoidable) of words into lines no wider than maxW
  wrap(role, size, words, maxW) {
    const n = words.length; if (!n) return [];
    const width = (i, j) => this.w(role, size, words.slice(i, j).join(' '));
    const best = new Array(n + 1).fill(Infinity), prev = new Array(n + 1).fill(0); best[0] = 0;
    for (let j = 1; j <= n; j++) for (let i = j - 1; i >= 0; i--) {
      const wd = width(i, j); if (wd > maxW && j - i > 1) break;
      const slack = Math.max(0, maxW - wd), last = j === n;
      // raggedness: every line's slack squared (the last line counts a quarter); a short lone last word costs extra
      let cost = last ? slack * slack * 0.25 + (j - i === 1 && n > 3 && wd < maxW * 0.3 ? maxW * maxW * 0.2 : 0) : slack * slack;
      if (wd > maxW) cost += 1e9;
      if (best[i] + cost < best[j]) { best[j] = best[i] + cost; prev[j] = i; }
    }
    const lines = []; for (let j = n; j > 0; j = prev[j]) lines.unshift([prev[j], j]);
    return lines;
  }

  // ------------------------------------------------------------------------------------------------ layout
  layout(text, t, lumaProbe = null, frame = {}) {
    try { return this._layout(text, t, lumaProbe, frame); }
    catch (e) {
      console.error('type.layout', e);
      const msg = String(e && (e.stack || e.message) || e).split('\n')[0];
      return { blocks: [{ mode: 'ERROR', box: [0, 0, 0, 0], on: true, error: msg }], dim: 0,
        draw: hud => { const c = hud.ctx; c.fillStyle = VOICE; c.font = '500 18px "IBM Plex Mono", monospace'; c.fillText('TYPE ERROR ' + msg.slice(0, 120), 80, 1040); } };
    }
  }

  _layout(text, t, lumaProbe, frame) {
    const tl = this.tl, fps = this.fps;
    const f = Math.round(t * fps);
    const shot = frame.shot || tl.shotAt(t);
    const rect = frame.rect || this.ctx.win.rect(t, shot);
    const specs = (Array.isArray(text) ? text : text ? [text] : []).filter(Boolean);
    const E = { t, f, fps, shot, rect, card: !!(frame.card || rect.card), specs, register: frame.register || shot.look, f0: shot.frames[0], f1: shot.frames[1] };
    if (!specs.length) return { blocks: [], dim: 0, draw() {} };
    const none = specs.find(s => s.mode === 'NONE' && (s.from === undefined || f >= F(s.from, fps)) && (s.to === undefined || f < F(s.to, fps)));
    if (none) return { blocks: [{ mode: 'NONE', box: [0, 0, 0, 0], on: true, safe: true }], dim: 0, draw() {} };
    E.truncAt = this._truncations(E);

    const blocks = [];
    for (const spec of specs) {
      const fn = this['_' + spec.mode];
      if (typeof fn !== 'function') continue;
      const out = fn.call(this, spec, E);
      if (out) for (const b of (Array.isArray(out) ? out : [out])) if (b) blocks.push(b);
    }
    // automatic ZH for the 4:3 span: one vertical column in the right margin for the line being sung
    const zhAuto = this._zhColumnAuto(E, blocks);
    if (zhAuto) blocks.push(zhAuto);

    // contrast lane (BIBLE 6.4)
    for (const b of blocks) this._contrast(b, lumaProbe, E);
    // phone safe areas (BIBLE 6.6)
    for (const b of blocks) b.safe = b.critical === false ? true : safeBox(b.box);
    let dim = 0;
    for (const b of blocks) if (b.dim) dim = Math.max(dim, b.dim);
    return {
      blocks: blocks.map(b => ({ mode: b.mode, box: b.box.map(v => Math.round(v)), on: true, line: b.line, ink: !!b.ink, band: !!b.band,
        contrast: b.contrast ? +b.contrast.toFixed(2) : null, safe: b.safe, layout: b.layout })),
      dim,
      draw: hud => { const c = hud.ctx; for (const b of blocks) { c.save(); if (b.band) drawBand(c, b.bandBox || b.box); b.draw(c, b.ink ? INK_TYPE : TYPE); c.restore(); } },
    };
  }

  // a CARD onset of a later line cuts the earlier lines' blocks (one type block at a time)
  _truncations(E) {
    const out = {};
    for (const s of E.specs) {
      if (s.mode !== 'CARD' || s.line === undefined) continue;
      const ws = lineWords(this.tl, s.line, { extras: false });
      const first = s.build ? Math.min(...Object.values(s.build)) : (ws[0] && ws[0].t);
      if (first === undefined) continue;
      for (let i = 0; i < s.line; i++) out[i] = Math.min(out[i] ?? Infinity, F(first, E.fps));
    }
    return out;
  }
  _cut(line, E) { return E.truncAt[line] ?? Infinity; }
  // the window a block is laid out for: the one its line settles into (a line that starts during a window move is set
  // for the move's target, so type never reflows while the window opens)
  layoutRect(E, fOn) {
    const T = fOn / E.fps;
    let tt = T + 8 / E.fps;
    for (const e of this.tl.doc.windows || []) if (e.t1 !== undefined && T >= e.t0 - 1e-6 && T < e.t1) tt = Math.max(tt, e.t1);
    return this.ctx.win.rect(tt, E.shot);
  }
  margins(r) { return { left: [L, r.x - GAP], right: [r.x + r.w + GAP, R], wide: r.x >= 300 }; }
  zhMode(E, fOn) {   // which ZH setting applies to a line that comes on at frame fOn
    const r = this.layoutRect(E, fOn);
    if (E.card) return 'none';
    if (r.x >= 300) return 'triptych';
    if (r.x >= 180) return 'column';
    return 'beneath';
  }
  zhOff(spec, E) { return spec.zh === false || /ZH is the image/i.test(E.shot.text_layout || ''); }

  // ------------------------------------------------------------------------------------------------ PREMISE
  _PREMISE(spec, E) {
    const { f, fps } = E;
    const fOff = F(spec.off, fps);
    if (f >= fOff + 3) return null;
    const alpha = f < fOff ? 1 : clamp01((fOff + 3 - f) / 4);            // f46 .75, f47 .5, f48 .25, f49 gone
    const cap = 40, size = this.sizeForCap('mono', cap), zsize = size * 0.96;
    const ons = spec.on.map(x => F(x, fps));
    if (f < ons[0]) return null;
    const lines = spec.lines_en, zh = spec.lines_zh || [];
    const base = [TOP + cap, TOP + cap + Math.round(cap * 1.9)];
    const typed = lines.map((s, i) => f < ons[i] ? -1 : Math.min(s.length, f - ons[i] + 1));
    const cur = typed[1] >= 0 ? 1 : 0;
    const beat = this.tl.beatAt(E.t);
    const r = this.layoutRect(E, ons[0]);
    const m = this.margins(r);
    const zx0 = m.right[1] - zsize / 2, zdx = zsize * 1.75;
    const self = this;
    const w0 = Math.max(...lines.map(s => this.w('mono', size, s)));
    return {
      mode: 'PREMISE', critical: true, zone: 'margin', box: [L, TOP - 8, w0 + size, base[1] - TOP + 24],
      draw(c, col) {
        c.globalAlpha = alpha;
        lines.forEach((s, i) => {
          const n = typed[i]; if (n < 0) return;
          self.font(c, 'mono', size); c.fillStyle = col; c.fillText(s.slice(0, n), L, base[i]);
          const blink = n < s.length || beat.phase < 0.5;                // cursor: solid while typing, then on the beat
          if (i === cur && blink) { const x = L + self.w('mono', size, s.slice(0, n)) + (n ? size * 0.08 : 0); c.fillRect(x, base[i] - cap, size * 0.56, cap); }
          const z = zh[i]; if (!z) return;
          const cps = [...z], k = Math.ceil(cps.length * n / s.length);
          self.vertical(c, cps.slice(0, k).join(''), { x: zx0 - i * zdx, y: TOP - zsize * 0.06, size: zsize, role: 'zhSans', color: col });
        });
      },
    };
  }

  // ------------------------------------------------------------------------------------------------ CARD
  _cardWords(spec, E) {
    const tl = this.tl;
    if (spec.text_en) return [{ w: spec.text_en, t: spec.on ?? E.shot.t0, e: (spec.on ?? E.shot.t0) + 1e3, k: 0, line: spec.line, constVoice: true }];
    if (spec.build && !/stop-card/.test(spec.layout || '')) {   // S39: one "just" per onset (lyric word + extra_vocals repeats)
      const all = lineWords(tl, spec.line, { extras: true });
      return Object.entries(spec.build).map(([key, bt], k) => {
        const w = all.find(x => Math.abs(x.t - bt) < 0.03) || { w: key.replace(/\d+$/, ''), t: bt, e: bt + 0.4 };
        return { ...w, k };
      });
    }
    let ws = lineWords(tl, spec.line, { from: spec.words_from, only: spec.words, extras: false });
    if (spec.words_to) {
      const k = ws.findIndex(w => w.w.replace(/[^\p{L}\p{N}'’?]/gu, '').toLowerCase() === spec.words_to.toLowerCase().replace(/[^\p{L}\p{N}'’?]/gu, ''));
      if (k >= 0) {
        const endsSentence = /[.?!]["”]?$/.test(ws[k].w);
        const next = this._nextSpec(E, spec);
        if (endsSentence || !next) ws = ws.slice(0, k + 1);
        else ws = ws.map((w, j) => j > k ? { ...w, laterShot: true } : w);   // laid out, revealed in the next shot
      }
    }
    // a card whose layout changes at the next cut (S47 -> S48 full-bleed): set only what appears in this shot
    const next = this._nextSpec(E, spec);
    if (!next || layoutKey(next, next._card) !== layoutKey(spec, E.card)) {
      const lastF = E.f1 - 1;
      ws = ws.map(w => {
        const segs = segments(w).filter(sg => F(sg.t, E.fps) <= lastF);
        if (!segs.length) return null;
        if (segs.length < segments(w).length) return { ...w, w: w.w.slice(0, segs[segs.length - 1].i1), parts: segs.length > 1 ? segs.map(s => s.t) : undefined, trimmed: true };
        return w;
      }).filter(Boolean);
    }
    return ws;
  }
  _nextSpec(E, spec) {
    const i = this.tl.shots.indexOf(E.shot), nx = this.tl.shots[i + 1];
    const s = nx && (nx.text || []).find(x => x.mode === 'CARD' && x.line === spec.line);
    return s ? { ...s, _card: /full frame|card/i.test(nx.window || '') } : null;
  }

  _CARD(spec, E) {
    const { f, fps, shot } = E;
    const lineObj = spec.line !== undefined ? this.tl.line(spec.line) : null;
    const ws = this._cardWords(spec, E);
    if (!ws.length) return null;
    const firstF = F(ws[0].t, fps);
    if (f < firstF) return null;
    const layout = layoutKey(spec, E.card);
    // exit: explicit until; else the next CARD / NONE of this shot; else max(line end, on-screen-in-this-shot + 1.2 s)
    const i0 = E.specs.indexOf(spec), nxt = E.specs.slice(i0 + 1).find(x => x.mode === 'CARD' || x.mode === 'NONE');
    let untilF;
    if (spec.until !== undefined) untilF = F(spec.until, fps);
    else {
      const visF = Math.max(firstF, E.f0);
      untilF = Math.max(lineObj ? F(lineObj.end, fps) : firstF, visF + Math.round(1.2 * fps));
    }
    let hardF = Infinity;
    if (nxt) hardF = F(nxt.mode === 'NONE' ? nxt.from : (nxt.line !== undefined ? lineWords(this.tl, nxt.line, { extras: false })[0].t : nxt.on), fps);
    const ff = spec.fade_frames || 4;
    if (f >= hardF || f >= untilF + ff) return null;
    const fade = f < untilF ? 1 : clamp01((untilF + ff - f) / (ff + 1));
    const over = !E.card && !/margin|small/.test(layout);
    // card dim: -1 stop over 4 frames from the card's appearance in this shot (full at once if it is up at the cut)
    const onF = Math.max(firstF, E.f0);
    const dimK = !over ? 0 : (onF === E.f0 && firstF < E.f0 ? 1 : clamp01((f - onF + 1) / 4)) * fade;
    let b;
    if (layout === 'margin-stack-left' && spec.rows) b = this._cardStack(spec, E, ws, fade);
    else if (/stop-card/.test(layout) || (layout === 'center-large' && isChorusCard(lineObj) && !/outline/.test(spec.style || '') && spec.line !== 40)) b = this._cardChorus(spec, E, ws, fade, layout);
    else if (spec.style === 'outline') b = this._cardChorus(spec, E, ws, fade, 'outline');
    else if (/small/.test(layout)) b = this._cardSmall(spec, E, ws, fade);
    else if (spec.build || spec.words_from === 'transformers') b = this._cardBuild(spec, E, ws, fade);
    else b = this._cardLine(spec, E, ws, fade, layout);
    if (!b) return null;
    b.dim = dimK; b.line = spec.line; b.layout = layout;
    return b;
  }

  // word colour: VOICE while sung, settling to the base colour over 8 frames; constVoice (the Omega) stays VOICE
  wcol(w, col, t) { if (w.constVoice) return VOICE; const st = wordState(w, t, this.fps); return st.on ? mix(VOICE, col, st.active ? 0 : st.settle) : col; }

  // draw a word (or its revealed letter parts) at x, y with the CARD pop; pivot: 'left' | 'center'
  drawWord(c, role, size, w, x, y, col, t, { pivot = 'left', popOn = true, outline = 0, alpha = 1, suffixVoice = null } = {}) {
    const segs = segments(w), xs = this.segX(role, size, w.w, segs), fps = this.fps, f = Math.round(t * fps);
    const colW = this.wcol(w, col, t);
    this.font(c, role, size);
    const ww = this.w(role, size, w.w);
    for (let k = 0; k < segs.length; k++) {
      const sf = F(segs[k].t, fps); if (f < sf) break;
      const s = popOn ? pop(f - sf) : 1;
      c.save(); c.globalAlpha *= alpha;
      const px = pivot === 'center' ? x + ww / 2 : x, py = y;
      if (s !== 1) { c.translate(px, py); c.scale(s, s); c.translate(-px, -py); }
      if (outline) { c.strokeStyle = colW; c.lineWidth = outline; c.lineJoin = 'round'; c.strokeText(segs[k].s, x + xs[k], y); }
      else { c.fillStyle = colW; c.fillText(segs[k].s, x + xs[k], y); }
      c.restore();
    }
    if (suffixVoice && f >= F(suffixVoice.t, fps)) {           // "trans|formers": the repeated suffix lights up again
      const st = wordState(suffixVoice, t, fps), k2 = st.active ? 0 : st.settle;
      if (k2 < 1) {
        const i0 = w.w.toLowerCase().lastIndexOf(suffixVoice.w.toLowerCase());
        if (i0 > 0) { const sx = this.w(role, size, w.w.slice(0, i0 + suffixVoice.w.length)) - this.w(role, size, w.w.slice(i0, i0 + suffixVoice.w.length));
          c.save(); c.fillStyle = mix(VOICE, col, k2); c.fillText(w.w.slice(i0, i0 + suffixVoice.w.length), x + sx, y); c.restore(); }
      }
    }
  }

  // S01: the left-margin stack, one row per spec row, cap ~100 sized to fit the margin column
  _cardStack(spec, E, ws, alpha) {
    const r = this.layoutRect(E, F(ws[0].t, E.fps)), m = this.margins(r);
    const colW = m.left[1] - m.left[0];
    let wi = 0;
    const rows = spec.rows.map(row => { const n = row.split(' ').length, rw = ws.slice(wi, wi + n); wi += n; return rw; });
    const cap = Math.min(0.095 * 1080, 100);
    let size = this.sizeForCap('card', cap);
    for (const rw of rows) { const wd = this.line('card', size, rw.map(w => w.w)).width; if (wd > colW) size *= colW / wd; }
    const pitch = size * 1.04, capPx = size * this.cap.card;
    const y0 = TOP + capPx, self = this;
    const lay = rows.map(rw => this.line('card', size, rw.map(w => w.w)));
    return {
      mode: 'CARD', critical: true, zone: 'margin', box: [L, TOP, colW, capPx + pitch * (rows.length - 1) + size * 0.24],
      draw(c, col) {
        c.globalAlpha = alpha;
        rows.forEach((rw, ri) => rw.forEach((w, k) => self.drawWord(c, 'card', size, w, L + lay[ri].xs[k], y0 + ri * pitch, col, E.t)));
      },
    };
  }

  // the chorus cards: a small italic line over the huge word ("I'm upping my" / "P(doom)"); stop-card = full frame,
  // cap 30 % (S18: x 1.1); center-large over the image, cap 18 %; outline = the huge word stroked (S32 / S33)
  _cardChorus(spec, E, ws, alpha, layout) {
    const stop = /stop-card/.test(layout), outline = layout === 'outline' || spec.style === 'outline';
    const all = ws, small = all.filter(w => !/P\(/.test(w.w));
    let huge = all.filter(w => /P\(/.test(w.w));
    if (stop) huge = huge.map(w => { const sg = segments(w)[0]; return { ...w, w: sg.s, t: sg.t, parts: undefined }; });
    const sc = spec.scale || 1;
    const hugeCap = (stop ? 0.30 : 0.18) * 1080 * sc;
    const hSize = this.sizeForCap('card', hugeCap);
    const iSize = this.sizeForCap('cardI', (stop ? 62 : 58) * sc);
    // horizontal: the block is centred on the complete "P(doom)" so the open parenthesis faces the empty half
    const fullHuge = 'P(doom)';
    const hugeW = this.w('card', hSize, fullHuge);
    const r = E.rect;
    const cx = stop ? 960 : r.x + r.w / 2;
    let x0 = Math.round(cx - hugeW / 2);
    if (stop) x0 = Math.max(x0, 200);
    const yHuge = Math.round(540 + hugeCap / 2 + (stop ? 0 : -20));
    const yI = Math.round(yHuge - hugeCap - iSize * 0.78);
    const smallLay = this.line('cardI', iSize, small.map(w => w.w));
    const self = this, t = E.t;
    const zh = !stop && E.shot.window !== '4:3' && this.zhMode(E, F(all[0].t, E.fps)) === 'beneath' && !this.zhOff(spec, E) ? this._zhBeneath(spec.line, E, 'card', hSize) : null;
    const zhY = yHuge + Math.round(hSize * 0.24) + (zh ? zh.size * 1.35 : 0);
    const hugeVis = huge.map(w => { const sg = segments(w).filter(q => E.f >= F(q.t, E.fps)); return sg.length ? w.w.slice(0, sg[sg.length - 1].i1) : ''; }).join('');
    const width = Math.max(smallLay.width, hugeVis ? this.w('card', hSize, hugeVis) : 0, zh ? this.w('zhSerif', zh.size, zh.text) : 0);
    return {
      mode: 'CARD', critical: true, zone: E.card ? 'card' : 'window', probe: !E.card, zhBeneath: !!zh,
      box: [x0, yI - iSize * this.cap.cardI - 8, width, yHuge - yI + iSize * this.cap.cardI + hSize * 0.24 + (zh ? zh.size * 1.6 : 0)],
      draw(c, col) {
        c.globalAlpha = alpha;
        small.forEach((w, k) => self.drawWord(c, 'cardI', iSize, w, x0 + smallLay.xs[k], yI, col, t, { popOn: true }));
        huge.forEach(w => self.drawWord(c, 'card', hSize, w, x0, yHuge, col, t, { outline: outline ? Math.max(2.5, hSize * 0.012) : 0 }));
        if (zh) zh.draw(c, col, x0, zhY, alpha);
      },
    };
  }

  // the Omega: small, VOICE, beside the point (spec.at from the scene, else right of the window centre)
  _cardSmall(spec, E, ws, alpha) {
    const cap = 58, size = this.sizeForCap('card', cap), w = ws[0];
    const r = E.rect, at = spec.at || [r.x + r.w / 2 + 70, 540 - 40];
    const self = this, t = E.t;
    return {
      mode: 'CARD', critical: true, zone: 'window', probe: false, box: [at[0], at[1] - cap, this.w('card', size, w.w), cap],
      draw(c) { c.globalAlpha = alpha; self.drawWord(c, 'card', size, { ...w, constVoice: true }, at[0], at[1], VOICE, t); },
    };
  }

  // S39 / S40: the build stack in the left third ("Just / just / just / just", then "transformers / all the way!")
  _cardBuild(spec, E, ws, alpha) {
    const rows = spec.build ? ws.map(w => [w]) : splitRows(ws, ['all']);
    const extras = spec.build ? [] : lineWords(this.tl, spec.line, { extras: true }).filter(w => w.extra);
    const cap = 118, size = this.sizeForCap('card', cap), pitch = size * 1.02, capPx = size * this.cap.card;
    const qw = ws.some(w => /^[“‘"']/.test(w.w)) ? this.w('card', size, '“') : 0;
    const x0 = Math.max(L + qw, E.rect.x + 72 + qw);            // a hung quote stays inside the safe area
    const zh = this.zhMode(E, F(ws[0].t, E.fps)) === 'beneath' && !this.zhOff(spec, E) ? this._zhBeneath(spec.line, E, 'card', size) : null;
    const hBlock = capPx + pitch * (rows.length - 1);
    const y0 = Math.round(540 - hBlock / 2 + capPx - (zh ? 30 : 0));
    const lay = rows.map(rw => this.line('card', size, rw.map(w => w.w)));
    const self = this, t = E.t;
    const zhY = y0 + pitch * (rows.length - 1) + size * 0.24 + (zh ? zh.size * 1.5 : 0);
    const width = Math.max(...lay.map(l => l.width));
    return {
      mode: 'CARD', critical: true, zone: 'window', probe: true, zhBeneath: !!zh, box: [x0, y0 - capPx, width, hBlock + size * 0.24 + (zh ? zh.size * 1.8 : 0)],
      draw(c, col) {
        c.globalAlpha = alpha;
        rows.forEach((rw, ri) => rw.forEach((w, k) => {
          const sfx = extras.find(x => x.t > w.t && w.w.toLowerCase().replace(/[^a-z]/g, '').endsWith(x.w.toLowerCase()) && x.w.length < w.w.length);
          if (sfx) w = { ...w, e: Math.min(w.e ?? sfx.t, sfx.t) };                  // it settles as its suffix relights
          const hang = k === 0 && /^[“‘"']/.test(w.w) ? self.w('card', size, w.w[0]) : 0;       // hanging punctuation
          self.drawWord(c, 'card', size, w, x0 + lay[ri].xs[k] - hang, y0 + ri * pitch, col, t, { suffixVoice: sfx || null });
        }));
        if (zh) zh.draw(c, col, x0, zhY, alpha);
      },
    };
  }

  // a line card: centred (center-large) / upper third / full-bleed; one row, or two balanced rows if it does not fit
  _cardLine(spec, E, ws, alpha, layout) {
    const r = this.layoutRect(E, Math.max(F(ws[0].t, E.fps), E.f0)), full = /full-bleed/.test(layout), upper = /upper-third/.test(layout);
    if (full && ws.some(w => /P\(/.test(w.w))) ws = ws.filter(w => /P\(/.test(w.w));      // S48: "P(doom)" fills the frame
    const words = ws.map(w => w.w);
    // measure: the safe width in a full-width window (a card may run edge to edge of the safe area), 86 % of a narrower
    // one; when the step wedge is up the card keeps clear of its column on both sides
    const wedge = E.shot.hud && E.shot.hud.wedge;
    let maxW = full ? R - L : r.w >= 1919 ? R - L : r.w * 0.86;
    if (wedge && !full) maxW = Math.min(maxW, r.w - 2 * 230);
    let cap = full ? 0.46 * 1080 : upper ? 0.12 * 1080 : E.card ? 0.24 * 1080 : spec.line === 40 ? 0.15 * 1080 : 0.13 * 1080;
    let size = this.sizeForCap('card', cap);
    let wd = this.line('card', size, words).width;
    let rows = [ws];
    if (full) { size *= maxW / wd; }
    else if (wd > maxW) {
      const minSize = this.sizeForCap('card', 0.12 * 1080);
      if (wd * minSize / size <= maxW) size *= maxW / wd;
      else { const lines = this.wrap('card', size, words, maxW); rows = lines.map(([a, b]) => ws.slice(a, b)); }
    }
    const capPx = size * this.cap.card, pitch = size * 1.02;
    const zh = !full && this.zhMode(E, F(ws[0].t, E.fps)) === 'beneath' && !this.zhOff(spec, E) ? this._zhBeneath(spec.line, E, 'card', size, spec.zh_small ? 0.4 : 0.55) : null;
    const hBlock = capPx + pitch * (rows.length - 1);
    const cy = upper ? 330 : full ? 540 : 500;
    const y0 = Math.round(cy - hBlock / 2 + capPx - (zh ? zh.size * 0.7 : 0));
    const cx = full ? 960 : r.x + r.w / 2;
    const lay = rows.map(rw => this.line('card', size, rw.map(w => w.w)));
    const self = this, t = E.t;
    const zhY = y0 + pitch * (rows.length - 1) + size * 0.25 + (zh ? zh.size * 1.45 : 0);
    const width = Math.max(...lay.map(l => l.width));
    return {
      mode: 'CARD', critical: true, zone: 'window', probe: true, zhBeneath: !!zh, box: [cx - width / 2, y0 - capPx, width, hBlock + size * 0.24 + (zh ? zh.size * 1.8 : 0)],
      draw(c, col) {
        c.globalAlpha = alpha;
        rows.forEach((rw, ri) => rw.forEach((w, k) => {
          if (w.laterShot) return;
          self.drawWord(c, 'card', size, w, cx - lay[ri].width / 2 + lay[ri].xs[k], y0 + ri * pitch, full ? VOICE : col, t, { pivot: 'left' });
        }));
        if (zh) zh.draw(c, col, cx, zhY, alpha, 'center');
      },
    };
  }

  // a small ZH line beneath a THOUGHT / CARD (16:9): 0.55x the EN size, capped at 4 % of the frame height
  _zhBeneath(line, E, enRole, enSize, k = 0.55) {
    if (line === undefined) return null;
    let z = zhLine(this.tl, line), to = null;
    if (line === 44) {                                       // "We'll never know." is withheld (NONE): the question only
      z = zhCut(z, 1); const q = this.tl.wordsOf(44).find(w => /\?/.test(w.w)); to = q ? q.t + 0.3 : null;
    }
    if (!z) return null;
    const size = Math.min(enSize * k, 0.04 * 1080), role = enRole === 'sub' ? 'zhSans' : 'zhSerif';
    const self = this, n = zhReveal(this.tl, line, E.t, { text: z, to });
    return {
      size, text: z,
      draw(c, col, x, y, alpha = 1, align = 'left') {
        if (!n) return;
        const str = [...z].slice(0, n).join('');
        self.font(c, role, size); c.fillStyle = col; c.globalAlpha = alpha;
        const xx = align === 'center' ? x - self.w(role, size, z) / 2 : x;
        c.fillText(str, xx, y);
      },
    };
  }

  // ------------------------------------------------------------------------------------------------ THOUGHT
  _THOUGHT(spec, E) {
    const { f, fps, t } = E, tl = this.tl;
    const l = tl.line(spec.line); if (!l) return null;
    const base = lineWords(tl, spec.line, { extras: false });
    const n = base.length, lead = spec.lead || 0;
    const ws = base.map((w, k) => ({ ...w, t: w.t - lead * (n > 1 ? k / (n - 1) : 1), parts: w.parts && w.parts.map(p => p - lead * (n > 1 ? k / (n - 1) : 1)) }));
    const fStart = Math.max(F(ws[0].t, fps), E.f0), fEnd = F(l.end, fps);
    const cut = this._cut(spec.line, E);
    if (f < F(ws[0].t, fps) || f >= fEnd + 6 || f >= cut) return null;
    const alpha = f < fEnd ? 1 : clamp01((fEnd + 6 - f) / 7);
    const r = this.layoutRect(E, fStart), m = this.margins(r);
    const inMargin = spec.layout === 'margin-stack-left' && m.wide;
    const small = spec.size === 'small';
    const cap = inMargin ? 56 : small ? 54 : 60;
    const size = this.sizeForCap('thought', cap), lead2 = size * 1.12;
    const words = ws.map((w, k) => displayWord(w, 'THOUGHT', k));
    let x0, colW, y0, zone = 'window';
    const upperLeft = /upper[- ]left/i.test(spec.layout || '') || /upper left/i.test(E.shot.text_layout || '');
    if (inMargin) { x0 = L; colW = m.left[1] - m.left[0]; y0 = TOP + size * this.cap.thought; zone = 'margin'; }
    else if (r.w <= 1440 + 1) {       // 4:3: inside the window, left (S10 small upper left; S12 left negative space)
      x0 = r.x + 72; colW = Math.min(620, r.w * 0.42);
      y0 = small ? 220 : 470;
    } else {                          // 16:9: the left third
      x0 = L; colW = 600; y0 = upperLeft ? 250 : 470;
    }
    if (spec.side === 'right' && !inMargin) x0 = r.x + r.w - 72 - colW;
    const lines = this.wrap('thought', size, words, colW);
    const zhb = !inMargin && this.zhMode(E, fStart) === 'beneath' && !this.zhOff(spec, E) ? this._zhBeneath(spec.line, E, 'thought', size) : null;
    const lays = lines.map(([a, b]) => this.line('thought', size, words.slice(a, b)));
    const hText = size * this.cap.thought + lead2 * (lines.length - 1);
    if (!inMargin && r.w > 1440 + 1 && !upperLeft) y0 = Math.round(540 - (hText + (zhb ? zhb.size * 1.6 : 0)) / 2 + size * this.cap.thought);
    const mirror = spec.mirror_word ? ws.findIndex(w => w.w === spec.mirror_word) : -1;
    const self = this;
    const width = Math.max(...lays.map(q => q.width));
    const zhY = y0 + lead2 * (lines.length - 1) + size * 0.3 + (zhb ? zhb.size * 1.3 : 0);
    const blk = {
      mode: 'THOUGHT', critical: true, zone, probe: !inMargin, line: spec.line, side: spec.side || 'left', zhBeneath: !!zhb,
      box: [x0, y0 - size * this.cap.thought - 6, width + 8, hText + size * 0.3 + (zhb ? zhb.size * 1.5 : 0) + 12],
      draw(c, col) {
        lines.forEach(([a, b], li) => {
          for (let k = a; k < b; k++) {
            const w = { ...ws[k], w: words[k] }, fo = F(w.t, fps); if (f < fo) continue;
            const df = f - fo, e = df >= 2 ? 1 : (df + 1) / 3;         // 3-frame fade, 4 px rise
            const x = x0 + lays[li].xs[k - a], y = y0 + li * lead2 + (1 - e) * 4;
            c.save(); c.globalAlpha = alpha * e;
            if (k === mirror) {                                         // S26: "backward," set mirrored
              const ww = lays[li].ws[k - a]; c.translate(x + ww / 2, 0); c.scale(-1, 1); c.translate(-(x + ww / 2), 0);
            }
            self.drawWord(c, 'thought', size, w, x, y, col, t, { popOn: false });
            c.restore();
          }
        });
        if (zhb) zhb.draw(c, col, x0, zhY, alpha);
      },
    };
    return blk;
  }

  // ------------------------------------------------------------------------------------------------ SUBTITLE
  _subSpan(line, E) {
    const tl = this.tl, fps = E.fps, l = tl.line(line), nx = tl.line(line + 1);
    const a = Math.max(F(l.start, fps) - 2, E.f0);
    let b = F(l.end, fps) + 6;
    if (nx) b = Math.min(b, Math.max(F(nx.start, fps) - 2, a + 1));
    return [a, Math.min(b, this._cut(line, E))];
  }
  _SUBTITLE(spec, E) {
    const { f, t } = E, tl = this.tl;
    const l = tl.line(spec.line); if (!l) return null;
    const [a, b] = this._subSpan(spec.line, E);
    if (f < a || f >= b) return null;
    const ws = lineWords(tl, spec.line, { extras: false });
    const words = ws.map(w => w.w);
    const size = 50, zsize = 46;
    const r = this.layoutRect(E, a), m = this.margins(r), mode = this.zhMode(E, a);
    const self = this;
    const drawRun = (c, col, idx, x, y, lay) => idx.forEach((k, j) => {
      const w = ws[k], st = wordState(w, t, this.fps);
      const colW = st.on ? mix(VOICE, col, st.active ? 0 : st.settle) : col;
      const segs = segments(w);
      this.font(c, 'sub', size); c.fillStyle = colW;
      if (segs.length > 1 && spec.parts) {                   // letters land on their parts; until then they wait at 22 %
        const xs = this.segX('sub', size, w.w, segs);
        segs.forEach((sg, q) => {
          const on = f >= F(sg.t, this.fps);
          c.globalAlpha = on ? 1 : 0.22; c.fillStyle = on ? colW : col;
          c.fillText(sg.s, x + lay.xs[j] + xs[q], y);
        });
        c.globalAlpha = 1;
      } else c.fillText(w.w, x + lay.xs[j], y);
    });
    if (mode === 'triptych') {        // the left margin, bottom-anchored, wrapped
      const colW = m.left[1] - m.left[0];
      const lines = this.wrap('sub', size, words, colW), lh = 62, yLast = 904;
      const lays = lines.map(([p, q]) => this.line('sub', size, words.slice(p, q)));
      const y0 = yLast - (lines.length - 1) * lh;
      const width = Math.max(...lays.map(q => q.width));
      return { mode: 'SUBTITLE', critical: true, zone: 'margin', line: spec.line, box: [L, y0 - 38, width, (lines.length - 1) * lh + 50],
        draw(c, col) { lines.forEach(([p, q], li) => drawRun(c, col, Array.from({ length: q - p }, (_, j) => p + j), L, y0 + li * lh, lays[li])); } };
    }
    const x = mode === 'column' ? r.x + 72 : L;
    const maxW = (mode === 'column' ? r.x + r.w - 72 : R) - x;
    let lines = [[0, words.length]];
    if (this.line('sub', size, words).width > maxW) lines = this.wrap('sub', size, words, maxW);
    const lh = 60, yEn = 880 - (lines.length - 1) * lh;
    const lays = lines.map(([p, q]) => this.line('sub', size, words.slice(p, q)));
    const zh = mode === 'beneath' && !this.zhOff(spec, E) ? zhSubtitle(zhLine(tl, spec.line)) : '';
    const width = Math.max(...lays.map(q => q.width), zh ? this.w('zhSans', zsize, zh) : 0);
    const hBox = 880 - yEn + 50 + (zh ? 56 : 0);
    return {
      mode: 'SUBTITLE', critical: true, zone: 'window', probe: true, line: spec.line, zhBeneath: !!zh, box: [x, yEn - 40, width, hBox],
      bandBox: [x - 28, yEn - 58, width + 56, hBox + 34],
      draw(c, col) {
        lines.forEach(([p, q], li) => drawRun(c, col, Array.from({ length: q - p }, (_, j) => p + j), x, yEn + li * lh, lays[li]));
        if (zh) { self.font(c, 'zhSans', zsize); c.fillStyle = col; c.fillText(zh, x, 936); }
      },
    };
  }

  // ------------------------------------------------------------------------------------------------ ZH (window spans)
  _ZH(spec, E) {
    if (E.card) return null;
    const { f } = E, tl = this.tl, l = tl.line(spec.line);
    if (!l) return null;
    // the ZH column lives as long as its EN partner in this shot (CARD: with the card; THOUGHT: dissolves with it)
    const partner = E.specs.find(s => s !== spec && s.line === spec.line && s.mode !== 'ZH');
    let a = Math.max(F(l.start, E.fps) - 2, E.f0), b = F(l.end, E.fps) + 6, alpha = 1;
    if (partner && partner.mode === 'CARD') b = E.f1;
    if (partner && partner.mode === 'SUBTITLE') [a, b] = this._subSpan(spec.line, E);
    b = Math.min(b, this._cut(spec.line, E));
    if (f < a || f >= b) return null;
    if (partner && partner.mode === 'THOUGHT' && f >= F(l.end, E.fps)) alpha = clamp01((F(l.end, E.fps) + 6 - f) / 7);
    const two = /2col/.test(spec.layout || '');
    return this._zhColumns(spec.line, E, a, { two, alpha });
  }
  _zhColumns(line, E, fOn, { two = false, alpha = 1 } = {}) {
    const r = this.layoutRect(E, fOn), m = this.margins(r);
    const z = zhLine(this.tl, line); if (!z) return null;
    const n = zhReveal(this.tl, line, E.t, { text: z }); if (!n) return null;
    const narrow = m.right[1] - m.right[0] < 280;
    const size = narrow ? 58 : 64, pitch = size * 1.14;
    const cps = [...z];
    const maxRows = Math.floor((1080 - 2 * TOP) / pitch);
    const rowsOf = s => verticalize(s).reduce((a, g) => a + (g.rotate ? (this.w('zhSerif', size * 0.9, g.ch) + size * 0.3) / pitch : 1), 0);
    let cols = [[0, cps.length]];
    if (!narrow && (two || rowsOf(z) > maxRows)) {
      let best = Math.ceil(cps.length / 2), bd = Infinity;
      cps.forEach((c, k) => { if (/[，。、？！]/.test(c) && Math.abs(k + 1 - cps.length / 2) < bd) { bd = Math.abs(k + 1 - cps.length / 2); best = k + 1; } });
      if (bd > 3) best = Math.ceil(cps.length / 2);
      cols = [[0, best], [best, cps.length]];
    }
    const xR = narrow ? (m.right[0] - GAP + 1920) / 2 : m.right[1] - size / 2;
    const dx = size * 1.7, self = this;
    const hMax = Math.max(...cols.map(([a, b]) => rowsOf(cps.slice(a, b).join('')))) * pitch;
    const x1 = xR + size / 2, x0 = xR - (cols.length - 1) * dx - size / 2;
    return {
      mode: 'ZH', critical: false, zone: 'margin', line, box: [x0, TOP - 6, x1 - x0, hMax + 12],
      draw(c, col) {
        c.globalAlpha = alpha;
        cols.forEach(([a, b], ci) => {
          const k = Math.min(b, n); if (k <= a) return;
          self.vertical(c, cps.slice(a, k).join(''), { x: xR - ci * dx, y: TOP - size * 0.06, size, pitch, role: 'zhSerif', color: col });
        });
      },
    };
  }
  // 4:3: the line being sung gets one column in the right margin (unless a spec already set ZH)
  _zhColumnAuto(E, blocks) {
    if (E.card || blocks.some(b => b.mode === 'ZH')) return null;
    const cands = blocks.filter(b => b.line !== undefined && b.mode !== 'QUESTION').map(b => b.line);
    if (!cands.length) return null;
    const line = Math.max(...cands);
    const spec = E.specs.find(s => s.line === line);
    if (spec && this.zhOff(spec, E)) return null;
    const l = this.tl.line(line), fOn = Math.max(F(l.start, E.fps) - 2, E.f0);
    if (blocks.some(b => b.line === line && b.zhBeneath)) return null;
    if (this.zhMode(E, Math.max(F(l.start, E.fps), E.f0)) !== 'column') return null;
    return this._zhColumns(line, E, fOn, {});
  }

  // vertical setting: one glyph per row centred on x from the em-box top y; Latin runs rotated 90 deg clockwise
  vertical(c, str, { x, y, size, pitch = size * 1.14, role = 'zhSerif', color = TYPE }) {
    this.font(c, role, size); c.fillStyle = color; c.textAlign = 'center'; c.textBaseline = 'middle';
    let yy = y;
    for (const g of verticalize(str)) {
      if (g.rotate) {
        const ls = size * 0.9; this.font(c, role, ls); c.textAlign = 'center'; c.textBaseline = 'middle';
        const w = this.w(role, ls, g.ch);
        c.save(); c.translate(x, yy + size * 0.12 + w / 2); c.rotate(Math.PI / 2); c.fillText(g.ch, 0, 0); c.restore();
        yy += w + size * 0.3;
        this.font(c, role, size); c.textAlign = 'center'; c.textBaseline = 'middle';
      } else { c.fillText(g.ch, x, yy + size * 0.5); yy += pitch; }
    }
    c.textAlign = 'left'; c.textBaseline = 'alphabetic';
    return yy - y;
  }

  // ------------------------------------------------------------------------------------------------ QUESTION
  _QUESTION(spec, E) {
    const { f, fps } = E;
    const on = F(spec.on, fps); if (f < on) return null;
    const en = spec.text_en, zh = spec.text_zh || '';
    const n = Math.min(en.length, f - on + 1);
    const fade = clamp01((E.f1 - f) / 8);                              // 8-frame fade into the cut
    const cap = 64, size = this.sizeForCap('question', cap), zs = size * 0.7;
    const r = E.rect, cx = r.x + r.w / 2, y = 800, yz = y + Math.round(zs * 1.45);
    const W = this.w('question', size, en), x0 = Math.round(cx - W / 2);
    const zcps = [...zh], zn = Math.ceil(zcps.length * n / en.length), ZW = this.w('zhSerifQ', zs, zh);
    const beat = this.tl.beatAt(E.t), self = this;
    return {
      mode: 'QUESTION', critical: true, zone: 'window', probe: !spec.ink, forceInk: !!spec.ink,
      box: [Math.min(x0, cx - ZW / 2), y - cap - 8, Math.max(W, ZW) + 30, yz - y + cap + 24],
      draw(c, col) {
        c.globalAlpha = fade;
        self.font(c, 'question', size); c.fillStyle = col; c.fillText(en.slice(0, n), x0, y);
        if (n < en.length || beat.phase < 0.5) { const x = x0 + self.w('question', size, en.slice(0, n)) + size * 0.06; c.fillRect(x, y - cap, size * 0.42, cap); }
        if (zn) { self.font(c, 'zhSerifQ', zs); c.fillText(zcps.slice(0, zn).join(''), Math.round(cx - ZW / 2), yz); }
      },
    };
  }

  // ------------------------------------------------------------------------------------------------ MONO (S29, S57)
  _MONO(spec, E) {
    const { f, fps } = E;
    const ons = (spec.on || []).map(x => F(x, fps));
    const first = ons[0] ?? E.f0; if (f < first) return null;
    const card = E.card;
    const cap = card ? 34 : 28, size = this.sizeForCap('mono', cap), track = card ? size * 0.12 : 0;
    const lines = spec.lines_en;
    const r = E.rect;
    const at = spec.at || (card ? [960, 470] : [r.x + r.w * 0.58, 470]);
    const lh = Math.round(cap * 2.1);
    // S29: line 1 types on C, line 2 on D, and its result (after the arrow) lands on R (the third letter part)
    const parts = this.tl.words.find(w => w.w === 'CDR');
    const resultF = !card && parts && parts.parts ? F(parts.parts[2], fps) : null;
    const self = this;
    const W = Math.max(...lines.map(s => this.w('mono', size, s) + track * s.length));
    return {
      mode: 'MONO', critical: true, zone: card ? 'card' : 'window', probe: !card,
      box: card ? [at[0] - W / 2, at[1] - cap - 6, W, cap + 16] : [at[0], at[1] - cap - 6, W, lh * (lines.length - 1) + cap + 16],
      draw(c, col) {
        lines.forEach((s, i) => {
          const o = ons[i] ?? first; if (f < o) return;
          let shown = s, voice = null;
          const arrow = s.indexOf('→');
          const rate = 2;                                               // HUD / mono typing: 2 chars per frame
          if (resultF !== null && i === lines.length - 1 && arrow > 0) {
            const head = s.slice(0, arrow + 2), tail = s.slice(arrow + 2);
            shown = head.slice(0, Math.min(head.length, (f - o + 1) * rate));
            if (f >= resultF) { shown = head; voice = { str: tail, df: f - resultF }; }
          } else shown = s.slice(0, Math.min(s.length, (f - o + 1) * rate));
          self.font(c, 'mono', size); c.letterSpacing = `${track}px`; c.fillStyle = col;
          const full = self.w('mono', size, s) + track * s.length;
          const x = card ? at[0] - full / 2 : at[0], y = at[1] + i * lh;
          c.fillText(shown, x, y);
          if (voice) {
            const sx = x + self.w('mono', size, shown) + track * shown.length;
            c.fillStyle = mix(VOICE, col, clamp01((voice.df - 6) / 8)); c.fillText(voice.str, sx, y);
          }
          const typing = shown.length < (voice ? shown.length : s.length);
          if (typing) { c.fillStyle = col; c.fillRect(x + self.w('mono', size, shown) + track * shown.length + 2, y - cap, size * 0.56, cap); }
        });
      },
    };
  }

  // S57: the approval box; the grease pencil ticks the first box at `on`
  _APPROVAL(spec, E) {
    const { f, fps } = E;
    const tick = F(spec.on, fps), appear = tick - 8;
    if (f < appear) return null;
    const size = 32, box = 30, gap = 76, track = size * 0.08;
    const labels = spec.boxes;
    const widths = labels.map(s => box + 18 + this.w('monoR', size, s) + track * s.length);
    const total = widths.reduce((a, b) => a + b, 0) + gap * (labels.length - 1);
    const y = 600, x0 = Math.round(960 - total / 2);
    const k = spec.boxes.indexOf(spec.tick);
    const typed = Math.min(1, (f - appear + 1) / 6);
    const self = this, pencil = this.ctx.pencil;
    return {
      mode: 'APPROVAL', critical: true, zone: 'card', box: [x0, y - box - 4, total, box + 12],
      draw(c, col) {
        let x = x0;
        labels.forEach((s, i) => {
          c.globalAlpha = 1; c.strokeStyle = col; c.lineWidth = 1.5; c.strokeRect(x + 0.75, y - box + 0.75 + 2, box - 1.5, box - 1.5);
          self.font(c, 'monoR', size); c.letterSpacing = `${track}px`; c.fillStyle = col;
          const n = Math.round(s.length * typed); c.fillText(s.slice(0, n), x + box + 18, y);
          if (i === k && pencil && f >= tick) {
            const pts = pencil.shape('tick', { x: x + box * 0.46, y: y - box * 0.3, size: box * 2.1, seed: 57 });
            pencil.draw(c, pts, E.t, { t0: tick / fps, dur: 0.22, width: 7.5, seed: 57 });
          }
          x += widths[i] + gap;
        });
      },
    };
  }

  _TITLE(spec, E) {
    const { f, fps } = E;
    const on = F(spec.on, fps); if (f < on) return null;
    const a = clamp01((f - on + 1) / 6);
    const parts = spec.text.split(' · ');
    const zs = 46, es = this.sizeForCap('mono', 17), track = es * 0.18;
    const zw = this.w('title', zs, parts[0]), dot = '  ·  ', ew = this.w('mono', es, (parts[1] || '')) + track * (parts[1] || '').length;
    const dw = this.w('mono', es, dot) + track * dot.length;
    const total = zw + dw + ew, x0 = 960 - total / 2, y = 890;
    const self = this;
    return {
      mode: 'TITLE', critical: true, zone: 'card', box: [x0, y - zs, total, zs + 12],
      draw(c, col) {
        c.globalAlpha = a;
        self.font(c, 'title', zs); c.fillStyle = col; c.fillText(parts[0], x0, y);
        self.font(c, 'mono', es); c.letterSpacing = `${track}px`; c.fillText(dot + (parts[1] || ''), x0 + zw, y - 2);
      },
    };
  }

  // ------------------------------------------------------------------------------------------------ contrast lane
  _contrast(b, probe, E) {
    b.ink = false; b.band = false;
    if (b.forceInk) { b.ink = true; b.contrast = 16.5; return; }
    if (b.zone === 'margin' || b.zone === 'card' || !b.probe) {
      const bg = b.zone === 'window' && /WHITE|STUDIO/.test(E.register) && !probe ? 0.9 : 0.04;
      b.ink = bg > 0.5; b.contrast = contrastOn(b.ink ? INK_TYPE : TYPE, bg); return;
    }
    if (!probe) { b.ink = /WHITE/.test(E.register); b.contrast = null; return; }
    let [x, y, w, h] = b.box;
    let p = probe(x, y, w, h);
    if (b.mode === 'THOUGHT' && p.mean > 0.45 && b.side !== 'right') {   // move THOUGHT to the darker side
      const rr = E.rect, mx = rr.x + rr.w - (x - rr.x) - w;
      const q = probe(mx, y, w, h);
      if (q.mean < p.mean - 0.1) { const dx = mx - x; const d0 = b.draw; b.draw = (c, col) => { c.translate(dx, 0); d0(c, col); }; b.box = [mx, y, w, h]; p = q; }
    }
    const cT = contrastOn(TYPE, p.mean), cI = contrastOn(INK_TYPE, p.mean);
    const target = b.mode === 'CARD' ? 3 : 4.5;
    b.luma = p;
    if ((b.mode === 'SUBTITLE' || b.mode === 'THOUGHT' || b.mode === 'MONO') && p.std > (b.mode === 'SUBTITLE' ? 0.15 : 0.2)) {
      // mixed box: TYPE on a soft INK band (70 %)
      b.band = true; b.ink = false; b.contrast = contrastOn(TYPE, Math.min(p.mean, 0.3) * 0.3 + 0.02); return;
    }
    b.ink = p.mean > 0.6 || cI > cT * 1.15;
    b.contrast = b.ink ? cI : cT;
    if (b.mode === 'CARD' && !b.ink && cT < target && b.dim > 0) {
      // a card over a bright or mixed image: dim further (up to 3 stops) until TYPE holds 3:1 on the bright parts
      const need = Math.min(3, Math.max(1, 2.2 * Math.log2((p.mean + p.std) / 0.45)));
      b.dim *= need; b.contrast = contrastOn(TYPE, Math.min(1, (p.mean + p.std)) * Math.pow(2, -need / 2.2));
    }
    if (b.mode === 'SUBTITLE' && !b.ink && b.contrast < target) { b.band = true; b.contrast = contrastOn(TYPE, p.mean * 0.3); }
  }
}

// the layout name of a CARD spec without its prose ("center-large (plate dimmed 1 stop)" -> "center-large")
function layoutKey(spec, card) { const m = /^[\w-]+/.exec(spec.layout || ''); return m ? m[0] : (card ? 'stop-card' : 'center-large'); }
function splitRows(ws, breakBefore) {
  const rows = [[]];
  for (const w of ws) { if (rows[rows.length - 1].length && breakBefore.includes(w.w.replace(/[^\p{L}]/gu, '').toLowerCase())) rows.push([]); rows[rows.length - 1].push(w); }
  return rows;
}
function safeBox([x, y, w, h]) {
  if (x < SAFE.x0 - 0.5 || y < SAFE.y0 - 0.5 || x + w > SAFE.x1 + 0.5 || y + h > SAFE.y1 + 0.5) return false;
  for (const [ox, oy, ow, oh] of SAFE.overlays) if (x < ox + ow && x + w > ox && y < oy + oh && y + h > oy) return false;
  return true;
}
// the contrast lane's soft INK band (70 %, feathered): a blurred shadow of an off-canvas rect
function drawBand(c, [x, y, w, h]) {
  c.save();
  const off = 4000, feather = 26;
  c.shadowColor = 'rgba(10,10,9,0.7)'; c.shadowBlur = feather; c.shadowOffsetX = off; c.shadowOffsetY = 0;
  const m = c.getTransform(); c.shadowOffsetX = off * m.a;
  c.fillStyle = '#000'; c.fillRect(x - off + feather / 2, y + feather / 2, w - feather, h - feather);
  c.restore();
}
