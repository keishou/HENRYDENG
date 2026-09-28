// Oura API v2 客户端 + 数据归一化。两种模式：
//  server：经本项目 Node 服务代理（OAuth2 code flow，token 在服务器）
//  direct：浏览器直连 api.ouraring.com（implicit flow 的 access_token 或旧 PAT）
import { localParts, addDays, median, todayISO, ringMinutes } from './time.js';

export const OURA_API = 'https://api.ouraring.com/v2/usercollection';
export const OURA_AUTHORIZE = 'https://cloud.ouraring.com/oauth/authorize';
export const DEFAULT_SCOPES = 'daily heartrate stress tag';
const COLLECTIONS = ['daily_readiness', 'daily_sleep', 'sleep', 'daily_activity', 'daily_stress', 'sleep_time', 'daily_resilience'];

export class OuraClient {
  /** @param {{mode:'server'|'direct', token?:string, appKey?:string}} opts */
  constructor(opts) { this.mode = opts.mode; this.token = opts.token || null; this.appKey = opts.appKey || ''; }

  async fetchCollection(collection, params = {}) {
    const docs = [];
    let nextToken = null;
    for (let guard = 0; guard < 20; guard++) {
      const q = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) if (v != null) q.set(k, v);
      if (nextToken) q.set('next_token', nextToken);
      const url = this.mode === 'server' ? `/api/oura/${collection}?${q}` : `${OURA_API}/${collection}?${q}`;
      const headers = {};
      if (this.mode === 'server') { if (this.appKey) headers['x-app-key'] = this.appKey; }
      else headers.Authorization = `Bearer ${this.token}`;
      let res;
      try { res = await fetch(url, { headers }); } catch (e) {
        throw new OuraError(this.mode === 'direct' ? '浏览器直连 Oura 失败（多半是 CORS 被拒）。请改用服务器模式：运行 npm start 并通过它访问。' : `网络错误：${e.message}`, 0);
      }
      if (res.status === 401) throw new OuraError('Oura 授权已失效，请重新连接', 401);
      if (res.status === 403) throw new OuraError(`没有读取 ${collection} 的权限：请在 Oura 应用设置里勾选相应 scope 后重新授权`, 403);
      if (res.status === 429) throw new OuraError('Oura 限流（429），稍后再试', 429);
      if (!res.ok) throw new OuraError(`Oura ${collection} 返回 ${res.status}`, res.status);
      const json = await res.json();
      docs.push(...(json.data || []));
      nextToken = json.next_token || null;
      if (!nextToken) break;
    }
    return docs;
  }

  /** 拉取最近 N 天所有集合 → { fetchedAt, raw } */
  async loadWindow(days = 30, tz, now = new Date()) {
    const end = todayISO(tz, now);
    const start = addDays(end, -days);
    const params = { start_date: start, end_date: addDays(end, 1) };
    const raw = {};
    const errors = [];
    await Promise.all(COLLECTIONS.map(async (c) => {
      try { raw[c] = await this.fetchCollection(c, params); }
      catch (e) {
        // 单个集合失败（比如缺 scope）不应拖垮整体
        if (e.status === 401) throw e;
        raw[c] = []; errors.push({ collection: c, message: e.message });
      }
    }));
    return { fetchedAt: now.toISOString(), start, end, raw, errors };
  }
}

export class OuraError extends Error { constructor(msg, status) { super(msg); this.status = status; } }

/** raw → 按天索引的结构，供引擎与分析共用 */
export function normalize(window, tz) {
  const days = {};
  const get = (d) => (days[d] ||= { day: d });
  const raw = window?.raw || {};
  for (const r of raw.daily_readiness || []) get(r.day).readiness = { score: r.score ?? null, temperature_deviation: r.temperature_deviation ?? null, temperature_trend_deviation: r.temperature_trend_deviation ?? null, contributors: r.contributors || {} };
  for (const s of raw.daily_sleep || []) get(s.day).sleep = { score: s.score ?? null, contributors: s.contributors || {} };
  for (const s of raw.sleep || []) {
    if (s.type && s.type !== 'long_sleep' && s.type !== 'sleep') continue;
    const cur = get(s.day).sleepDetail;
    const cand = pickSleepFields(s);
    if (!cur || (cand.total_sleep_duration || 0) > (cur.total_sleep_duration || 0)) get(s.day).sleepDetail = cand;
  }
  for (const a of raw.daily_activity || []) get(a.day).activity = { score: a.score ?? null, steps: a.steps ?? null, high_activity_time: a.high_activity_time ?? null, medium_activity_time: a.medium_activity_time ?? null, active_calories: a.active_calories ?? null };
  for (const s of raw.daily_stress || []) get(s.day).stress = { day_summary: s.day_summary ?? null, stress_high: s.stress_high ?? null, recovery_high: s.recovery_high ?? null };
  for (const s of raw.sleep_time || []) get(s.day).sleepTime = { optimal_bedtime: s.optimal_bedtime || null, recommendation: s.recommendation || null, status: s.status || null };
  for (const r of raw.daily_resilience || []) get(r.day).resilience = { level: r.level || null, contributors: r.contributors || {} };
  return { fetchedAt: window?.fetchedAt || null, errors: window?.errors || [], days };
}

