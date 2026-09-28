// ETHER · 以太 — generative audio. One engine, three uses:
//   live  : AudioContext, events applied at ctx.currentTime
//   record: same calls are logged as {t,name,args} (render mode, no sound)
//   offline: log is replayed into an OfflineAudioContext -> WAV (for the video)
window.ETHER_AUDIO = (() => {

const CHORDS = {
  0: [],                                              // prologue: hum only
  1: [146.83, 220.00, 369.99, 329.63, 554.37],        // D maj9
  2: [196.00, 293.66, 493.88, 739.99],                // G maj7
  3: [164.81, 246.94, 369.99, 392.00],                // E m add9
  4: [185.00, 277.18, 415.30, 440.00, 659.26],        // F# m9
  5: [110.00, 164.81, 246.94, 440.00],                // A sus2
  6: [123.47, 185.00, 277.18, 293.66],                // B m add9
  7: [146.83, 220.00, 246.94, 369.99],                // D 6
  8: [440.00],                                        // ending
};
const PENTA = [0, 2, 4, 7, 9, 12, 14, 16];

function makeNoise(ctx, seconds){
  const len = Math.floor(ctx.sampleRate*seconds);
  const buf = ctx.createBuffer(2, len, ctx.sampleRate);
  let s = 1234567;
  for (let c=0;c<2;c++){ const d = buf.getChannelData(c);
    for(let i=0;i<len;i++){ s = (s*1664525 + 1013904223) >>> 0; d[i] = (s/4294967296)*2-1; } }
  return buf;
}
function makeIR(ctx, seconds, decay){
  const len = Math.floor(ctx.sampleRate*seconds);
  const buf = ctx.createBuffer(2, len, ctx.sampleRate);
  let s = 987654;
  for (let c=0;c<2;c++){ const d = buf.getChannelData(c); let lp=0;
    for(let i=0;i<len;i++){ s = (s*1664525 + 1013904223) >>> 0; const n=(s/4294967296)*2-1;
      lp += (n-lp)*0.25; d[i] = lp*Math.pow(1-i/len, decay)*(i<200? i/200:1); } }
  return buf;
}

class Engine {
  constructor(ctx){
    this.ctx = ctx;
    const c = ctx;
    this.master = c.createGain(); this.master.gain.value = 0.0;
    this.hp = c.createBiquadFilter(); this.hp.type='lowpass'; this.hp.frequency.value = 18000; this.hp.Q.value = 0.5;
    this.comp = c.createDynamicsCompressor(); this.comp.threshold.value=-18; this.comp.ratio.value=3; this.comp.attack.value=0.02; this.comp.release.value=0.4;
    this.rev = c.createConvolver(); this.rev.buffer = makeIR(c, 3.2, 2.6);
    this.revGain = c.createGain(); this.revGain.gain.value = 0.42;
    this.dry = c.createGain(); this.dry.gain.value = 1.0;
    this.bus = c.createGain();
    this.bus.connect(this.dry); this.dry.connect(this.master);
    this.bus.connect(this.rev); this.rev.connect(this.revGain); this.revGain.connect(this.master);
    this.master.connect(this.hp); this.hp.connect(this.comp); this.comp.connect(c.destination);
    this.noiseBuf = makeNoise(c, 4);
    this.pads = []; this.layers = {};
    this.tickBuf = makeNoise(c, 0.06);
    this.started = false;
  }
  extraOut(node){ this.comp.connect(node); }
  start(at){ if(this.started) return; this.started=true;
    this.master.gain.setValueAtTime(0.0, at); this.master.gain.linearRampToValueAtTime(0.9, at+2.5);
    // ever-present hum (55Hz) — the machine
    const o = this.ctx.createOscillator(); o.type='sine'; o.frequency.value=55;
    const g = this.ctx.createGain(); g.gain.value=0.035; o.connect(g); g.connect(this.bus); o.start(at); this.hum=g;
    // wind: filtered noise with slow LFOs
    const n = this.ctx.createBufferSource(); n.buffer=this.noiseBuf; n.loop=true;
    const bp = this.ctx.createBiquadFilter(); bp.type='bandpass'; bp.frequency.value=380; bp.Q.value=0.6;
    const wg = this.ctx.createGain(); wg.gain.value=0.0;
    const lfo = this.ctx.createOscillator(); lfo.frequency.value=0.045; const lg=this.ctx.createGain(); lg.gain.value=220; lfo.connect(lg); lg.connect(bp.frequency);
    const lfo2 = this.ctx.createOscillator(); lfo2.frequency.value=0.11; const lg2=this.ctx.createGain(); lg2.gain.value=0.35; lfo2.connect(lg2);
    const wamp = this.ctx.createGain(); wamp.gain.value=0.65; lg2.connect(wamp.gain);
    n.connect(bp); bp.connect(wamp); wamp.connect(wg); wg.connect(this.bus);
    n.start(at); lfo.start(at); lfo2.start(at);
    this.wind = wg;
  }
  _pad(freqs, at, level){
    const c=this.ctx; const out=c.createGain(); out.gain.setValueAtTime(0.0001, at); out.gain.exponentialRampToValueAtTime(level, at+4.0);
    const lp=c.createBiquadFilter(); lp.type='lowpass'; lp.frequency.value=820; lp.Q.value=0.8;
    const lfo=c.createOscillator(); lfo.frequency.value=0.07; const lg=c.createGain(); lg.gain.value=260; lfo.connect(lg); lg.connect(lp.frequency); lfo.start(at);
    lp.connect(out); out.connect(this.bus);
    const oscs=[lfo];
    freqs.forEach((f,i)=>{
      for(const det of [-7, 6]){ const o=c.createOscillator(); o.type = i%2? 'triangle':'sawtooth'; o.frequency.value=f; o.detune.value=det + (i*3);
        const g=c.createGain(); g.gain.value = (i%2?0.10:0.045)/Math.sqrt(freqs.length); o.connect(g); g.connect(lp); o.start(at); oscs.push(o); }
    });
    return {out, oscs};
  }
  setScene(id, at){
    const c=this.ctx;
    // a scene change always brings the master back (silence() may have taken it away)
    if(this.started){ this.master.gain.cancelScheduledValues(at); this.master.gain.setValueAtTime(Math.max(this.master.gain.value, 0.0001), at); this.master.gain.setTargetAtTime(0.9, at, 1.6); }
    for(const p of this.pads){ p.out.gain.cancelScheduledValues(at); p.out.gain.setValueAtTime(Math.max(p.out.gain.value,0.0001), at); p.out.gain.exponentialRampToValueAtTime(0.0001, at+4.5); for(const o of p.oscs) o.stop(at+4.6); }
    this.pads = [];
    const chord = CHORDS[id]||[];
    if(chord.length){ this.pads.push(this._pad(chord, at, id===8?0.35:0.75)); }
    const windLvl = {0:0.0,1:0.16,2:0.22,3:0.0,4:0.02,5:0.10,6:0.0,7:0.20,8:0.24}[id]||0;
    this.wind.gain.cancelScheduledValues(at); this.wind.gain.setTargetAtTime(windLvl, at, 2.5);
    this.hum.gain.setTargetAtTime(id===0||id===3? 0.06 : 0.02, at, 2.0);
    // layers
    this._stopLayers(at);
    if(id===5) this._waves(at);
    if(id===6) this._crowd(at);
    if(id===3) this._modem(at);
  }
  _stopLayers(at){ for(const k in this.layers){ const L=this.layers[k]; L.g.gain.cancelScheduledValues(at); L.g.gain.setTargetAtTime(0.0, at, 1.5); for(const n of L.nodes){ try{ n.stop(at+6); }catch(e){} } } this.layers={}; }
  _waves(at){ const c=this.ctx; const n=c.createBufferSource(); n.buffer=this.noiseBuf; n.loop=true;
    const lp=c.createBiquadFilter(); lp.type='lowpass'; lp.frequency.value=650; const g=c.createGain(); g.gain.value=0;
    const lfo=c.createOscillator(); lfo.frequency.value=0.13; const lg=c.createGain(); lg.gain.value=0.12; lfo.connect(lg);
    const amp=c.createGain(); amp.gain.value=0.16; lg.connect(amp.gain);
    n.connect(lp); lp.connect(amp); amp.connect(g); g.connect(this.bus); n.start(at); lfo.start(at);
    g.gain.setTargetAtTime(1.0, at, 3.0); this.layers.waves={g, nodes:[n,lfo]}; }
  _crowd(at){ const c=this.ctx; const n=c.createBufferSource(); n.buffer=this.noiseBuf; n.loop=true; n.playbackRate.value=0.6;
    const bp=c.createBiquadFilter(); bp.type='bandpass'; bp.frequency.value=700; bp.Q.value=1.2; const g=c.createGain(); g.gain.value=0;
    const amp=c.createGain(); amp.gain.value=0.05; n.connect(bp); bp.connect(amp); amp.connect(g); g.connect(this.bus); n.start(at);
    g.gain.setTargetAtTime(1.0, at, 3.0);
    // distant pulse 70bpm, one minute ahead
    const nodes=[n];
    for(let i=0;i<70;i++){ const t0=at+1.0+i*(60/70); const o=c.createOscillator(); o.type='sine'; o.frequency.setValueAtTime(95,t0); o.frequency.exponentialRampToValueAtTime(42,t0+0.25);
      const og=c.createGain(); og.gain.setValueAtTime(0.0001,t0); og.gain.exponentialRampToValueAtTime(0.28,t0+0.012); og.gain.exponentialRampToValueAtTime(0.0001,t0+0.42);
      o.connect(og); og.connect(g); o.start(t0); o.stop(t0+0.5); nodes.push(o); }
    this.layers.crowd={g, nodes}; }
  _modem(at){ const c=this.ctx; const g=c.createGain(); g.gain.value=0; g.connect(this.bus);
    const o=c.createOscillator(); o.type='square'; o.frequency.value=1200; const og=c.createGain(); og.gain.value=0.006;
    const lfo=c.createOscillator(); lfo.type='square'; lfo.frequency.value=7; const lg=c.createGain(); lg.gain.value=400; lfo.connect(lg); lg.connect(o.frequency);
    const lp=c.createBiquadFilter(); lp.type='lowpass'; lp.frequency.value=2400; o.connect(og); og.connect(lp); lp.connect(g); o.start(at); lfo.start(at);
    g.gain.setTargetAtTime(1.0, at, 1.0); g.gain.setTargetAtTime(0.0, at+5.0, 1.5);
    this.layers.modem={g, nodes:[o,lfo]}; }
  note(freq, at, opts={}){
    const c=this.ctx; const g=c.createGain(); const lvl=opts.level||0.22; const dec=opts.decay||2.8;
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(lvl, at+0.012); g.gain.exponentialRampToValueAtTime(0.0001, at+dec);
    const o=c.createOscillator(); o.type='sine'; o.frequency.value=freq; o.connect(g);
    const o2=c.createOscillator(); o2.type='sine'; o2.frequency.value=freq*2.756; const g2=c.createGain(); g2.gain.value=0.18; o2.connect(g2); g2.connect(g);
    const o3=c.createOscillator(); o3.type='triangle'; o3.frequency.value=freq*0.5; const g3=c.createGain(); g3.gain.value=0.25; o3.connect(g3); g3.connect(g);
    g.connect(this.bus); o.start(at); o2.start(at); o3.start(at); o.stop(at+dec+0.1); o2.stop(at+dec+0.1); o3.stop(at+dec+0.1);
  }
  scaleNote(root, degree, at, opts){ const st = PENTA[((degree%PENTA.length)+PENTA.length)%PENTA.length] + 12*Math.floor(degree/PENTA.length); this.note(root*Math.pow(2, st/12), at, opts); }
  tick(at, hi){ const c=this.ctx; const n=c.createBufferSource(); n.buffer=this.tickBuf; const bp=c.createBiquadFilter(); bp.type='bandpass'; bp.frequency.value= hi? 4200: 2600; bp.Q.value=2.0;
    const g=c.createGain(); g.gain.setValueAtTime(hi?0.12:0.07, at); g.gain.exponentialRampToValueAtTime(0.0001, at+0.05); n.connect(bp); bp.connect(g); g.connect(this.master); n.start(at); n.stop(at+0.07); }
  headphones(on, at){ this.hp.frequency.cancelScheduledValues(at); this.hp.frequency.setTargetAtTime(on? 18000 : 520, at, 0.6);
    for(const p of this.pads){ p.out.gain.cancelScheduledValues(at); p.out.gain.setTargetAtTime(on? 0.75 : 0.0001, at, 1.2); } }
  gust(at){ this.wind.gain.cancelScheduledValues(at); const v=this.wind.gain.value; this.wind.gain.setTargetAtTime(Math.min(0.5, v*2.4+0.1), at, 0.4); this.wind.gain.setTargetAtTime(v, at+1.5, 1.8); }
  snap(at){ const c=this.ctx; const n=c.createBufferSource(); n.buffer=this.tickBuf; n.playbackRate.value=0.5; const g=c.createGain(); g.gain.setValueAtTime(0.5, at); g.gain.exponentialRampToValueAtTime(0.0001, at+0.12); n.connect(g); g.connect(this.bus); n.start(at); n.stop(at+0.13); }
  silence(at, secs){ this.master.gain.cancelScheduledValues(at); this.master.gain.setTargetAtTime(0.0, at, secs/3); }
  end(at){ this.master.gain.cancelScheduledValues(at); this.master.gain.setTargetAtTime(0.0, at, 2.0); }
}

// Event-recording facade with the same method names.
class Recorder { constructor(){ this.events=[]; this.t=0; }
  setTime(t){ this.t=t; }
  _log(name, args){ this.events.push({t:this.t, name, args}); }
  start(){ this._log('start',[]); } setScene(id){ this._log('setScene',[id]); } note(f,_,o){ this._log('note',[f,o||{}]); }
  scaleNote(r,d,_,o){ this._log('scaleNote',[r,d,o||{}]); } tick(_,hi){ this._log('tick',[!!hi]); } headphones(on){ this._log('headphones',[on]); }
  gust(){ this._log('gust',[]); } snap(){ this._log('snap',[]); } silence(_,s){ this._log('silence',[s]); } end(){ this._log('end',[]); }
}
// Live facade: fills in `at = ctx.currentTime`.
class Live { constructor(ctx){ this.ctx=ctx; this.e=new Engine(ctx); }
  get now(){ return this.ctx.currentTime + 0.02; }
  start(){ this.e.start(this.now); } setScene(id){ this.e.setScene(id, this.now); } note(f,_,o){ this.e.note(f,this.now,o); }
  scaleNote(r,d,_,o){ this.e.scaleNote(r,d,this.now,o); } tick(_,hi){ this.e.tick(this.now,hi); } headphones(on){ this.e.headphones(on,this.now); }
  gust(){ this.e.gust(this.now); } snap(){ this.e.snap(this.now); } silence(_,s){ this.e.silence(this.now,s); } end(){ this.e.end(this.now); }
  extraOut(n){ this.e.extraOut(n); } }

async function renderOffline(events, duration, sampleRate=48000){
  const ctx = new OfflineAudioContext(2, Math.ceil(duration*sampleRate), sampleRate);
  const e = new Engine(ctx);
  for(const ev of events){ const at = Math.max(0, ev.t); const a = ev.args;
    switch(ev.name){
      case 'start': e.start(at); break; case 'setScene': e.setScene(a[0], at); break;
      case 'note': e.note(a[0], at, a[1]); break; case 'scaleNote': e.scaleNote(a[0], a[1], at, a[2]); break;
      case 'tick': e.tick(at, a[0]); break; case 'headphones': e.headphones(a[0], at); break;
      case 'gust': e.gust(at); break; case 'snap': e.snap(at); break; case 'silence': e.silence(at, a[0]); break; case 'end': e.end(at); break;
    } }
  const buf = await ctx.startRendering();
  // -> 16-bit PCM interleaved, base64 chunks
  const L = buf.getChannelData(0), R = buf.getChannelData(1); const n = buf.length;
  const chunks=[]; const CH = 1<<19;
  for(let s=0; s<n; s+=CH){ const m=Math.min(CH, n-s); const b=new Int16Array(m*2);
    for(let i=0;i<m;i++){ const l=Math.max(-1,Math.min(1,L[s+i])), r=Math.max(-1,Math.min(1,R[s+i])); b[i*2]=l<0?l*32768:l*32767; b[i*2+1]=r<0?r*32768:r*32767; }
    let str=''; const u8=new Uint8Array(b.buffer); for(let i=0;i<u8.length;i+=8192) str+=String.fromCharCode.apply(null, u8.subarray(i,i+8192)); chunks.push(btoa(str)); }
  return {sampleRate, channels:2, chunks};
}

return { Engine, Recorder, Live, renderOffline, CHORDS };
})();
