// STUB - owned by lane B, replace. (Frozen on day 0 by lane A: keep the class, constructor and draw() signature.)
//
// proof.js - the proof-sheet HUD (BIBLE 6.7): the machine's telemetry about its own printing. At most two elements
// plus one type block per frame; registration marks are frame furniture. Everything lays out relative to the window.
//
//   const proof = new Proof(ctx)
//   proof.draw(hudState, windowRect, t)       draws into ctx.hud (the Hud canvas, 1920x1080 design space)
//     hudState   frameSpec.hud, with EVALUATED strings (scenes compute the value for t):
//                { proof: '0480' | null, wedge: '+2' | null, slug: 'ENLARGER 32 s · f/8 · GRADE 3 · 20 °C' | null,
//                  caption: 'PL. ...' | null, job: true | null, counter: 'ENLARGEMENT ×64' | null,
//                  marks: { doubled, rotate (deg), alpha } | null (registration marks; default on), hidden: bool }
//     windowRect { x, y, w, h } design px (the current window; elements sit inside it, inset 32 px)
//     t          film time
// This stub draws the registration marks, PROOF Nº and a plate caption in plain mono.
const TYPE = '#FAF9F5', VOICE = '#D97757';

export class Proof {
  constructor(ctx) { this.ctx = ctx; }
  draw(st, r, t) {
    const hud = this.ctx.hud, c = hud.ctx;
    if (!st || st.hidden) return;
    const m = st.marks === undefined ? {} : st.marks;
    if (m) {
      const a = m.alpha ?? 0.4, s = 12, off = 20;
      for (const [x, y] of [[r.x - off, r.y + off], [r.x + r.w + off, r.y + off], [r.x - off, r.y + r.h - off], [r.x + r.w + off, r.y + r.h - off]]) {
        if (x < 4 || x > 1916) continue;              // no room outside a full-width window
        c.save(); c.globalAlpha = a; c.strokeStyle = TYPE; c.lineWidth = 1;
        c.beginPath(); c.moveTo(x - s, y); c.lineTo(x + s, y); c.moveTo(x, y - s); c.lineTo(x, y + s); c.stroke();
        c.beginPath(); c.arc(x, y, s * 0.55, 0, Math.PI * 2); c.stroke(); c.restore();
      }
    }
    c.save(); c.textBaseline = 'alphabetic';
    if (st.proof) {
      c.font = '500 20px "IBM Plex Mono", monospace'; c.textAlign = 'right'; c.letterSpacing = '2px';
      const x = r.x + r.w - 32, y = r.y + 52;
      c.fillStyle = VOICE; c.fillText(String(st.proof), x, y);
      const w = c.measureText(String(st.proof)).width;
      c.fillStyle = TYPE; c.globalAlpha = 0.7; c.fillText('PROOF Nº ', x - w - 4, y);
    }
    if (st.caption) {
      c.globalAlpha = 0.75; c.fillStyle = TYPE; c.textAlign = 'left'; c.letterSpacing = '1.5px';
      c.font = '400 15px "IBM Plex Mono", monospace'; c.fillText(st.caption, r.x + 32, r.y + 48);
    }
    c.restore();
  }
}
