// timeline.js - the film's clock: shots.json + song.json (+ lyric_concepts zh, + the vocal envelope). Pure lookups.
//
//   const tl = await Timeline.load(assets)
//   tl.fps, tl.frames (3760), tl.duration, tl.bpm, tl.t0 (first beat), tl.beatPeriod
//   tl.frameOf(t) = round(t * fps)          tl.timeOf(f) = f / fps       (BIBLE 8.1: frame = round(t * 24))
//   tl.shots, tl.shot(id), tl.shotAtFrame(f), tl.shotAt(t)   (a shot covers frames [frames[0], frames[1]))
//   tl.frameCtx(t) -> s = { shot, tl: t - shot.t0, u: 0..1, f, fi: f - frames[0], n: frame count, last: bool }
//   EVERY lookup below is BY FRAME (BIBLE 8.1, 9.8.1): an event at time T is on screen from frame round(T * 24), and
//   film time t is always a frame time f / 24, so t is first quantised to f = round(t * 24) and compared with event
//   FRAMES, never raw seconds (t >= 2.045 would put "I" (f49 = 2.0417 s) a frame late). Each t-lookup has a frame twin.
//   tl.beats, tl.downbeats, tl.beatAt(t) / beatAtFrame(f) -> { i, t, phase 0..1, bar (1-based), beat (1..4), f }
//     beat i is current from its frame round((t0 + i * P) * 24); phase = (t - beat time) / P clamped to [0, 1)
//   tl.grid(div, t) / gridAtFrame(div, f) -> { i, t, phase, f }   div 1 = beats, 2 = 8ths, 4 = 16ths (t0 + n * P / div)
//   tl.gridTimes(div, a, b) -> [t...] in [a, b)
//   tl.lines[i] = song.json line + { zh }  tl.line(i), tl.lineAt(t) / lineAtFrame(f) (frame(start) <= f < frame(end),
//     held notes included)
//   tl.words (flat: { w, t, e, parts, line, k }), tl.wordAt(t) / wordAtFrame(f) (the word being sung: the latest word of
//     the current line whose onset frame <= f), tl.wordsOf(i)
//   tl.extras (song.json extra_vocals), tl.events, tl.eventsIn(a, b) (by frame: frame(a) <= frame(e.t) < frame(b)),
//     tl.sections, tl.sectionAt(t) / sectionAtFrame(f) (frame(t0) <= f < frame(t1))
//   tl.env(t) -> 0..1 vocal envelope (Demucs vocal stem, 50 ms attack, 1.5 s release; tools/voice_env.py); tl.hasEnv
//   tl.live(t) / liveAtFrame(f) -> bool: inside a sung-word span, exactly as validate_shots.py counts frames (BIBLE 2.3):
//     [frame(start) - 2, frame(end) + 6) per line, half-open, gaps under 0.6 s (14.4 frames) merged; tl.liveFrames
//   tl.reached(T, t) -> frame(t) >= frame(T)    tl.framesSince(T, t) -> frame(t) - frame(T)   (test events by FRAME)
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
    // sung-word spans (identical to validate_shots.py): seconds (liveSpans, for display) and frames (liveFrames,
    // half-open [a, b), what live() tests)
    const merge = (spans, gap) => {
      const out = [];
      for (const [a, b] of [...spans].sort((x, y) => x[0] - y[0])) {
        const m = out[out.length - 1];
        if (m && a - m[1] < gap) m[1] = Math.max(m[1], b); else out.push([a, b]);
      }
      return out;
    };
    this.liveSpans = merge(this.lines.map(l => [l.start - 2 / this.fps, l.end + 6 / this.fps]), 0.6);
    this.liveFrames = merge(this.lines.map(l => [this.frameOf(l.start) - 2, this.frameOf(l.end) + 6]), 0.6 * this.fps);
    // frame spans of lines, words and sections (lookups by frame)
    this._lineF = this.lines.map(l => [this.frameOf(l.start), this.frameOf(l.end)]);
    this._secF = this.sections.map(x => [this.frameOf(x.t0), this.frameOf(x.t1)]);
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

  // the grid point current at frame f: the latest n whose frame round((t0 + n * p) * fps) <= f
  _gridIndex(p, f) {
    let i = Math.floor((f / this.fps - this.t0) / p);
    while (this.frameOf(this.t0 + (i + 1) * p) <= f) i++;
    while (this.frameOf(this.t0 + i * p) > f) i--;
    return i;
  }
  beatAtFrame(f, t = f / this.fps) {
    const p = this.beatPeriod, i = this._gridIndex(p, f), bt = this.t0 + i * p;
    return { i, t: bt, f: this.frameOf(bt), phase: Math.min(0.999999, Math.max(0, (t - bt) / p)), bar: Math.floor(i / 4) + 1, beat: ((i % 4) + 4) % 4 + 1 };
  }
  beatAt(t) { return this.beatAtFrame(this.frameOf(t), t); }
  gridAtFrame(div, f, t = f / this.fps) {
    const p = this.beatPeriod / div, i = this._gridIndex(p, f), gt = this.t0 + i * p;
    return { i, t: gt, f: this.frameOf(gt), phase: Math.min(0.999999, Math.max(0, (t - gt) / p)) };
  }
  grid(div, t) { return this.gridAtFrame(div, this.frameOf(t), t); }
  gridTimes(div, a, b) {
    const p = this.beatPeriod / div, out = [];
    for (let i = Math.ceil((a - this.t0) / p - 1e-9); this.t0 + i * p < b - 1e-9; i++) out.push(+(this.t0 + i * p).toFixed(4));
    return out;
  }

  line(i) { return this.lines[i]; }
  lineAtFrame(f) { const k = this._lineF.findIndex(([a, b]) => f >= a && f < b); return k < 0 ? null : this.lines[k]; }
  lineAt(t) { return this.lineAtFrame(this.frameOf(t)); }
  wordsOf(i) { return this.words.filter(w => w.line === i); }
  wordAtFrame(f) {
    const l = this.lineAtFrame(f); if (!l) return null;
    let cur = null; for (const w of this.wordsOf(l.i)) if (this.frameOf(w.t) <= f) cur = w;
    return cur;
  }
  wordAt(t) { return this.wordAtFrame(this.frameOf(t)); }
  eventsIn(a, b) { const fa = this.frameOf(a), fb = this.frameOf(b); return this.events.filter(e => { const fe = this.frameOf(e.t); return fe >= fa && fe < fb; }); }
  sectionAtFrame(f) { const k = this._secF.findIndex(([a, b]) => f >= a && f < b); return k < 0 ? this.sections[f < 0 ? 0 : this.sections.length - 1] : this.sections[k]; }
  sectionAt(t) { return this.sectionAtFrame(this.frameOf(t)); }

  env(t) {
    if (!this.hasEnv) return 0;
    const d = this.envData, x = (t - (d.t0 || 0)) * d.rate, i = Math.floor(x), v = d.values;
    if (i < 0) return v[0]; if (i >= v.length - 1) return v[v.length - 1];
    return v[i] + (v[i + 1] - v[i]) * (x - i);
  }
  liveAtFrame(f) { return this.liveFrames.some(([a, b]) => f >= a && f < b); }
  live(t) { return this.liveAtFrame(this.frameOf(t)); }

  // frame-level event tests (BIBLE 8.1, 9.8.1: an event at time T changes the picture ON frame round(T * 24)). Film
  // time t is always a frame time f / 24, so compare frames, never raw seconds: t >= 2.852 would show "sparks" (f68.45)
  // one frame late, on f69.
  reached(T, t) { return this.frameOf(t) >= this.frameOf(T); }
  framesSince(T, t) { return this.frameOf(t) - this.frameOf(T); }
  hitFrames(shot) { return (shot.beat_hits || []).map(h => this.frameOf(h)); }
  hitAt(shot, f) { return this.hitFrames(shot).indexOf(f); }
  lastHit(shot, t) {
    const f = this.frameOf(t); let best = null;
    (shot.beat_hits || []).forEach((h, i) => { const hf = this.frameOf(h); if (hf <= f && (!best || hf >= best.f)) best = { i, t: h, f: hf, df: f - hf }; });
    return best;
  }
}
