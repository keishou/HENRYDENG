// S54 - THE WALK: the hall records him (140.2356-152.5083 s, frames 3366-3659; lane E). The film's one broken rule.
//
// One shot, the hall at night, locked on the aisle axis (eye height 1.55) with a slow zoom in: FOV 12 -> 3.5 deg,
// ease-in (exponential in the focal length, u^1.6), so the full figure at 12.5 m becomes his face filling the frame at
// 4.75 m on the last beat. He walks at the lens at half time (sequences.js S54: walk_runway_sym_loop, strikes on beats 1
// and 3, the L strike on the cut 140.2356; root z -12.5 -> -4.75) with no sung words: the vocal is a wordless pad. The
// rows of sheets are blank again and they record him: 12 captures on the beats of bars 78-80, 24 on the 8ths of bars
// 81-83, 16 on the 16ths of bar 84 (sequences.js CAPTURES_S54; the last four fall in S55, onto nothing). Each capture
// fixes on its sheet a side-view silhouette of his stride at that time (the M5 atlas, out/film/atlas/S54_captures.png)
// with a 0.1 s white flash on the sheet (prints.js capture): the hall behind him fills with a Muybridge sequence.
// Before each of the first captures the sheet flashes, for its beat, an image the film already showed, in film order
// (out/film/data/recap/, cached by src/sets/hall_recap.py). Capture 0 lands on the cut, so the recaps run one sheet
// ahead: recap k shows during beat k on the sheet of capture k+1 (S01 eyes on the cut ... S46 the empty stool on beat
// 11, captured on the bar-81 downbeat).
//
// Which sheets: the hall's rows are seen over their tops, so only the aisle-side strip of each row's inner sheet is
// unoccluded. The capture sheets are inner sheets (both sides, alternating) chosen at init, nearest first, that stay in
// the narrowing frame for 2 s after their capture and clear of his silhouette; each silhouette is aligned to its
// sheet's aisle-side edge (two atlas cells per capture) so the visible strip holds the figure. The captures march into
// the depth as the zoom tightens.
//
// Light: the backlight climbs from night toward white over the walk (hall.levelAt); no bloom or halation in the last bar
// (151.1447 on). 151.145: a 2-frame full-frame capture flash, and under it the 3D silhouette hands off to plate P10
// (stage 2). Stage 1: previsTags (or the export's __HALL_PREVIS) = the P10 previs (a soft low front fill lights his face
// evenly, as the plate prompt asks); otherwise the fallback: the silhouette walks on into the lens with the face in
// shadow. Past t1 (to 155.645, the previs segment's handle) he walks on and the lens widens to keep his face at its
// last-beat size (a close-up, never an eye ECU of the stand-in).
// HUD: PROOF spinning (proof.js). Text: the S53 card persists until "show?" ends (141.10), then none (type engine).
import * as THREE from 'three';
import { poseAt, layersAt, CAPTURES_S54, BEAT } from '../motion/sequences.js';
import { Prints } from '../sets/prints.js';

const T = { t0: 140.2356, t1: 152.5083, bar84: 151.1447, end: 152.46 };
const FOV = [12, 3.5], ZOOM_POW = 1.6;
const ATLAS_URL = '/out/film/atlas/S54_captures.png', ATLAS_JSON = '/out/film/atlas/S54_captures.json';
const RECAP_DIR = '/out/film/data/recap/';
const RECAPS = ['S01', 'S05', 'S06', 'S08', 'S10', 'S13', 'S17b', 'S21', 'S24', 'S34', 'S38', 'S46'];
const ASPECT = 16 / 9;

// the zoom: FOV at film time t (held at the ends)
function fovAt(t) {
  const u = Math.min(1, Math.max(0, (t - T.t0) / (T.end - T.t0)));
  return Math.exp(Math.log(FOV[0]) + (Math.log(FOV[1]) - Math.log(FOV[0])) * Math.pow(u, ZOOM_POW));
}

