// words.js - word / letter timing, Chinese lines and vertical setting (BIBLE 6.2, 6.3, 6.5; lane B). Pure functions of
// the timeline and t. Every time comes from song.json (lines[].words[].t / .e / .parts, lines[].end, extra_vocals);
// nothing is re-timed by ear. Every event is tested by FRAME: an event at T is on screen from frame round(T * fps).
//
// Frozen API (lane A, day 0):
//   lineWords(tl, i, { from, to, only, extras = true } = {}) -> [{ w, t, e, parts, line, k, extra? }]
//        the words of line i; from / to: first / last word text to keep (inclusive, matched without punctuation);
//        only: an explicit list of word texts to keep. extras: the extra_vocals "within_line" repeats are merged in
//        time order (line 34: the three extra "just"s at 109.56 / 110.18 / 110.65 and "formers" at 112.05) - they carry
//        extra: true so a layout can decide to show or skip them.
//   wordState(w, t, fps = 24) -> { on, active, settle, letters, seg, segOn, df }
//        on      from the onset's frame round(t * fps)
//        active  the word being sung: onset frame <= f < end frame (round(e * fps))
//        settle  VOICE -> TYPE: 0 while active, then 0 -> 1 over the 8 frames after the end frame (BIBLE 6.2 colour rule)
//        letters characters revealed so far (spelled-out words reveal on their parts: AGI, ChatGPT, NVDA ...)
//        seg     index of the latest revealed segment (segments(w)); segOn its onset frame; df frames since the onset
//   zhLine(tl, i) -> the line's Simplified Chinese (research/lyric_concepts.json "zh")
//   zhReveal(tl, i, t, { from, to, text } = {}) -> number of code points of the ZH string to show: reading units (hanzi
//        and whole Latin runs; punctuation rides with the unit before it) spread evenly from line start to line end - 0.3 s
//   verticalize(str) -> [{ ch, rotate, punct }]   one item per row: CJK upright, punctuation as vertical presentation
//        forms (punct: true), each embedded Latin run as one item rotated 90 deg clockwise (rotate: true)
// Additions (lane B):
//   segments(w) -> [{ s, t, i0, i1 }]   the letter groups a spelled-out word reveals on (uppercase split: Chat|G|P|T,
//        N|V|D|A; hyphen split: super-|dense; "P(" split: P(|doom)); one segment { s: w.w, t: w.t } otherwise
//   F(T, fps) frame of an event; reached(T, t, fps)
//   displayWord(w, mode) the word as set for a presence level (THOUGHT: the first word lowercase as sung unless it is a
//        name / acronym / "I")
//   zhSubtitle(str) Chinese subtitle convention for horizontal subtitles: "，" "、" -> a full-width space, a trailing
//        "。" dropped ("？" "！" and quotes kept)
//   zhCut(str, nSentences) the first n sentences of a ZH line (line 44 keeps "Ilya 看见了什么？" and withholds the rest)
//   revealUnits(str) -> [{ i0, i1 }]   the reading units of a ZH string (code point ranges)
export const VERTICAL_FORMS = { '，': '︐', ',': '︐', '。': '︒', '？': '︖', '?': '︖', '！': '︕', '!': '︕', '“': '﹁', '”': '﹂',
  '‘': '﹃', '’': '﹄', '、': '︑', '：': '︓', '；': '︔', '（': '︵', '）': '︶', '《': '︽', '》': '︾', '…': '︙', '—': '︱', '·': '・' };
