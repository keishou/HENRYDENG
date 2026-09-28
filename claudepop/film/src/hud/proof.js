// proof.js - the proof-sheet HUD (BIBLE 6.7; lane B): the machine's telemetry about its own printing. It never carries
// lyrics. At most two HUD elements per frame (+ one type block, which type.js owns); the registration marks and the
// EDGE OF PHOTOGRAPH hairlines are frame furniture and do not count. Everything lays out relative to the current window
// rect and moves out as it widens. Pure function of (hudState, window, t).
//
//   const proof = new Proof(ctx)
//   proof.draw(hudState, windowRect, t)      draws into ctx.hud (1920x1080 design space)
//     hudState  frameSpec.hud. Fields a scene sets override the film's HUD track for that frame; fields it leaves
//               undefined come from the track (BIBLE 6.7 values, evaluated from shots.json "hud" and the section
//               densities), so a scene can return hud: {} (or omit it) and get the designed HUD:
//               { proof: '0480' | null, wedge: '+2' | null, slug: 'ENLARGER 32 s · f/8 · GRADE 3 · 20 °C' | null,
//                 caption: 'PL. ...' | null, job: true | null, counter: 'ENLARGEMENT ×64' | null,
//                 marks: { doubled: 0..1, rotate: deg, alpha } | null, edges: bool | null, ink: bool, hidden: bool }
//               null hides an element; hidden: true hides the whole HUD; ink: INK digits / labels (white register).
//     windowRect { x, y, w, h } design px
//   proof.stateAt(t, shot?) -> the track's evaluated state at t (what draw() merges under the scene's fields)
//   proof.elements(hudState, t) -> [{ key, text, listed }] the elements that survive the density / 2-element rule
//   proof.proofAt(t) -> the PROOF Nº string at t (or null)
//
// Layout (design px): marks (24 px, hairline, TYPE 40 %) centred 40 px outside the window corners, or 40 px inside
// the frame corners when the window is full width. Marks outside the window sit on the INK surround, so they are always
// TYPE at 40 % (whatever the register); only marks inside a full-width window follow the register (INK TYPE on the white
// registers). Text elements share the marks' centre line (y 40 / 1040); PROOF Nº top right (IBM Plex Mono 500, 20 px;
// digits TYPE until "sparks" (2.852, BIBLE 3 / 6.7: the catchlights are the first colour inside the window), VOICE
// after); job line / plate caption / counter top left (15 px); step wedge on
// the left edge (11 patches PAPER -> INK, VOICE marker, "+n STOP"); slug line bottom centre (14 px). Every element
// types on with a block cursor (2 characters per frame; captions 3) when its run starts.
const TYPE = '#FAF9F5', INK_TYPE = '#111110', VOICE = '#D97757';
const MONO = '"IBM Plex Mono", "Noto Sans SC", monospace';
const F = (T, fps = 24) => Math.round(T * fps);
const clamp01 = x => Math.max(0, Math.min(1, x));
const fmt = n => n < 10000 ? String(n).padStart(4, '0') : n.toLocaleString('en-US');
const SLUG_TAIL = ' · f/8 · GRADE 3 · 20 °C';
const KEYS = ['job', 'caption', 'counter', 'wedge', 'slug', 'proof'];   // priority when more than two want the frame
const LIMIT = { premise: 0, low: 1, medium: 2, off: 0, none: 0, proof: 1, end: 0, card: 0 };
const VOICE_DIGITS_FROM = 2.852;   // "sparks": the first colour inside the window is the catchlights (BIBLE 3, 6.7)

export class Proof {
  constructor(ctx) {
    this.ctx = ctx; this.tl = ctx.tl; this.fps = ctx.tl.fps;
    this._runs = null;
  }

  // ------------------------------------------------------------------------------------------------ the track
  density(t, shot) {
    const f = F(t, this.fps), sec = this.tl.sectionAt(t), d = String(sec.hud_density || 'low');
    if (/card/i.test(shot.window || '')) return 'card';
    if (f >= F(133.38) && f < F(140.2356)) return 'none';
    if (/^none/.test(d)) return 'none';
    if (/PROOF only/i.test(d)) return 'proof';
    if (/end slug/i.test(d)) return 'end';
    if (/^off/.test(d)) return 'off';
    if (/^premise/.test(d)) return f >= F(2.045) ? 'low' : 'premise';
    if (/medium/.test(d)) return 'medium';
    return 'low';
  }

