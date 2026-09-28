// Lane F motion prep (BIBLE 5.7): contact sheets, heel-strike timing, sequence checks, the S54 capture atlas, the
// S30 / S35 print renders and the closed-eye test, all through the film's own code path (motion_prep.html).
//   node motion_prep.mjs gait            M2 A/B contact sheets (front long lens + side)      -> out/film/sheets/M2_*.jpg
//   node motion_prep.mjs strikes         M2 heel strikes on the posed skeleton vs the beat grid -> out/film/data/strikes.json
//   node motion_prep.mjs check           M4 sequence joins, FK, purity                       -> out/film/data/motion_check.json
//   node motion_prep.mjs seqsheets       M4 contact sheets of every sequence                 -> out/film/sheets/M4_<shot>.jpg
//   node motion_prep.mjs m1              M1 sitter front / side sheets in the studio          -> out/film/sheets/M1_*.jpg
//   node motion_prep.mjs lids            M3 closed-eye test at MCU                            -> out/film/sheets/M3_lids.jpg
//   node motion_prep.mjs atlas           M5 S54 side-silhouette atlas                         -> out/film/atlas/S54_captures.{png,json}
//   node motion_prep.mjs prints          M6 S30 / S35 stills under flat studio light          -> out/film/data/S30_print*.png, S35_*.png
// Face renders stay under out/ (gitignored).
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
import { serve, CHROME, CHROME_ARGS, CLAUDEPOP } from './serve.mjs';

const mode = process.argv[2] || 'check';
const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i < 0 ? d : process.argv[i + 1]; };
const OUT = path.join(CLAUDEPOP, 'out/film');
for (const d of ['sheets', 'data', 'atlas', 'previs']) fs.mkdirSync(path.join(OUT, d), { recursive: true });
const server = await serve();
const browser = await chromium.launch({ executablePath: CHROME, args: CHROME_ARGS });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.on('pageerror', e => console.log('[err]', e.message));
page.on('console', m => { if (/error|warn/i.test(m.type())) console.log('[page]', m.text()); });
await page.goto(`http://127.0.0.1:${server.address().port}/film/lookdev/motion_prep.html`);
await page.waitForFunction('window.ready === true', null, { timeout: 600000 });
const sheetPage = await browser.newPage({ viewport: { width: 1600, height: 900 } });
const frame = o => page.evaluate(o => window.frame(o), o);
const save = (file, dataUrl) => fs.writeFileSync(file, Buffer.from(dataUrl.split(',')[1], 'base64'));

async function sheet(file, title, cells, cols, cw, ch, note = '') {
  const html = cells.map(c => `<div style="position:relative;width:${cw}px;height:${ch}px;overflow:hidden"><img src="${c.img}" width="${cw}" height="${ch}">
    <span style="position:absolute;left:6px;top:4px;color:#ffd24a;font:12px monospace;text-shadow:0 0 3px #000">${c.label || ''}</span>
    ${c.label2 ? `<span style="position:absolute;left:6px;bottom:4px;color:#9fe0ff;font:11px monospace;text-shadow:0 0 3px #000">${c.label2}</span>` : ''}</div>`).join('');
  await sheetPage.setViewportSize({ width: cols * cw, height: 200 });
  await sheetPage.setContent(`<body style="margin:0;background:#111;width:${cols * cw}px"><div style="color:#eee;font:14px monospace;padding:8px">${title}</div>
    ${note ? `<div style="color:#aaa;font:12px monospace;padding:0 8px 8px">${note}</div>` : ''}
    <div style="display:flex;flex-wrap:wrap;width:${cols * cw}px">${html}</div></body>`);
  await sheetPage.screenshot({ path: file, type: 'jpeg', quality: 88, fullPage: true });
  console.log('wrote', path.relative(CLAUDEPOP, file));
}

