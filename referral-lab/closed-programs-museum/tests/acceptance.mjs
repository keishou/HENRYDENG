#!/usr/bin/env node
// Executable subset of the brief's acceptance tests (AT-01 … AT-16) against the reference build,
// plus a negative control: a mutated page must FAIL the same checks.
//   node reference/build.mjs && node reference/build.mjs --fixtures && node tests/acceptance.mjs
// Uses the preinstalled Playwright (PLAYWRIGHT_BROWSERS_PATH) — no downloads.
import { createServer } from 'node:http';
import { readFileSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { compile, scan, loadLexicon } from './lexicon-scan.mjs';

const require = createRequire(import.meta.url);
let playwright;
try { playwright = require('playwright'); } catch { playwright = createRequire('/opt/node22/lib/node_modules/')('playwright'); }
const { chromium } = playwright;

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '..');
const brief = JSON.parse(readFileSync(join(root, 'brief.json'), 'utf8'));
const B = brief.compose_closed_programs_museum;
const DC = B.data_contract;
const compiled = compile(loadLexicon());
const shotDir = resolve(process.env.MUSEUM_SHOT_DIR || join(root, 'tests', 'screenshots'));
mkdirSync(shotDir, { recursive: true });

const HONESTY = '点击 ≠ 收入 / Clicks ≠ income';
const NIA = '仅供参考，不构成投资建议 / For information only; not investment advice';
const CLIENT_DATE = '2026-09-23';

// ---------------------------------------------------------------- static server
const pages = {
  '/lab/museum': join(root, 'dist', 'lab', 'museum', 'index.html'),
  '/fixtures/lab/museum': join(root, 'dist-fixtures', 'lab', 'museum', 'index.html'),
};
let mutantHtml = null;
const server = createServer((req, res) => {
  const path = req.url.split('?')[0].replace(/\/$/, '');
  if (path === '/mutant/lab/museum' && mutantHtml) { res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); return res.end(mutantHtml); }
  const file = pages[path];
  if (file && existsSync(file)) { res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); return res.end(readFileSync(file)); }
  res.writeHead(404, { 'content-type': 'text/plain' }); res.end('not found');
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;

// ---------------------------------------------------------------- harness
const results = [];
function record(id, name, fn) {
  return fn().then(
    (detail) => results.push({ id, name, ok: true, detail }),
    (e) => results.push({ id, name, ok: false, detail: e.message }),
  );
}
const assert = (c, m) => { if (!c) throw new Error(m); };

const browser = await chromium.launch();
async function open(path, { width = 1440, height = 900, date = CLIENT_DATE, js = true, reducedMotion = 'no-preference' } = {}) {
  const context = await browser.newContext({ viewport: { width, height }, javaScriptEnabled: js, reducedMotion });
  await context.route((u) => !u.href.startsWith(ORIGIN), (route) => route.fulfill({ status: 200, contentType: 'text/html', body: '<p>external stub</p>' }));
  if (date) await context.addInitScript((d) => { window.__MUSEUM_CLIENT_DATE__ = d; }, date);
  const page = await context.newPage();
  await page.goto(ORIGIN + path, { waitUntil: 'networkidle' });
  if (js) await page.evaluate(() => document.fonts.ready);
  return { context, page };
}

