// plates.js - generated plates in the locked edit (lane A; shared). Stage 1 has no plates: every call returns null and
// the shot renders its previs (the scene's own layers). Stage 2 drops a take in and the same shot switches to it.
//
// On disk (gitignored; written by the stage 2 tools when a take is approved):
//   out/plates/<P>/plate.json   { take: 'take03', fps: 24, frames: 144, start_number: 1, pattern: 'frames/%05d.jpg',
//                                 matte: 'matte/%05d.png' | null, track: 'track.json' | null, w, h }
//   out/plates/<P>/<take>/frames/00001.jpg ...  (decoded with ffmpeg: Chromium here has no H.264 decoder)
//   out/plates/<P>/<take>/track.json            { fps, frames: [{ f, landmarks: [[x, y], ...] (plate px) } ...], w, h }
// Timing: plate time = gen.use[0] + (t - tGen), tGen = shot.t1 - (use[1] - use[0]) (the plate covers the end of its shot:
// all of it for full GEN shots, the last 2.47 s of S15 and 1.36 s of S54). Plate frame = round(plate time * fps).
//
//   const plates = new Plates(ctx)
//   await plates.load(id)         -> info | null  (reads plate.json once; core calls this for scene.needs.plates)
//   plates.has(id) -> bool        plates.info(id) -> info | null
//   plates.time(id, t) -> plate seconds | null      plates.index(id, t) -> 0-based frame index | null
//   await plates.prepare(id, t)   decodes the frame (and matte) for t; the core awaits this before scene.frame()
//   plates.frame(id, t) -> THREE.Texture | null     (sRGB; valid after prepare)
//   plates.matte(id, t) -> THREE.Texture | null
//   plates.track(id, t) -> { landmarks: [[x, y] ...] (0..1 of the plate frame), w, h } | null   (for the projection comp)
import * as THREE from 'three';

const pad = (n, w = 5) => String(n).padStart(w, '0');

export class Plates {
  constructor(ctx) { this.ctx = ctx; this.infos = new Map(); this.frames = new Map(); this.tracks = new Map(); this.keep = 6; }
  _shotFor(id) { return this.ctx.tl.shots.find(s => s.gen && s.gen.plate === id) || null; }
  async load(id) {
    if (this.infos.has(id)) return this.infos.get(id);
    const url = `/out/plates/${id}/plate.json`;
    let info = null;
    if (await this.ctx.assets.exists(url)) {
      try { info = { id, fps: 24, start_number: 1, pattern: 'frames/%05d.jpg', ...(await this.ctx.assets.json(url)) }; } catch { info = null; }
      if (info && info.track) {
        try { this.tracks.set(id, await this.ctx.assets.json(`/out/plates/${id}/${info.take}/${info.track}`)); } catch {}
      }
    }
    this.infos.set(id, info);
    return info;
  }
  has(id) { return !!this.infos.get(id); }
  info(id) { return this.infos.get(id) || null; }
  time(id, t) {
    const shot = this._shotFor(id); if (!shot) return null;
    const use = shot.gen.use || [0, shot.t1 - shot.t0];
    return use[0] + (t - (shot.t1 - (use[1] - use[0])));
  }
  index(id, t) {
    const info = this.info(id), pt = this.time(id, t);
    if (!info || pt === null) return null;
    return Math.max(0, Math.min((info.frames || 1e9) - 1, Math.round(pt * info.fps)));
  }
  _url(info, pattern, i) { return `/out/plates/${info.id}/${info.take}/${pattern.replace(/%0(\d)d/, (_, w) => pad(i + info.start_number, +w))}`; }
  async prepare(id, t) {
    const info = this.info(id); if (!info) return;
    const i = this.index(id, t);
    const want = [['f', info.pattern]].concat(info.matte ? [['m', info.matte]] : []);
    for (const [kind, pattern] of want) {
      const key = `${id}:${kind}:${i}`;
      if (this.frames.has(key)) continue;
      const tex = await this.ctx.assets.texture(this._url(info, pattern, i), { srgb: kind === 'f', mipmaps: false });
      this.frames.set(key, tex);
      if (this.frames.size > this.keep * 2) {           // bounded: plates are long JPEG sequences
        const old = this.frames.keys().next().value; this.frames.get(old).dispose(); this.frames.delete(old);
      }
    }
  }
  frame(id, t) { const i = this.index(id, t); return i === null ? null : this.frames.get(`${id}:f:${i}`) || null; }
  matte(id, t) { const i = this.index(id, t); return i === null ? null : this.frames.get(`${id}:m:${i}`) || null; }
  track(id, t) {
    const tr = this.tracks.get(id), i = this.index(id, t);
    if (!tr || i === null) return null;
    const fr = tr.frames.find(x => x.f === i) || null;
    return fr ? { landmarks: fr.landmarks.map(([x, y]) => [x / tr.w, y / tr.h]), w: tr.w, h: tr.h } : null;
  }
}

// A plate as a render layer: a full-frame quad (cover-fit into the window rect) for the core's layer stack.
export function plateLayer(tex, rect, over = false) {
  const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshBasicMaterial({ map: tex, depthTest: false, depthWrite: false, toneMapped: false }));
  const img = tex.image || { width: 16, height: 9 }, ar = img.width / img.height, rar = rect.w / rect.h;
  const sx = rect.w / 1920 * (ar > rar ? ar / rar : 1), sy = rect.h / 1080 * (ar > rar ? 1 : rar / ar);
  q.scale.set(sx, sy, 1); q.position.set(((rect.x + rect.w / 2) / 1920) * 2 - 1, 1 - ((rect.y + rect.h / 2) / 1080) * 2, 0);
  const scene = new THREE.Scene(); scene.add(q);
  return { scene, camera: new THREE.OrthographicCamera(-1, 1, 1, -1, -1, 1), over, dispose: () => { q.geometry.dispose(); q.material.dispose(); } };
}
