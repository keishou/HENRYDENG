// 评分引擎：把 Oura 身体数据 + 作息档案 + 间隔历史 → 24 小时逐时评分、今日结论、最佳窗口、提醒。
// 纯函数，浏览器与 Node（服务器每日计划）共用。所有规则见 README「评分逻辑与证据等级」。

import {
  localParts, makeLocalDate, parseHHMM, fmtHHMM, addDays, dayDiff, clamp, ringMinutes, defaultTZ,
} from './time.js';

export const GOALS = {
  sleep: '助眠优先',
  focus: '专注优先',
  balance: '平衡',
  recovery: '恢复优先',
};

export const DEFAULT_PROFILE = {
  goal: 'balance',
  wakeTime: '07:00',
  bedTime: '23:30',
  focusBlocks: [
    { start: '09:00', end: '12:00' },
    { start: '14:00', end: '18:00' },
  ],
  minIntervalHours: 36,
  targetIntervalDays: 3,
  useOuraBedtime: true,
  timezone: null,
};

export const VERDICT_LABEL = {
  go: '适合', ok: '可以', wait: '等待', rest: '休息', skip: '不建议',
};

/** 小时 → 时段桶（与 insights.js 共用） */
export function hourBucket(hour) {
  if (hour < 5) return 'late';
  if (hour < 11) return 'morning';
  if (hour < 17) return 'afternoon';
  if (hour < 21) return 'evening';
  return 'night';
}
export const BUCKET_LABEL = {
  morning: '早晨 5–11', afternoon: '午后 11–17', evening: '傍晚 17–21', night: '睡前 21–24', late: '深夜 0–5',
};

function bell(x, center, sigma) { const z = (x - center) / sigma; return Math.exp(-(z * z)); }

/** 解析就寝/起床时间：Oura sleep_time 窗口 > 近 14 天中位数 > 档案设置 */
export function resolveSchedule(profile, oura) {
  const out = {
    wakeM: parseHHMM(profile.wakeTime) ?? 420,
    bedM: parseHHMM(profile.bedTime) ?? 1410,
    bedSource: 'profile',
    wakeSource: 'profile',
    ouraWindow: null,
    recommendation: null,
  };
  const st = oura?.sleepTime;
  if (st?.optimal_bedtime && typeof st.optimal_bedtime.start_offset === 'number') {
    const s = ((Math.round(st.optimal_bedtime.start_offset / 60) % 1440) + 1440) % 1440;
    const e = ((Math.round(st.optimal_bedtime.end_offset / 60) % 1440) + 1440) % 1440;
    out.ouraWindow = { startM: s, endM: e, status: st.status || null };
    out.recommendation = st.recommendation || null;
    const usable = st.status === 'optimal_found' || st.status === 'only_recommended_found' || !st.status;
    if (profile.useOuraBedtime !== false && usable) {
      // 窗口可能跨午夜（如 22:30–00:30）：在环上取中点
      let span = e - s; if (span < 0) span += 1440;
      out.bedM = (s + Math.round(span / 2)) % 1440;
      out.bedSource = 'oura';
    }
  }
  const b = oura?.baselines;
  if (out.bedSource === 'profile' && typeof b?.bedtimeMinutes === 'number' && profile.useOuraBedtime !== false) {
    out.bedM = Math.round(b.bedtimeMinutes) % 1440; out.bedSource = 'history';
  }
  if (typeof b?.wakeMinutes === 'number' && profile.useOuraBedtime !== false) {
    out.wakeM = Math.round(b.wakeMinutes) % 1440; out.wakeSource = 'history';
  }
  return out;
}

