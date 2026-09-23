#!/usr/bin/env node
// Executable version of the brief's acceptance tests (AT-01 … AT-16) against the reference build,
// plus negative controls: deliberately broken pages must FAIL the same checks.
//   npm run build && npm run build:fixtures && node tests/acceptance.mjs
// Uses the preinstalled Playwright (PLAYWRIGHT_BROWSERS_PATH); nothing is downloaded.
// Not covered here: pixel-baseline comparison (AT-01 needs committed baselines) and the inbound
// link on the Claim Shredder / Rules Board routes (AT-07), which do not exist in this reference.
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
const mutants = {};
const server = createServer((req, res) => {
  const path = req.url.split('?')[0].replace(/\/$/, '');
  const html = mutants[path] ?? (pages[path] && existsSync(pages[path]) ? readFileSync(pages[path]) : null);
  if (html) { res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); return res.end(html); }
  res.writeHead(404, { 'content-type': 'text/plain' }); res.end('not found');
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ORIGIN = `http://127.0.0.1:${server.address().port}`;

// ---------------------------------------------------------------- harness
const results = [];
async function record(id, name, fn) {
  try { results.push({ id, name, ok: true, detail: await fn() }); } catch (e) { results.push({ id, name, ok: false, detail: e.message }); }
}
const assert = (c, m) => { if (!c) throw new Error(m); };
const rgExit = (args) => { try { execFileSync('rg', args, { stdio: 'pipe' }); return 0; } catch (e) { return e.status; } };

const browser = await chromium.launch();
async function open(path, { width = 1440, height = 900, date = CLIENT_DATE, js = true, reducedMotion = 'no-preference' } = {}) {
  const context = await browser.newContext({ viewport: { width, height }, javaScriptEnabled: js, reducedMotion });
  await context.route((u) => !u.href.startsWith(ORIGIN), (route) => route.fulfill({ status: 200, contentType: 'text/html', body: '<p>external stub</p>' }));
  if (date) await context.addInitScript((d) => { window.__MUSEUM_CLIENT_DATE__ = d; }, date);
  const page = await context.newPage();
  await page.goto(ORIGIN + path, { waitUntil: 'networkidle' });
  return { context, page };
}

// Shared DOM checks (also run against the negative controls) -----------------------
const noScroll = (page) => page.evaluate(() =>
  document.documentElement.scrollWidth <= innerWidth && document.body.scrollWidth <= innerWidth &&
  getComputedStyle(document.documentElement).overflowX === 'visible' && getComputedStyle(document.body).overflowX === 'visible');

const ctaCounts = (page) => page.evaluate(() => ({
  exact: document.querySelectorAll('[data-museum-row] [data-cta="join"], [data-museum-row] [data-cta="apply"]').length,
  controls: document.querySelectorAll('[data-museum-row] :is([data-cta], button, input, select, textarea, form, [role="button"])').length,
  oneLink: [...document.querySelectorAll('[data-museum-row]')].every((r) => r.querySelectorAll('a').length === 1 && r.querySelector('a[data-source-link]')),
  clickable: [...document.querySelectorAll('[data-museum-row] *')].filter((el) => !el.closest('a[data-source-link], summary') && (el.hasAttribute('onclick') || el.hasAttribute('tabindex') || getComputedStyle(el).cursor === 'pointer')).length,
  externalNonSource: [...document.querySelectorAll('a[href]')].filter((a) => new URL(a.href).origin !== location.origin && !a.matches('[data-museum-row] a[data-source-link]')).length,
}));
const ctaClean = (c) => c.exact === 0 && c.controls === 0 && c.oneLink && c.clickable === 0 && c.externalNonSource === 0;

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
  return [
    ...scan(d.text, 'rendered_text', compiled),
    ...d.controls.flatMap((c) => scan(c, 'control_names', compiled)),
    ...d.hrefs.flatMap((h) => scan(h, 'hrefs', compiled)),
    ...d.rowsNotCurrent.flatMap((t) => scan(t, 'row_text_not_current', compiled)),
  ];
}

