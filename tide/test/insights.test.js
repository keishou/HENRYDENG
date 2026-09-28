import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeSessions, intervalBucket, compositeOf } from '../public/js/insights.js';
import { makeLocalDate, addDays } from '../public/js/time.js';

const TZ = 'Asia/Shanghai';
function buildDays(start, n, fn) {
  const days = {};
  for (let i = 0; i < n; i++) { const d = addDays(start, i); days[d] = fn(d, i); }
  return days;
}
const normal = () => ({ readiness: { score: 75 }, sleep: { score: 75 }, sleepDetail: { average_hrv: 50, latency: 900, deep_sleep_duration: 5400, lowest_heart_rate: 52 } });
const good = () => ({ readiness: { score: 85 }, sleep: { score: 86 }, sleepDetail: { average_hrv: 60, latency: 480, deep_sleep_duration: 6000, lowest_heart_rate: 50 } });

test('sessions at night improve next-night metrics vs baseline', () => {
  const start = '2026-09-01';
  const sessionDays = ['2026-09-03', '2026-09-06', '2026-09-10', '2026-09-14', '2026-09-18'];
  const nights = new Set(sessionDays.map((d) => addDays(d, 1)));
  const days = buildDays(start, 25, (d) => (nights.has(d) ? good() : normal()));
  const sessions = sessionDays.map((d, i) => ({ id: `s${i}`, ts: makeLocalDate(d, 22 * 60, TZ).toISOString() }));
  const res = analyzeSessions({ sessions, days, tz: TZ });
  assert.equal(res.analyzed, 5);
  assert.equal(res.baseline.sleepScore, 75);
  assert.equal(res.overall.meanDelta.sleepScore, 11);
  assert.equal(res.overall.meanDelta.readiness, 10);
  assert.equal(res.overall.meanDelta.latencyMin, -7);
  assert.equal(res.byHour.night.n, 5);
  assert.ok(res.adjustments.byHourBucket.night > 0);
  assert.equal(res.adjustments.byHourBucket.morning, undefined);
  assert.equal(res.bestHourBucket.key, 'night');
  assert.ok(res.summary[0].includes('已分析 5 次'));
});

test('a 02:00 session belongs to the previous evening; missing night → unavailable', () => {
  const days = { '2026-09-05': normal(), '2026-09-06': good() };
  const sessions = [
    { id: 'a', ts: makeLocalDate('2026-09-05', 2 * 60, TZ).toISOString() },   // 9/5 02:00 → night day 9/5
    { id: 'b', ts: makeLocalDate('2026-09-20', 22 * 60, TZ).toISOString() },  // no data
  ];
  const res = analyzeSessions({ sessions, days, tz: TZ });
  assert.equal(res.outcomes[0].nightDay, '2026-09-05');
  assert.equal(res.outcomes[0].hourBucket, 'late');
  assert.equal(res.outcomes[0].available, true);
  assert.equal(res.outcomes[1].available, false);
  assert.equal(res.outcomes[1].intervalBucket, 'gt4d');
  assert.equal(intervalBucket(30), 'd1_2');
  assert.equal(intervalBucket(null), 'first');
});

test('composite weights', () => {
  assert.equal(compositeOf({ sleepScore: 10, readiness: 10, latencyMin: -10, hrv: 5, deepMin: 10 }, { hrv: 50 }), 29);
  assert.equal(compositeOf({}, {}), null);
});