// Shared DOM checks, reused by the negative control ------------------------------
async function ctaCounts(page) {
  return page.evaluate(() => ({
    exact: document.querySelectorAll('[data-museum-row] [data-cta="join"], [data-museum-row] [data-cta="apply"]').length,
    controls: document.querySelectorAll('[data-museum-row] :is([data-cta], button, input, select, textarea, form, [role="button"])').length,
    oneLink: [...document.querySelectorAll('[data-museum-row]')].every((r) => r.querySelectorAll('a').length === 1 && r.querySelector('a[data-source-link]')),
  }));
}
async function domLexiconHits(page) {
  const d = await page.evaluate(() => {
    const controls = [...document.querySelectorAll('a, button, input, select, textarea, summary, [role]')].map((el) =>
      [el.innerText || '', el.getAttribute('aria-label') || '', el.getAttribute('placeholder') || '', el.name || '', el.id || ''].join(' '));
    const attrs = [...document.querySelectorAll('[aria-label], [title], [placeholder], [alt]')].map((el) =>
      ['aria-label', 'title', 'placeholder', 'alt'].map((a) => el.getAttribute(a) || '').join(' '));
    return {
      text: document.body.innerText + '\n' + attrs.join('\n'),
      controls,
      hrefs: [...document.querySelectorAll('a[href], area[href], form[action]')].map((a) => a.href || a.action),
      rowsNotCurrent: [...document.querySelectorAll('[data-museum-row]:not([data-freshness="current"])')].map((r) => r.innerText),
    };
  });
  const hits = [
    ...scan(d.text, 'rendered_text', compiled),
    ...d.controls.flatMap((c) => scan(c, 'control_names', compiled)),
    ...d.hrefs.flatMap((h) => scan(h, 'hrefs', compiled)),
    ...d.rowsNotCurrent.flatMap((t) => scan(t, 'row_text_not_current', compiled)),
  ];
  return hits;
}
async function honestyVisible(page) {
  return page.evaluate((lit) => {
    const b = document.querySelector('[data-honesty-bar]');
    if (!b) return 'missing';
    const cs = getComputedStyle(b);
    if (!b.innerText.includes(lit)) return 'literal missing';
    if (b.closest('[hidden], [aria-hidden="true"], details:not([open])')) return 'inside hidden container';
    if (cs.display === 'none' || cs.visibility !== 'visible' || cs.opacity !== '1' || parseFloat(cs.fontSize) < 13) return 'weakened';
    const r = b.getBoundingClientRect();
    if (!(r.bottom > 0 && r.top < innerHeight && r.height > 0)) return 'not in viewport';
    return 'ok';
  }, HONESTY);
}

// ---------------------------------------------------------------- tests
await record('AT-01', 'screenshots 1440 / 360, fields visible, no CTA', async () => {
  const out = [];
  for (const width of [1440, 360]) {
    const { context, page } = await open('/lab/museum', { width, height: width === 1440 ? 900 : 740 });
    const shot = join(shotDir, `museum-${width}.png`);
    await page.screenshot({ path: shot, fullPage: true });
    const h1 = await page.locator('h1').innerText();
    assert(h1.replace(/\s+/g, ' ').trim() === '关门博物馆 Closed Programs Museum', `h1 was ${JSON.stringify(h1)}`);
    const vis = await page.evaluate(() => [...document.querySelectorAll('[data-museum-row]')].every((r) =>
      ['status', 'as_of', 'page_read', 'verified_on', 'freshness', 'source', 'why_not_joinable'].every((f) => { const el = r.querySelector(`[data-field="${f}"]`); return el && el.checkVisibility() && el.innerText.trim().length > 0; })));
    assert(vis, `row field not visible at ${width}`);
    assert((await honestyVisible(page)) === 'ok', 'honesty bar');
    assert(await page.locator('footer [data-nia-short]').isVisible(), 'footer line');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `horizontal scroll at ${width}`);
    const btn = await page.getByRole('button', { name: /加入|申请|注册|分享|复制|join|apply|sign ?up|share|copy|code/i }).count();
    const lnk = await page.getByRole('link', { name: /加入|申请|join|apply|sign ?up|share|code/i }).count();
    assert(btn === 0 && lnk === 0, `CTA-like controls: ${btn} buttons, ${lnk} links`);
    out.push(shot);
    await context.close();
  }
  return out.join(', ');
});

await record('AT-02', 'no join/apply CTA in any row (seed + fixtures)', async () => {
  for (const path of ['/lab/museum', '/fixtures/lab/museum']) {
    const { context, page } = await open(path);
    const c = await ctaCounts(page);
    assert(c.exact === 0 && c.controls === 0 && c.oneLink, `${path}: ${JSON.stringify(c)}`);
    await context.close();
  }
  return 'exact=0 controls=0 one-link-per-row on both pages';
});

await record('AT-03', 'required attributes non-empty and values visible', async () => {
  const { context, page } = await open('/lab/museum');
  const rows = await page.$$eval('[data-museum-row]', (rs) => rs.map((r) => ({ attrs: ['data-status', 'data-as-of', 'data-source-url', 'data-why-not-joinable-zh', 'data-why-not-joinable-en'].map((a) => r.getAttribute(a) || ''), src: r.dataset.sourceUrl, asOf: r.dataset.asOf, zh: r.dataset.whyNotJoinableZh, en: r.dataset.whyNotJoinableEn, text: r.innerText })));
  assert(rows.length === DC.seed.length, `rows ${rows.length}`);
  for (const r of rows) {
    assert(r.attrs.every((a) => a.trim()), 'empty attribute');
    for (const v of [r.asOf, r.src.replace('https://', ''), r.zh, r.en, '为何不可加入 / Why not joinable']) assert(r.text.includes(v), `not visible: ${v}`);
    assert(/官方来源 \/ Official source|候选官方来源，尚未读取 \/ Candidate official source, not yet read/.test(r.text), 'source label');
  }
  await context.close();
  return `${rows.length} rows ok`;
});

