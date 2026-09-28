// Look-dev page for the protagonist. Driven by capture.mjs through window.* functions; everything is a pure
// function of its parameters (clip time, film time), like the film renderer.
//   window.sheetPanel({ clip, t, az, w, h, layers })   one panel of a motion contact sheet (photo materials)
//   window.shot({ look, shot, t, w, h })               a look-dev frame: look L0..L3, shot 'wide' | 'medium' | 'close'
import * as THREE from 'three';
import { Avatar } from '../src/avatar.js';
import { Looks } from './looks.js';

const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, alpha: false });
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;

const av = await Avatar.load({ glb: '/out/avatar/subject.glb', manifest: '/out/avatar/motion/MANIFEST.json' });
window.clips = av.clipNames.map(n => ({ name: n, seconds: av.clip(n).seconds, loop: av.clip(n).loop, category: av.clip(n).category }));

// ------------------------------------------------------------------------------------------------ motion sheets
const sheet = new THREE.Scene();
sheet.background = new THREE.Color(0x2b2b2b);
sheet.add(new THREE.HemisphereLight(0xffffff, 0x5a5550, 1.5));
const key = new THREE.DirectionalLight(0xffffff, 1.8); key.position.set(2.5, 4, 3); sheet.add(key);
const rim = new THREE.DirectionalLight(0xdfe8ff, 0.7); rim.position.set(-3, 3, -3); sheet.add(rim);
const grid = new THREE.GridHelper(20, 80, 0x8a8a8a, 0x4a4a4a); grid.position.y = 0.001; sheet.add(grid);
const axes = new THREE.GridHelper(20, 20, 0xb0b0b0, 0x6a6a6a); axes.position.y = 0.002; sheet.add(axes);
const sheetCam = new THREE.PerspectiveCamera(24, 1, 0.05, 80);

window.sheetPanel = ({ clip, t, az = 30, el = 0, w = 360, h = 360, layers = {}, span = 2.3, follow = true, center = null, look = 'photo' }) => {
  renderer.setSize(w, h, false);
  av.setLook(look);
  if (av.root.parent !== sheet) sheet.add(av.root);
  const p = av.pose(clip, t);
  av.apply(p, { hands: { curl: 0.5 }, ...layers }, t);
  // frame the body: centre on the pelvis horizontally, fixed height band 0..span
  const c = center ? av.worldPos(center) : follow ? av.worldPos('root') : new THREE.Vector3();
  const a = THREE.MathUtils.degToRad(az), e = THREE.MathUtils.degToRad(el);
  const dist = span / 2 / Math.tan(THREE.MathUtils.degToRad(12)) * 1.02;
  const ty = center ? c.y : Math.max(0.55, Math.min(1.0, c.y));
  sheetCam.aspect = w / h; sheetCam.updateProjectionMatrix();
  sheetCam.position.set(c.x + Math.sin(a) * Math.cos(e) * dist, ty + (center ? Math.sin(e) * dist : 0.35), c.z + Math.cos(a) * Math.cos(e) * dist);
  sheetCam.lookAt(c.x, ty, c.z);
  renderer.render(sheet, sheetCam);
  return canvas.toDataURL('image/jpeg', 0.9);
};

// ------------------------------------------------------------------------------------------------ looks
const looks = new Looks(renderer, av);
await looks.init();
window.looks = looks;
window.shot = (params) => looks.render(params);
window.grab = (q = 0.92) => canvas.toDataURL('image/jpeg', q);
window.ready = true;
