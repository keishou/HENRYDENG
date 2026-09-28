// The thirteen shots. Each shot is a pure function of its local time `lt`:
// it poses its scene/camera and returns the grade for the post pass.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { NOISE } from './glsl.js';
import { clamp, lerp, smooth, ease, easeOut, easeIn, drift, rng } from './engine.js';
import { makeBustMaterial, makeCloud, makeWire } from './assets.js';
import { skyUniforms, waveUniforms, waveHeight, makeSky, makeOcean, makeRain, makeMotes, makeShip, makeLanterns } from './ocean.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const SCOPE = (H, W) => (H - W / 2.39) / 2 / H;

function look(cam, p, t, roll = 0) {
  cam.position.copy(p); cam.up.set(Math.sin(roll), Math.cos(roll), 0); cam.lookAt(t);
}
// sum of decaying flashes (lightning, impacts)
function flashes(T, times, decay = 7, flicker = true) {
  let f = 0;
  for (const te of times) {
    const d = T - te; if (d < 0 || d > 2) continue;
    f += Math.exp(-d * decay) * (flicker ? .65 + .35 * Math.sin(d * 90) : 1);
    const d2 = d - .13; if (flicker && d2 > 0) f += .7 * Math.exp(-d2 * decay * 1.4);
  }
  return f;
}

export class Shots {
  constructor(engine, A, TL) {
    this.e = engine; this.A = A; this.TL = TL;
    const W = engine.W, H = engine.H;
    this.bars = SCOPE(H, W);
    this.aspect = W / H;
    this.scaleY = H / 1080;                     // for point sizes
    this.bustMat = makeBustMaterial(A);
    this.bust = new THREE.Mesh(A.geometry, this.bustMat); this.bust.frustumCulled = false;
    this.cloud = makeCloud(A, { stride: 2, back: true });
    this.cloudU = this.cloud.material.uniforms;
    this.wire = makeWire(A);
    const pmrem = new THREE.PMREMGenerator(engine.renderer);
    this.env = pmrem.fromScene(new RoomEnvironment(), .04).texture;
    const f = A.face;
    this.eyeL = V3(...f.points[468]);   // iris centres (subject's right, left)
    this.eyeR = V3(...f.points[473]);
    this.nose = V3(...f.points[1]);
    this.photoCenter = V3((f.image_px / 2 - f.origin_px[0]) / f.px_per_unit, (f.origin_px[1] - f.image_px / 2) / f.px_per_unit, f.rim_z);
    this.photoSize = f.image_px / f.px_per_unit;
    this.cam = new THREE.PerspectiveCamera(30, this.aspect, .05, 2000);
    this.build();
  }

  resetBust(o = {}) {
    const u = this.bustMat.uniforms;
    const d = { scanY: -10, scanGlow: 0, photoMix: 1, lit: 1, crack: 0, gold: 1, wet: 0, age: 0, fog: 0, exposure: 1,
      slit: [0, .3, 0], keyDir: [-1, 1, 1], keyCol: [1, .95, .88], fillDir: [1, 0, 1], fillCol: [.05, .06, .08],
      rimDir: [1, .5, -1], rimCol: [.4, .5, .6], amb: [.02, .02, .025], fogCol: [0, 0, 0], env: [.5, .45, .4],
      rake: 0, cutFlat: 0 };
    const p = Object.assign(d, o);
    u.uScanY.value = p.scanY; u.uScanGlow.value = p.scanGlow; u.uPhotoMix.value = p.photoMix; u.uLit.value = p.lit;
    u.uCrack.value = p.crack; u.uGold.value = p.gold; u.uWet.value = p.wet; u.uAge.value = p.age;
    u.uFogDensity.value = p.fog; u.uExposure.value = p.exposure; u.uSlit.value.fromArray(p.slit);
    u.uKeyDir.value.fromArray(p.keyDir); u.uKeyCol.value.setRGB(...p.keyCol); u.uFillDir.value.fromArray(p.fillDir);
    u.uFillCol.value.setRGB(...p.fillCol); u.uRimDir.value.fromArray(p.rimDir); u.uRimCol.value.setRGB(...p.rimCol);
    u.uAmb.value.setRGB(...p.amb); u.uFogCol.value.setRGB(...p.fogCol); u.uEnv.value.setRGB(...p.env);
    u.uRake.value = p.rake; u.uCutFlat.value = p.cutFlat;
    this.bust.position.set(0, 0, 0); this.bust.rotation.set(0, 0, 0); this.bust.scale.setScalar(1);
  }

  resetCloud(o = {}) {
    const u = this.cloudU;
    const d = { size: 2.2, alpha: 1, dissolve: 0, swirl: 0, center: [0, 0, 0], ringR: 1.6, ringTilt: .35, breath: 0,
      pal: [1, 0, 0, 0], fog: 0, gain: 1 };
    const p = Object.assign(d, o);
    u.uSize.value = p.size * .006; u.uScale.value = this.e.H / (2 * Math.tan(THREE.MathUtils.degToRad(this.cam.fov) / 2)); u.uAlpha.value = p.alpha; u.uDissolve.value = p.dissolve;
    u.uSwirl.value = p.swirl; u.uCenter.value.fromArray(p.center); u.uRingR.value = p.ringR; u.uRingTilt.value = p.ringTilt;
    u.uBreath.value = p.breath; u.uPal.value.fromArray(p.pal); u.uFogDensity.value = p.fog; u.uGain.value = p.gain * .085;
    this.cloud.position.set(0, 0, 0); this.cloud.rotation.set(0, 0, 0); this.cloud.scale.setScalar(1);
  }

  build() {
    this.buildShutter();
    this.buildBlack();
    this.buildSea();
    this.buildPalace();
    this.buildNobody();
    this.buildYomi();
    this.buildInversion();
    this.buildBox();
  }

