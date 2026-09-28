// scene_template.js - a complete, working example of a shot module (BIBLE 9.3), kept by lane A as the reference for the
// scene lanes. Copy it to src/scenes/<SHOT_ID>.js and replace the body. It is not discovered as a shot by itself; try
// it on any shot with the override hook:  node film/still.mjs --shot S40 --override S40=/film/src/core/scene_template.js
//
// CONTRACT
//   export default { id, needs, init(ctx), frame(ctx, t, s) }
//   id      the shot id (must equal the file name)
//   needs   { sets: ['hall'], avatar: true, plates: ['P04'], assets: ['/out/film/data/certainty_1024.png'] }
//           preloaded by the core before init: ctx.sets.hall, ctx.avatar, ctx.plates.load('P04'), ctx.assets.*(url)
//   init(ctx)          async, once per page (the core guards it); build geometry / materials here. Idempotent.
//   frame(ctx, t, s)   sync or async; a PURE function of t (reset anything you mutate; no Math.random / Date / state
//                      carried between frames; seeded noise from ctx.rng). s = { shot, tl: t - shot.t0, u: 0..1,
//                      f: film frame, fi: frame within the shot, n: frames in the shot, last }.
//   returns the FRAME SPEC:
//     layers   [{ scene, camera, clearDepth = true }]   rendered in order into the HDR target (3D renders the full 16:9
//              view; the core masks it with the window). First layer clears to `clear` (default INK) unless the scene
//              has a background.
//     grade    'DARKROOM' | 'HALL' | 'STUDIO' | 'BEAM' | 'CYANOTYPE' | 'WHITE' | 'CARD'   (default: shot.look)
//     post     { halftoneAngle, pitch, exposure, grainFrozen, ...any grade.js preset key (overrides the preset);
//                flash 0..1 (to white), dim (stops, image only), fade 0..1 (whole frame to black) }
//     msaa     4 (default) | 0 | 2   MSAA samples for this frame (4x costs ~230 ms at 1080p under SwiftShader)
//     accent   [{ scene, camera, occlude } (3D VOICE objects, rendered on their own and composited after the grade;
//                 occlude: true lets the main layers hide them - same camera only, one extra depth-only pass)
//               | { draw(g2d, frame) } (2D marks on the HUD canvas in 1920x1080 design px, after the grade, under the
//                 HUD and the type)]
//     plate    { id: 'P04', from: 50.49, over: false } | null   stage 2 switches the previs for the plate when
//              out/plates/<P>/plate.json exists; stage 1 always renders your layers (tagged PREVIS with --previs-tags)
//     hud      { proof, wedge, slug, caption, job, counter, marks } | null   EVALUATED strings (src/hud/proof.js);
//              omit for the default (registration marks only); null for none
//     text     shot.text (default when omitted) | a modified copy | null (no type)
//     clear    0x0a0a09   the HDR clear colour
//   ctx.flags.faceSafe   true = render the BIBLE 12.1 fallback (the consent-pending shots S12 S37 S50 S51 test it every
//                        frame; URL ?safe=1, render.mjs --safe)
//   ctx.tl lookups are BY FRAME (beatAt, lineAt, wordAt, live, sectionAt); test events with tl.reached(T, t) /
//   tl.framesSince(T, t), never t >= T.
//     overlay  (hud, frame) => {}   optional 2D drawing on the HUD canvas after the window mask (debug labels)
import * as THREE from 'three';

export default {
  id: 'TEMPLATE',
  needs: { sets: ['hall'], avatar: true },
  async init(ctx) {
    // the hall set (lane E) owns its lights, floor, haze and prints; a scene only adds its own objects and a camera
    this.cam = new THREE.PerspectiveCamera(14, 16 / 9, 0.1, 200);
    // accent layer: a VOICE point (like the Omega point), composited after the grade so it stays pure orange
    this.accScene = new THREE.Scene();
    this.spark = new THREE.Mesh(new THREE.SphereGeometry(0.018, 16, 12), new THREE.MeshBasicMaterial({ color: ctx.color('VOICE') }));
    this.accScene.add(this.spark);
  },
  frame(ctx, t, s) {
    const hall = ctx.sets.hall, av = ctx.avatar, tl = ctx.tl;
    // the stand-in (shared across shots): re-parent into this scene, make him visible (a set may have hidden him),
    // set the look, pose it (pure function of t)
    if (av.root.parent !== hall.scene) hall.scene.add(av.root);
    av.root.visible = true;
    av.setLook('silhouette');
    if (hall.avatarLook) hall.avatarLook(av);
    const speed = av.beatSpeed('walk_runway_loop', 66);
    const pose = av.pose('walk_runway_loop', s.tl, { speed, place: { x: 0, z: -9, yaw: 0 } });
    av.apply(pose, { breath: { amp: 0.8 }, hands: { curl: 0.5 } }, t);
    // camera: chorus master (0, 1.55, 0) looking down -Z, a slow seeded drift
    this.cam.position.set(0.02 * ctx.rng.noise1(t * 0.3, 7), 1.55, 0); this.cam.lookAt(0, 1.4, -10);
    this.cam.updateMatrixWorld();
    const head = av.headAnchor();
    // the set's per-frame update after posing (lane E: it renders the floor reflection now); the voice is the light
    hall.update(t, { camera: this.cam, avatar: true, head, rim: 0.8 + 0.4 * tl.env(t) });
    this.spark.position.copy(head).add(new THREE.Vector3(0.03, 0, 0.12));
    return {
      layers: [{ scene: hall.scene, camera: this.cam }],
      grade: 'HALL',
      post: { flash: s.fi < 2 ? 0 : 0 },
      accent: [{ scene: this.accScene, camera: this.cam },
        { draw: (g, fr) => { g.strokeStyle = '#D97757'; g.lineWidth = 3; g.beginPath(); g.arc(fr.rect.x + fr.rect.w * 0.8, 300, 40 + 10 * s.u, 0, 6.283); g.stroke(); } }],
      hud: { proof: String(200 + Math.floor(s.u * 280)).padStart(4, '0'), caption: 'PL. TEMPLATE · EXAMPLE CAPTION · 2026-09-28' },
      text: s.shot.text,
    };
  },
};
