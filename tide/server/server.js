// 潮汐服务器：静态托管 + Oura OAuth2 + API 代理 + Web Push + 每日自动计划。
// 零外部依赖（web-push 可选：缺失时只是关闭推送）。
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadEnv, JsonStore, readJson, parseCookies, safeEqual, randomId, MIME } from './util.js';
import { OuraAuth } from './oura-auth.js';
import { computePlan, VERDICT_LABEL } from '../public/js/engine.js';
import { analyzeSessions } from '../public/js/insights.js';
import { OuraClient, normalize, todayContext, DEFAULT_SCOPES } from '../public/js/oura.js';
import { localParts, defaultTZ, parseHHMM } from '../public/js/time.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
loadEnv(path.join(ROOT, '.env'));

const PORT = Number(process.env.PORT || 8787);
const PUBLIC_URL = (process.env.PUBLIC_URL || `http://localhost:${PORT}`).replace(/\/$/, '');
const APP_PASSWORD = process.env.APP_PASSWORD || '';
const TZ = process.env.TZ || defaultTZ();
const DAILY_PLAN_AT = process.env.DAILY_PLAN_AT || '08:30';
const PUBLIC_DIR = path.join(ROOT, 'public');
const store = new JsonStore(path.join(ROOT, 'data'));
const log = { info: (...a) => console.log(new Date().toISOString(), ...a), warn: (...a) => console.warn(new Date().toISOString(), ...a) };

const auth = new OuraAuth({
  clientId: process.env.OURA_CLIENT_ID || '', clientSecret: process.env.OURA_CLIENT_SECRET || '',
  redirectUri: `${PUBLIC_URL}/auth/callback`, scopes: process.env.OURA_SCOPES || DEFAULT_SCOPES, store, log,
});

/* ---------------- Web Push ---------------- */
let webpush = null; let vapid = null;
try {
  webpush = (await import('web-push')).default;
  vapid = store.read('vapid', null);
  if (!vapid) { vapid = webpush.generateVAPIDKeys(); store.write('vapid', vapid); log.info('[push] 已生成 VAPID 密钥'); }
  webpush.setVapidDetails(process.env.VAPID_SUBJECT || 'mailto:tide@example.com', vapid.publicKey, vapid.privateKey);
} catch (e) { webpush = null; log.warn('[push] 未启用：', e.message); }
const pushConfigured = !!webpush;

function subscriptions() { return store.read('subscriptions', []); }
function saveSubscriptions(list) { store.write('subscriptions', list); }
async function sendPush(payload, only = null) {
  if (!webpush) return { sent: 0 };
  const subs = subscriptions(); const keep = []; let sent = 0;
  for (const s of subs) {
    if (only && s.subscription.endpoint !== only) { keep.push(s); continue; }
    try { await webpush.sendNotification(s.subscription, JSON.stringify(payload), { TTL: 3600 }); sent++; keep.push(s); }
    catch (e) {
      if (e.statusCode === 404 || e.statusCode === 410) log.warn('[push] 订阅失效，移除');
      else { log.warn('[push] 发送失败', e.statusCode || e.message); keep.push(s); }
    }
  }
  if (keep.length !== subs.length) saveSubscriptions(keep);
  return { sent };
}

/* ---------------- 提醒调度 ---------------- */
function schedule() { return store.read('schedule', { reminders: [] }); }
function setSchedule(reminders, source) {
  const list = (reminders || []).filter((r) => r && r.at && r.title).map((r) => ({ id: randomId(8), at: r.at, kind: r.kind || 'reminder', title: r.title, body: r.body || '' }));
  store.write('schedule', { reminders: list, source, updatedAt: new Date().toISOString() });
  return list.length;
}
async function pumpSchedule() {
  const s = schedule(); if (!s.reminders?.length) return;
  const now = Date.now(); const due = s.reminders.filter((r) => new Date(r.at).getTime() <= now);
  if (!due.length) return;
  const rest = s.reminders.filter((r) => new Date(r.at).getTime() > now);
  store.write('schedule', { ...s, reminders: rest });
  for (const r of due) {
    if (now - new Date(r.at).getTime() > 30 * 60000) continue; // 过期太久就不发了
    const res = await sendPush({ title: r.title, body: r.body, tag: `tide-${r.kind}` });
    log.info(`[push] ${r.kind} "${r.title}" → ${res.sent}`);
  }
}

