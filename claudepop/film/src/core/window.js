// window.js - the picture window (BIBLE 4.4): a centred rect whose shape says how much of the frame is evidence.
// Outside it is INK. Everything is in the 1920x1080 design space; multiply by ctx.k for output pixels.
//
//   const win = new WindowTrack(shotsDoc)
//   win.rect(t, shot?) -> { x, y, w, h, shape, full, k, from }   the window at film time t (t = f / 24)
//       shape: the target shape string ('7:9' | '1:1' | '4:3' | '16:9'); k: 0..1 progress of the running move;
//       from: the rect it moves from (the "EDGE OF PHOTOGRAPH" hairlines hang there), or null when settled.
//       A shot whose "window" is "full frame (card)" (S07, S18, S57) is full frame regardless of the track.
//   win.widthOf(shape) -> design px (height is always 1080: 7:9 = 840, 1:1 = 1080, 4:3 = 1440, 16:9 = 1920)
//   win.px(rect, k) -> rect in output pixels (rounded to whole pixels, so the mask edge is crisp)
//
// Track semantics (shots.json "windows", in order): { t0, shape } switches at t0; { t0, dur_frames, shape } moves over
// dur_frames frames starting ON frame round(t0 * 24) (ease-out cubic: the step lands on the hit and settles);
// { t0, t1, shape, ease: 'smoothstep' } moves across [t0, t1].
const W = 1920, H = 1080;
const SHAPES = { '7:9': 840, '1:1': 1080, '4:3': 1440, '16:9': 1920 };
const smooth = x => { x = Math.min(1, Math.max(0, x)); return x * x * (3 - 2 * x); };
const easeOut = x => { x = Math.min(1, Math.max(0, x)); return 1 - (1 - x) ** 3; };

export class WindowTrack {
  constructor(doc) {
    this.fps = doc.fps;
    this.track = doc.windows.map(e => ({ ...e, w: this.widthOf(e.shape) }));
  }
  widthOf(shape) {
    if (SHAPES[shape]) return SHAPES[shape];
    const m = /^(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)$/.exec(shape || '');
    return m ? Math.min(W, Math.round(H * +m[1] / +m[2])) : W;
  }
  _rect(w, shape) { w = Math.round(w); return { x: (W - w) / 2, y: 0, w, h: H, shape, full: w >= W }; }
  rect(t, shot = null) {
    if (shot && /full frame|card/i.test(shot.window || '')) return { ...this._rect(W, '16:9'), k: 1, from: null, card: true };
    const f = t * this.fps;
    let w = this.track[0].w, shape = this.track[0].shape, k = 1, from = null;
    for (let i = 1; i < this.track.length; i++) {
      const e = this.track[i], w0 = w;
      let p;
      if (e.dur_frames) p = easeOut((f - Math.round(e.t0 * this.fps) + 1) / e.dur_frames);
      else if (e.t1 !== undefined) p = (e.ease === 'linear' ? (x => Math.min(1, Math.max(0, x))) : smooth)((t - e.t0) / (e.t1 - e.t0));
      else p = t >= e.t0 - 1e-9 ? 1 : 0;
      const started = e.dur_frames ? f >= Math.round(e.t0 * this.fps) : t >= e.t0 - 1e-9;
      if (!started) break;
      w = w0 + (e.w - w0) * p; shape = e.shape; k = p; from = p < 1 ? this._rect(w0, this.track[i - 1].shape) : null;
    }
    return { ...this._rect(w, shape), k, from };
  }
  px(r, k) {
    const x0 = Math.round(r.x * k), y0 = Math.round(r.y * k), x1 = Math.round((r.x + r.w) * k), y1 = Math.round((r.y + r.h) * k);
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  }
}
