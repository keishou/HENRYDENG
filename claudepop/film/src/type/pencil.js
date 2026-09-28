// pencil.js - the grease pencil (BIBLE 6.1, 7; lane B): the machine's hand, choosing, keeping, approving. Not a font:
// animated strokes of a china marker in VOICE, with a waxy, broken edge (the wax skips on the paper tooth), pressure
// that swells in and lifts off, and a hand's speed profile (slow start, fast middle, slow finish). Drawn onto any 2D
// context (the HUD canvas via hud.ctx in design px, or a print's texture canvas in its own px), so the same mark works
// in screen space and on paper. Pure function of (points, t, options): no state, seeded texture.
//
//   const pencil = new Pencil(ctx)
//   pencil.shape(kind, params) -> points [[x, y], ...]
//        'circle' { cx, cy, r, rx = r, ry = r, start = -0.4 (rad), overshoot = 0.18, wobble = 0.02, tilt = 0, seed }
//                  a hand-drawn loop: slightly elliptical, drifting radius, the end overshoots past the start
//        'tick'   { x, y, size, seed }   (x, y = the tick's elbow)       'cross' { x, y, size, seed } (two strokes)
//        'line'   { x0, y0, x1, y1, bow = 0.015, seed }                   'crop' { x, y, w, h, arm = 40 } (4 L marks)
//        'path'   { points } any polyline
//        Multi-stroke shapes (cross, crop) return an array of strokes: [[x, y]...][]; draw() takes either.
//   pencil.draw(g2d, pointsOrStrokes, t, { t0 = 0, dur = 0.5, width = 6, color = VOICE, alpha = 1, seed = 0,
//        gap = 0.06 (s between the strokes of a multi-stroke mark) })
//        draws the part of the mark revealed at time t (nothing before t0, complete after t0 + dur)
//   pencil.lengthOf(points) -> arc length
export const VOICE = '#D97757';
const TAU = Math.PI * 2;

// deterministic hash / value noise (independent of core/rng so a print texture canvas can use the pencil in a worker)
function h32(a, b = 0) { let h = Math.imul(a | 0, 0x9E3779B1) ^ Math.imul(b | 0, 0x85EBCA77); h ^= h >>> 15; h = Math.imul(h, 0x2C1B3C6D); h ^= h >>> 12; h = Math.imul(h, 0x297A2D39); h ^= h >>> 15; return (h >>> 0) / 4294967296; }
function vnoise(x, seed) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return (h32(i, seed) * (1 - u) + h32(i + 1, seed) * u) * 2 - 1; }
const clamp01 = x => Math.max(0, Math.min(1, x));
// the hand's speed: progress along the stroke for normalised time k (ease in-out, slightly front-loaded)
const handEase = k => { k = clamp01(k); return k < 0.5 ? 2 * k * k * (1.35 - 0.35 * k * 2) / 1.0 : 1 - Math.pow(-2 * k + 2, 2.2) / 2; };

export class Pencil {
  constructor(ctx) { this.ctx = ctx; }