  proofAt(t) {
    const tl = this.tl, fps = this.fps, f = F(t, fps), R = T => f >= F(T, fps);
    const count = (ts) => ts.filter(R).length;
    let n = null;
    if (!R(2.045)) n = null;
    else if (!R(7.725)) n = 1;
    else if (!R(9.545)) n = 2 + count([7.9629, 8.4174, 8.872, 9.3265]);                  // S03: a print per beat
    else if (!R(16.5992)) n = 6;
    else if (!R(23.872)) n = 7;                                                          // the one exposure
    else if (!R(33.4)) n = Math.min(24, 7 + count(tl.gridTimes(1, 23.872, 33.4)));       // chorus 1: a print a beat
    else if (!R(35.6)) n = Math.min(60, 24 + (f - F(33.4, fps)));                        // S13: the 36 frames
    else if (!R(38.4174)) n = 60;
    else if (!R(52.9629)) n = 200 + 10 * Math.min(28, count(tl.gridTimes(2, 45.6902, 52.9629)));  // S15: a row per 8th
    else if (!R(57.945)) n = 480;
    else if (!R(72.9629)) n = 479;                                                       // S17b: the only decrement
    else if (!R(77.725)) n = 12288;                                                      // S25, bar 41
    else if (!R(118.887)) n = 12288 * 2 ** count([78.4174, 78.872, 79.3265]);            // S27: x2 per beat -> 98,304
    else if (!R(129.83)) n = 100000;                                                     // S44
    else if (!R(131.995)) n = 2 ** (17 + count(tl.shot('S51') ? tl.shot('S51').internal_cuts || [] : []));   // S51: 2^n
    else if (!R(133.38)) n = 2 ** 26 + 1;                                                // S52: one more sheet
    else if (!R(140.2356)) n = null;
    else if (!R(152.9629)) {                                                             // S54-S55: spinning
      const base = String(2 ** 26 + 1).split('').map(Number);
      const k = Math.min(base.length, 2 + Math.floor((t - 140.2356) / (152.508 - 140.2356) * (base.length - 1)));
      const dig = base.map((d, i) => i >= base.length - k ? hashDigit(f, i) : d);
      return Number(dig.join('')).toLocaleString('en-US');
    }
    return n === null ? null : fmt(n);
  }

  // the track's state for time t (BIBLE 6.7 + shots.json "hud")
  stateAt(t, shot = null) {
    const tl = this.tl, fps = this.fps, f = F(t, fps);
    shot = shot || tl.shotAtFrame(f);
    const h = shot.hud || {}, d = this.density(t, shot), st = { listed: new Set(), density: d };
    st.ink = /STUDIO|WHITE/.test(shot.look || ''); st.inkDigits = shot.look === 'WHITE';   // the white registers
    const inWin = v => Array.isArray(v) ? f >= F(v[0], fps) && f < F(v[1], fps) : !!v;
    // marks: frame furniture from frame 0; not on the black cards, in the breakdown or the silence
    st.marks = (d === 'none' || d === 'off' || d === 'proof' || d === 'card') ? null : {};
    if (st.marks && shot.id === 'S06') st.marks.doubled = 1 - smooth((t - 16.5992) / (21.36 - 16.5992));
    if (st.marks && f >= F(82.0, fps)) st.marks.rotate = 90 * smooth((f - F(82.0, fps) + 1) / 6);
    st.edges = shot.id === 'S06' && Array.isArray(h.edge_labels) && f < F(h.edge_labels[1], fps) + 4 ? clamp01((F(h.edge_labels[1], fps) + 4 - f) / 5) : null;
    if (d === 'none' || d === 'premise' || d === 'end') return st;
    if (d === 'card' && shot.id !== 'S18') return st;
    const proof = this.proofAt(t);
    if (d === 'proof') { st.proof = proof; st.listed.add('proof'); return st; }
    // listed elements (shots.json)
    if (h.job_line && inWin(h.job_line)) { st.job = true; st.listed.add('job'); }
    let cap = h.caption;
    if (cap === undefined) {                           // lettered shots (S43a-d) keep their first sibling's caption
      const m = /^(S\d+)([a-z])$/.exec(shot.id);
      if (m) for (const s of tl.shots) { if (s === shot) break; if (s.id.startsWith(m[1]) && s.hud && s.hud.caption) cap = s.hud.caption; }
    }
    if (cap) { st.caption = cap; st.listed.add('caption'); }
    if (h.counter) { st.counter = this._counter(shot, t); st.listed.add('counter'); }
    const wedge = h.wedge || (shot.id === 'S18' ? '+2' : null);
    if (wedge) { st.wedge = wedge; st.listed.add('wedge'); }
    if (h.slug && d !== 'off' && d !== 'card') { st.slug = /·/.test(h.slug) ? h.slug : h.slug + SLUG_TAIL; st.listed.add('slug'); }
    if (d === 'off' || d === 'card') { for (const k of KEYS) if (k !== 'wedge') { delete st[k]; st.listed.delete(k); } return st; }
    st.proof = proof;
    if (h.proof !== undefined && proof) st.listed.add('proof');
    return st;
  }
  _counter(shot, t) {
    const k = (shot.beat_hits || []).filter(x => F(t, this.fps) >= F(x, this.fps)).length;
    return 'ENLARGEMENT ×' + (4 ** k).toLocaleString('en-US');
  }

