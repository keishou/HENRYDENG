// S01 - THE TRAY: eyes develop (0.000-5.900 s, frames 0-141; lane C). The hook (BIBLE 3).
//
// 7:9 window; from directly above, the photograph as a print under a thin layer of developer in a black tray, cropped to
// the face (src/fx/print.js: the chin just above the bottom edge, the hair inside the top); the lower right corner of the
// tray and its meniscus in the window; the safelight lies on the liquid as a large soft veil over the paper's upper left.
// Frame 0 is already this image.
//   f6    the liquid starts to rock (one wave per 2 bars); development begins in 16 pulses on the 16th grid (f6 ... f47),
//         each doubling the developed ink AREA (dots in order of darkness x certainty): the first pulse is two specks
//         where the pupils are, the eyes read by f27 (held grey until their hits), then the hair as a cloud
//   f49   "I"      the voice enters: the light comes up (src/fx/voice.js, gated until now) and the pupils snap to black
//   f60   "see"    the irises reach full density
//   f68   "sparks" a VOICE catchlight in each eye (a small hot core, a tight halo that lifts the iris), the only colour
//         inside the window, with a 6-frame bloom
//   f87 / f104 / f109  A-G-I: brows and lash line; nostrils and lip line; the hair mass
//   f114 / f120 / f126 "in your eyes": midtones fill outward from the eyes in three steps; ear rims, outer hairline,
//         jaw outline stay thin (the certainty cap)
//   f130-131  the print blinks: its own upper lids close over the eyes (a warp of the paper image), the catchlights go
//         out for 2 frames, the lids reopen over f132-133
// The development clock after the pulses follows the voice (the safelight too: tray.update's default light).
// Text (premise, the margin stack, the ZH columns) is the shot's text spec, drawn by the core's type path.
// Face numbers (iris centres, the photo's catchlights) are read at run time from out/film/data/certainty_1024.json.
import { develop } from '../fx/develop.js';
import { loadPrint, PRINT_ASSETS, blinkEyes } from '../fx/print.js';
import { voiceLight } from '../fx/voice.js';

const T = {
  start: 0.2356, I: 2.045, see: 2.5, sparks: 2.852, A: 3.635, G: 4.32, I2: 4.54, in: 4.77, your: 5.01, eyes: 5.23, blink: 5.4,
};
const VOICE = [217, 119, 87];
// the blink by frames from its hit (5.40 = f130): closed on the hit, 2 frames shut, reopening
const BLINK = [1, 1, 0.22, 0.06];

export default {
  id: 'S01',
  needs: { sets: ['tray'], assets: PRINT_ASSETS },
  async init(ctx) {
    this.print = await loadPrint(ctx);
    this.eyes = blinkEyes(this.print.meta, this.print.crop);
  },
  frame(ctx, t, s) {
    const tl = ctx.tl, tray = ctx.sets.tray, P = this.print, f = s.f;
    const db = tl.framesSince(T.blink, t), blink = db >= 0 && db < BLINK.length ? BLINK[db] : 0;
    const ht = (ctx.grades && ctx.grades.DARKROOM && ctx.grades.DARKROOM.halftone) || {};
    const pass = develop(ctx, {
      key: 'S01', src: P.src, certainty: P.cert, regions: P.regions, crop: P.crop, t,
      tStart: T.start, pulses16: true, pulseStart: Math.pow(2, -8), rankBias: { pupil: 0.6, iris: 0.3 }, rankDither: 0.7, tau0: 0.45, tau0First: 0.8, gamma: 1.7, k0: 0.95, rate: 0.25, midLift: 1.2,
      lead: [
        { region: 'pupil', t: T.I, frames: 0, hold: 0.4 },
        { region: 'iris', t: T.see, frames: 0, hold: 0.3 },
        { region: 'browlash', t: T.A },
        { region: 'noselip', t: T.G, density: [0.4, 0.75] },
        { region: 'hair', t: T.I2 },
      ],
      outward: { steps: [[T.in, 0.5], [T.your, 0.85], [T.eyes, 1.4]], soft: 0.4, first: 0.85 },
      halftone: { pitch: 4 * tray.metresPerPx1080, angle: 45, amount: ht.amount ?? 0.38 },
      blink: blink > 0 ? { amount: blink, eyes: this.eyes } : null,
    });
    tray.update(t, { print: pass, liquid: { rock: { t0: T.start } } });

    // the VOICE catchlights: where the photo has its own, riding the same refraction as the print; hidden while the
    // lids cover them
    const accent = [];
    if (tl.reached(T.sparks, t) && blink < 0.2) {
      const df = tl.framesSince(T.sparks, t), lvl = voiceLight(tl)(t);
      const irisPx = P.meta.iris[0][2] / P.crop[3] * (tray.PRINT.h / (tray.metresPerPx1080 * 1080)) * 1080;   // iris radius, design px
      const pts = P.meta.catch.map(([px, py]) => {
        const [u, v] = pass.printUV(px, py), [ru, rv] = tray.refracted(u, v, t);
        return tray.project(tray.printUVToLocal(ru, rv));
      });
      accent.push({ draw: g => drawSparks(g, pts, irisPx, df, lvl) });
    }
    return {
      layers: [{ scene: tray.scene, camera: tray.camera }],
      grade: 'DARKROOM',
      post: { halftone: null, vignette: 0.25 },   // the print carries its own screen (paper space); the vignette at the
      msaa: 0,                                     // bible's lower bound, so the light's own falloff shapes the paper
      accent,
      hud: { proof: tl.reached(T.I, t) ? '0001' : null, marks: {} },
    };
  },
};

