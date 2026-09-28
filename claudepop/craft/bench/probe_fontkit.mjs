// Renders fontkit variable outlines next to Chrome's native variable-font rendering, to see which outline source is trustworthy.
import * as fontkit from 'fontkit'; import puppeteer from 'puppeteer-core'; import { pathToFileURL } from 'node:url'; import { writeFileSync } from 'node:fs';
const f = fontkit.openSync('fonts/RobotoFlex.ttf');
function textPath(str, axes, size) { const v = f.getVariation(axes); const run = v.layout(str); const s = size / v.unitsPerEm; let x = 0, d = '';
  run.glyphs.forEach((g, i) => { const p = g.path.scale(s, -s).translate(x, 0); d += p.toSVG() + ' '; x += run.positions[i].xAdvance * s; }); return { d, adv: x }; }
const rows = [
  ['fontkit wght1000 wdth50', textPath('P(DOOM)', { wght: 1000, wdth: 50 }, 180)],
  ['fontkit wght1000 wdth25', textPath('P(DOOM)', { wght: 1000, wdth: 25 }, 180)],
  ['fontkit wght1000 wdth25 YTUC760 opsz144', textPath('P(DOOM)', { wght: 1000, wdth: 25, YTUC: 760, opsz: 144 }, 180)],
  ['fontkit wght100 wdth151', textPath('P(DOOM)', { wght: 100, wdth: 151 }, 180)],
];
const b = await puppeteer.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', headless: true, args: ['--allow-file-access-from-files', '--no-sandbox', '--disable-accelerated-2d-canvas'] });
const p = await b.newPage(); await p.goto(pathToFileURL(process.cwd() + '/probe_outlines.html').href);
const u = await p.evaluate(async rows => { await document.fonts.load('1000 100px RF'); const c = document.getElementById('c'); c.height = 1300; const x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, 1800, 1300);
  const lab = (t, y) => { x.font = '22px sans-serif'; x.fontStretch = 'normal'; x.fillStyle = '#c00'; x.fillText(t, 10, y); x.fillStyle = '#000'; };
  lab('native canvas 1000 + fontStretch ultra-condensed (50%)', 30); x.font = '1000 180px RF'; x.fontStretch = 'ultra-condensed'; x.fillText('P(DOOM)', 10, 200); x.fontStretch = 'normal';
  rows.forEach(([t, r], i) => { const y = 460 + i * 250; lab(t + '  (advance ' + Math.round(r.adv) + 'px)', y - 200); x.save(); x.translate(10, y); x.fill(new Path2D(r.d)); x.restore(); });
  return c.toDataURL('image/png'); }, rows);
writeFileSync('probe_fontkit.png', Buffer.from(u.split(',')[1], 'base64')); await b.close(); console.log('ok');
