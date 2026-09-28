// 本地时间工具（支持 IANA 时区）。浏览器与 Node 共用，无 DOM 依赖。

const fmtCache = new Map();

function formatter(tz) {
  const key = tz || 'local';
  let f = fmtCache.get(key);
  if (!f) {
    f = new Intl.DateTimeFormat('en-US', {
      timeZone: tz || undefined,
      hourCycle: 'h23',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      weekday: 'short',
    });
    fmtCache.set(key, f);
  }
  return f;
}

export function defaultTZ() {
  try { return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'; } catch { return 'UTC'; }
}

export function pad2(n) { return String(n).padStart(2, '0'); }

/** 把 Date 拆成某时区下的本地各部分 */
export function localParts(date, tz) {
  const d = date instanceof Date ? date : new Date(date);
  const parts = {};
  for (const p of formatter(tz).formatToParts(d)) parts[p.type] = p.value;
  const year = +parts.year, month = +parts.month, day = +parts.day;
  const hour = +parts.hour === 24 ? 0 : +parts.hour;
  const minute = +parts.minute, second = +parts.second;
  const weekdayMap = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  return {
    year, month, day, hour, minute, second,
    weekday: weekdayMap[parts.weekday] ?? 0,
    dayISO: `${year}-${pad2(month)}-${pad2(day)}`,
    minutes: hour * 60 + minute,
  };
}

/** 该时刻在时区 tz 的偏移（本地 - UTC，毫秒） */
export function tzOffsetMs(date, tz) {
  const p = localParts(date, tz);
  const asUTC = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  return asUTC - Math.floor(date.getTime() / 1000) * 1000;
}

/** 由本地日期 + 当日分钟数 构造 Date（处理 DST 边缘） */
export function makeLocalDate(dayISO, minutes, tz) {
  const [y, m, d] = dayISO.split('-').map(Number);
  const extraDays = Math.floor(minutes / 1440);
  const min = ((minutes % 1440) + 1440) % 1440;
  const asUTC = Date.UTC(y, m - 1, d + extraDays, Math.floor(min / 60), min % 60, 0);
  let date = new Date(asUTC - tzOffsetMs(new Date(asUTC), tz));
  const off2 = tzOffsetMs(date, tz);
  const date2 = new Date(asUTC - off2);
  if (date2.getTime() !== date.getTime()) date = date2;
  return date;
}

export function parseHHMM(s) {
  if (typeof s === 'number') return s;
  const m = /^(\d{1,2}):(\d{2})$/.exec(String(s || '').trim());
  if (!m) return null;
  return (+m[1]) * 60 + (+m[2]);
}

export function fmtHHMM(minutes) {
  const m = ((Math.round(minutes) % 1440) + 1440) % 1440;
  return `${pad2(Math.floor(m / 60))}:${pad2(m % 60)}`;
}

export function addDays(dayISO, n) {
  const [y, m, d] = dayISO.split('-').map(Number);
  const t = Date.UTC(y, m - 1, d + n);
  const x = new Date(t);
  return `${x.getUTCFullYear()}-${pad2(x.getUTCMonth() + 1)}-${pad2(x.getUTCDate())}`;
}

export function dayDiff(a, b) {
  const [ya, ma, da] = a.split('-').map(Number);
  const [yb, mb, db] = b.split('-').map(Number);
  return Math.round((Date.UTC(yb, mb - 1, db) - Date.UTC(ya, ma - 1, da)) / 86400000);
}

export function todayISO(tz, now = new Date()) { return localParts(now, tz).dayISO; }

export function median(arr) {
  const a = arr.filter((x) => typeof x === 'number' && Number.isFinite(x)).sort((x, y) => x - y);
  if (!a.length) return null;
  const mid = Math.floor(a.length / 2);
  return a.length % 2 ? a[mid] : (a[mid - 1] + a[mid]) / 2;
}

export function mean(arr) {
  const a = arr.filter((x) => typeof x === 'number' && Number.isFinite(x));
  if (!a.length) return null;
  return a.reduce((s, x) => s + x, 0) / a.length;
}

export function clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }

/** "23:30"/"01:10" 之类的就寝时间 → 相对 wake 的环形分钟（处理跨午夜） */
export function ringMinutes(minute, wakeM) { return ((minute - wakeM) % 1440 + 1440) % 1440; }