// lexicon.forbidden[honesty_bar_hidden].dom_checks, at the current scroll position and at the bottom.
async function honestyChecks(page, { checkHeight = true } = {}) {
  return page.evaluate(({ lit, checkHeight }) => {
    const b = document.querySelector('[data-honesty-bar]');
    if (!b) return 'missing';
    if (!b.innerText.includes(lit)) return 'literal missing';
    if (b.closest('[hidden], [aria-hidden="true"], details:not([open])')) return 'inside hidden container';
    const weak = [b, ...b.querySelectorAll('*')].find((e) => { const s = getComputedStyle(e); return !(s.opacity === '1' && s.transform === 'none' && s.visibility === 'visible' && s.display !== 'none' && parseFloat(s.fontSize) >= 13); });
    if (weak) return `weakened at <${weak.tagName.toLowerCase()}>`;
    for (let a = b.parentElement; a; a = a.parentElement) { const s = getComputedStyle(a); if (s.opacity !== '1' || s.transform !== 'none') return 'ancestor faded/transformed'; }
    const inView = () => { const r = b.getBoundingClientRect(); return r.height >= 24 && (!checkHeight || r.height <= 48) && r.top >= 0 && r.bottom <= innerHeight; };
    const y0 = scrollY;
    if (!inView()) { const r = b.getBoundingClientRect(); return `not fully in view (${r.top.toFixed(0)}–${r.bottom.toFixed(0)}, h=${r.height.toFixed(0)})`; }
    window.scrollTo(0, document.body.scrollHeight); // getBoundingClientRect forces layout, so no frame wait (works without JS too)
    const bottomOk = inView();
    window.scrollTo(0, y0);
    return bottomOk ? 'ok' : 'not in view at page bottom';
  }, { lit: HONESTY, checkHeight });
}

// ---------------------------------------------------------------- tests
await record('AT-01', 'screenshots 1440 / 360 (sticky bars static), fields and disclosure visible, no overflow, no CTA', async () => {
  const out = [];
  for (const width of [1440, 360]) {
    const { context, page } = await open('/lab/museum', { width, height: width === 1440 ? 900 : 740 });
    const shot = join(shotDir, `museum-${width}.png`);
    await page.screenshot({ path: shot, fullPage: true, style: '[data-honesty-bar],[data-disclosure-strip]{position:static!important}' });
    const h1 = await page.locator('h1').innerText();
    assert(h1.replace(/\s+/g, ' ').trim() === '关门博物馆 Closed Programs Museum', `h1 was ${JSON.stringify(h1)}`);
    const vis = await page.evaluate(() => [...document.querySelectorAll('[data-museum-row]')].every((r) =>
      ['status', 'as_of', 'page_read', 'verified_on', 'freshness', 'source', 'why_not_joinable'].every((f) => { const el = r.querySelector(`[data-field="${f}"]`); return el && el.checkVisibility() && el.innerText.trim().length > 0; })));
    assert(vis, `row field not visible at ${width}`);
    for (const sel of ['[data-honesty-bar]', 'footer [data-nia-short]', '[data-disclosure-body][lang="zh-CN"]', '[data-disclosure-body][lang="en"]'])
      assert(await page.locator(sel).isVisible(), `${sel} not visible at ${width}`);
    assert(await noScroll(page), `horizontal overflow at ${width}`);
    const btn = await page.getByRole('button', { name: /加入|申请|注册|分享|复制|join|apply|sign ?up|share|copy|code/i }).count();
    const lnk = await page.getByRole('link', { name: /加入|申请|注册|分享|复制|成为|开户|join|apply|sign ?up|register|share|copy|become|code/i }).count();
    assert(btn === 0 && lnk === 0, `CTA-like controls: ${btn} buttons, ${lnk} links`);
    out.push(shot);
    await context.close();
  }
  return out.map((p) => p.split('/').pop()).join(', ');
});

await record('AT-02', 'no join/apply CTA, control, clickable or extra link in any row (seed + fixtures)', async () => {
  for (const path of ['/lab/museum', '/fixtures/lab/museum']) {
    const { context, page } = await open(path);
    const c = await ctaCounts(page);
    assert(ctaClean(c), `${path}: ${JSON.stringify(c)}`);
    await context.close();
  }
  return 'exact=0 controls=0 clickable=0 one-link-per-row on both pages';
});

await record('AT-03', 'required attributes non-empty and values visible', async () => {
  const { context, page } = await open('/lab/museum');
  const rows = await page.$$eval('[data-museum-row]', (rs) => rs.map((r) => ({ attrs: ['data-status', 'data-as-of', 'data-source-url', 'data-why-not-joinable-zh', 'data-why-not-joinable-en'].map((a) => r.getAttribute(a) || ''), src: r.dataset.sourceUrl, asOf: r.dataset.asOf, zh: r.dataset.whyNotJoinableZh, en: r.dataset.whyNotJoinableEn, text: r.innerText })));
  assert(rows.length === DC.seed.length, `rows ${rows.length}`);
  for (const r of rows) {
    assert(r.attrs.every((a) => a.trim()), 'empty attribute');
    for (const v of [r.asOf, r.src.replace('https://', ''), r.zh, r.en, '官方来源 / Official source', '为何不可加入 / Why not joinable']) assert(r.text.includes(v), `not visible: ${v}`);
  }
  await context.close();
  return `${rows.length} rows ok`;
});

