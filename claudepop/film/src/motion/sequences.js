// sequences.js - lane F motion: the stand-in's body on the film timeline, per shot (BIBLE 5.5-5.7: M1, M2, M4, M6).
//
// Every time here is a film time in seconds from claudepop/analysis/song.json (gapless decode) and the shot table in
// claudepop/shots.json; nothing is re-timed by ear. Walks are at half time: one step per two beats (66 steps/min),
// heel strikes on beats 1 and 3 (the half-time grid t0 + n * 2 * 60/132). The strike phase of each walk is solved
// from the clip's own heel-strike times (MANIFEST.json gait.heel_strikes, measured on the skinned shoe by
// avatar/tools/motion_lib.py) and checked on the posed skeleton by film/lookdev/motion_prep.mjs (strikes).
//
// Pure functions of their arguments (BIBLE 9.2): no clock, no randomness, no state between frames. sequenceFor()
// caches the av.sequence it builds per avatar; the cache holds only data derived from the spec and the clips.
//
// API
//   SHOTS                       { id: spec } the motion spec of every shot that shows the stand-in (see below)
//   sequenceFor(av, id)         -> { pose(t), heading(t), segments, marks }   av.sequence of the shot, placed in world
//                                  space (metres, Y up, the hall aisle along -Z from the camera end, as in the set
//                                  specs); marks = named world points / times the set needs (pivot, stop, tear...)
//   poseAt(av, id, t)           -> pose (plain data) for av.apply
//   layersAt(id, t, { lens })   -> the procedural layers for av.apply at film time t; lens = camera position
//                                  (THREE.Vector3 or [x, y, z]) for look targets
//   apply(av, id, t, { lens })  poseAt + layersAt + av.apply in one call; returns av
//   CAPTURES_S54                52 capture times of the S54 Muybridge sheets (bars 78-80 beats, 81-83 8ths, 84 16ths)
//   GAIT                        the chosen half-time gait (M2 A/B)
//   beatT(bar, beat), T0, BEAT  the song grid
//
// Spec fields: segments (av.sequence segments; `walk: { foot, strike }` on a walk segment solves its `from` so that
// foot's heel strikes at film time `strike`), place (world placement of segment 0), anchor ({ t, x, z } shifts the
// whole sequence so the root is at x, z at film time t), layers(t, lens) -> av.apply layers, pose (static key).

export const BPM = 132, T0 = 0.2356, BEAT = 60 / BPM, HALF = 2 * BEAT, EIGHTH = BEAT / 2, SIXTEENTH = BEAT / 4;
export const beatT = (bar, beat = 1) => T0 + ((bar - 1) * 4 + (beat - 1)) * BEAT;   // bar 1 beat 1 = t0
const r4 = x => Math.round(x * 1e4) / 1e4;

// M2: the half-time gait. speed 'half' resolves to (the clip's step period) / (two beats), so each step lasts exactly
// two beats. walk_runway_sym_loop is walk_runway_loop (CMU 142_04 "Cool") made symmetric by motion_lib.py: its two
// captured steps last 0.59 s and 0.71 s (one heel never plants), so no single speed puts both strikes on the grid;
// the symmetric loop keeps the clean left-stance half-cycle and its mirror (steps 0.632 / 0.635 s) -> speed 0.697.
// B (walk_slow_loop) steps every 1.467 s: half time would need 1.61x its capture (limit 1.15x), so it is out.
export const GAIT = { clip: 'walk_runway_sym_loop', speed: 'half' };
// half-time walks settle into each footfall: speed x (1 - WARP cos) anchored on the strikes (avatar.js `warp`); the
// captured swing (0.60 s) would otherwise take 0.86 s on film and float; with 0.25 it takes about 0.72 s
export let WARP = 0.25;
export function setGaitWarp(a) { WARP = a; _cache = new WeakMap(); }   // review / A-B only
const GAIT_TEAR = { clip: 'walk_runway_sym_loop', speed: 1.0 };                    // S43: as captured (shots.json)

// look / breath helpers
const V = v => (Array.isArray(v) ? v : [v.x, v.y, v.z]);
const ease = u => { u = Math.min(1, Math.max(0, u)); return u * u * u * (u * (u * 6 - 15) + 10); };
const lerp3 = (a, b, u) => [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u];