/** 身体状态评估：返回全局加减分与原因 */
export function assessBody(oura, goal) {
  const mods = { global: 0, day: 0, preBed: 0, reasons: [], flags: { rest: false, illness: false, lowReadiness: false, poorSleep: false, stressed: false } };
  const add = (where, pts, text, kind = 'body') => { mods[where] += pts; mods.reasons.push({ text, pts, kind }); };
  if (!oura) { mods.reasons.push({ text: '未连接 Oura：仅按作息与间隔评分', pts: 0, kind: 'info' }); return mods; }

  const r = oura.readiness;
  if (r && typeof r.score === 'number') {
    if (r.score >= 85) add('global', 8, `Readiness ${r.score}，身体状态好`);
    else if (r.score >= 70) mods.reasons.push({ text: `Readiness ${r.score}，正常`, pts: 0, kind: 'body' });
    else if (r.score >= 60) add('global', -8, `Readiness ${r.score}，恢复一般`);
    else { add('global', -20, `Readiness ${r.score}，恢复不足`); mods.flags.lowReadiness = true; }
    if (r.score < 50) mods.flags.rest = true;
  }
  const t = r?.temperature_deviation;
  if (typeof t === 'number') {
    if (t >= 0.5) { add('global', -40, `体温比基线高 ${t.toFixed(2)}°C，可能在生病/炎症，今天以休息为主`); mods.flags.illness = true; mods.flags.rest = true; }
    else if (t >= 0.3) add('global', -12, `体温略高 (+${t.toFixed(2)}°C)`);
  }
  const sd = oura.sleepDetail; const b = oura.baselines || {};
  if (sd && typeof sd.average_hrv === 'number' && typeof b.hrv === 'number' && b.hrv > 0) {
    const ratio = sd.average_hrv / b.hrv;
    if (ratio < 0.8) add('global', -12, `夜间 HRV ${Math.round(sd.average_hrv)} ms，比 14 天基线低 ${Math.round((1 - ratio) * 100)}%`);
    else if (ratio > 1.1) add('global', 5, `夜间 HRV ${Math.round(sd.average_hrv)} ms，高于基线`);
  }
  if (sd && typeof sd.lowest_heart_rate === 'number' && typeof b.rhr === 'number' && b.rhr > 0) {
    const ratio = sd.lowest_heart_rate / b.rhr;
    if (ratio > 1.08) add('global', -10, `静息心率 ${sd.lowest_heart_rate} bpm，比基线高 ${Math.round((ratio - 1) * 100)}%`);
  }
  const s = oura.sleep;
  if (s && typeof s.score === 'number') {
    if (s.score < 60) {
      add('day', -12, `昨晚睡眠 ${s.score}，白天精力不足`);
      add('preBed', 8, '昨晚睡得差：今晚睡前窗口可作助眠');
      mods.flags.poorSleep = true;
    } else if (s.score >= 85) add('global', 3, `昨晚睡眠 ${s.score}，状态好`);
  }
  const st = oura.stress;
  if (st?.day_summary === 'stressful') { add('preBed', 8, '近日压力偏高：睡前释放有助放松'); mods.flags.stressed = true; }
  else if (st?.day_summary === 'restored') mods.reasons.push({ text: '压力恢复良好', pts: 0, kind: 'body' });
  const res = oura.resilience;
  if (res?.level === 'limited') add('global', -8, '长期韧性 limited：优先恢复');
  if (goal === 'recovery' && (mods.flags.lowReadiness || mods.flags.poorSleep)) add('global', -8, '恢复优先模式：状态不佳时更保守');
  return mods;
}

/** 间隔评估 */
export function assessInterval(now, sessions, profile) {
  const last = lastSessionTime(sessions);
  const minMs = (profile.minIntervalHours ?? 36) * 3600000;
  const out = { last, hoursSince: null, daysSince: null, nextAllowedAt: null, bonus: 0, reasons: [], inCooldown: false };
  if (!last) { out.reasons.push({ text: '暂无记录：先记一笔，引擎才能学习你的间隔', pts: 0, kind: 'interval' }); return out; }
  out.hoursSince = (now.getTime() - last.getTime()) / 3600000;
  out.daysSince = out.hoursSince / 24;
  out.nextAllowedAt = new Date(last.getTime() + minMs);
  if (now < out.nextAllowedAt) {
    out.inCooldown = true;
    out.reasons.push({ text: `距上次 ${fmtDuration(out.hoursSince)}，未到最短间隔 ${profile.minIntervalHours}h`, pts: -30, kind: 'interval' });
  } else {
    const target = profile.targetIntervalDays ?? 3;
    if (out.daysSince >= target * 2) { out.bonus = 12; out.reasons.push({ text: `距上次 ${fmtDuration(out.hoursSince)}，远超目标间隔`, pts: 12, kind: 'interval' }); }
    else if (out.daysSince >= target) { out.bonus = 8; out.reasons.push({ text: `距上次 ${fmtDuration(out.hoursSince)}，已到目标间隔 ${target} 天`, pts: 8, kind: 'interval' }); }
    else out.reasons.push({ text: `距上次 ${fmtDuration(out.hoursSince)}，已过最短间隔`, pts: 0, kind: 'interval' });
  }
  return out;
}

