// STUB - owned by lane C, replace. (Frozen on day 0 by lane A: keep the class, constructor, height(), update() and mesh.)
//
// liquid.js - the developer in the tray (BIBLE 4.8): height field = rocking wave (1.5 mm, wavelength 0.3 m, one crossing
// per 2 bars) + drop rings (0.25 m/s, decay 1.2 s) + surges (S09) + agitation tilt (S26) + pressure ring (S20).
// Shading: print UV refracted by grad(h) * 0.8, Fresnel reflection of the safelight rectangle, transmission 0.96.
//
//   const liq = new Liquid(ctx, { width = 0.34, depth = 0.42, res = 128 })
//   liq.height(x, z, t) -> metres (closed form; pure)
//   liq.update(t, { drops: [{ t, x, z }], surge: { t, dir } | null, tilt: radians, ring: { t, x, z } | null })
//   liq.mesh    THREE.Mesh of the liquid surface, local to the tray (surface at y 0)
import * as THREE from 'three';

export class Liquid {
  constructor(ctx, { width = 0.34, depth = 0.42, res = 128 } = {}) {
    this.ctx = ctx; this.width = width; this.depth = depth;
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(width, depth, 1, 1).rotateX(-Math.PI / 2),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.0, depthWrite: false }));
    this.state = {};
  }
  height(x, z, t) { return 0.0015 * Math.sin((z / 0.3 + t / (2 * 1.818182)) * Math.PI * 2); }
  update(t, events = {}) { this.state = { t, ...events }; }
}
