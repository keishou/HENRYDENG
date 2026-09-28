// 页面控制器：连接状态、数据刷新、计划计算、渲染、提醒。
import { computePlan, GOALS, VERDICT_LABEL, fmtDuration } from './engine.js';
import { analyzeSessions, BUCKET_LABEL, INTERVAL_LABEL, INTERVAL_BUCKETS, METRIC_DEFS } from './insights.js';
import { localParts, fmtHHMM, defaultTZ, parseHHMM, pad2 } from './time.js';
import { store, uid } from './store.js';
import { OuraClient, normalize, todayContext, buildImplicitAuthUrl, parseImplicitCallback } from './oura.js';
import { buildDemoWindow } from './demo.js';
import { notificationSupport, requestPermission, scheduleLocal, showNow, subscribePush, unsubscribePush, currentPushSubscription, buildICS, downloadText } from './reminders.js';

const $ = (s) => document.querySelector(s);
const state = { server: null, client: null, normalized: null, ctx: null, plan: null, insights: null, tz: defaultTZ(), pushSub: null, tableView: false };

/* ---------- 基础工具 ---------- */
function toast(msg, ms = 2600) { const t = $('#toast'); t.textContent = msg; t.classList.remove('hidden'); clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.add('hidden'), ms); }
async function apiFetch(path, opts = {}) {
  const headers = { 'content-type': 'application/json', ...(opts.headers || {}) };
  const key = store.getAppKey(); if (key) headers['x-app-key'] = key;
  const res = await fetch(path, { ...opts, headers });
  if (!res.ok) { let msg = `${res.status}`; try { msg = (await res.json()).error || msg; } catch { /* ignore */ } throw new Error(msg); }
  const ct = res.headers.get('content-type') || '';
  return ct.includes('json') ? res.json() : res.text();
}
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const signed = (v, d = 0) => (typeof v === 'number' ? `${v > 0 ? '+' : ''}${v.toFixed(d)}` : '—');
function localInputValue(date, tz) { const p = localParts(date, tz); return `${p.dayISO}T${pad2(p.hour)}:${pad2(p.minute)}`; }
function fromLocalInput(v, tz) { const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})/.exec(v); if (!m) return null; return import('./time.js').then(({ makeLocalDate }) => makeLocalDate(m[1], (+m[2]) * 60 + (+m[3]), tz)); }

/* ---------- 初始化 ---------- */
async function init() {
  const profile = store.getProfile();
  state.tz = profile.timezone || defaultTZ();
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js').catch((e) => console.warn('sw', e));
  bindUI();
  await detectServer();
  handleCallbacks();
  setupClient();
  renderSettings();
  await refresh({ useCache: true });
  setInterval(() => { if (state.plan) compute(); }, 60000);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') refresh({ useCache: true }); });
}

async function detectServer() {
  try {
    const res = await fetch('/api/config', { headers: store.getAppKey() ? { 'x-app-key': store.getAppKey() } : {} });
    if (!res.ok) { state.server = res.status === 401 ? { needsKey: true } : null; return; }
    state.server = await res.json();
  } catch { state.server = null; }
}

function handleCallbacks() {
  const q = new URLSearchParams(location.search);
  if (q.get('connected') === '1') { toast('Oura 已连接'); history.replaceState(null, '', location.pathname); }
  if (q.get('error')) { toast(`授权失败：${q.get('error')}`, 5000); history.replaceState(null, '', location.pathname); }
  const cb = parseImplicitCallback(location.hash);
  if (cb) {
    if (cb.error) toast(cb.error, 5000);
    else { store.setDirectToken({ token: cb.token, expiresAt: cb.expiresAt, scope: cb.scope }); toast('已获得 Oura 授权（30 天）'); }
    history.replaceState(null, '', location.pathname);
  }
}

function setupClient() {
  state.client = null;
  if (store.isDemo()) return;
  if (state.server?.connected) state.client = new OuraClient({ mode: 'server', appKey: store.getAppKey() });
  else if (!state.server) {
    const t = store.getDirectToken();
    if (t?.token && (!t.expiresAt || t.expiresAt > Date.now())) state.client = new OuraClient({ mode: 'direct', token: t.token });
  }
}

