// 本地存储：档案、记录、Oura 缓存、连接状态。全部在浏览器 localStorage。
import { DEFAULT_PROFILE } from './engine.js';

const NS = 'tide:';
function read(key, fallback) {
  try { const v = localStorage.getItem(NS + key); return v == null ? fallback : JSON.parse(v); } catch { return fallback; }
}
function write(key, value) {
  try { if (value === undefined) localStorage.removeItem(NS + key); else localStorage.setItem(NS + key, JSON.stringify(value)); } catch { /* 隐私模式等 */ }
}

export const store = {
  getProfile() { return { ...DEFAULT_PROFILE, ...read('profile', {}) }; },
  setProfile(p) { write('profile', p); },

  isDemo() { return !!read('demo', false); },
  setDemo(on) { write('demo', !!on); },

  sessionsKey() { return this.isDemo() ? 'sessions_demo' : 'sessions'; },
  getSessions() { return read(this.sessionsKey(), []); },
  setSessions(list) { write(this.sessionsKey(), list); },
  addSession(s) { const list = this.getSessions(); list.push(s); this.setSessions(list); return list; },
  removeSession(id) { this.setSessions(this.getSessions().filter((s) => s.id !== id)); },

  getOuraCache() { return read(this.isDemo() ? 'oura_demo' : 'oura', null); },
  setOuraCache(v) { write(this.isDemo() ? 'oura_demo' : 'oura', v); },

  // 直连模式的 token（静态部署 / 旧 PAT）
  getDirectToken() { return read('direct_token', null); },
  setDirectToken(t) { write('direct_token', t || undefined); },
  getClientId() { return read('client_id', ''); },
  setClientId(v) { write('client_id', v || undefined); },

  getAppKey() { return read('app_key', ''); },
  setAppKey(v) { write('app_key', v || undefined); },

  getNotifyPrefs() { return { local: true, push: false, ...read('notify', {}) }; },
  setNotifyPrefs(v) { write('notify', v); },

  getLastPlan() { return read('last_plan', null); },
  setLastPlan(v) { write('last_plan', v); },

  exportAll() {
    const out = {};
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(NS) && !k.includes('token') && !k.includes('app_key')) out[k.slice(NS.length)] = read(k.slice(NS.length), null);
    }
    return out;
  },
  importAll(obj) {
    for (const [k, v] of Object.entries(obj || {})) if (!k.includes('token') && !k.includes('app_key')) write(k, v);
  },
  clearAll() {
    const keys = [];
    for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k && k.startsWith(NS)) keys.push(k); }
    keys.forEach((k) => localStorage.removeItem(k));
  },
};

export function uid() { return Math.random().toString(36).slice(2, 10) + Date.now().toString(36); }