  // merge the scene's fields over the track and apply the density / two-element rule
  resolve(scene, t) {
    const shot = this.ctx.frame && this.ctx.frame.shot && F(this.ctx.frame.t, this.fps) === F(t, this.fps) ? this.ctx.frame.shot : this.tl.shotAt(t);
    const auto = this.stateAt(t, shot);
    const st = { ...auto };
    const listed = new Set(auto.listed);
    for (const [k, v] of Object.entries(scene || {})) {
      if (v === undefined) continue;
      if (k === 'marks') { st.marks = v === null ? null : (auto.marks === null && Object.keys(v).length === 0 ? null : { ...(auto.marks || {}), ...v }); continue; }
      st[k] = v;
      if (KEYS.includes(k)) { if (v === null || v === false) listed.delete(k); else listed.add(k); }
    }
    const limit = LIMIT[auto.density] ?? 2;
    const els = [];
    for (const k of KEYS) if (st[k] && listed.has(k)) els.push({ key: k, text: st[k], listed: true });
    for (const k of KEYS) if (st[k] && !listed.has(k) && els.length < limit) els.push({ key: k, text: st[k], listed: false });
    st.els = els.slice(0, 2);
    return st;
  }
  elements(scene, t) { return this.resolve(scene, t).els.map(({ key, text, listed }) => ({ key, text, listed })); }

  // the frame each element's current run started (for the type-on), from the track; scene-only elements: the shot start
  runStart(key, text, t) {
    if (!this._runs) this._buildRuns();
    const f = F(t, this.fps), r = this._runs[key];
    if (r) for (let i = r.length - 1; i >= 0; i--) if (r[i][0] <= f && f < r[i][1] && (key !== 'caption' || r[i][2] === text)) return r[i][0];
    return this.tl.shotAtFrame(f).frames[0];
  }
  _buildRuns() {
    this._runs = {};
    let prev = {};
    for (let f = 0; f < this.tl.frames; f++) {
      const st = this.resolve({}, f / this.fps), cur = {};
      for (const e of st.els) cur[e.key] = e.key === 'caption' || e.key === 'wedge' ? String(e.text) : '1';
      for (const k of KEYS) {
        if (cur[k] !== undefined && prev[k] === cur[k]) this._runs[k][this._runs[k].length - 1][1] = f + 1;
        else if (cur[k] !== undefined) (this._runs[k] ||= []).push([f, f + 1, cur[k]]);
      }
      prev = cur;
    }
  }

