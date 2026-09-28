// 个人 n-of-1 分析：把你记录的每次释放，与随后那一夜的 Oura 睡眠/HRV/次日 Readiness 对比基线，
// 按“时段”和“间隔”分桶，得出对你个人最有利的时机，并给引擎输出修正分。

import { localParts, addDays, median, mean, clamp, defaultTZ } from './time.js';
import { hourBucket, BUCKET_LABEL } from './engine.js';

export const INTERVAL_BUCKETS = ['first', 'lt1d', 'd1_2', 'd2_4', 'gt4d'];
export const INTERVAL_LABEL = { first: '首次/无前次', lt1d: '<24 小时', d1_2: '1–2 天', d2_4: '2–4 天', gt4d: '>4 天' };

export function intervalBucket(hours) {
  if (hours == null) return 'first';
  if (hours < 24) return 'lt1d';
  if (hours < 48) return 'd1_2';
  if (hours < 96) return 'd2_4';
  return 'gt4d';
}

const METRICS = [
  { key: 'sleepScore', label: '睡眠分', unit: '', get: (d) => d.sleep?.score },
  { key: 'readiness', label: '次日 Readiness', unit: '', get: (d) => d.readiness?.score },
  { key: 'hrv', label: '夜间 HRV', unit: 'ms', get: (d) => d.sleepDetail?.average_hrv },
  { key: 'latencyMin', label: '入睡时长', unit: 'min', get: (d) => (typeof d.sleepDetail?.latency === 'number' ? d.sleepDetail.latency / 60 : null), lowerBetter: true },
  { key: 'deepMin', label: '深睡', unit: 'min', get: (d) => (typeof d.sleepDetail?.deep_sleep_duration === 'number' ? d.sleepDetail.deep_sleep_duration / 60 : null) },
  { key: 'rhr', label: '最低心率', unit: 'bpm', get: (d) => d.sleepDetail?.lowest_heart_rate, lowerBetter: true },
];
export const METRIC_DEFS = METRICS;

/**
 * @param {object} p
 * @param {Array} p.sessions [{id, ts}]
 * @param {object} p.days  { 'YYYY-MM-DD': { readiness, sleep, sleepDetail } }  由 oura.js 提供
 * @param {string} [p.tz]
 */
export function analyzeSessions({ sessions = [], days = {}, tz }) {
  const zone = tz || defaultTZ();
  const sorted = [...sessions].map((s) => ({ ...s, t: new Date(s.ts) })).filter((s) => !Number.isNaN(s.t.getTime())).sort((a, b) => a.t - b.t);

  // 每次记录 → 影响的那一夜（Oura 的 day = 醒来日期）
  const outcomes = [];
  let prev = null;
  const sessionNights = new Set();
  for (const s of sorted) {
    const p = localParts(s.t, zone);
    const effectiveDay = p.hour < 5 ? addDays(p.dayISO, -1) : p.dayISO;
    const nightDay = addDays(effectiveDay, 1);
    sessionNights.add(nightDay);
    const hoursSincePrev = prev ? (s.t - prev.t) / 3600000 : null;
    outcomes.push({
      id: s.id, ts: s.ts, hour: p.hour, dayISO: p.dayISO, nightDay,
      hourBucket: hourBucket(p.hour), intervalBucket: intervalBucket(hoursSincePrev), hoursSincePrev,
      metrics: null, deltas: null, available: false,
    });
    prev = s;
  }

  // 基线：非“释放之夜”的中位数；样本不足则用全部
  const allDays = Object.keys(days).sort();
  let baselineDays = allDays.filter((d) => !sessionNights.has(d));
  if (baselineDays.length < 5) baselineDays = allDays;
  const baseline = {};
  for (const m of METRICS) baseline[m.key] = median(baselineDays.map((d) => m.get(days[d] || {})));
  const baselineN = baselineDays.length;

  for (const o of outcomes) {
    const d = days[o.nightDay];
    if (!d) continue;
    const metrics = {}; const deltas = {}; let any = false;
    for (const m of METRICS) {
      const v = m.get(d);
      metrics[m.key] = typeof v === 'number' ? v : null;
      deltas[m.key] = typeof v === 'number' && typeof baseline[m.key] === 'number' ? v - baseline[m.key] : null;
      if (deltas[m.key] != null) any = true;
    }
    o.metrics = metrics; o.deltas = deltas; o.available = any;
  }

  const avail = outcomes.filter((o) => o.available);
  const byHour = groupStats(avail, (o) => o.hourBucket, Object.keys(BUCKET_LABEL), baseline);
  const byInterval = groupStats(avail, (o) => o.intervalBucket, INTERVAL_BUCKETS, baseline);
  const overall = statsOf(avail, baseline);

  // 引擎修正：每个时段桶 n≥4 才生效，按综合影响换算成 ±15 内的分
  const adjustments = { byHourBucket: {} };
  for (const [k, g] of Object.entries(byHour)) {
    if (g.n >= 4 && typeof g.composite === 'number') adjustments.byHourBucket[k] = clamp(Math.round(g.composite * 0.6), -15, 15);
  }
  const bestHour = pickBest(byHour), bestInterval = pickBest(byInterval);

  return {
    tz: zone, baseline, baselineN, totalSessions: outcomes.length, analyzed: avail.length,
    overall, byHour, byInterval, adjustments, outcomes,
    bestHourBucket: bestHour, bestIntervalBucket: bestInterval,
    summary: buildSummary({ overall, byHour, byInterval, bestHour, bestInterval, analyzed: avail.length }),
  };
}

