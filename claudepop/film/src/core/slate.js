// slate.js - the animatic skeleton (lane A): every shot without a module in src/scenes/ renders as a slate. A neutral
// grey field inside the shot's window (its value follows the register, so the brightness arc reads), the shot id, title,
// source tag, timecode, the shot's text through ctx.type (placeholder type until lane B lands), and a 2-frame tick on
// every beat_hit. It goes through the whole finish chain (post SLATE grade, window mask, HUD canvas) like any scene.
// Every slate label stays inside y 90-990 (design px), clear of the proof-sheet HUD bands at y 40 / 1040, and the
// bottom ruler sits below the subtitle lines (EN 880 / ZH 936).
import * as THREE from 'three';

// display-sRGB value of the field per register (neutral greys; the bright registers flip the labels to INK TYPE)
const FIELD = { DARKROOM: 0x1d, BEAM: 0x16, HALL: 0x34, STUDIO: 0xd6, WHITE: 0xec, CARD: 0x0a, CYANOTYPE: 0x1d };
const BRIGHT = new Set(['STUDIO', 'WHITE']);
const TYPE = '#FAF9F5', INK_TYPE = '#111110';
const MONO = '"IBM Plex Mono", "DejaVu Sans Mono", monospace';

// ACES fit (as post.js) and its inverse, so the field comes out of the post chain at exactly the intended grey
const aces = x => Math.min(1, Math.max(0, (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)));
const srgbToLin = v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
function sceneValueFor(srgb8) {
  const target = srgbToLin(srgb8 / 255); let lo = 0, hi = 16;
  for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if (aces(m) < target) lo = m; else hi = m; }
  return (lo + hi) / 2;
}
const tc = (f, fps) => { const s = Math.floor(f / fps); return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}:${String(f % fps).padStart(2, '0')}`; };
const LANE = { tray: 'C', line: 'D', cards: 'B/D', hall: 'E', studio_beam: 'F' };

export default {
  id: 'SLATE',
  needs: {},
  async init(ctx) {
    this.scene = new THREE.Scene();
    this.mat = new THREE.MeshBasicMaterial({ color: 0x000000, toneMapped: false });
    this.scene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), this.mat));
    this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -1, 1);
  },
  frame(ctx, t, s) {
    const shot = s.shot, tl = ctx.tl, reg = shot.look in FIELD ? shot.look : 'DARKROOM';
    const hit = tl.hitAt(shot, s.f) >= 0 ? tl.hitAt(shot, s.f) : tl.hitAt(shot, s.f - 1);   // 2-frame tick
    const base = FIELD[reg] + (hit >= 0 ? (BRIGHT.has(reg) ? -14 : 16) : 0);
    const v = sceneValueFor(base);
    this.mat.color.setRGB(v, v, v, THREE.LinearSRGBColorSpace);
    return {
      layers: [{ scene: this.scene, camera: this.camera }],
      grade: 'SLATE', post: {}, msaa: 0, hud: { marks: {} },
      text: shot.text,
      overlay: (hud, fr) => drawSlate(hud.ctx, ctx, fr, t, s, reg, hit),
    };
  },
};

// BIBLE 12.1 fallbacks of the consent-pending shots
const SAFE_NOTE = {
  S12: 'the projection spills onto the wall, the clay head out of focus',
  S37: 'the front stops at the hairline',
  S50: 'the turn stops at 60 deg',
  S51: 'contrast and grain only',
};

function drawSlate(c, ctx, fr, t, s, reg, hit) {
  const shot = s.shot, tl = ctx.tl, r = fr.rect, fps = tl.fps;
  const fg = BRIGHT.has(reg) ? INK_TYPE : TYPE;
  const L = r.x + 40, R = r.x + r.w - 40, top = r.y + 86, narrow = r.w < 1000;   // top: the id's cap line sits at y ~93
  c.textBaseline = 'alphabetic'; c.fillStyle = fg; c.strokeStyle = fg; c.letterSpacing = '0px';
  const txt = (s, x, y, size, { w = 400, a = 1, align = 'left', track = 0, max = 0 } = {}) => {
    c.font = `${w} ${size}px ${MONO}`; c.globalAlpha = a; c.textAlign = align; c.letterSpacing = `${track}px`;
    let str = s; if (max) while (str.length > 4 && c.measureText(str).width > max) str = str.slice(0, -2);
    if (str !== s) str = str.replace(/.$/, '…');
    c.fillText(str, x, y); c.letterSpacing = '0px'; return c.measureText(str).width;
  };
  // top-left: id, source tag, title, register / module
  const idw = txt(shot.id, L, top + 38, 44, { w: 500 });
  const src = shot.source === 'GEN' ? `GEN · ${shot.gen && shot.gen.plate || ''}` : shot.source;
  c.font = `500 15px ${MONO}`; c.letterSpacing = '2px'; const sw = c.measureText(src).width;
  c.globalAlpha = 0.85; c.lineWidth = 1; c.strokeRect(L + idw + 18.5, top + 13.5, sw + 18, 26); c.letterSpacing = '0px';
  txt(src, L + idw + 28, top + 32, 15, { w: 500, a: 0.95, track: 2 });
  const titleMax = (narrow ? r.w - 80 : r.w * 0.58);
  txt(shot.title, L, top + 76, 20, { a: 0.95, max: titleMax });
  const live = shot.he_live && (shot.rule_break || tl.live(t)) ? '  ·  HE LIVE' : '';
  txt(`${reg}  ·  ${shot.module.toUpperCase()} (LANE ${LANE[shot.module] || '?'})${live}`, L, top + 104, 14, { a: 0.6, track: 1.5, max: titleMax });
  // camera and HUD notes under the title block (narrow windows: under the timecode block)
  const note = s => String(s || '').replace(/\s+/g, ' ');
  const ny = narrow ? top + 262 : top + 132;
  txt('CAM  ' + note(shot.camera), L, ny, 13, { a: 0.5, max: R - L });
  if (shot.hud) txt('HUD  ' + note(Object.entries(shot.hud).map(([k, v]) => v === true ? k : `${k} ${Array.isArray(v) ? v.join('-') : v}`).join(' · ')), L, ny + 20, 13, { a: 0.5, max: R - L });
  // consent-pending shots (BIBLE 12.1): which version this render is, so the two variants' slates differ
  if (shot.consent || (ctx.flags && ctx.flags.faceSafeShots.includes(shot.id))) {
    const safe = ctx.flags && ctx.flags.safe(shot.id);
    txt((safe ? 'FACE-SAFE FALLBACK  ' + (SAFE_NOTE[shot.id] || '') : 'FULL VERSION (CONSENT PENDING; safe=1 renders the fallback)'),
      L, ny + 40, 13, { w: 500, a: 0.8, max: R - L });
  }
  // top-right: timecode, frame, shot-local time, bar / beat with a 4-step metronome
  const ty = narrow ? top + 150 : top + 36, TX = narrow ? L : R, al = narrow ? 'left' : 'right';
  txt(tc(s.f, fps), TX, ty, 30, { w: 500, align: al, track: 1 });
  txt(`F ${String(s.f).padStart(4, '0')}   ${(s.tl >= 0 ? '+' : '') + s.tl.toFixed(3)} / ${(shot.t1 - shot.t0).toFixed(3)} s`, TX, ty + 28, 14, { a: 0.7, align: al });
  const b = tl.beatAt(t);
  const bw = txt(`BAR ${b.bar} · ${b.beat}`, TX + (narrow ? 0 : -58), ty + 52, 14, { a: 0.7, align: al });
  const mx = narrow ? L + bw + 16 : R - 44;
  for (let i = 0; i < 4; i++) { c.globalAlpha = i + 1 === b.beat ? 0.95 : 0.25; c.fillRect(mx + i * 11, ty + 42, 7, 7); }
  // the beat_hit tick: a hairline across the window top and the hit label, for 2 frames
  if (hit >= 0) {
    const h = shot.beat_hits[hit], w = tl.wordAt(h + 1e-4);
    c.globalAlpha = 1; c.fillRect(r.x, r.y + 88, r.w, 3);
    txt(`HIT ${hit + 1}/${shot.beat_hits.length}   ${h.toFixed(3)}${w && Math.abs(w.t - h) < 0.06 ? `   “${w.w}”` : ''}`, r.x + r.w / 2, narrow ? top + 222 : top + 150, 17, { w: 500, align: 'center', track: 1 });
  }
  // bottom: the shot ruler (bars, hits, playhead); its tick tops (y 954) clear the ZH subtitle, its labels end by y 990
  const y = r.y + r.h - 112;
  const X = tt => L + (R - L) * Math.min(1, Math.max(0, (tt - shot.t0) / (shot.t1 - shot.t0)));
  c.globalAlpha = 0.35; c.fillRect(L, y, R - L, 1);
  for (const d of tl.downbeats) if (d > shot.t0 && d < shot.t1) c.fillRect(Math.round(X(d)), y - 5, 1, 6);
  c.globalAlpha = 0.9; for (const h of shot.beat_hits || []) c.fillRect(Math.round(X(h)) - 1, y - 14, 2, 15);
  c.globalAlpha = 0.95; c.fillRect(L, y - 1, X(t) - L, 3);
  txt(shot.t0.toFixed(3), L, y + 18, 13, { a: 0.55 });
  txt(shot.t1.toFixed(3), R, y + 18, 13, { a: 0.55, align: 'right' });
  c.globalAlpha = 1;
}
