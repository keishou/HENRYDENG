// Sea, sky and weather: shared by THE SEA, THE WAVE and the RETURN.
import * as THREE from 'three';
import { NOISE, SKY, WAVES } from './glsl.js';
import { rng } from './engine.js';

export function skyUniforms() {
  return {
    uZenith: { value: new THREE.Color() }, uHorizon: { value: new THREE.Color() }, uGround: { value: new THREE.Color() },
    uSunDir: { value: new THREE.Vector3(0, .1, -1).normalize() }, uSunCol: { value: new THREE.Color() },
    uCloudCol: { value: new THREE.Color() }, uCloudAmt: { value: 1 }, uFlash: { value: 0 }, uEnso: { value: 0 },
    uTime: { value: 0 }, uSunSize: { value: 1 },
  };
}

export function waveUniforms() {
  return { uAmp: { value: 1 }, uChop: { value: .8 }, uGiant: { value: 0 }, uGiantPos: { value: -300 },
    uGiantW: { value: 14 }, uGiantDir: { value: new THREE.Vector2(0, 1) } };
}

// JS twin of waveH() for floating props
export function waveHeight(x, z, t, W) {
  let h = 0;
  const amp = W.uAmp.value;
  for (let i = 0; i < 9; i++) {
    const ang = i * 2.399 + .3, dx = Math.cos(ang), dz = Math.sin(ang);
    const wl = 7.5 * Math.pow(.72, i), k = 2 * Math.PI / wl, w = Math.sqrt(9.8 * k) * .55;
    h += amp * wl * .028 * Math.sin(k * (dx * x + dz * z) - w * t + i * 1.7);
  }
  return h;
}

export function makeSky(skyU) {
  const m = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, uniforms: skyU,
    vertexShader: /* glsl */`varying vec3 vD; void main(){ vD = normalize(position);
      vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.); gl_Position = p.xyww; }`,
    fragmentShader: /* glsl */`${NOISE}${SKY} varying vec3 vD; void main(){ gl_FragColor = vec4(skyColor(normalize(vD)), 1.); }`,
  });
  const s = new THREE.Mesh(new THREE.SphereGeometry(800, 48, 24), m);
  s.frustumCulled = false; s.renderOrder = -10;
  return s;
}

