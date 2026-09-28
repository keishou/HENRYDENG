// ETHER · 以太 — engine, scenes, overlay, autopilot, render hooks.
(() => {
'use strict';
const W = 1280, H = 720;
const Q = new URLSearchParams(location.search);
const RENDER = Q.get('render') === '1';
const AUTO = RENDER || Q.get('auto') === '1';
const SEED = parseInt(Q.get('seed') || '7', 10);
const START_SCENE = parseInt(Q.get('scene') || '0', 10);
const T = window.ETHER_TEXT, SH = window.ETHER_SHADERS, AU = window.ETHER_AUDIO;

// ---------- deterministic randomness ----------
function mulberry32(a){ return function(){ a|=0; a=a+0x6D2B79F5|0; let t=Math.imul(a^a>>>15,1|a); t=t+Math.imul(t^t>>>7,61|t)^t; return ((t^t>>>14)>>>0)/4294967296; }; }
const rnd = mulberry32(SEED);
function shuffle(arr){ const a=arr.slice(); for(let i=a.length-1;i>0;i--){ const j=Math.floor(rnd()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; }
function h1(i){ const s=Math.sin(i*127.1+311.7)*43758.5453; return s-Math.floor(s); }
function n1(x){ const i=Math.floor(x), f=x-i, u=f*f*(3-2*f); return h1(i)+(h1(i+1)-h1(i))*u; }
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)); const lerp=(a,b,t)=>a+(b-a)*t; const ss=(a,b,x)=>{ const t=clamp((x-a)/(b-a),0,1); return t*t*(3-2*t); };

// ---------- fonts ----------
const F = {
  serif: '"Noto Serif SC","Songti SC","SimSun","WenQuanYi Zen Hei",serif',
  latin: '"Cormorant Garamond","Noto Serif SC",Georgia,serif',
  mono: '"Noto Sans SC","WenQuanYi Zen Hei Mono","Menlo",monospace',
};

// ---------- GL ----------
const glc = document.getElementById('gl');
const gl = glc.getContext('webgl2', { antialias:false, alpha:false, preserveDrawingBuffer: RENDER, powerPreference:'high-performance' });
if(!gl){ document.getElementById('gate').innerHTML = '<p>需要 WebGL2 / WebGL2 required</p>'; return; }
glc.width = W; glc.height = H;
const ov = document.createElement('canvas'); ov.width=W; ov.height=H; const ctx = ov.getContext('2d');
const snap = document.createElement('canvas'); snap.width=W; snap.height=H; const sctx = snap.getContext('2d');

function compile(type, src){ const s=gl.createShader(type); gl.shaderSource(s,src); gl.compileShader(s);
  if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)){ const log=gl.getShaderInfoLog(s); console.error(log); throw new Error('shader: '+log); } return s; }
function program(vs, fs){ const p=gl.createProgram(); gl.attachShader(p,compile(gl.VERTEX_SHADER,vs)); gl.attachShader(p,compile(gl.FRAGMENT_SHADER,fs)); gl.linkProgram(p);
  if(!gl.getProgramParameter(p,gl.LINK_STATUS)) throw new Error('link: '+gl.getProgramInfoLog(p)); const u={}; return { p, u(name){ if(!(name in u)) u[name]=gl.getUniformLocation(p,name); return u[name]; } }; }
const PS = program(SH.VERT, SH.SCENE), PC = program(SH.VERT, SH.COMP), PB = program(SH.VERT, SH.BLOOM), PP = program(SH.VERT, SH.POST);
// scene quality: procedural pass resolution factor (software GL -> half res; the overlay stays crisp)
const RENDERER = (() => { try { const e=gl.getExtension('WEBGL_debug_renderer_info'); return e? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER); } catch(err){ return ''; } })();
const QUAL = Q.get('q') ? parseFloat(Q.get('q')) : (/SwiftShader|llvmpipe|Software/i.test(RENDERER) ? 0.5 : 1.0);
const SW = Math.round(W*QUAL), SHh = Math.round(H*QUAL), BW = Math.round(W/4), BH = Math.round(H/4);
const vbo = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vbo); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
const vao = gl.createVertexArray(); gl.bindVertexArray(vao); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,2,gl.FLOAT,false,0,0);
function makeTex(){ const t=gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D,t); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE); return t; }
const texOv = makeTex(); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,W,H,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
function target(w,h){ const tex=makeTex(); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,w,h,0,gl.RGBA,gl.UNSIGNED_BYTE,null); const fb=gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER,fb); gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,tex,0); gl.bindFramebuffer(gl.FRAMEBUFFER,null); return {tex,fb,w,h}; }
const rtScene = target(SW,SHh), rtComp = target(W,H), rtBloom = target(BW,BH);

// ---------- assets ----------
const IMG = {};
function loadImg(name, src){ return new Promise((res,rej)=>{ const im=new Image(); im.onload=()=>{IMG[name]=im;res();}; im.onerror=rej; im.src=src; }); }

// ---------- state ----------
const G = {
  t:0, st:0, scene:START_SCENE, from:-1, mix:0, trans:null, snapAlpha:0,
  cam:{x:0,y:0}, shake:{x:0,y:0}, listen:0, params:[1,0,0,0],
  player:{x:420, wx:0, y:600, dir:1, walk:0, walking:false, scale:0.85, listening:0, headphones:'on', still:0, armsUp:false, stick:false, tilt:0},
  input:{left:false,right:false,up:false,space:false,spaceEdge:false,enterEdge:false,anyEdge:false,yn:null,typed:''},
  post:{grain:0.06, aberr:0.5, vig:0.7, letter:0, crt:0, pillar:0, dv:0, flash:0, fade:1, bloom:0.4, desat:0, warm:0.3},
  postT:{},
  discs:new Float32Array(32), nDiscs:0,
  card:null, hintT:0, finished:false, audio:null, muted:false,
};
const discsScreen = []; // {x,y,r,phase,hit}

// ---------- thought stream ----------
const Stream = {
  items:[],
  emit(text, style='drift', o={}){
    const it = { text, style, t0:G.t, life:o.life||7.5, x:o.x, y:o.y, size:o.size, color:o.color||'#f2f2f2', font:o.font||F.serif, shadow:o.shadow!==false, dark:o.dark||false };
    if(style==='drift'){ it.x = o.x ?? clamp(G.player.x + (rnd()<0.5?-1:1)*(120+rnd()*160), 120, W-140); it.y = o.y ?? (300 + rnd()*160); it.size=o.size||27; }
    if(style==='sub'){ const n=this.items.filter(i=>i.style==='sub' && (G.t-i.t0) < i.life-1.0).length; it.x = W/2; it.y = (o.y ?? 640) - n*42; it.size=o.size||26; }
    if(style==='center'){ it.x=W/2; it.y=o.y ?? 330; it.size=o.size||40; it.life=o.life||6; }
    if(style==='vertical'){ it.x = o.x ?? (W-110 - rnd()*60); it.y = o.y ?? 90; it.size=o.size||24; it.life=o.life||9; }
    if(style==='corner'){ it.x = o.x ?? 90; it.y = o.y ?? 120; it.size=o.size||20; }
    this.items.push(it);
  },
  clear(){ this.items=[]; },
  draw(ctx){
    const alive=[];
    for(const it of this.items){ const a=G.t-it.t0; if(a>it.life) continue; alive.push(it);
      const al = ss(0,1.1,a) * ss(it.life, it.life-1.6, a);
      ctx.save(); ctx.globalAlpha = al*0.96; ctx.fillStyle = it.color; ctx.font = `400 ${it.size}px ${it.font}`; ctx.textBaseline='middle';
      if(it.shadow){ ctx.shadowColor = it.dark? 'rgba(255,255,255,0.35)':'rgba(0,0,0,0.65)'; ctx.shadowBlur = 12; }
      if(it.style==='vertical'){ ctx.textAlign='center'; let y=it.y; for(const ch of it.text){ ctx.fillText(ch, it.x, y + a*3); y += it.size*1.12; } }
      else if(it.style==='drift'){ ctx.textAlign='left'; ctx.fillText(it.text, it.x - Math.min(it.text.length*it.size*0.5, it.x-40), it.y - a*9); }
      else { ctx.textAlign='center'; if(it.style==='center'){ ctx.letterSpacing='0.08em'; } ctx.fillText(it.text, it.x, it.y - (it.style==='center'? a*4:0)); }
      ctx.restore(); }
    this.items = alive;
  }
};