// ------------------------------------------------------------------------------------------------ the shots
export const SHOTS = {
  // S02 previs of P01: MCU in the darkroom, alive, looking back (swallow = noise seed 2)
  S02: {
    t0: 5.9, t1: 7.725,
    segments: [{ clip: 'stand_breathe_loop', at: 5.9, loop: true, yaw: 0 }],
    layers: (t, lens) => ({ hands: { curl: 0.5 }, breath: { amp: 1.0, period: 4.4 }, noise: { amp: 0.3, seed: 2 },
      look: lens ? { target: lens, weight: 1 } : undefined }),
  },
  // S05 previs of P02: the sitter on the stool (M1). Eyes a little below the lens, lifted into it on "boss" 15.675
  // over 12 frames; the head turns at most 8 deg, the eyes at most 14 deg (clean range of the stand-in's eyes).
  S05: {
    t0: 13.18, t1: 16.5992,
    pose: { clip: 'pose_sit_stool_upright', t: 0 },
    segments: [{ clip: 'pose_sit_stool_upright', at: 13.18, yaw: 0 }],
    layers: (t, lens, av) => {
      const l = lens ? V(lens) : null;
      let target;
      if (l) {
        const floor = [0, 0, 1.5];                                   // 1.5 m ahead of the sitter, on the floor
        target = lerp3(floor, l, ease((t - 15.675) / (12 / 24)));
      }
      return { breath: { amp: 0.8, period: 4.4 }, look: target ? { target, weight: 1, maxDeg: 8, eyesMax: 14 } : undefined };
    },
  },
  // S06 previs / fallback of P03: MCU in the beam, eyes closed (M3 lids), chin at most 10 deg up
  S06: {
    t0: 16.5992, t1: 22.9629,
    segments: [{ clip: 'stand_breathe_loop', at: 16.5992, loop: true, yaw: 0 }],
    layers: (t, lens) => ({ hands: { curl: 0.5 }, breath: { amp: 0.6, period: 4.4 }, lids: { close: 1 },
      look: lens ? { target: lens, weight: 1, eyes: false } : undefined }),
  },
  // S15 ONE TAKE: stand hidden in the backlight -> half-time walk at the lens from "We" 38.63 (first strike 39.3265,
  // bar 22 beat 3) -> the stopping step lands on 51.1447 (bar 29 beat 1), MCU, frontal, holding the lens.
  // Aisle: root from z = -11.2 (start) to -3.0 (stop), camera end at z ~ 0 (lane E). A/B gait: set GAIT above.
  S15: {
    t0: 38.4174, t1: 52.9629,
    segments: [
      { clip: 'stand_breathe_loop', at: 38.4174, loop: true, yaw: 0 },
      { ...GAIT, at: 38.63, fade: 0.55, loop: true, yaw: 0, walk: { foot: 'R', strike: beatT(22, 3) } },
      { clip: 'stand_breathe_loop', at: beatT(29, 1) - 0.6, fade: 0.6, loop: true, yaw: 0 },
    ],
    anchor: { t: beatT(29, 1) + 0.25, x: 0, z: -3.0 },
    layers: (t, lens) => ({ hands: { curl: 0.5 }, breath: { amp: 0.8, period: 4.4 }, noise: { amp: 0.2, seed: 5 },
      look: lens && t >= 49.0 ? { target: lens, weight: ease((t - 49.0) / 0.8), maxDeg: 25 } : undefined }),
    strikes: { from: 39.0, to: 50.8 },     // the M2 check window (strikes expected on every half-time beat)
  },
  // S16 previs of P05: his back to us at the far end, facing the backlight
  S16: {
    t0: 52.9629, t1: 56.5992,
    segments: [{ clip: 'stand_breathe_loop', at: 52.9629, loop: true, yaw: Math.PI }],
    layers: () => ({ hands: { curl: 0.5 }, breath: { amp: 0.8, period: 4.4 } }),
  },
  // S28a + S28b: one walk away from the camera (yaw pi) with strikes on 81.1447 (bar 45 beat 3) and 82.0538 (bar 46
  // beat 1, the right foot); on "turn" he pivots 90 deg to his left on that planted right foot (82.0538-82.50), the
  // next step goes into the sheet (hidden from 82.53, lane E). One continuous body across the S28a/S28b cut.
  S28: {
    t0: 81.365, t1: 85.02,
    segments: [
      { ...GAIT, at: 79.0, loop: true, yaw: Math.PI, walk: { foot: 'R', strike: beatT(46, 1) },
        turn: { at: beatT(46, 1), dur: 0.45, deg: 90, pivot: 'R' } },
    ],
    anchor: { t: 81.365, x: 0, z: -14.0 },
    layers: () => ({ hands: { curl: 0.5 }, breath: { amp: 0.8, period: 4.4 } }),
    strikes: { from: 79.8, to: 82.2 },
  },
  // S40: small, backlit, frontal, standing in the aisle under the crane
  S40: {
    t0: 111.1447, t1: 113.359,
    segments: [{ clip: 'stand_breathe_loop', at: 111.1447, loop: true, yaw: 0 }],
    layers: () => ({ hands: { curl: 0.5 }, breath: { amp: 0.8, period: 4.4 } }),
  },
  // S41 BEAM II: frontal in the beam, looking at the lens; on "disobey" he pivots 90 deg to his left on the right foot
  // and steps out (left foot strikes 114.327, the beat under "disobey"), out of the beam by 114.67. The walk-off is at
  // capture speed (a half-time step would still be in the beam at 114.67).
  S41: {
    t0: 113.359, t1: 115.205,
    segments: [
      { clip: 'stand_breathe_loop', at: 113.359, loop: true, yaw: 0 },
      { ...GAIT_TEAR, at: 114.02, fade: 0.3, loop: true, yaw: 0,
        walk: { foot: 'L', strike: beatT(63, 4) }, turn: { at: 114.02, dur: 0.38, deg: 90, pivot: 'R' } },
    ],
    place: { x: 0, z: 0 },
    layers: (t, lens) => ({ hands: { curl: 0.5 }, breath: { amp: 0.6, period: 4.4 },
      look: lens && t < 114.1 ? { target: lens, weight: 1 - ease((t - 113.95) / 0.15) } : undefined }),
  },
  // S54 THE WALK: at the lens at half time, a strike on every beat 1 and 3 from the cut 140.2356 (bar 78 beat 1),
  // from z = -12.5 until the P10 previs segment ends (155.645)
  S54: {
    t0: 140.2356, t1: 152.5083,
    segments: [{ ...GAIT, at: 138.9, loop: true, yaw: 0, walk: { foot: 'L', strike: beatT(78, 1) } }],
    anchor: { t: beatT(78, 1), x: 0, z: -12.5 },
    layers: (t, lens) => ({ hands: { curl: 0.5 }, breath: { amp: 0.8, period: 4.4 }, noise: { amp: 0.15, seed: 9 },
      look: lens ? { target: lens, weight: 1, maxDeg: 20 } : undefined }),
    strikes: { from: 140.2, to: 155.6 },
  },
};
// S43a-d: a new sheet per beat cut; each cut is its own take at capture speed with a heel strike on its cut beat,
// the feet alternating L R L R so the cuts read as one walk that steps on every beat. Root at z = -4.0 on the beat.
[['S43a', 117.03, beatT(65, 2), 'L'], ['S43b', 117.5083, beatT(65, 3), 'R'], ['S43c', 117.9629, beatT(65, 4), 'L'],
 ['S43d', 118.4174, beatT(66, 1), 'R']].forEach(([id, t0, strike, foot], i, all) => {
  SHOTS[id] = {
    t0, t1: i + 1 < all.length ? all[i + 1][1] : 118.887,
    segments: [{ ...GAIT_TEAR, at: t0 - 1.0, loop: true, yaw: 0, walk: { foot, strike } }],
    anchor: { t: strike, x: 0, z: -4.0 },
    layers: () => ({ hands: { curl: 0.5 }, breath: { amp: 0.8, period: 4.4 } }),
    strikes: { from: t0, to: t0 + 0.47 },
  };
});
// S30 (M6): the print of him seated on the studio floor, knees drawn up; S35 (M6): face in hands on the stool.
// Rendered once as stills under flat studio light (film/lookdev/motion_prep.mjs prints -> out/film/data/).
SHOTS.S30 = { still: true, pose: { clip: 'sit_floor', t: 0.0 }, segments: [{ clip: 'sit_floor', at: 0, yaw: 0 }],
  layers: (t, lens) => ({ hands: { curl: 0.45 }, look: lens ? { target: lens, weight: 1, maxDeg: 45 } : undefined }) };
