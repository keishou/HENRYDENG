// Typography layer: epigraphs, Dunkirk-style chapter cards, monologue lines,
// stream-of-consciousness fragments, the Urashima counter and the title.
import { smooth, clamp, rng } from './engine.js';

export async function loadFonts() {
  const faces = [
    ['Mincho', 'assets/fonts/ShipporiMincho-Regular.ttf', {}],
    ['MinchoB', 'assets/fonts/ShipporiMincho-Bold.ttf', {}],
    ['Garamond', 'assets/fonts/EBGaramond[wght].ttf', {}],
    ['GaramondI', 'assets/fonts/EBGaramond-Italic[wght].ttf', { style: 'italic' }],
    ['Jost', 'assets/fonts/Jost[wght].ttf', {}],
  ];
  for (const [name, url, desc] of faces) {
    const f = new FontFace(name, `url("${encodeURI(url)}")`, desc);
    await f.load(); document.fonts.add(f);
  }
}

// Shared with score.py: the accelerating ticks of the Dragon Palace.
export function palaceTicks(ev) {
  const { t0, t1, start_interval: a, end_interval: b, years_end: Y } = ev;
  const ticks = [];
  for (let t = t0; t < t1;) {
    ticks.push(t);
    const f = (t - t0) / (t1 - t0);
    t += a * Math.pow(b / a, f);
  }
  const n = ticks.length; let prev = 0;
  const years = ticks.map((_, k) => (prev = Math.max(prev + 1, Math.round(Y * Math.pow((k + 1) / n, 2.2)))));
  return { ticks, years };
}

const KANJI_NUM = n => {
  const d = '〇一二三四五六七八九';
  if (n < 10) return d[n];
  const h = Math.floor(n / 100), t = Math.floor(n / 10) % 10, o = n % 10;
  return (h ? (h > 1 ? d[h] : '') + '百' : '') + (t ? (t > 1 ? d[t] : '') + '十' : '') + (o ? d[o] : '');
};

export class TextLayer {
  constructor(engine, TL) {
    this.e = engine; this.TL = TL; this.ctx = engine.textCtx;
    this.W = engine.W; this.H = engine.H; this.s = engine.W / 1920;
    this.palace = palaceTicks(TL.events.palace_ticks);
  }

  font(px, fam, weight = '') { return `${weight} ${Math.round(px * this.s)}px ${fam}`.trim(); }

  draw(T, aspect) {
    const { ctx, W, H, s } = this;
    ctx.clearRect(0, 0, W, H);
    const bar = aspect === 'imax' ? 0 : Math.round((H - W / 2.39) / 2);
    const top = bar, bottom = H - bar;
    for (const c of this.TL.texts) {
      if (T < c.t0 - .01 || T > c.t1 + .01) continue;
      const a = smooth(c.t0, c.t0 + .8, T) * (1 - smooth(c.t1 - .9, c.t1, T));
      const p = (T - c.t0) / (c.t1 - c.t0);
      ctx.save();
      ctx.globalAlpha = a;
      ctx.fillStyle = 'rgb(240,236,228)';
      ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
      ctx.shadowColor = 'rgba(0,0,0,.65)'; ctx.shadowBlur = 14 * s;
      this[c.style]?.(c, p, T, { top, bottom, a });
      ctx.restore();
    }
  }

  epigraph(c) {
    const { ctx, W, H } = this;
    ctx.font = this.font(40, 'GaramondI', 'italic'); ctx.fillText(c.el, W / 2, H * .47);
    ctx.globalAlpha *= .8;
    ctx.font = this.font(27, 'Mincho'); ctx.fillText(c.ja, W / 2, H * .47 + 62 * this.s);
  }

  chapter(c, p, T, { bottom }) {
    const { ctx, W, s } = this;
    ctx.textAlign = 'left';
    const x = W * .07;
    ctx.font = this.font(72, 'MinchoB'); ctx.fillText(c.ja, x, bottom - 118 * s);
    ctx.letterSpacing = `${Math.round(7 * s)}px`;
    ctx.font = this.font(19, 'Jost', '400'); ctx.globalAlpha *= .85;
    ctx.fillText(c.en, x + 3 * s, bottom - 76 * s);
  }