  // ------------------------------------------------------------------------------------------------ drawing
  draw(scene, r, t) {
    try { this._draw(scene, r, t); } catch (e) { console.error('proof.draw', e); }
  }
  _draw(scene, r, t) {
    if (!scene || scene.hidden) return;
    const hud = this.ctx.hud, c = hud.ctx, fps = this.fps, f = F(t, fps);
    const st = this.resolve(scene, t);
    const col = st.ink ? INK_TYPE : TYPE;
    const hair = Math.max(1, 1 / hud.s);
    const full = r.x < 64;
    const inset = full ? (st.marks ? 84 : 32) : 32;        // past the marks when they sit inside the frame
    const yT = 40, yB = 1040;
    c.save(); c.textBaseline = 'alphabetic'; c.shadowBlur = 0;

    // registration marks (furniture)
    if (st.marks) {
      const m = st.marks, a = m.alpha ?? 0.4, rot = (m.rotate || 0) * Math.PI / 180;
      const cs = full ? [[40, 40], [1880, 40], [40, 1040], [1880, 1040]] : [[r.x - 40, 40], [r.x + r.w + 40, 40], [r.x - 40, 1040], [r.x + r.w + 40, 1040]];
      c.strokeStyle = full ? col : TYPE; c.lineWidth = hair;      // outside the window: on INK, always TYPE
      for (const [x, y] of cs) {
        mark(c, x, y, rot, a);
        if (m.doubled > 0.002) {                          // S06: the ghost set, offset like the projection, converging
          const gx = (x - 960) * (1.1 - 1) * m.doubled + r.w * 0.06 * m.doubled, gy = (y - 540) * 0.1 * m.doubled - 1080 * 0.04 * m.doubled;
          mark(c, x + gx, y + gy, rot, a * 0.8);
        }
      }
    }
    // EDGE OF PHOTOGRAPH (S06, one bar): the 7:9 edges as hairlines inside the new window
    if (st.edges) {
      const a = 0.38 * st.edges;
      c.globalAlpha = a; c.fillStyle = col;
      for (const x of [540, 1380]) c.fillRect(x - hair / 2, 0, hair, 1080);
      c.font = `400 12px ${MONO}`; c.letterSpacing = '1.8px'; c.globalAlpha = 0.6 * st.edges;
      c.save(); c.translate(540 - 10, 540); c.rotate(-Math.PI / 2); c.textAlign = 'center'; c.fillText('EDGE OF PHOTOGRAPH', 0, 0); c.restore();
      c.save(); c.translate(1380 + 10, 540); c.rotate(Math.PI / 2); c.textAlign = 'center'; c.fillText('EDGE OF PHOTOGRAPH', 0, 0); c.restore();
      c.letterSpacing = '0px';
    }

    // elements
    const typeOn = (key, str, rate = 2) => { const f0 = this.runStart(key, key === 'caption' ? str : null, t); return Math.min(str.length, Math.max(0, (f - f0 + 1) * rate)); };
    const left = r.x + inset, right = r.x + r.w - inset;
    let tlUsed = false;
    for (const e of st.els) {
      if (e.key === 'proof') {
        const digits = String(e.text), label = 'PROOF Nº ';
        c.font = `500 20px ${MONO}`; c.letterSpacing = '2px'; c.textAlign = 'left';
        const all = label + digits, n = typeOn('proof', all);
        const wAll = c.measureText(all).width, x0 = right - wAll, y = yT + 7;
        const shownL = all.slice(0, Math.min(n, label.length)), shownD = n > label.length ? digits.slice(0, n - label.length) : '';
        c.globalAlpha = 0.72; c.fillStyle = col; c.fillText(shownL, x0, y);
        c.globalAlpha = 1; c.fillStyle = st.inkDigits ? INK_TYPE : f < F(VOICE_DIGITS_FROM, fps) ? col : VOICE;
        c.fillText(shownD, x0 + c.measureText(label).width, y);
        if (n < all.length) cursor(c, x0 + c.measureText(all.slice(0, n)).width, y, 20, col);
      } else if (e.key === 'job' || e.key === 'caption' || e.key === 'counter') {
        if (tlUsed) continue; tlUsed = true;
        const lines = e.key === 'job' ? (r.w < 1500 ? ['LATENT IMAGE · JOB 0928', 'FROM 1 PHOTOGRAPH · FRONT ONLY'] : ['LATENT IMAGE · JOB 0928 · FROM 1 PHOTOGRAPH · FRONT ONLY']) : [String(e.text)];
        c.font = `${e.key === 'caption' ? 400 : 500} 15px ${MONO}`; c.letterSpacing = '1.5px'; c.textAlign = 'left'; c.fillStyle = col;
        let budget = typeOn(e.key, lines.join('\n'), e.key === 'caption' ? 3 : 2);
        lines.forEach((s, i) => {
          const n = Math.max(0, Math.min(s.length, budget)); budget -= s.length + 1;
          const y = yT + 5 + i * 22;
          c.globalAlpha = e.key === 'caption' ? 0.86 : 0.8; c.fillText(s.slice(0, n), left, y);
          if (n > 0 && n < s.length) cursor(c, left + c.measureText(s.slice(0, n)).width, y, 15, col);
        });
      } else if (e.key === 'slug') {
        const s = String(e.text);
        c.font = `400 14px ${MONO}`; c.letterSpacing = '1.4px'; c.textAlign = 'left'; c.fillStyle = col;
        const n = typeOn('slug', s), w = c.measureText(s).width, x0 = r.x + r.w / 2 - w / 2, y = yB + 5;
        c.globalAlpha = 0.72; c.fillText(s.slice(0, n), x0, y);
        if (n < s.length) cursor(c, x0 + c.measureText(s.slice(0, n)).width, y, 14, col);
      } else if (e.key === 'wedge') {
        this._wedge(c, String(e.text), left, t, col, hair, typeOn);
      }
    }
    c.restore();
  }

