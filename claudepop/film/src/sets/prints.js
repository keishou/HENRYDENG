// STUB - owned by lane E, replace. (Frozen on day 0 by lane A: keep the class, constructor, layout(), set(), update()
// and object; lanes D (line prints) and E (the hall audience) build on it.)
//
// prints.js - many hanging prints as instanced quads with curl segments; real paperclip meshes within 2 m of the camera,
// textured impostors beyond (never instance real clip meshes in bulk: BIBLE 9.6).
//
//   const prints = new Prints(ctx, { max = 400, atlas = null, size = [0.56, 0.72] })
//       atlas: { texture, cols, rows } (cells hold print images) | null
//   prints.layout(kind, opts) -> ids [int]
//       kind 'rows'  { z0, dz, rows, xs: [[x0, x1], ...], y, perLine }   drying lines across the hall (BIBLE 4.8 HALL)
//            'line'  { x0, x1, y, z, count }                              one wire
//            'grid'  { x0, y0, dx, dy, cols, rows, z }                    a wall
//   prints.set(id, { tex (atlas cell index), density 0..1, gloss, sway, turn (rad about the clip axis), clip: bool,
//                    fall: { t0, seed } | null, capture: { t, cell } | null })
//   prints.update(t)      writes instance transforms / attributes for time t (pure function of t and the set() state;
//                         call set() for every print you change at the start of frame(), then update(t))
//   prints.object         THREE.Object3D to add to a scene
import * as THREE from 'three';

export class Prints {
  constructor(ctx, { max = 400, atlas = null, size = [0.56, 0.72] } = {}) {
    this.ctx = ctx; this.max = max; this.atlas = atlas; this.size = size;
    this.mesh = new THREE.InstancedMesh(new THREE.PlaneGeometry(size[0], size[1]),
      new THREE.MeshBasicMaterial({ color: 0xf2efe8, side: THREE.DoubleSide }), max);
    this.mesh.count = 0; this.mesh.frustumCulled = false;
    this.object = new THREE.Group(); this.object.add(this.mesh);
    this.items = [];
  }
  layout(kind, o = {}) {
    const ids = [], add = (x, y, z) => { if (this.items.length >= this.max) return; ids.push(this.items.length); this.items.push({ x, y, z, props: {} }); };
    if (kind === 'rows') {
      const { z0 = -1.5, dz = -1.5, rows = 10, xs = [[-5.4, -1.4], [1.4, 5.4]], y = 1.75, perLine = 5 } = o;
      for (let r = 0; r < rows; r++) for (const [x0, x1] of xs) for (let i = 0; i < perLine; i++) add(x0 + (x1 - x0) * (i + 0.5) / perLine, y - this.size[1] / 2, z0 + r * dz);
    } else if (kind === 'line') {
      const { x0 = -1, x1 = 1, y = 1.9, z = 0, count = 5 } = o;
      for (let i = 0; i < count; i++) add(x0 + (x1 - x0) * (i + 0.5) / count, y - this.size[1] / 2, z);
    } else if (kind === 'grid') {
      const { x0 = 0, y0 = 0, dx = 0.7, dy = 0.9, cols = 4, rows = 3, z = 0 } = o;
      for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) add(x0 + c * dx, y0 + r * dy, z);
    }
    return ids;
  }
  set(id, props) { Object.assign(this.items[id].props, props); }
  update(t) {
    const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s = new THREE.Vector3(1, 1, 1), p = new THREE.Vector3();
    this.items.forEach((it, i) => { e.set(0, it.props.turn || 0, 0); q.setFromEuler(e); p.set(it.x, it.y, it.z); m.compose(p, q, s); this.mesh.setMatrixAt(i, m); });
    this.mesh.count = this.items.length; this.mesh.instanceMatrix.needsUpdate = true;
  }
}
