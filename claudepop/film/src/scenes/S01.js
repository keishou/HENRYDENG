// S01 - THE TRAY: eyes develop (0.000-5.900 s, frames 0-141; lane C). The hook (BIBLE 3).
//
// 7:9 window; from directly above, the photograph as a print under a thin layer of developer in a black tray; the
// safelight lies on the liquid as a soft grey rectangle at upper left. Frame 0 is already this image.
//   f6    the liquid starts to rock (one wave per 2 bars); development begins in 16 pulses on the 16th grid (f6 ... f47),
//         each doubling the developed dots, ordered by darkness x certainty: pupils and irises first, the hair a cloud
//   f49   "I"      the pupils snap to full density            f60  "see"    the irises reach full density
//   f68   "sparks" a VOICE catchlight in each eye, the only colour inside the window, with a 6-frame bloom
//   f87 / f104 / f109  A-G-I: brows and lash line; nostrils and lip line; the hair mass
//   f114 / f120 / f126 "in your eyes": midtones fill outward from the eyes in three steps; ear rims, outer hairline,
//         jaw outline stay thin (the certainty cap)
//   f130-131  the print blinks: both catchlights out for 2 frames
// The development clock after the pulses follows the voice (the safelight too: tray.update's default light).
// Text (premise, the margin stack, the ZH columns) is the shot's text spec, drawn by the core's type path.
// Face numbers (iris centres, the photo's catchlights) are read at run time from out/film/data/certainty_1024.json.
import { develop } from '../fx/develop.js';
import { loadPrint, PRINT_ASSETS } from '../fx/print.js';

const T = {
  start: 0.2356, I: 2.045, see: 2.5, sparks: 2.852, A: 3.635, G: 4.32, I2: 4.54, in: 4.77, your: 5.01, eyes: 5.23, blink: 5.4,
};
const VOICE = [217, 119, 87];

export default {
  id: 'S01',
  needs: { sets: ['tray'], assets: PRINT_ASSETS },
  async init(ctx) {
    this.print = await loadPrint(ctx);
  },
  frame(ctx, t, s) {
    const tl = ctx.tl, tray = ctx.sets.tray, P = this.print, f = s.f;
    const pass = develop(ctx, {
      key: 'S01', src: P.src, certainty: P.cert, regions: P.regions, crop: P.crop, t,
      tStart: T.start, pulses16: true, k0: 0.95, rate: 0.25, midLift: 1.2,
      lead: [
        { region: 'pupil', t: T.I, frames: 0 },
        { region: 'iris', t: T.see, frames: 2 },
        { region: 'browlash', t: T.A },
        { region: 'noselip', t: T.G, density: [0.4, 0.75] },
        { region: 'hair', t: T.I2 },
      ],
      outward: { steps: [[T.in, 0.42], [T.your, 0.78], [T.eyes, 1.4]], soft: 0.4 },
      halftone: { pitch: 4 * tray.metresPerPx1080, angle: 45 },
    });
    tray.update(t, { print: pass, liquid: { rock: { t0: T.start } } });

    // the VOICE catchlights: where the photo has its own, riding the same refraction as the print
    const accent = [];
    const sparksOn = tl.reached(T.sparks, t), blink = f >= tl.frameOf(T.blink) && f < tl.frameOf(T.blink) + 2;
    if (sparksOn && !blink) {
      const df = tl.framesSince(T.sparks, t), env = tl.env(t);
      const irisPx = P.meta.iris[0][2] / P.crop[3] * (tray.PRINT.h / (tray.metresPerPx1080 * 1080)) * 1080;   // iris radius, design px
      const pts = P.meta.catch.map(([px, py]) => {
        const [u, v] = pass.printUV(px, py), [ru, rv] = tray.refracted(u, v, t);
        return tray.project(tray.printUVToLocal(ru, rv));
      });
      accent.push({ draw: g => drawSparks(g, pts, irisPx, df, env) });
    }
    return {
      layers: [{ scene: tray.scene, camera: tray.camera }],
      grade: 'DARKROOM',
      post: { halftone: null },            // the print carries its own 45 deg round-dot screen, in paper space
      msaa: 0,                             // top-down: every edge is axis-aligned or shader-antialiased
      accent,
      hud: { proof: tl.reached(T.I, t) ? '0001' : null, marks: {} },
    };
  },
};

// a small VOICE spark in each eye; on its first frame a bloom that settles over 6 frames
function drawSparks(g, pts, irisPx, df, env) {
  const [r, gg, b] = VOICE, col = a => `rgba(${r},${gg},${b},${a})`;
  const bloom = df < 6 ? Math.pow(1 - df / 6, 2) : 0;
  const core = Math.max(2.2, irisPx * 0.2);
  for (const p of pts) {
    const R = core * (2.4 + 3.2 * bloom);
    const gr = g.createRadialGradient(p.x, p.y, 0, p.x, p.y, R);
    const a0 = 0.3 + 0.4 * bloom + 0.06 * env;
    gr.addColorStop(0, col(a0)); gr.addColorStop(0.35, col(a0 * 0.45)); gr.addColorStop(1, col(0));
    g.fillStyle = gr; g.beginPath(); g.arc(p.x, p.y, R, 0, Math.PI * 2); g.fill();
    g.fillStyle = col(1); g.beginPath(); g.arc(p.x, p.y, core, 0, Math.PI * 2); g.fill();
  }
}