await record('AT-04', 'source links: https, official host, no query/hash, plain style; rg finds no ref/via/code', async () => {
  const { context, page } = await open('/lab/museum');
  const hosts = Object.values(DC.official_domains).flat();
  const links = await page.$$eval('a[data-source-link]', (as) => as.map((a) => { const u = new URL(a.href); return { protocol: u.protocol, host: u.hostname, search: u.search, hash: u.hash, rel: a.rel, rp: a.referrerPolicy, bg: getComputedStyle(a).backgroundColor, row: a.closest('[data-museum-row]').dataset.sourceUrl, href: a.getAttribute('href') }; }));
  for (const l of links) {
    assert(l.protocol === 'https:' && l.search === '' && l.hash === '' && l.href === l.row, `bad link ${l.href}`);
    assert(l.rel.includes('noopener') && l.rel.includes('noreferrer') && l.rp === 'no-referrer', 'rel/referrerpolicy');
    assert(l.bg === 'rgba(0, 0, 0, 0)', 'source link has a background');
    assert(hosts.includes(l.host), `host ${l.host}`);
  }
  const bad = await page.$$eval('a[href]', (as) => as.filter((a) => { const u = new URL(a.href); return /[?&](ref|via|code)=/i.test(u.search + u.hash) || (u.origin !== location.origin && (u.search || u.hash)); }).length);
  assert(bad === 0, `${bad} links with params`);
  await context.close();
  for (const dir of ['dist', 'dist-fixtures']) {
    for (const re of ['[?&](ref|via|code)=', '[?&](ref|via|code|referral|invite|aff|affiliate|utm_[a-z]+)=']) {
      let code = 0;
      try { execFileSync('rg', ['-n', '--pcre2', re, join(root, dir)], { stdio: 'pipe' }); } catch (e) { code = e.status; }
      assert(code === 1, `rg ${re} in ${dir} exited ${code}`);
    }
  }
  return `${links.length} links ok, rg exit 1`;
});

await record('AT-05', 'unread/stale never current; client date drives freshness', async () => {
  const { context, page } = await open('/fixtures/lab/museum');
  const rows = await page.$$eval('[data-museum-row]', (rs) => rs.map((e) => ({ id: e.dataset.rowId, pr: e.dataset.pageRead, v: e.dataset.verifiedOn, f: e.dataset.freshness, t: e.innerText, ctl: e.querySelectorAll('[data-cta], button, input').length })));
  for (const f of brief.fixtures.filter((x) => x.expect.valid)) {
    const r = rows.find((x) => x.id === f.row.id);
    assert(r, `fixture row ${f.row.id} not rendered`);
    assert(r.f === f.expect.freshness, `${f.id}: ${r.f} ≠ ${f.expect.freshness}`);
    for (const s of f.expect.visible_text_includes || []) assert(r.t.includes(s), `${f.id}: missing ${s}`);
    for (const s of f.expect.visible_text_excludes || []) assert(!r.t.includes(s), `${f.id}: unexpected ${s}`);
    for (const [a, v] of Object.entries(f.expect.attributes || {})) {
      const got = await page.getAttribute(`[data-row-id="${f.row.id}"]`, a);
      assert(got === v, `${f.id}: ${a}=${got} ≠ ${v}`);
    }
    if (f.expect.after_opening_check_record_includes) {
      await page.click(`[data-row-id="${f.row.id}"] summary`);
      const t = await page.locator(`[data-row-id="${f.row.id}"]`).innerText();
      for (const s of f.expect.after_opening_check_record_includes) assert(t.includes(s), `${f.id}: after open missing ${s}`);
    }
    assert(r.ctl === 0, `${f.id}: control in row`);
    if (r.pr !== 'true') assert(r.f === 'unconfirmed' && r.t.includes('待核对 / Unconfirmed'), `${f.id} unread not unconfirmed`);
    if (r.f !== 'current') assert(!r.t.includes('来源已读取，90 天内已核对'), `${f.id} claims current`);
  }
  await context.close();
  const later = await open('/fixtures/lab/museum', { date: '2026-12-31' });
  const f05 = await later.page.getAttribute('[data-row-id="notion-affiliate-fixture-boundary-90"]', 'data-freshness');
  assert(f05 === 'stale', `FX-05 on 2026-12-31 should be stale, was ${f05}`);
  await later.context.close();
  return `${rows.length} fixture rows ok; FX-05 flips to stale on 2026-12-31`;
});

