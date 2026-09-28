import test from 'node:test';
import assert from 'node:assert/strict';
import { computePlan, DEFAULT_PROFILE, resolveSchedule, hourBucket } from '../public/js/engine.js';
import { makeLocalDate, localParts, fmtHHMM, parseHHMM, addDays } from '../public/js/time.js';

const TZ = 'Asia/Shanghai';
const profile = { ...DEFAULT_PROFILE, timezone: TZ };
const healthy = {
  readiness: { score: 88, temperature_deviation: 0.02, contributors: {} },
  sleep: { score: 82, contributors: {} },
  sleepDetail: { average_hrv: 52, lowest_heart_rate: 50, latency: 600, total_sleep_duration: 7 * 3600 },
  stress: { day_summary: 'normal' },
  sleepTime: null,
  baselines: { hrv: 50, rhr: 50 },
};
const at = (day, hhmm) => makeLocalDate(day, parseHHMM(hhmm), TZ);

test('time: makeLocalDate roundtrips across zones', () => {
  for (const tz of ['Asia/Shanghai', 'America/New_York', 'Europe/Berlin', 'UTC']) {
    for (const [day, m] of [['2026-09-28', 0], ['2026-09-28', 90], ['2026-03-08', 240], ['2026-11-01', 90], ['2026-12-31', 1439]]) {
      const d = makeLocalDate(day, m, tz);
      const p = localParts(d, tz);
      assert.equal(p.dayISO, day, `${tz} ${day} ${m}`);
      assert.equal(p.minutes, m, `${tz} ${day} ${m}`);
    }
  }
  assert.equal(addDays('2026-02-28', 1), '2026-03-01');
  // DST 缺口（纽约 2026-03-08 02:30 不存在）：仍应返回合法时间且不抛错
  const gap = localParts(makeLocalDate('2026-03-08', 150, 'America/New_York'), 'America/New_York');
  assert.equal(gap.dayISO, '2026-03-08');
  assert.equal(fmtHHMM(1470), '00:30');
});

test('healthy day at 10:00 → go, best window in the pre-bed range', () => {
  const plan = computePlan({ now: at('2026-09-28', '10:00'), profile, oura: healthy, sessions: [] });
  assert.equal(plan.verdict, 'go');
  assert.ok(plan.bestWindow, 'has window');
  const s = parseHHMM(plan.bestWindow.startLabel), e = parseHHMM(plan.bestWindow.endLabel);
  assert.ok(s >= 21 * 60 && e <= 23 * 60 + 30, `window ${plan.bestWindow.startLabel}-${plan.bestWindow.endLabel}`);
  assert.equal(plan.slots.length, 24);
  // focus block hour scores lower than pre-bed hour
  const h10 = plan.slots[10].score, h22 = plan.slots[22].score;
  assert.ok(h10 < h22, `focus ${h10} < prebed ${h22}`);
  assert.ok(plan.slots[10].reasons.some((r) => r.includes('专注')));
  // sleep hours are zero
  assert.equal(plan.slots[3].score, 0);
  assert.ok(plan.slots[9].past && !plan.slots[10].past && plan.slots[10].current);
});

test('elevated temperature → rest verdict and rest notice', () => {
  const sick = { ...healthy, readiness: { score: 70, temperature_deviation: 0.7 } };
  const plan = computePlan({ now: at('2026-09-28', '09:00'), profile, oura: sick, sessions: [] });
  assert.equal(plan.verdict, 'rest');
  assert.ok(plan.flags.illness);
  assert.ok(plan.reminders.some((r) => r.kind === 'rest'));
  assert.ok(Math.max(...plan.slots.map((s) => s.score)) <= 60);
});

test('cooldown: session 10h ago with 36h minimum → wait, slots capped until nextAllowedAt', () => {
  const now = at('2026-09-28', '12:00');
  const last = new Date(now.getTime() - 10 * 3600000);
  const plan = computePlan({ now, profile, oura: healthy, sessions: [{ ts: last.toISOString() }] });
  assert.equal(plan.verdict, 'wait');
  assert.equal(plan.interval.inCooldown, true);
  assert.equal(new Date(plan.interval.nextAllowedAt).getTime(), last.getTime() + 36 * 3600000);
  for (const s of plan.slots) if (!s.past) assert.ok(s.score <= 20, `hour ${s.hour} score ${s.score}`);
  assert.ok(plan.reminders.some((r) => r.kind === 'cooldown_end'));
});

test('target interval reached adds bonus; reminders all in future and sorted', () => {
  const now = at('2026-09-28', '08:00');
  const last = new Date(now.getTime() - 4 * 24 * 3600000);
  const plan = computePlan({ now, profile, oura: healthy, sessions: [{ ts: last.toISOString() }] });
  assert.ok(plan.reasons.some((r) => r.kind === 'interval' && r.pts > 0));
  let prev = 0;
  for (const r of plan.reminders) {
    const t = new Date(r.at).getTime();
    assert.ok(t > now.getTime(), 'future');
    assert.ok(t >= prev, 'sorted'); prev = t;
  }
  assert.ok(plan.reminders.some((r) => r.kind === 'window'));
  assert.ok(plan.reminders.some((r) => r.kind === 'bedtime'));
});

test('oura sleep_time window with negative offsets → bedtime 22:30–00:30 midpoint 23:30', () => {
  const oura = { ...healthy, sleepTime: { optimal_bedtime: { start_offset: -5400, end_offset: 1800, day_tz: 28800 }, status: 'optimal_found', recommendation: 'follow_optimal_bedtime' } };
  const sched = resolveSchedule(profile, oura);
  assert.equal(sched.bedSource, 'oura');
  assert.equal(fmtHHMM(sched.ouraWindow.startM), '22:30');
  assert.equal(fmtHHMM(sched.ouraWindow.endM), '00:30');
  assert.equal(fmtHHMM(sched.bedM), '23:30');
  const off = resolveSchedule({ ...profile, useOuraBedtime: false }, oura);
  assert.equal(off.bedSource, 'profile');
});

test('no oura data still produces a plan driven by schedule', () => {
  const plan = computePlan({ now: at('2026-09-28', '19:00'), profile, oura: null, sessions: [] });
  assert.ok(['go', 'ok'].includes(plan.verdict));
  assert.ok(plan.reasons.some((r) => r.kind === 'info'));
});

test('focus goal penalises work hours harder than sleep goal', () => {
  const now = at('2026-09-28', '07:30');
  const f = computePlan({ now, profile: { ...profile, goal: 'focus' }, oura: healthy });
  const s = computePlan({ now, profile: { ...profile, goal: 'sleep' }, oura: healthy });
  assert.ok(f.slots[10].score < s.slots[10].score);
  assert.ok(f.slots[22].score <= s.slots[22].score);
});

test('personal adjustments shift bucket scores', () => {
  const now = at('2026-09-28', '07:30');
  const base = computePlan({ now, profile, oura: healthy });
  const adj = computePlan({ now, profile, oura: healthy, adjustments: { byHourBucket: { night: 10, morning: -10 } } });
  assert.equal(adj.slots[22].score - base.slots[22].score, 10);
  assert.equal(base.slots[8].score - adj.slots[8].score, 10);
  assert.equal(hourBucket(22), 'night');
});

test('late-night now after bedtime → window already gone', () => {
  const plan = computePlan({ now: at('2026-09-28', '23:50'), profile: { ...profile, bedTime: '23:30' }, oura: healthy });
  assert.equal(plan.verdict, 'skip');
  assert.equal(plan.bestWindow, null);
});
