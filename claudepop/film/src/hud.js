// hud.js - the type / HUD layer: a 2D canvas drawn in a 1920x1080 design space (scaled to any output size), composited
// by post.js after the grade. Every draw call is a pure function of its arguments and the film time t (tickers,
// counters, waveforms), so frames render identically in any order.
//
//   await loadFonts(base = '/fonts/')  Inter Tight (grotesque), IBM Plex Mono (HUD labels), Barlow Condensed (display
//                                      numerals), Instrument Serif (subtitle / italic titles); all SIL OFL (look-dev
//                                      faces; the film's own faces load in src/type/type.js). Falls back to /out/fonts/
// The film's proof-sheet HUD is src/hud/proof.js; these primitives serve the look-dev harness and scenes' overlays.
//   const hud = new Hud(W, H); hud.clear();
//   hud.mono(text, x, y, o)            tiny letter-spaced monospace label   o: {size, color, alpha, align, track, weight}
//   hud.text(runs, x, y, o)            one line of mixed-colour runs: [['I\'m upping my ', '#fff'], ['P(doom).', ORANGE]]
//   hud.rule(x0, y0, x1, y1, o)        hairline           hud.cross(x, y, s)     corner crosshair
//   hud.brackets(x, y, w, h, o)        corner brackets (tracking frame)     hud.ruler(x, y0, y1, t, o) frame ruler
//   hud.ticker(items, y, t, o)         bottom news ticker, scrolls with t    hud.wave(x, y, w, h, t)   mini waveform
//   hud.counter(x, y, str, label, o)   boxed accent digits                   hud.card(x, y, w, rows, o) receipt card
//   hud.subtitle(text, y, o)           centred serif subtitle
//   hud.pixels()                       RGBA bytes for upload (post.js takes the Hud itself: post.render(..., hud))
export const ORANGE = '#D97757';
export const FONTS = {
  sans: '"Inter Tight", "Helvetica Neue", Arial, sans-serif',
  mono: '"IBM Plex Mono", "DejaVu Sans Mono", monospace',
  cond: '"Barlow Condensed", "Arial Narrow", sans-serif',
  serif: '"Instrument Serif", Georgia, serif',
};

export async function loadFonts(base = '/fonts/') {
  const list = [
    ['Inter Tight', 'InterTight.ttf', { weight: '100 900' }],
    ['IBM Plex Mono', 'IBMPlexMono-Regular.ttf', { weight: '400' }],
    ['IBM Plex Mono', 'IBMPlexMono-Medium.ttf', { weight: '500' }],
    ['Barlow Condensed', 'BarlowCondensed-Medium.ttf', { weight: '500' }],
    ['Barlow Condensed', 'BarlowCondensed-SemiBold.ttf', { weight: '600' }],
    ['Instrument Serif', 'InstrumentSerif-Regular.ttf', { style: 'normal' }],
    ['Instrument Serif', 'InstrumentSerif-Italic.ttf', { style: 'italic' }],
  ];
  // each file from `base`, falling back to the other font folder (claudepop/fonts/ from film/fetch_fonts.sh, or the
  // legacy claudepop/out/fonts/)
  const bases = [...new Set([base, '/fonts/', '/out/fonts/'])];
  await Promise.all(list.map(async ([fam, file, desc]) => {
    for (const b of bases) {
      try { const f = new FontFace(fam, `url(${b}${file})`, desc); await f.load(); document.fonts.add(f); return; } catch {}
    }
    console.warn('hud.js: font not found', file);
  }));
  await document.fonts.ready;
}