// ---------- avatar ----------
function drawAvatar(ctx, x, y, o){
  const s=o.scale||1, P=G.player; const walk=o.walk||0; const walking=!!o.walking; const inkA = o.alpha ?? 0.93;
  ctx.save(); ctx.translate(x,y); ctx.scale(s,s);
  ctx.fillStyle='rgba(0,0,0,0.26)'; ctx.beginPath(); ctx.ellipse(0,3,44,7,0,0,Math.PI*2); ctx.fill();
  const ink = `rgba(16,16,22,${inkA})`; ctx.strokeStyle=ink; ctx.fillStyle=ink; ctx.lineCap='round'; ctx.lineJoin='round';
  const sw = walking? Math.sin(walk):0; const bob = walking? Math.abs(Math.cos(walk))*3:0;
  // legs
  ctx.lineWidth=13;
  for(const side of [-1,1]){ const ph = side<0? sw : -sw; const fx = ph*18*P.dir, kx = fx*0.5 + Math.max(0,ph)*7*P.dir; ctx.beginPath(); ctx.moveTo(side*9, -95-bob); ctx.lineTo(kx+side*5, -50-bob*0.5); ctx.lineTo(fx+side*7, 0); ctx.stroke(); }
  // torso
  ctx.beginPath(); ctx.moveTo(-28,-176-bob); ctx.quadraticCurveTo(0,-183-bob,28,-176-bob); ctx.quadraticCurveTo(26,-130-bob,20,-90-bob); ctx.lineTo(-20,-90-bob); ctx.quadraticCurveTo(-26,-130-bob,-28,-176-bob); ctx.fill();
  // arms
  ctx.lineWidth=10;
  if(o.armsUp){ ctx.beginPath(); ctx.moveTo(24,-170-bob); ctx.lineTo(44,-215-bob); ctx.lineTo(40,-262-bob); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-24,-170-bob); ctx.lineTo(-34,-120-bob); ctx.stroke(); }
  else if(o.stick){ ctx.beginPath(); ctx.moveTo(24,-170-bob); ctx.lineTo(46,-210-bob); ctx.lineTo(42,-255-bob); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-24,-170-bob); ctx.lineTo(-30,-105-bob); ctx.stroke();
    ctx.strokeStyle='rgba(185,255,200,0.95)'; ctx.lineWidth=7; ctx.beginPath(); ctx.moveTo(42,-262-bob); ctx.lineTo(52,-340-bob); ctx.stroke(); ctx.strokeStyle=ink; }
  else { const a1 = walking? Math.sin(walk)*14:0; ctx.beginPath(); ctx.moveTo(24,-170-bob); ctx.lineTo(30+a1*P.dir,-100-bob); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-24,-170-bob); ctx.lineTo(-30-a1*P.dir,-100-bob); ctx.stroke(); }
  // neck + head (the ID photo, always frontal)
  ctx.fillRect(-6,-192-bob,12,18);
  ctx.save(); ctx.translate(0,-184-bob); ctx.rotate(o.tilt||0);
  if(o.listen>0){ const L=o.listen; for(let k=0;k<3;k++){ const ph=(G.t*0.5+k*0.33)%1; ctx.strokeStyle=`rgba(180,215,255,${(1-ph)*0.45*L})`; ctx.lineWidth=1.5; ctx.beginPath(); ctx.arc(0,-38,52+ph*70,0,Math.PI*2); ctx.stroke(); } }
  const im=IMG.face; if(im){ ctx.drawImage(im,-32,-80,64,82); }
  // headphones
  if(o.headphones==='on'){ ctx.strokeStyle='rgba(12,12,16,0.96)'; ctx.lineWidth=5; ctx.beginPath(); ctx.arc(0,-42,36,Math.PI*1.08,Math.PI*1.92); ctx.stroke();
    ctx.fillStyle='rgba(12,12,16,0.97)'; for(const sd of [-1,1]){ ctx.beginPath(); ctx.ellipse(sd*35,-34,9,14,0,0,Math.PI*2); ctx.fill(); }
    ctx.fillStyle='rgba(90,90,100,0.6)'; ctx.beginPath(); ctx.ellipse(-36,-37,3,5,0,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle='rgba(20,20,26,0.85)'; ctx.lineWidth=1.6; ctx.beginPath(); ctx.moveTo(-36,-22); ctx.quadraticCurveTo(-48,40,-22,86); ctx.stroke(); }
  ctx.restore();
  if(o.headphones==='neck'){ ctx.strokeStyle='rgba(12,12,16,0.96)'; ctx.lineWidth=5; ctx.beginPath(); ctx.arc(0,-178-bob,24,Math.PI*0.1,Math.PI*0.9); ctx.stroke(); ctx.fillStyle='rgba(12,12,16,0.97)';
    for(const sd of [-1,1]){ ctx.beginPath(); ctx.ellipse(sd*24,-172-bob,8,12,0,0,Math.PI*2); ctx.fill(); } }
  ctx.restore();
}

// ---------- chapter card ----------
function drawCard(ctx){
  const c=G.card; if(!c) return; const a=G.t-c.t0; if(a>5.2){ G.card=null; return; }
  const al = ss(0,0.9,a)*ss(5.2,4.0,a); const ch=c.ch;
  ctx.save(); ctx.globalAlpha=al; ctx.textBaseline='alphabetic'; ctx.textAlign='left';
  const x=96, y=548;
  // soft dark backing so the card reads on bright scenes
  const gr=ctx.createRadialGradient(x+120,y-10,20,x+120,y-10,300); gr.addColorStop(0,'rgba(0,0,0,0.42)'); gr.addColorStop(1,'rgba(0,0,0,0)'); ctx.fillStyle=gr; ctx.fillRect(x-260,y-320,760,560);
  ctx.shadowColor='rgba(0,0,0,0.55)'; ctx.shadowBlur=14;
  ctx.fillStyle='#f4f4f4'; ctx.font=`400 20px ${F.latin}`; ctx.letterSpacing='0.45em'; ctx.fillText(ch.num, x, y-62);
  ctx.font=`400 50px ${F.serif}`; ctx.letterSpacing='0.18em'; ctx.fillText(ch.zh, x, y);
  ctx.font=`italic 400 21px ${F.latin}`; ctx.letterSpacing='0.12em'; ctx.fillStyle='rgba(244,244,244,0.85)'; ctx.fillText(ch.en, x+2, y+34);
  ctx.font=`400 17px ${F.serif}`; ctx.letterSpacing='0.25em'; ctx.fillStyle='rgba(244,244,244,0.7)'; ctx.fillText(ch.line, x+2, y+64);
  ctx.strokeStyle='rgba(255,255,255,0.55)'; ctx.lineWidth=1; ctx.beginPath(); ctx.moveTo(x,y-46); ctx.lineTo(x+Math.min(1,a/1.4)*140,y-46); ctx.stroke();
  ctx.restore();
}