// heel strikes from tracked heel heights: the heel falls through (planted + 1.2 cm) after a swing above (planted + 3 cm)
function strikesOf(tr, key) {
  const y = tr[key].map(p => p[1]), t = tr.t;
  const g = [...y].sort((a, b) => a - b)[Math.floor(y.length * 0.05)];
  const out = []; let armed = false;
  for (let i = 1; i < y.length; i++) {
    if (y[i] > g + 0.03) armed = true;
    if (armed && y[i - 1] >= g + 0.012 && y[i] < g + 0.012) {
      const a = (y[i - 1] - (g + 0.012)) / (y[i - 1] - y[i]);
      out.push(t[i - 1] + a * (t[i] - t[i - 1])); armed = false;
    }
  }
  return out;
}
const T0 = 0.2356, BEAT = 60 / 132;

if (mode === 'strikes') {
  const shots = (arg('shots', 'S15,S28,S54,S43a,S43b,S43c,S43d,S41')).split(',');
  const res = {};
  for (const id of shots) {
    const spec = await page.evaluate(id => { const s = window.SEQ.SHOTS[id]; return { strikes: s.strikes, t0: s.t0, t1: s.t1 }; }, id);
    const win = spec.strikes || { from: spec.t0, to: spec.t1 };
    const tr = await page.evaluate(o => window.heelTrack(o), { shot: id, t0: win.from - 0.6, t1: win.to + 0.1, dt: 1 / 480 });
    const all = [...strikesOf(tr, 'LH').map(t => ['L', t]), ...strikesOf(tr, 'RH').map(t => ['R', t])]
      .filter(([, t]) => t >= win.from - 0.05 && t <= win.to).sort((a, b) => a[1] - b[1]);
    const rows = all.map(([foot, t]) => {
      const n = Math.round((t - T0) / BEAT), tb = T0 + n * BEAT, bar = Math.floor(n / 4) + 1, beat = (n % 4) + 1;
      // expected grid for half-time walks: beats 1 and 3; S43 / S41 cut-beat strikes: any beat
      return { foot, t: +t.toFixed(4), beat_t: +tb.toFixed(4), bar, beat, err_ms: +((t - tb) * 1000).toFixed(1), err_frames: +((t - tb) * 24).toFixed(2),
        frame: Math.round(t * 24), beat_frame: Math.round(tb * 24) };
    });
    const halfOK = rows.every(r => /^S4[13]/.test(id) || r.beat === 1 || r.beat === 3);
    res[id] = { window: win, strikes: rows, max_abs_err_frames: Math.max(0, ...rows.map(r => Math.abs(r.err_frames))), on_beats_1_3: halfOK,
      alternating: rows.every((r, i) => !i || r.foot !== rows[i - 1].foot) };
    console.log(id, JSON.stringify({ n: rows.length, max_err_frames: res[id].max_abs_err_frames, on_beats_1_3: halfOK, alt: res[id].alternating }));
    for (const r of rows) console.log('   ', r.foot, r.t, `bar ${r.bar} beat ${r.beat}`, `${r.err_ms} ms`, `${r.err_frames} f`, `frame ${r.frame} vs ${r.beat_frame}`);
  }
  fs.writeFileSync(path.join(OUT, 'data/strikes.json'), JSON.stringify(res, null, 1));
}

if (mode === 'check') {
  const r = await page.evaluate(() => window.check());
  fs.writeFileSync(path.join(OUT, 'data/motion_check.json'), JSON.stringify(r, null, 1));
  console.log(JSON.stringify(r, null, 1));
}

