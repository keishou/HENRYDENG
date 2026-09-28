// 演示数据：30 天合成的 Oura 记录 + 几次示例记录，让没有戒指/没连接时也能看到完整界面。
import { addDays, makeLocalDate, todayISO } from './time.js';

function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

export function buildDemoWindow(tz, now = new Date(), days = 30) {
  const rand = rng(20260928);
  const end = todayISO(tz, now);
  const start = addDays(end, -days);
  const raw = { daily_readiness: [], daily_sleep: [], sleep: [], daily_activity: [], daily_stress: [], sleep_time: [], daily_resilience: [] };
  const n = (mu, sd) => mu + (rand() + rand() + rand() - 1.5) * sd * 1.6;
  for (let i = 0; i <= days; i++) {
    const day = addDays(start, i);
    const sick = i === days - 9; // 某一天体温偏高
    const bedM = Math.round(n(23 * 60 + 20, 35));
    const wakeM = Math.round(n(7 * 60, 25));
    const bedtimeStart = makeLocalDate(addDays(day, -1), bedM, tz);
    const bedtimeEnd = makeLocalDate(day, wakeM, tz);
    const tib = (bedtimeEnd - bedtimeStart) / 1000;
    const eff = Math.round(n(88, 4));
    const total = Math.round(tib * eff / 100);
    const sleepScore = Math.round(Math.min(95, Math.max(45, n(78, 8) - (sick ? 15 : 0))));
    const readiness = Math.round(Math.min(96, Math.max(40, n(79, 9) - (sick ? 30 : 0))));
    const hrv = Math.round(n(48, 7) - (sick ? 12 : 0));
    const rhr = Math.round(n(52, 2.5) + (sick ? 6 : 0));
    raw.daily_readiness.push({ id: `r${i}`, day, score: readiness, temperature_deviation: +(sick ? 0.62 : n(0.02, 0.12)).toFixed(2), temperature_trend_deviation: 0, timestamp: `${day}T00:00:00+08:00`, contributors: { hrv_balance: Math.round(n(75, 10)), resting_heart_rate: Math.round(n(80, 10)), recovery_index: Math.round(n(78, 12)), sleep_balance: Math.round(n(80, 10)), previous_night: sleepScore, activity_balance: Math.round(n(80, 8)), body_temperature: sick ? 30 : 95 } });
    raw.daily_sleep.push({ id: `s${i}`, day, score: sleepScore, timestamp: `${day}T00:00:00+08:00`, contributors: { deep_sleep: Math.round(n(75, 10)), efficiency: eff, latency: Math.round(n(80, 12)), rem_sleep: Math.round(n(75, 12)), restfulness: Math.round(n(70, 12)), timing: Math.round(n(85, 8)), total_sleep: Math.round(n(80, 10)) } });
    raw.sleep.push({ id: `sl${i}`, day, type: 'long_sleep', bedtime_start: bedtimeStart.toISOString(), bedtime_end: bedtimeEnd.toISOString(), average_hrv: hrv, average_heart_rate: rhr + 5, lowest_heart_rate: rhr, latency: Math.round(Math.max(120, n(720, 240))), efficiency: eff, time_in_bed: Math.round(tib), total_sleep_duration: total, deep_sleep_duration: Math.round(total * n(0.2, 0.03)), rem_sleep_duration: Math.round(total * n(0.22, 0.03)), light_sleep_duration: Math.round(total * 0.55), average_breath: +n(14.5, 0.6).toFixed(1) });
    raw.daily_activity.push({ id: `a${i}`, day, score: Math.round(n(80, 8)), steps: Math.round(n(8500, 2500)), high_activity_time: Math.round(Math.max(0, n(900, 900))), medium_activity_time: Math.round(n(3600, 1200)), active_calories: Math.round(n(450, 120)) });
    const stressHigh = Math.round(Math.max(0, n(5400, 3600)));
    raw.daily_stress.push({ id: `st${i}`, day, day_summary: stressHigh > 9000 ? 'stressful' : stressHigh < 2400 ? 'restored' : 'normal', stress_high: stressHigh, recovery_high: Math.round(Math.max(0, n(7200, 3000))) });
    raw.sleep_time.push({ id: `t${i}`, day, optimal_bedtime: { day_tz: 28800, start_offset: -5400, end_offset: 1800 }, recommendation: 'follow_optimal_bedtime', status: 'optimal_found' });
    raw.daily_resilience.push({ id: `re${i}`, day, level: 'solid', contributors: { sleep_recovery: 70, daytime_recovery: 65, stress: 60 } });
  }
  // 让“睡前”释放之夜略好一点、“早晨”之夜略差一点，用于演示洞察
  const byDay = Object.fromEntries(raw.daily_sleep.map((s) => [s.day, s]));
  const rByDay = Object.fromEntries(raw.daily_readiness.map((s) => [s.day, s]));
  const slByDay = Object.fromEntries(raw.sleep.map((s) => [s.day, s]));
  const sessions = [];
  const plan = [[27, 22], [24, 22], [21, 9], [18, 22], [15, 22], [12, 9], [9, 23], [6, 21], [3, 9]];
  for (const [back, hour] of plan) {
    const day = addDays(end, -back);
    const ts = makeLocalDate(day, hour * 60 + 10, tz).toISOString();
    sessions.push({ id: `demo${back}`, ts, note: '', demo: true });
    const night = addDays(day, 1);
    const good = hour >= 21;
    if (byDay[night]) byDay[night].score = Math.min(96, Math.max(40, byDay[night].score + (good ? 7 : -5)));
    if (rByDay[night]) rByDay[night].score = Math.min(96, Math.max(40, rByDay[night].score + (good ? 5 : -6)));
    if (slByDay[night]) { slByDay[night].latency = Math.max(120, slByDay[night].latency + (good ? -240 : 180)); slByDay[night].average_hrv += good ? 4 : -3; }
  }
  return { window: { fetchedAt: now.toISOString(), start, end, raw, errors: [] }, sessions };
}
