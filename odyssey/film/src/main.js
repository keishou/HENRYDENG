// Timeline driver. window.renderAt(T) draws the frame at time T (seconds) — the
// capture script calls it once per frame, so the film is fully deterministic.
import { Engine } from './engine.js';
import { loadAssets } from './assets.js';
import { loadFonts, TextLayer } from './text.js';
import { Shots } from './shots.js';

const Q = new URLSearchParams(location.search);
const W = +(Q.get('w') || 1920), H = +(Q.get('h') || 1080);
const GRAIN = Q.has('grain') ? +Q.get('grain') : 1;
const TL = await (await fetch('timeline.json')).json();
await loadFonts();
const A = await loadAssets();
const engine = new Engine(document.getElementById('c'), W, H);
const text = new TextLayer(engine, TL);
const shots = new Shots(engine, A, TL);

function resolve(T) {
  const main = TL.scenes.find(s => T >= s.t0 && T < s.t1) || TL.scenes[TL.scenes.length - 1];
  for (const ins of TL.inserts) {
    if (T >= ins.t && T < ins.t + ins.dur) {
      const sc = TL.scenes.find(s => s.id === ins.scene);
      return { id: ins.scene, lt: ins.local + (T - ins.t), dur: sc.t1 - sc.t0, aspect: sc.aspect, main, insert: true };
    }
  }
  return { id: main.id, lt: T - main.t0, dur: main.t1 - main.t0, aspect: main.aspect, main };
}

window.renderAt = T => {
  const r = resolve(T);
  for (const o of [shots.bust, shots.cloud, shots.wire]) o.parent?.remove(o);
  const sh = shots.shot(r.id, r.lt, r.dur);
  text.draw(T, r.main.aspect);
  if (r.insert) Object.assign(sh.post, { flash: 0, fade: 0, exposure: (sh.post.exposure ?? 1) * 1.25 });
  sh.post.grain = (sh.post.grain ?? .07) * GRAIN;
  engine.render(sh, sh.post, T);
  sh.after?.();
  return r.id;
};
window.TL = TL;
window.ready = true;

// Preview: play in real time (no audio) unless driven by the capture script.
if (!Q.has('capture')) {
  const t0 = performance.now() - (+(Q.get('t') || 0)) * 1000;
  const loop = () => { window.renderAt(((performance.now() - t0) / 1000) % TL.duration); requestAnimationFrame(loop); };
  loop();
}