await record('AT-04', 'source links are the only external links: https, official host, no query/hash, equal to the seed; rg clean', async () => {
  const hosts = Object.values(DC.official_domains).flat();
  for (const [path, expected] of [['/lab/museum', DC.seed.map((r) => r.source_url)], ['/fixtures/lab/museum', brief.fixtures.filter((f) => f.expect.valid).map((f) => f.row.source_url)]]) {
    const { context, page } = await open(path);
    const links = await page.$$eval('a[data-source-link]', (as) => as.map((a) => { const u = new URL(a.href); return { protocol: u.protocol, host: u.hostname, search: u.search, hash: u.hash, rel: a.rel, rp: a.referrerPolicy, bg: getComputedStyle(a).backgroundColor, row: a.closest('[data-museum-row]').dataset.sourceUrl, href: a.getAttribute('href') }; }));
    for (const l of links) {
      assert(l.protocol === 'https:' && l.search === '' && l.hash === '' && l.href === l.row, `bad link ${l.href}`);
      assert(l.rel.includes('noopener') && l.rel.includes('noreferrer') && l.rp === 'no-referrer', 'rel/referrerpolicy');
      assert(l.bg === 'rgba(0, 0, 0, 0)', 'source link has a background');
      assert(hosts.includes(l.host), `host ${l.host}`);
    }
    assert(JSON.stringify(links.map((l) => l.href).sort()) === JSON.stringify([...expected].sort()), `${path}: hrefs differ from reviewed data`);
    assert((await ctaCounts(page)).externalNonSource === 0, 'external link outside the rows');
    await context.close();
  }
  for (const dir of ['dist', 'dist-fixtures']) for (const re of ['[?&](ref|via|code)=', '[?&](ref|via|code|referral|invite|aff|affiliate|utm_[a-z]+)='])
    assert(rgExit(['-n', '--pcre2', re, join(root, dir)]) === 1, `rg ${re} in ${dir}`);
  return 'hrefs equal seed/fixture URLs; rg exit 1';
});

await record('AT-05', 'unread/stale never current; client date drives freshness', async () => {
  const { context, page } = await open('/fixtures/lab/museum');
  let n = 0;
  for (const f of brief.fixtures.filter((x) => x.expect.valid)) {
    const sel = `[data-row-id="${f.row.id}"]`;
    const r = await page.$eval(sel, (e) => ({ pr: e.dataset.pageRead, f: e.dataset.freshness, t: e.innerText, ctl: e.querySelectorAll('[data-cta], button, input').length }));
    assert(r.f === f.expect.freshness, `${f.id}: ${r.f} ≠ ${f.expect.freshness}`);
    for (const s of f.expect.visible_text_includes || []) assert(r.t.includes(s), `${f.id}: missing ${s}`);
    for (const s of f.expect.visible_text_excludes || []) assert(!r.t.includes(s), `${f.id}: unexpected ${s}`);
    for (const [a, v] of Object.entries(f.expect.attributes || {})) assert((await page.getAttribute(sel, a)) === v, `${f.id}: ${a}`);
    if (f.expect.after_opening_check_record_includes) {
      await page.click(`${sel} summary`);
      const t = await page.locator(sel).innerText();
      for (const s of f.expect.after_opening_check_record_includes) assert(t.includes(s), `${f.id}: after open missing ${s}`);
    }
    assert(r.ctl === 0, `${f.id}: control in row`);
    if (r.pr !== 'true') assert(r.f === 'unconfirmed' && r.t.includes('待核对 / Unconfirmed'), `${f.id} unread not unconfirmed`);
    if (r.f !== 'current') assert(!r.t.includes('来源已读取，90 天内已核对'), `${f.id} claims current`);
    n++;
  }
  await context.close();
  const later = await open('/fixtures/lab/museum', { date: '2026-12-31' });
  const f05 = await later.page.getAttribute('[data-row-id="notion-affiliate-fixture-boundary-90"]', 'data-freshness');
  assert(f05 === 'stale', `FX-05 on 2026-12-31 should be stale, was ${f05}`);
  await later.context.close();
  return `${n} fixture rows ok; FX-05 flips to stale on 2026-12-31`;
});