/* ---------- 数据刷新与计算 ---------- */
async function refresh({ useCache = false } = {}) {
  const btn = $('#btn-refresh'); btn.classList.add('spin');
  try {
    const profile = store.getProfile();
    state.tz = profile.timezone || defaultTZ();
    if (store.isDemo()) {
      const demo = buildDemoWindow(state.tz);
      state.normalized = normalize(demo.window, state.tz);
      if (!store.getSessions().length) store.setSessions(demo.sessions);
    } else if (state.client) {
      const cache = store.getOuraCache();
      const fresh = cache && Date.now() - new Date(cache.fetchedAt).getTime() < 30 * 60000;
      if (useCache && fresh) state.normalized = normalize(cache, state.tz);
      else {
        try {
          const win = await state.client.loadWindow(30, state.tz);
          store.setOuraCache(win);
          state.normalized = normalize(win, state.tz);
          if (win.errors.length) toast(`部分数据未取到：${win.errors.map((e) => e.collection).join(', ')}`, 4000);
        } catch (e) {
          if (cache) { state.normalized = normalize(cache, state.tz); toast(`用缓存数据：${e.message}`, 5000); }
          else { state.normalized = null; toast(e.message, 6000); }
        }
      }
    } else {
      state.normalized = null;
    }
    compute();
    syncServerState();
  } finally { btn.classList.remove('spin'); }
}

function compute() {
  const profile = store.getProfile();
  const sessions = store.getSessions();
  const now = new Date();
  state.ctx = state.normalized ? todayContext(state.normalized, state.tz, now) : null;
  state.insights = analyzeSessions({ sessions, days: state.normalized?.days || {}, tz: state.tz });
  state.plan = computePlan({ now, profile: { ...profile, timezone: state.tz }, oura: state.ctx, sessions, adjustments: state.insights.adjustments });
  store.setLastPlan(state.plan);
  renderToday();
  renderLog();
  renderInsights();
  const prefs = store.getNotifyPrefs();
  if (prefs.local && typeof Notification !== 'undefined' && Notification.permission === 'granted') scheduleLocal(state.plan.reminders, now);
  syncServerSchedule();
}

let syncTimer = null;
function syncServerState() {
  if (!state.server || store.isDemo()) return;
  clearTimeout(syncTimer);
  syncTimer = setTimeout(() => {
    apiFetch('/api/state', { method: 'PUT', body: JSON.stringify({ profile: { ...store.getProfile(), timezone: state.tz }, sessions: store.getSessions() }) }).catch(() => {});
  }, 800);
}
let schedTimer = null;
function syncServerSchedule() {
  if (!state.server?.pushConfigured || !state.plan) return;
  clearTimeout(schedTimer);
  schedTimer = setTimeout(async () => {
    const sub = await currentPushSubscription();
    if (!sub) return;
    apiFetch('/push/schedule', { method: 'POST', body: JSON.stringify({ endpoint: sub.endpoint, reminders: state.plan.reminders, day: state.plan.day }) }).catch(() => {});
  }, 1200);
}

