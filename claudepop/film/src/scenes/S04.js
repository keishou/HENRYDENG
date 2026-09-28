// S04 - The drop (9.545-13.180 s, frames 229-315; lane C). L3 "There was a sudden drop in your training loss" (grokking).
//
// 7:9 window, the tray lens again (as S01). His face lies soft under the rocking developer: the same print, out of focus
// and a little thin. A single drop falls into frame and strikes the liquid on "drop" (10.70, f257): a crown, then rings
// at 0.25 m/s; behind the ring front the face is sharp and at full density. A hairline loss curve in the upper left
// margin steps down on the same frame. The bass swells in at 12.054 and is full at 12.963 (beat hits): the rocking
// deepens, each time with a swell that enters on the hit frame. Held to "now" (13.18) so the live man never enters
// before the voice. Text: the shot's SUBTITLE (left margin, bottom) and the vertical ZH, via the core's type path.
import { develop } from '../fx/develop.js';
import { loadPrint, PRINT_ASSETS } from '../fx/print.js';

const T = { drop: 10.7, swell: 12.0538, full: 12.9629 };
// the strike point, as a framing rule relative to the eyes (no face numbers in the source): in the hair above the
// screen-left eye, 0.2 interocular distances outward and 0.62 up from its iris centre (face data read at run time)
const DROP_REL = [-0.2, -0.62];
const TYPE = '250,249,245';

export default {
  id: 'S04',
  needs: { sets: ['tray'], assets: PRINT_ASSETS },
  async init(ctx) {
    this.print = await loadPrint(ctx);
    const [a, b] = this.print.meta.iris, iod = Math.hypot(b[0] - a[0], b[1] - a[1]), L = a[0] < b[0] ? a : b;
    this.dropPx = [L[0] + DROP_REL[0] * iod, L[1] + DROP_REL[1] * iod];
  },
  frame(ctx, t, s) {
    const tl = ctx.tl, tray = ctx.sets.tray, P = this.print;
    const DROP_UV = pass0UV(P, this.dropPx);
    const pass = develop(ctx, {
      key: 'S04', src: P.src, certainty: P.cert, crop: P.crop, t, tStart: -60, clock: 'linear', midLift: 0.8,
      halftone: { pitch: 4 * tray.metresPerPx1080, angle: 45 },
      soft: { lod: 3.3, sharpLod: 0, density: 0.8, rings: [{ t: T.drop, uv: DROP_UV, speed: 0.25 / tray.PRINT.h, width: 0.08 }] },
    });
    const d = tray.printUVToLocal(DROP_UV[0], DROP_UV[1]);
    const dir = [0.26, 0.97], from = -0.19;            // swells enter at the top edge of the print, on their hit frame
    tray.update(t, {
      print: pass,
      liquid: {
        rock: { t0: 0.2356, enter: false, boosts: [{ t: T.swell, gain: 1.45 }, { t: T.full, gain: 1.9 }] },
        drops: [{ t: T.drop, x: d.x, z: d.z, amp: 0.07 }],
        surge: [{ t: T.swell, dir, amp: 0.0024, speed: 0.3, width: 0.04, from }, { t: T.full, dir, amp: 0.0032, speed: 0.3, width: 0.045, from }],
      },
      falling: [{ t: T.drop, x: d.x, z: d.z, h: 0.45 }],
    });
    return {
      layers: [{ scene: tray.scene, camera: tray.camera }],
      grade: 'DARKROOM',
      post: { halftone: null },
      msaa: 0,
      accent: [{ draw: (g, fr) => lossCurve(g, fr.rect, t, tl) }],
      hud: { proof: '0006', marks: {} },
    };
  },
};

// source px (top-left origin) -> print uv through the print's crop
function pass0UV(P, [px, py]) { const c = P.crop; return [(px - c[0]) / c[2], 1 - (py - c[1]) / c[3]]; }

// the machine's training loss, a hairline in the upper left margin: a long noisy plateau, then on "drop" (f257) the
// sudden fall (grokking), then a low floor. Drawn up to the current frame; the step lands on its own frame.
function lossCurve(g, rect, t, tl) {
  const x0 = 72, x1 = Math.min(rect.x - 64, 420), y0 = 132, y1 = 300;
  if (x1 - x0 < 120) return;
  const a = 9.545, b = 13.18, fDrop = tl.frameOf(T.drop), fNow = tl.frameOf(t);
  const loss = f => {                              // a pure function of the frame: plateau -> cliff -> floor
    const n = f;
    const noise = 0.035 * Math.sin(n * 2.31) * Math.sin(n * 0.73 + 1.1) + 0.02 * Math.sin(n * 5.17 + 0.4);
    if (f < fDrop) return 0.86 - 0.05 * (f - tl.frameOf(a)) / (fDrop - tl.frameOf(a)) + noise;
    const k = f - fDrop;
    return 0.2 + 0.1 * Math.exp(-k / 6) - 0.04 * Math.min(1, k / 40) + noise * 0.35;
  };
  const X = f => x0 + (x1 - x0) * (f / 24 - a) / (b - a), Y = v => y1 - (y1 - y0) * v;
  g.save();
  g.strokeStyle = `rgba(${TYPE},0.22)`; g.lineWidth = 1;
  g.beginPath(); g.moveTo(x0, y0 - 6); g.lineTo(x0, y1); g.lineTo(x1, y1); g.stroke();       // axes, hairline
  g.strokeStyle = `rgba(${TYPE},0.72)`; g.lineWidth = 1.5; g.lineJoin = 'round';
  g.beginPath();
  const f0 = tl.frameOf(a);
  for (let f = f0; f <= fNow; f++) {
    const x = X(f), v = loss(f);
    if (f === f0) g.moveTo(x, Y(v));
    else if (f === fDrop) { g.lineTo(x, Y(loss(f - 1))); g.lineTo(x, Y(v)); }               // the cliff is vertical
    else g.lineTo(x, Y(v));
  }
  g.stroke();
  const v = loss(fNow);
  g.fillStyle = `rgba(${TYPE},0.9)`; g.beginPath(); g.arc(X(fNow), Y(v), 2.5, 0, Math.PI * 2); g.fill();
  g.font = '400 14px "IBM Plex Mono", monospace'; g.letterSpacing = '1.4px'; g.fillStyle = `rgba(${TYPE},0.6)`;
  g.textBaseline = 'alphabetic'; g.fillText('TRAINING LOSS', x0, y0 - 16);
  g.restore();
}