  // step wedge: 11 patches PAPER -> INK down the left edge; the VOICE marker drops one patch per chorus (+n STOP)
  _wedge(c, label, x, t, col, hair, typeOn) {
    const n = parseInt(label, 10) || 0, P = 16, G = 3, N = 11;
    const y0 = 540 - (N * P + (N - 1) * G) / 2;
    const shot = this.tl.shotAt(t), f = F(t, this.fps);
    // the drop: from patch 5+n-1 to 5+n over 4 frames on the first frame this chorus's wedge is up
    const f0 = this.runStart('wedge', label, t);
    const k = clamp01((f - f0 + 1) / 4), idx = 5 + (n - 1) + smooth(k);
    for (let i = 0; i < N; i++) {
      const v = Math.round(242 - (242 - 10) * Math.pow(i / (N - 1), 0.85));
      c.globalAlpha = 1; c.fillStyle = `rgb(${v},${Math.round(v * 0.99)},${Math.round(v * 0.96)})`;
      c.fillRect(x, y0 + i * (P + G), P, P);
      c.globalAlpha = 0.35; c.strokeStyle = col; c.lineWidth = hair; c.strokeRect(x + hair / 2, y0 + i * (P + G) + hair / 2, P - hair, P - hair);
    }
    const my = y0 + idx * (P + G) + P / 2;
    c.globalAlpha = 1; c.fillStyle = VOICE;
    c.beginPath(); c.moveTo(x + P + 5, my); c.lineTo(x + P + 13, my - 5); c.lineTo(x + P + 13, my + 5); c.closePath(); c.fill();
    const s = `${label.startsWith('+') ? label : '+' + label} STOP`;
    c.font = `500 14px ${MONO}`; c.letterSpacing = '1.4px'; c.textAlign = 'left'; c.fillStyle = col; c.globalAlpha = 0.85;
    const m = typeOn('wedge', s);
    c.fillText(s.slice(0, m), x + P + 20, my + 5);
    if (m < s.length) cursor(c, x + P + 20 + c.measureText(s.slice(0, m)).width, my + 5, 14, col);
  }
}

function smooth(x) { x = clamp01(x); return x * x * (3 - 2 * x); }
function hashDigit(f, i) { let h = Math.imul(f + 1, 2654435761) ^ Math.imul(i + 7, 40503); h ^= h >>> 15; h = Math.imul(h, 2246822519); h ^= h >>> 13; return (h >>> 0) % 10; }
// registration mark: 24 px crosshair with a 7 px circle
function mark(c, x, y, rot, a) {
  c.save(); c.globalAlpha = a; c.translate(x, y); if (rot) c.rotate(rot);
  c.beginPath(); c.moveTo(-12, 0); c.lineTo(12, 0); c.moveTo(0, -12); c.lineTo(0, 12); c.stroke();
  c.beginPath(); c.arc(0, 0, 7, 0, Math.PI * 2); c.stroke();
  c.restore();
}
function cursor(c, x, y, size, col) { c.save(); c.globalAlpha = 0.9; c.fillStyle = col; c.fillRect(x + 1, y - size * 0.72, size * 0.55, size * 0.72); c.restore(); }
