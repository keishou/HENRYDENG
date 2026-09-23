#!/usr/bin/env node
// Validates brief.json against the return contract and against itself:
// shape, verbatim do/dont lines, lexicon self-test, copy vs lexicon, token contrast,
// seed truthfulness, and every fixture's expected validity / freshness.
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateRow, freshness, daysBetween, UNVERIFIED_AS_OF, HEDGE_ZH, HEDGE_EN } from '../reference/museum-core.mjs';
import { compile, selfTest, scan } from '../tests/lexicon-scan.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const briefPath = resolve(here, '..', process.argv[2] || 'brief.json');
const raw = readFileSync(briefPath, 'utf8');
const errors = [];
const ok = (cond, msg) => { if (!cond) errors.push(msg); };
const eqSet = (a, b) => a.length === b.length && a.every((x) => b.includes(x));

let brief;
try { brief = JSON.parse(raw); } catch (e) { console.error('INVALID JSON', e.message); process.exit(1); }

// 1. Shape --------------------------------------------------------------------
ok(eqSet(Object.keys(brief), ['compose_closed_programs_museum', 'label_set', 'fixtures', 'standing_disclosure']), `top-level keys: ${Object.keys(brief)}`);
const B = brief.compose_closed_programs_museum;
ok(eqSet(Object.keys(B), ['problem', 'do', 'dont', 'ia', 'data_contract', 'lexicon', 'copy', 'dont_repeat', 'acceptance', 'open_questions']), `compose keys: ${Object.keys(B)}`);
ok(typeof B.problem === 'string' && B.problem.length > 80, 'problem');
for (const k of ['do', 'dont', 'dont_repeat', 'acceptance', 'open_questions']) ok(Array.isArray(B[k]), `${k} is array`);
for (const k of ['ia', 'data_contract', 'lexicon', 'copy']) ok(B[k] && typeof B[k] === 'object' && !Array.isArray(B[k]), `${k} is object`);
ok(B.open_questions.length <= 2, 'open_questions <= 2');
ok(B.dont_repeat.length >= 6 && B.dont_repeat.every((d) => d.zh?.trim() && d.en?.trim()), 'dont_repeat >= 6 bilingual');
ok(Array.isArray(brief.label_set) && brief.label_set.length > 0, 'label_set');
ok(Array.isArray(brief.fixtures) && brief.fixtures.length >= 4, 'fixtures >= 4');
ok(brief.standing_disclosure?.zh?.trim() && brief.standing_disclosure?.en?.trim(), 'standing_disclosure zh/en');

// 2. Verbatim DO / DONT lines from the prompt ---------------------------------
const DO_REQ = [
  'Build the museum as a quiet archive of closed, capped, and geo-excluded counterexamples; link it internally from Claim Shredder and the Rules Board, never from an external brand.',
  'Put `status`, `as_of`, official `source_url`, `page_read`, `verified_on`, and bilingual `why_not_joinable` on every row and render all of them visibly.',
  'Keep the attribution bar `点击 ≠ 收入 / Clicks ≠ income` and the standing bilingual disclosure visible on every view.',
  'Use the dark board tokens, restrained museum-label/tombstone annotation, bilingual zh-primary/en-secondary copy, responsive cards, keyboard access, WCAG AA, and reduced-motion behavior specified below.',
];
const DONT_REQ = [
  'Never provide a join/apply CTA, referral/share link, code field, or FOMO treatment for a closed, capped, geo-excluded, stale, or unverified row.',
  'Never omit `as_of`, official source, or the bilingual reason why the program is not joinable; never present stale evidence as current.',
  'Never use earnings estimates, take-rate calculators, 「你能拿」, guaranteed income, 必赚, 10000x, urgency, confetti, neon, LIVE, countdown, investment advice, or gravity.li/GRAVITY branding.',
  'Never generate, store, infer, or add referral codes or `ref`/`via`/`code` outbound parameters; this feature has no `{own_link}`.',
  'Never hide or weaken `点击 ≠ 收入 / Clicks ≠ income`.',
];
for (const s of DO_REQ) ok(B.do.includes(s), `do[] missing verbatim: ${s.slice(0, 60)}`);
for (const s of DONT_REQ) ok(B.dont.includes(s), `dont[] missing verbatim: ${s.slice(0, 60)}`);
const dontJoined = B.dont.join('\n');
for (const ban of ['earnings estimates', 'take-rate calculators', '「你能拿」', 'guaranteed income', '必赚', '10000x', 'generating or storing referral codes', 'ref, via and code', '{own_link}', 'urgency UI', 'confetti', 'neon', 'LIVE', 'countdown', 'join CTA on closed, capped or geo rows', 'hiding 点击 ≠ 收入 / Clicks ≠ income', 'claiming freshness without page_read', 'investment advice'])
  ok(dontJoined.includes(ban), `dont[] lacks explicit ban: ${ban}`);

