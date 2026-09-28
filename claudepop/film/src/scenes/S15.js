// S15 - ONE TAKE: the hall walk (38.4174-52.9629 s, frames 922-1270; lane E). Verse 2, L12-L15.
//
// The locked long lens down the aisle (FOV 11, eye height 1.55; BIBLE 4.8). 38.417: the hall is empty, the sheets blank
// and glowing. On "We" (38.63) he steps out of the backlight: the stand-in is hidden until that frame, then condenses out
// of the glare (the veil clears by the first heel strike, 39.3265, bar 22 beat 3) and walks at the lens at half time
// (sequences.js S15: walk_runway_sym_loop, strikes on beats 1 and 3, root z -10.5 -> -3.0), a backlit silhouette with a
// faint low front fill. 41.36-44.095 the window opens 4:3 -> 16:9 (core window track): more hall at the sides.
// From 45.6902 the audience develops him: one row per 8th note, from the sheets he has just passed (row 6, at the frame
// edges: the change shows on the hit frame) away into the hall toward the light (28 rows: rows 6 -> 33, both sides, 10
// prints per 8th: PROOF 0200 -> 0480), each print the photograph developing by develop()'s chemistry (the hall's photo
// atlas; eyes and shadows first, density capped by certainty), each row a step glossier than the last ("optimizing,
// accelerating"). Seen over the rows' tops, the far rows show only their top strips: a wave of darkening runs into
// the depth, with whole faces on the near rows. 49.0 his eyes
// find the lens. 50.49 "atoms": the halftone screen rotates 45 -> 15 -> 75 -> 45 (grade.js halftoneAngleAt; settles
// 52.83), and under it the 3D figure hands off to plate P04 (stage 2; stage 1 renders the previs = the fallback: the 3D
// take continues). He stops at MCU on 51.1447 (bar 29 beat 1), frontal, holding the lens; face half in shadow under a
// soft fill within 30 deg of the axis (BIBLE 5.3). The focus follows him (cheap defocus on the sheets, hairlines, panel).
//
// Previs of P04 (stage 2 input, BIBLE 10.1.3): frames past t1 (to 55.49) continue the hold; with previsTags (or the
// export's __HALL_PREVIS) the fill is raised so the face reads for the video model (the plate prompt's "soft low front
// fill lights his face"); without it the fallback lighting (face half in shadow) plays.
import * as THREE from 'three';
import { poseAt, layersAt } from '../motion/sequences.js';
import { halftoneAngleAt } from '../grade.js';
import { PRINT_ASSETS } from '../fx/print.js';

const T = { t0: 38.4174, we: 38.63, strike1: 39.3265, dev0: 45.6902, rot0: 50.49, stop: 51.1447, rot1: 52.83, t1: 52.9629 };
const EIGHTH = 60 / 132 / 2;
const DEV = { first: 6, last: 33, rate: 3.2, tau0: 0.9 };       // rows (near -> far), chemistry clock (film s -> develop s)
const TILT = 1.0 * Math.PI / 180;
const ease = u => { u = Math.min(1, Math.max(0, u)); return u * u * (3 - 2 * u); };

export default {
  id: 'S15',
  needs: { sets: ['hall'], avatar: true, plates: ['P04'], assets: PRINT_ASSETS },
  async init(ctx) {
    this.cam = new THREE.PerspectiveCamera(11, 16 / 9, 0.1, 200);
    // locked, level but for a 1 deg tilt up: the MCU at the stop has headroom and his head stays under the upper-third card
    this.cam.position.set(0, 1.55, 0); this.cam.rotation.set(TILT, 0, 0, 'YXZ'); this.cam.updateMatrixWorld();
    this.photo = await ctx.sets.hall.photoAtlas();
    this._head = new THREE.Vector3();
  },
  frame(ctx, t, s) {
    const hall = ctx.sets.hall, av = ctx.avatar, tl = ctx.tl, cam = this.cam;
    const previs = !!(ctx.frame && ctx.frame.previsTags) || !!globalThis.__HALL_PREVIS;
    // ---- the stand-in
    if (av.root.parent !== hall.scene) hall.scene.add(av.root);
    hall.avatarLook(av);
    av.apply(poseAt(av, 'S15', t), layersAt('S15', t, { lens: cam.position, av }), t);
    av.root.updateMatrixWorld(true);
    const head = av.headAnchor(this._head);
    const shown = tl.reached(T.we, t);
    av.root.visible = shown;
    // the veil clears from the "We" frame (already visibly begun on it) to the first heel strike
    const nVeil = tl.frameOf(T.strike1) - tl.frameOf(T.we);
    const veil = shown ? 0.82 * (1 - ease(tl.framesSince(T.we, t) / nVeil)) : 1;
    // ---- the audience develops him: a row per 8th from 45.6902, far rows first
    const pr = hall.resetPrints(), P = this.photo, R = hall.rows;
    pr.setAtlas(P.atlas);
    const n = DEV.last - DEV.first + 1;
    for (let k = 0; k < n; k++) {
      const tp = T.dev0 + k * EIGHTH;
      if (!tl.reached(tp, t)) break;
      const row = DEV.first + k, tau = DEV.tau0 + Math.max(0, tl.framesSince(tp, t)) / 24 * DEV.rate;
      const density = hall.stripDensity(tau), gloss = k / (n - 1);
      for (let line = 0; line < 2; line++) for (let col = 0; col < R.perLine; col++) {
        const id = R.ids[row][line][col], v = ctx.rng.hash('S15', row, line, col) % P.strips.length;
        pr.set(id, { tex: P.strips[v], density, gloss });
      }
    }
    // ---- light and focus: the footlight rises as he nears (his face fill at MCU); the lens follows him
    const dist = Math.max(0.5, cam.position.z - head.z);
    const near = ease((10.5 - dist) / 7.5);
    const fill = (previs ? 1.25 : 0.7) * (0.3 + 0.7 * near);
    const level = hall.levelAt(t) * (1 + 0.3 * veil);
    // the audience's light: images must read on the near rows (the rows behind shade them less than in the blank master)
    const sheets = { kappa: 0.085, key: 0.012 + 0.03 * ease((t - T.dev0) / 3) };
    hall.update(t, { camera: cam, avatar: true, head, veil, level, fill, even: previs, rim: 1, sheets, focus: { distance: Math.min(14, Math.max(3, dist)), coc: 90 } });
    return {
      layers: [{ scene: hall.scene, camera: cam }],
      grade: 'HALL',
      post: { halftoneAngle: halftoneAngleAt(t) },
      msaa: hall.CFG.msaa >= 0 ? hall.CFG.msaa : 0,
      plate: { id: 'P04', from: T.rot0 },
    };
  },
};
