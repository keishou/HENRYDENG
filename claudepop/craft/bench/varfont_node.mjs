// Verifies that variable-font glyph OUTLINES can be extracted at arbitrary axis values (for canvas Path2D / SDF / deformation).
import * as fontkit from 'fontkit';
import opentype from 'opentype.js';
import { readFileSync } from 'node:fs';
const file = 'fonts/RobotoFlex.ttf';
const f = fontkit.openSync(file);
console.log('fontkit axes:', Object.entries(f.variationAxes).map(([k, v]) => `${k}:${v.min}..${v.max}`).join(' '));
for (const coords of [{ wght: 100, wdth: 25 }, { wght: 1000, wdth: 25 }, { wght: 400, wdth: 100 }, { wght: 1000, wdth: 151, XTRA: 603 }]) {
  const t0 = performance.now();
  const v = f.getVariation(coords);
  const run = v.layout('P(DOOM)');
  let adv = 0, cmds = 0; for (let i = 0; i < run.glyphs.length; i++) { adv += run.positions[i].xAdvance; cmds += run.glyphs[i].path.commands.length; }
  const svg = run.glyphs[1].path.toSVG().slice(0, 60);
  console.log(JSON.stringify(coords), 'advance(units)=', adv, 'pathCmds=', cmds, 'ms=', (performance.now() - t0).toFixed(1), svg);
}
// opentype.js 2.x
const buf = readFileSync(file);
const of = opentype.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
console.log('opentype.js axes:', of.tables.fvar?.axes.map(a => `${a.tag}:${a.minValue}..${a.maxValue}`).join(' '));
for (const c of [{ wght: 100, wdth: 25 }, { wght: 1000, wdth: 151 }]) {
  try {
    of.variation.set(c);
    const p = of.getPath('P(DOOM)', 0, 0, 1000);
    const bb = p.getBoundingBox();
    console.log('opentype', JSON.stringify(c), 'bbox w=', (bb.x2 - bb.x1).toFixed(0), 'cmds=', p.commands.length);
  } catch (e) { console.log('opentype variation error', e.message); }
}