// a catchlight: a small hot core (VOICE toward white at its centre), a thin VOICE rim and a tight luminous halo that
// lifts the iris (VOICE mixed toward white at low alpha: brighter, not redder); on its first frame a bloom that settles
// over 6 frames. Mixing VOICE with white keeps its hue exactly (the palette rule).
function drawSparks(g, pts, irisPx, df, lvl) {
  const [r, gg, b] = VOICE, mixW = (k, a) => `rgba(${Math.round(r + (255 - r) * k)},${Math.round(gg + (255 - gg) * k)},${Math.round(b + (255 - b) * k)},${a})`;
  const bloom = df < 6 ? Math.pow(1 - df / 6, 2) : 0;
  const core = Math.max(2.0, irisPx * 0.15), breathe = 0.9 + 0.1 * lvl;
  for (const p of pts) {
    // halo: the iris lifted around the spark (a luminous grey-warm veil, inside the iris)
    const R = core * (3.1 + 1.1 * bloom);
    const h = g.createRadialGradient(p.x, p.y, core * 0.8, p.x, p.y, R);
    h.addColorStop(0, mixW(0.7, (0.30 + 0.28 * bloom) * breathe)); h.addColorStop(0.35, mixW(0.78, (0.11 + 0.12 * bloom) * breathe)); h.addColorStop(1, mixW(0.8, 0));
    g.fillStyle = h; g.beginPath(); g.arc(p.x, p.y, R, 0, Math.PI * 2); g.fill();
    // a thin VOICE glow hugging the core
    const r2 = core * (1.7 + 0.6 * bloom), gl = g.createRadialGradient(p.x, p.y, core * 0.7, p.x, p.y, r2);
    gl.addColorStop(0, mixW(0.1, 0.75 * breathe)); gl.addColorStop(1, mixW(0.1, 0));
    g.fillStyle = gl; g.beginPath(); g.arc(p.x, p.y, r2, 0, Math.PI * 2); g.fill();
    // the core: crisp, VOICE toward white at its centre
    const c = g.createRadialGradient(p.x - core * 0.2, p.y - core * 0.2, 0, p.x, p.y, core);
    c.addColorStop(0, mixW(0.7, 1)); c.addColorStop(0.5, mixW(0.25, 1)); c.addColorStop(0.9, mixW(0, 1)); c.addColorStop(1, mixW(0, 0.6));
    g.fillStyle = c; g.beginPath(); g.arc(p.x, p.y, core, 0, Math.PI * 2); g.fill();
  }
}