export function lastSessionTime(sessions) {
  let best = null;
  for (const s of sessions || []) {
    const t = new Date(s.ts);
    if (Number.isNaN(t.getTime())) continue;
    if (!best || t > best) best = t;
  }
  return best;
}

export function fmtDuration(hours) {
  if (hours == null) return '—';
  if (hours < 24) return `${Math.round(hours)} 小时`;
  const d = Math.floor(hours / 24), h = Math.round(hours % 24);
  return h ? `${d} 天 ${h} 小时` : `${d} 天`;
}

/**
 * 主入口。
 * @param {object} p
 * @param {Date} p.now
 * @param {object} p.profile  DEFAULT_PROFILE 形状
 * @param {object|null} p.oura  oura.js normalize() 输出（今日）
 * @param {Array} p.sessions  [{ts}]
 * @param {object|null} p.adjustments insights.js 输出 {byHourBucket:{morning:+3,...}}
 */
export function computePlan({ now = new Date(), profile = DEFAULT_PROFILE, oura = null, sessions = [], adjustments = null }) {
  const prof = { ...DEFAULT_PROFILE, ...(profile || {}) };
  const tz = prof.timezone || defaultTZ();
  const nowP = localParts(now, tz);
  const sched = resolveSchedule(prof, oura);
  const body = assessBody(oura, prof.goal);
  const interval = assessInterval(now, sessions, prof);
  const goal = prof.goal;

  const wakeM = sched.wakeM;
  const bedRel = ringMinutes(sched.bedM, wakeM); // 就寝相对起床的分钟
  const focus = (prof.focusBlocks || []).map((f) => ({ s: ringMinutes(parseHHMM(f.start) ?? 0, wakeM), e: ringMinutes(parseHHMM(f.end) ?? 0, wakeM) })).filter((f) => f.e > f.s);
  const focusPenaltyMul = goal === 'focus' ? 1.3 : goal === 'sleep' ? 0.8 : 1.0;
  const preBedMul = goal === 'sleep' ? 1.2 : goal === 'focus' ? 0.9 : 1.0;

  // 今天的 24 个小时槽，按“当前本地日”的 0..23 时
  const slots = [];
  for (let h = 0; h < 24; h++) {
    const mid = h * 60 + 30;
    const rel = ringMinutes(mid, wakeM);
    const start = makeLocalDate(nowP.dayISO, h * 60, tz);
    const end = makeLocalDate(nowP.dayISO, h * 60 + 60, tz);
    const reasons = [];
    let score;
    let phase;
    if (rel >= bedRel) {
      const over = rel - bedRel;
      phase = over < 120 ? 'late' : 'sleep';
      score = over < 120 ? 8 : 0;
      reasons.push(over < 120 ? '已过就寝时间：会推迟入睡' : '睡眠时段');
    } else {
      phase = 'day';
      score = 40;
      const mtb = bedRel - rel; // 距就寝分钟
      if (mtb >= 20 && mtb <= 180) {
        const bonus = 35 * bell(mtb, 80, 45) * preBedMul;
        score += bonus;
        if (bonus >= 8) reasons.push('睡前 1–2 小时：高潮后催乳素/催产素上升、副交感占优，有助入睡');
        score += body.preBed;
      } else if (mtb < 20) {
        score -= 5; reasons.push('太贴近就寝：清理与清醒会把入睡往后推');
      }
      if (rel >= 30 && rel <= 120) { score += 6; reasons.push('晨间：睾酮与精力处于日内高位'); }
      for (const f of focus) {
        if (rel >= f.s && rel < f.e) { score -= 35 * focusPenaltyMul; reasons.push('专注时段：高潮后短时动力/警觉下降，影响工作'); break; }
        if (rel < f.s && f.s - rel <= 90) { score -= 25 * focusPenaltyMul; reasons.push('专注时段前 90 分钟：留给状态爬升'); break; }
      }
      score += body.day + body.global + interval.bonus;
    }
    // 个人数据学习的修正
    const bucket = hourBucket(h);
    const adj = adjustments?.byHourBucket?.[bucket];
    if (typeof adj === 'number' && adj !== 0 && phase === 'day') { score += clamp(adj, -15, 15); reasons.push(`你的数据：${BUCKET_LABEL[bucket]} 时段 ${adj > 0 ? '+' : ''}${adj}`); }
    // 冷却期
    let cooldown = false;
    if (interval.nextAllowedAt && end <= interval.nextAllowedAt) { score = Math.min(score, 20); cooldown = true; reasons.push('冷却期：未到最短间隔'); }
    else if (interval.nextAllowedAt && start < interval.nextAllowedAt && end > interval.nextAllowedAt) { reasons.push(`冷却期于 ${fmtHHMM(localParts(interval.nextAllowedAt, tz).minutes)} 结束`); }
    score = clamp(Math.round(score), 0, 100);
    slots.push({ hour: h, start, end, score, phase, reasons, past: end <= now, current: start <= now && now < end, cooldown, bucket });
  }

  // 结论
  const future = slots.filter((s) => !s.past && s.phase === 'day' && !s.cooldown);
  const best = pickWindow(future);
  let verdict;
  if (body.flags.rest) verdict = 'rest';
  else if (interval.inCooldown && (!best || best.score < 45)) verdict = 'wait';
  else if (!best) verdict = 'skip';
  else if (best.score >= 60) verdict = 'go';
  else if (best.score >= 45) verdict = 'ok';
  else verdict = 'skip';

  const reasons = [...body.reasons, ...interval.reasons];
  const headline = buildHeadline(verdict, best, body, interval, tz, { ...sched, __todayISO: nowP.dayISO });

  const reminders = buildReminders({ now, tz, nowP, sched, best, interval, verdict, prof, body });
  return {
    generatedAt: now.toISOString(),
    tz, day: nowP.dayISO, goal,
    verdict, verdictLabel: VERDICT_LABEL[verdict], headline,
    reasons, flags: body.flags,
    schedule: { wake: fmtHHMM(sched.wakeM), bed: fmtHHMM(sched.bedM), bedSource: sched.bedSource, wakeSource: sched.wakeSource, ouraWindow: sched.ouraWindow ? { start: fmtHHMM(sched.ouraWindow.startM), end: fmtHHMM(sched.ouraWindow.endM), status: sched.ouraWindow.status } : null, recommendation: sched.recommendation },
    interval: { hoursSince: interval.hoursSince, daysSince: interval.daysSince, nextAllowedAt: interval.nextAllowedAt ? interval.nextAllowedAt.toISOString() : null, inCooldown: interval.inCooldown, last: interval.last ? interval.last.toISOString() : null },
    bestWindow: best ? { start: best.start.toISOString(), end: best.end.toISOString(), startLabel: fmtHHMM(best.startM), endLabel: fmtHHMM(best.endM), score: best.score, purpose: best.purpose, reasons: best.reasons } : null,
    slots: slots.map((s) => ({ hour: s.hour, score: s.score, phase: s.phase, past: s.past, current: s.current, cooldown: s.cooldown, reasons: s.reasons, start: s.start.toISOString(), end: s.end.toISOString() })),
    reminders,
  };

  function pickWindow(list) {
    if (!list.length) return null;
    let top = list[0];
    for (const s of list) if (s.score > top.score) top = s;
    const thr = top.score - 8;
    const idx = list.indexOf(top);
    let i0 = idx, i1 = idx;
    while (i0 > 0 && list[i0 - 1].hour === list[i0].hour - 1 && list[i0 - 1].score >= thr) i0--;
    while (i1 < list.length - 1 && list[i1 + 1].hour === list[i1].hour + 1 && list[i1 + 1].score >= thr) i1++;
    const startM = list[i0].hour * 60, endM = list[i1].hour * 60 + 60;
    const inPreBed = list.slice(i0, i1 + 1).some((s) => s.reasons.some((r) => r.startsWith('睡前 1–2 小时')));
    const purpose = inPreBed ? (body.flags.stressed ? '助眠 · 减压' : '助眠') : body.flags.stressed ? '减压' : '自由';
    const reasonsSet = new Set();
    for (const s of list.slice(i0, i1 + 1)) for (const r of s.reasons) reasonsSet.add(r);
    return { start: list[i0].start, end: list[i1].end, startM, endM, score: top.score, purpose, reasons: [...reasonsSet] };
  }
}