/* ---------- 渲染：今日 ---------- */
function renderToday() {
  const plan = state.plan, ctx = state.ctx;
  const v = $('#verdict'); v.className = `card verdict verdict-${plan.verdict}`;
  $('#verdict-tag').textContent = VERDICT_LABEL[plan.verdict];
  $('#verdict-meta').textContent = `${GOALS[plan.goal]} · ${plan.day}${ctx ? ` · 数据 ${ctx.dataDay}` : ' · 无 Oura 数据'}`;
  $('#headline').textContent = plan.headline;
  const sn = $('#stale-note');
  if (ctx?.stale) { sn.textContent = `今天的 Oura 数据还没同步（最新是 ${ctx.dataDay}），先按它算。戴着戒指打开 Oura App 同步后再刷新。`; sn.classList.remove('hidden'); } else sn.classList.add('hidden');

  // 连接状态
  const pill = $('#conn-pill');
  if (store.isDemo()) { pill.textContent = '演示数据'; pill.className = 'pill pill-warn'; }
  else if (state.client) { pill.textContent = state.client.mode === 'server' ? 'Oura 已连接' : 'Oura 直连'; pill.className = 'pill pill-good'; }
  else { pill.textContent = '未连接'; pill.className = 'pill pill-muted'; }

  renderChips();
  renderChart();
  // 最佳窗口
  const wc = $('#window-card');
  if (plan.bestWindow) {
    wc.classList.remove('hidden');
    $('#window-title').textContent = `最佳窗口 ${plan.bestWindow.startLabel}–${plan.bestWindow.endLabel} · ${plan.bestWindow.purpose}`;
    $('#window-score').textContent = `评分 ${plan.bestWindow.score}`;
    $('#window-reasons').innerHTML = plan.bestWindow.reasons.map((r) => `<li><span class="pts"></span><span>${esc(r)}</span></li>`).join('') || '<li>—</li>';
  } else wc.classList.add('hidden');
  $('#reasons').innerHTML = plan.reasons.map((r) => `<li><span class="pts ${r.pts > 0 ? 'pos' : r.pts < 0 ? 'neg' : ''}">${r.pts ? signed(r.pts) : '·'}</span><span>${esc(r.text)}</span></li>`).join('');
  // 提醒
  const rl = $('#reminders');
  rl.innerHTML = plan.reminders.length ? plan.reminders.map((r) => `<li><span class="t">${fmtHHMM(localParts(new Date(r.at), state.tz).minutes)}</span><span><div>${esc(r.title)}</div><div class="b">${esc(r.body)}</div></span></li>`).join('') : '<li class="note">今天没有待触发的提醒</li>';
  renderNotifyState();
  // 作息
  const s = plan.schedule;
  const src = { oura: 'Oura 最佳就寝窗口', history: '近 14 天实际作息', profile: '你的设置' }[s.bedSource];
  $('#schedule').innerHTML = `<dl class="kv"><dt>起床</dt><dd>${s.wake}${s.wakeSource === 'history' ? '（近 14 天中位）' : ''}</dd><dt>就寝目标</dt><dd>${s.bed}（${src}）</dd>${s.ouraWindow ? `<dt>Oura 窗口</dt><dd>${s.ouraWindow.start}–${s.ouraWindow.end}${s.ouraWindow.status && s.ouraWindow.status !== 'optimal_found' ? ` · ${s.ouraWindow.status}` : ''}</dd>` : ''}${s.recommendation ? `<dt>Oura 建议</dt><dd>${recLabel(s.recommendation)}</dd>` : ''}<dt>距上次</dt><dd>${plan.interval.hoursSince == null ? '无记录' : fmtDuration(plan.interval.hoursSince)}${plan.interval.inCooldown ? `，冷却至 ${fmtHHMM(localParts(new Date(plan.interval.nextAllowedAt), state.tz).minutes)}` : ''}</dd></dl>`;
}
function recLabel(r) { return { improve_efficiency: '提高睡眠效率', earlier_bedtime: '早点睡', later_bedtime: '晚点睡', earlier_wake_up_time: '早点起', later_wake_up_time: '晚点起', follow_optimal_bedtime: '按最佳窗口就寝' }[r] || r; }

function renderChips() {
  const ctx = state.ctx; const el = $('#chips');
  if (!ctx) { el.innerHTML = `<div class="chip"><span class="k">Oura</span><span class="v">—</span><span class="d">${store.isDemo() ? '' : '去设置连接'}</span></div>`; return; }
  const b = ctx.baselines || {};
  const chips = [];
  const cls = (v, lo, hi) => (v == null ? '' : v >= hi ? 'good' : v < lo ? 'bad' : 'warn');
  chips.push({ k: 'Readiness', v: ctx.readiness?.score ?? '—', d: b.readiness != null && ctx.readiness?.score != null ? signed(ctx.readiness.score - b.readiness) : '', c: cls(ctx.readiness?.score, 60, 80) });
  chips.push({ k: '睡眠分', v: ctx.sleep?.score ?? '—', d: b.sleepScore != null && ctx.sleep?.score != null ? signed(ctx.sleep.score - b.sleepScore) : '', c: cls(ctx.sleep?.score, 60, 80) });
  const hrv = ctx.sleepDetail?.average_hrv;
  chips.push({ k: '夜间 HRV', v: hrv != null ? `${Math.round(hrv)}` : '—', d: hrv != null && b.hrv ? `${signed(((hrv / b.hrv) - 1) * 100)}%` : 'ms', c: hrv != null && b.hrv ? (hrv / b.hrv < 0.8 ? 'bad' : hrv / b.hrv > 1.05 ? 'good' : '') : '' });
  const rhr = ctx.sleepDetail?.lowest_heart_rate;
  chips.push({ k: '最低心率', v: rhr ?? '—', d: rhr != null && b.rhr ? (rhr - b.rhr === 0 ? '= 基线' : signed(rhr - b.rhr)) : 'bpm', c: rhr != null && b.rhr ? (rhr / b.rhr > 1.08 ? 'bad' : '') : '' });
  const t = ctx.readiness?.temperature_deviation;
  chips.push({ k: '体温偏差', v: t != null ? `${t > 0 ? '+' : ''}${t.toFixed(2)}°` : '—', d: '', c: t != null ? (t >= 0.5 ? 'bad' : t >= 0.3 ? 'warn' : 'good') : '' });
  const st = ctx.stress?.day_summary;
  chips.push({ k: '压力日', v: { restored: '恢复', normal: '正常', stressful: '偏高' }[st] || '—', d: '', c: st === 'stressful' ? 'warn' : st === 'restored' ? 'good' : '' });
  if (ctx.sleepDetail?.total_sleep_duration) chips.push({ k: '睡眠时长', v: `${(ctx.sleepDetail.total_sleep_duration / 3600).toFixed(1)}h`, d: ctx.sleepDetail.latency != null ? `入睡 ${Math.round(ctx.sleepDetail.latency / 60)}m` : '', c: '' });
  el.innerHTML = chips.map((c) => `<div class="chip ${c.c}"><span class="k">${c.k}</span><span class="v">${esc(c.v)}</span><span class="d">${esc(c.d)}</span></div>`).join('');
}