export default {
  id: 'S54',
  needs: { sets: ['hall'], avatar: true, plates: ['P10'], assets: [ATLAS_URL, ATLAS_JSON, RECAP_DIR + 'recap.json'] },
  async init(ctx) {
    const hall = ctx.sets.hall, av = ctx.avatar, A = ctx.assets;
    this.cam = new THREE.PerspectiveCamera(FOV[0], ASPECT, 0.1, 200);
    // aim: level at the lens height, tilted up just enough to centre his eyes at the end of the zoom
    const pEnd = poseAt(av, 'S54', T.end), eye = av.fkHead(pEnd, 'head');
    this.tilt = Math.atan2(eye[1] + 0.07 - 1.55, 0 - pEnd.root[2]);
    this.distEnd = -eye[2];
    this.cam.position.set(0, 1.55, 0);
    // ---- the capture atlas: blank, recaps, and per capture its silhouette aligned left and right
    const [tex, meta] = await Promise.all([A.texture(ATLAS_URL, { srgb: false, mipmaps: false }), A.json(ATLAS_JSON)]);
    const recapMeta = await A.json(RECAP_DIR + 'recap.json').catch(() => ({ shots: [] }));
    const recapTex = await Promise.all(RECAPS.map(id => (recapMeta.shots.find(r => r.id === id && r.source)
      ? A.texture(RECAP_DIR + id + '.jpg').catch(() => null) : Promise.resolve(null))));
    const bbox = figureBoxes(tex.image, meta);
    const W = tex.image.width, H = tex.image.height, entries = [null];
    this.recapCell = RECAPS.map((id, i) => { entries.push(recapTex[i] ? { texture: recapTex[i], mode: 'photo', tone: { gamma: 1.0 } } : null); return entries.length - 1; });
    this.capCell = meta.captures.map((c, i) => {
      const [bx0, bx1] = bbox[i], m = 10, clip = [c.x / W, 1 - (c.y + c.h) / H, (c.x + c.w) / W, 1 - c.y / H];
      const v0 = 1 - (c.y + c.h) / H, v1 = 1 - c.y / H;
      const L = { texture: tex, mode: 'silhouette', tone: { density: 1.5 }, clip, rect: [(bx0 - m) / W, v0, (bx0 - m + c.w) / W, v1] };
      const R = { texture: tex, mode: 'silhouette', tone: { density: 1.5 }, clip, rect: [(bx1 + m - c.w) / W, v0, (bx1 + m) / W, v1] };
      entries.push(L, R);
      return [entries.length - 2, entries.length - 1];                 // [figure at the left edge, at the right edge]
    });
    this.capAtlas = Prints.buildAtlas(ctx, entries, { cols: 12, rows: Math.ceil(entries.length / 12), cellW: 280, cellH: 360, border: 0.045 });
    // ---- which sheet records each capture (pure: computed once from the shot's camera and motion)
    this.plan = planCaptures(ctx, this, av);
  },
  frame(ctx, t, s) {
    const hall = ctx.sets.hall, av = ctx.avatar, tl = ctx.tl, cam = this.cam;
    const previs = !!(ctx.frame && ctx.frame.previsTags) || !!globalThis.__HALL_PREVIS;
    setCamera(cam, t, this.tilt, t > T.end ? -av.fkHead(poseAt(av, 'S54', t), 'head')[2] : null, this.distEnd);
    // ---- the stand-in
    if (av.root.parent !== hall.scene) hall.scene.add(av.root);
    hall.avatarLook(av);
    av.root.visible = true;
    av.apply(poseAt(av, 'S54', t), layersAt('S54', t, { lens: cam.position, av }), t);
    av.root.updateMatrixWorld(true);
    const head = av.headAnchor(new THREE.Vector3());
    // ---- the sheets: blank; recaps a beat ahead; captures fix his stride
    const pr = hall.resetPrints();
    pr.setAtlas(this.capAtlas);
    for (const c of this.plan) {
      const props = { capture: { t: c.t, cell: c.cell, flash: 0.1, density: 1 } };
      if (c.recap !== undefined && this.recapCell[c.recap] !== undefined) props.recap = { t0: c.t - BEAT, t1: c.t, cell: this.recapCell[c.recap], density: 1 };
      pr.set(c.id, props);
    }
    // ---- light, focus, finish
    const dist = Math.max(0.5, cam.position.z - head.z);
    const level = hall.levelAt(t);
    // fallback: the face stays in shadow (a dark shape filling the frame); previs: the plate's even low fill
    const fill = previs ? 1.25 : 0.05;
    const k = Math.pow(Math.tan(5.5 * Math.PI / 180) / Math.tan(cam.fov / 2 * Math.PI / 180), 2);   // coc grows with f^2
    hall.update(t, { camera: cam, avatar: true, head, level, fill, even: previs, rim: previs ? 1 : 0.8, sheets: { kappa: 0.1, key: 0.02 }, focus: { distance: dist, coc: Math.min(70 * k, 420) } });
    const f = tl.frameOf(t), fb = tl.frameOf(T.bar84), lastBar = f >= fb;
    return {
      layers: [{ scene: hall.scene, camera: cam }],
      grade: 'HALL',
      // the bloom thins as the light climbs (the silhouette stays a shape, not a glow); none in the last bar
      post: { flash: f === fb || f === fb + 1 ? 1 : 0,
        ...(lastBar ? { bloom: null, halation: 0 } : { bloom: { thresh: 0.85, amount: 0.35 * Math.pow(6 / level, 0.9) }, halation: 0.2 * Math.pow(6 / level, 1.2) }) },
      msaa: hall.CFG.msaa >= 0 ? hall.CFG.msaa : 0,
      plate: { id: 'P10', from: T.bar84 },
    };
  },
};

