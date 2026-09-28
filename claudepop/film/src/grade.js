// grade.js - register presets for the finish chain (BIBLE 4.7 table; lane B). A preset is plain data in the film's own
// vocabulary; src/post.js (Post.renderFrame) turns it into shader uniforms. Frozen names (lane A, day 0): GRADES, grade().
//
//   GRADES[name] -> preset                name = a shots.json "look": DARKROOM | HALL | STUDIO | BEAM | CYANOTYPE | WHITE | CARD
//                                          (+ SLATE, the neutral animatic grade of the core's slate scene)
//   grade(name, overrides?) -> preset      a deep copy with overrides merged (frameSpec.post goes here; a `halftone`
//                                          override keeps the preset's amount when it only sets pitch / angle)
//
// Preset fields
//   exposure        scene exposure before the ACES-fit tone curve (the card / freeze dim are applied on top, image only)
//   bloom           'voice' (no scene bloom; the VOICE accents bloom) | { thresh, amount } (thresh on display luminance)
//                   | null;   halation: amount of the wide cold glow around what blooms (HALL backlight)
//   mono 0..1       monochrome mix (luma, split-toned by toneShadow / toneHigh [r, g, b] multipliers)
//   satCap          max HSV saturation after the grade (HALL 0.12)
//   keepHue         { h (deg), w (deg) }: a hue band exempt from the mono mix (CYANOTYPE: the print's blue)
//   contrast        slope at the pivot of an S-curve that keeps 0 and 1 (display space);  lift (blacks up), gain
//   halftone        { pitch (px at 1080p, scaled with the output height), angle (deg), amount (0..1 mix of the AM
//                   screen in linear light; the mean tone is preserved) } | null
//   grain           sigma of the monochrome, luminance-weighted silver grain (display units); grainFrozen: seed = shot
//   vignette        0..0.35, relative to the window rect
//   paper / ink     WHITE / CARD: nothing printed (no dots, no grain, no vignette)
export const GRADES = {
  DARKROOM: { mono: 1, toneShadow: [0.96, 0.98, 1.00], toneHigh: [1.00, 0.99, 0.97], contrast: 1.12, lift: 0.012, gain: 1,
    halftone: { pitch: 4, angle: 45, amount: 0.38 }, grain: 0.015, bloom: 'voice', halation: 0, vignette: 0.3, exposure: 1 },
  HALL: { mono: 0.88, satCap: 0.12, toneShadow: [0.90, 0.96, 1.06], toneHigh: [0.97, 1.00, 1.03], contrast: 1.05, lift: 0.03, gain: 1,
    halftone: { pitch: 4, angle: 45, amount: 0.32 }, grain: 0.015, bloom: { thresh: 0.85, amount: 0.35 }, halation: 0.2, vignette: 0.3, exposure: 1 },
  STUDIO: { mono: 1, toneShadow: [1, 1, 1], toneHigh: [1.00, 0.99, 0.97], contrast: 0.95, lift: 0.02, gain: 1,
    halftone: { pitch: 4, angle: 45, amount: 0.3 }, grain: 0.012, bloom: null, halation: 0, vignette: 0.25, exposure: 1 },
  BEAM: { mono: 1, toneShadow: [1, 1, 1], toneHigh: [1, 1, 1], contrast: 1.15, lift: 0, gain: 1,
    halftone: { pitch: 4, angle: 45, amount: 0.38 }, grain: 0.015, bloom: null, halation: 0, vignette: 0.3, exposure: 1 },
  CYANOTYPE: { mono: 1, keepHue: { h: 213, w: 38 }, toneShadow: [1, 1, 1], toneHigh: [1, 1, 1], contrast: 1.1, lift: 0.01, gain: 1,
    halftone: { pitch: 4, angle: 45, amount: 0.35 }, grain: 0.015, grainFrozen: true, bloom: null, halation: 0, vignette: 0.3, cyan: true, exposure: 1 },
  WHITE: { paper: true, mono: 1, toneShadow: [1, 1, 1], toneHigh: [1, 1, 1], contrast: 1, lift: 0, gain: 1, halftone: null, grain: 0,
    bloom: null, halation: 0, vignette: 0, exposure: 1 },
  CARD: { ink: true, mono: 1, toneShadow: [1, 1, 1], toneHigh: [1, 1, 1], contrast: 1, lift: 0, gain: 1, halftone: null, grain: 0,
    bloom: null, halation: 0, vignette: 0, exposure: 1 },
  SLATE: { mono: 1, toneShadow: [1, 1, 1], toneHigh: [1, 1, 1], contrast: 1, lift: 0, gain: 1, halftone: null, grain: 0.006,
    bloom: null, halation: 0, vignette: 0, exposure: 1 },
};

export function grade(name, overrides = {}) {
  const base = GRADES[name] || GRADES.DARKROOM;
  const out = { ...structuredClone(base), name: GRADES[name] ? name : 'DARKROOM' };
  for (const [k, v] of Object.entries(overrides || {})) {
    if (v === undefined) continue;
    if (k === 'halftone' && v && base.halftone) out.halftone = { ...base.halftone, ...v };
    else out[k] = v && typeof v === 'object' && !Array.isArray(v) ? structuredClone(v) : v;
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------- per-shot finish
// Defaults a shot's frameSpec.post should carry (the core may merge SHOT_POST[shot.id] under the scene's own post).
// The chorus trays coarsen the screen with each stop of exposure (BIBLE 4.5): +1 4.5 px, +2 5, +3 6, +4 7.
export const SHOT_POST = { S09: { pitch: 4.5 }, S20: { pitch: 5 }, S32: { pitch: 6 }, S47: { pitch: 7 } };
// S15 "atoms" (50.49 -> 52.83): the screen rotates 45 -> 15 -> 75 -> 45 deg, moire sweeping the frame (the film's only
// morph; it hides the plate handoff at 50.49-50.95). Pure function of film time; 45 outside the span.
const ROT = [[50.49, 45], [51.27, 15], [52.05, 75], [52.83, 45]];
export function halftoneAngleAt(t) {
  if (t <= ROT[0][0] || t >= ROT[ROT.length - 1][0]) return 45;
  for (let i = 1; i < ROT.length; i++) if (t < ROT[i][0]) {
    const [a, x] = ROT[i - 1], [b, y] = ROT[i], u = (t - a) / (b - a), s = u * u * (3 - 2 * u);
    return x + (y - x) * s;
  }
  return 45;
}