  shape(kind, p = {}) {
    const seed = p.seed ?? 1;
    if (kind === 'circle') {
      const { cx, cy, r = 40, rx = r, ry = r, start = -0.4, overshoot = 0.18, wobble = 0.02, tilt = 0 } = p;
      const n = 96, span = TAU * (1 + overshoot), pts = [];
      const ct = Math.cos(tilt), st = Math.sin(tilt);
      for (let i = 0; i <= n; i++) {
        const u = i / n, a = start + span * u;
        // the radius drifts (the loop does not close on itself) and wobbles with the hand
        const dr = 1 + wobble * vnoise(u * 5, seed) + 0.035 * (u - 0.5) + 0.02 * Math.sin(a * 2 + seed);
        const x = Math.cos(a) * rx * dr, y = Math.sin(a) * ry * dr;
        pts.push([cx + x * ct - y * st, cy + x * st + y * ct]);
      }
      return pts;
    }
    if (kind === 'tick') {
      const { x, y, size = 30 } = p;                 // short down-stroke into the elbow, long flick up and right
      const a = [x - size * 0.34, y - size * 0.2], b = [x, y + size * 0.02], c = [x + size * 0.62, y - size * 0.6];
      const pts = [];
      for (let i = 0; i <= 10; i++) { const u = i / 10; pts.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u + Math.sin(u * Math.PI) * size * 0.03]); }
      for (let i = 1; i <= 22; i++) { const u = i / 22; pts.push([b[0] + (c[0] - b[0]) * u - Math.sin(u * Math.PI) * size * 0.05, b[1] + (c[1] - b[1]) * u + Math.sin(u * Math.PI) * size * 0.02]); }
      return pts;
    }
    if (kind === 'cross') {
      const { x, y, size = 30 } = p, s = size / 2;
      return [this.shape('line', { x0: x - s, y0: y - s, x1: x + s, y1: y + s, seed }), this.shape('line', { x0: x + s * 0.95, y0: y - s * 1.05, x1: x - s * 1.02, y1: y + s * 0.92, seed: seed + 1 })];
    }
    if (kind === 'line') {
      const { x0, y0, x1, y1, bow = 0.015 } = p, L = Math.hypot(x1 - x0, y1 - y0), nx = -(y1 - y0) / (L || 1), ny = (x1 - x0) / (L || 1);
      const pts = [], n = Math.max(8, Math.round(L / 6));
      for (let i = 0; i <= n; i++) { const u = i / n, b = Math.sin(u * Math.PI) * bow * L * (h32(seed, 3) > 0.5 ? 1 : -1) + vnoise(u * 3, seed) * L * 0.004; pts.push([x0 + (x1 - x0) * u + nx * b, y0 + (y1 - y0) * u + ny * b]); }
      return pts;
    }
    if (kind === 'crop') {
      const { x, y, w, h, arm = 40 } = p;
      const L = (ax, ay, bx, by, cx, cy, s) => [...this.shape('line', { x0: ax, y0: ay, x1: bx, y1: by, bow: 0.01, seed: s }), ...this.shape('line', { x0: bx, y0: by, x1: cx, y1: cy, bow: 0.01, seed: s + 1 }).slice(1)];
      return [L(x, y + arm, x, y, x + arm, y, seed), L(x + w - arm, y, x + w, y, x + w, y + arm, seed + 2),
        L(x + w, y + h - arm, x + w, y + h, x + w - arm, y + h, seed + 4), L(x + arm, y + h, x, y + h, x, y + h - arm, seed + 6)];
    }
    if (kind === 'path') return (p.points || []).map(q => [q[0], q[1]]);
    return [];
  }

  lengthOf(pts) { let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }

  draw(g, pts, t, { t0 = 0, dur = 0.5, width = 6, color = VOICE, alpha = 1, seed = 0, gap = 0.06 } = {}) {
    if (!pts || !pts.length || t < t0) return;
    const strokes = Array.isArray(pts[0][0]) ? pts : [pts];
    const lens = strokes.map(s => this.lengthOf(s)), total = lens.reduce((a, b) => a + b, 0) || 1;
    const drawT = Math.max(0.01, dur - gap * (strokes.length - 1));
    let ts = t0;
    strokes.forEach((s, i) => {
      const d = drawT * lens[i] / total;
      if (t >= ts) this._stroke(g, s, clamp01((t - ts) / d), { width, color, alpha, seed: seed * 31 + i });
      ts += d + gap;
    });
  }

  // one stroke: the centreline resampled every ~0.8 output px; across it, n wax streaks (the marker's width split into
  // strands) deposit where the paper tooth (a fixed per-pixel texture in paper space) lets them - the edges catch less
  // wax than the middle and light pressure less than firm, which gives the broken, waxy edge
  _stroke(g, pts, k, { width, color, alpha, seed }) {
    if (k <= 0 || pts.length < 2) return;
    const cum = [0]; for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const L = cum[cum.length - 1]; if (L <= 0) return;
    const shown = L * handEase(k);
    const tr = g.getTransform(), scale = Math.max(0.1, Math.hypot(tr.a, tr.b));
    const step = 0.8 / scale, px1 = 1 / scale;
    const n = Math.max(3, Math.min(11, Math.round(width * scale / 1.1)));
    const dot = Math.max(px1 * 1.1, width / n * 1.35);
    g.save(); g.fillStyle = color;
    let j = 0;
    for (let s = 0; s <= shown; s += step) {
      while (j < pts.length - 2 && cum[j + 1] < s) j++;
      const u = (s - cum[j]) / Math.max(1e-6, cum[j + 1] - cum[j]);
      const x = pts[j][0] + (pts[j + 1][0] - pts[j][0]) * u, y = pts[j][1] + (pts[j + 1][1] - pts[j][1]) * u;
      const dx = pts[j + 1][0] - pts[j][0], dy = pts[j + 1][1] - pts[j][1], dl = Math.hypot(dx, dy) || 1;
      const nx = -dy / dl, ny = dx / dl, q = s / L;
      // pressure: lands firm, swells, lifts off thin at the end (and tapers at the live tip while drawing)
      let pr = Math.min(1, 0.5 + q * 7) * Math.min(1, (1 - q) * 6 + 0.3);
      if (k < 1) pr *= Math.min(1, (shown - s) / (width * 2) + 0.5);
      const w = width * pr * (1 + 0.14 * vnoise(s * 0.3, seed) + 0.07 * vnoise(s * 1.9, seed + 9));
      const drift = 0.1 * width * vnoise(s * 0.45, seed + 3);
      for (let i = 0; i < n; i++) {
        const v = (i + 0.5) / n - 0.5, edge = Math.abs(v) * 2;
        const X = x + nx * (v * w + drift), Y = y + ny * (v * w + drift);
        const tooth = h32(Math.round(X * scale * 0.9), Math.round(Y * scale * 0.9) ^ (seed * 7919));
        if (tooth > (0.97 - 0.6 * edge * edge) * (0.55 + 0.45 * pr)) continue;
        g.globalAlpha = alpha * (0.62 + 0.38 * h32(i + 31 * Math.round(s * scale), seed + 5));
        g.fillRect(X - dot / 2, Y - dot / 2, dot, dot);
      }
    }
    g.restore();
  }
}