// ---------- scenes ----------
const SCENES = [];
const I = G.input, P = G.player;
function walkUpdate(dt, speed, minX, maxX, useWorld){
  let dx=0; if(I.left) dx-=1; if(I.right) dx+=1;
  P.walking = dx!==0; if(dx){ P.dir = dx; P.walk += dt*7.5; P.still=0; if(useWorld){ P.wx = clamp(P.wx+dx*speed*dt, minX, maxX); } else { P.x = clamp(P.x+dx*speed*dt, minX, maxX); } }
  else P.still += dt;
}
const S = {}; // helpers per-scene
function chapter(n){ G.card={t0:G.t, ch:T.chapters[n]}; }
function audioScene(id){ if(G.audio) G.audio.setScene(id); }

// 0 · prologue
SCENES.push({ name:'prologue', shader:0, post:{grain:0.05, aberr:0.35, vig:0.55, crt:0.7, bloom:0.5, letter:0, pillar:0, dv:0, warm:0, desat:0},
  enter(){ this.lines=T.prologue; this.done=false; P.headphones='on'; audioScene(0); },
  update(dt){ const st=G.st; if(AUTO? st>8.5 : (I.anyEdge && st>1.5)) { if(!this.done){ this.done=true; go(1,'mix'); } } },
  draw(ctx){ const st=G.st; ctx.save(); ctx.font=`400 15px ${F.mono}`; ctx.fillStyle='rgba(150,235,170,0.85)'; ctx.textBaseline='top';
    let y=52; this.lines.forEach((ln,i)=>{ const t0=0.6+i*1.25; if(st<t0) return; const n=Math.floor((st-t0)*32); ctx.fillText(ln.slice(0,n), 64, y); y+=26; });
    if(Math.floor(st*2.2)%2===0){ ctx.fillRect(64, y+2, 9, 16); }
    const ta = ss(1.6,3.4,st); ctx.globalAlpha=ta; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillStyle='#f0f0f0';
    ctx.font=`400 104px ${F.serif}`; ctx.letterSpacing='0.3em'; ctx.fillText('以太', W/2+16, 318);
    ctx.font=`400 26px ${F.latin}`; ctx.letterSpacing='0.7em'; ctx.fillStyle='rgba(240,240,240,0.8)'; ctx.fillText('ETHER', W/2+10, 398);
    ctx.font=`400 15px ${F.serif}`; ctx.letterSpacing='0.35em'; ctx.fillStyle='rgba(240,240,240,0.5)'; ctx.fillText(T.title.sub, W/2+4, 446);
    if(!AUTO && st>3){ ctx.globalAlpha=ta*(0.5+0.5*Math.sin(st*3)); ctx.font=`400 14px ${F.serif}`; ctx.fillText('按任意键 登录', W/2, 600); }
    ctx.restore(); },
});

// 1 · the field
SCENES.push({ name:'field', shader:1, post:{grain:0.07, aberr:0.55, vig:0.75, crt:0, bloom:0.35, letter:0.06, pillar:0, dv:0, warm:0.35, desat:0},
  enter(){ P.wx=0; P.x=460; P.y=604; P.scale=0.86; P.headphones='on'; P.dir=1; this.thoughts=shuffle(T.field); this.ti=0; this.nextT=3.2; this.listenQ=T.fieldListen.slice(); this.li=0; this.lnext=0; this.gust=6; chapter(1); audioScene(1); G.hintT=G.t; },
  update(dt){ const st=G.st;
    if(AUTO){ I.right = (st<7.5) || (st>13.5 && st<23.5); I.space = st>8.5 && st<12.8; }
    walkUpdate(dt, 150, 0, 4200, true); G.cam.x = P.wx; P.x = 460;
    const wantListen = I.space || P.still>2.6; P.listening = lerp(P.listening, wantListen?1:0, 1-Math.exp(-dt*2.2)); G.listen=P.listening;
    G.postT.desat = P.listening*0.22; G.postT.aberr = 0.55 + P.listening*0.6;
    if(st>this.nextT && this.ti<this.thoughts.length){ const style = ['drift','vertical','sub','drift','sub','vertical'][this.ti%6]; Stream.emit(this.thoughts[this.ti++], style); this.nextT = st + 5.2 + rnd()*1.5; }
    if(P.listening>0.6 && st>this.lnext && this.li<this.listenQ.length){ Stream.emit(this.listenQ[this.li++], 'center', {size:36, life:5}); this.lnext = st+4.2; }
    if(st>this.gust){ this.gust = st + 5 + rnd()*4; if(G.audio) G.audio.gust(); }
    if(G.audio && this.ti%3===0 && st>this.nextT-0.1 && st<this.nextT+dt){ G.audio.scaleNote(146.83*2, Math.floor(rnd()*6), 0, {level:0.12, decay:4}); }
    if(P.wx>=4100 || (AUTO && st>24.5)) go(2,'white'); },
  draw(ctx){ const cx=G.cam.x;
    // power lines
    ctx.save(); ctx.strokeStyle='rgba(28,28,34,0.82)'; ctx.lineCap='round';
    const poles=[]; for(let k=-1;k<12;k++){ const sx = 300 + k*640 - cx*0.86; if(sx>-80 && sx<W+80) poles.push(sx); }
    for(const sx of poles){ ctx.lineWidth=3.2; ctx.beginPath(); ctx.moveTo(sx,522); ctx.lineTo(sx,214); ctx.stroke(); ctx.lineWidth=2.2; ctx.beginPath(); ctx.moveTo(sx-22,236); ctx.lineTo(sx+22,236); ctx.stroke(); ctx.beginPath(); ctx.moveTo(sx-16,256); ctx.lineTo(sx+16,256); ctx.stroke(); }
    ctx.lineWidth=1; ctx.strokeStyle='rgba(28,28,34,0.55)';
    for(let k=-1;k<12;k++){ const a = 300 + k*640 - cx*0.86, b = a+640; if(b<-80||a>W+80) continue; for(const [yy,sag] of [[236,26],[256,24]]){ ctx.beginPath(); ctx.moveTo(a-22,yy); ctx.quadraticCurveTo((a+b)/2, yy+sag*2, b-22, yy); ctx.stroke(); } }
    ctx.restore();
    drawAvatar(ctx, P.x, P.y, {scale:P.scale, walk:P.walk, walking:P.walking, headphones:P.headphones, listen:P.listening});
    if(!AUTO){ const a=G.t-G.hintT; if(a<9){ ctx.save(); ctx.globalAlpha=ss(1,2.5,a)*ss(9,7,a)*0.75; ctx.font=`400 15px ${F.serif}`; ctx.fillStyle='#fff'; ctx.textAlign='right'; ctx.letterSpacing='0.2em'; ctx.shadowColor='rgba(0,0,0,.6)'; ctx.shadowBlur=8; T.hints.forEach((h,i)=>ctx.fillText(h, W-70, 80+i*26)); ctx.restore(); } } },
});

