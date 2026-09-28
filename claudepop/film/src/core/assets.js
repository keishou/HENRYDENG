// assets.js - cached loaders. URLs are server paths rooted at claudepop/ ('/out/avatar/subject.glb', '/shots.json').
// Every call records its URL under the current scope ('core', 'set:hall', 'shot:S15'), so render.mjs can key the
// shot cache on the mtimes of exactly the files a shot used. Loads happen in init() or the first frame; the returned
// objects are shared and must be treated as read-only (clone before mutating).
//
//   assets.json(url)                 parsed JSON
//   assets.bin(url)                  ArrayBuffer
//   assets.image(url)                ImageBitmap (decoded, no premultiply, no flip)
//   assets.texture(url, { srgb = true, flipY = true, mipmaps = true, repeat = false }) -> THREE.Texture
//   assets.glb(url)                  GLTF result (scene graph shared: clone(true) before modifying)
//   assets.points(url)               { count, positions: Float32Array, colors: Uint8Array, classes: Uint8Array|null }
//                                    (the out/avatar/bust/points.bin layout, as read by avatar/tools/head_points.py)
//   assets.exists(url)               HEAD probe -> bool (cached)
//   assets.list(dir)                 directory listing via the render server (/__ls), [] when unsupported
//   assets.fonts(list)               register FontFaces, trying /fonts/ (lane B, BIBLE 6.1) then /out/fonts/ for each file
//   assets.scope(name, fn)           run fn with a usage scope (core does this around set/scene init and frames)
//   assets.used(scope) -> [url]
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export class Assets {
  constructor() { this.cache = new Map(); this.usage = new Map(); this.cur = 'core'; this._exists = new Map(); }
  _touch(url) { let s = this.usage.get(this.cur); if (!s) this.usage.set(this.cur, (s = new Set())); s.add(url.split('?')[0]); }
  async scope(name, fn) { const prev = this.cur; this.cur = name; try { return await fn(); } finally { this.cur = prev; } }
  scopeSync(name, fn) { const prev = this.cur; this.cur = name; try { return fn(); } finally { this.cur = prev; } }
  used(scope) { return [...(this.usage.get(scope) || [])]; }
  _get(kind, url, make) {
    this._touch(url);
    const key = kind + ':' + url;
    if (!this.cache.has(key)) {
      const p = make().catch(e => { this.cache.delete(key); throw new Error(`asset ${url}: ${e.message || e}`); });
      this.cache.set(key, p);
    }
    return this.cache.get(key);
  }
  async _fetch(url) { const r = await fetch(url); if (!r.ok) throw new Error('HTTP ' + r.status); return r; }
  json(url) { return this._get('json', url, async () => (await this._fetch(url)).json()); }
  bin(url) { return this._get('bin', url, async () => (await this._fetch(url)).arrayBuffer()); }
  image(url) { return this._get('img', url, async () => createImageBitmap(await (await this._fetch(url)).blob(), { premultiplyAlpha: 'none', colorSpaceConversion: 'none' })); }
  texture(url, { srgb = true, flipY = true, mipmaps = true, repeat = false } = {}) {
    return this._get(`tex${+srgb}${+flipY}${+mipmaps}${+repeat}`, url, async () => {
      const img = await createImageBitmap(await (await this._fetch(url)).blob(), { imageOrientation: flipY ? 'flipY' : 'from-image', premultiplyAlpha: 'none', colorSpaceConversion: 'none' });
      const tex = new THREE.Texture(img);
      tex.flipY = false;                               // ImageBitmap: flip at decode time instead (WebGL ignores flipY for bitmaps)
      tex.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      tex.generateMipmaps = mipmaps; tex.minFilter = mipmaps ? THREE.LinearMipmapLinearFilter : THREE.LinearFilter;
      tex.anisotropy = 4;
      if (repeat) tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
      tex.needsUpdate = true;
      return tex;
    });
  }
  glb(url) { return this._get('glb', url, () => new GLTFLoader().loadAsync(url)); }
  // odyssey bust point cloud (out/avatar/bust/points.bin): uint32 count, 4 pad bytes, float32 xyz * n, u8 rgb * n, u8 class * n
  points(url) {
    return this._get('pts', url, async () => {
      const buf = await (await this._fetch(url)).arrayBuffer();
      const n = new Uint32Array(buf, 0, 1)[0];
      return { count: n, positions: new Float32Array(buf, 8, n * 3), colors: new Uint8Array(buf, 8 + n * 12, n * 3),
        classes: buf.byteLength >= 8 + n * 16 ? new Uint8Array(buf, 8 + n * 15, n) : null };
    });
  }
  async exists(url) {
    this._touch(url);
    if (!this._exists.has(url)) this._exists.set(url, fetch(url, { method: 'HEAD' }).then(r => r.ok).catch(() => false));
    return this._exists.get(url);
  }
  async list(dir) {
    try { const r = await fetch('/__ls?dir=' + encodeURIComponent(dir.replace(/^\//, ''))); return r.ok ? await r.json() : []; } catch { return []; }
  }
  // list: [family, file, descriptors]; resolves to the families that loaded. Bases tried in order.
  async fonts(list, bases = ['/fonts/', '/out/fonts/']) {
    const ok = [];
    await Promise.all(list.map(async ([fam, file, desc = {}]) => {
      for (const b of bases) {
        if (!(await this.exists(b + file))) continue;
        try { const f = new FontFace(fam, `url(${b}${file})`, desc); await f.load(); document.fonts.add(f); ok.push(fam); return; } catch {}
      }
    }));
    await document.fonts.ready;
    return ok;
  }
}