// past the last beat (the previs handle, after the cut) the lens widens as he nears so his face keeps the size it has
// on the last beat: a close-up, never an eye ECU of the stand-in (BIBLE 5.3.1)
function setCamera(cam, t, tilt, dist = null, distEnd = null) {
  cam.fov = t > T.end && dist && distEnd ? 2 * Math.atan(Math.tan(FOV[1] / 2 * Math.PI / 180) * distEnd / dist) * 180 / Math.PI : fovAt(t);
  cam.aspect = ASPECT; cam.updateProjectionMatrix();
  cam.position.set(0, 1.55, 0);
  cam.rotation.set(tilt, 0, 0, 'YXZ');
  cam.updateMatrixWorld();
}

// horizontal extent (px, atlas space) of the white figure in each capture cell (CPU read of the decoded atlas)
function figureBoxes(img, meta) {
  const cv = new OffscreenCanvas(img.width, img.height), g = cv.getContext('2d', { willReadFrequently: true });
  g.drawImage(img, 0, 0);
  // the texture was decoded flipped (flipY at decode): rows are bottom-up
  const d = g.getImageData(0, 0, img.width, img.height).data, W = img.width, H = img.height;
  return meta.captures.map(c => {
    let x0 = c.x + c.w, x1 = c.x;
    for (let y = c.y; y < c.y + c.h; y += 2) {
      const row = H - 1 - y;
      for (let x = c.x; x < c.x + c.w; x++) if (d[(row * W + x) * 4] > 96) { if (x < x0) x0 = x; if (x > x1) x1 = x; }
    }
    return x1 >= x0 ? [x0, x1] : [c.x + c.w * 0.3, c.x + c.w * 0.7];
  });
}

// For each capture time: the nearest inner sheet (col 0, either side, alternating) whose aisle-side strip is inside the
// frame from the capture until 2 s later (or the shot end) and clear of his silhouette; not already used.
function planCaptures(ctx, self, av) {
  const hall = ctx.sets.hall, R = hall.rows, cam = new THREE.PerspectiveCamera(), used = new Set(), plan = [];
  const inFrame = (t, x, z, head) => {
    setCamera(cam, t, self.tilt);
    const tanX = Math.tan(cam.fov / 2 * Math.PI / 180) * ASPECT, d = -z;
    const edge = (Math.abs(x) - 0.28 + 0.06) / d;                      // the sheet's aisle-side edge (+ 6 cm in)
    const clearHim = (0.36 / Math.max(0.5, -head[2])) + 0.004;         // his half width (arm swing) on screen
    return edge < tanX * 0.94 && edge > clearHim;
  };
  CAPTURES_S54.forEach((tc, i) => {
    if (tc >= T.t1 - 1e-6) return;
    const hold = Math.min(tc + 2.0, T.end);
    const heads = [tc, hold].map(tt => av.fkHead(poseAt(av, 'S54', tt), 'head'));
    const want = i % 2 ? 1 : 0;                                        // line 1 = +X side, 0 = -X side
    let best = null;
    for (const line of [want, 1 - want]) {
      for (let r = 2; r < R.n; r++) {
        const id = R.ids[r][line][0]; if (used.has(id)) continue;
        const it = hall.prints.items[id];
        if (inFrame(tc, it.x, it.z, heads[0]) && inFrame(hold, it.x, it.z, heads[1])) { if (!best || it.z > best.z + 1e-6) best = { id, z: it.z, line }; break; }
      }
      if (best && best.line === want) break;
    }
    if (!best) return;
    used.add(best.id);
    // the figure sits at the sheet's aisle-side edge: +X side -> the sheet's left (as seen), -X side -> its right
    plan.push({ i, t: tc, id: best.id, cell: self.capCell[i][best.line === 1 ? 0 : 1] });
  });
  // recap k on the sheet of capture k + 1, during beat k
  plan.forEach((c, j) => { if (c.i >= 1 && c.i <= RECAPS.length) c.recap = c.i - 1; });
  return plan;
}