// 2 · the kite
SCENES.push({ name:'kite', shader:2, post:{grain:0.06, aberr:0.7, vig:0.6, crt:0, bloom:0.35, letter:0.06, pillar:0, dv:0, warm:0.25, desat:0},
  enter(){ P.x=640; P.y=760; P.scale=1.05; P.walking=false; this.thoughts=shuffle(T.kite); this.ti=0; this.nextT=2.5; this.broken=false; this.BREAK=15.5; this.k={x:700,y:200,vx:0,vy:0,rot:0}; this.pull=0; this.gust=3; this.strAlpha=1; chapter(2); audioScene(2); G.cam.x=0; },
  update(dt){ const st=G.st; const k=this.k;
    if(AUTO){ I.up = (st>3&&st<5)||(st>8&&st<9.5)||(st>12&&st<13.5); I.left=false; I.right=false; }
    this.pull = lerp(this.pull, I.up?1:0, 1-Math.exp(-dt*4));
    G.cam.x += dt*30;
    if(!this.broken){ const wx = 640 + 250*(n1(st*0.13+3)*2-1) + 60*Math.sin(st*0.7); const wy = 210 + 80*(n1(st*0.21+9)*2-1) - this.pull*110;
      k.x = lerp(k.x, wx, 1-Math.exp(-dt*0.9)); k.y = lerp(k.y, wy, 1-Math.exp(-dt*1.2)); k.rot = (k.x-640)*0.0009 + Math.sin(st*1.3)*0.06;
      if(st>=this.BREAK){ this.broken=true; k.vx=140; k.vy=-90; if(G.audio) G.audio.snap(); Stream.emit(T.kiteBreak, 'center', {size:44, life:4.5}); } }
    else { k.vy -= 40*dt; k.vx += 25*dt; k.x += k.vx*dt; k.y += k.vy*dt; k.rot += dt*0.9; this.strAlpha = Math.max(0, this.strAlpha - dt*0.6); }
    if(st>this.nextT && this.ti<this.thoughts.length && !this.broken){ { const sty=['sub','vertical','drift'][this.ti%3]; Stream.emit(this.thoughts[this.ti++], sty, sty==='drift'? {x:200+rnd()*260, y:380+rnd()*140} : {}); this.nextT = st + 4.6; } }
    if(st>this.gust){ this.gust = st + 3.5 + rnd()*3; if(G.audio){ G.audio.gust(); G.audio.scaleNote(196*2, 2+Math.floor(rnd()*5), 0, {level:0.10, decay:5}); } }
    P.tilt = -0.22; P.armsUp = true;
    if(st > this.BREAK + 4.2) go(3,'cut'); },
  draw(ctx){ const k=this.k, st=G.st;
    // string
    const hx = P.x+42*P.scale, hy = P.y-262*P.scale;
    ctx.save(); ctx.strokeStyle=`rgba(255,255,255,${0.55*this.strAlpha})`; ctx.lineWidth=1.2; ctx.beginPath(); ctx.moveTo(hx,hy);
    if(!this.broken){ const mx=(hx+k.x)/2 + 90*Math.sin(st*0.5), my=(hy+k.y)/2 + 40; ctx.quadraticCurveTo(mx,my,k.x,k.y+48); }
    else { const fall = Math.min(1,(st-this.BREAK)*0.5); ctx.quadraticCurveTo(hx+80, hy-200+fall*400, hx+30+fall*120, hy-80+fall*350); }
    ctx.stroke(); ctx.restore();
    // kite
    ctx.save(); ctx.translate(k.x,k.y); ctx.rotate(k.rot);
    ctx.fillStyle='#c9323b'; ctx.strokeStyle='rgba(40,10,12,0.8)'; ctx.lineWidth=1.5;
    ctx.beginPath(); ctx.moveTo(0,-42); ctx.lineTo(30,0); ctx.lineTo(0,50); ctx.lineTo(-30,0); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0,-42); ctx.lineTo(0,50); ctx.moveTo(-30,0); ctx.lineTo(30,0); ctx.stroke();
    ctx.fillStyle='rgba(255,255,255,0.25)'; ctx.beginPath(); ctx.moveTo(0,-42); ctx.lineTo(30,0); ctx.lineTo(0,0); ctx.closePath(); ctx.fill();
    ctx.strokeStyle='rgba(255,240,240,0.85)'; ctx.lineWidth=1.5; ctx.beginPath(); ctx.moveTo(0,50); for(let i=1;i<=8;i++){ ctx.lineTo(Math.sin(st*3+i*0.9)*12*(i/8), 50+i*16); } ctx.stroke();
    ctx.restore();
    drawAvatar(ctx, P.x, P.y, {scale:P.scale, headphones:'on', armsUp:!this.broken, tilt:-0.2, listen:0}); },
});

// 3 · the BBS
SCENES.push({ name:'bbs', shader:3, post:{grain:0.05, aberr:0.9, vig:0.85, crt:1.0, bloom:0.9, letter:0, pillar:0, dv:0, warm:0, desat:0},
  enter(){ this.feed=[]; this.fi=0; this.nextT=1.6; this.typed=''; this.posted=null; this.answer=null; this.qShown=false; this.phase='feed'; this.tickN=0; this.mosaic=14; this.autoType=0;
    I.typed=''; chapter(3); audioScene(3); const ime=document.getElementById('ime'); if(ime && !AUTO){ ime.value=''; ime.focus(); } },
  push(handle, text, cls){ this.feed.push({h:handle, t:text, cls:cls||'', t0:G.st, n:0}); if(this.feed.length>13) this.feed.shift(); },
  update(dt){ const st=G.st; const B=T.bbs;
    if(this.phase==='feed'){ if(st>this.nextT){ if(this.fi<8){ const f=B.feed[this.fi++]; this.push(f[0], f[1]); this.nextT = st + 1.35 + (f[1].length*0.02); } else { this.push('系统', B.login.replace('系统：',''), 'sys'); this.phase='input'; this.inputT=st; this.mosaic=22; } } }
    if(this.phase==='input'){
      if(AUTO){ const a = st - this.inputT - 1.2; if(a>0){ const n=Math.min(B.myPost.length, Math.floor(a*9)); if(n>this.autoType){ this.autoType=n; I.typed=B.myPost.slice(0,n); if(G.audio) G.audio.tick(0,false); } if(n>=B.myPost.length && a>B.myPost.length/9+1.0){ I.enterEdge=true; } } }
      if(I.enterEdge && I.typed.trim().length){ this.push('我', I.typed, 'me'); this.posted=I.typed; I.typed=''; const ime=document.getElementById('ime'); if(ime) ime.value=''; this.phase='reply'; this.replyT=st; if(G.audio) G.audio.tick(0,true); }
    }
    if(this.phase==='reply'){ if(st>this.replyT+1.7 && this.fi<11){ const f=B.feed[this.fi++]; this.push(f[0],f[1]); this.replyT=st; } if(this.fi>=11 && st>this.replyT+1.8){ this.push('白噪', '你也听见了吗  [Y / N]', 'q'); this.phase='question'; this.qT=st; } }
    if(this.phase==='question'){ if(AUTO && st>this.qT+3.2) I.yn='y'; if(I.yn){ this.answer=I.yn; this.push('我', I.yn==='y'?'Y':'N', 'me'); this.push('白噪', (I.yn==='y'?B.yes:B.no).replace('白噪：',''), ''); I.yn=null; this.phase='after'; this.aT=st; this.ai=0; if(G.audio) G.audio.scaleNote(164.81*2, 4, 0, {level:0.2, decay:6}); } }
    if(this.phase==='after'){ if(st>this.aT+2.2 && this.ai<B.after.length){ const ln=B.after[this.ai++]; const i=ln.indexOf('：'); this.push(ln.slice(0,i), ln.slice(i+1), ln.startsWith('系统')?'sys':''); this.aT=st; } if(this.ai>=B.after.length && st>this.aT+2.6) go(4,'cut'); }
    // typewriter ticks
    for(const f of this.feed){ const n=Math.min(f.t.length, Math.floor((st-f.t0)*26)); if(n>f.n){ if(G.audio && (n%2===0)) G.audio.tick(0,false); f.n=n; } }
  },
  draw(ctx){ const st=G.st; const B=T.bbs;
    ctx.save(); ctx.textBaseline='top'; ctx.font=`400 15px ${F.mono}`;
    ctx.fillStyle='rgba(150,235,170,0.6)'; ctx.fillText(B.header, 70, 40); ctx.fillRect(70, 64, 720, 1);
    let y=84; for(const f of this.feed){ const vis=f.t.slice(0, f.n);
      const hc = f.cls==='me'? '#ffffff' : f.cls==='sys'? 'rgba(120,180,140,0.8)' : 'rgba(150,235,170,0.95)';
      ctx.fillStyle=hc; ctx.font=`400 15px ${F.mono}`; ctx.fillText(f.h+'：', 70, y);
      ctx.fillStyle = f.cls==='me'? '#ffffff' : f.cls==='q'? '#eaffea' : f.cls==='sys'? 'rgba(160,200,170,0.75)' : 'rgba(220,255,225,0.9)';
      ctx.font=`400 17px ${F.serif}`; ctx.fillText(vis, 70+ctx.measureText(f.h).width*0.9+34, y-1); y+=33; }
    // input line
    const cur = Math.floor(st*2.5)%2===0;
    ctx.fillStyle='rgba(150,235,170,0.5)'; ctx.fillRect(70, 612, 720, 1);
    ctx.fillStyle='#ffffff'; ctx.font=`400 17px ${F.serif}`; const line = (this.phase==='input'? I.typed : '') ; ctx.fillText('> '+line + (cur && this.phase==='input' ? '▍':''), 70, 630);
    if(this.phase==='input' && !AUTO){ ctx.fillStyle='rgba(150,235,170,0.5)'; ctx.font=`400 13px ${F.serif}`; ctx.fillText('输入一句话，Enter 发送', 70, 662); }
    if(this.phase==='question' && !AUTO){ ctx.fillStyle='rgba(150,235,170,0.5)'; ctx.font=`400 13px ${F.serif}`; ctx.fillText('按 Y 或 N', 70, 662); }
    // webcam: face hidden (mosaic)
    const bx=1010, by=84, bw=190, bh=250; ctx.strokeStyle='rgba(150,235,170,0.55)'; ctx.lineWidth=1; ctx.strokeRect(bx,by,bw,bh);
    const im=IMG.portrait; if(im){ const m=this.mosaic; const mc = this._mc || (this._mc=document.createElement('canvas')); mc.width=m; mc.height=Math.round(m*1.32); const mctx=mc.getContext('2d'); mctx.drawImage(im,0,0,mc.width,mc.height);
      ctx.save(); ctx.imageSmoothingEnabled=false; ctx.globalAlpha=0.8; ctx.drawImage(mc, bx+8, by+8, bw-16, bh-16); ctx.restore();
      ctx.fillStyle='rgba(60,255,120,0.14)'; ctx.fillRect(bx+8,by+8,bw-16,bh-16); ctx.fillStyle='rgba(0,0,0,0.35)'; for(let yy=by+8; yy<by+bh-8; yy+=3) ctx.fillRect(bx+8,yy,bw-16,1); }
    ctx.fillStyle='rgba(150,235,170,0.7)'; ctx.font=`400 12px ${F.mono}`; ctx.fillText('CAM 01 · 脸：隐藏', bx, by+bh+8);
    if(Math.floor(st*1.5)%2===0){ ctx.fillStyle='rgba(255,80,80,0.9)'; ctx.beginPath(); ctx.arc(bx+bw-14, by+14, 4, 0, Math.PI*2); ctx.fill(); }
    ctx.restore(); },
});

