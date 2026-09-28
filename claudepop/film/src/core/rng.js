// rng.js - seeded randomness for a renderer where every frame is a pure function of t (BIBLE 9.2). Never use
// Math.random or Date in film code; derive every random number from a seed (shot id, object index, frame).
//
//   hash(...keys) -> uint32            stable hash of strings / numbers (e.g. hash('S15', 'print', 37))
//   hash01(...keys) -> [0, 1)          the same, as a float
//   rand(seed) -> () => [0, 1)         mulberry32 stream (for building a scene once in init; do not keep one across frames)
//   pick(arr, ...keys), range(a, b, ...keys), gauss(...keys)
//   noise1(t, seed) -> [-1, 1]         smooth value noise (re-exported from avatar.js, the same function the stand-in uses)
//   fbm1(t, seed, octaves = 3)         fractal sum of noise1
//   noise2(x, y, seed) -> [-1, 1]      smooth 2D value noise (quintic fade)
//   frozenSeed(shotId) -> int          grain seed for still prints ("frozen grain": the same every frame of a shot)
export { noise1 } from '../avatar.js';
import { noise1 } from '../avatar.js';

export function hash(...keys) {
  let h = 2166136261 >>> 0;                       // FNV-1a over the keys' string forms, then a murmur finaliser
  for (const k of keys) {
    const s = typeof k === 'number' ? (Number.isInteger(k) ? 'i' + k : 'f' + k.toPrecision(17)) : String(k);
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    h ^= 0x9e37; h = Math.imul(h, 16777619);
  }
  h ^= h >>> 16; h = Math.imul(h, 0x85ebca6b); h ^= h >>> 13; h = Math.imul(h, 0xc2b2ae35); h ^= h >>> 16;
  return h >>> 0;
}
export const hash01 = (...keys) => hash(...keys) / 4294967296;
export function rand(seed) {
  let a = (typeof seed === 'number' ? seed : hash(seed)) >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
export const pick = (arr, ...keys) => arr[Math.floor(hash01(...keys) * arr.length)];
export const range = (a, b, ...keys) => a + (b - a) * hash01(...keys);
export function gauss(...keys) {                  // standard normal (Box-Muller on two hashed uniforms)
  const u = Math.max(1e-12, hash01(...keys, 'g1')), v = hash01(...keys, 'g2');
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}
export function fbm1(t, seed = 0, octaves = 3) {
  let s = 0, a = 1, f = 1, n = 0;
  for (let o = 0; o < octaves; o++) { s += a * noise1(t * f + o * 17.13, seed + o * 101); n += a; a *= 0.5; f *= 2.03; }
  return s / n;
}
export function noise2(x, y, seed = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const q = t => t * t * t * (t * (t * 6 - 15) + 10);
  const h = (i, j) => hash(i, j, seed) / 4294967296;
  const u = q(xf), v = q(yf);
  const a = h(xi, yi), b = h(xi + 1, yi), c = h(xi, yi + 1), d = h(xi + 1, yi + 1);
  return ((a + (b - a) * u) * (1 - v) + (c + (d - c) * u) * v) * 2 - 1;
}
export const frozenSeed = shotId => hash('frozen-grain', shotId) % 100000;
