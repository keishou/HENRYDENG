// Checks of avatar.js in the real page: purity / determinism, loop seams, sequence continuity, root-motion modes,
// start heading of every clip, and pixel determinism of a look-dev frame rendered out of order and in a fresh browser.
//   node avatar_test.mjs        -> prints a JSON report (also claudepop/out/lookdev/avatar_test.json)
import { chromium } from 'playwright-core';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { serve, CHROME, CHROME_ARGS, CLAUDEPOP } from './serve.mjs';

const server = await serve();
const url = `http://127.0.0.1:${server.address().port}/film/lookdev/index.html`;
const open = async () => {
  const browser = await chromium.launch({ executablePath: CHROME, args: CHROME_ARGS });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.log('[err]', e.message));
  await page.goto(url); await page.waitForFunction('window.ready === true', null, { timeout: 600000 });
  return { browser, page };
};
const md5 = b64 => crypto.createHash('md5').update(Buffer.from(b64, 'base64')).digest('hex');
const frame = (page, p) => page.evaluate(p => { window.shot(p); return window.grab(0.95).slice(23); }, p);

const { browser, page } = await open();
const rep = await page.evaluate(() => {
  const av = window.looks.av, out = {};
  const maxAbs = (a, b) => { let m = 0; for (let i = 0; i < a.length; i++) m = Math.max(m, Math.abs(a[i] - b[i])); return m; };
  const qd = (a, b) => { let m = 0; for (let i = 0; i < a.length; i += 4) { const d = Math.abs(a[i] * b[i] + a[i + 1] * b[i + 1] + a[i + 2] * b[i + 2] + a[i + 3] * b[i + 3]); m = Math.max(m, 2 * Math.acos(Math.min(1, d)) * 180 / Math.PI); } return m; };
  // purity
  const p1 = av.pose('walk_runway_loop', 3.3), x = av.pose('lie_down', 5), p2 = av.pose('walk_runway_loop', 3.3);
  out.pose_pure = maxAbs(p1.q, p2.q) === 0 && maxAbs(p1.root, p2.root) === 0;
  const snap = () => av.bones.map(b => b.matrixWorld.elements.slice()).flat();
  av.apply(p1, { breath: {}, noise: {}, hands: {} }, 3.3); const m1 = snap();
  av.apply(x, { breath: {}, noise: {}, hands: {} }, 9.1);
  av.apply(p1, { breath: {}, noise: {}, hands: {} }, 3.3); const m2 = snap();
  out.apply_pure_max_diff = maxAbs(m1, m2);
  // loop seams: per-frame step across the seam vs a typical step
  out.loops = {};
  for (const n of av.clipNames.filter(n => av.clip(n).loop)) {
    const c = av.clip(n), T = c.seconds, dt = 1 / 30;
    const a = av.pose(n, T - dt / 2), b = av.pose(n, T + dt / 2), m0 = av.pose(n, T / 2 - dt / 2), m1_ = av.pose(n, T / 2 + dt / 2);
    const step = (u, v) => Math.hypot(u.root[0] - v.root[0], u.root[1] - v.root[1], u.root[2] - v.root[2]);
    out.loops[n] = { seam_root_step_mm: +(step(a, b) * 1000).toFixed(1), mid_root_step_mm: +(step(m0, m1_) * 1000).toFixed(1),
      seam_max_bone_deg: +qd(a.q, b.q).toFixed(2), mid_max_bone_deg: +qd(m0.q, m1_.q).toFixed(2),
      after_10_cycles_z_m: +av.pose(n, 10 * T).root[2].toFixed(3) };
  }
  // start heading of every clip (0 = facing +Z) and root at t=0
  out.start = {};
  for (const n of av.clipNames) { const p = av.pose(n, 0); out.start[n] = { heading_deg: +(av.heading(p) * 180 / Math.PI).toFixed(1), x: +p.root[0].toFixed(3), z: +p.root[2].toFixed(3) }; }
  // root motion modes
  const L = [];
  for (let t = 0; t < 8; t += 0.5) { const p = av.pose('turn_in_place_ccw', t, { rootMotion: 'lock' }); L.push([p.root[0], p.root[2], av.heading(p)]); }
  out.lock = { max_xz: Math.max(...L.map(v => Math.hypot(v[0], v[1]))), heading_range_deg: +((Math.max(...L.map(v => v[2])) - Math.min(...L.map(v => v[2]))) * 180 / Math.PI).toFixed(2) };
  const off = av.pose('walk_slow', 6, { rootMotion: false }); out.off_xz = Math.hypot(off.root[0], off.root[2]);
  // sequence continuity (no fade -> the only jump at a boundary is the pose change, not the root)
  const seq = av.sequence([{ clip: 'walk_slow_loop', at: 0, loop: true, fade: 0 }, { clip: 'walk_stop_lookup', at: 4.0, from: 3.2, fade: 0 },
    { clip: 'turn_in_place_ccw', at: 7.5, from: 0.5, fade: 0 }], { x: 1, z: -3, yaw: 0.4 });
  out.sequence = seq.segments.map((s, i) => {
    if (!i) return { clip: s.clip };
    const a = seq.pose(s.at - 1e-4), b = seq.pose(s.at + 1e-4);
    return { clip: s.clip, at: s.at, root_jump_mm: +(Math.hypot(a.root[0] - b.root[0], a.root[2] - b.root[2]) * 1000).toFixed(2),
      heading_jump_deg: +(((av.heading(b) - av.heading(a)) * 180 / Math.PI + 540) % 360 - 180).toFixed(2) };
  });
  const seqF = av.sequence([{ clip: 'walk_slow_loop', at: 0, loop: true }, { clip: 'walk_stop_lookup', at: 4.0, from: 3.2, fade: 0.8 }]);
  let worst = 0; for (let t = 3.9; t < 5.0; t += 1 / 240) { const a = seqF.pose(t), b = seqF.pose(t + 1 / 240); worst = Math.max(worst, Math.hypot(a.root[0] - b.root[0], a.root[2] - b.root[2])); }
  out.crossfade_max_root_speed_mps = +(worst * 240).toFixed(3);
  out.beat_speed_runway_on_66bpm = +av.beatSpeed('walk_runway_loop', 66).toFixed(4);
  return out;
});
// pixel determinism: the same frame out of order, and in a fresh browser
const f1 = md5(await frame(page, { look: 'L2', shot: 'wide', t: 2.0 }));
await frame(page, { look: 'L2', shot: 'wide', t: 5.0 });
await frame(page, { look: 'L1', shot: 'close', t: 1.0 });
const f2 = md5(await frame(page, { look: 'L2', shot: 'wide', t: 2.0 }));
const g1 = md5(await frame(page, { look: 'L3', shot: 'medium', t: 1.5 }));
await browser.close();
const b2 = await open();
const f3 = md5(await frame(b2.page, { look: 'L2', shot: 'wide', t: 2.0 }));
const g2 = md5(await frame(b2.page, { look: 'L3', shot: 'medium', t: 1.5 }));
await b2.browser.close(); server.close();
rep.pixels = { L2_same_page_out_of_order: f1 === f2, L2_fresh_browser: f1 === f3, L3_fresh_browser: g1 === g2 };
fs.writeFileSync(path.join(CLAUDEPOP, 'out/lookdev/avatar_test.json'), JSON.stringify(rep, null, 1));
console.log(JSON.stringify(rep, null, 1));
