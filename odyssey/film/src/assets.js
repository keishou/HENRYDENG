// Loads the reconstruction (bust.glb, points.bin, facemesh.json) and builds the
// materials every shot shares: the bust (photo ↔ marble ↔ kintsugi), the particle
// face, and the landmark tessellation.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { NOISE } from './glsl.js';
import { rng } from './engine.js';

export async function loadAssets() {
  const gltf = await new GLTFLoader().loadAsync('assets/bust.glb');
  let src; gltf.scene.traverse(o => { if (o.isMesh) src = o; });
  const map = src.material.map; map.colorSpace = THREE.SRGBColorSpace; map.anisotropy = 4;
  const photo = await new THREE.TextureLoader().loadAsync('assets/photo_full.jpg');
  photo.colorSpace = THREE.SRGBColorSpace;
  const face = await (await fetch('assets/facemesh.json')).json();
  const buf = await (await fetch('assets/points.bin')).arrayBuffer();
  const [count, nFront] = new Uint32Array(buf, 0, 2);
  const pos = new Float32Array(buf, 8, count * 3);
  const col = new Uint8Array(buf, 8 + count * 12, count * 3);
  const cls = new Uint8Array(buf, 8 + count * 15, count);
  return { geometry: src.geometry, map, photo, face, cloud: { count, nFront, pos, col, cls } };
}

