// paperkit.js: small, dependency-free helpers for a premium paper / risograph look on Canvas2D + WebGL2.
// Written for CPU-only headless Chromium (SwiftShader). Everything is deterministic (seeded) so frames re-render identically.
// Used by bench.html (timings) and demo.html (test card). Plain script: exposes window.PK.
(function () {
  'use strict';
  // ---------- deterministic randomness ----------
  function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function hash2(x, y, s) { let h = (x * 374761393 + y * 668265263 + s * 2147483647) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
  function vnoise(x, y, s) { // value noise, smoothstep-interpolated
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const a = hash2(xi, yi, s), b = hash2(xi + 1, yi, s), c = hash2(xi, yi + 1, s), d = hash2(xi + 1, yi + 1, s);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  function fbm(x, y, s, oct = 4) { let f = 0, amp = 0.5, fr = 1; for (let i = 0; i < oct; i++) { f += amp * vnoise(x * fr, y * fr, s + i * 17); fr *= 2.03; amp *= 0.5; } return f; }

  // ---------- paper texture (generated ONCE, then reused every frame as a multiply layer) ----------
  // Returns a canvas: mid-grey-ish (around 1.0 = white) mottling + grain + fibres, designed for 'multiply' over art,
  // plus a second canvas `tooth` (grain only) that the riso shader uses to break up ink.
  function makePaper(w, h, seed = 7, opt = {}) {
    const base = opt.base || [244, 238, 226];            // warm cream
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    const x = c.getContext('2d', { willReadFrequently: true });
    const img = x.createImageData(w, h), d = img.data;
    const tooth = new Uint8ClampedArray(w * h);
    for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
      const m = fbm(i / 420, j / 420, seed, 3);            // large cloudy mottling ("formation" of the sheet)
      const g = hash2(i, j, seed + 99);                    // per-pixel tooth
      const g2 = vnoise(i / 2.3, j / 2.3, seed + 5);       // slightly larger grain clumps
      const k = 1 - 0.05 * (m - 0.5) * 2 - 0.035 * (g - 0.5) - 0.05 * (g2 - 0.5);
      const o = (j * w + i) * 4;
      d[o] = base[0] * k; d[o + 1] = base[1] * k; d[o + 2] = base[2] * k; d[o + 3] = 255;
      tooth[j * w + i] = 255 * (0.55 * g + 0.45 * g2);
    }
    x.putImageData(img, 0, 0);
    // fibres: short curved hairlines, some lighter (raised), some darker (embedded)
    const r = mulberry32(seed * 31 + 1);
    const n = Math.round(w * h / 900);
    x.lineCap = 'round';
    for (let i = 0; i < n; i++) {
      const px = r() * w, py = r() * h, len = 6 + r() * 26, a = r() * Math.PI * 2, bend = (r() - 0.5) * 0.6;
      const dark = r() < 0.55;
      x.strokeStyle = dark ? `rgba(120,100,70,${0.05 + r() * 0.08})` : `rgba(255,255,250,${0.25 + r() * 0.35})`;
      x.lineWidth = 0.5 + r() * 0.9;
      x.beginPath(); x.moveTo(px, py);
      x.quadraticCurveTo(px + Math.cos(a + bend) * len * 0.5, py + Math.sin(a + bend) * len * 0.5, px + Math.cos(a) * len, py + Math.sin(a) * len);
      x.stroke();
    }
    const t = document.createElement('canvas'); t.width = w; t.height = h;
    const tx = t.getContext('2d'); const ti = tx.createImageData(w, h);
    for (let i = 0; i < w * h; i++) { ti.data[i * 4] = ti.data[i * 4 + 1] = ti.data[i * 4 + 2] = tooth[i]; ti.data[i * 4 + 3] = 255; }
    tx.putImageData(ti, 0, 0);
    return { paper: c, tooth: t };
  }

  // ---------- torn / cut paper shapes ----------
  // Midpoint displacement along each edge; `amp` in px; returns a dense polygon. Deterministic via seed.
  function tearPolygon(pts, seed = 1, amp = 6, minSeg = 3) {
    const r = mulberry32(seed); const out = [];
    function sub(a, b, am, depth) {
      const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
      if (L < minSeg || depth > 12) { out.push(b); return; }
      const nx = -dy / L, ny = dx / L, off = (r() - 0.5) * 2 * am;
      const m = [(a[0] + b[0]) / 2 + nx * off, (a[1] + b[1]) / 2 + ny * off];
      sub(a, m, am * 0.55, depth + 1); sub(m, b, am * 0.55, depth + 1);
    }
    for (let i = 0; i < pts.length; i++) { const a = pts[i], b = pts[(i + 1) % pts.length]; if (i === 0) out.push(a); sub(a, b, amp, 0); }
    return out;
  }
  function pathOf(ctx, poly, dx = 0, dy = 0) { ctx.beginPath(); ctx.moveTo(poly[0][0] + dx, poly[0][1] + dy); for (let i = 1; i < poly.length; i++) ctx.lineTo(poly[i][0] + dx, poly[i][1] + dy); ctx.closePath(); }
  // Bake a cut-out into a sprite ONCE: soft contact shadow + white torn core rim + coloured face + subtle grain.
  // Per frame you only drawImage() the sprite with a transform (cheap on CPU raster).
  function bakeCutout(poly, fill, opt = {}) {
    const pad = opt.pad ?? 40, sh = opt.shadow ?? 14;
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; for (const [x, y] of poly) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
    const w = Math.ceil(x1 - x0 + pad * 2), h = Math.ceil(y1 - y0 + pad * 2);
    const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d');
    const P = poly.map(([a, b]) => [a - x0 + pad, b - y0 + pad]);
    // shadow: blurred silhouette, offset down-right (paper lifted ~2 mm off the table)
    x.save(); x.filter = `blur(${sh * 0.6}px)`; x.fillStyle = 'rgba(40,25,10,0.35)'; pathOf(x, P, sh * 0.35, sh * 0.55); x.fill(); x.restore();
    // torn white core (the fibrous paper interior exposed at a tear), slightly larger than the face
    if (opt.rim !== false) { x.fillStyle = opt.rimColor || '#fbf7ee'; pathOf(x, tearPolygon(P, (opt.seed || 1) + 7, 2.5, 2)); x.fill(); }
    // coloured face, inset a touch so the rim shows unevenly
    x.fillStyle = fill; x.save(); x.translate(w / 2, h / 2); x.scale(0.985, 0.985); x.translate(-w / 2, -h / 2); pathOf(x, P); x.fill(); x.restore();
    return { canvas: c, ox: x0 - pad, oy: y0 - pad };
  }

  // ---------- stop-motion "boil" ----------
  // Drawings change on twos/threes: key all hand-jitter noise on the drawing index, not on t.
  const boilIndex = (t, drawFps = 12, cycle = 0) => { const k = Math.floor(t * drawFps + 1e-6); return cycle ? k % cycle : k; };
  function jitterPoly(poly, seed, amp) { const r = mulberry32(seed); return poly.map(([x, y]) => [x + (r() - 0.5) * 2 * amp, y + (r() - 0.5) * 2 * amp]); }
  // Hand-inked line: variable width ribbon from a centreline, tapered ends, jitter per boil frame.
  function inkStroke(ctx, pts, seed, width = 4, jitter = 1.2) {
    const r = mulberry32(seed); const L = [], R = [];
    for (let i = 0; i < pts.length; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l;
      const u = i / (pts.length - 1), taper = Math.sin(Math.PI * Math.min(1, u * 1.15)) ** 0.6;
      const wv = width * (0.55 + 0.45 * taper) * (0.85 + 0.3 * r());
      const jx = (r() - 0.5) * jitter, jy = (r() - 0.5) * jitter;
      L.push([pts[i][0] + nx * wv / 2 + jx, pts[i][1] + ny * wv / 2 + jy]); R.push([pts[i][0] - nx * wv / 2 + jx, pts[i][1] - ny * wv / 2 + jy]);
    }
    ctx.beginPath(); ctx.moveTo(L[0][0], L[0][1]);
    for (let i = 1; i < L.length; i++) ctx.lineTo(L[i][0], L[i][1]);
    for (let i = R.length - 1; i >= 0; i--) ctx.lineTo(R[i][0], R[i][1]);
    ctx.closePath(); ctx.fill();
  }

  // ---------- WebGL2 risograph compositor ----------
  // Inputs: up to 4 "ink" layers as canvases (alpha = ink coverage), paper + tooth canvases (uploaded once).
  // Per layer: misregistration offset (px), halftone screen angle + cell size, ink colour, density.
  // Solid coverage (>0.92) prints solid (with tooth speckle); mid-tones become rotated AM dots; ink edges get a
  // noise-thresholded 'bleed'. Layers overprint multiplicatively (like transparent riso inks).
  const VS = `#version 300 es
  in vec2 p; out vec2 uv; void main(){ uv = p*0.5+0.5; gl_Position = vec4(p,0.,1.); }`;
  const FS = `#version 300 es
  precision highp float; in vec2 uv; out vec4 o;
  uniform sampler2D paper, tooth, ink0, ink1, ink2, ink3;
  uniform vec2 res; uniform int n;
  uniform vec3 col[4]; uniform vec2 off[4]; uniform float ang[4], cell[4], dens[4];
  float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1,311.7)))*43758.5453); }
  float layer(sampler2D s, int i, vec2 px){
    vec2 q = (px + off[i]) / res;   // canvas uploads are top-row-first, px is top-left origin
    float c = texture(s, q).a;
    float t = texture(tooth, vec2(uv.x, 1.0-uv.y)).r;
    // ink bleed / starved edges: threshold coverage against paper tooth
    float solid = smoothstep(0.5, 0.62, c + (t - 0.5) * 0.35);
    // AM halftone for mid-tones
    float a = ang[i]; mat2 R = mat2(cos(a), -sin(a), sin(a), cos(a));
    vec2 g = R * px / cell[i]; vec2 f = fract(g) - 0.5;
    float rad = sqrt(clamp(c, 0.0, 1.0)) * 0.62;
    float dotm = 1.0 - smoothstep(rad - 0.08, rad + 0.08, length(f) + (t - 0.5) * 0.12);
    float m = c > 0.92 ? solid : mix(dotm * step(0.04, c), solid, smoothstep(0.8, 0.92, c));
    // starved ink: tooth pokes through solids
    m *= 1.0 - 0.28 * smoothstep(0.72, 0.95, t);
    return m * dens[i];
  }
  void main(){
    vec2 px = vec2(uv.x, 1.0 - uv.y) * res;
    vec3 base = texture(paper, vec2(uv.x, 1.0-uv.y)).rgb;
    vec3 acc = base;
    if (n > 0) acc *= mix(vec3(1.0), col[0], layer(ink0, 0, px));
    if (n > 1) acc *= mix(vec3(1.0), col[1], layer(ink1, 1, px));
    if (n > 2) acc *= mix(vec3(1.0), col[2], layer(ink2, 2, px));
    if (n > 3) acc *= mix(vec3(1.0), col[3], layer(ink3, 3, px));
    o = vec4(acc, 1.0);
  }`;
  class RisoGL {
    constructor(w, h) {
      this.w = w; this.h = h; const c = this.canvas = document.createElement('canvas'); c.width = w; c.height = h;
      const gl = this.gl = c.getContext('webgl2', { preserveDrawingBuffer: true, antialias: false, premultipliedAlpha: false });
      if (!gl) throw new Error('no webgl2');
      const sh = (t, s) => { const o = gl.createShader(t); gl.shaderSource(o, s); gl.compileShader(o); if (!gl.getShaderParameter(o, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(o)); return o; };
      const pr = this.pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
      if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(pr));
      gl.useProgram(pr);
      const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
      const loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      this.tex = {}; ['paper', 'tooth', 'ink0', 'ink1', 'ink2', 'ink3'].forEach((k, i) => { const t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 0]));
        gl.uniform1i(gl.getUniformLocation(pr, k), i); this.tex[k] = { t, unit: i }; });
      gl.uniform2f(gl.getUniformLocation(pr, 'res'), w, h); gl.viewport(0, 0, w, h);
      this.u = n => gl.getUniformLocation(pr, n);
    }
    upload(name, canvas) { const gl = this.gl, T = this.tex[name]; gl.activeTexture(gl.TEXTURE0 + T.unit); gl.bindTexture(gl.TEXTURE_2D, T.t); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, canvas); }
    setPaper(paper, tooth) { this.upload('paper', paper); this.upload('tooth', tooth); }
    // layers: [{canvas, color:[r,g,b] 0..1, off:[dx,dy] px, ang: radians, cell: px, dens: 0..1}]
    render(layers) {
      const gl = this.gl;
      layers.forEach((L, i) => this.upload('ink' + i, L.canvas));
      const col = [], off = [], ang = [], cell = [], dens = [];
      for (let i = 0; i < 4; i++) { const L = layers[i] || { color: [1, 1, 1], off: [0, 0], ang: 0, cell: 8, dens: 0 };
        col.push(...L.color); off.push(...L.off); ang.push(L.ang); cell.push(L.cell); dens.push(L.dens ?? 1); }
      gl.uniform1i(this.u('n'), layers.length); gl.uniform3fv(this.u('col'), col); gl.uniform2fv(this.u('off'), off);
      gl.uniform1fv(this.u('ang'), ang); gl.uniform1fv(this.u('cell'), cell); gl.uniform1fv(this.u('dens'), dens);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      return this.canvas;
    }
  }

  // ---------- Riso ink palette (approximate sRGB of common RISO ink swatches; verify against the printer's chart) ----------
  const INK = {
    fluoPink: [1.0, 0.28, 0.69], blue: [0.0, 0.47, 0.75], yellow: [1.0, 0.91, 0.0], teal: [0.0, 0.51, 0.54],
    orange: [1.0, 0.42, 0.18], black: [0.0, 0.0, 0.0], federalBlue: [0.24, 0.33, 0.62], red: [1.0, 0.25, 0.25],
  };
  const hex = c => `rgb(${Math.round(c[0] * 255)},${Math.round(c[1] * 255)},${Math.round(c[2] * 255)})`;

  window.PK = { mulberry32, hash2, vnoise, fbm, makePaper, tearPolygon, pathOf, bakeCutout, boilIndex, jitterPoly, inkStroke, RisoGL, INK, hex };
})();