await record('AT-06', 'forbidden lexicon: dist scan, DOM scan, rg with Unicode escapes, gravity count', async () => {
  for (const dir of ['dist', 'dist-fixtures']) execFileSync('node', [join(here, 'lexicon-scan.mjs'), join(root, dir)], { stdio: 'pipe' });
  assert(rgExit(['-n', '--pcre2', '\\x{4F60}\\x{80FD}\\x{62FF}|\\x{5FC5}\\x{8D5A}|\\x{7A33}\\x{8D5A}|\\x{5012}\\x{8BA1}\\x{65F6}|\\x{9650}\\x{65F6}|\\x{7ACB}\\x{5373}', join(root, 'dist')]) === 1, 'CJK rg');
  assert(rgExit(['-n', '--pcre2', '10,?000\\s*[x×]|\\bLIVE\\b|(?i:count[ -]?down|confetti|\\bneon\\b|take[ -]?rate|guarantee)', join(root, 'dist')]) === 1, 'hype rg');
  const counts = execFileSync('rg', ['--count-matches', '-i', 'gravity', join(root, 'dist')], { encoding: 'utf8' }).trim().split('\n');
  assert(counts.length === 1 && counts[0].endsWith('index.html:2'), `gravity count ${counts}`);
  for (const path of ['/lab/museum', '/fixtures/lab/museum']) {
    const { context, page } = await open(path);
    const hits = await domLexiconHits(page);
    assert(hits.length === 0, `${path}: ${JSON.stringify(hits.slice(0, 5))}`);
    const g = await page.evaluate(() => {
      const nodes = [];
      const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (w.nextNode()) if (/gravity/i.test(w.currentNode.data)) nodes.push(w.currentNode);
      return { contained: nodes.every((n) => n.parentElement.closest('[data-non-affiliation]')), n: document.querySelectorAll('[data-non-affiliation]').length };
    });
    assert(g.contained && g.n === 2, `gravity ${JSON.stringify(g)}`);
    await context.close();
  }
  return 'scan 0 hits, rg exit 1, gravity 2 per file, only in [data-non-affiliation]';
});