// 3. Lexicon --------------------------------------------------------------------
const L = B.lexicon;
const compiled = compile(L);
for (const e of selfTest(compiled)) errors.push(`lexicon self-test: ${e}`);
for (const t of ['gravity.li', 'GRAVITY', '你能拿', '必赚', '10000x', 'ref', 'via', 'code', 'LIVE', 'countdown'])
  ok(Object.hasOwn(L.literal_token_index, t), `literal_token_index lacks ${t}`);
const reqLits = L.required_copy.map((r) => r.literal);
ok(reqLits.includes('点击 ≠ 收入 / Clicks ≠ income'), 'required_copy lacks honesty literal');
ok(reqLits.includes('not investment advice'), 'required_copy lacks "not investment advice"');
ok(/^[\x00-\x7F]*$/.test(JSON.stringify(L.forbidden.map((g) => g.patterns))), 'forbidden pattern sources must be ASCII (CJK as \\u escapes)');
for (const lit of reqLits) {
  // A required literal must not trip a forbidden group even before the allowlist, except the groups
  // whose words the disclosure uses only in the negative ("not investment advice", "not gravity.li",
  // "no referral codes"), which the allowlist step removes.
  const negated = ['investment_advice', 'gravity_branding', 'referral_code_generation_or_storage'];
  const hits = scan(lit, 'rendered_text', compiled, { allowlist: false }).filter((h) => !negated.includes(h.group));
  ok(hits.length === 0, `required literal trips forbidden group ${hits.map((h) => h.group)}: ${lit}`);
}
for (const id of ['earnings_estimate', 'take_rate_calculator', 'ni_neng_na', 'guaranteed_income', 'bi_zhuan', 'multiplier_10000x', 'referral_code_generation_or_storage', 'outbound_ref_via_code_params', 'urgency_ui', 'confetti', 'neon', 'live_badge', 'countdown', 'join_cta', 'honesty_bar_hidden', 'freshness_claim_without_evidence', 'investment_advice', 'gravity_branding'])
  ok(L.forbidden.some((g) => g.id === id), `lexicon lacks group ${id}`);

// 4. Copy -----------------------------------------------------------------------
const C = B.copy;
for (const k of ['title', 'subtitle', 'filters', 'empty_state', 'row_labels', 'source_label', 'reason_label', 'stale_state', 'internal_links', 'footer'])
  ok(C[k] && JSON.stringify(C[k]).includes('"zh"') && JSON.stringify(C[k]).includes('"en"'), `copy.${k} lacks zh/en`);
const disp = (o) => `${o.zh} / ${o.en}`;
ok(C.title.zh === '关门博物馆' && C.title.en === 'Closed Programs Museum', 'title');
ok(disp(C.internal_links.back_to_claim_shredder) === '回到 Claim Shredder / Back to Claim Shredder', 'shredder link text');
ok(disp(C.internal_links.view_rules_board) === '查看规则板 / View rules board', 'rules link text');
ok(disp(C.footer.short_line) === '仅供参考，不构成投资建议 / For information only; not investment advice', 'footer short line');
ok(disp(C.stale_state.label) === '复核已过期 / Last check has expired', 'stale label');
ok(disp(C.unconfirmed_state.label) === '待核对 / Unconfirmed', 'unconfirmed label');
ok(C.as_of_unverified === UNVERIFIED_AS_OF, 'unverified literal');
ok(/standing_disclosure/.test(C.footer.disclosure), 'footer.disclosure must point at standing_disclosure');
ok(reqLits.includes(brief.standing_disclosure.zh) && reqLits.includes(brief.standing_disclosure.en), 'standing_disclosure must be required_copy literals');

