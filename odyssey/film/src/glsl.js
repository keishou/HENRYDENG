// Shared GLSL chunks. Everything is procedural and deterministic in time.

export const NOISE = /* glsl */`
float hash11(float p){ p = fract(p * .1031); p *= p + 33.33; p *= p + p; return fract(p); }
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float hash13(vec3 p3){ p3 = fract(p3 * .1031); p3 += dot(p3, p3.zyx + 31.32); return fract((p3.x + p3.y) * p3.z); }
vec3 hash33(vec3 p3){ p3 = fract(p3 * vec3(.1031, .1030, .0973)); p3 += dot(p3, p3.yxz + 33.33);
  return fract((p3.xxy + p3.yxx) * p3.zyx); }
float vnoise(vec3 x){
  vec3 i = floor(x), f = fract(x); f = f * f * (3. - 2. * f);
  return mix(mix(mix(hash13(i), hash13(i + vec3(1,0,0)), f.x), mix(hash13(i + vec3(0,1,0)), hash13(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash13(i + vec3(0,0,1)), hash13(i + vec3(1,0,1)), f.x), mix(hash13(i + vec3(0,1,1)), hash13(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float fbm(vec3 p){ float a = .5, s = 0.; for (int i = 0; i < 5; i++){ s += a * vnoise(p); p = p * 2.03 + 17.1; a *= .5; } return s; }
float fbm3(vec3 p){ float a = .5, s = 0.; for (int i = 0; i < 3; i++){ s += a * vnoise(p); p = p * 2.07 + 11.3; a *= .5; } return s; }
// cellular noise: x = F1, y = F2
vec2 voronoi(vec3 p){
  vec3 i = floor(p), f = fract(p); float d1 = 8., d2 = 8.;
  for (int z = -1; z <= 1; z++) for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++){
    vec3 g = vec3(x, y, z); vec3 r = g + hash33(i + g) - f; float d = dot(r, r);
    if (d < d1){ d2 = d1; d1 = d; } else if (d < d2) d2 = d;
  }
  return sqrt(vec2(d1, d2));
}
`;

// Sky used by the dome and by ocean reflections.
export const SKY = /* glsl */`
uniform vec3 uZenith, uHorizon, uGround, uSunDir, uSunCol, uCloudCol;
uniform float uCloudAmt, uFlash, uEnso, uTime, uSunSize;
float ensoRing(vec3 d){
  // brush-stroke ring of light around the sun: open circle, uneven pressure
  float ang = acos(clamp(dot(d, uSunDir), -1., 1.));
  vec3 t1 = normalize(cross(uSunDir, vec3(0., 1., 0.)));
  vec3 t2 = cross(t1, uSunDir);
  float th = atan(dot(d, t2), dot(d, t1));
  float u = fract((th + 3.14159) / 6.28318 + .23);
  float R = .19 + .006 * sin(th * 3.);
  float w = .012 + .02 * pow(u, 1.5) * (.6 + .4 * vnoise(vec3(th * 9., 0., 1.)));
  float bristle = .55 + .45 * vnoise(vec3(th * 60., ang * 300., 2.));
  float draw = smoothstep(uEnso * 1.02, uEnso * 1.02 - .02, u) * smoothstep(0., .03, u);
  return exp(-pow((ang - R) / w, 2.)) * bristle * draw;
}
vec3 skyColor(vec3 d){
  float h = d.y;
  vec3 col = mix(uHorizon, uZenith, pow(clamp(h, 0., 1.), .45));
  col = mix(col, uGround, smoothstep(0., -.08, h));
  float sd = max(dot(d, uSunDir), 0.);
  col += uSunCol * (pow(sd, 900. / uSunSize) * 30. + pow(sd, 12.) * .35 + pow(sd, 3.) * .12);
  if (h > -.02){
    vec2 cp = d.xz / (h + .12) * .9;
    float c = fbm(vec3(cp * 1.3 + vec2(uTime * .012, 0.), uTime * .01));
    c = smoothstep(.42 - uCloudAmt * .25, .85, c) * uCloudAmt;
    vec3 cc = uCloudCol * (.55 + .6 * fbm(vec3(cp * 3.1, 2.))) + uSunCol * pow(sd, 6.) * .6;
    cc += vec3(.85, .9, 1.) * uFlash * (1.2 + fbm(vec3(cp * 2., 5.)));
    col = mix(col, cc, c * smoothstep(-.02, .08, h));
  }
  col += vec3(.9, .95, 1.) * uFlash * .25;
  col += uSunCol * ensoRing(d) * 6.;
  return col;
}
`;

// Ocean height field (kept in sync with ocean.js: waveHeight()).
export const WAVES = /* glsl */`
uniform float uAmp, uChop, uGiant, uGiantPos, uGiantW;
uniform vec2 uGiantDir;
const int NW = 9;
float waveH(vec2 p, float t, out vec2 disp){
  float h = 0.; disp = vec2(0.);
  for (int i = 0; i < NW; i++){
    float fi = float(i);
    float ang = fi * 2.399 + .3;
    vec2 dir = vec2(cos(ang), sin(ang));
    float wl = 7.5 * pow(.72, fi);
    float k = 6.28318 / wl, w = sqrt(9.8 * k) * .55;
    float a = uAmp * wl * .028;
    float ph = k * dot(dir, p) - w * t + fi * 1.7;
    h += a * sin(ph);
    disp += dir * a * uChop * cos(ph);
  }
  // the giant wave: an asymmetric travelling ridge that leans toward the viewer
  float s = dot(p, uGiantDir) - uGiantPos;
  float lat = dot(p, vec2(-uGiantDir.y, uGiantDir.x));
  float env = .86 + .1 * sin(lat * .045 + 1.3) + .04 * sin(lat * .21);
  float wBack = uGiantW * 2.2, wFront = uGiantW * .55;
  float g = s < 0. ? exp(-s * s / (wBack * wBack)) : exp(-s * s / (wFront * wFront));
  h += uGiant * env * g;
  disp += uGiantDir * uGiant * env * g * .22 * smoothstep(.2, 1., g);
  return h;
}
`;