await record('AT-07', 'required copy on every view (22 states + fixtures + no-JS)', async () => {
  let views = 0;
  const check = async (page, label) => {
    const h = await honestyChecks(page);
    assert(h === 'ok', `${label}: honesty bar ${h}`);
    assert((await page.locator('footer[data-standing-disclosure] [data-nia-short]').innerText()) === NIA, `${label}: NIA`);
    const ft = await page.locator('footer[data-standing-disclosure]').innerText();
    assert(ft.includes(brief.standing_disclosure.zh) && ft.includes(brief.standing_disclosure.en), `${label}: disclosure`);
    const nav = await page.$$eval('nav[data-internal-nav] a', (as) => as.map((a) => [a.innerText.trim(), a.getAttribute('href')]));
    assert(JSON.stringify(nav) === JSON.stringify([['回到 Claim Shredder / Back to Claim Shredder', DC.routes.claim_shredder], ['查看规则板 / View rules board', DC.routes.rules_board]]), `${label}: nav ${JSON.stringify(nav)}`);
    const same = await page.$$eval('a[href]', (as) => as.filter((a) => new URL(a.href).origin === location.origin).map((a) => a.getAttribute('href')));
    assert(same.every((h) => [DC.routes.claim_shredder, DC.routes.rules_board, '#collection', '#disclosure'].includes(h)), `${label}: internal hrefs ${same}`);
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
    ['details open', (p) => p.click('li:not([hidden]) > [data-museum-row] summary')],
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

await record('AT-08', 'request spy: only the document on load; zero requests during interactions', async () => {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await context.addInitScript((d) => { window.__MUSEUM_CLIENT_DATE__ = d; }, CLIENT_DATE);
  await context.route((u) => !u.href.startsWith(ORIGIN), (route) => route.fulfill({ status: 200, contentType: 'text/html', body: 'stub' }));
  const page = await context.newPage();
  const reqs = [];
  context.on('request', (r) => reqs.push(r.url()));
  await page.goto(ORIGIN + '/lab/museum', { waitUntil: 'networkidle' });
  const loaded = reqs.filter((u) => !u.startsWith('data:'));
  assert(JSON.stringify(loaded) === JSON.stringify([page.url()]), `load requests: ${loaded}`);
  const head = await page.evaluate(() => [
    !!document.querySelector('meta[http-equiv="Content-Security-Policy"]'),
    !!document.querySelector('meta[name="referrer"][content="no-referrer"]'),
    !!document.querySelector('link[rel="icon"][href="data:,"]'),
  ]);
  assert(head.every(Boolean), `head nodes ${head}`);
  assert(rgExit(['-n', '--pcre2', 'url\\((?!["\\x27]?data:)|rel="(preload|stylesheet|prefetch|preconnect|dns-prefetch)"|<script[^>]*\\bsrc=', join(root, 'dist')]) === 1, 'external resource reference in dist');
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
  await page.waitForTimeout(1000);
  assert(reqs.length === 0, `requests during interaction: ${reqs}`);
  assert(page.url() === url0, 'URL changed');
  const expected = await page.getAttribute('li:not([hidden]) a[data-source-link]', 'href');
  const [popup] = await Promise.all([context.waitForEvent('page'), page.click('li:not([hidden]) a[data-source-link]')]);
  await popup.waitForLoadState('domcontentloaded');
  assert(popup.url() === expected && new URL(popup.url()).search === '', `popup ${popup.url()}`);
  await context.close();
  assert(rgExit(['-n', '--pcre2', '\\bfetch\\(|XMLHttpRequest|sendBeacon|new WebSocket|EventSource|googletagmanager|google-analytics|gtag\\(|plausible|segment|sentry', join(root, 'dist')]) === 1, 'network API in bundle');
  return `load: document only; interactions: 0; popup → ${expected.slice(0, 40)}…`;
});

await record('AT-09', 'keyboard: order forward and back at 360×740, 1280×720, 1440×900; focus visible and never covered', async () => {
  const expected = ['skip', 'search', 'status', 'freshness', 'sort', 'reset', 'source', 'summary', 'source', 'summary', 'source', 'summary', 'nav', 'nav'];
  const probe = () => {
    const a = document.activeElement;
    const target = a.matches('input[type=radio]') ? a.closest('label') : a;
    const cs = getComputedStyle(target);
    const r = target.getBoundingClientRect();
    const x = Math.min(innerWidth - 1, Math.max(0, r.left + r.width / 2));
    const y = Math.min(innerHeight - 1, Math.max(0, r.top + r.height / 2));
    const hit = document.elementFromPoint(x, y);
    const kind = a.matches('.skip-link') ? 'skip' : a.matches('input[type=search]') ? 'search' : a.matches('input[name=status]') ? 'status' : a.matches('input[name=freshness]') ? 'freshness' : a.matches('select') ? 'sort' : a.matches('button[type=reset]') ? 'reset' : a.matches('[data-source-link]') ? 'source' : a.matches('summary') ? 'summary' : a.closest('[data-internal-nav]') ? 'nav' : a.tagName;
    const inView = r.top >= 0 && r.bottom <= innerHeight;
    return { kind, outline: cs.outlineStyle, ow: parseFloat(cs.outlineWidth), covered: !(hit && (target.contains(hit) || hit.contains(target))), inView };
  };
  const out = [];
  for (const [w, h] of [[360, 740], [1280, 720], [1440, 900]]) {
    const { context, page } = await open('/lab/museum', { width: w, height: h });
    const fwd = [];
    for (let i = 0; i < expected.length; i++) {
      await page.keyboard.press('Tab');
      const p = await page.evaluate(probe);
      fwd.push(p.kind);
      assert(p.outline !== 'none' && p.ow >= 2, `${w}×${h}: no focus ring on ${p.kind}`);
      assert(!p.covered && p.inView, `${w}×${h}: ${p.kind} covered or off-screen (forward, stop ${i})`);
    }
    assert(JSON.stringify(fwd) === JSON.stringify(expected), `${w}×${h} order ${fwd}`);
    const back = [];
    for (let i = expected.length - 2; i >= 0; i--) {
      await page.keyboard.press('Shift+Tab');
      const p = await page.evaluate(probe);
      back.push(p.kind);
      assert(!p.covered && p.inView, `${w}×${h}: ${p.kind} covered or off-screen (backward, stop ${i})`);
    }
    assert(JSON.stringify(back) === JSON.stringify(expected.slice(0, -1).reverse()), `${w}×${h} reverse order ${back}`);
    if (w === 1440) {
      await page.focus('input[name=status][value=all]');
      await page.keyboard.press('ArrowRight');
      assert((await page.$eval('input[name=status]:checked', (e) => e.value)) === 'closed', 'arrow key');
      const bgs = await page.$$eval('input[name=status]', (is) => is.map((i) => [i.checked, getComputedStyle(i.closest('label')).backgroundColor]));
      const checkedBg = bgs.find(([c]) => c)[1];
      assert(bgs.filter(([c]) => !c).every(([, bg]) => bg !== checkedBg), 'checked pill not distinguishable');
      await page.focus('.skip-link');
      await page.keyboard.press('Enter');
      const skip = await page.evaluate(() => [document.activeElement.id, getComputedStyle(document.activeElement).outlineStyle]);
      assert(skip[0] === 'collection' && skip[1] !== 'none', `skip target ${skip}`);
      await page.focus('nav[data-internal-nav] li:last-child a');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      assert(await page.evaluate(() => document.activeElement.matches('.skip-link')), 'focus did not wrap to the skip link');
    }
    out.push(`${w}×${h}`);
    await context.close();
  }
  return `order ok forward+back at ${out.join(', ')}`;
});

await record('AT-10', 'reduced motion removes the only transition', async () => {
  const r = await open('/lab/museum', { reducedMotion: 'reduce' });
  await r.page.check('input[name=status][value=capped]', { force: true });
  await r.page.check('input[name=status][value=all]', { force: true });
  const reduce = await r.page.evaluate(() => [...document.querySelectorAll('[data-museum-list] > li, .record')].every((el) => /^0s(, 0s)*$/.test(getComputedStyle(el).transitionDuration)) && document.getAnimations().length === 0);
  assert(reduce, 'transitions under reduce');
  await r.context.close();
  const n = await open('/lab/museum');
  const normal = await n.page.evaluate(() => { const cs = getComputedStyle(document.querySelector('[data-museum-list] > li')); return [cs.transitionProperty, cs.transitionDuration]; });
  assert(normal[0] === 'opacity' && normal[1] === '0.15s', `normal ${normal}`);
  const bad = await n.page.evaluate(() => [...document.querySelectorAll('*')].filter((el) => /transform|all/.test(getComputedStyle(el).transitionProperty) && !/^0s(, 0s)*$/.test(getComputedStyle(el).transitionDuration)).length);
  assert(bad === 0, `${bad} elements with transform/all transitions`);
  await n.context.close();
  return 'reduce: 0s; default: opacity 150ms only';
});

await record('AT-11', 'WCAG AA text contrast, lang tagging, structure', async () => {
  const { context, page } = await open('/lab/museum');
  await page.click('li:not([hidden]) > [data-museum-row] summary');
  const res = await page.evaluate((landmarks) => {
    const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const [r, g, b, a = 1] = m[1].split(',').map((x) => parseFloat(x)); return { r, g, b, a }; };
    const lum = ({ r, g, b }) => [r, g, b].map((v) => v / 255).map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)).reduce((s, c, i) => s + c * [0.2126, 0.7152, 0.0722][i], 0);
    const bgOf = (el) => { for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c && c.a === 1) return c; } return parse(getComputedStyle(document.documentElement).backgroundColor); };
    let min = 99, worst = '';
    for (const el of document.querySelectorAll('body *')) {
      if (!el.checkVisibility() || el.closest('.vh')) continue;
      if (![...el.childNodes].some((n) => n.nodeType === 3 && n.data.trim())) continue;
      const [a, b] = [lum(parse(getComputedStyle(el).color)), lum(bgOf(el))].sort((x, y) => y - x);
      const ratio = (a + 0.05) / (b + 0.05);
      if (ratio < min) { min = ratio; worst = el.tagName + ' ' + el.textContent.trim().slice(0, 30); }
    }
    const untagged = [];
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (w.nextNode()) {
      const n = w.currentNode;
      if (n.parentElement.closest('option, script, style')) continue;
      const t = n.data.replace(/https?:\/\/\S+|[\w.-]+\.(com|so|li)\/\S*|gravity\.li|Referral Lab|Claim Shredder|Notion|IBKR|Binance/g, '');
      if (/[A-Za-z]{4,}/.test(t) && n.parentElement.closest('[lang]').lang !== 'en') untagged.push(n.data.trim().slice(0, 40));
    }
    const h = [...document.querySelectorAll('h1, h2, h3')].map((e) => +e.tagName[1]);
    return {
      min, worst, untagged,
      h1: document.querySelectorAll('h1').length,
      skipped: h.some((lvl, i) => i > 0 && lvl > h[i - 1] + 1),
      lang: document.documentElement.lang,
      unlabeled: [...document.querySelectorAll('input, select, textarea')].filter((e) => !(e.labels?.length || e.getAttribute('aria-labelledby') || e.getAttribute('aria-label'))).length,
      landmarks: landmarks.map((s) => document.querySelectorAll(s).length),
    };
  }, ['header[role=banner]', 'main', 'form[role=search]', 'section#collection', 'nav[data-internal-nav]', 'footer[role=contentinfo]']);
  assert(res.min >= 4.5, `min contrast ${res.min.toFixed(2)} at ${res.worst}`);
  assert(res.untagged.length === 0, `English text without lang=en: ${JSON.stringify(res.untagged.slice(0, 5))}`);
  assert(res.h1 === 1 && !res.skipped && res.lang === 'zh-CN' && res.unlabeled === 0 && res.landmarks.every((n) => n === 1), JSON.stringify(res));
  await context.close();
  return `min text contrast ${res.min.toFixed(2)}:1; all English tagged`;
});