// 4 · the record shop
SCENES.push({ name:'cd', shader:4, post:{grain:0.075, aberr:0.6, vig:0.9, crt:0, bloom:0.55, letter:0.06, pillar:0, dv:0, warm:0.15, desat:0},
  enter(){ P.x=180; P.y=648; P.scale=0.8; P.headphones='on'; P.dir=1; P.tilt=0; P.armsUp=false; this.thoughts=shuffle(T.cd); this.ti=0; this.got=0; this.doneT=null;
    discsScreen.length=0; const xs=[330, 470, 610, 760, 900, 1050]; xs.forEach((x,i)=>{ discsScreen.push({x, y: 250 + (i%2)*95 + rnd()*30, r: 58 + rnd()*22, phase: rnd()*6.28, hit:false, hitT:0}); });
    this.order = [0,1,2,3,4,5]; this.target=0; this.noteI=0; this.waitUntil=2.0; chapter(4); audioScene(4); G.cam.x=0; },
  update(dt){ const st=G.st;
    if(AUTO){ const d = this.target<discsScreen.length? discsScreen[this.order[this.target]] : null; I.left=false; I.right=false; I.space=false;
      if(d && st>this.waitUntil){ if(Math.abs(P.x-d.x)>8){ if(P.x<d.x) I.right=true; else I.left=true; } else if(!d.hit){ I.spaceEdge = true; this.waitUntil = st + 3.4; } } }
    walkUpdate(dt, 170, 120, 1160, false);
    G.nDiscs = discsScreen.length; const asp=W/H;
    discsScreen.forEach((d,i)=>{ d.y += Math.sin(G.t*0.8 + d.phase)*0.05; G.discs[i*4]=(d.x/W*2-1)*asp; G.discs[i*4+1]=-(d.y/H*2-1); G.discs[i*4+2]=d.r/H*2; G.discs[i*4+3]=d.phase + (d.hit? (G.t-d.hitT)*0.8:0); });
    if(I.spaceEdge){ for(const d of discsScreen){ if(!d.hit && Math.abs(d.x-P.x)<d.r*0.75){ d.hit=true; d.hitT=G.t; this.got++; this.target++;
      if(G.audio) G.audio.scaleNote(185*2, [0,2,4,5,7,9][this.noteI++%6], 0, {level:0.26, decay:5.5});
      if(this.ti<this.thoughts.length) Stream.emit(this.thoughts[this.ti++], 'drift', {x: clamp(d.x-140, 80, W-420), y: d.y+d.r+60, size:25});
      break; } } }
    if(this.got>=discsScreen.length && this.doneT===null){ this.doneT=st; }
    if(this.doneT!==null && st>this.doneT+4.5) go(5,'cut'); },
  draw(ctx){ ctx.save();
    for(const d of discsScreen){ ctx.strokeStyle='rgba(200,200,210,0.35)'; ctx.lineWidth=1; ctx.beginPath(); ctx.moveTo(d.x, 0); ctx.lineTo(d.x, d.y-d.r); ctx.stroke();
      if(d.hit){ const a=G.t-d.hitT; ctx.strokeStyle=`rgba(255,255,255,${0.6*Math.max(0,1-a/2.5)})`; ctx.lineWidth=1.5; ctx.beginPath(); ctx.arc(d.x,d.y,d.r+8+a*30,0,Math.PI*2); ctx.stroke(); } }
    // collected marks
    ctx.fillStyle='rgba(255,255,255,0.7)'; for(let i=0;i<discsScreen.length;i++){ ctx.beginPath(); ctx.arc(W/2-45+i*18, 690, 3, 0, Math.PI*2); if(i<this.got) ctx.fill(); else ctx.stroke(); }
    ctx.restore();
    drawAvatar(ctx, P.x, P.y, {scale:P.scale, walk:P.walk, walking:P.walking, headphones:'on', listen:0});
    if(!AUTO){ ctx.save(); ctx.globalAlpha=0.55; ctx.font=`400 14px ${F.serif}`; ctx.fillStyle='#fff'; ctx.textAlign='center'; ctx.letterSpacing='0.2em'; ctx.fillText('走到光碟下方，按空格 取下它', W/2, 60); ctx.restore(); } },
});