function seqColor(score) { return score >= 80 ? 'var(--seq-5)' : score >= 60 ? 'var(--seq-4)' : score >= 40 ? 'var(--seq-3)' : score >= 20 ? 'var(--seq-2)' : 'var(--seq-1)'; }

function renderChart() {
  const plan = state.plan; const el = $('#chart');
  const W = 720, H = 210, padL = 8, padR = 8, padT = 22, padB = 26;
  const cw = (W - padL - padR) / 24, gap = 2;
  const y = (s) => padT + (H - padT - padB) * (1 - s / 100);
  const parts = [];
  parts.push('<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="var(--surface)"/><rect width="2" height="6" fill="var(--seq-2)"/></pattern></defs>');
  // 睡眠时段底带
  plan.slots.forEach((s, i) => { if (s.phase === 'sleep') parts.push(`<rect class="sleepband" x="${padL + i * cw}" y="${padT}" width="${cw}" height="${H - padT - padB}"/>`); });
  // 最佳窗口底带
  if (plan.bestWindow) {
    const s0 = parseHHMM(plan.bestWindow.startLabel) / 60, s1 = parseHHMM(plan.bestWindow.endLabel) / 60;
    const e1 = s1 <= s0 ? 24 : s1;
    parts.push(`<rect class="win" x="${padL + s0 * cw}" y="${padT - 6}" width="${(e1 - s0) * cw}" height="${H - padT - padB + 6}" rx="4"/>`);
    parts.push(`<text class="lbl" x="${padL + ((s0 + e1) / 2) * cw}" y="${padT - 10}" text-anchor="middle">最佳 ${plan.bestWindow.startLabel}–${plan.bestWindow.endLabel}</text>`);
  }
  for (const g of [50, 100]) parts.push(`<line class="grid" x1="${padL}" x2="${W - padR}" y1="${y(g)}" y2="${y(g)}"/>`);
  parts.push(`<line class="grid" x1="${padL}" x2="${W - padR}" y1="${y(0)}" y2="${y(0)}"/>`);
  plan.slots.forEach((s, i) => {
    const x = padL + i * cw + gap / 2, w = cw - gap;
    const h = Math.max(0, y(0) - y(s.score));
    const fill = s.past ? 'var(--past)' : s.cooldown ? 'url(#hatch)' : seqColor(s.score);
    if (s.score > 0) parts.push(`<rect class="bar" data-i="${i}" x="${x}" y="${y(s.score)}" width="${w}" height="${h}" rx="3" fill="${fill}"${s.cooldown && !s.past ? ' stroke="var(--seq-2)" stroke-width="1"' : ''}/>`);
    if (s.current) parts.push(`<rect class="now" x="${x - 1}" y="${padT - 2}" width="${w + 2}" height="${H - padT - padB + 4}" rx="4"/>`);
    parts.push(`<rect class="hit" data-i="${i}" x="${padL + i * cw}" y="${padT - 6}" width="${cw}" height="${H - padT - padB + 6}"/>`);
  });
  for (const h of [0, 6, 12, 18, 24]) parts.push(`<text class="axis" x="${padL + h * cw}" y="${H - 8}" text-anchor="${h === 0 ? 'start' : h === 24 ? 'end' : 'middle'}">${h}:00</text>`);
  const top = plan.slots.filter((s) => !s.past && s.phase === 'day').sort((a, b) => b.score - a.score)[0];
  if (top) parts.push(`<text class="lbl" x="${padL + top.hour * cw + cw / 2}" y="${y(top.score) - 4}" text-anchor="middle">${top.score}</text>`);
  el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">${parts.join('')}</svg>`;
  // hover / tap
  const tip = $('#chart-tip');
  const show = (i, ev) => {
    const s = plan.slots[i];
    tip.innerHTML = `<b>${pad2(s.hour)}:00–${pad2(s.hour + 1)}:00 · 评分 ${s.score}${s.past ? '（已过）' : s.current ? '（现在）' : ''}</b>${s.reasons.length ? `<ul>${s.reasons.map((r) => `<li>${esc(r)}</li>`).join('')}</ul>` : ''}`;
    tip.classList.remove('hidden');
    const rect = el.getBoundingClientRect();
    const px = (ev.clientX ?? rect.left + rect.width / 2) - rect.left;
    tip.style.left = `${Math.min(Math.max(8, px - 120), rect.width - 268)}px`;
    tip.style.top = `${Math.max(0, (ev.clientY ?? rect.top) - rect.top - 90)}px`;
    el.querySelectorAll('.bar').forEach((b) => b.classList.toggle('hover', +b.dataset.i === i));
  };
  el.querySelectorAll('.hit').forEach((h) => {
    h.addEventListener('mousemove', (ev) => show(+h.dataset.i, ev));
    h.addEventListener('click', (ev) => show(+h.dataset.i, ev));
  });
  el.addEventListener('mouseleave', () => { tip.classList.add('hidden'); el.querySelectorAll('.bar.hover').forEach((b) => b.classList.remove('hover')); });
  // 表格视图
  $('#chart-table').innerHTML = `<table><thead><tr><th>时段</th><th class="num">评分</th><th>说明</th></tr></thead><tbody>${plan.slots.map((s) => `<tr><td>${pad2(s.hour)}:00${s.current ? ' ◂' : ''}</td><td class="num">${s.score}</td><td>${esc(s.reasons.join('；'))}</td></tr>`).join('')}</tbody></table>`;
}