/* ---------------- 每日计划 ---------------- */
let lastPlanDay = store.read('plan', null)?.day || null;
async function runDailyPlan({ trigger = 'cron' } = {}) {
  const st = store.read('state', { profile: null, sessions: [] });
  const profile = { ...(st.profile || {}) };
  const tz = profile.timezone || TZ;
  profile.timezone = tz;
  const now = new Date();
  let ctx = null; let normalized = null;
  if (auth.connected) {
    const token = await auth.accessToken();
    const client = new OuraClient({ mode: 'direct', token });
    const win = await client.loadWindow(30, tz, now);
    normalized = normalize(win, tz);
    ctx = todayContext(normalized, tz, now);
    store.write('oura_cache', win);
  }
  const insights = analyzeSessions({ sessions: st.sessions || [], days: normalized?.days || {}, tz });
  const plan = computePlan({ now, profile, oura: ctx, sessions: st.sessions || [], adjustments: insights.adjustments });
  store.write('plan', { ...plan, trigger });
  lastPlanDay = plan.day;
  const scheduled = setSchedule(plan.reminders, `server:${trigger}`);
  const summary = { title: `今天：${VERDICT_LABEL[plan.verdict]}`, body: plan.headline, tag: 'tide-daily' };
  const res = await sendPush(summary);
  log.info(`[plan] ${plan.day} ${plan.verdict} "${plan.headline}" 提醒 ${scheduled} 条，推送 ${res.sent}`);
  return { plan, scheduled, pushed: res.sent };
}
function dailyTick() {
  const st = store.read('state', null);
  const tz = st?.profile?.timezone || TZ;
  const p = localParts(new Date(), tz);
  const target = parseHHMM(DAILY_PLAN_AT) ?? 510;
  if (p.minutes >= target && p.minutes < target + 3 && lastPlanDay !== p.dayISO) {
    lastPlanDay = p.dayISO;
    runDailyPlan({ trigger: 'cron' }).catch((e) => log.warn('[plan] 失败：', e.message));
  }
}
setInterval(() => { pumpSchedule().catch((e) => log.warn('[push] pump', e.message)); dailyTick(); }, 20000);

/* ---------------- HTTP ---------------- */
function send(res, status, body, headers = {}) {
  const isObj = body !== null && typeof body === 'object' && !Buffer.isBuffer(body);
  res.writeHead(status, { 'content-type': isObj ? 'application/json; charset=utf-8' : (headers['content-type'] || 'text/plain; charset=utf-8'), 'cache-control': 'no-store', ...headers });
  res.end(isObj ? JSON.stringify(body) : body);
}
function redirect(res, to, headers = {}) { res.writeHead(302, { location: to, ...headers }); res.end(); }
function authorized(req, url) {
  if (!APP_PASSWORD) return true;
  const key = req.headers['x-app-key'] || url.searchParams.get('key') || parseCookies(req).tide_key || '';
  return safeEqual(key, APP_PASSWORD);
}

async function handleApi(req, res, url) {
  const p = url.pathname;
  if (p === '/api/config') {
    const t = auth.tokens();
    return send(res, 200, { serverMode: true, oauthConfigured: auth.configured, connected: auth.connected, expiresAt: t?.expires_at || null, scopes: t?.scope || '', pushConfigured, vapidPublicKey: vapid?.publicKey || null, tz: TZ, dailyPlanAt: DAILY_PLAN_AT, requiresKey: !!APP_PASSWORD, publicUrl: PUBLIC_URL, redirectUri: auth.redirectUri });
  }
  const m = /^\/api\/oura\/([a-z0-9_]+)$/.exec(p);
  if (m && req.method === 'GET') {
    if (!auth.connected) return send(res, 401, { error: '未连接 Oura' });
    const q = new URLSearchParams();
    for (const k of ['start_date', 'end_date', 'next_token', 'start_datetime', 'end_datetime']) if (url.searchParams.has(k)) q.set(k, url.searchParams.get(k));
    const target = `https://api.ouraring.com/v2/usercollection/${m[1]}?${q}`;
    const call = async (token) => fetch(target, { headers: { authorization: `Bearer ${token}` } });
    try {
      let token = await auth.accessToken();
      let r = await call(token);
      if (r.status === 401) { token = await auth.accessToken({ force: true }); r = await call(token); }
      const text = await r.text();
      return send(res, r.status, text, { 'content-type': r.headers.get('content-type') || 'application/json; charset=utf-8' });
    } catch (e) { return send(res, e.status || 502, { error: e.message }); }
  }
  if (p === '/api/state') {
    if (req.method === 'GET') return send(res, 200, store.read('state', { profile: null, sessions: [] }));
    if (req.method === 'PUT') {
      const body = await readJson(req);
      const profile = body.profile && typeof body.profile === 'object' ? body.profile : null;
      const sessions = Array.isArray(body.sessions) ? body.sessions.filter((s) => s && s.ts).slice(-2000) : [];
      store.write('state', { profile, sessions, updatedAt: new Date().toISOString() });
      return send(res, 200, { ok: true, sessions: sessions.length });
    }
  }
  if (p === '/api/plan' && req.method === 'GET') return send(res, 200, store.read('plan', null) || { error: '还没算过' });
  if (p === '/api/plan/run' && req.method === 'POST') {
    try { const r = await runDailyPlan({ trigger: 'manual' }); return send(res, 200, r); }
    catch (e) { return send(res, e.status || 500, { error: e.message }); }
  }
  return send(res, 404, { error: 'not found' });
}