// ---------------------------------------------------------------- bust
export function makeBustMaterial(A) {
  return new THREE.ShaderMaterial({
    uniforms: {
      uMap: { value: A.map }, uTime: { value: 0 },
      uScanY: { value: -10 }, uScanSoft: { value: .35 }, uPlaneZ: { value: A.face.rim_z },
      uScanGlow: { value: 0 }, uScanCol: { value: new THREE.Color(1, .82, .6) },
      uPhotoMix: { value: 1 }, uLit: { value: 1 }, uCrack: { value: 0 }, uGold: { value: 1 }, uWet: { value: 0 },
      uAge: { value: 0 },
      uKeyDir: { value: new THREE.Vector3(-1, 1, 1) }, uKeyCol: { value: new THREE.Color(1, .95, .88) },
      uFillDir: { value: new THREE.Vector3(1, 0, 1) }, uFillCol: { value: new THREE.Color(.05, .06, .08) },
      uRimDir: { value: new THREE.Vector3(1, .5, -1) }, uRimCol: { value: new THREE.Color(.4, .5, .6) },
      uAmb: { value: new THREE.Color(.02, .02, .025) },
      uSlit: { value: new THREE.Vector3(0, .3, 0) },     // y, width, amount: a band of light across the eyes
      uFogCol: { value: new THREE.Color(0, 0, 0) }, uFogDensity: { value: 0 },
      uEnv: { value: new THREE.Color(.5, .45, .4) }, uExposure: { value: 1 }, uRake: { value: 0 }, uCutFlat: { value: 0 },
    },
    vertexShader: /* glsl */`
      uniform float uScanY, uScanSoft, uPlaneZ;
      varying vec3 vObj, vW, vN; varying vec2 vUv; varying float vScan, vRel;
      void main(){
        vec3 p = position;
        float r = smoothstep(uScanY - uScanSoft, uScanY + uScanSoft, p.y);
        vScan = exp(-abs(p.y - uScanY) * 14.) * (1. - step(uScanY, -9.)); vRel = r;
        vec3 q = vec3(p.xy, mix(uPlaneZ + .004, p.z, r));
        vec3 n = normalize(mix(vec3(0., 0., 1.), normal, r));
        vObj = p; vUv = uv;
        vec4 w = modelMatrix * vec4(q, 1.); vW = w.xyz;
        vN = normalize(mat3(modelMatrix) * n);
        gl_Position = projectionMatrix * viewMatrix * w;
      }`,
    fragmentShader: /* glsl */`
      ${NOISE}
      uniform sampler2D uMap; uniform float uTime, uScanGlow, uPhotoMix, uLit, uCrack, uGold, uWet, uAge, uFogDensity, uExposure, uRake, uCutFlat;
      uniform vec3 uScanCol, uKeyDir, uKeyCol, uFillDir, uFillCol, uRimDir, uRimCol, uAmb, uSlit, uFogCol, uEnv;
      varying vec3 vObj, vW, vN; varying vec2 vUv; varying float vScan, vRel;
      vec3 marble(vec3 p){
        float n = fbm(p * 1.4);
        float v = abs(sin(p.x * 1.7 + p.y * 2.3 + p.z * .9 + n * 7.5));
        float vein = pow(1. - v, 9.) * .5 + pow(1. - abs(sin(p.y * 4.1 - p.x * 1.3 + n * 12.)), 28.) * .3;
        vec3 base = vec3(.83, .81, .77) * (.9 + .1 * fbm(p * 7.));
        base = mix(base, vec3(.36, .37, .39), vein);
        // age: grime settling into the hollows and the lower face
        float grime = smoothstep(.45, .8, fbm(p * 2.6 + 3.)) * uAge;
        return mix(base, base * vec3(.55, .52, .45), grime);
      }
      void main(){
        if (uCutFlat > .5 && vRel < .02) discard;     // flat parts: let the printed photo show
        vec3 N = normalize(vN); if (!gl_FrontFacing) N = -N;
        vec3 V = normalize(cameraPosition - vW);
        vec3 photo = texture2D(uMap, vUv).rgb;
        vec3 alb = mix(marble(vObj), photo, uPhotoMix);
        // kintsugi: cellular fracture lines grown from a seed on the left cheek
        vec3 wp = vObj * 1.25 + (vec3(fbm3(vObj * 2.), fbm3(vObj * 2. + 4.), fbm3(vObj * 2. + 9.)) - .5) * .5;
        vec2 F = voronoi(wp);
        float edge = F.y - F.x;
        float grow = length(vObj - vec3(-.55, -.35, 1.)) / 3.4 + fbm3(vObj * 1.7) * .3;
        float vis = smoothstep(grow - .06, grow, uCrack);
        float line = (1. - smoothstep(.009, .026, edge)) * vis;
        float front = exp(-abs(uCrack - grow) * 22.) * line;
        vec3 gold = vec3(1., .74, .32);
        float isGold = line * uGold;
        alb = mix(alb, gold * .9, isGold);
        alb *= mix(1., .5, uWet * (1. - isGold));
        // lighting
        vec3 L = normalize(uKeyDir);
        float slit = mix(1., exp(-pow((vObj.y - uSlit.x) / uSlit.y, 2.)), uSlit.z);
        float wrap = mix(.15, .35, 1. - uPhotoMix);
        float diff = max((dot(N, L) + wrap) / (1. + wrap), 0.) * slit;
        float fill = max(dot(N, normalize(uFillDir)) * .5 + .5, 0.);
        vec3 H = normalize(L + V);
        float shin = mix(mix(28., 70., uWet), 140., isGold);
        float spec = pow(max(dot(N, H), 0.), shin) * mix(mix(.12, .9, uWet) * (1. - uPhotoMix * .7), 2.2, isGold) * slit;
        float fres = pow(1. - max(dot(N, V), 0.), 4.);
        float rim = fres * max(dot(N, normalize(uRimDir)) * .6 + .4, 0.);
        vec3 lit = alb * (uAmb + uKeyCol * diff + uFillCol * fill)
                 + mix(uKeyCol, uKeyCol * gold * 1.6, isGold) * spec
                 + uRimCol * rim * mix(1., 2.2, isGold)
                 + uEnv * fres * .15 * (uWet + isGold);
        // translucency of stone toward the key light
        lit += alb * uKeyCol * pow(max(dot(-N, L), 0.), 2.) * .06 * (1. - uPhotoMix);
        float rake = mix(1., .82 + .3 * smoothstep(-1.5, 3., vW.x + vW.y), uRake);
        vec3 col = mix(photo * rake, lit, uLit);
        col += gold * isGold * uGold * (.3 + front * 6.);
        col += uScanCol * vScan * uScanGlow * 3.;
        col *= uExposure;
        float d = length(vW - cameraPosition);
        col = mix(col, uFogCol, 1. - exp(-d * uFogDensity));
        gl_FragColor = vec4(col, 1.);
      }`,
  });
}