function renderNotifyState() {
  const el = $('#notify-state'); const sup = notificationSupport();
  if (!sup.notification) { el.textContent = '此浏览器不支持'; el.className = 'pill pill-muted'; $('#btn-notify').disabled = true; return; }
  const p = Notification.permission;
  if (p === 'granted') { el.textContent = state.pushSub ? '本地 + 推送' : '本地通知'; el.className = 'pill pill-good'; $('#btn-notify').textContent = '发一条测试'; }
  else if (p === 'denied') { el.textContent = '已被拒绝'; el.className = 'pill pill-bad'; }
  else { el.textContent = '未开启'; el.className = 'pill pill-muted'; }
}

/* ---------- 渲染：记录 ---------- */
function renderLog() {
  const sessions = [...store.getSessions()].sort((a, b) => new Date(b.ts) - new Date(a.ts));
  $('#log-count').textContent = String(sessions.length);
  const outcomes = Object.fromEntries((state.insights?.outcomes || []).map((o) => [o.id, o]));
  const moods = { 1: '很差', 2: '差', 3: '一般', 4: '好', 5: '很好' };
  $('#log-list').innerHTML = sessions.length ? sessions.map((s) => {
    const p = localParts(new Date(s.ts), state.tz);
    const o = outcomes[s.id];
    let outcome = '<span class="note">这一夜的 Oura 数据还没到</span>';
    if (o?.available) {
      outcome = METRIC_DEFS.map((m) => { const d = o.deltas[m.key]; if (d == null) return ''; const good = m.lowerBetter ? d < 0 : d > 0; const cls = d === 0 ? '' : good ? 'pos' : 'neg'; return `<span>${m.label} <b class="${cls}">${signed(d, m.key === 'hrv' || m.key === 'latencyMin' || m.key === 'deepMin' ? 0 : 0)}${m.unit}</b></span>`; }).join('');
    }
    return `<li data-id="${esc(s.id)}"><div class="top"><span class="when">${p.dayISO} ${pad2(p.hour)}:${pad2(p.minute)}</span><span class="meta">${o ? BUCKET_LABEL[o.hourBucket] : ''}${o?.hoursSincePrev != null ? ` · 间隔 ${fmtDuration(o.hoursSincePrev)}` : ''}</span><button class="del" data-del="${esc(s.id)}">删除</button></div>${s.before || s.after || s.note ? `<div class="meta">${s.before ? `之前 ${moods[s.before]}` : ''}${s.after ? ` · 之后 ${moods[s.after]}` : ''}${s.note ? ` · ${esc(s.note)}` : ''}</div>` : ''}<div class="outcome">${outcome}</div></li>`;
  }).join('') : '<li class="note">还没有记录。用右下角按钮或上面的表单记一笔。</li>';
}