if (mode === 'gait') {
  // M2 A/B: one full cycle at half time (2 steps = 4 beats) every 3 frames, front (S15 long lens) and side
  const variants = [
    { key: 'A', clip: 'walk_runway_sym_loop', label: 'A  walk_runway_sym_loop (symmetric)' },
    { key: 'A0', clip: 'walk_runway_loop', label: 'A0 walk_runway_loop (as captured)' },
    { key: 'B', clip: 'walk_slow_loop', label: 'B  walk_slow_loop' },
  ];
  for (const v of variants) {
    const info = await page.evaluate(c => { const k = window.av.clip(c); return { step: k.loop_info.step_period_s, strikes: k.gait.heel_strikes, cyc: k.seconds }; }, v.clip);
    const speed = +(info.step / (2 * BEAT)).toFixed(4);
    const cells = [];
    const n = 16, film = 4 * BEAT;               // two steps at half time
    for (const view of ['front', 'side']) for (let i = 0; i < n; i++) {
      const tf = i * film / n, tc = info.strikes[0].t + tf * speed;
      const cam = view === 'front' ? { pos: [0, 1.55, 11], target: [0, 0.95, 0], fov: 11 } : { pos: [5.2, 1.0, 0], target: [0, 0.9, 0], fov: 22 };
      const img = await frame({ envName: 'grid', clip: v.clip, t: tc, speed: 1, loop: true, cam, follow: view === 'front' ? { off: [0, 1.55, 11], aim: [0, 0.95, 0] } : { off: [5.2, 1.0, 0], aim: [0, 0.9, 0] }, w: 220, h: 300, layers: { hands: { curl: 0.5 }, breath: { amp: 0.8 } } });
      cells.push({ img, label: `${view} +${Math.round(tf * 24)}f`, label2: i % 4 === 0 ? `beat ${i / 4 + 1}` : '' });
    }
    await sheet(path.join(OUT, `sheets/M2_${v.key}.jpg`), `M2 ${v.label} | half-time speed ${speed} (step ${info.step}s -> ${(2 * BEAT).toFixed(3)}s) | strikes ${JSON.stringify(info.strikes.map(s => s.foot + '@' + s.t))}`,
      cells, 16, 220, 300, 'one gait cycle = 2 steps = 4 beats at half time; frames every 1/16 of it (~2.7 film frames); heel strikes on beats 1 and 3');
  }
}

if (mode === 'strip') {
  // consecutive film frames of one half-time step (S54), side view following the root, warp off vs on
  const t0 = +arg('t0', 145.6902), n = +arg('n', 24);
  const cells = [];
  for (const wv of (arg('warps', '0,0.25')).split(',').map(Number)) {
    await page.evaluate(a => window.SEQ.setGaitWarp(a), wv);
    for (let k = 0; k < n; k++) {
      const t = t0 + k / 24;
      cells.push({ img: await frame({ envName: 'grid', shot: 'S54', t, cam: { fov: 22 }, follow: { off: [-4.6, 1.0, 0], aim: [0, 0.9, 0] }, w: 150, h: 230, layers: { hands: { curl: 0.5 } } }),
        label: `w${wv} f${k}`, label2: k === 0 ? 'strike' : k === 22 ? 'strike' : '' });
    }
  }
  await page.evaluate(() => window.SEQ.setGaitWarp(0.25));
  await sheet(path.join(OUT, 'sheets/M2_strip.jpg'), `M2 spacing: consecutive 24 fps frames of one half-time step (S54 from ${t0}), row per warp amount`, cells, n, 150, 230);
}

if (mode === 'seqsheets') {
  const plans = {
    S15: { times: [38.4174, 38.63, 39.0, 39.3265, 40.236, 41.145, 44.0, 47.5, 49.3, 50.236, 50.6, 50.9, 51.145, 51.6, 52.5, 52.95], cam: { pos: [0, 1.55, 0], target: [0, 1.25, -12], fov: 11 } },
    S54: { times: [140.2356, 140.69, 141.145, 142.054, 143.872, 145.69, 147.51, 149.33, 150.24, 151.145, 151.6, 152.05, 152.5, 153.5, 154.5, 155.6], cam: { pos: [0, 1.55, 0], target: [0, 1.25, -12], fov: 12 } },
    S28: { times: [81.0, 81.145, 81.365, 81.6, 81.8, 82.0, 82.054, 82.15, 82.25, 82.35, 82.45, 82.53, 82.7, 82.96, 83.3, 83.6], follow: { off: [0, 1.5, 2.5], aim: [0, 1.2, -4] }, cam: { fov: 20 } },
    S41: { times: [113.36, 113.8, 113.95, 114.02, 114.1, 114.15, 114.2, 114.25, 114.3, 114.327, 114.4, 114.45, 114.5, 114.6, 114.67, 115.2], cam: { pos: [0, 1.62, 2.4], target: [0, 1.5, 0], fov: 16 } },
  };
  for (const [id, pl] of Object.entries(plans)) {
    const cells = [];
    for (const view of ['shot', 'top']) for (const t of pl.times) {
      let cam = pl.cam, follow = pl.follow;
      if (view === 'top') {
        const m = await page.evaluate(([id, t]) => { const p = window.SEQ.poseAt(window.av, id, t); return [p.root[0], p.root[2]]; }, [id, t]);
        cam = { pos: [m[0] + 3.2, 2.4, m[1] + 0.6], target: [m[0], 0.8, m[1]], fov: 30 }; follow = null;
      }
      const img = await frame({ envName: 'grid', shot: id, t, cam: follow ? { ...cam, pos: [0, 0, 0], target: [0, 0, 0] } : cam, follow, w: 220, h: 260, lens: cam.pos || [0, 1.55, 0] });
      cells.push({ img, label: `${view} ${t.toFixed(3)}`, label2: `f${Math.round(t * 24)}` });
    }
    await sheet(path.join(OUT, `sheets/M4_${id}.jpg`), `M4 ${id} sequence (film times; row 1 shot camera, row 2 side / 3-4 view following the root)`, cells, 16, 220, 260);
  }
}