await record('AT-12', 'mutations: build rejects every invalid fixture; client state cannot make a row joinable', async () => {
  const invalid = brief.fixtures.filter((f) => !f.expect.valid);
  for (const f of invalid) {
    let code = 0, err = '';
    try { execFileSync('node', [join(root, 'reference', 'build.mjs'), '--inject', f.id, '--out', join(shotDir, '.inject-tmp')], { stdio: 'pipe' }); } catch (e) { code = e.status; err = String(e.stderr); }
    assert(code === 1 && err.includes(f.expect.error_code), `build with ${f.id} exited ${code} (${err.trim().slice(0, 80)})`);
  }
  const { context, page } = await open('/lab/museum');
  await page.evaluate(() => { const r = document.querySelector('[data-museum-row]'); r.dataset.status = 'open'; r.dataset.pageRead = 'true'; r.dataset.verifiedOn = '2026-09-23'; });
  await page.check('input[name=status][value=closed]', { force: true });
  await page.check('input[name=status][value=all]', { force: true });
  const s1 = await page.evaluate(() => ({ hidden: document.querySelector('[data-museum-row]').closest('li').hidden, notice: document.querySelector('[data-rejected-notice]').innerText, visible: document.querySelector('[data-rejected-notice]').checkVisibility() }));
  assert(s1.hidden && s1.visible && s1.notice === '1 条记录未通过校验，未显示。 / 1 record(s) failed validation and are not shown.', JSON.stringify(s1));
  await page.evaluate(() => { document.querySelectorAll('[data-museum-row]')[1].dataset.verifiedOn = '2026-09-23'; });
  await page.check('input[name=freshness][value=unconfirmed]', { force: true });
  await page.check('input[name=freshness][value=all]', { force: true });
  const s2 = await page.evaluate(() => { const r = document.querySelectorAll('[data-museum-row]')[1]; return { hidden: r.closest('li').hidden, code: r.dataset.rejected, current: document.body.innerText.includes('来源已读取，90 天内已核对') }; });
  assert(s2.hidden && s2.code === 'MUSEUM_E_HEDGE' && !s2.current, JSON.stringify(s2));
  assert(ctaClean(await ctaCounts(page)), 'CTA after mutation');
  await context.close();
  return `${invalid.length} invalid fixtures fail the build with their exact code; client mutations hidden + counted`;
});