export function makeOcean(skyU, waveU, { size = 900, seg = 360 } = {}) {
  const u = Object.assign({}, skyU, waveU, {
    uDeep: { value: new THREE.Color(.004, .02, .03) }, uSSS: { value: new THREE.Color(.02, .12, .12) },
    uFoamCol: { value: new THREE.Color(.9, .92, .9) }, uFogCol: { value: new THREE.Color() }, uFogDist: { value: 250 },
    uGlint: { value: 1 }, uFoamAmt: { value: .4 }, uLights: { value: [] }, uNLights: { value: 0 },
  });
  const m = new THREE.ShaderMaterial({
    uniforms: u,
    vertexShader: /* glsl */`
      ${WAVES}
      uniform float uTime; varying vec3 vW; varying float vH;
      void main(){
        vec4 w = modelMatrix * vec4(position, 1.);
        vec2 disp; float h = waveH(w.xz, uTime, disp);
        w.xz += disp; w.y += h; vW = w.xyz; vH = h;
        gl_Position = projectionMatrix * viewMatrix * w;
      }`,
    fragmentShader: /* glsl */`
      ${NOISE}${SKY}${WAVES}
      uniform vec3 uDeep, uSSS, uFoamCol, uFogCol; uniform float uFogDist, uGlint, uFoamAmt;
      varying vec3 vW; varying float vH;
      float hAt(vec2 p){ vec2 d; float h = waveH(p, uTime, d);
        h += (fbm3(vec3(p * 1.7, uTime * .35)) - .5) * .12 * uAmp + (vnoise(vec3(p * 5.3, uTime * .8)) - .5) * .03 * uAmp;
        return h; }
      void main(){
        vec3 V = normalize(cameraPosition - vW);
        float dist = length(cameraPosition - vW);
        float e = mix(.04, 1.2, clamp(dist / 180., 0., 1.));
        vec2 p = vW.xz;
        float h0 = hAt(p), hx = hAt(p + vec2(e, 0.)), hz = hAt(p + vec2(0., e));
        vec3 N = normalize(vec3(h0 - hx, e, h0 - hz));
        N = normalize(mix(N, vec3(0., 1., 0.), clamp(dist / 500., 0., .85)));
        float F = .02 + .98 * pow(1. - max(dot(N, V), 0.), 5.);
        vec3 R = reflect(-V, N); R.y = abs(R.y);
        vec3 refl = skyColor(R);
        float gr = uGiant > .1 ? vH / (uGiant + 1e-3) : 0.;
        vec3 body = uDeep + uSSS * clamp(vH * .15 + .2, 0., 1.) * max(dot(normalize(vec3(uSunDir.x, 0., uSunDir.z)), -V) * .5 + .5, 0.);
        body = body * (1. - smoothstep(.1, .5, gr) * .6) + uSSS * 2.5 * smoothstep(.5, .88, gr) * (1. - smoothstep(.9, 1., gr));
        vec3 col = mix(body, refl, F);
        col += uSunCol * pow(max(dot(R, uSunDir), 0.), 600.) * 60. * uGlint;
        // crest foam: the giant wave's lip and ordinary whitecaps
        float g = smoothstep(.72, .97, gr) + smoothstep(.3, .75, gr) * .35 * smoothstep(.55, .8, fbm(vec3(p.x * .9, p.y * .12, uTime * .3)));
        float claws = smoothstep(.45, .75, fbm(vec3(p * .45, uTime * .4)) + g * .6);
        float caps = smoothstep(.62, .9, fbm(vec3(p * .8, uTime * .25))) * smoothstep(.3, 1.2, vH / max(uAmp, .01));
        float foam = clamp(g * claws * 1.4 + caps * uFoamAmt, 0., 1.);
        col = mix(col, uFoamCol * (.6 + .4 * max(dot(N, normalize(uSunDir + vec3(0., .6, 0.))), 0.)) + uFlash * .4, foam);
        col = mix(col, uFogCol, 1. - exp(-dist / uFogDist));
        gl_FragColor = vec4(col, 1.);
      }`,
  });
  const g = new THREE.PlaneGeometry(size, size, seg, seg);
  // concentrate resolution near the origin: remap grid radially
  const P = g.attributes.position;
  for (let i = 0; i < P.count; i++) {
    const x = P.getX(i), y = P.getY(i), r = Math.hypot(x, y) / (size / 2);
    const k = r > 0 ? Math.pow(r, 1.8) / r : 0;
    P.setXY(i, x * k, y * k);
  }
  g.rotateX(-Math.PI / 2);
  const mesh = new THREE.Mesh(g, m); mesh.frustumCulled = false;
  return mesh;
}

// camera-attached rain streaks
export function makeRain(n = 2600, seed = 5) {
  const r = rng(seed), P = new Float32Array(n * 6), R = new Float32Array(n * 2);
  for (let i = 0; i < n; i++) {
    const x = (r() - .5) * 24, y = (r() - .5) * 14, z = -2 - r() * 26;
    P.set([x, y, z, x, y, z], i * 6); R.set([r(), 0], i * 2); R[i * 2 + 1] = 1;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(P, 3));
  const end = new Float32Array(n * 2); for (let i = 0; i < n; i++) { end[i * 2] = 0; end[i * 2 + 1] = 1; }
  g.setAttribute('aEnd', new THREE.BufferAttribute(end, 1));
  const rnd = new Float32Array(n * 2); for (let i = 0; i < n; i++) rnd[i * 2] = rnd[i * 2 + 1] = R[i * 2];
  g.setAttribute('aRnd', new THREE.BufferAttribute(rnd, 1));
  const m = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime: { value: 0 }, uAlpha: { value: .25 }, uFlash: { value: 0 } },
    vertexShader: /* glsl */`attribute float aEnd, aRnd; uniform float uTime; varying float vE;
      void main(){ vec3 p = position; float fall = mod(p.y - uTime * (13. + aRnd * 6.), 14.) - 7.;
        p.y = fall - aEnd * .55; p.x += aEnd * .12 + fall * .03; vE = aEnd;
        gl_Position = projectionMatrix * vec4(p, 1.); }`,
    fragmentShader: /* glsl */`uniform float uAlpha, uFlash; varying float vE;
      void main(){ gl_FragColor = vec4(vec3(.7, .75, .8) * (1. + uFlash * 3.) * uAlpha * (1. - vE * .8), 1.); }`,
  });
  const l = new THREE.LineSegments(g, m); l.frustumCulled = false;
  return l;
}