if (mode === 'm1') {
  const clip = arg('clip', 'pose_sit_stool_upright');
  const st = await page.evaluate(c => window.av.clip(c).props.stool, clip);
  const place = { x: -st.x, z: -st.z };      // the seat centre on the tape X at the origin
  const views = [
    ['front 50mm', { pos: [0, 1.25, 3.4], target: [0, 0.78, 0], fov: 30 }],
    ['front 3/4 L', { pos: [2.0, 1.2, 2.8], target: [0, 0.78, 0], fov: 30 }],
    ['side (from +X)', { pos: [3.4, 0.9, 0.15], target: [0, 0.78, 0.15], fov: 30 }],
    ['side (from -X)', { pos: [-3.4, 0.9, 0.15], target: [0, 0.78, 0.15], fov: 30 }],
    ['hands close L', { pos: [0.75, 1.05, 1.0], target: [0.12, 0.68, 0.22], fov: 30 }],
    ['hands close R', { pos: [-0.75, 1.05, 1.0], target: [-0.12, 0.68, 0.22], fov: 30 }],
    ['top', { pos: [0.01, 3.2, 0.9], target: [0, 0.6, 0.1], fov: 30 }],
    ['back 3/4', { pos: [-2.0, 1.3, -2.6], target: [0, 0.78, 0], fov: 30 }],
    ['feet close', { pos: [0.2, 0.35, 1.4], target: [0, 0.12, 0.35], fov: 30 }],
  ];
  const cells = [];
  for (const [label, cam] of views) {
    const img = await frame({ envName: 'studio', clip, t: 0, place, cam, w: 420, h: 540, layers: { breath: { amp: 0 } } });
    cells.push({ img, label });
  }
  const ck = await page.evaluate(c => window.av.clip(c).checks, clip);
  await sheet(path.join(OUT, `sheets/M1_${clip}.jpg`), `M1 ${clip} on the 0.60 m stool (flat studio light) | seat centre z ${st.z} (clip space)`, cells, 5, 420, 540,
    JSON.stringify(ck).slice(0, 400));
}

if (mode === 'lids') {
  const cells = [];
  const cams = [['MCU 85mm', { pos: [0, 1.62, 2.1], target: [0, 1.55, 0], fov: 16 }], ['CU', { pos: [0, 1.66, 0.9], target: [0, 1.64, 0], fov: 16 }],
    ['CU 20deg', { pos: [0.31, 1.66, 0.85], target: [0, 1.64, 0], fov: 16 }]];
  const closes = (arg('close', '0,0.5,1')).split(',').map(Number);
  const up = +arg('up', 30), lo = +arg('lo', 6);
  for (const [label, cam] of cams) for (const c of closes) {
    const img = await frame({ envName: 'grid', clip: 'stand_breathe_loop', t: 0, cam, w: 420, h: 420,
      layers: { hands: { curl: 0.5 }, lids: { close: c, upperDeg: up, lowerDeg: lo } } });
    cells.push({ img, label: `${label} close ${c}`, label2: `upper ${up} lower ${lo}` });
  }
  await sheet(path.join(OUT, `sheets/M3_lids_u${up}_l${lo}.jpg`), `M3 lid bones closed-eye test (stand_breathe_loop, grid light)`, cells, closes.length * 3, 420, 420);
}

