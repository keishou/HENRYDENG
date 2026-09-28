// 提醒：页面内定时通知（Notification API）、Web Push 订阅（需服务器）、ICS 日历导出。
import { localParts, fmtHHMM } from './time.js';

const timers = [];

export function notificationSupport() {
  return { notification: typeof Notification !== 'undefined', sw: 'serviceWorker' in navigator, push: 'PushManager' in window };
}

export async function requestPermission() {
  if (typeof Notification === 'undefined') return 'unsupported';
  if (Notification.permission === 'granted') return 'granted';
  return Notification.requestPermission();
}

export async function showNow(title, body, tag = 'tide') {
  try {
    const reg = await navigator.serviceWorker?.getRegistration();
    if (reg?.showNotification) return reg.showNotification(title, { body, tag, icon: './icons/icon.svg', badge: './icons/icon.svg', renotify: true });
    if (typeof Notification !== 'undefined' && Notification.permission === 'granted') new Notification(title, { body, tag });
  } catch (e) { console.warn('notify failed', e); }
}

/** 页面打开期间，用 setTimeout 触发未来 24h 内的提醒 */
export function scheduleLocal(reminders, now = new Date()) {
  clearLocal();
  let n = 0;
  for (const r of reminders || []) {
    const delay = new Date(r.at).getTime() - now.getTime();
    if (delay < 0 || delay > 24 * 3600000) continue;
    timers.push(setTimeout(() => showNow(r.title, r.body, `tide-${r.kind}`), delay));
    n++;
  }
  return n;
}
export function clearLocal() { while (timers.length) clearTimeout(timers.pop()); }

function urlB64ToUint8(base64) {
  const pad = '='.repeat((4 - (base64.length % 4)) % 4);
  const b = (base64 + pad).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(b); const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

export async function subscribePush(vapidPublicKey, apiFetch) {
  const reg = await navigator.serviceWorker.ready;
  let sub = await reg.pushManager.getSubscription();
  if (!sub) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlB64ToUint8(vapidPublicKey) });
  await apiFetch('/push/subscribe', { method: 'POST', body: JSON.stringify(sub.toJSON()) });
  return sub;
}
export async function unsubscribePush(apiFetch) {
  const reg = await navigator.serviceWorker.ready;
  const sub = await reg.pushManager.getSubscription();
  if (sub) { await apiFetch('/push/unsubscribe', { method: 'POST', body: JSON.stringify({ endpoint: sub.endpoint }) }).catch(() => {}); await sub.unsubscribe(); }
}
export async function currentPushSubscription() {
  try { const reg = await navigator.serviceWorker.ready; return reg.pushManager.getSubscription(); } catch { return null; }
}

/** 导出 .ics（每条提醒一个事件，带 0 分钟提前的 VALARM） */
export function buildICS(reminders, tz) {
  const esc = (s) => String(s || '').replace(/\\/g, '\\\\').replace(/;/g, '\;').replace(/,/g, '\\,').replace(/\n/g, '\\n');
  const stamp = (d) => new Date(d).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//tide//zh-CN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH'];
  for (const r of reminders) {
    const start = new Date(r.at);
    const end = new Date(start.getTime() + 15 * 60000);
    lines.push('BEGIN:VEVENT', `UID:tide-${r.kind}-${stamp(start)}@tide`, `DTSTAMP:${stamp(new Date())}`, `DTSTART:${stamp(start)}`, `DTEND:${stamp(end)}`,
      `SUMMARY:${esc(r.title)}`, `DESCRIPTION:${esc(r.body)}`, 'BEGIN:VALARM', 'TRIGGER:-PT0M', 'ACTION:DISPLAY', `DESCRIPTION:${esc(r.title)}`, 'END:VALARM', 'END:VEVENT');
  }
  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
}

export function downloadText(filename, text, mime = 'text/plain') {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

export function reminderLabel(r, tz) {
  const p = localParts(new Date(r.at), tz);
  return `${fmtHHMM(p.minutes)} · ${r.title}`;
}
