#!/usr/bin/env node
// Static build for the Closed Programs Museum reference page.
//   node reference/build.mjs                     → dist/lab/museum/index.html from the brief's seed
//   node reference/build.mjs --fixtures          → dist-fixtures/lab/museum/index.html from valid fixtures
//   node reference/build.mjs --inject FX-10      → seed + one fixture row; exits 1 if that row is invalid
// Every row is validated first; any invalid row fails the whole build (no partial output).
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { validateRow, freshness, recheckDue, UNVERIFIED_AS_OF } from './museum-core.mjs';
import { renderRow, esc, bi, biText } from './museum-render.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '..');
const args = process.argv.slice(2);
const flag = (name) => args.includes(name);
const opt = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };

const brief = JSON.parse(readFileSync(join(root, 'brief.json'), 'utf8'));
const B = brief.compose_closed_programs_museum;
const C = B.copy;

const fixturesMode = flag('--fixtures');
const context = fixturesMode ? 'fixtures' : 'seed';
let rows = fixturesMode ? brief.fixtures.filter((f) => f.expect.valid).map((f) => f.row) : [...B.data_contract.seed];
if (opt('--inject')) {
  const f = brief.fixtures.find((x) => x.id === opt('--inject'));
  if (!f) { console.error(`unknown fixture ${opt('--inject')}`); process.exit(2); }
  rows.push(f.row);
}
const outDir = resolve(root, opt('--out') || (fixturesMode ? 'dist-fixtures' : 'dist'));

// 1. Validate — fail the build on any invalid row.
const ids = new Set();
let failed = false;
for (const row of rows) {
  const v = validateRow(row, { context });
  if (ids.has(row.id)) { console.error(`MUSEUM_E_ID duplicate ${row.id}`); failed = true; }
  ids.add(row.id);
  if (!v.valid) { console.error(`${v.code} ${row.id}: ${v.detail}`); failed = true; }
}
if (failed) process.exit(1);

// 2. Pre-render: static default freshness is always "unconfirmed"; the client upgrades it.
const sortKey = (r) => (/^\d{4}-\d{2}-\d{2}$/.test(r.as_of) ? r.as_of : '');
rows.sort((a, b) => {
  const da = sortKey(a), db = sortKey(b);
  if (da !== db) return da && db ? (da < db ? 1 : -1) : da ? -1 : 1;
  return a.program.en.localeCompare(b.program.en, 'en');
});
const cards = rows.map((r) => renderRow(r, 'unconfirmed', null)).join('\n');

const p = (o) => bi([o.zh, o.en]);
const disp = (o) => `${o.zh} / ${o.en}`;
const radios = (name, opts) =>
  Object.entries(opts).map(([value, o], i) =>
    `<label class="pill"><input type="radio" name="${name}" value="${value}"${i === 0 ? ' checked' : ''}><span>${esc(o.zh)} / <span lang="en">${esc(o.en)}</span></span></label>`).join('');

const F = C.filters;
const D = C.footer;
const nonAffil = (text, lit) => `<span data-non-affiliation>${esc(lit)}</span>${esc(text.slice(lit.length))}`;

