// S08 - HALL MASTER C1: blank sheets (23.872-25.690 s, frames 573-616; lane E). The chorus master (BIBLE 4.8, 7 THE
// AUDIENCE): the hall down its aisle, the long lens (FOV 14, eye height 1.55, locked, symmetrical); rows of blank white
// sheets hang across both sides like a seated audience, glowing through with the cold backlight at the far end; haze;
// the wet black floor. Nobody. The window steps 1:1 -> 4:3 on the crash (core window track, 8 frames); the CARD
// completes "(doom)" (type engine; the image dims 1 stop while it is up, to 25.07) and the L7 SUBTITLE runs at the
// bottom. The crash (23.872, the cut) lands as light: the backlight is a little over its level on the cut frame and
// settles over a beat, and a faint shiver runs through the sheets from the back rows forward. HUD: wedge +1, slug
// ENLARGER 16 s (from shots.json via the proof HUD).
const T = { crash: 23.872 };

export default {
  id: 'S08',
  needs: { sets: ['hall'] },
  async init(ctx) {
    const THREE = ctx.THREE;
    this.cam = new THREE.PerspectiveCamera(14, 16 / 9, 0.1, 200);
    this.cam.position.set(0, 1.55, 0); this.cam.lookAt(0, 1.55, -10);
  },
  frame(ctx, t, s) {
    const hall = ctx.sets.hall, tl = ctx.tl;
    hall.resetPrints();
    // the crash: the light over its level on the cut frame, settling over a beat (a pure function of the frame)
    const df = Math.max(0, tl.framesSince(T.crash, t));
    const level = hall.levelAt(t) * (1 + 0.22 * Math.exp(-df / 5));
    hall.update(t, { camera: this.cam, level, tremble: { t: T.crash, amp: 0.012, speed: 60 }, focus: { distance: 16, coc: 110 } });
    return {
      layers: [{ scene: hall.scene, camera: this.cam }],
      grade: 'HALL',
      post: hall.post(t),
      msaa: hall.CFG.msaa >= 0 ? hall.CFG.msaa : 0,
    };
  },
};