await record('AT-06', 'forbidden lexicon: dist scan, DOM scan, rg with Unicode escapes, gravity containment', async () => {
  execFileSync('node', [join(here, 'lexicon-scan.mjs'), join(root, 'dist')], { stdio: 'pipe' });
  execFileSync('node', [join(here, 'lexicon-scan.mjs'), join(root, 'dist-fixtures')], { stdio: 'pipe' });
  const rgs = [
    ['\\x{4F60}\\x{80FD}\\x{62FF}|\\x{5FC5}\\x{8D5A}|\\x{7A33}\\x{8D5A}|\\x{5012}\\x{8BA1}\\x{65F6}|\\x{9650}\\x{65F6}|\\x{7ACB}\\x{5373}'],
    ['10,?000\\s*[x×]|\\bLIVE\\b|count[ -]?down|confetti|\\bneon\\b|take[ -]?rate|guaranteed'],
  ];
  for (const [re] of rgs) {
    let code = 0;
    try { execFileSync('rg', ['-n', '--pcre2', re, join(root, 'dist')], { stdio: 'pipe' }); } catch (e) { code = e.status; }
    assert(code === 1, `rg ${re} exited ${code}`);
  }
  for (const path of ['/lab/museum', '/fixtures/lab/museum']) {
    const { context, page } = await open(path);
    const hits = await domLexiconHits(page);
    assert(hits.length === 0, `${path}: ${JSON.stringify(hits.slice(0, 5))}`);
    const g = await page.evaluate(() => {
      const nodes = [];
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (w.nextNode()) if (/gravity/i.test(w.currentNode.data)) nodes.push(w.currentNode);
      return {
        contained: nodes.every((n) => n.parentElement.closest('[data-non-affiliation]')),
        n: document.querySelectorAll('[data-non-affiliation]').length,
        brand: document.querySelectorAll('a[href*="gravity" i], img[src*="gravity" i], img[alt*="gravity" i], [class*="gravity" i]').length,
      };
    });
    assert(g.contained && g.n === 2 && g.brand === 0, `gravity ${JSON.stringify(g)}`);
    const claim = await page.$$eval('[data-museum-row]', (rs) => rs.some((r) => /现可加入|仍可加入|目前开放|currently (available|open|accepting)|still (open|available|accepting)|is joinable/i.test(r.innerText)));
    assert(!claim, 'joinable claim in a row');
    await context.close();
  }
  return 'scan 0 hits, rg exit 1, gravity only in [data-non-affiliation]';
});

