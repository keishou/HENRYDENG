/* 潮汐 service worker：离线壳缓存 + 推送通知 */
const CACHE = 'tide-v1';
const SHELL = ['./', './index.html', './css/app.css', './js/app.js', './js/engine.js', './js/insights.js', './js/time.js', './js/oura.js', './js/store.js', './js/demo.js', './js/reminders.js', './manifest.webmanifest', './icons/icon.svg', './icons/icon-maskable.svg'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/auth/') || url.pathname.startsWith('/push/')) return;
  // 网络优先，失败回退缓存（保证更新及时）
  e.respondWith(fetch(e.request).then((res) => { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); return res; }).catch(() => caches.match(e.request)));
});
self.addEventListener('push', (e) => {
  let data = {};
  try { data = e.data ? e.data.json() : {}; } catch { data = { title: '潮汐', body: e.data ? e.data.text() : '' }; }
  const title = data.title || '潮汐';
  e.waitUntil(self.registration.showNotification(title, { body: data.body || '', tag: data.tag || 'tide', icon: './icons/icon.svg', badge: './icons/icon.svg', renotify: true, data: { url: data.url || './' } }));
});
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const target = new URL(e.notification.data?.url || './', self.location.origin).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
    for (const c of list) if (c.url.startsWith(self.location.origin)) { c.focus(); return; }
    return self.clients.openWindow(target);
  }));
});
