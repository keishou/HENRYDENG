// timeline.js - the film's clock: shots.json + song.json (+ lyric_concepts zh, + the vocal envelope). Pure lookups.
//
//   const tl = await Timeline.load(assets)
//   tl.fps, tl.frames (3760), tl.duration, tl.bpm, tl.t0 (first beat), tl.beatPeriod
//   tl.frameOf(t) = round(t * fps)          tl.timeOf(f) = f / fps       (BIBLE 8.1: frame = round(t * 24))
//   tl.shots, tl.shot(id), tl.shotAtFrame(f), tl.shotAt(t)   (a shot covers frames [frames[0], frames[1]))
//   tl.frameCtx(t) -> s = { shot, tl: t - shot.t0, u: 0..1, f, fi: f - frames[0], n: frame count, last: bool }
//   tl.beats, tl.downbeats, tl.beatAt(t) -> { i, t, phase 0..1, bar (1-based), beat (1..4) }
//   tl.grid(div, t) -> { i, t, phase }     div 1 = beats, 2 = 8ths, 4 = 16ths (t0 + n * beatPeriod / div)
//   tl.gridTimes(div, a, b) -> [t...] in [a, b)
//   tl.lines[i] = song.json line + { zh }  tl.line(i), tl.lineAt(t) (start <= t < end, held notes included)
//   tl.words (flat: { w, t, e, parts, line, k }), tl.wordAt(t) (the word being sung: its onset <= t < next onset,
//     inside the line), tl.wordsOf(i)
//   tl.extras (song.json extra_vocals), tl.events, tl.eventsIn(a, b), tl.sections, tl.sectionAt(t)
//   tl.env(t) -> 0..1 vocal envelope (Demucs vocal stem, 50 ms attack, 1.5 s release; tools/voice_env.py); tl.hasEnv
//   tl.live(t) -> bool: inside a sung-word span (line start - 2 f .. line end + 6 f, gaps < 0.6 s merged; BIBLE 2.3)
//   tl.hitFrames(shot) -> [f...] (round(beat_hit * fps)); tl.hitAt(shot, f) -> index or -1;
//   tl.lastHit(shot, t) -> { i, t, f, df } | null   (the latest beat_hit at or before t; df = frames since it)
export class Timeline {
  static async load(assets) {
    const [doc, song, concepts, env] = await Promise.all([
      assets.json('/shots.json'), assets.json('/analysis/song.json'),
      assets.json('/research/lyric_concepts.json').catch(() => []),
      assets.json('/out/film/data/voice_env.json').catch(() => null)]);
    return new Timeline(doc, song, concepts, env);
  }

  constructor(doc, song, concepts = [], env = null) {
    this.doc = doc; this.song = song;
    this.fps = doc.fps; this.frames = doc.frames; this.duration = doc.duration;
    this.bpm = song.bpm; this.t0 = song.t0; this.beatPeriod = song.beat_period;
    this.shots = doc.shots;
    this._byId = Object.fromEntries(this.shots.map(s => [s.id, s]));
    this._frameShot = new Array(this.frames);
    for (const s of this.shots) for (let f = s.frames[0]; f < s.frames[1]; f++) this._frameShot[f] = s;
    this.beats = song.beats; this.downbeats = song.downbeats;
    const zh = Object.fromEntries((concepts || []).map(c => [c.i, c.zh]));
    this.lines = song.lines.map(l => ({ ...l, zh: zh[l.i] || '' }));
    this.words = this.lines.flatMap(l => l.words.map((w, k) => ({ ...w, line: l.i, k })));
    this.extras = song.extra_vocals || [];
    this.events = song.events || [];
    this.sections = doc.sections || song.sections;
    // sung-word spans (identical to validate_shots.py)
    const spans = this.lines.map(l => [l.start - 2 / this.fps, l.end + 6 / this.fps]).sort((a, b) => a[0] - b[0]);
    this.liveSpans = [];
    for (const [a, b] of spans) {
      const m = this.liveSpans[this.liveSpans.length - 1];
      if (m && a - m[1] < 0.6) m[1] = Math.max(m[1], b); else this.liveSpans.push([a, b]);
    }
    this.envData = env; this.hasEnv = !!(env && env.values && env.values.length);
  }

  frameOf(t) { return Math.round(t * this.fps); }
  timeOf(f) { return f / this.fps; }
  shot(id) { return this._byId[id]; }
  shotAtFrame(f) { return this._frameShot[Math.max(0, Math.min(this.frames - 1, f))]; }
  shotAt(t) { return this.shotAtFrame(this.frameOf(t)); }
  frameCtx(t) {
    const f = this.frameOf(t), shot = this.shotAtFrame(f);
    const n = shot.frames[1] - shot.frames[0], fi = f - shot.frames[0];
    return { shot, tl: t - shot.t0, u: Math.min(1, Math.max(0, (t - shot.t0) / (shot.t1 - shot.t0))), f, fi, n, last: fi === n - 1 };
  }

  beatAt(t) {
    const x = (t - this.t0) / this.beatPeriod, i = Math.floor(x);
    return { i, t: this.t0 + i * this.beatPeriod, phase: x - i, bar: Math.floor(i / 4) + 1, beat: ((i % 4) + 4) % 4 + 1 };
  }
  grid(div, t) {
    const p = this.beatPeriod / div, x = (t - this.t0) / p, i = Math.floor(x);
    return { i, t: this.t0 + i * p, phase: x - i };
  }
  gridTimes(div, a, b) {
    const p = this.beatPeriod / div, out = [];
    for (let i = Math.ceil((a - this.t0) / p - 1e-9); this.t0 + i * p < b - 1e-9; i++) out.push(+(this.t0 + i * p).toFixed(4));
    return out;
  }

  line(i) { return this.lines[i]; }
  lineAt(t) { return this.lines.find(l => t >= l.start && t < l.end) || null; }
  wordsOf(i) { return this.words.filter(w => w.line === i); }
  wordAt(t) {
    const l = this.lineAt(t); if (!l) return null;
    const ws = this.wordsOf(l.i);
    let cur = null; for (const w of ws) if (w.t <= t) cur = w;
    return cur;
  }
  eventsIn(a, b) { return this.events.filter(e => e.t >= a && e.t < b); }
  sectionAt(t) { return this.sections.find(s => t >= s.t0 && t < s.t1) || this.sections[this.sections.length - 1]; }

  env(t) {
    if (!this.hasEnv) return 0;
    const d = this.envData, x = (t - (d.t0 || 0)) * d.rate, i = Math.floor(x), v = d.values;
    if (i < 0) return v[0]; if (i >= v.length - 1) return v[v.length - 1];
    return v[i] + (v[i + 1] - v[i]) * (x - i);
  }
  live(t) { return this.liveSpans.some(([a, b]) => t >= a && t <= b); }

  hitFrames(shot) { return (shot.beat_hits || []).map(h => this.frameOf(h)); }
  hitAt(shot, f) { return this.hitFrames(shot).indexOf(f); }
  lastHit(shot, t) {
    const f = this.frameOf(t); let best = null;
    (shot.beat_hits || []).forEach((h, i) => { const hf = this.frameOf(h); if (hf <= f && (!best || hf >= best.f)) best = { i, t: h, f: hf, df: f - hf }; });
    return best;
  }
}
