// Offline variable-font outline cache: per-glyph SVG path data at exact axis values (fontkit), consumed in-page as Path2D.
// Why: canvas can only drive wght (numeric) and wdth (9 keywords); fontkit gives every axis (wdth 25, XTRA, YTUC, opsz...)
// and per-glyph paths (per-letter animation, tearing, SDF). NOTE: Chrome auto-applies opsz = font px size (clamped),
// so pass opsz explicitly to match native rendering. opentype.js 2.0.0 interpolated Roboto Flex incorrectly in our test.
//   node gen_type.mjs  -> type_cache.json
import * as fontkit from 'fontkit'; import { writeFileSync } from 'node:fs';
const fonts = { RF: fontkit.openSync('fonts/RobotoFlex.ttf') };
function glyphs(font, str, axes, size) {
  const v = font.getVariation(axes), run = v.layout(str), s = size / v.unitsPerEm; let x = 0; const out = [];
  run.glyphs.forEach((g, i) => { out.push({ ch: str[i] ?? '', x: +x.toFixed(2), d: g.path.scale(s, -s).toSVG() }); x += run.positions[i].xAdvance * s; });
  return { adv: +x.toFixed(2), glyphs: out };
}
const jobs = {
  hero_pdoom: ['RF', 'P(DOOM)', { wght: 1000, wdth: 25, opsz: 144, YTUC: 760 }, 400],
  hero_pdoom_light: ['RF', 'P(DOOM)', { wght: 100, wdth: 151, opsz: 144 }, 700],
};
const cache = {}; for (const [k, [f, s, a, size]] of Object.entries(jobs)) { cache[k] = { axes: a, size, ...glyphs(fonts[f], s, a, size) }; console.log(k, 'advance', cache[k].adv); }
writeFileSync('type_cache.json', JSON.stringify(cache));