// 5 · the sea (DV)
SCENES.push({ name:'sea', shader:5, post:{grain:0.11, aberr:0.9, vig:0.55, crt:0, bloom:0.25, letter:0, pillar:0.125, dv:1.0, warm:0.0, desat:0.05},
  enter(){ P.x=300; P.y=676; P.scale=0.68; P.headphones='on'; P.dir=1; this.thoughts=shuffle(T.sea); this.ti=0; this.nextT=2.8; this.tc0=14*60+22; chapter(5); audioScene(5); G.cam.x=0; },
  update(dt){ const st=G.st;
    if(AUTO){ I.right = (st<7.5) || (st>12.5 && st<19); I.left=false; }
    walkUpdate(dt, 95, 220, 1060, false); G.cam.x = P.x*0.6;
    G.shake.x = 0.014*(n1(st*1.9)*2-1); G.shake.y = 0.011*(n1(st*2.6+5)*2-1);
    if(st>this.nextT && this.ti<this.thoughts.length){ Stream.emit(this.thoughts[this.ti++], ['sub','drift','vertical'][this.ti%3], {x: 430+rnd()*200, y:380+rnd()*80, dark:false}); this.nextT = st + 4.4 + rnd(); }
    if(G.audio && Math.floor(st/7)!==Math.floor((st-dt)/7)) G.audio.scaleNote(110*4, Math.floor(rnd()*5), 0, {level:0.09, decay:6});
    if(AUTO && st>20.5) go(6,'cut'); if(!AUTO && P.x>=1060 && st>12) go(6,'cut'); },
  draw(ctx){ const st=G.st; const L=160, R=W-160;
    drawAvatar(ctx, P.x, P.y, {scale:P.scale, walk:P.walk, walking:P.walking, headphones:'on', listen:0});
    ctx.save(); ctx.font=`400 20px ${F.mono}`; ctx.fillStyle='#fff'; ctx.textBaseline='top'; ctx.shadowColor='rgba(0,0,0,0.6)'; ctx.shadowBlur=4;
    if(Math.floor(st*1.6)%2===0){ ctx.fillStyle='#ff3b3b'; ctx.beginPath(); ctx.arc(L+52, 60, 7, 0, Math.PI*2); ctx.fill(); }
    ctx.fillStyle='#fff'; ctx.fillText('REC', L+68, 49);
    const tcs = this.tc0 + st; const mm=Math.floor(tcs/60), ssec=Math.floor(tcs%60), fr=Math.floor((tcs%1)*30);
    ctx.textAlign='right'; ctx.fillText(`00:${String(mm).padStart(2,'0')}:${String(ssec).padStart(2,'0')}:${String(fr).padStart(2,'0')}`, R-48, 49);
    ctx.font=`400 16px ${F.mono}`; ctx.fillText('SP', R-48, 78);
    ctx.textAlign='left'; ctx.fillText('夏  ·  DV', L+48, 640);
    ctx.textAlign='right'; ctx.fillText('12%', R-48, 640); ctx.strokeStyle='#fff'; ctx.lineWidth=1.5; ctx.strokeRect(R-118, 642, 34, 14); ctx.fillRect(R-116, 644, 4, 10);
    // viewfinder brackets
    ctx.strokeStyle='rgba(255,255,255,0.7)'; ctx.lineWidth=2; const m=36, l=26;
    for(const [x,y,sx,sy] of [[L+m,m,1,1],[R-m,m,-1,1],[L+m,H-m,1,-1],[R-m,H-m,-1,-1]]){ ctx.beginPath(); ctx.moveTo(x, y+sy*l); ctx.lineTo(x,y); ctx.lineTo(x+sx*l, y); ctx.stroke(); }
    ctx.restore(); },
});

// 6 · the concert
const sticks=[]; for(let i=0;i<820;i++){ const d=rnd(); sticks.push({x: rnd()*W, y: 470 + d*250, d, ph: rnd()*6.28, sp: 0.9+rnd()*0.7, len: 18+d*28}); }
sticks.sort((a,b)=>a.y-b.y);
SCENES.push({ name:'concert', shader:6, post:{grain:0.08, aberr:0.7, vig:0.95, crt:0, bloom:1.5, letter:0.06, pillar:0, dv:0, warm:0.1, desat:0},
  enter(){ P.x=640; P.y=716; P.scale=0.95; P.headphones='on'; P.stick=false; this.thoughts=shuffle(T.concert); this.ti=0; this.nextT=2.2; this.sync=0; this.light=1; this.out=false; this.outT=0; chapter(6); audioScene(6); G.cam.x=0; },
  update(dt){ const st=G.st;
    if(AUTO){ I.space = st>3.0 && st<13.5; }
    const raise = I.space; P.stick = raise; this.sync = lerp(this.sync, raise?1:0, 1-Math.exp(-dt*0.5));
    if(st>14.0 && !this.out){ this.out=true; this.outT=st; Stream.clear(); Stream.emit(T.concertOut, 'center', {size:40, life:5, dark:true}); if(G.audio) G.audio.silence(0, 3); }
    if(this.out){ this.light = Math.max(0, this.light - dt*0.7); }
    G.params[0]=this.light;
    if(st>this.nextT && this.ti<this.thoughts.length && !this.out){ Stream.emit(this.thoughts[this.ti++], ['sub','center','vertical'][this.ti%3], {size: this.ti%3===1? 30:24, y: this.ti%3===1? 250: undefined}); this.nextT = st + 4.3; }
    if(st>this.outT+5.0 && this.out) go(7,'cut'); },
  draw(ctx){ const st=G.st; const L=this.light;
    ctx.save(); ctx.lineCap='round';
    for(const s of sticks){ const ang = Math.sin(st*s.sp*(1-this.sync*0.4) + s.ph*(1-this.sync*0.85))*(0.38-0.2*this.sync);
      const a = (0.35+0.6*s.d)*L; ctx.strokeStyle=`rgba(180,255,195,${a})`; ctx.lineWidth=1.5+s.d*2.8; ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(s.x+Math.sin(ang)*s.len, s.y-Math.cos(ang)*s.len); ctx.stroke(); }
    ctx.restore();
    drawAvatar(ctx, P.x, P.y, {scale:P.scale, headphones:'on', stick:P.stick && L>0.05, listen:0, alpha:0.97}); },
});

// 7 · dusk, return
SCENES.push({ name:'dusk', shader:7, post:{grain:0.08, aberr:0.5, vig:0.85, crt:0, bloom:0.5, letter:0.06, pillar:0, dv:0, warm:0.3, desat:0},
  enter(){ P.wx=600; P.x=460; P.y=604; P.scale=0.86; P.headphones='on'; P.dir=1; P.stick=false; P.armsUp=false; P.tilt=0; this.thoughts=T.dusk.slice(); this.ti=0; this.nextT=3.0; this.off=false; this.offQ=T.duskOff.slice(); this.oi=0; this.onext=0; chapter(7); audioScene(7); },
  update(dt){ const st=G.st;
    if(AUTO){ I.right = st>1 && st<13; I.space = false; if(st>15.2 && st<15.4) I.spaceEdge=true; }
    walkUpdate(dt, 110, 0, 4200, true); G.cam.x=P.wx; P.x=460;
    if(I.spaceEdge && !this.off && st>3){ this.off=true; P.headphones='neck'; if(G.audio) G.audio.headphones(false); this.onext=st+1.5; Stream.clear(); }
    if(!this.off && st>this.nextT && this.ti<2){ Stream.emit(this.thoughts[this.ti++], ['sub','vertical'][this.ti%2]); this.nextT=st+5; }
    if(this.off){ if(st>this.onext && this.oi<this.offQ.length){ Stream.emit(this.offQ[this.oi++], 'center', {size:38, life:4.5}); this.onext=st+3.0; }
      else if(this.oi>=this.offQ.length && st>this.onext && this.ti<this.thoughts.length){ Stream.emit(this.thoughts[this.ti++], ['sub','center','sub','vertical','sub'][this.ti%5], {size: 26}); this.onext=st+4.2; } }
    G.listen = 0;
    if(this.off && this.ti>=this.thoughts.length && st>this.onext+1.2) go(8,'cut'); if(AUTO && st>46) go(8,'cut'); },
  draw(ctx){ drawAvatar(ctx, P.x, P.y, {scale:P.scale, walk:P.walk, walking:P.walking, headphones:P.headphones, listen:0});
    if(!AUTO && !this.off){ ctx.save(); ctx.globalAlpha=0.5; ctx.font=`400 14px ${F.serif}`; ctx.fillStyle='#fff'; ctx.textAlign='center'; ctx.letterSpacing='0.2em'; ctx.fillText('空格：摘下耳机', W/2, 60); ctx.restore(); } },
});