// Every UI string (copy, labels, seed text, disclosure) must pass the lexicon as rendered text.
const META_KEYS = new Set(['link_text_rule', 'order', 'href', 'display_rule', 'element', 'placement', 'disclosure']);
const uiStrings = [];
(function collect(o, path) {
  if (typeof o === 'string') uiStrings.push([path, o]);
  else if (Array.isArray(o)) o.forEach((v, i) => collect(v, `${path}[${i}]`));
  else if (o && typeof o === 'object') for (const [k, v] of Object.entries(o)) if (!META_KEYS.has(k)) collect(v, `${path}.${k}`);
})({ copy: C, label_set: brief.label_set.map(({ zh, en, display }) => ({ zh, en, display })), disclosure: brief.standing_disclosure, seed: B.data_contract.seed.map((r) => ({ program: r.program, why: r.why_not_joinable })) }, '');
for (const [path, s] of uiStrings) {
  const probe = s.replace(/\{(shown|total|n)\}/g, '3');
  for (const scope of ['rendered_text', 'control_names']) for (const h of scan(probe, scope, compiled)) errors.push(`UI copy trips lexicon [${h.group}] at ${path}: ${JSON.stringify(h.match)}`);
}

// Disclosure content requirements.
const dz = brief.standing_disclosure.zh, de = brief.standing_disclosure.en;
for (const w of ['独立站点', '并非 gravity.li', '无关联', '认可或背书', '官方页面为准', '变更', '推荐码', '推荐参数', '不计算', '承诺', '仅供参考', '不构成投资建议', '法律', '税务']) ok(dz.includes(w), `disclosure.zh lacks ${w}`);
for (const w of ['independent site', 'not gravity.li', 'not affiliated', 'endorsed', 'Official pages prevail', 'change', 'referral codes', 'referral parameters', 'calculated', 'promised', 'For information only', 'not investment advice', 'legal', 'tax advice']) ok(de.includes(w), `disclosure.en lacks ${w}`);

// 5. Contrast (WCAG 2.x) ----------------------------------------------------------
const tok = B.ia.tokens;
const lum = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };
const contrast = [];
for (const fg of ['--text', '--muted', '--chip-closed', '--chip-capped', '--chip-geo']) for (const bg of ['--bg', '--surface']) {
  const r = ratio(tok[fg], tok[bg]);
  contrast.push(`${fg} on ${bg}: ${r.toFixed(2)}`);
  ok(r >= 4.5, `contrast ${fg} on ${bg} = ${r.toFixed(2)} < 4.5`);
}
for (const fg of ['--focus', '--field-border']) for (const bg of ['--bg', '--surface']) ok(ratio(tok[fg], tok[bg]) >= 3, `non-text contrast ${fg} on ${bg} < 3`);
ok(ratio(tok['--bg'], tok['--text']) >= 4.5, 'inverse pill (bg on text)');
ok(Object.entries({ '--bg': '#0B0E12', '--surface': '#10151B', '--hairline': '#1F2630', '--text': '#DCE1E8', '--muted': '#8C96A4', '--chip-closed': '#B97474', '--chip-capped': '#C8A45E', '--chip-geo': '#8C96A4' }).every(([k, v]) => tok[k] === v), 'tokens match the specified board tokens');

// 6. Seed -----------------------------------------------------------------------
const seed = B.data_contract.seed;
const byId = Object.fromEntries(seed.map((r) => [r.id, r]));
ok(eqSet(byId['notion-affiliate']?.status || [], ['closed']), 'notion closed');
ok(eqSet(byId['ibkr-refer-a-friend']?.status || [], ['capped', 'geo_excluded']), 'ibkr capped+geo');
ok(eqSet(byId['binance-referral-fee-share']?.status || [], ['geo_excluded']), 'binance geo');
for (const r of seed) {
  const v = validateRow(r, { context: 'seed' });
  ok(v.valid, `seed ${r.id} invalid: ${v.code} ${v.detail}`);
  ok(r.page_read === false && r.verified_on === null && r.as_of === UNVERIFIED_AS_OF, `seed ${r.id} must be unverified (no official page was read)`);
  ok(freshness(r, '2026-09-23') === 'unconfirmed', `seed ${r.id} freshness`);
  ok(r.why_not_joinable.zh.includes(HEDGE_ZH) && r.why_not_joinable.en.toLowerCase().includes(HEDGE_EN), `seed ${r.id} hedge`);
  const text = JSON.stringify({ p: r.program, w: r.why_not_joinable });
  ok(!/\d|%|[$€£¥]/.test(text), `seed ${r.id} states a number/amount/rate`);
  for (const k of ['status', 'as_of', 'source_url', 'page_read', 'verified_on', 'why_not_joinable']) ok(Object.hasOwn(r, k), `seed ${r.id} lacks ${k}`);
}