// ---------------------------------------------------------------- particle face
export function makeCloud(A, { stride = 2, back = true, seed = 3 } = {}) {
  const c = A.cloud, r = rng(seed);
  const idx = [];
  for (let i = 0; i < c.nFront; i += stride) idx.push(i);
  if (back) for (let i = c.nFront; i < c.count; i++) idx.push(i);
  const n = idx.length;
  const P = new Float32Array(n * 3), C = new Float32Array(n * 3), R = new Float32Array(n * 4);
  idx.forEach((j, k) => {
    P[k * 3] = c.pos[j * 3]; P[k * 3 + 1] = c.pos[j * 3 + 1]; P[k * 3 + 2] = c.pos[j * 3 + 2];
    C[k * 3] = c.col[j * 3] / 255; C[k * 3 + 1] = c.col[j * 3 + 1] / 255; C[k * 3 + 2] = c.col[j * 3 + 2] / 255;
    R[k * 4] = r(); R[k * 4 + 1] = r(); R[k * 4 + 2] = r(); R[k * 4 + 3] = r();
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(P, 3));
  g.setAttribute('color', new THREE.BufferAttribute(C, 3));
  g.setAttribute('aRnd', new THREE.BufferAttribute(R, 4));
  const m = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, vertexColors: true,
    uniforms: {
      uTime: { value: 0 }, uSize: { value: 2 }, uScale: { value: 1 }, uAlpha: { value: 1 },
      uDissolve: { value: 0 }, uSwirl: { value: 0 }, uCenter: { value: new THREE.Vector3() },
      uRingR: { value: 1.6 }, uRingTilt: { value: .35 }, uBreath: { value: 0 },
      uPal: { value: new THREE.Vector4(1, 0, 0, 0) },  // photo, bioluminescent, mono, sakura
      uFogDensity: { value: 0 }, uGain: { value: 1 },
    },
    vertexShader: /* glsl */`
      ${NOISE}
      attribute vec4 aRnd;
      uniform float uTime, uSize, uScale, uDissolve, uSwirl, uRingR, uRingTilt, uBreath, uFogDensity;
      uniform vec3 uCenter; uniform vec4 uPal;
      varying vec3 vCol; varying float vA;
      void main(){
        vec3 p = position;
        float rnd = aRnd.x;
        p += (vec3(vnoise(p * 2.1 + uTime * .3), vnoise(p * 2.1 + 7. + uTime * .3), vnoise(p * 2.1 + 13. + uTime * .3)) - .5) * uBreath;
        float dk = clamp(uDissolve * 1.7 - rnd * .7, 0., 1.);
        vec3 flow = vec3(vnoise(p * .6 + vec3(0., uTime * .15, 0.)), vnoise(p * .6 + vec3(5., uTime * .15, 1.)), vnoise(p * .6 + vec3(9., 2., uTime * .15))) - .5;
        vec3 dir = normalize(aRnd.yzw - .5 + vec3(0., .25, 0.));
        p += (dir * 2.2 + flow * 7.) * dk * dk * 2.6;
        float sk = clamp(uSwirl * 1.6 - rnd * .6, 0., 1.); sk = sk * sk * (3. - 2. * sk);
        float R = uRingR * (.8 + aRnd.z * .85);
        float ang = aRnd.y * 6.2832 + uTime * (.9 / (R * .8)) ;
        vec3 ring = vec3(cos(ang) * R, (aRnd.w - .5) * .08 * R, sin(ang) * R);
        ring = vec3(ring.x, ring.y * cos(uRingTilt) - ring.z * sin(uRingTilt), ring.y * sin(uRingTilt) + ring.z * cos(uRingTilt));
        vec3 target = uCenter + ring;
        vec3 mid = mix(p, target, .5) + vec3(0., 1.2, 0.) * sin(sk * 3.1416) ;
        p = mix(mix(p, mid, sk), mix(mid, target, sk), sk);
        float lum = dot(color, vec3(.333));
        vec3 bio = mix(vec3(.02, .35, .7), vec3(1., .78, .42), smoothstep(.3, .75, lum)) * (.35 + 1.4 * lum);
        vec3 mono = vec3(.25 + lum * 1.1);
        vec3 sak = mix(vec3(1., .62, .72), vec3(1., .95, .96), aRnd.w) * .9;
        vCol = color * uPal.x + bio * uPal.y + mono * uPal.z + sak * uPal.w;
        vCol *= mix(1., 1.6, sk) ;
        vec4 mv = modelViewMatrix * vec4(p, 1.);
        gl_PointSize = clamp(uSize * uScale / -mv.z * (.55 + .9 * aRnd.w) * (1. + dk * 1.5), 1., 24.);
        vA = exp(-(-mv.z) * uFogDensity) * (1. - dk * .35);
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: /* glsl */`
      uniform float uAlpha, uGain; varying vec3 vCol; varying float vA;
      void main(){ float d = length(gl_PointCoord - .5); float a = smoothstep(.5, .05, d);
        gl_FragColor = vec4(vCol * a * uAlpha * vA * uGain, 1.); }`,
  });
  const pts = new THREE.Points(g, m); pts.frustumCulled = false;
  return pts;
}

// ---------------------------------------------------------------- landmark tessellation
export function makeWire(A) {
  const P = A.face.points, T = A.face.triangles, nose = P[1];
  const seen = new Set(), pos = [], ord = [];
  const d = p => Math.hypot(p[0] - nose[0], p[1] - nose[1], p[2] - nose[2]);
  for (const t of T) for (const [a, b] of [[t[0], t[1]], [t[1], t[2]], [t[2], t[0]]]) {
    const key = a < b ? `${a}_${b}` : `${b}_${a}`;
    if (seen.has(key)) continue; seen.add(key);
    pos.push(...P[a], ...P[b]);
    const o = (d(P[a]) + d(P[b])) / 2; ord.push(o, o);
  }
  const mx = Math.max(...ord);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('aOrd', new THREE.Float32BufferAttribute(ord.map(o => o / mx), 1));
  const m = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uProgress: { value: 0 }, uAlpha: { value: 1 }, uCol: { value: new THREE.Color(.55, .85, 1) }, uTime: { value: 0 } },
    vertexShader: /* glsl */`attribute float aOrd; varying float vO; varying vec3 vP;
      void main(){ vO = aOrd; vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }`,
    fragmentShader: /* glsl */`uniform float uProgress, uAlpha, uTime; uniform vec3 uCol; varying float vO; varying vec3 vP;
      void main(){ float a = smoothstep(uProgress, uProgress - .04, vO);
        float front = exp(-abs(uProgress - vO) * 60.) * 3.;
        float flick = .75 + .25 * sin(uTime * 23. + vP.y * 40.);
        gl_FragColor = vec4(uCol * (a * .55 * flick + front * step(vO, uProgress + .01)) * uAlpha, 1.); }`,
  });
  const lines = new THREE.LineSegments(g, m); lines.frustumCulled = false;
  // landmark nodes
  const ng = new THREE.BufferGeometry();
  ng.setAttribute('position', new THREE.Float32BufferAttribute(P.flat(), 3));
  ng.setAttribute('aOrd', new THREE.Float32BufferAttribute(P.map(p => d(p) / mx), 1));
  const nm = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uProgress: { value: 0 }, uAlpha: { value: 1 }, uScale: { value: 1 } },
    vertexShader: /* glsl */`attribute float aOrd; uniform float uProgress, uScale; varying float vA;
      void main(){ vA = smoothstep(uProgress, uProgress - .02, aOrd); vec4 mv = modelViewMatrix * vec4(position, 1.);
        gl_PointSize = clamp(3.5 * uScale / -mv.z, 1., 6.); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: /* glsl */`uniform float uAlpha; varying float vA; void main(){ float d = length(gl_PointCoord - .5);
        gl_FragColor = vec4(vec3(.8, .95, 1.) * smoothstep(.5, .1, d) * vA * uAlpha, 1.); }`,
  });
  const nodes = new THREE.Points(ng, nm); nodes.frustumCulled = false;
  const grp = new THREE.Group(); grp.add(lines, nodes);
  grp.userData = { lines: m, nodes: nm };
  return grp;
}