SHOTS.S35 = { still: true, pose: { clip: 'pose_sit_stool_face_in_hands', t: 0 },
  segments: [{ clip: 'pose_sit_stool_face_in_hands', at: 0, yaw: 0 }], layers: () => ({}) };
SHOTS.S46 = { still: true, empty: true };   // the empty stool: no body

// S54 captures: bars 78-80 on the beats, 81-83 on the 8ths, 84 on the 16ths (the last four during S55, onto nothing)
export const CAPTURES_S54 = [
  ...Array.from({ length: 12 }, (_, k) => beatT(78, 1) + k * BEAT),
  ...Array.from({ length: 24 }, (_, k) => beatT(81, 1) + k * EIGHTH),
  ...Array.from({ length: 16 }, (_, k) => beatT(84, 1) + k * SIXTEENTH),
].map(r4);

// ------------------------------------------------------------------------------------------------ building
let _cache = new WeakMap();

// the half-time speed of a loop: one step per two beats (66 steps / min)
export function halfSpeed(av, clip) {
  const sp = av.clip(clip).loop_info?.step_period_s;
  if (!sp) throw new Error(clip + ' has no step period');
  return sp / HALF;
}

function solveWalk(av, seg) {
  // from so that clip time at film time `strike` is a heel strike of `foot`: from + (strike - at) * speed = s + k * T
  const c = av.clip(seg.clip);
  const s = c.gait?.heel_strikes?.find(e => e.foot === seg.walk.foot);
  if (!s) throw new Error(`${seg.clip}: no ${seg.walk.foot} heel strike in the manifest (rebuild with motion_lib.py)`);
  const T = c.seconds;
  const from = s.t - (seg.walk.strike - seg.at) * seg.speed;
  return ((from % T) + T) % T;
}