// 8 · ending
SCENES.push({ name:'ending', shader:0, post:{grain:0.06, aberr:0.3, vig:0.7, crt:0, bloom:0.4, letter:0, pillar:0, dv:0, warm:0.2, desat:0},
  enter(){ this.lines=T.ending; audioScene(8); Stream.clear(); this.done=false; },
  update(dt){ const st=G.st; if(st>25 && !this.done){ this.done=true; if(RENDER){ if(G.audio) G.audio.end(); G.finished=true; } else go(0,'cut'); } },
  draw(ctx){ const st=G.st; ctx.save();
    const pa = ss(0.8,3.2,st); ctx.globalAlpha=pa; ctx.translate(W/2, 250); ctx.rotate(-0.045);
    ctx.shadowColor='rgba(0,0,0,0.6)'; ctx.shadowBlur=30; ctx.fillStyle='#f3f1ea'; ctx.fillRect(-100,-140,200,290); ctx.shadowBlur=0;
    const im=IMG.portrait; if(im) ctx.drawImage(im, -88, -128, 176, 250);
    ctx.fillStyle='rgba(40,40,40,0.75)'; ctx.font=`400 13px ${F.serif}`; ctx.textAlign='center'; ctx.letterSpacing='0.3em'; ctx.fillText('我', 0, 140);
    ctx.restore();
    ctx.save(); ctx.textAlign='center'; ctx.textBaseline='middle';
    this.lines.forEach((ln,i)=>{ const t0=4.0+i*2.8; const a=ss(t0,t0+1.4,st)*(i<2? 1 : ss(t0+9, t0+7.5, st)); if(a<=0) return; ctx.globalAlpha=a;
      const big = i===1; ctx.font = big? `400 32px ${F.latin}` : `400 ${i===0?30:19}px ${F.serif}`; ctx.letterSpacing = big? '0.7em' : (i===0?'0.3em':'0.18em'); ctx.fillStyle = i<2? '#f2f2f2':'rgba(220,220,220,0.8)';
      const y = i<2 ? (460 + i*44) : (560 + (i-2)*30); ctx.fillText(ln, W/2 + (big? 10:0), y); });
    if(st>4 && Math.floor(st*2)%2===0){ ctx.globalAlpha=0.7; ctx.fillStyle='#cfe'; ctx.fillRect(W/2-4, 690, 8, 14); }
    ctx.restore(); },
});

// ---------- transitions ----------
function go(n, style){ if(G.trans) return; G.trans={to:n, style, t:0, switched:false};
  if(style==='mix'){ sctx.clearRect(0,0,W,H); sctx.drawImage(ov,0,0); G.from=G.scene; G.mix=0; switchTo(n); }
}
function switchTo(n){ Stream.clear(); G.scene=n; G.st=0; I.typed=''; G.listen=0; G.shake.x=G.shake.y=0; const sc=SCENES[n]; Object.assign(G.postT, sc.post); sc.enter(); }
function updateTrans(dt){ const tr=G.trans; if(!tr) return; tr.t+=dt;
  if(tr.style==='mix'){ G.mix = ss(0,2.6,tr.t); if(tr.t>=2.6){ G.mix=0; G.from=-1; G.trans=null; } }
  else if(tr.style==='cut'){ if(!tr.switched){ G.post.fade = ss(0,0.8,tr.t); if(tr.t>=0.9){ tr.switched=true; switchTo(tr.to); tr.t=0; } } else { G.post.fade = 1-ss(0,1.4,tr.t); if(tr.t>=1.4){ G.post.fade=0; G.trans=null; } } }
  else if(tr.style==='white'){ if(!tr.switched){ G.post.flash = ss(0,0.7,tr.t); if(tr.t>=0.75){ tr.switched=true; switchTo(tr.to); tr.t=0; } } else { G.post.flash = 1-ss(0,1.8,tr.t); if(tr.t>=1.8){ G.post.flash=0; G.trans=null; } } }
}

// ---------- update / render ----------
function update(dt){
  G.t += dt; G.st += dt;
  if(G.audio && G.audio.setTime) G.audio.setTime(G.t);
  const sc = SCENES[G.scene];
  if(!(G.trans && G.trans.style!=='mix' && !G.trans.switched)) sc.update(dt);
  updateTrans(dt);
  // post tween
  for(const k in G.postT){ if(k==='fade'||k==='flash') continue; G.post[k] = lerp(G.post[k], G.postT[k], 1-Math.exp(-dt*1.6)); }
  I.spaceEdge=false; I.enterEdge=false; I.anyEdge=false;
}
function drawOverlay(){
  ctx.clearRect(0,0,W,H);
  const sc=SCENES[G.scene];
  if(G.from>=0 && G.mix<1){ ctx.save(); ctx.globalAlpha=1-G.mix; ctx.drawImage(snap,0,0); ctx.restore(); ctx.save(); ctx.globalAlpha=G.mix; sc.draw(ctx); ctx.restore(); }
  else sc.draw(ctx);
  Stream.draw(ctx); drawCard(ctx);
}
function render(){
  drawOverlay();
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, texOv); gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,ov);
  const sc=SCENES[G.scene], fromSc = G.from>=0? SCENES[G.from]: null;
  // A · procedural scene (possibly low-res)
  gl.bindFramebuffer(gl.FRAMEBUFFER, rtScene.fb); gl.viewport(0,0,SW,SHh); gl.useProgram(PS.p); gl.bindVertexArray(vao);
  gl.uniform2f(PS.u('uRes'),SW,SHh); gl.uniform1f(PS.u('uTime'),G.t);
  gl.uniform1i(PS.u('uSceneA'), fromSc? fromSc.shader : sc.shader); gl.uniform1i(PS.u('uSceneB'), sc.shader); gl.uniform1f(PS.u('uMix'), fromSc? G.mix : 0);
  gl.uniform2f(PS.u('uCam'), G.cam.x, G.cam.y); gl.uniform2f(PS.u('uShake'), G.shake.x, G.shake.y);
  gl.uniform1f(PS.u('uDusk'), 0); gl.uniform1f(PS.u('uListen'), G.listen);
  gl.uniform4fv(PS.u('uDiscs'), G.discs); gl.uniform1i(PS.u('uNDiscs'), sc.name==='cd'? G.nDiscs:0); gl.uniform4f(PS.u('uParams'), G.params[0],G.params[1],G.params[2],G.params[3]);
  gl.drawArrays(gl.TRIANGLES,0,3);
  // B · composite scene + crisp overlay at full res
  gl.bindFramebuffer(gl.FRAMEBUFFER, rtComp.fb); gl.viewport(0,0,W,H); gl.useProgram(PC.p);
  gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, rtScene.tex); gl.uniform1i(PC.u('uScene'),1); gl.uniform1i(PC.u('uOverlay'),0);
  gl.drawArrays(gl.TRIANGLES,0,3);
  // C · bloom at quarter res
  gl.bindFramebuffer(gl.FRAMEBUFFER, rtBloom.fb); gl.viewport(0,0,BW,BH); gl.useProgram(PB.p);
  gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, rtComp.tex); gl.uniform1i(PB.u('uTex'),2); gl.uniform2f(PB.u('uRes'),BW,BH);
  gl.drawArrays(gl.TRIANGLES,0,3);
  // D · film post
  gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0,0,W,H); gl.useProgram(PP.p);
  gl.uniform1i(PP.u('uTex'),2); gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, rtBloom.tex); gl.uniform1i(PP.u('uBloomTex'),3);
  gl.uniform2f(PP.u('uRes'),W,H); gl.uniform1f(PP.u('uTime'),G.t);
  const p=G.post; for(const k of ['grain','aberr','vig','letter','crt','pillar','dv','flash','fade','bloom','desat','warm']){ gl.uniform1f(PP.u('u'+k[0].toUpperCase()+k.slice(1)), p[k]); }
  gl.drawArrays(gl.TRIANGLES,0,3);
}

