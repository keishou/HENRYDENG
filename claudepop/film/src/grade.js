// STUB - owned by lane B, replace. (Frozen on day 0 by lane A: keep the export names and the preset keys.)
//
// grade.js - register presets for the finish chain (BIBLE 4.7 table). A preset is plain data in the film's own
// vocabulary; the post chain (src/post.js, lane B) turns it into shader uniforms. Until lane B's post understands this
// vocabulary directly, src/core/finish.js maps it onto the legacy post.js params.
//
//   GRADES[name] -> preset                name = a shots.json "look": DARKROOM | HALL | STUDIO | BEAM | CYANOTYPE | WHITE | CARD
//                                          (+ SLATE, the neutral animatic grade used by the core's slate scene)
//   grade(name, overrides?) -> preset      a copy of the preset with overrides merged (frameSpec.post goes here)
//
// Preset fields: mono 0..1, satCap (max saturation after grade), toneShadow / toneHigh [r,g,b] split tone,
//   contrast, lift, gain, exposure, halftone { pitch (px at 1080p), angle (deg) } | null, grain (fraction),
//   grainFrozen (bool: seed = shot id), bloom { thresh, amount } | 'voice' | null, halation, vignette,
//   paper (WHITE: paper tooth, nothing printed), ink (CARD: INK field, type only), cyan (CYANOTYPE ramp on the print)
export const GRADES = {
  DARKROOM: { mono: 1, toneShadow: [0.96, 0.98, 1.00], toneHigh: [1.00, 0.99, 0.97], contrast: 1.12, lift: 0.012,
    halftone: { pitch: 4, angle: 45 }, grain: 0.015, bloom: 'voice', halation: 0, vignette: 0.3 },
  HALL: { mono: 0.88, satCap: 0.12, toneShadow: [0.90, 0.96, 1.06], toneHigh: [0.97, 1.00, 1.03], contrast: 1.05, lift: 0.03,
    halftone: { pitch: 4, angle: 45 }, grain: 0.015, bloom: { thresh: 0.85, amount: 0.35 }, halation: 0.2, vignette: 0.3 },
  STUDIO: { mono: 1, toneShadow: [1, 1, 1], toneHigh: [1.00, 0.99, 0.97], contrast: 0.95, lift: 0.02,
    halftone: { pitch: 4, angle: 45 }, grain: 0.012, bloom: null, halation: 0, vignette: 0.25 },
  BEAM: { mono: 1, toneShadow: [1, 1, 1], toneHigh: [1, 1, 1], contrast: 1.15, lift: 0,
    halftone: { pitch: 4, angle: 45 }, grain: 0.015, bloom: null, halation: 0, vignette: 0.3 },
  CYANOTYPE: { mono: 1, toneShadow: [1, 1, 1], toneHigh: [1, 1, 1], contrast: 1.1, lift: 0.01,
    halftone: { pitch: 4, angle: 45 }, grain: 0.015, grainFrozen: true, bloom: null, halation: 0, vignette: 0.3, cyan: true },
  WHITE: { paper: true, mono: 1, contrast: 1, lift: 0, halftone: null, grain: 0, bloom: null, vignette: 0 },
  CARD: { ink: true, mono: 1, contrast: 1, lift: 0, halftone: null, grain: 0, bloom: null, vignette: 0 },
  SLATE: { mono: 1, toneShadow: [1, 1, 1], toneHigh: [1, 1, 1], contrast: 1, lift: 0, halftone: null, grain: 0.006,
    bloom: null, halation: 0, vignette: 0 },
};

export function grade(name, overrides = {}) {
  const base = GRADES[name] || GRADES.DARKROOM;
  return { ...structuredClone(base), ...overrides, name: GRADES[name] ? name : 'DARKROOM' };
}