export function sequenceFor(av, id) {
  let per = _cache.get(av);
  if (!per) { per = {}; _cache.set(av, per); }
  if (per[id]) return per[id];
  const spec = SHOTS[id];
  if (!spec || !spec.segments) throw new Error('no motion for ' + id);
  const build = () => spec.segments.map(s => {
    const o = { ...s };
    if (o.speed === 'half') {
      o.speed = halfSpeed(av, o.clip);
      if (o.walk && WARP) o.warp = { amp: WARP, period: HALF, anchor: o.walk.strike };
    }
    if (o.walk) o.from = solveWalk(av, o);
    if (o.turn) o.turn = { ...o.turn };
    delete o.walk;
    return o;
  });
  let place = { x: 0, z: 0, ...(spec.place || {}) };
  let seq = av.sequence(build(), place);
  if (spec.anchor) {   // rigid shift so the root passes through (x, z) at film time anchor.t
    const p = seq.pose(spec.anchor.t);
    place = { ...place, x: place.x + spec.anchor.x - p.root[0], z: place.z + spec.anchor.z - p.root[2] };
    seq = av.sequence(build(), place);
  }
  const marks = {};
  for (const s of seq.segments) if (s.turn) marks.pivot = { t: s.turn.at, x: s.turn.P[0], z: s.turn.P[1] };
  if (spec.anchor) { const p = seq.pose(spec.anchor.t); marks.anchor = { t: spec.anchor.t, x: p.root[0], z: p.root[2] }; }
  per[id] = { ...seq, id, marks };
  return per[id];
}

export function poseAt(av, id, t) {
  const spec = SHOTS[id];
  if (spec.pose && spec.still) return av.pose(spec.pose.clip, spec.pose.t);
  return sequenceFor(av, id).pose(t);
}

export function layersAt(id, t, { lens, av } = {}) {
  const spec = SHOTS[id];
  return spec.layers ? spec.layers(t, lens ? V(lens) : null, av) : {};
}

export function apply(av, id, t, opts = {}) {
  return av.apply(poseAt(av, id, t), layersAt(id, t, { ...opts, av }), t);
}

// where a static pose's stool goes: world placement of the pose so its seat centre lands on (x, z) (the tape X)
export function placeOnStool(av, clip, x, z, yaw = 0) {
  const st = av.clip(clip).props?.stool || { x: 0, z: 0 };
  const c = Math.cos(yaw), s = Math.sin(yaw);
  return { x: x - (st.x * c + st.z * s), z: z - (-st.x * s + st.z * c), yaw };
}