await record('AT-13', 'no horizontal overflow (and none clipped away) at 320/360/640/1440; 16px gutters at 360', async () => {
  for (const w of [320, 360, 640, 1440]) {
    const { context, page } = await open('/lab/museum', { width: w, height: 800 });
    await page.click('li:not([hidden]) > [data-museum-row] summary');
    assert(await noScroll(page), `overflow at ${w}`);
    if (w === 360) assert(await page.$$eval('[data-museum-row]', (rs) => rs.every((r) => { const b = r.getBoundingClientRect(); return b.left >= 16 && b.right <= innerWidth - 16; })), 'gutter');
    await context.close();
  }
  return 'ok';
});

await record('AT-14', 'bar ≤48px and strip ≤44px stay in view at 360×740; all static at 360×420', async () => {
  const { context, page } = await open('/lab/museum', { width: 360, height: 740 });
  for (const y of [0, 0.5, 1]) {
    await page.evaluate((f) => window.scrollTo(0, document.body.scrollHeight * f), y);
    const vis = await page.evaluate(() => {
      const inView = (el) => { const r = el.getBoundingClientRect(); return r.height > 0 && r.bottom > 0 && r.top < innerHeight; };
      const bar = document.querySelector('[data-honesty-bar]'), strip = document.querySelector('[data-disclosure-strip]');
      return { bar: inView(bar), nia: inView(strip) || inView(document.querySelector('footer [data-nia-short]')), barH: bar.getBoundingClientRect().height, stripH: strip.getBoundingClientRect().height };
    });
    assert(vis.bar && vis.nia && vis.barH <= 48 && vis.stripH <= 44, `scroll ${y}: ${JSON.stringify(vis)}`);
    assert((await honestyChecks(page)) === 'ok', `honesty checks at scroll ${y}`);
  }
  await context.close();
  const short = await open('/lab/museum', { width: 360, height: 420 });
  const pos = await short.page.evaluate(() => ['[data-honesty-bar]', '[data-disclosure-strip]', '[data-filter-form]'].map((s) => getComputedStyle(document.querySelector(s)).position));
  assert(pos.every((p) => p === 'static') && (await noScroll(short.page)), `short viewport ${pos}`);
  await short.context.close();
  return 'sticky + within caps; static at 420px height';
});