/* ---------- 渲染：洞察 ---------- */
function renderInsights() {
  const ins = state.insights;
  $('#insight-summary').innerHTML = ins.summary.map((l) => `<p>${esc(l)}</p>`).join('') + (ins.analyzed ? `<p class="note">基线：${ins.baselineN} 个非记录之夜的中位数（睡眠分 ${ins.baseline.sleepScore ?? '—'}，Readiness ${ins.baseline.readiness ?? '—'}，HRV ${ins.baseline.hrv ?? '—'} ms，入睡 ${ins.baseline.latencyMin != null ? Math.round(ins.baseline.latencyMin) : '—'} 分钟）</p>` : '');
  const table = (groups, labels, keys, adj) => `<table><thead><tr><th>分桶</th><th class="num">n</th><th class="num">睡眠分</th><th class="num">Readiness</th><th class="num">入睡(分)</th><th class="num">HRV</th><th class="num">综合</th><th>可信度</th>${adj ? '<th class="num">修正</th>' : ''}</tr></thead><tbody>${keys.map((k) => { const g = groups[k]; const c = (v, lowerBetter) => { if (v == null) return '<td class="num">—</td>'; const good = lowerBetter ? v < 0 : v > 0; return `<td class="num ${v === 0 ? '' : good ? 'pos' : 'neg'}">${signed(v, 1)}</td>`; }; return `<tr><td>${labels[k]}</td><td class="num">${g.n}</td>${c(g.meanDelta.sleepScore)}${c(g.meanDelta.readiness)}${c(g.meanDelta.latencyMin, true)}${c(g.meanDelta.hrv)}${c(g.composite)}<td>${g.confidence.label}</td>${adj ? `<td class="num">${adj[k] != null ? signed(adj[k]) : '—'}</td>` : ''}</tr>`; }).join('')}</tbody></table>`;
  $('#insight-hour').innerHTML = table(ins.byHour, BUCKET_LABEL, Object.keys(BUCKET_LABEL), ins.adjustments.byHourBucket);
  $('#insight-interval').innerHTML = table(ins.byInterval, INTERVAL_LABEL, INTERVAL_BUCKETS, null);
}

/* ---------- 渲染：设置 ---------- */
function renderSettings() {
  const p = store.getProfile();
  $('#p-goal').value = p.goal; $('#p-wake').value = p.wakeTime; $('#p-bed').value = p.bedTime; $('#p-oura-bed').checked = p.useOuraBedtime !== false;
  $('#p-min').value = p.minIntervalHours; $('#p-target').value = p.targetIntervalDays; $('#p-tz').value = p.timezone || '';
  renderFocusBlocks(p.focusBlocks || []);
  $('#demo-toggle').checked = store.isDemo();
  // 连接
  const srv = $('#conn-server'), dir = $('#conn-direct');
  if (state.server) {
    srv.classList.remove('hidden'); dir.classList.add('hidden');
    const s = state.server;
    if (s.needsKey) { $('#conn-server-status').textContent = '服务器要求访问口令。'; $('#appkey-row').classList.remove('hidden'); $('#btn-oauth').classList.add('hidden'); }
    else {
      $('#appkey-row').classList.toggle('hidden', !s.requiresKey);
      $('#btn-oauth').classList.toggle('hidden', s.connected || !s.oauthConfigured);
      $('#btn-logout').classList.toggle('hidden', !s.connected);
      $('#conn-server-status').textContent = s.connected ? `已连接 Oura（token 到期 ${s.expiresAt ? new Date(s.expiresAt).toLocaleString() : '未知'}，服务器会自动续期）。` : s.oauthConfigured ? '服务器已配置 OAuth，点下面登录。' : '服务器还没配置 OURA_CLIENT_ID / OURA_CLIENT_SECRET，见 README。';
    }
    $('#app-key').value = store.getAppKey();
    $('#btn-oauth').href = `/auth/login${store.getAppKey() ? `?key=${encodeURIComponent(store.getAppKey())}` : ''}`;
    const push = $('#push-status');
    push.textContent = s.pushConfigured ? `服务器每天 ${s.dailyPlanAt} 自动算一次并推送；订阅后关掉页面也能收到。` : '服务器未启用推送（web-push 未安装或 VAPID 生成失败）。';
    $('#btn-push').disabled = !s.pushConfigured; $('#btn-push-test').disabled = !s.pushConfigured; $('#btn-plan-now').disabled = !s.connected;
  } else {
    srv.classList.add('hidden'); dir.classList.remove('hidden');
    $('#client-id').value = store.getClientId();
    const t = store.getDirectToken();
    $('#conn-direct-status').textContent = t?.token ? `已保存 token${t.expiresAt ? `，到期 ${new Date(t.expiresAt).toLocaleDateString()}` : ''}。` : '尚未授权。';
    $('#push-status').textContent = '静态模式没有服务器，无法推送。可用“导出到日历”作为替代。';
    $('#btn-push').disabled = true; $('#btn-push-test').disabled = true; $('#btn-plan-now').disabled = true;
  }
  currentPushSubscription().then((sub) => { state.pushSub = sub; $('#btn-push').textContent = sub ? '取消推送订阅' : '订阅推送'; renderNotifyState(); });
}
function renderFocusBlocks(blocks) {
  $('#focus-blocks').innerHTML = blocks.map((b, i) => `<div class="focus-row"><input type="time" value="${esc(b.start)}" data-k="start" data-i="${i}" required> <span>–</span> <input type="time" value="${esc(b.end)}" data-k="end" data-i="${i}" required><button type="button" class="link-btn" data-rm="${i}">删</button></div>`).join('') || '<p class="note">没有专注时段：全天按作息评分。</p>';
}
function readFocusBlocks() {
  const rows = [...$('#focus-blocks').querySelectorAll('.focus-row')];
  return rows.map((r) => ({ start: r.querySelector('[data-k="start"]').value, end: r.querySelector('[data-k="end"]').value })).filter((b) => b.start && b.end);
}