await record('AT-07', 'required copy on every view', async () => {
  let views = 0;
  const check = async (page, label) => {
    assert((await honestyVisible(page)) === 'ok', `${label}: honesty bar`);
    assert((await page.locator('footer[data-standing-disclosure] [data-nia-short]').innerText()) === NIA, `${label}: NIA`);
    const ft = await page.locator('footer[data-standing-disclosure]').innerText();
    assert(ft.includes(brief.standing_disclosure.zh) && ft.includes(brief.standing_disclosure.en), `${label}: disclosure`);
    const nav = await page.$$eval('nav[data-internal-nav] a', (as) => as.map((a) => [a.innerText.trim(), a.getAttribute('href')]));
    assert(JSON.stringify(nav) === JSON.stringify([['回到 Claim Shredder / Back to Claim Shredder', DC.routes.claim_shredder], ['查看规则板 / View rules board', DC.routes.rules_board]].map(([t, h]) => [t, h])), `${label}: nav ${JSON.stringify(nav)}`);
    const sameOrigin = await page.$$eval('a[href]', (as) => as.filter((a) => new URL(a.href).origin === location.origin).map((a) => a.getAttribute('href')));
    assert(sameOrigin.every((h) => [DC.routes.claim_shredder, DC.routes.rules_board, '#collection', '#disclosure'].includes(h)), `${label}: internal hrefs ${sameOrigin}`);
    views++;
  };
  const states = [
    ['default', async () => {}],
    ['status=closed', (p) => p.check('input[name=status][value=closed]', { force: true })],
    ['status=capped', (p) => p.check('input[name=status][value=capped]', { force: true })],
    ['status=geo', (p) => p.check('input[name=status][value=geo_excluded]', { force: true })],
    ['fresh=current', (p) => p.check('input[name=freshness][value=current]', { force: true })],
    ['fresh=stale', (p) => p.check('input[name=freshness][value=stale]', { force: true })],
    ['fresh=unconfirmed', (p) => p.check('input[name=freshness][value=unconfirmed]', { force: true })],
    ['search zzz', async (p) => { await p.fill('input[type=search]', 'zzz'); assert(await p.locator('[data-empty-state]').isVisible(), 'empty state'); }],
    ['search notion', (p) => p.fill('input[type=search]', 'notion')],
    ['sort name', (p) => p.selectOption('select[name=sort]', 'name_asc')],
    ['details open', (p) => p.click('[data-museum-row] summary')],
  ];
  for (const [w, h] of [[1440, 900], [360, 740]]) for (const [label, act] of states) {
    const { context, page } = await open('/lab/museum', { width: w, height: h });
    await act(page);
    await check(page, `${label}@${w}`);
    await context.close();
  }
  for (const [path, js] of [['/fixtures/lab/museum', true], ['/lab/museum', false]]) {
    const { context, page } = await open(path, { js });
    await check(page, `${path} js=${js}`);
    await context.close();
  }
  return `${views} views`;
});

