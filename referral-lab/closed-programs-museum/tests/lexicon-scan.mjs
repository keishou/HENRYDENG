#!/usr/bin/env node
// Lexicon scanner for the Closed Programs Museum.
//   node tests/lexicon-scan.mjs dist/            → self-test, then scan every built file; exit 1 on any hit
// Exports compile/selfTest/scan helpers for the validator and the Playwright suite.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, resolve, dirname, extname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));

export function loadLexicon(briefPath = resolve(here, '..', 'brief.json')) {
  const brief = JSON.parse(readFileSync(briefPath, 'utf8'));
  return brief.compose_closed_programs_museum.lexicon;
}

const withG = (flags) => (flags.includes('g') ? flags : flags + 'g');

export function compile(lexicon) {
  const allow = [
    ...lexicon.required_copy.map((r) => r.literal),
    ...lexicon.forbidden.flatMap((g) => g.allowlisted_literals || []),
  ].sort((a, b) => b.length - a.length);
  const groups = lexicon.forbidden.map((g) => ({
    ...g,
    res: g.patterns.map((p) => new RegExp(p.source, withG(p.flags))),
    rowRes: (g.row_scope_patterns || []).map((p) => new RegExp(p.source, withG(p.flags))),
  }));
  return { allow, groups };
}

const normalize = (text) => String(text).normalize('NFC').replace(/[\u2018\u2019\u02BC]/g, "'");

export function applyAllowlist(text, compiled) {
  let t = normalize(text);
  for (const lit of compiled.allow) t = t.split(lit.normalize('NFC')).join(' ');
  return t;
}

// scope: rendered_text | control_names | hrefs | built_assets | built_css | row_text_not_current
export function scan(text, scope, compiled, { allowlist = scope !== 'hrefs' } = {}) {
  const t = allowlist ? applyAllowlist(text, compiled) : normalize(text);
  const hits = [];
  for (const g of compiled.groups) {
    const res = [];
    if (g.scopes.includes(scope)) res.push(...g.res);
    if (scope === 'row_text_not_current') res.push(...g.rowRes);
    for (const re of res) {
      re.lastIndex = 0;
      for (const m of t.matchAll(re)) hits.push({ group: g.id, scope, match: m[0] });
    }
  }
  return hits;
}

export function selfTest(compiled) {
  const errors = [];
  for (const g of compiled.groups) {
    const all = [...g.res, ...g.rowRes];
    for (const s of g.should_match || []) {
      if (!all.some((re) => { re.lastIndex = 0; return re.test(s); })) errors.push(`${g.id}: should_match not matched: ${s}`);
    }
    for (const s of g.should_not_match || []) {
      const t = applyAllowlist(s, compiled);
      for (const re of all) { re.lastIndex = 0; if (re.test(t)) errors.push(`${g.id}: should_not_match matched ${re}: ${s}`); }
    }
  }
  return errors;
}

const decode = (s) => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');

// Split an HTML file into scannable pieces: script bodies, style bodies, attribute values, text.
export function htmlPieces(html) {
  const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map((m) => m[1]);
  const styles = [...html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)].map((m) => m[1]);
  const rest = html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, ' ').replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, ' ');
  const attrs = [...rest.matchAll(/\s[\w:-]+="([^"]*)"/g)].map((m) => decode(m[1]));
  const text = decode(rest.replace(/<[^>]+>/g, ''));
  return { scripts, styles, attrs, text };
}

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) yield* walk(p);
    else yield p;
  }
}

export function scanDist(dir, compiled) {
  const hits = [];
  for (const file of walk(dir)) {
    const ext = extname(file);
    const src = readFileSync(file, 'utf8');
    const add = (h) => hits.push(...h.map((x) => ({ ...x, file })));
    if (ext === '.html') {
      const { scripts, styles, attrs, text } = htmlPieces(src);
      for (const s of scripts) add(scan(s, 'built_assets', compiled));
      for (const s of styles) { add(scan(s, 'built_assets', compiled)); add(scan(s, 'built_css', compiled)); }
      for (const a of attrs) { add(scan(a, 'built_assets', compiled)); add(scan(a, 'hrefs', compiled)); }
      add(scan(text, 'built_assets', compiled));
    } else if (ext === '.css') {
      add(scan(src, 'built_assets', compiled)); add(scan(src, 'built_css', compiled));
    } else if (['.js', '.mjs', '.json', '.svg'].includes(ext)) {
      add(scan(src, 'built_assets', compiled));
    }
  }
  return hits;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const dir = resolve(process.argv[2] || resolve(here, '..', 'dist'));
  const compiled = compile(loadLexicon());
  const errs = selfTest(compiled);
  if (errs.length) { console.error('LEXICON SELF-TEST FAILED'); for (const e of errs) console.error('  ' + e); process.exit(1); }
  const hits = scanDist(dir, compiled);
  if (hits.length) {
    console.error(`LEXICON HITS in ${dir}:`);
    for (const h of hits) console.error(`  [${h.group}/${h.scope}] ${h.file}: ${JSON.stringify(h.match)}`);
    process.exit(1);
  }
  console.log(`lexicon: self-test ok, 0 hits in ${dir}`);
}
