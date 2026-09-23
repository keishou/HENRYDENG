// Pure row validation and freshness logic for the Closed Programs Museum.
// Shared by the build, the validator and (inlined) the browser runtime.

export const UNVERIFIED_AS_OF = '未核实 / Not yet checked against the official page';
export const FRESHNESS_WINDOW_DAYS = 90;
export const HEDGE_ZH = '尚未对照官方页面核对';
export const HEDGE_EN = 'not yet checked against the official page';
export const STATUS_ORDER = ['closed', 'capped', 'geo_excluded'];
export const OFFICIAL_DOMAINS = {
  notion: ['www.notion.com', 'notion.com'],
  ibkr: ['www.interactivebrokers.com', 'investors.interactivebrokers.com', 'ndcdyn.interactivebrokers.com'],
  binance: ['www.binance.com'],
};

const ALLOWED_KEYS = new Set(['id', 'org', 'program', 'status', 'as_of', 'source_url', 'page_read', 'verified_on', 'why_not_joinable', 'fixture_only']);
const ISO = /^\d{4}-\d{2}-\d{2}$/;
// CJK written as escapes so the shipped bundle never contains the banned words themselves.
const MONEY_OR_RATE = /[$\u20AC\u00A3\u00A5%]|\b(USD|HKD|CNY|EUR|GBP)\b|\u7F8E\u5143|\u6E2F\u5143|\u4EBA\u6C11\u5E01|\u5143|\u767E\u5206\u4E4B/;

export function isIsoDate(s) {
  if (typeof s !== 'string' || !ISO.test(s)) return false;
  const [y, m, d] = s.split('-').map(Number);
  const t = new Date(Date.UTC(y, m - 1, d));
  return t.getUTCFullYear() === y && t.getUTCMonth() === m - 1 && t.getUTCDate() === d;
}

function utc(s) {
  const [y, m, d] = s.split('-').map(Number);
  return Date.UTC(y, m - 1, d);
}

export function daysBetween(from, to) {
  return (utc(to) - utc(from)) / 86_400_000;
}

export function freshness(row, clientDate) {
  if (row.page_read !== true) return 'unconfirmed';
  if (!isIsoDate(row.verified_on) || !isIsoDate(clientDate)) return 'unconfirmed';
  const days = daysBetween(row.verified_on, clientDate);
  if (days < 0) return 'unconfirmed';
  return days <= FRESHNESS_WINDOW_DAYS ? 'current' : 'stale';
}

export function recheckDue(verifiedOn) {
  if (!isIsoDate(verifiedOn)) return null;
  return new Date(utc(verifiedOn) + FRESHNESS_WINDOW_DAYS * 86_400_000).toISOString().slice(0, 10);
}

const fail = (code, detail) => ({ valid: false, code, detail });

// Returns { valid: true } or { valid: false, code, detail }. Checks run in a fixed
// order so each fixture maps to exactly one error code.
export function validateRow(row, { context = 'seed' } = {}) {
  if (!row || typeof row !== 'object') return fail('MUSEUM_E_FORBIDDEN_KEY', 'row is not an object');
  for (const k of Object.keys(row)) if (!ALLOWED_KEYS.has(k)) return fail('MUSEUM_E_FORBIDDEN_KEY', k);
  if (row.fixture_only !== undefined && (row.fixture_only !== true || context !== 'fixtures'))
    return fail('MUSEUM_E_FIXTURE_IN_SEED', row.id);
  if (typeof row.id !== 'string' || !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(row.id)) return fail('MUSEUM_E_ID', row.id);
  if (!Object.hasOwn(OFFICIAL_DOMAINS, row.org)) return fail('MUSEUM_E_ID', `org ${row.org}`);
  if (!row.program || !String(row.program.zh || '').trim() || !String(row.program.en || '').trim())
    return fail('MUSEUM_E_ID', 'program name');

  // INV-01 status
  if (!Array.isArray(row.status) || row.status.length < 1 || row.status.length > 3 ||
      new Set(row.status).size !== row.status.length || !row.status.every((s) => STATUS_ORDER.includes(s)))
    return fail('MUSEUM_E_STATUS', JSON.stringify(row.status));

  // INV-03 source
  let u;
  try { u = new URL(row.source_url); } catch { return fail('MUSEUM_E_SOURCE', 'unparseable'); }
  if (u.protocol !== 'https:' || u.search !== '' || u.hash !== '' || u.username || u.password || u.port ||
      row.source_url.includes('?') || row.source_url.includes('#') ||
      !OFFICIAL_DOMAINS[row.org].includes(u.hostname))
    return fail('MUSEUM_E_SOURCE', row.source_url);

  // INV-06 verified_on
  if (typeof row.page_read !== 'boolean') return fail('MUSEUM_E_VERIFIED_ON', 'page_read not boolean');
  if (row.verified_on !== null && !isIsoDate(row.verified_on)) return fail('MUSEUM_E_VERIFIED_ON', row.verified_on);
  if (row.page_read === true && row.verified_on === null) return fail('MUSEUM_E_VERIFIED_ON', 'page_read without date');

  // INV-05 hedge / unread rows carry no date
  const zh = String(row.why_not_joinable?.zh ?? '');
  const en = String(row.why_not_joinable?.en ?? '');
  if (row.page_read !== true) {
    if (row.verified_on !== null) return fail('MUSEUM_E_HEDGE', 'verified_on set while page_read is false');
  }

  // INV-02 as_of
  const expectedAsOf = row.page_read === true ? row.verified_on : UNVERIFIED_AS_OF;
  if (typeof row.as_of !== 'string' || row.as_of.trim() === '' || row.as_of !== expectedAsOf)
    return fail('MUSEUM_E_AS_OF', row.as_of);

  // INV-04 reason
  if (!zh.trim() || !en.trim() || zh.length > 90 || en.length > 220) return fail('MUSEUM_E_REASON', 'empty or too long');
  if (MONEY_OR_RATE.test(zh) || MONEY_OR_RATE.test(en)) return fail('MUSEUM_E_REASON', 'money or rate');
  const digitsOutsideDates = (s) => /\d/.test(s.replace(/\d{4}-\d{2}-\d{2}/g, ''));
  if (digitsOutsideDates(zh) || digitsOutsideDates(en)) return fail('MUSEUM_E_REASON', 'digits');
  if (row.page_read !== true && (!zh.includes(HEDGE_ZH) || !en.toLowerCase().includes(HEDGE_EN)))
    return fail('MUSEUM_E_HEDGE', 'unverified reason lacks hedge');

  return { valid: true };
}