export class Hud {
  constructor(W, H) {
    this.canvas = document.createElement('canvas');
    this.canvas.width = W; this.canvas.height = H;
    this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });   // CPU-backed: cheap texture upload under SwiftShader
    this.W = W; this.H = H; this.s = W / 1920;
    this.shadows = true;   // soft dark halo under type and hairlines (legible on bright plates); costs ~CPU blur per call
  }
  // straight-alpha RGBA bytes, top row first (getImageData on a CPU-backed canvas: ~3 ms at 720p). Uploading these as a
  // DataTexture is ~4x cheaper under SwiftShader than a CanvasTexture (which goes through a colour-converting path).
  pixels() { return this.ctx.getImageData(0, 0, this.W, this.H).data; }
  clear() {
    const c = this.ctx;
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.clearRect(0, 0, this.W, this.H);
    c.setTransform(this.s, 0, 0, this.s, 0, 0);
    c.textBaseline = 'alphabetic';
    return this;
  }
  _font(fam, size, weight = 400, style = 'normal') { this.ctx.font = `${style} ${weight} ${size}px ${FONTS[fam] || fam}`; }
  mono(text, x, y, { size = 13, color = '#e8ecf2', alpha = 0.85, align = 'left', track = 1.6, weight = 400 } = {}) {
    const c = this.ctx; this._font('mono', size, weight);
    c.letterSpacing = `${track}px`; c.fillStyle = color; c.globalAlpha = alpha; c.textAlign = align;
    c.shadowColor = 'rgba(0,0,0,0.45)'; c.shadowBlur = this.shadows ? 3 : 0;
    c.fillText(text, x, y); c.shadowBlur = 0; c.globalAlpha = 1; c.letterSpacing = '0px';
    return c.measureText(text).width + track * text.length;
  }
  text(runs, x, y, { fam = 'sans', size = 64, weight = 600, style = 'normal', track = -1, alpha = 1, align = 'left' } = {}) {
    const c = this.ctx; this._font(fam, size, weight, style);
    c.letterSpacing = `${track}px`; c.textAlign = 'left'; c.globalAlpha = alpha;
    const widths = runs.map(([s]) => c.measureText(s).width);
    const total = widths.reduce((a, b) => a + b, 0);
    let cx = align === 'center' ? x - total / 2 : align === 'right' ? x - total : x;
    runs.forEach(([s, col, a = 1], i) => { c.globalAlpha = alpha * a; c.fillStyle = col; c.fillText(s, cx, y); cx += widths[i]; });
    c.globalAlpha = 1; c.letterSpacing = '0px';
    return total;
  }
  rule(x0, y0, x1, y1, { color = '#e8ecf2', alpha = 0.55, width = 1 } = {}) {
    const c = this.ctx; c.strokeStyle = color; c.globalAlpha = alpha; c.lineWidth = width;
    c.shadowColor = 'rgba(0,0,0,0.5)'; c.shadowBlur = this.shadows ? 2 : 0;
    c.beginPath(); c.moveTo(x0, y0); c.lineTo(x1, y1); c.stroke(); c.globalAlpha = 1; c.shadowBlur = 0;
  }
  cross(x, y, s = 9, o = {}) { this.rule(x - s, y, x + s, y, o); this.rule(x, y - s, x, y + s, o); }
  brackets(x, y, w, h, { len = 22, color = '#e8ecf2', alpha = 0.8, width = 1.2 } = {}) {
    const c = this.ctx; c.strokeStyle = color; c.globalAlpha = alpha; c.lineWidth = width; c.beginPath();
    c.shadowColor = 'rgba(0,0,0,0.55)'; c.shadowBlur = this.shadows ? 3 : 0;
    for (const [px, py, dx, dy] of [[x, y, 1, 1], [x + w, y, -1, 1], [x, y + h, 1, -1], [x + w, y + h, -1, -1]]) {
      c.moveTo(px + dx * len, py); c.lineTo(px, py); c.lineTo(px, py + dy * len);
    }
    c.stroke(); c.globalAlpha = 1; c.shadowBlur = 0;
  }
  ruler(x, y0, y1, t, { step = 18, every = 5, color = '#e8ecf2', alpha = 0.45, fps = 24 } = {}) {
    const f0 = Math.floor(t * fps);
    for (let y = y0, k = 0; y <= y1; y += step, k++) {
      const major = (k % every) === 0;
      this.rule(x, y, x + (major ? 14 : 7), y, { color, alpha });
      if (major) this.mono(String(f0 + k).padStart(3, '0').slice(-3), x + 20, y + 4, { size: 10, alpha: alpha * 1.2 });
    }
  }
  ticker(items, y, t, { size = 14, speed = 70, color = '#e8ecf2', alpha = 0.8, sep = '   ✱   ', accent = ORANGE } = {}) {
    const c = this.ctx; this._font('mono', size); c.letterSpacing = '2px'; c.textAlign = 'left';
    const parts = items.flatMap(s => [[s, color], [sep, accent]]);
    const widths = parts.map(([s]) => c.measureText(s).width + 2 * s.length);
    const total = widths.reduce((a, b) => a + b, 0);
    let x = -((t * speed) % total);
    c.globalAlpha = alpha;
    while (x < 1920) {
      parts.forEach(([s, col], i) => { if (x + widths[i] > 0 && x < 1920) { c.fillStyle = col; c.fillText(s, x, y); } x += widths[i]; });
    }
    c.globalAlpha = 1; c.letterSpacing = '0px';
  }
  wave(x, y, w, h, t, { bars = 36, color = '#e8ecf2', alpha = 0.7, seed = 3 } = {}) {
    const c = this.ctx; c.fillStyle = color; c.globalAlpha = alpha;
    const bw = w / bars;
    for (let i = 0; i < bars; i++) {
      const v = 0.25 + 0.75 * Math.abs(Math.sin(i * 1.7 + seed + t * 5.3) * Math.sin(i * 0.37 + t * 2.1 + seed * 2.0));
      c.fillRect(x + i * bw, y - v * h, Math.max(1, bw * 0.45), v * h);
    }
    c.globalAlpha = 1;
  }
  counter(x, y, str, label, { size = 44, color = ORANGE, box = true } = {}) {
    const c = this.ctx; this._font('cond', size, 500); c.textAlign = 'left';
    let cx = x;
    for (const ch of str) {
      const w = ch === '.' ? size * 0.28 : size * 0.62;
      if (box && ch !== '.') { c.fillStyle = 'rgba(20,22,26,0.55)'; c.fillRect(cx - 3, y - size * 0.82, w + 2, size * 0.98); }
      c.fillStyle = color; c.fillText(ch, cx + (ch === '.' ? 0 : w * 0.08), y); cx += w + 4;
    }
    if (label) label.forEach((l, i) => this.mono(l, cx + 10, y - size * 0.5 + i * 17, { size: 12, track: 2.5, alpha: 0.85 }));
    return cx;
  }
  card(x, y, w, rows, { title = '', tag = '', bg = '#ecebe6', ink = '#15171a' } = {}) {
    const c = this.ctx, rh = 21, h = 70 + rows.length * rh + 46;
    c.fillStyle = bg; c.globalAlpha = 0.96; c.fillRect(x, y, w, h); c.globalAlpha = 1;
    this.mono(rows.head || 'LOOK 03 / 11', x + 12, y + 20, { size: 10, color: ink, alpha: 0.9 });
    if (tag) { c.fillStyle = ORANGE; const tw = this.ctx.measureText(tag).width + 16; c.fillRect(x + w - tw - 10, y + 9, tw, 16); this.mono(tag, x + w - tw - 2, y + 21, { size: 10, color: '#fff', alpha: 1 }); }
    this._font('cond', 26, 600); c.fillStyle = ink; c.textAlign = 'left'; c.fillText(title, x + 12, y + 52);
    this.rule(x + 12, y + 62, x + w - 12, y + 62, { color: ink, alpha: 0.5 });
    rows.forEach(([k, v], i) => {
      const yy = y + 82 + i * rh;
      this.mono(k, x + 12, yy, { size: 11, color: ink, alpha: 0.85 });
      this.mono(v, x + w - 12, yy, { size: 11, color: ink, alpha: 0.85, align: 'right' });
      this.rule(x + 12, yy + 7, x + w - 12, yy + 7, { color: ink, alpha: 0.12 });
    });
    const by = y + h - 36;   // barcode (deterministic from the title)
    let bx = x + w - 150, seed = [...title].reduce((a, ch) => a * 31 + ch.charCodeAt(0), 7) >>> 0;
    c.fillStyle = ink;
    while (bx < x + w - 14) { seed = (seed * 1103515245 + 12345) >>> 0; const bw = 1 + (seed >>> 28) % 3; c.fillRect(bx, by, bw, 22); bx += bw + 1 + ((seed >>> 24) & 1); }
    this.mono('△ ○ □ ✕', x + 12, by + 16, { size: 13, color: ink, alpha: 0.8 });
  }
  subtitle(text, y, { size = 34, color = '#f2efe9', alpha = 0.92, italic = true, align = 'center', x = 960 } = {}) {
    const c = this.ctx; this._font('serif', size, 400, italic ? 'italic' : 'normal');
    c.textAlign = align; c.fillStyle = color; c.globalAlpha = alpha;
    c.shadowColor = 'rgba(0,0,0,0.5)'; c.shadowBlur = this.shadows ? 8 : 0;
    c.fillText(text, x, y); c.shadowBlur = 0; c.globalAlpha = 1;
  }
}