const html = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; form-action 'none'; base-uri 'none'">
<link rel="icon" href="data:,">
<title>${esc(B.ia.document_title)}</title>
<style>${readFileSync(join(here, 'museum.css'), 'utf8')}</style>
</head>
<body data-context="${context}">
<a class="skip-link" href="#collection">${p(C.skip_link)}</a>
<div class="page">
<header role="banner" data-museum-header>
<p class="crumbs">${biText(C.breadcrumb.display)}</p>
<h1>${esc(C.title.zh)} <span lang="en" class="en">${esc(C.title.en)}</span></h1>
<p class="subtitle">${esc(C.subtitle.zh)} <span lang="en" class="en">${esc(C.subtitle.en)}</span></p>
</header>
<main id="main">
<section data-museum-intro aria-labelledby="museum-label">
<p id="museum-label" class="museum-label">${p(C.museum_label)}</p>
<p class="purpose">${esc(C.purpose.zh)} <span lang="en" class="en">${esc(C.purpose.en)}</span></p>
</section>
<p role="note" data-honesty-bar aria-label="${esc(disp(C.honesty_bar.aria_label))}"><strong>${biText(C.honesty_bar.literal)}</strong></p>
<div class="board">
<form role="search" data-filter-form aria-labelledby="filter-heading" hidden>
<h2 id="filter-heading">${p(F.region_heading)}</h2>
<div class="field field-search"><label for="museum-q">${p(F.search_label)}</label>
<input type="search" id="museum-q" name="q" autocomplete="off" spellcheck="false" placeholder="${esc(disp(F.search_placeholder))}" aria-describedby="museum-q-hint">
<p id="museum-q-hint" class="hint">${p(F.search_hint)}</p></div>
<fieldset><legend>${p(F.status_legend)}</legend><div class="pills">${radios('status', F.status_options)}</div></fieldset>
<fieldset><legend>${p(F.freshness_legend)}</legend><div class="pills">${radios('freshness', F.freshness_options)}</div></fieldset>
<div class="field"><label for="museum-sort">${p(F.sort_label)}</label>
<select id="museum-sort" name="sort" aria-describedby="museum-sort-hint">${Object.entries(F.sort_options).map(([v, o]) => `<option value="${v}">${esc(disp(o))}</option>`).join('')}</select>
<p id="museum-sort-hint" class="hint">${p(F.sort_note)}</p></div>
<button type="reset">${p(F.clear)}</button>
</form>
<section id="collection" aria-labelledby="collection-heading" tabindex="-1">
<h2 id="collection-heading">${p(C.collection_heading)}</h2>
<p role="status" aria-live="polite" data-result-count tabindex="-1">显示 ${rows.length} / ${rows.length} 件 · <span lang="en">Showing ${rows.length} of ${rows.length}</span></p>
<p data-rejected-notice hidden></p>
<ol class="cards" data-museum-list>
${cards}
</ol>
<div data-empty-state hidden><p><strong>${p(C.empty_state.title)}</strong></p><p>${p(C.empty_state.body)}</p><button type="button" data-clear>${p(C.empty_state.action)}</button></div>
</section>
</div>
<nav data-internal-nav aria-label="${esc(disp(C.internal_links.nav_label))}">
<ul><li><a href="${esc(C.internal_links.back_to_claim_shredder.href)}">${p(C.internal_links.back_to_claim_shredder)}</a></li><li><a href="${esc(C.internal_links.view_rules_board.href)}">${p(C.internal_links.view_rules_board)}</a></li></ul>
<p class="hint">${p(C.internal_links.reopened_note)}</p>
</nav>
</main>
</div>
<p data-disclosure-strip aria-hidden="true">${p(D.short_line)}</p>
<footer role="contentinfo" data-standing-disclosure id="disclosure"><div class="page">
<p data-nia-short>${p(D.short_line)}</p>
<h2>${p(D.disclosure_heading)}</h2>
<p lang="zh-CN" data-disclosure-body>${nonAffil(brief.standing_disclosure.zh, D.non_affiliation_literal.zh)}</p>
<p lang="en" data-disclosure-body>${nonAffil(brief.standing_disclosure.en, D.non_affiliation_literal.en)}</p>
<p class="hint">${p(D.data_note)}</p>
</div></footer>
<script>
${[readFileSync(join(here, 'museum-core.mjs'), 'utf8'), readFileSync(join(here, 'museum-render.mjs'), 'utf8')]
  .map((s) => s.replace(/^export\s+/gm, ''))
  .join('\n')}
${readFileSync(join(here, 'museum-runtime.js'), 'utf8')}
</script>
</body>
</html>
`;

if (html.includes(UNVERIFIED_AS_OF) === false && rows.some((r) => r.page_read !== true)) {
  console.error('unverified literal missing from output');
  process.exit(1);
}
mkdirSync(join(outDir, 'lab', 'museum'), { recursive: true });
writeFileSync(join(outDir, 'lab', 'museum', 'index.html'), html);
console.log(`built ${rows.length} row(s) → ${join(outDir, 'lab', 'museum', 'index.html')} (context=${context})`);