await record('AT-08', 'request spy: zero requests after load; only same-origin during load', async () => {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await context.addInitScript((d) => { window.__MUSEUM_CLIENT_DATE__ = d; }, CLIENT_DATE);
  await context.route((u) => !u.href.startsWith(ORIGIN), (route) => route.fulfill({ status: 200, contentType: 'text/html', body: 'stub' }));
  const page = await context.newPage();
  const reqs = [];
  context.on('request', (r) => reqs.push(r.url()));
  await page.goto(ORIGIN + '/lab/museum', { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  assert(reqs.every((u) => u.startsWith(ORIGIN)), `third-party at load: ${reqs}`);
  const loadCount = reqs.length;
  reqs.length = 0;
  const url0 = page.url();
  await page.fill('input[type=search]', '币安');
  await page.keyboard.press('Enter');
  await page.fill('input[type=search]', 'zzz');
  await page.keyboard.press('Escape');
  await page.check('input[name=status][value=capped]', { force: true });
  await page.check('input[name=freshness][value=unconfirmed]', { force: true });
  await page.selectOption('select[name=sort]', 'name_asc');
  await page.click('li:not([hidden]) > [data-museum-row] summary');
  await page.click('button[type=reset]');
  await page.hover('a[data-source-link]');
  await page.waitForTimeout(500);
  assert(reqs.length === 0, `requests during interaction: ${reqs}`);
  assert(page.url() === url0, 'URL changed');
  const [popup] = await Promise.all([context.waitForEvent('page'), page.click('a[data-source-link]')]);
  await popup.waitForLoadState('domcontentloaded');
  const expected = await page.getAttribute('a[data-source-link]', 'href');
  assert(popup.url() === expected && new URL(popup.url()).search === '', `popup ${popup.url()}`);
  await context.close();
  let code = 0;
  try { execFileSync('rg', ['-n', '--pcre2', '\\bfetch\\(|XMLHttpRequest|sendBeacon|new WebSocket|EventSource|rel="(prefetch|preconnect|dns-prefetch)"|googletagmanager|google-analytics|gtag\\(|plausible|segment|sentry', join(root, 'dist')], { stdio: 'pipe' }); } catch (e) { code = e.status; }
  assert(code === 1, `network API in bundle (rg exit ${code})`);
  return `load: ${loadCount} same-origin request(s); interactions: 0; popup → ${expected}`;
});

await record('AT-09', 'keyboard-only: tab order, visible focus, not covered by sticky bars', async () => {
  const { context, page } = await open('/lab/museum', { width: 1440, height: 900 });
  const seq = [];
  const expected = ['skip', 'search', 'status', 'freshness', 'sort', 'reset', 'source', 'summary', 'source', 'summary', 'source', 'summary', 'nav', 'nav'];
  for (let i = 0; i < expected.length; i++) {
    await page.keyboard.press('Tab');
    const info = await page.evaluate(() => {
      const a = document.activeElement;
      const target = a.matches('input[type=radio]') ? a.closest('label') : a;
      const cs = getComputedStyle(target);
      const r = target.getBoundingClientRect();
      const hit = document.elementFromPoint(Math.min(innerWidth - 1, Math.max(0, r.left + r.width / 2)), Math.min(innerHeight - 1, Math.max(0, r.top + Math.min(r.height / 2, 10))));
      const kind = a.matches('.skip-link') ? 'skip' : a.matches('input[type=search]') ? 'search' : a.matches('input[name=status]') ? 'status' : a.matches('input[name=freshness]') ? 'freshness' : a.matches('select') ? 'sort' : a.matches('button[type=reset]') ? 'reset' : a.matches('[data-source-link]') ? 'source' : a.matches('summary') ? 'summary' : a.closest('[data-internal-nav]') ? 'nav' : a.tagName;
      return { kind, outline: cs.outlineStyle, ow: parseFloat(cs.outlineWidth), covered: !(hit && (target.contains(hit) || hit.contains(target) || hit === target)) };
    });
    seq.push(info.kind);
    assert(info.outline !== 'none' && info.ow >= 2, `no focus ring on ${info.kind}`);
    assert(!info.covered, `${info.kind} covered by another element`);
  }
  assert(JSON.stringify(seq) === JSON.stringify(expected), `order ${seq}`);
  // no trap: Tab past the last link leaves the page (body) and the next Tab wraps to the skip link
  await page.keyboard.press('Tab');
  await page.keyboard.press('Tab');
  assert(await page.evaluate(() => document.activeElement.matches('.skip-link')), 'focus did not wrap to the skip link');
  // arrow keys move within the status group and filter immediately
  await page.focus('input[name=status][value=all]');
  await page.keyboard.press('ArrowRight');
  const checked = await page.$eval('input[name=status]:checked', (e) => e.value);
  assert(checked === 'closed', `arrow → ${checked}`);
  await context.close();
  return seq.slice(0, expected.length).join(' → ');
});

await record('AT-10', 'reduced motion removes the only transition', async () => {
  const r = await open('/lab/museum', { reducedMotion: 'reduce' });
  await r.page.check('input[name=status][value=capped]', { force: true });
  await r.page.check('input[name=status][value=all]', { force: true });
  const reduce = await r.page.evaluate(() => [...document.querySelectorAll('.cards > li, .record')].every((el) => /^0s(, 0s)*$/.test(getComputedStyle(el).transitionDuration)) && document.getAnimations().length === 0);
  assert(reduce, 'transitions under reduce');
  await r.context.close();
  const n = await open('/lab/museum');
  const normal = await n.page.evaluate(() => { const cs = getComputedStyle(document.querySelector('.cards > li')); return [cs.transitionProperty, cs.transitionDuration]; });
  assert(normal[0] === 'opacity' && normal[1] === '0.15s', `normal ${normal}`);
  const noTransform = await n.page.evaluate(() => [...document.querySelectorAll('*')].every((el) => !/transform|all/.test(getComputedStyle(el).transitionProperty) || getComputedStyle(el).transitionDuration === '0s'));
  assert(noTransform, 'transform transition present');
  await n.context.close();
  return 'reduce: 0s; default: opacity 150ms only';
});

await record('AT-11', 'WCAG AA text contrast in the DOM + structure', async () => {
  const { context, page } = await open('/lab/museum');
  const res = await page.evaluate(() => {
    const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const [r, g, b, a = 1] = m[1].split(',').map((x) => parseFloat(x)); return { r, g, b, a }; };
    const lum = ({ r, g, b }) => [r, g, b].map((v) => v / 255).map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)).reduce((s, c, i) => s + c * [0.2126, 0.7152, 0.0722][i], 0);
    const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c.a === 1) return c; } return parse(getComputedStyle(document.documentElement).backgroundColor); };
    let min = 99, worst = '';
    for (const el of document.querySelectorAll('body *')) {
      if (!el.checkVisibility() || el.closest('.vh')) continue;
      if (![...el.childNodes].some((n) => n.nodeType === 3 && n.data.trim())) continue;
      const fg = parse(getComputedStyle(el).color), bg = bgOf(el);
      const [a, b] = [lum(fg), lum(bg)].sort((x, y) => y - x);
      const ratio = (a + 0.05) / (b + 0.05);
      if (ratio < min) { min = ratio; worst = el.tagName + '.' + el.className + ' ' + el.textContent.trim().slice(0, 30); }
    }
    const h = [...document.querySelectorAll('h1, h2, h3')].map((e) => +e.tagName[1]);
    const skipped = h.some((lvl, i) => i > 0 && lvl > h[i - 1] + 1);
    const unlabeled = [...document.querySelectorAll('input, select, textarea')].filter((e) => !(e.labels?.length || e.getAttribute('aria-labelledby') || e.getAttribute('aria-label'))).length;
    return { min, worst, h1: document.querySelectorAll('h1').length, skipped, lang: document.documentElement.lang, unlabeled,
      landmarks: ['header[role=banner]', 'main', 'form[role=search]', 'section#collection', 'nav[data-internal-nav]', 'footer[role=contentinfo]'].map((s) => document.querySelectorAll(s).length) };
  });
  assert(res.min >= 4.5, `min contrast ${res.min.toFixed(2)} at ${res.worst}`);
  assert(res.h1 === 1 && !res.skipped && res.lang === 'zh-CN' && res.unlabeled === 0 && res.landmarks.every((n) => n === 1), JSON.stringify(res));
  await context.close();
  return `min text contrast ${res.min.toFixed(2)}:1`;
});

