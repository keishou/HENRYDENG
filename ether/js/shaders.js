// ETHER · 以太 — GLSL scenes (WebGL2). Everything procedural; no external textures except the 2D overlay.
window.ETHER_SHADERS = (() => {
const VERT = `#version 300 es
in vec2 aPos; out vec2 vUv;
void main(){ vUv = aPos*0.5+0.5; gl_Position = vec4(aPos,0.0,1.0); }`;

const COMMON = `
float hash(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float noise(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
  float a=hash(i), b=hash(i+vec2(1,0)), c=hash(i+vec2(0,1)), d=hash(i+vec2(1,1));
  return mix(mix(a,b,f.x),mix(c,d,f.x),f.y); }
float fbm(vec2 p){ float v=0.0, a=0.5; mat2 m=mat2(1.6,1.2,-1.2,1.6);
  for(int i=0;i<5;i++){ v+=a*noise(p); p=m*p; a*=0.5; } return v; }
float fbm3(vec2 p){ float v=0.0, a=0.5; mat2 m=mat2(1.6,1.2,-1.2,1.6);
  for(int i=0;i<3;i++){ v+=a*noise(p); p=m*p; a*=0.5; } return v; }
`;

const SCENE = `#version 300 es
precision highp float;
in vec2 vUv; out vec4 fragColor;
uniform vec2 uRes; uniform float uTime;
uniform int uSceneA; uniform int uSceneB; uniform float uMix;
uniform vec2 uCam; uniform vec2 uShake;
uniform float uDusk; uniform float uListen;
uniform vec4 uDiscs[8]; uniform int uNDiscs;
uniform vec4 uParams;
${COMMON}

// ---------- I / VII : the rice field (day -> dusk via uDusk) ----------
vec3 sceneField(vec2 p, float t, float dusk, float cam){
  float hz = 0.12;
  vec3 skyTop = mix(vec3(0.10,0.30,0.68), vec3(0.08,0.05,0.20), dusk);
  vec3 skyBot = mix(vec3(0.72,0.86,0.95), vec3(0.93,0.52,0.30), dusk);
  vec3 fogc   = mix(vec3(0.72,0.86,0.95), vec3(0.75,0.42,0.33), dusk);
  vec3 col;
  if (p.y > hz) {
    float g = clamp((p.y-hz)/(1.0-hz),0.0,1.0);
    col = mix(skyBot, skyTop, pow(g,0.65));
    vec2 sunp = mix(vec2(0.95,0.72), vec2(-0.55,0.55), dusk);
    float sd = length(p-sunp);
    col += (1.0-dusk)*vec3(1.0,0.96,0.82)*0.30*exp(-sd*3.0);
    col += dusk*vec3(0.95,0.95,1.0)*(1.1*smoothstep(0.072,0.064,sd) + 0.18*exp(-sd*4.5));
    float st = step(0.9965, hash(floor(p*260.0)+7.0)) * dusk * smoothstep(0.15,0.7,g);
    col += st*vec3(0.8,0.85,1.0)*(0.5+0.5*sin(t*2.0+hash(floor(p*260.0))*40.0));
    float cz = 1.0/(p.y-hz+0.05);
    vec2 cp = vec2(p.x*cz*0.35 + t*0.012 + cam*0.004, cz*0.35 + 3.1);
    float cl = fbm(cp*1.15);
    float cm = smoothstep(0.46,0.76,cl) * smoothstep(0.0,0.22,p.y-hz);
    vec3 cloudCol = mix(vec3(1.0,1.0,1.0), vec3(0.72,0.40,0.52), dusk);
    vec3 cloudSh  = mix(vec3(0.70,0.78,0.90), vec3(0.22,0.13,0.32), dusk);
    col = mix(col, mix(cloudSh, cloudCol, smoothstep(0.5,0.95,cl)), cm*0.92);
    // distant ridge
    float ridge = 0.045 + 0.075*fbm3(vec2(p.x*1.1 + cam*0.0008 + 5.0, 1.7));
    vec3 mtn = mix(vec3(0.46,0.58,0.76), vec3(0.20,0.14,0.30), dusk);
    col = mix(col, mix(mtn, skyBot, 0.45), smoothstep(hz+ridge+0.004, hz+ridge-0.004, p.y));
    float trees = 0.010 + 0.022*noise(vec2(p.x*26.0 + cam*0.002, 3.0)) + 0.008*noise(vec2(p.x*90.0 + cam*0.002, 8.0));
    vec3 treeCol = mix(vec3(0.16,0.30,0.20), vec3(0.08,0.06,0.14), dusk);
    col = mix(col, mix(treeCol, skyBot, 0.25), smoothstep(hz+trees+0.003, hz+trees-0.003, p.y));
  } else {
    float z = 1.0/(hz - p.y + 0.012);
    float wx = p.x*z + cam*0.01;
    float rows = 0.5+0.5*sin(wx*2.6);
    float detail = fbm(vec2(wx*2.6, z*1.8 + 11.0));
    float wind = fbm3(vec2(wx*0.11 - t*0.32, z*0.05 + t*0.07));
    vec3 g1 = mix(vec3(0.15,0.40,0.13), vec3(0.05,0.13,0.12), dusk);
    vec3 g2 = mix(vec3(0.55,0.74,0.24), vec3(0.15,0.30,0.22), dusk);
    col = mix(g1, g2, clamp(detail*0.75 + rows*0.3 - 0.1,0.0,1.0));
    col += (1.0-dusk)*vec3(0.22,0.26,0.04)*smoothstep(0.52,0.80,wind);
    col += dusk*vec3(0.05,0.08,0.10)*smoothstep(0.55,0.8,wind);
    // shimmering water between rows (young paddy)
    float water = smoothstep(0.85,1.0,rows)*smoothstep(0.35,0.6,noise(vec2(wx*3.0,z*1.5)));
    col = mix(col, fogc*0.9, water*0.35);
    // near-field tufts / soil lines
    float tuft = noise(vec2(wx*16.0, z*10.0 + 21.0));
    col = mix(col, g1*0.8, smoothstep(0.66,0.92,tuft)*smoothstep(3.0,1.2,z)*0.22);
    float fog = 1.0-exp(-z*0.040);
    col = mix(col, fogc, fog*0.86);
    col *= 1.0 - 0.28*smoothstep(-0.55,-1.0,p.y);
  }
  // listening: the blue deepens
  col = mix(col, col*vec3(0.85,0.95,1.15), uListen*0.6);
  return col;
}

// ---------- II : looking up, the kite sky ----------
vec3 sceneSky(vec2 p, float t){
  vec2 sunp = vec2(0.62, 0.48);
  float sd = length(p-sunp);
  vec3 col = mix(vec3(0.66,0.82,0.95), vec3(0.10,0.34,0.78), clamp(length(p*vec2(0.8,1.0))*0.75,0.0,1.0));
  col += vec3(1.0,0.97,0.85)*0.30*exp(-sd*3.4) + vec3(1.0,0.98,0.9)*smoothstep(0.075,0.05,sd)*0.8;
  vec2 cp = p*1.3 + vec2(t*0.028, t*0.011) + uCam*0.0006;
  float cl = fbm(cp + 2.0);
  float cm = smoothstep(0.43,0.72,cl);
  col = mix(col, mix(vec3(0.74,0.82,0.93), vec3(1.0), smoothstep(0.5,0.9,cl)), cm*0.88);
  // wispy high cirrus
  float ci = fbm3(vec2(p.x*3.0 + t*0.05, p.y*0.6 + 9.0));
  col += vec3(0.08)*smoothstep(0.55,0.8,ci);
  // lens ghosts
  col += vec3(0.9,0.75,0.45)*0.07*smoothstep(0.14,0.0,length(p+sunp*0.55));
  col += vec3(0.5,0.8,1.0)*0.05*smoothstep(0.06,0.0,length(p+sunp*0.9));
  return col;
}

// ---------- III : the BBS, phosphor black ----------
vec3 sceneBBS(vec2 p, float t){
  vec3 col = vec3(0.008,0.016,0.012);
  col += vec3(0.0,0.045,0.02)*noise(p*60.0 + t*3.0)*0.4;
  float band = smoothstep(0.92,1.0, sin(p.y*2.2 - t*0.35));
  col += vec3(0.015,0.05,0.03)*band;
  col += vec3(0.02,0.05,0.035)*exp(-length(p*vec2(0.7,1.0))*1.4);
  return col;
}

// ---------- IV : the record shop, discs of sliced light ----------
vec3 sceneCD(vec2 p, float t){
  vec3 col = vec3(0.045,0.040,0.048);
  col += vec3(0.30,0.26,0.22)*exp(-length((p-vec2(0.05,0.95))*vec2(0.85,0.55))*1.7);
  col += vec3(0.10,0.12,0.18)*exp(-length((p-vec2(-1.2,-0.2))*vec2(0.6,1.0))*1.5);
  // shelves (soft horizontal lines) 
  float shelf = smoothstep(0.02,0.0,abs(fract(p.y*2.5+0.3)-0.5)) * smoothstep(0.2,0.0,p.y+0.95);
  col += vec3(0.05)*shelf;
  // dust
  vec2 dp = p*140.0 + vec2(t*0.9, -t*2.2);
  float dust = step(0.9975, hash(floor(dp))) * (0.5+0.5*sin(t*3.0+hash(floor(dp))*20.0));
  col += dust*vec3(0.35,0.33,0.3);
  for(int i=0;i<8;i++){
    if(i>=uNDiscs) break;
    vec4 D = uDiscs[i]; vec2 d = p - D.xy; float r = D.z; float l = length(d);
    float ring = smoothstep(r, r-0.004, l) * smoothstep(r*0.30, r*0.33, l);
    float a = atan(d.y, d.x);
    float groove = 0.5+0.5*sin(l*900.0);
    float v = pow(0.5+0.5*sin(a*2.0 + D.w*3.0 + t*0.25), 6.0);
    float v2 = pow(0.5+0.5*sin(a*2.0 + D.w*3.0 + t*0.25 + 3.1416), 6.0);
    float beam = max(v, v2*0.7);
    float hue = 0.06*cos(a) + l/r*2.2 + D.w + t*0.03;
    vec3 rain = 0.5+0.5*cos(6.2831*(hue + vec3(0.0,0.33,0.67)));
    vec3 silver = vec3(0.62,0.63,0.66)*(0.55 + 0.35*smoothstep(0.0,1.0,l/r)) + 0.06*groove;
    silver *= 0.8 + 0.25*pow(0.5+0.5*sin(a*1.0 + D.w + t*0.1), 2.0);
    vec3 disc = mix(silver, rain*1.05, beam*0.85);
    disc += vec3(0.5)*smoothstep(0.012,0.0,abs(l-r));
    disc += vec3(0.25)*smoothstep(0.01,0.0,abs(l-r*0.315));
    col = mix(col, disc, ring);
    col += rain*0.10*exp(-max(l-r,0.0)*30.0)*beam;
  }
  return col;
}

// ---------- V : the sea, digital video ----------
vec3 sceneSea(vec2 p, float t){
  p += uShake;
  float hz = -0.02;
  vec3 skyTop = vec3(0.48,0.66,0.85), skyBot = vec3(0.86,0.91,0.94);
  vec2 sunp = vec2(0.28, 0.30);
  if (p.y > hz) {
    float g = clamp((p.y-hz)/(1.0-hz),0.0,1.0);
    vec3 col = mix(skyBot, skyTop, pow(g,0.6));
    float sd = length(p-sunp);
    col += vec3(1.0,0.96,0.86)*(0.55*exp(-sd*4.0) + smoothstep(0.06,0.046,sd));
    float cz = 1.0/(p.y-hz+0.07);
    float cl = fbm(vec2(p.x*cz*0.28 + t*0.01, cz*0.3 + 4.0));
    col = mix(col, vec3(1.0), smoothstep(0.56,0.82,cl)*smoothstep(0.0,0.3,p.y-hz)*0.75);
    return col;
  }
  float z = 1.0/(hz - p.y + 0.014);
  float wx = p.x*z + uCam.x*0.01;
  // shore
  float shoreY = -0.74 + 0.025*sin(p.x*3.0 + t*0.7) + 0.02*noise(vec2(p.x*6.0, t*0.3));
  if (p.y < shoreY) {
    vec3 sand = mix(vec3(0.78,0.72,0.60), vec3(0.62,0.56,0.46), noise(vec2(p.x*40.0, p.y*40.0)));
    float wet = smoothstep(shoreY-0.08, shoreY, p.y);
    sand = mix(sand, vec3(0.45,0.50,0.50), wet*0.5);
    return sand;
  }
  float w = 0.0;
  w += sin(z*3.0 + t*1.1 + wx*0.2)*0.5;
  w += sin(z*7.0 - t*0.8 + wx*0.7)*0.25;
  w += noise(vec2(wx*2.0, z*3.0 - t*0.5))*0.7;
  vec3 deep = vec3(0.04,0.28,0.42), shallow = vec3(0.32,0.64,0.72);
  vec3 col = mix(shallow, deep, clamp(w*0.5+0.5,0.0,1.0));
  float gl = smoothstep(0.90,1.0, noise(vec2(wx*22.0, z*28.0 - t*3.5))) * exp(-abs(p.x-sunp.x)*2.6) * smoothstep(0.5,6.0,z);
  col += gl*vec3(1.0,0.98,0.9)*1.6;
  float foam = smoothstep(0.62,0.78, fbm3(vec2(wx*1.5, z*4.0 - t*0.6)+w)) * smoothstep(2.2,1.0,z);
  col = mix(col, vec3(0.92,0.95,0.95), foam*0.8);
  float edge = smoothstep(shoreY+0.06, shoreY, p.y);
  col = mix(col, vec3(0.9,0.93,0.92), edge*0.7);
  col = mix(col, skyBot, 1.0-exp(-z*0.03));
  return col;
}

// ---------- VI : the concert, light through fog ----------
vec3 sceneConcert(vec2 p, float t){
  vec3 col = vec3(0.004,0.005,0.009);
  float I = uParams.x;
  vec2 lp = vec2(0.0, 1.08); vec2 d = p - lp; float ang = atan(d.x, -d.y);
  float fog = fbm3(p*2.2 + vec2(t*0.06, -t*0.12) + 3.0);
  float cone = smoothstep(0.62, 0.0, abs(ang)) * exp(-length(d)*1.15);
  col += vec3(0.62,0.86,0.74)*cone*(0.22+0.55*fog)*I;
  float sw = sin(t*0.27)*0.7;
  vec2 d2 = p - vec2(sw, 1.05); float ang2 = atan(d2.x, -d2.y);
  col += vec3(0.5,0.62,1.0)*smoothstep(0.07,0.0,abs(ang2))*exp(-length(d2)*0.7)*0.55*I*(0.5+0.5*fog);
  float sw2 = sin(t*0.19+2.0)*0.9;
  vec2 d3 = p - vec2(sw2, 1.05); float ang3 = atan(d3.x, -d3.y);
  col += vec3(0.9,0.6,0.8)*smoothstep(0.05,0.0,abs(ang3))*exp(-length(d3)*0.8)*0.35*I;
  // stage glow
  col += vec3(0.4,0.55,0.5)*exp(-length((p-vec2(0.0,0.05))*vec2(0.5,1.4))*2.2)*I*0.5;
  // crowd silhouette
  float heads = -0.42 + 0.07*fbm3(vec2(p.x*5.0, 0.5)) + 0.025*sin(p.x*38.0);
  col *= smoothstep(heads-0.03, heads+0.03, p.y);
  return col;
}

vec3 render(int id, vec2 p, float t){
  if(id==1) return sceneField(p, t, uDusk, uCam.x);
  if(id==2) return sceneSky(p, t);
  if(id==3) return sceneBBS(p, t);
  if(id==4) return sceneCD(p, t);
  if(id==5) return sceneSea(p, t);
  if(id==6) return sceneConcert(p, t);
  if(id==7) return sceneField(p, t, 1.0, uCam.x);
  return vec3(0.0);
}

void main(){
  float asp = uRes.x/uRes.y;
  vec2 p = (vUv*2.0-1.0)*vec2(asp,1.0);
  vec3 col = render(uSceneA, p, uTime);
  if(uMix > 0.001){ vec3 c2 = render(uSceneB, p, uTime); col = mix(col, c2, uMix); }
  fragColor = vec4(col, 1.0);
}`;

// composite: low-res scene (bilinear) + full-res premultiplied overlay
const COMP = `#version 300 es
precision highp float;
in vec2 vUv; out vec4 fragColor;
uniform sampler2D uScene; uniform sampler2D uOverlay;
void main(){
  vec3 col = texture(uScene, vUv).rgb;
  vec4 ov = texture(uOverlay, vec2(vUv.x, 1.0-vUv.y));
  col = col*(1.0-ov.a) + ov.rgb;
  fragColor = vec4(col, 1.0);
}`;

// bloom: bright-pass + wide blur at quarter resolution
const BLOOM = `#version 300 es
precision highp float;
in vec2 vUv; out vec4 fragColor;
uniform sampler2D uTex; uniform vec2 uRes;
void main(){
  vec2 texel = 1.0/uRes; vec3 b = vec3(0.0); float wsum = 0.0;
  for(int i=0;i<8;i++){ float a = float(i)*0.7854; vec2 off = vec2(cos(a),sin(a))*1.5*texel; b += max(texture(uTex, vUv+off).rgb - 0.60, 0.0); wsum += 1.0; }
  for(int i=0;i<8;i++){ float a = float(i)*0.7854+0.39; vec2 off = vec2(cos(a),sin(a))*3.5*texel; b += max(texture(uTex, vUv+off).rgb - 0.60, 0.0)*0.7; wsum += 0.7; }
  for(int i=0;i<8;i++){ float a = float(i)*0.7854+0.2; vec2 off = vec2(cos(a),sin(a))*6.5*texel; b += max(texture(uTex, vUv+off).rgb - 0.60, 0.0)*0.45; wsum += 0.45; }
  fragColor = vec4(b/wsum*1.9, 1.0);
}`;

const POST = `#version 300 es
precision highp float;
in vec2 vUv; out vec4 fragColor;
uniform sampler2D uTex; uniform sampler2D uBloomTex; uniform vec2 uRes; uniform float uTime;
uniform float uGrain, uAberr, uVig, uLetter, uCRT, uPillar, uDV, uFlash, uFade, uBloom, uDesat, uWarm;
${COMMON}
void main(){
  vec2 uv = vUv;
  if(uCRT>0.0){ vec2 c = uv*2.0-1.0; c *= 1.0 + uCRT*0.07*dot(c,c); uv = mix(uv, c*0.5+0.5, uCRT); }
  vec2 texel = 1.0/uRes;
  vec2 dir = (uv-0.5);
  float ab = uAberr*2.2;
  vec3 col;
  col.r = texture(uTex, uv + dir*ab*texel*2.0).r;
  col.g = texture(uTex, uv).g;
  col.b = texture(uTex, uv - dir*ab*texel*2.0).b;
  if(uDV>0.0){
    vec2 blk = vec2(6.0,3.0);
    vec2 buv = (floor(uv*uRes/blk)+0.5)*blk/uRes;
    vec3 c2 = texture(uTex, buv + vec2(texel.x*1.5,0.0)).rgb;
    float l1 = dot(col, vec3(0.299,0.587,0.114)); float l2 = dot(c2, vec3(0.299,0.587,0.114));
    vec3 chroma = c2 - l2;
    col = mix(col, vec3(l1) + chroma*1.15, uDV);
    col = mix(col, floor(col*28.0)/28.0, uDV*0.6);
    // interlace tearing line
    float tear = step(0.985, hash(vec2(floor(uv.y*uRes.y*0.5), floor(uTime*8.0))));
    col = mix(col, texture(uTex, uv+vec2(texel.x*6.0,0.0)).rgb, tear*uDV*0.8);
  }
  if(uBloom>0.0){ vec3 b = texture(uBloomTex, uv).rgb; col += b*uBloom*0.55; }
  float lum = dot(col, vec3(0.299,0.587,0.114));
  col = mix(col, vec3(lum), uDesat);
  // gentle film curve + warmth
  col = pow(max(col,0.0), vec3(1.0/1.06));
  col = mix(col, col*vec3(1.04,1.0,0.94)+vec3(0.02,0.01,0.0), uWarm);
  vec2 q = uv*2.0-1.0; float v = 1.0 - uVig*dot(q*vec2(1.0,1.2),q*vec2(1.0,1.2))*0.38;
  col *= clamp(v,0.0,1.0);
  if(uCRT>0.0){ col *= 1.0 - uCRT*0.16*(0.5+0.5*sin(uv.y*uRes.y*3.1416)); col *= 1.0 - uCRT*0.05*(0.5+0.5*sin(uv.x*uRes.x*2.094)); }
  float g = hash(uv*uRes + fract(uTime*7.31)*137.0) - 0.5;
  float g2 = hash(floor(uv*uRes*0.5) + fract(uTime*5.13)*91.0) - 0.5;
  col += (g*0.7+g2*0.5)*uGrain*(0.95 - 0.55*lum);
  if(uCRT>0.0 && (uv.x<0.0||uv.x>1.0||uv.y<0.0||uv.y>1.0)) col = vec3(0.0);
  float lb = step(uLetter, uv.y) * step(uLetter, 1.0-uv.y);
  float pb = step(uPillar, uv.x) * step(uPillar, 1.0-uv.x);
  col *= lb*pb;
  col = mix(col, vec3(1.0), uFlash);
  col *= 1.0-uFade;
  fragColor = vec4(col, 1.0);
}`;
return { VERT, SCENE, COMP, BLOOM, POST };
})();
