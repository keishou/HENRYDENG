// Browser runtime (inlined after museum-core + museum-render by build.mjs).
// Recomputes freshness from the injected client date, re-validates every row from its
// data attributes, and filters, searches and sorts by toggling [hidden] and reordering <li>.
// It makes no network calls and keeps no persistent state.

(function () {
  const body = document.body;
  const context = body.dataset.context === 'fixtures' ? 'fixtures' : 'seed';
  const pad = (n) => String(n).padStart(2, '0');
  const now = new Date();
  const injected = typeof window.__MUSEUM_CLIENT_DATE__ === 'string' ? window.__MUSEUM_CLIENT_DATE__ : null;
  const clientDate = injected && isIsoDate(injected)
    ? injected
    : `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
  body.dataset.clientDate = clientDate;

  const form = document.querySelector('[data-filter-form]');
  const list = document.querySelector('[data-museum-list]');
  const count = document.querySelector('[data-result-count]');
  const empty = document.querySelector('[data-empty-state]');
  const rejectedNotice = document.querySelector('[data-rejected-notice]');
  const items = [...list.children];
  const total = items.length;
  let announceTimer = null;

  function rowFromDom(el) {
    const d = el.dataset;
    const pr = d.pageRead === 'true' ? true : d.pageRead === 'false' ? false : d.pageRead;
    return {
      id: d.rowId,
      org: d.org,
      program: { zh: d.programZh || '', en: d.programEn || '' },
      status: (d.status || '').split(' ').filter(Boolean),
      as_of: d.asOf ?? '',
      source_url: d.sourceUrl ?? '',
      page_read: pr,
      verified_on: d.verifiedOn ? d.verifiedOn : null,
      why_not_joinable: { zh: d.whyNotJoinableZh ?? '', en: d.whyNotJoinableEn ?? '' },
      ...(context === 'fixtures' ? { fixture_only: true } : {}),
    };
  }

  const norm = (s) => String(s).normalize('NFKC').toLowerCase().trim();

  function sortKey(row) {
    return [isIsoDate(row.as_of) ? row.as_of : '', row.program.en.toLowerCase()];
  }

  function apply({ announce = true } = {}) {
    const fd = new FormData(form);
    const q = norm(fd.get('q') || '');
    const status = fd.get('status') || 'all';
    const fresh = fd.get('freshness') || 'all';
    const sort = fd.get('sort') || 'checked_desc';
    let shown = 0;
    let rejected = 0;
    const entries = [];

    for (const li of items) {
      const el = li.querySelector('[data-museum-row]');
      const row = rowFromDom(el);
      const v = validateRow(row, { context });
      if (!v.valid) {
        li.hidden = true;
        el.dataset.rejected = v.code;
        rejected++;
        entries.push({ li, row, keep: false });
        continue;
      }
      delete el.dataset.rejected;
      const f = freshness(row, clientDate);
      const sig = JSON.stringify([row, f]);
      if (el.dataset.sig !== sig) {
        el.dataset.freshness = f;
        el.querySelector('[data-facts]').innerHTML = renderFacts(row, f, row.page_read === true ? recheckDue(row.verified_on) : null);
        el.dataset.sig = sig;
      }
      const match =
        (!q || norm(row.program.zh).includes(q) || norm(row.program.en).includes(q)) &&
        (status === 'all' || row.status.includes(status)) &&
        (fresh === 'all' || f === fresh);
      const wasHidden = li.hidden;
      li.hidden = !match;
      if (match) {
        shown++;
        if (wasHidden) {
          li.classList.add('entering');
          requestAnimationFrame(() => requestAnimationFrame(() => li.classList.remove('entering')));
        }
      }
      entries.push({ li, row, keep: true });
    }

    entries.sort((a, b) => {
      if (sort === 'name_asc') return a.row.program.en.localeCompare(b.row.program.en, 'en');
      const [da, na] = sortKey(a.row);
      const [db, nb] = sortKey(b.row);
      if (da !== db) return da && db ? (da < db ? 1 : -1) : da ? -1 : 1;
      return na.localeCompare(nb, 'en');
    });
    const active = document.activeElement;
    const current = [...list.children];
    if (entries.some((e, i) => current[i] !== e.li)) for (const e of entries) list.appendChild(e.li);
    if (active && active !== document.body && list.contains(active)) {
      if (active.closest('li[hidden]')) count.focus();
      else if (document.activeElement !== active) active.focus({ preventScroll: true });
    }

    empty.hidden = !(shown === 0 && total > 0);
    rejectedNotice.hidden = rejected === 0;
    rejectedNotice.textContent = rejected
      ? `${rejected} 条记录未通过校验，未显示。 / ${rejected} record(s) failed validation and are not shown.`
      : '';

    const text = `显示 ${shown} / ${total} 件 · Showing ${shown} of ${total}`;
    if (!announce) count.textContent = text;
    else {
      clearTimeout(announceTimer);
      announceTimer = setTimeout(() => { count.textContent = text; }, 250);
    }
  }

  form.addEventListener('submit', (e) => e.preventDefault());
  const search = form.querySelector('input[type="search"]');
  // Esc clears the query explicitly (Chromium's native clear does not fire an input event).
  search.addEventListener('keydown', (e) => { if (e.key === 'Escape' && search.value) { search.value = ''; apply(); } });
  search.addEventListener('search', () => apply());
  form.addEventListener('input', () => apply());
  form.addEventListener('change', () => apply());
  form.addEventListener('reset', () => requestAnimationFrame(() => apply()));
  empty.querySelector('[data-clear]').addEventListener('click', () => { form.reset(); search.focus(); });

  form.hidden = false;
  apply({ announce: false });
})();
