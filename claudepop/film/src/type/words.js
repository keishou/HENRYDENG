// STUB - owned by lane B, replace. (Frozen on day 0 by lane A: keep these export names and signatures.)
//
// words.js - word / letter timing, Chinese lines and vertical setting (BIBLE 6.2, 6.3, 6.5). Pure functions of the
// timeline and t. Times come only from song.json (never re-timed by ear).
//
//   lineWords(tl, i, { from, to, only } = {}) -> [{ w, t, e, parts, line, k }]
//        the words of line i; from / to: first / last word text to keep (inclusive, matched without punctuation);
//        only: an explicit list of word texts to keep
//   wordState(w, t, fps = 24) -> { on, active, settle, letters }
//        on: t >= onset; active: the word being sung (onset <= t < end); settle: 0 at the onset frame -> 1 after 8 frames
//        (VOICE -> TYPE); letters: letters revealed so far when the word is spelled out on its parts (AGI, ChatGPT ...)
//   zhLine(tl, i) -> the line's Simplified Chinese (research/lyric_concepts.json "zh")
//   zhReveal(tl, i, t) -> number of ZH characters revealed (spread evenly from line start to line end - 0.3 s)
//   verticalize(str) -> [{ ch, rotate }]   one glyph per row: CJK upright, punctuation as vertical presentation forms,
//        embedded Latin runs as one rotated item (rotate: true, ch = the whole run)
export const VERTICAL_FORMS = { '，': '︐', '。': '︒', '？': '︖', '！': '︕', '“': '﹁', '”': '﹂', '、': '︑', '：': '︓', '；': '︔', '（': '︵', '）': '︶' };
const bare = s => s.replace(/[^\p{L}\p{N}'’]/gu, '').toLowerCase();

export function lineWords(tl, i, { from = null, to = null, only = null } = {}) {
  let ws = tl.wordsOf(i);
  if (from) { const k = ws.findIndex(w => bare(w.w) === bare(from)); if (k >= 0) ws = ws.slice(k); }
  if (to) { const k = ws.findIndex(w => bare(w.w) === bare(to)); if (k >= 0) ws = ws.slice(0, k + 1); }
  if (only) { const set = only.map(bare); ws = ws.filter(w => set.includes(bare(w.w))); }
  return ws;
}
export function wordState(w, t, fps = 24) {
  const on = t >= w.t - 1e-6;
  const df = Math.round(t * fps) - Math.round(w.t * fps);
  let letters = w.w.length;
  if (w.parts && w.parts.length > 1) {
    const n = w.parts.filter(p => t >= p - 1e-6).length;
    const letterish = [...w.w].filter(c => /[\p{L}\p{N}]/u.test(c)).length;
    letters = n >= w.parts.length ? w.w.length : Math.round(w.w.length * n / Math.max(letterish, w.parts.length));
    letters = Math.max(on ? 1 : 0, letters);
  }
  return { on, active: on && t < (w.e ?? w.t + 0.3), settle: on ? Math.min(1, df / 8) : 0, letters: on ? letters : 0 };
}
export const zhLine = (tl, i) => (tl.line(i) && tl.line(i).zh) || '';
export function zhReveal(tl, i, t) {
  const l = tl.line(i), zh = zhLine(tl, i), n = [...zh].length;
  if (!n || t < l.start) return 0;
  const span = Math.max(0.2, l.end - 0.3 - l.start);
  return Math.min(n, 1 + Math.floor((t - l.start) / span * (n - 1) + 1e-6));
}
export function verticalize(str) {
  const out = []; let latin = '';
  const flush = () => { if (latin) { out.push({ ch: latin, rotate: true }); latin = ''; } };
  for (const c of str) {
    if (/[A-Za-z0-9.\-]/.test(c)) { latin += c; continue; }
    flush();
    if (c === ' ') continue;
    out.push({ ch: VERTICAL_FORMS[c] || c, rotate: false });
  }
  flush();
  return out;
}