  line(c, p, T, { bottom }) {
    const { ctx, W, s } = this;
    let ja = c.ja;
    const chars = [...ja];
    if (c.type) ja = chars.slice(0, Math.ceil(chars.length * clamp(p / .4))).join('');
    if (c.reverse) {
      const k = Math.ceil(chars.length * clamp(p / .45));
      ja = chars.map((ch, i) => (i >= chars.length - k ? ch : '　')).join('');
    }
    const y = bottom - (c.cite ? 150 : 128) * s;
    ctx.font = this.font(chars.length > 22 ? 36 : 42, 'Mincho'); ctx.fillText(ja, W / 2, y);
    ctx.globalAlpha *= .78 * smooth(.08, .3, p);
    ctx.font = this.font(26, 'GaramondI', 'italic'); ctx.fillText(c.en, W / 2, y + 46 * s);
    if (c.cite) {
      ctx.globalAlpha *= .75;
      ctx.font = this.font(17, 'Mincho'); ctx.fillText('— ' + c.cite, W / 2, y + 84 * s);
    }
  }

  drift(c, p, T) {
    const { ctx, W, H, s } = this;
    const r = rng(11);
    c.words.forEach((w, i) => {
      const x = W * (.12 + .76 * r()), y = H * (.24 + .52 * r()), size = 22 + 34 * r();
      const d0 = .08 + i * .1, d1 = d0 + .38;
      const a = smooth(d0, d0 + .1, p) * (1 - smooth(d1, d1 + .14, p));
      if (a <= 0) return;
      ctx.save();
      ctx.globalAlpha *= a * .55;
      ctx.filter = i % 2 ? `blur(${1.5 * s}px)` : 'none';
      ctx.font = this.font(size, /[a-z]/i.test(w) ? 'GaramondI' : 'Mincho', /[a-z]/i.test(w) ? 'italic' : '');
      ctx.fillText(w, x, y - p * 40 * s);
      ctx.restore();
    });
  }

  counter(c, p, T, { top }) {
    const { ctx, W, s } = this;
    const { ticks, years } = this.palace;
    let k = -1; for (let i = 0; i < ticks.length; i++) if (ticks[i] <= T) k = i;
    const n = k < 0 ? 0 : years[k];
    ctx.textAlign = 'right';
    const x = W * .93;
    ctx.globalAlpha *= .85;
    ctx.font = this.font(30, 'Mincho'); ctx.fillText(`地上　${KANJI_NUM(n)}年`, x, top + 78 * s);
    ctx.letterSpacing = `${Math.round(5 * s)}px`;
    ctx.globalAlpha *= .7;
    ctx.font = this.font(15, 'Jost', '400'); ctx.fillText(`ABOVE · ${n} YEAR${n === 1 ? '' : 'S'}`, x, top + 108 * s);
  }

  big(c, p, T) {
    const { ctx, W, H, s } = this;
    ctx.font = this.font(118, 'Mincho'); ctx.fillText(c.ja, W / 2, H * .53);
    ctx.globalAlpha *= smooth(.15, .35, p);
    ctx.letterSpacing = `${Math.round(10 * s)}px`;
    ctx.font = this.font(30, 'Garamond'); ctx.fillText(c.en, W / 2, H * .53 + 86 * s);
  }

  tunnel(c, p, T) {
    const { ctx, W, H, s } = this;
    for (let i = 0; i < 7; i++) {
      const z = ((i / 7 + p * 1.6) % 1);             // 0 far .. 1 near
      const size = 14 + 260 * Math.pow(z, 3.2);
      const a = smooth(0, .25, z) * (1 - smooth(.72, .95, z));
      ctx.save();
      ctx.globalAlpha *= a * .5;
      ctx.filter = `blur(${(z * 5 * s).toFixed(1)}px)`;
      ctx.font = this.font(size, 'Mincho'); ctx.fillText(c.word, W / 2, H * .5 + size * .35);
      ctx.restore();
    }
  }

  title_a(c, p) {
    const { ctx, W, H, s } = this;
    ctx.letterSpacing = `${Math.round(48 * s)}px`;
    ctx.font = this.font(128, 'Garamond'); ctx.fillText('ΟΥΤΙΣ', W / 2 + 24 * s, H * .54);
  }

  title_b(c, p) {
    const { ctx, W, H, s } = this;
    ctx.font = this.font(150, 'Mincho'); ctx.letterSpacing = `${Math.round(40 * s)}px`;
    ctx.fillText('無名', W / 2 + 20 * s, H * .52);
    ctx.globalAlpha *= smooth(.12, .4, p) * .85;
    ctx.letterSpacing = `${Math.round(12 * s)}px`;
    ctx.font = this.font(21, 'Jost', '400'); ctx.fillText('A JAPANESE ODYSSEY', W / 2 + 6 * s, H * .52 + 92 * s);
  }
}