// 7. Fixtures -------------------------------------------------------------------
const patchedKeys = new Set();
let staleFixture = false;
for (const f of brief.fixtures) {
  ok(f.row && f.expect && f.client_date, `fixture ${f.id} shape`);
  const v = validateRow(f.row, { context: f.context === 'production_seed' ? 'seed' : 'fixtures' });
  ok(v.valid === f.expect.valid, `fixture ${f.id}: valid=${v.valid} expected ${f.expect.valid} (${v.code} ${v.detail || ''})`);
  if (!f.expect.valid) ok(v.code === f.expect.error_code, `fixture ${f.id}: code ${v.code} expected ${f.expect.error_code}`);
  if (f.expect.valid) {
    const fr = freshness(f.row, f.client_date);
    ok(fr === f.expect.freshness, `fixture ${f.id}: freshness ${fr} expected ${f.expect.freshness}`);
    if (f.expect.days_since_check !== undefined) ok(daysBetween(f.row.verified_on, f.client_date) === f.expect.days_since_check, `fixture ${f.id} days`);
    ok(f.expect.attributes && Object.keys(f.expect.attributes).length > 0, `fixture ${f.id} asserts attributes`);
    if (fr === 'stale' && f.row.page_read === true && daysBetween(f.row.verified_on, f.client_date) > 90) staleFixture = true;
  }
  ok(f.expect.cta_count === 0, `fixture ${f.id} must assert cta_count 0`);
  const base = f.mutation_of && byId[f.mutation_of];
  ok(!f.patch, `fixture ${f.id} must not carry a patch (row is the source of truth)`);
  if (base) for (const k of new Set([...Object.keys(base), ...Object.keys(f.row)])) if (JSON.stringify(base[k]) !== JSON.stringify(f.row[k])) patchedKeys.add(k);
}
for (const id of ['FX-01-notion-closed', 'FX-02-ibkr-capped-geo', 'FX-03-binance-geo']) {
  const f = brief.fixtures.find((x) => x.id === id);
  ok(f, `fixture ${id} missing`);
  if (f) {
    ok(f.expect.visible_text_includes.includes(UNVERIFIED_AS_OF), `${id} asserts visible as_of`);
    ok(f.expect.source_href === f.row.source_url && f.expect.source_href_search === '' && f.expect.source_href_hash === '', `${id} asserts source href`);
    ok(f.expect.why_not_joinable_nonempty?.zh && f.expect.why_not_joinable_nonempty?.en, `${id} asserts reasons`);
  }
}
ok(staleFixture, 'a stale fixture with page_read=true and verified_on > 90 days is required');
for (const k of ['verified_on', 'page_read', 'status', 'source_url']) ok(patchedKeys.has(k), `no fixture mutates ${k}`);

// 8. Label set ------------------------------------------------------------------
for (const l of brief.label_set) ok(l.id && l.zh && l.en && l.display, `label ${l.id}`);
for (const d of ['已停招 Closed', '限额 Capped', '限地区 Geo-limited', '复核已过期 / Last check has expired', '待核对 / Unconfirmed', UNVERIFIED_AS_OF])
  ok(brief.label_set.some((l) => l.display === d), `label_set lacks ${d}`);

// 9. Acceptance -----------------------------------------------------------------
const A = JSON.stringify(B.acceptance);
for (const needle of [
  `document.querySelectorAll('[data-museum-row] [data-cta=\\"join\\"], [data-museum-row] [data-cta=\\"apply\\"]').length`,
  '1440', '360', 'rg -n', 'reqs', 'reducedMotion', '\\\\x{4F60}\\\\x{80FD}\\\\x{62FF}', 'data-why-not-joinable', 'screenshot', '点击 ≠ 收入 / Clicks ≠ income', '仅供参考，不构成投资建议 / For information only; not investment advice',
]) ok(A.includes(needle), `acceptance lacks ${needle}`);
ok(B.acceptance.every((t) => t.id && t.title && Array.isArray(t.steps) && t.pass && t.fails_if), 'acceptance items need id/title/steps/pass/fails_if');

// Report --------------------------------------------------------------------------
const cjk = (raw.match(/[　-鿿＀-￯]/g) || []).length;
console.log(`brief: ${raw.length} bytes pretty, ${JSON.stringify(brief).length} minified, ~${Math.round((JSON.stringify(brief).length - cjk) / 3.6 + cjk * 1.3)} tokens`);
console.log('contrast: ' + contrast.join(' | '));
if (errors.length) { console.error(`\n${errors.length} problem(s):`); for (const e of errors) console.error(' - ' + e); process.exit(1); }
console.log('brief OK');