await record('AT-16', 'no-JS: every row unconfirmed, form hidden, required copy present', async () => {
  const { context, page } = await open('/lab/museum', { js: false, date: null });
  const s = await page.evaluate(() => ({ fresh: [...document.querySelectorAll('[data-museum-row]')].map((r) => r.dataset.freshness), text: document.body.innerText, forms: document.querySelectorAll('[data-filter-form]:not([hidden])').length }));
  assert(s.fresh.every((f) => f === 'unconfirmed') && s.text.includes('待核对 / Unconfirmed') && s.forms === 0, JSON.stringify({ fresh: s.fresh, forms: s.forms }));
  assert(s.text.includes(HONESTY) && s.text.includes(NIA), 'required copy without JS');
  await context.close();
  return 'ok';
});

// ---------------------------------------------------------------- negative controls
const base = readFileSync(pages['/lab/museum'], 'utf8');
await record('NEG-1', 'mutant (join button, ?ref= source, 限时/LIVE/你能拿/10000x, hidden honesty bar) is caught', async () => {
  mutants['/mutant1/lab/museum'] = base
    .replace('<div class="card-facts" data-facts>', '<button data-cta="join" type="button">立即加入 Join now</button><p>限时 LIVE 你能拿 10000x</p><div class="card-facts" data-facts>')
    .replaceAll('https://www.notion.com/affiliates"', 'https://www.notion.com/affiliates?ref=abc"')
    .replace('[data-honesty-bar] {', '[data-honesty-bar] { display: none;');
  const { context, page } = await open('/mutant1/lab/museum');
  const c = await ctaCounts(page);
  const groups = [...new Set((await domLexiconHits(page)).map((h) => h.group))].sort();
  const bar = await honestyChecks(page);
  const cssHits = scan(mutants['/mutant1/lab/museum'].match(/<style>([\s\S]*?)<\/style>/)[1], 'built_css', compiled);
  const hidden = await page.evaluate(() => document.querySelector('[data-row-id="notion-affiliate"]').closest('li').hidden);
  assert(c.exact > 0 && c.controls > 0, `CTA not caught ${JSON.stringify(c)}`);
  for (const g of ['join_cta', 'urgency_ui', 'live_badge', 'ni_neng_na', 'multiplier_10000x', 'outbound_ref_via_code_params']) assert(groups.includes(g), `group ${g} not caught (${groups})`);
  assert(bar !== 'ok' && cssHits.some((h) => h.group === 'honesty_bar_hidden') && hidden, `bar=${bar} css=${cssHits.length} hidden=${hidden}`);
  await context.close();
  return `caught: cta=${c.exact}, groups=${groups.join(',')}, honesty=${bar}`;
});

await record('NEG-2', 'mutant (faded <strong> in bar, onclick div in a card, external join link, clipped overflow, code shown as text) is caught', async () => {
  mutants['/mutant2/lab/museum'] = base
    .replace('[data-honesty-bar] strong { font-weight: 500; }', '[data-honesty-bar] strong { font-weight: 500; opacity: .03; }')
    .replace('<div class="card-facts" data-facts>', '<div onclick="void 0" style="cursor:pointer">Referral code: MUSEUM50</div><div class="card-facts" data-facts>')
    .replace('</nav>\n</main>', '<a href="https://www.notion.com/affiliates">官网</a></nav>\n</main>')
    .replace('body {\n  margin: 0;', 'body {\n  margin: 0; overflow-x: clip;')
    .replace('</footer>', '<div style="width:2000px">wide</div></footer>');
  const { context, page } = await open('/mutant2/lab/museum', { width: 360, height: 740 });
  const bar = await honestyChecks(page);
  const c = await ctaCounts(page);
  const groups = [...new Set((await domLexiconHits(page)).map((h) => h.group))];
  const scroll = await noScroll(page);
  const cssHits = scan(mutants['/mutant2/lab/museum'].match(/<style>([\s\S]*?)<\/style>/)[1], 'built_css', compiled);
  assert(bar.startsWith('weakened'), `faded strong not caught: ${bar}`);
  assert(cssHits.some((h) => h.group === 'honesty_bar_hidden'), 'CSS opacity on bar child not caught');
  assert(c.clickable > 0 && c.externalNonSource > 0, `clickable/external not caught ${JSON.stringify(c)}`);
  assert(groups.includes('referral_code_generation_or_storage'), `code-as-text not caught (${groups})`);
  assert(!scroll, 'clipped overflow not caught');
  await context.close();
  return `caught: honesty=${bar}, clickable=${c.clickable}, external=${c.externalNonSource}, code-text, overflow`;
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