// world-space snow / dust / marine snow volume that follows the camera
export function makeMotes(n, { seed = 9, box = 30, size = 2.5, color = [1, 1, 1], fall = .6 } = {}) {
  const r = rng(seed), P = new Float32Array(n * 3), R = new Float32Array(n);
  for (let i = 0; i < n; i++) { P.set([r() * box, r() * box, r() * box], i * 3); R[i] = r(); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(P, 3));
  g.setAttribute('aRnd', new THREE.BufferAttribute(R, 1));
  const m = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    uniforms: { uTime: { value: 0 }, uBox: { value: box }, uCam: { value: new THREE.Vector3() }, uSize: { value: size },
      uCol: { value: new THREE.Color(...color) }, uAlpha: { value: 1 }, uFall: { value: fall }, uScale: { value: 1 } },
    vertexShader: /* glsl */`attribute float aRnd; uniform float uTime, uBox, uSize, uFall, uScale; uniform vec3 uCam;
      varying float vA;
      void main(){ vec3 p = position + vec3(sin(uTime * .3 + aRnd * 20.) * .6, -uTime * uFall * (.6 + aRnd * .8), cos(uTime * .23 + aRnd * 13.) * .6);
        p = uCam + mod(p - uCam, uBox) - uBox * .5;
        vec4 mv = modelViewMatrix * vec4(p, 1.);
        float dz = -mv.z; vA = smoothstep(.5, 2., dz) * smoothstep(uBox * .5, uBox * .25, dz);
        gl_PointSize = clamp(uSize * uScale * (.5 + aRnd) / dz, 1., 18.);
        gl_Position = projectionMatrix * mv; }`,
    fragmentShader: /* glsl */`uniform vec3 uCol; uniform float uAlpha; varying float vA;
      void main(){ float d = length(gl_PointCoord - .5); gl_FragColor = vec4(uCol * smoothstep(.5, .0, d) * vA * uAlpha, 1.); }`,
  });
  const p = new THREE.Points(g, m); p.frustumCulled = false;
  return p;
}

// Odysseus' ship: a dark hull, a mast, a square sail and one lamp
export function makeShip() {
  const grp = new THREE.Group();
  const dark = new THREE.MeshBasicMaterial({ color: 0x050607 });
  const hull = new THREE.Mesh(new THREE.CylinderGeometry(.09, .09, 1, 10, 1, false, 0, Math.PI), dark);
  hull.rotation.z = Math.PI / 2; hull.rotation.x = Math.PI; hull.scale.set(1, 1, .5);
  const mast = new THREE.Mesh(new THREE.BoxGeometry(.012, .55, .012), dark); mast.position.y = .27;
  const sail = new THREE.Mesh(new THREE.PlaneGeometry(.36, .3), new THREE.MeshBasicMaterial({ color: 0x2a221a, side: THREE.DoubleSide }));
  sail.position.set(0, .34, 0); sail.rotation.y = Math.PI / 2 * .85;
  const lamp = new THREE.Mesh(new THREE.SphereGeometry(.018, 8, 6), new THREE.MeshBasicMaterial({ color: new THREE.Color(8, 4.5, 1.8) }));
  lamp.position.set(.42, .06, 0);
  grp.add(hull, mast, sail, lamp);
  return grp;
}

// tōrō nagashi: paper lanterns set adrift for the dead
export function makeLanterns(n = 40, seed = 21, spread = [-40, 40, -10, 45]) {
  const r = rng(seed), grp = new THREE.Group();
  const geo = new THREE.BoxGeometry(.1, .12, .1);
  for (let i = 0; i < n; i++) {
    const hot = 3 + r() * 4;
    const m = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: new THREE.Color(hot, hot * .52, hot * .2) }));
    m.position.set(spread[0] + r() * (spread[1] - spread[0]), 0, spread[2] + r() * (spread[3] - spread[2]));
    m.userData.ph = r() * 6.28; m.rotation.y = r() * 3;
    grp.add(m);
  }
  return grp;
}