// ---------- input ----------
const KEYS = {ArrowLeft:'left', a:'left', A:'left', ArrowRight:'right', d:'right', D:'right', ArrowUp:'up', w:'up', W:'up', ' ':'space'};
window.addEventListener('keydown', e => { if(AUTO) return; const k=KEYS[e.key]; I.anyEdge=true;
  const typing = SCENES[G.scene].name==='bbs';
  if(k && !(typing && k==='space')){ if(k==='space' && !I.space) I.spaceEdge=true; I[k]=true; e.preventDefault(); }
  if(e.key==='Enter'){ I.enterEdge=true; I.anyEdge=true; }
  if(typing && (e.key==='y'||e.key==='Y')) I.yn='y'; if(typing && (e.key==='n'||e.key==='N')) I.yn='n';
  if(!typing && e.key==='Enter' && G.scene===0) I.anyEdge=true; });
window.addEventListener('keyup', e => { const k=KEYS[e.key]; if(k) I[k]=false; });
const ime=document.getElementById('ime'); if(ime){ ime.addEventListener('input', ()=>{ I.typed = ime.value.slice(0,60); }); }
glc.addEventListener('pointerdown', e => { if(AUTO) return; const r=glc.getBoundingClientRect(); const x=(e.clientX-r.left)/r.width; I.anyEdge=true; if(x<0.33) I.left=true; else if(x>0.67) I.right=true; else { I.space=true; I.spaceEdge=true; } });
window.addEventListener('pointerup', ()=>{ I.left=false; I.right=false; I.space=false; });

// ---------- boot ----------
async function loadFonts(){ if(!document.fonts) return; const all = JSON.stringify(T);
  const jobs=[]; for(const f of ['400 20px "Noto Serif SC"','600 20px "Noto Serif SC"','400 20px "Cormorant Garamond"','italic 400 20px "Cormorant Garamond"','400 20px "Noto Sans SC"']) jobs.push(document.fonts.load(f, all).catch(()=>{}));
  await Promise.race([Promise.all(jobs), new Promise(r=>setTimeout(r, RENDER? 25000: 2500))]); await document.fonts.ready; }

const ready = (async () => {
  await Promise.all([loadImg('face','assets/face.png'), loadImg('portrait','assets/portrait.png')]);
  await loadFonts();
  if(RENDER){ G.audio = new AU.Recorder(); G.audio.setTime(0); G.audio.start(); }
  switchTo(START_SCENE); G.post.fade=1; G.trans={to:START_SCENE, style:'cut', t:0, switched:true};
  return true;
})();

function startLive(){ const gate=document.getElementById('gate'); gate.style.opacity=0; setTimeout(()=>gate.classList.add('hidden'), 1200);
  try { const actx = new (window.AudioContext||window.webkitAudioContext)(); G.audio = new AU.Live(actx); G.audio.start(); G.audio.setScene(SCENES[G.scene].shader===0 && G.scene===0? 0 : G.scene); G.actx=actx; } catch(e){ console.warn('audio unavailable', e); }
  let last=performance.now();
  function loop(now){ const dt=Math.min(0.05,(now-last)/1000); last=now; update(dt); render(); requestAnimationFrame(loop); }
  requestAnimationFrame(loop);
}
if(!RENDER){ ready.then(()=>{ const gate=document.getElementById('gate'); gate.addEventListener('click', startLive, {once:true}); window.addEventListener('keydown', function h(){ startLive(); window.removeEventListener('keydown', h); }, {once:true}); }); }
else { document.getElementById('gate').classList.add('hidden'); document.getElementById('ui').classList.add('hidden'); }

// recording / mute / fullscreen
(function ui(){ const bRec=document.getElementById('btnRec'), bMute=document.getElementById('btnMute'), bFull=document.getElementById('btnFull'); if(!bRec) return; let rec=null, chunks=[];
  if(window.ETHER_NO_DOWNLOAD || typeof MediaRecorder==='undefined') bRec.classList.add('hidden');
  bRec.addEventListener('click', ()=>{ if(rec){ rec.stop(); return; }
    const stream = glc.captureStream(30); if(G.actx && G.audio){ const dest=G.actx.createMediaStreamDestination(); G.audio.extraOut(dest); const at=dest.stream.getAudioTracks()[0]; if(at) stream.addTrack(at); }
    const mime = ['video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm'].find(m=>MediaRecorder.isTypeSupported(m));
    rec = new MediaRecorder(stream, {mimeType:mime, videoBitsPerSecond: 9e6}); chunks=[]; rec.ondataavailable=e=>{ if(e.data.size) chunks.push(e.data); };
    rec.onstop=()=>{ const blob=new Blob(chunks,{type:'video/webm'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`以太-意识流-${Date.now()}.webm`; a.click(); rec=null; bRec.classList.remove('on'); bRec.textContent='● 录制'; };
    rec.start(500); bRec.classList.add('on'); bRec.textContent='■ 停止'; });
  bMute.addEventListener('click', ()=>{ if(!G.actx) return; if(G.actx.state==='running'){ G.actx.suspend(); bMute.textContent='取消静音'; } else { G.actx.resume(); bMute.textContent='静音'; } });
  bFull.addEventListener('click', ()=>{ const st=document.getElementById('stage'); try{ if(document.fullscreenElement) document.exitFullscreen(); else if(st.requestFullscreen) st.requestFullscreen().catch(()=>{}); }catch(e){} });
})();

// ---------- render-mode hooks ----------
window.ETHER = {
  ready, W, H,
  step(dt){ update(dt); render(); },
  stepLogic(dt){ update(dt); },
  frame(q){ return glc.toDataURL('image/jpeg', q||0.93); },
  done(){ return G.finished; },
  time(){ return G.t; }, scene(){ return SCENES[G.scene].name; },
  events(){ return G.audio && G.audio.events ? G.audio.events : []; },
  jump(n){ G.trans=null; switchTo(n); G.post.fade=0; G.post.flash=0; },
  renderAudio(duration){ return AU.renderOffline(G.audio.events, duration); },
  bench(n){ n=n||3; const px=new Uint8Array(4); const t=performance.now(); for(let i=0;i<n;i++){ update(1/30); render(); gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,px); } return {msPerFrame:(performance.now()-t)/n, qual:QUAL, renderer:RENDERER}; },
  G,
};
})();
