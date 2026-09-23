// Generates brief.json, the single source of truth for the Closed Programs Museum brief.
// Regex sources are escaped to ASCII here, so edit this file and re-run `npm run generate`.
import { writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = process.argv[2] || resolve(dirname(fileURLToPath(import.meta.url)), '..', 'brief.json');

// ---------------------------------------------------------------------------
// Shared literals
// ---------------------------------------------------------------------------
const HONESTY = '点击 ≠ 收入 / Clicks ≠ income';
const NIA_SHORT = '仅供参考，不构成投资建议 / For information only; not investment advice';
const UNVERIFIED = '未核实 / Not yet checked against the official page';
const STALE = '复核已过期 / Last check has expired';
const UNCONFIRMED = '待核对 / Unconfirmed';
const CURRENT = '来源已读取，90 天内已核对 / Source read; checked within 90 days';
const BACK_SHREDDER = '回到 Claim Shredder / Back to Claim Shredder';
const VIEW_RULES = '查看规则板 / View rules board';
const SOURCE_LABEL = '官方来源 / Official source';
const CANDIDATE = '候选链接 / Candidate link';
const HEDGE_ZH = '尚未对照官方页面核对';
const HEDGE_EN = 'not yet checked against the official page';

const DISCLOSURE = {
  zh: '本站为独立站点，并非 gravity.li，与所列公司均无关联，也未获其认可或背书。计划状态以各公司官方页面为准，条款可能随时变更。本站不提供任何推荐码或推荐参数，不计算、不承诺任何收入。仅供参考，不构成投资建议，也不构成法律或税务建议。',
  en: 'This is an independent site, not gravity.li, and is not affiliated with or endorsed by any company listed. Official pages prevail, and terms can change at any time. No referral codes or referral parameters are provided here, and no income is calculated or promised. For information only; not investment advice, and not legal or tax advice.',
};
const NON_AFFIL = { zh: '本站为独立站点，并非 gravity.li', en: 'This is an independent site, not gravity.li' };

const CLIENT_DATE = '2026-09-23';

const ROUTES = {
  museum: '/lab/museum',
  claim_shredder: '/lab/claim-shredder',
  rules_board: '/lab/rules-board',
};

const OFFICIAL_DOMAINS = {
  notion: ['www.notion.com', 'notion.com'],
  ibkr: ['www.interactivebrokers.com', 'investors.interactivebrokers.com', 'ndcdyn.interactivebrokers.com'],
  binance: ['www.binance.com'],
};

const pair = (zh, en) => ({ zh, en });
const disp = (p) => `${p.zh} / ${p.en}`;

// ---------------------------------------------------------------------------
// Seed rows. Each fact is either the product brief's listed status or a candidate
// URL located by search on 2026-09-23. No official page could be read (the
// domains were egress-blocked), so every row is page_read=false / verified_on=null.
// ---------------------------------------------------------------------------
const SEED = [
  {
    id: 'notion-affiliate',
    org: 'notion',
    program: pair('Notion 联盟计划', 'Notion Affiliate Program'),
    status: ['closed'],
    as_of: UNVERIFIED,
    source_url: 'https://www.notion.com/affiliates',
    page_read: false,
    verified_on: null,
    why_not_joinable: pair(
      `本馆记录为已停招：不再接受新成员。${HEDGE_ZH}，以官方页面为准。`,
      'Recorded here as closed: no longer taking new members. Not yet checked against the official page, which prevails.'
    ),
  },
  {
    id: 'ibkr-refer-a-friend',
    org: 'ibkr',
    program: pair('盈透证券推荐好友计划', 'IBKR Refer-a-Friend'),
    status: ['capped', 'geo_excluded'],
    as_of: UNVERIFIED,
    source_url: 'https://www.interactivebrokers.com/en/trading/referral-member-to-member.php',
    page_read: false,
    verified_on: null,
    why_not_joinable: pair(
      `本馆记录为限额且限地区：计划设有上限，部分地区不适用。${HEDGE_ZH}，以官方页面为准。`,
      'Recorded here as capped and geo-limited: the program has a cap and excludes some regions. Not yet checked against the official page, which prevails.'
    ),
  },
  {
    id: 'binance-referral-fee-share',
    org: 'binance',
    program: pair('币安推荐手续费分成', 'Binance Referral Fee-share'),
    status: ['geo_excluded'],
    as_of: UNVERIFIED,
    source_url: 'https://www.binance.com/en/support/faq/terms-and-conditions-for-binance-referral-program-d06a66559cdd4185aea360752405633e',
    page_read: false,
    verified_on: null,
    why_not_joinable: pair(
      `本馆记录为限地区：推荐手续费分成在部分司法辖区不可用。${HEDGE_ZH}，以官方页面为准。`,
      'Recorded here as geo-limited: the referral fee-share is unavailable in some jurisdictions. Not yet checked against the official page, which prevails.'
    ),
  },
];

// ---------------------------------------------------------------------------
// Copy
// ---------------------------------------------------------------------------
const COPY = {
  display_rule: 'Each {zh, en} pair renders as zh + " / " + en with the English half in <span lang="en">, unless the pair gives its own display. Status chips use a single space (spec literal). <option> text and aria-label values use the same combined string without markup. Tagging the English half never changes innerText, so the exact literals still match.',
  document_title: '关门博物馆 / Closed Programs Museum · Referral Lab',
  skip_link: pair('跳到馆藏', 'Skip to the collection'),
  breadcrumb: { display: 'Referral Lab › 关门博物馆 / Closed Programs Museum', element: '<p class="crumbs"> plain text, not a nav landmark' },
  title: pair('关门博物馆', 'Closed Programs Museum'),
  subtitle: pair('已停招、限额或限地区的推荐计划存档。', 'An archive of closed, capped, or geo-limited referral programs.'),
  museum_label: pair('馆藏档案 · 均不可加入', 'Archive · none can be joined'),
  purpose: pair(
    '这里把不可加入的计划留作反例存档，逐条写明状态、核对日期、官方来源和不可加入的原因，供对照规则板时参考。',
    'Programs that cannot be joined are kept here as counterexamples, each with its status, check date, official source, and the reason it cannot be joined, for reference alongside the rules board.'
  ),
  honesty_bar: { literal: HONESTY, aria_label: pair('归因说明', 'Attribution note') },
  filters: {
    region_heading: pair('筛选馆藏', 'Filter the collection'),
    search_label: pair('搜索计划名称', 'Search program names'),
    search_placeholder: pair('例如 Notion', 'e.g. Notion'),
    search_hint: pair('只在本页内筛选，不发送任何请求。', 'Filters this page only; nothing is sent anywhere.'),
    status_legend: pair('状态', 'Status'),
    status_options: {
      all: pair('全部', 'All'),
      closed: pair('已停招', 'Closed'),
      capped: pair('限额', 'Capped'),
      geo_excluded: pair('限地区', 'Geo-limited'),
    },
    freshness_legend: pair('核对状态', 'Check status'),
    freshness_options: {
      all: pair('全部', 'All'),
      current: pair('90 天内已核对', 'Checked within 90 days'),
      stale: pair('复核已过期', 'Last check has expired'),
      unconfirmed: pair('待核对', 'Unconfirmed'),
    },
    sort_label: pair('排序', 'Sort'),
    sort_options: { checked_desc: pair('最近核对在前', 'Latest check first'), name_asc: pair('名称 A–Z', 'Name A–Z') },
    sort_note: pair('未核实的记录排在最后。', 'Unverified records are listed last.'),
    clear: pair('清除筛选', 'Clear filters'),
    result_count: { zh: '显示 {shown} / {total} 件', en: 'Showing {shown} of {total}', display: '显示 {shown} / {total} 件 · Showing {shown} of {total}' },
  },
  collection_heading: pair('馆藏', 'Collection'),
  empty_state: {
    title: pair('没有符合条件的馆藏', 'No items match'),
    body: pair('请调整筛选条件，或清除搜索。', 'Adjust the filters or clear the search.'),
    action: pair('清除筛选', 'Clear filters'),
  },
  empty_collection: pair('馆藏暂为空。', 'The collection is empty for now.'),
  rejected_notice: { zh: '{n} 条记录未通过校验，未显示。', en: '{n} record(s) failed validation and are not shown.' },
  row_labels: {
    status: pair('状态', 'Status'),
    as_of: pair('核对日期', 'Checked'),
    page_read: pair('来源读取', 'Page read'),
    page_read_true: pair('已读取', 'Read'),
    page_read_false: pair('未读取', 'Not read'),
    verified_on: pair('最近复核', 'Last verified'),
    verified_on_none: pair('尚未复核', 'Not yet verified'),
    freshness: pair('核对状态', 'Check status'),
    recheck_due: pair('复核截止', 'Re-check due'),
    check_record: pair('核对记录', 'Check record'),
    freshness_rule: pair('规则：已读取官方页面，且复核日期距今不超过 90 天，才算已核对。', 'Rule: a record counts as checked only when the official page was read and the last verification is no more than 90 days old.'),
  },
  status_chips: { closed: '已停招 Closed', capped: '限额 Capped', geo_excluded: '限地区 Geo-limited', order: ['closed', 'capped', 'geo_excluded'] },
  source_label: {
    label: pair('官方来源', 'Official source'),
    candidate_qualifier: pair('候选链接', 'Candidate link'),
    new_tab_hint: pair('（在新标签页打开）', '(opens in a new tab)'),
    link_text_rule: `Visible link text is the URL host + pathname without "https://" (e.g. "www.notion.com/affiliates"). The label above it always reads ${SOURCE_LABEL}, followed by the muted qualifier ${CANDIDATE} when page_read !== true.`,
  },
  reason_label: { label: pair('为何不可加入', 'Why not joinable'), wall_label_caption: pair('展签', 'Wall label') },
  as_of_unverified: UNVERIFIED,
  stale_state: {
    label: pair('复核已过期', 'Last check has expired'),
    helper: pair('上次核对已超过 90 天。此记录仅作存档，现状未经确认。', 'The last check is more than 90 days old. This record is kept for the archive; its current status is unconfirmed.'),
  },
  unconfirmed_state: { label: pair('待核对', 'Unconfirmed'), helper: pair('请以官方页面为准。', 'The official page prevails.') },
  current_state: {
    label: pair('来源已读取，90 天内已核对', 'Source read; checked within 90 days'),
    helper: pair('核对较新只说明记录没有过期；该计划仍不可加入。', 'A recent check only means this record has not expired; the program still cannot be joined.'),
  },
  internal_links: {
    nav_label: pair('Referral Lab 内部导航', 'Referral Lab internal links'),
    back_to_claim_shredder: { zh: '回到 Claim Shredder', en: 'Back to Claim Shredder', href: ROUTES.claim_shredder },
    view_rules_board: { zh: '查看规则板', en: 'View rules board', href: ROUTES.rules_board },
    inbound: { zh: '查看关门博物馆', en: 'View the Closed Programs Museum', href: ROUTES.museum, placement: 'Exactly once on routes.claim_shredder and once on routes.rules_board, as a plain text link.' },
    reopened_note: pair('若某计划重新开放，它会移出本馆，并在规则板上重新核对。', 'If a program reopens, it leaves this museum and is re-checked on the rules board.'),
  },
  footer: {
    short_line: pair('仅供参考，不构成投资建议', 'For information only; not investment advice'),
    disclosure_heading: pair('声明', 'Disclosure'),
    disclosure: 'Renders the top-level standing_disclosure.zh and .en verbatim.',
    non_affiliation_literal: NON_AFFIL,
    data_note: pair('本页所有筛选均在浏览器内完成，不做统计或追踪。', 'All filtering happens in your browser; nothing is tracked or measured.'),
  },
};

// ---------------------------------------------------------------------------
// Label set (canonical registry of every rendered label/state)
// ---------------------------------------------------------------------------
const L = (id, kind, zh, en, extra = {}) => ({ id, kind, zh, en, display: `${zh} / ${en}`, ...extra });
const LABEL_SET = [
  { id: 'status.closed', kind: 'status_chip', data_value: 'closed', zh: '已停招', en: 'Closed', display: '已停招 Closed', token: '--chip-closed', hex: '#B97474' },
  { id: 'status.capped', kind: 'status_chip', data_value: 'capped', zh: '限额', en: 'Capped', display: '限额 Capped', token: '--chip-capped', hex: '#C8A45E' },
  { id: 'status.geo_excluded', kind: 'status_chip', data_value: 'geo_excluded', zh: '限地区', en: 'Geo-limited', display: '限地区 Geo-limited', token: '--chip-geo', hex: '#8C96A4' },
  L('freshness.current', 'freshness_state', '来源已读取，90 天内已核对', 'Source read; checked within 90 days', { data_value: 'current' }),
  L('freshness.stale', 'freshness_state', '复核已过期', 'Last check has expired', { data_value: 'stale' }),
  L('freshness.unconfirmed', 'freshness_state', '待核对', 'Unconfirmed', { data_value: 'unconfirmed' }),
  L('as_of.unverified', 'as_of_literal', '未核实', 'Not yet checked against the official page'),
  L('page_read.true', 'page_read_state', '已读取', 'Read', { data_value: 'true' }),
  L('page_read.false', 'page_read_state', '未读取', 'Not read', { data_value: 'false' }),
  L('field.status', 'row_label', '状态', 'Status'),
  L('field.as_of', 'row_label', '核对日期', 'Checked'),
  L('field.page_read', 'row_label', '来源读取', 'Page read'),
  L('field.verified_on', 'row_label', '最近复核', 'Last verified'),
  L('field.freshness', 'row_label', '核对状态', 'Check status'),
  L('field.source', 'row_label', '官方来源', 'Official source'),
  L('field.source_candidate', 'row_qualifier', '候选链接', 'Candidate link'),
  L('field.why_not_joinable', 'row_label', '为何不可加入', 'Why not joinable'),
  L('field.wall_label', 'row_label', '展签', 'Wall label'),
  L('field.recheck_due', 'row_label', '复核截止', 'Re-check due'),
  L('field.check_record', 'disclosure_summary', '核对记录', 'Check record'),
  L('bar.honesty', 'required_copy', '点击 ≠ 收入', 'Clicks ≠ income'),
  L('footer.not_investment_advice', 'required_copy', '仅供参考，不构成投资建议', 'For information only; not investment advice'),
  L('nav.back_to_claim_shredder', 'internal_link', '回到 Claim Shredder', 'Back to Claim Shredder', { href: ROUTES.claim_shredder }),
  L('nav.view_rules_board', 'internal_link', '查看规则板', 'View rules board', { href: ROUTES.rules_board }),
  L('nav.inbound_museum', 'internal_link', '查看关门博物馆', 'View the Closed Programs Museum', { href: ROUTES.museum }),
];

// ---------------------------------------------------------------------------
// Lexicon: forbidden groups with self-tests; required copy acts as an allowlist.
// Non-ASCII characters in pattern sources are emitted as \uXXXX / \u{XXXXX} escapes so
// the lexicon is ASCII-only and never matches itself when scanned.
// ---------------------------------------------------------------------------
const escapeNonAscii = (s) =>
  s.replace(/[^\x00-\x7F]/gu, (c) => {
    const cp = c.codePointAt(0);
    return cp > 0xffff ? `\\u{${cp.toString(16).toUpperCase()}}` : `\\u${cp.toString(16).toUpperCase().padStart(4, '0')}`;
  });
const P = (re) => ({ source: escapeNonAscii(re.source), flags: re.flags });

const REQUIRED_COPY = [
  { id: 'RC-honesty', literal: HONESTY, where: '[data-honesty-bar] on every route/view' },
  { id: 'RC-nia-short', literal: NIA_SHORT, where: 'footer[data-standing-disclosure] [data-nia-short] (plus body > [data-disclosure-strip])' },
  { id: 'RC-nia-phrase', literal: 'not investment advice', where: 'inside RC-nia-short and standing_disclosure.en' },
  { id: 'RC-disclosure-zh', literal: DISCLOSURE.zh, where: 'footer [data-disclosure-body][lang="zh-CN"]' },
  { id: 'RC-disclosure-en', literal: DISCLOSURE.en, where: 'footer [data-disclosure-body][lang="en"]' },
  { id: 'RC-back-shredder', literal: BACK_SHREDDER, where: `nav[data-internal-nav] a[href="${ROUTES.claim_shredder}"]` },
  { id: 'RC-view-rules', literal: VIEW_RULES, where: `nav[data-internal-nav] a[href="${ROUTES.rules_board}"]` },
  { id: 'RC-source-label', literal: SOURCE_LABEL, where: 'every [data-museum-row]' },
  { id: 'RC-as-of-unverified', literal: UNVERIFIED, where: '[data-field="as_of"] whenever page_read !== true' },
  { id: 'RC-stale', literal: STALE, where: '[data-freshness="stale"] [data-field="freshness"]' },
  { id: 'RC-unconfirmed', literal: UNCONFIRMED, where: '[data-freshness="unconfirmed"] [data-field="freshness"]' },
];

const FORBIDDEN = [
  {
    id: 'earnings_estimate',
    bans: 'earnings estimates, income forecasts, reward amounts framed as what the reader gets',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [
      P(/(预计|预估|预期|估算|潜在|每月可|每年可)\s*(收益|收入|佣金|返佣|奖励)|(?<![\d〇一二三四五六七八九十]\s*)[月年]入/u),
      P(/\b(estimated|projected|potential|expected|monthly|annual|passive)\s+(earnings|income|commissions?|payouts?|rewards?)\b/i),
      P(/\bearnings?\s+(estimates?|estimators?|projections?|forecasts?)\b/i),
      P(/\b(earn|make)\s+(up\s+to\s+)?(US)?[$€£¥]\s?\d/i),
      P(/(US)?[$€£¥]\s?\d[\d,.]*\s*(\/|per|每)\s*(mo|month|yr|year|referral|friend|月|年|人)/iu),
    ],
    should_match: ['预计收益 ¥3,000', 'Estimated earnings', 'earnings estimator', 'earn up to $500', '$200 per referral', '月入过万', '轻松月入3万'],
    should_not_match: ['本页不计算、不预测任何收入。', 'This page does not calculate or forecast any income.', '9月入馆', '2026 年入藏'],
  },
  {
    id: 'take_rate_calculator',
    bans: 'take-rate / commission calculators',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [
      P(/take[\s-]?rates?/i),
      P(/\b(commission|payout|referral|earnings?|income|rebate|kickback|fee[\s-]?share)\s+(calculator|estimator|simulator)\b/i),
      P(/\bcalculators?\b/i),
      P(/计算器|测算器|(抽成|分成|佣金|返佣)(比例)?\s*(计算|测算)/u),
    ],
    dom_checks: ['document.querySelectorAll(\'input[type="number"], input[type="range"], output\').length === 0'],
    should_match: ['take rate', 'Take-rate', 'commission calculator', '佣金计算器', '分成比例测算'],
    should_not_match: ['This page does not calculate or forecast any income.', 'Referral Fee-share', 'clip-path: inset(50%)'],
  },
  {
    id: 'rate_or_percentage',
    bans: 'any percentage, fee-share rate, take rate or currency amount in visible text (stylesheet percentages are not text and are out of scope)',
    scopes: ['rendered_text', 'control_names'],
    patterns: [
      P(/\d\s*[%％]|百分之|\bper\s?cent\b/iu),
      P(/(US)?[$€£¥￥]\s?\d|\d\s*(元|美元|港元)|\d\s*(USD|HKD|CNY|USDT)\b/iu),
    ],
    should_match: ['up to 40% commission', '20％', '百分之二十', '30 percent', '每位好友 ￥50', '50美元', '每邀请一位好友奖励 ¥50'],
    should_not_match: ['显示 3 / 3 件 · Showing 3 of 3', '2026-09-23'],
  },
  {
    id: 'ni_neng_na',
    bans: '「你能拿」 and "you can earn/get" personal-outcome framing',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [
      P(/你能拿/u),
      P(/[你您](可以|能|将|会)(拿|赚|获得|领)/u),
      P(/\byou(\s+will|'ll|\s+can|\s+could)\s+(earn|make|get\s+paid|receive|pocket)\b/i),
    ],
    unicode_escaped: { '你能拿': '\\u4F60\\u80FD\\u62FF' },
    should_match: ['你能拿多少', '你可以赚', '您可以赚到佣金', 'you can earn', "you'll receive"],
    should_not_match: ['为何不可加入 / Why not joinable', 'None of them can be joined'],
  },
  {
    id: 'guaranteed_income',
    bans: 'guaranteed income, risk-free or passive-income claims',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [
      P(/\bguarantee(d|s)?\b/i),
      P(/\b(risk[\s-]?free|passive\s+income|sure\s+(win|profit))\b/i),
      P(/(保证|保障|确保)(收入|收益|回报)|稳赚|保本|躺赚|被动收入/u),
    ],
    unicode_escaped: { '保证收入': '\\u4FDD\\u8BC1\\u6536\\u5165', '稳赚': '\\u7A33\\u8D5A' },
    should_match: ['guaranteed income', 'risk-free', '保证收入', '稳赚', '被动收入'],
    should_not_match: ['no income is calculated or promised', '点击 ≠ 收入'],
  },
  {
    id: 'bi_zhuan',
    bans: '必赚 and sure-profit variants',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [P(/必赚|包赚|稳赚/u)],
    unicode_escaped: { '必赚': '\\u5FC5\\u8D5A' },
    should_match: ['必赚', '包赚'],
    should_not_match: ['本页不计算、不预测任何收入。'],
  },
  {
    id: 'multiplier_10000x',
    bans: '10000x and any N×/N倍 multiplier hype',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [P(/10,?000\s*[x×]/i), P(/\b\d[\d,]*\s*[x×](?![a-z0-9])/i), P(/[\d一二三四五六七八九十百千万亿]+\s*倍|翻倍/u)],
    should_match: ['10000x', '10,000×', '100x returns', '100倍', '1万倍', '翻倍'],
    should_not_match: ['2026-09-23', 'www.binance.com/en/support/faq/terms-and-conditions-for-binance-referral-program-d06a66559cdd4185aea360752405633e'],
  },
  {
    id: 'referral_code_generation_or_storage',
    bans: 'generating, storing, inferring, copying, shortening or displaying referral/invite/founder codes',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [
      P(/\b(referral|invite|invitation|promo|founder|ref|affiliate)[\s_-]?codes?\b/i),
      P(/(推荐|邀请|优惠|创始人|专属)码/u),
      P(/navigator\.(clipboard|share)\b/),
      P(/(localStorage|sessionStorage|indexedDB|document\.cookie)/),
    ],
    dom_checks: [
      "document.querySelectorAll('input:not([type=\"search\"]):not([type=\"radio\"]), textarea').length === 0",
      "[...document.querySelectorAll('input, select, textarea')].every(el => !/code|ref|via|invite|\\u7801/i.test([el.name, el.id, el.placeholder, el.getAttribute('aria-label') || ''].join(' ')))",
    ],
    should_match: ['referral_code', 'referralCode', 'inviteCode', 'Referral code: MUSEUM50', '邀请码', '推荐码', 'navigator.clipboard.writeText(x)', "localStorage.setItem('ref','x')"],
    should_not_match: ['Referral Fee-share'],
  },
  {
    id: 'outbound_ref_via_code_params',
    bans: 'ref / via / code (and other referral or tracking) parameters on outbound links; this feature has no user-typed {own_link}',
    tokens: ['ref', 'via', 'code'],
    scopes: ['hrefs', 'built_assets'],
    patterns: [
      P(/[?&](ref|via|code|referral|referral_code|ref_code|invite|invite_code|inviter|aff|aff_id|affiliate|partner|utm_[a-z]+)=/i),
      P(/\{own_link\}/),
    ],
    should_match: ['https://www.notion.com/affiliates?ref=abc', 'https://x.com/a&via=me', '?code=FOUNDER', '{own_link}'],
    should_not_match: ['https://www.notion.com/affiliates', 'https://www.interactivebrokers.com/en/trading/referral-member-to-member.php'],
  },
  {
    id: 'control_label_ref_via_code',
    bans: 'bare ref / via / code tokens in any control label, link text or accessible name',
    tokens: ['ref', 'via', 'code'],
    scopes: ['control_names'],
    patterns: [P(/\b(ref|via|code)\b/i)],
    should_match: ['Copy code', 'via Notion', 'Add ref'],
    should_not_match: ['www.interactivebrokers.com/en/trading/referral-member-to-member.php', 'Referral Fee-share', SOURCE_LABEL],
  },
  {
    id: 'urgency_ui',
    bans: 'urgency and scarcity pressure (hurry, last chance, limited time, only N left, closing soon, join now)',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [
      P(/\b(hurry|act\s+now|last\s+chance|limited[\s-]time|ending\s+soon|ends?\s+(today|tonight|soon)|only\s+\d+\s+(left|spots?|places?)|don'?t\s+miss|before\s+it'?s\s+gone|today\s+only|fomo)\b/i),
      P(/\b(closing\s+soon|(a\s+)?few\s+(spots?|places?)\s+left)\b|赶紧|即将(关闭|结束|截止)/iu),
      P(/限时|最后机会|仅剩|抓紧|马上|赶快|立即|错过|即将截止|名额有限|先到先得|手慢无/u),
    ],
    dom_checks: ["document.querySelectorAll('marquee, blink, [role=\"timer\"], [data-urgency]').length === 0"],
    unicode_escaped: { '限时': '\\u9650\\u65F6', '立即': '\\u7ACB\\u5373' },
    should_match: ['Hurry', 'last chance', 'limited-time offer', 'only 3 left', 'Closing soon', 'Only a few spots left', '限时', '名额有限', '立即加入', '赶紧加入'],
    should_not_match: ['限地区 Geo-limited', '限额 Capped', 'Last check has expired', '复核已过期'],
  },
  {
    id: 'confetti',
    bans: 'confetti, celebration effects and hype emoji',
    scopes: ['rendered_text', 'built_assets'],
    patterns: [P(/confetti|party[\s-]?popper|fireworks|\u{1F389}|\u{1F38A}|\u{1F680}|\u{1F525}|\u{1F4B0}|\u{1F4B8}|\u{1F911}|\u2728/iu)],
    should_match: ['canvas-confetti', 'confetti()', '🎉', '🚀', '💰'],
    should_not_match: ['关门博物馆 / Closed Programs Museum'],
  },
  {
    id: 'neon',
    bans: 'neon, glow, shadows and any colour outside the tokens',
    scopes: ['built_css', 'rendered_text'],
    patterns: [
      P(/\bneon\b/i),
      P(/\bglow(ing)?\b/i),
      P(/text-shadow\s*:(?!\s*none\b)/i),
      P(/drop-shadow\(/i),
      P(/box-shadow\s*:(?!\s*none\b)/i),
    ],
    dom_checks: [
      'every element: getComputedStyle(el).textShadow === "none" && getComputedStyle(el).boxShadow === "none"',
      "rg -o --pcre2 '#[0-9A-Fa-f]{3,8}\\b|rgba?\\(|hsla?\\(' dist/ returns only values listed in ia.tokens",
    ],
    should_match: ['.x{text-shadow:0 0 8px #0ff}', 'neon', 'box-shadow: 0 0 5px 3px #0ff', '.chip{box-shadow:0 0 1rem var(--chip-geo)}', 'filter: drop-shadow(0 0 4px red)'],
    should_not_match: ['text-shadow: none', 'box-shadow: none', 'outline: 2px solid var(--focus)'],
  },
  {
    id: 'live_badge',
    bans: 'LIVE badges, live data and real-time claims',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [P(/\bLIVE\b/), P(/\blive\s+(now|data|price|prices|rates?|feed|status|updates?)\b/i), P(/直播|实时/u)],
    note: 'Case-sensitive for the uppercase badge, so the attribute aria-live="polite" in built assets never matches; live_word adds the case-insensitive check on visible text only.',
    should_match: ['LIVE', 'live data', '实时', '直播'],
    should_not_match: ['aria-live="polite"', 'Last verified', 'Delivered'],
  },
  {
    id: 'live_word',
    bans: 'live / real-time claims in visible text, any case',
    scopes: ['rendered_text', 'control_names'],
    patterns: [P(/\b(live|real[\s-]?time)\b/i)],
    should_match: ['Live', 'Real-time status'],
    should_not_match: ['Delivered', 'Last verified'],
  },
  {
    id: 'countdown',
    bans: 'countdowns, timers and ticking clocks',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [P(/count[\s-]?down/i), P(/倒计时/u), P(/\b\d{1,2}:\d{2}:\d{2}\b/), P(/\bsetInterval\s*\(/)],
    unicode_escaped: { '倒计时': '\\u5012\\u8BA1\\u65F6' },
    dom_checks: ["document.querySelectorAll('[role=\"timer\"], [data-countdown]').length === 0"],
    should_match: ['countdown', 'Count-down', '倒计时', '02:14:59', 'setInterval(tick, 1000)'],
    should_not_match: ['2026-09-23', 'Latest check first'],
  },
  {
    id: 'join_cta',
    bans: 'join / apply / sign-up / become-a-member / open-an-account / share / copy calls to action anywhere in a museum row',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [
      P(/(立即|马上|现在|点击)(加入|申请|注册|领取)/u),
      P(/\b(join|apply|sign\s*up|register|enroll)\s+(now|today|here|free|for\s+free)\b/i),
      P(/\b(learn\s+how\s+to\s+join|get\s+started|claim\s+(your|now)|get\s+your\s+link|share\s+(your\s+)?link)\b/i),
      P(/如何加入|加入计划|申请加入|获取链接|分享链接|复制链接/u),
      P(/^\s*(?:(加入|申请|注册|分享|复制|成为|开户)|(join|apply|sign\s*up|register|share|copy|invite|become|open\s+an?\s+account|start\s+(referring|earning))\b)/iu),
      P(/\b(become\s+an?\s+(affiliate|partner|referrer|member)|open\s+an?\s+account)\b|成为(推广者|联盟|会员)|开户/iu),
    ],
    dom_checks: [
      "document.querySelectorAll('[data-museum-row] [data-cta=\"join\"], [data-museum-row] [data-cta=\"apply\"]').length === 0",
      "document.querySelectorAll('[data-museum-row] :is([data-cta], button, input, select, textarea, form, [role=\"button\"], [role=\"link\"]:not(a))').length === 0",
      "[...document.querySelectorAll('[data-museum-row]')].every(r => r.querySelectorAll('a').length === 1 && r.querySelectorAll('a[data-source-link]').length === 1)",
      "[...document.querySelectorAll('[data-museum-row] *')].filter(el => !el.closest('a[data-source-link], summary') && (el.hasAttribute('onclick') || el.hasAttribute('tabindex') || getComputedStyle(el).cursor === 'pointer')).length === 0",
    ],
    should_match: ['立即加入', '点击申请', 'Join now', 'Apply today', 'Learn how to join', 'Share your link', '如何加入', 'Join', 'Copy link', '成为推广者 / Become an affiliate', '去官网开户 / Open an account'],
    should_not_match: ['为何不可加入 / Why not joinable', 'None of them can be joined', VIEW_RULES],
  },
  {
    id: 'honesty_bar_hidden',
    bans: 'hiding, shrinking, transforming, fading or collapsing 点击 ≠ 收入 / Clicks ≠ income',
    scopes: ['built_css'],
    patterns: [
      P(/\[data-honesty-bar\][^{]*\{[^}]*(display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*(0|\.)|transform\s*:(?!\s*none\b)|clip(-path)?\s*:|font-size\s*:\s*(?!\s)(?!(1[3-9]|[2-9]\d)(\.\d+)?px\b|inherit\b)|height\s*:\s*0)/i),
    ],
    dom_checks: [
      "const b = document.querySelector('[data-honesty-bar]'); b.innerText.includes('点击 ≠ 收入 / Clicks ≠ income') && !b.closest('[hidden], [aria-hidden=\"true\"], details:not([open])')",
      "[b, ...b.querySelectorAll('*')].every(e => { const s = getComputedStyle(e); return s.opacity === '1' && s.transform === 'none' && s.visibility === 'visible' && s.display !== 'none' && parseFloat(s.fontSize) >= 13; })",
      "every ancestor of b computes opacity '1' and transform 'none'",
      'b.getBoundingClientRect() has height ≥ 24 and ≤ 48 and lies fully inside the viewport at scrollY = 0 and after window.scrollTo(0, document.body.scrollHeight)',
    ],
    should_match: ['[data-honesty-bar]{display:none}', '[data-honesty-bar] { opacity: 0 }', '[data-honesty-bar]{opacity:0.01}', '[data-honesty-bar]{font-size:10px}', '[data-honesty-bar] strong{font-size:30%}', '[data-honesty-bar]{transform:scale(.06)}'],
    should_not_match: ['[data-honesty-bar]{position:sticky;top:0;opacity:1}', '[data-honesty-bar]{font-size:15px}'],
  },
  {
    id: 'freshness_claim_without_evidence',
    bans: 'claiming freshness or current availability without page_read === true and verified_on within 90 days; claiming any museum row is joinable',
    scopes: ['rendered_text', 'row_text_not_current'],
    patterns: [
      P(/现可加入|仍可加入|目前开放|正在招募|仍在运营|已恢复|重新开放招募/u),
      P(/\b(currently|still|now)\s+(available|open|active|accepting|joinable)\b/i),
      P(/\b(up[\s-]to[\s-]date|verified\s+(today|current)|is\s+joinable|can\s+be\s+joined\s+(now|today))\b/i),
    ],
    row_scope_patterns: [P(/已核实|最新|来源已读取，90 天内已核对|Source read; checked within 90 days|\bfresh\b/i)],
    row_scope: '[data-museum-row]:not([data-freshness="current"])',
    dom_checks: [
      "[...document.querySelectorAll('[data-museum-row][data-freshness=\"current\"]')].every(r => r.dataset.pageRead === 'true' && /^\\d{4}-\\d{2}-\\d{2}$/.test(r.dataset.verifiedOn) && (Date.parse(document.body.dataset.clientDate) - Date.parse(r.dataset.verifiedOn)) / 864e5 <= 90)",
    ],
    should_match: ['现可加入', 'currently accepting', 'still open', 'up to date', 'is joinable'],
    should_not_match: ['None of them can be joined', 'the program still cannot be joined', 'If a program reopens, it leaves this museum and is re-checked on the rules board.', '若某计划重新开放，它会移出本馆，并在规则板上重新核对。'],
  },
  {
    id: 'investment_advice',
    bans: 'any investment advice or trade/account recommendation',
    scopes: ['rendered_text', 'control_names', 'built_assets'],
    patterns: [
      P(/(?<!not\s)\binvestment\s+advice\b/i),
      P(/(?<!不构成)投资建议/u),
      P(/\b(you\s+should|we\s+recommend|recommended\s+to)\s+(buy|sell|hold|invest|trade|open\s+an\s+account|deposit)\b/i),
      P(/\b(strong\s+buy|price\s+target|to\s+the\s+moon)\b/i),
      P(/买入|卖出|抄底|梭哈|上车|(建议|推荐)你?(开户|入金|投资)/u),
    ],
    note: 'Negative lookbehinds keep "not investment advice" and "不构成投资建议" legal; the full disclosure literals are removed by the allowlist step first.',
    should_match: ['investment advice: buy BTC', '投资建议：买入', 'you should buy', 'we recommend open an account', '建议你开户'],
    should_not_match: [NIA_SHORT, 'For information only; not investment advice'],
  },
  {
    id: 'gravity_branding',
    bans: 'gravity.li / GRAVITY branding, links, logos or names outside the allowlisted non-affiliation clause',
    tokens: ['gravity.li', 'GRAVITY'],
    scopes: ['rendered_text', 'hrefs', 'control_names', 'built_assets'],
    patterns: [P(/gravity\.li/i), P(/\bGRAVITY\b/), P(/gravity/i)],
    dom_checks: [
      "document.querySelectorAll('a[href*=\"gravity\" i], img[src*=\"gravity\" i], img[alt*=\"gravity\" i], [class*=\"gravity\" i]').length === 0",
      'every text node matching /gravity/i has an ancestor [data-non-affiliation] whose textContent is exactly an allowlisted literal; document.querySelectorAll("[data-non-affiliation]").length === 2',
    ],
    allowlisted_literals: [NON_AFFIL.zh, NON_AFFIL.en],
    should_match: ['gravity.li', 'GRAVITY', 'Powered by Gravity', 'https://gravity.li/r/x'],
    should_not_match: ['关门博物馆 / Closed Programs Museum'],
  },
];

const LEXICON = {
  version: '1.1.0',
  engine: 'ECMAScript RegExp (Node >= 20 / evergreen browsers). CJK is written as \\u escapes; rg equivalents use --pcre2 with \\x{....}.',
  procedure: [
    '1. Collect text per scope. rendered_text = document.body.innerText plus every aria-label / title / placeholder / alt value, in every AT-07 view. control_names = accessible name + visible text + name/id/placeholder of every a, button, input, select, textarea, summary and [role]. hrefs = every a[href], area[href], form[action] resolved with new URL(). built_assets = every css/js/json/svg file under dist/ as-is; for each .html file, its tag-stripped, entity-decoded text, each attribute value, and each <script>/<style> body, scanned separately. built_css = dist/**/*.css plus inline <style> bodies. row_text_not_current = innerText of each [data-museum-row]:not([data-freshness="current"]).',
    '2. Normalize with String.prototype.normalize("NFC"), then map U+2018, U+2019 and U+02BC to \'.',
    '3. Allowlist step: remove every required_copy literal and every allowlisted_literal (longest first, all occurrences) before scanning every scope except hrefs, which are never allowlisted.',
    '4. Run every forbidden pattern whose scopes include the scope (add the g flag when scanning). Any match fails the build and prints the group id, scope, file or selector, and matched text.',
    '4b. Evaluate every group\'s dom_checks in each AT-07 view. Any false result fails the build.',
    '5. Self-test first: every should_match sample must match its group, and no should_not_match sample (after the allowlist step) may match it. Otherwise the lexicon is broken and the build fails.',
    '6. The lexicon lives in tests/, never in dist/, so a dist scan cannot match its own definitions.',
  ],
  required_copy: REQUIRED_COPY,
  forbidden: FORBIDDEN,
  literal_token_index: {
    'gravity.li': 'gravity_branding',
    GRAVITY: 'gravity_branding',
    '你能拿': 'ni_neng_na',
    '必赚': 'bi_zhuan',
    '10000x': 'multiplier_10000x',
    ref: 'outbound_ref_via_code_params + control_label_ref_via_code',
    via: 'outbound_ref_via_code_params + control_label_ref_via_code',
    code: 'outbound_ref_via_code_params + control_label_ref_via_code + referral_code_generation_or_storage',
    LIVE: 'live_badge + live_word',
    countdown: 'countdown',
    'earnings estimates': 'earnings_estimate',
    'take-rate calculators': 'take_rate_calculator + rate_or_percentage',
    'guaranteed income': 'guaranteed_income',
    'urgency UI': 'urgency_ui',
    confetti: 'confetti',
    neon: 'neon',
    'join CTA': 'join_cta',
    'hiding 点击 ≠ 收入 / Clicks ≠ income': 'honesty_bar_hidden',
    'freshness without page_read and verified_on': 'freshness_claim_without_evidence',
    'investment advice': 'investment_advice',
  },
};

// ---------------------------------------------------------------------------
// IA
// ---------------------------------------------------------------------------
const TOKENS = {
  '--bg': '#0B0E12',
  '--surface': '#10151B',
  '--hairline': '#1F2630',
  '--text': '#DCE1E8',
  '--muted': '#8C96A4',
  '--chip-closed': '#B97474',
  '--chip-capped': '#C8A45E',
  '--chip-geo': '#8C96A4',
  '--focus': '#DCE1E8',
  '--field-border': '#8C96A4',
};

const IA = {
  route: ROUTES.museum,
  document_title: COPY.document_title,
  rendering: 'Static pre-render at build time into one self-contained document. Every valid seed row is emitted as HTML, together with the honesty bar and the standing disclosure. A small inline script then (a) computes freshness from data-page-read, data-verified-on and the client date and relabels each row, and (b) filters, searches and sorts by toggling the hidden attribute and reordering the <li> elements. The script holds no row data and makes no network calls. Without JavaScript every row keeps the build-time default data-freshness="unconfirmed" (待核对 / Unconfirmed), and the filter form stays hidden, so nothing is ever shown as fresh by default.',
  client_date: 'window.__MUSEUM_CLIENT_DATE__ (YYYY-MM-DD, injected by tests), otherwise the local calendar date. It is written to <body data-client-date>.',
  order: [
    { n: 1, id: 'header', element: '<header role="banner" data-museum-header>', content: `Skip link 跳到馆藏 / Skip to the collection; breadcrumb line <p class="crumbs">${COPY.breadcrumb.display}</p> (not a nav); <h1>关门博物馆 <span lang="en">Closed Programs Museum</span></h1>; one-line subtitle. Height ≤ 152px at 1440px and ≤ 176px at 360px.` },
    { n: 2, id: 'museum_label', element: '<section data-museum-intro aria-labelledby="museum-label">', content: 'The museum label 馆藏档案 · 均不可加入 / Archive · none can be joined (12/16, --muted, letter-spacing .08em, 1px --hairline top rule), then the one-sentence purpose (zh 15/24, en 13/20 --muted).' },
    { n: 3, id: 'honesty_bar', element: '<p role="note" data-honesty-bar aria-label="归因说明 / Attribution note">', content: 'The exact literal 点击 ≠ 收入 / Clicks ≠ income and nothing else (15/24, weight 500, --text). Full-width 1px --hairline top and bottom borders on --bg, 8px vertical padding, ≈42px tall and ≤ 48px at every width. position: sticky; top: 0; z-index 2. It cannot be dismissed or collapsed, and is never inside <details>.' },
    { n: 4, id: 'filters', element: '<form role="search" data-filter-form aria-labelledby="filter-heading" hidden>', content: 'Heading 筛选馆藏 / Filter the collection; <input type="search" name="q" id="museum-q">; status radios name="status" (all | closed | capped | geo_excluded, default all); check-status radios name="freshness" (all | current | stale | unconfirmed, default all); <select name="sort"> (checked_desc default | name_asc); <button type="reset">; hint lines. The form has no action or method, and its submit event calls preventDefault(). It ships hidden and only the script reveals it. Search matches the zh and en program names, case-insensitive, after NFKC normalisation and trim. The status filter matches rows whose status array includes the value. checked_desc sorts ISO as_of newest first, then unverified rows, with ties broken by the English name.' },
    { n: 5, id: 'collection', element: '<section id="collection" tabindex="-1" aria-labelledby="collection-heading"><ol data-museum-list>', content: 'Heading 馆藏 / Collection; live result count; [data-rejected-notice] (hidden); an ordered list of <li><article data-museum-row>; [data-empty-state] (hidden) containing its own Clear filters button.' },
    { n: 6, id: 'internal_nav', element: '<nav data-internal-nav aria-label="Referral Lab 内部导航 / Referral Lab internal links">', content: `Two plain text links: ${BACK_SHREDDER} → ${ROUTES.claim_shredder} and ${VIEW_RULES} → ${ROUTES.rules_board}; then the reopened note in --muted. The inbound link 查看关门博物馆 / View the Closed Programs Museum → ${ROUTES.museum} appears once on each of those two routes.` },
    { n: 7, id: 'footer', element: '<footer role="contentinfo" data-standing-disclosure id="disclosure">', content: 'The short line (exact literal) in [data-nia-short]; heading 声明 / Disclosure; <p lang="zh-CN" data-disclosure-body> and <p lang="en" data-disclosure-body> render standing_disclosure verbatim, each with its non-affiliation clause wrapped in <span data-non-affiliation>; the data note. The visual strip <p data-disclosure-strip aria-hidden="true"> with the short line (position: sticky; bottom: 0; 12/16; padding 4px 16px; ≤ 44px even when it wraps at 320–360px) is a direct child of <body>, immediately before <footer> and never inside it, because sticky positioning is clamped to its parent.' },
  ],
  landmarks: [
    'banner = <header>',
    'main = <main id="main"> wraps sections 2 to 6',
    'search = <form role="search"> (the filter rail, nested inside main)',
    'region = <section id="collection" aria-labelledby="collection-heading">',
    'navigation "Referral Lab 内部导航 / Referral Lab internal links"',
    'contentinfo = <footer>',
  ],
  layout: {
    wide: {
      min_width: 1024,
      container: 'max-width 1200px, centered, 32px side gutters',
      grid: 'Sections 1 to 3 span full width. Below them a CSS grid: grid-template-columns: 280px minmax(0, 1fr); column-gap: 32px. Left: the filter rail (align-self: start). It is position: sticky; top: 56px only under @media (min-height: 840px), and static otherwise, because the ≈700px rail must never sit under the disclosure strip. Right: the collection column (max-width 760px). Sections 6 and 7 span full width below.',
      card_internal: 'From 768px the card uses a two-column grid, minmax(0, 1fr) for identity and wall label and 280px for the facts <dl>, with a 24px gap, so each card reads like a catalogue table row. Card padding 20px 24px.',
      one_screen_budget: 'One scrolling board, with no tabs, pagination or second route. At 1440×900 the header, museum label, honesty bar, filter heading, search box and the top of the first card are above the fold. The honesty bar stays pinned at the top and the disclosure strip at the bottom.',
    },
    medium: {
      range: '640–1023px',
      container: '24px side gutters, single column',
      grid: 'The filter form becomes one wrapping row above the cards: search at 100% width, then the radio groups and sort wrap (flex-wrap: wrap; gap 12px 24px). Cards are full width. They use the two-column internal grid from 768px and stack below it.',
    },
    narrow: {
      max_width: 639,
      container: '16px side gutters; nothing is wider than 100vw − 32px; long URLs use overflow-wrap: anywhere. html and body keep overflow-x: visible, so overflow is never clipped away and hidden from the checks.',
      grid: 'Single column. The search input is full width. Radio options render as wrapping outline pills with min-height 44px; the visible pill is the hit area. At every width the checked pill is filled: label:has(input:checked) { background: var(--text); color: var(--bg); border-color: var(--text) } (14.7:1). Under @media (forced-colors: active) it also gets outline: 3px solid Highlight. Cards stack in this order: name, chips, wall label, facts <dl> (each <dt> above its <dd>). Card padding 16px.',
      sticky: 'Honesty bar sticky at top (literal only, ≈42px, ≤ 48px at every width). Disclosure strip sticky at bottom (≤ 44px). @media (max-height: 480px) switches the bar, the strip and the filter rail to position: static, so zoomed and landscape views still reflow (WCAG 1.4.10).',
    },
  },
  card: {
    element: '<li><article data-museum-row aria-labelledby="row-{id}-title" …data attributes>',
    hierarchy: [
      '1. <h3 id="row-{id}-title">: the zh program name (17/24, weight 500, --text), then <span lang="en"> the en name (13/20, --muted) on its own line.',
      '2. Status chips <ul aria-label="状态 / Status" data-field="status">: one <li class="chip chip--{status}"> per status, in the order closed, capped, geo_excluded. Outline chips: 1px border and text in the chip token, transparent background, 12/16, padding 2px 8px, radius 2px. Not interactive.',
      '3. Wall label <figure data-field="why_not_joinable" class="wall-label">: <figcaption>展签 / Wall label · 为何不可加入 / Why not joinable</figcaption> (12/16, --muted), then <p lang="zh-CN"> the zh reason (15/24, --text) and <p lang="en"> the en reason (13/20, --muted). Frame: 1px --hairline border, 12px 16px padding, --bg surface (one step darker than the card). No icon, no cross or RIP imagery, no joke.',
      `4. Facts <dl>: 核对日期 / Checked → as_of (a <time datetime> when it is an ISO date, otherwise the exact unverified literal); 来源读取 / Page read → 已读取 / Read or 未读取 / Not read; 最近复核 / Last verified → verified_on or 尚未复核 / Not yet verified; 核对状态 / Check status → the freshness label and helper; ${SOURCE_LABEL} (plus the muted ${CANDIDATE} qualifier when page_read !== true) → one plain <a data-source-link>.`,
      '5. <details data-check-record><summary>核对记录 / Check record</summary>: the freshness rule sentence; 复核截止 / Re-check due (verified_on + 90 days, only when verified_on is set); the full source URL as text. Opening it makes no request.',
    ],
    dom_example: '<article data-museum-row data-row-id="notion-affiliate" data-org="notion" data-program-zh="Notion 联盟计划" data-program-en="Notion Affiliate Program" data-status="closed" data-as-of="未核实 / Not yet checked against the official page" data-source-url="https://www.notion.com/affiliates" data-page-read="false" data-verified-on="" data-freshness="unconfirmed" data-why-not-joinable-zh="…" data-why-not-joinable-en="…" aria-labelledby="row-notion-affiliate-title">…<a data-source-link href="https://www.notion.com/affiliates" target="_blank" rel="noopener noreferrer nofollow" referrerpolicy="no-referrer">www.notion.com/affiliates<span class="vh">（在新标签页打开） / (opens in a new tab)</span></a>…</article>',
    forbidden_children: 'No button, input, select, textarea, form, [data-cta], [role=button], onclick, tabindex, pointer-cursor element, share or copy affordance, code field, or second link. The only <a> is the source link.',
    source_link_style: 'Inline text link in --text with a 1px --muted underline (text-underline-offset 3px). Transparent background, no padding box, no border, no icon button. It must never look like a button.',
    stale_treatment: 'data-freshness="stale": the card border becomes 1px dashed --muted, and the freshness value reads 复核已过期 / Last check has expired plus its helper. The card stays in place and fully readable, with no opacity change and no strikethrough.',
    unconfirmed_treatment: `data-freshness="unconfirmed": 1px dashed --hairline border; the freshness value reads 待核对 / Unconfirmed plus its helper. The ${CANDIDATE} qualifier appears under ${SOURCE_LABEL} when page_read !== true.`,
  },
  tokens: TOKENS,
  typography: {
    families: '"IBM Plex Sans", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, sans-serif',
    font_loading: 'Fonts are inlined and never fetched. @font-face src uses base64 WOFF2 data: URIs: IBM Plex Sans 400/500 as a Latin subset, and Noto Sans SC 400/500 subset to every glyph in the built copy and seed. font-display: swap; CSP font-src data:. No font file request, no preload, no third-party host. CJK typed into search that falls outside the subset uses system fonts, with no request.',
    base: '15px / 24px (zh primary text)',
    secondary_en: '13px / 20px, --muted',
    h1: '20px / 28px, weight 500',
    h3: '17px / 24px, weight 500',
    label: '12px / 16px, --muted, letter-spacing .04em',
    numerals: 'Dates use font-variant-numeric: tabular-nums and are formatted YYYY-MM-DD, never relative (not "3 days ago").',
  },
  motion: {
    allowed: 'Only opacity. A <li> re-entering after a filter change fades from 0 to 1 over 150ms linear, and an opened Check record body fades the same way. No transform, no scroll-linked motion, no looping animation.',
    reduced: '@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }',
    exempt: 'The honesty bar, footer and disclosure strip never animate.',
  },
  focus: 'Every focusable element gets outline: 2px solid var(--focus) with outline-offset: 2px, and it is never removed. The only outline: none allowed is the :focus:not(:focus-visible) mouse case. #collection:focus keeps its ring (offset 4px). The skip link becomes visible at top-left when focused. Radio pills show the ring on the label through label:has(input:focus-visible).',
  keyboard: [
    'Tab order (the breadcrumb is plain text): skip link → search → status radios (one tab stop; arrow keys move and apply) → check-status radios (one tab stop) → sort select → Clear filters → for each card, its source link then its Check record summary → Back to Claim Shredder → View rules board.',
    'Enter in search only filters: submit is prevented, so there is no navigation and no request. Esc in the search input clears the query through an explicit keydown handler, and the results update.',
    'Space or Enter on a Check record summary toggles it (native details). Filtering never moves focus, except that when the focused card becomes hidden, focus moves to the result count <p tabindex="-1">.',
    'The skip link target #collection has tabindex="-1". It receives focus and shows the 2px --focus ring.',
    'There are no keyboard traps, and the sticky bars hold nothing focusable. html { scroll-padding-top: 64px; scroll-padding-bottom: 56px } and the matching scroll-margin on :focus keep every focused element clear of the ≤ 48px bar and the ≤ 44px strip (WCAG 2.4.11).',
  ],
  aria: {
    honesty_bar: 'role="note" aria-label="归因说明 / Attribution note"',
    result_count: '<p role="status" aria-live="polite" data-result-count tabindex="-1">, written 700ms after the last input (debounced) and only when its text changes.',
    chips: '<ul aria-label="状态 / Status"> with plain <li> text. Colour is never the only signal, because each chip spells out its status.',
    source_link: 'Accessible name = visible URL text + the visually hidden （在新标签页打开） / (opens in a new tab).',
    freshness: '<dd data-field="freshness"> holds visible text; there are no icon-only states.',
    empty_state: 'Revealed by removing [hidden] and announced through the result count: 显示 0 / 3 件 · Showing 0 of 3.',
    lang: '<html lang="zh-CN">. Every bilingual string renders as zh / <span lang="en">en</span>, which leaves innerText unchanged. This covers the as_of literal, internal links, [data-nia-short], the strip and the result count. <option> text and aria-label values stay plain combined text.',
  },
  wcag_aa: 'Every text token meets 4.5:1 or better on --bg and on --surface, and the inverse checked pill (--bg on --text) passes too; tools/validate-brief.mjs checks all of these. The focus ring and field borders meet 3:1 (WCAG 1.4.11). --hairline is decorative only and is never the sole boundary of a control.',
};

// ---------------------------------------------------------------------------
// Data contract
// ---------------------------------------------------------------------------
const ROW_SCHEMA = {
  $schema: 'https://json-schema.org/draft/2020-12/schema',
  type: 'object',
  additionalProperties: false,
  required: ['id', 'org', 'program', 'status', 'as_of', 'source_url', 'page_read', 'verified_on', 'why_not_joinable'],
  properties: {
    id: { type: 'string', pattern: '^[a-z0-9]+(-[a-z0-9]+)*$' },
    org: { enum: Object.keys(OFFICIAL_DOMAINS) },
    program: { type: 'object', additionalProperties: false, required: ['zh', 'en'], properties: { zh: { type: 'string', minLength: 1, maxLength: 40 }, en: { type: 'string', minLength: 1, maxLength: 60 } } },
    status: { type: 'array', minItems: 1, maxItems: 3, uniqueItems: true, items: { enum: ['closed', 'capped', 'geo_excluded'] } },
    as_of: { oneOf: [{ type: 'string', pattern: '^\\d{4}-\\d{2}-\\d{2}$' }, { const: UNVERIFIED }] },
    source_url: { type: 'string', pattern: '^https://[a-z0-9.-]+/[^?#\\s]*$' },
    page_read: { type: 'boolean' },
    verified_on: { oneOf: [{ type: 'string', pattern: '^\\d{4}-\\d{2}-\\d{2}$' }, { type: 'null' }] },
    why_not_joinable: { type: 'object', additionalProperties: false, required: ['zh', 'en'], properties: { zh: { type: 'string', minLength: 8, maxLength: 90 }, en: { type: 'string', minLength: 20, maxLength: 220 } } },
    fixture_only: { const: true, description: 'Test fixtures only. The production build rejects any row that carries it.' },
  },
};

const INVARIANTS = [
  { id: 'INV-01', code: 'MUSEUM_E_STATUS', rule: 'status is a non-empty array of unique values from {closed, capped, geo_excluded}. Any other value (open, active, reopened, joinable, unknown) rejects the row. A reopened program leaves the museum.' },
  { id: 'INV-02', code: 'MUSEUM_E_AS_OF', rule: `as_of is never empty. If page_read === true and verified_on is a valid date, as_of === verified_on. Otherwise as_of === "${UNVERIFIED}".` },
  { id: 'INV-03', code: 'MUSEUM_E_SOURCE', rule: 'source_url parses with new URL(); protocol === "https:", hostname ∈ official_domains[org], search === "", hash === "", and there is no username, password or port.' },
  { id: 'INV-04', code: 'MUSEUM_E_REASON', rule: 'why_not_joinable.zh and .en are non-empty after trim and within the length limits. They contain no currency symbol or code ($ € £ ¥ USD HKD CNY 美元 港元 元), no percentage, and no digits except in an ISO date.' },
  { id: 'INV-05', code: 'MUSEUM_E_HEDGE', rule: `If page_read !== true: verified_on === null, why_not_joinable.zh contains "${HEDGE_ZH}", and why_not_joinable.en contains "${HEDGE_EN}" (case-insensitive).` },
  { id: 'INV-06', code: 'MUSEUM_E_VERIFIED_ON', rule: 'verified_on is null or a real calendar date (a round trip through Date.UTC reproduces it). If page_read === true, verified_on is not null.' },
  { id: 'INV-07', code: 'MUSEUM_E_FORBIDDEN_KEY', rule: 'Only schema keys are allowed, so rows carrying cta, join_url, apply_url, referral_link, share_url, own_link, code, ref, via, reward, earnings, rate or take_rate are rejected.' },
  { id: 'INV-08', code: 'MUSEUM_E_FIXTURE_IN_SEED', rule: 'A row with fixture_only: true may appear only in fixtures, never in the seed or the production build.' },
  { id: 'INV-09', code: 'MUSEUM_E_ID', rule: 'id matches ^[a-z0-9]+(-[a-z0-9]+)*$ and is unique; org ∈ official_domains; program.zh and program.en are non-empty.' },
];

const DATA_CONTRACT = {
  version: '1.1.0',
  row_schema: ROW_SCHEMA,
  constants: { UNVERIFIED_AS_OF: UNVERIFIED, FRESHNESS_WINDOW_DAYS: 90, HEDGE_ZH, HEDGE_EN, STATUS_ORDER: ['closed', 'capped', 'geo_excluded'] },
  official_domains: OFFICIAL_DOMAINS,
  invariants: INVARIANTS,
  check_order: 'validateRow returns the first failure, checking in this order: INV-07, INV-08, INV-09, INV-01, INV-03, INV-06, INV-05 (verified_on must be null when page_read !== true), INV-02, INV-04, INV-05 (hedge text). Each fixture therefore maps to exactly one error code.',
  freshness: {
    window_days: 90,
    algorithm: [
      'if row.page_read !== true → "unconfirmed"',
      'if verified_on is not a valid ISO calendar date → "unconfirmed"',
      'days = (Date.UTC(client_date) − Date.UTC(verified_on)) / 86_400_000',
      'if days < 0 (a future date or client clock skew) → "unconfirmed"',
      'if days <= 90 → "current"; else → "stale"',
    ],
    labels: { current: CURRENT, stale: STALE, unconfirmed: UNCONFIRMED },
    note: '"current" means only that the evidence is recent. It never means the program is open, and it never enables any control. Freshness is recomputed on the client from the client date on every render and filter pass; the static HTML default is "unconfirmed".',
    recheck_due: 'verified_on + 90 days (YYYY-MM-DD), shown only inside Check record.',
  },
  dom_attributes: {
    '[data-museum-row]': {
      'data-row-id': 'row.id',
      'data-org': 'row.org',
      'data-program-zh': 'row.program.zh',
      'data-program-en': 'row.program.en',
      'data-status': 'row.status joined with single spaces, e.g. "capped geo_excluded" (non-empty)',
      'data-as-of': 'row.as_of verbatim (non-empty)',
      'data-source-url': 'row.source_url verbatim (non-empty)',
      'data-page-read': '"true" | "false"',
      'data-verified-on': 'row.verified_on or ""',
      'data-freshness': '"current" | "stale" | "unconfirmed" (computed; static default "unconfirmed")',
      'data-why-not-joinable-zh': 'row.why_not_joinable.zh (non-empty)',
      'data-why-not-joinable-en': 'row.why_not_joinable.en (non-empty)',
    },
    '[data-field]': 'status | as_of | page_read | verified_on | freshness | source | why_not_joinable: the visible value containers, one of each per row',
    others: '[data-source-link] (the single <a> per row), [data-honesty-bar], footer[data-standing-disclosure], [data-nia-short], [data-disclosure-body], [data-non-affiliation], body > [data-disclosure-strip], nav[data-internal-nav], form[data-filter-form], [data-result-count], [data-empty-state], [data-rejected-notice], body[data-client-date]',
  },
  routes: { ...ROUTES, note: 'Relative in-app paths (placeholders until confirmed). Tests read them from here. Same-origin links on the museum page may only be these two routes, #collection and #disclosure.' },
  network_policy: [
    'dist/lab/museum/index.html is one self-contained document: inline <style> and <script>, fonts as data: URIs, and no <link rel="stylesheet|preload|preconnect|prefetch">, <script src> or url() that is not data:. The document request is the only request made on load, and there are zero third-party requests.',
    '<head> carries <meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; img-src data:; font-src data:; form-action \'none\'; base-uri \'none\'">, <meta name="referrer" content="no-referrer"> and <link rel="icon" href="data:,">. The icon link stops the automatic /favicon.ico request.',
    'After load, searching, filtering, sorting, clearing, opening Check record, and focus or hover make zero requests. The bundle has no fetch, XMLHttpRequest, sendBeacon, WebSocket, EventSource, image beacon, prefetch or preconnect.',
    'The only later request allowed is a navigation the user starts: activating an official source link (target=_blank, rel="noopener noreferrer nofollow", referrerpolicy="no-referrer") or an internal nav link.',
    'No analytics, tag manager, pixel, error reporter or A/B script; no cookies and no Web Storage.',
  ],
  build_pipeline: [
    '1. Load the seed rows from JSON checked into the repo. They are never fetched at runtime.',
    '2. Validate each row against row_schema and the invariants, in check_order. Any failure exits non-zero and prints the row id and error code; there is no partial build.',
    '3. Pre-render the one-file HTML with data-freshness="unconfirmed" on every row.',
    '4. Run the lexicon over dist/, then the Playwright acceptance suite.',
  ],
  runtime_guard: 'On every render or filter pass the client re-validates each [data-museum-row] from its data attributes, using the same rules in the same order. A row that fails is hidden and counted in [data-rejected-notice]. Its facts are re-rendered from the attributes, and no code path creates a control inside a row. Client state therefore cannot turn a stale, unverified or reopened row into anything joinable.',
  seed: SEED,
  seed_provenance: {
    checked_on: CLIENT_DATE,
    method: 'Candidate official URLs were located by domain-restricted web search on 2026-09-23. Direct reads of www.notion.com, www.interactivebrokers.com (and its investors. and ndcdyn. hosts) and www.binance.com were refused by this build environment\'s egress policy (CONNECT 403), and a second, independent re-fetch that day was refused the same way.',
    consequence: 'Every seed row is page_read=false, verified_on=null and as_of="未核实 / Not yet checked against the official page". Statuses are the product brief\'s listed statuses, framed as "recorded here as …" with the unverified hedge. No cap figure, jurisdiction list, reward amount or rate is stated, because none has been read on an official page.',
    to_verify: {
      'notion-affiliate': 'Read https://www.notion.com/affiliates and record verbatim wording on whether the program is closed to new affiliates.',
      'ibkr-refer-a-friend': 'Read https://www.interactivebrokers.com/en/trading/referral-member-to-member.php and the Refer-a-Friend terms (https://ndcdyn.interactivebrokers.com/aces/Agreement/AgreementVersion/4841). Record the cap sentence and the excluded-jurisdiction sentence verbatim.',
      'binance-referral-fee-share': 'Read the Terms and Conditions for Binance Referral Program FAQ (the source_url) and https://www.binance.com/en/terms. Record the jurisdiction sentences verbatim. The same FAQ id also appears under a "lite referral" slug, so confirm the page title.',
    },
  },
};

// ---------------------------------------------------------------------------
// Fixtures (row is the only source of truth; mutation_of names the seed row it derives from)
// ---------------------------------------------------------------------------
const seedById = Object.fromEntries(SEED.map((r) => [r.id, r]));
const clone = (x) => JSON.parse(JSON.stringify(x));
const FIXTURE_REASON = pair(
  '测试夹具：假定官方页面曾在核对日期被读取。仅用于渲染测试，不是事实记录。',
  'Test fixture: assumes the official page was read on the check date. For rendering tests only; not a factual record.'
);
function mutate(baseId, patch, fixtureName) {
  const row = { ...clone(seedById[baseId]), ...clone(patch) };
  if (fixtureName) {
    row.id = `${baseId}-fixture-${fixtureName}`;
    row.program = pair(`${row.program.zh}（测试夹具）`, `${row.program.en} (test fixture)`);
    row.why_not_joinable = clone(FIXTURE_REASON);
    row.fixture_only = true;
  }
  return row;
}

const NO_CTA = { cta_count: 0, row_controls_count: 0, links_in_row: 1 };
const srcExpect = (row) => ({ source_href: row.source_url, source_href_search: '', source_href_hash: '', why_not_joinable_nonempty: { zh: true, en: true } });

function seedFixture(id, title, rowId, chips, extra = {}) {
  const row = clone(seedById[rowId]);
  return {
    id, title, client_date: CLIENT_DATE, row,
    expect: {
      valid: true, rendered: true, freshness: 'unconfirmed',
      attributes: { 'data-status': row.status.join(' '), 'data-as-of': UNVERIFIED, 'data-source-url': row.source_url, 'data-page-read': 'false', 'data-verified-on': '', 'data-freshness': 'unconfirmed' },
      visible_text_includes: [...chips, UNVERIFIED, SOURCE_LABEL, CANDIDATE, UNCONFIRMED, '未读取 / Not read', '尚未复核 / Not yet verified', row.why_not_joinable.zh, row.why_not_joinable.en, row.source_url.replace('https://', '')],
      ...srcExpect(row), ...NO_CTA, ...extra,
    },
  };
}

function validFixture(id, title, base, patch, name, expect) {
  const row = mutate(base, patch, name);
  return { id, title, client_date: CLIENT_DATE, mutation_of: base, row, expect: { valid: true, rendered: true, ...expect, ...srcExpect(row), ...NO_CTA } };
}

function invalidFixture(id, title, base, patch, code, context) {
  return { id, title, client_date: CLIENT_DATE, mutation_of: base, ...(context ? { context } : {}), row: mutate(base, patch), expect: { valid: false, error_code: code, rendered: false, cta_count: 0 } };
}

const reasonWithRate = pair(`本馆记录为限地区：分成比例 20%。${HEDGE_ZH}，以官方页面为准。`, 'Recorded here as geo-limited: 20% fee-share. Not yet checked against the official page, which prevails.');

const FIXTURES = [
  seedFixture('FX-01-notion-closed', 'Notion Affiliate: closed, unverified seed row, no CTA', 'notion-affiliate', ['已停招 Closed']),
  seedFixture('FX-02-ibkr-capped-geo', 'IBKR Refer-a-Friend: capped and geo-excluded (two chips), unverified, no CTA', 'ibkr-refer-a-friend', ['限额 Capped', '限地区 Geo-limited'], { chip_order: ['capped', 'geo_excluded'], chips_not_present: ['已停招 Closed'] }),
  seedFixture('FX-03-binance-geo', 'Binance Referral Fee-share: geo-restricted only, unverified, no CTA', 'binance-referral-fee-share', ['限地区 Geo-limited'], { chips_not_present: ['已停招 Closed', '限额 Capped'] }),
  validFixture('FX-04-stale-page-read-true', 'Stale: page_read=true but verified_on is 145 days old, so it renders as expired, never current, with no CTA', 'ibkr-refer-a-friend',
    { page_read: true, verified_on: '2026-05-01', as_of: '2026-05-01' }, 'stale', {
      freshness: 'stale', days_since_check: 145,
      attributes: { 'data-as-of': '2026-05-01', 'data-page-read': 'true', 'data-verified-on': '2026-05-01', 'data-freshness': 'stale' },
      visible_text_includes: ['2026-05-01', STALE, disp(COPY.stale_state.helper), '已读取 / Read', SOURCE_LABEL, FIXTURE_REASON.zh, FIXTURE_REASON.en],
      visible_text_excludes: [CURRENT, CANDIDATE],
    }),
  validFixture('FX-05-boundary-90-days-current', 'Boundary: exactly 90 days is still current, yet the row stays non-joinable with no CTA', 'notion-affiliate',
    { page_read: true, verified_on: '2026-06-25', as_of: '2026-06-25' }, 'boundary-90', {
      freshness: 'current', days_since_check: 90,
      attributes: { 'data-freshness': 'current', 'data-verified-on': '2026-06-25' },
      visible_text_includes: [CURRENT, disp(COPY.current_state.helper), '2026-06-25'],
      after_opening_check_record_includes: ['复核截止 / Re-check due', '2026-09-23'],
    }),
  validFixture('FX-06-boundary-91-days-stale', 'Boundary: 91 days is stale', 'notion-affiliate',
    { page_read: true, verified_on: '2026-06-24', as_of: '2026-06-24' }, 'boundary-91', {
      freshness: 'stale', days_since_check: 91, attributes: { 'data-freshness': 'stale' }, visible_text_includes: [STALE, '2026-06-24'], visible_text_excludes: [CURRENT],
    }),
  validFixture('FX-07-future-verified-on-unconfirmed', 'verified_on after the client date (clock skew or typo) renders as unconfirmed, not current', 'binance-referral-fee-share',
    { page_read: true, verified_on: '2026-10-01', as_of: '2026-10-01' }, 'future', {
      freshness: 'unconfirmed', attributes: { 'data-freshness': 'unconfirmed' }, visible_text_includes: [UNCONFIRMED, '2026-10-01'], visible_text_excludes: [CURRENT],
    }),
  invalidFixture('FX-08-page-read-false-with-date-rejected', 'page_read=false with a verified_on date is rejected: a check date cannot exist without a page read', 'notion-affiliate', { verified_on: '2026-09-20' }, 'MUSEUM_E_HEDGE'),
  invalidFixture('FX-09-page-read-true-no-date-rejected', 'page_read=true with verified_on=null is rejected', 'ibkr-refer-a-friend', { page_read: true }, 'MUSEUM_E_VERIFIED_ON'),
  invalidFixture('FX-10-status-open-rejected', 'status ["open"] is rejected: a reopened program leaves the museum', 'notion-affiliate', { status: ['open'] }, 'MUSEUM_E_STATUS'),
  invalidFixture('FX-11-status-empty-rejected', 'status [] is rejected', 'binance-referral-fee-share', { status: [] }, 'MUSEUM_E_STATUS'),
  invalidFixture('FX-12-source-ref-param-rejected', 'A source_url carrying ?ref= is rejected', 'notion-affiliate', { source_url: 'https://www.notion.com/affiliates?ref=abc123' }, 'MUSEUM_E_SOURCE'),
  invalidFixture('FX-13-source-http-rejected', 'A plain-http source_url is rejected', 'ibkr-refer-a-friend', { source_url: 'http://www.interactivebrokers.com/en/trading/referral-member-to-member.php' }, 'MUSEUM_E_SOURCE'),
  invalidFixture('FX-14-source-unofficial-domain-rejected', 'A source_url on a non-official domain is rejected', 'binance-referral-fee-share', { source_url: 'https://binance-referral.example.com/terms' }, 'MUSEUM_E_SOURCE'),
  invalidFixture('FX-15-source-hash-rejected', 'A source_url with a #hash is rejected', 'notion-affiliate', { source_url: 'https://www.notion.com/affiliates#via=me' }, 'MUSEUM_E_SOURCE'),
  invalidFixture('FX-16-as-of-empty-rejected', 'An empty as_of is rejected (as_of is never omitted)', 'ibkr-refer-a-friend', { as_of: '' }, 'MUSEUM_E_AS_OF'),
  invalidFixture('FX-17-as-of-date-while-unread-rejected', 'An ISO as_of while page_read=false is rejected', 'binance-referral-fee-share', { as_of: '2026-09-23' }, 'MUSEUM_E_AS_OF'),
  invalidFixture('FX-18-reason-en-empty-rejected', 'An empty English why_not_joinable is rejected', 'notion-affiliate', { why_not_joinable: pair(seedById['notion-affiliate'].why_not_joinable.zh, '  ') }, 'MUSEUM_E_REASON'),
  invalidFixture('FX-19-impossible-date-rejected', 'The impossible date 2026-02-30 is rejected', 'ibkr-refer-a-friend', { page_read: true, verified_on: '2026-02-30', as_of: '2026-02-30' }, 'MUSEUM_E_VERIFIED_ON'),
  invalidFixture('FX-20-join-url-key-rejected', 'A join_url key is rejected: rows cannot carry a CTA target', 'notion-affiliate', { join_url: 'https://www.notion.com/affiliates' }, 'MUSEUM_E_FORBIDDEN_KEY'),
  invalidFixture('FX-21-reason-with-rate-rejected', 'A why_not_joinable that states a rate is rejected', 'binance-referral-fee-share', { why_not_joinable: reasonWithRate }, 'MUSEUM_E_REASON'),
  invalidFixture('FX-22-fixture-row-in-seed-rejected', 'A fixture_only row placed in the production seed fails the build', 'notion-affiliate', { fixture_only: true }, 'MUSEUM_E_FIXTURE_IN_SEED', 'production_seed'),
];

// ---------------------------------------------------------------------------
// Acceptance tests
// ---------------------------------------------------------------------------
const NO_SCROLL = "document.documentElement.scrollWidth <= innerWidth && document.body.scrollWidth <= innerWidth && getComputedStyle(document.documentElement).overflowX === 'visible' && getComputedStyle(document.body).overflowX === 'visible'";
const ACCEPTANCE = [
  {
    id: 'AT-01', title: 'Screenshots at 1440px and 360px show the full archive, and no join, apply, share or code control', method: 'playwright-screenshot',
    steps: [
      "for (const width of [1440, 360]) { await page.setViewportSize({ width, height: width === 1440 ? 900 : 740 }); await page.addInitScript(() => { window.__MUSEUM_CLIENT_DATE__ = '2026-09-23'; }); await page.goto('/lab/museum'); const buf = await page.screenshot({ fullPage: true, style: '[data-honesty-bar],[data-disclosure-strip]{position:static!important}' }); expect(buf).toMatchSnapshot(`museum-${width}.png`, { maxDiffPixelRatio: 0.01 }); }",
      `At both widths: h1.innerText.replace(/\\s+/g, ' ').trim() === '关门博物馆 Closed Programs Museum'; in every [data-museum-row], the [data-field] nodes status, as_of, page_read, verified_on, freshness, source and why_not_joinable pass checkVisibility() and have non-empty innerText; [data-honesty-bar], footer [data-nia-short], [data-disclosure-body][lang="zh-CN"] and [data-disclosure-body][lang="en"] are visible; ${NO_SCROLL}.`,
      "No CTA: page.getByRole('button', { name: /加入|申请|注册|分享|复制|join|apply|sign ?up|share|copy|code/i }) and page.getByRole('link', { name: /加入|申请|注册|分享|复制|成为|开户|join|apply|sign ?up|register|share|copy|become|code/i }) both have count 0.",
    ],
    pass: 'Both screenshots match their committed baselines (committed after the first human-approved run), and every assertion holds at both widths.',
    fails_if: 'Pixel drift over 1%, horizontal overflow, any row field hidden or empty, a missing honesty bar or disclosure, or any CTA-like control.',
  },
  {
    id: 'AT-02', title: 'No join/apply CTA in any row, for every seed and fixture', method: 'playwright-dom',
    steps: [
      'Run on dist/lab/museum/index.html (the seed) and on dist-fixtures/lab/museum/index.html, which `npm run build:fixtures` renders from every fixture with expect.valid === true (FX-01 to FX-07).',
      "expect(await page.evaluate(() => document.querySelectorAll('[data-museum-row] [data-cta=\"join\"], [data-museum-row] [data-cta=\"apply\"]').length)).toBe(0)",
      "expect(await page.evaluate(() => document.querySelectorAll('[data-museum-row] :is([data-cta], button, input, select, textarea, form, [role=\"button\"])').length)).toBe(0)",
      "expect(await page.evaluate(() => [...document.querySelectorAll('[data-museum-row]')].every(r => r.querySelectorAll('a').length === 1 && r.querySelector('a[data-source-link]')))).toBe(true)",
      "expect(await page.evaluate(() => [...document.querySelectorAll('[data-museum-row] *')].filter(el => !el.closest('a[data-source-link], summary') && (el.hasAttribute('onclick') || el.hasAttribute('tabindex') || getComputedStyle(el).cursor === 'pointer')).length)).toBe(0)",
    ],
    pass: 'All four evaluations return the expected value on both pages.',
    fails_if: 'Any count above 0, or any row with zero links or more than one.',
  },
  {
    id: 'AT-03', title: 'Every row carries the required attributes and renders their values visibly', method: 'playwright-dom',
    steps: [
      "expect(await page.$$eval('[data-museum-row]', rs => rs.every(r => ['data-status','data-as-of','data-source-url','data-why-not-joinable-zh','data-why-not-joinable-en'].every(a => (r.getAttribute(a) || '').trim().length > 0)))).toBe(true)",
      "const rows = await page.$$eval('[data-museum-row]', rs => rs.map(r => ({ asOf: r.dataset.asOf, src: r.dataset.sourceUrl, zh: r.dataset.whyNotJoinableZh, en: r.dataset.whyNotJoinableEn, text: r.innerText })));",
      "for (const r of rows) for (const v of [r.asOf, r.src.replace('https://', ''), r.zh, r.en, '官方来源 / Official source', '为何不可加入 / Why not joinable']) expect(r.text).toContain(v); expect(rows.length).toBe(data_contract.seed.length);",
    ],
    pass: 'Every row passes.',
    fails_if: 'An empty attribute, or a value that is missing from innerText. A value found only in an attribute or in visually hidden text does not count.',
  },
  {
    id: 'AT-04', title: 'Source links are the only external links: plain HTTPS official URLs with no parameters, matching the reviewed seed', method: 'playwright-dom + rg',
    steps: [
      "const links = await page.$$eval('a[data-source-link]', as => as.map(a => { const u = new URL(a.href); return { protocol: u.protocol, host: u.hostname, search: u.search, hash: u.hash, rel: a.rel, rp: a.referrerPolicy, bg: getComputedStyle(a).backgroundColor, row: a.closest('[data-museum-row]').dataset.sourceUrl, href: a.getAttribute('href') }; }));",
      "for (const l of links) { expect(l.protocol).toBe('https:'); expect(l.search).toBe(''); expect(l.hash).toBe(''); expect(l.href).toBe(l.row); expect(l.rel).toContain('noopener'); expect(l.rel).toContain('noreferrer'); expect(l.rp).toBe('no-referrer'); expect(l.bg).toBe('rgba(0, 0, 0, 0)'); expect(Object.values(official_domains).flat()).toContain(l.host); }",
      'On the seed page, expect(links.map(l => l.href).sort()).toEqual(data_contract.seed.map(r => r.source_url).sort()). On the fixture page, compare against the row.source_url of every fixture with expect.valid === true.',
      "In every AT-07 view: expect(await page.$$eval('a[href]', as => as.filter(a => new URL(a.href).origin !== location.origin && !a.matches('[data-museum-row] a[data-source-link]')).length)).toBe(0)",
      "rg -n --pcre2 '[?&](ref|via|code)=' dist/ → must exit 1; rg -n --pcre2 '[?&](ref|via|code|referral|invite|aff|affiliate|utm_[a-z]+)=' dist/ → must exit 1",
    ],
    pass: 'Every assertion holds and both rg commands exit 1.',
    fails_if: 'Any external link other than a row source link, a query or hash on a source link, a host outside the allowlist, a href that differs from the seed, an rg match, or a source link styled with a background.',
  },
  {
    id: 'AT-05', title: 'Unread or stale evidence renders as unconfirmed or expired, never current, and still shows no CTA', method: 'unit + playwright-dom',
    steps: [
      'Unit: for every fixture with expect.valid === true, freshness(fixture.row, fixture.client_date) === fixture.expect.freshness. FX-04 → stale (145 days); FX-05 → current (90); FX-06 → stale (91); FX-07 → unconfirmed (future date); FX-01 to FX-03 → unconfirmed (page_read=false).',
      "DOM, fixture page, client date 2026-09-23: for each valid fixture, the row [data-row-id=row.id] has every expect.attributes value, innerText contains every visible_text_includes entry and none of visible_text_excludes, and after_opening_check_record_includes holds once its summary is clicked. Any row with data-page-read !== 'true' shows 待核对 / Unconfirmed; any row not current lacks 来源已读取，90 天内已核对; no row contains [data-cta], button or input.",
      'Set the injected client date to 2026-12-31 and reload: FX-05 (verified 2026-06-25) must flip to stale, which proves freshness uses the client date rather than the build date.',
    ],
    pass: 'Every unit and DOM assertion holds, including the flip.',
    fails_if: 'An unread or >90-day row labelled current, a missing stale or unconfirmed literal, or any control inside such a row.',
  },
  {
    id: 'AT-06', title: 'The forbidden lexicon finds nothing in the built UI (the scan covers the build, not this brief)', method: 'node + rg',
    steps: [
      'node tests/lexicon-scan.mjs dist/ runs the lexicon procedure (self-test, allowlist, every group) over dist/ and over the rendered DOM of every AT-07 view, and exits non-zero on any hit.',
      "rg -n --pcre2 '\\x{4F60}\\x{80FD}\\x{62FF}|\\x{5FC5}\\x{8D5A}|\\x{7A33}\\x{8D5A}|\\x{5012}\\x{8BA1}\\x{65F6}|\\x{9650}\\x{65F6}|\\x{7ACB}\\x{5373}' dist/ → exit 1 (你能拿 必赚 稳赚 倒计时 限时 立即)",
      "rg -n --pcre2 '10,?000\\s*[x×]|\\bLIVE\\b|(?i:count[ -]?down|confetti|\\bneon\\b|take[ -]?rate|guarantee)' dist/ → exit 1 (LIVE stays case-sensitive so aria-live never matches)",
      "rg --count-matches -i gravity dist/ → exactly one line per HTML file, each ending ':2' (the two [data-non-affiliation] spans), and no other file",
      'DOM: every text node matching /gravity/i has an ancestor [data-non-affiliation]; there are exactly 2 [data-non-affiliation] elements; no [data-museum-row] innerText matches /现可加入|仍可加入|目前开放|currently (available|open|accepting)|still (open|available|accepting)|is joinable/i.',
    ],
    pass: 'The scan exits 0, each exit-1 rg exits 1, and the gravity count is exactly 2 per HTML file.',
    fails_if: 'Any forbidden match outside the allowlisted required copy, or a lexicon self-test failure.',
  },
  {
    id: 'AT-07', title: 'Required copy on every route and view', method: 'playwright-dom',
    steps: [
      "Views: default; status = closed / capped / geo_excluded; check status = current / stale / unconfirmed; search 'zzz' (empty state visible); search 'notion'; sort = name_asc; first visible Check record opened. Each view at 1440×900 and 360×740, plus the fixture page and the no-JS page.",
      "Per view: every dom_check of lexicon group honesty_bar_hidden holds (the bar contains the exact literal 点击 ≠ 收入 / Clicks ≠ income; it and its descendants compute opacity 1, transform none and font-size ≥ 13px; it is fully in the viewport at the top and after scrolling to the bottom).",
      "Per view: expect(await page.locator('footer[data-standing-disclosure] [data-nia-short]').innerText()).toBe('仅供参考，不构成投资建议 / For information only; not investment advice'), and the footer innerText contains standing_disclosure.zh and standing_disclosure.en exactly.",
      "Per view: nav[data-internal-nav] links are exactly ['回到 Claim Shredder / Back to Claim Shredder' → routes.claim_shredder, '查看规则板 / View rules board' → routes.rules_board]. Every other same-origin href is '#collection' or '#disclosure'.",
      "On routes.claim_shredder and routes.rules_board: document.querySelectorAll('a[href=\"/lab/museum\"]') has exactly one match, and its innerText is '查看关门博物馆 / View the Closed Programs Museum'.",
    ],
    pass: 'Every assertion holds in every view.',
    fails_if: 'A view that is missing any literal (matched exactly, including U+2260 ≠ and the ASCII spaces around it), or a weakened or hidden honesty bar.',
  },
  {
    id: 'AT-08', title: 'Request spy: only the document request on load, and zero requests while searching, filtering, sorting and expanding', method: 'playwright-network',
    steps: [
      "const reqs = []; context.on('request', r => reqs.push(r.url())); await page.goto('/lab/museum', { waitUntil: 'networkidle' });",
      "Load phase: expect(reqs.filter(u => !u.startsWith('data:'))).toEqual([page.url()]) (the document only). The <head> holds the CSP meta, meta[name=referrer][content=no-referrer] and link[rel=icon][href='data:,']. rg -n --pcre2 'url\\((?![\"\\x27]?data:)|rel=\"(preload|stylesheet|prefetch|preconnect|dns-prefetch)\"|<script[^>]*\\bsrc=' dist/ → exit 1.",
      "reqs.length = 0; await page.fill('input[type=search]', '币安'); await page.keyboard.press('Enter'); await page.fill('input[type=search]', 'zzz'); await page.keyboard.press('Escape'); await page.check('input[name=status][value=capped]'); await page.check('input[name=freshness][value=unconfirmed]'); await page.selectOption('select[name=sort]', 'name_asc'); await page.click('li:not([hidden]) > [data-museum-row] summary'); await page.click('button[type=reset]'); await page.hover('a[data-source-link]'); await page.waitForTimeout(1000);",
      'expect(reqs).toEqual([]); page.url() is unchanged (pressing Enter caused no navigation).',
      "Static: rg -n --pcre2 '\\bfetch\\(|XMLHttpRequest|sendBeacon|new WebSocket|EventSource|googletagmanager|google-analytics|gtag\\(|plausible|segment|sentry' dist/ → exit 1.",
      "Positive control: clicking a source link opens exactly one new page, whose URL equals that link's href with an empty query.",
    ],
    pass: 'The load phase is exactly the document request, reqs is [] after the interactions, both rg commands exit 1, and the positive control opens exactly the official URL.',
    fails_if: 'Any load request other than the document, any request during the interactions, a URL change on Enter, or any network API in the bundle.',
  },
  {
    id: 'AT-09', title: 'Keyboard-only operation, visible focus, and focus never hidden under the sticky bars', method: 'playwright-keyboard',
    steps: [
      'At 360×740, 1280×720 and 1440×900, press Tab from the top and record the kind of each document.activeElement. The sequence must be: skip, search, status, freshness, sort, reset, then source and summary for each card, then nav, nav. Then walk it backwards with Shift+Tab from the last internal link.',
      'At every stop: the outline is not none and is at least 2px wide (for radios, check the associated label). elementFromPoint at the centre of the element (for radios, the label) returns the element or one of its descendants or ancestors, so neither the sticky bar nor the strip covers it.',
      'Arrow keys in the status group change the checked radio and the shown rows without any Tab. The checked radio\'s label computes a backgroundColor different from its unchecked siblings. Enter on the skip link focuses #collection, which then shows its ring. Esc clears the search.',
      'Tabbing past the last internal link leaves the page, and the next Tab returns to the skip link (no trap).',
    ],
    pass: 'The recorded sequence equals the expected list in both directions at all three sizes, and every focus check passes.',
    fails_if: 'A missing or extra stop, an invisible focus ring, focus covered by a sticky bar, a checked pill that looks unchecked, or a keyboard trap.',
  },
  {
    id: 'AT-10', title: 'Reduced motion removes the only animation', method: 'playwright-media',
    steps: [
      "await page.emulateMedia({ reducedMotion: 'reduce' }); change a filter; every [data-museum-list] > li and every details body computes a transitionDuration matching /^0s(, 0s)*$/, and document.getAnimations().length === 0.",
      "await page.emulateMedia({ reducedMotion: 'no-preference' }); getComputedStyle(li).transitionProperty === 'opacity' and transitionDuration === '0.15s'. No element has a transform or all transition with a non-zero duration.",
    ],
    pass: 'Zero-duration transitions and no animations under reduce; only the 150ms opacity transition otherwise.',
    fails_if: 'Any non-zero transition under reduce, or any animated property other than opacity.',
  },
  {
    id: 'AT-11', title: 'WCAG AA contrast, language tagging and structure', method: 'node + playwright-dom',
    steps: [
      'node tools/validate-brief.mjs computes the contrast of every text token on --bg and --surface (≥ 4.5:1), of the inverse checked pill, and of --focus and --field-border (≥ 3:1).',
      'DOM: every visible element with a direct text node has a contrast of at least 4.5 against the nearest opaque ancestor background. No text qualifies as large, so the large-text exemption is never used.',
      "Structure: exactly one h1; h1 → h2 → h3 with no skipped level; html[lang='zh-CN']; each ia.landmarks entry exists once; every form control has a label. Language: every text node outside <option>, <script> and <style> that still matches /[A-Za-z]{4,}/, after removing URLs and the names Referral Lab, Claim Shredder, Notion, IBKR, Binance and gravity.li, has parentElement.closest('[lang]').lang === 'en'.",
    ],
    pass: 'Every ratio meets its threshold and every structure and language check holds.',
    fails_if: 'Any ratio below its threshold, or any structure or language check that fails.',
  },
  {
    id: 'AT-12', title: 'Mutation fixtures and client state cannot make a row joinable', method: 'unit + build + playwright-dom',
    steps: [
      'Unit: for each fixture, validateRow(fixture.row, { context: fixture.context === "production_seed" ? "seed" : "fixtures" }) returns valid === expect.valid and code === expect.error_code, following data_contract.check_order. Diffed against its mutation_of seed row, FX-04 to FX-22 change verified_on, page_read, status, source_url, as_of, why_not_joinable, forbidden keys and fixture_only.',
      'Build: adding any single invalid fixture row to the seed makes `npm run build` exit non-zero and print that row\'s error code.',
      "Client state: page.evaluate(() => { const r = document.querySelector('[data-museum-row]'); r.dataset.status = 'open'; r.dataset.pageRead = 'true'; r.dataset.verifiedOn = '2026-09-23'; }), then change any filter. That row's <li> is hidden, [data-rejected-notice] reads 1 条记录未通过校验，未显示。 / 1 record(s) failed validation and are not shown., and the AT-02 CTA selectors still return 0.",
      "Client state: set another row's data-verified-on to the client date while data-page-read stays 'false', then re-filter. That row is hidden as MUSEUM_E_HEDGE, and no row shows 来源已读取，90 天内已核对.",
    ],
    pass: 'Every unit result matches, the build fails for every invalid row, and both client-state mutations are neutralised.',
    fails_if: 'Any mismatch, a build that passes with an invalid row, or a mutated row that becomes current, visible or open, or gains a control.',
  },
  {
    id: 'AT-13', title: 'No horizontal scroll at 320, 360, 640 and 1440', method: 'playwright-dom',
    steps: [
      `for (const w of [320, 360, 640, 1440]) { await page.setViewportSize({ width: w, height: 800 }); open the first Check record; expect(await page.evaluate(() => ${NO_SCROLL})).toBe(true); }`,
      'At 360: every [data-museum-row] satisfies getBoundingClientRect().left >= 16 && right <= innerWidth - 16, and the long Binance source link wraps inside its card.',
    ],
    pass: 'No overflow at any width, with visible overflow (nothing clipped away), and the gutters hold at 360.',
    fails_if: 'scrollWidth > innerWidth on html or body, overflow-x set to clip or hidden, or a card crossing the 16px gutter.',
  },
  {
    id: 'AT-14', title: 'The honesty bar and the not-investment-advice line stay in view on narrow screens', method: 'playwright-dom',
    steps: [
      "At 360×740, after scrolling to 0, 50% and 100% of document.body.scrollHeight: [data-honesty-bar] intersects the viewport, and so does [data-disclosure-strip] or footer [data-nia-short]. The [data-honesty-bar] height is ≤ 48 and the [data-disclosure-strip] height is ≤ 44, and the honesty_bar_hidden dom_checks hold.",
      'At 360×420: the bar, the strip and the filter rail compute position: static, and there is still no horizontal overflow.',
    ],
    pass: 'Both stay visible at every scroll position at 360×740, within their height caps, and fall back to static at short heights.',
    fails_if: 'Either one scrolls out of view, exceeds its height cap, or is still sticky at 360×420.',
  },
  {
    id: 'AT-15', title: 'Seed truthfulness on 2026-09-23', method: 'unit',
    steps: [
      'For every data_contract.seed row with page_read === false: verified_on === null, as_of === constants.UNVERIFIED_AS_OF, why_not_joinable.zh includes HEDGE_ZH, why_not_joinable.en.toLowerCase() includes HEDGE_EN, and freshness(row, "2026-09-23") === "unconfirmed".',
      'No seed string matches /\\d|%|[$€£¥]/, except source_url, id, as_of and verified_on.',
      'A row changes to page_read=true only through a commit that sets verified_on and as_of to the read date and rewrites why_not_joinable from the page text. After that commit the reason has no hedge, and freshness is current until verified_on + 90 days.',
    ],
    pass: 'Every seed row satisfies these rules.',
    fails_if: 'A seed row claims a read or a date without the evidence commit, or states an unread fact.',
  },
  {
    id: 'AT-16', title: 'No-JS rendering is safe by default', method: 'playwright (javaScriptEnabled: false)',
    steps: [
      "Every row has data-freshness=\"unconfirmed\" and shows 待核对 / Unconfirmed. The honesty bar, footer disclosure and internal links are present, and document.querySelectorAll('[data-filter-form]:not([hidden])').length === 0, so no GET submission is possible.",
    ],
    pass: 'Holds.',
    fails_if: 'Any row appears current without JS, required copy is missing, or the form is visible.',
  },
];

// ---------------------------------------------------------------------------
// Do / Dont / dont_repeat / open questions
// ---------------------------------------------------------------------------
const DO = [
  'Build the museum as a quiet archive of closed, capped, and geo-excluded counterexamples; link it internally from Claim Shredder and the Rules Board, never from an external brand.',
  'Put `status`, `as_of`, official `source_url`, `page_read`, `verified_on`, and bilingual `why_not_joinable` on every row and render all of them visibly.',
  'Keep the attribution bar `点击 ≠ 收入 / Clicks ≠ income` and the standing bilingual disclosure visible on every view.',
  'Use the dark board tokens, restrained museum-label/tombstone annotation, bilingual zh-primary/en-secondary copy, responsive cards, keyboard access, WCAG AA, and reduced-motion behavior specified below.',
  'Pre-render every row with data-freshness="unconfirmed", then let the client compute current / stale / unconfirmed from page_read, verified_on and the client date (a 90-day window, inclusive). "Current" only means the evidence is fresh; it never means the program is open.',
  `Whenever page_read !== true, show 未核实 / Not yet checked against the official page as as_of, and add the muted qualifier ${CANDIDATE} under ${SOURCE_LABEL}. Seed every row this way until an official page has actually been read.`,
  'Render the reason as a quiet museum wall label (展签 / Wall label · 为何不可加入 / Why not joinable): hairline frame, zh line first, muted en line, with no icon, no cross or RIP imagery, and no joke.',
  'Render each source as one plain underlined text link to the exact official https URL (no query, no hash), with target="_blank", rel="noopener noreferrer nofollow" and referrerpolicy="no-referrer". It is the only link in a card and the only external link on the page.',
  'Validate each row against the schema and the invariants in check_order: at build time (fail the build) and again on the client on every filter pass (hide the row and count it in [data-rejected-notice]).',
  'Keep all search, filter, sort and expand behaviour in memory on the client, with no request beyond the document itself, fonts inlined as data: URIs, a CSP that blocks connections and form submission, and no cookies or Web Storage.',
  'Move any program whose official page shows it has reopened out of the museum and onto the rules board for fresh verification, and say so in the internal nav note.',
  `Link back with the exact texts ${BACK_SHREDDER} (${ROUTES.claim_shredder}) and ${VIEW_RULES} (${ROUTES.rules_board}), and place 查看关门博物馆 / View the Closed Programs Museum once on each of those two routes.`,
];

const DONT = [
  'Never provide a join/apply CTA, referral/share link, code field, or FOMO treatment for a closed, capped, geo-excluded, stale, or unverified row.',
  'Never omit `as_of`, official source, or the bilingual reason why the program is not joinable; never present stale evidence as current.',
  'Never use earnings estimates, take-rate calculators, 「你能拿」, guaranteed income, 必赚, 10000x, urgency, confetti, neon, LIVE, countdown, investment advice, or gravity.li/GRAVITY branding.',
  'Never generate, store, infer, or add referral codes or `ref`/`via`/`code` outbound parameters; this feature has no `{own_link}`.',
  'Never hide or weaken `点击 ≠ 收入 / Clicks ≠ income`.',
  'Ban earnings estimates (lexicon: earnings_estimate), including reward amounts, per-referral figures and "estimated/potential earnings".',
  'Ban take-rate calculators (lexicon: take_rate_calculator): no number or range inputs and no <output>. Ban any percentage, fee-share rate, take rate or currency amount in visible text (lexicon: rate_or_percentage).',
  'Ban 「你能拿」 and every "you can earn / you will get" framing, 您 forms included (lexicon: ni_neng_na).',
  'Ban guaranteed income, risk-free, passive-income, 保证收入, 稳赚 and 躺赚 claims (lexicon: guaranteed_income).',
  'Ban 必赚 and 包赚 (lexicon: bi_zhuan).',
  'Ban 10000x and every N×, N倍 or 翻倍 multiplier (lexicon: multiplier_10000x).',
  'Ban generating or storing referral codes. No code, invite or founder-code field and no code shown as text; no clipboard, share, localStorage, sessionStorage, IndexedDB or cookie use (lexicon: referral_code_generation_or_storage).',
  'Ban ref, via and code (and other referral or tracking parameters) on outbound links. The only exception anywhere in Referral Lab is a user-typed {own_link}, and this feature has none (lexicon: outbound_ref_via_code_params, control_label_ref_via_code).',
  'Ban urgency UI: hurry, last chance, limited time, only N left, closing soon, 限时, 名额有限, 赶紧, 立即, marquee and role="timer" (lexicon: urgency_ui).',
  'Ban confetti and celebration effects or emoji (lexicon: confetti).',
  'Ban neon, glow, text-shadow, box-shadow and drop-shadow treatments, and any colour outside the tokens (lexicon: neon).',
  'Ban LIVE badges and any live or real-time claim, 实时 and 直播 included (lexicon: live_badge, live_word).',
  'Ban countdowns, timers, 倒计时, HH:MM:SS displays and setInterval ticking (lexicon: countdown). The only setTimeout allowed is the single 700ms debounce of the result-count live region.',
  'Ban any join CTA on closed, capped or geo rows. That covers buttons, forms, second links, onclick or tabindex elements, "learn how to join", become-a-member, open-an-account, share and copy (lexicon: join_cta).',
  'Ban hiding 点击 ≠ 收入 / Clicks ≠ income by any means: display, visibility, opacity, transform, clip, font-size under 13px, collapsing, dismissing, or moving it into <details> (lexicon: honesty_bar_hidden).',
  'Ban claiming freshness without page_read === true and verified_on within 90 days, and ban any claim that a museum row is open, current or joinable (lexicon: freshness_claim_without_evidence).',
  'Ban any investment advice or buy/sell/open-account recommendation. Only the negated 不构成投资建议 / not investment advice is allowed (lexicon: investment_advice).',
  'Ban gravity.li / GRAVITY branding, links, logos and names. The only allowed mention is the non-affiliation clause in the footer (lexicon: gravity_branding).',
  'Do not state cap figures, jurisdiction lists, reward amounts or fee-share rates that have not been read on the official page. Never state reward amounts or rates at all.',
  'Do not fetch fonts, analytics or any runtime data, do not clip overflow to hide it, and do not persist filter state.',
];

const DONT_REPEAT = [
  { zh: '已停招、限额、限地区的记录永远没有加入按钮、申请入口、分享或推荐码。', en: 'Closed, capped and geo-limited rows never get a join button, apply entry, share control or referral code.' },
  { zh: '每条记录必须同时有 as_of、官方来源和中英双语的「为何不可加入」。缺任何一项，构建即失败。', en: 'Every row needs as_of, an official source and a bilingual why-not-joinable reason together. If any one is missing, the build fails.' },
  { zh: '过期就是待核对：没有读取官方页面，或上次核对已超过 90 天，只能显示待核对或复核已过期，不能显示为 90 天内已核对。', en: 'Stale means unconfirmed: without a page read, or with a last check over 90 days old, a row shows Unconfirmed or Last check has expired, never checked within 90 days.' },
  { zh: '点击 ≠ 收入。这句话在每个视图都可见，不能隐藏、缩小或折叠。', en: 'Clicks ≠ income. The line is visible on every view and is never hidden, shrunk or collapsed.' },
  { zh: '官方来源只是一个普通链接：https、无参数、无 #，不带 ref、via 或 code，也不做成按钮样式。', en: 'An official source is a plain link: https, with no query, no hash, no ref, via or code, and no button styling.' },
  { zh: '博物馆是档案，不是错失恐惧清单：没有倒计时、LIVE、名额紧张、收益估算或庆祝效果。', en: 'A museum is an archive, not a FOMO list: no countdown, LIVE, scarcity, earnings estimate or celebration effect.' },
  { zh: '未读取官方页面的事实不能写进卡片：不写上限数字、地区名单、奖励金额或分成比例。', en: 'Facts not read on the official page never go on a card: no cap figures, region lists, reward amounts or fee-share rates.' },
  { zh: '计划若重新开放，就移出博物馆，交给规则板重新核对，不会在这里增设入口。', en: 'If a program reopens, it leaves the museum for a fresh check on the rules board; it never gains an entry point here.' },
];

const OPEN_QUESTIONS = [
  'The handoff/rules context was not attached. On 2026-09-23 this environment could not open notion.com, interactivebrokers.com or binance.com, so every seed ships as 未核实 / Not yet checked against the official page, with a search-located candidate URL. Who will read those pages from an open network (see data_contract.seed_provenance.to_verify), and do the handoff URLs match or replace data_contract.seed[*].source_url?',
  `Are ${ROUTES.claim_shredder}, ${ROUTES.rules_board} and ${ROUTES.museum} the real Referral Lab routes? They are placeholders in data_contract.routes, which the internal-link tests read.`,
];

const PROBLEM =
  'Referral Lab needs honest counterexamples. People who use the Claim Shredder and the Rules Board need to see that the lab also records programs they cannot join: closed, capped or geo-excluded. That record must never turn into a FOMO list, a disguised join funnel or an earnings pitch. The Closed Programs Museum is a calm, bilingual (zh-CN primary, English secondary) evidence archive in one self-contained page. Each row shows its status, as_of, official source, page_read and verified_on freshness, and a wall-label reason why it is not joinable. It has no CTAs, codes, referral parameters, earnings or network activity, and 点击 ≠ 收入 / Clicks ≠ income and the not-investment-advice disclosure are always in view.';

const BRIEF = {
  compose_closed_programs_museum: {
    problem: PROBLEM,
    do: DO,
    dont: DONT,
    ia: IA,
    data_contract: DATA_CONTRACT,
    lexicon: LEXICON,
    copy: COPY,
    dont_repeat: DONT_REPEAT,
    acceptance: ACCEPTANCE,
    open_questions: OPEN_QUESTIONS,
  },
  label_set: LABEL_SET,
  fixtures: FIXTURES,
  standing_disclosure: DISCLOSURE,
};

writeFileSync(OUT, JSON.stringify(BRIEF, null, 2) + '\n');
console.log('wrote', OUT, JSON.stringify(BRIEF).length, 'bytes (minified)');