  // ------------------------------------------------------------------ passport page + photo
  buildShutter() {
    const s = new THREE.Scene();
    const c = document.createElement('canvas'); c.width = 2048; c.height = 2304;   // 128 px per unit
    const g = c.getContext('2d');
    g.fillStyle = '#cfccc5'; g.fillRect(0, 0, c.width, c.height);
    const r = rng(4);
    for (let i = 0; i < 30000; i++) {            // paper fibres
      g.strokeStyle = `rgba(${r() < .5 ? '255,255,255' : '90,85,80'},${.03 + r() * .05})`;
      g.lineWidth = .6 + r(); g.beginPath();
      const x = r() * c.width, y = r() * c.height, a = r() * 6.28, l = 3 + r() * 14;
      g.moveTo(x, y); g.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); g.stroke();
    }
    g.fillStyle = 'rgba(40,40,45,.9)';
    g.setLineDash([3, 7]); g.strokeStyle = 'rgba(40,40,45,.8)'; g.lineWidth = 2.5;
    g.beginPath(); g.moveTo(1024 - 440, 1184); g.lineTo(1024 + 440, 1184); g.stroke();
    g.font = '30px Jost'; g.textAlign = 'center'; g.fillText('Signature du titulaire*', 1024 + 60, 1232);
    const pageTex = new THREE.CanvasTexture(c); pageTex.colorSpace = THREE.SRGBColorSpace; pageTex.anisotropy = 4;
    // the page is 8 units wide; the 5.12-unit photo sits in its upper half
    const pw = 16, ph = 18;
    const page = new THREE.Mesh(new THREE.PlaneGeometry(pw, ph), new THREE.MeshStandardMaterial({ map: pageTex, roughness: .95 }));
    page.position.set(this.photoCenter.x, this.photoCenter.y - 3.2, this.photoCenter.z - .012);
    const photoMat = new THREE.ShaderMaterial({
      uniforms: { uMap: { value: this.A.photo }, uLight: { value: 1 }, uDim: { value: 0 }, uGrain: { value: 1 } },
      vertexShader: /* glsl */`varying vec2 vUv; varying vec3 vW; void main(){ vUv = uv; vec4 w = modelMatrix * vec4(position, 1.); vW = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w; }`,
      fragmentShader: /* glsl */`${NOISE} uniform sampler2D uMap; uniform float uLight, uDim; varying vec2 vUv; varying vec3 vW;
        void main(){ vec3 c = texture2D(uMap, vUv).rgb;
          float paper = .94 + .06 * vnoise(vec3(vUv * 900., 1.)) + .03 * vnoise(vec3(vUv * 90., 3.));
          float rake = .82 + .3 * smoothstep(-1.5, 3., vW.x + vW.y);
          gl_FragColor = vec4(c * paper * rake * uLight * (1. - uDim), 1.); }`,
    });
    const photo = new THREE.Mesh(new THREE.PlaneGeometry(this.photoSize, this.photoSize), photoMat);
    photo.position.copy(this.photoCenter).add(V3(0, 0, -.004));
    // the signature: 無, written into its own small texture as the pen moves
    const sc = document.createElement('canvas'); sc.width = 512; sc.height = 384;
    const sigTex = new THREE.CanvasTexture(sc); sigTex.colorSpace = THREE.SRGBColorSpace;
    const sig = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.2), new THREE.MeshBasicMaterial({ map: sigTex, transparent: true, depthWrite: false }));
    sig.position.set(this.photoCenter.x + .15, this.photoCenter.y - 3.05, this.photoCenter.z - .006);
    s.add(page, photo, sig);
    s.add(new THREE.AmbientLight(0xffffff, .55));
    const key = new THREE.DirectionalLight(0xfff1e0, 1.6); key.position.set(-4, 6, 5); s.add(key);
    this.shutter = { scene: s, page, photo, photoMat, sig, sc, sigTex, sigDrawn: -1 };
  }

  drawSignature(k) {
    const S = this.shutter;
    const q = Math.round(k * 60) / 60;
    if (q === S.sigDrawn) return;
    S.sigDrawn = q;
    const g = S.sc.getContext('2d');
    g.clearRect(0, 0, 512, 384);
    if (q <= 0) { S.sigTex.needsUpdate = true; return; }
    g.save();
    // reveal roughly in stroke order: top-to-bottom sweeps, left-to-right within a sweep
    g.beginPath();
    const rows = 5, rowH = 384 / rows, prog = q * rows;
    for (let i = 0; i < rows; i++) {
      const f = clamp(prog - i); if (f <= 0) break;
      g.rect(0, i * rowH, 512 * f, rowH + 1);
    }
    g.clip();
    g.fillStyle = 'rgba(12,12,20,.92)'; g.font = '300px MinchoB'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.translate(256, 196); g.rotate(-.06); g.transform(1, 0, -.12, 1, 0, 0);
    g.fillText('無', 0, 0);
    g.restore();
    S.sigTex.needsUpdate = true;
  }

  shutterShot(lt) {        // 7 → 20
    const S = this.shutter, cam = this.cam;
    S.scene.add(this.bust);
    S.page.visible = true; S.sig.visible = false;
    const scan = smooth(5, 10.2, lt);
    this.resetBust({ scanY: lerp(2.6, -3.2, ease(scan)), scanGlow: scan > 0 && scan < 1 ? 1 : 0, lit: lerp(.15, .9, smooth(7, 11, lt)),
      rake: 1, cutFlat: 1,
      keyDir: [-1.2, 1.4, 1.6], keyCol: [1.1, 1.02, .95], amb: [.18, .17, .16], fillCol: [.25, .25, .27], rimCol: [.3, .3, .32] });
    S.photoMat.uniforms.uDim.value = .25 * smooth(8, 12, lt);
    const eye = this.eyeL.clone(); eye.z = this.photoCenter.z;
    let pos, tgt, fov = 18;
    if (lt < 5.2) {                                  // ECU drifting across the eyes, grazing the print
      const k = ease(lt / 5.2);
      tgt = V3(lerp(this.eyeL.x - .15, this.eyeR.x + .05, k), lerp(.06, -.02, k), this.photoCenter.z);
      pos = tgt.clone().add(V3(-.25 + .2 * k, .12, lerp(1.25, 1.05, k)));
      fov = 16;
    } else {                                         // the scan; pull back and swing round
      const k = ease((lt - 5.2) / 7.8);
      const yaw = lerp(0, .62, k), dist = lerp(1.6, 9.2, easeOut((lt - 5.2) / 5));
      tgt = V3(lerp(this.eyeR.x * .5, 0, k), lerp(0, -.35, k), lerp(this.photoCenter.z, .3, k));
      pos = tgt.clone().add(V3(Math.sin(yaw) * dist, lerp(.1, .6, k), Math.cos(yaw) * dist));
      fov = lerp(17, 24, k);
    }
    pos.add(drift(lt, 1).multiplyScalar(.012));
    cam.fov = fov; cam.updateProjectionMatrix(); look(cam, pos, tgt, -.02);
    return { scene: S.scene, camera: cam, post: { bars: this.bars, grain: .085, sat: .9, contrast: 1.05, split: .6,
      gain: [1.02, 1, .96], exposure: 1.05, bloom: .5, vig: .5, fade: 1 - smooth(0, 1.2, lt) } };
  }

  shutterBackShot(lt) {    // 160 → 172
    const S = this.shutter, cam = this.cam;
    S.scene.add(this.bust); S.page.visible = true; S.sig.visible = true;
    const flat = smooth(4.2, 7.6, lt);
    this.resetBust({ scanY: lerp(-3.2, 2.8, ease(flat)), scanGlow: flat > 0 && flat < 1 ? .7 : 0,
      photoMix: smooth(0, 3.2, lt), lit: lerp(1, 0, smooth(3, 7, lt)), crack: 1.4, gold: lerp(1, .8, smooth(4, 8, lt)),
      rake: smooth(3, 7, lt),
      keyDir: [-1.2, 1.4, 1.6], keyCol: [1.1, 1.02, .95], amb: [.18, .17, .16], fillCol: [.25, .25, .27], rimCol: [.3, .3, .32] });
    S.photoMat.uniforms.uDim.value = .25 * (1 - smooth(5, 8, lt));
    this.drawSignature(smooth(6.1, 7.9, lt));
    const k = ease(lt / 8);
    const tgt = V3(lerp(0, this.photoCenter.x, k), lerp(-.3, this.photoCenter.y - 1.1, k), lerp(.4, this.photoCenter.z, k));
    const yaw = lerp(-.45, 0, ease(lt / 7));
    const dist = lerp(8.5, 15.5, ease((lt - 3) / 5));
    const pos = tgt.clone().add(V3(Math.sin(yaw) * dist, lerp(.4, 0, k), Math.cos(yaw) * dist)).add(drift(lt, 7).multiplyScalar(.01));
    cam.fov = 26; cam.updateProjectionMatrix(); look(cam, pos, tgt);
    const T = 160 + lt;
    const shutter = this.TL.events.shutter;
    const flash = T >= shutter && T < shutter + .09 ? 1 : 0;
    const after = smooth(shutter + .1, shutter + 1.6, T);
    return { scene: S.scene, camera: cam, post: { bars: this.bars, grain: .085, sat: .9, split: .5, gain: [1.02, 1, .96],
      flash, fade: T > shutter ? .35 + .65 * after : 0, bloom: .5, vig: .5 } };
  }

  // ------------------------------------------------------------------ black
  buildBlack() { this.black = { scene: new THREE.Scene() }; }
  blackShot(lt, dur) {
    return { scene: this.black.scene, camera: this.cam, post: { bars: this.bars, grain: .08, fade: 0 } };
  }

  // ------------------------------------------------------------------ bust in darkness
  bustShot(lt) {           // 20 → 31
    const s = this.black.scene, cam = this.cam;
    s.add(this.bust); s.add(this.wire);
    const rot = lerp(.42, -.3, ease(lt / 11));
    const slit = smooth(5.5, 8, lt);
    this.resetBust({ keyDir: [-1.6, 1.1, 1.0], keyCol: [1.35, 1.2, 1.02], fillCol: [.03, .045, .06], rimCol: [.35, .5, .7],
      rimDir: [1.2, .4, -1], amb: [.008, .01, .014], slit: [this.eyeL.y + .02, .32, slit] });
    this.bust.rotation.y = rot; this.wire.rotation.y = rot;
    const w = this.wire.userData;
    const prog = smooth(.6, 5.2, lt) * 1.05;
    w.lines.uniforms.uProgress.value = prog; w.nodes.uniforms.uProgress.value = prog;
    w.lines.uniforms.uTime.value = lt; w.nodes.uniforms.uScale.value = this.e.H;
    const wa = 1 - smooth(6.5, 9, lt);
    w.lines.uniforms.uAlpha.value = wa * .8; w.nodes.uniforms.uAlpha.value = wa;
    this.wire.visible = wa > 0;
    const k = ease(smooth(5.5, 11, lt));
    const eye = this.eyeL.clone().applyAxisAngle(V3(0, 1, 0), rot);
    const tgt = V3(0, -.3, .2).lerp(eye, k);
    const dist = lerp(10.5, 2.3, k);
    const pos = tgt.clone().add(V3(lerp(.8, .25, k), lerp(.3, .05, k), dist)).add(drift(lt, 2).multiplyScalar(lerp(.02, .006, k)));
    cam.fov = lerp(25, 20, k); cam.updateProjectionMatrix(); look(cam, pos, tgt);
    const r = { scene: s, camera: cam, post: { bars: this.bars, grain: .075, contrast: 1.12, split: 1, sat: .95, bloom: .8,
      bloomThresh: .7, vig: .55, exposure: 1.1 } };
    r.after = () => { s.remove(this.wire); };
    return r;
  }

  // ------------------------------------------------------------------ the sea
  buildSea() {
    const s = new THREE.Scene();
    this.skyU = skyUniforms(); this.waveU = waveUniforms();
    this.sky = makeSky(this.skyU);
    this.ocean = makeOcean(this.skyU, this.waveU);
    this.rain = makeRain();
    this.ship = makeShip();
    this.lanterns = makeLanterns(46, 21, [-45, 45, -20, 55]);
    this.snow = makeMotes(5000, { seed: 31, box: 26, size: 26, color: [1, .97, .95], fall: .5 });
    s.add(this.sky, this.ocean, this.ship, this.lanterns, this.snow, this.rain);
    this.seaScene = s;
  }

  poseSea(lt, T) {
    for (const k of ['uTime']) { this.skyU[k].value = T; }
    this.ocean.position.set(Math.round(this.cam.position.x), 0, Math.round(this.cam.position.z));
    const W = this.waveU;
    this.lanterns.children.forEach((m, i) => {
      m.position.y = waveHeight(m.position.x, m.position.z, T, W) + .03;
      m.rotation.z = Math.sin(T * .9 + m.userData.ph) * .15;
    });
  }

  placeShip(x, z, T, heading = 0) {
    const y = waveHeight(x, z, T, this.waveU);
    this.ship.position.set(x, y - .02, z);
    this.ship.rotation.set(Math.sin(T * 1.1) * .05, heading, Math.sin(T * .8 + 1) * .06);
  }

  stormSky(flash) {
    const u = this.skyU;
    u.uZenith.value.setRGB(.012, .016, .024); u.uHorizon.value.setRGB(.07, .085, .1); u.uGround.value.setRGB(.01, .012, .015);
    u.uSunDir.value.set(-.6, .05, -1).normalize(); u.uSunCol.value.setRGB(.25, .12, .06); u.uSunSize.value = 1;
    u.uCloudCol.value.setRGB(.05, .06, .075); u.uCloudAmt.value = 1.25; u.uFlash.value = flash; u.uEnso.value = 0;
  }

  seaShot(lt) {            // 31 → 45, IMAX
    const T = 31 + lt, cam = this.cam, s = this.seaScene;
    const fl = flashes(T, this.TL.events.lightning);
    this.stormSky(fl);
    const W = this.waveU; W.uAmp.value = 1.15; W.uChop.value = .95; W.uGiant.value = 0;
    const o = this.ocean.material.uniforms;
    o.uDeep.value.setRGB(.003, .012, .018); o.uSSS.value.setRGB(.01, .05, .055); o.uFogCol.value.setRGB(.06, .075, .09);
    o.uFogDist.value = 160; o.uGlint.value = .3; o.uFoamAmt.value = .55;
    s.add(this.bust);
    const S = 3.3; this.bust.scale.setScalar(S);
    this.resetBust({ photoMix: 0, wet: .6, keyDir: [-.7, .9, .6], keyCol: [.34, .36, .4].map(v => v + fl * 2.4),
      fillCol: [.07, .085, .1], fillDir: [.6, .2, 1], rimCol: [.18, .2, .24].map(v => v + fl * 1.2), rimDir: [.4, 1, -.5],
      amb: [.03, .035, .045], fog: .006, fogCol: [.06, .075, .09], env: [.3, .34, .4] });
    this.bust.scale.setScalar(S); this.bust.position.set(0, 4.1, 0); this.bust.rotation.y = .12;
    this.snow.visible = false; this.ship.visible = true; this.lanterns.visible = true;
    let pos, tgt, roll = 0;
    if (lt < 7.2) {       // wide helicopter push over the water
      const k = ease(lt / 7.2);
      pos = V3(lerp(-9, -5, k), lerp(2.1, 1.5, k), lerp(64, 40, k));
      tgt = V3(0, 5.2, 0); roll = lerp(-.03, .01, k);
      cam.fov = 34;
      this.placeShip(lerp(2.2, 2.6, k), 26, T, -.4);
    } else {              // circling closer in the rain
      const k = ease((lt - 7.2) / 6.8);
      const a = lerp(.95, .45, k), d = lerp(23, 18, k);
      pos = V3(Math.sin(a) * d, lerp(1.1, 1.7, k), Math.cos(a) * d);
      tgt = V3(0, lerp(5.6, 6.2, k), 0); roll = .02;
      cam.fov = 30;
      this.placeShip(-6, 13, T, .6);
    }
    pos.add(drift(T, 3).multiplyScalar(.18));
    pos.y = Math.max(pos.y, waveHeight(pos.x, pos.z, T, W) + .6);
    cam.updateProjectionMatrix(); look(cam, pos, tgt, roll);
    this.poseSea(lt, T);
    this.rain.material.uniforms.uTime.value = T; this.rain.material.uniforms.uFlash.value = fl;
    this.rain.material.uniforms.uAlpha.value = .13;
    this.rain.visible = true;
    return { scene: s, camera: cam, clear: 0x000000,
      post: { bars: 0, grain: .075, sat: .5, contrast: 1.12, split: .8, gain: [.95, 1, 1.05], exposure: 1.25 + fl * .6,
        bloom: .7, bloomThresh: .8, vig: .45, ca: .002 } };
  }

  waveShot(lt) {           // 59 → 72, IMAX: the sea stands up
    const T = 59 + lt, cam = this.cam, s = this.seaScene;
    const u = this.skyU;
    u.uZenith.value.setRGB(.01, .02, .045); u.uHorizon.value.setRGB(.16, .19, .23); u.uGround.value.setRGB(.01, .015, .03);
    u.uSunDir.value.set(.3, .2, -1).normalize(); u.uSunCol.value.setRGB(.03, .03, .03); u.uSunSize.value = 1.5;
    u.uCloudCol.value.setRGB(.1, .12, .16); u.uCloudAmt.value = .9; u.uFlash.value = 0; u.uEnso.value = 0;
    const W = this.waveU; W.uAmp.value = .9; W.uChop.value = .9;
    const rush = easeIn(smooth(8.6, 11.7, lt));
    W.uGiant.value = 34 * smooth(.5, 7.5, lt); W.uGiantW.value = 15;
    W.uGiantPos.value = lt < 8.6 ? lerp(-240, -78, ease(lt / 8.6)) : lerp(-78, 14, rush); W.uGiantDir.value.set(0, 1);
    const o = this.ocean.material.uniforms;
    o.uDeep.value.setRGB(.003, .012, .03); o.uSSS.value.setRGB(.015, .07, .1); o.uFogCol.value.setRGB(.14, .17, .21);
    o.uFogDist.value = 520; o.uGlint.value = .25; o.uFoamAmt.value = .5; o.uFoamCol.value.setRGB(.93, .9, .82);
    s.add(this.bust);
    this.resetBust({ photoMix: 0, wet: .55, keyDir: [.5, .7, .9], keyCol: [.42, .44, .48], fillCol: [.06, .08, .11],
      rimCol: [.4, .44, .5], rimDir: [0, .8, -1], amb: [.03, .04, .055], fog: .004, fogCol: [.14, .17, .21], env: [.3, .35, .4] });
    this.bust.scale.setScalar(3.3); this.bust.position.set(0, 4.1, 0); this.bust.rotation.y = -.2;
    this.snow.visible = false; this.ship.visible = true; this.lanterns.visible = false; this.rain.visible = false;
    this.placeShip(-3.5, 9, T, 1.2);
    const k = ease(lt / 11.6);
    const pos = V3(lerp(6, 4.2, k), lerp(1.5, 1.1, k), lerp(27, 22, k));
    const crest = V3(0, 34 * smooth(.5, 7.5, lt) + 2, W.uGiantPos.value);
    const tgt = V3(-.5, 6.5, 0).lerp(crest, clamp(smooth(3, 11.4, lt) * .75));
    pos.add(drift(T, 5).multiplyScalar(.1 + .45 * smooth(9, 11.6, lt)));
    cam.fov = lerp(40, 58, easeIn(smooth(8, 11.6, lt))); cam.updateProjectionMatrix(); look(cam, pos, tgt, lerp(0, -.06, k));
    this.poseSea(lt, T);
    const crash = this.TL.events.impacts.find(t => t > 70 && t < 71);
    const flash = smooth(crash - .5, crash, T) * (T < crash + .3 ? 1 : 0);
    const fade = T >= crash + .3 ? 1 : 0;
    return { scene: s, camera: cam, clear: 0,
      post: { bars: 0, grain: .08, sat: .75, contrast: 1.2, lift: [0, .005, .02], gain: [.88, .98, 1.12], exposure: 1.3,
        bloom: .6, vig: .5, flash, fade } };
  }

  returnShot(lt) {         // 138 → 160, IMAX: dawn
    const T = 138 + lt, cam = this.cam, s = this.seaScene;
    const u = this.skyU;
    u.uZenith.value.setRGB(.09, .12, .22); u.uHorizon.value.setRGB(1.0, .56, .33); u.uGround.value.setRGB(.05, .04, .05);
    u.uSunDir.value.set(-.42, .085, -1).normalize(); u.uSunCol.value.setRGB(1.5, .95, .52); u.uSunSize.value = 1.6;
    u.uCloudCol.value.setRGB(.55, .38, .36); u.uCloudAmt.value = .55; u.uFlash.value = 0;
    u.uEnso.value = smooth(2.5, 9.5, lt);
    const W = this.waveU; W.uAmp.value = .42; W.uChop.value = .6; W.uGiant.value = 0;
    const o = this.ocean.material.uniforms;
    o.uDeep.value.setRGB(.01, .02, .035); o.uSSS.value.setRGB(.05, .06, .06); o.uFogCol.value.setRGB(.75, .5, .38);
    o.uFogDist.value = 380; o.uGlint.value = 1.2; o.uFoamAmt.value = .15; o.uFoamCol.value.setRGB(1, .9, .8);
    s.add(this.bust);
    this.resetBust({ photoMix: 0, wet: .3, crack: 1.4, gold: 1, age: .3, keyDir: [-1, .45, .45], keyCol: [1.25, .88, .6],
      fillCol: [.1, .1, .14], fillDir: [.6, .2, 1], rimCol: [1.2, .8, .5], rimDir: [-.3, .3, -1], amb: [.025, .025, .035],
      fog: .0015, fogCol: [.75, .5, .38], env: [.9, .6, .45] });
    this.bust.scale.setScalar(3.3); this.bust.position.set(0, 4.1, 0); this.bust.rotation.y = .05;
    this.snow.visible = true; this.ship.visible = true; this.lanterns.visible = false; this.rain.visible = false;
    let pos, tgt, fov;
    if (lt < 8) {                   // behind the little ship, rising
      const k = ease(lt / 8);
      this.placeShip(lerp(1.5, 1.2, k), lerp(19, 15.5, k), T, Math.PI / 2 + .9);
      pos = V3(lerp(3, 2.2, k), lerp(.5, 2.6, k), lerp(30, 26, k)); tgt = V3(0, lerp(4, 5.5, k), 0); fov = 32;
    } else if (lt < 15) {           // the orbit: the face turns into the light
      const k = ease((lt - 8) / 7);
      this.placeShip(1.1, 14.6, T, Math.PI / 2 + .1);
      const a = lerp(1.15, .38, k), d = lerp(19, 14, k);
      pos = V3(Math.sin(a) * d, lerp(3.2, 4.8, k), Math.cos(a) * d); tgt = V3(0, lerp(5.4, 6.3, k), 0); fov = 30;
    } else {                        // push to the eyes
      const k = ease((lt - 15) / 7);
      this.placeShip(1.1, 14.6, T, Math.PI / 2 + .1);
      const eye = this.eyeL.clone().multiplyScalar(3.3).add(V3(0, 4.1, 0));
      tgt = V3(0, 6.2, 0).lerp(eye, k);
      const a = lerp(.38, .22, k), d = lerp(14, 7.8, k);
      pos = V3(Math.sin(a) * d, lerp(4.8, 4.35, k), Math.cos(a) * d).add(V3(0, 0, 0)); fov = lerp(30, 24, k);
    }
    pos.add(drift(T, 9).multiplyScalar(.08));
    pos.y = Math.max(pos.y, waveHeight(pos.x, pos.z, T, W) + .4);
    cam.fov = fov; cam.updateProjectionMatrix(); look(cam, pos, tgt);
    this.poseSea(lt, T);
    const su = this.snow.material.uniforms;
    su.uTime.value = T; su.uCam.value.copy(cam.position); su.uScale.value = this.e.H / 1080 * 40; su.uAlpha.value = .55;
    return { scene: s, camera: cam, clear: 0,
      post: { bars: 0, grain: .065, sat: 1.05, contrast: 1.12, split: .5, gain: [1.04, 1, .95], exposure: .95, bloom: .8,
        bloomThresh: .95, vig: .45 } };
  }

  // ------------------------------------------------------------------ the palace (underwater)
  buildPalace() {
    const s = new THREE.Scene();
    const bg = new THREE.Mesh(new THREE.SphereGeometry(500, 32, 16), new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false, uniforms: { uTime: { value: 0 } },
      vertexShader: /* glsl */`varying vec3 vD; void main(){ vD = normalize(position); vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.); gl_Position = p.xyww; }`,
      fragmentShader: /* glsl */`${NOISE} uniform float uTime; varying vec3 vD;
        void main(){ vec3 d = normalize(vD);
          vec3 col = mix(vec3(.0, .006, .012), vec3(.02, .16, .2), pow(smoothstep(-.6, 1., d.y), 1.6));
          vec2 q = d.xz / (d.y + 1.25);
          float rays = pow(fbm3(vec3(q.x * 7., q.y * 7., uTime * .07)), 2.2) * smoothstep(-.3, .9, d.y);
          col += vec3(.1, .45, .5) * rays * 1.3;
          float sun = pow(max(d.y, 0.), 12.); col += vec3(.3, .8, .8) * sun * (.7 + .3 * vnoise(vec3(q * 30., uTime)));
          gl_FragColor = vec4(col, 1.); }`,
    }));
    bg.frustumCulled = false;
    this.marine = makeMotes(3500, { seed: 41, box: 16, size: 7, color: [.6, .9, .95], fall: .06 });
    s.add(bg, this.marine);
    this.palace = { scene: s, bg };
  }

  palaceShot(lt) {         // 45 → 59
    const P = this.palace, cam = this.cam, T = 45 + lt;
    P.scene.add(this.cloud);
    P.bg.material.uniforms.uTime.value = T;
    this.resetCloud({ pal: [0, 1, 0, 0], size: 2.4, breath: .05, fog: .02, gain: 1.1, alpha: smooth(0, 1.5, lt) });
    this.cloudU.uTime.value = T;
    this.cloud.rotation.y = lerp(.55, -.2, lt / 14);
    this.cloud.rotation.x = -.08;
    const k = ease(lt / 14);
    let pos, tgt;
    if (lt < 8.5) {
      pos = V3(lerp(-3.5, -1.2, k), lerp(-5.2, -1.4, k), lerp(6.5, 8.4, k)); tgt = V3(0, lerp(.6, 0, k), 0);
    } else {
      const k2 = ease((lt - 8.5) / 5.5);
      tgt = V3(0, 0, 0).lerp(this.eyeR.clone().applyAxisAngle(V3(0, 1, 0), this.cloud.rotation.y), k2 * .85);
      pos = V3(lerp(-1.2, .3, k2), lerp(-1.4, .1, k2), lerp(8.4, 3.2, k2));
    }
    pos.add(drift(T, 4).multiplyScalar(.12));
    cam.fov = 30; cam.updateProjectionMatrix(); look(cam, pos, tgt, Math.sin(T * .2) * .04);
    const mu = this.marine.material.uniforms;
    mu.uTime.value = T; mu.uCam.value.copy(cam.position); mu.uScale.value = this.e.H / 1080 * 30; mu.uAlpha.value = .45;
    return { scene: P.scene, camera: cam, post: { bars: this.bars, grain: .07, sat: 1.1, contrast: 1.05, bloom: 1.1,
      bloomThresh: .45, vig: .55, exposure: 1.1, gain: [.92, 1.02, 1.05] } };
  }

  // ------------------------------------------------------------------ nobody (ensō, B&W)
  buildNobody() {
    const s = new THREE.Scene();
    const enso = new THREE.Mesh(new THREE.PlaneGeometry(9, 9), new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uDraw: { value: 0 }, uTime: { value: 0 }, uGain: { value: 1 } },
      vertexShader: /* glsl */`varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }`,
      fragmentShader: /* glsl */`${NOISE} uniform float uDraw, uTime, uGain; varying vec2 vUv;
        void main(){ vec2 p = (vUv - .5) * 9.; float r = length(p); float th = atan(p.y, p.x);
          float u = fract((-th + 1.9) / 6.28318);                        // stroke parameter, clockwise from lower-left
          float press = .55 + .45 * sin(u * 3.1416) + .15 * vnoise(vec3(u * 14., 0., 1.));
          float R = 2.3 + .05 * sin(th * 2. + .5) + .1 * u;
          float w = .045 + .13 * press * (1. - pow(u, 3.) * .6);
          float bristle = .45 + .55 * smoothstep(.25, .7, vnoise(vec3(u * 90., (r - R) * 40., 2.)));
          float dry = smoothstep(.75, 1., u) * smoothstep(.35, .75, vnoise(vec3(u * 40., (r - R) * 25., 5.)));
          float ink = smoothstep(w, w * .55, abs(r - R)) * bristle * (1. - dry * .9);
          float drawn = smoothstep(uDraw, uDraw - .015, u) * step(.001, uDraw);
          float glow = exp(-abs(r - R) * 3.) * .08 * drawn;
          float core = smoothstep(R - w * 1.2, R - w * 2.5, r);           // the void inside
          vec3 col = vec3(1.) * (ink * drawn * .95 + glow) * uGain;
          gl_FragColor = vec4(col, 1.); }`,
    }));
    const voidDisk = new THREE.Mesh(new THREE.CircleGeometry(2.05, 64), new THREE.MeshBasicMaterial({ color: 0x000000 }));
    voidDisk.position.z = -.02;
    const grp = new THREE.Group(); grp.add(voidDisk, enso); grp.position.set(1.4, .2, -3);
    s.add(grp);
    this.nobody = { scene: s, enso, grp };
  }

  nobodyShot(lt) {         // 72 → 87
    const N = this.nobody, cam = this.cam, T = 72 + lt;
    N.scene.add(this.cloud);
    N.enso.material.uniforms.uDraw.value = smooth(1.6, 5.2, lt) * 1.0;
    N.enso.material.uniforms.uTime.value = T;
    this.cloud.position.set(-2.3, -.1, 0); this.cloud.rotation.set(0, .5, 0); this.cloud.updateMatrixWorld(true);
    const center = this.cloud.worldToLocal(N.grp.position.clone());
    this.resetCloud({ pal: [0, 0, 1, 0], size: 2.1, swirl: smooth(5.2, 13.5, lt), center: center.toArray(), ringR: 2.6,
      ringTilt: 1.25, breath: .02, gain: .9, alpha: smooth(1.2, 2.5, lt) });
    this.cloud.position.set(-2.3, -.1, 0); this.cloud.rotation.set(0, .5, 0);
    this.cloudU.uTime.value = T;
    const k = ease(lt / 15);
    const pos = V3(lerp(-.4, .2, k), lerp(.2, .1, k), lerp(12.5, 10.2, k)).add(drift(T, 6).multiplyScalar(.03));
    cam.fov = 32; cam.updateProjectionMatrix(); look(cam, pos, V3(lerp(-.6, .6, k), .1, -1), lerp(.03, -.02, k));
    cam.updateMatrixWorld(true);
    const c = N.grp.position.clone().project(cam);
    const blackout = 1 - smooth(1.15, 1.25, lt);
    return { scene: N.scene, camera: cam, post: { bars: this.bars, bw: 1, contrast: 1.35, grain: .11, bloom: .9, bloomThresh: .6,
      vig: .6, warp: [c.x * .5 + .5, c.y * .5 + .5, smooth(2, 6, lt) * .9], fade: blackout, exposure: 1.1 } };
  }

  // ------------------------------------------------------------------ yomi: the torii corridor
  buildYomi() {
    const s = new THREE.Scene();
    const parts = [];
    const box = (w, h, d, x, y, z, col) => {
      const g = new THREE.BoxGeometry(w, h, d); g.translate(x, y, z);
      const c = new Float32Array(g.attributes.position.count * 3);
      for (let i = 0; i < c.length; i += 3) c.set(col, i);
      g.setAttribute('color', new THREE.BufferAttribute(c, 3)); parts.push(g);
    };
    const cyl = (r, h, x, y, z, col) => {
      const g = new THREE.CylinderGeometry(r * .92, r, h, 14); g.translate(x, y, z);
      const c = new Float32Array(g.attributes.position.count * 3);
      for (let i = 0; i < c.length; i += 3) c.set(col, i);
      g.setAttribute('color', new THREE.BufferAttribute(c, 3)); parts.push(g);
    };
    const red = [.55, .045, .018], blk = [.012, .01, .009];
    cyl(.085, 2.9, -1.05, 0, 0, red); cyl(.085, 2.9, 1.05, 0, 0, red);
    box(.24, .16, .24, -1.05, -1.4, 0, blk); box(.24, .16, .24, 1.05, -1.4, 0, blk);
    box(3.1, .12, .26, 0, 1.48, 0, blk);            // kasagi
    box(2.9, .12, .22, 0, 1.37, 0, red);            // shimaki
    box(2.6, .11, .1, 0, 1.0, 0, red);              // nuki
    box(.1, .3, .09, 0, 1.2, 0, red);               // gakuzuka
    const geo = mergeGeometries(parts);
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: .62, metalness: 0, envMapIntensity: .04 });
    const n = 64, spacing = 1.05;
    const inst = new THREE.InstancedMesh(geo, mat, n);
    const m = new THREE.Matrix4();
    for (let i = 0; i < n; i++) { m.makeTranslation(0, 0, -i * spacing); inst.setMatrixAt(i, m); }
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(3.2, n * spacing + 10), new THREE.MeshStandardMaterial({ color: 0x0b0a0a, roughness: .3, metalness: .2 }));
    floor.rotation.x = -Math.PI / 2; floor.position.set(0, -1.45, -n * spacing / 2 + 3);
    const tunnel = new THREE.Group(); tunnel.add(inst, floor);
    const lamp = new THREE.PointLight(0xffa860, 4, 10, 1.7);
    const end = new THREE.Mesh(new THREE.PlaneGeometry(2.3, 2.9), new THREE.MeshBasicMaterial({ color: new THREE.Color(3, 2.6, 2.2) }));
    end.position.set(0, -.05, -n * spacing + .3);
    tunnel.add(end);
    s.add(tunnel, lamp, new THREE.AmbientLight(0x301010, .15));
    s.fog = new THREE.FogExp2(0x000000, .085);
    s.environment = this.env;
    this.yomi = { scene: s, tunnel, lamp, spacing, n, end };
  }

  yomiShot(lt) {           // 87 → 102
    const Y = this.yomi, cam = this.cam, T = 87 + lt;
    const z = -lt * 2.9 - easeIn(smooth(10, 15, lt)) * 12;
    const roll = lerp(0, .5, ease(lt / 10)) + easeIn(smooth(9, 15, lt)) * 2.4;
    Y.tunnel.rotation.z = roll;
    const pos = V3(0, .05, 2 + z).add(drift(T, 8).multiplyScalar(.035));
    cam.fov = 44; cam.updateProjectionMatrix(); look(cam, pos, pos.clone().add(V3(0, .03, -5)));
    const flick = .8 + .12 * Math.sin(T * 17) + .08 * Math.sin(T * 41.3);
    Y.lamp.position.copy(pos).add(V3(.25, .6, -2.4)); Y.lamp.intensity = 3.2 * flick;
    Y.scene.fog.density = lerp(.09, .06, smooth(8, 15, lt));
    Y.end.material.color.setRGB(1, .9, .8).multiplyScalar(2 + 10 * smooth(11, 15, lt));
    return { scene: Y.scene, camera: cam, post: { bars: this.bars, grain: .085, sat: 1.05, contrast: 1.22, lift: [.004, 0, 0],
      gain: [1.04, .95, .92], bloom: .7, bloomThresh: .8, vig: .65, exposure: .95, flash: smooth(13.6, 15, lt) * .9 } };
  }

  // ------------------------------------------------------------------ inversion (Penelope / Tenet)
  buildInversion() {
    const s = new THREE.Scene();
    const n = 1100, r = rng(77);
    const base = new THREE.PlaneGeometry(.13, .16);
    const g = new THREE.InstancedBufferGeometry().copy(base); g.instanceCount = n;
    const O = new Float32Array(n * 4);
    for (let i = 0; i < n; i++) O.set([(r() - .5) * 14, r() * 12, -r() * 10 + 3, r()], i * 4);
    g.setAttribute('aO', new THREE.InstancedBufferAttribute(O, 4));
    const m = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, side: THREE.DoubleSide,
      uniforms: { uTime: { value: 0 }, uAlpha: { value: 1 } },
      vertexShader: /* glsl */`attribute vec4 aO; uniform float uTime; varying vec2 vUv; varying float vShade;
        mat3 rot(vec3 a, float t){ a = normalize(a); float c = cos(t), s = sin(t), C = 1. - c;
          return mat3(c + a.x*a.x*C, a.y*a.x*C + a.z*s, a.z*a.x*C - a.y*s, a.x*a.y*C - a.z*s, c + a.y*a.y*C, a.z*a.y*C + a.x*s,
                      a.x*a.z*C + a.y*s, a.y*a.z*C - a.x*s, c + a.z*a.z*C); }
        void main(){ vUv = uv;
          // petals rise: time runs backwards for them
          float y = mod(aO.y + uTime * (.35 + aO.w * .3), 12.) - 6.;
          vec3 c = vec3(aO.x + sin(uTime * .5 + aO.w * 30.) * .4, y, aO.z);
          mat3 R = rot(vec3(aO.w, 1. - aO.w, .5), -uTime * (1.2 + aO.w * 2.) + aO.w * 20.);
          vec3 p = c + R * position;
          vShade = abs((R * vec3(0., 0., 1.)).z) * .7 + .3;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.); }`,
      fragmentShader: /* glsl */`uniform float uAlpha; varying vec2 vUv; varying float vShade;
        void main(){ vec2 p = vUv - .5; p.x *= 1.25;
          float shape = length(vec2(p.x, (p.y + .1) * .8)) < .42 - .12 * smoothstep(.2, .5, p.y) * (1. - smoothstep(.0, .08, abs(p.x))) ? 1. : 0.;
          if (shape < .5) discard;
          vec3 col = mix(vec3(.95, .55, .66), vec3(1., .86, .9), vUv.y) * vShade * .8;
          gl_FragColor = vec4(col * uAlpha, uAlpha); }`,
    });
    const petals = new THREE.Mesh(g, m); petals.frustumCulled = false;
    s.add(petals);
    this.inv = { scene: s, petals };
  }

  inversionShot(lt) {      // 102 → 117
    const I = this.inv, cam = this.cam, T = 102 + lt;
    I.scene.add(this.cloud);
    I.petals.material.uniforms.uTime.value = T;
    const form = ease(smooth(1, 12, lt));
    const k = form;
    this.resetCloud({ pal: [k, 0, 0, 1 - k], size: lerp(2.6, 2.2, k), dissolve: 1 - form, gain: lerp(.8, 1.05, k), breath: .02 });
    this.cloudU.uTime.value = 300 - T;                   // inverted flow
    this.cloud.rotation.y = lerp(-.9, .15, ease(lt / 15));
    const kk = ease(lt / 15);
    const pos = V3(lerp(.8, -.6, kk), lerp(-.3, .15, kk), lerp(6.5, 9.5, kk)).add(drift(300 - T, 10).multiplyScalar(.05));
    cam.fov = 30; cam.updateProjectionMatrix(); look(cam, pos, V3(0, lerp(-.2, -.1, kk), 0), .02);
    return { scene: I.scene, camera: cam, post: { bars: this.bars, grain: .075, sat: .95, contrast: 1.05, gain: [1.04, .98, 1],
      bloom: .9, bloomThresh: .55, vig: .5, flash: (1 - smooth(0, .8, lt)) * .9 } };
  }

  // ------------------------------------------------------------------ the box → stone → gold
  buildBox() {
    const s = new THREE.Scene();
    const lacquer = new THREE.MeshStandardMaterial({ color: 0x0a0605, roughness: .2, metalness: .15, envMapIntensity: 1.1 });
    const gold = new THREE.MeshStandardMaterial({ color: 0xd9a441, roughness: .3, metalness: 1, envMapIntensity: 1.3 });
    const cordM = new THREE.MeshStandardMaterial({ color: 0x8a0d0a, roughness: .6 });
    const box = new THREE.Group();
    const body = new THREE.Mesh(new THREE.BoxGeometry(1.4, .66, 1.0), lacquer); body.position.y = .33;
    const inside = new THREE.Mesh(new THREE.PlaneGeometry(1.3, .9), new THREE.MeshBasicMaterial({ color: new THREE.Color(0, 0, 0) }));
    inside.rotation.x = -Math.PI / 2; inside.position.y = .6;
    const lidPivot = new THREE.Group(); lidPivot.position.set(0, .66, -.5);
    const lid = new THREE.Mesh(new THREE.BoxGeometry(1.46, .2, 1.06), lacquer); lid.position.set(0, .1, .5);
    lidPivot.add(lid);
    for (const [w, h, d, x, y, z, par] of [[1.47, .02, .02, 0, .2, 1.03, lid], [1.47, .02, .02, 0, .2, -.03, lid],
      [.02, .02, 1.07, .73, .2, .5, lid], [.02, .02, 1.07, -.73, .2, .5, lid]]) {
      const e = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), gold); e.position.set(x, y, z); (par === lid ? lidPivot : box).add(e);
    }
    const cord = new THREE.Group();
    for (const [w, h, d] of [[1.5, .04, .045], [.045, .04, 1.1]]) { const c = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), cordM); c.position.set(0, .215, .5); cord.add(c); }
    const knot = new THREE.Mesh(new THREE.TorusGeometry(.08, .025, 8, 20), cordM); knot.position.set(0, .23, .5); knot.rotation.x = Math.PI / 2; cord.add(knot);
    lidPivot.add(cord);
    box.add(body, inside, lidPivot);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color: 0x050505, roughness: .22, metalness: .5 }));
    floor.rotation.x = -Math.PI / 2;
    const spot = new THREE.SpotLight(0xfff0dd, 60, 14, .32, .6, 1.4); spot.position.set(.3, 7, 1.2); spot.target = box;
    const inner = new THREE.PointLight(0xffffff, 0, 6, 1.5); inner.position.set(0, 1.1, 0);
    // smoke
    const n = 1800, r = rng(55), R = new Float32Array(n * 4);
    for (let i = 0; i < n; i++) R.set([r(), r(), r(), r()], i * 4);
    const sg = new THREE.BufferGeometry();
    sg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * 3), 3));
    sg.setAttribute('aRnd', new THREE.BufferAttribute(R, 4));
    const smoke = new THREE.Points(sg, new THREE.ShaderMaterial({
      transparent: true, depthWrite: false,
      uniforms: { uAge: { value: 0 }, uScale: { value: 1 }, uAlpha: { value: 1 } },
      vertexShader: /* glsl */`${NOISE} attribute vec4 aRnd; uniform float uAge, uScale; varying float vA; varying vec4 vR;
        void main(){ vR = aRnd;
          float a = max(uAge - aRnd.x * 1.2, 0.);
          float up = a * (1.6 + aRnd.y * 2.2) + a * a * .25;
          vec3 p = vec3((aRnd.z - .5) * .9, .6 + up, (aRnd.w - .5) * .6);
          vec3 q = p * .5 + vec3(0., -uAge * .4, 0.);
          p += (vec3(vnoise(q), vnoise(q + 5.), vnoise(q + 9.)) - .5) * (1. + a * 2.4);
          p.xz *= 1. + a * (1.1 + aRnd.y);
          vec4 mv = modelViewMatrix * vec4(p, 1.);
          gl_PointSize = clamp((.12 + a * .8) * uScale / -mv.z, 2., 420.);
          vA = smoothstep(0., .25, a) * (1. - smoothstep(3.5, 6., a)) * step(.001, a);
          gl_Position = projectionMatrix * mv; }`,
      fragmentShader: /* glsl */`${NOISE} uniform float uAlpha; varying float vA; varying vec4 vR;
        void main(){ vec2 p = gl_PointCoord - .5; float d = length(p);
          float n = fbm3(vec3(p * 3. + vR.xy * 10., vR.z * 5.));
          float a = smoothstep(.5, .1, d) * (.35 + .65 * n) * vA * uAlpha;
          gl_FragColor = vec4(vec3(.95, .96, 1.), a * .32); }`,
    }));
    smoke.frustumCulled = false;
    box.add(smoke);
    const rimL = new THREE.SpotLight(0xc8d8ff, 40, 12, .5, .5, 1.2); rimL.position.set(-1.5, 3, -4); rimL.target = box;
    s.add(box, floor, spot, inner, rimL, new THREE.AmbientLight(0x202024, .2));
    s.environment = this.env;
    this.dust = makeMotes(900, { seed: 61, box: 8, size: 1.6, color: [1, .95, .85], fall: .05 });
    s.add(this.dust);
    this.boxS = { scene: s, box, lidPivot, cord, inner, smoke, spot, floor, inside };
    this.stone = new THREE.Scene();
  }

  boxShot(lt) {            // 117 → 138
    const B = this.boxS, cam = this.cam, T = 117 + lt;
    if (lt < 11) {
      B.box.visible = true;
      const open = ease(smooth(7.5, 9.2, lt));
      B.lidPivot.rotation.x = -1.95 * open;
      B.cord.visible = lt < 7.1;
      B.inner.intensity = 40 * smooth(7.6, 8.4, lt);
      B.inside.material.color.setScalar(4 * smooth(7.5, 8.6, lt));
      B.smoke.material.uniforms.uAge.value = Math.max(0, lt - 7.7);
      B.smoke.material.uniforms.uScale.value = this.e.H * 1.2;
      const k = ease(lt / 7.5), k2 = ease(smooth(7.5, 11, lt));
      const pos = V3(lerp(-2.6, -1.7, k), lerp(2.3, 1.7, k) + k2 * .5, lerp(6.4, 4.6, k) + k2 * 1.2).add(drift(T, 11).multiplyScalar(.02));
      const tgt = V3(0, lerp(.35, .45, k) + k2 * 1.3, 0);
      cam.fov = 30; cam.updateProjectionMatrix(); look(cam, pos, tgt);
      const du = this.dust.material.uniforms;
      du.uTime.value = T; du.uCam.value.copy(cam.position); du.uScale.value = this.e.H / 1080 * 22; du.uAlpha.value = .25;
      const white = smooth(9.4, 10.9, lt);
      return { scene: B.scene, camera: cam, post: { bars: this.bars, grain: .08, contrast: 1.15, sat: .9, gain: [1.04, 1, .95],
        bloom: .9, bloomThresh: .9, vig: .6, flash: white, exposure: 1.1 } };
    }
    // the stone head, aged three hundred years, and the gold arriving in its cracks
    const s = this.stone; s.add(this.bust);
    const crack = lerp(0, 1.4, smooth(12.2, 18.5, lt));
    this.resetBust({ photoMix: 0, age: 1, crack, gold: 1, keyDir: [-1.3, 1.0, .7], keyCol: [.85, .74, .6],
      fillCol: [.05, .05, .06], rimCol: [.35, .3, .25], rimDir: [1, .3, -1], amb: [.015, .014, .014], env: [.6, .5, .35] });
    this.bust.rotation.y = .3;
    const k = ease((lt - 11) / 10);
    const cheek = V3(-.55, -.3, 1.0).applyAxisAngle(V3(0, 1, 0), .3);
    const tgt = cheek.clone().lerp(V3(0, -.2, .3), k);
    const dir = V3(-.25, .1, 1).normalize();
    const pos = tgt.clone().add(dir.multiplyScalar(lerp(1.4, 8.5, k))).add(drift(T, 12).multiplyScalar(.01));
    cam.fov = lerp(22, 26, k); cam.updateProjectionMatrix(); look(cam, pos, tgt);
    return { scene: s, camera: cam, post: { bars: this.bars, grain: .075, contrast: 1.12, sat: .95, split: .7, gain: [1.03, 1, .95],
      bloom: .7, bloomThresh: .9, vig: .6, flash: 1 - smooth(11, 12.4, lt), exposure: .9 } };
  }

  titleShot(lt) {
    return { scene: this.black.scene, camera: this.cam, post: { bars: this.bars, grain: .08 } };
  }

  // ------------------------------------------------------------------ dispatch
  shot(id, lt, dur) {
    switch (id) {
      case 'open': return this.blackShot(lt, dur);
      case 'shutter': return this.shutterShot(lt);
      case 'bust': return this.bustShot(lt);
      case 'sea': return this.seaShot(lt);
      case 'palace': return this.palaceShot(lt);
      case 'wave': return this.waveShot(lt);
      case 'nobody': return this.nobodyShot(lt);
      case 'yomi': return this.yomiShot(lt);
      case 'inversion': return this.inversionShot(lt);
      case 'box': return this.boxShot(lt);
      case 'return': return this.returnShot(lt);
      case 'shutter_back': return this.shutterBackShot(lt);
      case 'title': return this.titleShot(lt);
    }
  }
}
