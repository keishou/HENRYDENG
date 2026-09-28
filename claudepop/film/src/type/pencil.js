// STUB - owned by lane B, replace. (Frozen on day 0 by lane A: keep the class, constructor, shape() and draw()
// signatures; lane D draws the S13 circle, S45 ticks, S49 branch and S57 tick through it.)
//
// pencil.js - the grease pencil (BIBLE 6.1, 7): the machine's hand. Not a font: animated strokes with a waxy edge in
// VOICE. Drawn onto any 2D canvas context (the HUD canvas via hud.ctx, or a print's texture canvas), so the same mark
// works in screen space and on paper. Pure function of t.
//
//   const pencil = new Pencil(ctx)
//   pencil.shape(kind, params) -> points [[x, y], ...]
//        kind 'circle' { cx, cy, r, rx?, ry?, start = -0.4 (rad), overshoot = 0.18, wobble = 0.02, seed }
//             'tick'   { x, y, size }        'cross' { x, y, size }      'line' { x0, y0, x1, y1 }
//             'crop'   { x, y, w, h, arm }   (four corner crop marks, S42)
//   pencil.draw(g2d, points, t, { t0, dur = 0.5, width = 6, color = VOICE, alpha = 1, seed = 0 })
//        draws the part of the stroke revealed at time t (0 before t0, complete after t0 + dur; ease-out speed)
export const VOICE = '#D97757';

export class Pencil {
  constructor(ctx) { this.ctx = ctx; }
  shape(kind, p = {}) {
    const pts = [];
    if (kind === 'circle') {
      const { cx, cy, r = 40, rx = r, ry = r, start = -0.4, overshoot = 0.18 } = p;
      const n = 64, span = Math.PI * 2 * (1 + overshoot);
      for (let i = 0; i <= n; i++) { const a = start + span * i / n; pts.push([cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]); }
    } else if (kind === 'tick') {
      const { x, y, size = 30 } = p; pts.push([x - size * 0.5, y - size * 0.1], [x - size * 0.15, y + size * 0.35], [x + size * 0.55, y - size * 0.55]);
    } else if (kind === 'cross') {
      const { x, y, size = 30 } = p; pts.push([x - size / 2, y - size / 2], [x + size / 2, y + size / 2]);
    } else if (kind === 'line') {
      pts.push([p.x0, p.y0], [p.x1, p.y1]);
    } else if (kind === 'crop') {
      const { x, y, w, h, arm = 40 } = p; pts.push([x, y + arm], [x, y], [x + arm, y]);
    }
    return pts;
  }
  draw(g, pts, t, { t0 = 0, dur = 0.5, width = 6, color = VOICE, alpha = 1 } = {}) {
    if (t < t0 || pts.length < 2) return;
    const k = Math.min(1, (t - t0) / dur), e = 1 - (1 - k) ** 2;
    const lens = [0]; for (let i = 1; i < pts.length; i++) lens.push(lens[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const L = lens[lens.length - 1] * e;
    g.save(); g.globalAlpha = alpha; g.strokeStyle = color; g.lineWidth = width; g.lineCap = 'round'; g.lineJoin = 'round';
    g.beginPath(); g.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) {
      if (lens[i] <= L) g.lineTo(pts[i][0], pts[i][1]);
      else { const u = (L - lens[i - 1]) / (lens[i] - lens[i - 1] || 1); g.lineTo(pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * u, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * u); break; }
    }
    g.stroke(); g.restore();
  }
}