function pickSleepFields(s) {
  return {
    bedtime_start: s.bedtime_start, bedtime_end: s.bedtime_end, type: s.type || null,
    average_hrv: s.average_hrv ?? null, average_heart_rate: s.average_heart_rate ?? null, lowest_heart_rate: s.lowest_heart_rate ?? null,
    latency: s.latency ?? null, efficiency: s.efficiency ?? null, total_sleep_duration: s.total_sleep_duration ?? null,
    deep_sleep_duration: s.deep_sleep_duration ?? null, rem_sleep_duration: s.rem_sleep_duration ?? null, light_sleep_duration: s.light_sleep_duration ?? null,
    average_breath: s.average_breath ?? null, readiness: s.readiness || null,
  };
}

/** 取“今天”的上下文（今天没数据就退到最近一天）+ 14 天基线 */
export function todayContext(normalized, tz, now = new Date()) {
  const days = normalized?.days || {};
  const today = todayISO(tz, now);
  const sorted = Object.keys(days).sort();
  let dataDay = null;
  for (let i = sorted.length - 1; i >= 0; i--) { const d = sorted[i]; if (d <= today && (days[d].readiness || days[d].sleep || days[d].sleepDetail)) { dataDay = d; break; } }
  if (!dataDay) return null;
  const d = days[dataDay];
  const latest = (field) => { for (let i = sorted.length - 1; i >= 0; i--) { const x = days[sorted[i]]; if (sorted[i] <= today && x[field]) return x[field]; } return null; };
  const base = baselines(days, dataDay, tz);
  return {
    dataDay, today, stale: dataDay !== today,
    readiness: d.readiness || null, sleep: d.sleep || null, sleepDetail: d.sleepDetail || null,
    activity: d.activity || latest('activity'), stress: d.stress || latest('stress'), sleepTime: latest('sleepTime'), resilience: latest('resilience'),
    baselines: base,
  };
}

export function baselines(days, beforeDay, tz, n = 14) {
  const keys = Object.keys(days).filter((k) => k < beforeDay).sort().slice(-n);
  const hrv = [], rhr = [], sleepScore = [], readiness = [], bedRel = [], wake = [];
  for (const k of keys) {
    const d = days[k];
    if (typeof d.sleepDetail?.average_hrv === 'number') hrv.push(d.sleepDetail.average_hrv);
    if (typeof d.sleepDetail?.lowest_heart_rate === 'number') rhr.push(d.sleepDetail.lowest_heart_rate);
    if (typeof d.sleep?.score === 'number') sleepScore.push(d.sleep.score);
    if (typeof d.readiness?.score === 'number') readiness.push(d.readiness.score);
    if (d.sleepDetail?.bedtime_start) { const p = localParts(new Date(d.sleepDetail.bedtime_start), tz); bedRel.push(ringMinutes(p.minutes, 18 * 60)); }
    if (d.sleepDetail?.bedtime_end) wake.push(localParts(new Date(d.sleepDetail.bedtime_end), tz).minutes);
  }
  const bedMed = median(bedRel);
  return {
    n: keys.length,
    hrv: median(hrv), rhr: median(rhr), sleepScore: median(sleepScore), readiness: median(readiness),
    bedtimeMinutes: bedMed == null ? null : (bedMed + 18 * 60) % 1440,
    wakeMinutes: median(wake),
  };
}

/** 静态部署用：构造 implicit flow 授权 URL（response_type=token，30 天有效，无 refresh） */
export function buildImplicitAuthUrl(clientId, redirectUri, scopes = DEFAULT_SCOPES) {
  const state = Math.random().toString(36).slice(2);
  sessionStorage.setItem('tide:oauth_state', state);
  const q = new URLSearchParams({ response_type: 'token', client_id: clientId, redirect_uri: redirectUri, scope: scopes, state });
  return `${OURA_AUTHORIZE}?${q}`;
}

/** 解析 implicit flow 回跳的 hash */
export function parseImplicitCallback(hash) {
  if (!hash || !hash.includes('access_token')) return null;
  const q = new URLSearchParams(hash.replace(/^#/, ''));
  const token = q.get('access_token');
  const state = q.get('state');
  const expected = sessionStorage.getItem('tide:oauth_state');
  if (!token) return null;
  if (expected && state !== expected) return { error: 'state 不匹配，已忽略此次回跳' };
  const expiresIn = +q.get('expires_in') || 30 * 86400;
  return { token, expiresAt: Date.now() + expiresIn * 1000, scope: q.get('scope') || '' };
}