function statsOf(list, baseline) {
  const n = list.length;
  const meanDelta = {};
  for (const m of METRICS) meanDelta[m.key] = mean(list.map((o) => o.deltas?.[m.key]));
  const composite = compositeOf(meanDelta, baseline);
  return { n, meanDelta, composite, confidence: confidenceOf(n) };
}

function groupStats(list, keyFn, keys, baseline) {
  const out = {};
  for (const k of keys) out[k] = statsOf(list.filter((o) => keyFn(o) === k), baseline);
  return out;
}

/** 综合“夜间影响”：睡眠分Δ + ReadinessΔ − 入睡Δ/2 + HRV相对Δ%×0.3 + 深睡Δ/10 */
export function compositeOf(md, baseline) {
  let total = 0, parts = 0;
  const take = (v, w) => { if (typeof v === 'number' && Number.isFinite(v)) { total += v * w; parts++; } };
  take(md.sleepScore, 1);
  take(md.readiness, 1);
  take(md.latencyMin, -0.5);
  if (typeof md.hrv === 'number' && typeof baseline?.hrv === 'number' && baseline.hrv > 0) take((md.hrv / baseline.hrv) * 100, 0.3);
  take(md.deepMin, 0.1);
  return parts ? Math.round(total * 10) / 10 : null;
}

export function confidenceOf(n) {
  if (n < 3) return { level: 'insufficient', label: '数据不足', n };
  if (n < 6) return { level: 'preliminary', label: '初步', n };
  return { level: 'ok', label: '较可靠', n };
}

function pickBest(groups) {
  let best = null;
  for (const [k, g] of Object.entries(groups)) {
    if (g.n < 3 || typeof g.composite !== 'number') continue;
    if (!best || g.composite > best.composite) best = { key: k, composite: g.composite, n: g.n };
  }
  return best;
}

function buildSummary({ overall, byHour, byInterval, bestHour, bestInterval, analyzed }) {
  const lines = [];
  if (analyzed === 0) { lines.push('还没有可对比的夜晚：记录几次并等 Oura 同步后，这里会显示对你个人的影响。'); return lines; }
  const fmt = (v, digits = 1) => (typeof v === 'number' ? `${v > 0 ? '+' : ''}${v.toFixed(digits)}` : '—');
  lines.push(`已分析 ${analyzed} 次。总体：睡眠分 ${fmt(overall.meanDelta.sleepScore)}，次日 Readiness ${fmt(overall.meanDelta.readiness)}，入睡 ${fmt(overall.meanDelta.latencyMin)} 分钟，夜间 HRV ${fmt(overall.meanDelta.hrv)} ms（相对你的基线，${overall.confidence.label}）。`);
  if (bestHour) lines.push(`对你最友好的时段：${BUCKET_LABEL[bestHour.key]}（综合 ${fmt(bestHour.composite)}，n=${bestHour.n}）。`);
  else lines.push('时段对比：每个时段至少 3 次记录后才会给出结论。');
  if (bestInterval) lines.push(`最合适的间隔：${INTERVAL_LABEL[bestInterval.key]}（综合 ${fmt(bestInterval.composite)}，n=${bestInterval.n}）。`);
  const worst = Object.entries(byHour).filter(([, g]) => g.n >= 3 && typeof g.composite === 'number').sort((a, b) => a[1].composite - b[1].composite)[0];
  if (worst && bestHour && worst[0] !== bestHour.key && worst[1].composite < 0) lines.push(`注意：${BUCKET_LABEL[worst[0]]} 之后的夜晚指标偏差（综合 ${fmt(worst[1].composite)}，n=${worst[1].n}）。`);
  return lines;
}

export { BUCKET_LABEL };