/* ---------- 事件 ---------- */
function bindUI() {
  document.querySelectorAll('.tab-btn').forEach((b) => b.addEventListener('click', () => switchTab(b.dataset.tab)));
  $('#fab').addEventListener('click', () => { switchTab('log'); $('#log-ts').value = localInputValue(new Date(), state.tz); $('#log-ts').focus(); });
  $('#btn-refresh').addEventListener('click', () => refresh({ useCache: false }));
  $('#btn-table').addEventListener('click', () => { state.tableView = !state.tableView; $('#chart-table').classList.toggle('hidden', !state.tableView); $('#chart').classList.toggle('hidden', state.tableView); $('#btn-table').textContent = state.tableView ? '图表' : '表格'; $('#btn-table').setAttribute('aria-pressed', String(state.tableView)); });
  $('#btn-notify').addEventListener('click', async () => {
    const r = await requestPermission();
    if (r === 'granted') { store.setNotifyPrefs({ ...store.getNotifyPrefs(), local: true }); const n = scheduleLocal(state.plan.reminders); showNow('潮汐', n ? `通知已开启，今天还有 ${n} 条提醒` : '通知已开启'); }
    else toast(r === 'denied' ? '通知被浏览器拒绝，请在系统设置里允许' : '此环境不支持通知');
    renderNotifyState();
  });
  $('#btn-ics').addEventListener('click', () => { if (!state.plan?.reminders.length) return toast('今天没有可导出的提醒'); downloadText(`tide-${state.plan.day}.ics`, buildICS(state.plan.reminders, state.tz), 'text/calendar'); });

  // 记录
  $('#log-ts').value = localInputValue(new Date(), state.tz);
  $('#btn-log-now').addEventListener('click', () => { $('#log-ts').value = localInputValue(new Date(), state.tz); });
  $('#log-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const d = await fromLocalInput($('#log-ts').value, state.tz);
    if (!d) return toast('时间格式不对');
    store.addSession({ id: uid(), ts: d.toISOString(), before: $('#log-before').value ? +$('#log-before').value : null, after: $('#log-after').value ? +$('#log-after').value : null, note: $('#log-note').value.trim() });
    $('#log-note').value = ''; $('#log-before').value = ''; $('#log-after').value = '';
    toast('已记录'); compute(); syncServerState(); switchTab('today');
  });
  $('#log-list').addEventListener('click', (e) => { const id = e.target?.dataset?.del; if (!id) return; if (!confirm('删除这条记录？')) return; store.removeSession(id); compute(); syncServerState(); });

  // 设置：档案
  $('#profile-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const tz = $('#p-tz').value.trim();
    if (tz) { try { Intl.DateTimeFormat(undefined, { timeZone: tz }); } catch { return toast('时区名无效'); } }
    const p = { ...store.getProfile(), goal: $('#p-goal').value, wakeTime: $('#p-wake').value, bedTime: $('#p-bed').value, useOuraBedtime: $('#p-oura-bed').checked, focusBlocks: readFocusBlocks(), minIntervalHours: +$('#p-min').value, targetIntervalDays: +$('#p-target').value, timezone: tz || null };
    store.setProfile(p); state.tz = p.timezone || defaultTZ(); toast('已保存'); compute(); syncServerState();
  });
  $('#btn-add-focus').addEventListener('click', () => renderFocusBlocks([...readFocusBlocks(), { start: '09:00', end: '12:00' }]));
  $('#focus-blocks').addEventListener('click', (e) => { const i = e.target?.dataset?.rm; if (i == null) return; const b = readFocusBlocks(); b.splice(+i, 1); renderFocusBlocks(b); });

  // 设置：连接
  $('#app-key').addEventListener('change', async () => { store.setAppKey($('#app-key').value.trim()); await detectServer(); setupClient(); renderSettings(); refresh(); });
  $('#btn-oauth').addEventListener('click', (e) => { if (!state.server?.oauthConfigured) { e.preventDefault(); toast('服务器未配置 OAuth'); } });
  $('#btn-logout').addEventListener('click', async () => { await apiFetch('/auth/logout', { method: 'POST' }).catch(() => {}); store.setOuraCache(undefined); await detectServer(); setupClient(); renderSettings(); refresh(); });
  $('#btn-implicit').addEventListener('click', () => { const id = $('#client-id').value.trim(); if (!id) return toast('先填 Client ID'); store.setClientId(id); location.href = buildImplicitAuthUrl(id, location.origin + location.pathname); });
  $('#btn-save-token').addEventListener('click', () => { const t = $('#direct-token').value.trim(); if (!t) return toast('token 为空'); store.setDirectToken({ token: t, expiresAt: null }); $('#direct-token').value = ''; setupClient(); renderSettings(); refresh(); });
  $('#btn-clear-token').addEventListener('click', () => { store.setDirectToken(null); store.setOuraCache(undefined); setupClient(); renderSettings(); refresh(); });
  $('#demo-toggle').addEventListener('change', () => { store.setDemo($('#demo-toggle').checked); setupClient(); renderSettings(); refresh(); toast(store.isDemo() ? '演示模式：合成数据' : '已退出演示模式'); });

  // 推送
  $('#btn-push').addEventListener('click', async () => {
    try {
      if (state.pushSub) { await unsubscribePush(apiFetch); state.pushSub = null; toast('已取消推送'); }
      else {
        const perm = await requestPermission(); if (perm !== 'granted') return toast('需要先允许通知');
        state.pushSub = await subscribePush(state.server.vapidPublicKey, apiFetch); toast('已订阅推送'); syncServerSchedule();
      }
    } catch (e) { toast(`推送失败：${e.message}`, 5000); }
    renderSettings();
  });
  $('#btn-push-test').addEventListener('click', () => apiFetch('/push/test', { method: 'POST', body: '{}' }).then((r) => toast(`已发送到 ${r.sent} 个订阅`)).catch((e) => toast(`失败：${e.message}`)));
  $('#btn-plan-now').addEventListener('click', () => apiFetch('/api/plan/run', { method: 'POST', body: '{}' }).then((r) => toast(`服务器已计算：${r.plan?.headline || 'ok'}，安排 ${r.scheduled} 条提醒`, 5000)).catch((e) => toast(`失败：${e.message}`)));

  // 数据
  $('#btn-export').addEventListener('click', () => downloadText(`tide-backup-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(store.exportAll(), null, 2), 'application/json'));
  $('#import-file').addEventListener('change', async (e) => { const f = e.target.files?.[0]; if (!f) return; try { store.importAll(JSON.parse(await f.text())); toast('已导入'); renderSettings(); refresh({ useCache: true }); } catch { toast('文件不是有效 JSON'); } e.target.value = ''; });
  $('#btn-clear').addEventListener('click', () => { if (confirm('清空这台设备上的全部记录与设置？')) { store.clearAll(); location.reload(); } });
}

function switchTab(name) {
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('active', t.id === `tab-${name}`));
  document.querySelectorAll('.tab-btn').forEach((b) => b.classList.toggle('active', b.dataset.tab === name));
  window.scrollTo({ top: 0 });
}

init().catch((e) => { console.error(e); toast(`启动失败：${e.message}`, 8000); });
