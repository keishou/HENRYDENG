// voice.js - "the voice is the light" (BIBLE 2.1, 4.3; lane C, shared): the vocal envelope turned into a light level that
// reads on screen and never flickers.
//
//   const L = voiceLight(ctx.tl, opts)     -> t => 0..1 (memoized per timeline + options; a pure function of the frame)
//   L.frames                               Float32Array, one value per film frame
//
// The raw envelope (tools/voice_env.py: Demucs vocal stem, 50 ms attack) steps on single frames and sits near 0.8
// whenever she sings, so as a light it either flickers or does nothing. Per film frame f:
//   1. lead: read the envelope 1.5 frames ahead (its own rise lags a sung onset by about a frame; the extra half frame
//      leads it, so the light's biggest step lands on the onset frame, a whisper of it the frame before). The lead never
//      reads across a cut: in a shot's last frames the envelope is read at most at the shot's last frame (no light step
//      on the frame before a cut)
//   2. gate: before the first sung word (gate, default 2.045: "I") the level is 0 - the stem's bleed under the intro
//      never moves the light
//   3. perceptual map: v = smoothstep(lo, hi, e) spreads the range the envelope actually lives in while she sings
//      (0.5 .. 0.93) over 0 .. 1
//   4. attack / release: one-pole, attack 0.5 per frame (a rise takes at least 2 frames: 50 %, 75 %, 88 %), release 0.1
//      per frame (the light falls over ~0.4 s)
// The tray's safelight is then base x (0.55 + 0.45 x L(t)) (BIBLE 4.3).
const memo = new WeakMap();
export const VOICE_LIGHT = { gate: 2.045, lead: 1.5, lo: 0.5, hi: 0.93, attack: 0.5, release: 0.1 };

export function voiceLight(tl, opts = {}) {
  const o = { ...VOICE_LIGHT, ...opts }, key = JSON.stringify(o);
  let m = memo.get(tl); if (!m) memo.set(tl, (m = new Map()));
  if (m.has(key)) return m.get(key);
  const fps = tl.fps || 24, n = tl.frames || Math.ceil((tl.duration || 160) * fps) + 1, out = new Float32Array(n + 2);
  const fGate = Math.round(o.gate * fps) - o.lead;
  const endOf = f => { const s = tl.shotAtFrame ? tl.shotAtFrame(f) : null; return s ? s.frames[1] - 1 : Infinity; };
  const sm = x => { const t = Math.min(1, Math.max(0, (x - o.lo) / (o.hi - o.lo))); return t * t * (3 - 2 * t); };
  let y = 0;
  for (let f = 0; f < out.length; f++) {
    const e = f < fGate || !tl.hasEnv ? 0 : tl.env(Math.min(f + o.lead, Math.max(f, endOf(f))) / fps);
    const v = sm(e);
    y += (v - y) * (v > y ? o.attack : o.release);
    out[f] = y;
  }
  const fn = t => out[Math.max(0, Math.min(out.length - 1, Math.round(t * fps)))];
  fn.frames = out;
  m.set(key, fn);
  return fn;
}