function buildHeadline(verdict, best, body, interval, tz, sched) {
  switch (verdict) {
    case 'rest': return body.flags.illness ? '体温偏高，今天让身体休息' : 'Readiness 很低，今天休息，明天再看';
    case 'wait': {
      if (!interval.nextAllowedAt) return '今天先等等';
      const p = localParts(interval.nextAllowedAt, tz);
      const dayWord = dayWordFor(p.dayISO, sched.__todayISO || p.dayISO);
      return `还在冷却期，${dayWord}${fmtHHMM(p.minutes)} 之后再说`;
    }
    case 'go': return `今天适合，最佳窗口 ${fmtHHMM(best.startM)}–${fmtHHMM(best.endM)}（${best.purpose}）`;
    case 'ok': return `可以，但不算最佳：${fmtHHMM(best.startM)}–${fmtHHMM(best.endM)}`;
    default: return best ? '今天剩余时段都不理想，建议跳过' : `今天窗口已过，就寝 ${fmtHHMM(sched.bedM)}`;
  }
}

function buildReminders({ now, tz, nowP, sched, best, interval, verdict, prof, body }) {
  const list = [];
  const push = (at, kind, title, text) => { if (at && at.getTime() > now.getTime() + 30000) list.push({ at: at.toISOString(), kind, title, body: text }); };
  if (best && (verdict === 'go' || verdict === 'ok')) {
    push(best.start, 'window', `最佳窗口开始 ${fmtHHMM(best.startM)}–${fmtHHMM(best.endM)}`, `${best.purpose} · 评分 ${best.score}。${(best.reasons[0] || '')}`);
  }
  // 就寝管理：睡前 30 分钟收尾提醒 + 就寝时间
  const bedToday = bedDateFor(nowP.dayISO, sched, tz);
  push(new Date(bedToday.getTime() - 30 * 60000), 'winddown', '睡前 30 分钟', `准备放下手机、调暗灯光。今晚目标就寝 ${fmtHHMM(sched.bedM)}${sched.bedSource === 'oura' ? '（Oura 最佳就寝窗口）' : ''}`);
  push(bedToday, 'bedtime', '就寝时间到', sched.ouraWindow ? `Oura 建议窗口 ${fmtHHMM(sched.ouraWindow.startM)}–${fmtHHMM(sched.ouraWindow.endM)}` : '按计划睡觉，明早 Readiness 会说话');
  if (interval.nextAllowedAt && interval.nextAllowedAt.getTime() - now.getTime() < 36 * 3600000) {
    push(interval.nextAllowedAt, 'cooldown_end', '冷却期结束', `距上次已满 ${prof.minIntervalHours} 小时，之后按当日评分安排`);
  }
  if (verdict === 'rest') {
    list.push({ at: new Date(now.getTime() + 60000).toISOString(), kind: 'rest', title: '今天身体优先', body: body.reasons.find((r) => r.pts <= -20)?.text || '今天休息' });
  }
  list.sort((a, b) => a.at.localeCompare(b.at));
  return list;
}

function dayWordFor(dayISO, todayISO) {
  const diff = dayDiff(todayISO, dayISO);
  if (diff <= 0) return '今天 ';
  if (diff === 1) return '明天 ';
  if (diff === 2) return '后天 ';
  return `${dayISO.slice(5).replace('-', '/')} `;
}

/** 今天这一“作息日”的就寝 Date（就寝在午夜后则落到次日凌晨） */
export function bedDateFor(dayISO, sched, tz) {
  const wakeM = sched.wakeM, bedM = sched.bedM;
  const bedRel = ringMinutes(bedM, wakeM);
  const minutes = wakeM + bedRel; // 可能 > 1440
  return makeLocalDate(dayISO, minutes, tz);
}

export { addDays };