await record('AT-12', 'mutations: build rejects invalid rows; client state cannot make a row joinable', async () => {
  const invalid = brief.fixtures.filter((f) => !f.expect.valid);
  for (const f of invalid) {
    let code = 0;
    try { execFileSync('node', [join(root, 'reference', 'build.mjs'), '--inject', f.id, '--out', join(shotDir, '..', '.inject-tmp')], { stdio: 'pipe' }); } catch (e) { code = e.status; }
    assert(code === 1, `build with ${f.id} exited ${code}`);
  }
  const { context, page } = await open('/lab/museum');
  await page.evaluate(() => { const r = document.querySelector('[data-museum-row]'); r.dataset.status = 'open'; r.dataset.pageRead = 'true'; r.dataset.verifiedOn = '2026-09-23'; });
  await page.check('input[name=status][value=closed]', { force: true });
  await page.check('input[name=status][value=all]', { force: true });
  const s1 = await page.evaluate(() => ({ hidden: document.querySelector('[data-museum-row]').closest('li').hidden, notice: document.querySelector('[data-rejected-notice]').innerText, visible: document.querySelector('[data-rejected-notice]').checkVisibility() }));
  assert(s1.hidden && s1.visible && s1.notice === '1 条记录未通过校验，未显示。 / 1 record(s) failed validation and are not shown.', JSON.stringify(s1));
  await page.evaluate(() => { const r = document.querySelectorAll('[data-museum-row]')[1]; r.dataset.verifiedOn = '2026-09-23'; });
  await page.check('input[name=freshness][value=unconfirmed]', { force: true });
  await page.check('input[name=freshness][value=all]', { force: true });
  const s2 = await page.evaluate(() => ({ second: document.querySelectorAll('[data-museum-row]')[1].closest('li').hidden, code: document.querySelectorAll('[data-museum-row]')[1].dataset.rejected, current: document.body.innerText.includes('来源已读取，90 天内已核对') }));
  assert(s2.second && s2.code === 'MUSEUM_E_HEDGE' && !s2.current, JSON.stringify(s2));
  const c = await ctaCounts(page);
  assert(c.exact === 0 && c.controls === 0, 'CTA after mutation');
  await context.close();
  return `${invalid.length} invalid fixtures fail the build; client mutations hidden + counted`;
});

await record('AT-13', 'no horizontal scroll at 320/360/640/1440; 16px gutters at 360', async () => {
  for (const w of [320, 360, 640, 1440]) {
    const { context, page } = await open('/lab/museum', { width: w, height: 800 });
    await page.click('[data-museum-row] summary').catch(() => {});
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `overflow at ${w}`);
    if (w === 360) assert(await page.$$eval('[data-museum-row]', (rs) => rs.every((r) => { const b = r.getBoundingClientRect(); return b.left >= 16 && b.right <= innerWidth - 16; })), 'gutter');
    await context.close();
  }
  return 'ok';
});