async function handlePush(req, res, url) {
  if (!pushConfigured) return send(res, 503, { error: '推送未启用' });
  const p = url.pathname;
  if (p === '/push/vapid-public-key') return send(res, 200, { publicKey: vapid.publicKey });
  if (p === '/push/subscribe' && req.method === 'POST') {
    const sub = await readJson(req);
    if (!sub?.endpoint || !sub?.keys?.p256dh) return send(res, 400, { error: '订阅格式不对' });
    const list = subscriptions().filter((s) => s.subscription.endpoint !== sub.endpoint);
    list.push({ subscription: sub, createdAt: new Date().toISOString(), ua: req.headers['user-agent'] || '' });
    saveSubscriptions(list);
    return send(res, 200, { ok: true, count: list.length });
  }
  if (p === '/push/unsubscribe' && req.method === 'POST') {
    const { endpoint } = await readJson(req);
    saveSubscriptions(subscriptions().filter((s) => s.subscription.endpoint !== endpoint));
    return send(res, 200, { ok: true });
  }
  if (p === '/push/test' && req.method === 'POST') {
    const r = await sendPush({ title: '潮汐 · 测试', body: '推送通了。关掉页面也能收到这类提醒。', tag: 'tide-test' });
    return send(res, 200, r);
  }
  if (p === '/push/schedule' && req.method === 'POST') {
    const body = await readJson(req);
    const n = setSchedule(body.reminders, 'client');
    return send(res, 200, { scheduled: n });
  }
  return send(res, 404, { error: 'not found' });
}

async function handleAuth(req, res, url) {
  const p = url.pathname;
  if (p === '/auth/login') {
    if (!auth.configured) return send(res, 500, '服务器未配置 OURA_CLIENT_ID / OURA_CLIENT_SECRET');
    const state = auth.newState();
    const cookies = [`tide_state=${state}; Path=/; HttpOnly; SameSite=Lax; Max-Age=600`];
    if (APP_PASSWORD) cookies.push(`tide_key=${encodeURIComponent(url.searchParams.get('key') || '')}; Path=/; HttpOnly; SameSite=Lax; Max-Age=600`);
    res.writeHead(302, { location: auth.loginUrl(state), 'set-cookie': cookies }); return res.end();
  }
  if (p === '/auth/callback') {
    const cookies = parseCookies(req);
    const err = url.searchParams.get('error');
    if (err) return redirect(res, `/?error=${encodeURIComponent(err)}`);
    const code = url.searchParams.get('code'); const state = url.searchParams.get('state');
    if (!code || !state || state !== cookies.tide_state) return redirect(res, '/?error=state_mismatch');
    try { await auth.exchangeCode(code); log.info('[oura] 已连接'); return redirect(res, '/?connected=1', { 'set-cookie': 'tide_state=; Path=/; Max-Age=0' }); }
    catch (e) { log.warn('[oura] 换取 token 失败：', e.message); return redirect(res, `/?error=${encodeURIComponent(e.message.slice(0, 120))}`); }
  }
  if (p === '/auth/logout' && req.method === 'POST') { await auth.logout(); store.remove('plan'); return send(res, 200, { ok: true }); }
  return send(res, 404, { error: 'not found' });
}

function serveStatic(req, res, url) {
  let rel = decodeURIComponent(url.pathname);
  if (rel === '/') rel = '/index.html';
  const file = path.normalize(path.join(PUBLIC_DIR, rel));
  if (!file.startsWith(PUBLIC_DIR)) return send(res, 403, 'forbidden');
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) return send(res, 404, 'not found');
    const ext = path.extname(file).toLowerCase();
    const noCache = ext === '.html' || ext === '.js' || ext === '.webmanifest' || ext === '.css';
    res.writeHead(200, { 'content-type': MIME[ext] || 'application/octet-stream', 'cache-control': noCache ? 'no-cache' : 'public, max-age=86400', 'service-worker-allowed': '/' });
    fs.createReadStream(file).pipe(res);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, PUBLIC_URL);
  try {
    if (url.pathname.startsWith('/auth/')) {
      if (url.pathname !== '/auth/callback' && !authorized(req, url)) return send(res, 401, { error: '需要访问口令' });
      return await handleAuth(req, res, url);
    }
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/push/')) {
      if (!authorized(req, url)) return send(res, 401, { error: '需要访问口令' });
      return url.pathname.startsWith('/api/') ? await handleApi(req, res, url) : await handlePush(req, res, url);
    }
    if (req.method !== 'GET' && req.method !== 'HEAD') return send(res, 405, 'method not allowed');
    return serveStatic(req, res, url);
  } catch (e) {
    log.warn('[http]', req.method, url.pathname, e.message);
    if (!res.headersSent) send(res, 500, { error: e.message });
  }
});

server.listen(PORT, () => {
  log.info(`潮汐 服务已启动：${PUBLIC_URL}  (端口 ${PORT}, 时区 ${TZ}, 每日计划 ${DAILY_PLAN_AT})`);
  log.info(`Oura OAuth：${auth.configured ? '已配置' : '未配置'}  redirect_uri=${auth.redirectUri}  推送：${pushConfigured ? '已启用' : '未启用'}`);
});
