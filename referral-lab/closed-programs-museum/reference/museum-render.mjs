// HTML string renderers shared by the static build (Node) and the browser runtime.
// Every interpolated value goes through esc(). Rows never render a control other than
// the single source link and the Check record <details>.

export const T = {
  statusChip: { closed: ['已停招', 'Closed'], capped: ['限额', 'Capped'], geo_excluded: ['限地区', 'Geo-limited'] },
  asOf: ['核对日期', 'Checked'],
  pageRead: ['来源读取', 'Page read'],
  pageReadTrue: ['已读取', 'Read'],
  pageReadFalse: ['未读取', 'Not read'],
  verifiedOn: ['最近复核', 'Last verified'],
  verifiedOnNone: ['尚未复核', 'Not yet verified'],
  freshness: ['核对状态', 'Check status'],
  source: ['官方来源', 'Official source'],
  sourceCandidate: ['候选链接', 'Candidate link'],
  newTab: ['（在新标签页打开）', '(opens in a new tab)'],
  wallLabel: ['展签', 'Wall label'],
  reason: ['为何不可加入', 'Why not joinable'],
  checkRecord: ['核对记录', 'Check record'],
  recheckDue: ['复核截止', 'Re-check due'],
  rule: ['规则：已读取官方页面，且复核日期距今不超过 90 天，才算已核对。', 'Rule: a record counts as checked only when the official page was read and the last verification is no more than 90 days old.'],
  fresh: {
    current: [['来源已读取，90 天内已核对', 'Source read; checked within 90 days'], ['核对较新只说明记录没有过期；该计划仍不可加入。', 'A recent check only means this record has not expired; the program still cannot be joined.']],
    stale: [['复核已过期', 'Last check has expired'], ['上次核对已超过 90 天。此记录仅作存档，现状未经确认。', 'The last check is more than 90 days old. This record is kept for the archive; its current status is unconfirmed.']],
    unconfirmed: [['待核对', 'Unconfirmed'], ['请以官方页面为准。', 'The official page prevails.']],
  },
};

export function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

// "zh / en" with the English half tagged.
export function bi([zh, en], sep = ' / ') {
  return `${esc(zh)}${sep}<span lang="en">${esc(en)}</span>`;
}

// Tags the English half of an already-combined "zh / en" string.
export function biText(s) {
  const i = String(s).indexOf(' / ');
  return i < 0 ? esc(s) : bi([s.slice(0, i), s.slice(i + 3)]);
}

const isoRe = /^\d{4}-\d{2}-\d{2}$/;
const dateHtml = (d) => `<time datetime="${esc(d)}">${esc(d)}</time>`;

export function sourceText(url) {
  const u = new URL(url);
  return u.hostname + u.pathname;
}

export function renderFacts(row, fresh, recheckDueDate) {
  const [label, helper] = T.fresh[fresh];
  const read = row.page_read === true;
  return `<dl class="facts">
<div class="fact"><dt>${bi(T.asOf)}</dt><dd data-field="as_of">${isoRe.test(row.as_of) ? dateHtml(row.as_of) : biText(row.as_of)}</dd></div>
<div class="fact"><dt>${bi(T.pageRead)}</dt><dd data-field="page_read">${bi(read ? T.pageReadTrue : T.pageReadFalse)}</dd></div>
<div class="fact"><dt>${bi(T.verifiedOn)}</dt><dd data-field="verified_on">${row.verified_on ? dateHtml(row.verified_on) : bi(T.verifiedOnNone)}</dd></div>
<div class="fact"><dt>${bi(T.freshness)}</dt><dd data-field="freshness"><span class="fresh-label">${bi(label)}</span><span class="helper">${bi(helper)}</span></dd></div>
<div class="fact"><dt>${bi(T.source)}${read ? '' : `<span class="qualifier">${bi(T.sourceCandidate)}</span>`}</dt><dd data-field="source"><a data-source-link href="${esc(row.source_url)}" target="_blank" rel="noopener noreferrer nofollow" referrerpolicy="no-referrer">${esc(sourceText(row.source_url))}<span class="vh">${bi(T.newTab)}</span></a></dd></div>
</dl>
<details data-check-record><summary>${bi(T.checkRecord)}</summary><div class="record">
<p>${bi(T.rule)}</p>
${recheckDueDate ? `<p>${bi(T.recheckDue)}：${dateHtml(recheckDueDate)}</p>` : ''}
<p class="record-url">${esc(row.source_url)}</p>
</div></details>`;
}

export function renderRow(row, fresh, recheckDueDate) {
  const chips = ['closed', 'capped', 'geo_excluded']
    .filter((s) => row.status.includes(s))
    .map((s) => `<li class="chip chip--${s}">${esc(T.statusChip[s][0])} <span lang="en">${esc(T.statusChip[s][1])}</span></li>`)
    .join('');
  return `<li><article data-museum-row data-row-id="${esc(row.id)}" data-org="${esc(row.org)}" data-program-zh="${esc(row.program.zh)}" data-program-en="${esc(row.program.en)}" data-status="${esc(row.status.join(' '))}" data-as-of="${esc(row.as_of)}" data-source-url="${esc(row.source_url)}" data-page-read="${row.page_read === true ? 'true' : 'false'}" data-verified-on="${esc(row.verified_on ?? '')}" data-freshness="${esc(fresh)}" data-why-not-joinable-zh="${esc(row.why_not_joinable.zh)}" data-why-not-joinable-en="${esc(row.why_not_joinable.en)}" aria-labelledby="row-${esc(row.id)}-title">
<div class="card-main">
<h3 id="row-${esc(row.id)}-title"><span class="name-zh">${esc(row.program.zh)}</span> <span class="name-en" lang="en">${esc(row.program.en)}</span></h3>
<ul class="chips" aria-label="状态 / Status" data-field="status">${chips}</ul>
<figure class="wall-label" data-field="why_not_joinable">
<figcaption>${bi(T.wallLabel)} · ${bi(T.reason)}</figcaption>
<p lang="zh-CN" class="reason-zh">${esc(row.why_not_joinable.zh)}</p>
<p lang="en" class="reason-en">${esc(row.why_not_joinable.en)}</p>
</figure>
</div>
<div class="card-facts" data-facts>${renderFacts(row, fresh, recheckDueDate)}</div>
</article></li>`;
}