if (mode === 'atlas') {
  const times = await page.evaluate(() => window.SEQ.CAPTURES_S54);
  const r = await page.evaluate(o => window.atlas(o), { shot: 'S54', times, cellW: +arg('cw', 280), cellH: +arg('ch', 360), cols: 13 });
  save(path.join(OUT, 'atlas/S54_captures.png'), r.png);
  const meta = { shot: 'S54', note: 'side-view silhouettes of the S54 walk at the capture times (white = figure, black = empty); orthographic, camera on the figure\'s right (-X) so he walks left -> right; figure height scale fixed (cell height = span m), ground line at `ground` of the cell height from the bottom',
    cols: r.cols, rows: r.rows, cellW: r.cellW, cellH: r.cellH, span_m: r.span, ground: r.ground, captures: r.meta };
  fs.writeFileSync(path.join(OUT, 'atlas/S54_captures.json'), JSON.stringify(meta, null, 1));
  console.log('atlas', r.cols, 'x', r.rows, 'cells', r.meta.length);
}

if (mode === 'prints') {
  // S30: seated on the studio floor, knees drawn up, looking into the lens; a 4:5 print, frontal, eye level, 50 mm
  const t30 = +arg('t30', 0.0);
  const w = +arg('w', 1600), h = Math.round(w * 5 / 4);
  const cam30 = { pos: [0, 0.62, 3.6], target: [0, 0.46, 0], fov: 27 };
  const p30 = await page.evaluate(t => { const p = window.av.pose('sit_floor', t); return [p.root[0], p.root[2]]; }, t30);
  const place30 = { x: -p30[0], z: -p30[1] + 0.1 };
  let img = await frame({ envName: 'studio', clip: 'sit_floor', t: t30, place: place30, stool: false, cam: cam30, w, h, fmt: 'png',
    layers: { hands: { curl: 0.45 }, look: { target: cam30.pos, weight: 1, maxDeg: 50 } } });
  save(path.join(OUT, 'data/S30_print.png'), img);
  save(path.join(OUT, 'previs/S30_print.jpg'), await frame({ envName: 'studio', clip: 'sit_floor', t: t30, place: place30, stool: false, cam: cam30, w, h, q: 0.93,
    layers: { hands: { curl: 0.45 }, look: { target: cam30.pos, weight: 1, maxDeg: 50 } } }));
  // S35: on the stool, face in hands; 16:9, eye level, 35 mm, flat light; plus the alpha matte version for the comp
  const st = await page.evaluate(() => window.av.clip('pose_sit_stool_face_in_hands').props.stool);
  const place35 = { x: -st.x, z: -st.z };
  const cam35 = { pos: [0, 1.15, 3.9], target: [0, 0.8, 0], fov: 38 };
  const W = +arg('w35', 1920), H = Math.round(W * 9 / 16);
  save(path.join(OUT, 'data/S35_still.png'), await frame({ envName: 'studio', clip: 'pose_sit_stool_face_in_hands', t: 0, place: place35, cam: cam35, w: W, h: H, fmt: 'png', layers: {} }));
  save(path.join(OUT, 'data/S35_matte.png'), await frame({ envName: 'studio', clip: 'pose_sit_stool_face_in_hands', t: 0, place: place35, cam: cam35, w: W, h: H, fmt: 'png', layers: {}, transparent: true, stool: true }));
  save(path.join(OUT, 'previs/S35_first.jpg'), await frame({ envName: 'studio', clip: 'pose_sit_stool_face_in_hands', t: 0, place: place35, cam: cam35, w: W, h: H, q: 0.93, layers: {} }));
  fs.writeFileSync(path.join(OUT, 'data/prints.json'), JSON.stringify({
    S30: { file: 'out/film/data/S30_print.png', clip: 'sit_floor', t: t30, place: place30, camera: cam30, size: [w, h], light: 'flat studio (hemisphere + frontal soft key from the camera)' },
    S35: { file: 'out/film/data/S35_still.png', matte: 'out/film/data/S35_matte.png (RGBA, figure + stool over transparent)', clip: 'pose_sit_stool_face_in_hands', place: place35, camera: cam35, size: [W, H] },
  }, null, 1));
  console.log('prints written');
}

await browser.close(); server.close();