await record('AT-14', 'honesty bar + NIA strip stay in view at 360×740; static at 360×420', async () => {
  const { context, page } = await open('/lab/museum', { width: 360, height: 740 });
  for (const y of [0, 0.5, 1]) {
    await page.evaluate((f) => window.scrollTo(0, document.body.scrollHeight * f), y);
    const vis = await page.evaluate(() => {
      const inView = (el) => { const r = el.getBoundingClientRect(); return r.height > 0 && r.bottom > 0 && r.top < innerHeight; };
      return { bar: inView(document.querySelector('[data-honesty-bar]')), nia: inView(document.querySelector('[data-disclosure-strip]')) || inView(document.querySelector('footer [data-nia-short]')) };
    });
    assert(vis.bar && vis.nia, `scroll ${y}: ${JSON.stringify(vis)}`);
  }
  await context.close();
  const short = await open('/lab/museum', { width: 360, height: 420 });
  const pos = await short.page.evaluate(() => [getComputedStyle(document.querySelector('[data-honesty-bar]')).position, getComputedStyle(document.querySelector('[data-disclosure-strip]')).position, document.documentElement.scrollWidth <= innerWidth]);
  assert(pos[0] === 'static' && pos[1] === 'static' && pos[2], `short viewport ${pos}`);
  await short.context.close();
  return 'sticky in view; static fallback at 420px height';
});

await record('AT-16', 'no-JS: every row unconfirmed, form absent, required copy present', async () => {
  const { context, page } = await open('/lab/museum', { js: false, date: null });
  const s = await page.evaluate(() => ({ fresh: [...document.querySelectorAll('[data-museum-row]')].map((r) => r.dataset.freshness), text: document.body.innerText, forms: document.querySelectorAll('[data-filter-form]:not([hidden])').length }));
  assert(s.fresh.every((f) => f === 'unconfirmed') && s.text.includes('待核对 / Unconfirmed') && s.forms === 0, JSON.stringify({ fresh: s.fresh, forms: s.forms }));
  assert(s.text.includes(HONESTY) && s.text.includes(NIA), 'required copy without JS');
  await context.close();
  return 'ok';
});

// ---------------------------------------------------------------- negative control
// A deliberately broken page must be caught by the same checks (proves falsifiability).
await record('NEG', 'mutant page (join button, ?ref= link, 限时, LIVE, hidden honesty bar) is caught', async () => {
  mutantHtml = readFileSync(pages['/lab/museum'], 'utf8')
    .replace('<div class="card-facts" data-facts>', '<button data-cta="join" type="button">立即加入 Join now</button><p>限时 LIVE 你能拿 10000x</p><div class="card-facts" data-facts>')
    .replaceAll('https://www.notion.com/affiliates"', 'https://www.notion.com/affiliates?ref=abc"')
    .replace('[data-honesty-bar] {', '[data-honesty-bar] { display: none;');
  const { context, page } = await open('/mutant/lab/museum');
  const c = await ctaCounts(page);
  const hits = await domLexiconHits(page);
  const bar = await honestyVisible(page);
  const groups = [...new Set(hits.map((h) => h.group))].sort();
  assert(c.exact > 0 && c.controls > 0, `CTA not caught ${JSON.stringify(c)}`);
  for (const g of ['join_cta', 'urgency_ui', 'live_badge', 'ni_neng_na', 'multiplier_10000x', 'outbound_ref_via_code_params']) assert(groups.includes(g), `group ${g} not caught (${groups})`);
  assert(bar !== 'ok', 'hidden honesty bar not caught');
  const cssHits = scan(mutantHtml.match(/<style>([\s\S]*?)<\/style>/)[1], 'built_css', compiled);
  const hidden = await page.evaluate(() => document.querySelector('[data-row-id="notion-affiliate"]').closest('li').hidden);
  assert(hidden, 'runtime did not hide the row whose source carries ?ref=');
  assert(cssHits.some((h) => h.group === 'honesty_bar_hidden'), 'CSS hide not caught by lexicon');
  await context.close();
  return `caught: cta=${c.exact}, lexicon groups=${groups.join(',')}, honesty=${bar}, css=${cssHits.map((h) => h.group).join(',')}`;
});

await browser.close();
server.close();

let failed = 0;
for (const r of results) {
  if (!r.ok) failed++;
  console.log(`${r.ok ? 'PASS' : 'FAIL'} ${r.id} ${r.name}${r.detail ? ' — ' + r.detail : ''}`);
}
writeFileSync(join(shotDir, 'results.json'), JSON.stringify(results, null, 2));
console.log(`\n${results.length - failed}/${results.length} passed`);
process.exit(failed ? 1 : 0);