export const F = (T, fps = 24) => Math.round(T * fps);
export const reached = (T, t, fps = 24) => Math.round(t * fps) >= Math.round(T * fps);
const bare = s => s.replace(/[^\p{L}\p{N}'’]/gu, '').toLowerCase();
const PUNCT = /[\p{P}\p{S}\s]/u;
const CJK = /[㐀-鿿豈-﫿]/;

function extrasOf(tl, i) {
  const out = [];
  for (const x of tl.extras || []) if (x.within_line === i) for (const w of x.words || []) out.push({ w: w.w, t: w.t, e: w.e ?? null, line: i, extra: true });
  return out;
}

export function lineWords(tl, i, { from = null, to = null, only = null, extras = true } = {}) {
  let ws = tl.wordsOf(i).map(w => ({ ...w }));
  if (extras) {
    const xs = extrasOf(tl, i);
    if (xs.length) {
      ws = ws.concat(xs).sort((a, b) => a.t - b.t);
      // an extra's end = the next onset; the word it interrupts keeps its own end but not past the extra's onset
      for (let k = 0; k < ws.length; k++) {
        const nx = ws[k + 1];
        if (ws[k].extra && ws[k].e == null) ws[k].e = nx ? nx.t : ws[k].t + 0.3;
        else if (nx && nx.extra && ws[k].e > nx.t) ws[k].e = nx.t;
      }
    }
  }
  ws.forEach((w, k) => { w.k = k; });
  if (from) { const k = ws.findIndex(w => bare(w.w) === bare(from)); if (k >= 0) ws = ws.slice(k); }
  if (to) { const k = ws.findIndex(w => bare(w.w) === bare(to)); if (k >= 0) ws = ws.slice(0, k + 1); }
  if (only) { const set = only.map(bare); ws = ws.filter(w => set.includes(bare(w.w))); }
  return ws;
}

// letter groups for spelled-out words (song.json parts)
export function segments(w) {
  const s = w.w, p = w.parts;
  if (!p || p.length < 2) return [{ s, t: w.t, i0: 0, i1: s.length }];
  const cut = idx => {                                  // idx = start indices of segments 1..n-1
    const b = [0, ...idx, s.length];
    return p.map((t, k) => ({ s: s.slice(b[k], b[k + 1]), t, i0: b[k], i1: b[k + 1] }));
  };
  const lead = s.match(/^[^\p{L}\p{N}]*/u)[0].length;
  const ups = [...s].map((c, k) => (k > lead && /\p{Lu}/u.test(c)) ? k : -1).filter(k => k > 0);
  const firstUp = /\p{Lu}/u.test(s[lead] || '');
  if (firstUp && ups.length === p.length - 1) return cut(ups);                 // Chat|G|P|T,  N|V|D|A  Post-|Chinchilla,
  const hy = [...s].map((c, k) => c === '-' ? k + 1 : -1).filter(k => k > 0);
  if (hy.length === p.length - 1) return cut(hy);                              // super-|dense  pre-|training
  const par = s.indexOf('(');
  if (par >= 0 && p.length === 2) return cut([par + 1]);                       // P(|doom)
  const n = p.length, L = s.length;                                             // fallback: even split
  return cut(Array.from({ length: n - 1 }, (_, k) => Math.round(L * (k + 1) / n)));
}

export function wordState(w, t, fps = 24) {
  const f = Math.round(t * fps), fo = Math.round(w.t * fps), fe = Math.round((w.e ?? (w.t + 0.3)) * fps);
  const on = f >= fo;
  if (!on) return { on: false, active: false, settle: 0, letters: 0, seg: -1, segOn: fo, df: f - fo };
  const segs = segments(w);
  let seg = 0; for (let k = 0; k < segs.length; k++) if (f >= Math.round(segs[k].t * fps)) seg = k;
  const active = f < Math.max(fe, fo + 1);
  const settle = active ? 0 : Math.min(1, (f - Math.max(fe, fo + 1) + 1) / 8);
  return { on, active, settle, letters: segs[seg].i1, seg, segOn: Math.round(segs[seg].t * fps), df: f - fo };
}

// ---------------------------------------------------------------------------------------------------- display forms
const KEEP_CASE = new Set(['i', "i'm", 'sydney', 'gato', 'chatgpt', 'nvda', 'loom', 'post-chinchilla', 'ilya', 'omega']);
export function displayWord(w, mode, k = w.k) {
  const s = w.w;
  if (mode === 'THOUGHT' || mode === 'QUESTION') {
    if (k === 0 && !KEEP_CASE.has(bare(s).replace(/,$/, '')) && !/\p{Lu}.*\p{Lu}/u.test(s)) return s.charAt(0).toLowerCase() + s.slice(1);
  }
  return s;
}

// ---------------------------------------------------------------------------------------------------- Chinese
export const zhLine = (tl, i) => (tl.line(i) && tl.line(i).zh) || '';
export function zhSubtitle(str) {
  return str.replace(/[，、]\s*/g, '　').replace(/[。]+$/u, '').replace(/　+$/u, '').trim();
}
export function zhCut(str, n = 1) {
  const cps = [...str]; let seen = 0;
  for (let k = 0; k < cps.length; k++) if (/[？！。?!]/u.test(cps[k]) && ++seen === n) return cps.slice(0, k + 1).join('');
  return str;
}
// reading units: a hanzi, or a whole Latin run (ChatGPT, Ilya); punctuation and spaces join the unit before them
export function revealUnits(str) {
  const cps = [...str], units = [];
  for (let k = 0; k < cps.length; k++) {
    const c = cps[k];
    if (PUNCT.test(c) && units.length && !/[“‘（《]/u.test(c)) { units[units.length - 1].i1 = k + 1; continue; }
    if (/[“‘（《]/u.test(c)) { units.push({ i0: k, i1: k + 1, open: true }); continue; }
    const u = units[units.length - 1];
    if (u && u.open) { u.i1 = k + 1; u.open = false; u.latin = /[A-Za-z0-9]/.test(c); continue; }   // an opening quote rides with the next unit
    const latin = /[A-Za-z0-9]/.test(c);
    if (latin && u && u.latin && u.i1 === k) { u.i1 = k + 1; continue; }                          // a Latin run is one unit
    units.push({ i0: k, i1: k + 1, latin });
  }
  return units;
}
export function zhReveal(tl, i, t, { text = null, from = null, to = null, fps = 24 } = {}) {
  const l = tl.line(i), zh = text ?? zhLine(tl, i);
  if (!l || !zh) return 0;
  const units = revealUnits(zh), n = units.length;
  const a = from ?? l.start, b = Math.max(a + 0.2, (to ?? l.end) - 0.3);
  const f = Math.round(t * fps);
  let k = -1;
  for (let u = 0; u < n; u++) if (f >= Math.round((a + (n > 1 ? u / (n - 1) : 0) * (b - a)) * fps)) k = u;
  return k < 0 ? 0 : units[k].i1;
}

export function verticalize(str) {
  const out = []; let latin = '';
  const flush = () => { if (latin) { out.push({ ch: latin.trim(), rotate: true, punct: false }); latin = ''; } };
  for (const c of str) {
    if (/[A-Za-z0-9.\-+/]/.test(c) || (c === ' ' && latin)) { latin += c; continue; }
    flush();
    if (c === ' ' || c === '　') continue;
    const v = VERTICAL_FORMS[c];
    out.push({ ch: v || c, rotate: false, punct: !!v || (PUNCT.test(c) && !CJK.test(c)) });
  }
  flush();
  return out.filter(g => g.ch);
}
